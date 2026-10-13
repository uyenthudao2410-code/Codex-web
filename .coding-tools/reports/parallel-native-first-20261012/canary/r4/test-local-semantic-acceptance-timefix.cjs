'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');
const helper = require('./local-semantic-acceptance-timefix.cjs');

const archive = path.resolve('dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked/resources/app.asar');
const helperPath = path.resolve(__dirname, 'local-semantic-acceptance-timefix.cjs');
const helperSource = fs.readFileSync(helperPath, 'utf8');
const productionUserDataAt = helperSource.indexOf("app.setPath('userData', productionUserData)");
const whenReadyAt = helperSource.indexOf('await app.whenReady()');
const isolatedUserDataAfterReadyAt = helperSource.indexOf("app.setPath('userData', isolated)", whenReadyAt);
assert(productionUserDataAt >= 0 && whenReadyAt > productionUserDataAt
  && isolatedUserDataAfterReadyAt > whenReadyAt, 'safeStorage userData ordering changed');
const electron = path.resolve('node_modules/electron/dist/electron.exe');
const electronRead = spawnSync(electron, ['-e', [
  `const helper=require(${JSON.stringify(helperPath)});`,
  `const archive=${JSON.stringify(archive)};`,
  'const bytes=helper.readPhysicalFile(archive);',
  'if (bytes.length < 1000000) throw new Error("ARCHIVE_TOO_SMALL");',
  'process.stdout.write(JSON.stringify({ok:true,bytes:bytes.length}));',
].join(' ')], { env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, encoding: 'utf8', windowsHide: true });
assert.equal(electronRead.status, 0, electronRead.stderr || electronRead.stdout);
assert.deepEqual(JSON.parse(electronRead.stdout), { ok: true, bytes: 7379480 });

const argvProbe = spawnSync(electron, ['-e', [
  `process.argv=['electron','--user-data-dir=semantic-operator-profile',${JSON.stringify(helperPath)},'audit'];`,
  `const helper=require(${JSON.stringify(helperPath)});`,
  'process.stdout.write(JSON.stringify({mode:helper.invocationMode}));',
].join(' ')], { env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }, encoding: 'utf8', windowsHide: true });
assert.equal(argvProbe.status, 0, argvProbe.stderr || argvProbe.stdout);
assert.deepEqual(JSON.parse(argvProbe.stdout), { mode: 'audit' });

