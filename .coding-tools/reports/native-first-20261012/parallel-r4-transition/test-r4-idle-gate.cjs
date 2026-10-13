'use strict';
// Exercise the controller's actual read-only gate with preserved observer data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, 'packaged-operations.cjs'), 'utf8');
const gateSource = source.slice(source.indexOf('  const serverFence = () => {'), source.indexOf('  let result;'));
const original = JSON.parse(fs.readFileSync(path.join(__dirname, '../../parallel-native-first-20261012/server-readiness-before-r4.json'), 'utf8'));
const targets = [
  { workspace_id: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94', workspace_generation: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' },
  { workspace_id: 'workspace_bc86004be2684b958ab7a9a6f9530cd7', workspace_generation: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a' }
];
function invoke(fence, now = original.capture_completed_at_ms + 1000) {
  return vm.runInNewContext(gateSource + '\nserverFence();', {
    option: () => 'fixture', read: () => fence, digest: () => 'fixture-sha', targets,
    Date: { now: () => now }, requireState: (condition, code) => { if (!condition) throw new Error(code); }
  });
}
function rejects(edit) { const fixture = structuredClone(original); edit(fixture); assert.throws(() => invoke(fixture), /FRESH_EXACT_IDLE_SERVER_CENSUS_REQUIRED/); }
// The captured report has one expired dispatch blocker from another device and
// retired workspace. The gate records it and permits the current two-scope
// handoff because the current device census is idle.
assert.deepEqual(invoke(original).foreign_expired_blockers, ['act_0f0a49c6424d42d3bc7bc49ad46e4ffa']);
const idle = structuredClone(original);
idle.global_live_work_by_scope.active_actions = [];
idle.global_live_work_by_scope.blocking_action_identities = [];
assert.equal(invoke(idle).admission_fence_claimed, false);
assert.throws(() => invoke(idle, idle.capture_completed_at_ms + 120001), /FRESH_EXACT_IDLE_SERVER_CENSUS_REQUIRED/);
rejects(fence => { fence.global_live_work_by_scope.active_actions.push({ action_id: 'new' }); });
rejects(fence => { fence.expected_current_scopes['Codex-web'].expected_generation = 'other'; });
rejects(fence => { fence.historical_unknown_actions_preserved.find(item => item.action_id === 'act_3849e259d55546639794cec40f63fea8').disposition = null; });
rejects(fence => { fence.historical_unknown_actions_preserved.pop(); });
rejects(fence => { fence.node.device_id = 'other'; });
console.log('7 r4 idle gate cases passed; no runtime calls.');
