'use strict';
// Guard verification only; no IPC, native lifecycle, process launch or HTTP writes.
const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const h = require('./transition-r14.cjs');
const now = h.currentAuthorityWindow.requested_at_ms + 3600000;
const state = { schema_version: 29, queued_actions: 0, accepted_actions: 0, open_writers: 0, open_tasks: 0, target_unsettled_actions: 0 };
const server = () => ({ ...h.target, ...h.currentAuthorityWindow, pilot_id: null, prior_pilot_id: h.currentAuthorityWindow.pilot_id,
  prior_pilot_revoked: true, phase: 'r14_same_window_read_only_observation', next_operation: h.activationOperation,
  next_phase: 'intake_closed', admission: 'recovery', ok: true, host: '100.116.112.22', service: 'codex-control-plane.service',
  source_revision: h.serverRevision, service_instance_id: 'cp-existing-instance', observed_at_ms: now - 1000,
  approved_window_covered: true, grant_expires_at_ms: h.currentAuthorityWindow.expires_at_ms + 1,
  capabilities: { read: true, write: true, exec: true }, state: { ...state } });
const authority = () => ({ ...server(), ...h.currentAuthorityWindow, phase: 'r13_5h_authority_renewed', approval_id: h.authorityApprovalId,
  duration_ms: h.authorityDurationMs, policy_assignment: { ...h.target, context_id: h.currentAuthorityWindow.context_id, expires_at_ms: h.currentAuthorityWindow.expires_at_ms } });
const approval = () => ({ approved: true, source: 'human_user_response', approval_id: 'call_future_test_only_approval',
  operation: h.activationOperation, candidate_tag: 'workflow-timeout-1012-r14', target: { ...h.target },
  context_id: h.currentAuthorityWindow.context_id, expires_at_ms: h.currentAuthorityWindow.expires_at_ms,
  approved_at_ms: now - 1, r13_owned_executor_cleanup_refresh: true, pilot_replacement_same_principal_binding_expiry: true, new_approved_patch_verification_canary: true,
  authority_extension: false, ubuntu_deploy_or_restart: false, windows_reboot: false, semantic_acceptance: false });
