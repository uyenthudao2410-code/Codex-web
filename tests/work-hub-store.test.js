'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const storeApi = require('../renderer/work-hub-store');
const {
  normalizeText, fillTemplate, createStore, buildRequest,
  handoffPreview, formatHandoffText, searchAll, TASK_TYPES,
} = storeApi;
const store = storeApi;
function freshStore() { return createStore(memoryAdapter()); }
const PROJECT_A = 'E:\\DEV\\Alpha';
const PROJECT_B = 'E:\\DEV\\Beta';

function memoryAdapter() {
  let saved = null;
  return {
    load: () => saved,
    save: (data) => { saved = JSON.parse(JSON.stringify(data)); },
    dump: () => saved,
  };
}

test('normalizeText strips Vietnamese diacritics for search', () => {
  assert.equal(normalizeText('Tìm kiếm Thư mục Đã lưu'), 'tim kiem thu muc da luu');
  assert.equal(normalizeText('  Nhiều   khoảng  trắng '), 'nhieu khoang trang');
});

test('F01 prompt library: seeds, upsert, fill, remove, persists', () => {
  const adapter = memoryAdapter();
  const store = createStore(adapter);
  assert.ok(store.listPrompts().length >= 3);
  const created = store.upsertPrompt({ name: 'Mẫu của tôi', body: 'Làm {{request}} trong {{project}}' });
  assert.equal(fillTemplate(created.body, { request: 'việc A', project: 'P1' }), 'Làm việc A trong P1');
  assert.equal(fillTemplate('X {{missing}} Y', {}), 'X {{missing}} Y');
  const reopened = createStore(adapter);
  assert.ok(reopened.listPrompts().some((p) => p.id === created.id));
  reopened.removePrompt(created.id);
  assert.ok(!createStore(adapter).listPrompts().some((p) => p.id === created.id));
  assert.throws(() => store.upsertPrompt({ name: '', body: 'x' }), /Tên mẫu/);
});

test('F03 pins: pinned projects sort first, alias is the label', () => {
  const store = createStore(memoryAdapter());
  store.setPin('E:\\DEV\\Beta', { pinned: true, alias: 'Dự án Beta' });
  const sorted = store.sortProjects(['E:\\DEV\\Alpha', 'E:\\DEV\\Beta', 'E:\\DEV\\Gamma']);
  assert.equal(sorted[0], 'E:\\DEV\\Beta');
  assert.equal(store.projectLabel('E:\\DEV\\Beta'), 'Dự án Beta');
  assert.equal(store.projectLabel('E:\\DEV\\Alpha'), 'Alpha');
  store.setPin('E:\\DEV\\Beta', { pinned: false, alias: '' });
  assert.equal(store.pinOf('E:\\DEV\\Beta').pinned, false);
});

test('F05 basket is isolated per project and dedupes paths', () => {
  const store = createStore(memoryAdapter());
  store.addToBasket('E:\\A', { path: 'src\\a.js', size: 10 });
  store.addToBasket('E:\\A', { path: 'src/a.js', size: 10 });
  store.addToBasket('E:\\B', { path: 'src\\b.js' });
  assert.equal(store.basketFor('E:\\A').length, 1);
  assert.equal(store.basketFor('E:\\B').length, 1);
  assert.match(store.contextPackageText('E:\\A'), /src\\a\.js \(10 bytes\)/);
  store.removeFromBasket('E:\\A', 'src/a.js');
  assert.equal(store.basketFor('E:\\A').length, 0);
});

test('F04 buildRequest enforces required fields and appends completion criteria', () => {
  assert.throws(() => buildRequest({ type: 'bugfix', fields: {} }), /Hiện tượng lỗi/);
  const text = buildRequest({
    type: 'bugfix',
    fields: { symptom: 'Đăng nhập lỗi 500', expected: 'Đăng nhập thành công' },
    project: 'E:\\Shop',
    filesText: 'Ngữ cảnh: a.js',
  });
  assert.match(text, /\[Sửa lỗi\] Dự án: E:\\Shop/);
  assert.match(text, /Hiện tượng lỗi: Đăng nhập lỗi 500/);
  assert.match(text, /Tiêu chí hoàn thành:/);
  assert.ok(TASK_TYPES.review);
});

