'use strict';
// Additive continuation of the exact documented full-clean handoff. Root executes.
// Frozen v2 bytes stay unchanged. No restart, metadata/authority change or replay.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const helper = path.join(__dirname, 'activate-r10-v2.cjs');
const historicalJournal = path.join(__dirname, 'windows-activation-v2.jsonl');
const journal = path.join(__dirname, 'windows-handoff-continuation.jsonl');
const expectedHelper = '4b689f8533f1de77130257543b408aec43b3f91e79579015a7a10a054db06b05';
const expectedJournal = '4213950067cc15136df9dfd4da95978c5d216f47754ac37464367da7ab2a24b3';
const expectedEpoch = 'activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba';
const expectedOperation = 'full-clean-mv3tmvoi-424499179795d11e85d23af6';
const installation = '36cd3af6fe1da4607cfe3035d48becd97dc12265901b480401bf44389ff1d1dc';
const previous = { pid: 24760, process_start_token: '134361965753174000', instance_id: '96b17ff815a3028b43929ddf0e3b212e' };
const replacement = { pid: 14516, process_start_token: '134361966532424140', instance_id: '683d283f8174b82d1c906d53fd41e190' };
const ui = { pid: 15660, process_start_token: '134361966677348870', instance_id: 'b007c2e1e77e2e79f2c9ae023511ad31' };
const native = { pid: 6064, process_start_token: '134361966557949550' };
const revisions = { coding: '61b291bb0c3a31ec793a7301fd6e95096372757e50a2e7dfff84fa4758740995', ui: 'a6cde0058d937525b6c937a330c60fe3802faa4f1f3ec78c252dd3e9fa87db6f', host: '5e0b6a773f4296211dee1460ee2862016c909bfc5888b35e8c1a469931322150' };
const fail = code => { throw Object.assign(new Error(), { code }); };
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const safeCode = value => String(value || '').replace(/[^a-zA-Z0-9_.:-]/g, '').slice(0, 128);
function emit(value) {
  const row = { observed_at: new Date().toISOString(), continuation_helper_sha256: sha(__filename), ...value };
  fs.appendFileSync(journal, `${JSON.stringify(row)}\n`);
  process.stdout.write(`${JSON.stringify(row)}\n`);
  return row;
}
function rows(file) {
  return fs.existsSync(file) ? fs.readFileSync(file, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse) : [];
}
function historicalGuard() {
  if (sha(helper) !== expectedHelper || sha(historicalJournal) !== expectedJournal) fail('FROZEN_V2_HELPER_OR_HANDOFF_JOURNAL_CHANGED');
  const history = rows(historicalJournal);
  const started = history.findLast(row => row.phase === 'candidate_started' && row.tag === 'r10');
  const handoff = history.findLast(row => row.phase === 'refresh' && row.tag === 'r10');
  const seen = history.findLast(row => row.phase === 'status' && row.tag === 'r10');
  if (!started || !handoff || !seen || started.descriptor.installation_id !== installation
    || started.descriptor.instance_id !== previous.instance_id || started.owner.pid !== previous.pid || started.owner.process_start_token !== previous.process_start_token
    || handoff.state !== 'HANDOFF' || handoff.epoch !== expectedEpoch || handoff.pending_acceptance?.unchanged !== true
    || seen.descriptor.installation_id !== installation || seen.descriptor.instance_id !== replacement.instance_id
    || seen.owner.pid !== replacement.pid || seen.owner.process_start_token !== replacement.process_start_token
    || seen.epoch.activation_epoch_id !== expectedEpoch || seen.ui.instance_id !== ui.instance_id || seen.ui.identity.pid !== ui.pid || seen.ui.identity.process_start_token !== ui.process_start_token
    || seen.components.native.pid !== native.pid || seen.components.native.process_start_token !== native.process_start_token
    || Date.parse(handoff.observed_at) <= Date.parse(started.observed_at) || Date.parse(seen.observed_at) <= Date.parse(handoff.observed_at)) fail('EXACT_DOCUMENTED_R10_HANDOFF_REQUIRED');
}
// Load the pinned helper in memory under its original filename, suppressing its
// CLI main only. Hooks redirect evidence and replace the obsolete pre-handoff
// currentR10 pin. Original authorization/package/policy/census guards are reused.
historicalGuard();
let code = fs.readFileSync(helper, 'utf8');
const terminal = "main().catch(error => { emit({ ok: false, code: safeText(error.code || 'R10_ACTIVATION_FAILED'), cause_code: safeText(error.cause?.code), no_automatic_retry: true }); process.exitCode = 1; });";
if (code.split(terminal).length !== 2 || code.slice(code.indexOf(terminal) + terminal.length).trim()) fail('FROZEN_HELPER_ENTRYPOINT_NOT_EXACT');
code = code.replace(terminal, `module.exports = { verifyFiles, mutationGuard, renewalGuard, observedDescriptor, authenticated, descriptorIdentity, readJson, inspectRuntime, censusFor, assertCensus, inspectPoliciesNoProbe, assertPoliciesUnchanged, assertPendingRecords, zeroVmProof, startAgent, proof, observeLifecycleProcessIdentity, sameProcessIdentity,
  installContinuationHooks(hooks) { emit = hooks.emit; lastReceipt = hooks.lastReceipt; currentR10 = hooks.currentR10; } };`);
