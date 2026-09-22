const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  COMPONENT_SPECS,
  ComponentRevisionTracker,
  componentOwnsPath,
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
  assert.equal(componentOwnsPath('demo', 'component/lib/a.js', specs), true);
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

test('Recovery Host revision owns the semantic watchdog implementation it loads', () => {
  assert.equal(
    COMPONENT_SPECS.recovery_host.files.includes('electron/services/mcpSemanticHealth.js'),
    true
  );
});

test('Recovery Host revision owns the connector attestation boundary it loads', () => {
  assert.equal(
    COMPONENT_SPECS.recovery_host.files.includes('electron/services/connectorAttestation.js'),
    true
  );
});

test('Electron UI revision owns its real-renderer performance collector and loaded dashboard assets', () => {
  assert.equal(
    COMPONENT_SPECS.electron_ui.files.includes('electron/services/uiPerformanceMetrics.js'),
    true
  );
  assert.equal(componentOwnsPath('electron_ui', 'electron/services/uiPerformanceMetrics.js'), true);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/index.html'), true);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/dashboard.js'), true);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/fonts/PlusJakartaSans-latin.woff2'), true);
  assert.equal(componentOwnsPath('electron_ui', 'renderer/not-a-runtime-resource.txt'), false);
  assert.equal(COMPONENT_SPECS.electron_ui.excluded_files, undefined);
});

test('Electron UI revision changes when loaded token dashboard document or font bytes change', (t) => {
  const { appRoot } = fixture(t);
  for (const relative of COMPONENT_SPECS.electron_ui.files) {
    const target = path.join(appRoot, ...relative.split('/'));
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, `${relative}\n`);
  }
  const rendererRoot = path.join(appRoot, 'renderer');
  const dashboard = path.join(rendererRoot, 'index.html');
  const font = path.join(rendererRoot, 'fonts', 'fixture.woff2');
  fs.mkdirSync(path.dirname(font), { recursive: true });
  fs.writeFileSync(dashboard, '<link rel="stylesheet" href="fonts.css">\n');
  fs.writeFileSync(path.join(rendererRoot, 'fonts.css'), '@font-face { src: url(./fonts/fixture.woff2); }\n');
  fs.writeFileSync(font, Buffer.from([0x77, 0x4f, 0x46, 0x32, 0x01]));
  fs.writeFileSync(path.join(rendererRoot, 'not-a-runtime-resource.txt'), 'unowned fixture\n');

  const initial = hashComponentRevision(appRoot, 'electron_ui');
  fs.appendFileSync(dashboard, '<!-- changed dashboard document -->\n');
  const afterDashboard = hashComponentRevision(appRoot, 'electron_ui');
  assert.notEqual(afterDashboard.revision, initial.revision);

  fs.appendFileSync(font, Buffer.from([0x02]));
  const afterFont = hashComponentRevision(appRoot, 'electron_ui');
  assert.notEqual(afterFont.revision, afterDashboard.revision);

  fs.appendFileSync(path.join(rendererRoot, 'not-a-runtime-resource.txt'), 'still unowned\n');
  assert.equal(
    hashComponentRevision(appRoot, 'electron_ui').revision,
    afterFont.revision,
    'an unsupported renderer fixture is not part of the Electron UI revision'
  );
});

test('Recovery Host revision manifest owns stale-host bootstrap source', () => {
  assert.equal(
    COMPONENT_SPECS.recovery_host.files.includes('electron/services/recoveryBootstrap.js'),
    true
  );
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/recoveryBootstrap.js'), true);
  assert.equal(
    COMPONENT_SPECS.recovery_host.files.includes('resources/recovery-supervisor/recovery-supervisor.ps1'),
    true
  );
  assert.equal(componentOwnsPath('recovery_host', 'resources/recovery-supervisor/recovery-supervisor.ps1'), true);
});

test('activation census sources are owned by the components that execute them', () => {
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/activationClosure.js'), true);
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/activationPostflight.js'), true);
  assert.equal(componentOwnsPath('recovery_host', 'electron/services/fullCleanActivation.js'), true);
  assert.equal(
    componentOwnsPath('coding_mcp', 'resources/coding-tools-mcp/coding_tools_mcp/activation_ledger_census.py'),
    true
  );
});

test('Recovery Host legacy revision bridge pins added device identity bytes', (t) => {
  const { appRoot } = fixture(t);
  for (const relative of Object.keys(RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS)) {
    const target = path.join(appRoot, ...relative.split('/'));
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(__dirname, '..', ...relative.split('/')), target);
  }
  const bridge = recoveryHostLegacyV1Revision(appRoot);
  assert.equal(bridge.contract, RECOVERY_HOST_LEGACY_V1_CONTRACT);
  assert.deepEqual(
    bridge.pinned_added_files,
    Object.entries(RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS).map(([relative, sha256]) => ({ path: relative, sha256 }))
  );
  const relative = 'electron/services/deviceIdentity.js';
  const target = path.join(appRoot, ...relative.split('/'));
  const canonicalText = fs.readFileSync(target, 'utf8').replace(/\r\n/g, '\n');
  fs.writeFileSync(target, canonicalText.replace(/\n/g, '\r\n'), 'utf8');
  assert.equal(
    recoveryHostLegacyV1Revision(appRoot).pinned_added_files[0].sha256,
    RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS[relative],
    'checkout-only CRLF materialization must not invalidate the pinned legacy source contract'
  );
  fs.appendFileSync(target, '\n// tampered after legacy authorization\n');
  assert.throws(() => recoveryHostLegacyV1Revision(appRoot), { code: 'REVISION_BRIDGE_DIGEST_MISMATCH' });
});
