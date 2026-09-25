const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { DatabaseSync } = require('node:sqlite');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { componentOwnsPath, componentOwners } = require('../electron/services/componentRevision');
const { resolvePythonExecutable } = require('./helpers/python-executable');
const {
  AcceptedCodeActivationController,
  acceptedReceipts,
  evaluateActivationEligibility,
  fingerprintPaths,
  gitStatus,
  parseGitStatus,
  workspaceIdentity
} = require('../electron/services/recoveryActionStore');

const REPO_ROOT = path.resolve(__dirname, '..');
const PYTHON = resolvePythonExecutable();

function lifecycleCounts() {
  return {
    active_tool_calls: 0,
    active_commands: 0,
    starting_commands: 0,
    active_background_operations: 0,
    active_managed_processes: 0,
    foreign_heavy_processes: 0,
    active_agent_lanes: 0,
    threshold_sensitive_stale_candidates: 0,
    owned_codex_sidecar_residues: 0
  };
}

function canonicalPythonFingerprint(workspace, identity) {
  const python = [
    'import json,sys',
    'from pathlib import Path',
    'from coding_tools_mcp.orchestration_ledger import fingerprint_paths',
    'value=json.loads(sys.stdin.read())',
    "print(fingerprint_paths(Path(value['root']), value['paths'], extra=value['extra']))"
  ].join(';');
  return execFileSync(PYTHON, ['-c', python], {
    input: JSON.stringify({
      root: workspace,
      paths: identity.entries.map((item) => item.path),
      extra: { head: identity.head, branch: identity.branch, entries: identity.entries }
    }),
    encoding: 'utf8',
    windowsHide: true,
    env: {
      ...process.env,
      PYTHONPATH: [path.join(REPO_ROOT, 'resources', 'coding-tools-mcp'), process.env.PYTHONPATH || '']
        .filter(Boolean)
        .join(path.delimiter)
    }
  }).trim();
}

function git(root, args) {
  return execFileSync('git', ['-C', root, ...args], { encoding: 'utf8', windowsHide: true });
}

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content, 'utf8');
}

function acceptedReceipt(workspace, relative) {
  const file = path.join(workspace, ...relative.split('/'));
  if (!fs.existsSync(file)) return { path: relative, state: 'missing', sha256: null, size_bytes: 0 };
  const content = fs.readFileSync(file);
  return { path: relative, state: 'file', sha256: crypto.createHash('sha256').update(content).digest('hex'), size_bytes: content.length };
}

function acceptedFileSet(workspace, files, { runId, waveId, source = 'task_modified_files' } = {}) {
  const receiptKind = source === 'explicit_acceptance_attestations'
    ? 'explicit_existing_file'
    : source === 'durable_wave_patch_surface' ? 'durable_wave_patch_surface' : 'task_modified_file';
  const receipts = files.map((relative) => {
    const receipt = acceptedReceipt(workspace, relative);
    return {
      ...receipt,
      receipt_kind: receiptKind,
      run_id: runId,
      wave_id: waveId,
      restart_safe: true,
      content_addressed: receipt.state === 'file',
      ...(receiptKind === 'explicit_existing_file' ? { expected_sha256: receipt.sha256 } : {})
    };
  });
  return {
    schema_version: 2,
    source,
    run_id: runId,
    wave_id: waveId,
    complete: true,
    count: receipts.length,
    total_bytes: receipts.reduce((total, item) => total + item.size_bytes, 0),
    files: receipts,
    incomplete_reasons: []
  };
}

