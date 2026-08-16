const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { DatabaseSync } = require('node:sqlite');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { componentOwnsPath } = require('../electron/services/componentRevision');
const {
  AcceptedCodeActivationController,
  gitStatus,
  workspaceIdentity
} = require('../electron/services/recoveryActionStore');

const REPO_ROOT = path.resolve(__dirname, '..');

function canonicalPythonFingerprint(workspace, identity) {
  const python = [
    'import json,sys',
    'from pathlib import Path',
    'from coding_tools_mcp.orchestration_ledger import fingerprint_paths',
    'value=json.loads(sys.stdin.read())',
    "print(fingerprint_paths(Path(value['root']), value['paths'], extra=value['extra']))"
  ].join(';');
  return execFileSync('python', ['-c', python], {
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

function acceptedFileSet(workspace, files) {
  const receipts = files.map((relative) => acceptedReceipt(workspace, relative));
  return {
    schema_version: 1,
    complete: true,
    count: receipts.length,
    total_bytes: receipts.reduce((total, item) => total + item.size_bytes, 0),
    files: receipts,
    incomplete_reasons: []
  };
}

function insertAcceptedCheckpoint(workspace, { checkpointId, runId, waveId, head, files, createdAt, worktreeFp = null }) {
  const database = new DatabaseSync(path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3'));
  const metadata = { accepted_files: acceptedFileSet(workspace, files) };
  if (worktreeFp) metadata.worktree_fp = worktreeFp;
  database.prepare(`
    INSERT INTO checkpoints(checkpoint_id, run_id, wave_id, git_head, proof_fingerprint, status, created_at, metadata_json)
    VALUES (?, ?, ?, ?, ?, 'accepted', ?, ?)
  `).run(checkpointId, runId, waveId, head, 'a'.repeat(64), createdAt, JSON.stringify(metadata));
  database.close();
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
  return new AcceptedCodeActivationController({
    paths,
    settings: { load: () => ({ workspace }) },
    revisions: { disk: (component) => ({ revision: String(diskRevision(component)) }) },
    runningRevisionProvider: (component) => ({ running_revision: String(runningRevision(component)), disk_revision: String(diskRevision(component)) }),
    activation,
    log: { warn() {} },
    intervalMs: 60000
  });
}

test('component ownership recognizes only fixed activation manifests', () => {
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/recoveryHost.js'), true);
  assert.equal(componentOwnsPath('coding_mcp', 'resources/coding-tools-mcp/coding_tools_mcp/server.py'), true);
  assert.equal(componentOwnsPath('coding_mcp', 'resources/coding-tools-mcp/tests/test_coordination_state.py'), false);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/control-center.js'), true);
  assert.equal(componentOwnsPath('electron_ui', 'electron/services/nativeService.js'), false);
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

test('Recovery Host worktree fingerprint is byte-compatible with canonical Python acceptance fingerprint', async (t) => {
  const { workspace } = await fixture(t);
  const identity = await workspaceIdentity(workspace);
  assert.equal(identity.worktree_fp, canonicalPythonFingerprint(workspace, identity));
});

test('finally accepted tracked recovery-host code activates automatically from canonical checkpoint', async (t) => {
  const { workspace, paths } = await fixture(t);
  const calls = { preflight: 0, activate: 0 };
  const activation = {
    preflight: async () => { calls.preflight += 1; return { safe: true, code: 'READY' }; },
    activate: async (request) => {
      calls.activate += 1;
      return { state: 'completed', component: request.component, result: { activated: true }, expires_at_unix_ms: request.expires_at_unix_ms };
    },
    status: () => { throw new Error('not expected'); }
  };
  const controller = controllerFor(paths, workspace, activation);
  await controller.tick();
  assert.deepEqual(calls, { preflight: 1, activate: 1 });
  assert.equal(controller.status().completed, 1);
  assert.equal(controller.status().blocked, 0);
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
  assert.equal(state.baseline.components.recovery_host.receipts.some((item) => item.path === 'electron/services/nativeService.js'), true);
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
  assert.equal(state.baseline.components.recovery_host.receipts.some((item) => item.path === 'electron/services/nativeService.js'), true);
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
    preflight: async () => alreadyCurrent ? ({ safe: false, code: 'ALREADY_CURRENT' }) : ({ safe: true, code: 'READY' }),
    activate: async (request) => { activationCalls += 1; recoveryRunning = request.expected_disk_revision; return { state: 'completed' }; },
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
  assert.equal(activationCalls, 1);
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
