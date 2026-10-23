'use strict';
/*
 * W1 CoS companion adapter tests.
 *
 * A real HTTP server on loopback plays the CoS Local Control API exactly as
 * the W0-verified contract describes it (protocol 1, Bearer token from a
 * token file, discovery through endpoint.json, allowlist projections).
 * The adapter under test reads endpoint.json + token from a temp "CoS
 * userData" folder, the same way it will read the real CoS folder on
 * Windows in W0.2. No Electron, no real CoS, no network beyond loopback.
 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const {
  CosCompanionAdapter,
  resolveCosUserDataDir,
} = require('../electron/services/cosCompanionAdapter');
const { normalize } = require('../electron/services/config');

const TOKEN = 'test-token-0123456789abcdef-SECRET-do-not-leak';

const SESSION = {
  id: 'sess-1',
  title: 'Phiên kiểm thử W1',
  conversationId: 'conv-abc-123',
  projectId: null,
  startedAt: 1792800000000,
  updatedAt: 1792803600000,
  endedAt: null,
  events: 2,
  userMessages: 1,
  toolCalls: 0,
  lastToolCallAt: null,
  lastAssistantFinalAt: 1792803500000,
  lastTurnEndAt: 1792803500000,
  activityExpiresAt: null,
  errors: 0,
  toolRejected: 0,
  toolInternalErrors: 0,
  processExitNonzero: 0,
  estimatedTokens: 42,
  contextTokens: 42,
  lastTurnOutcome: 'completed',
  activeTurnId: null,
  model: 'gpt-test',
  agents: [],
  origin: null,
};

function healthBody(overrides = {}) {
  return {
    ok: true,
    protocol: 1,
    routes: ['/v1/health', '/v1/status', '/v1/sessions'],
    actions: { enabled: false, routes: ['POST /v1/inputs'] },
    pid: 4242,
    appVersion: '2.1.45',
    startedAt: '2026-10-23T11:00:00.000Z',
    uptimeSeconds: 60,
    ...overrides,
  };
}

function statusBody() {
  return {
    appVersion: '2.1.45',
    connection: {
      state: 'connected',
      detail: 'bridge paired',
      handshakeAt: 1792800000000,
      lastRequestAt: 1792800000000,
      lastToolCallAt: null,
      tunnel: null,
      surfaces: [],
    },
    bridge: { running: true, port: 8765, portOverridden: false, paired: true, present: true, lastSeenAt: 1792800000000, extensionVersion: '2.1.45', error: null },
    plugins: [],
    update: { current: '2.1.45', latest: null, stage: 'idle', error: null, checkedAt: null },
    toolCalls: { running: 0, settling: 0, inFlight: 0, inFlightMcpRequests: 0 },
  };
}

/**
 * Start a fake CoS listener. Behavior knobs let each test break the contract
 * in one specific way (wrong expected token, protocol drift, malformed JSON).
 */