test('F20 recipes CRUD with validation', () => {
  const store = createStore(memoryAdapter());
  const recipe = store.upsertRecipe({ name: 'Test module', command: 'npm test', cwd: 'E:\\A' });
  assert.equal(store.listRecipes().length, 1);
  store.upsertRecipe({ id: recipe.id, name: 'Test module', command: 'npm run test:unit', cwd: 'E:\\A' });
  assert.equal(store.listRecipes()[0].command, 'npm run test:unit');
  assert.throws(() => store.upsertRecipe({ name: 'x', command: '' }), /Lệnh/);
  store.removeRecipe(recipe.id);
  assert.equal(store.listRecipes().length, 0);
});

test('F20 project recipes include subdirectories and shared commands without sibling projects', () => {
  const s = freshStore();
  s.upsertRecipe({ name: 'Root', command: 'npm test', cwd: PROJECT_A });
  s.upsertRecipe({ name: 'Module', command: 'npm test', cwd: `${PROJECT_A}\\packages\\web` });
  s.upsertRecipe({ name: 'Other', command: 'npm test', cwd: PROJECT_B });
  s.upsertRecipe({ name: 'Sibling', command: 'npm test', cwd: `${PROJECT_A}-old` });
  s.upsertRecipe({ name: 'Shared', command: 'git status', cwd: '' });
  assert.deepEqual(s.listRecipes('e:/dev/ALPHA/').map((recipe) => recipe.name), ['Root', 'Module', 'Shared']);
  assert.deepEqual(s.listRecipes(PROJECT_B).map((recipe) => recipe.name), ['Other', 'Shared']);
  assert.equal(s.listRecipes().length, 5);
  assert.deepEqual(s.listRecipes(''), []);
});

test('F22 notification gate fires once per event and honors the toggle', () => {
  const store = createStore(memoryAdapter());
  assert.equal(store.claimNotification('task-1:done'), true);
  assert.equal(store.claimNotification('task-1:done'), false);
  assert.equal(store.claimNotification('task-2:failed'), true);
  store.setNotificationsEnabled(false);
  assert.equal(store.claimNotification('task-3:done'), false);
});

test('F29 handoff preview separates done from unverified work', () => {
  const preview = handoffPreview({
    objective: 'Sửa lỗi đăng nhập',
    status: 'paused',
    next_step: 'Chạy test',
    steps: [
      { title: 'Đọc mã', status: 'done' },
      { title: 'Chạy test', status: 'pending' },
    ],
    tests: [{ name: 'login.test', status: 'failed' }],
    files: [{ path: 'src/login.js' }],
  });
  assert.deepEqual(preview.doneSteps, ['Đọc mã']);
  assert.ok(preview.unverified.some((x) => x.includes('Chạy test')));
  assert.ok(preview.unverified.some((x) => x.includes('login.test')));
  const text = formatHandoffText(preview);
  assert.match(text, /Mục tiêu: Sửa lỗi đăng nhập/);
  assert.match(text, /Bước tiếp theo: Chạy test/);
  assert.equal(handoffPreview(null), null);
});

test('F31 searchAll matches without diacritics and ranks title hits first', () => {
  const entries = [
    { kind: 'page', title: 'Cài đặt', detail: 'tùy chọn ứng dụng' },
    { kind: 'prompt', title: 'Sửa lỗi đăng nhập', detail: 'mẫu' },
    { kind: 'recipe', title: 'Test module', detail: 'cai dat lai moi truong' },
  ];
  const byTitle = searchAll(entries, 'cai dat');
  assert.equal(byTitle[0].title, 'Cài đặt');
  const byDetail = searchAll(entries, 'moi truong');
  assert.equal(byDetail.length, 1);
  assert.equal(byDetail[0].kind, 'recipe');
  assert.deepEqual(searchAll(entries, ''), []);
  assert.deepEqual(searchAll(entries, 'khong-co-dau-nay'), []);
});

