'use strict';
// Read-only content-free observation. No heartbeat, sync, restart, policy or VM probe.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../../../../../..');
const services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked');
const paths = createRuntimePaths({ dataRoot: 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant', appRoot: path.join(candidate, 'resources/app.asar'), resourcesRoot: path.join(candidate, 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(candidate, 'Coding Tools MCP.exe') });
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const select = (row, fields) => Object.fromEntries(fields.map(field => [field, row?.[field] ?? null]));
function read(file) { const bytes = fs.readFileSync(file); if (bytes.length > 1024 * 1024) throw Object.assign(new Error(), { code: 'INPUT_LIMIT' }); return JSON.parse(bytes.toString('utf8')); }
async function main() {
  if (sha(fs.readFileSync(path.join(candidate, 'resources/app.asar'))) !== '3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226') throw Object.assign(new Error(), { code: 'R9_PACKAGE_CHANGED' });
  const descriptor = loadRecoveryDescriptor(paths); if (!descriptorMatchesInstallation(descriptor, paths.runtimeIdentity())) throw Object.assign(new Error(), { code: 'DESCRIPTOR_CHANGED' });
  const client = new RecoveryIpcClient({ paths }), options = descriptorRequestOptions(descriptor);
  const status = await client.status({ ...options, fresh: true });
  const projection = await client.call('runtime.lightweight_snapshot', [], options);
  const rawEpoch = await client.call('runtime.activation_epoch_status', [], options);
  const epoch = read(paths.activationEpochFile()).current, policy = read(paths.controlPlaneReadOnlyPolicyFile()), route = read(paths.controlPlaneRouteEvidenceFile());
  const revision = r => select(r, ['state', 'running_revision', 'disk_revision', 'pending_revision', 'update_pending', 'updatePending']);
  const report = { kind: 'read_only_r9_authority_gap_observation', observed_at: new Date().toISOString(), helper_sha256: sha(fs.readFileSync(__filename)),
    descriptor: select(descriptor, ['installation_id', 'instance_id', 'owner_pid', 'owner_process_start_token']),
    durable: select(epoch, ['activation_epoch_id', 'operation_id', 'state', 'admission_state', 'ready_commit_digest', 'ready_at_unix_ms', 'expires_at_unix_ms']),
    durable_error_code: epoch?.error?.code || null,
    raw_epoch: select(rawEpoch, ['activation_epoch_id', 'operation_id', 'state', 'admission_open', 'update_incomplete', 'ready_commit_digest', 'error_code']),
    projection: select(projection, ['executionRole', 'fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'centralStatusReason', 'updateIncomplete', 'failureKind']),
    projected_epoch: select(projection.activationEpoch, ['activation_epoch_id', 'operation_id', 'state', 'admission_open', 'update_incomplete', 'error_code']),
    host_runtime: select(status.runtime, ['execution_role', 'central_connected', 'authority_ready', 'central_status_reason', 'fully_ready', 'update_incomplete', 'recovering']),
    full_clean: select(status.full_clean_activation, ['available', 'state', 'running_revision', 'disk_revision', 'activation_epoch_id']),
    ready_adoption: select(status.ready_adoption, ['state', 'code']), bootstrap: select(status.recovery_bootstrap, ['state', 'operation_id', 'error_code']),
    code_revision: revision(status.code_revision), ui_revision: revision(status.electron_ui_revision), native_revision: revision(projection.codeRevision?.codingMcp),
    metadata_policy: select(policy, ['enabled', 'expires_at_ms', 'context_id', 'device_id', 'workspace_id', 'workspace_generation']),
    route: select(route, ['device_id', 'endpoint_id', 'observed_at_ms', 'runtime_readiness', 'policy_state', 'policy_expires_at_ms', 'policy_sha256']),
    runtime_mutated: false, authority_mutated: false, sandbox_probe_performed: false };
  const file = path.join(__dirname, `r9-authority-gap-${report.observed_at.replace(/[^0-9TZ]/g, '')}.json`); fs.writeFileSync(file, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ file, sha256: sha(fs.readFileSync(file)), ...report }) + '\n');
}
main().catch(error => { process.stdout.write(JSON.stringify({ ok: false, code: String(error.code || 'READ_OBSERVATION_FAILED').replace(/[^A-Z0-9_]/g, '').slice(0, 96) }) + '\n'); process.exitCode = 1; });
