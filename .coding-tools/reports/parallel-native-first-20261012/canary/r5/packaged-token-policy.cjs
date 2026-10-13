'use strict';

// Packaged operator for the one token probe. It changes only the Codex-web
// scoped native prefix, records an intent before the write, and restores the
// exact native_first baseline after the probe.
const fs = require('node:fs');
const originalFs = require('original-fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = 'E:\\DEV\\Codex-web';
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked');
const reportRoot = path.join(root, '.coding-tools/reports/parallel-native-first-20261012/canary/r5');
const parityPath = path.join(root, '.coding-tools/reports/native-first-20261012/parallel-r4-timefix-parity.json');
const smokePath = path.join(root, '.coding-tools/reports/native-first-20261012/parallel-r4-timefix-smoke-full.json');
const mode = process.argv[2];
const option = name => { const i = process.argv.indexOf(name); return i < 0 ? undefined : process.argv[i + 1]; };
const fail = code => { throw Object.assign(new Error(code), { code }); };
const requireState = (value, code) => { if (!value) fail(code); };
const sha = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
const read = file => { requireState(path.isAbsolute(file) && fs.statSync(file).isFile(), 'RECEIPT_REQUIRED'); return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); };
const canonical = value => Array.isArray(value) ? `[${value.map(canonical).join(',')}]`
  : value && typeof value === 'object' ? `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}` : JSON.stringify(value);