test('D0 handoff uses the canonical projection schema (steps.text/test_results/modified_files)', () => {
  const task = {
    task_id: 'task-1',
    objective: 'Sửa đăng nhập',
    status: 'in_progress',
    details_available: true,
    orchestration: { run_id: 'run-9' },
    steps: [
      { id: 's1', text: 'Đọc mã đăng nhập', status: 'completed' },
      { id: 's2', text: 'Viết test', status: 'in_progress' },
    ],
    test_results: [
      { command: 'npm test', status: 'failed', exit_code: 1, duration_ms: 42 },
      { command: 'npm run lint', status: 'passed', exit_code: 0 },
    ],
    modified_files: [{ path: 'src/login.js', operation: 'update' }],
    last_build_report: null,
  };
  const preview = store.handoffPreview(task);
  assert.deepEqual(preview.doneSteps, ['Đọc mã đăng nhập']);
  assert.ok(preview.unverified.some((u) => u.includes('Viết test')));
  assert.ok(preview.unverified.some((u) => u.includes('npm test')));
  assert.deepEqual(preview.files, ['src/login.js']);
  assert.equal(preview.taskId, 'task-1');
  assert.equal(preview.runId, 'run-9');
  const report = store.buildReportText(task, { generatedAt: '2026-10-22T00:00:00Z' });
  assert.match(report, /Đọc mã đăng nhập/);
  assert.match(report, /LỖI · npm test/);
});

test('D0 handoff marks missing detail instead of inventing results', () => {
  const preview = store.handoffPreview({ objective: 'X', status: 'running', details_available: false });
  assert.equal(preview.detailsAvailable, false);
  assert.ok(!preview.unverified.some((u) => u.includes('Chưa có kết quả kiểm thử')));
  assert.match(store.formatHandoffText(preview), /details_available=false/);
});

test('F02 drafts are per project and survive a store reload', () => {
  const adapter = memoryAdapter();
  const s = createStore(adapter);
  s.saveDraft(PROJECT_A, 'yêu cầu đang soạn');
  const reopened = createStore(adapter);
  assert.equal(reopened.getDraft(PROJECT_A).text, 'yêu cầu đang soạn');
  assert.equal(reopened.getDraft(PROJECT_A).type, 'bugfix');
  assert.equal(reopened.getDraft(PROJECT_B), null);
  reopened.saveDraft(PROJECT_A, '');
  assert.equal(createStore(adapter).getDraft(PROJECT_A), null);
});

test('F02 full request draft restores task fields, prompt and preview per project', () => {
  const adapter = memoryAdapter();
  const s = createStore(adapter);
  s.saveDraft(PROJECT_A, {
    type: 'feature',
    fields: { goal: 'Thêm tìm kiếm', behavior: 'Mở đúng tệp', constraints: 'Giữ thay đổi ngoài phạm vi' },
    promptId: 'seed-docs',
    text: 'Bản yêu cầu đã chỉnh sửa',
  });
  s.saveDraft(PROJECT_B, { type: 'review', fields: { scope: 'module B' }, promptId: 'seed-review', text: '' });
  const reopened = createStore(adapter);
  const a = reopened.getDraft('e:/dev/alpha/');
  assert.equal(a.type, 'feature');
  assert.deepEqual(a.fields, { goal: 'Thêm tìm kiếm', behavior: 'Mở đúng tệp', constraints: 'Giữ thay đổi ngoài phạm vi' });
  assert.equal(a.promptId, 'seed-docs');
  assert.equal(a.text, 'Bản yêu cầu đã chỉnh sửa');
  assert.ok(a.updatedAt > 0);
  assert.equal(reopened.getDraft(PROJECT_B).fields.scope, 'module B');
  a.fields.goal = 'Không được sửa store qua tham chiếu';
  assert.equal(reopened.getDraft(PROJECT_A).fields.goal, 'Thêm tìm kiếm');
  reopened.saveDraft(PROJECT_A, 'Bản preview mới');
  const updated = createStore(adapter).getDraft(PROJECT_A);
  assert.equal(updated.text, 'Bản preview mới');
  assert.equal(updated.type, 'feature');
  assert.equal(updated.fields.goal, 'Thêm tìm kiếm');
  reopened.clearDraft(PROJECT_A);
  assert.equal(createStore(adapter).getDraft(PROJECT_A), null);
  assert.equal(createStore(adapter).getDraft(PROJECT_B).type, 'review');
});

