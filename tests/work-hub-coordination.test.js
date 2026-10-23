const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');
const coordination = require('../electron/services/workHubCoordination');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-coord-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const dir = path.join(root, '.coding-tools', 'orchestration');
  fs.mkdirSync(dir, { recursive: true });
  const db = new DatabaseSync(path.join(dir, 'ledger.sqlite3'));
  db.exec(`
    CREATE TABLE runs (run_id TEXT, task_id TEXT, objective TEXT, status TEXT, started_at TEXT, finished_at TEXT, metadata_json TEXT);
    CREATE TABLE waves (wave_id TEXT, run_id TEXT, ordinal INTEGER, execution_mode TEXT, base_head TEXT, worktree_fp TEXT, contract_fp TEXT, status TEXT, started_at TEXT, finished_at TEXT, metadata_json TEXT);
    CREATE TABLE delegations (delegation_id TEXT, wave_id TEXT, parent_delegation_id TEXT, authority_owner TEXT, route_requested TEXT, route_resolved TEXT, model TEXT, effort TEXT, allowed_scope_json TEXT, status TEXT, started_at TEXT, finished_at TEXT, metadata_json TEXT);
    CREATE TABLE agent_lanes (lane_id TEXT, run_id TEXT, wave_id TEXT, semantic_key TEXT, role TEXT, provider TEXT, thread_id TEXT, session_id TEXT, lifecycle TEXT, profile TEXT, model TEXT, effort TEXT, base_head TEXT, worktree_fp TEXT, contract_fp TEXT, last_turn_id TEXT, created_at TEXT, updated_at TEXT, metadata_json TEXT);
    CREATE TABLE controller_leases (run_id TEXT, fencing_token INTEGER, lease_id TEXT, owner_client_id TEXT, status TEXT, expires_at TEXT, updated_at TEXT);
    CREATE TABLE proofs (proof_id TEXT, run_id TEXT, wave_id TEXT, stage_id TEXT, stage_version TEXT, input_fingerprint TEXT, status TEXT, command_hash TEXT, started_at TEXT, finished_at TEXT, duration_ms INTEGER, exit_code INTEGER, cache_hit INTEGER, upstream_json TEXT, metadata_json TEXT);
    CREATE TABLE events (seq INTEGER, event_id TEXT, run_id TEXT, wave_id TEXT, delegation_id TEXT, event_type TEXT, state_before TEXT, state_after TEXT, event_time TEXT, payload_json TEXT, prev_hash TEXT, event_hash TEXT);
    CREATE TABLE coordination_messages (message_id TEXT, run_id TEXT, wave_id TEXT, lane_id TEXT, direction TEXT, kind TEXT, status TEXT, base_head TEXT, worktree_fp TEXT, created_at TEXT, acknowledged_at TEXT, payload_json TEXT);
  `);
  db.prepare('INSERT INTO runs VALUES (?,?,?,?,?,?,?)').run('run-1', 'task-1', 'Build the thing', 'accepted', '2026-10-23T00:00:00Z', '2026-10-23T01:00:00Z', '{}');
  db.prepare('INSERT INTO waves VALUES (?,?,?,?,?,?,?,?,?,?,?)').run('wave-1', 'run-1', 1, 'local', 'abc12345', '', '', 'completed', '2026-10-23T00:00:00Z', '2026-10-23T00:30:00Z', '{}');
  db.prepare('INSERT INTO delegations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)').run('del-1', 'wave-1', null, 'CODEX:luna', 'luna', 'luna', 'gpt-test', 'high', '["src/"]', 'completed', '2026-10-23T00:01:00Z', '2026-10-23T00:20:00Z', '{}');
  db.prepare('INSERT INTO agent_lanes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)').run('lane-1', 'run-1', 'wave-1', 'impl', 'worker', 'codex', '', '', 'closed', '', 'gpt-test', 'high', '', '', '', '', '2026-10-23T00:01:00Z', '2026-10-23T00:20:00Z', '{}');
  db.prepare('INSERT INTO controller_leases VALUES (?,?,?,?,?,?,?)').run('run-1', 7, 'lease-1', 'client-a', 'released', '2026-10-23T02:00:00Z', '2026-10-23T01:00:00Z');
  db.prepare('INSERT INTO proofs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)').run('proof-1', 'run-1', 'wave-1', 'unit-tests', '1', '', 'passed', '', '2026-10-23T00:25:00Z', '2026-10-23T00:26:00Z', 1000, 0, 0, '{}', '{}');
  db.prepare('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)').run(1, 'ev-1', 'run-1', 'wave-1', null, 'wave_completed', 'running', 'completed', '2026-10-23T00:30:00Z', '{}', '', '');
  db.close();
  return root;
}

