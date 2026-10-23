'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {
  resolveInsideRoot, listDir, readTextFile, writeTextFile, copyIntoWorkspace,
  searchText, gitStatus, gitFileDiff, gitLog, gitBlame, gitHead, gitCommitFiles,
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

test('gitCommitFiles expected_head guard: matching HEAD commits, stale HEAD refuses before staging', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  const head0 = git('rev-parse', 'HEAD').trim();
  assert.equal(await gitHead(root), head0);
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  const ok = await gitCommitFiles(root, ['src/login.js'], 'feat: guarded', { expectedHead: head0 });
  assert.match(ok.hash, /^[0-9a-f]{40}$/);
  // A second change reviewed against the now-stale head0 must be refused
  // before anything is staged, and HEAD must not move.
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v3\n');
  await assert.rejects(
    () => gitCommitFiles(root, ['src/login.js'], 'feat: stale', { expectedHead: head0 }),
    /HEAD đã thay đổi/
  );
  assert.equal(git('rev-parse', 'HEAD').trim(), ok.hash);
  assert.equal(git('diff', '--cached', '--name-only').trim(), '');
  // Malformed expectedHead is rejected outright.
  await assert.rejects(
    () => gitCommitFiles(root, ['src/login.js'], 'feat: bad', { expectedHead: 'xyz' }),
    /expectedHead không hợp lệ/
  );
});

test('delivery policy: repo ritual runs before commit and its staged set lands as a snapshot commit', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  // Fixture "ritual": the stage script refreshes + stages a data file; the
  // check script passes only while a marker exists.
  fs.mkdirSync(path.join(root, '.coding-tools'));
  fs.writeFileSync(path.join(root, 'stage.js'),
    "const fs=require('fs');const{execFileSync}=require('child_process');fs.writeFileSync('.coding-tools/delivery.txt','snap\\n');execFileSync('git',['add','--','.coding-tools/delivery.txt']);\n");
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: 'fixture', private: true,
    scripts: {
      'stage:coding-tools-delivery': 'node stage.js',
      'check:coding-tools-delivery': "node -e \"process.exit(require('fs').existsSync('.coding-tools/delivery.txt')?0:1)\"",
    },
  }));
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  const out = await gitCommitFiles(root, ['src/login.js'], 'feat: with policy');
  assert.equal(out.deliveryPolicy, true);
  assert.match(out.deliverySnapshot || '', /^[0-9a-f]{40}$/);
  const names = git('show', '--name-only', '--format=', 'HEAD').trim();
  assert.equal(names, '.coding-tools/delivery.txt');
  const first = git('show', '--name-only', '--format=', 'HEAD~1').trim();
  assert.equal(first, 'src/login.js');
});

test('delivery policy: a failing check refuses the commit and unstages only this attempt', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  fs.mkdirSync(path.join(root, '.coding-tools'));
  fs.writeFileSync(path.join(root, 'stage.js'),
    "const fs=require('fs');const{execFileSync}=require('child_process');fs.writeFileSync('.coding-tools/delivery.txt','snap\\n');execFileSync('git',['add','--','.coding-tools/delivery.txt']);\n");
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: 'fixture', private: true,
    scripts: {
      'stage:coding-tools-delivery': 'node stage.js',
      'check:coding-tools-delivery': "node -e \"process.exit(1)\"",
    },
  }));
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  const head0 = git('rev-parse', 'HEAD').trim();
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  await assert.rejects(() => gitCommitFiles(root, ['src/login.js'], 'feat: blocked'), /Delivery policy/);
  assert.equal(git('rev-parse', 'HEAD').trim(), head0);
  assert.equal(git('diff', '--cached', '--name-only').trim(), '');
  assert.equal(fs.readFileSync(path.join(root, '.coding-tools', 'delivery.txt'), 'utf8'), 'snap\n');
});