test('F02 draft reload validates known form fields and enforces content limits', () => {
  const adapter = memoryAdapter();
  adapter.save({ drafts: {
    [store.workspaceKeyOf(PROJECT_A)]: {
      type: 'feature', text: 'x'.repeat(21000), promptId: 'p'.repeat(250),
      fields: { goal: 'g'.repeat(5000), unknown: 'not a form field' },
    },
    [store.workspaceKeyOf(PROJECT_B)]: { text: 'legacy draft', updatedAt: 17 },
  } });
  const s = createStore(adapter);
  const draft = s.getDraft(PROJECT_A);
  assert.equal(draft.text.length, 20000);
  assert.equal(draft.promptId.length, 200);
  assert.equal(draft.fields.goal.length, 4000);
  assert.equal(draft.fields.unknown, undefined);
  assert.equal(s.getDraft(PROJECT_B).text, 'legacy draft');
  assert.equal(s.getDraft(PROJECT_B).updatedAt, 17);
  assert.equal(s.getDraft(PROJECT_B).type, 'bugfix');
  assert.equal(s.saveDraft(PROJECT_B, []), null);
});

test('F10 patch approval is bound to the exact diff hash', () => {
  const s = freshStore();
  const hash = store.hashText('diff --git a/x b/x\n+line');
  assert.equal(s.isPatchApproved('src/x.js', hash), false);
  s.approvePatch('src/x.js', hash);
  assert.equal(s.isPatchApproved('src/x.js', hash), true);
  assert.equal(s.isPatchApproved('src/x.js', store.hashText('diff khác')), false);
});

test('F15 queue orders, pauses and dispatches one item at a time', () => {
  const s = freshStore();
  const a = s.enqueue(PROJECT_A, { title: 'Việc 1', text: '...' });
  const b = s.enqueue(PROJECT_A, { title: 'Việc 2', text: '...' });
  s.moveQueueItem(PROJECT_A, b.id, -1);
  assert.equal(s.nextQueuedItem(PROJECT_A).id, b.id);
  s.setQueuePaused(PROJECT_A, true);
  assert.equal(s.nextQueuedItem(PROJECT_A), null);
  s.setQueuePaused(PROJECT_A, false);
  s.setQueueItemStatus(PROJECT_A, b.id, 'running');
  assert.equal(s.nextQueuedItem(PROJECT_A).id, a.id);
});

test('F18 feedback tracks saved/copied/acknowledged separately', () => {
  const s = freshStore();
  const item = s.addFeedback(PROJECT_A, 'chỉ sửa module A');
  assert.equal(item.state, 'saved');
  s.setFeedbackState(PROJECT_A, item.id, 'copied');
  assert.equal(s.listFeedback(PROJECT_A)[0].state, 'copied');
  s.setFeedbackState(PROJECT_A, item.id, 'acknowledged');
  assert.equal(s.listFeedback(PROJECT_A)[0].state, 'acknowledged');
});

test('F23 goal prep builds a bounded continuation request', () => {
  const s = freshStore();
  s.setGoalPrep(PROJECT_A, { criteria: 'test đạt', maxTurns: 3, maxMinutes: 30 });
  const text = store.goalRequestText(PROJECT_A, s.goalPrepFor(PROJECT_A));
  assert.match(text, /tối đa 3 lượt và 30 phút/);
  assert.match(text, /test đạt/);
});

test('P5 goal prep keeps its task/RUN binding across a load round-trip', () => {
  const adapter = memoryAdapter();
  const s = createStore(adapter);
  const saved = s.setGoalPrep(PROJECT_A, { criteria: 'chuẩn bị X', maxTurns: 4, maxMinutes: 45, taskId: 'task-42', runId: 'run-99' });
  assert.equal(saved.taskId, 'task-42');
  assert.equal(saved.runId, 'run-99');
  const reopened = createStore(adapter);
  const prep = reopened.goalPrepFor(PROJECT_A);
  assert.equal(prep.taskId, 'task-42');
  assert.equal(prep.runId, 'run-99');
  // A prep saved with no panel RUN stays explicitly unbound — never an
  // invented binding — and survives the round-trip the same way.
  s.setGoalPrep(PROJECT_B, { criteria: 'chuẩn bị Y', maxTurns: 2, maxMinutes: 15 });
  const unbound = createStore(adapter).goalPrepFor(PROJECT_B);
  assert.equal(unbound.taskId, '');
  assert.equal(unbound.runId, '');
});

