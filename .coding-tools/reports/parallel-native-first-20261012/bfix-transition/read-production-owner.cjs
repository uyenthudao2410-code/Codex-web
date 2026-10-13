'use strict';
process.stdout.write('OWNER_READ_START\n');
process.on('uncaughtException', error => { process.stderr.write(`OWNER_READ_UNCAUGHT ${error?.stack || error}\n`); process.exitCode = 1; });
process.on('unhandledRejection', error => { process.stderr.write(`OWNER_READ_REJECTION ${error?.stack || error}\n`); process.exitCode = 1; });
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../../../..');
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources/app.asar');
const load = name => require(path.join(appRoot, 'electron/services', name));
const { RuntimePaths } = load('runtimePaths');
const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
const { processIdentityFrom, observeLifecycleProcessIdentity, sameProcessIdentity } = load('processIdentity');
const { canonicalLedgerCensus } = load('fullCleanActivation');

const paths = new RuntimePaths({
  dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'),
  appRoot,
  resourcesRoot: path.join(candidate, 'resources/resources'),
  executablePath: executable,
  runtimeMode: 'packaged'
});
const client = new RecoveryIpcClient({ paths });
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const safe = value => ({
  fullyReady: value?.fullyReady,
  mcpRunning: value?.mcpRunning,
  nativeAlive: value?.nativeAlive,
  centralConnected: value?.centralConnected,
  authorityReady: value?.authorityReady,
  componentsReady: value?.componentsReady,
  updateIncomplete: value?.updateIncomplete,
  executionRole: value?.executionRole,
  activationEpochId: value?.activationEpochId,
  activationState: value?.activationState,
  connectorContractState: value?.connectorContractState,
  workspace: value?.workspace,
  deviceId: value?.deviceId
});

async function main() {
  const descriptor = loadRecoveryDescriptor(paths);
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  if (!verified || !descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity())) throw new Error('SELECTED_PACKAGED_HOST_NOT_VERIFIED');
  const requestOptions = descriptorRequestOptions(verified.descriptor);
  const ping = await client.call('recovery.ping', [], requestOptions);
  const runtime = await client.call('runtime.lightweight_snapshot', [], requestOptions);
  const activation = await client.call('runtime.activation_epoch_status', [], requestOptions);
  const status = await client.call('recovery.status', [{ fresh: true }], requestOptions);
  const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  const owner = processIdentityFrom(verified.descriptor);
  const observedOwner = await observeLifecycleProcessIdentity(owner.pid);
  const manifestPath = path.join(paths.dataRoot(), 'recovery-supervisor/manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  process.stdout.write(JSON.stringify({
    ok: true,
    observed_at: new Date().toISOString(),
    candidate,
    candidate_hashes: { executable: digest(executable), app_asar: digest(appRoot) },
    descriptor: {
      owner_pid: verified.descriptor.owner_pid,
      owner_process_start_token: verified.descriptor.owner_process_start_token,
      instance_id: verified.descriptor.instance_id,
      installation_id: verified.descriptor.installation_id,
      runtime_mode: verified.descriptor.runtime_mode,
      app_root: verified.descriptor.app_root,
      ready: verified.descriptor.ready
    },
    process_identity: { state: observedOwner.state, same: sameProcessIdentity(owner, observedOwner) },
    ping: { ok: ping?.ok === true, ready: ping?.data?.ready === true },
    runtime: safe(runtime),
    activation: {
      activation_epoch_id: activation?.activation_epoch_id,
      state: activation?.state,
      admission_open: activation?.admission_open,
      update_incomplete: activation?.update_incomplete
    },
    recovery_status: {
      ui_alive: status?.electron_ui_recovery?.alive,
      ui_suppressed: status?.electron_ui_recovery?.suppressed,
      runtime_mode: status?.runtime_mode
    },
    census: {
      safe: census?.safe,
      blockers: census?.lifecycle?.blockers || [],
      unexplained_active_runs: census?.lifecycle?.unexplained_active_runs,
      unbound_live_resource_residues: census?.lifecycle?.unbound_live_resource_residues,
      counts: census?.counts || {}
    },
    supervisor_manifest: {
      mode: manifest.mode,
      app_root: manifest.app_root,
      executable: manifest.executable,
      sha256: digest(manifestPath)
    }
  }, null, 2) + '\n');
}

main().catch(error => {
  process.stdout.write(JSON.stringify({ ok: false, code: error?.code || 'OWNER_READ_FAILED', message: String(error?.message || error) }) + '\n');
  process.exitCode = 1;
});
