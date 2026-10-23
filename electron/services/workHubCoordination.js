'use strict';
/*
 * Work Hub coordination (parity M2). Read model over the orchestration
 * ledger: runs, waves, delegations (workers), agent lanes, controller
 * leases, proofs and the event feed — always by exact run/wave identity.
 *
 * Steering uses an explicit state machine stored in the workspace outbox
 * (.coding-tools/work-hub-steering.json + capsule files under
 * .coding-tools/steering-outbox/):
 *   draft -> saved -> dispatched -> acknowledged -> consumed
 * 'dispatched' only means the capsule file was written (with sha256).
 * 'acknowledged' / 'consumed' are NEVER set by the UI: they are derived
 * at read time from ledger evidence (a coordination_messages row whose
 * payload references the capsule id and carries acknowledged_at, or a
 * later run that references the capsule). Without evidence the record
 * stays at 'dispatched' and is labeled as unacknowledged.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function ledgerPath(root) {
  return path.join(root, '.coding-tools', 'orchestration', 'ledger.sqlite3');
}

function openLedger(root) {
  const file = ledgerPath(root);
  if (!fs.existsSync(file)) return null;
  const { DatabaseSync } = require('node:sqlite');
  return new DatabaseSync(file, { readOnly: true, timeout: 1500 });
}

function parseJson(text) {
  try { return JSON.parse(text || '{}'); } catch { return {}; }
}

function listRuns(root, limit = 20) {
  const db = openLedger(root);
  if (!db) return { available: false, runs: [] };
  try {
    const bounded = Math.max(1, Math.min(100, Number(limit) || 20));
    const rows = db.prepare(
      `SELECT r.run_id, r.task_id, r.objective, r.status, r.started_at, r.finished_at,
              (SELECT COUNT(*) FROM waves w WHERE w.run_id = r.run_id) AS wave_count,
              (SELECT COUNT(*) FROM agent_lanes l WHERE l.run_id = r.run_id) AS lane_count
         FROM runs r ORDER BY r.started_at DESC LIMIT ?`
    ).all(bounded);
    return {
      available: true,
      runs: rows.map((r) => ({
        runId: r.run_id,
        taskId: r.task_id,
        objective: String(r.objective || '').slice(0, 240),
        status: r.status,
        startedAt: r.started_at,
        finishedAt: r.finished_at,
        waveCount: r.wave_count,
        laneCount: r.lane_count,
      })),
    };
  } finally {
    db.close();
  }
}

function runDetail(root, runId) {
  const db = openLedger(root);
  if (!db) return { available: false };
  try {
    const run = db.prepare('SELECT run_id, task_id, objective, status, started_at, finished_at FROM runs WHERE run_id = ?').get(String(runId));
    if (!run) return { available: true, found: false };
    const waves = db.prepare(
      'SELECT wave_id, ordinal, execution_mode, base_head, status, started_at, finished_at FROM waves WHERE run_id = ? ORDER BY ordinal'
    ).all(run.run_id).map((w) => ({
      waveId: w.wave_id, ordinal: w.ordinal, mode: w.execution_mode,
      baseHead: w.base_head, status: w.status, startedAt: w.started_at, finishedAt: w.finished_at,
    }));
    const workers = db.prepare(
      `SELECT d.delegation_id, d.wave_id, d.authority_owner, d.route_resolved, d.model, d.effort,
              d.allowed_scope_json, d.status, d.started_at, d.finished_at
         FROM delegations d JOIN waves w ON w.wave_id = d.wave_id WHERE w.run_id = ? ORDER BY d.started_at`
    ).all(run.run_id).map((d) => ({
      delegationId: d.delegation_id, waveId: d.wave_id, owner: d.authority_owner,
      route: d.route_resolved, model: d.model, effort: d.effort,
      scope: parseJson(d.allowed_scope_json), status: d.status,
      startedAt: d.started_at, finishedAt: d.finished_at,
    }));
    const lanes = db.prepare(
      'SELECT lane_id, wave_id, role, provider, model, effort, lifecycle FROM agent_lanes WHERE run_id = ? ORDER BY created_at'
    ).all(run.run_id).map((l) => ({
      laneId: l.lane_id, waveId: l.wave_id, role: l.role, provider: l.provider,
      model: l.model, effort: l.effort, lifecycle: l.lifecycle,
    }));
    const leaseRow = db.prepare(
      'SELECT lease_id, owner_client_id, status, expires_at, fencing_token FROM controller_leases WHERE run_id = ? ORDER BY updated_at DESC LIMIT 1'
    ).get(run.run_id);
    const proofs = db.prepare(
      `SELECT stage_id, status, exit_code, duration_ms, cache_hit, started_at
         FROM proofs WHERE run_id = ? ORDER BY started_at DESC LIMIT 30`
    ).all(run.run_id).map((p) => ({
      stage: p.stage_id, status: p.status, exitCode: p.exit_code,
      durationMs: p.duration_ms, cacheHit: Boolean(p.cache_hit), startedAt: p.started_at,
    }));
    const activity = db.prepare(
      `SELECT event_type, state_before, state_after, event_time, wave_id
         FROM events WHERE run_id = ? ORDER BY seq DESC LIMIT 40`
    ).all(run.run_id).map((e) => ({
      type: e.event_type, from: e.state_before, to: e.state_after, at: e.event_time, waveId: e.wave_id,
    })).reverse();
    const messages = db.prepare(
      `SELECT message_id, wave_id, lane_id, direction, kind, status, created_at, acknowledged_at, payload_json
         FROM coordination_messages WHERE run_id = ? ORDER BY created_at`
    ).all(run.run_id).map((m) => ({
      messageId: m.message_id, waveId: m.wave_id, laneId: m.lane_id, direction: m.direction,
      kind: m.kind, status: m.status, createdAt: m.created_at, acknowledgedAt: m.acknowledged_at,
    }));
    return {
      available: true,
      found: true,
      run: {
        runId: run.run_id, taskId: run.task_id, objective: String(run.objective || '').slice(0, 500),
        status: run.status, startedAt: run.started_at, finishedAt: run.finished_at,
      },
      waves, workers, lanes,
      lease: leaseRow ? {
        leaseId: leaseRow.lease_id, owner: leaseRow.owner_client_id, status: leaseRow.status,
        expiresAt: leaseRow.expires_at, fencingToken: leaseRow.fencing_token,
      } : null,
      proofs, activity, messages,
    };
  } finally {
    db.close();
  }
}

// ---------------- steering outbox ------------------------------------------
function outboxFile(root) {
  return path.join(root, '.coding-tools', 'work-hub-steering.json');
}

function outboxDir(root) {
  return path.join(root, '.coding-tools', 'steering-outbox');
}

function readOutbox(root) {
  try {
    const parsed = JSON.parse(fs.readFileSync(outboxFile(root), 'utf8'));
    return Array.isArray(parsed.records) ? parsed.records : [];
  } catch {
    return [];
  }
}

function writeOutbox(root, records) {
  const file = outboxFile(root);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.tmp-${process.pid}`;
  fs.writeFileSync(temp, JSON.stringify({ version: 1, records }, null, 2));
  fs.renameSync(temp, file);
}

function steeringEvidence(root, record) {
  // Evidence ladder: a coordination message for the same run whose payload
  // references this capsule id. acknowledged_at set -> acknowledged. A
  // later run whose objective/metadata references it -> consumed (checked
  // by callers through run metadata; here we only prove acknowledgement).
  const db = openLedger(root);
  if (!db) return { state: record.state, evidence: null };
  try {
    const rows = db.prepare(
      'SELECT message_id, acknowledged_at, payload_json FROM coordination_messages WHERE run_id = ?'
    ).all(record.runId);
    for (const row of rows) {
      if (String(row.payload_json || '').includes(record.id)) {
        if (row.acknowledged_at) return { state: 'acknowledged', evidence: { messageId: row.message_id, acknowledgedAt: row.acknowledged_at } };
        return { state: 'dispatched', evidence: { messageId: row.message_id, acknowledgedAt: null } };
      }
    }
    return { state: record.state, evidence: null };
  } finally {
    db.close();
  }
}

function listSteering(root) {
  return readOutbox(root).map((record) => {
    if (record.state === 'dispatched' || record.state === 'acknowledged') {
      const { state, evidence } = steeringEvidence(root, record);
      return { ...record, state, evidence };
    }
    return { ...record, evidence: null };
  });
}

function saveSteering(root, payload) {
  const text = String(payload?.text || '').trim();
  if (!text) throw new Error('Điều chỉnh trống.');
  if (text.length > 4000) throw new Error('Điều chỉnh quá dài (tối đa 4000 ký tự).');
  const runId = String(payload?.runId || '').trim();
  if (!runId) throw new Error('Chưa chọn RUN để điều chỉnh.');
  const records = readOutbox(root);
  const now = new Date().toISOString();
  const id = String(payload?.id || '').trim() || `steer-${crypto.randomBytes(6).toString('hex')}`;
  const existing = records.find((r) => r.id === id);
  if (existing) {
    if (existing.state !== 'draft' && existing.state !== 'saved') {
      throw new Error('Điều chỉnh đã dispatch — không sửa được nữa.');
    }
    existing.text = text;
    existing.state = 'saved';
    existing.updatedAt = now;
    writeOutbox(root, records);
    return existing;
  }
  const record = {
    id, runId,
    waveId: String(payload?.waveId || '').trim() || null,
    recipient: String(payload?.recipient || '').trim().slice(0, 120) || 'controller',
    text, state: 'saved', createdAt: now, updatedAt: now,
    capsulePath: null, capsuleSha256: null, dispatchedAt: null,
  };
  records.push(record);
  writeOutbox(root, records);
  return record;
}

function dispatchSteering(root, id) {
  const records = readOutbox(root);
  const record = records.find((r) => r.id === String(id));
  if (!record) throw new Error('Không tìm thấy điều chỉnh.');
  if (record.state === 'dispatched') return record;
  if (record.state !== 'saved' && record.state !== 'draft') {
    throw new Error(`Không dispatch được từ trạng thái ${record.state}.`);
  }
  const dir = outboxDir(root);
  fs.mkdirSync(dir, { recursive: true });
  const capsule = {
    version: 1, kind: 'work-hub-steering', id: record.id, run_id: record.runId,
    wave_id: record.waveId, recipient: record.recipient, text: record.text,
    created_at: record.createdAt, dispatched_at: new Date().toISOString(),
  };
  const body = JSON.stringify(capsule, null, 2);
  const file = path.join(dir, `${record.id}.json`);
  fs.writeFileSync(file, body);
  record.state = 'dispatched';
  record.capsulePath = path.relative(root, file).split(path.sep).join('/');
  record.capsuleSha256 = crypto.createHash('sha256').update(body).digest('hex');
  record.dispatchedAt = capsule.dispatched_at;
  record.updatedAt = capsule.dispatched_at;
  writeOutbox(root, records);
  return record;
}

module.exports = {
  listRuns, runDetail, listSteering, saveSteering, dispatchSteering,
  ledgerPath, outboxFile,
};
