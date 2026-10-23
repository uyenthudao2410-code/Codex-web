'use strict';
/*
 * Chat On Steroids (CoS) companion adapter — W1 read-only pilot.
 *
 * Thin client for the CoS Local Control API (contract verified in W0, see
 * docs/research/261023_COS_WEBCODEX_W0_AUDIT.md and the wire contract in the
 * CoS source at src/shared/control-api.ts, protocol 1):
 *
 *   - The listener is HTTP on 127.0.0.1 with an EPHEMERAL port. Discovery is
 *     through files in the CoS userData folder, never a hardcoded port:
 *       <userData>/control-api/endpoint.json  { protocol, port, pid, ... }
 *       <userData>/control-api/token         Bearer token, rotated per launch
 *   - The token is read here, in the Electron main process only. It is never
 *     returned from any method, never logged and never written to disk by
 *     this adapter. Responses are additionally scrubbed against the token
 *     before they leave this module (defense in depth).
 *   - Read-only by construction: this module issues GET requests only. It
 *     has no code path that can POST, and it never enables CoS actions —
 *     ACTIONS_AUTHORIZED is only *reported* when CoS itself says
 *     `actions.enabled === true` in /v1/health.
 *
 * Identity rule (plan §4.2): CoS conversationId / sessionId are kept verbatim
 * and every projected session/event is labeled observation: 'OBSERVED'. The
 * adapter never infers a Codex-web run_id / job_id / proof, and never writes
 * to the EOCL ledger.
 *
 * Connection states (plan §4.3):
 *   DISCONNECTED          flag off, CoS not running, or never connected
 *   CONNECTED_READ_ONLY   health OK, CoS actions off
 *   ACTIONS_AUTHORIZED    health OK and CoS itself reports actions enabled
 *   STALE                 was connected, the latest request failed
 *   UNKNOWN               the peer answered but its data cannot be trusted
 *                         (protocol mismatch, malformed payload)
 *
 * Every public method resolves with a result object and never throws:
 *   { ok: true,  state, data }
 *   { ok: false, state, error: { code, message } }
 * so a dead or misbehaving CoS can never take the main process down with it.
 */
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const CONTROL_API_PROTOCOL = 1;
const DEFAULT_TIMEOUT_MS = 5000;
const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
const MAX_TEXT_CHARS = 20000;

const CONNECTION_STATES = Object.freeze({
  DISCONNECTED: 'DISCONNECTED',
  CONNECTED_READ_ONLY: 'CONNECTED_READ_ONLY',
  ACTIONS_AUTHORIZED: 'ACTIONS_AUTHORIZED',
  STALE: 'STALE',
  UNKNOWN: 'UNKNOWN',
});

class CosCompanionError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'CosCompanionError';
    this.code = code;
  }
}

/**
 * Locate the CoS userData folder. Order: explicit setting, environment
 * override (COS_USERDATA_DIR, also used by tests), then the standard
 * Electron userData location for the CoS app (productName
 * "Chat On Steroids", electron-builder appId com.chatonsteroids.app).
 */
function defaultCosUserDataDir({ env = process.env, platform = process.platform, homedir = os.homedir() } = {}) {
  if (platform === 'win32') {
    const appData = String(env.APPDATA || '').trim() || path.win32.join(homedir, 'AppData', 'Roaming');
    return path.win32.join(appData, 'Chat On Steroids');
  }
  if (platform === 'darwin') {
    return path.join(homedir, 'Library', 'Application Support', 'Chat On Steroids');
  }
  const configHome = String(env.XDG_CONFIG_HOME || '').trim() || path.join(homedir, '.config');
  return path.join(configHome, 'Chat On Steroids');
}

function resolveCosUserDataDir(options = {}) {
  const settingDir = String(options.settingDir || '').trim();
  if (settingDir) return settingDir;
  const env = options.env || process.env;
  const envDir = String(env.COS_USERDATA_DIR || env.COS_COMPANION_USERDATA_DIR || '').trim();
  if (envDir) return envDir;
  return defaultCosUserDataDir({ env, platform: options.platform, homedir: options.homedir });
}

function cutText(value, limit = MAX_TEXT_CHARS) {
  const text = String(value ?? '');
  return text.length > limit ? text.slice(0, limit) : text;
}

