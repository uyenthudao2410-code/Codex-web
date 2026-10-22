'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {
  resolveInsideRoot, listDir, readTextFile, writeTextFile, copyIntoWorkspace,
  searchText, gitStatus, gitFileDiff, gitLog, gitBlame, gitCommitFiles,
  gitWorktreeList, gitWorktreeAdd, gitWorktreeRemove,
} = require('../electron/services/workHubFiles');

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'workhub-'));
  fs.mkdirSync(path.join(root, 'src'));
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'function login() {\n  return checkPassword();\n}\n');
  fs.writeFileSync(path.join(root, 'README.md'), '# Demo\nMật khẩu được kiểm tra ở login.\n');
  fs.writeFileSync(path.join(root, 'bin.dat'), Buffer.from([0, 1, 2, 0, 3]));
  fs.mkdirSync(path.join(root, 'node_modules', 'pkg'), { recursive: true });
  fs.writeFileSync(path.join(root, 'node_modules', 'pkg', 'index.js'), 'checkPassword in dependency\n');
  return root;
}

test('resolveInsideRoot blocks escaping the workspace', () => {
  const root = fixture();
  assert.equal(resolveInsideRoot(root, 'src/login.js').rel, 'src/login.js');
  assert.throws(() => resolveInsideRoot(root, '../outside.txt'), /ngoài thư mục/);
  assert.throws(() => resolveInsideRoot(root, path.join(os.tmpdir(), 'elsewhere.txt')), /ngoài thư mục/);
});

test('F06 listDir lists dirs first with sizes and respects the cap', () => {
  const root = fixture();
  const { entries, rel } = listDir(root, '');
  assert.equal(rel, '');
  assert.equal(entries[0].type, 'dir');
  const readme = entries.find((e) => e.name === 'README.md');
  assert.ok(readme.size > 0);
  const src = listDir(root, 'src');
  assert.deepEqual(src.entries.map((e) => e.name), ['login.js']);
});

test('F06 readTextFile returns text and flags binary files', () => {
  const root = fixture();
  const text = readTextFile(root, 'src/login.js');
  assert.equal(text.binary, false);
  assert.match(text.content, /checkPassword/);
  const bin = readTextFile(root, 'bin.dat');
  assert.equal(bin.binary, true);
  assert.equal(bin.content, '');
});

test('F06 searchText finds content lines and skips dependency dirs', async () => {
  const root = fixture();
  const { results } = await searchText(root, 'checkPassword');
  assert.ok(results.some((r) => r.rel === 'src/login.js' && r.line === 2));
  assert.ok(!results.some((r) => r.rel.includes('node_modules')));
  await assert.rejects(() => searchText(root, 'x'), /ít nhất 2 ký tự/);
});

test('D0 containment: symlink inside the workspace cannot escape it', () => {
  const root = fixture();
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'workhub-outside-'));
  fs.writeFileSync(path.join(outside, 'secret.txt'), 'top secret');
  try {
    fs.symlinkSync(outside, path.join(root, 'link-out'), 'junction');
  } catch { return; /* symlink not permitted on this platform */ }
  assert.throws(() => readTextFile(root, 'link-out/secret.txt'), /ngoài thư mục/);
  assert.throws(() => listDir(root, 'link-out'), /ngoài thư mục/);
});

test('D0 readTextFile is bounded and returns a content hash', () => {
  const root = fixture();
  const big = path.join(root, 'big.txt');
  fs.writeFileSync(big, 'a'.repeat(5000));
  const out = readTextFile(root, 'big.txt', { readMaxBytes: 1024 });
  assert.equal(out.truncated, true);
  assert.equal(out.content.length, 1024);
  assert.match(out.hash, /^[0-9a-f]{64}$/);
});

test('F08 writeTextFile honors the expected-hash guard', () => {
  const root = fixture();
  const before = readTextFile(root, 'src/login.js');
  const written = writeTextFile(root, 'src/login.js', `${before.content}// edited\n`, before.hash);
  assert.notEqual(written.hash, before.hash);
  assert.throws(() => writeTextFile(root, 'src/login.js', 'stale write', before.hash), /đã thay đổi bên ngoài/);
  assert.throws(() => writeTextFile(root, 'README.md', 'overwrite', null), /đã tồn tại/);
  const created = writeTextFile(root, 'notes/new.txt', 'hello', null);
  assert.equal(created.rel, 'notes/new.txt');
});

