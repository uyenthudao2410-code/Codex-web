'use strict';
/*
 * Work Hub file access (catalog 261022: F06, F09, F12).
 * Read-only operations strictly inside one root (the active workspace,
 * resolved by electron/main.js from settings). No writes, no shell:
 * git runs through execFile with an argv array.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFile } = require('child_process');
const { canonicalPathKey } = require('./pathSemantics');

const SKIP_DIRS = new Set(['.git', 'node_modules', '.coding-tools', 'dist', 'target', '.next', 'coverage']);
const DEFAULTS = {
  maxEntries: 300,
  readMaxBytes: 256 * 1024,
  searchMaxResults: 60,
  searchMaxFiles: 1500,
  searchMaxFileBytes: 512 * 1024,
  diffMaxChars: 200 * 1024,
};

function isInside(rootPath, targetPath) {
  const relative = path.relative(rootPath, targetPath);
  return relative === '' || (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
}

function resolveInsideRoot(root, rel) {
  const rootResolved = path.resolve(String(root || ''));
  const requested = String(rel || '').trim();
  const target = requested
    ? (path.isAbsolute(requested) ? path.resolve(requested) : path.resolve(rootResolved, requested))
    : rootResolved;
  if (!isInside(rootResolved, target)) {
    throw new Error('Đường dẫn nằm ngoài thư mục làm việc.');
  }
  // Physical containment: a symlink/junction inside the workspace must not
  // lead reads or searches outside it. Verify with real paths when the
  // target (or its nearest existing ancestor) can be resolved.
  let realRoot = rootResolved;
  try { realRoot = fs.realpathSync(rootResolved); } catch { /* root itself missing: callers surface ENOENT */ }
  let probe = target;
  while (true) {
    try {
      const realTarget = fs.realpathSync(probe);
      if (!isInside(realRoot, realTarget)) throw new Error('Đường dẫn nằm ngoài thư mục làm việc.');
      break;
    } catch (error) {
      if (error && error.message === 'Đường dẫn nằm ngoài thư mục làm việc.') throw error;
      const parent = path.dirname(probe);
      if (parent === probe) break;
      probe = parent;
    }
  }
  return { root: rootResolved, target, rel: path.relative(rootResolved, target).split(path.sep).join('/') };
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
  // Bounded read: never load more than maxBytes (+1 to detect truncation)
  // into memory, however large the file is.
  const fd = fs.openSync(target, 'r');
  let buffer;
  try {
    buffer = Buffer.alloc(Math.min(stat.size, maxBytes + 1));
    const read = fs.readSync(fd, buffer, 0, buffer.length, 0);
    buffer = buffer.subarray(0, read);
  } finally { fs.closeSync(fd); }
  const hash = crypto.createHash('sha256').update(buffer).digest('hex');
  if (looksBinary(buffer)) return { rel: relOut, size: stat.size, binary: true, content: '', truncated: false, hash };
  const truncated = stat.size > maxBytes;
  return {
    rel: relOut,
    size: stat.size,
    binary: false,
    content: buffer.subarray(0, maxBytes).toString('utf8'),
    truncated,
    hash,
  };
}

