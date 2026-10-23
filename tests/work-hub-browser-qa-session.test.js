'use strict';
/* W5 — Browser QA session identity + element generation contract:
 * element refs carry (sessionId, generation) and go stale on navigation. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const { createBrowserQa, extractElements } = require('../electron/services/workHubBrowserQa');

const PAGE_ONE = '<html><head><title>One</title></head><body>'
  + '<button id="save-btn">Save now</button><a href="/next" id="go">Go next</a>'
  + '<input name="q" type="text"></body></html>';
const PAGE_TWO = '<html><head><title>Two</title></head><body>'
  + '<button id="delete-btn">Delete</button></body></html>';

function fakeWindow(html) {
  const wc = new EventEmitter();
  wc.session = { webRequest: { onErrorOccurred: () => {} } };
  wc.loadURL = async (url) => { wc.url = url; };
  wc.executeJavaScript = async (code) => (code.includes('document.title') ? 'T' : html);
  wc.capturePage = async () => ({ toPNG: () => Buffer.from('PNGDATA') });
  wc.getURL = () => wc.url;
  return { webContents: wc, destroy() {} };
}

function fixtureRoot(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-qa-session-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

test('extractElements issues refs bound to session + generation', () => {
  const elements = extractElements(PAGE_ONE, 'sess-x', 3);
  assert.equal(elements.length, 3);
  assert.deepEqual(elements[0].ref, { sessionId: 'sess-x', generation: 3, ordinal: 0 });
  assert.equal(elements[0].id, 'save-btn');
  assert.equal(elements[0].text, 'Save now');
  assert.equal(elements[2].name, 'q');
});

test('session captures bump generation and stale refs are rejected', async (t) => {
  const root = fixtureRoot(t);
  const pages = [PAGE_ONE, PAGE_TWO];
  const qa = createBrowserQa({ createWindow: () => fakeWindow(pages.shift()) });

  const session = qa.openSession();
  assert.equal(session.generation, 0);

  const first = await qa.captureInSession(root, { sessionId: session.id, url: 'http://localhost/one' });
  assert.equal(first.sessionId, session.id);
  assert.equal(first.generation, 1);
  const saveRef = first.elements.find((e) => e.id === 'save-btn').ref;
  const resolved = qa.resolveElementRef(session.id, saveRef);
  assert.equal(resolved.ok, true);
  assert.equal(resolved.element.id, 'save-btn');

  // Navigation: a new capture in the same session bumps the generation.
  const second = await qa.captureInSession(root, { sessionId: session.id, url: 'http://localhost/two' });
  assert.equal(second.generation, 2);

  const stale = qa.resolveElementRef(session.id, saveRef);
  assert.equal(stale.ok, false);
  assert.equal(stale.code, 'BROWSER_ELEMENT_STALE');
  assert.equal(stale.currentGeneration, 2);

  const freshRef = second.elements.find((e) => e.id === 'delete-btn').ref;
  assert.equal(qa.resolveElementRef(session.id, freshRef).ok, true);

  // Refs from another session never resolve here.
  const foreign = qa.resolveElementRef(session.id, { sessionId: 'qa-session-nope', generation: 2, ordinal: 0 });
  assert.equal(foreign.ok, false);
  assert.equal(foreign.code, 'BROWSER_SESSION_NOT_FOUND');

  assert.equal(qa.listSessions().length, 1);
  assert.equal(qa.closeSession(session.id), true);
  await assert.rejects(() => qa.captureInSession(root, { sessionId: session.id, url: 'http://localhost/x' }), /không tồn tại/);
});

test('plain capture stays session-less and backward compatible', async (t) => {
  const root = fixtureRoot(t);
  const qa = createBrowserQa({ createWindow: () => fakeWindow(PAGE_ONE) });
  const record = await qa.capture(root, { url: 'http://localhost/one' });
  assert.equal(record.sessionId, null);
  assert.equal(record.generation, null);
  assert.deepEqual(record.elements, []);
  assert.equal(record.status, 'loaded');
});