const loaded = new Module(helper, module);
loaded.filename = helper;
loaded.paths = Module._nodeModulePaths(path.dirname(helper));
loaded._compile(code, helper);
const v2 = loaded.exports;
function durableGuard(observed) {
  const durable = v2.readJson(observed.paths.activationEpochFile(), 16 * 1024 * 1024).current;
  if (!durable || durable.activation_epoch_id !== expectedEpoch || durable.operation_id !== expectedOperation
    || !['VERIFYING', 'READY'].includes(durable.state) || durable.error
    || durable.owner_pid !== previous.pid || durable.owner_instance_id !== previous.instance_id
    || durable.component_evidence?.recovery_host?.pid !== previous.pid || durable.component_evidence?.recovery_host?.instance_id !== previous.instance_id
    || durable.metadata?.reason !== 'operator approved r10 setup exec contract activation preserving pending acceptance'
    || durable.metadata.refresh !== true || durable.metadata.allow_acceptance_pending !== true || durable.metadata.activation_mode !== 'full_clean_refresh'
    || durable.metadata.execution_role !== 'central_executor' || durable.metadata.component_profile !== 'central_executor_v1'
    || durable.source_checkpoint !== null || !Array.isArray(durable.transitions)) fail('EXACT_DURABLE_HANDOFF_REQUIRED');
  const transitions = durable.transitions;
  const h = transitions.findIndex(row => row.state === 'HANDOFF' && row.reason === 'replacement-recovery-host-requested');
  const s = transitions.findIndex((row, index) => index > h && row.state === 'STARTING' && row.reason === 'replacement-loading-durable-runtime');
  const p = transitions.findIndex((row, index) => index > s && row.state === 'VERIFYING' && row.reason === 'replacement-census');
  if (h < 0 || s <= h || p <= s || (durable.state !== 'READY' && (durable.admission_state !== 'CLOSED' || durable.expires_at_unix_ms <= Date.now()))) fail('HANDOFF_TRANSITIONS_OR_EXPIRY_NOT_EXACT');
  const proof = durable.state === 'READY' ? durable.verification?.final_census : durable.verification;
  if (!proof || proof.activation_epoch_id !== expectedEpoch || proof.host_pid !== replacement.pid || proof.host_instance_id !== replacement.instance_id
    || proof.expected_old_host_pid !== previous.pid || proof.expected_old_host_instance_id !== previous.instance_id
    || proof.ui_instance_id !== ui.instance_id || proof.running_revision !== revisions.coding || proof.disk_revision !== revisions.coding
    || proof.ui_running_revision !== revisions.ui || proof.recovery_host_running_revision !== revisions.host
    || ['workspace_matches', 'device_matches', 'revision_matches', 'recovery_host_revision_matches', 'recovery_host_epoch_matches', 'process_identity_verified', 'process_identity_changed', 'epoch_matches', 'all_components_same_epoch'].some(key => proof[key] !== true)) fail('DURABLE_REPLACEMENT_IDENTITY_PROOF_REQUIRED');
  return { activation_epoch_id: durable.activation_epoch_id, operation_id: durable.operation_id, state: durable.state, admission_state: durable.admission_state,
    request_fingerprint: durable.request_fingerprint, expires_at_unix_ms: durable.expires_at_unix_ms, old_host: previous, replacement_host: replacement,
    transition_chain_verified: true, component_identity_proof_verified: true };
}
async function currentR10() {
  historicalGuard();
  const observed = await v2.observedDescriptor();
  const descriptor = observed.descriptor;
  if (observed.tag !== 'r10' || descriptor.installation_id !== installation || descriptor.instance_id !== replacement.instance_id
    || descriptor.owner_pid !== replacement.pid || descriptor.owner_process_start_token !== replacement.process_start_token
    || observed.owner.state !== 'live' || !v2.sameProcessIdentity(replacement, observed.owner)) fail('EXACT_REPLACEMENT_HOST_IDENTITY_CHANGED');
  if ((await v2.observeLifecycleProcessIdentity(previous.pid)).state !== 'absent') fail('OLD_HANDOFF_HOST_NOT_ABSENT');
  for (const component of [ui, native]) {
    const identity = await v2.observeLifecycleProcessIdentity(component.pid);
    if (identity.state !== 'live' || !v2.sameProcessIdentity(component, identity)) fail('EXACT_HANDOFF_COMPONENT_CHANGED');
  }
  const state = v2.readJson(observed.paths.stateFile());
  if (state.nativePid !== native.pid || state.nativeProcessStartToken !== native.process_start_token || state.nativeActivationEpochId !== expectedEpoch) fail('NATIVE_HANDOFF_STATE_CHANGED');
  durableGuard(observed);
  return observed;
}
v2.installContinuationHooks({ emit, currentR10, lastReceipt: (phase, tag) => [...rows(historicalJournal), ...rows(journal)].findLast(row => row.phase === phase && (!tag || row.tag === tag)) || null });
async function prepare() {
  historicalGuard(); v2.verifyFiles();
  const observed = await currentR10();
  const identity = await v2.inspectRuntime(observed, 'handoff_continuation_preparation');
  if (identity.ui.instance_id !== ui.instance_id || identity.ui.registered !== true || identity.ui.alive !== true || identity.epoch.activation_epoch_id !== expectedEpoch) fail('HANDOFF_RUNTIME_OBSERVATION_MISMATCH');
  v2.assertCensus(await v2.censusFor(observed, 'continuation_preparation_census'), true);
  v2.assertPoliciesUnchanged(await v2.inspectPoliciesNoProbe(observed));
  const pending = v2.assertPendingRecords(observed.paths);
  v2.zeroVmProof('continuation_preparation');
  emit({ phase: 'continuation_prepared', tag: 'r10', durable_handoff: durableGuard(observed), pending_acceptance: pending,
    source_package_verified: true, readiness_not_forged: true, runtime_mutated: false, authority_mutated: false, frozen_v2_helper_sha256: expectedHelper, frozen_v2_journal_sha256: expectedJournal });
}
async function main() {
  const phase = process.argv[2];
  if (phase === 'prepare') await prepare();
  else if (phase === 'agent') {
    await prepare(); v2.mutationGuard(); const observed = await currentR10();
    v2.zeroVmProof('before_continuation_agent');
    v2.assertPendingRecords(observed.paths);
    await v2.startAgent();
  } else if (phase === 'proof') {
    v2.verifyFiles(); await currentR10(); await v2.proof();
  } else fail('PHASE_OUTSIDE_HANDOFF_CONTINUATION_SCOPE');
}
main().catch(error => { emit({ ok: false, code: safeCode(error.code || 'R10_HANDOFF_CONTINUATION_FAILED'), cause_code: safeCode(error.cause?.code), no_automatic_retry: true }); process.exitCode = 1; });
