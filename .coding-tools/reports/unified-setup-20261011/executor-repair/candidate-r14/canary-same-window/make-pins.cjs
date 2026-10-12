'use strict';
// Pin actual post-activation observations; this does not issue a MCP request.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const packet = require('../activation-windows-same-window/transition-r14.cjs');
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
function arg(name) { const values = process.argv.filter(v => v.startsWith('--' + name + '=')); need(values.length === 1, 'EXACT_PIN_INPUT_REQUIRED'); return values[0].slice(name.length + 3); }
function pinned(name) { const file = arg(name), raw = fs.readFileSync(file); need(path.isAbsolute(file) && sha(raw) === arg(name + '-sha256'), 'PINNED_INPUT_CHANGED'); return { file, sha256: sha(raw), value: JSON.parse(raw) }; }
function main() {
  const native = pinned('native-preflight'), authority = pinned('authority-receipt');
  const rows = authority.value.public_receipts || [authority.value], selected = rows.filter(v => v.phase === 'r14_same_window_read_only_observation' && v.next_phase === 'intake_reopened');
  need(selected.length === 1, 'EXACT_REOPEN_OBSERVATION_REQUIRED'); const server = selected[0];
  packet.guardServer(server, { admissions: ['scoped_pilot'] });
  need(native.value.ok === true && native.value.kind === 'r14_same_window_query_only_native_preflight'
    && native.value.package?.candidate_tag === 'workflow-timeout-1012-r14' && native.value.package?.helper_manifest_sha256 === '77ab6e95eef25874c309d6233cf0f3f855f7b8f39ed14ffe03455e55de76b389'
    && native.value.native_preflight?.cold_sandbox === true && native.value.native_preflight?.no_active_jobs === true
    && native.value.observed_at_ms <= Date.now() && Date.now() - native.value.observed_at_ms < 60000, 'FRESH_COLD_EXACT_R14_PREFLIGHT_REQUIRED');
  const approval = pinned('approval'); packet.guardApproval(approval.value, server.approval_id);
  need(/^[a-f0-9]{64}$/.test(server.next_marker_sha256) && /^[a-f0-9]{64}$/.test(authority.sha256), 'REAL_R14_AUTHORITY_MARKER_PIN_REQUIRED');
  const prepared = JSON.parse(fs.readFileSync(path.join(__dirname, 'static-preparation.json'))), probe = native.value.native_preflight;
  need(probe.preimage_sha256 === prepared.existing_preimage_sha256 && probe.checker_sha256 === prepared.checker_sha256
    && probe.old_run_sha256 === packet.oldPending[0].run_record_sha256 && probe.old_wave_sha256 === packet.oldPending[0].wave_record_sha256
    && probe.second_old_run_sha256 === packet.oldPending[1].run_record_sha256 && probe.second_old_wave_sha256 === packet.oldPending[1].wave_record_sha256,
    'EXACT_CURRENT_PREIMAGE_AND_BOTH_PENDING_REQUIRED');
  for (const key of ['activation_epoch', 'runtime_instance_id', 'mcp_server_instance_id', 'contract_version']) need(server[key] === native.value[key], 'REOPEN_NATIVE_INSTANCE_CHANGED');
  const pins = { requested_at_ms: server.requested_at_ms, expires_at_ms: server.expires_at_ms, context_id: server.context_id,
    pilot_id: server.pilot_id, service_instance_id: server.service_instance_id, activation_epoch: native.value.activation_epoch,
    runtime_instance_id: native.value.runtime_instance_id, mcp_server_instance_id: native.value.mcp_server_instance_id,
    contract_version: native.value.contract_version, native_tool_contract_sha256: native.value.native_tool_contract_sha256,
    native_preflight: { ...probe, receipt_sha256: native.sha256 }, approval_id: server.approval_id,
    authority_receipt_sha256: authority.sha256, authority_marker_sha256: server.next_marker_sha256 };
  const file = path.join(__dirname, 'pins-live-' + Date.now() + '.json');
  fs.writeFileSync(file, JSON.stringify(pins, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ok: true, pins_path: file, pins_sha256: sha(fs.readFileSync(file)), runtime_contacted: false, authority_extended: false }) + '\n');
}
if (require.main === module) { try { main(); } catch (e) { process.stdout.write(JSON.stringify({ ok: false, code: e.code || 'R14_CANARY_PINS_REFUSED', runtime_contacted: false }) + '\n'); process.exitCode = 2; } }