test('listRuns reads the ledger with wave and lane counts', (t) => {
  const root = fixture(t);
  const data = coordination.listRuns(root, 10);
  assert.equal(data.available, true);
  assert.equal(data.runs.length, 1);
  assert.equal(data.runs[0].runId, 'run-1');
  assert.equal(data.runs[0].waveCount, 1);
  assert.equal(data.runs[0].laneCount, 1);
});

test('runDetail joins workers, lanes, lease, proofs and activity by exact run', (t) => {
  const root = fixture(t);
  const detail = coordination.runDetail(root, 'run-1');
  assert.equal(detail.found, true);
  assert.equal(detail.workers.length, 1);
  assert.equal(detail.workers[0].owner, 'CODEX:luna');
  assert.deepEqual(detail.workers[0].scope, ['src/']);
  assert.equal(detail.lanes[0].role, 'worker');
  assert.equal(detail.lease.owner, 'client-a');
  assert.equal(detail.proofs[0].stage, 'unit-tests');
  assert.equal(detail.activity[0].type, 'wave_completed');
  const missing = coordination.runDetail(root, 'run-nope');
  assert.equal(missing.found, false);
});

test('a project without a ledger reports unavailable instead of failing', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-coord-empty-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  assert.equal(coordination.listRuns(root).available, false);
});

test('steering moves draft->saved->dispatched with a hashed capsule', (t) => {
  const root = fixture(t);
  const saved = coordination.saveSteering(root, { runId: 'run-1', text: 'Chỉ sửa module A', recipient: 'controller' });
  assert.equal(saved.state, 'saved');
  const dispatched = coordination.dispatchSteering(root, saved.id);
  assert.equal(dispatched.state, 'dispatched');
  assert.ok(dispatched.capsuleSha256 && dispatched.capsuleSha256.length === 64);
  const capsuleFile = path.join(root, dispatched.capsulePath);
  assert.ok(fs.existsSync(capsuleFile));
  const listed = coordination.listSteering(root);
  assert.equal(listed[0].state, 'dispatched');
  assert.equal(listed[0].evidence, null);
});

test('acknowledged is derived only from ledger evidence referencing the capsule', (t) => {
  const root = fixture(t);
  const saved = coordination.saveSteering(root, { runId: 'run-1', text: 'Dừng mở rộng phạm vi' });
  coordination.dispatchSteering(root, saved.id);
  const db = new DatabaseSync(path.join(root, '.coding-tools', 'orchestration', 'ledger.sqlite3'));
  db.prepare('INSERT INTO coordination_messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?)')
    .run('msg-1', 'run-1', 'wave-1', 'lane-1', 'inbound', 'steering', 'acknowledged', '', '', '2026-10-23T03:00:00Z', '2026-10-23T03:05:00Z', JSON.stringify({ capsule: saved.id }));
  db.close();
  const listed = coordination.listSteering(root);
  assert.equal(listed[0].state, 'acknowledged');
  assert.equal(listed[0].evidence.acknowledgedAt, '2026-10-23T03:05:00Z');
});

test('dispatched steering cannot be edited or re-dispatched into a new capsule', (t) => {
  const root = fixture(t);
  const saved = coordination.saveSteering(root, { runId: 'run-1', text: 'Giữ nguyên phạm vi' });
  coordination.dispatchSteering(root, saved.id);
  assert.throws(() => coordination.saveSteering(root, { id: saved.id, runId: 'run-1', text: 'Sửa lại' }), /đã dispatch/);
  const again = coordination.dispatchSteering(root, saved.id);
  assert.equal(again.capsuleSha256, coordination.listSteering(root)[0].capsuleSha256);
});
