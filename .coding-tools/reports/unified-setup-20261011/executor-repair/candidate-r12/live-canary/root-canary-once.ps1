# Root-only one-attempt driver. Preparation of this file performs no effects.
# Root invocation: powershell.exe -NoProfile -ExecutionPolicy Bypass -File <this file>
#   -ReopenedReceipt <absolute r12 reopen receipt> -ExpectedReceiptSha256 <exact file SHA256>
#   -ApprovalId call_1KzUkF0gMn6uVpHd3QisTzXF -Execute
# Stops after one dispatch. Observe, output capture, correlation and cleanup are separate.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ReopenedReceipt,
  [Parameter(Mandatory=$true)][string]$ExpectedReceiptSha256,
  [Parameter(Mandatory=$true)][string]$ApprovalId,
  [switch]$Execute
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$r12Root = 'E:\Github\Tools-Codex-web'
$r12Here = [IO.Path]::GetFullPath($PSScriptRoot)
$r12ManifestSha = '9e99998631a9bcdda82a6460fa2657fa47a77633fdc8e488a071aa8ce9709495'
$r12NativeSha = '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'
$r12IntentPath = Join-Path $r12Here 'root-canary-once.intent.json'
$r12ResultPath = Join-Path $r12Here 'root-canary-once.result.json'
$r12Stage = 'input_guard'
$r12Started = $false
$r12PublicState = [ordered]@{phase='root_r12_canary_once';ok=$false;dispatch_replay_forbidden=$true;acceptance_performed=$false;stderr_disclosed=$false}