test('delivery policy: unrelated pre-staged files refuse the commit instead of being swept into a snapshot', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  fs.mkdirSync(path.join(root, '.coding-tools'));
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: 'fixture', private: true,
    scripts: {
      'stage:coding-tools-delivery': "node -e \"process.exit(0)\"",
      'check:coding-tools-delivery': "node -e \"process.exit(0)\"",
    },
  }));
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  const head0 = git('rev-parse', 'HEAD').trim();
  fs.writeFileSync(path.join(root, 'README.md'), '# Changed elsewhere\n');
  git('add', '--', 'README.md');
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  await assert.rejects(
    () => gitCommitFiles(root, ['src/login.js'], 'feat: guarded policy'),
    /tệp ngoài lựa chọn/,
  );
  assert.equal(git('rev-parse', 'HEAD').trim(), head0);
  assert.equal(git('diff', '--cached', '--name-only').trim(), 'README.md');
});

test('delivery policy: HEAD moving during the ritual refuses the commit', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  fs.mkdirSync(path.join(root, '.coding-tools'));
  // The "ritual" here simulates a concurrent writer: it stages the delivery
  // file AND lands its own commit while the policy runs.
  fs.writeFileSync(path.join(root, 'stage.js'),
    "const fs=require('fs');const{execFileSync}=require('child_process');fs.writeFileSync('.coding-tools/delivery.txt','snap\\n');fs.appendFileSync('README.md','writer\\n');execFileSync('git',['add','--','.coding-tools/delivery.txt','README.md']);execFileSync('git',['commit','-qm','concurrent writer']);\n");
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: 'fixture', private: true,
    scripts: {
      'stage:coding-tools-delivery': 'node stage.js',
      'check:coding-tools-delivery': "node -e \"process.exit(0)\"",
    },
  }));
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('add', '-A');
  git('commit', '-qm', 'init');
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  await assert.rejects(
    () => gitCommitFiles(root, ['src/login.js'], 'feat: raced'),
    /HEAD đã thay đổi trong lúc chạy delivery policy/,
  );
  // The other writer's commit stands; ours was not created on top of it.
  assert.equal(git('log', '-1', '--format=%s').trim(), 'concurrent writer');
  assert.equal(git('log', '--format=%s').trim().split('\n').filter((s) => s === 'feat: raced').length, 0);
  assert.match(git('status', '--porcelain'), /src\/login\.js/);
});

test('delivery policy: check failure restores the previous staged content of a pre-staged path', async () => {
  const root = fixture();
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  fs.mkdirSync(path.join(root, '.coding-tools'));
  fs.writeFileSync(path.join(root, 'stage.js'),
    "const fs=require('fs');const{execFileSync}=require('child_process');fs.writeFileSync('.coding-tools/delivery.txt','snap\\n');fs.writeFileSync('.coding-tools/notes.txt','ritual overwrite\\n');execFileSync('git',['add','--','.coding-tools/delivery.txt','.coding-tools/notes.txt']);\n");
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    name: 'fixture', private: true,
    scripts: {
      'stage:coding-tools-delivery': 'node stage.js',
      'check:coding-tools-delivery': "node -e \"process.exit(1)\"",
    },
  }));
  git('init', '-q');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  // Pre-stage a .coding-tools file whose staged content must survive the
  // refusal (the guard allows pre-staged delivery files; the ritual then
  // overwrites that path in the index before the check fails).
  fs.writeFileSync(path.join(root, '.coding-tools', 'notes.txt'), 'staged v1\n');
  git('add', '-A');
  git('commit', '-qm', 'init');
  fs.writeFileSync(path.join(root, '.coding-tools', 'notes.txt'), 'staged v2\n');
  git('add', '--', '.coding-tools/notes.txt');
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'v2\n');
  await assert.rejects(() => gitCommitFiles(root, ['src/login.js'], 'feat: blocked'), /Delivery policy/);
  assert.equal(git('show', ':.coding-tools/notes.txt'), 'staged v2\n');
  assert.equal(git('diff', '--cached', '--name-only').trim(), '.coding-tools/notes.txt');
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
