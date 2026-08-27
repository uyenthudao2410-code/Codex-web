const http = require('node:http');
const { normalizeWorkspacePath, workspaceKey } = require('./config');

const DEFAULT_INTERVAL_MS = 60_000;
const DEFAULT_FAILURE_THRESHOLD = 2;
// workspace_context is a semantic probe, not a loopback liveness check. On a
// dirty Windows checkout the first request can legitimately spend several
// seconds reading Git and the canonical ledger. A 2.5s deadline caused the
// watchdog to abort a healthy response and then restart the MCP process. Keep
// the probe bounded, but leave enough budget for one complete read-only call.
const DEFAULT_TIMEOUT_MS = 10_000;
const DEFAULT_RESTART_COOLDOWN_MS = 120_000;

function semanticFailurePolicy(result) {
  const reason = String(result?.reason || 'unknown');
  if (['workspace_mismatch', 'invalid_json', 'unexpected_result'].includes(reason)) {
    return { deterministic: true, restartable: false };
  }
  if (reason === 'http_status' && [400, 401, 403, 404, 405].includes(Number(result?.statusCode || 0))) {
    return { deterministic: true, restartable: false };
  }
  if (reason === 'jsonrpc_error' && [-32600, -32601, -32602].includes(Number(result?.errorCode))) {
    return { deterministic: true, restartable: false };
  }
  return { deterministic: false, restartable: true };
}

function probeMcpSemanticHealth({ port, token, expectedWorkspace = '', timeoutMs = DEFAULT_TIMEOUT_MS }) {
  return new Promise((resolve) => {
    const body = JSON.stringify({
      jsonrpc: '2.0',
      id: 'recovery-semantic-health',
      method: 'tools/call',
      params: {
        name: 'workspace_context',
        arguments: { detail: 'compact', max_entries: 1 },
        _meta: {
          'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': { name: 'recovery-semantic-watchdog', version: '1' }
        }
      }
    });
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };
    const request = http.request({
      host: '127.0.0.1',
      port: Number(port),
      path: '/mcp',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'MCP-Protocol-Version': '2026-07-28',
        'Mcp-Method': 'tools/call',
        'Mcp-Name': 'workspace_context',
        'X-Coding-Tools-Client-Id': 'recovery-semantic-watchdog',
        'X-Coding-Tools-Client-Type': 'electron'
      },
      timeout: Math.max(250, Number(timeoutMs) || DEFAULT_TIMEOUT_MS)
    }, (response) => {
      let responseBody = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => {
        if (responseBody.length < 65536) responseBody += chunk;
      });
      response.on('end', () => {
        if (response.statusCode !== 200) {
          finish({ ok: false, reason: 'http_status', statusCode: Number(response.statusCode || 0) });
          return;
        }
        let parsed;
        try { parsed = JSON.parse(responseBody); }
        catch {
          finish({ ok: false, reason: 'invalid_json' });
          return;
        }
        if (parsed?.error) {
          finish({
            ok: false,
            reason: 'jsonrpc_error',
            errorCode: parsed.error.code ?? null,
            errorMessage: String(parsed.error.message || '').slice(0, 240)
          });
          return;
        }
        const structured = parsed?.result?.structuredContent;
        if (!structured || typeof structured.workspace !== 'string' || !structured.workspace.trim()) {
          finish({ ok: false, reason: 'unexpected_result' });
          return;
        }
        const workspace = normalizeWorkspacePath(structured.workspace);
        const expected = normalizeWorkspacePath(expectedWorkspace);
        if (expected && workspaceKey(workspace) !== workspaceKey(expected)) {
          finish({
            ok: false,
            reason: 'workspace_mismatch',
            workspace,
            expectedWorkspace: expected
          });
          return;
        }
        finish({ ok: true, workspace });
      });
    });
    request.on('timeout', () => {
      request.destroy();
      finish({ ok: false, reason: 'timeout' });
    });
    request.on('error', () => finish({ ok: false, reason: 'transport_error' }));
    request.end(body);
  });
}

class SemanticMcpHealthWatchdog {
  constructor({
    settings,
    secrets,
    orchestrator,
    log,
    probe = probeMcpSemanticHealth,
    isSuppressed = () => false,
    intervalMs = DEFAULT_INTERVAL_MS,
    failureThreshold = DEFAULT_FAILURE_THRESHOLD,
    restartCooldownMs = DEFAULT_RESTART_COOLDOWN_MS
  }) {
    this.settings = settings;
    this.secrets = secrets;
    this.orchestrator = orchestrator;
    this.log = log;
    this.probe = probe;
    this.isSuppressed = isSuppressed;
    this.intervalMs = Math.max(1000, Number(intervalMs) || DEFAULT_INTERVAL_MS);
    this.failureThreshold = Math.max(1, Number(failureThreshold) || DEFAULT_FAILURE_THRESHOLD);
    this.restartCooldownMs = Math.max(1000, Number(restartCooldownMs) || DEFAULT_RESTART_COOLDOWN_MS);
    this.failures = 0;
    this.nextRestartAt = 0;
    this.timer = null;
    this.inFlight = null;
  }

