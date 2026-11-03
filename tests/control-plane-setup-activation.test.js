'use strict';

// Fix A (03/11): the setup continuation must activate the selected folder
// after the owner's confirm dialog, because registration alone never
// creates the server binding that policy-authority checks require. Slices
// the real startSetupContinuation out of renderer/app.js and runs it in vm
// with stubbed helpers, following the app-setup-refresh.test.js pattern.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer/app.js'), 'utf8');
function section(start, end) {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing app fragment: ${start}`);
  return source.slice(from, to);
}
const fnSource = section('async function startSetupContinuation(', '\nasync function continueSetup() {');

const WORKSPACE = {
  workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
  workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
  display_name: 'my-project',
  workspace_path: 'C:\\test\\proj',
  capabilities: { read: true, write: true, exec: false },
};

function fixture(activateImpl) {
  const activateCalls = [];
  const continueCalls = [];
  const stored = [];
  const api = activateImpl === null ? {} : {
    activateControlPlaneWorkspace: async (req) => {
      activateCalls.push(req);
      return activateImpl(req);
    },
  };
  const state = {
    setupStartBusy: false, setupContinuationBusy: false, centralPermissionBusy: false,
    centralWorkspaceBusy: false, centralPolicyBusy: false, centralExecBusy: false,
    centralEnrollmentBusy: false, setupContinuation: null, setupContinuationTimer: null,
    centralWorkspaceSelection: {
      workspace_id: WORKSPACE.workspace_id,
      workspace_generation: WORKSPACE.workspace_generation,
    },
    centralWorkspaceCandidate: '', centralWorkspaceActivationReceipt: null,
    centralExecutionMode: undefined,
    snapshot: {
      settings: { controlPlaneServerUrl: 'https://ubuntu.test' },
      device: { device_id: 'device-0001', display_name: 'Máy bàn' },
    },
    centralEnrollmentStatus: null,
  };
  const context = vm.createContext({
    state,
    window: { confirm: () => true },
    localStorage: { setItem: (k, v) => stored.push([k, v]) },
    api,
    unwrap: (r) => { if (!r?.ok) throw new Error('not ok'); return r.data; },
    assertPackagedCentralSetup: () => {},
    cancelSetupContinuation: () => {},
    renderSetupExecution: () => {},
    reconcileControlPlaneEnrollment: async () => {
      state.centralEnrollmentStatus = { fresh: true, state: 'approved' };
    },
    requestControlPlaneEnrollment: async () => {},
    centralSetupGuidance: () => ({ detail: '' }),
    navigate: () => {},
    selectedCentralWorkspace: () => WORKSPACE,
    chooseControlPlaneWorkspace: async () => true,
    setupOrigin: () => 'https://ubuntu.test',
    setupDevice: () => 'device-0001',
    inspectControlPlaneExecPolicy: async () => {},
    centralWorkspaceCapabilitiesFromUi: () => ({ read: true, write: true, exec: false }),
    centralWorkspaceCapabilityLabel: () => 'Đọc + Sửa',
    centralWorkspaceCapabilitiesChanged: () => false,
    isLocalExecution: () => true,
    registerControlPlaneWorkspace: async () => {
      throw new Error('should not register when a selection exists');
    },
    replaceControlPlaneWorkspace: async () => {
      throw new Error('should not replace when capabilities match');
    },
    saveSetupSelection: () => {},
    continueSetup: async () => { continueCalls.push(true); return 'continued'; },
  });
  const start = vm.runInContext(fnSource + '\nstartSetupContinuation;', context);
  return { state, activateCalls, continueCalls, stored, start };
}

function okReceipt(req) {
  return {
    ok: true,
    data: {
      device_id: 'device-0001',
      workspace_id: req.workspaceId,
      workspace_generation: req.workspaceGeneration,
      binding_id: 'bind_' + 'e'.repeat(32),
      state: 'active',
      workspace_path: WORKSPACE.workspace_path,
    },
  };
}

test('setup continuation activates the selected folder after confirm', async () => {
  const f = fixture(async (req) => okReceipt(req));
  const result = await f.start();
  assert.equal(result, 'continued');
  assert.equal(f.activateCalls.length, 1);
  // Field-wise comparison: the request object is created inside the vm
  // realm, so deepStrictEqual rejects it on prototype even when the
  // structure matches.
  assert.equal(f.activateCalls[0].workspaceId, WORKSPACE.workspace_id);
  assert.equal(f.activateCalls[0].workspaceGeneration, WORKSPACE.workspace_generation);
  assert.equal(f.activateCalls[0].confirmActivate, true);
  assert.equal(f.state.centralWorkspaceActivationReceipt.binding_id, 'bind_' + 'e'.repeat(32));
  assert.equal(f.state.centralWorkspaceActivationReceipt.workspace_path, WORKSPACE.workspace_path);
  assert.equal(f.continueCalls.length, 1);
  assert.equal(f.stored.length, 1);
  assert.equal(f.stored[0][0], 'coding-tools-active-folder-v1');
});

test('a failed activation stops the flow with a plain-language error', async () => {
  const f = fixture(async () => { throw new Error('boom'); });
  await assert.rejects(() => f.start(), /Không thể kích hoạt thư mục đã chọn trên Ubuntu: boom/);
  assert.equal(f.continueCalls.length, 0);
});

test('an app build without the activate bridge refuses instead of silently skipping', async () => {
  const f = fixture(null);
  await assert.rejects(() => f.start(), /chưa hỗ trợ kích hoạt thư mục/);
  assert.equal(f.continueCalls.length, 0);
});
