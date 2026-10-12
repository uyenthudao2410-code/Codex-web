'use strict';
// Root-only evidence preparation. No IPC, process control, policy or authority effect.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const BASE = path.resolve(__dirname, '../activation-windows-same-window');
const PRIOR = path.join(BASE, 'attempts/r14-same-window-20261012_070300');
const BASE_SHA = 'b875e90526322528ae4406492b7915ed9ce049a28943d9c5f661e26fd07e0d74';
const MANIFEST_SHA = '77ab6e95eef25874c309d6233cf0f3f855f7b8f39ed14ffe03455e55de76b389';
const INTENT_SHA = 'd0db4ec785c36742319c3b4f1728b2ce673640eddf688dc69e61f8208d252389';
const PIN_SHA = '97148905848cefc3087e10c58e21b8f26755ed425a53abb280c7c2838ff45e74';
const APPROVAL_ID = 'call_VVCZ5vN5tTi8XytTvFyQyHY0';
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
const canonical = value => JSON.stringify(value, (_, item) => item && typeof item === 'object' && !Array.isArray(item)
  ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
function arg(name) { const rows = process.argv.filter(v => v.startsWith('--' + name + '=')); need(rows.length === 1, 'EXACT_PUBLIC_INPUT_REQUIRED'); return rows[0].slice(name.length + 3); }
function pinned(name) { const file = arg(name); need(path.isAbsolute(file), 'ABSOLUTE_INPUT_REQUIRED'); const raw = fs.readFileSync(file); need(sha(raw) === arg(name + '-sha256'), 'PUBLIC_RECEIPT_PIN_CHANGED'); return { file, sha256: sha(raw), value: JSON.parse(raw) }; }
function immutable(file, raw) { fs.writeFileSync(file, raw, { flag: 'wx' }); }
function main() {
  need(process.argv.includes('--prepare-reconciled-attempt'), 'EXPLICIT_ROOT_PREPARATION_REQUIRED');
  need(sha(fs.readFileSync(path.join(BASE, 'transition-r14.cjs'))) === BASE_SHA
    && sha(fs.readFileSync(path.join(BASE, 'helper-manifest.json'))) === MANIFEST_SHA, 'FROZEN_PACKET_CHANGED');
  const base = require(path.join(BASE, 'transition-r14.cjs'));
  const approval = pinned('approval'), server = pinned('server'), reconciliation = pinned('reconciliation');
  base.guardApproval(approval.value, APPROVAL_ID);
  const central = base.publicReceipt(server.value); base.guardServer(central);
  need(central.next_phase === 'intake_closed', 'EXACT_CLOSED_INTAKE_REQUIRED');
  const intentRaw = fs.readFileSync(path.join(PRIOR, 'activate-intent.json'));
  const pinRaw = fs.readFileSync(path.join(PRIOR, 'post-cleanup-pin.json'));
  need(sha(intentRaw) === INTENT_SHA && sha(pinRaw) === PIN_SHA, 'ORIGINAL_REFUSAL_INPUT_CHANGED');
  const intent = JSON.parse(intentRaw), old = JSON.parse(pinRaw), current = base.publicReceipt(reconciliation.value);
  const journalRaw = fs.readFileSync(path.join(PRIOR, 'transition.jsonl'));
  need(journalRaw.length < 2 * 1024 * 1024, 'PRIOR_JOURNAL_TOO_LARGE');
  const records = journalRaw.toString('utf8').trimEnd().split('\n').map(raw => ({ raw, value: JSON.parse(raw) }));
  const requests = records.filter(row => row.value.phase === 'r13_owned_cleanup_requested');
  const reserves = records.filter(row => row.value.phase === 'activate');
  const refusals = records.filter(row => row.value.ok === false && row.value.code === 'EXACT_OLD_AGENT_NOT_QUIESCENT');
  need(requests.length === 1 && reserves.length === 1 && refusals.length === 1
    && canonical(reserves[0].value) === canonical(intent)
    && refusals[0].value.helper_sha256 === BASE_SHA && refusals[0].value.observed_at_ms === 1791763748218
    && records.indexOf(refusals[0]) === records.indexOf(reserves[0]) + 1
    && records.slice(records.indexOf(refusals[0]) + 1).every(row => row.value.phase === 'r13_owned_cleanup_completed'),
    'ORIGINAL_PRE_EFFECT_REFUSAL_NOT_EXACT');
  const actual = records.filter(row => canonical(row.value) === canonical(current));
  const now = Date.now(), c = current.census;
  need(actual.length === 1 && current.phase === 'r13_owned_cleanup_completed' && current.ok === true
    && current.helper_sha256 === BASE_SHA && current.observed_at_ms <= now && now - current.observed_at_ms < 60000
    && current.supported_owned_manager_cleanup === true && current.direct_vm_termination === false
    && current.runtime_mutated === false && current.server_mutated === false && current.authority_extended === false
    && ['owner', 'native'].every(k => canonical(current[k]) === canonical(old[k]))
    && canonical(current.descriptor) === canonical(old.descriptor) && canonical(current.ui) === canonical(old.ui)
    && canonical(current.agent?.identity) === canonical(old.agent.identity)
    && current.agent?.agent_instance_id === old.agent.agent_instance_id
    && current.agent.agent_started_at_ms === old.agent.agent_started_at_ms
    && current.agent.last_iteration_state === 'completed' && current.agent.last_heartbeat_state === 'succeeded'
    && current.agent.last_error_code === null && current.agent.last_error_scope === null
    && current.agent.last_heartbeat_at_ms <= now && now - current.agent.last_heartbeat_at_ms < 60000
    && current.epoch?.state === 'READY' && current.epoch.admission_open === true && current.epoch.update_incomplete === false
    && current.epoch.activation_epoch_id === requests[0].value.activation_epoch_id
    && current.native_identity?.identity_current === true && current.native_identity.mcp_ready === true
    && current.native_identity.activation_epoch_id === current.epoch.activation_epoch_id
    && current.native_identity.current_activation_epoch_id === current.epoch.activation_epoch_id
    && ['mcp_process_instance_id', 'mcp_server_instance_id', 'tool_contract_sha256', 'recovery_host_instance_id'].every(k => current.native_identity[k] === old.native_identity[k])
    && current.readiness?.fullyReady === true && current.readiness.centralConnected === true
    && current.readiness.authorityReady === true && current.readiness.updateIncomplete === false
    && canonical(current.pending_acceptance) === canonical(old.pending_acceptance)
    && current.vm_zero?.content_free === true && current.vm_zero.host_count === 0 && current.vm_zero.backend_count === 0
    && c?.content_free === true && c.canonical_mutated === false && c.snapshot?.query_only === true && c.snapshot.immutable === true
    && canonical(c.snapshot.integrity_check) === '["ok"]'
    && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes'].every(k => c.counts[k] === 0)
    && c.lifecycle?.projection_drift === false && c.lifecycle.live_owned_runs.length === 0
    && c.lifecycle.unexplained_active_runs === 0 && c.lifecycle.unbound_live_resource_residues === 0
    && canonical([...c.lifecycle.awaiting_acceptance_runs].sort()) === canonical(base.oldPending.map(v => v.run_id).sort()),
    'FRESH_AUTHENTIC_UNCHANGED_NO_EFFECT_RECONCILIATION_REQUIRED');
  const profile = base.pathsFor('r13');
  for (const kind of ['ReadOnly', 'FileRead', 'ApprovedPatch', 'Exec']) need(sha(fs.readFileSync(profile['controlPlane' + kind + 'PolicyFile']())) === old.policies[kind].file_sha256, 'EXISTING_POLICY_CHANGED');
  const name = arg('new-attempt'); need(/^r14-same-window-[A-Za-z0-9_-]{8,80}$/.test(name) && name !== path.basename(PRIOR), 'NEW_EXCLUSIVE_ATTEMPT_REQUIRED');
  const destination = path.join(BASE, 'attempts', name); need(!fs.existsSync(destination), 'NEW_ATTEMPT_ALREADY_EXISTS_NO_REPLAY');
  const provenance = { phase: 'r14_attempt_reconciled_before_first_activation_effect', observed_at_ms: now,
    helper_sha256: sha(fs.readFileSync(__filename)), original_attempt: path.basename(PRIOR), new_attempt: name,
    original_journal_sha256: sha(journalRaw), original_activate_intent_sha256: INTENT_SHA,
    original_post_cleanup_pin_sha256: PIN_SHA, original_refusal_record_sha256: sha(Buffer.from(refusals[0].raw)),
    retained_cleanup_request_record_sha256: sha(Buffer.from(requests[0].raw)), retained_cleanup_completed_record_sha256: sha(Buffer.from(actual[0].raw)),
    approval_id: APPROVAL_ID, approval_receipt_sha256: approval.sha256, server_receipt_sha256: server.sha256,
    reconciliation_receipt_sha256: reconciliation.sha256, original_packet_sha256: MANIFEST_SHA,
    original_activation_effects_observed: false, cleanup_refresh_repeated: false, runtime_mutated: false, server_mutated: false,
    original_intents_preserved: true, authority_extended: false, semantic_acceptance_performed: false };
  fs.mkdirSync(destination); immutable(path.join(destination, 'reconciled-attempt-provenance.json'), JSON.stringify(provenance, null, 2) + '\n');
  immutable(path.join(destination, 'transition.jsonl'), requests[0].raw + '\n' + actual[0].raw + '\n' + JSON.stringify(provenance) + '\n');
  process.stdout.write(JSON.stringify({ ok: true, phase: provenance.phase, new_attempt: name, attempt_directory: destination,
    provenance_sha256: sha(fs.readFileSync(path.join(destination, 'reconciled-attempt-provenance.json'))),
    journal_sha256: sha(fs.readFileSync(path.join(destination, 'transition.jsonl'))), original_packet_sha256: MANIFEST_SHA,
    cleanup_refresh_repeated: false, runtime_mutated: false, server_mutated: false, guard_weakened: false }) + '\n');
}
if (require.main === module) { try { main(); } catch (e) { process.stdout.write(JSON.stringify({ ok: false,
  code: /^[A-Z0-9_]{1,128}$/.test(e.code || '') ? e.code : 'RECONCILED_ATTEMPT_PREPARATION_REFUSED',
  runtime_mutated: false, server_mutated: false, original_intents_preserved: true, no_automatic_retry: true }) + '\n'); process.exitCode = 2; } }