function writeTextFile(root, rel, content, expectedHash, options = {}) {
  const maxBytes = options.writeMaxBytes || 1024 * 1024;
  const text = String(content ?? '');
  if (Buffer.byteLength(text, 'utf8') > maxBytes) throw new Error('Nội dung vượt quá giới hạn ghi 1MB.');
  const { target, rel: relOut } = resolveInsideRoot(root, rel);
  const exists = fs.existsSync(target);
  if (expectedHash === null || expectedHash === undefined) {
    if (exists) throw new Error('Tệp đã tồn tại — cần xác nhận ghi đè với phiên bản hiện tại.');
  } else {
    if (!exists) throw new Error('Tệp không còn tồn tại.');
    const current = readTextFile(root, relOut, { readMaxBytes: maxBytes });
    if (current.truncated) throw new Error('Tệp quá lớn để kiểm tra phiên bản trước khi ghi.');
    if (current.hash !== expectedHash) throw new Error('Tệp đã thay đổi bên ngoài kể từ khi mở — không ghi đè.');
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const tmp = `${target}.workhub-tmp-${process.pid}`;
  fs.writeFileSync(tmp, text, 'utf8');
  fs.renameSync(tmp, target);
  const after = readTextFile(root, relOut, { readMaxBytes: maxBytes });
  return { rel: relOut, size: after.size, hash: after.hash };
}

function copyIntoWorkspace(root, sourceAbsolute, destDirRel) {
  const source = path.resolve(String(sourceAbsolute || ''));
  if (!fs.existsSync(source) || !fs.statSync(source).isFile()) throw new Error('Tệp nguồn không tồn tại.');
  const { target: destDir } = resolveInsideRoot(root, destDirRel || '');
  fs.mkdirSync(destDir, { recursive: true });
  const ext = path.extname(source);
  const base = path.basename(source, ext);
  let candidate = path.join(destDir, path.basename(source));
  let counter = 2;
  while (fs.existsSync(candidate)) {
    candidate = path.join(destDir, `${base} (${counter})${ext}`);
    counter += 1;
  }
  fs.copyFileSync(source, candidate);
  return { rel: toRel(path.resolve(String(root)), candidate), size: fs.statSync(candidate).size };
}

async function searchText(root, query, options = {}) {
  const needle = String(query || '').trim().toLowerCase();
  if (needle.length < 2) throw new Error('Từ khóa tìm kiếm cần ít nhất 2 ký tự.');
  const maxResults = options.searchMaxResults || DEFAULTS.searchMaxResults;
  const maxFiles = options.searchMaxFiles || DEFAULTS.searchMaxFiles;
  const maxFileBytes = options.searchMaxFileBytes || DEFAULTS.searchMaxFileBytes;
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const results = [];
  let scanned = 0;
  let budgetExhausted = false;
  const stack = [rootResolved];
  const yieldToEventLoop = () => new Promise((resolve) => setImmediate(resolve));
  while (stack.length && results.length < maxResults) {
    if (scanned >= maxFiles) { budgetExhausted = stack.length > 0; break; }
    const dir = stack.pop();
    let entries;
    try { entries = await fs.promises.readdir(dir, { withFileTypes: true }); } catch { continue; }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) stack.push(full);
        continue;
      }
      if (!entry.isFile() || results.length >= maxResults) continue;
      if (scanned >= maxFiles) { budgetExhausted = true; break; }
      let stat;
      try { stat = await fs.promises.stat(full); } catch { continue; }
      if (stat.size > maxFileBytes) continue;
      scanned += 1;
      if (scanned % 100 === 0) await yieldToEventLoop();
      let content;
      try {
        const buffer = await fs.promises.readFile(full);
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
  return { query: String(query), results, scannedFiles: scanned, truncated: results.length >= maxResults, budgetExhausted };
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
  // -z keeps filenames byte-exact (spaces, quotes, Unicode) and reports a
  // rename as two NUL-separated paths: the new path, then the original.
  const out = await runGit(rootResolved, ['status', '--porcelain', '-z', '--untracked-files=normal']);
  const fields = out.split('\0');
  const items = [];
  for (let i = 0; i < fields.length; i += 1) {
    const field = fields[i];
    if (!field || field.length < 4) continue;
    const status = field.slice(0, 2);
    const itemPath = field.slice(3);
    if (!itemPath) continue;
    const item = { status, path: itemPath };
    if (status.includes('R') || status.includes('C')) {
      const original = fields[i + 1];
      if (original) { item.origPath = original; i += 1; }
    }
    items.push(item);
  }
  return items;
}

async function gitLog(root, limit = 20) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const count = Math.max(1, Math.min(100, Number(limit) || 20));
  const out = await runGit(rootResolved, ['log', `--max-count=${count}`, '--pretty=format:%H%x1f%h%x1f%s%x1f%an%x1f%aI', '-z']);
  return out.split('\0').filter(Boolean).map((record) => {
    const [hash, short, subject, author, date] = record.split('\x1f');
    return { hash: hash || '', short: short || '', subject: subject || '', author: author || '', date: date || '' };
  }).filter((item) => item.hash);
}