function insertAcceptedCheckpoint(workspace, { checkpointId, runId, waveId, head, files, createdAt, worktreeFp = null }) {
  const database = new DatabaseSync(path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3'));
  const metadata = { accepted_files: acceptedFileSet(workspace, files, { runId, waveId }) };
  if (worktreeFp) metadata.worktree_fp = worktreeFp;
  database.prepare(`
    INSERT INTO checkpoints(checkpoint_id, run_id, wave_id, git_head, proof_fingerprint, status, created_at, metadata_json)
    VALUES (?, ?, ?, ?, ?, 'accepted', ?, ?)
  `).run(checkpointId, runId, waveId, head, 'a'.repeat(64), createdAt, JSON.stringify(metadata));
  database.close();
}

function canonicalPythonIdentity(workspace) {
  const python = [
    'import json,sys',
    'from pathlib import Path',
    'from coding_tools_mcp.server import Runtime',
    'runtime=Runtime(Path(sys.argv[1]))',
    'try:',
    '    status=runtime.git_status({"path": ".", "max_entries": 2000, "include_untracked": True})',
    '    identity=runtime._orchestration_workspace_identity(".")',
    '    print(json.dumps({"status": status, "identity": identity}, ensure_ascii=True))',
    'finally:',
    '    runtime.close()'
  ].join('\n');
  return JSON.parse(execFileSync(PYTHON, ['-c', python, workspace], {
    encoding: 'utf8',
    windowsHide: true,
    env: {
      ...process.env,
      PYTHONDONTWRITEBYTECODE: '1',
      PYTHONPATH: [path.join(REPO_ROOT, 'resources', 'coding-tools-mcp'), process.env.PYTHONPATH || '']
        .filter(Boolean)
        .join(path.delimiter)
    }
  }));
}

function checkpointFor(workspace, {
  checkpointId = 'checkpoint-evaluator-0001',
  runId = 'run-evaluator-0001',
  waveId = 'wave-evaluator-0001',
  head = git(workspace, ['rev-parse', 'HEAD']).trim(),
  files = ['electron/services/recoveryHost.js'],
  source = 'task_modified_files',
  proofFingerprint = files.length ? 'a'.repeat(64) : ''
} = {}) {
  return {
    checkpoint_id: checkpointId,
    run_id: runId,
    wave_id: waveId,
    git_head: head,
    proof_fingerprint: proofFingerprint,
    status: 'accepted',
    metadata: { accepted_files: acceptedFileSet(workspace, files, { runId, waveId, source }) }
  };
}

function postflightFor(request, overrides = {}) {
  const expected = request.expected_disk_revision;
  return {
    schema_version: 2,
    operation_id: request.operation_id,
    source_checkpoint_id: request.source_checkpoint.checkpoint_id,
    run_id: request.source_checkpoint.run_id,
    wave_id: request.source_checkpoint.wave_id,
    component: request.component,
    old_instance_state: 'RUNNING',
    old_instance_id: 'instance_old_000000000001',
    new_instance_id: 'instance_new_000000000001',
    already_current: false,
    expected_revision: expected,
    running_revision: expected,
    disk_revision: expected,
    revision_contract: 'current',
    started_at: '2026-01-01T00:00:00.000Z',
    completed_at: '2026-01-01T00:00:01.000Z',
    health_verified: true,
    postflight_verified: true,
    lifecycle_decision: {
      schema_version: 1,
      operation_id: request.operation_id,
      clean: true,
      code: 'READY',
      reason: 'idle',
      observed_at: '2026-01-01T00:00:01.000Z',
      canonical_lifecycle_observed: true,
      source_checkpoint_verified: true,
      fence_released: true,
      fenced: false,
      fence_operation_id: null,
      counts: lifecycleCounts(),
      unexplained_active_runs: 0,
      unbound_live_resource_residues: 0
    },
    ...overrides
  };
}

async function fixture(t, options = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-auto-activation-'));
  const workspace = path.join(root, 'workspace');
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(workspace, 'resources');
  fs.mkdirSync(workspace, { recursive: true });
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  git(workspace, ['init']);
  git(workspace, ['config', 'user.email', 'fixture@example.invalid']);
  git(workspace, ['config', 'user.name', 'Fixture']);
  git(workspace, ['config', 'status.showUntrackedFiles', 'no']);
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 1 };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'baseline']);
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 2 };\n');
  if (options.concurrentUntracked) {
    write(path.join(workspace, 'electron', 'services', 'nativeService.js'), 'module.exports = { concurrent: true };\n');
  }
  const identity = await workspaceIdentity(workspace);
  const coding = path.join(workspace, '.coding-tools');
  fs.mkdirSync(path.join(coding, 'orchestration'), { recursive: true });
  const runId = 'run-auto-activation-0001';
  const waveId = 'wave-auto-activation-0001';
  const checkpointId = 'checkpoint-auto-activation-0001';
  write(path.join(coding, 'task-state.json'), JSON.stringify({
    task_id: 'task-auto-activation-0001',
    status: 'completed',
    modified_files: [{ path: 'electron/services/recoveryHost.js', operation: 'modified' }],
    orchestration: { orchestration_state: 'CHECKPOINTED', run_id: runId, wave_id: waveId }
  }));
  const database = new DatabaseSync(path.join(coding, 'orchestration', 'ledger.sqlite3'));
  database.exec(`
    CREATE TABLE checkpoints (
      checkpoint_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      wave_id TEXT,
      git_head TEXT NOT NULL DEFAULT '',
      proof_fingerprint TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      metadata_json TEXT NOT NULL DEFAULT '{}'
    )
  `);
  database.close();
  insertAcceptedCheckpoint(workspace, {
    checkpointId,
    runId,
    waveId,
    head: identity.head,
    files: ['electron/services/recoveryHost.js'],
    createdAt: '2026-01-01T00:00:00.000Z',
    worktreeFp: identity.worktree_fp
  });
  const paths = createRuntimePaths({ dataRoot, resourcesRoot, appRoot: workspace });
  t.after(() => fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }));
  return { workspace, paths };
}

function controllerFor(paths, workspace, activation, options = {}) {
  const diskRevision = typeof options.diskRevision === 'function' ? options.diskRevision : () => String(options.diskRevision || 'b'.repeat(64));
  const runningRevision = typeof options.runningRevision === 'function' ? options.runningRevision : (component) => String(options.runningRevision || diskRevision(component));
  const activationAdapter = {
    ...activation,
    activate: async (request) => {
      const record = await activation.activate(request);
      const operationBound = { ...record, operation_id: record?.operation_id || request.operation_id };
      if (options.rawActivationResults === true || record?.state !== 'completed' || record?.result?.postflight) return operationBound;
      return { ...operationBound, result: { ...(record?.result || {}), postflight: postflightFor(request) } };
    }
  };
  return new AcceptedCodeActivationController({
    paths,
    settings: { load: () => ({ workspace }) },
    revisions: { disk: (component) => ({ revision: String(diskRevision(component)) }) },
    runningRevisionProvider: (component) => ({ running_revision: String(runningRevision(component)), disk_revision: String(diskRevision(component)) }),
    activation: activationAdapter,
    acceptedCheckpointProvider: options.acceptedCheckpointProvider,
    log: { warn() {} },
    intervalMs: 60000
  });
}

test('component ownership recognizes only fixed activation manifests', () => {
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/recoveryHost.js'), true);
  assert.equal(componentOwnsPath('recovery_host', 'resources/recovery-supervisor/recovery-supervisor.ps1'), true);
  assert.equal(componentOwnsPath('coding_mcp', 'resources/coding-tools-mcp/coding_tools_mcp/server.py'), true);
  assert.equal(componentOwnsPath('coding_mcp', 'resources/coding-tools-mcp/tests/test_coordination_state.py'), false);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/control-center.js'), true);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/browser.html'), true);
  assert.equal(componentOwnsPath('electron_ui', 'electron/services/chatEvaluationJournal.js'), false);
  assert.equal(componentOwnsPath('electron_ui', 'electron/services/nativeService.js'), false);
  assert.deepEqual(componentOwners('package.json'), ['recovery_host', 'electron_ui']);
  assert.deepEqual(componentOwners('docs/CURRENT_STATE.md'), []);
  assert.deepEqual(componentOwners('tests/runtime-lifecycle.test.js'), []);
});

test('activation eligibility accepts strict v2 receipts and deterministic component ownership', async (t) => {
  const { workspace } = await fixture(t);
  const checkpoint = checkpointFor(workspace);
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, true);
  assert.equal(result.code, 'ACTIVATABLE');
  assert.deepEqual(result.affected_components, ['recovery_host']);
  assert.equal(acceptedReceipts(checkpoint)?.[0].run_id, checkpoint.run_id);
});

test('accepted executor hub shell source maps exactly to electron_ui activation', async (t) => {
  const { workspace } = await fixture(t);
  write(path.join(workspace, 'renderer', 'browser.html'), '<main>executor hub</main>\n');
  const checkpoint = checkpointFor(workspace, { files: ['renderer/browser.html'] });
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, true);
  assert.equal(result.code, 'ACTIVATABLE');
  assert.equal(result.accepted_receipts_complete, true);
  assert.deepEqual(result.affected_components, ['electron_ui']);
});

