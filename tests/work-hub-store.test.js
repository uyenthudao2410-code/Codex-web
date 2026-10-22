'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  normalizeText, fillTemplate, createStore, buildRequest,
  handoffPreview, formatHandoffText, searchAll, TASK_TYPES,
} = require('../renderer/work-hub-store');

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