async function gitShow(root, hash) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const clean = String(hash || '').trim();
  if (!/^[0-9a-fA-F]{7,64}$/.test(clean)) throw new Error('Mã commit không hợp lệ.');
  const out = await runGit(rootResolved, ['show', '--stat', '--pretty=format:%H %s', clean]);
  return { hash: clean, text: out.slice(0, DEFAULTS.diffMaxChars), truncated: out.length > DEFAULTS.diffMaxChars };
}

async function gitBlame(root, rel) {
  const { root: rootResolved, rel: relOut } = resolveInsideRoot(root, rel);
  const out = await runGit(rootResolved, ['blame', '--line-porcelain', '--', relOut]);
  const lines = [];
  let current = null;
  for (const line of out.split(/\r?\n/)) {
    if (/^[0-9a-f]{40} \d+ \d+/.test(line)) {
      if (current) lines.push(current);
      const parts = line.split(' ');
      current = { hash: parts[0], line: Number(parts[2]) || lines.length + 1, author: '', text: '' };
    } else if (current && line.startsWith('author ')) current.author = line.slice(7);
    else if (current && line.startsWith('\t')) current.text = line.slice(1);
  }
  if (current) lines.push(current);
  return { rel: relOut, lines: lines.slice(0, 2000) };
}

async function gitFileDiff(root, rel, options = {}) {
  const maxChars = options.diffMaxChars || DEFAULTS.diffMaxChars;
  const { root: rootResolved, rel: relOut } = resolveInsideRoot(root, rel);
  const [unstaged, staged, head] = await Promise.all([
    runGit(rootResolved, ['diff', '--', relOut]),
    runGit(rootResolved, ['diff', '--cached', '--', relOut]),
    runGit(rootResolved, ['rev-parse', 'HEAD']).catch(() => ''),
  ]);
  const combined = [staged ? `# Đã stage\n${staged}` : '', unstaged ? `# Chưa stage\n${unstaged}` : '']
    .filter(Boolean).join('\n');
  // W2 (§5.1): the diff is only meaningful against the HEAD it was read at.
  // Return that HEAD plus a sha256 fingerprint of the exact (untruncated)
  // diff text so the UI can label the data stale when HEAD moves and can
  // bind patch approval to this exact content server-side, not only to a
  // renderer-side hash.
  const fingerprint = crypto.createHash('sha256').update(combined).digest('hex');
  return {
    rel: relOut,
    diff: combined.slice(0, maxChars),
    truncated: combined.length > maxChars,
    head: String(head || '').trim(),
    fingerprint,
  };
}

async function gitHead(root) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  return (await runGit(rootResolved, ['rev-parse', 'HEAD']).catch(() => '')).trim();
}

async function stagedFileList(rootResolved) {
  const out = await runGit(rootResolved, ['diff', '--cached', '--name-only', '-z']).catch(() => '');
  return out.split('\0').map((file) => file.trim()).filter(Boolean);
}

