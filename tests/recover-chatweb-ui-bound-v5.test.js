const test = require('node:test');
const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const wrapperPath = path.join(__dirname, '..', 'recover_chatweb_ui_bound_v5.cmd');

function source() {
  return fs.readFileSync(wrapperPath, 'utf8');
}

function powershellFunction(text, name, nextName) {
  const start = text.indexOf(`function ${name} {`);
  const end = text.indexOf(`function ${nextName} {`, start);
  assert.ok(start >= 0 && end > start, `${name} must be present and bounded`);
  return text.slice(start, end);
}

function runPowerShell(sourceText) {
  const encoded = Buffer.from(sourceText, 'utf16le').toString('base64');
  return childProcess.spawnSync('powershell.exe', [
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy', 'Bypass',
    '-EncodedCommand', encoded
  ], { encoding: 'utf8' });
}

test('V5 keeps workspace authority in the UI profile and rejects cwd-dependent paths', () => {
  const text = source();
  assert.match(text, /\$uiWorkspaceRaw = \[string\]\$settings\.workspace/);
  assert.ok(text.includes("$driveQualified = $expanded -match '^[A-Za-z]:[\\\\/]'"));
  assert.ok(text.includes("$uncQualified = $expanded -match '^[\\\\/]{2}"));
  assert.match(text, /if \(-not \(\$driveQualified -or \$uncQualified\)\) \{ return '' \}/);
  assert.doesNotMatch(text, /E:\\DEV\\Codex-web/i);
});

