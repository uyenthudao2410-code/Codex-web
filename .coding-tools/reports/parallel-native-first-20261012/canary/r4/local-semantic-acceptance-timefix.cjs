'use strict';
// Root operator helper. Preparation is offline. Audit/accept use the supported
// local MCP API and the installed profile's bearer in memory only. Never mint
// connector attestation, import a proof from another RUN or replay a mutation.
const fs = require('node:fs');
// Electron's patched fs treats an app.asar path as an archive-internal path.
// Use the same original-fs convention as @electron/asar for the archive's
// physical bytes while retaining Electron fs for files addressed inside it.
const originalFs = process.versions.electron ? require('original-fs') : fs;
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const ROOT = 'E:\\DEV\\Codex-web';
const HERE = __dirname;
const CANDIDATE = path.join(ROOT, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked');
const OPERATOR_ELECTRON = path.join(ROOT, 'node_modules/electron/dist/electron.exe');
const CLIENT = 'electron-native-first-canary-acceptance';
const HEX = /^[a-f0-9]{64}$/;
const ID = /^[a-f0-9]{32}$/;
const readPhysicalFile = file => originalFs.readFileSync(file);
const need = (value, code) => { if (!value) throw Object.assign(new Error(), { code }); };
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
let descriptorGuard;
const arg = name => { const at = process.argv.indexOf('--' + name); need(at > 0 && at + 1 < process.argv.length, 'EXACT_ARGUMENT_REQUIRED'); return process.argv[at + 1]; };
const samePath = (left, right) => path.resolve(left).toLowerCase() === path.resolve(right).toLowerCase();
const scriptIndex = process.argv.findIndex((value, index) => index > 0 && typeof value === 'string'
  && samePath(value, __filename));
// Electron keeps its switches before the script path; Node puts the script at argv[1].
// Derive the mode immediately after this helper's own script entry in both forms.
const mode = process.argv[scriptIndex >= 0 ? scriptIndex + 1 : 2];
function read(file, expected, ndjson = false) {
  need(path.isAbsolute(file) && HEX.test(expected), 'PUBLIC_INPUT_PIN_INVALID');
  const stat = fs.lstatSync(file);
  need(stat.isFile() && !stat.isSymbolicLink() && stat.size <= 2 * 1024 * 1024, 'PUBLIC_INPUT_BOUND_INVALID');
  const raw = fs.readFileSync(file);
  need(sha(raw) === expected, 'PUBLIC_INPUT_CHANGED');
  const text = raw.toString('utf8').replace(/^\uFEFF/, '');
  return ndjson ? text.split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line)) : JSON.parse(text);
}
function finalCanary(rows) {
  const matches = rows.filter(row => row.phase === 'final' && row.operation === 'native_first_shared_mcp_canary');
  need(matches.length === 1, 'EXACT_FINAL_CANARY_REQUIRED');
  const value = matches[0];
  need(value.workspace_id === 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94'
    && value.workspace_generation === 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097'
    && ID.test(value.attempt_id) && value.proofs && typeof value.proofs === 'object', 'EXACT_CANARY_SCOPE_REQUIRED');
  return value;
}

