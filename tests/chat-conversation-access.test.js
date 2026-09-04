const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const {
  CONVERSATION_ACCESS_FILTER,
  isConversationApiRequest,
  conversationPathKey,
  classifyConversationAccess,
  accessDeniedMessage,
  createConversationAccessTracker,
  ensureConversationAccessMonitor,
  releaseConversationAccessMonitor
} = require('../electron/services/chatConversationAccess');

test('conversation access verdict uses only URL and numeric status', () => {
  const denied = 'https://chatgpt.com/backend-api/conversation/abc123-def456';
  assert.equal(classifyConversationAccess(denied, 403), 'denied');
  assert.equal(classifyConversationAccess(denied, 401), 'denied');
  assert.equal(classifyConversationAccess('https://www.chatgpt.com/backend-api/conversation/abc123', 403), 'denied');
  assert.equal(classifyConversationAccess('https://chatgpt.com/backend-api/conversation', 403), 'denied');
  assert.equal(classifyConversationAccess(denied, 200), 'recovered');
  assert.equal(classifyConversationAccess(denied, 500), null);
  assert.equal(classifyConversationAccess(denied, 0), null);
  assert.equal(classifyConversationAccess(denied, Number.NaN), null);
  assert.equal(classifyConversationAccess('https://chatgpt.com/backend-api/conversations', 403), null);
  assert.equal(classifyConversationAccess('https://chatgpt.com/api/conversation/abc', 403), null);
  assert.equal(classifyConversationAccess('https://evil.com/backend-api/conversation/abc', 403), null);
  assert.equal(classifyConversationAccess('http://chatgpt.com/backend-api/conversation/abc', 403), null);
  assert.equal(classifyConversationAccess('not a url', 403), null);
  assert.equal(classifyConversationAccess('', 403), null);
  assert.ok(Array.isArray(CONVERSATION_ACCESS_FILTER) && CONVERSATION_ACCESS_FILTER.length === 2);
  assert.ok(isConversationApiRequest(denied));
  assert.equal(isConversationApiRequest('https://chatgpt.com/c/abc123'), false);
  assert.equal(conversationPathKey(denied), '/backend-api/conversation/abc123-def456');
  assert.equal(conversationPathKey('not a url'), null);
});

