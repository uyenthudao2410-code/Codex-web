'use strict';
/*
 * Work Hub file access (catalog 261022: F06, F09, F12).
 * Read-only operations strictly inside one root (the active workspace,
 * resolved by electron/main.js from settings). No writes, no shell:
 * git runs through execFile with an argv array.
 */
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const SKIP_DIRS = new Set(['.git', 'node_modules', '.coding-tools', 'dist', 'target', '.next', 'coverage']);
const DEFAULTS = {
  maxEntries: 300,
  readMaxBytes: 256 * 1024,
  searchMaxResults: 60,
  searchMaxFiles: 1500,
  searchMaxFileBytes: 512 * 1024,
  diffMaxChars: 200 * 1024,
};

function resolveInsideRoot(root, rel) {
  const rootResolved = path.resolve(String(root || ''));
  const requested = String(rel || '').trim();
  const target = requested
    ? (path.isAbsolute(requested) ? path.resolve(requested) : path.resolve(rootResolved, requested))
    : rootResolved;
  const relative = path.relative(rootResolved, target);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error('Đường dẫn nằm ngoài thư mục làm việc.');
  }
  return { root: rootResolved, target, rel: relative.split(path.sep).join('/') };
}

function toRel(root, target) {
  return path.relative(root, target).split(path.sep).join('/');
}

function listDir(root, rel, options = {}) {
  const maxEntries = options.maxEntries || DEFAULTS.maxEntries;
  const { root: rootResolved, target, rel: relOut } = resolveInsideRoot(root, rel);
  const stat = fs.statSync(target);
  if (!stat.isDirectory()) throw new Error('Đường dẫn không phải thư mục.');
  const entries = fs.readdirSync(target, { withFileTypes: true })
    .filter((entry) => entry.name !== '.git')
    .map((entry) => {
      const full = path.join(target, entry.name);
      let size = null;
      if (entry.isFile()) { try { size = fs.statSync(full).size; } catch { size = null; } }
      return {
        name: entry.name,
        rel: toRel(rootResolved, full),
        type: entry.isDirectory() ? 'dir' : 'file',
        size,
      };
    })
    .sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name) : a.type === 'dir' ? -1 : 1));
  return { root: rootResolved, rel: relOut, entries: entries.slice(0, maxEntries), truncated: entries.length > maxEntries };
}

function looksBinary(buffer) {
  const probe = buffer.subarray(0, Math.min(buffer.length, 8192));
  return probe.includes(0);
}

function readTextFile(root, rel, options = {}) {
  const maxBytes = options.readMaxBytes || DEFAULTS.readMaxBytes;
  const { target, rel: relOut } = resolveInsideRoot(root, rel);
  const stat = fs.statSync(target);
  if (!stat.isFile()) throw new Error('Đường dẫn không phải tệp.');
  const buffer = fs.readFileSync(target);
  if (looksBinary(buffer)) return { rel: relOut, size: stat.size, binary: true, content: '', truncated: false };
  const truncated = buffer.length > maxBytes;
  return {
    rel: relOut,
    size: stat.size,
    binary: false,
    content: buffer.subarray(0, maxBytes).toString('utf8'),
    truncated,
  };
}

function searchText(root, query, options = {}) {
  const needle = String(query || '').trim().toLowerCase();
  if (needle.length < 2) throw new Error('Từ khóa tìm kiếm cần ít nhất 2 ký tự.');
  const maxResults = options.searchMaxResults || DEFAULTS.searchMaxResults;
  const maxFiles = options.searchMaxFiles || DEFAULTS.searchMaxFiles;
  const maxFileBytes = options.searchMaxFileBytes || DEFAULTS.searchMaxFileBytes;
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const results = [];
  let scanned = 0;
  const stack = [rootResolved];
  while (stack.length && results.length < maxResults && scanned < maxFiles) {
    const dir = stack.pop();
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) stack.push(full);
        continue;
      }
      if (!entry.isFile() || scanned >= maxFiles || results.length >= maxResults) continue;
      let stat;
      try { stat = fs.statSync(full); } catch { continue; }
      if (stat.size > maxFileBytes) continue;
      scanned += 1;
      let content;
      try {
        const buffer = fs.readFileSync(full);
        if (looksBinary(buffer)) continue;
        content = buffer.toString('utf8');
      } catch { continue; }
      const lines = content.split(/\r?\n/);
      for (let i = 0; i < lines.length && results.length < maxResults; i += 1) {
        if (lines[i].toLowerCase().includes(needle)) {
          results.push({ rel: toRel(rootResolved, full), line: i + 1, text: lines[i].trim().slice(0, 240) });
        }
      }
    }
  }
  return { query: String(query), results, scannedFiles: scanned, truncated: results.length >= maxResults };
}

function runGit(root, args, options = {}) {
  return new Promise((resolve, reject) => {
    execFile('git', args, {
      cwd: root,
      timeout: options.timeout || 10000,
      maxBuffer: 4 * 1024 * 1024,
      windowsHide: true,
    }, (error, stdout) => {
      if (error && !stdout) reject(new Error(`git ${args[0]} thất bại: ${error.message}`));
      else resolve(String(stdout || ''));
    });
  });
}

async function gitStatus(root) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const out = await runGit(rootResolved, ['status', '--porcelain', '--untracked-files=normal']);
  return out.split(/\r?\n/).filter(Boolean).map((line) => ({
    status: line.slice(0, 2),
    path: line.slice(3).trim(),
  })).filter((item) => item.path);
}

async function gitFileDiff(root, rel, options = {}) {
  const maxChars = options.diffMaxChars || DEFAULTS.diffMaxChars;
  const { root: rootResolved, rel: relOut } = resolveInsideRoot(root, rel);
  const [unstaged, staged] = await Promise.all([
    runGit(rootResolved, ['diff', '--', relOut]),
    runGit(rootResolved, ['diff', '--cached', '--', relOut]),
  ]);
  const combined = [staged ? `# Đã stage\n${staged}` : '', unstaged ? `# Chưa stage\n${unstaged}` : '']
    .filter(Boolean).join('\n');
  return { rel: relOut, diff: combined.slice(0, maxChars), truncated: combined.length > maxChars };
}

module.exports = {
  SKIP_DIRS, DEFAULTS,
  resolveInsideRoot, listDir, readTextFile, searchText, gitStatus, gitFileDiff,
};
