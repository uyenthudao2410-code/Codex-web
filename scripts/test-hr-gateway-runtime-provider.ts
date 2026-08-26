import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const providerPath = path.join(root, 'scripts', 'providers', 'hr-gateway-runtime-provider.ps1');
const runnerPath = path.join(root, 'scripts', 'providers', 'hr-gateway-task-runner.ps1');
const packagePath = path.join(root, 'package.json');
const provider = fs.readFileSync(providerPath, 'utf8');
const runner = fs.readFileSync(runnerPath, 'utf8');
const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8')) as { scripts: Record<string, string> };

function stripComments(source: string) {
  return source.split(/\r?\n/u).filter(line => !line.trim().startsWith('#')).join('\n');
}

for (const target of [providerPath, runnerPath]) {
  const escaped = target.replaceAll("'", "''");
  const syntax = spawnSync('powershell.exe', ['-NoProfile', '-Command', `$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile('${escaped}',[ref]$tokens,[ref]$errors) | Out-Null; if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }`], { cwd: root, encoding: 'utf8', timeout: 20_000 });
  assert.equal(syntax.status, 0, `PowerShell syntax failed for ${path.basename(target)}: ${syntax.stderr || syntax.stdout}`);
}

const providerCode = stripComments(provider);
const runnerCode = stripComments(runner);
for (const source of [providerCode, runnerCode]) {
  for (const forbidden of [/@sta\/finance/iu, /runtime:finance/iu, /dev:finance/iu, /finance:runtime/iu, /\b4000\b/u, /\b55432\b/u, /\b6379\b/u, /docker(?:\.exe)?/iu]) {
    assert.doesNotMatch(source, forbidden, `HR-only provider boundary violated by ${forbidden}`);
  }
}

assert.match(provider, /\$taskName = 'STA-HR-Gateway-Local'/u);
assert.match(provider, /\$gatewayPort = 3001/u);
assert.match(runner, /\$gatewayPort = 3001/u);
assert.match(provider, /New-ScheduledTaskPrincipal[\s\S]*?-LogonType Interactive[\s\S]*?-RunLevel Limited/u);
assert.match(provider, /New-ScheduledTaskSettingsSet[\s\S]*?-RestartCount 5[\s\S]*?-ExecutionTimeLimit \(\[TimeSpan\]::Zero\)/u);
assert.match(provider, /New-ScheduledTaskTrigger -AtLogOn -User \$currentUser/u);
assert.match(provider, /HR_GATEWAY_RUNTIME_TASK_NAME_COLLISION/u);
assert.match(provider, /HR_GATEWAY_PORT_IN_USE_UNOWNED/u);
assert.match(provider, /HR_GATEWAY_LISTENER_IDENTITY_CHANGED/u);
assert.match(provider, /HR_GATEWAY_MIXED_SUPERVISOR_ACTIVE/u);
assert.match(provider, /taskkill\.exe \/pid \(\[string\]\$current\.pid\) \/T \/F/u);

for (const source of [provider, runner]) {
  assert.match(source, /Get-HrGatewaySourceFingerprint/u);
  assert.match(source, /node_modules/u);
  assert.match(source, /certs/u);
  assert.match(source, /\.env/u);
  assert.match(source, /Get-FileHash[\s\S]*?-Algorithm SHA256/u);
}
assert.match(runner, /Test-GatewayHealth/u);
assert.match(runner, /healthStatus = 'ready'/u);
assert.match(runner, /sourceFingerprint = \$sourceFingerprint/u);
assert.match(runner, /gatewayCreationDate = \$creationDate/u);
assert.ok(runner.indexOf("healthStatus = 'ready'") > runner.indexOf('Test-GatewayHealth'), 'ready receipt must be written only after health proof');
assert.match(provider, /receiptSourceCurrent/u);
assert.match(provider, /receiptProcessCurrent/u);
assert.match(provider, /listenerMatchesReceipt/u);

for (const name of ['hr:gateway:runtime:status','hr:gateway:runtime:register','hr:gateway:runtime:ensure','hr:gateway:runtime:start','hr:gateway:runtime:stop','hr:gateway:runtime:unregister','test:hr-gateway-runtime-provider']) {
  assert.ok(packageJson.scripts[name], `${name} must be registered`);
}

const status = spawnSync('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', providerPath, '-Action', 'Status'], { cwd: root, encoding: 'utf8', timeout: 60_000 });
assert.equal(status.status, 0, `read-only HR Gateway provider Status failed: ${status.stderr || status.stdout}`);
const observed = JSON.parse(status.stdout.trim()) as Record<string, unknown>;
assert.equal(observed.event, 'hr.local.gateway-runtime-provider');
assert.equal(observed.action, 'status');
assert.equal(observed.taskName, 'STA-HR-Gateway-Local');
assert.equal(observed.port, 3001);
assert.equal(observed.hosting, 'WINDOWS_SCHEDULED_TASK');
assert.equal(observed.authority, 'LOCAL_ONLY');
assert.equal(observed.gatePromotion, false);
assert.equal(typeof observed.sourceFingerprint, 'string');
assert.equal((observed.sourceFingerprint as string).length, 64);

console.log(JSON.stringify({ event: 'hr.local.gateway-runtime-provider.source-proof', status: 'PASS', observed: { taskRegistered: observed.taskRegistered, portListening: observed.portListening, ready: observed.ready, receiptSourceCurrent: observed.receiptSourceCurrent }, assertions: { powershellSyntaxValid: true, hrOnlyPortAndTaskBoundary: true, noFinanceRuntimeMutationSurface: true, currentUserLimitedScheduledTask: true, boundedRestartPolicy: true, checkoutOwnedListenerTakeoverOnly: true, pidCreationIdentityRevalidated: true, currentSourceFingerprintReceipt: true, healthBeforeReadyReceipt: true, readOnlyStatusAvailable: true } }));