test('activation eligibility rejects receipt provenance mismatch', async (t) => {
  const { workspace } = await fixture(t);
  const checkpoint = checkpointFor(workspace);
  checkpoint.metadata.accepted_files.files[0].wave_id = 'wave-other-0001';
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, false);
  assert.equal(result.code, 'RECEIPT_PROVENANCE_INVALID');
});

test('historical v1 accepted receipts remain non-activatable', async (t) => {
  const { workspace } = await fixture(t);
  const checkpoint = checkpointFor(workspace);
  checkpoint.metadata.accepted_files.schema_version = 1;
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, false);
  assert.equal(result.code, 'RECEIPT_SCHEMA_UNSUPPORTED');
});

test('activation eligibility rejects accepted source byte drift', async (t) => {
  const { workspace } = await fixture(t);
  const checkpoint = checkpointFor(workspace);
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { drifted: true };\n');
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, false);
  assert.equal(result.code, 'SOURCE_DRIFT');
});

test('activation eligibility rejects unmapped runtime-sensitive source', async (t) => {
  const { workspace } = await fixture(t);
  write(path.join(workspace, 'electron', 'services', 'unmappedRuntime.js'), 'module.exports = true;\n');
  const checkpoint = checkpointFor(workspace, { files: ['electron/services/unmappedRuntime.js'] });
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, false);
  assert.equal(result.code, 'COMPONENT_MAPPING_UNMAPPED');
});

test('true no-mutation accepted checkpoint is activation eligible without component targets', async (t) => {
  const { workspace } = await fixture(t);
  const checkpoint = checkpointFor(workspace, { files: [] });
  const result = evaluateActivationEligibility(checkpoint, { workspace, currentHead: checkpoint.git_head });
  assert.equal(result.eligible, true);
  assert.equal(result.accepted_receipts_complete, true);
  assert.deepEqual(result.affected_components, []);
  assert.equal(result.proof_fingerprint, '');
});

test('zero-target controller performs fresh lifecycle verification with the canonical empty proof', async (t) => {
  const { workspace, paths } = await fixture(t);
  const checkpoint = checkpointFor(workspace, { files: [] });
  let observed = null;
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { throw new Error('component preflight must not run'); },
    activate: async () => { throw new Error('component activation must not run'); },
    status: () => null,
    verifyCheckpointLifecycle: async (request) => {
      observed = request;
      return {
        schema_version: 1,
        operation_id: request.operationId,
        clean: true,
        code: 'READY',
        reason: 'idle',
        observed_at: '2026-08-25T08:00:01.000Z',
        canonical_lifecycle_observed: true,
        source_checkpoint_verified: true,
        fence_released: true,
        fenced: false,
        fence_operation_id: null,
        counts: lifecycleCounts(),
        unexplained_active_runs: 0,
        unbound_live_resource_residues: 0
      };
    }
  }, {
    acceptedCheckpointProvider: () => [checkpoint]
  });
  assert.equal(await controller.discover(), false);
  assert.equal(observed.sourceCheckpoint.proof_fingerprint, '');
  assert.equal(observed.sourceCheckpoint.checkpoint_id, checkpoint.checkpoint_id);
  const closure = controller.status().closure_input;
  assert.equal(closure.proof_fingerprint, '');
  assert.equal(closure.lifecycle_clean, true);
  assert.equal(closure.components_current, true);
});

test('newer component-bearing checkpoint takes source authority over an older zero-target lifecycle audit', async (t) => {
  const { workspace, paths } = await fixture(t);
  const sourcePath = 'resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py';
  const testPath = 'resources/coding-tools-mcp/tests/test_problem_lineage.py';
  write(path.join(workspace, ...sourcePath.split('/')), 'PROBLEM_LINEAGE = true;\n');
  write(path.join(workspace, ...testPath.split('/')), 'def test_problem_lineage():\n    assert True\n');
  const zeroTarget = checkpointFor(workspace, {
    checkpointId: 'checkpoint-zero-target-0001',
    runId: 'run-zero-target-0001',
    waveId: 'wave-zero-target-0001',
    files: []
  });
  const codingMcp = checkpointFor(workspace, {
    checkpointId: 'checkpoint-coding-mcp-0002',
    runId: 'run-coding-mcp-0002',
    waveId: 'wave-coding-mcp-0002',
    files: [sourcePath, testPath],
    source: 'explicit_acceptance_attestations'
  });
  let lifecycleVerifications = 0;
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { throw new Error('discover must not preflight a newly selected component'); },
    activate: async () => { throw new Error('discover must not activate a newly selected component'); },
    status: () => null,
    verifyCheckpointLifecycle: async () => {
      lifecycleVerifications += 1;
      throw new Error('the older zero-target audit must not replace current component source authority');
    }
  }, {
    acceptedCheckpointProvider: () => [zeroTarget, codingMcp]
  });

  assert.equal(await controller.discover(), true);
  const state = controller.loadState();
  assert.equal(state.active_checkpoint_id, codingMcp.checkpoint_id);
  assert.equal(state.closure_input.source_checkpoint_id, codingMcp.checkpoint_id);
  assert.deepEqual(state.closure_input.affected_components, ['coding_mcp']);
  assert.equal(state.processed_checkpoint_ids.includes(zeroTarget.checkpoint_id), false);
  assert.equal(lifecycleVerifications, 0);
});

