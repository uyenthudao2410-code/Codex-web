param(
  [Parameter(Mandatory=$true)][string]$Candidate,
  [Parameter(Mandatory=$true)][string]$Epoch,
  [Parameter(Mandatory=$true)][string]$PackageProof
)
$ErrorActionPreference = 'Stop'
$taskObserver = Join-Path $PSScriptRoot 'verify-live-renderer.cjs'
$taskExecutable = Join-Path $Candidate 'Coding Tools MCP.exe'
$taskId = [guid]::NewGuid().ToString('N')
$taskStdout = Join-Path $PSScriptRoot ('live-renderer-' + $taskId + '.stdout.json')
$taskStderr = Join-Path $PSScriptRoot ('live-renderer-' + $taskId + '.stderr.txt')
if ($Candidate.Contains('"') -or $Epoch.Contains('"') -or $PackageProof.Contains('"')) { throw 'Unexpected argument quote' }
$taskArguments = @(('"' + $taskObserver + '"'), ('"' + $Candidate + '"'), $Epoch, ('"' + $PackageProof + '"'))
$taskPreviousRunAsNode = $env:ELECTRON_RUN_AS_NODE
try {
  $env:ELECTRON_RUN_AS_NODE = '1'
  $taskProcess = Start-Process -FilePath $taskExecutable -ArgumentList $taskArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $taskStdout -RedirectStandardError $taskStderr
  $taskOutputPath = if ($taskProcess.ExitCode -eq 0) { $taskStdout } else { $taskStderr }
  $taskOutput = Get-Content -LiteralPath $taskOutputPath -Raw
  if ($taskOutput.Trim()) { Write-Output $taskOutput.Trim() }
  Write-Output ('PROCESS_EXIT=' + $taskProcess.ExitCode)
  exit $taskProcess.ExitCode
} finally {
  $env:ELECTRON_RUN_AS_NODE = $taskPreviousRunAsNode
}
