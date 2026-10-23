'use strict';
/*
 * Work Hub code navigation (catalog 261022: F13 / parity M1.5).
 * Real providers only:
 *  - TypeScript language service (in-process) for JS/TS definition,
 *    references and document symbols.
 *  - Pyright language server over stdio LSP for Python.
 *  - A bounded text search that is ALWAYS labeled as a fallback; it is
 *    never presented as semantic navigation.
 * Every entry point resolves the target file strictly inside the active
 * project root (same fencing as workHubFiles).
 */
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { resolveInsideRoot, searchText, SKIP_DIRS } = require('./workHubFiles');

const TS_EXTENSIONS = new Set(['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.mts', '.cts']);
const PY_EXTENSIONS = new Set(['.py']);
const MAX_PROJECT_FILES = 800;

function languageOf(rel) {
  const ext = path.extname(String(rel || '')).toLowerCase();
  if (TS_EXTENSIONS.has(ext)) return 'typescript';
  if (PY_EXTENSIONS.has(ext)) return 'python';
  return null;
}

function wordAt(content, line1, character1) {
  const lines = String(content || '').split(/\r?\n/);
  const line = lines[line1 - 1] || '';
  const index = Math.max(0, Math.min(line.length, character1 - 1));
  const isWord = (ch) => /[A-Za-z0-9_$]/.test(ch || '');
  let start = index;
  let end = index;
  while (start > 0 && isWord(line[start - 1])) start -= 1;
  while (end < line.length && isWord(line[end])) end += 1;
  return { word: line.slice(start, end), start: start + 1, end };
}

// ---------------- TypeScript provider (in-process language service) --------
function createTypeScriptProvider(ts) {
  function languageService(root) {
    const files = [];
    const walk = (dir) => {
      if (files.length >= MAX_PROJECT_FILES) return;
      let entries = [];
      try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
      for (const entry of entries) {
        if (files.length >= MAX_PROJECT_FILES) return;
        if (entry.isDirectory()) {
          if (!SKIP_DIRS.has(entry.name) && !entry.name.startsWith('.')) walk(path.join(dir, entry.name));
        } else if (TS_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
          files.push(path.join(dir, entry.name));
        }
      }
    };
    walk(root);
    const host = {
      getScriptFileNames: () => files,
      getScriptVersion: (file) => {
        try { return String(fs.statSync(file).mtimeMs); } catch { return '0'; }
      },
      getScriptSnapshot: (file) => {
        try { return ts.ScriptSnapshot.fromString(fs.readFileSync(file, 'utf8')); } catch { return undefined; }
      },
      getCurrentDirectory: () => root,
      getCompilationSettings: () => ({
        allowJs: true, checkJs: false, module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022, moduleResolution: ts.ModuleResolutionKind.NodeJs,
        jsx: ts.JsxEmit.Preserve, esModuleInterop: true,
      }),
      getDefaultLibFileName: (options) => ts.getDefaultLibFilePath(options),
      fileExists: ts.sys.fileExists,
      readFile: ts.sys.readFile,
      readDirectory: ts.sys.readDirectory,
    };
    return ts.createLanguageService(host, ts.createDocumentRegistry());
  }

  function lineStartsOf(content) {
    const starts = [0];
    for (let i = 0; i < content.length; i += 1) {
      if (content[i] === '\n') starts.push(i + 1);
    }
    return starts;
  }

  function offsetOf(root, rel, line1, character1) {
    const absolute = path.join(root, rel);
    const content = fs.readFileSync(absolute, 'utf8');
    const lineStarts = lineStartsOf(content);
    const lineIndex = Math.max(0, Math.min(lineStarts.length - 1, line1 - 1));
    return { absolute, offset: lineStarts[lineIndex] + Math.max(0, character1 - 1) };
  }

  function toLocation(root, fileName, textSpan) {
    const content = fs.readFileSync(fileName, 'utf8');
    const lineStarts = lineStartsOf(content);
    let line = 0;
    while (line + 1 < lineStarts.length && lineStarts[line + 1] <= textSpan.start) line += 1;
    return {
      path: path.relative(root, fileName).split(path.sep).join('/'),
      line: line + 1,
      character: textSpan.start - lineStarts[line] + 1,
    };
  }

  return {
    id: 'typescript',
    definition(root, rel, line, character) {
      const service = languageService(root);
      const { absolute, offset } = offsetOf(root, rel, line, character);
      const defs = service.getDefinitionAtPosition(absolute, offset) || [];
      return defs
        .filter((d) => !d.fileName.includes(`${path.sep}node_modules${path.sep}typescript${path.sep}lib`))
        .map((d) => ({ ...toLocation(root, d.fileName, d.textSpan), kind: ts.ScriptElementKind[d.kind] || d.kind }));
    },
    references(root, rel, line, character) {
      const service = languageService(root);
      const { absolute, offset } = offsetOf(root, rel, line, character);
      const refs = service.getReferencesAtPosition(absolute, offset) || [];
      return refs.map((r) => ({ ...toLocation(root, r.fileName, r.textSpan), isWriteAccess: Boolean(r.isWriteAccess) }));
    },
    symbols(root, rel) {
      const service = languageService(root);
      const absolute = path.join(root, rel);
      const tree = service.getNavigationTree(absolute);
      const out = [];
      const visit = (node, depth) => {
        for (const child of node.childItems || []) {
          const span = child.spans && child.spans[0];
          if (span) out.push({ name: child.text, kind: child.kind, ...toLocation(root, absolute, span), depth });
          visit(child, depth + 1);
        }
      };
      if (tree) visit(tree, 0);
      return out;
    },
  };
}

