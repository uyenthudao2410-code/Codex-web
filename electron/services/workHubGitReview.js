'use strict';
/*
 * Work Hub Git range review (W5 — WebCodex §8 git_review contract port).
 *
 * workHubFiles already covers working-tree status/diff/log/show/blame.
 * What was missing is committed-range analysis: for a range `from..to`,
 * report the commit list, per-file changes with rename detection
 * (git -M), additions/deletions, grouping by subsystem (top-level path
 * segment) and a sha256 source fingerprint of the exact range content so
 * a review can be bound to — and invalidated by — the reviewed range.
 *
 * Read-only: every command is a query; nothing here mutates the repo.
 */
const { execFile } = require('child_process');
const crypto = require('crypto');
const path = require('path');

const MAX_COMMITS = 200;
const MAX_FILES = 500;

// A rev is a hash, HEAD, a ref name or a short relative form (HEAD~3).
// '..' is rejected so callers cannot smuggle their own range syntax;
// the range is always built here from two separate revs.
const REV_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/~^@{}-]{0,99}$/;

function validateRev(raw, label) {
  const rev = String(raw || '').trim();
  if (!rev || rev.includes('..') || !REV_PATTERN.test(rev)) {
    throw new Error(`Rev ${label} không hợp lệ.`);
  }
  return rev;
}

function runGit(root, args, options = {}) {
  return new Promise((resolve, reject) => {
    execFile('git', args, {
      cwd: root,
      timeout: options.timeout || 15000,
      maxBuffer: 8 * 1024 * 1024,
      windowsHide: true,
    }, (error, stdout) => {
      if (error && !stdout) reject(new Error(`git ${args[0]} thất bại: ${error.message}`));
      else resolve(String(stdout || ''));
    });
  });
}

function subsystemOf(filePath) {
  const parts = String(filePath).split('/').filter(Boolean);
  return parts.length > 1 ? parts[0] : '(root)';
}

function parseNameStatus(zText) {
  const fields = String(zText || '').split('\0');
  const files = [];
  for (let i = 0; i < fields.length; i += 1) {
    const status = fields[i];
    if (!status) continue;
    const code = status[0];
    if (code === 'R' || code === 'C') {
      const origPath = fields[i + 1] || '';
      const filePath = fields[i + 2] || '';
      i += 2;
      if (filePath) files.push({ status: code, path: filePath, origPath, renamed: code === 'R' });
    } else {
      const filePath = fields[i + 1] || '';
      i += 1;
      if (filePath) files.push({ status: code, path: filePath, origPath: null, renamed: false });
    }
  }
  return files;
}

function parseNumstat(zText) {
  // Verified -z layout (git 2.43): normal entries are one field
  // "adds\tdels\tpath"; rename entries are "adds\tdels\t" + "old" + "new"
  // as three separate NUL fields. Stats are keyed by the NEW path.
  const stats = new Map();
  const fields = String(zText || '').split('\0');
  for (let i = 0; i < fields.length; i += 1) {
    const match = fields[i].match(/^(-|\d+)\t(-|\d+)\t([\s\S]*)$/);
    if (!match) continue;
    let filePath = match[3];
    if (!filePath) {
      // Rename form: the following two fields are old and new paths.
      i += 1;
      i += 1;
      filePath = fields[i] || '';
    }
    if (!filePath) continue;
    stats.set(filePath, {
      additions: match[1] === '-' ? null : Number(match[1]),
      deletions: match[2] === '-' ? null : Number(match[2]),
      binary: match[1] === '-' && match[2] === '-',
    });
  }
  return stats;
}

async function gitRangeReview(root, range = {}) {
  const rootResolved = path.resolve(String(root || ''));
  const from = validateRev(range.from || 'HEAD~1', 'from');
  const to = validateRev(range.to || 'HEAD', 'to');
  const spec = `${from}..${to}`;

  const [fromHashRaw, toHashRaw, logOut, nameStatusOut, numstatOut] = await Promise.all([
    runGit(rootResolved, ['rev-parse', '--verify', `${from}^{commit}`]),
    runGit(rootResolved, ['rev-parse', '--verify', `${to}^{commit}`]),
    runGit(rootResolved, ['log', `--max-count=${MAX_COMMITS}`, '--pretty=format:%H%x1f%s%x1f%an%x1f%aI', '-z', spec]),
    runGit(rootResolved, ['diff', '--name-status', '-M', '-z', spec]),
    runGit(rootResolved, ['diff', '--numstat', '-z', spec]),
  ]);
  const fromHash = fromHashRaw.trim();
  const toHash = toHashRaw.trim();

  const commits = logOut.split('\0').filter(Boolean).map((record) => {
    const [hash, subject, author, date] = record.split('\x1f');
    return { hash: hash || '', subject: subject || '', author: author || '', date: date || '' };
  }).filter((c) => c.hash);

  const stats = parseNumstat(numstatOut);
  const allFiles = parseNameStatus(nameStatusOut);
  const files = allFiles.slice(0, MAX_FILES).map((file) => {
    const stat = stats.get(file.path) || { additions: null, deletions: null, binary: false };
    return { ...file, subsystem: subsystemOf(file.path), ...stat };
  });

  const subsystems = new Map();
  for (const file of files) {
    const group = subsystems.get(file.subsystem) || { subsystem: file.subsystem, files: 0, additions: 0, deletions: 0, renames: 0 };
    group.files += 1;
    group.additions += file.additions || 0;
    group.deletions += file.deletions || 0;
    if (file.renamed) group.renames += 1;
    subsystems.set(file.subsystem, group);
  }

  const totals = {
    files: allFiles.length,
    commits: commits.length,
    additions: files.reduce((sum, f) => sum + (f.additions || 0), 0),
    deletions: files.reduce((sum, f) => sum + (f.deletions || 0), 0),
    renames: files.filter((f) => f.renamed).length,
  };

  // Source fingerprint of the range: binds the resolved endpoint hashes
  // and the canonical per-file change list. If either endpoint moves or
  // the range content changes, the fingerprint changes.
  const canonical = [
    fromHash,
    toHash,
    ...allFiles.map((f) => `${f.status}\t${f.origPath || ''}\t${f.path}`),
  ].join('\n');
  const fingerprint = crypto.createHash('sha256').update(canonical).digest('hex');

  return {
    from, to, fromHash, toHash,
    commits,
    files,
    subsystems: [...subsystems.values()].sort((a, b) => b.files - a.files || a.subsystem.localeCompare(b.subsystem)),
    totals,
    fingerprint,
    truncated: allFiles.length > MAX_FILES || commits.length >= MAX_COMMITS,
  };
}

module.exports = { gitRangeReview, validateRev, parseNameStatus, subsystemOf };
