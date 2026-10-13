'use strict';
// Offline exact-scope mutation and partial-receipt boundaries.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { installCanaryApprovals } = require('./canary-policy-approvals.cjs');

function fixture(t) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'canary-policy-offline-'));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const relative = 'tests/fixtures/parallel-native-overlap-20261012/hold.cjs';
  const targets = ['Codex-web', 'Autocad'].map((label, index) => ({ workspace_path: path.join(temporary, label),
    workspace_id: `workspace-reviewed-${index}`, workspace_generation: `generation-reviewed-${index}` }));
  const manifest = { prepared: true, targets: targets.map(target => {
    const file = path.join(target.workspace_path, relative);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, 'reviewed fixture ' + path.basename(target.workspace_path));
    return { workspace_label: path.basename(target.workspace_path), files: [{ path: relative,
      sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'), size_bytes: fs.statSync(file).size }] };
  }) };
  const fixtureManifestPath = path.join(temporary, 'manifest.json');
  fs.writeFileSync(fixtureManifestPath, JSON.stringify(manifest));
  const policies = new Map(targets.map(target => [target.workspace_id, { state: 'enabled',
    workspace_id: target.workspace_id, workspace_generation: target.workspace_generation,
    execution_mode: 'native_first', native_argv_prefixes: [['node', 'existing-reviewed.js']] }]));
  const installs = [];
  const enrollment = {
    async inspectLocalExecPolicy({ workspaceId }) { return policies.get(workspaceId); },
    async installStandingWorkspaceExecPolicy(request) {
      installs.push(request);
      policies.set(request.workspaceId, { ...policies.get(request.workspaceId), execution_mode: request.executionMode,
        native_argv_prefixes: request.nativeArgvPrefixes });
    }
  };
  const expectedEpoch = 'activation-reviewed-123';
  const ready = { activation_epoch_id: expectedEpoch, state: 'READY', admission_open: true };
  return { targets, enrollment, installs, policies, ready, expectedEpoch, fixtureManifestPath, approvalSet: 'overlap',
    observeActivation: async () => ready };
}

test('two exact policies preserve existing prefixes and emit each verified receipt', async t => {
  const state = fixture(t);
  const records = [];
  const receipt = await installCanaryApprovals({ ...state, onVerifiedTarget: record => records.push(record) });
  assert.equal(state.installs.length, 2);
  assert.equal(records.length, 2);
  assert.equal(receipt.approval_set, 'overlap');
  for (const [index, request] of state.installs.entries()) {
    assert.equal(request.workspaceId, state.targets[index].workspace_id);
    assert.equal(request.workspaceGeneration, state.targets[index].workspace_generation);
    assert.equal(request.executionMode, 'native_only');
    assert.deepEqual(request.nativeArgvPrefixes, [['node', 'existing-reviewed.js'],
      ['node', 'tests/fixtures/parallel-native-overlap-20261012/hold.cjs']]);
  }
});

test('changed READY epoch prevents first mutation', async t => {
  const state = fixture(t);
  let observations = 0;
  await assert.rejects(installCanaryApprovals({ ...state, observeActivation: async () =>
    ++observations === 1 ? state.ready : { ...state.ready, activation_epoch_id: 'activation-retired-123' } }),
  { code: 'ACTIVATION_CHANGED_BEFORE_CANARY_APPROVAL' });
  assert.equal(state.installs.length, 0);
});

test('first successful target receipt survives later exact-scope rejection', async t => {
  const state = fixture(t);
  state.policies.get(state.targets[1].workspace_id).workspace_generation = 'generation-retired';
  const records = [];
  await assert.rejects(installCanaryApprovals({ ...state, onVerifiedTarget: record => records.push(record) }),
    { code: 'EXACT_EXISTING_EXEC_POLICY_REQUIRED' });
  assert.equal(state.installs.length, 1);
  assert.equal(records.length, 1);
  assert.equal(records[0].workspace_label, 'Codex-web');
});