test('processed component source is retained instead of being replaced by an older zero-target checkpoint', async (t) => {
  const { workspace, paths } = await fixture(t);
  const sourcePath = 'resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py';
  const testPath = 'resources/coding-tools-mcp/tests/test_problem_lineage.py';
  write(path.join(workspace, ...sourcePath.split('/')), 'PROBLEM_LINEAGE = true;\n');
  write(path.join(workspace, ...testPath.split('/')), 'def test_problem_lineage():\n    assert True\n');
  const zeroTarget = checkpointFor(workspace, {
    checkpointId: 'checkpoint-zero-target-0003',
    runId: 'run-zero-target-0003',
    waveId: 'wave-zero-target-0003',
    files: []
  });
  const codingMcp = checkpointFor(workspace, {
    checkpointId: 'checkpoint-coding-mcp-0004',
    runId: 'run-coding-mcp-0004',
    waveId: 'wave-coding-mcp-0004',
    files: [sourcePath, testPath],
    source: 'explicit_acceptance_attestations'
  });
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { throw new Error('a retained source authority must not be reactivated'); },
    activate: async () => { throw new Error('a retained source authority must not be reactivated'); },
    status: () => null,
    verifyCheckpointLifecycle: async () => { throw new Error('the older zero-target audit must not overwrite component authority'); }
  }, {
    acceptedCheckpointProvider: () => [zeroTarget, codingMcp]
  });
  const head = git(workspace, ['rev-parse', 'HEAD']).trim();
  const state = controller.loadState();
  state.processed_checkpoint_ids = [codingMcp.checkpoint_id];
  state.closure_input = controller.newClosureInput(evaluateActivationEligibility(codingMcp, { workspace, currentHead: head }));
  controller.saveState(state);

  assert.equal(await controller.discover(), false);
  const after = controller.loadState();
  assert.equal(after.closure_input.source_checkpoint_id, codingMcp.checkpoint_id);
  assert.deepEqual(after.closure_input.affected_components, ['coding_mcp']);
  assert.equal(after.processed_checkpoint_ids.includes(zeroTarget.checkpoint_id), false);
});

test('empty proof is rejected for a mutation-bearing checkpoint and identity input is never normalized', async (t) => {
  const { workspace } = await fixture(t);
  const mutationBearing = checkpointFor(workspace, { proofFingerprint: '' });
  assert.equal(evaluateActivationEligibility(mutationBearing, {
    workspace,
    currentHead: mutationBearing.git_head
  }).code, 'CHECKPOINT_IDENTITY_INVALID');

  for (const overrides of [
    { checkpoint_id: ` ${'checkpoint-evaluator-0001'}` },
    { run_id: 'run-evaluator-0001 ' },
    { wave_id: 123 },
    { proof_fingerprint: 'A'.repeat(64) },
    { git_head: mutationBearing.git_head.toUpperCase() }
  ]) {
    const checkpoint = { ...checkpointFor(workspace), ...overrides };
    const result = evaluateActivationEligibility(checkpoint, {
      workspace,
      currentHead: checkpointFor(workspace).git_head
    });
    assert.equal(result.eligible, false);
    assert.equal(result.code, 'CHECKPOINT_IDENTITY_INVALID');
  }
});

test('controller status identifies the V2 baseline and accepted-receipt trust model', async (t) => {
  const { workspace, paths } = await fixture(t);
  const controller = controllerFor(paths, workspace, {
    preflight: async () => ({ safe: false, code: 'RUNTIME_BUSY' }),
    activate: async () => ({ state: 'refused' }),
    status: () => null
  });
  assert.equal(controller.status().trust_model, 'running_baseline_accepted_receipts_v2');
  assert.equal(controller.status().continuity_mode, 'detached_runtime_children_v1');
});

test('idle controller with an established baseline skips component revision identity probes until accepted work appears', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskReads = 0;
  let runningReads = 0;
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { throw new Error('idle controller must not enter preflight'); },
    activate: async () => { throw new Error('idle controller must not activate'); },
    status: () => null
  }, {
    acceptedCheckpointProvider: () => [],
    diskRevision: () => { diskReads += 1; return 'b'.repeat(64); },
    runningRevision: () => { runningReads += 1; return 'b'.repeat(64); }
  });
  const state = controller.loadState();
  await controller.ensureBaseline(workspace, state, await gitStatus(workspace, true));
  const baselineDiskReads = diskReads;
  const baselineRunningReads = runningReads;
  assert.ok(baselineDiskReads > 0);
  assert.ok(baselineRunningReads > 0);

  await controller.tick();

  assert.equal(diskReads, baselineDiskReads);
  assert.equal(runningReads, baselineRunningReads);
});

test('Recovery Host worktree fingerprint is byte-compatible with canonical Python acceptance fingerprint', async (t) => {
  const { workspace } = await fixture(t);
  const identity = await workspaceIdentity(workspace);
  assert.equal(identity.worktree_fp, canonicalPythonFingerprint(workspace, identity));
});

test('NUL-delimited Git parsers preserve Unicode paths and Node/Python worktree identity remains byte-compatible', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-fingerprint-unicode-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }));
  git(root, ['init']);
  git(root, ['config', 'user.email', 'fixture@example.invalid']);
  git(root, ['config', 'user.name', 'Fixture']);
  const relative = 'café.js';
  write(path.join(root, relative), 'module.exports = "first";\n');
  git(root, ['add', relative]);
  git(root, ['commit', '-m', 'unicode baseline']);
  write(path.join(root, relative), 'module.exports = "second";\n');

  const pythonFirst = canonicalPythonIdentity(root);
  const nodeStatusFirst = await gitStatus(root, true);
  const nodeFirst = await workspaceIdentity(root);
  const sourceEntries = (entries) => entries.filter((item) => {
    const key = process.platform === 'win32' ? item.path.toLowerCase() : item.path;
    return key !== '.coding-tools' && !key.startsWith('.coding-tools/');
  });
  assert.deepEqual(sourceEntries(nodeStatusFirst.entries), sourceEntries(pythonFirst.status.entries));
  assert.equal(nodeFirst.entries[0].path, relative);
  assert.equal(nodeFirst.worktree_fp, pythonFirst.identity.worktree_fp);

  write(path.join(root, relative), 'module.exports = "third";\n');
  const pythonSecond = canonicalPythonIdentity(root);
  const nodeSecond = await workspaceIdentity(root);
  assert.equal(nodeSecond.worktree_fp, pythonSecond.identity.worktree_fp);
  assert.notEqual(nodeSecond.worktree_fp, nodeFirst.worktree_fp);
});

