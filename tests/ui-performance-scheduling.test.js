const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (name) => fs.readFileSync(path.join(root, name), 'utf8');

test('browser workspace polling is single-flight, visibility-aware, and self-scheduled', () => {
  const source = read('renderer/browser.js');
  assert.match(source, /let workspaceRefreshInFlight = null;/);
  assert.match(source, /if \(workspaceRefreshInFlight\) return workspaceRefreshInFlight;/);
  assert.match(source, /if \(!force && document\.visibilityState === 'hidden'\) return;/);
  assert.match(source, /async function pollWorkspace\(\)/);
  assert.match(source, /setTimeout\(pollWorkspace, workspacePollDelay\(\)\)/);
  assert.doesNotMatch(source, /setInterval\(refreshWorkspace/);
  assert.match(source, /void refreshWorkspace\(true\)/);
});

test('browser skips rebuilding the workspace selector when the workspace projection is unchanged', () => {
  const source = read('renderer/browser.js');
  assert.match(source, /let lastWorkspaceSignature = '';/);
  assert.match(source, /const workspaceListChanged = signature !== lastWorkspaceSignature;/);
  assert.match(source, /if \(!workspaceListChanged\) return;/);
  assert.match(source, /lastWorkspaceSignature = signature;/);
});

test('control center coalesces heartbeat renders and avoids repeated DOM state writes', () => {
  const source = read('renderer/control-center.js');
  assert.match(source, /if \(element\.textContent !== text\) element\.textContent = text;/);
  assert.match(source, /function scheduleHeartbeatRender\(\)/);
  assert.match(source, /if \(heartbeatRenderScheduled\)/);
  assert.match(source, /window\.requestAnimationFrame\(commit\)/);
  assert.match(source, /element\.dataset\.state !== state/);
  assert.match(source, /const flowChanged = group\.dataset\.flow !== flow;/);
  const heartbeatStart = source.indexOf('api.onHeartbeat?.');
  assert.ok(heartbeatStart >= 0, 'heartbeat subscription must remain present');
  const heartbeatBlock = source.slice(heartbeatStart);
  assert.match(heartbeatBlock, /scheduleHeartbeatRender\(\)/);
  assert.doesNotMatch(heartbeatBlock, /\n\s*renderAll\(\);/);
});
