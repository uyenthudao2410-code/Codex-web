'use strict';
// Evidence-only observer. Run using the selected package executable with
// ELECTRON_RUN_AS_NODE=1. No Electron app/profile or UI window is created.
// Args: <candidate win-unpacked> <exact READY epoch> <package proof JSON>.
const fs = require('node:fs');
const originalFs = require('original-fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');

const root = 'E:\\DEV\\Codex-web';
const expectedFolder = 'E:\\DEV\\Autocad';
const expectedWorkspaceId = 'workspace_bc86004be2684b958ab7a9a6f9530cd7';
const expectedGeneration = 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a';
const pinnedRendererHash = '8dbc227e9f762c035d339d37e1f37aa4a4785c69dd48f46a50283f5b2c2e70ab';
const pinnedHtmlHash = '0bdce1403a81b2c3a12082912520de931beb0e63dd1b53913ee0c8cf89883505';
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const diskHash = file => sha256(originalFs.readFileSync(file));
let stage = 'arguments';
let candidate;
function requireState(condition, code) {
  if (!condition) throw Object.assign(new Error(code), { code });
}
function samePath(left, right) {
  return path.normalize(String(left || '')).toLowerCase() === path.normalize(String(right || '')).toLowerCase();
}

// Minimal DOM adapter: all production renderer functions run unmodified.
// The adapter records text/attributes and never dispatches event handlers.
function memoryDom() {
  const nodes = new Map();
  const element = () => {
    const children = [];
    const queried = new Map();
    const classes = new Set();
    const node = {
      textContent: '', value: '', title: '', dataset: {}, style: {}, children,
      hidden: false, disabled: false, checked: false,
      classList: {
        add: (...names) => names.forEach(name => classes.add(name)),
        remove: (...names) => names.forEach(name => classes.delete(name)),
        toggle(name, enabled) {
          const next = enabled === undefined ? !classes.has(name) : enabled;
          if (next) classes.add(name); else classes.delete(name);
          return next;
        },
        contains: name => classes.has(name)
      },
      querySelector(selector) {
        if (!queried.has(selector)) queried.set(selector, element());
        return queried.get(selector);
      },
      querySelectorAll: () => [],
      setAttribute(name, value) { node[name] = String(value); },
      removeAttribute(name) { delete node[name]; },
      append: (...items) => children.push(...items),
      appendChild: item => children.push(item),
      replaceChildren: (...items) => { children.splice(0, children.length, ...items); },
      addEventListener() {}, remove() {}, focus() {}, scrollIntoView() {},
      closest: () => node
    };
    return node;
  };
  const document = {
    body: element(), documentElement: element(),
    querySelector(selector) {
      if (!nodes.has(selector)) nodes.set(selector, element());
      return nodes.get(selector);
    },
    querySelectorAll: () => [],
    createElement: () => element(),
    getElementById(id) { return document.querySelector(`#${id}`); }
  };
  return { document, nodes };
}

function renderActualSource(source, evidence) {
  const start = source.lastIndexOf('\ninitialize();');
  requireState(start > 0 && source.slice(start).trim() === 'initialize();', 'RENDERER_STARTUP_BOUNDARY_CHANGED');
  const { document, nodes } = memoryDom();
  const forbidden = () => { throw Object.assign(new Error('VM side effect requested'), { code: 'RENDERER_SIDE_EFFECT_REJECTED' }); };
  const context = vm.createContext({
    document, window: { mcpAssistant: {}, confirm: forbidden },
    localStorage: { getItem: () => null, setItem: forbidden },
    location: { hash: '' }, history: { replaceState: forbidden },
    setTimeout: forbidden, setInterval: forbidden, clearTimeout() {},
    requestAnimationFrame: forbidden,
    __liveEvidence: evidence
  });
  // Only automatic initialize() is excluded. No renderer function is replaced.
  vm.runInContext(source.slice(0, start), context, { timeout: 5000, filename: 'packaged-renderer/app.js' });
  vm.runInContext('Object.assign(state, __liveEvidence); renderSnapshot(state.snapshot, { forceForms: true });',
    context, { timeout: 5000, filename: 'live-renderer-evidence' });
  const labels = Object.fromEntries(['sideWorkspace', 'deviceWorkspace', 'executionWorkspaceLabel', 'selectedWorkspace', 'workspaceMeta']
    .map(id => [id, document.querySelector(`#${id}`).textContent]));
  requireState(Object.values(labels).every(value => value === expectedFolder), 'TARGET_LABELS_NOT_EXACT');
  const access = vm.runInContext('setupWorkspaceAccess(selectedCentralWorkspace())', context, { timeout: 1000 });
  requireState(access.read === true && access.patch === true && access.exec === true, 'RENDERER_PERMISSIONS_NOT_CURRENT');
  const workspaceStatus = document.querySelector('#workspaceStatus').textContent;
  requireState(workspaceStatus === 'Thư mục MCP hiện tại', 'CURRENT_WORKSPACE_STATUS_NOT_EXACT');
  const before = JSON.stringify(labels);
  const snapshot = vm.runInContext('state.snapshot', context);
  requireState(samePath(snapshot.settings.workspace, root) && samePath(snapshot.device.workspace, root), 'NATIVE_DEFAULT_CHANGED');
  vm.runInContext('applyHeartbeat({ signalStale: true });', context, { timeout: 5000 });
  requireState(['sideWorkspace', 'deviceWorkspace', 'executionWorkspaceLabel', 'selectedWorkspace']
    .every(id => document.querySelector(`#${id}`).textContent === 'Chưa kích hoạt thư mục'), 'STALE_LABELS_RETAINED');
  return {
    labels: JSON.parse(before),
    workspace_status: workspaceStatus,
    native_default_workspace: snapshot.settings.workspace,
    device_runtime_workspace: snapshot.device.workspace,
    git_application_state: nodes.get('#deviceGitState')?.textContent || null,
    permissions: { read: access.read, write: access.patch, exec: access.exec },
    stale_heartbeat_clears_labels: true,
    actual_functions: ['renderSnapshot', 'renderCentralExecutorMode', 'renderSetupState', 'renderDevice',
      'renderSetupExecution', 'renderWorkspaceTarget', 'centralActiveWorkspacePath', 'setupWorkspaceAccess', 'applyHeartbeat'],
    replaced_renderer_functions: [],
    automatic_initialize_excluded: true,
    direct_live_screenshot_claimed: false
  };
}

