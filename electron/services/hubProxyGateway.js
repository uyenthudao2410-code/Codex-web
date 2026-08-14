const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const { hubProxyDescriptorFile } = require('../paths');
const { writeJsonAtomic } = require('./jsonStore');

const MAX_REQUEST_BYTES = 1024 * 1024;
const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
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
    if (request.method !== 'POST' || (request.url !== '/mcp' && !isHeartbeat)) {
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
    const declaredLength = Number(request.headers['content-length'] || 0);
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > MAX_REQUEST_BYTES) {
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
      if (total > MAX_REQUEST_BYTES) {
        request.destroy();
        failOnce(413, 'Request too large');
        return;
      }
      chunks.push(chunk);
    });
    request.on('error', () => failOnce(400, 'Invalid proxy request'));
    request.on('end', () => {
      if (finished) return;
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
        path: isHeartbeat ? '/__control/hub' : '/mcp',
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
  MAX_REQUEST_BYTES,
  MAX_RESPONSE_BYTES
};
