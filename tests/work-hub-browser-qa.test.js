const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const { createBrowserQa, validateUrl } = require('../electron/services/workHubBrowserQa');

function fakeWindow({ html = '<html><head><title>App</title></head><body>Hello QA</body></html>', failLoad = false } = {}) {
  const wc = new EventEmitter();
  wc.session = { webRequest: { onErrorOccurred: (fn) => { wc._networkHandler = fn; } } };
  wc.loadURL = async (url) => {
    wc.url = url;
    wc.emit('console-message', 2, 'Some error from page');
    wc.emit('console-message', 0, 'info log');
    if (wc._networkHandler) wc._networkHandler({ url: 'http://x/dead.png', error: 'net::ERR_FAILED' });
    if (failLoad) throw new Error('ERR_CONNECTION_REFUSED');
  };
  wc.executeJavaScript = async (code) => (code.includes('document.title') ? 'App' : html);
  wc.capturePage = async () => ({ toPNG: () => Buffer.from('PNGDATA') });
  wc.getURL = () => wc.url;
  return {
    webContents: wc,
    destroyed: false,
    destroy() { this.destroyed = true; },
  };
}

function fixtureRoot(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-qa-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

test('validateUrl only allows http/https without embedded credentials', () => {
  assert.equal(validateUrl('http://localhost:5173/app'), 'http://localhost:5173/app');
  assert.throws(() => validateUrl('file:///etc/passwd'), /http\/https/);
  assert.throws(() => validateUrl('https://user:pass@example.com'), /đăng nhập/);
  assert.throws(() => validateUrl('not a url'), /không hợp lệ/);
});

test('capture records identity, console, network, DOM, screenshot and verdict', async (t) => {
  const root = fixtureRoot(t);
  let win;
  const qa = createBrowserQa({ createWindow: () => { win = fakeWindow(); return win; } });
  const record = await qa.capture(root, { url: 'http://localhost:5173', expectedText: 'Hello QA', jobId: 'job-9' });
  assert.equal(record.status, 'loaded');
  assert.equal(record.title, 'App');
  assert.equal(record.consoleErrors, 1);
  assert.equal(record.networkErrors.length, 1);
  assert.equal(record.verdict.pass, true);
  assert.equal(record.jobId, 'job-9');
  assert.ok(record.screenshot.sha256.length === 64);
  assert.ok(fs.existsSync(path.join(root, record.screenshot.path)));
  assert.equal(win.destroyed, true, 'window must be destroyed after capture');
  const listed = qa.listCaptures(root);
  assert.equal(listed.length, 1);
  assert.equal(listed[0].id, record.id);
});

test('a failing expectation is reported as not passed, not hidden', async (t) => {
  const root = fixtureRoot(t);
  const qa = createBrowserQa({ createWindow: () => fakeWindow() });
  const record = await qa.capture(root, { url: 'http://localhost:5173', expectedText: 'Missing text' });
  assert.equal(record.verdict.found, false);
  assert.equal(record.verdict.pass, false);
});

test('a load failure is recorded with its error and no fabricated DOM', async (t) => {
  const root = fixtureRoot(t);
  const qa = createBrowserQa({ createWindow: () => fakeWindow({ failLoad: true }) });
  const record = await qa.capture(root, { url: 'http://localhost:9' });
  assert.equal(record.status, 'failed');
  assert.match(record.loadError, /ERR_CONNECTION_REFUSED/);
  assert.equal(record.domChars, 0);
  assert.equal(record.screenshot, null);
});