test('F24 schedules become due by interval and record runs', () => {
  const s = freshStore();
  const recipe = s.upsertRecipe({ name: 'Test', command: 'npm test', cwd: PROJECT_A });
  const schedule = s.upsertSchedule({ name: 'Test hằng ngày', recipeId: recipe.id, intervalHours: 24 });
  const day = 24 * 3600 * 1000;
  assert.equal(s.dueSchedules(schedule.createdAt + day + 1).length, 1);
  s.markScheduleRun(schedule.id, schedule.createdAt + day + 1);
  assert.equal(s.dueSchedules(schedule.createdAt + day + 2).length, 0);
  assert.throws(() => s.upsertSchedule({ name: 'X', recipeId: 'missing' }), /lệnh đã lưu/);
});

test('F32 notes and F34 skills are per project', () => {
  const s = freshStore();
  s.upsertNote(PROJECT_A, { title: 'Quy ước', body: 'Dùng npm test', pinned: true });
  assert.equal(s.listNotes(PROJECT_A).length, 1);
  assert.equal(s.listNotes(PROJECT_B).length, 0);
  const skill = s.upsertSkill({ name: 'Review', content: 'Các bước review' });
  assert.equal(s.skillsForProject(PROJECT_A).length, 0);
  s.setSkillForProject(skill.id, PROJECT_A, true);
  assert.equal(s.skillsForProject(PROJECT_A).length, 1);
});

test('F39 chats and F40 ssh targets are stored with validation', () => {
  const s = freshStore();
  s.upsertChat(PROJECT_A, { label: 'Chat sửa lỗi', url: 'https://example.com/chat' });
  assert.equal(s.listChats(PROJECT_A)[0].label, 'Chat sửa lỗi');
  const target = s.upsertSshTarget({ name: 'svhome', host: '100.116.112.22', user: 'svhome', remoteDir: '~/Codex-web' });
  assert.deepEqual(store.sshArgs(target, 'git status'), ['-p', '22', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'svhome@100.116.112.22', 'cd ~/Codex-web && git status']);
  const pkg = store.contextContentText(PROJECT_A, [{ path: 'a.js', size: 3, content: 'x=1', truncated: true, hash: 'abc' }]);
  assert.match(pkg, /đã bị cắt/);
});

test('A8 regression: taskRunId uses the canonical orchestration path first', () => {
  assert.equal(storeApi.taskRunId({ orchestration: { run_id: 'run-A' }, run_id: 'run-other' }), 'run-A');
  assert.equal(storeApi.taskRunId({ run_id: 'run-B' }), 'run-B');
  assert.equal(storeApi.taskRunId({}), '');
  assert.equal(storeApi.taskRunId(null), '');
});

test('A8 regression: capsuleView normalizes the recorded capsule shape', () => {
  const view = storeApi.capsuleView({
    capsule_id: 'cap-1', run_id: 'run-A', version: 3, status: 'recorded', created_at: '2026-10-22T09:00:00Z', sha256: 'abc123',
    payload: { panel_summary: 'Đã sửa xong module X', runtime: { objective: 'Sửa module X', base_head: 'deadbeefcafe', task_status: 'completed' } },
  });
  assert.equal(view.runId, 'run-A');
  assert.equal(view.objective, 'Sửa module X');
  assert.equal(view.panelSummary, 'Đã sửa xong module X');
  assert.equal(view.baseHead, 'deadbeefcafe');
  assert.equal(view.taskStatus, 'completed');
  assert.equal(storeApi.capsuleView(null), null);
});