// ---------------- Pyright provider (LSP over stdio) -----------------------
function resolvePyrightServer() {
  const candidates = [];
  try {
    const { execFileSync } = require('child_process');
    const globalRoot = execFileSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['root', '-g'], { encoding: 'utf8', timeout: 5000 }).trim();
    if (globalRoot) {
      candidates.push(path.join(globalRoot, 'pyright', 'langserver.js'));
      candidates.push(path.join(globalRoot, 'pyright', 'dist', 'pyright-langserver.js'));
    }
  } catch { /* npm not available */ }
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return { command: process.execPath, args: [candidate, '--stdio'], label: candidate };
  }
  return null;
}

class LspSession {
  constructor(command, args, root) {
    this.root = root;
    this.nextId = 1;
    this.pending = new Map();
    this.buffer = Buffer.alloc(0);
    this.opened = new Set();
    this.child = spawn(command, args, { cwd: root, stdio: ['pipe', 'pipe', 'pipe'] });
    this.child.stdout.on('data', (chunk) => this.onData(chunk));
    this.child.on('error', () => this.failAll(new Error('Không khởi động được pyright-langserver.')));
  }

  onData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (true) {
      const headerEnd = this.buffer.indexOf('\r\n\r\n');
      if (headerEnd < 0) return;
      const header = this.buffer.slice(0, headerEnd).toString('ascii');
      const match = /Content-Length: (\d+)/i.exec(header);
      if (!match) { this.buffer = this.buffer.slice(headerEnd + 4); continue; }
      const length = Number(match[1]);
      if (this.buffer.length < headerEnd + 4 + length) return;
      const body = this.buffer.slice(headerEnd + 4, headerEnd + 4 + length).toString('utf8');
      this.buffer = this.buffer.slice(headerEnd + 4 + length);
      let message;
      try { message = JSON.parse(body); } catch { continue; }
      if (message.id !== undefined && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(message.error.message || 'LSP error'));
        else resolve(message.result);
      }
    }
  }

  failAll(error) {
    for (const { reject } of this.pending.values()) reject(error);
    this.pending.clear();
  }

  send(payload) {
    const body = JSON.stringify(payload);
    this.child.stdin.write(`Content-Length: ${Buffer.byteLength(body)}\r\n\r\n${body}`);
  }

  request(method, params, timeoutMs = 20000) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`Hết thời gian chờ ${method}.`)); }, timeoutMs);
      this.pending.set(id, {
        resolve: (value) => { clearTimeout(timer); resolve(value); },
        reject: (error) => { clearTimeout(timer); reject(error); },
      });
      this.send({ jsonrpc: '2.0', id, method, params });
    });
  }

  notify(method, params) {
    this.send({ jsonrpc: '2.0', method, params });
  }

  async initialize() {
    await this.request('initialize', {
      processId: process.pid,
      rootUri: `file://${this.root.replace(/\\/g, '/')}`,
      capabilities: {},
      workspaceFolders: [{ uri: `file://${this.root.replace(/\\/g, '/')}`, name: path.basename(this.root) }],
    });
    this.notify('initialized', {});
  }

  async open(rel) {
    if (this.opened.has(rel)) return;
    const absolute = path.join(this.root, rel);
    const content = fs.readFileSync(absolute, 'utf8');
    this.notify('textDocument/didOpen', {
      textDocument: { uri: `file://${absolute.replace(/\\/g, '/')}`, languageId: 'python', version: 1, text: content },
    });
    this.opened.add(rel);
  }

  dispose() {
    try { this.child.kill(); } catch { /* already gone */ }
  }
}