async function startFakeCos(t, behavior = {}) {
  const expectedToken = behavior.expectedToken || TOKEN;
  const server = http.createServer((req, res) => {
    const reply = (status, body, raw = false) => {
      const text = raw ? String(body) : JSON.stringify(body);
      res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
      res.end(text);
    };
    if (req.headers.authorization !== `Bearer ${expectedToken}`) {
      reply(401, { error: 'unauthorized' });
      return;
    }
    const url = new URL(req.url, 'http://127.0.0.1');
    if (url.pathname === '/v1/health') {
      if (behavior.malformedHealth) { reply(200, 'this is {not json', true); return; }
      reply(200, healthBody(behavior.healthOverrides || {}));
      return;
    }
    if (url.pathname === '/v1/status') { reply(200, statusBody()); return; }
    if (url.pathname === '/v1/sessions') {
      reply(200, { sessions: [{ ...SESSION, pressure: { level: 'ok', advisory: 0, limit: 100 } }], total: 1, nextCursor: null, activeId: 'sess-1' });
      return;
    }
    if (url.pathname === '/v1/sessions/sess-1') { reply(200, { session: SESSION }); return; }
    if (url.pathname === '/v1/sessions/sess-1/events') {
      reply(200, {
        events: [
          { seq: 1, position: 1, time: 1792800001000, kind: 'user_message', source: 'user', messageId: 'm1', message: { text: 'Xin chào CoS', chars: 12, truncated: false } },
          { seq: 2, position: 2, time: 1792800002000, kind: 'assistant_message', source: 'assistant', final: true, message: { text: 'Chào bạn', chars: 8, truncated: false } },
        ],
        total: 2,
        nextFrom: 3,
      });
      return;
    }
    reply(404, { error: 'not_found' });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const { port } = server.address();

  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cos-companion-test-'));
  t.after(() => fs.rmSync(userDataDir, { recursive: true, force: true }));
  const apiDir = path.join(userDataDir, 'control-api');
  fs.mkdirSync(apiDir, { recursive: true });
  fs.writeFileSync(path.join(apiDir, 'endpoint.json'), JSON.stringify({
    protocol: behavior.endpointProtocol !== undefined ? behavior.endpointProtocol : 1,
    port,
    pid: 4242,
    appVersion: '2.1.45',
    startedAt: '2026-10-23T11:00:00.000Z',
  }));
  fs.writeFileSync(path.join(apiDir, 'token'), `${behavior.tokenFile !== undefined ? behavior.tokenFile : TOKEN}\n`);
  return { server, port, userDataDir };
}

function makeAdapter(userDataDir, overrides = {}) {
  return new CosCompanionAdapter({ enabled: true, userDataDir, timeoutMs: 2000, ...overrides });
}

function assertNoTokenLeak(value, label) {
  const serialized = JSON.stringify(value) || '';
  assert.ok(!serialized.includes(TOKEN), `${label} must not contain the CoS token`);
}

test('happy path: discovery, health, status, sessions and events stay OBSERVED', async (t) => {
  const { userDataDir } = await startFakeCos(t);
  const adapter = makeAdapter(userDataDir);

  const status = await adapter.getStatus();
  assert.equal(status.ok, true);
  assert.equal(status.state, 'CONNECTED_READ_ONLY');
  assert.equal(status.data.connectionState, 'connected');
  assertNoTokenLeak(status, 'status result');

  const sessions = await adapter.listSessions();
  assert.equal(sessions.ok, true);
  assert.equal(sessions.data.sessions.length, 1);
  const session = sessions.data.sessions[0];
  assert.equal(session.sessionId, 'sess-1');
  assert.equal(session.conversationId, 'conv-abc-123');
  assert.equal(session.observation, 'OBSERVED');
  assert.equal('runId' in session, false);
  assert.equal('jobId' in session, false);
  assertNoTokenLeak(sessions, 'sessions result');

  const events = await adapter.getSessionEvents('sess-1');
  assert.equal(events.ok, true);
  assert.equal(events.data.events.length, 2);
  assert.equal(events.data.events[0].text, 'Xin chào CoS');
  assert.equal(events.data.events[0].observation, 'OBSERVED');
  assert.equal(events.data.nextFrom, 3);
  assertNoTokenLeak(events, 'events result');

  const view = adapter.getConnectionView();
  assert.equal(view.state, 'CONNECTED_READ_ONLY');
  assert.equal(view.actionsAuthorized, false);
  assert.equal(view.workersReadable, false);
  assertNoTokenLeak(view, 'connection view');
});

test('(a) wrong token in the token file -> COS_AUTH, clear error, no token in the result', async (t) => {
  const { userDataDir } = await startFakeCos(t, { tokenFile: 'wrong-token-value' });
  const adapter = makeAdapter(userDataDir);
  const result = await adapter.listSessions();
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'COS_AUTH');
  assertNoTokenLeak(result, 'auth failure result');
  assert.ok(!JSON.stringify(result).includes('wrong-token-value'), 'even the wrong token must not leak');
});

test('(b) protocol mismatch in endpoint.json -> refused before any request', async (t) => {
  const { userDataDir } = await startFakeCos(t, { endpointProtocol: 2 });
  const adapter = makeAdapter(userDataDir);
  const result = await adapter.probe();
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'COS_PROTOCOL_MISMATCH');
  assert.equal(result.state, 'UNKNOWN');
});

test('(b2) protocol mismatch reported by /v1/health -> refused', async (t) => {
  const { userDataDir } = await startFakeCos(t, { healthOverrides: { protocol: 99 } });
  const adapter = makeAdapter(userDataDir);
  const result = await adapter.probe();
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'COS_PROTOCOL_MISMATCH');
  assert.equal(result.state, 'UNKNOWN');
});