async function main() {
  const expectedEpochId = String(process.argv[3] || '');
  requireState(/^activation-[A-Za-z0-9_-]+$/.test(expectedEpochId), 'EXACT_READY_EPOCH_REQUIRED');
  candidate = fs.realpathSync(path.resolve(process.argv[2] || ''));
  requireState(candidate.toLowerCase().startsWith(path.join(root, 'dist').toLowerCase() + path.sep), 'CANDIDATE_OUTSIDE_WORKSPACE');
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  const appRoot = path.join(candidate, 'resources', 'app.asar');
  requireState(samePath(fs.realpathSync(process.execPath), fs.realpathSync(executable)), 'SELECTED_ELECTRON_EXECUTABLE_REQUIRED');
  const proofFile = fs.realpathSync(path.resolve(process.argv[4] || ''));
  requireState(proofFile.toLowerCase().startsWith(__dirname.toLowerCase() + path.sep), 'PACKAGE_PROOF_OUTSIDE_EVIDENCE_DIRECTORY');
  stage = 'package_hashes';
  const proof = JSON.parse(fs.readFileSync(proofFile, 'utf8'));
  requireState(proof.ok === true && samePath(proof.candidate, candidate)
    && diskHash(appRoot) === proof.app_asar_sha256 && diskHash(executable) === proof.executable_sha256,
  'EXACT_VERIFIED_PACKAGE_REQUIRED');
  const sourceBytes = fs.readFileSync(path.join(appRoot, 'renderer', 'app.js'));
  const htmlBytes = fs.readFileSync(path.join(appRoot, 'renderer', 'index.html'));
  requireState(sha256(sourceBytes) === pinnedRendererHash && sha256(htmlBytes) === pinnedHtmlHash, 'EXACT_RENDERER_BYTES_REQUIRED');
  requireState(htmlBytes.toString('utf8').includes('<span>Git ứng dụng</span><code id="deviceGitState">'), 'APPLICATION_GIT_LABEL_REQUIRED');

  stage = 'verified_live_host';
  const load = name => require(path.join(appRoot, 'electron', 'services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { readVerifiedReadyHost, descriptorMatchesInstallation, descriptorRequestOptions } = load('recoveryHostLauncher');
  const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
  const { readDeviceIdentity } = load('deviceIdentity');
  requireState(process.env.APPDATA && path.isAbsolute(process.env.APPDATA), 'EXISTING_APPDATA_REQUIRED');
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
    resourcesRoot: path.join(candidate, 'resources', 'resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2);
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'SELECTED_READY_HOST_NOT_VERIFIED');
  const requestOptions = descriptorRequestOptions(verified.descriptor);
  const exactCall = (action, args = []) => client.call(action, args, requestOptions);
  const requireReadyEpoch = epoch => requireState(epoch?.activation_epoch_id === expectedEpochId
    && (epoch.state || epoch.epoch_state) === 'READY' && epoch.admission_open === true, 'READY_EPOCH_CHANGED');
  requireReadyEpoch(await exactCall('runtime.activation_epoch_status'));
  const device = readDeviceIdentity(paths.deviceFile());
  const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
  stage = 'fresh_authenticated_observations';
  const [snapshot, authority, inventory, filePolicies] = await Promise.all([
    exactCall('runtime.snapshot'), service.reconcileAuthorityStatus({ deviceIdentity: device }),
    service.listWorkspaces(), service.inspectStandingWorkspaceFilePolicies()
  ]);
  requireState(snapshot.settings?.executionRole === 'central_executor' && snapshot.status?.fullyReady === true
    && snapshot.status.signalStale !== true && snapshot.status.telemetryAvailable !== false
    && snapshot.device?.device_id === device.device_id, 'CURRENT_RUNTIME_SNAPSHOT_NOT_READY');
  const workspaces = inventory.filter(item => item.workspace_id === expectedWorkspaceId && item.workspace_generation === expectedGeneration);
  requireState(workspaces.length === 1 && samePath(workspaces[0].workspace_path, expectedFolder), 'EXACT_REGISTERED_FOLDER_NOT_FOUND');
  const workspace = workspaces[0];
  requireState(authority.fresh === true && authority.state === 'active' && authority.device_id === device.device_id, 'CURRENT_AUTHORITY_NOT_ACTIVE');
  const targets = authority.targets.filter(target => target.workspace_id === expectedWorkspaceId
    && target.workspace_generation === expectedGeneration && target.dispatch_state === 'dispatchable');
  requireState(targets.length === 1, 'EXACT_AUTHORITY_TARGET_REQUIRED');
  const execObservation = await service.inspectStandingWorkspaceExecPolicy({ workspaceId: expectedWorkspaceId,
    workspaceGeneration: expectedGeneration, probeSandbox: false });
  stage = 'actual_packaged_full_render';
  const rendered = renderActualSource(sourceBytes.toString('utf8'), {
    snapshot, centralWorkspaces: inventory, centralWorkspaceInventoryStatus: 'loaded',
    centralWorkspaceSelection: { workspace_id: expectedWorkspaceId, workspace_generation: expectedGeneration },
    centralWorkspaceCapabilities: workspace.capabilities, centralWorkspacePreset: 'code',
    centralAuthorityStatus: authority, centralFilePolicies: filePolicies, centralFilePolicyStatus: 'loaded',
    centralExecObservations: { [`${expectedWorkspaceId}:${expectedGeneration}`]: execObservation }
  });
  stage = 'post_observation_epoch';
  requireReadyEpoch(await exactCall('runtime.activation_epoch_status'));
  const report = {
    schema_version: 1, operation: 'live_data_packaged_renderer_verification', ok: true,
    observed_at_utc: new Date().toISOString(), candidate, expected_epoch_id: expectedEpochId,
    renderer_sha256: pinnedRendererHash, html_sha256: pinnedHtmlHash,
    app_asar_sha256: proof.app_asar_sha256,
    device_id: device.device_id, workspace_id: expectedWorkspaceId, workspace_generation: expectedGeneration,
    authority: { fresh: authority.fresh, state: authority.state, observed_at_ms: authority.observed_at_ms,
      binding_id: targets[0].binding_id, dispatch_state: targets[0].dispatch_state,
      presence_state: targets[0].presence_state, readiness: targets[0].readiness },
    policy_observed_at_ms: { read: filePolicies.file_read?.authority_observed_at_ms,
      write: filePolicies.approved_patch?.authority_observed_at_ms, exec: execObservation.policy?.authority_observed_at_ms },
    rendered, raw_snapshots_or_secrets_written: false, sandbox_probe_requested: false,
    external_mutation_requested: false, existing_activation_epoch_unchanged: true
  };
  const reportPath = path.join(__dirname, `live-renderer-verification-${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), { flag: 'wx' });
  console.log(JSON.stringify({ ok: true, operation: report.operation, report_path: reportPath,
    labels: rendered.labels, native_default_workspace: rendered.native_default_workspace,
    permissions: rendered.permissions, epoch_unchanged: true, direct_live_screenshot_claimed: false }));
}

main().then(() => process.exit(0), error => {
  // Deliberately omit error messages, stacks, snapshots and descriptor fields.
  const report = { ok: false, operation: 'live_data_packaged_renderer_verification', stage,
    code: /^[A-Z][A-Z0-9_]{2,100}$/.test(error?.code || '') ? error.code : 'LIVE_RENDERER_VERIFICATION_FAILED',
    observed_at_utc: new Date().toISOString(), candidate: candidate || null };
  const reportPath = path.join(__dirname, `live-renderer-verification-failure-${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), { flag: 'wx' });
  console.error(JSON.stringify({ ...report, report_path: reportPath }));
  process.exit(1);
});