function partial() {
  return { phase: 'final', operation: 'native_first_shared_mcp_canary', ok: false,
    error_code: 'ORIGINAL_JOB_IDENTITY_NOT_VERIFIED', attempt_id: 'a'.repeat(32),
    task_id: 'task_' + 'b'.repeat(32), workspace_id: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94',
    workspace_generation: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097',
    binding_id: 'bind_' + 'c'.repeat(32),
    proof_counts: { reads: 100, patches: 20, readbacks: 20, node_jobs: 0, git_jobs: 0 },
    requires_reconciliation: false, unresolved_original_actions: [], task_closed_verified: true,
    writer_released_verified: true, final_action_status: { node_01: { state: 'completed', process_state: 'completed', reconciliation_required: false } } };
}
function continuation(source, hash) {
  const proofs = {};
  for (let i = 1; i <= 10; i += 1) proofs[`node_${String(i).padStart(2, '0')}`] = { job_id: `job_${i}`, command_id: `cmd_${i}`, local_handle: `handle_${i}` };
  proofs.git_status = { job_id: 'job_git_status', command_id: 'cmd_git_status', local_handle: 'handle_git_status' };
  return { phase: 'final', operation: 'native_exec_continuation', ok: false, error_code: 'EXEC_TERMINAL_PAYLOAD_INVALID', attempt_id: 'c'.repeat(32),
    workspace_id: source.workspace_id, workspace_generation: source.workspace_generation, binding_id: source.binding_id,
    source_partial: { sha256: hash, final: { attempt_id: source.attempt_id, error_code: source.error_code, task_id: source.task_id } },
    proofs, proof_counts: { node_jobs: 10, git_jobs: 1, approved_build: 0, build_readback: 0 },
    task_closed_verified: true, writer_released_verified: true };
}
function resume(source, hash) {
  const common = { job_id: 'job_resume', command_id: 'cmd_resume', local_handle: 'handle_resume' };
  return { phase: 'final', operation: 'native_exec_continuation_resume', ok: false, error_code: 'KeyError', attempt_id: 'd'.repeat(32),
    workspace_id: source.workspace_id, workspace_generation: source.workspace_generation, binding_id: source.binding_id,
    source_continuation: { sha256: hash }, proofs: { git_diff: common, git_log: common, build: common },
    proof_counts: { git_jobs: 2, approved_build: 1, build_readback: 0 }, task_closed_verified: true, writer_released_verified: true };
}
function finalizer(source, hash) {
  return { phase: 'final', operation: 'native_exec_readback_finalizer', ok: true, attempt_id: 'e'.repeat(32),
    task_id: 'task_' + 'f'.repeat(32), action_ids: { build_readback: 'act_' + '0'.repeat(32) },
    workspace_id: source.workspace_id, workspace_generation: source.workspace_generation, binding_id: source.binding_id,
    source_resume: { sha256: hash }, proofs: { build_readback: { action_id: 'act_' + '0'.repeat(32), receipt_id: 'receipt_readback' } },
    proof_counts: { build_readback: 1 }, task_closed_verified: true, writer_released_verified: true };
}
function observer(source, hash) {
  const action_id = 'act_' + '1'.repeat(32);
  return { phase: 'final', operation: 'native_exec_continuation_final', ok: true,
    workspace_id: source.workspace_id, workspace_generation: source.workspace_generation, binding_id: source.binding_id,
    source_finalizer_sha256: hash, source_finalizer: { sha256: hash, final: source },
    action_id,
    proofs: { build_readback: { action_id, receipt_id: 'receipt_readback' } },
    proof_counts: { build_readback: 1, new_dispatch_performed: false },
    task_closed_verified: true, writer_released_verified: true,
    readback_action_replayed: false, new_dispatch_performed: false };
}
const p = partial();
const c = continuation(p, 'f'.repeat(64));
const r = resume(c, 'a'.repeat(64));
const f = finalizer(r, 'b'.repeat(64));
const finalizerHash = '6e29a90b6ee29f0b516f8ab0065b2c063d4ea9ff3f327f8bd56be74e9d531b04';
const observerHash = 'd'.repeat(64);
const o = observer(f, finalizerHash);
function validate(overrides = {}) {
  return helper.validateEvidenceSet(overrides.partial || p, 'f'.repeat(64), overrides.continuation || c, 'a'.repeat(64),
    overrides.resume || r, 'b'.repeat(64), overrides.finalizer || f, finalizerHash,
    overrides.observer || o, overrides.observerHash || observerHash);
}
const evidence = validate();
assert.equal(evidence.original_actions_replayed, false);
assert.equal(evidence.readback_finalizer_proof_counts.build_readback, 1);
assert.equal(evidence.readback_observer_proof_counts.build_readback, 1);
assert.equal(evidence.readback_finalizer_sha256, finalizerHash);
assert.equal(evidence.readback_observer_sha256, observerHash);
assert.equal(evidence.readback_observer_attempt_id, null);
assert.equal(helper.finalReadbackObserver([f, o]), o);
assert.throws(() => helper.finalReadbackObserver([f]), error => error.code === 'EXACT_FINAL_READBACK_OBSERVER_REQUIRED');
assert.throws(() => helper.finalReadbackObserver([o, o]), error => error.code === 'EXACT_FINAL_READBACK_OBSERVER_REQUIRED');
assert.throws(() => validate({ partial: { ...p, ok: true } }), error => error.code === 'PARTIAL_CANARY_FAILURE_NOT_PRESERVED');
assert.throws(() => validate({ continuation: { ...c, source_partial: { ...c.source_partial, sha256: '0'.repeat(64) } } }), error => error.code === 'CONTINUATION_SOURCE_BINDING_INVALID');
assert.throws(() => validate({ finalizer: { ...f, ok: false } }), error => error.code === 'READBACK_FINALIZER_CHAIN_INVALID');
assert.throws(() => validate({ finalizer: { ...f, source_resume: { sha256: '0'.repeat(64) } } }), error => error.code === 'READBACK_FINALIZER_CHAIN_INVALID');
for (const changed of [
  { ok: false }, { source_finalizer_sha256: '0'.repeat(64) },
  { source_finalizer: { ...o.source_finalizer, sha256: '0'.repeat(64) } },
  { source_finalizer: { ...o.source_finalizer, final: { ...f, task_id: 'task_wrong' } } },
  { action_id: 'act_' + '2'.repeat(32) },
  { proofs: { build_readback: { ...o.proofs.build_readback, action_id: 'act_' + '2'.repeat(32) } } },
  { readback_action_replayed: true }, { new_dispatch_performed: true },
  { task_closed_verified: false }, { writer_released_verified: false },
]) assert.throws(() => validate({ observer: { ...o, ...changed } }), error => error.code === 'READBACK_OBSERVER_CHAIN_INVALID');
assert.throws(() => validate({ observerHash: 'invalid' }), error => error.code === 'READBACK_OBSERVER_CHAIN_INVALID');
assert.throws(() => validate({ observer: { ...o, binding_id: 'bind_wrong' } }), error => error.code === 'READBACK_OBSERVER_SCOPE_CHANGED');
process.stdout.write('timefix semantic evidence-set tests passed\n');
