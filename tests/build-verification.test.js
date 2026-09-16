const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { detectProject, collectArtifacts, requireWorkspace } = require('../electron/services/buildVerificationService');
const {
  assertSanitizedPackagedResources,
  assertExactPackagedResources,
  assertExactControlPlaneAdapter,
  CONTROL_PLANE_ADAPTER_FILES
} = require('../scripts/verify-packaged-resources');
const { cleanDistRoot } = require('../scripts/clean-dist');

test('build verification detects Electron package scripts', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-build-'));
  try {
    fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({ name: 'demo', version: '1.2.3', main: 'main.js', scripts: { test: 'node --test', dist: 'electron-builder' }, build: { directories: { output: 'release' } } }));
    const project = detectProject(root);
    assert.equal(project.type, 'electron');
    assert.equal(project.testCommand, 'npm run test');
    assert.equal(project.buildCommand, 'npm run dist');
    assert.deepEqual(project.artifacts, ['release', 'build']);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('artifact collection rejects paths outside workspace and hashes files', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-artifact-'));
  try {
    fs.mkdirSync(path.join(root, 'dist'));
    fs.writeFileSync(path.join(root, 'dist', 'app.exe'), 'artifact');
    const artifacts = await collectArtifacts(root, ['dist']);
    assert.equal(artifacts.length, 1);
    assert.equal(artifacts[0].sha256.length, 64);
    await assert.rejects(() => collectArtifacts(root, ['..']), /thư mục làm việc/i);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('workspace is required before build verification', () => {
  assert.throws(() => requireWorkspace(''), /Vui lòng chọn thư mục làm việc/i);
});

test('electron packaging excludes volatile resource evidence and validates the packed tree', () => {
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
  const resources = packageJson.build?.extraResources || [];
  const codingResources = resources.find((entry) => entry.from === 'resources' && entry.to === 'resources');
  assert.ok(codingResources, 'resources extraResources entry is required');
  const requiredFilters = [
    '!coding-tools-mcp/tests/**',
    '!coding-tools-mcp/benchmarks/**',
    '!coding-tools-mcp/scripts/**',
    '!**/__pycache__/**',
    '!**/.pytest_cache/**',
    '!**/*.egg-info/**',
    '!**/.coding-tools/**',
    '!**/*.pyc',
    '!**/*.pyo',
  ];
  for (const filter of requiredFilters) {
    assert.ok(codingResources.filter?.includes(filter), `missing packaging sanitation filter: ${filter}`);
  }
  const staleRunHelper = resources.find((entry) => entry.from === 'resources/coding-tools-mcp/scripts/reconcile_exact_stale_run.py');
  assert.deepEqual(staleRunHelper, {
    from: 'resources/coding-tools-mcp/scripts/reconcile_exact_stale_run.py',
    to: 'resources/coding-tools-mcp/scripts/reconcile_exact_stale_run.py'
  }, 'the exact stale-run helper must be packaged independently of the excluded scripts tree');
  const controlPlaneAdapter = resources.find((entry) => entry.from === 'control-plane/control_plane' && entry.to === 'resources/control-plane');
  assert.deepEqual(controlPlaneAdapter?.filter?.slice().sort(), [...CONTROL_PLANE_ADAPTER_FILES].sort(),
    'the installed node adapter must have one explicit packaged file set');
  assert.deepEqual(packageJson.build?.electronLanguages, ['en-US', 'vi']);
  assert.equal(packageJson.build?.afterPack, 'scripts/verify-packaged-resources.js');
  assert.match(packageJson.scripts?.dist || '', /node scripts\/clean-dist\.js/);
  assert.match(packageJson.scripts?.['dist:dir'] || '', /node scripts\/clean-dist\.js/);
  assert.match(packageJson.scripts?.['dist:control-plane'] || '', /build-control-plane-release\.py --output-dir dist/);
  const packagedSmoke = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'packaged-recovery-smoke.js'), 'utf8');
  assert.match(packagedSmoke, /CODEX_PACKAGED_APP_ROOT/);
  assert.match(packagedSmoke, /reconcile_exact_stale_run\.py/);
  assert.match(packagedSmoke, /assertExactControlPlaneAdapter/);
  assert.equal(fs.existsSync(path.join(__dirname, '..', 'scripts', 'installed-recovery-smoke.js')), true);
});

test('dist cleaner removes stale package output before Electron Builder runs', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-dist-clean-'));
  try {
    fs.mkdirSync(path.join(root, 'dist', 'win-unpacked'), { recursive: true });
    fs.writeFileSync(path.join(root, 'dist', 'win-unpacked', 'stale.txt'), 'stale');
    const removed = cleanDistRoot(root);
    assert.equal(removed, path.join(root, 'dist'));
    assert.equal(fs.existsSync(removed), false);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('packaged resources must be byte-identical to the current allowed source projection', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-packaged-exact-'));
  const source = path.join(root, 'source');
  const packaged = path.join(root, 'packaged');
  try {
    fs.mkdirSync(path.join(source, 'recovery-supervisor'), { recursive: true });
    fs.mkdirSync(path.join(packaged, 'recovery-supervisor'), { recursive: true });
    fs.writeFileSync(path.join(source, 'recovery-supervisor', 'recovery-supervisor.ps1'), 'current');
    fs.mkdirSync(path.join(source, 'coding-tools-mcp', '.coding-tools'), { recursive: true });
    fs.writeFileSync(path.join(source, 'coding-tools-mcp', '.coding-tools', 'performance.json'), 'runtime-only');
    fs.mkdirSync(path.join(source, 'coding-tools-mcp', 'scripts'), { recursive: true });
    fs.mkdirSync(path.join(packaged, 'coding-tools-mcp', 'scripts'), { recursive: true });
    fs.writeFileSync(path.join(source, 'coding-tools-mcp', 'scripts', 'reconcile_exact_stale_run.py'), 'official helper');
    fs.writeFileSync(path.join(packaged, 'coding-tools-mcp', 'scripts', 'reconcile_exact_stale_run.py'), 'official helper');
    fs.writeFileSync(path.join(packaged, 'recovery-supervisor', 'recovery-supervisor.ps1'), 'current');
    assert.equal(assertExactPackagedResources(source, packaged).exact_source, true);

    fs.writeFileSync(path.join(packaged, 'recovery-supervisor', 'recovery-supervisor.ps1'), 'stale');
    assert.throws(() => assertExactPackagedResources(source, packaged), /source mismatch/);

    fs.writeFileSync(path.join(packaged, 'recovery-supervisor', 'recovery-supervisor.ps1'), 'current');
    fs.rmSync(path.join(packaged, 'recovery-supervisor', 'recovery-supervisor.ps1'));
    assert.throws(() => assertExactPackagedResources(source, packaged), /missing from current source projection/);

    fs.writeFileSync(path.join(packaged, 'recovery-supervisor', 'recovery-supervisor.ps1'), 'current');
    fs.writeFileSync(path.join(packaged, 'stale-resource.txt'), 'unexpected');
    assert.throws(() => assertExactPackagedResources(source, packaged), /not present in current source/);
    fs.rmSync(path.join(packaged, 'stale-resource.txt'));

    fs.mkdirSync(path.join(packaged, 'control-plane'), { recursive: true });
    fs.writeFileSync(path.join(packaged, 'control-plane', 'node-agent.cmd'), 'verified separately');
    assert.throws(() => assertExactPackagedResources(source, packaged), /not present in current source/);
    assert.equal(assertExactPackagedResources(source, packaged, {
      separatelyVerifiedTopLevelDirectories: ['control-plane']
    }).exact_source, true);
    fs.writeFileSync(path.join(packaged, 'unrelated-extra.txt'), 'unexpected');
    assert.throws(() => assertExactPackagedResources(source, packaged, {
      separatelyVerifiedTopLevelDirectories: ['control-plane']
    }), /not present in current source/);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('packaged control-plane adapter has the exact allowlisted installed file set', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-packaged-adapter-'));
  const source = path.join(root, 'source');
  const packaged = path.join(root, 'packaged');
  try {
    fs.mkdirSync(source, { recursive: true });
    fs.mkdirSync(packaged, { recursive: true });
    for (const file of CONTROL_PLANE_ADAPTER_FILES) {
      fs.writeFileSync(path.join(source, file), `source:${file}`);
      fs.writeFileSync(path.join(packaged, file), `source:${file}`);
    }
    assert.equal(assertExactControlPlaneAdapter(source, packaged).exact_source, true);
    fs.writeFileSync(path.join(packaged, 'node_agent.py'), 'drift');
    assert.throws(() => assertExactControlPlaneAdapter(source, packaged), /source mismatch/);
    fs.writeFileSync(path.join(packaged, 'node_agent.py'), 'source:node_agent.py');
    fs.writeFileSync(path.join(packaged, 'unexpected.py'), 'unexpected');
    assert.throws(() => assertExactControlPlaneAdapter(source, packaged), /unexpected file set/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('packaged resource sanitation rejects raw reports and Python cache metadata', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'web-mcp-packaged-resources-'));
  const writeCleanFixture = () => {
    fs.mkdirSync(path.join(root, 'coding-tools-mcp', 'coding_tools_mcp'), { recursive: true });
    fs.writeFileSync(path.join(root, 'coding-tools-mcp', 'coding_tools_mcp', 'server.py'), 'print("ok")\n');
  };
  try {
    writeCleanFixture();
    assert.equal(assertSanitizedPackagedResources(root).sanitized, true);

    const sanctionedHelper = path.join(root, 'coding-tools-mcp', 'scripts', 'reconcile_exact_stale_run.py');
    fs.mkdirSync(path.dirname(sanctionedHelper), { recursive: true });
    fs.writeFileSync(sanctionedHelper, 'official helper');
    assert.equal(assertSanitizedPackagedResources(root).sanitized, true);
    fs.writeFileSync(path.join(path.dirname(sanctionedHelper), 'report_runtime.py'), 'forbidden');
    assert.throws(() => assertSanitizedPackagedResources(root), /packaged resources sanitation failed/);
    fs.rmSync(path.join(root, 'coding-tools-mcp'), { recursive: true, force: true });
    writeCleanFixture();

    const cases = [
      ['coding-tools-mcp', 'tests', 'test_runtime.py'],
      ['coding-tools-mcp', 'benchmarks', 'runtime_activation.py'],
      ['coding-tools-mcp', 'scripts', 'report_runtime.py'],
      ['coding-tools-mcp', 'coding_tools_mcp', '__pycache__', 'server.pyc'],
      ['coding-tools-mcp', '.pytest_cache', 'v', 'cache', 'nodeids'],
      ['coding-tools-mcp', 'coding_tools_mcp.egg-info', 'PKG-INFO'],
      ['coding-tools-mcp', '.coding-tools', 'performance.json'],
      ['coding-tools-mcp', 'python_vendor', 'jwt', 'api_jwt.pyo'],
    ];
    for (const parts of cases) {
      const target = path.join(root, ...parts);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, 'forbidden');
      assert.throws(() => assertSanitizedPackagedResources(root), /packaged resources sanitation failed/);
      fs.rmSync(path.join(root, 'coding-tools-mcp'), { recursive: true, force: true });
      writeCleanFixture();
    }
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