async function gitCommitFiles(root, files, message, options = {}) {
  // M1.2/B07: commit exactly the files the user selected in the Changes tab.
  // The commit is pathspec-limited, so staged or unstaged changes in other
  // files are never swept in.
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const cleanMessage = String(message || '').trim().slice(0, 4000);
  if (!cleanMessage) throw new Error('Cần nhập nội dung commit.');
  const list = [...new Set((Array.isArray(files) ? files : [])
    .map((file) => String(file || '').trim()).filter(Boolean))];
  if (!list.length) throw new Error('Chưa chọn tệp nào để commit.');
  if (list.length > 200) throw new Error('Quá nhiều tệp trong một commit (tối đa 200).');
  for (const rel of list) resolveInsideRoot(rootResolved, rel);
  const before = (await runGit(rootResolved, ['rev-parse', 'HEAD']).catch(() => '')).trim();
  // expected_head guard (parity report 23/10 §5.3): when the caller passes
  // the HEAD it observed while the user reviewed the change list, refuse
  // BEFORE staging anything if HEAD has since moved — another writer may
  // have committed in between, and the selection was reviewed against the
  // old tree. Absent expectedHead keeps the legacy behavior.
  const expectedHead = String(options?.expectedHead || '').trim().toLowerCase();
  if (expectedHead) {
    if (!/^[0-9a-f]{40,64}$/.test(expectedHead)) throw new Error('expectedHead không hợp lệ.');
    if (before.toLowerCase() !== expectedHead) {
      throw new Error(`HEAD đã thay đổi kể từ lúc tải danh sách (kỳ vọng ${expectedHead.slice(0, 10)}, hiện tại ${before.slice(0, 10) || 'chưa có'}). Tải lại thay đổi rồi commit.`);
    }
  }
  // Repository delivery policy (AGENTS.md): when the repo has a
  // .coding-tools tree and its package.json declares the delivery ritual,
  // that ritual must run BEFORE any commit into the repo. The stage script
  // refreshes and stages only the .coding-tools delivery set; the check
  // verifies it. Refuse up front if the index already contains unrelated
  // staged files, because the snapshot step must never sweep another
  // writer's staged work into a delivery commit.
  const policy = options?.deliveryPolicy === false ? null : detectDeliveryPolicy(rootResolved);
  if (policy) {
    const stagedBefore = await stagedFileList(rootResolved);
    const stagedBeforeSet = new Set(stagedBefore);
    const unrelated = stagedBefore.filter(
      (file) => !list.includes(file) && !file.startsWith('.coding-tools/'),
    );
    if (unrelated.length) {
      throw new Error(`Repo có chính sách delivery nhưng index đang stage tệp ngoài lựa chọn: ${unrelated.slice(0, 5).join(', ')}. Xử lý các tệp đã stage đó trước khi commit.`);
    }
    // Snapshot the exact index tree before the ritual. On any refusal the
    // index is restored from this tree, which also restores the previous
    // staged CONTENT of a path the ritual overwrote — unstaging paths alone
    // would lose it. The working tree and HEAD are never touched by the
    // restore. (write-tree fails on an unmerged index; then fall back to
    // unstaging only the paths this attempt newly staged.)
    const indexTreeBefore = (await runGit(rootResolved, ['write-tree']).catch(() => '')).trim();
    const rollbackIndex = async () => {
      if (indexTreeBefore) {
        await runGit(rootResolved, ['read-tree', indexTreeBefore]).catch(() => '');
        return;
      }
      const stagedNow = await stagedFileList(rootResolved);
      const newlyStaged = stagedNow.filter((file) => !stagedBeforeSet.has(file));
      if (newlyStaged.length) {
        await runGit(rootResolved, ['restore', '--staged', '--', ...newlyStaged]).catch(() => '');
      }
    };
    try {
      await runNpmScript(rootResolved, policy.stage);
      await runNpmScript(rootResolved, policy.check);
    } catch (error) {
      await rollbackIndex();
      throw error;
    }
    const stagedAfterPolicy = await stagedFileList(rootResolved);
    const unexpected = stagedAfterPolicy.filter(
      (file) => !stagedBeforeSet.has(file) && !list.includes(file) && !file.startsWith('.coding-tools/'),
    );
    if (unexpected.length) {
      await rollbackIndex();
      throw new Error(`Delivery policy stage đã stage tệp ngoài .coding-tools: ${unexpected.slice(0, 5).join(', ')}. Commit bị từ chối.`);
    }
    // Re-verify HEAD immediately before committing: the ritual can run for
    // minutes, and another writer may have committed meanwhile. The change
    // selection (and expectedHead, when given) was reviewed against the
    // HEAD captured at entry, so any drift refuses the commit.
    const headAfterPolicy = (await runGit(rootResolved, ['rev-parse', 'HEAD']).catch(() => '')).trim();
    if (headAfterPolicy !== before) {
      await rollbackIndex();
      throw new Error(`HEAD đã thay đổi trong lúc chạy delivery policy (trước ${before.slice(0, 10) || 'chưa có'}, nay ${headAfterPolicy.slice(0, 10) || 'chưa có'}). Tải lại thay đổi rồi commit.`);
    }
  }
  await runGit(rootResolved, ['add', '--', ...list], { timeout: 30000 });
  await runGit(rootResolved, ['commit', '-m', cleanMessage, '--', ...list], { timeout: 30000 });
  const hash = (await runGit(rootResolved, ['rev-parse', 'HEAD'])).trim();
  if (!hash || hash === before) throw new Error('Commit không tạo được — có thể các tệp đã chọn không còn thay đổi.');
  const result = { hash, files: list.length };
  if (policy) {
    result.deliveryPolicy = true;
    // The ritual staged the delivery set into the index; the pathspec
    // commit above deliberately left it staged. Land only that verified
    // .coding-tools set as the snapshot commit, mirroring the manual
    // two-commit delivery flow. Anything unexpected stays staged and is
    // reported instead of being swept into the snapshot.
    const stagedLeft = await stagedFileList(rootResolved);
    const deliveryFiles = stagedLeft.filter((file) => file.startsWith('.coding-tools/'));
    const otherFiles = stagedLeft.filter((file) => !file.startsWith('.coding-tools/'));
    // Only land the snapshot directly on top of the source commit just
    // made; if another writer moved HEAD in between, leave the verified
    // delivery set staged and report it as pending instead of stacking it
    // onto a foreign commit.
    const headNow = (await runGit(rootResolved, ['rev-parse', 'HEAD']).catch(() => '')).trim();
    if (deliveryFiles.length && !otherFiles.length && headNow === hash) {
      await runGit(rootResolved, ['commit', '-m', 'chore(coding-tools): delivery snapshot'], { timeout: 30000 });
      result.deliverySnapshot = (await runGit(rootResolved, ['rev-parse', 'HEAD'])).trim();
    } else if (stagedLeft.length) {
      result.deliverySnapshotPending = stagedLeft;
    }
  }
  return result;
}

