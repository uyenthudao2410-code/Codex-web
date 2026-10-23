const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createWorkHubLsp } = require('../electron/services/workHubLsp');

function fixture(t, files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-lsp-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const [rel, content] of Object.entries(files)) {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content);
  }
  return root;
}

const JS_FILES = {
  'lib.js': "'use strict';\nfunction greet(name) {\n  return 'hello ' + name;\n}\nmodule.exports = { greet };\n",
  'app.js': "'use strict';\nconst { greet } = require('./lib');\nconst message = greet('world');\nconsole.log(message);\n",
};

test('providers report real status and an honestly labeled fallback', () => {
  const lsp = createWorkHubLsp();
  const providers = lsp.providers();
  const ts = providers.find((p) => p.id === 'typescript');
  assert.equal(ts.status, 'ready');
  const fallback = providers.find((p) => p.id === 'text-search');
  assert.equal(fallback.kind, 'fallback');
});

test('typescript definition jumps from a call site to the declaring file', async (t) => {
  const root = fixture(t, JS_FILES);
  const lsp = createWorkHubLsp();
  // app.js line 3: "const message = greet('world');" — greet starts at column 17.
  const result = await lsp.definition(root, 'app.js', 3, 18);
  assert.equal(result.provider, 'typescript');
  assert.equal(result.fallback, false);
  assert.ok(result.results.length >= 1, 'expected at least one definition');
  const target = result.results[0];
  assert.equal(target.path, 'lib.js');
  assert.equal(target.line, 2);
});

test('typescript references from a call site reach the declaration file', async (t) => {
  const root = fixture(t, JS_FILES);
  const lsp = createWorkHubLsp();
  const result = await lsp.references(root, 'app.js', 3, 18);
  assert.equal(result.provider, 'typescript');
  assert.ok(result.results.some((r) => r.path === 'lib.js' && r.line === 2), 'declaration in lib.js must be a reference');
  assert.ok(result.results.some((r) => r.path === 'app.js' && r.line === 2), 'import binding in app.js must be a reference');
});

test('typescript document symbols list the declared function', async (t) => {
  const root = fixture(t, JS_FILES);
  const lsp = createWorkHubLsp();
  const result = await lsp.symbols(root, 'lib.js');
  assert.equal(result.provider, 'typescript');
  assert.ok(result.symbols.some((s) => s.name === 'greet'));
});

test('navigation refuses paths outside the project root', async (t) => {
  const root = fixture(t, JS_FILES);
  const lsp = createWorkHubLsp();
  await assert.rejects(() => lsp.definition(root, '../outside.js', 1, 1), /ngoài thư mục/);
});

test('files without a language server fall back to labeled text search', async (t) => {
  const root = fixture(t, { 'notes.md': '# Title\nsome needle here\n', 'other.md': 'needle again\n' });
  const lsp = createWorkHubLsp({ tsModule: false, pyrightServer: null });
  const result = await lsp.definition(root, 'notes.md', 2, 7);
  assert.equal(result.provider, 'text-search');
  assert.equal(result.fallback, true);
  assert.equal(result.word, 'needle');
  assert.ok(result.results.length >= 2);
});

test('python definition resolves through pyright when the server is installed', async (t) => {
  const lspProbe = createWorkHubLsp();
  const pyright = lspProbe.providers().find((p) => p.id === 'pyright');
  if (!pyright || pyright.status !== 'ready') {
    t.skip('pyright-langserver not installed in this environment');
    return;
  }
  const root = fixture(t, {
    'helpers.py': 'def compute_total(items):\n    return sum(items)\n',
    'main.py': 'from helpers import compute_total\n\nresult = compute_total([1, 2, 3])\nprint(result)\n',
  });
  t.after(() => lspProbe.dispose());
  const result = await lspProbe.definition(root, 'main.py', 3, 12);
  assert.equal(result.provider, 'pyright');
  assert.equal(result.fallback, false);
  assert.ok(result.results.some((r) => r.path === 'helpers.py' && r.line === 1), JSON.stringify(result.results));
});
