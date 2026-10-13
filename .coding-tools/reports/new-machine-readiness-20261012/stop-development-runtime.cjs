'use strict';

// One operator transition for this machine. It does not create source
// acceptance, change workspace authority, or delete any durable state.
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const root = 'E:\\DEV\\Codex-web';
const reportRoot = __dirname;
const { createDevelopmentPaths, createRuntimeDependencies } = require(path.join(root, 'scripts/dev-ui-lifecycle'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(root, 'electron/services/recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost,
  suppressDevelopmentRecoverySupervisor } = require(path.join(root, 'electron/services/recoveryHostLauncher'));
const { canonicalLedgerCensus } = require(path.join(root, 'electron/services/fullCleanActivation'));
const { sameAbsolutePath } = require(path.join(root, 'electron/services/pathSemantics'));
const { observeLifecycleProcessIdentity, processIdentityFrom, sameProcessIdentity,
  terminateExactProcessTree, waitForExactProcessExit } = require(path.join(root, 'electron/services/processIdentity'));

function requireState(condition, code) {
  if (!condition) throw Object.assign(new Error(code), { code });
}

function exactDevelopmentSupervisorManifest(paths) {
  const current = path.join(paths.dataRoot(), 'recovery-supervisor', 'manifest.json');
  const localAppData = String(process.env.LOCALAPPDATA || '').trim();
  requireState(path.isAbsolute(localAppData), 'LOCAL_APP_DATA_UNAVAILABLE');
  const legacy = path.join(localAppData, 'WebMcpRecoverySupervisor', 'manifest.json');
  for (const manifestFile of [current, legacy]) {
    let stat;
    try { stat = fs.statSync(manifestFile); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    requireState(stat.isFile() && stat.size <= 65536, 'SUPERVISOR_MANIFEST_INVALID');
    const contents = fs.readFileSync(manifestFile, 'utf8');
    const manifest = JSON.parse(contents);
    requireState(manifest.schema_version === 1 && manifest.mode === 'development'
      && sameAbsolutePath(fs.realpathSync(manifest.app_root), fs.realpathSync(paths.appRoot()))
      && sameAbsolutePath(fs.realpathSync(manifest.executable), fs.realpathSync(paths.executablePath())),
    'SUPERVISOR_BELONGS_TO_ANOTHER_INSTALLATION');
    return { manifestFile, contents };
  }
  return null;
}

function requireSameHost(observation, descriptor, identity) {
  requireState(observation?.hostAvailable === true && observation.installationMatches === true
    && observation.descriptor.owner_pid === descriptor.owner_pid
    && observation.descriptor.instance_id === descriptor.instance_id
    && observation.descriptor.installation_id === descriptor.installation_id
    && sameProcessIdentity(identity, processIdentityFrom(observation.descriptor)), 'RECOVERY_OWNER_CHANGED');
}

async function main() {
  requireState(process.argv[2] === '--execute', 'EXPLICIT_OPERATOR_EXECUTION_REQUIRED');
  const candidate = fs.realpathSync(path.resolve(process.argv[3] || ''));
  requireState(candidate.toLowerCase().startsWith(path.join(root, 'dist').toLowerCase() + path.sep), 'CANDIDATE_OUTSIDE_WORKSPACE_DIST');
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  const appRoot = path.join(candidate, 'resources', 'app.asar');
  requireState(fs.statSync(executable).isFile() && fs.statSync(appRoot).isFile(), 'CANDIDATE_NOT_BUILT');
  requireState(execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', windowsHide: true }).trim()
    === '7999c4151cb501db86f2e4d0a2275d33fc248324', 'EXPECTED_GIT_HEAD_CHANGED');
  const paths = createDevelopmentPaths({ appRoot: root });
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'CURRENT_DEVELOPMENT_HOST_NOT_VERIFIED');
  const descriptor = verified.descriptor;
  const identity = processIdentityFrom(await observeLifecycleProcessIdentity(descriptor.owner_pid));
  requireState(sameProcessIdentity(processIdentityFrom(descriptor), identity), 'HOST_PROCESS_IDENTITY_CHANGED');
  const before = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  fs.writeFileSync(path.join(reportRoot, 'census-before-operator-stop.json'), JSON.stringify(before, null, 2));
  const workCounts = ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
    'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'];
  requireState(workCounts.every(key => before.counts[key] === 0), 'ACTIVE_WORK_PREVENTS_OPERATOR_STOP');
  requireState(Array.isArray(before.lifecycle?.blockers)
    && before.lifecycle.blockers.every(blocker => blocker === 'live_runtime_state_process')
    && (before.safe === true || before.reason === 'live_runtime_state_process'), 'CANONICAL_CENSUS_HAS_ANOTHER_BLOCKER');
  requireState(before.lifecycle.unexplained_active_runs === 0 && before.lifecycle.unbound_live_resource_residues === 0,
    'UNEXPLAINED_LIFECYCLE_PREVENTS_OPERATOR_STOP');
  const supervisorManifest = exactDevelopmentSupervisorManifest(paths);
  const guardedFs = Object.create(fs);
  guardedFs.readFileSync = (file, options) => {
    const contents = fs.readFileSync(file, options);
    requireState(supervisorManifest && sameAbsolutePath(file, supervisorManifest.manifestFile)
      && contents === supervisorManifest.contents, 'SUPERVISOR_MANIFEST_CHANGED');
    return contents;
  };
  const supervisor = suppressDevelopmentRecoverySupervisor({
    expectedAppRoot: appRoot, expectedExecutable: executable, fsApi: guardedFs
  });
  requireState(supervisorManifest ? supervisor.suppressed === true : supervisor.reason === 'manifest_unavailable',
    'DEVELOPMENT_SUPERVISOR_NOT_SUPPRESSED');
  const uiDependencies = createRuntimeDependencies({ paths });
  const ui = await uiDependencies.inspect();
  requireSameHost(ui, descriptor, identity);
  requireState(sameProcessIdentity(identity, await observeLifecycleProcessIdentity(identity.pid)), 'RECOVERY_OS_IDENTITY_CHANGED');
  if (ui.ui.state === 'MISSING') {
    requireState(ui.status.electron_ui_recovery.alive === false, 'UI_PROCESS_STATE_UNCERTAIN');
  } else {
    requireState(['CURRENT', 'STALE'].includes(ui.ui.state) && ui.ui.runtimeMode === 'development'
      && ui.ui.installationId === paths.runtimeIdentity().installation_id && ui.ui.instanceId && ui.ui.pid,
    'UI_INSTALLATION_UNVERIFIED');
    const uiIdentity = processIdentityFrom(await observeLifecycleProcessIdentity(ui.ui.pid));
    await uiDependencies.suppress(ui);
    const currentUi = await uiDependencies.inspect();
    requireSameHost(currentUi, descriptor, identity);
    requireState(currentUi.ui.instanceId === ui.ui.instanceId && currentUi.ui.pid === ui.ui.pid
      && currentUi.ui.runtimeMode === 'development' && currentUi.ui.installationId === ui.ui.installationId
      && sameProcessIdentity(uiIdentity, await observeLifecycleProcessIdentity(uiIdentity.pid)), 'UI_PROCESS_IDENTITY_CHANGED');
    await uiDependencies.signal('stop', ui.ui.instanceId);
    await waitForExactProcessExit(uiIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 20000 });
  }
  await client.stop({ manual: true }, descriptorRequestOptions(descriptor));
  const stopped = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  fs.writeFileSync(path.join(reportRoot, 'census-after-supervised-stop.json'), JSON.stringify(stopped, null, 2));
  requireState(stopped.safe === true, 'STOPPED_CANONICAL_CENSUS_NOT_QUIESCENT');
  const current = loadRecoveryDescriptor(paths);
  requireState(current.owner_pid === descriptor.owner_pid && current.instance_id === descriptor.instance_id
    && current.installation_id === descriptor.installation_id, 'RECOVERY_OWNER_CHANGED');
  requireState(sameProcessIdentity(identity, await observeLifecycleProcessIdentity(identity.pid)), 'RECOVERY_OS_IDENTITY_CHANGED');
  const retirement = await terminateExactProcessTree(identity, {
    observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 20000
  });
  await waitForExactProcessExit(identity, { observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 20000 });
  const receipt = { operation: 'operator_stop_development_for_packaged_installation', observed_at: new Date().toISOString(),
    old_host_pid: identity.pid, old_host_instance_id: descriptor.instance_id, old_installation_id: descriptor.installation_id,
    candidate, supervisor, retirement, canonical_safe_after_primary_stop: stopped.safe,
    accepting_history_preserved: true, source_acceptance_created: false, durable_state_deleted: false };
  fs.writeFileSync(path.join(reportRoot, 'development-retirement-receipt.json'), JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt));
}

main().catch(error => {
  console.error(JSON.stringify({ ok: false, code: error.code || error.name, operation: 'operator_stop_development_for_packaged_installation' }));
  process.exitCode = 1;
});
