# Root-only authenticated output read. This file's preparation performs no effects.
# Use actual durable correlation.completed_at_ms, not receipt/overview arrival time.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Observation,
  [Parameter(Mandatory=$true)][string]$ObservationSha256,
  [Parameter(Mandatory=$true)][string]$Pins,
  [Parameter(Mandatory=$true)][string]$PinsSha256,
  [Parameter(Mandatory=$true)][long]$CompletedAtMs,
  [switch]$Execute
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$r12CaptureHere = [IO.Path]::GetFullPath($PSScriptRoot)
$r12CaptureRoot = 'E:\Github\Tools-Codex-web'
$r12CaptureProfile = 'C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
$r12CaptureHelper = Join-Path $r12CaptureHere 'native-output-read.cjs'
$r12CaptureExecutable = Join-Path $r12CaptureRoot 'node_modules\electron\dist\electron.exe'
$r12CaptureOutput = $null
function Need-Capture([bool]$Test,[string]$Code) { if (-not $Test) { throw [InvalidOperationException]::new($Code) } }
function Capture-Sha([string]$Path) {
  $stream=[IO.File]::OpenRead($Path);$hash=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
  finally { $hash.Dispose();$stream.Dispose() }
}
function Quote-CaptureArgument([string]$Text) {
  Need-Capture ($Text -notmatch '[\x00-\x1f"]' -and -not $Text.EndsWith('\')) 'CAPTURE_ARGUMENT_UNSAFE'
  return '"'+$Text+'"'
}
try {
  Need-Capture ([bool]$Execute) 'EXPLICIT_ROOT_CAPTURE_REQUIRED'
  Need-Capture ($r12CaptureHere -ieq (Join-Path $r12CaptureRoot '.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r12\live-canary')) 'EXACT_CAPTURE_DIRECTORY_REQUIRED'
  Need-Capture ((Capture-Sha $r12CaptureHelper) -ceq '03b3901906a7f8a553b62adaec004463eeaf3c8e0c4353bdf4d68bb9d7f67dd4') 'FROZEN_R12_OUTPUT_READER_CHANGED'
  foreach ($r12InputPin in @(@($Observation,$ObservationSha256),@($Pins,$PinsSha256))) {
    Need-Capture ([IO.Path]::IsPathRooted([string]$r12InputPin[0]) -and [string]$r12InputPin[1] -cmatch '^[a-f0-9]{64}$' -and
      (Capture-Sha ([string]$r12InputPin[0])) -ceq [string]$r12InputPin[1]) 'EXACT_PUBLIC_CAPTURE_INPUT_HASH_REQUIRED'
  }
  $age = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()-$CompletedAtMs
  Need-Capture ($age -ge 0 -and $age -lt 300000) 'OUTPUT_RETENTION_WINDOW_EXPIRED'
  $r12CaptureOutput=Join-Path $r12CaptureHere ('native-output-'+[DateTime]::UtcNow.ToString("yyyyMMdd'T'HHmmssfff'Z'")+'.json')
  Need-Capture (-not (Test-Path -LiteralPath $r12CaptureOutput)) 'OUTPUT_RECEIPT_ALREADY_EXISTS'
  $r12CaptureArguments=@("--user-data-dir=$r12CaptureProfile",$r12CaptureHelper,
    "--observation=$([IO.Path]::GetFullPath($Observation))","--observation-sha256=$ObservationSha256",
    "--pins=$([IO.Path]::GetFullPath($Pins))","--pins-sha256=$PinsSha256",
    "--completed-at-ms=$CompletedAtMs","--receipt=$r12CaptureOutput")
  $r12CaptureSpec=[Diagnostics.ProcessStartInfo]::new()
  $r12CaptureSpec.FileName=$r12CaptureExecutable
  $r12CaptureSpec.Arguments=(@($r12CaptureArguments|ForEach-Object {Quote-CaptureArgument ([string]$_)})-join ' ')
  $r12CaptureSpec.WorkingDirectory=$r12CaptureRoot
  $r12CaptureSpec.UseShellExecute=$false
  $r12CaptureSpec.CreateNoWindow=$true
  $r12CaptureSpec.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
  $r12CaptureSpec.RedirectStandardOutput=$true
  $r12CaptureSpec.RedirectStandardError=$true
  $r12CaptureSpec.EnvironmentVariables.Remove('ELECTRON_RUN_AS_NODE')
  $r12CaptureSpec.EnvironmentVariables.Remove('NODE_OPTIONS')
  $r12CaptureSpec.EnvironmentVariables.Remove('NODE_EXTRA_CA_CERTS')
  $r12CaptureProcess=[Diagnostics.Process]::Start($r12CaptureSpec)
  Need-Capture ($null -ne $r12CaptureProcess) 'CAPTURE_START_OUTCOME_UNKNOWN_INSPECT_RECEIPT'
  $r12CaptureStdout=$r12CaptureProcess.StandardOutput.ReadToEndAsync()
  $r12CaptureStderr=$r12CaptureProcess.StandardError.ReadToEndAsync()
  try {
    Need-Capture ($r12CaptureProcess.WaitForExit(60000)) 'CAPTURE_TIMEOUT_INSPECT_EXACT_RECEIPT_AND_PROCESS'
    $r12CaptureRaw=$r12CaptureStdout.GetAwaiter().GetResult()
    $null=$r12CaptureStderr.GetAwaiter().GetResult() # Never print stderr or private credentials.
    Need-Capture ($r12CaptureRaw.Length -le 262144 -and $r12CaptureRaw -notmatch 'Bearer\s|PRIVATE KEY|Authorization\s*:') 'CAPTURE_PUBLIC_OUTPUT_UNSAFE'
    $r12CapturePublic=$r12CaptureRaw.Trim()|ConvertFrom-Json
    Need-Capture ($r12CaptureProcess.ExitCode -eq 0 -and $r12CapturePublic.ok -eq $true -and
      $r12CapturePublic.attestation_claimed -eq $false -and $r12CapturePublic.secret_values_emitted -eq $false -and
      $r12CapturePublic.receipt_path -ieq $r12CaptureOutput -and
      (Capture-Sha $r12CaptureOutput) -ceq [string]$r12CapturePublic.receipt_sha256) 'CAPTURE_FAILED_OR_RECEIPT_UNPROVEN'
    $r12CapturePublic|ConvertTo-Json -Depth 12 -Compress|Write-Output
  } finally { $r12CaptureProcess.Dispose() }
} catch {
  $r12CaptureCode=[string]$_.Exception.Message
  if ($r12CaptureCode -cnotmatch '^[A-Z0-9_]{8,128}$') {$r12CaptureCode='ROOT_NATIVE_CAPTURE_REFUSED_INSPECT_EXACT_RECEIPT'}
  @{ok=$false;phase='root_native_capture_failed';code=$r12CaptureCode;receipt_path=$r12CaptureOutput;
    attestation_claimed=$false;acceptance_performed=$false;stderr_disclosed=$false}|ConvertTo-Json -Compress|Write-Output
  exit 2
}