test('NUL-delimited Git parser consumes rename/copy source paths and fails closed on malformed input', () => {
  const parsed = parseGitStatus(Buffer.from(
    '## main...origin/main [ahead 1]\0R  current.js\0original.js\0C  copied.js\0source.js\0',
    'utf8'
  ));
  assert.equal(parsed.branch, 'main');
  assert.deepEqual(parsed.entries, [
    { path: 'current.js', original_path: 'original.js', index_status: 'R', worktree_status: ' ' },
    { path: 'copied.js', original_path: 'source.js', index_status: 'C', worktree_status: ' ' }
  ]);

  assert.throws(
    () => parseGitStatus(Buffer.from([0x23, 0x23, 0x20, 0x6d, 0x61, 0x69, 0x6e, 0x00, 0x3f, 0x3f, 0x20, 0xff, 0x00])),
    { code: 'AUTO_ACTIVATION_GIT_MALFORMED' }
  );
  assert.throws(
    () => parseGitStatus(Buffer.from('## main\0R  current.js\0', 'utf8')),
    { code: 'AUTO_ACTIVATION_GIT_MALFORMED' }
  );
  assert.throws(
    () => parseGitStatus(Buffer.from(['## main', ...Array.from({ length: 2001 }, (_unused, index) => `?? file-${index}.js`), ''].join('\0'), 'utf8')),
    { code: 'AUTO_ACTIVATION_GIT_TOO_LARGE' }
  );
});

test('Recovery Host and Python fingerprints remain byte-compatible beyond 500 entries', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-fingerprint-many-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }));
  const entries = Array.from({ length: 501 }, (_unused, index) => ({
    path: `source/missing-${String(index).padStart(4, '0')}.js`,
    index_status: '',
    worktree_status: '?'
  }));
  const identity = { head: 'a'.repeat(40), branch: 'main', entries };
  const electronFingerprint = fingerprintPaths(root, entries, identity.head, identity.branch);
  assert.equal(electronFingerprint, canonicalPythonFingerprint(root, identity));
});

test('workspace identity forces complete untracked discovery despite Git configuration', async (t) => {
  const { workspace } = await fixture(t, { concurrentUntracked: true });
  assert.equal(git(workspace, ['config', 'status.showUntrackedFiles']).trim(), 'no');
  const identity = await workspaceIdentity(workspace);
  assert.equal(identity.entries.some((item) => item.path === 'electron/services/nativeService.js'), true);
  assert.equal(identity.worktree_fp, canonicalPythonFingerprint(workspace, identity));
});

test('Windows workspace identity excludes case aliases of protected runtime evidence', {
  skip: process.platform !== 'win32' ? 'Windows protected-path aliases are case-insensitive' : false
}, async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-fingerprint-protected-case-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }));
  git(root, ['init']);
  git(root, ['config', 'user.email', 'fixture@example.invalid']);
  git(root, ['config', 'user.name', 'Fixture']);
  write(path.join(root, 'app.js'), 'module.exports = true;\n');
  git(root, ['add', 'app.js']);
  git(root, ['commit', '-m', 'baseline']);
  write(path.join(root, '.CODING-TOOLS', 'runtime.json'), '{}\n');
  const identity = await workspaceIdentity(root);
  assert.deepEqual(identity.entries, []);
  assert.equal(identity.worktree_fp, canonicalPythonFingerprint(root, identity));
});

test('Recovery Host and Python fingerprints use the same outside marker for linked targets', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-fingerprint-link-'));
  const workspace = path.join(root, 'workspace');
  const outside = path.join(root, 'outside');
  fs.mkdirSync(workspace, { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  write(path.join(outside, 'secret.txt'), 'outside bytes must not enter the source fingerprint\n');
  try {
    fs.symlinkSync(outside, path.join(workspace, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  } catch (error) {
    fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 });
    t.skip(`directory link creation unavailable: ${String(error?.code || error?.name || 'Error')}`);
    return;
  }
  t.after(() => fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }));
  const entries = [{ path: 'linked/secret.txt', index_status: '', worktree_status: 'M' }];
  const identity = { head: 'b'.repeat(40), branch: 'main', entries };
  const electronFingerprint = fingerprintPaths(workspace, entries, identity.head, identity.branch);
  assert.equal(electronFingerprint, canonicalPythonFingerprint(workspace, identity));
});

test('finally accepted tracked recovery-host code activates automatically from canonical checkpoint', async (t) => {
  const { workspace, paths } = await fixture(t);
  const calls = { preflight: 0, activate: 0, request: null };
  const activation = {
    preflight: async () => { calls.preflight += 1; return { safe: true, code: 'READY' }; },
    activate: async (request) => {
      calls.activate += 1;
      calls.request = request;
      return { state: 'completed', component: request.component, result: { activated: true }, expires_at_unix_ms: request.expires_at_unix_ms };
    },
    status: () => { throw new Error('not expected'); }
  };
  const controller = controllerFor(paths, workspace, activation);
  await controller.tick();
  assert.equal(calls.preflight, 1);
  assert.equal(calls.activate, 1);
  assert.deepEqual(calls.request.source_checkpoint, {
    checkpoint_id: 'checkpoint-auto-activation-0001',
    run_id: 'run-auto-activation-0001',
    wave_id: 'wave-auto-activation-0001',
    proof_fingerprint: 'a'.repeat(64),
    git_head: git(workspace, ['rev-parse', 'HEAD']).trim()
  });
  assert.equal(controller.status().completed, 1);
  assert.equal(controller.status().blocked, 0);
  assert.equal(controller.status().closure_input.source_checkpoint_id, 'checkpoint-auto-activation-0001');
  assert.deepEqual(controller.status().closure_input.affected_components, ['recovery_host']);
  assert.equal(controller.status().closure_input.components_current, true);
  assert.equal(controller.status().closure_input.lifecycle_clean, true);
});

test('completed action without verified postflight cannot advance baseline or close components', async (t) => {
  const { workspace, paths } = await fixture(t);
  const controller = controllerFor(paths, workspace, {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async () => ({ state: 'completed', result: { activated: true } }),
    status: () => null
  }, {
    diskRevision: () => 'c'.repeat(64),
    runningRevision: () => 'b'.repeat(64),
    rawActivationResults: true
  });
  await controller.tick();
  const state = controller.loadState();
  assert.equal(state.intents[0].state, 'failed');
  assert.equal(state.intents[0].error.code, 'POSTFLIGHT_UNVERIFIED');
  assert.equal(state.baseline.components.recovery_host.revision, 'b'.repeat(64));
  assert.equal(state.closure_input.components_current, false);
});

test('checkpoint-bound verified postflight advances baseline and closes affected components', async (t) => {
  const { workspace, paths } = await fixture(t);
  const controller = controllerFor(paths, workspace, {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async (request) => ({
      state: 'completed',
      result: { activated: true, postflight: postflightFor(request) }
    }),
    status: () => null
  }, {
    diskRevision: () => 'c'.repeat(64),
    runningRevision: () => 'b'.repeat(64),
    rawActivationResults: true
  });
  await controller.tick();
  const state = controller.loadState();
  assert.equal(state.intents[0].state, 'completed');
  assert.equal(state.baseline.components.recovery_host.revision, 'c'.repeat(64));
  assert.equal(state.closure_input.components_current, true);
  assert.equal(state.closure_input.postflight_receipts.recovery_host.postflight_verified, true);
});