test('V5 loads the wrapper current checkout through the official lifecycle', () => {
  const text = source();
  assert.match(text, /Split-Path -Parent \$WrapperPath/);
  assert.match(text, /scripts\\dev-ui-lifecycle\.js/);
  assert.match(text, /\$output = @\(& \$node \$lifecycle 'refresh'/);
  assert.match(text, /Push-Location -LiteralPath \$checkout/);
  assert.match(text, /Pop-Location/);
  assert.match(text, /Invoke-CurrentCheckoutRefresh \$env:RECOVERY_SELF \$uiWorkspaceRaw/);
  const lifecycleCall = text.indexOf('Invoke-CurrentCheckoutRefresh $env:RECOVERY_SELF $uiWorkspaceRaw');
  const staleHostCall = text.indexOf("Invoke-RecoveryAction $descriptor 'runtime.activation_epoch_status'");
  assert.ok(lifecycleCall >= 0 && staleHostCall > lifecycleCall,
    'the current-checkout lifecycle must run before post-refresh host polling');
  assert.doesNotMatch(text, /Read-JsonFile \$descriptorPath/);
  assert.doesNotMatch(text, /Invoke-RecoveryAction \$descriptor 'runtime\.restart'/);
  assert.doesNotMatch(text, /FULL_CLEAN_REFRESH_HANDOFF_OBSERVED/);
});

test('V5 preserves structured HTTP errors before transport fallback', () => {
  const text = source();
  const detailsIndex = text.indexOf('$ErrorRecord.ErrorDetails.Message');
  const streamIndex = text.indexOf('$response.GetResponseStream()');
  assert.ok(detailsIndex >= 0, 'ErrorDetails.Message must be inspected');
  assert.ok(streamIndex > detailsIndex, 'the response stream is only a fallback after ErrorDetails.Message');
  assert.match(text, /Read-HttpErrorBody \$_/);
});

test('V5 can classify a projection record from its nested durable epoch state', () => {
  const text = source();
  assert.match(text, /\$Epoch\.verification\.runtime\.activationEpoch\.epoch_state/);
  assert.match(text, /\$knownDurable -contains \$projected/);
  assert.match(text, /\$projected -eq 'UPDATE_INCOMPLETE'/);
  assert.match(text, /\$knownDurable -contains \$durable/);
  assert.match(text, /if \(\$projected -eq 'UPDATE_INCOMPLETE'\) \{ return '' \}/);
});

test('V5 PowerShell durable-state classifier preserves terminal authority and rejects contradictions', {
  skip: process.platform !== 'win32' ? 'Windows PowerShell regression' : false
}, () => {
  const text = source();
  const classifier = powershellFunction(text, 'Get-EpochDurableState', 'Normalize-Workspace');
  const script = `
function Fail-Recovery {
  param([string]$Code, [string]$Message)
  throw [System.InvalidOperationException]::new("$Code|$Message")
}
${classifier}
$cases = @(
  [pscustomobject]@{ state = 'FAILED'; epoch_state = 'VERIFYING'; verification = [pscustomobject]@{ runtime = [pscustomobject]@{ activationEpoch = [pscustomobject]@{ epoch_state = 'READY' } } } },
  [pscustomobject]@{ state = 'READY'; epoch_state = 'FAILED'; verification = [pscustomobject]@{ runtime = [pscustomobject]@{ activationEpoch = [pscustomobject]@{ epoch_state = 'VERIFYING' } } } },
  [pscustomobject]@{ state = 'UPDATE_INCOMPLETE'; epoch_state = 'STOPPING' },
  [pscustomobject]@{ state = 'UPDATE_INCOMPLETE'; verification = [pscustomobject]@{ runtime = [pscustomobject]@{ activationEpoch = [pscustomobject]@{ epoch_state = 'HANDOFF' } } } }
)
$values = @($cases | ForEach-Object { Get-EpochDurableState $_ })
$contradiction = ''
try {
  [void](Get-EpochDurableState ([pscustomobject]@{ state = 'VERIFYING'; epoch_state = 'FAILED' }))
} catch {
  $contradiction = [string]$_.Exception.Message
}
$unknown = ''
try {
  [void](Get-EpochDurableState ([pscustomobject]@{ state = 'UPDATE_INCOMPLETE'; epoch_state = 'UNKNOWN_FROM_HOST' }))
} catch {
  $unknown = [string]$_.Exception.Message
}
[pscustomobject]@{ values = $values; contradiction = $contradiction; unknown = $unknown } | ConvertTo-Json -Compress
`;
  const result = runPowerShell(script);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const parsed = JSON.parse(result.stdout.trim());
  assert.deepEqual(parsed.values, ['FAILED', 'READY', 'STOPPING', 'HANDOFF']);
  assert.match(parsed.contradiction, /^ACTIVATION_EPOCH_STATE_CONTRADICTORY\|/);
  assert.match(parsed.unknown, /^ACTIVATION_EPOCH_STATE_INVALID\|/);
});

test('V5 verifies the Recovery Host installation and exact OS process-start identity', () => {
  const text = source();
  assert.match(text, /function Get-ExpectedInstallationIdentity/);
  assert.match(text, /createDevelopmentPaths\(\{appRoot:process\.cwd\(\)\}\)/);
  assert.match(text, /function Get-ProcessStartToken/);
  assert.match(text, /StartTime\.ToUniversalTime\(\)\.ToFileTimeUtc\(\)/);
  assert.match(text, /creation = \$creation - \(\$creation % 10\)/);
  assert.match(text, /Normalize-ProcessStartToken \$value\.owner_process_start_token/);
  assert.match(text, /\$observedToken -ne \$descriptorToken/);
  assert.match(text, /Assert-DescriptorExpectedInstallation \$descriptor \$expectedInstallation/);
});

test('V5 pins and rereads the descriptor before every authenticated IPC action', () => {
  const text = source();
  assert.match(text, /function Assert-DescriptorPinned/);
  assert.match(text, /owner_process_start_token/);
  assert.match(text, /installation_id/);
  assert.match(text, /function Read-PinnedDescriptor/);
  assert.match(text, /RECOVERY_DESCRIPTOR_UNPINNED/);
  assert.match(text, /Read-PinnedDescriptor \$DescriptorPath \$PinnedDescriptor \$ExpectedEpochId/);
  assert.match(text, /\$pinnedDescriptor = \$descriptor/);
  assert.match(text, /\$descriptorPath \$expectedEpochId/);
  assert.match(text, /RECOVERY_DESCRIPTOR_CHANGED/);
});

test('V5 fails closed when the pinned descriptor endpoint or bearer drifts', () => {
  const text = source();
  const start = text.indexOf('function Assert-DescriptorPinned');
  const end = text.indexOf('function Read-PinnedDescriptor', start);
  assert.ok(start >= 0 && end > start, 'descriptor pin function must be present and bounded');
  const body = text.slice(start, end);
  assert.match(body, /\$portMatches = \(\[int\]\$Observed\.port -eq \[int\]\$Pinned\.port\)/);
  assert.match(body, /\$tokenMatches = \[String\]::Equals\(/);
  assert.match(body, /\[string\]\$Observed\.token/);
  assert.match(body, /\[string\]\$Pinned\.token/);
  assert.match(body, /\[StringComparison\]::Ordinal/);
  assert.match(body, /-and \$portMatches/);
  assert.match(body, /-and \$tokenMatches/);
  assert.doesNotMatch(body, /Observed\.token.*(?:Write|message|details)/is,
    'bearer values must never be copied into diagnostics');
  assert.doesNotMatch(body, /Pinned\.token.*(?:Write|message|details)/is,
    'pinned bearer values must never be copied into diagnostics');
});

test('V5 leaves connector acknowledgement/finalization to the exact coordinator and only polls receipts', () => {
  const text = source();
  assert.doesNotMatch(text, /'runtime\.acknowledge_connector_contract'/);
  assert.doesNotMatch(text, /CURRENT_CONNECTOR_ACK_PASS/);
  assert.match(text, /function Test-EpochSnapshotBinding/);
  assert.match(text, /operation_id/);
  assert.match(text, /function Test-ConnectorReadySnapshot/);
  assert.match(text, /CURRENT_ACKNOWLEDGED/);
  assert.match(text, /CURRENT_COMPATIBLE_ACKNOWLEDGED/);
  assert.match(text, /connectorRediscovered -eq \$true/);
  assert.match(text, /connectorCompatibilityAcknowledged -eq \$true/);
  assert.match(text, /connectorFreshnessMode -eq 'compatible_activation_bootstrap'/);
  assert.match(text, /connectorRefreshRequired -ne \$false/);
  assert.match(text, /connectorAcknowledgementPending -ne \$false/);
  assert.match(text, /Test-EpochSnapshotBinding \$lastSnapshot \$lastEpoch/);
  assert.match(text, /CURRENT_CONNECTOR_READY_OBSERVED/);
  const epochPoll = text.indexOf("'runtime.activation_epoch_status'");
  const snapshotPoll = text.indexOf("'runtime.lightweight_snapshot'");
  assert.ok(epochPoll >= 0 && snapshotPoll > epochPoll,
    'the wrapper must observe coordinator epoch and runtime receipts without mutating connector acknowledgement');
});

test('V5 refuses to adopt an active non-refresh durable epoch', () => {
  const text = source();
  assert.match(text, /function Test-RefreshEpochRecord/);
  assert.match(text, /ACTIVATION_EPOCH_CONFLICT/);
  assert.match(text, /Test-RefreshEpochRecord \$beforeEpoch/);
  assert.match(text, /request_intent/);
  assert.match(text, /intent\.metadata\.refresh/);
  assert.match(text, /metadata\.refresh/);
  assert.match(text, /source_checkpoint/);
});