test('A8 regression: headMatches compares prefixes and refuses weak evidence', () => {
  assert.equal(storeApi.headMatches('deadbeefcafe1234', 'deadbeefcafe1234'), true);
  assert.equal(storeApi.headMatches('deadbeefcafe1234', 'deadbeef'), true);
  assert.equal(storeApi.headMatches('deadbeefcafe1234', '0123456789abcdef'), false);
  assert.equal(storeApi.headMatches('', 'deadbeef'), null);
  assert.equal(storeApi.headMatches('deadbeef', ''), null);
  assert.equal(storeApi.headMatches('abc', 'abc'), null);
});

test('P2 canonical key: legacy buckets stay readable, writes land on the canonical key, migration moves the rest', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wh-store-p2-'));
  const link = `${dir}-link`;
  fs.symlinkSync(dir, link);
  try {
    const adapter = memoryAdapter();
    const store = createStore(adapter);
    // Legacy writes (no resolver yet): keyed by the raw spelling.
    store.setPin(link, { pinned: true, alias: 'Dự án' });
    store.saveDraft(link, 'nháp cũ');
    store.upsertNote(link, { title: 'Ghi chú cũ', body: 'nội dung' });
    store.upsertChat(link, { label: 'Chat cũ', url: 'https://example.invalid/x' });
    const legacyKey = storeApi.workspaceKeyOf(link);
    const canonicalKey = storeApi.workspaceKeyOf(dir);
    assert.notEqual(legacyKey, canonicalKey);
    assert.equal(adapter.dump().pins[legacyKey].alias, 'Dự án');
    // Resolver on: the same workspace addressed by its raw spelling reads
    // the legacy bucket, and a write moves it to the canonical key.
    store.setCanonicalKeyResolver((workspace) => storeApi.workspaceKeyOf(workspace) === legacyKey ? dir : null);
    assert.equal(store.pinOf(link).alias, 'Dự án');
    assert.equal(store.getDraft(link).text, 'nháp cũ');
    store.setPin(link, { alias: 'Dự án mới' });
    const dumped = adapter.dump();
    assert.equal(dumped.pins[canonicalKey].alias, 'Dự án mới');
    assert.equal(dumped.pins[legacyKey], undefined);
    // Migration moves the remaining legacy buckets; a bucket already
    // present under the canonical key is left untouched (canonical wins).
    const moved = store.migrateWorkspaceKey(legacyKey, canonicalKey);
    assert.ok(moved.includes('drafts'));
    assert.ok(moved.includes('notes'));
    assert.ok(moved.includes('chats'));
    assert.ok(!moved.includes('pins'));
    assert.equal(store.listNotes(link).length, 1);
    assert.equal(store.listChats(link).length, 1);
    assert.equal(store.getDraft(link).text, 'nháp cũ');
    // No-op and empty-key guards never report a phantom move.
    assert.deepEqual(store.migrateWorkspaceKey(legacyKey, canonicalKey), []);
    assert.deepEqual(store.migrateWorkspaceKey('', canonicalKey), []);
  } finally {
    fs.rmSync(link, { force: true });
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('P2 canonical key: recipes pinned by either spelling of the project match', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wh-store-p2-recipes-'));
  const link = `${dir}-link`;
  fs.symlinkSync(dir, link);
  try {
    const store = createStore(memoryAdapter());
    const legacyKey = storeApi.workspaceKeyOf(link);
    store.setCanonicalKeyResolver((workspace) => storeApi.workspaceKeyOf(workspace) === legacyKey ? dir : null);
    store.upsertRecipe({ name: 'Lệnh legacy', command: 'echo a', cwd: link });
    store.upsertRecipe({ name: 'Lệnh canonical', command: 'echo b', cwd: dir });
    store.upsertRecipe({ name: 'Lệnh dùng chung', command: 'echo c', cwd: '' });
    store.upsertRecipe({ name: 'Lệnh hàng xóm', command: 'echo d', cwd: `${dir}-sibling` });
    assert.deepEqual(store.listRecipes(link).map((r) => r.name), ['Lệnh legacy', 'Lệnh canonical', 'Lệnh dùng chung']);
  } finally {
    fs.rmSync(link, { force: true });
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