test('automatic activation defers while canonical preflight is busy and retries after it becomes safe', async (t) => {
  const { workspace, paths } = await fixture(t);
  let safe = false;
  let activations = 0;
  const activation = {
    preflight: async () => safe ? { safe: true, code: 'READY' } : { safe: false, code: 'RUNTIME_BUSY', runtime: { reason: 'orchestration_active' } },
    activate: async (request) => {
      activations += 1;
      return { state: 'completed', result: { activated: true }, expires_at_unix_ms: request.expires_at_unix_ms };
    },
    status: () => { throw new Error('not expected'); }
  };
  const controller = controllerFor(paths, workspace, activation);
  await controller.tick();
  assert.equal(activations, 0);
  assert.equal(controller.status().deferred, 1);
  safe = true;
  await controller.tick();
  assert.equal(activations, 1);
  assert.equal(controller.status().completed, 1);
});

test('pre-existing dirty component source is trusted only as a matching running baseline', async (t) => {
  const { workspace, paths } = await fixture(t, { concurrentUntracked: true });
  let activations = 0;
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async () => { activations += 1; return { state: 'completed' }; },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation);
  await controller.tick();
  assert.equal(activations, 1);
  const state = JSON.parse(fs.readFileSync(paths.acceptedCodeActivationFile(), 'utf8'));
  assert.equal(state.intents[0].state, 'completed');
  assert.equal(state.baseline.components.recovery_host.receipts.some((item) => item.path === 'electron/services/nativeService.js'), true, JSON.stringify({ baseline: state.baseline.components.recovery_host, trusted: state.intents[0].trusted_receipts }));
});

test('component bytes changed after running baseline are blocked without final acceptance', async (t) => {
  const { workspace, paths } = await fixture(t, { concurrentUntracked: true });
  let activations = 0;
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async () => { activations += 1; return { state: 'completed' }; },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation);
  const baselineState = controller.loadState();
  await controller.ensureBaseline(workspace, baselineState, await gitStatus(workspace, true));
  write(path.join(workspace, 'electron', 'services', 'nativeService.js'), 'module.exports = { concurrent: false, changedAfterBaseline: true };\n');
  await controller.tick();
  assert.equal(activations, 0);
  const state = JSON.parse(fs.readFileSync(paths.acceptedCodeActivationFile(), 'utf8'));
  assert.equal(state.intents[0].state, 'blocked');
  assert.equal(state.intents[0].error.code, 'UNACCEPTED_COMPONENT_DIRTY');
  assert.deepEqual(state.intents[0].error.files, ['electron/services/nativeService.js']);
});

test('later accepted untracked source activates with prior accepted dirty wave through receipt union', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskRevision = 'b'.repeat(64);
  let runningRevision = diskRevision;
  const activations = [];
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async (request) => {
      activations.push(request.expected_disk_revision);
      runningRevision = request.expected_disk_revision;
      return { state: 'completed', result: { activated: true } };
    },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, {
    diskRevision: () => diskRevision,
    runningRevision: () => runningRevision
  });
  await controller.tick();
  assert.deepEqual(activations, ['b'.repeat(64)]);

  write(path.join(workspace, 'electron', 'services', 'nativeService.js'), 'module.exports = { acceptedUntracked: true };\n');
  diskRevision = 'c'.repeat(64);
  const head = git(workspace, ['rev-parse', 'HEAD']).trim();
  insertAcceptedCheckpoint(workspace, {
    checkpointId: 'checkpoint-auto-activation-0002',
    runId: 'run-auto-activation-0002',
    waveId: 'wave-auto-activation-0002',
    head,
    files: ['electron/services/nativeService.js'],
    createdAt: '2026-01-01T00:00:01.000Z'
  });

  await controller.tick();
  assert.deepEqual(activations, ['b'.repeat(64), 'c'.repeat(64)]);
  const state = JSON.parse(fs.readFileSync(paths.acceptedCodeActivationFile(), 'utf8'));
  assert.equal(state.processed_checkpoint_ids.includes('checkpoint-auto-activation-0001'), true);
  const second = state.intents.find((item) => item.checkpoint_id === 'checkpoint-auto-activation-0002');
  assert.equal(second.state, 'completed');
  assert.equal(state.baseline.components.recovery_host.revision, 'c'.repeat(64));
  assert.equal(state.baseline.components.recovery_host.receipts.some((item) => item.path === 'electron/services/nativeService.js'), true, JSON.stringify(state.baseline.components.recovery_host));
});

test('accepted committed recovery-host bytes on a new Git HEAD activate from the prior component baseline', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskRevision = 'b'.repeat(64);
  let runningRevision = diskRevision;
  const activations = [];
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async (request) => { activations.push(request.expected_disk_revision); runningRevision = request.expected_disk_revision; return { state: 'completed', result: { activated: true } }; },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, { diskRevision: () => diskRevision, runningRevision: () => runningRevision });
  await controller.tick();
  const oldHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 3 };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'accepted new head']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  diskRevision = 'c'.repeat(64);
  insertAcceptedCheckpoint(workspace, { checkpointId: 'checkpoint-auto-activation-new-head', runId: 'run-auto-activation-new-head', waveId: 'wave-auto-activation-new-head', head: newHead, files: ['electron/services/recoveryHost.js'], createdAt: '2026-01-01T00:00:02.000Z' });
  await controller.tick();
  const state = controller.loadState();
  assert.notEqual(oldHead, newHead);
  assert.deepEqual(activations, ['b'.repeat(64), 'c'.repeat(64)]);
  assert.equal(state.baseline.components.recovery_host.head, newHead);
  assert.equal(state.baseline.components.recovery_host.revision, 'c'.repeat(64));
});

