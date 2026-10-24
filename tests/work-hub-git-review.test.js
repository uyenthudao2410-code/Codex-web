'use strict';
/* W5 — git range review contract: rename detection, subsystem grouping,
 * and a source fingerprint bound to the resolved range endpoints. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { gitRangeReview, validateRev, subsystemOf } = require('../electron/services/workHubGitReview');

const GIT_ENV = {
  ...process.env,
  GIT_AUTHOR_NAME: 'T', GIT_AUTHOR_EMAIL: 't@t',
  GIT_COMMITTER_NAME: 'T', GIT_COMMITTER_EMAIL: 't@t',
};

function git(root, args) {
  return execFileSync('git', args, { cwd: root, env: GIT_ENV, encoding: 'utf8' });
}

function fixtureRepo(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-git-review-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  git(root, ['init', '-q', '.']);
  fs.mkdirSync(path.join(root, 'src'), { recursive: true });
  fs.mkdirSync(path.join(root, 'core'), { recursive: true });
  fs.writeFileSync(path.join(root, 'src', 'old.js'), 'a\nb\nc\n');
  fs.writeFileSync(path.join(root, 'core', 'main.py'), 'x\n');
  git(root, ['add', '-A']);
  git(root, ['commit', '-qm', 'one']);
  git(root, ['mv', 'src/old.js', 'src/new.js']);
  fs.writeFileSync(path.join(root, 'src', 'new.js'), 'a\nb\nc\nd\n');
  fs.writeFileSync(path.join(root, 'core', 'main.py'), 'x\ny\n');
  fs.writeFileSync(path.join(root, 'README.md'), 'new\n');
  git(root, ['add', '-A']);
  git(root, ['commit', '-qm', 'two']);
  return root;
}

test('validateRev accepts hashes/refs and rejects range smuggling', () => {
  assert.equal(validateRev('HEAD~1', 'from'), 'HEAD~1');
  assert.equal(validateRev('a1b2c3d', 'from'), 'a1b2c3d');
  assert.throws(() => validateRev('HEAD..HEAD~2', 'from'), /không hợp lệ/);
  assert.throws(() => validateRev('', 'from'), /không hợp lệ/);
  assert.throws(() => validateRev('--upload-pack=x', 'from'), /không hợp lệ/);
});

test('subsystemOf groups by the top-level segment', () => {
  assert.equal(subsystemOf('src/new.js'), 'src');
  assert.equal(subsystemOf('README.md'), '(root)');
});

test('range review reports commits, renames, subsystems and fingerprint', async (t) => {
  const root = fixtureRepo(t);
  const review = await gitRangeReview(root, { from: 'HEAD~1', to: 'HEAD' });
  assert.equal(review.commits.length, 1);
  assert.equal(review.commits[0].subject, 'two');
  assert.ok(review.fromHash.length === 40 && review.toHash.length === 40);
  assert.notEqual(review.fromHash, review.toHash);

  const renamed = review.files.find((f) => f.renamed);
  assert.ok(renamed, 'rename must be detected');
  assert.equal(renamed.origPath, 'src/old.js');
  assert.equal(renamed.path, 'src/new.js');
  assert.equal(renamed.additions, 1);
  assert.equal(review.totals.renames, 1);
  assert.equal(review.totals.files, 3);

  const bySubsystem = Object.fromEntries(review.subsystems.map((s) => [s.subsystem, s]));
  assert.equal(bySubsystem.src.files, 1);
  assert.equal(bySubsystem.core.files, 1);
  assert.equal(bySubsystem['(root)'].files, 1);
  assert.equal(bySubsystem.src.renames, 1);

  assert.match(review.fingerprint, /^[0-9a-f]{64}$/);
  const again = await gitRangeReview(root, { from: 'HEAD~1', to: 'HEAD' });
  assert.equal(again.fingerprint, review.fingerprint, 'same range → same fingerprint');
});

test('IPC/preload/UI wiring sits after workhub:check-url and exposes a specific function', () => {
  const repoRoot = path.join(__dirname, '..');
  const mainSource = fs.readFileSync(path.join(repoRoot, 'electron/main.js'), 'utf8');
  const preloadSource = fs.readFileSync(path.join(repoRoot, 'electron/preload.js'), 'utf8');
  const markup = fs.readFileSync(path.join(repoRoot, 'renderer/index.html'), 'utf8');
  const renderer = fs.readFileSync(path.join(repoRoot, 'renderer/work-hub.js'), 'utf8');

  // The handler must live in the safe zone AFTER workhub:check-url: the
  // work-hub-scope fixture only evaluates main.js up to that handler.
  const checkUrlAt = mainSource.indexOf("secureHandle('workhub:check-url'");
  const handlerAt = mainSource.indexOf("secureHandle('workhub:git-review'");
  assert.ok(checkUrlAt >= 0 && handlerAt > checkUrlAt, 'git-review handler must be registered after check-url');
  const handler = mainSource.slice(handlerAt, handlerAt + 400);
  assert.match(handler, /gitRangeReview\(/);
  assert.match(handler, /scopedWorkHubRoot\(payload\?\.expectedWorkspace\)/);
  assert.match(handler, /payload\?\.from/);
  assert.match(handler, /payload\?\.to/);
  assert.match(mainSource, /require\('\.\/services\/workHubGitReview'\)/);

  // Preload exposes one specific function, not a generic transport.
  assert.match(preloadSource, /workhubGitReview: \(payload\) => ipcRenderer\.invoke\('workhub:git-review', payload\)/);

  // Renderer: base/head inputs + run button near the changes panel, and
  // the render path uses the scoped preload call with a STALE label.
  for (const id of ['whGitReviewFrom', 'whGitReviewTo', 'whGitReviewRun', 'whGitReview']) {
    assert.ok(markup.includes(`id="${id}"`), `index.html must contain #${id}`);
  }
  assert.match(renderer, /workhubGitReview\(\{ from:/);
  assert.match(renderer, /expectedWorkspace: scope\.workspace/);
  assert.match(renderer, /STALE — HEAD hiện tại/);
  assert.match(renderer, /gitReviewIsStale/);
});

test('fingerprint changes when the range endpoint moves', async (t) => {
  const root = fixtureRepo(t);
  fs.writeFileSync(path.join(root, 'core', 'main.py'), 'x\ny\nz\n');
  git(root, ['add', '-A']);
  git(root, ['commit', '-qm', 'three']);
  const wider = await gitRangeReview(root, { from: 'HEAD~2', to: 'HEAD' });
  const headOnly = await gitRangeReview(root, { from: 'HEAD~1', to: 'HEAD' });
  assert.equal(wider.commits.length, 2);
  assert.notEqual(wider.fingerprint, headOnly.fingerprint);
});
