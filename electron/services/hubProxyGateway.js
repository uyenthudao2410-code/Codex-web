const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const { hubProxyDescriptorFile } = require('../paths');
const { writeJsonAtomic } = require('./jsonStore');

const MAX_REQUEST_BYTES = 1024 * 1024;
const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
const MAX_TELEMETRY_REQUEST_BYTES = 16 * 1024;
const DEFAULT_PROXY_IDENTITY = Object.freeze({
  clientId: 'codex-desktop',
  clientType: 'codex_desktop',
  clientName: 'codex-desktop-proxy'
});
const ALLOWED_PROXY_IDENTITIES = new Map([
  ['codex-desktop|codex_desktop', DEFAULT_PROXY_IDENTITY],
  ['opencode|opencode', Object.freeze({ clientId: 'opencode', clientType: 'opencode', clientName: 'opencode-proxy' })]
]);

function sameToken(left, right) {
  const a = Buffer.from(String(left || ''), 'utf8');
  const b = Buffer.from(String(right || ''), 'utf8');
  return a.length > 0 && a.length === b.length && crypto.timingSafeEqual(a, b);
}

function proxyIdentityFromHeaders(headers = {}) {
  const clientId = String(headers['x-coding-tools-proxy-client-id'] || '').trim();
  const clientType = String(headers['x-coding-tools-proxy-client-type'] || '').trim();
  if (!clientId && !clientType) return DEFAULT_PROXY_IDENTITY;
  if (!clientId || !clientType) return null;
  return ALLOWED_PROXY_IDENTITIES.get(`${clientId}|${clientType}`) || null;
}

function normalizeProviderTelemetry(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const allowed = new Set([
    'schema_version', 'event_type', 'session_id', 'message_id', 'provider_id', 'model_id', 'status',
    'started_at_ms', 'completed_at_ms', 'duration_ms', 'finish', 'error_name', 'provider_cost',
    'input_tokens', 'output_tokens', 'reasoning_output_tokens', 'cache_read_tokens', 'cache_write_tokens',
    'provider_dispatch_id', 'provider_delegation_id'
  ]);
  if (Object.keys(value).some((key) => !allowed.has(key))) return null;
  if (value.schema_version !== 1 || value.event_type !== 'message.updated') return null;
  const boundedText = (name, max, required = false) => {
    const text = String(value[name] ?? '').trim();
    if ((required && !text) || text.length > max || /[\u0000-\u001f]/.test(text)) return null;
    return text;
  };
  const numeric = (name, { integer = false, required = false } = {}) => {
    if (value[name] === undefined || value[name] === null) return required ? null : undefined;
    const number = value[name];
    if (typeof number !== 'number' || !Number.isFinite(number) || number < 0 || (integer && !Number.isInteger(number))) return null;
    return number;
  };
  const sessionId = boundedText('session_id', 256, true);
  const messageId = boundedText('message_id', 256, true);
  const providerId = boundedText('provider_id', 160, true);
  const modelId = boundedText('model_id', 200, true);
  const status = boundedText('status', 32, true);
  if (!sessionId || !messageId || !providerId || !modelId || !['active', 'completed', 'failed'].includes(status)) return null;
  const result = { schema_version: 1, event_type: 'message.updated', session_id: sessionId, message_id: messageId, provider_id: providerId, model_id: modelId, status };
  for (const name of ['started_at_ms', 'provider_cost']) {
    const number = numeric(name, { required: true });
    if (number === null) return null;
    result[name] = number;
  }
  for (const name of ['input_tokens', 'output_tokens', 'reasoning_output_tokens', 'cache_read_tokens', 'cache_write_tokens']) {
    const number = numeric(name, { integer: true, required: true });
    if (number === null) return null;
    result[name] = number;
  }
  for (const name of ['completed_at_ms', 'duration_ms']) {
    const number = numeric(name);
    if (number === null) return null;
    if (number !== undefined) result[name] = number;
  }
  for (const [name, max] of [['provider_dispatch_id', 256], ['provider_delegation_id', 256], ['finish', 100], ['error_name', 120]]) {
    const text = boundedText(name, max);
    if (text === null) return null;
    if (text) result[name] = text;
  }
  return result;
}