test('component activation bounds the committed delta after ownership filtering', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskRevision = 'b'.repeat(64);
  let runningRevision = diskRevision;
  const activations = [];
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async (request) => {
      activations.push(request.expected_disk_revision);
      runningRevision = request.expected_disk_revision;
      return { state: 'completed', result: { activated: true } };
    },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, {
    diskRevision: () => diskRevision,
    runningRevision: () => runningRevision
  });
  await controller.tick();

  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 3 };\n');
  for (let index = 0; index < 2001; index += 1) {
    write(path.join(workspace, 'docs', 'history', `entry-${String(index).padStart(4, '0')}.txt`), 'historical non-component path\n');
  }
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'large repository delta with one recovery-host change']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  diskRevision = 'c'.repeat(64);
  insertAcceptedCheckpoint(workspace, {
    checkpointId: 'checkpoint-auto-activation-component-filter',
    runId: 'run-auto-activation-component-filter',
    waveId: 'wave-auto-activation-component-filter',
    head: newHead,
    files: ['electron/services/recoveryHost.js'],
    createdAt: '2026-01-01T00:00:02.500Z'
  });

  await controller.tick();
  const state = controller.loadState();
  const intent = state.intents.find((item) => item.checkpoint_id === 'checkpoint-auto-activation-component-filter');
  assert.deepEqual(activations, ['b'.repeat(64), 'c'.repeat(64)]);
  assert.equal(intent.state, 'completed');
  assert.equal(controller.status().last_error, null);
});

test('unaccepted committed component delta blocks a new-HEAD checkpoint', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskRevision = 'b'.repeat(64);
  let runningRevision = diskRevision;
  const activation = {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async (request) => { runningRevision = request.expected_disk_revision; return { state: 'completed' }; },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, { diskRevision: () => diskRevision, runningRevision: () => runningRevision });
  await controller.tick();
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 3, unaccepted: true };\n');
  write(path.join(workspace, 'electron', 'services', 'nativeService.js'), 'module.exports = { accepted: true };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'mixed trust head']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  diskRevision = 'c'.repeat(64);
  insertAcceptedCheckpoint(workspace, { checkpointId: 'checkpoint-auto-activation-partial-head', runId: 'run-auto-activation-partial-head', waveId: 'wave-auto-activation-partial-head', head: newHead, files: ['electron/services/nativeService.js'], createdAt: '2026-01-01T00:00:03.000Z' });
  await controller.tick();
  const state = controller.loadState();
  const intent = state.intents.find((item) => item.checkpoint_id === 'checkpoint-auto-activation-partial-head');
  assert.equal(intent.state, 'blocked');
  assert.equal(intent.error.code, 'UNACCEPTED_COMPONENT_DIRTY');
  assert.deepEqual(intent.error.files, ['electron/services/recoveryHost.js']);
});

test('ALREADY_CURRENT accepted bytes on a new HEAD advance the trusted component row', async (t) => {
  const { workspace, paths } = await fixture(t);
  const stableRevision = 'd'.repeat(64);
  let recoveryDisk = 'b'.repeat(64);
  let recoveryRunning = recoveryDisk;
  let activationCalls = 0;
  let alreadyCurrent = false;
  const activation = {
    preflight: async () => alreadyCurrent ? ({ safe: true, code: 'ALREADY_CURRENT' }) : ({ safe: true, code: 'READY' }),
    activate: async (request) => { activationCalls += 1; recoveryRunning = request.expected_disk_revision; return { state: 'completed', result: alreadyCurrent ? { activated: false, already_current: true } : { activated: true } }; },
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, {
    diskRevision: (component) => component === 'recovery_host' ? recoveryDisk : stableRevision,
    runningRevision: (component) => component === 'recovery_host' ? recoveryRunning : stableRevision
  });
  await controller.tick();
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 4 };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'externally loaded accepted head']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  recoveryDisk = 'e'.repeat(64);
  recoveryRunning = recoveryDisk;
  alreadyCurrent = true;
  insertAcceptedCheckpoint(workspace, { checkpointId: 'checkpoint-auto-activation-already-current', runId: 'run-auto-activation-already-current', waveId: 'wave-auto-activation-already-current', head: newHead, files: ['electron/services/recoveryHost.js'], createdAt: '2026-01-01T00:00:04.000Z' });
  await controller.tick();
  const state = controller.loadState();
  const intent = state.intents.find((item) => item.checkpoint_id === 'checkpoint-auto-activation-already-current');
  assert.equal(activationCalls, 2);
  assert.equal(intent.state, 'completed');
  assert.equal(intent.result.already_current, true);
  assert.equal(state.baseline.components.recovery_host.head, newHead);
  assert.equal(state.baseline.components.recovery_host.revision, 'e'.repeat(64));
});

test('unchanged component may advance its head while changed component remains on the prior head', async (t) => {
  const { workspace, paths } = await fixture(t);
  const oldHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  let recoveryDisk = 'b'.repeat(64);
  const recoveryRunning = 'b'.repeat(64);
  const uiRevision = 'd'.repeat(64);
  let busy = false;
  const activation = {
    preflight: async () => busy ? { safe: false, code: 'RUNTIME_BUSY', runtime: { reason: 'test' } } : { safe: true, code: 'READY' },
    activate: async () => ({ state: 'completed' }),
    status: () => null
  };
  const controller = controllerFor(paths, workspace, activation, {
    diskRevision: (component) => component === 'recovery_host' ? recoveryDisk : uiRevision,
    runningRevision: (component) => component === 'recovery_host' ? recoveryRunning : uiRevision
  });
  await controller.tick();
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 5 };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'component-specific head']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  recoveryDisk = 'f'.repeat(64);
  insertAcceptedCheckpoint(workspace, { checkpointId: 'checkpoint-auto-activation-mixed-head', runId: 'run-auto-activation-mixed-head', waveId: 'wave-auto-activation-mixed-head', head: newHead, files: ['electron/services/recoveryHost.js'], createdAt: '2026-01-01T00:00:05.000Z' });
  busy = true;
  await controller.tick();
  const state = controller.loadState();
  assert.equal(state.baseline.components.recovery_host.head, oldHead);
  assert.equal(state.baseline.components.electron_ui.head, newHead);
});

