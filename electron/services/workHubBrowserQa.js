'use strict';
/*
 * Work Hub browser QA (parity M3.1). Captures one page in an offscreen
 * Electron window: page identity (final URL + title), console messages,
 * failed network requests, a bounded DOM snapshot, a PNG screenshot
 * (with sha256) and an optional expected-text verdict. Records land in
 * .coding-tools/browser-qa/ and can be linked to a Job id.
 *
 * The window factory is injected so the capture logic is testable
 * without a real display. M3.2 (Windows Computer Use) is a separate
 * adapter and intentionally NOT part of this service.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const MAX_DOM_CHARS = 200 * 1024;
const MAX_CONSOLE = 100;
const MAX_NETWORK = 50;

function validateUrl(raw) {
  const text = String(raw || '').trim();
  let url;
  try { url = new URL(text); } catch { throw new Error('URL không hợp lệ.'); }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new Error('Chỉ hỗ trợ http/https cho Browser QA.');
  }
  if (url.username || url.password) throw new Error('URL không được chứa thông tin đăng nhập.');
  return url.toString();
}

function qaDir(root) {
  return path.join(root, '.coding-tools', 'browser-qa');
}

function readIndex(root) {
  try {
    const parsed = JSON.parse(fs.readFileSync(path.join(qaDir(root), 'index.json'), 'utf8'));
    return Array.isArray(parsed.records) ? parsed.records : [];
  } catch {
    return [];
  }
}

function listCaptures(root, limit = 20) {
  return readIndex(root).slice(-Math.max(1, Math.min(100, limit))).reverse();
}

const MAX_ELEMENTS = 50;
const ELEMENT_PATTERN = /<(a|button|input|select|textarea|label|h[1-6])\b([^>]*)>([^<]{0,120})?/gi;

function attrValue(attrs, name) {
  const match = String(attrs || '').match(new RegExp(`\\b${name}\\s*=\\s*"([^"]*)"`, 'i'))
    || String(attrs || '').match(new RegExp(`\\b${name}\\s*=\\s*'([^']*)'`, 'i'));
  return match ? match[1].slice(0, 120) : '';
}

/*
 * Element references for a captured page (W5 — WebCodex §8 browser
 * identity port). A ref is only meaningful for the exact (session,
 * generation) it was issued in: any later navigation or reload in the
 * session bumps the generation and makes older refs stale.
 */