const scopeSha = value => crypto.createHash('sha256').update(canonical(value)).digest('hex');
const target = { workspaceId: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94', workspaceGeneration: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' };
const other = { workspaceId: 'workspace_bc86004be2684b958ab7a9a6f9530cd7', workspaceGeneration: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a' };
const tokenPrefix = ['node', '.coding-tools/reports/parallel-native-first-20261012/canary/r5/token-child-launcher.js'];
const report = (operation, value, file) => {
  const output = file || path.join(reportRoot, `packaged-token-${operation}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}.json`);
  requireState(path.resolve(output).toLowerCase().startsWith(reportRoot.toLowerCase() + path.sep), 'REPORT_PATH_INVALID');
  const record = { schema_version: 1, operation, observed_at_ms: Date.now(), candidate, ok: true, ...value, report_path: output };
  fs.writeFileSync(output, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
  return record;
};

async function main() {
  requireState(['install', 'restore'].includes(mode), 'TOKEN_POLICY_MODE_INVALID');
  const parity = read(parityPath), smoke = read(smokePath);
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  const archive = path.join(candidate, 'resources/app.asar');
  requireState(parity.ok === true && parity.candidate.toLowerCase() === candidate.toLowerCase()
    && sha(executable) === parity.executable_sha256 && sha(archive) === parity.app_asar_sha256
    && smoke.ok === true && smoke.candidate.toLowerCase() === candidate.toLowerCase()
    && smoke.sha256.source_package_parity_receipt === sha(parityPath)
    && smoke.sha256.executable === parity.executable_sha256 && smoke.sha256.app_asar === parity.app_asar_sha256
    && smoke.production_descriptor_stable === true, 'EXACT_SOURCE_PACKAGE_AND_SMOKE_REQUIRED');
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(), 'SELECTED_PACKAGED_ELECTRON_REQUIRED');
  const verifier = require(path.join(root, 'scripts/verify-packaged-resources'));
  verifier.assertExactPackagedResources(path.join(root, 'resources'), path.join(candidate, 'resources/resources'), { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
  verifier.assertExactControlPlaneAdapter(path.join(root, 'control-plane/control_plane'), path.join(candidate, 'resources/resources/control-plane'));
  const load = name => require(path.join(archive, 'electron/services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
  const { canonicalLedgerCensus } = load('fullCleanActivation');
  const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot: archive,
    resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2);
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'EXACT_READY_HOST_REQUIRED');
  const expected = descriptorRequestOptions(verified.descriptor);
  const epoch = await client.call('runtime.activation_epoch_status', [], expected);
  requireState(epoch.state === 'READY' && epoch.admission_open === true, 'READY_OPEN_EPOCH_REQUIRED');
  const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  requireState(census.lifecycle?.unexplained_active_runs === 0 && census.lifecycle?.unbound_live_resource_residues === 0
    && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'].every(key => census.counts[key] === 0), 'ACTIVE_LOCAL_WORK_PREVENTS_POLICY_CHANGE');
  const enrollment = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
  const before = await enrollment.inspectLocalExecPolicy(target);
  const otherBefore = await enrollment.inspectLocalExecPolicy(other);
  requireState(before.state === 'enabled' && before.execution_mode === 'native_first' && Array.isArray(before.native_argv_prefixes), 'CODEX_NATIVE_FIRST_BASELINE_REQUIRED');
  requireState(otherBefore.state === 'enabled' && otherBefore.execution_mode === 'native_first' && Array.isArray(otherBefore.native_argv_prefixes), 'AUTOCAD_NATIVE_FIRST_BASELINE_REQUIRED');
  const storeFile = path.join(paths.dataRoot(), 'control-plane-exec-policy.json');
  const store = read(storeFile); const entries = Array.isArray(store.policies) ? store.policies : [store];
  const otherEntry = entries.find(entry => entry.workspace_id === other.workspaceId && entry.workspace_generation === other.workspaceGeneration);
  requireState(otherEntry, 'AUTOCAD_POLICY_ENTRY_REQUIRED');
  const common = { activation_epoch_id: epoch.activation_epoch_id, owner_instance_id: verified.descriptor.instance_id,
    parity_sha256: sha(parityPath), smoke_sha256: sha(smokePath), baseline_policy_sha256: before.policy_sha256,
    baseline_native_argv_prefixes: before.native_argv_prefixes, other_scope_sha256: scopeSha(otherEntry), token_prefix: tokenPrefix };
  if (mode === 'install') {
    requireState(before.native_argv_prefixes.length === 0, 'TOKEN_POLICY_ALREADY_INSTALLED_USE_ORIGINAL_RECEIPT');
    const intent = report('packaged-token-install-intent', { ...common, effect_observed: false });
    const installed = await enrollment.installStandingWorkspaceExecPolicy({ ...target, executionMode: 'native_first', nativeArgvPrefixes: [tokenPrefix], probeSandbox: false, replaceExisting: true });
    const after = await enrollment.inspectLocalExecPolicy(target);
    const otherAfter = await enrollment.inspectLocalExecPolicy(other);
    requireState(after.policy_sha256 === installed.policy_sha256 && after.execution_mode === 'native_first'
      && canonical(after.native_argv_prefixes) === canonical([tokenPrefix]) && otherAfter.policy_sha256 === otherBefore.policy_sha256, 'TOKEN_POLICY_INSTALL_NOT_EXACT');
    const result = report('packaged-token-install', { ...common, intent_receipt: intent.report_path, after, other_scope_unchanged: true });
    process.stdout.write(JSON.stringify({ ok: true, report_path: result.report_path, policy_sha256: after.policy_sha256 }) + '\n');
  } else {
    const install = read(option('--install-report'));
    requireState(install.operation === 'packaged-token-install' && install.ok === true, 'TOKEN_INSTALL_RECEIPT_REQUIRED');
    const baselinePrefixes = install.baseline_native_argv_prefixes || [];
    requireState(baselinePrefixes.length === 0 && otherBefore.policy_sha256 === '0d42309ae640f768ba2c5e114822e3cd0d536a2dbab93d381850faf120c10782', 'ORIGINAL_EMPTY_BASELINE_REQUIRED');
    const alreadyRestored = canonical(before.native_argv_prefixes) === canonical(baselinePrefixes);
    requireState(before.execution_mode === 'native_first' && (alreadyRestored || canonical(before.native_argv_prefixes) === canonical([tokenPrefix])), 'TOKEN_POLICY_CURRENT_REQUIRED');
    const restored = alreadyRestored ? { policy_sha256: before.policy_sha256, mutation_performed: false }
      : await enrollment.installStandingWorkspaceExecPolicy({ ...target, executionMode: 'native_first', nativeArgvPrefixes: baselinePrefixes, probeSandbox: false, replaceExisting: true });
    const after = await enrollment.inspectLocalExecPolicy(target);
    const otherAfter = await enrollment.inspectLocalExecPolicy(other);
    const afterStore = read(storeFile);
    const afterEntries = Array.isArray(afterStore.policies) ? afterStore.policies : [afterStore];
    const otherAfterEntry = afterEntries.find(entry => entry.workspace_id === other.workspaceId && entry.workspace_generation === other.workspaceGeneration);
    requireState(after.execution_mode === 'native_first' && after.policy_sha256 === install.baseline_policy_sha256
      && canonical(after.native_argv_prefixes) === canonical(baselinePrefixes)
      && otherAfter.policy_sha256 === otherBefore.policy_sha256 && scopeSha(otherAfterEntry) === install.other_scope_sha256, 'TOKEN_POLICY_RESTORE_NOT_EXACT');
    const result = report('packaged-token-restore', { ...common, install_report: option('--install-report'), restored, after, other_scope_unchanged: true, mutation_performed: !alreadyRestored });
    process.stdout.write(JSON.stringify({ ok: true, report_path: result.report_path }) + '\n');
  }
}

main().catch(error => {
  const result = report(`packaged-token-${mode || 'unknown'}-failure`, { ok: false, code: error.code || 'TOKEN_POLICY_FAILED', mutating_action_started: mode === 'install' || mode === 'restore' });
  process.stderr.write(JSON.stringify({ ok: false, code: result.code, report_path: result.report_path }) + '\n');
  process.exitCode = 1;
});
