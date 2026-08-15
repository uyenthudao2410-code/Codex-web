const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { detectProject, collectArtifacts, requireWorkspace } = require('../electron/services/buildVerificationService');
const { assertSanitizedPackagedResources } = require('../scripts/verify-packaged-resources');

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
    '!coding-tools-mcp/benchmarks/reports/**',
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
  assert.equal(packageJson.build?.afterPack, 'scripts/verify-packaged-resources.js');
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

    const cases = [
      ['coding-tools-mcp', 'benchmarks', 'reports', 'runtime.json'],
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