function detectDeliveryPolicy(rootResolved) {
  try {
    if (!fs.statSync(path.join(rootResolved, '.coding-tools')).isDirectory()) return null;
    const pkg = JSON.parse(fs.readFileSync(path.join(rootResolved, 'package.json'), 'utf8'));
    const scripts = (pkg && pkg.scripts) || {};
    if (scripts['stage:coding-tools-delivery'] && scripts['check:coding-tools-delivery']) {
      return { stage: 'stage:coding-tools-delivery', check: 'check:coding-tools-delivery' };
    }
  } catch { /* no .coding-tools tree or package.json: no delivery policy */ }
  return null;
}

function runNpmScript(rootResolved, script) {
  // `script` is always one of the two fixed delivery-policy names returned
  // by detectDeliveryPolicy — never caller input. On Windows, Node refuses
  // to spawn npm.cmd directly (EINVAL since the .cmd spawn hardening), so
  // route through cmd.exe there.
  const isWin = process.platform === 'win32';
  const file = isWin ? 'cmd.exe' : 'npm';
  const args = isWin ? ['/d', '/s', '/c', `npm run ${script}`] : ['run', script];
  return new Promise((resolve, reject) => {
    execFile(file, args, { cwd: rootResolved, timeout: 300000, windowsHide: true, maxBuffer: 16 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        const tail = String(stderr || stdout || error.message).trim().split('\n').slice(-4).join('\n');
        reject(new Error(`Delivery policy "${script}" thất bại — commit bị từ chối.\n${tail}`));
        return;
      }
      resolve(String(stdout || ''));
    });
  });
}

function managedWorktreeBase(rootResolved) {
  return path.join(path.dirname(rootResolved), `${path.basename(rootResolved)}.worktrees`);
}