/** Keep the CoS identity verbatim; the only added fact is the OBSERVED label. */
function projectSession(session) {
  if (!session || typeof session !== 'object') return null;
  return {
    sessionId: String(session.id || ''),
    conversationId: session.conversationId != null ? String(session.conversationId) : null,
    projectId: session.projectId != null ? String(session.projectId) : null,
    title: cutText(session.title || '', 300),
    startedAt: Number.isFinite(session.startedAt) ? session.startedAt : null,
    updatedAt: Number.isFinite(session.updatedAt) ? session.updatedAt : null,
    endedAt: Number.isFinite(session.endedAt) ? session.endedAt : null,
    events: Number.isFinite(session.events) ? session.events : null,
    userMessages: Number.isFinite(session.userMessages) ? session.userMessages : null,
    toolCalls: Number.isFinite(session.toolCalls) ? session.toolCalls : null,
    model: session.model != null ? String(session.model) : null,
    lastTurnOutcome: session.lastTurnOutcome != null ? String(session.lastTurnOutcome) : null,
    observation: 'OBSERVED',
  };
}

function projectEvent(event) {
  if (!event || typeof event !== 'object') return null;
  const projected = {
    seq: Number.isFinite(event.seq) ? event.seq : null,
    position: Number.isFinite(event.position) ? event.position : null,
    time: Number.isFinite(event.time) ? event.time : null,
    kind: String(event.kind || ''),
    source: String(event.source || ''),
    observation: 'OBSERVED',
  };
  if (event.unreadable === true) projected.unreadable = true;
  if (event.message && typeof event.message === 'object') {
    projected.text = cutText(event.message.text || '');
    projected.textChars = Number.isFinite(event.message.chars) ? event.message.chars : null;
    projected.textTruncated = event.message.truncated === true;
  }
  if (typeof event.detail === 'string') projected.detail = cutText(event.detail, 2000);
  if (typeof event.outcome === 'string') projected.outcome = event.outcome;
  if (event.tool && typeof event.tool === 'object') {
    projected.toolName = String(event.tool.name || '');
    projected.toolOutcome = String(event.tool.outcome || '');
  }
  return projected;
}

/** Replace any occurrence of the token inside a value about to leave main. */
function scrubToken(value, token) {
  if (!token) return value;
  if (typeof value === 'string') return value.includes(token) ? value.split(token).join('[redacted]') : value;
  if (Array.isArray(value)) return value.map((item) => scrubToken(item, token));
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, item] of Object.entries(value)) out[key] = scrubToken(item, token);
    return out;
  }
  return value;
}

class CosCompanionAdapter {
  constructor(options = {}) {
    this.enabled = options.enabled !== undefined ? Boolean(options.enabled) : false;
    this.userDataDir = options.userDataDir ? String(options.userDataDir) : resolveCosUserDataDir(options);
    this.timeoutMs = Number.isFinite(options.timeoutMs) && options.timeoutMs > 0
      ? Number(options.timeoutMs)
      : DEFAULT_TIMEOUT_MS;
    this.state = CONNECTION_STATES.DISCONNECTED;
    this.lastOkAt = null;
    this.lastError = null;
    this.health = null;
  }

  configure({ enabled, userDataDir } = {}) {
    if (enabled !== undefined) this.enabled = Boolean(enabled);
    if (userDataDir !== undefined && String(userDataDir) !== this.userDataDir) {
      this.userDataDir = String(userDataDir);
      this.state = CONNECTION_STATES.DISCONNECTED;
      this.lastOkAt = null;
      this.lastError = null;
      this.health = null;
    }
    if (!this.enabled) this.state = CONNECTION_STATES.DISCONNECTED;
    return this;
  }

  getConnectionView() {
    return {
      enabled: this.enabled,
      state: this.enabled ? this.state : CONNECTION_STATES.DISCONNECTED,
      protocol: this.health ? this.health.protocol : null,
      appVersion: this.health ? this.health.appVersion : null,
      actionsAuthorized: this.state === CONNECTION_STATES.ACTIONS_AUTHORIZED,
      lastOkAt: this.lastOkAt,
      lastError: this.lastError,
      workersReadable: false,
      workersNote: 'Worker CoS không đọc được ở chế độ read-only (W0 sai lệch S1: GET /v1/workers bị khóa sau allowActions). Work Hub chỉ hiển thị worker EOCL.',
    };
  }