class HubProxyGateway {
  constructor({ settings, secrets, log, descriptorPath = hubProxyDescriptorFile() }) {
    this.settings = settings;
    this.secrets = secrets;
    this.log = log;
    this.descriptorPath = descriptorPath;
    this.server = null;
    this.token = '';
    this.port = 0;
  }

  async start() {
    if (this.server) return this.descriptor();
    this.token = crypto.randomBytes(32).toString('base64url');
    this.server = http.createServer((request, response) => this.handle(request, response));
    await new Promise((resolve, reject) => {
      const fail = (error) => { this.server = null; reject(error); };
      this.server.once('error', fail);
      this.server.listen(0, '127.0.0.1', () => {
        this.server.removeListener('error', fail);
        resolve();
      });
    });
    const address = this.server.address();
    this.port = Number(address && typeof address === 'object' ? address.port : 0);
    const descriptor = this.descriptor();
    writeJsonAtomic(this.descriptorPath, descriptor);
    try { fs.chmodSync(this.descriptorPath, 0o600); } catch { /* best effort on Windows */ }
    this.log?.info?.('Execution Hub local proxy gateway đã sẵn sàng', { port: this.port });
    return descriptor;
  }

  descriptor() {
    return {
      version: 1,
      host: '127.0.0.1',
      port: this.port,
      token: this.token,
      electron_pid: process.pid,
      created_at: new Date().toISOString()
    };
  }

  async stop() {
    const server = this.server;
    this.server = null;
    this.token = '';
    this.port = 0;
    try { fs.rmSync(this.descriptorPath, { force: true }); } catch { /* best effort */ }
    if (!server) return false;
    await new Promise((resolve) => server.close(() => resolve()));
    return true;
  }

  reject(response, status, message) {
    const body = JSON.stringify({ error: message });
    response.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  }

