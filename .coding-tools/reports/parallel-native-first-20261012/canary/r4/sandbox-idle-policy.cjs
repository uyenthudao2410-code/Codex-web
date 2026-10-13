'use strict';
// Preparation observes; apply changes exactly one scoped execution policy.
const fs = require('node:fs');
const originalFs = require('original-fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = 'E:\\DEV\\Codex-web';
const reportRoot = __dirname;
const expectedCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked');
const mode = process.argv[2];
const option = name => { const i = process.argv.indexOf(name); return i < 0 ? undefined : process.argv[i + 1]; };
const requireState = (ok, code) => { if (!ok) throw Object.assign(new Error(code), { code }); };
const sha = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
const canonical = value => Array.isArray(value) ? `[${value.map(canonical).join(',')}]`
  : value && typeof value === 'object' ? `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}` : JSON.stringify(value);
const scopeSha = value => crypto.createHash('sha256').update(canonical(value)).digest('hex');
const read = file => {
  requireState(path.isAbsolute(file) && fs.statSync(file).isFile() && fs.statSync(file).size <= 2097152, 'BOUNDED_ABSOLUTE_RECEIPT_REQUIRED');
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
};
const targets = [
  { workspaceId: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94', workspaceGeneration: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097', path: root },
  { workspaceId: 'workspace_bc86004be2684b958ab7a9a6f9530cd7', workspaceGeneration: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a', path: 'E:\\DEV\\Autocad' }
];
let mutating = false;
const save = (kind, value, file) => {
  const report = { schema_version: 1, operation: kind, ok: true, observed_at_ms: Date.now(), ...value };
  report.report_path = file || path.join(reportRoot, `${kind}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}.json`);
  requireState(path.resolve(report.report_path).startsWith(reportRoot + path.sep), 'CANARY_RECEIPT_PATH_REQUIRED');
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  return report;
};

async function main() {
  requireState(['prepare', 'isolate', 'restore'].includes(mode), 'POLICY_OPERATION_INVALID');
  const parityPath = option('--parity-proof');
  const smokePath = option('--smoke-proof');
  const parity = read(parityPath);
  const smoke = read(smokePath);
  const candidate = path.resolve(parity.candidate);
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  const archive = path.join(candidate, 'resources/app.asar');
  requireState(candidate.toLowerCase() === path.resolve(expectedCandidate).toLowerCase() && parity.ok === true
    && parity.proof_kind === 'exact_source_package_parity' && sha(executable) === parity.executable_sha256
    && sha(archive) === parity.app_asar_sha256 && smoke.ok === true && smoke.candidate === candidate
    && smoke.sha256.source_package_parity_receipt === sha(parityPath)
    && smoke.sha256.executable === parity.executable_sha256 && smoke.sha256.app_asar === parity.app_asar_sha256
    && smoke.production_descriptor_stable === true && smoke.fixture_generations_alive_after?.length === 0
    && smoke.candidate_process_census_after?.length === 0 && smoke.profiles_remaining_after?.length === 0, 'EXACT_SOURCE_PACKAGE_AND_SMOKE_REQUIRED');
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(), 'SELECTED_PACKAGED_ELECTRON_REQUIRED');
  for (const [relative, hash] of Object.entries(parity.code_sha256)) requireState(sha(path.join(root, relative)) === hash, 'SOURCE_CHANGED_AFTER_PACKAGE_PROOF');
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
  requireState(census.lifecycle?.blockers?.every(reason => reason === 'live_runtime_state_process')
    && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0
    && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes',
      'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'].every(key => census.counts[key] === 0), 'IDLE_EXACT_LOCAL_WORK_REQUIRED');
  const enrollment = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
  const observed = [];
  for (const target of targets) observed.push(await enrollment.inspectLocalExecPolicy(target));
  requireState(observed.every((policy, index) => policy.state === 'enabled' && policy.workspace_id === targets[index].workspaceId
    && policy.workspace_generation === targets[index].workspaceGeneration), 'BOTH_SCOPED_POLICIES_REQUIRED');
  const storeFile = path.join(paths.dataRoot(), 'control-plane-exec-policy.json');
  const scopeEntry = target => {
    const store = read(storeFile);
    const entries = Array.isArray(store.policies) ? store.policies : [store];
    const matches = entries.filter(entry => entry.workspace_id === target.workspaceId && entry.workspace_generation === target.workspaceGeneration);
    requireState(matches.length === 1, 'EXACT_POLICY_SCOPE_NOT_UNIQUE');
    return matches[0];
  };
  const otherScope = scopeSha(scopeEntry(targets[1]));
  const common = { candidate, activation_epoch_id: epoch.activation_epoch_id, owner_instance_id: verified.descriptor.instance_id,
    parity_sha256: sha(parityPath), smoke_sha256: sha(smokePath), other_scope_sha256: otherScope };
  let result;
  if (mode === 'prepare') {
    requireState(observed[0].execution_mode === 'native_first', 'EXPECTED_NATIVE_FIRST_POLICY_REQUIRED');
    const output = option('--output');
    requireState(path.isAbsolute(output), 'NEW_ABSOLUTE_PLAN_REQUIRED');
    result = save('isolated-idle-policy-plan', { ...common, before: observed, census, mutations: 0,
      planned_argv: ['node', '--version'], planned_mode: 'isolated', target: targets[0] }, output);
  } else {
    requireState(process.argv.includes('--apply'), 'EXPLICIT_APPLY_REQUIRED');
    const planPath = option('--plan');
    const plan = read(planPath);
    requireState(plan.operation === 'isolated-idle-policy-plan' && plan.ok === true && plan.candidate === candidate
      && plan.activation_epoch_id === epoch.activation_epoch_id && plan.owner_instance_id === verified.descriptor.instance_id
      && plan.other_scope_sha256 === otherScope && plan.parity_sha256 === common.parity_sha256
      && plan.before[0].workspace_id === targets[0].workspaceId && plan.before[0].workspace_generation === targets[0].workspaceGeneration,
      'EXACT_POLICY_PLAN_REQUIRED');
    const wantedMode = mode === 'isolate' ? 'isolated' : plan.before[0].execution_mode;
    if (mode === 'isolate') {
      requireState(Date.now() - plan.observed_at_ms >= 0 && Date.now() - plan.observed_at_ms <= 300000
        && observed[0].policy_sha256 === plan.before[0].policy_sha256 && observed[1].policy_sha256 === plan.before[1].policy_sha256
        && observed[0].execution_mode === plan.before[0].execution_mode
        && canonical(observed[0].native_argv_prefixes) === canonical(plan.before[0].native_argv_prefixes),
        'FRESH_UNCHANGED_POLICY_PLAN_REQUIRED');
    } else {
      const isolated = read(option('--isolated-receipt'));
      requireState(isolated.operation === 'isolated-idle-policy-isolate' && isolated.ok === true
        && isolated.plan_sha256 === sha(planPath) && isolated.after.policy_sha256 === observed[0].policy_sha256
        && observed[0].execution_mode === 'isolated', 'EXACT_CURRENT_ISOLATED_POLICY_REQUIRED');
      const remotePath = option('--remote-receipt');
      requireState(path.isAbsolute(remotePath) && fs.statSync(remotePath).isFile() && fs.statSync(remotePath).size <= 2097152,
        'BOUNDED_ORIGINAL_REMOTE_RECEIPT_REQUIRED');
      const remoteRows = fs.readFileSync(remotePath, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
      const finals = remoteRows.filter(value => value.operation === 'isolated_idle_shared_mcp_canary' && value.phase === 'final');
      requireState(finals.length === 1 && finals[0].workspace_id === targets[0].workspaceId
        && finals[0].workspace_generation === targets[0].workspaceGeneration && finals[0].requires_reconciliation === false
        && finals[0].final_action_status?.action_id === finals[0].action_id && finals[0].final_action_status?.settled_at_ms != null
        && finals[0].final_action_status?.reconciliation_required === false && finals[0].task_closed_verified === true
        && finals[0].writer_released_verified === true, 'ORIGINAL_REMOTE_ACTION_MUST_BE_SETTLED_BEFORE_RESTORE');
    }
    // Save intent first. Do not retry an uncertain install without inspection.
    const intent = save(`isolated-idle-policy-${mode}-intent`, { ...common, plan_sha256: sha(planPath), before: observed,
      wanted_mode: wantedMode, effect_observed: false });
    mutating = true;
    const installed = await enrollment.installStandingWorkspaceExecPolicy({ ...targets[0], executionMode: wantedMode,
      nativeArgvPrefixes: plan.before[0].native_argv_prefixes || [], probeSandbox: false, replaceExisting: true });
    requireState(scopeSha(scopeEntry(targets[1])) === otherScope, 'OTHER_WORKSPACE_POLICY_CHANGED');
    const after = await enrollment.inspectLocalExecPolicy(targets[0]);
    requireState(after.execution_mode === wantedMode && after.policy_sha256 === installed.policy_sha256
      && canonical(after.native_argv_prefixes) === canonical(plan.before[0].native_argv_prefixes || []), 'EXACT_SCOPED_POLICY_RESULT_REQUIRED');
    result = save(`isolated-idle-policy-${mode}`, { ...common, plan_sha256: sha(planPath), intent_receipt: intent.report_path,
      after, other_scope_unchanged: true, vm_probe_started: false });
  }
  process.stdout.write(JSON.stringify({ ok: true, operation: result.operation, report_path: result.report_path, mutating }) + '\n', () => process.exit(0));
}
main().catch(error => {
  const result = save('isolated-idle-policy-failure', { ok: false, mode, code: error.code || 'POLICY_HELPER_FAILED', mutating_action_started: mutating,
    next_action: mutating ? 'Inspect original policy intent and both exact scopes before retry or restoration.' : 'Resolve read-only gate.' });
  process.stderr.write(JSON.stringify({ ok: false, code: result.code, report_path: result.report_path, mutating }) + '\n', () => process.exit(1));
});