test('F07 copyIntoWorkspace renames on collision', () => {
  const root = fixture();
  const sourceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'workhub-src-'));
  const source = path.join(sourceDir, 'README.md');
  fs.writeFileSync(source, 'imported');
  const first = copyIntoWorkspace(root, source, 'imports');
  assert.equal(first.rel, 'imports/README.md');
  const second = copyIntoWorkspace(root, source, 'imports');
  assert.equal(second.rel, 'imports/README (2).md');
});

function gitRepo() {
  const root = fixture();
  const { execFileSync } = require('node:child_process');
  const git = (...args) => execFileSync('git', args, { cwd: root });
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '.');
  git('commit', '-qm', 'init');
  return { root, git };
}

test('F09 git status and diff report working-tree changes', async () => {
  const { root } = gitRepo();
  fs.appendFileSync(path.join(root, 'src', 'login.js'), '// changed\n');
  const status = await gitStatus(root);
  assert.ok(status.some((item) => item.path === 'src/login.js'));
  const { diff } = await gitFileDiff(root, 'src/login.js');
  assert.match(diff, /\+.. changed/);
});

test('D0 git status -z keeps renames, untracked and unicode names exact', async () => {
  const { root, git } = gitRepo();
  git('mv', 'src/login.js', 'src/login-renamed.js');
  fs.writeFileSync(path.join(root, 'tệp mới.txt'), 'noi dung');
  const status = await gitStatus(root);
  const rename = status.find((item) => item.path === 'src/login-renamed.js');
  assert.ok(rename, 'rename entry exists');
  assert.equal(rename.origPath, 'src/login.js');
  assert.ok(status.some((item) => item.path === 'tệp mới.txt' && item.status === '??'));
});

test('F25 gitLog and gitBlame read real history', async () => {
  const { root } = gitRepo();
  const log = await gitLog(root, 5);
  assert.equal(log.length, 1);
  assert.equal(log[0].subject, 'init');
  const blame = await gitBlame(root, 'src/login.js');
  assert.ok(blame.lines.length >= 3);
  assert.equal(blame.lines[0].author, 'Test');
});

test('M1.2 gitCommitFiles commits only the selected paths', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'changed\n');
  fs.writeFileSync(path.join(root, 'README.md'), 'changed too\n');
  fs.writeFileSync(path.join(root, 'new.txt'), 'brand new\n');
  const result = await gitCommitFiles(root, ['src/login.js', 'new.txt'], 'feat: selected only');
  assert.equal(result.files, 2);
  assert.match(result.hash, /^[0-9a-f]{40}$/);
  const committed = git('show', '--pretty=format:', '--name-only', 'HEAD').trim().split('\n').sort();
  assert.deepEqual(committed, ['new.txt', 'src/login.js']);
  const status = await gitStatus(root);
  assert.deepEqual(status.map((item) => item.path), ['README.md']);
  await assert.rejects(() => gitCommitFiles(root, [], 'x'), /Chưa chọn tệp/);
  await assert.rejects(() => gitCommitFiles(root, ['README.md'], '  '), /nội dung commit/);
  await assert.rejects(() => gitCommitFiles(root, ['../outside.txt'], 'x'), /ngoài thư mục/);
});

test('M1.3 managed worktrees: add, list, remove inside the sibling folder only', async () => {
  const parent = fs.mkdtempSync(path.join(os.tmpdir(), 'workhub-wt-'));
  const root = path.join(parent, 'proj');
  fs.mkdirSync(root);
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  fs.writeFileSync(path.join(root, 'a.txt'), 'a\n');
  git('add', '-A');
  git('commit', '-qm', 'init');
  const added = await gitWorktreeAdd(root, 'Fix Login!', '');
  assert.equal(added.branch, 'work/fix-login');
  assert.ok(added.path.includes(`${path.sep}proj.worktrees${path.sep}fix-login`));
  assert.ok(fs.existsSync(path.join(added.path, 'a.txt')));
  const list = await gitWorktreeList(root);
  assert.equal(list.length, 2);
  assert.equal(list.find((item) => item.managed)?.branch, 'work/fix-login');
  await assert.rejects(() => gitWorktreeRemove(root, root), /Chỉ gỡ được worktree do ứng dụng quản lý/);
  const removed = await gitWorktreeRemove(root, added.path);
  assert.equal(removed.removed, added.path);
  assert.equal((await gitWorktreeList(root)).length, 1);
});
