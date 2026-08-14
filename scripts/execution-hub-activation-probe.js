const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');

const MAX_DESCRIPTOR_BYTES = 16 * 1024;
const DEFAULT_TIMEOUT_MS = 1500;

function descriptorPath(env = process.env) {
  const configured = String(env.CODING_TOOLS_MCP_PROXY_DESCRIPTOR || '').trim();
  if (configured) return configured;
  const appData = String(env.APPDATA || '').trim();
  return appData ? path.join(appData, 'web-mcp-assistant', 'execution-hub-proxy.json') : '';
}

async function loadDescriptor(target) {
  if (!target) throw Object.assign(new Error('Execution Hub descriptor path is unavailable.'), { code: 'DESCRIPTOR_PATH_UNAVAILABLE' });
  let raw;
  try {
    raw = await fs.readFile(target, 'utf8');
  } catch {
    throw Object.assign(new Error('Execution Hub descriptor is not available.'), { code: 'DESCRIPTOR_UNAVAILABLE' });
  }
  if (Buffer.byteLength(raw, 'utf8') > MAX_DESCRIPTOR_BYTES) {
    throw Object.assign(new Error('Execution Hub descriptor exceeds the bounded size.'), { code: 'DESCRIPTOR_INVALID' });
  }
  let value;
  try { value = JSON.parse(raw); } catch {
    throw Object.assign(new Error('Execution Hub descriptor is invalid JSON.'), { code: 'DESCRIPTOR_INVALID' });
  }
  const host = String(value?.host || '');
  const port = Number(value?.port || 0);
  const token = String(value?.token || '');
  if (value?.version !== 1 || !['127.0.0.1', 'localhost'].includes(host)) {
    throw Object.assign(new Error('Execution Hub descriptor has an unsupported endpoint.'), { code: 'DESCRIPTOR_INVALID' });
  }
  if (!Number.isInteger(port) || port < 1 || port > 65535 || token.length < 32) {
    throw Object.assign(new Error('Execution Hub descriptor is incomplete.'), { code: 'DESCRIPTOR_INVALID' });
  }
  return {
    version: 1,
    host: '127.0.0.1',
    port,
    token,
    electronPid: Number.isInteger(Number(value.electron_pid)) ? Number(value.electron_pid) : null,
  };
}

function requestTelemetryRoute(descriptor, timeoutMs) {
  return new Promise((resolve, reject) => {
    const body = Buffer.from('{}');
    const request = http.request({
      host: descriptor.host,
      port: descriptor.port,
      path: '/__hub_proxy/telemetry',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${descriptor.token}`,
        'Content-Type': 'application/json',
        'Content-Length': body.length,
      },
      timeout: timeoutMs,
    }, (response) => {
      response.resume();
      response.on('end', () => resolve(Number(response.statusCode || 0)));
    });
    request.on('timeout', () => request.destroy(new Error('probe timeout')));
    request.on('error', () => reject(Object.assign(new Error('Execution Hub gateway is not reachable.'), { code: 'GATEWAY_UNREACHABLE' })));
    request.end(body);
  });
}

async function probeActivation({ descriptorFile = descriptorPath(), timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  let descriptor;
  try {
    descriptor = await loadDescriptor(descriptorFile);
  } catch (error) {
    return { ok: false, route_loaded: false, code: error.code || 'PROBE_FAILED', message: error.message };
  }
  let status;
  try {
    status = await requestTelemetryRoute(descriptor, Math.max(100, Number(timeoutMs) || DEFAULT_TIMEOUT_MS));
  } catch (error) {
    return { ok: false, route_loaded: false, code: error.code || 'GATEWAY_UNREACHABLE', message: error.message };
  }
  const base = {
    status,
    descriptor_version: descriptor.version,
    host: descriptor.host,
    port: descriptor.port,
    electron_pid: descriptor.electronPid,
  };
  if (status === 403) {
    return { ok: true, route_loaded: true, ...base };
  }
  if (status === 404) {
    return { ok: false, route_loaded: false, code: 'ELECTRON_RESTART_REQUIRED', message: 'Electron is reachable but has not loaded the telemetry gateway route.', ...base };
  }
  if (status === 401) {
    return { ok: false, route_loaded: false, code: 'DESCRIPTOR_STALE', message: 'The descriptor token does not match the running Electron gateway.', ...base };
  }
  return { ok: false, route_loaded: false, code: 'UNEXPECTED_GATEWAY_RESPONSE', message: 'Telemetry route probe returned an unexpected status.', ...base };
}

async function main() {
  const result = await probeActivation();
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  main().catch(() => {
    process.stdout.write(`${JSON.stringify({ ok: false, route_loaded: false, code: 'PROBE_FAILED' })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  descriptorPath,
  loadDescriptor,
  probeActivation,
  MAX_DESCRIPTOR_BYTES,
  DEFAULT_TIMEOUT_MS,
};