  suppressed() {
    if (this.isSuppressed()) return true;
    if (this.orchestrator?.busy || this.orchestrator?.recovering) return true;
    try {
      if (this.orchestrator?.isManuallyStopped?.()) return true;
    } catch {
      return true;
    }
    return false;
  }

  async checkOnce() {
    if (this.inFlight) return this.inFlight;
    const operation = (async () => {
      if (this.suppressed()) return { ok: true, skipped: true, reason: 'suppressed' };
      const current = this.settings?.load?.() || {};
      const port = Number(current.mcpPort || 0);
      const token = String(this.secrets?.get?.('mcpAuthToken') || '');
      const expectedWorkspace = normalizeWorkspacePath(current.workspace);
      if (!Number.isInteger(port) || port <= 0 || !token || !expectedWorkspace) {
        return { ok: true, skipped: true, reason: 'not_configured' };
      }

      const result = await this.probe({ port, token, expectedWorkspace });
      if (result?.ok) {
        if (this.failures > 0) {
          this.log?.info?.('Coding MCP semantic tool-plane health recovered', { previousFailures: this.failures });
        }
        this.failures = 0;
        return result;
      }

      this.failures += 1;
      const policy = semanticFailurePolicy(result);
      const failureThreshold = this.failureThreshold;
      this.log?.warn?.('Coding MCP HTTP health is reachable but semantic tool-plane probe failed', {
        failures: this.failures,
        threshold: failureThreshold,
        reason: String(result?.reason || 'unknown'),
        errorCode: result?.errorCode ?? null,
        deterministic: policy.deterministic
      });
      if (!policy.restartable) {
        return { ...result, failures: this.failures, recoveryBlocked: true, recoveryDeferred: true, deterministicFailure: true };
      }
      if (this.failures < failureThreshold) return { ...result, failures: this.failures };
      if (Date.now() < this.nextRestartAt || this.suppressed()) {
        return { ...result, failures: this.failures, recoveryDeferred: true };
      }

      this.nextRestartAt = Date.now() + this.restartCooldownMs;
      try {
        if (typeof this.orchestrator?.recoverMcpOnly !== 'function') {
          throw Object.assign(new Error('Coding MCP-only semantic recovery is unavailable.'), {
            code: 'MCP_RECOVERY_UNAVAILABLE'
          });
        }
        await this.orchestrator.recoverMcpOnly({
          replaceLiveOwned: true,
          reason: 'semantic_watchdog_soft_recovery'
        });
        const observedFailures = this.failures;
        this.failures = 0;
        this.log?.warn?.('Recovery Host replaced only Coding MCP after repeated semantic tool-plane failures', {
          failures: observedFailures,
          reason: String(result?.reason || 'unknown')
        });
        return { ...result, recovered: true, failures: observedFailures };
      } catch (error) {
        this.log?.error?.(error?.message || 'Semantic Coding MCP recovery failed', {
          stage: 'semantic-mcp-recovery',
          code: String(error?.code || 'SEMANTIC_MCP_RECOVERY_FAILED')
        });
        return { ...result, failures: this.failures, recoveryFailed: true };
      }
    })();
    this.inFlight = operation;
    try {
      return await operation;
    } finally {
      if (this.inFlight === operation) this.inFlight = null;
    }
  }

  start() {
    if (this.timer) return false;
    this.timer = setInterval(() => {
      this.checkOnce().catch((error) => {
        this.log?.error?.(error?.message || 'Semantic Coding MCP health check failed', {
          stage: 'semantic-mcp-watchdog',
          code: String(error?.code || 'SEMANTIC_MCP_WATCHDOG_FAILED')
        });
      });
    }, this.intervalMs);
    this.timer.unref?.();
    return true;
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    return true;
  }
}

module.exports = {
  probeMcpSemanticHealth,
  semanticFailurePolicy,
  SemanticMcpHealthWatchdog,
  DEFAULT_INTERVAL_MS,
  DEFAULT_FAILURE_THRESHOLD,
  DEFAULT_RESTART_COOLDOWN_MS
};