function createPyrightProvider(resolved) {
  const sessions = new Map();
  async function session(root) {
    const existing = sessions.get(root);
    if (existing) return existing;
    const created = new LspSession(resolved.command, resolved.args, root);
    sessions.set(root, created);
    try {
      await created.initialize();
    } catch (error) {
      sessions.delete(root);
      created.dispose();
      throw error;
    }
    return created;
  }
  function uri(root, rel) {
    return `file://${path.join(root, rel).replace(/\\/g, '/')}`;
  }
  function toLocation(root, item) {
    const range = item.range || (item.targetSelectionRange ? { start: item.targetSelectionRange.start } : null);
    const targetUri = item.uri || item.targetUri || '';
    if (!range) return null;
    return {
      path: path.relative(root, decodeURIComponent(targetUri.replace(/^file:\/\//, ''))).split(path.sep).join('/'),
      line: range.start.line + 1,
      character: range.start.character + 1,
    };
  }
  return {
    id: 'pyright',
    disposeAll() {
      for (const s of sessions.values()) s.dispose();
      sessions.clear();
    },
    async definition(root, rel, line, character) {
      const s = await session(root);
      await s.open(rel);
      const result = await s.request('textDocument/definition', {
        textDocument: { uri: uri(root, rel) },
        position: { line: line - 1, character: character - 1 },
      });
      const items = Array.isArray(result) ? result : (result ? [result] : []);
      return items.map((item) => toLocation(root, item)).filter(Boolean);
    },
    async references(root, rel, line, character) {
      const s = await session(root);
      await s.open(rel);
      const result = await s.request('textDocument/references', {
        textDocument: { uri: uri(root, rel) },
        position: { line: line - 1, character: character - 1 },
        context: { includeDeclaration: true },
      });
      return (result || []).map((item) => toLocation(root, item)).filter(Boolean);
    },
    async symbols(root, rel) {
      const s = await session(root);
      await s.open(rel);
      const result = await s.request('textDocument/documentSymbol', { textDocument: { uri: uri(root, rel) } });
      const out = [];
      const visit = (nodes, depth) => {
        for (const node of nodes || []) {
          const range = node.selectionRange || node.range;
          if (range) out.push({ name: node.name, kind: String(node.kind), line: range.start.line + 1, character: range.start.character + 1, path: rel, depth });
          visit(node.children, depth + 1);
        }
      };
      visit(result, 0);
      return out;
    },
  };
}

// ---------------- Service facade --------------------------------------------
function createWorkHubLsp(overrides = {}) {
  const tsProviderHolder = { provider: null, error: null };
  function tsProvider() {
    if (tsProviderHolder.provider || tsProviderHolder.error) return tsProviderHolder.provider;
    try {
      if (overrides.tsModule === false) throw new Error('TypeScript provider disabled by configuration.');
      const ts = overrides.tsModule || require('typescript');
      tsProviderHolder.provider = createTypeScriptProvider(ts);
    } catch (error) {
      tsProviderHolder.error = error;
    }
    return tsProviderHolder.provider;
  }
  const pyrightResolved = overrides.pyrightServer !== undefined ? overrides.pyrightServer : resolvePyrightServer();
  const pyright = pyrightResolved ? createPyrightProvider(pyrightResolved) : null;

  function providers() {
    return [
      {
        id: 'typescript', kind: 'language-server', languages: ['javascript', 'typescript'],
        status: tsProvider() ? 'ready' : 'unavailable',
        detail: tsProvider() ? `TypeScript ${require('typescript').version} language service` : 'Gói typescript chưa sẵn sàng.',
      },
      {
        id: 'pyright', kind: 'language-server', languages: ['python'],
        status: pyright ? 'ready' : 'unavailable',
        detail: pyright ? `pyright-langserver (${pyrightResolved.label})` : 'Chưa tìm thấy pyright-langserver.',
      },
      {
        id: 'text-search', kind: 'fallback', languages: ['*'],
        status: 'available', detail: 'Tìm văn bản có giới hạn — KHÔNG phải định vị ngữ nghĩa.',
      },
    ];
  }

  async function fallback(root, rel, line, character) {
    const { target } = resolveInsideRoot(root, rel);
    const content = fs.readFileSync(target, 'utf8');
    const { word } = wordAt(content, line, character);
    if (!word) return { provider: 'text-search', fallback: true, word: '', results: [] };
    const found = await searchText(root, word);
    const results = (found.results || []).map((r) => ({ path: r.rel, line: r.line, character: 1, text: r.text }));
    return { provider: 'text-search', fallback: true, word, results };
  }

  async function navigate(root, rel, line, character, action) {
    const { target, rel: normalizedRel } = resolveInsideRoot(root, rel);
    if (!fs.existsSync(target)) throw new Error('Tệp không tồn tại trong dự án.');
    const language = languageOf(normalizedRel);
    const provider = language === 'typescript' ? tsProvider() : language === 'python' ? pyright : null;
    if (!provider) return fallback(root, normalizedRel, line, character);
    const results = action === 'definition'
      ? await provider.definition(root, normalizedRel, line, character)
      : await provider.references(root, normalizedRel, line, character);
    return { provider: provider.id, fallback: false, results };
  }

  return {
    providers,
    dispose() {
      if (pyright) pyright.disposeAll();
    },
    definition: (root, rel, line, character) => navigate(root, rel, line, character, 'definition'),
    references: (root, rel, line, character) => navigate(root, rel, line, character, 'references'),
    async symbols(root, rel) {
      const { rel: normalizedRel } = resolveInsideRoot(root, rel);
      const language = languageOf(normalizedRel);
      const provider = language === 'typescript' ? tsProvider() : language === 'python' ? pyright : null;
      if (!provider) return { provider: 'none', fallback: true, symbols: [] };
      const symbols = await provider.symbols(root, normalizedRel);
      return { provider: provider.id, fallback: false, symbols };
    },
    wordAt,
    languageOf,
  };
}

const defaultService = createWorkHubLsp();

module.exports = {
  createWorkHubLsp,
  providers: (...args) => defaultService.providers(...args),
  definition: (...args) => defaultService.definition(...args),
  references: (...args) => defaultService.references(...args),
  symbols: (...args) => defaultService.symbols(...args),
  wordAt,
  languageOf,
};