  _fail(error) {
    const code = error instanceof CosCompanionError ? error.code : 'COS_UNEXPECTED';
    const message = error instanceof Error ? error.message : String(error);
    this.lastError = { code, message, at: new Date().toISOString() };
    if (code === 'COS_PROTOCOL_MISMATCH' || code === 'COS_MALFORMED') {
      this.state = CONNECTION_STATES.UNKNOWN;
    } else if (!this.enabled || code === 'COS_DISABLED' || code === 'COS_NOT_RUNNING' || code === 'COS_ENDPOINT_INVALID') {
      this.state = this.lastOkAt ? CONNECTION_STATES.STALE : CONNECTION_STATES.DISCONNECTED;
      if (code === 'COS_NOT_RUNNING' || code === 'COS_ENDPOINT_INVALID') this.state = CONNECTION_STATES.DISCONNECTED;
    } else {
      this.state = this.lastOkAt ? CONNECTION_STATES.STALE : CONNECTION_STATES.DISCONNECTED;
    }
    return { ok: false, state: this.getConnectionView().state, error: { code, message } };
  }

  _succeed(data) {
    const actionsEnabled = this.health ? this.health.actionsEnabled === true : false;
    this.state = actionsEnabled
      ? CONNECTION_STATES.ACTIONS_AUTHORIZED
      : CONNECTION_STATES.CONNECTED_READ_ONLY;
    this.lastOkAt = new Date().toISOString();
    this.lastError = null;
    return { ok: true, state: this.state, data };
  }

  _discovery() {
    const dir = path.join(this.userDataDir, 'control-api');
    let endpointRaw;
    try {
      endpointRaw = fs.readFileSync(path.join(dir, 'endpoint.json'), 'utf8');
    } catch {
      throw new CosCompanionError('COS_NOT_RUNNING', 'Không tìm thấy endpoint.json của CoS — CoS chưa chạy hoặc Local Control API chưa bật.');
    }
    let endpoint;
    try { endpoint = JSON.parse(endpointRaw); } catch {
      throw new CosCompanionError('COS_MALFORMED', 'endpoint.json của CoS không phải JSON hợp lệ.');
    }
    if (!endpoint || typeof endpoint !== 'object'
      || !Number.isInteger(endpoint.port) || endpoint.port < 1 || endpoint.port > 65535) {
      throw new CosCompanionError('COS_ENDPOINT_INVALID', 'endpoint.json của CoS thiếu cổng hợp lệ.');
    }
    if (endpoint.protocol !== CONTROL_API_PROTOCOL) {
      throw new CosCompanionError(
        'COS_PROTOCOL_MISMATCH',
        `CoS Control API protocol ${String(endpoint.protocol)} không khớp protocol ${CONTROL_API_PROTOCOL} mà adapter hỗ trợ.`
      );
    }
    let token;
    try {
      token = fs.readFileSync(path.join(dir, 'token'), 'utf8').trim();
    } catch {
      throw new CosCompanionError('COS_NOT_RUNNING', 'Không đọc được token của CoS Control API trong thư mục userData.');
    }
    if (!token) throw new CosCompanionError('COS_AUTH', 'Token CoS Control API trống.');
    return { port: endpoint.port, token, endpoint };
  }