function extractElements(dom, sessionId, generation) {
  const elements = [];
  const text = String(dom || '');
  ELEMENT_PATTERN.lastIndex = 0;
  let match;
  while ((match = ELEMENT_PATTERN.exec(text)) !== null && elements.length < MAX_ELEMENTS) {
    const ordinal = elements.length;
    elements.push({
      ref: { sessionId, generation, ordinal },
      tag: match[1].toLowerCase(),
      id: attrValue(match[2], 'id'),
      name: attrValue(match[2], 'name'),
      text: String(match[3] || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    });
  }
  return elements;
}

function createBrowserQa(overrides = {}) {
  const createWindow = overrides.createWindow;
  if (typeof createWindow !== 'function') throw new Error('Browser QA cần một window factory.');
  const sessions = new Map();

  function sessionView(session) {
    return {
      id: session.id,
      generation: session.generation,
      captures: session.captures,
      lastUrl: session.lastUrl,
      createdAt: session.createdAt,
    };
  }

  function openSession() {
    const session = {
      id: `qa-session-${crypto.randomBytes(6).toString('hex')}`,
      generation: 0,
      captures: 0,
      lastUrl: '',
      createdAt: new Date().toISOString(),
      currentElements: [],
    };
    sessions.set(session.id, session);
    return sessionView(session);
  }

  function getSession(sessionId) {
    return sessions.get(String(sessionId || '')) || null;
  }

  function closeSession(sessionId) {
    return sessions.delete(String(sessionId || ''));
  }

  function listSessions() {
    return [...sessions.values()].map(sessionView);
  }

  /*
   * Resolve an element ref against the live session. A ref is rejected
   * as stale when its generation is not the session's current one (the
   * page navigated or reloaded since the ref was issued) — acting on a
   * stale ref could click the wrong element on the new page.
   */
  function resolveElementRef(sessionId, ref) {
    const session = getSession(sessionId);
    if (!session || !ref || ref.sessionId !== session.id) {
      return { ok: false, code: 'BROWSER_SESSION_NOT_FOUND' };
    }
    if (Number(ref.generation) !== session.generation) {
      return { ok: false, code: 'BROWSER_ELEMENT_STALE', currentGeneration: session.generation };
    }
    const element = session.currentElements.find((item) => item.ref.ordinal === Number(ref.ordinal));
    if (!element) return { ok: false, code: 'BROWSER_ELEMENT_NOT_FOUND' };
    return { ok: true, element };
  }

  async function capture(root, payload, session = null) {
    const url = validateUrl(payload?.url);
    const expectedText = String(payload?.expectedText || '').slice(0, 500);
    const jobId = String(payload?.jobId || '').slice(0, 120) || null;
    const timeoutMs = Math.max(5000, Math.min(60000, Number(payload?.timeoutMs) || 20000));
    const id = `qa-${crypto.randomBytes(6).toString('hex')}`;
    const at = new Date().toISOString();
    const consoleMessages = [];
    const networkErrors = [];
    const win = createWindow();
    const wc = win.webContents;
    wc.on('console-message', (...args) => {
      // Electron delivers (event, level, message, line, sourceId); older
      // shapes pass a single details object. Normalize both.
      let level = 0;
      let message = '';
      if (args.length >= 3 && typeof args[1] === 'number') {
        level = args[1]; message = args[2];
      } else if (args.length >= 2 && typeof args[0] === 'number') {
        level = args[0]; message = args[1];
      } else if (args[0] && typeof args[0] === 'object') {
        level = Number(args[0].level) || 0; message = args[0].message;
      }
      if (consoleMessages.length < MAX_CONSOLE) {
        consoleMessages.push({ level, message: String(message || '').slice(0, 500) });
      }
    });
    try {
      wc.session?.webRequest?.onErrorOccurred?.((details) => {
        if (networkErrors.length < MAX_NETWORK) {
          networkErrors.push({ url: String(details.url || '').slice(0, 500), error: String(details.error || '') });
        }
      });
    } catch { /* network capture is best-effort */ }

    let status = 'loaded';
    let loadError = '';
    try {
      await Promise.race([
        wc.loadURL(url),
        new Promise((_, reject) => {
          const timer = setTimeout(() => reject(new Error('QA_LOAD_TIMEOUT')), timeoutMs);
          timer.unref?.();
        }),
      ]);
    } catch (error) {
      status = 'failed';
      loadError = String(error?.message || error).slice(0, 300);
    }

    let title = '';
    let finalUrl = url;
    let dom = '';
    let screenshot = null;
    if (status === 'loaded') {
      try { title = String(await wc.executeJavaScript('document.title', true) || ''); } catch { /* keep empty */ }
      try { finalUrl = String(wc.getURL() || url); } catch { /* keep input url */ }
      try {
        dom = String(await wc.executeJavaScript('document.documentElement ? document.documentElement.outerHTML : ""', true) || '');
      } catch { /* DOM unavailable (e.g. PDF) */ }
      try {
        const image = await wc.capturePage();
        const png = image.toPNG();
        const dir = qaDir(root);
        fs.mkdirSync(dir, { recursive: true });
        const file = path.join(dir, `${id}.png`);
        fs.writeFileSync(file, png);
        screenshot = {
          path: path.relative(root, file).split(path.sep).join('/'),
          sha256: crypto.createHash('sha256').update(png).digest('hex'),
          bytes: png.length,
        };
      } catch { /* screenshot is best-effort evidence */ }
    }

    const verdict = expectedText
      ? { expectedText, found: dom.includes(expectedText), pass: dom.includes(expectedText) }
      : null;
    let elements = [];
    if (session) {
      elements = status === 'loaded' ? extractElements(dom, session.id, session.generation) : [];
      session.currentElements = elements;
      session.lastUrl = finalUrl;
    }
    const record = {
      id, at, url, finalUrl, title: title.slice(0, 300), status, loadError,
      sessionId: session ? session.id : null,
      generation: session ? session.generation : null,
      elements,
      console: consoleMessages,
      consoleErrors: consoleMessages.filter((m) => m.level === 2 || m.level === 3 || m.level === 'error').length,
      networkErrors,
      domChars: dom.length,
      domExcerpt: dom.slice(0, 2000),
      screenshot, verdict, jobId,
    };
    try {
      const dir = qaDir(root);
      fs.mkdirSync(dir, { recursive: true });
      const records = readIndex(root);
      records.push({ ...record, domExcerpt: undefined });
      fs.writeFileSync(path.join(dir, 'index.json'), JSON.stringify({ version: 1, records: records.slice(-100) }, null, 2));
      fs.writeFileSync(path.join(dir, `${id}.json`), JSON.stringify(record, null, 2));
    } catch { /* the live result still returns even if persistence fails */ }
    try { win.destroy(); } catch { /* already gone */ }
    return record;
  }

  /*
   * Capture as a navigation inside an existing session: every call bumps
   * the session generation, which is what invalidates element refs from
   * earlier pages in the same session.
   */
  async function captureInSession(root, payload) {
    const session = getSession(payload?.sessionId);
    if (!session) throw new Error('Phiên Browser QA không tồn tại.');
    session.generation += 1;
    session.captures += 1;
    return capture(root, payload, session);
  }

  return {
    capture, captureInSession, listCaptures, list: listCaptures,
    openSession, getSession: (id) => { const s = getSession(id); return s ? sessionView(s) : null; },
    closeSession, listSessions, resolveElementRef,
  };
}

module.exports = { createBrowserQa, validateUrl, listCaptures, extractElements };