const refused = (fn, code) => assert.throws(fn, e => e.code === code);
test('existing authority is preserved with original context and expiry', () => {
  assert.equal(h.guardAuthority(authority(), h.guardServer(server(), { now }), now).expires_at_ms, 1791776571067);
});
test('authority extension, context replacement and unbound assignment are refused', () => {
  for (const patch of [{ expires_at_ms: h.currentAuthorityWindow.expires_at_ms + 1 }, { context_id: 'ctx_other' },
    { service_instance_id: 'cp-other' }, { approval_id: 'call_other' }]) refused(() => h.guardAuthority({ ...authority(), ...patch }, server(), now), 'EXACT_EXISTING_AUTHORITY_WINDOW_REQUIRED');
  const a = authority(); a.policy_assignment.root = 'E:\\Elsewhere'; refused(() => h.guardAuthority(a, server(), now), 'EXACT_EXISTING_AUTHORITY_WINDOW_REQUIRED');
});
test('fresh closure must prove prior pilot revoked and zero central work', () => {
  for (const patch of [{ prior_pilot_revoked: false }, { observed_at_ms: now - 60000 }, { admission: 'open' },
    { expires_at_ms: h.currentAuthorityWindow.expires_at_ms + 1 }]) refused(() => h.guardServer({ ...server(), ...patch }, { now }), 'FRESH_EXACT_SERVER_RECEIPT_REQUIRED');
  refused(() => h.guardServer({ ...server(), pilot_id: h.currentAuthorityWindow.pilot_id }, { now }), 'REVOKED_PILOT_MUST_NOT_BE_REUSED');
  refused(() => h.guardServer({ ...server(), state: { ...state, open_tasks: 1 } }, { now }), 'SERVER_NOT_QUIESCENT_OR_SCHEMA_CHANGED');
});
test('replacement pilot and reopen require same binding principal and expiry', () => {
  const s = { ...server(), next_phase: 'intake_reopened', admission: 'scoped_pilot', pilot_id: 'pilot_0123456789abcdef0123456789abcdef',
    replacement_pilot_same_principal: true, replacement_pilot_same_binding: true, replacement_pilot_expires_at_ms: h.currentAuthorityWindow.expires_at_ms };
  h.guardServer(s, { now, admissions: ['recovery', 'scoped_pilot'] });
  for (const patch of [{ replacement_pilot_same_principal: false }, { replacement_pilot_same_binding: false },
    { replacement_pilot_expires_at_ms: s.replacement_pilot_expires_at_ms + 1 }, { pilot_id: h.currentAuthorityWindow.pilot_id }]) refused(() => h.guardServer({ ...s, ...patch }, { now, admissions: ['recovery', 'scoped_pilot'] }), 'EXACT_SAME_WINDOW_REPLACEMENT_PILOT_REQUIRED');
});
test('future r14 approval is separate from previous r13 authority approval', () => {
  h.guardApproval(approval(), approval().approval_id, now);
  for (const id of [h.authorityApprovalId, h.originalApprovalId, 'unapproved']) refused(() => h.guardApproval({ ...approval(), approval_id: id }, id, now), 'EXPLICIT_FUTURE_R14_APPROVAL_REQUIRED');
  for (const patch of [{ approved: false }, { r13_owned_executor_cleanup_refresh: false }, { pilot_replacement_same_principal_binding_expiry: false }, { new_approved_patch_verification_canary: false },
    { authority_extension: true }, { windows_reboot: true }, { ubuntu_deploy_or_restart: true }, { semantic_acceptance: true }]) refused(() => h.guardApproval({ ...approval(), ...patch }, approval().approval_id, now), 'EXPLICIT_FUTURE_R14_APPROVAL_REQUIRED');
});
test('existing authority requires at least twelve minutes at effect boundary', () => {
  const at = h.currentAuthorityWindow.expires_at_ms - h.minimumWindowMs;
  h.guardAuthority(authority(), server(), at);
  refused(() => h.guardAuthority(authority(), server(), at + 1), 'EXACT_EXISTING_AUTHORITY_WINDOW_REQUIRED');
});
test('census preserves both pending RUNs and refuses active Jobs or omitted history', () => {
  const c = { mutated_canonical_ledger: false, content_free: true, safe: false, code: 'RUNTIME_BUSY',
    snapshot: { query_only: true, immutable: true, integrity_check: ['ok'], foreign_key_check_rows: 0 },
    lifecycle: { awaiting_acceptance_runs: h.oldPending.map(f => f.run_id), projection_drift: false, live_owned_runs: [],
      unexplained_active_runs: 0, unbound_live_resource_residues: 0, blockers: ['live_runtime_state_process'] },
    counts: { active_tool_calls: 0, active_commands: 0, starting_commands: 0, active_background_operations: 0,
      active_managed_processes: 0, foreign_heavy_processes: 0, active_agent_lanes: 0 } };
  h.assertCensus(c); const active = structuredClone(c); active.counts.active_managed_processes = 1;
  refused(() => h.assertCensus(active), 'CANONICAL_CENSUS_NOT_QUIESCENT');
  const omitted = structuredClone(c); omitted.lifecycle.awaiting_acceptance_runs.pop(); refused(() => h.assertCensus(omitted), 'CANONICAL_CENSUS_NOT_QUIESCENT');
});
test('all existing policy hashes including metadata are preserved', () => {
  const before = Object.fromEntries(['ReadOnly','FileRead','ApprovedPatch','Exec'].map(k => [k, { file_sha256: k }]));
  h.guardUnchangedPolicies(before, structuredClone(before));
  for (const kind of Object.keys(before)) { const drift = structuredClone(before); drift[kind].file_sha256 = 'other'; refused(() => h.guardUnchangedPolicies(drift, before), 'PINNED_EXISTING_POLICY_CHANGED'); }
});
test('r14 agent is bounded to remaining authority and never zero', () => {
  assert.equal(h.boundedAgentIterations(now + 150000, now), 9);
  assert.equal(h.boundedAgentIterations(now + 18000000, now), 1199);
  refused(() => h.boundedAgentIterations(now + 15000, now), 'NO_BOUNDED_AGENT_WINDOW');
});
test('actual existing renewal fits unchanged-authority guard', () => {
  const file = path.join(__dirname, '../../candidate-r13/authority-5h/remote-receipts/renew-20261011T224251426341Z.json');
  const n = h.publicReceipt(JSON.parse(fs.readFileSync(file, 'utf8'))), s = server(); s.service_instance_id = n.service_instance_id;
  h.guardAuthority(n, s, now);
});