test('denied copy never embeds the request URL or conversation identity', () => {
  for (const status of [401, 403, 500, undefined]) {
    const message = accessDeniedMessage(status);
    assert.match(message, /ChatGPT từ chối truy cập conversation/);
    assert.match(message, /Đăng nhập lại/);
    assert.doesNotMatch(message, /abc123|conversation\/|https?:\/\//);
  }
  assert.match(accessDeniedMessage(401), /HTTP 401/);
  assert.match(accessDeniedMessage(403), /HTTP 403/);
});

test('recovery clears only the exact denied target, never a sibling endpoint', () => {
  const tracker = createConversationAccessTracker();
  const abc = 'https://chatgpt.com/backend-api/conversation/conversation-ABC';
  const xyz = 'https://chatgpt.com/backend-api/conversation/conversation-XYZ';
  const list = 'https://chatgpt.com/backend-api/conversations?limit=20';

  const first = tracker.observe(abc, 403);
  assert.deepEqual({ changed: first.changed, denied: first.denied }, { changed: true, denied: true });
  assert.match(first.message, /HTTP 403/);
  assert.equal(JSON.stringify(first).includes('conversation-ABC'), false, 'tracker results must not carry raw identity');

  const repeat = tracker.observe(abc, 403);
  assert.deepEqual(repeat, { changed: false, denied: true, message: null });

  const listOk = tracker.observe(list, 200);
  assert.deepEqual(listOk, { changed: false, denied: true, message: null }, 'list endpoint must not clear a conversation denial');

  const siblingOk = tracker.observe(xyz, 200);
  assert.deepEqual(siblingOk, { changed: false, denied: true, message: null }, 'sibling conversation must not clear the denial');

  const targetOk = tracker.observe(abc, 200);
  assert.deepEqual(targetOk, { changed: true, denied: false, message: null }, 'only the denied target recovers');

  assert.deepEqual(tracker.snapshot(), { denied: false });
  assert.equal(JSON.stringify(tracker.snapshot()).includes('conversation-'), false);
});

test('tracker reset drops a stale denial without logging identity', () => {
  const tracker = createConversationAccessTracker();
  tracker.observe('https://chatgpt.com/backend-api/conversation/conversation-ABC', 403);
  assert.equal(tracker.snapshot().denied, true);
  assert.equal(tracker.reset(), true);
  assert.deepEqual(tracker.snapshot(), { denied: false });
  assert.equal(tracker.reset(), false);
  assert.deepEqual(
    tracker.observe('https://chatgpt.com/backend-api/conversation/conversation-ABC', 500),
    { changed: false, denied: false, message: null }
  );
});

function fakeSession() {
  const calls = [];
  return {
    calls,
    webRequest: {
      onCompleted: (filter, listener) => {
        calls.push([filter, listener]);
      }
    }
  };
}

test('session dispatcher attaches once and always routes to the live subscriber', () => {
  const chatSession = fakeSession();
  const seen1 = [];
  const seen2 = [];
  assert.equal(ensureConversationAccessMonitor(chatSession, (url, status) => seen1.push([url, status])), true);
  assert.equal(ensureConversationAccessMonitor(chatSession, (url, status) => seen2.push([url, status])), true);
  assert.equal(chatSession.calls.length, 1, 'Electron honors only the last webRequest listener; attach exactly once');
  assert.deepEqual(chatSession.calls[0][0], { urls: CONVERSATION_ACCESS_FILTER });
  const [, listener] = chatSession.calls[0];
  listener({ url: 'https://chatgpt.com/backend-api/conversation/AAA', statusCode: 403 });
  assert.deepEqual(seen1, []);
  assert.deepEqual(seen2, [[ 'https://chatgpt.com/backend-api/conversation/AAA', 403 ]]);
  assert.equal(releaseConversationAccessMonitor(chatSession, () => {}), true, 'releasing a foreign subscriber is a no-op success');
  listener({ url: 'https://chatgpt.com/backend-api/conversation/AAA', statusCode: 200 });
  assert.equal(seen2.length, 2, 'foreign release must not detach the live subscriber');
  const live = (url, status) => seen1.push(['live', url, status]);
  assert.equal(releaseConversationAccessMonitor(chatSession, seen2.push), true);
  assert.equal(ensureConversationAccessMonitor(chatSession, live), true);
  listener({ url: 'https://chatgpt.com/backend-api/conversation/AAA', statusCode: 200 });
  assert.deepEqual(seen1[seen1.length - 1], ['live', 'https://chatgpt.com/backend-api/conversation/AAA', 200]);
  assert.equal(ensureConversationAccessMonitor(null, live), false);
  assert.equal(ensureConversationAccessMonitor(chatSession, null), false);
  assert.equal(releaseConversationAccessMonitor(null, live), false);
});

test('chat controller routes access signals through the tracker and resets on navigation', () => {
  const controller = read('electron/chatViewController.js');
  assert.match(controller, /chatConversationAccess/);
  assert.match(controller, /createConversationAccessTracker/);
  assert.match(controller, /ensureConversationAccessMonitor/);
  assert.match(controller, /releaseConversationAccessMonitor/);
  assert.match(controller, /observeConversationAccess\(url, statusCode\)/);
  assert.match(controller, /resetConversationAccess\(\)/);
  assert.match(controller, /conversationAccessTracker/);
  assert.match(controller, /conversationAccessSubscriber/);
  assert.match(controller, /conversation-access-denied/);
  assert.match(controller, /conversationAccessDenied/);
  assert.doesNotMatch(controller, /__mcpConversationAccessBound/);
  const observeStart = controller.indexOf('  observeConversationAccess(url, statusCode) {');
  assert.ok(observeStart >= 0, 'observe handler must remain discoverable');
  const observeBlock = controller.slice(observeStart, observeStart + 1400);
  assert.match(observeBlock, /conversationAccessTracker\.observe\(url, statusCode\)/);
  assert.match(observeBlock, /result\.changed !== true/);
  assert.match(observeBlock, /this\.emitState\(\)/);
  assert.match(observeBlock, /endpoint: 'backend-api\/conversation'/);
  const warnStart = observeBlock.indexOf("this.log.warn('ChatGPT từ chối");
  assert.ok(warnStart >= 0, 'denied branch must log a sanitized warn');
  const warnBlock = observeBlock.slice(warnStart, warnStart + 400);
  assert.doesNotMatch(warnBlock, /details(\?\.|\.)url|url,/, 'request URLs carry conversation IDs and must not be logged');
  assert.doesNotMatch(observeBlock, /innerText|textContent|responseBody|getResponseBody/);
  const navigateBlock = controller.slice(controller.indexOf("contents.on('did-navigate'"), controller.indexOf("contents.on('did-navigate'") + 700);
  assert.match(navigateBlock, /resetConversationAccess/);
  const inPageBlock = controller.slice(controller.indexOf("contents.on('did-navigate-in-page'"), controller.indexOf("contents.on('did-navigate-in-page'") + 700);
  assert.match(inPageBlock, /resetConversationAccess/);
  assert.match(controller, /releaseConversationAccessMonitor\(session\.fromPartition/);
  const helper = read('electron/services/chatConversationAccess.js');
  assert.doesNotMatch(helper, /innerText|textContent|responseBody|getResponseBody|cookies|localStorage/);
});

test('exactly one webRequest completed listener exists across the Electron layer', () => {
  const controller = read('electron/chatViewController.js');
  const helper = read('electron/services/chatConversationAccess.js');
  assert.equal((helper.match(/webRequest\.onCompleted\(\{/g) || []).length, 1, 'the dispatcher helper owns the single registration site');
  assert.equal((controller.match(/webRequest\.onCompleted\(\{/g) || []).length, 0, 'callers route through the dispatcher, never attach directly');
});

test('main chat window exposes session reset next to the toolbar controls', () => {
  const preload = read('electron/browserPreload.js');
  assert.match(preload, /clearChatSession: \(\) => ipcRenderer\.invoke\('chat:clear-session'\)/);
  const html = read('renderer/browser.html');
  assert.match(html, /id="resetSessionButton"/);
  assert.match(html, /Đăng nhập lại/);
  const browser = read('renderer/browser.js');
  assert.match(browser, /\$\('#resetSessionButton'\)\.onclick/);
  assert.match(browser, /window\.confirm\(/);
  assert.match(browser, /api\.clearChatSession\(\)/);
  assert.match(browser, /\$\('#switchState'\)\.textContent/);
  const main = read('electron/main.js');
  assert.match(main, /secureHandle\('chat:clear-session'/);
});