// The timeoutfix canary deliberately ended after the first standalone exec
// exposed a harness-only identity assumption.  Keep that receipt immutable and
// bind the remaining exec evidence as a separate, fresh task.  This validator
// accepts the evidence set only when both receipts prove their own terminal
// cleanup and the continuation is cryptographically bound to the exact failed
// receipt.  It never changes the failed receipt or replays an original action.
function finalContinuation(rows) {
  const matches = rows.filter(row => row.phase === 'final' && row.operation === 'native_exec_continuation');
  need(matches.length === 1, 'EXACT_FINAL_CONTINUATION_REQUIRED');
  return matches[0];
}
function finalReceipt(rows, operation) {
  const matches = rows.filter(row => row.phase === 'final' && row.operation === operation);
  need(matches.length === 1, 'EXACT_FINAL_CHAIN_RECEIPT_REQUIRED');
  return matches[0];
}
function finalReadbackObserver(rows) {
  const matches = rows.filter(row => row.phase === 'final' && row.operation === 'native_exec_continuation_final');
  need(matches.length === 1, 'EXACT_FINAL_READBACK_OBSERVER_REQUIRED');
  return matches[0];
}
function validateEvidenceSet(partial, partialHash, continuation, continuationHash, resume, resumeHash, finalizer, finalizerHash, observer, observerHash) {
  need(partial.ok === false && partial.error_code === 'ORIGINAL_JOB_IDENTITY_NOT_VERIFIED',
    'PARTIAL_CANARY_FAILURE_NOT_PRESERVED');
  need(JSON.stringify(partial.proof_counts) === JSON.stringify({ reads: 100, patches: 20, readbacks: 20, node_jobs: 0, git_jobs: 0 }),
    'PARTIAL_CANARY_COUNTS_INVALID');
  need(partial.requires_reconciliation === false && Array.isArray(partial.unresolved_original_actions)
    && partial.unresolved_original_actions.length === 0 && partial.task_closed_verified === true
    && partial.writer_released_verified === true, 'PARTIAL_CANARY_CLEANUP_INVALID');
  const node = partial.final_action_status?.node_01;
  need(node?.state === 'completed' && node?.process_state === 'completed'
    && node?.reconciliation_required === false, 'PARTIAL_NODE_ACTION_NOT_TERMINAL');
  need(continuation.ok === false && continuation.error_code === 'EXEC_TERMINAL_PAYLOAD_INVALID'
    && continuation.task_closed_verified === true && continuation.writer_released_verified === true
    && continuation.source_partial?.sha256 === partialHash
    && continuation.source_partial?.final?.attempt_id === partial.attempt_id
    && continuation.source_partial?.final?.error_code === partial.error_code
    && continuation.source_partial?.final?.task_id === partial.task_id,
    'CONTINUATION_SOURCE_BINDING_INVALID');
  need(continuation.workspace_id === partial.workspace_id
    && continuation.workspace_generation === partial.workspace_generation
    && continuation.binding_id === partial.binding_id,
    'CONTINUATION_SCOPE_CHANGED');
  need(continuation.proof_counts?.node_jobs === 10 && continuation.proof_counts?.git_jobs === 1
    && continuation.proof_counts?.approved_build === 0 && continuation.proof_counts?.build_readback === 0,
    'CONTINUATION_PROOF_COUNTS_INVALID');
  const proofs = continuation.proofs || {};
  need(Object.keys(proofs).filter(key => /^node_\d{2}$/.test(key)).length === 10 && proofs.git_status,
    'CONTINUATION_PROOFS_INCOMPLETE');
  const jobs = Object.keys(proofs).filter(key => /^node_\d{2}$/.test(key)).map(key => proofs[key]);
  need(new Set(jobs.map(proof => proof.job_id)).size === 10 && jobs.every(proof => proof.job_id && proof.command_id && proof.local_handle),
    'CONTINUATION_NODE_JOB_IDENTITY_INVALID');
  need(Object.values(proofs).every(proof => proof.runtime_identity == null || typeof proof.runtime_identity === 'object'),
    'CONTINUATION_PROOF_SHAPE_INVALID');
  need(resume.ok === false && resume.error_code === 'KeyError' && resume.task_closed_verified === true
    && resume.writer_released_verified === true && resume.source_continuation?.sha256 === continuationHash
    && resume.proof_counts?.git_jobs === 2 && resume.proof_counts?.approved_build === 1
    && resume.proof_counts?.build_readback === 0,
    'CONTINUATION_RESUME_CHAIN_INVALID');
  need(resume.proofs?.git_diff && resume.proofs?.git_log && resume.proofs?.build
    && finalizer.ok === true && finalizer.task_closed_verified === true && finalizer.writer_released_verified === true
    && finalizer.source_resume?.sha256 === resumeHash
    && finalizer.proof_counts?.build_readback === 1
    && finalizer.proofs?.build_readback
    && /^act_[a-f0-9]{32}$/.test(finalizer.action_ids?.build_readback)
    && finalizer.proofs.build_readback.action_id === finalizer.action_ids.build_readback,
    'READBACK_FINALIZER_CHAIN_INVALID');
  need(resume.workspace_id === partial.workspace_id && resume.workspace_generation === partial.workspace_generation
    && resume.binding_id === partial.binding_id && finalizer.workspace_id === partial.workspace_id
    && finalizer.workspace_generation === partial.workspace_generation && finalizer.binding_id === partial.binding_id,
    'CONTINUATION_CHAIN_SCOPE_CHANGED');
  if (observer) {
    need(HEX.test(observerHash) && observer.ok === true && observer.task_closed_verified === true
      && observer.writer_released_verified === true
      && observer.source_finalizer_sha256 === finalizerHash
      && observer.source_finalizer?.sha256 === finalizerHash
      && observer.source_finalizer?.final?.attempt_id === finalizer.attempt_id
      && observer.source_finalizer?.final?.task_id === finalizer.task_id
      && /^act_[a-f0-9]{32}$/.test(observer.action_id)
      && observer.action_id !== finalizer.action_ids.build_readback
      && observer.readback_action_replayed === false
      && observer.new_dispatch_performed === false
      && observer.proof_counts?.build_readback === 1
      && observer.proofs?.build_readback?.action_id === observer.action_id,
      'READBACK_OBSERVER_CHAIN_INVALID');
    need(observer.workspace_id === partial.workspace_id && observer.workspace_generation === partial.workspace_generation
      && observer.binding_id === partial.binding_id, 'READBACK_OBSERVER_SCOPE_CHANGED');
  }
  return { partial_attempt_id: partial.attempt_id, continuation_attempt_id: continuation.attempt_id,
    continuation_resume_attempt_id: resume.attempt_id, readback_finalizer_attempt_id: finalizer.attempt_id,
    readback_observer_attempt_id: observer?.attempt_id || null,
    readback_finalizer_sha256: finalizerHash, readback_observer_sha256: observerHash || null,
    partial_error_code: partial.error_code, partial_proof_counts: partial.proof_counts,
    continuation_proof_counts: continuation.proof_counts, continuation_resume_proof_counts: resume.proof_counts,
    readback_finalizer_proof_counts: finalizer.proof_counts,
    readback_observer_proof_counts: observer?.proof_counts || null,
    aggregate_counts: { reads: 100, patches: 20, readbacks: 20, node_jobs: 10, git_jobs: 3, approved_build: 1, build_readback: 1 },
    original_actions_replayed: false };
}
function targetsFromCanary(canary) {
  const registry = JSON.parse(fs.readFileSync(path.join(ROOT, '.coding-tools/orchestration/task-context-workspaces.json'), 'utf8'));
  const result = [];
  for (let index = 1; index <= 20; index += 1) {
    const lane = `patch_${String(index).padStart(3, '0')}`;
    const proof = canary.proofs[lane];
    if (!proof) continue; // A partial canary can be audited but cannot be accepted.
    const relative = `tests/fixtures/native-first-canary/file-${String(index).padStart(3, '0')}.txt`;
    const readback = canary.proofs[`readback_${String(index).padStart(3, '0')}`];
    need(ID.test(proof.run_id) && ID.test(proof.wave_id) && HEX.test(proof.postimage_sha256)
      && proof.action_id === canary.action_ids[lane] && readback?.path === relative
      && readback.content_sha256 === proof.postimage_sha256, 'ORIGINAL_PATCH_READBACK_LINEAGE_REQUIRED');
    const file = path.join(ROOT, relative), stat = fs.lstatSync(file);
    need(stat.isFile() && !stat.isSymbolicLink() && sha(fs.readFileSync(file)) === proof.postimage_sha256,
      'CURRENT_POSTIMAGE_CHANGED');
    const contexts = Object.entries(registry.contexts || {}).filter(([context, entry]) => {
      if (!/^cpap_[a-f0-9]{56}$/.test(context) || !samePath(entry.canonical_root, ROOT)) return false;
      const file = path.join(ROOT, '.coding-tools/task-contexts', sha(Buffer.from('mcp2026:' + context)).slice(0, 24) + '.json');
      if (!fs.existsSync(file)) return false;
      const state = JSON.parse(fs.readFileSync(file, 'utf8'));
      return state.orchestration?.run_id === proof.run_id;
    });
    need(contexts.length === 1, 'EXACT_ORIGINAL_PATCH_CONTEXT_REQUIRED');
    result.push({ lane, original_action_id: proof.action_id, original_task_id: canary.task_id,
      task_context_id: contexts[0][0],
      run_id: proof.run_id, wave_id: proof.wave_id,
      acceptance_files: [{ path: relative, sha256: proof.postimage_sha256 }] });
  }
  need(new Set(result.map(value => value.run_id + ':' + value.wave_id)).size === result.length,
    'DUPLICATE_PATCH_RUN_WAVE');
  return result;
}
function projectAudit(payload, target) {
  const run = payload.audit?.run, waves = payload.audit?.waves || [], proofs = payload.audit?.proofs || [];
  const projection = payload.orchestration?.orchestration || payload.orchestration || {};
  const state = projection.orchestration_state || projection.state || payload.state?.orchestration?.orchestration_state;
  need((projection.run_id || run?.run_id) === target.run_id
    && (projection.wave_id || payload.state?.orchestration?.wave_id) === target.wave_id,
    'AUDIT_ORIGINAL_RUN_WAVE_MISMATCH');
  return { run_id: target.run_id, wave_id: target.wave_id, state,
    run_status: run?.status || null,
    proofs: proofs.filter(proof => proof.run_id === target.run_id && proof.wave_id === target.wave_id)
      .map(proof => ({ proof_id: proof.proof_id, stage_id: proof.stage_id, status: proof.status,
        input_fingerprint: proof.input_fingerprint, exit_code: proof.exit_code ?? null,
        command_hash: proof.command_hash, cache_hit: proof.cache_hit,
        proof_reuse: proof.metadata?.proof_reuse || null,
        result_status: proof.metadata?.result?.status || null,
        cancelled: proof.metadata?.result?.cancelled === true,
        timed_out: proof.metadata?.result?.timed_out === true,
        proof_source_binding: proof.metadata?.proof_source_binding || null })),
    checkpoint: projection.checkpoint || null,
    completion_report_id: payload.completion_report?.report_id || payload.state?.completion_report_id || null,
    waves: waves.filter(wave => wave.wave_id === target.wave_id).map(wave => ({ wave_id: wave.wave_id, status: wave.status })) };
}
function realVerifierProof(proof, target, command) {
  const commandHash = sha(Buffer.from(command));
  return proof.status === 'passed' && HEX.test(proof.input_fingerprint)
    && proof.stage_id === 'check:' + commandHash.slice(0, 16) && proof.command_hash === commandHash
    && proof.exit_code === 0 && (proof.cache_hit === false || proof.cache_hit === 0) && !proof.proof_reuse
    && proof.result_status === 'passed' && !proof.cancelled && !proof.timed_out
    && JSON.stringify(proof.proof_source_binding?.paths) === JSON.stringify(target.acceptance_files.map(file => file.path).sort());
}
function toolPayload(response, expectedId) {
  need(response.id === expectedId && !response.error && response.result?.isError !== true
    && response.result?.structuredContent && typeof response.result.structuredContent === 'object', 'LOCAL_MCP_GUARD_REJECTED');
  return response.result.structuredContent;
}
function requestJson(port, token, route, body, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const failure = code => reject(Object.assign(new Error(), { code }));
    const bytes = body == null ? null : Buffer.from(JSON.stringify(body));
    const request = http.request({ hostname: '127.0.0.1', port, path: route,
      method: bytes ? 'POST' : 'GET', timeout: timeoutMs,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json',
        ...(bytes ? { 'Content-Length': bytes.length, 'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': 'tools/call', 'Mcp-Name': body?.params?.name || 'task_control',
          'X-Coding-Tools-Client-Id': CLIENT, 'X-Coding-Tools-Client-Type': 'electron' } : {}) } }, response => {
      const chunks = []; let length = 0;
      response.on('data', chunk => { length += chunk.length; if (length <= 2 * 1024 * 1024) chunks.push(chunk); });
      response.on('end', () => {
        if (response.statusCode !== 200 || length > 2 * 1024 * 1024) return failure('LOCAL_API_RESPONSE_REJECTED');
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { failure('LOCAL_API_JSON_INVALID'); }
      });
    });
    request.on('timeout', () => { request.destroy(); failure('LOCAL_API_TIMEOUT_OBSERVE_ORIGINAL'); });
    request.on('error', () => failure('LOCAL_API_TRANSPORT_FAILED_OBSERVE_ORIGINAL'));
    request.end(bytes);
  });
}
function emit(report) {
  if (descriptorGuard) {
    report.production_descriptor_stable = sha(fs.readFileSync(descriptorGuard.file)) === descriptorGuard.sha256;
    if (!report.production_descriptor_stable) { report.ok = false; report.code = 'PRODUCTION_DESCRIPTOR_CHANGED'; }
  }
  const file = path.join(HERE, `semantic-${report.operation}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}.json`);
  report.report_path = file;
  fs.writeFileSync(file, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ok: report.ok, operation: report.operation,
    report_path: file, accepted_count: report.accepted_count || 0, blockers: report.blockers || [] }) + '\n');
  return report;
}
async function main() {
  need(['prepare', 'prepare-verifier', 'audit', 'reject', 'accept', 'replan'].includes(mode), 'MODE_INVALID');
  need(sha(fs.readFileSync(__filename)) === arg('helper-sha256'), 'REVIEWED_HELPER_CHANGED');
  const pins = read(arg('pins'), arg('pins-sha256'));
  const canaryHash = arg('canary-sha256');
  const canary = finalCanary(read(arg('canary'), canaryHash, true));
  const continuationHash = arg('continuation-sha256');
  const continuation = finalContinuation(read(arg('continuation'), continuationHash, true));
  const continuationResumeHash = arg('continuation-resume-sha256');
  const continuationResume = finalReceipt(read(arg('continuation-resume'), continuationResumeHash, true), 'native_exec_continuation_resume');
  const readbackFinalizerHash = arg('readback-finalizer-sha256');
  const readbackFinalizer = finalReceipt(read(arg('readback-finalizer'), readbackFinalizerHash, true), 'native_exec_readback_finalizer');
  const hasArgument = name => process.argv.includes('--' + name);
  const readbackObserverHash = hasArgument('readback-observer-sha256') ? arg('readback-observer-sha256') : null;
  const readbackObserver = readbackObserverHash
    ? finalReadbackObserver(read(arg('readback-observer'), readbackObserverHash, true)) : null;
  const evidenceSet = validateEvidenceSet(canary, canaryHash, continuation, continuationHash,
    continuationResume, continuationResumeHash, readbackFinalizer, readbackFinalizerHash, readbackObserver, readbackObserverHash);
  const targets = targetsFromCanary(canary);
  need(pins.activation_verified === true && pins.workspace_label === 'Codex-web'
    && HEX.test(pins.local_tool_contract_sha256)
    && canary.workspace_id === pins.workspace_id
    && canary.workspace_generation === pins.workspace_generation
    && [continuation, continuationResume, readbackFinalizer, ...(readbackObserver ? [readbackObserver] : [])].every(value => value.workspace_id === pins.workspace_id
      && value.workspace_generation === pins.workspace_generation && value.binding_id === pins.binding_id
      && value.activation_epoch === pins.activation_epoch && value.process_instance_id === pins.process_instance_id
      && value.server_instance_id === pins.server_instance_id
      && value.local_tool_contract_sha256 === pins.local_tool_contract_sha256), 'ACTIVATED_CODEX_PINS_REQUIRED');
  const expectedRuntime = { activation_epoch_id: pins.activation_epoch,
    process_instance_id: pins.process_instance_id, server_instance_id: pins.server_instance_id,
    tool_contract_sha256: pins.local_tool_contract_sha256 };
  for (const proof of [...Object.values(continuation.proofs || {}), ...Object.values(continuationResume.proofs || {}),
    ...Object.values(readbackFinalizer.proofs || {}), ...(readbackObserver ? Object.values(readbackObserver.proofs || {}) : [])]) {
    need(proof.runtime_identity && JSON.stringify(proof.runtime_identity) === JSON.stringify(expectedRuntime),
      'CONTINUATION_RUNTIME_IDENTITY_CHANGED');
  }
  const report = { schema_version: 1, operation: mode, ok: true, observed_at: new Date().toISOString(),
    provenance: 'local_authenticated_operator', connector_attestation_claimed: false,
    canary_sha256: canaryHash, continuation_sha256: continuationHash,
    continuation_resume_sha256: continuationResumeHash,
    readback_finalizer_sha256: readbackFinalizerHash, readback_observer_sha256: readbackObserverHash,
    original_attempt_id: canary.attempt_id, continuation_attempt_id: continuation.attempt_id,
    evidence_set: evidenceSet, targets,
    original_actions_replayed: false, acceptance_performed: false, accepted_count: 0,
    runtime_identity: { activation_epoch: pins.activation_epoch, process_instance_id: pins.process_instance_id,
      server_instance_id: pins.server_instance_id, tool_contract_sha256: pins.local_tool_contract_sha256 } };
  if (mode === 'prepare') { report.api_invoked = false; emit(report); return; }
  const successfulCanary = () => need(canary.task_closed_verified === true
    && canary.writer_released_verified === true && targets.length === 20 && !canary.requires_reconciliation
    && Array.isArray(canary.unresolved_original_actions) && !canary.unresolved_original_actions.length
    && continuation.ok === false && continuation.task_closed_verified === true
    && continuation.writer_released_verified === true
    && continuationResume.task_closed_verified === true && continuationResume.writer_released_verified === true
    && readbackFinalizer.ok === true && readbackFinalizer.task_closed_verified === true
    && readbackFinalizer.writer_released_verified === true
    && (!readbackObserver || (readbackObserver.ok === true && readbackObserver.task_closed_verified === true
      && readbackObserver.writer_released_verified === true)), 'SUCCESSFUL_TERMINAL_EVIDENCE_SET_REQUIRED');
  if (mode === 'prepare-verifier') {
    successfulCanary();
    need(process.argv.includes('--prepare-fixture'), 'ADDITIVE_VERIFIER_PREPARATION_REQUIRED');
    const source = path.join(HERE, 'prepared-verify-postimages.cjs');
    const bytes = fs.readFileSync(source), sourceStat = fs.lstatSync(source);
    need(sourceStat.isFile() && !sourceStat.isSymbolicLink() && bytes.length < 8192
      && HEX.test(arg('verifier-sha256')) && sha(bytes) === arg('verifier-sha256'), 'REVIEWED_VERIFIER_CHANGED');
    const fixture = path.join(ROOT, 'tests/fixtures/native-first-canary');
    need(fs.lstatSync(fixture).isDirectory() && !fs.lstatSync(fixture).isSymbolicLink(), 'FIXTURE_DIRECTORY_CHANGED');
    const target = path.join(fixture, 'verify-postimages.cjs');
    need(!fs.existsSync(target), 'ADDITIVE_VERIFIER_ALREADY_EXISTS');
    fs.writeFileSync(target, bytes, { flag: 'wx' });
    need(sha(fs.readFileSync(target)) === arg('verifier-sha256'), 'PREPARED_VERIFIER_READBACK_CHANGED');
    emit({ ...report, api_invoked: false, fixture_prepared: true, fixture_path: target,
      fixture_sha256: sha(bytes), existing_fixtures_changed: false, verifier_executed: false });
    return;
  }
  need(samePath(process.execPath, OPERATOR_ELECTRON) && process.env.ELECTRON_RUN_AS_NODE !== '1'
    && HEX.test(arg('operator-exe-sha256')) && sha(fs.readFileSync(process.execPath)) === arg('operator-exe-sha256'),
    'EXACT_NORMAL_OPERATOR_ELECTRON_REQUIRED');
  const parity = read(arg('parity'), arg('parity-sha256'));
  const smoke = read(arg('smoke'), arg('smoke-sha256'));
  need(parity.ok === true && parity.proof_kind === 'exact_source_package_parity' && samePath(parity.candidate, CANDIDATE)
    && smoke.result?.ok === true && smoke.exit_code === 0 && smoke.production_descriptor_stable === true
    && samePath(smoke.candidate, CANDIDATE) && smoke.sha256?.source_package_parity_receipt === arg('parity-sha256')
    && parity.executable_sha256 === smoke.sha256.executable && parity.app_asar_sha256 === smoke.sha256.app_asar
    && sha(fs.readFileSync(path.join(CANDIDATE, 'Coding Tools MCP.exe'))) === parity.executable_sha256
     && sha(readPhysicalFile(path.join(CANDIDATE, 'resources/app.asar'))) === parity.app_asar_sha256,
    'EXACT_REVIEWED_R4_PACKAGE_REQUIRED');
  const { app } = require('electron');
  const isolated = path.join(HERE, 'semantic-operator-profile');
  const productionUserData = path.join(process.env.APPDATA, 'web-mcp-assistant');
  need(samePath(app.commandLine.getSwitchValue('user-data-dir'), isolated), 'ISOLATED_OPERATOR_PROFILE_REQUIRED');
  // safeStorage decrypts the production secrets.bin using the userData path
  // selected before ready. Keep session data isolated, then restore userData
  // after readiness before making any semantic API calls.
  app.setPath('userData', productionUserData);
  await app.whenReady();
  app.setPath('userData', isolated);
  app.setPath('sessionData', path.join(isolated, 'session-data'));
  const appRoot = path.join(CANDIDATE, 'resources/app.asar');
  for (const relative of ['electron/paths.js', 'electron/services/runtimePaths.js',
    'electron/services/runtimeIdentity.js', 'electron/services/secretStore.js', 'electron/services/jsonStore.js']) {
    const expected = parity.code_sha256?.[relative];
    need(HEX.test(expected) && sha(fs.readFileSync(path.join(appRoot, relative))) === expected
      && sha(fs.readFileSync(path.join(ROOT, relative))) === expected, 'REVIEWED_OPERATOR_SOURCE_CHANGED');
  }
  const { RuntimePaths } = require(path.join(appRoot, 'electron/services/runtimePaths'));
  const paths = new RuntimePaths({ dataRoot: productionUserData,
    appRoot, resourcesRoot: path.join(CANDIDATE, 'resources/resources'), runtimeMode: 'packaged', executablePath: process.execPath });
  descriptorGuard = { file: paths.recoveryHostDescriptorFile(), sha256: sha(fs.readFileSync(paths.recoveryHostDescriptorFile())) };
  report.operator_runtime = { type: 'normal_stock_electron', executable: process.execPath,
    executable_sha256: arg('operator-exe-sha256'), production_app_asar_sha256: parity.app_asar_sha256,
    isolated_profile: isolated, production_main_started: false };
  const settings = JSON.parse(fs.readFileSync(paths.settingsFile(), 'utf8'));
  need(samePath(settings.workspace, ROOT) && Number.isSafeInteger(settings.mcpPort), 'EXACT_LOCAL_SETTINGS_REQUIRED');
  const { SecretStore } = require(path.join(appRoot, 'electron/services/secretStore'));
  const token = new SecretStore(paths).get('mcpAuthToken');
  need(typeof token === 'string' && token.length >= 32, 'LOCAL_BEARER_UNAVAILABLE');
  const health = await requestJson(settings.mcpPort, token, '/__control/health');
  need(health.ready === true && samePath(health.workspace, ROOT)
    && health.activation_epoch_id === pins.activation_epoch
    && health.process_instance_id === pins.process_instance_id
    && (health.instance_id || health.server_instance_id) === pins.server_instance_id
    && health.tool_contract?.sha256 === pins.local_tool_contract_sha256, 'ACTUAL_LOCAL_HEALTH_IDENTITY_CHANGED');
  const invokeTool = async (tool, arguments_) => {
    const action = arguments_.action || arguments_.phase;
    const id = `semantic-${action}-${crypto.randomBytes(8).toString('hex')}`;
    const response = await requestJson(settings.mcpPort, token, '/mcp', { jsonrpc: '2.0', id, method: 'tools/call',
      params: { name: tool, arguments: arguments_,
        _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {}, 'io.modelcontextprotocol/clientInfo': { name: CLIENT, version: '1' } } } },
      tool === 'agent_workflow' ? 90000 : 15000);
    return toolPayload(response, id);
  };
  const invoke = (action, target, extra = {}) => invokeTool('task_control', {
    action, task_context_id: target.task_context_id, run_id: target.run_id, wave_id: target.wave_id, ...extra });
  report.before = [];
  for (const target of targets) report.before.push(projectAudit(await invoke('audit', target, { limit: 100, wave_id: undefined }), target));
  report.blockers = report.before.flatMap(value => value.state !== 'ACCEPTING' ? [`${value.run_id}:NOT_ACCEPTING`]
    : !value.proofs.some(proof => proof.status === 'passed' && HEX.test(proof.input_fingerprint))
      ? [`${value.run_id}:EXACT_PASSED_PROOF_REQUIRED`] : []);
  if (mode === 'audit') { report.api_invoked = true; emit(report); app.quit(); return; }
  need(process.argv.includes('--apply') && process.argv.includes('--claim-controller'), 'EXPLICIT_OPERATOR_ACCEPTANCE_REQUIRED');
  successfulCanary();
  if (mode === 'accept') need(report.blockers.length === 0, 'EXACT_WAVE_PROOF_BLOCKS_ACCEPTANCE');
  if (mode === 'reject') {
    need(report.before.every(value => value.state === 'ACCEPTING'
      && !value.proofs.some(proof => proof.status === 'passed')), 'REJECTION_ONLY_FOR_EXACT_MISSING_PROOF_WAVES');
    report.rejections = [];
  }
  let rejectionReceipt;
  if (mode === 'replan') {
    need(process.argv.includes('--verify-command-approved') && process.argv.includes('--operator-checkpoint-reported'),
      'VISIBLE_REJECTION_CHECKPOINT_REQUIRED');
    rejectionReceipt = read(arg('rejection'), arg('rejection-sha256'));
    need(rejectionReceipt.operation === 'reject' && rejectionReceipt.ok === true
      && rejectionReceipt.canary_sha256 === canaryHash && rejectionReceipt.rejections?.length === targets.length,
      'EXACT_REJECTION_RECEIPT_REQUIRED');
    const verifier = path.join(ROOT, 'tests/fixtures/native-first-canary/verify-postimages.cjs');
    need(!fs.lstatSync(verifier).isSymbolicLink() && sha(fs.readFileSync(verifier)) === arg('verifier-sha256'), 'FIXTURE_VERIFIER_SOURCE_CHANGED');
    for (const target of targets) {
      const rejected = rejectionReceipt.rejections.filter(value => value.run_id === target.run_id
        && value.wave_id === target.wave_id && value.task_context_id === target.task_context_id);
      const before = report.before.find(value => value.run_id === target.run_id && value.wave_id === target.wave_id);
      need(rejected.length === 1 && typeof rejected[0].report_id === 'string' && rejected[0].report_id
        && before.state === 'REPLAN' && before.completion_report_id === rejected[0].report_id
        && !before.proofs.some(proof => proof.status === 'passed'), 'EXACT_REJECTED_REPLAN_SCOPE_REQUIRED');
    }
    report.blockers = []; report.operator_report_acknowledgements = [];
    report.proof_replans = [];
  }
  report.controller_transfers = []; report.after = [];
  for (const target of targets) {
    need(sha(fs.readFileSync(descriptorGuard.file)) === descriptorGuard.sha256, 'PRODUCTION_DESCRIPTOR_CHANGED');
    targetsFromCanary(canary); // Recheck exact current bytes before each mutation.
    const key = 'native-first-semantic:' + sha(Buffer.from(`${mode}:${canaryHash}:${target.run_id}:${target.wave_id}`));
    const intent = path.join(HERE, `semantic-intent-${mode}-${target.run_id}-${target.wave_id}.json`);
    fs.writeFileSync(intent, JSON.stringify({ operation: 'semantic_acceptance_intent', canary_sha256: canaryHash,
      target, idempotency_key: key, created_at: new Date().toISOString(), automatic_retry_forbidden: true }) + '\n', { flag: 'wx' });
    await requestJson(settings.mcpPort, token, '/__control/hub', { action: 'heartbeat', client_id: CLIENT, client_type: 'electron' });
    const transfer = await requestJson(settings.mcpPort, token, '/__control/hub',
      { action: 'transfer_controller', run_id: target.run_id, target_client_id: CLIENT });
    need(transfer.ok === true && transfer.transferred === true && transfer.run_id === target.run_id
      && transfer.target_client_id === CLIENT, 'OPERATOR_CONTROLLER_TRANSFER_NOT_CONFIRMED');
    report.controller_transfers.push({ run_id: target.run_id, fencing_token: transfer.fencing_token,
      owner_client_id: transfer.owner_client_id, lease_id: transfer.lease_id });
    let acceptedTarget = target;
    if (mode === 'reject') {
      const beforeReject = projectAudit(await invoke('audit', target, { limit: 100, wave_id: undefined }), target);
      need(beforeReject.state === 'ACCEPTING' && !beforeReject.proofs.some(proof => proof.status === 'passed'),
        'ORIGINAL_WAVE_CHANGED_BEFORE_REJECTION');
      const rejection = await invoke('reject', target, {
        reason: 'Original exact patch and readback passed; this original wave has no independently executed proof. Preserve patch and replan proof only, without applying it again.',
        idempotency_key: key + ':reject' });
      need(rejection.rejected === true && rejection.state?.orchestration?.run_id === target.run_id
        && rejection.state.orchestration.wave_id === target.wave_id, 'ORIGINAL_WAVE_REJECTION_NOT_CONFIRMED');
      // Reject's returned state precedes final report publication. Observe the
      // persisted latch through supported audit; a raw completion report has
      // no report_id, and the earlier state may contain a superseded latch.
      const rejectedAudit = projectAudit(await invoke('audit', target, { limit: 100, wave_id: undefined }), target);
      need(rejectedAudit.state === 'REPLAN', 'ORIGINAL_REJECTION_REPLAN_NOT_CONFIRMED');
      const reportId = rejectedAudit.completion_report_id;
      need(typeof reportId === 'string' && reportId, 'EXACT_REJECTION_REPORT_REQUIRED');
      report.rejections.push({ run_id: target.run_id, wave_id: target.wave_id,
        task_context_id: target.task_context_id, report_id: reportId,
        state: rejectedAudit.state, patch_reapplied: false });
      emit({ ...report, operation: 'rejection-progress', targets: [target],
        requires_operator_visible_checkpoint: true });
      continue;
    }
    if (mode === 'replan') {
      const rejected = rejectionReceipt.rejections.find(value => value.run_id === target.run_id);
      const fresh = projectAudit(await invoke('audit', target, { limit: 100, wave_id: undefined }), target);
      need(fresh.state === 'REPLAN' && fresh.completion_report_id === rejected.report_id,
        'REJECTION_REPORT_CHANGED_BEFORE_ACKNOWLEDGEMENT');
      const acknowledgement = await invoke('update', target, { payload: {
        extension: 'operator_report_ack_v1', report_id: rejected.report_id } });
      need(acknowledgement.acknowledged === true && acknowledgement.report_id === rejected.report_id,
        'EXACT_OPERATOR_REPORT_ACKNOWLEDGEMENT_REQUIRED');
      report.operator_report_acknowledgements.push({ run_id: target.run_id, original_wave_id: target.wave_id,
        task_context_id: target.task_context_id, report_id: rejected.report_id, checkpoint_reported_by_operator: true });
      const verifierCommand = 'node tests/fixtures/native-first-canary/verify-postimages.cjs';
      let result = await invokeTool('agent_workflow', { task_context_id: target.task_context_id,
        workflow: 'custom', phase: 'execute', execution_mode: 'mcp_only', execution_route: 'deterministic',
        path: '.', workdir: '.', paths: target.acceptance_files.map(file => file.path),
        adopt_existing_files: target.acceptance_files, verification: 'none', commands: [verifierCommand],
        replan_reason: `Verify existing postimage from original action ${target.original_action_id}, original wave ${target.wave_id}; no patch replay.`,
        timeout_seconds: 60, idempotency_key: key + ':verify' });
      if (result.status === 'running' && result.background_operation) {
        const operationId = result.background_operation.operation_id;
        need(typeof operationId === 'string' && /^[A-Za-z0-9_-]{8,128}$/.test(operationId), 'ORIGINAL_BACKGROUND_HANDLE_REQUIRED');
        const deadline = Date.now() + 90000;
        for (;;) {
          emit({ ...report, operation: 'proof-background-progress', targets: [target],
            original_background_operation_id: operationId, requires_operator_visible_checkpoint: true });
          need(Date.now() < deadline, 'BACKGROUND_OBSERVATION_BOUND_AUDIT_ORIGINAL');
          const observation = await invoke('operation', target, { operation_id: operationId, wait_ms: 10000 });
          const operation = observation.background_operation;
          need(operation?.operation_id === operationId && operation.tool === 'agent_workflow'
            && samePath(operation.workspace, ROOT), 'BACKGROUND_ORIGINAL_HANDLE_CHANGED');
          if (operation.status === 'running') continue;
          need(operation.status === 'completed' && operation.result?.isError !== true
            && operation.result?.structuredContent, 'BACKGROUND_ORIGINAL_WORKFLOW_NOT_SUCCESSFUL');
          result = operation.result.structuredContent;
          break;
        }
      }
      const projected = result.orchestration?.orchestration || result.orchestration || {};
      need(projected.run_id === target.run_id && ID.test(projected.wave_id) && projected.wave_id !== target.wave_id
        && projected.orchestration_state === 'ACCEPTING' && result.execution?.ok === true,
        'PROOF_REPLAN_NEW_WAVE_NOT_CONFIRMED');
      acceptedTarget = { ...target, original_wave_id: target.wave_id, wave_id: projected.wave_id };
      const proofAudit = projectAudit(await invoke('audit', acceptedTarget, { limit: 100, wave_id: undefined }), acceptedTarget);
      need(proofAudit.state === 'ACCEPTING' && proofAudit.proofs.some(proof => realVerifierProof(proof, target, verifierCommand)),
        'REAL_REPLAN_PROOF_REQUIRED');
      report.proof_replans.push({ original_action_id: target.original_action_id,
        run_id: target.run_id, original_wave_id: target.wave_id, proof_wave_id: acceptedTarget.wave_id,
        task_context_id: target.task_context_id, verifier_command: verifierCommand,
        verifier_sha256: arg('verifier-sha256'), proof_audit: proofAudit,
        old_wave_accepted: false, patch_reapplied: false, native_execution_claimed: false });
      emit({ ...report, operation: 'replan-proof-progress', targets: [acceptedTarget] });
    }
    const result = await invoke('accept', acceptedTarget, { acceptance_files: target.acceptance_files, idempotency_key: key + ':accept' });
    need(result.accepted === true && result.state?.orchestration?.run_id === target.run_id
      && result.state.orchestration.wave_id === acceptedTarget.wave_id, 'EXACT_ACCEPTANCE_NOT_CONFIRMED');
    report.acceptance_performed = true; report.accepted_count += 1;
    report.after.push(projectAudit(await invoke('audit', acceptedTarget, { limit: 100, wave_id: undefined }), acceptedTarget));
    emit({ ...report, operation: 'accept-progress', targets: [acceptedTarget] });
  }
  if (mode === 'reject') report.requires_operator_visible_checkpoint = true;
  emit(report); app.quit();
}
module.exports = { finalCanary, finalContinuation, finalReadbackObserver, validateEvidenceSet, targetsFromCanary, projectAudit, toolPayload, realVerifierProof, readPhysicalFile, invocationMode: mode };
if (require.main === module || process.env.CODEX_ELECTRON_OPERATOR === '1') main().catch(error => {
  emit({ operation: 'failure', ok: false, code: String(error.code || 'SEMANTIC_HELPER_FAILED'),
    error_message: String(error.message || ''),
    error_stack: String(error.stack || '').slice(0, 4000),
    partial_mutation_possible: ['prepare-verifier', 'reject', 'accept', 'replan'].includes(mode), automatic_retry_forbidden: true,
    next_action: 'Inspect original RUN/WAVE through audit; do not repeat acceptance/transfer after uncertain response.' });
  try { require('electron').app.quit(); } catch {}
  process.exitCode = 1;
});
