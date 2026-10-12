'use strict';
// Produces reviewable helpers only. Does not invoke a helper mutation phase.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const repo = 'E:\\Github\\Tools-Codex-web';
const priorDir = path.join(__dirname, '../../candidate-r13/activation-windows-5h');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const writeNew = (name, text) => fs.writeFileSync(path.join(__dirname, name), text, { flag: 'wx' });
const replace = (text, from, to) => { if (!text.includes(from)) throw new Error('PREPARATION_ANCHOR_MISSING'); return text.replace(from, to); };
let s = fs.readFileSync(path.join(priorDir, 'transition-r13.cjs'), 'utf8').replaceAll('\r\n', '\n').replaceAll('r13', 'r14').replaceAll('r12', 'r13').replaceAll('R13', 'R14').replaceAll('R12', 'R13');
s = replace(s, "const previousAuthorityWindow = { context_id: 'ctx_d7a539dd85264a62951fddad0ffa2f23', pilot_id: 'pilot_98c0b502568a4f888b3106838004c117', requested_at_ms: 1791747735200, expires_at_ms: 1791751335200 };", "const currentAuthorityWindow = { context_id: 'ctx_1e7e2fec6f0e43018db7a51c6980e5c2', pilot_id: 'pilot_b1cb26c319fb489aae24d3b746318447', requested_at_ms: 1791758571067, expires_at_ms: 1791776571067 };");
s = replace(s, "const renewalApprovalId = 'call_a60e931056bd402b997c6c10b0796d81';", "const authorityApprovalId = 'call_a60e931056bd402b997c6c10b0796d81';");
s = replace(s, "const renewalOperation = 'owner_approved_r14_initial_verification_5h';", "const activationOperation = 'owner_approved_r14_same_window_activation';");
s = replace(s, "const tags = { r13: 'policy-contract-1012-r13', r14: 'source-fingerprint-1012-r14' };", "const tags = { r13: 'source-fingerprint-1012-r13', r14: 'workflow-timeout-1012-r14' };");
s = replace(s, "const oldPending = { run_id: '95e909f0040a448faa9f1f3257e2ee2c', wave_id: 'c101beadfc6d4f2fbc13845052c84693',\n  run_record_sha256: 'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590', wave_record_sha256: '59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce' };", "const oldPending = [\n  { run_id: '95e909f0040a448faa9f1f3257e2ee2c', wave_id: 'c101beadfc6d4f2fbc13845052c84693', run_record_sha256: 'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590', wave_record_sha256: '59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce' },\n  { run_id: 'fbaf4b0700d04794af4062671c1bcd2b', wave_id: 'e712eca9463e465fb1905264c998f50c', run_record_sha256: '6a66aac3bf8d389938a0b4284b487378c180ce7bfca9cf1d5f754fc20077a2ca', wave_record_sha256: '3d2c5310ba6e9d91d32ba09c3d2b191c722cc0fe550b25cba371650e360a2b4d' }\n];");
s = replace(s, '/^r14-5h-[A-Za-z0-9_-]{8,80}$/', '/^r14-same-window-[A-Za-z0-9_-]{8,80}$/');
s = replace(s, "../candidate-parity-20261011T200058268Z.json", "../candidate-parity-20261011T231029495Z.json");
s = replace(s, '7c2c60851359f619472bbfafb649529b3eaae90ee6a4626a724c401b91323b88', '59e4a0af303424a42db59831f83e8205420f6143a446f530bd9a9a272d4ae51a');
s = replace(s, 'e9351a360eaa7c016514015a27ea06c762604e12c2a5ca436a550abbf09f29ff', 'a618711528b418db77a901a5b83537bde2d511618ef630ab22670a2e6579625d');
s = replace(s, "sha(pathsFor('r14').appRoot()) === '2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1'", "sha(pathsFor('r14').appRoot()) === 'f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324'");
s = replace(s, "sha(pathsFor('r14').executablePath()) === '797d4d00d855c05da17117471816ebafc7e2b3397d09c738eea49cf7368bfbb8'", "sha(pathsFor('r14').executablePath()) === '8270535a8149b54527172f9b774ea1fd6ed975fde44e4bb91022bdde31dea154'");
const guardStart = s.indexOf('function guardServer('), guardEnd = s.indexOf("const ps =", guardStart);
if (guardStart < 0 || guardEnd < 0) throw new Error('GUARD_ANCHOR_MISSING');
s = s.slice(0, guardStart) + `function guardServer(s, { now = Date.now(), admissions = ['recovery'] } = {}) {
  need(s.ok === true && s.host === '100.116.112.22' && s.service === 'codex-control-plane.service' && s.source_revision === serverRevision
    && /^[A-Za-z0-9_.:-]+$/.test(s.service_instance_id || '') && s.binding_id === target.binding_id && admissions.includes(s.admission)
    && s.phase === 'r14_same_window_read_only_observation' && s.next_operation === activationOperation
    && (s.admission === 'recovery' ? ['intake_closed', 'pilot_replaced'].includes(s.next_phase) : s.next_phase === 'intake_reopened')
    && s.context_id === currentAuthorityWindow.context_id && s.requested_at_ms === currentAuthorityWindow.requested_at_ms
    && s.expires_at_ms === currentAuthorityWindow.expires_at_ms && s.prior_pilot_id === currentAuthorityWindow.pilot_id
    && s.prior_pilot_revoked === true && s.approved_window_covered === true && s.grant_expires_at_ms >= currentAuthorityWindow.expires_at_ms
    && ['device_id', 'workspace_id', 'workspace_generation', 'profile'].every(k => s[k] === target[k])
    && typeof s.root === 'string' && path.isAbsolute(s.root) && key(s.root) === key(repo)
    && ['read', 'write', 'exec'].every(k => s.capabilities?.[k] === true)
    && Number.isSafeInteger(s.observed_at_ms) && now - s.observed_at_ms >= 0 && now - s.observed_at_ms < 60000, 'FRESH_EXACT_SERVER_RECEIPT_REQUIRED');
  need(s.state?.schema_version === 29 && ['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks', 'target_unsettled_actions'].every(k => s.state[k] === 0), 'SERVER_NOT_QUIESCENT_OR_SCHEMA_CHANGED');
  if (s.next_phase === 'intake_closed') need(s.pilot_id === null, 'REVOKED_PILOT_MUST_NOT_BE_REUSED');
  else need(/^pilot_[a-f0-9]{32}$/.test(s.pilot_id || '') && s.pilot_id !== currentAuthorityWindow.pilot_id && s.replacement_pilot_same_principal === true
    && s.replacement_pilot_same_binding === true && s.replacement_pilot_expires_at_ms === currentAuthorityWindow.expires_at_ms, 'EXACT_SAME_WINDOW_REPLACEMENT_PILOT_REQUIRED');
  return s;
}
function guardAuthority(n, s, now = Date.now()) {
  need(n.ok === true && n.source_revision === serverRevision && n.host === s.host && n.service === s.service && n.service_instance_id === s.service_instance_id
    && n.phase === 'r13_5h_authority_renewed' && n.approval_id === authorityApprovalId && n.binding_id === target.binding_id
    && ['context_id', 'requested_at_ms', 'expires_at_ms', 'pilot_id'].every(k => n[k] === currentAuthorityWindow[k])
    && n.duration_ms === authorityDurationMs && n.expires_at_ms - now >= minimumWindowMs
    && n.approved_window_covered === true && n.grant_expires_at_ms >= n.expires_at_ms
    && ['device_id', 'workspace_id', 'workspace_generation', 'profile'].every(k => n[k] === target[k])
    && typeof n.root === 'string' && key(n.root) === key(repo)
    && n.policy_assignment?.context_id === n.context_id && n.policy_assignment?.expires_at_ms === n.expires_at_ms
    && ['binding_id', 'device_id', 'workspace_id', 'workspace_generation', 'profile'].every(k => n.policy_assignment[k] === target[k])
    && key(n.policy_assignment.root) === key(repo), 'EXACT_EXISTING_AUTHORITY_WINDOW_REQUIRED');
  return n;
}
function guardApproval(a, approvalId, now = Date.now()) {
  need(a.approved === true && a.source === 'human_user_response' && /^call_[A-Za-z0-9_-]+$/.test(approvalId || '')
    && ![authorityApprovalId, originalApprovalId].includes(approvalId) && a.approval_id === approvalId
    && a.operation === activationOperation && a.candidate_tag === tags.r14
    && a.context_id === currentAuthorityWindow.context_id && a.expires_at_ms === currentAuthorityWindow.expires_at_ms
    && a.pilot_replacement_same_principal_binding_expiry === true && a.authority_extension === false
    && a.ubuntu_deploy_or_restart === false && a.windows_reboot === false && a.semantic_acceptance === false
    && equal(a.target, target) && Number.isSafeInteger(a.approved_at_ms) && a.approved_at_ms <= now && now < a.expires_at_ms, 'EXPLICIT_FUTURE_R14_APPROVAL_REQUIRED');
  return a;
}
function mutationGuard() {
  verifyCandidate(); need(process.argv.includes('--operator-approved-r14-same-window'), 'EXPLICIT_R14_APPROVAL_REQUIRED');
  need(sha(path.join(__dirname, 'helper-manifest.json')) === arg('manifest-sha256'), 'HELPER_MANIFEST_CHANGED');
  need(!fs.existsSync(path.join(dataRoot, 'recovery-supervisor/manifest.json')) && !fs.existsSync('C:\\\\Users\\\\daoth\\\\AppData\\\\Local\\\\WebMcpRecoverySupervisor\\\\manifest.json'), 'INSTALLED_SUPPORTED_SUPERVISOR_REQUIRES_RECONCILIATION');
  guardApproval(pinned('approval'), arg('approval-id')); const s = guardServer(pinned('server')); return guardAuthority(pinned('authority'), s);
}
` + s.slice(guardEnd);
const pendingStart = s.indexOf('const pendingCode ='), pendingEnd = s.indexOf('function assertCensus(', pendingStart);
s = s.slice(0, pendingStart) + `const pendingCode = \`import hashlib,json,sqlite3,sys\\nfrom pathlib import Path\\nfrom contextlib import closing\\nresult=[]\\nwith closing(sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True,timeout=10)) as d:\\n d.row_factory=sqlite3.Row;d.execute("PRAGMA query_only=ON");d.execute("BEGIN")\\n for f in json.loads(sys.argv[2]):\\n  record=dict(f)\\n  for t,c,field in (("runs","run_id","run_record_sha256"),("waves","wave_id","wave_record_sha256")):\\n   rows=d.execute(f"SELECT * FROM {t} WHERE {c}=?",(f[c],)).fetchall()\\n   if len(rows)!=1:raise SystemExit(2)\\n   record[field]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\\n  result.append(record)\\n d.rollback()\\nprint(json.dumps(result))\`;
function pending(paths) { const r = spawnSync(paths.portablePython(), ['-B', '-I', '-c', pendingCode, path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), JSON.stringify(oldPending)], { windowsHide: true, shell: false, timeout: 15000, encoding: 'utf8', maxBuffer: 8192 }); need(!r.error && r.status === 0, 'QUERY_ONLY_PENDING_READ_FAILED'); need(equal(JSON.parse(r.stdout), oldPending), 'HISTORICAL_PENDING_CHANGED'); return { families: oldPending, unchanged: true, query_only: true }; }
` + s.slice(pendingEnd);
s = replace(s, 'equal(c.lifecycle.awaiting_acceptance_runs, [oldPending.run_id])', 'equal([...c.lifecycle.awaiting_acceptance_runs].sort(), oldPending.map(f => f.run_id).sort())');
s = replace(s, 'equal(p.pending_acceptance, { ...oldPending, unchanged: true, query_only: true })', 'equal(p.pending_acceptance, { families: oldPending, unchanged: true, query_only: true })');
s = replace(s, "const packageProof = verifyCandidate(), o = await observed('r13'), runtime = await runtimeObservation(o), c = await census(o);", "const packageProof = verifyCandidate(), o = await observed('r13'), runtime = await runtimeObservation(o), c = await census(o); need(o.owner.pid === 11476 && runtime.agent.identity.pid === 10396 && runtime.agent.identity.state === 'live' && runtime.agent.last_iteration_state === 'completed', 'FRESH_EXACT_OLD_HOST_AGENT_REQUIRED');");
s = replace(s, "function launchLeaf(kind, n, intentFile, maxIterations = null) { mutationGuard(); const argv =", "function launchLeaf(kind, n, intentFile, maxIterations = null) { mutationGuard(); const argv =");
s = replace(s, "'-OperatorApprovedR14FiveHours'", "'-OperatorApprovedR14SameWindow'");
s = replace(s, "'-RenewalReceipt', arg('renewal'), '-RenewalSha256', arg('renewal-sha256')", "'-AuthorityReceipt', arg('authority'), '-AuthoritySha256', arg('authority-sha256'), '-ApprovalReceipt', arg('approval'), '-ApprovalSha256', arg('approval-sha256')");
const policyStart = s.indexOf('async function policySync()'), policyEnd = s.indexOf('async function startAgent()', policyStart);
s = s.slice(0, policyStart) + `async function policySync() {
  const n = mutationGuard(), o = await currentR14(), c = await census(o), p = oldPin(); pending(o.paths); zeroVm();
  const current = guardUnchangedPolicies(policySnapshot(o.paths), p.policies);
  need(current.ReadOnly.value.expires_at_ms === n.expires_at_ms && ['FileRead', 'ApprovedPatch', 'Exec'].every(k => current[k].value.authority_mode === 'standing' && current[k].value.expires_at_ms === null), 'UNCHANGED_EXISTING_POLICIES_REQUIRED');
  await reserve('policy', { validation_only: true, context_id: n.context_id, authority_expires_at_ms: n.expires_at_ms });
  emit({ phase: 'r14_policies_synced', ok: true, authority_expires_at_ms: n.expires_at_ms, authority_context_id: n.context_id,
    policies: Object.fromEntries(Object.entries(current).map(([k, v]) => [k, { file_sha256: v.file_sha256, facade_contract: v.value.facade_contract }])),
    census: censusSummary(c), pending_acceptance: pending(o.paths), read_only_policy_renewed: false, standing_policy_hashes_preserved: true,
    standing_policies_reinstalled: false, no_new_sandbox_probe: true, runtime_mutated: false });
}
` + s.slice(policyEnd);
s = replace(s, 'explicit r14 source fingerprint activation under approved five-hour authority with pending history preserved', 'explicit r14 initial workflow timeout activation under unchanged authority window with both pending families preserved');
s = replace(s, "const s = guardServer(pinned('server'), { admissions: ['recovery', 'scoped_pilot'] }), n = guardRenewal(pinned('renewal'), s, Date.now(), arg('approval-id'))", "guardApproval(pinned('approval'), arg('approval-id')); const s = guardServer(pinned('server'), { admissions: ['recovery', 'scoped_pilot'] }), n = guardAuthority(pinned('authority'), s)");
s = s.replace(/module\.exports = \{[^\n]+\};/, "module.exports = { guardServer, guardAuthority, guardApproval, guardUnchangedPolicies, boundedAgentIterations, assertCensus, standingPolicyDigest, target, facade, serverRevision, oldPending, currentAuthorityWindow, authorityDurationMs, authorityApprovalId, activationOperation, maximumAgentIterations, originalApprovalId, minimumWindowMs, pathsFor, publicReceipt, canonical, psEnvironment, verifyCandidate };");
// Remove obsolete renewal helpers so the packet has one unchanged-policy path.
s = s.replace(/function guardPolicyRenewal\([^\n]+\n/, '').replace(/function guardReplacement\([^\n]+\n/, '');
writeNew('transition-r14.cjs', s);
writeNew('query-job.py', fs.readFileSync(path.join(priorDir, 'query-job.py'), 'utf8'));
process.stdout.write(JSON.stringify({ ok: true, generated: ['transition-r14.cjs', 'query-job.py'], runtime_mutated: false, server_mutated: false }) + '\n');