  /** One GET against the loopback listener. The token never leaves this scope except as the Authorization header. */
  _request(route) {
    return new Promise((resolve, reject) => {
      let discovery;
      try { discovery = this._discovery(); } catch (error) { reject(error); return; }
      const { port, token } = discovery;
      const request = http.request({
        host: '127.0.0.1',
        port,
        path: route,
        method: 'GET',
        headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
      }, (response) => {
        const chunks = [];
        let size = 0;
        response.on('data', (chunk) => {
          size += chunk.length;
          if (size > MAX_RESPONSE_BYTES) {
            request.destroy(new CosCompanionError('COS_MALFORMED', 'Phản hồi CoS vượt quá kích thước cho phép.'));
            return;
          }
          chunks.push(chunk);
        });
        response.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          const status = response.statusCode || 0;
          if (status === 401 || status === 403) {
            reject(new CosCompanionError('COS_AUTH', `CoS Control API từ chối xác thực (HTTP ${status}). Token có thể đã xoay sau khi CoS khởi động lại.`));
            return;
          }
          if (status === 429) {
            reject(new CosCompanionError('COS_RATE_LIMITED', 'CoS Control API báo rate_limited — tôn trọng giới hạn của server, thử lại sau.'));
            return;
          }
          if (status < 200 || status >= 300) {
            let serverError = '';
            try { serverError = String(JSON.parse(text)?.error || ''); } catch { serverError = ''; }
            reject(new CosCompanionError('COS_HTTP_ERROR', `CoS Control API trả HTTP ${status}${serverError ? ` (${serverError})` : ''}.`));
            return;
          }
          let body;
          try { body = JSON.parse(text); } catch {
            reject(new CosCompanionError('COS_MALFORMED', 'CoS Control API trả phản hồi không phải JSON hợp lệ.'));
            return;
          }
          resolve(scrubToken(body, token));
        });
        response.on('error', () => reject(new CosCompanionError('COS_UNREACHABLE', 'Kết nối tới CoS Control API bị đứt giữa chừng.')));
      });
      request.setTimeout(this.timeoutMs, () => {
        request.destroy(new CosCompanionError('COS_TIMEOUT', `CoS Control API không trả lời trong ${this.timeoutMs}ms.`));
      });
      request.on('error', (error) => {
        if (error instanceof CosCompanionError) { reject(error); return; }
        reject(new CosCompanionError('COS_UNREACHABLE', 'Không kết nối được tới CoS Control API trên 127.0.0.1 — CoS có thể đã tắt.'));
      });
      request.end();
    });
  }

  async _get(route) {
    if (!this.enabled) {
      return { failure: this._fail(new CosCompanionError('COS_DISABLED', 'Tích hợp CoS companion đang tắt (cosCompanionEnabled=false).')) };
    }
    try {
      const body = await this._request(route);
      return { body };
    } catch (error) {
      return { failure: this._fail(error) };
    }
  }

  /** Health is answered by CoS without asking any owner; it also carries the actions switch state. */
  async probe() {
    const { body, failure } = await this._get('/v1/health');
    if (failure) return failure;
    if (!body || typeof body !== 'object' || body.ok !== true || !Number.isFinite(body.protocol)) {
      return this._fail(new CosCompanionError('COS_MALFORMED', 'Phản hồi /v1/health của CoS thiếu trường bắt buộc.'));
    }
    if (body.protocol !== CONTROL_API_PROTOCOL) {
      return this._fail(new CosCompanionError(
        'COS_PROTOCOL_MISMATCH',
        `CoS Control API protocol ${String(body.protocol)} không khớp protocol ${CONTROL_API_PROTOCOL} mà adapter hỗ trợ.`
      ));
    }
    this.health = {
      protocol: body.protocol,
      appVersion: body.appVersion != null ? String(body.appVersion) : null,
      pid: Number.isFinite(body.pid) ? body.pid : null,
      startedAt: body.startedAt != null ? String(body.startedAt) : null,
      uptimeSeconds: Number.isFinite(body.uptimeSeconds) ? body.uptimeSeconds : null,
      actionsEnabled: body.actions?.enabled === true,
    };
    return this._succeed({ health: this.health, connection: this.getConnectionView() });
  }

  async getHealth() {
    return this.probe();
  }

  async getStatus() {
    const health = await this.probe();
    if (!health.ok) return health;
    const { body, failure } = await this._get('/v1/status');
    if (failure) return failure;
    if (!body || typeof body !== 'object' || !body.connection || typeof body.connection !== 'object') {
      return this._fail(new CosCompanionError('COS_MALFORMED', 'Phản hồi /v1/status của CoS thiếu khối connection.'));
    }
    return this._succeed({
      appVersion: body.appVersion != null ? String(body.appVersion) : null,
      connectionState: body.connection.state != null ? String(body.connection.state) : null,
      connectionDetail: cutText(body.connection.detail || '', 500),
      bridgeRunning: body.bridge?.running === true,
      bridgePaired: body.bridge?.paired === true,
      toolCallsRunning: Number.isFinite(body.toolCalls?.running) ? body.toolCalls.running : null,
    });
  }

  async listSessions(options = {}) {
    const health = await this.probe();
    if (!health.ok) return health;
    const limit = Math.max(1, Math.min(50, Number(options.limit) || 20));
    const params = new URLSearchParams({ limit: String(limit) });
    if (options.cursor) params.set('cursor', String(options.cursor));
    const { body, failure } = await this._get(`/v1/sessions?${params.toString()}`);
    if (failure) return failure;
    if (!body || typeof body !== 'object' || !Array.isArray(body.sessions)) {
      return this._fail(new CosCompanionError('COS_MALFORMED', 'Phản hồi /v1/sessions của CoS thiếu danh sách phiên.'));
    }
    return this._succeed({
      sessions: body.sessions.map(projectSession).filter(Boolean),
      total: Number.isFinite(body.total) ? body.total : body.sessions.length,
      nextCursor: body.nextCursor != null ? String(body.nextCursor) : null,
      activeId: body.activeId != null ? String(body.activeId) : null,
      observedAt: new Date().toISOString(),
    });
  }

  async getSession(sessionId, options = {}) {
    const id = String(sessionId || '').trim();
    if (!id) return this._fail(new CosCompanionError('COS_BAD_REQUEST', 'Thiếu sessionId của CoS.'));
    const health = await this.probe();
    if (!health.ok) return health;
    const suffix = options.live ? '?live=1' : '';
    const { body, failure } = await this._get(`/v1/sessions/${encodeURIComponent(id)}${suffix}`);
    if (failure) return failure;
    if (!body || typeof body !== 'object' || !body.session || typeof body.session !== 'object') {
      return this._fail(new CosCompanionError('COS_MALFORMED', 'Phản hồi chi tiết phiên của CoS thiếu khối session.'));
    }
    const data = { session: projectSession(body.session), observedAt: new Date().toISOString() };
    if (body.live && typeof body.live === 'object') {
      data.live = {
        activeTurnId: body.live.activeTurnId != null ? String(body.live.activeTurnId) : null,
        automation: body.live.automation != null ? String(body.live.automation) : null,
        blocked: body.live.blocked != null ? String(body.live.blocked) : '',
      };
    } else if (options.live) {
      data.live = null;
    }
    return this._succeed(data);
  }

  async getSessionEvents(sessionId, options = {}) {
    const id = String(sessionId || '').trim();
    if (!id) return this._fail(new CosCompanionError('COS_BAD_REQUEST', 'Thiếu sessionId của CoS.'));
    const health = await this.probe();
    if (!health.ok) return health;
    const params = new URLSearchParams();
    const from = Number(options.from);
    if (Number.isFinite(from) && from >= 0) params.set('from', String(Math.floor(from)));
    params.set('limit', String(Math.max(1, Math.min(200, Number(options.limit) || 50))));
    if (Array.isArray(options.kinds) && options.kinds.length) {
      params.set('kinds', options.kinds.map((kind) => String(kind)).join(','));
    }
    const query = params.toString();
    const { body, failure } = await this._get(`/v1/sessions/${encodeURIComponent(id)}/events${query ? `?${query}` : ''}`);
    if (failure) return failure;
    if (!body || typeof body !== 'object' || !Array.isArray(body.events)) {
      return this._fail(new CosCompanionError('COS_MALFORMED', 'Phản hồi events của CoS thiếu danh sách sự kiện.'));
    }
    return this._succeed({
      sessionId: id,
      events: body.events.map(projectEvent).filter(Boolean),
      total: Number.isFinite(body.total) ? body.total : body.events.length,
      nextFrom: Number.isFinite(body.nextFrom) ? body.nextFrom : null,
      observedAt: new Date().toISOString(),
    });
  }
}

function createCosCompanionAdapter(options) {
  return new CosCompanionAdapter(options);
}

module.exports = {
  CosCompanionAdapter,
  CosCompanionError,
  CONNECTION_STATES,
  CONTROL_API_PROTOCOL,
  createCosCompanionAdapter,
  defaultCosUserDataDir,
  resolveCosUserDataDir,
  projectSession,
  projectEvent,
};