// git reports worktree paths with forward slashes even on Windows, while
// path.join/path.resolve produce backslashes there. Compare managed-path
// prefixes separator-insensitively or managed worktrees are never
// recognized on Windows (found by the M1.3 test on a Windows host).
// Canonical keys additionally collapse 8.3/junction/subst aliases: git
// returns worktree paths in long form while the managed base may be spelled
// in short form, and the prefix must still match.
function pathHasPrefix(candidate, prefix) {
  const candidateKey = canonicalPathKey(candidate);
  const prefixKey = canonicalPathKey(prefix);
  if (!candidateKey || !prefixKey) return false;
  return candidateKey === prefixKey || candidateKey.startsWith(`${prefixKey}${path.sep}`);
}

async function gitWorktreeList(root) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const out = await runGit(rootResolved, ['worktree', 'list', '--porcelain']);
  const items = [];
  let current = null;
  for (const line of out.split(/\r?\n/)) {
    if (line.startsWith('worktree ')) {
      if (current) items.push(current);
      current = { path: line.slice(9), head: '', branch: '', managed: false };
    } else if (current && line.startsWith('HEAD ')) current.head = line.slice(5);
    else if (current && line.startsWith('branch ')) current.branch = line.slice(7).replace('refs/heads/', '');
  }
  if (current) items.push(current);
  const base = managedWorktreeBase(rootResolved);
  for (const item of items) item.managed = pathHasPrefix(item.path, base);
  return items;
}

async function gitWorktreeAdd(root, name, branch) {
  // M1.3/B06: managed worktrees live in a sibling "<project>.worktrees"
  // folder so they are easy to inventory and can never escape the project
  // neighbourhood. The branch is created when it does not exist yet.
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const slug = String(name || '').trim().toLowerCase().replace(/[^a-z0-9-_]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
  if (!slug) throw new Error('Cần tên cho worktree (chữ, số, dấu - hoặc _).');
  const cleanBranch = String(branch || `work/${slug}`).trim().slice(0, 120);
  if (!/^[\w./-]+$/.test(cleanBranch) || cleanBranch.includes('..')) throw new Error('Tên nhánh không hợp lệ.');
  const target = path.join(managedWorktreeBase(rootResolved), slug);
  if (fs.existsSync(target)) throw new Error('Worktree này đã tồn tại.');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const branches = await runGit(rootResolved, ['branch', '--list', cleanBranch]);
  if (branches.trim()) await runGit(rootResolved, ['worktree', 'add', target, cleanBranch], { timeout: 60000 });
  else await runGit(rootResolved, ['worktree', 'add', '-b', cleanBranch, target], { timeout: 60000 });
  return { path: target, branch: cleanBranch };
}

async function gitWorktreeRemove(root, worktreePath) {
  const { root: rootResolved } = resolveInsideRoot(root, '');
  const target = path.resolve(String(worktreePath || ''));
  const base = managedWorktreeBase(rootResolved);
  if (!pathHasPrefix(target, base) || canonicalPathKey(target) === canonicalPathKey(rootResolved)) {
    throw new Error('Chỉ gỡ được worktree do ứng dụng quản lý (trong thư mục .worktrees cạnh dự án).');
  }
  await runGit(rootResolved, ['worktree', 'remove', target], { timeout: 30000 });
  return { removed: target };
}

const IMAGE_MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp' };

function readImageData(root, rel, options = {}) {
  const maxBytes = options.imageMaxBytes || 5 * 1024 * 1024;
  const { target, rel: relOut } = resolveInsideRoot(root, rel);
  const mime = IMAGE_MIME[path.extname(target).toLowerCase()];
  if (!mime) throw new Error('Định dạng ảnh chưa hỗ trợ xem trước.');
  const stat = fs.statSync(target);
  if (stat.size > maxBytes) throw new Error('Ảnh vượt quá giới hạn xem trước 5MB.');
  return { rel: relOut, mime, size: stat.size, base64: fs.readFileSync(target).toString('base64') };
}

module.exports = {
  SKIP_DIRS, DEFAULTS,
  resolveInsideRoot, listDir, readTextFile, writeTextFile, copyIntoWorkspace, readImageData,
  searchText, gitStatus, gitFileDiff, gitLog, gitShow, gitBlame, gitHead, gitCommitFiles,
  gitWorktreeList, gitWorktreeAdd, gitWorktreeRemove,
  pathHasPrefix,
};