  handle(request, response) {
    const isHeartbeat = request.url === '/__hub_proxy/heartbeat';
    const isTelemetry = request.url === '/__hub_proxy/telemetry';
    if (request.method !== 'POST' || (request.url !== '/mcp' && !isHeartbeat && !isTelemetry)) {
      this.reject(response, 404, 'Not found');
      return;
    }
    const authorization = String(request.headers.authorization || '');
    const supplied = authorization.startsWith('Bearer ') ? authorization.slice(7) : '';
    if (!sameToken(supplied, this.token)) {
      this.reject(response, 401, 'Unauthorized');
      return;
    }
    const proxyIdentity = proxyIdentityFromHeaders(request.headers);
    if (!proxyIdentity) {
      this.reject(response, 403, 'Proxy client identity is not allowlisted');
      return;
    }
    if (isTelemetry && (proxyIdentity.clientId !== 'opencode' || proxyIdentity.clientType !== 'opencode')) {
      this.reject(response, 403, 'Provider telemetry requires the OpenCode proxy identity');
      return;
    }
    const declaredLength = Number(request.headers['content-length'] || 0);
    const requestLimit = isTelemetry ? MAX_TELEMETRY_REQUEST_BYTES : MAX_REQUEST_BYTES;
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > requestLimit) {
      this.reject(response, 413, 'Request too large');
      return;
    }
    const chunks = [];
    let total = 0;
    let finished = false;
    const failOnce = (status, message) => {
      if (finished) return;
      finished = true;
      this.reject(response, status, message);
    };
    request.on('data', (chunk) => {
      total += chunk.length;
      if (total > requestLimit) {
        request.destroy();
        failOnce(413, 'Request too large');
        return;
      }
      chunks.push(chunk);
    });
    request.on('error', () => failOnce(400, 'Invalid proxy request'));
    request.on('end', () => {
      if (finished) return;
      let normalizedTelemetry = null;
      if (isTelemetry) {
        try { normalizedTelemetry = normalizeProviderTelemetry(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { normalizedTelemetry = null; }
        if (!normalizedTelemetry) {
          failOnce(400, 'Invalid provider telemetry payload');
          return;
        }
      }
      const settings = this.settings.load();
      const mcpToken = this.secrets.get('mcpAuthToken');
      if (!mcpToken || !Number.isInteger(Number(settings.mcpPort))) {
        failOnce(503, 'Coding Tools MCP is not available');
        return;
      }
      const body = isHeartbeat
        ? Buffer.from(JSON.stringify({
          action: 'heartbeat',
          client_id: proxyIdentity.clientId,
          client_type: proxyIdentity.clientType,
          client_name: proxyIdentity.clientName
        }))
        : isTelemetry
          ? Buffer.from(JSON.stringify({
            action: 'provider_telemetry',
            client_id: proxyIdentity.clientId,
            client_type: proxyIdentity.clientType,
            client_name: proxyIdentity.clientName,
            telemetry: normalizedTelemetry
          }))
        : Buffer.concat(chunks);
      const forwardedHeaders = {
        Authorization: `Bearer ${mcpToken}`,
        'Content-Type': 'application/json',
        'Content-Length': body.length
      };
      if (!isHeartbeat) {
        forwardedHeaders['X-Coding-Tools-Client-Id'] = proxyIdentity.clientId;
        forwardedHeaders['X-Coding-Tools-Client-Type'] = proxyIdentity.clientType;
        for (const name of ['mcp-protocol-version', 'mcp-method', 'mcp-name', 'mcp-session-id', 'accept']) {
          if (request.headers[name]) forwardedHeaders[name] = request.headers[name];
        }
      }
      const upstream = http.request({
        host: '127.0.0.1',
        port: Number(settings.mcpPort),
        path: (isHeartbeat || isTelemetry) ? '/__control/hub' : '/mcp',
        method: 'POST',
        headers: forwardedHeaders,
        timeout: 30000
      }, (upstreamResponse) => {
        const responseChunks = [];
        let responseBytes = 0;
        upstreamResponse.on('data', (chunk) => {
          responseBytes += chunk.length;
          if (responseBytes <= MAX_RESPONSE_BYTES) responseChunks.push(chunk);
        });
        upstreamResponse.on('end', () => {
          if (finished) return;
          finished = true;
          if (responseBytes > MAX_RESPONSE_BYTES) {
            this.reject(response, 502, 'Upstream MCP response exceeded proxy limit');
            return;
          }
          const upstreamBody = Buffer.concat(responseChunks);
          const headers = {};
          if (upstreamResponse.headers['content-type']) headers['Content-Type'] = upstreamResponse.headers['content-type'];
          if (upstreamResponse.headers['mcp-session-id']) headers['Mcp-Session-Id'] = upstreamResponse.headers['mcp-session-id'];
          if (upstreamResponse.headers['mcp-protocol-version']) headers['MCP-Protocol-Version'] = upstreamResponse.headers['mcp-protocol-version'];
          headers['Content-Length'] = upstreamBody.length;
          response.writeHead(upstreamResponse.statusCode || 502, headers);
          response.end(upstreamBody);
        });
      });
      upstream.on('timeout', () => upstream.destroy(new Error('upstream timeout')));
      upstream.on('error', () => failOnce(503, 'Coding Tools MCP is not available'));
      upstream.end(body);
    });
  }
}

module.exports = {
  HubProxyGateway,
  sameToken,
  proxyIdentityFromHeaders,
  normalizeProviderTelemetry,
  MAX_REQUEST_BYTES,
  MAX_RESPONSE_BYTES,
  MAX_TELEMETRY_REQUEST_BYTES
};