test('legacy V2 baseline rows inherit the legacy head without trusting changed new-HEAD bytes', async (t) => {
  const { workspace, paths } = await fixture(t);
  let diskRevision = 'b'.repeat(64);
  const runningRevision = 'b'.repeat(64);
  const controller = controllerFor(paths, workspace, { preflight: async () => ({ safe: false, code: 'RUNTIME_BUSY' }), activate: async () => ({ state: 'refused' }), status: () => null }, { diskRevision: () => diskRevision, runningRevision: () => runningRevision });
  const initial = controller.loadState();
  await controller.ensureBaseline(workspace, initial, await gitStatus(workspace, true));
  const legacy = JSON.parse(fs.readFileSync(paths.acceptedCodeActivationFile(), 'utf8'));
  const legacyHead = legacy.baseline.head;
  for (const row of Object.values(legacy.baseline.components)) delete row.head;
  fs.writeFileSync(paths.acceptedCodeActivationFile(), JSON.stringify(legacy), 'utf8');
  write(path.join(workspace, 'electron', 'services', 'recoveryHost.js'), 'module.exports = { version: 6, legacyGuard: true };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'unaccepted legacy transition']);
  diskRevision = 'c'.repeat(64);
  await controller.tick();
  const state = controller.loadState();
  assert.equal(state.baseline.components.recovery_host.head, legacyHead);
  assert.equal(state.baseline.components.recovery_host.revision, 'b'.repeat(64));
});

test('automatic activation skips terminal intents and advances the next pending component', async (t) => {
  const { workspace, paths } = await fixture(t);
  const controller = controllerFor(paths, workspace, {
    preflight: async () => ({ safe: true, code: 'READY' }),
    activate: async () => ({ state: 'completed' }),
    status: () => null
  });
  controller.discover = async () => false;
  const checkpointId = 'checkpoint-terminal-skip-0001';
  const state = controller.loadState();
  state.active_checkpoint_id = checkpointId;
  state.intents = [
    { checkpoint_id: checkpointId, component: 'recovery_host', state: 'failed' },
    { checkpoint_id: checkpointId, component: 'coding_mcp', state: 'blocked' },
    { checkpoint_id: checkpointId, component: 'electron_ui', state: 'pending' }
  ];
  controller.saveState(state);
  const processed = [];
  controller.processIntent = async (current, intent) => {
    processed.push(intent.component);
    intent.state = 'completed';
    controller.saveState(current);
  };
  await controller.tick();
  assert.deepEqual(processed, ['electron_ui']);
});

test('stale active checkpoint is superseded and current-head accepted work can progress', async (t) => {
  const { workspace, paths } = await fixture(t);
  const oldHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  let preflights = 0;
  let activations = 0;
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { preflights += 1; return { safe: true, code: 'READY' }; },
    activate: async () => { activations += 1; return { state: 'completed', result: { activated: true } }; },
    status: () => { throw new Error('stale intent without an operation must not be polled'); }
  });
  const initial = controller.loadState();
  await controller.ensureBaseline(workspace, initial, await gitStatus(workspace, true));

  write(path.join(workspace, 'renderer', 'control-center.js'), 'module.exports = { currentHead: true };\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'current accepted head']);
  const newHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  insertAcceptedCheckpoint(workspace, {
    checkpointId: 'checkpoint-current-head-0002',
    runId: 'run-current-head-0002',
    waveId: 'wave-current-head-0002',
    head: newHead,
    files: ['renderer/control-center.js'],
    createdAt: '2026-01-01T00:00:06.000Z'
  });

  const stale = controller.loadState();
  stale.active_checkpoint_id = 'checkpoint-auto-activation-0001';
  stale.intents = [
    { checkpoint_id: 'checkpoint-auto-activation-0001', component: 'recovery_host', state: 'failed', accepted_head: oldHead, current_operation_id: null },
    { checkpoint_id: 'checkpoint-auto-activation-0001', component: 'coding_mcp', state: 'blocked', accepted_head: oldHead, current_operation_id: null },
    { checkpoint_id: 'checkpoint-auto-activation-0001', component: 'electron_ui', state: 'pending', accepted_head: oldHead, current_operation_id: null }
  ];
  controller.saveState(stale);

  await controller.tick();
  const state = controller.loadState();
  const oldUi = state.intents.find((item) => item.checkpoint_id === 'checkpoint-auto-activation-0001' && item.component === 'electron_ui');
  const current = state.intents.find((item) => item.checkpoint_id === 'checkpoint-current-head-0002');
  assert.notEqual(oldHead, newHead);
  assert.equal(oldUi.state, 'superseded');
  assert.equal(oldUi.error.code, 'BASE_HEAD_CHANGED');
  assert.equal(state.processed_checkpoint_ids.includes('checkpoint-auto-activation-0001'), true);
  assert.equal(current.state, 'completed');
  assert.equal(current.accepted_head, newHead);
  assert.equal(preflights, 1);
  assert.equal(activations, 1);
  assert.equal(controller.status().last_error, null);
});

test('stale awaiting intent with an in-flight operation is reconciled instead of superseded', async (t) => {
  const { workspace, paths } = await fixture(t);
  const oldHead = git(workspace, ['rev-parse', 'HEAD']).trim();
  let statusCalls = 0;
  const controller = controllerFor(paths, workspace, {
    preflight: async () => { throw new Error('in-flight stale intent must not start another activation'); },
    activate: async () => { throw new Error('in-flight stale intent must not start another activation'); },
    status: (operationId) => {
      statusCalls += 1;
      assert.equal(operationId, 'auto_inflight_operation_0001');
      return { state: 'accepted', expires_at_unix_ms: Date.now() + 60_000 };
    }
  });
  const initial = controller.loadState();
  await controller.ensureBaseline(workspace, initial, await gitStatus(workspace, true));
  write(path.join(workspace, 'README-test-head.txt'), 'new head\n');
  git(workspace, ['add', '.']);
  git(workspace, ['commit', '-m', 'head changes while operation is active']);

  const state = controller.loadState();
  state.active_checkpoint_id = 'checkpoint-inflight-old-head';
  state.intents = [{
    checkpoint_id: 'checkpoint-inflight-old-head',
    component: 'recovery_host',
    state: 'awaiting',
    accepted_head: oldHead,
    current_operation_id: 'auto_inflight_operation_0001',
    attempt: 1
  }];
  controller.saveState(state);

  await controller.tick();
  const after = controller.loadState();
  assert.equal(statusCalls, 1);
  assert.equal(after.intents[0].state, 'awaiting');
  assert.equal(after.intents[0].current_operation_id, 'auto_inflight_operation_0001');
  assert.equal(after.active_checkpoint_id, 'checkpoint-inflight-old-head');
  assert.equal(controller.status().last_error, null);
});
