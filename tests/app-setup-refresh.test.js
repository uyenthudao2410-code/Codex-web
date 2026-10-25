'use strict';

// GUI round 4 residual (b): a 'workspace-refresh' click whose load fails at
// a pre-try gate must surface a named error instead of dying as an
// unhandled rejection behind the vague "lỗi chưa rõ" line. Slices the real
// handleSetupPrimaryAction out of renderer/app.js and runs it in vm with
// stubbed refresh/toast/render — the click listener calls it without
// await/catch (app.js:3749), so a throw here used to be unhandled.

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

function fixture(refreshImpl) {
  const toasts = [];
  const renders = [];
  const state = {
    snapshot: { settings: {} },
    centralWorkspaceInventoryStatus: 'not_loaded',
    centralWorkspaceInventoryError: null,
  };
  const context = vm.createContext({
    state,
    $: (selector) => (selector === '#setupPrimaryAction'
      ? { dataset: { setupAction: 'workspace-refresh' } } : null),
    refreshControlPlaneWorkspaces: refreshImpl,
    toast: (title, message, type) => toasts.push({ title, message, type }),
    renderSetupState: (snapshot) => renders.push(snapshot),
  });
  vm.runInContext(section('async function handleSetupPrimaryAction() {', 'function navigate('), context);
  return { context, state, toasts, renders, run: () => context.handleSetupPrimaryAction() };
}

test('(b) gate throw with a code is recorded as a named unknown error + error toast', async () => {
  const fx = fixture(async () => { throw { code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED' }; });
  await fx.run();
  assert.equal(fx.state.centralWorkspaceInventoryStatus, 'unknown');
  assert.equal(fx.state.centralWorkspaceInventoryError, 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED');
  assert.equal(fx.toasts.length, 1);
  assert.equal(fx.toasts[0].type, 'error');
  assert.match(fx.toasts[0].message, /CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED/);
  assert.equal(fx.renders.length, 1);
});

test('(b) gate throw without a code falls back to the error message', async () => {
  const fx = fixture(async () => { throw new Error('Đọc inventory thất bại'); });
  await fx.run();
  assert.equal(fx.state.centralWorkspaceInventoryStatus, 'unknown');
  assert.equal(fx.state.centralWorkspaceInventoryError, 'Đọc inventory thất bại');
  assert.equal(fx.toasts.length, 1);
  assert.equal(fx.toasts[0].type, 'error');
});

test('(b) successful refresh records no error and shows no error toast', async () => {
  const fx = fixture(async () => ['ws-1']);
  await fx.run();
  assert.equal(fx.state.centralWorkspaceInventoryStatus, 'not_loaded');
  assert.equal(fx.state.centralWorkspaceInventoryError, null);
  assert.equal(fx.toasts.length, 0);
});
