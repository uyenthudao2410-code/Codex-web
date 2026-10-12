'use strict';
// Root preflight: one authenticated read-only identity call, no census/activation.
const fs = require('node:fs');
const path = require('node:path');
const {createRuntimePaths} = require('E:/Github/Tools-Codex-web/electron/services/runtimePaths');
const {RecoveryIpcClient} = require('E:/Github/Tools-Codex-web/electron/services/recoveryIpc');
const {descriptorRequestOptions, descriptorMatchesInstallation} = require('E:/Github/Tools-Codex-web/electron/services/recoveryHostLauncher');
const {observeLifecycleProcessIdentity, sameProcessIdentity} = require('E:/Github/Tools-Codex-web/electron/services/processIdentity');
const REPO = 'E:\\Github\\Tools-Codex-web';
const PROFILE = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const CANDIDATE = path.join(REPO, 'dist/windows-candidate-mxc-wsb-cbe1774-source-fingerprint-1012-r13/win-unpacked');
const EXPECTED = {
  activation_epoch_id: 'activation-mv4f0vbd-d6ff8f434f6de1929cedd4266c042dcd',
  process_instance_id: '6UTUCFZxzWswLzYo',
  server_instance_id: 'N-RYdpKzr66ftnM5',
  tool_contract_sha256: '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'
};
const need = (value, code) => {if (!value) throw Object.assign(new Error(), {code});};
async function main() {
  const paths = createRuntimePaths({dataRoot: PROFILE, appRoot: path.join(CANDIDATE, 'resources/app.asar'),
    resourcesRoot: path.join(CANDIDATE, 'resources/resources'), runtimeMode: 'packaged',
    executablePath: path.join(CANDIDATE, 'Coding Tools MCP.exe')});
  const descriptor = JSON.parse(fs.readFileSync(paths.recoveryHostDescriptorFile(), 'utf8'));
  need(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'EXACT_R13_INSTALLATION_REQUIRED');
  need(descriptor.owner_pid === 11476 && String(descriptor.owner_process_start_token) === '134362325643887110', 'EXACT_ROOT_OBSERVED_HOST_REQUIRED');
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  need(owner.state === 'live' && sameProcessIdentity({pid: descriptor.owner_pid,
    process_start_token: descriptor.owner_process_start_token}, owner), 'EXACT_HOST_PROCESS_NOT_LIVE');
  const client = new RecoveryIpcClient({paths});
  const identity = await client.call('runtime.identity_observation', [], descriptorRequestOptions(descriptor));
  need(identity.observation_schema_version === 1 && identity.observation_kind === 'mcp_identity_read_only'
    && identity.mcp_ready === true && identity.identity_current === true
    && identity.activation_epoch_id === identity.current_activation_epoch_id, 'CURRENT_READY_IDENTITY_REQUIRED');
  need(identity.activation_epoch_id === EXPECTED.activation_epoch_id
    && identity.mcp_process_instance_id === EXPECTED.process_instance_id
    && identity.mcp_server_instance_id === EXPECTED.server_instance_id
    && identity.tool_contract_sha256 === EXPECTED.tool_contract_sha256, 'EXACT_CAPTURED_NATIVE_IDENTITY_REQUIRED');
  const ownerAfter = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  need(ownerAfter.state === 'live' && sameProcessIdentity({pid: descriptor.owner_pid,
    process_start_token: descriptor.owner_process_start_token}, ownerAfter), 'HOST_CHANGED_DURING_IDENTITY_READ');
  return {ok: true, kind: 'r13_5h_root_current_native_identity_read_only', observed_at_ms: Date.now(),
    native_identity: EXPECTED, current_identity: true, mcp_ready: true,
    host_owner_pid: descriptor.owner_pid, host_process_verified: true,
    authenticated_read_only: true, activation_performed: false, acceptance_performed: false,
    mutated_canonical_ledger: false, secret_values_emitted: false};
}
if (require.main === module) main().then(value => process.stdout.write(JSON.stringify(value)+'\n')).catch(error => {
  const code = /^[A-Z0-9_]{1,128}$/.test(error.code || '') ? error.code : 'SAFE_READ_ONLY_NATIVE_IDENTITY_FAILED';
  process.stdout.write(JSON.stringify({ok: false, code, activation_performed: false,
    mutated_canonical_ledger: false, secret_values_emitted: false})+'\n');
  process.exitCode = 2;
});
