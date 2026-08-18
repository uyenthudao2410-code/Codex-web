$ErrorActionPreference = 'Stop'

$root = (Get-Location).Path
$helperRel = 'tmp/commit-current-snapshot-20260818.ps1'
$realIndex = Join-Path $root '.git\index'
$realLock = Join-Path $root '.git\index.lock'
$tmp = Join-Path $env:TEMP ('codex_git_snapshot_' + [guid]::NewGuid().ToString('N'))
$altIndex = Join-Path $env:TEMP ('codex_alt_index_' + [guid]::NewGuid().ToString('N'))
$exclude = @(
  '.coding-tools/orchestration/ledger.sqlite3-shm',
  '.coding-tools/orchestration/ledger.sqlite3-wal'
)
$oldGitIndex = $env:GIT_INDEX_FILE
$commitMade = $false
$synced = $false

if (-not (Test-Path -LiteralPath $realIndex)) {
  throw 'real Git index is missing'
}
Copy-Item -LiteralPath $realIndex -Destination $altIndex -Force
$env:GIT_INDEX_FILE = $altIndex
Write-Output ('ALT_INDEX=' + $altIndex)

function Stage-CodingTools([string]$snapRoot) {
  if (Test-Path -LiteralPath $snapRoot) {
    Remove-Item -LiteralPath $snapRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Path $snapRoot -Force | Out-Null

  $snapshot = @{}
  $base = Join-Path $root '.coding-tools'
  $files = @(Get-ChildItem -LiteralPath $base -Recurse -File -Force)

  foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length + 1).Replace('\', '/')
    if ($exclude -contains $rel) {
      continue
    }

    $dest = Join-Path $snapRoot ($rel.Replace('/', '\'))
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) {
      New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if ($rel -eq '.coding-tools/orchestration/ledger.sqlite3') {
      & python -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" $f.FullName $dest
      if ($LASTEXITCODE -ne 0) {
        throw 'sqlite backup failed'
      }
    } else {
      Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
    }
    $snapshot[$rel] = $dest
  }

  $tracked = @(& git ls-files -- .coding-tools)
  if ($LASTEXITCODE -ne 0) {
    throw 'git ls-files failed'
  }
  foreach ($rel in $tracked) {
    if ([string]::IsNullOrWhiteSpace($rel)) {
      continue
    }
    if (($exclude -contains $rel) -or (-not $snapshot.ContainsKey($rel))) {
      & git update-index --force-remove -- $rel
      if ($LASTEXITCODE -ne 0) {
        throw ('update-index remove failed: ' + $rel)
      }
    }
  }

  foreach ($rel in @($snapshot.Keys | Sort-Object)) {
    $src = $snapshot[$rel]
    $hash = (& git hash-object -w -- $src).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($hash)) {
      throw ('hash-object failed: ' + $rel)
    }

    $entry = @(& git ls-files -s -- $rel)
    if ($LASTEXITCODE -ne 0) {
      throw ('git ls-files -s failed: ' + $rel)
    }
    if ($entry.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($entry[0])) {
      $mode = ($entry[0] -split '\s+')[0]
    } else {
      $mode = '100644'
    }

    & git update-index --add --cacheinfo $mode $hash $rel
    if ($LASTEXITCODE -ne 0) {
      throw ('update-index add failed: ' + $rel)
    }
  }
}

try {
  & git fetch origin main
  if ($LASTEXITCODE -ne 0) { throw 'git fetch failed' }
  Write-Output 'FETCH_DONE'

  & git merge-base --is-ancestor origin/main HEAD
  if ($LASTEXITCODE -ne 0) { throw 'origin/main is not an ancestor of HEAD' }
  Write-Output 'ANCESTRY_DONE'

  & git add -A -- . ':(exclude).coding-tools' (':(exclude)' + $helperRel)
  if ($LASTEXITCODE -ne 0) { throw 'git add non-.coding-tools failed' }
  Stage-CodingTools $tmp
  Write-Output 'STAGE1_DONE'

  & npm run check:coding-tools-delivery
  if ($LASTEXITCODE -ne 0) { throw 'coding-tools delivery guard 1 failed' }
  Write-Output 'GUARD1_DONE'

  & git add -A -- . ':(exclude).coding-tools' (':(exclude)' + $helperRel)
  if ($LASTEXITCODE -ne 0) { throw 'final git add non-.coding-tools failed' }
  Stage-CodingTools $tmp
  Write-Output 'STAGE2_DONE'

  & npm run check:coding-tools-delivery
  if ($LASTEXITCODE -ne 0) { throw 'coding-tools delivery guard 2 failed' }
  Write-Output 'GUARD2_DONE'

  Stage-CodingTools $tmp
  Write-Output 'STAGE3_FINAL_DONE'

  & git diff --cached --check
  if ($LASTEXITCODE -ne 0) { throw 'git diff --cached --check failed' }

  & git diff --cached --quiet
  $diffExit = $LASTEXITCODE
  if ($diffExit -eq 0) { throw 'no staged changes to commit' }
  if ($diffExit -ne 1) { throw ('git diff --cached --quiet failed with ' + $diffExit) }
  Write-Output 'STAGED_DIFF_CONFIRMED'

  & git commit -m 'chore: snapshot current project state'
  if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
  $commitMade = $true

  $committedHead = (& git rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($committedHead)) {
    throw 'could not resolve committed HEAD'
  }
  Write-Output ('COMMIT_DONE=' + $committedHead)

  $env:GIT_INDEX_FILE = $null
  $deadline = [DateTime]::UtcNow.AddSeconds(30)
  $lockStream = $null
  while ($null -eq $lockStream) {
    try {
      $lockStream = [System.IO.File]::Open($realLock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    } catch [System.IO.IOException] {
      if ([DateTime]::UtcNow -ge $deadline) {
        throw 'could not acquire real index lock within 30 seconds'
      }
      Start-Sleep -Milliseconds 100
    }
  }

  try {
    $src = [System.IO.File]::OpenRead($altIndex)
    try {
      $src.CopyTo($lockStream)
    } finally {
      $src.Dispose()
    }
  } finally {
    $lockStream.Dispose()
  }

  Move-Item -LiteralPath $realLock -Destination $realIndex -Force
  $synced = $true
  Write-Output 'REAL_INDEX_SYNCED'

  & git push origin main
  if ($LASTEXITCODE -ne 0) { throw 'git push failed' }
  Write-Output 'PUSH_DONE'

  $head = (& git rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0) { throw 'git rev-parse HEAD failed' }
  $remote = (& git rev-parse origin/main).Trim()
  if ($LASTEXITCODE -ne 0) { throw 'git rev-parse origin/main failed' }
  Write-Output ('HEAD=' + $head)
  Write-Output ('ORIGIN_MAIN=' + $remote)
  if ($head -ne $remote) { throw 'local HEAD does not equal origin/main' }

  & git check-ignore -v --no-index .coding-tools/orchestration/ledger.sqlite3-shm .coding-tools/orchestration/ledger.sqlite3-wal
  if ($LASTEXITCODE -ne 0) { throw 'sidecar ignore verification failed' }

  & git ls-files --error-unmatch .coding-tools/orchestration/ledger.sqlite3
  if ($LASTEXITCODE -ne 0) { throw 'ledger.sqlite3 is not tracked' }
  Write-Output 'POLICY_VERIFY_DONE'

  & git status --short --branch
  if ($LASTEXITCODE -ne 0) { throw 'final git status failed' }
  Write-Output 'SCRIPT_DONE'
} finally {
  if ($null -eq $oldGitIndex) {
    $env:GIT_INDEX_FILE = $null
  } else {
    $env:GIT_INDEX_FILE = $oldGitIndex
  }
  if (Test-Path -LiteralPath $tmp) {
    Remove-Item -LiteralPath $tmp -Recurse -Force
  }
  if ((-not $commitMade) -or $synced) {
    if (Test-Path -LiteralPath $altIndex) {
      Remove-Item -LiteralPath $altIndex -Force
    }
  } else {
    Write-Output ('PRESERVED_ALT_INDEX=' + $altIndex)
  }
}
