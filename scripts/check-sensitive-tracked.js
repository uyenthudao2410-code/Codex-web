const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const FORBIDDEN_TRACKED_PATHS = ['ACC', 'docs/ac'];
const TOKENISH_VALUE = /(?:^|\s)(?:bearer|basic|token|apikey|api-key)?\s*[=:]?\s*[a-z0-9._~+\/=:-]{16,}(?:[;\s]|$)/i;
const HTTP_SECRET_HEADER = /^\s*(authorization|proxy-authorization|cookie|set-cookie|x-api-key|x-auth-token|api-key)\s*:\s*(.+)$/gim;

function runGit(args) {
  return spawnSync('git', args, {
    encoding: 'utf8',
    windowsHide: true,
  });
}

function nulList(value) {
  return String(value || '').split('\0').filter(Boolean);
}

function fail(lines) {
  for (const line of lines) console.error(line);
  process.exit(1);
}

function looksLikeText(buffer) {
  const sample = buffer.subarray(0, Math.min(buffer.length, 8192));
  if (sample.includes(0)) return false;

  let controls = 0;
  for (const byte of sample) {
    if (byte < 9 || (byte > 13 && byte < 32)) controls += 1;
  }
  return controls <= Math.max(4, Math.floor(sample.length / 100));
}

function rawHttpCredentialDump(text) {
  const headers = new Set();
  for (const match of text.matchAll(HTTP_SECRET_HEADER)) {
    if (TOKENISH_VALUE.test(match[2])) headers.add(match[1].toLowerCase());
  }

  if (headers.size >= 2) return true;

  // Browser/proxy exports often serialize header objects rather than raw
  // header lines. Repeated HTTP frames plus this exact three-family set is a
  // high-signal credential capture even when the values are JSON-escaped.
  const httpFrames = (text.match(/HTTP\/1\.[01]/gi) || []).length;
  return httpFrames >= 4
    && /authorization/i.test(text)
    && /set-cookie/i.test(text)
    && /(?:x-)?api-key/i.test(text);
}

function findSensitiveContentIssues(content) {
  if (!looksLikeText(content)) return [];
  return rawHttpCredentialDump(content.toString('utf8'))
    ? ['raw_http_credential_dump']
    : [];
}

function main() {
  const root = runGit(['rev-parse', '--show-toplevel']);
  if (root.status !== 0) fail(['repository secret check: not inside a Git worktree']);

  const repoRoot = root.stdout.trim();
  const pathCheck = runGit([
    '-C',
    repoRoot,
    'ls-files',
    '-z',
    '--',
    ...FORBIDDEN_TRACKED_PATHS,
  ]);
  if (pathCheck.status !== 0) {
    fail([`repository secret check: git ls-files failed (exit ${pathCheck.status})`]);
  }

  const issues = nulList(pathCheck.stdout).map((trackedPath) => ({
    path: trackedPath,
    rule: 'forbidden_credential_path',
  }));

  const tracked = runGit(['-C', repoRoot, 'ls-files', '-z']);
  if (tracked.status !== 0) {
    fail([`repository secret check: tracked-file enumeration failed (exit ${tracked.status})`]);
  }

  const deleted = runGit([
    '-C',
    repoRoot,
    'diff',
    '--name-only',
    '--diff-filter=D',
    '-z',
  ]);
  if (deleted.status !== 0) {
    fail([`repository secret check: deleted-file enumeration failed (exit ${deleted.status})`]);
  }
  const deletedFromWorkingTree = new Set(nulList(deleted.stdout));

  for (const trackedPath of nulList(tracked.stdout)) {
    const absolutePath = path.join(repoRoot, trackedPath);
    let content;
    try {
      const metadata = fs.lstatSync(absolutePath);
      // A gitlink is tracked by this repository as a directory entry; its
      // contents belong to its own repository and cannot be scanned here.
      if (metadata.isDirectory()) continue;
      content = metadata.isSymbolicLink()
        ? Buffer.from(fs.readlinkSync(absolutePath))
        : fs.readFileSync(absolutePath);
    } catch {
      if (deletedFromWorkingTree.has(trackedPath)) continue;
      issues.push({ path: trackedPath, rule: 'tracked_file_unreadable' });
      continue;
    }
    for (const rule of findSensitiveContentIssues(content)) {
      issues.push({ path: trackedPath, rule });
    }
  }

  if (issues.length) {
    fail([
      'repository secret check: tracked content or paths may contain credential material:',
      ...issues.map((issue) => `  ${issue.path} (${issue.rule})`),
      'Remove the file from the current tip, rotate/revoke any credential that may have been committed, and assess history rewrite separately.',
    ]);
  }

  console.log('repository secret check: PASS');
}

if (require.main === module) main();

module.exports = { findSensitiveContentIssues, looksLikeText, rawHttpCredentialDump };
