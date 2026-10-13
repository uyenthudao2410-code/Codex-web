'use strict';
// Synthetic adapter smoke only. This never makes a live-runtime claim.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = 'E:\\DEV\\Codex-web';
const helperPath = path.join(__dirname, 'verify-live-renderer.cjs');
const helper = fs.readFileSync(helperPath, 'utf8');
const renderer = fs.readFileSync(path.join(root, 'renderer', 'app.js'), 'utf8');
const expectedFolder = 'E:\\DEV\\Autocad';
const workspace = { workspace_id: 'workspace_bc86004be2684b958ab7a9a6f9530cd7',
  workspace_generation: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a',
  display_name: 'Autocad', workspace_path: expectedFolder, capabilities: { read: true, write: true, exec: true } };
const context = vm.createContext({ root, expectedFolder, vm, path,
  document: { body: { dataset: {} } } });
vm.runInContext(helper.slice(helper.indexOf('function requireState('), helper.indexOf('async function main(')), context);
vm.runInContext(renderer.slice(renderer.indexOf('function createPreviewApi('), renderer.indexOf('\nconst pageMeta')), context);
async function main() {
  const snapshot = (await vm.runInContext('createPreviewApi().snapshot()', context)).data;
  Object.assign(snapshot.settings, { executionRole: 'central_executor', workspace: root,
    controlPlaneServerUrl: 'https://synthetic.example.test' });
  Object.assign(snapshot.status, { centralConnected: true, authorityReady: true, signalStale: false, telemetryAvailable: true });
  snapshot.device.workspace = root;
  const contract = { schema_version: 32, profile: 'control-plane-private-tunnel-service-v1', sha256: 'f'.repeat(64) };
  const policy = hash => ({ state: 'enabled', workspace_id: workspace.workspace_id,
    workspace_generation: workspace.workspace_generation, policy_sha256: hash.repeat(64),
    facade_contract: contract, current_facade_contract: contract, authority_observed_at_ms: Date.now() });
  context.__source = renderer;
  context.__evidence = { snapshot, centralWorkspaces: [workspace], centralWorkspaceInventoryStatus: 'loaded',
    centralWorkspaceSelection: { workspace_id: workspace.workspace_id, workspace_generation: workspace.workspace_generation },
    centralWorkspaceCapabilities: workspace.capabilities, centralWorkspacePreset: 'code',
    centralAuthorityStatus: { fresh: true, state: 'active', dispatchable_target_count: 1,
      targets: [{ ...workspace, dispatch_state: 'dispatchable', presence_state: 'online', readiness: 'ready', policy_state: 'enabled' }] },
    centralFilePolicies: { file_read: policy('a'), approved_patch: policy('b') }, centralFilePolicyStatus: 'loaded',
    centralExecObservations: { [`${workspace.workspace_id}:${workspace.workspace_generation}`]: { policy: policy('c'), sandbox: { state: 'not_checked' } } }
  };
  const result = vm.runInContext('renderActualSource(__source, __evidence)', context, { timeout: 10000 });
  const report = { ok: true, synthetic_data_only: true, actual_full_renderer_functions: true,
    helper_sha256: crypto.createHash('sha256').update(helper).digest('hex'),
    renderer_sha256: crypto.createHash('sha256').update(renderer).digest('hex'),
    labels: result.labels, stale_heartbeat_clears_labels: result.stale_heartbeat_clears_labels,
    replaced_renderer_functions: result.replaced_renderer_functions,
    live_claim: false, observed_at_utc: new Date().toISOString() };
  fs.writeFileSync(path.join(__dirname, 'renderer-dom-selfcheck.json'), JSON.stringify(report, null, 2), { flag: 'wx' });
  console.log(JSON.stringify(report));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