function Require-R12([bool]$Condition,[string]$Code) {
  if (-not $Condition) { throw [InvalidOperationException]::new($Code) }
}
function File-Sha256([string]$Path) {
  $stream = [IO.File]::OpenRead($Path)
  $algorithm = [Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
  finally { $algorithm.Dispose(); $stream.Dispose() }
}
function Read-PublicJson([string]$Path) {
  Require-R12 ([IO.Path]::IsPathRooted($Path)) 'ABSOLUTE_PUBLIC_RECEIPT_REQUIRED'
  $item = Get-Item -LiteralPath $Path -Force
  Require-R12 (-not $item.PSIsContainer -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $item.Length -le 1048576) 'PUBLIC_RECEIPT_UNSAFE'
  $raw = [IO.File]::ReadAllText($Path)
  Require-R12 ($raw -notmatch 'Bearer\s|PRIVATE KEY|Authorization\s*:') 'PRIVATE_RECEIPT_REJECTED'
  return ($raw | ConvertFrom-Json)
}
function Write-ExclusiveJson([string]$Path,$Value) {
  $raw = [Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 40 -Compress) + "`n")
  $stream = [IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
  try { $stream.Write($raw,0,$raw.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}
function Assert-HelperPins {
  $manifestPath = Join-Path $r12Here 'helper-manifest.json'
  Require-R12 ((File-Sha256 $manifestPath) -ceq $r12ManifestSha) 'FROZEN_R12_MANIFEST_CHANGED'
  $manifest = Read-PublicJson $manifestPath
  foreach ($record in @($manifest.files)) {
    Require-R12 ([IO.Path]::GetFileName([string]$record.path) -ceq [string]$record.path) 'FROZEN_HELPER_PATH_UNSAFE'
    $file = Join-Path $r12Here ([string]$record.path)
    Require-R12 ((File-Sha256 $file) -ceq [string]$record.sha256 -and (Get-Item -LiteralPath $file).Length -eq [long]$record.bytes) 'FROZEN_R12_HELPER_CHANGED'
  }
}
function Assert-RemainingWindow($Authority) {
  $now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  Require-R12 ([long]$Authority.requested_at_ms -eq 1791747735200 -and [long]$Authority.expires_at_ms -eq 1791751335200 -and
    [long]$Authority.expires_at_ms - [long]$Authority.requested_at_ms -eq 3600000 -and
    [long]$Authority.requested_at_ms -le $now -and [long]$Authority.expires_at_ms - $now -ge 720000) 'APPROVED_WINDOW_INVALID_OR_LESS_THAN_12_MINUTES'
}
function Quote-FixedArgument([string]$Text) {
  Require-R12 ($Text -notmatch '[\x00-\x1f"]' -and -not $Text.EndsWith('\')) 'STRUCTURED_ARGUMENT_UNSAFE'
  return '"' + $Text + '"'
}
function Invoke-OneJson([string]$Executable,[string[]]$Arguments,[string]$Phase) {
  Assert-HelperPins
  Assert-RemainingWindow $r12Authority
  $spec = [Diagnostics.ProcessStartInfo]::new()
  $spec.FileName = $Executable
  $spec.Arguments = (@($Arguments | ForEach-Object { Quote-FixedArgument ([string]$_) }) -join ' ')
  $spec.WorkingDirectory = $r12Root
  $spec.UseShellExecute = $false
  $spec.CreateNoWindow = $true
  $spec.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
  $spec.RedirectStandardOutput = $true
  $spec.RedirectStandardError = $true
  $process = [Diagnostics.Process]::Start($spec)
  Require-R12 ($null -ne $process) 'HELPER_START_OUTCOME_UNKNOWN_NO_REPLAY'
  $stdoutTask = $process.StandardOutput.ReadToEndAsync()
  $stderrTask = $process.StandardError.ReadToEndAsync()
  try {
    if (-not $process.WaitForExit(300000)) {
      $r12PublicState['unfinished_helper_pid'] = $process.Id
      throw [InvalidOperationException]::new('HELPER_TIMEOUT_OUTCOME_UNKNOWN_OBSERVE_DO_NOT_REPLAY')
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $null = $stderrTask.GetAwaiter().GetResult() # Memory only; never disclose stderr.
    Require-R12 ($stdout.Length -le 1048576 -and $stdout -notmatch 'Bearer\s|PRIVATE KEY|Authorization\s*:') 'HELPER_PUBLIC_OUTPUT_UNSAFE'
    $value = $stdout.Trim() | ConvertFrom-Json
    Require-R12 ($process.ExitCode -eq 0 -and $value.ok -eq $true) 'HELPER_REFUSED_OR_OUTCOME_UNKNOWN_NO_REPLAY'
    [ordered]@{phase=('root_r12_' + $Phase);ok=$true;dispatch_replay_forbidden=$true;stderr_disclosed=$false} | ConvertTo-Json -Compress | Write-Host
    return $value
  } finally { $process.Dispose() }
}

try {
  Require-R12 ($Execute -and $ApprovalId -ceq 'call_1KzUkF0gMn6uVpHd3QisTzXF') 'EXPLICIT_APPROVED_R12_EXECUTION_REQUIRED'
  Require-R12 ([IO.Path]::GetFullPath($r12Here) -ieq (Join-Path $r12Root '.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r12\live-canary')) 'EXACT_R12_RUNNER_LOCATION_REQUIRED'
  Require-R12 ($ExpectedReceiptSha256 -cmatch '^[a-f0-9]{64}$' -and (File-Sha256 $ReopenedReceipt) -ceq $ExpectedReceiptSha256) 'EXACT_REOPENED_RECEIPT_HASH_REQUIRED'
  $r12Envelope = Read-PublicJson $ReopenedReceipt
  $r12Rows = if ($r12Envelope.PSObject.Properties.Name -contains 'public_receipts') { @($r12Envelope.public_receipts) } else { @($r12Envelope) }
  $r12Reopens = @($r12Rows | Where-Object { $_.ok -eq $true -and $_.phase -ceq 'r12_intake_reopened' })
  Require-R12 ($r12Reopens.Count -eq 1) 'EXACT_R12_REOPEN_RECEIPT_REQUIRED'
  $r12Authority = $r12Reopens[0]
  $r12Expected = @{
    host='100.116.112.22';service='codex-control-plane.service';admission='scoped_pilot';approval_id=$ApprovalId;
    binding_id='bind_3e05bf64cb3e4bab93d930ae1692bebb';device_id='72ceec2d-e3f2-472f-8e3c-99fffe053035';
    workspace_id='workspace_dda1d78e9a21402aa6213f72af64f788';workspace_generation='generation_c2f13e8d02344cf6a38a3f42ecfa59b6';
    root=$r12Root;profile='web-mcp-assistant';context_id='ctx_d7a539dd85264a62951fddad0ffa2f23';pilot_id='pilot_98c0b502568a4f888b3106838004c117';
    source_revision='9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c';duration_ms=3600000;
    prior_marker_sha256='e3d29f73b0395dd47ff46dd9bbb62831afce0a14183d23c2cd0ca88c5ceaf34c';prior_marker_unchanged=$true;
    service_restarted=$false;deployed=$false
  }
  foreach ($field in $r12Expected.Keys) { Require-R12 ($r12Authority.$field -ceq $r12Expected[$field]) 'R12_REOPEN_SCOPE_OR_IDENTITY_CHANGED' }
  Require-R12 ($r12Authority.next_marker_sha256 -cmatch '^[a-f0-9]{64}$') 'R12_REOPEN_MARKER_DIGEST_REQUIRED'
  Assert-RemainingWindow $r12Authority
  Assert-HelperPins
  Require-R12 (-not (Test-Path -LiteralPath $r12IntentPath) -and -not (Test-Path -LiteralPath $r12ResultPath)) 'ROOT_ONCE_INTENT_ALREADY_EXISTS_OBSERVE_DO_NOT_REPLAY'
  $r12Node = (Get-Command node.exe -CommandType Application).Source
  $r12Python = (Get-Command python.exe -CommandType Application).Source
  Write-ExclusiveJson $r12IntentPath ([ordered]@{kind='r12_root_once_intent';approval_id=$ApprovalId;reopened_receipt=[IO.Path]::GetFullPath($ReopenedReceipt);
    reopened_receipt_sha256=$ExpectedReceiptSha256;helper_manifest_sha256=$r12ManifestSha;requested_at_ms=[long]$r12Authority.requested_at_ms;
    expires_at_ms=[long]$r12Authority.expires_at_ms;created_at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();replay_forbidden=$true})
  $r12Started = $true
  $r12Stage = 'native_preflight'
  $r12Native = Invoke-OneJson $r12Node @((Join-Path $r12Here 'native-preflight.cjs')) $r12Stage
  Require-R12 ($r12Native.kind -ceq 'r12_query_only_native_preflight' -and $r12Native.authenticated_identity_observation -eq $true -and
    $r12Native.attestation_claimed -eq $false -and $r12Native.native_tool_contract_sha256 -ceq $r12NativeSha -and
    $r12Native.receipt_sha256 -cmatch '^[a-f0-9]{64}$' -and (File-Sha256 $r12Native.receipt_path) -ceq $r12Native.receipt_sha256) 'EXACT_AUTHENTICATED_R12_NATIVE_RECEIPT_REQUIRED'
  Require-R12 (([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() - [long]$r12Native.native_preflight.observed_at_ms) -ge 0 -and
    ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() - [long]$r12Native.native_preflight.observed_at_ms) -lt 60000) 'NATIVE_PREFLIGHT_STALE'
  $r12ProofPins = [ordered]@{}
  foreach ($field in @('observed_at_ms','source_head','preimage_sha256','checker_sha256','old_run_sha256','old_wave_sha256','no_active_jobs')) { $r12ProofPins[$field] = $r12Native.native_preflight.$field }
  $r12ProofPins['receipt_sha256'] = $r12Native.receipt_sha256
  $r12Pins = [ordered]@{}
  foreach ($field in @('requested_at_ms','expires_at_ms','context_id','pilot_id','service_instance_id','approval_id')) { $r12Pins[$field] = $r12Authority.$field }
  $r12Pins['authority_receipt_sha256'] = $ExpectedReceiptSha256
  $r12Pins['authority_marker_sha256'] = $r12Authority.next_marker_sha256
  foreach ($field in @('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version','native_tool_contract_sha256')) { $r12Pins[$field] = $r12Native.$field }
  $r12Pins['native_preflight'] = $r12ProofPins
  $r12PinsPath = Join-Path $r12Here 'root-canary-once.pins.json'
  Write-ExclusiveJson $r12PinsPath $r12Pins
  $r12PublicState['pins_path'] = $r12PinsPath
  $r12PublicState['native_receipt_path'] = $r12Native.receipt_path
  $r12PublicState['authority_receipt_path'] = [IO.Path]::GetFullPath($ReopenedReceipt)
  $r12Stage = 'prepare'
  $r12Prepared = Invoke-OneJson $r12Python @('-B',(Join-Path $r12Here 'root-canary-ssh.py'),'prepare','--pins',$r12PinsPath,
    '--native-preflight',[string]$r12Native.receipt_path,'--expected-native-preflight-sha256',[string]$r12Native.receipt_sha256,
    '--authority-receipt',[IO.Path]::GetFullPath($ReopenedReceipt),'--expected-authority-receipt-sha256',$ExpectedReceiptSha256) $r12Stage
  $r12PublicState['manifest_path'] = $r12Prepared.manifest_path
  foreach ($r12Phase in @('stage','preflight','dispatch')) {
    $r12Stage = $r12Phase
    $r12Returned = Invoke-OneJson $r12Python @('-B',(Join-Path $r12Here 'root-canary-ssh.py'),$r12Phase,'--manifest',[string]$r12Prepared.manifest_path,'--execute') $r12Phase
    if ($r12Returned.PSObject.Properties.Name -contains 'receipt_path') { $r12PublicState[($r12Phase + '_receipt_path')] = $r12Returned.receipt_path }
  }
  $r12PublicState['ok'] = $true
  $r12PublicState['last_phase'] = 'dispatch'
  $r12PublicState['next_action'] = 'OBSERVE_SAME_MANIFEST_THEN_CAPTURE_OUTPUT_WITHIN_300_SECONDS_OF_COMPLETION'
  Write-ExclusiveJson $r12ResultPath $r12PublicState
  $r12PublicState['result_path'] = $r12ResultPath
  $r12PublicState | ConvertTo-Json -Depth 12 -Compress | Write-Output
} catch {
  $r12Failure = [string]$_.Exception.Message
  if ($r12Failure -cnotmatch '^[A-Z0-9_]{8,128}$') { $r12Failure = 'ROOT_ONCE_DRIVER_REFUSED_RECONCILE_CURRENT_STAGE_NO_REPLAY' }
  $r12PublicState['code'] = $r12Failure
  $r12PublicState['last_phase'] = $r12Stage
  $r12PublicState['next_action'] = 'READ_ONLY_RECONCILE_INTENT_MANIFEST_AND_EXACT_CANARY_FAMILY_DO_NOT_RERUN_DRIVER'
  if ($r12Started -and -not (Test-Path -LiteralPath $r12ResultPath)) { Write-ExclusiveJson $r12ResultPath $r12PublicState }
  $r12PublicState | ConvertTo-Json -Depth 12 -Compress | Write-Output
  exit 2
}