test('(c) server dies mid-flight -> STALE, then calls keep failing soft without crashing', async (t) => {
  const { server, userDataDir } = await startFakeCos(t);
  const adapter = makeAdapter(userDataDir);
  const first = await adapter.listSessions();
  assert.equal(first.ok, true);
  assert.equal(first.state, 'CONNECTED_READ_ONLY');

  await new Promise((resolve) => server.close(resolve));

  const second = await adapter.listSessions();
  assert.equal(second.ok, false);
  assert.equal(second.state, 'STALE');
  assert.equal(second.error.code, 'COS_UNREACHABLE');

  const third = await adapter.getStatus();
  assert.equal(third.ok, false);
  assert.equal(third.state, 'STALE');
});

test('(c2) CoS never started (no endpoint.json) -> DISCONNECTED, not an exception', async (t) => {
  const emptyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cos-companion-empty-'));
  t.after(() => fs.rmSync(emptyDir, { recursive: true, force: true }));
  const adapter = makeAdapter(emptyDir);
  const result = await adapter.probe();
  assert.equal(result.ok, false);
  assert.equal(result.state, 'DISCONNECTED');
  assert.equal(result.error.code, 'COS_NOT_RUNNING');
});

test('(d) malformed JSON from the server -> controlled UNKNOWN error', async (t) => {
  const { userDataDir } = await startFakeCos(t, { malformedHealth: true });
  const adapter = makeAdapter(userDataDir);
  const result = await adapter.probe();
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'COS_MALFORMED');
  assert.equal(result.state, 'UNKNOWN');
});

test('(e) token never appears in any object the adapter returns', async (t) => {
  const { userDataDir } = await startFakeCos(t);
  const adapter = makeAdapter(userDataDir);
  const results = [
    await adapter.probe(),
    await adapter.getStatus(),
    await adapter.listSessions(),
    await adapter.getSession('sess-1'),
    await adapter.getSessionEvents('sess-1'),
    adapter.getConnectionView(),
  ];
  for (const [index, result] of results.entries()) assertNoTokenLeak(result, `result #${index}`);
});

test('(f) flag off -> adapter never connects and reports COS_DISABLED', async (t) => {
  const { userDataDir } = await startFakeCos(t);
  const adapter = makeAdapter(userDataDir, { enabled: false });
  const result = await adapter.listSessions();
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'COS_DISABLED');
  assert.equal(result.state, 'DISCONNECTED');
  assert.equal(adapter.getConnectionView().state, 'DISCONNECTED');

  adapter.configure({ enabled: true });
  const after = await adapter.listSessions();
  assert.equal(after.ok, true);
});

test('ACTIONS_AUTHORIZED is reported only when CoS itself enables actions', async (t) => {
  const { userDataDir } = await startFakeCos(t, {
    healthOverrides: { actions: { enabled: true, routes: ['POST /v1/inputs'] } },
  });
  const adapter = makeAdapter(userDataDir);
  const probe = await adapter.probe();
  assert.equal(probe.ok, true);
  assert.equal(probe.state, 'ACTIONS_AUTHORIZED');
  assert.equal(probe.data.health.actionsEnabled, true);
  // The adapter stays read-only even then: it exposes no write method at all.
  assert.equal(typeof adapter.sendInput, 'undefined');
  assert.equal(typeof adapter.postInput, 'undefined');
});

test('settings: cosCompanion flags default off and normalize keeps them', () => {
  const fresh = normalize({});
  assert.equal(fresh.cosCompanionEnabled, false);
  assert.equal(fresh.cosCompanionUserDataDir, '');
  const on = normalize({ cosCompanionEnabled: true, cosCompanionUserDataDir: '  D:/CoS/userData  ' });
  assert.equal(on.cosCompanionEnabled, true);
  assert.equal(on.cosCompanionUserDataDir, 'D:/CoS/userData');
});

test('userData discovery: setting wins, then COS_USERDATA_DIR, then the platform default', () => {
  assert.equal(
    resolveCosUserDataDir({ settingDir: 'X:/custom', env: { COS_USERDATA_DIR: 'Y:/env' } }),
    'X:/custom'
  );
  assert.equal(
    resolveCosUserDataDir({ settingDir: '', env: { COS_USERDATA_DIR: 'Y:/env' } }),
    'Y:/env'
  );
  const win = resolveCosUserDataDir({ env: { APPDATA: 'C:/Users/Test/AppData/Roaming' }, platform: 'win32', homedir: 'C:/Users/Test' });
  assert.ok(win.replace(/\\/g, '/').endsWith('AppData/Roaming/Chat On Steroids'), win);
});
