const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  ComponentRevisionTracker,
  hashComponentRevision,
  recoveryHostLegacyV1Revision,
  RECOVERY_HOST_LEGACY_V1_CONTRACT,
  RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS
} = require('../electron/services/componentRevision');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-component-revision-'));
  const appRoot = path.join(root, 'app');
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(appRoot, 'resources');
  fs.mkdirSync(path.join(appRoot, 'component'), { recursive: true });
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return {
    appRoot,
    paths: createRuntimePaths({ appRoot, dataRoot, resourcesRoot }),
    specs: {
      demo: {
        files: ['component/entry.js'],
        directories: [{ path: 'component/lib', extensions: ['.js'] }]
      }
    }
  };
}

test('component revision hashes only the allowlisted component inputs deterministically', (t) => {
  const { appRoot, specs } = fixture(t);
  fs.mkdirSync(path.join(appRoot, 'component', 'lib'), { recursive: true });
  fs.writeFileSync(path.join(appRoot, 'component', 'entry.js'), 'module.exports = 1;\n');
  fs.writeFileSync(path.join(appRoot, 'component', 'lib', 'b.js'), 'b\n');
  fs.writeFileSync(path.join(appRoot, 'component', 'lib', 'a.js'), 'a\n');
  fs.writeFileSync(path.join(appRoot, 'component', 'ignored.txt'), 'ignored\n');
  const first = hashComponentRevision(appRoot, 'demo', specs);
  fs.writeFileSync(path.join(appRoot, 'component', 'ignored.txt'), 'changed but ignored\n');
  const second = hashComponentRevision(appRoot, 'demo', specs);
  assert.equal(first.revision, second.revision);
  assert.equal(first.file_count, 3);
  assert.equal(first.missing_files, 0);
  fs.writeFileSync(path.join(appRoot, 'component', 'lib', 'a.js'), 'changed\n');
  assert.notEqual(hashComponentRevision(appRoot, 'demo', specs).revision, first.revision);
});

test('revision tracker keeps the running revision stable and marks disk changes pending', (t) => {
  const { appRoot, paths, specs } = fixture(t);
  fs.writeFileSync(path.join(appRoot, 'component', 'entry.js'), 'version one\n');
  let now = Date.parse('2026-08-16T00:00:00.000Z');
  const tracker = new ComponentRevisionTracker({
    paths,
    specs,
    refreshIntervalMs: 30_000,
    now: () => now
  });
  const running = tracker.captureRunning('demo');
  assert.deepEqual(tracker.status('demo'), {
    running_revision: running,
    disk_revision: running,
    update_pending: false,
    state: 'current',
    checked_at: '2026-08-16T00:00:00.000Z',
    file_count: 2
  });

  fs.writeFileSync(path.join(appRoot, 'component', 'entry.js'), 'version two\n');
  assert.equal(tracker.status('demo').update_pending, false, 'cached observation must avoid hashing on every heartbeat');
  now += 30_000;
  const pending = tracker.status('demo');
  assert.equal(pending.running_revision, running);
  assert.notEqual(pending.disk_revision, running);
  assert.equal(pending.update_pending, true);
  assert.equal(pending.state, 'update_pending');
});

test('revision tracker reports unknown until a process revision is captured', (t) => {
  const { appRoot, paths, specs } = fixture(t);
  fs.writeFileSync(path.join(appRoot, 'component', 'entry.js'), 'version one\n');
  const status = new ComponentRevisionTracker({ paths, specs }).status('demo', null);
  assert.equal(status.running_revision, null);
  assert.equal(status.update_pending, null);
  assert.equal(status.state, 'unknown');
});

test('Coding MCP revision resolves from resourcesRoot independently of packaged appRoot', (t) => {
  const { paths } = fixture(t);
  const packageRoot = path.join(paths.resourcesRoot(), 'coding-tools-mcp');
  fs.mkdirSync(path.join(packageRoot, 'coding_tools_mcp'), { recursive: true });
  fs.writeFileSync(path.join(packageRoot, 'pyproject.toml'), '[project]\nname = "fixture"\n');
  fs.writeFileSync(path.join(packageRoot, 'coding_tools_mcp', 'server.py'), 'READY = True\n');
  const disk = new ComponentRevisionTracker({ paths }).disk('coding_mcp', { force: true });
  assert.equal(disk.file_count, 2);
  assert.equal(disk.missing_files, 0);
  assert.ok(disk.total_bytes > 0);
});

test('Recovery Host legacy revision bridge pins added device identity bytes', (t) => {
  const { appRoot } = fixture(t);
  const relative = 'electron/services/deviceIdentity.js';
  const target = path.join(appRoot, ...relative.split('/'));
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(path.join(__dirname, '..', ...relative.split('/')), target);
  const bridge = recoveryHostLegacyV1Revision(appRoot);
  assert.equal(bridge.contract, RECOVERY_HOST_LEGACY_V1_CONTRACT);
  assert.deepEqual(bridge.pinned_added_files, [{
    path: relative,
    sha256: RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS[relative]
  }]);
  fs.appendFileSync(target, '\n// tampered after legacy authorization\n');
  assert.throws(() => recoveryHostLegacyV1Revision(appRoot), { code: 'REVISION_BRIDGE_DIGEST_MISMATCH' });
});
