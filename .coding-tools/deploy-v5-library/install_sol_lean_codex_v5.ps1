[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ArchivePath = "",
    [string]$ManifestPath = "",
    [string]$DestinationRoot = (Join-Path $HOME ".codex\skills"),
    [switch]$RemoveBackupOnSuccess
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedPackageSha256 = "858632ab57fe58c07083f2a1344b8169bad54a28a4947c6a11cf934a4159aa87"
$SkillName = "sol-lean-codex"

if (-not $ArchivePath) {
    $ArchivePath = Join-Path $RepositoryRoot "resources\skills\sol-lean-codex\skill.zip"
}
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $RepositoryRoot "resources\skills\sol-lean-codex\manifest.json"
}

$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)
$ManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)
$DestinationRoot = [System.IO.Path]::GetFullPath($DestinationRoot)

if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "Skill archive not found: $ArchivePath"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Skill manifest not found: $ManifestPath"
}

$archiveSha = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($archiveSha -ne $ExpectedPackageSha256) {
    throw "Skill archive SHA256 mismatch. Expected $ExpectedPackageSha256, got $archiveSha"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$manifest.skill_name -ne $SkillName) {
    throw "Manifest skill_name mismatch: $($manifest.skill_name)"
}
if ([string]$manifest.package_sha256 -ne $ExpectedPackageSha256) {
    throw "Manifest package SHA256 mismatch."
}

function Assert-SkillTree {
    param([Parameter(Mandatory=$true)][string]$SkillRoot)

    if (-not (Test-Path -LiteralPath $SkillRoot -PathType Container)) {
        throw "Skill root missing: $SkillRoot"
    }

    $files = @(Get-ChildItem -LiteralPath $SkillRoot -Recurse -File)
    $expectedCount = [int]$manifest.file_count
    if ($files.Count -ne $expectedCount) {
        throw "Skill file count mismatch. Expected $expectedCount, got $($files.Count)."
    }

    foreach ($entry in $manifest.files.PSObject.Properties) {
        $relative = [string]$entry.Name
        $expectedHash = ([string]$entry.Value).ToLowerInvariant()
        $candidate = Join-Path $SkillRoot ($relative -replace '/', '\\')
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Missing skill file: $relative"
        }
        $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Skill file hash mismatch for $relative. Expected $expectedHash, got $actualHash"
        }
    }
}

function Resolve-ValidationPython {
    $native = Join-Path $RepositoryRoot "resources\native-python\python.exe"
    if (Test-Path -LiteralPath $native -PathType Leaf) {
        return $native
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) { return $python.Source }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return $python.Source }
    throw "No Python runtime is available to run the skill comparator tests."
}

function Invoke-SkillComparator {
    param([Parameter(Mandatory=$true)][string]$SkillRoot)
    $python = Resolve-ValidationPython
    $testFile = Join-Path $SkillRoot "scripts\test_compare_route_policies.py"
    & $python $testFile
    if ($LASTEXITCODE -ne 0) {
        throw "Skill comparator tests failed with exit code $LASTEXITCODE."
    }
}

New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
$stageParent = Join-Path $DestinationRoot (".{0}.stage-{1}" -f $SkillName, [Guid]::NewGuid().ToString("N"))
$stageSkill = Join-Path $stageParent $SkillName
$finalSkill = Join-Path $DestinationRoot $SkillName
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupSkill = Join-Path $DestinationRoot ("{0}.backup-{1}-{2}" -f $SkillName, $timestamp, [Guid]::NewGuid().ToString("N").Substring(0,8))
$backupCreated = $false
$installed = $false

try {
    New-Item -ItemType Directory -Path $stageParent -Force | Out-Null
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $stageParent -Force

    Assert-SkillTree -SkillRoot $stageSkill
    Invoke-SkillComparator -SkillRoot $stageSkill

    if (Test-Path -LiteralPath $finalSkill) {
        Move-Item -LiteralPath $finalSkill -Destination $backupSkill
        $backupCreated = $true
    }

    Move-Item -LiteralPath $stageSkill -Destination $finalSkill
    $installed = $true

    Assert-SkillTree -SkillRoot $finalSkill
    Invoke-SkillComparator -SkillRoot $finalSkill

    if ($RemoveBackupOnSuccess -and $backupCreated -and (Test-Path -LiteralPath $backupSkill)) {
        Remove-Item -LiteralPath $backupSkill -Recurse -Force
        $backupCreated = $false
    }

    $skillMdSha = (Get-FileHash -LiteralPath (Join-Path $finalSkill "SKILL.md") -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Output ("INSTALLED={0}" -f $finalSkill)
    Write-Output ("PACKAGE_SHA256={0}" -f $archiveSha)
    Write-Output ("SKILL_MD_SHA256={0}" -f $skillMdSha)
    Write-Output ("FILES={0}" -f $manifest.file_count)
    if ($backupCreated) {
        Write-Output ("BACKUP={0}" -f $backupSkill)
    }
}
catch {
    if ($installed -and (Test-Path -LiteralPath $finalSkill)) {
        Remove-Item -LiteralPath $finalSkill -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($backupCreated -and (Test-Path -LiteralPath $backupSkill)) {
        Move-Item -LiteralPath $backupSkill -Destination $finalSkill -ErrorAction SilentlyContinue
    }
    throw
}
finally {
    if (Test-Path -LiteralPath $stageParent) {
        Remove-Item -LiteralPath $stageParent -Recurse -Force -ErrorAction SilentlyContinue
    }
}
