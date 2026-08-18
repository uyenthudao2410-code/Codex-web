const http = require('node:http');

const DEFAULT_INTERVAL_MS = 15_000;
const DEFAULT_FAILURE_THRESHOLD = 3;
const DEFAULT_TIMEOUT_MS = 2_500;
const DEFAULT_RESTART_COOLDOWN_MS = 60_000;

function probeMcpSemanticHealth({ port, token, timeoutMs = DEFAULT_TIMEOUT_MS }) {
  return new Promise((resolve) => {
    const body = JSON.stringify({
      jsonrpc: '2.0',
      id: 'recovery-semantic-health',
      method: 'tools/call',
      params: {
        name: 'workspace_context',
        arguments: { detail: 'compact', max_entries: 1 }
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
        'MCP-Protocol-Version': '2025-11-25'
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
        finish({ ok: true, workspace: structured.workspace });
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
      if (!Number.isInteger(port) || port <= 0 || !token) {
        return { ok: true, skipped: true, reason: 'not_configured' };
      }

      const result = await this.probe({ port, token });
      if (result?.ok) {
        if (this.failures > 0) {
          this.log?.info?.('Coding MCP semantic tool-plane health recovered', { previousFailures: this.failures });
        }
        this.failures = 0;
        return result;
      }

      this.failures += 1;
      this.log?.warn?.('Coding MCP HTTP health is reachable but semantic tool-plane probe failed', {
        failures: this.failures,
        threshold: this.failureThreshold,
        reason: String(result?.reason || 'unknown'),
        errorCode: result?.errorCode ?? null
      });
      if (this.failures < this.failureThreshold) return { ...result, failures: this.failures };
      if (Date.now() < this.nextRestartAt || this.suppressed()) {
        return { ...result, failures: this.failures, recoveryDeferred: true };
      }

      this.nextRestartAt = Date.now() + this.restartCooldownMs;
      try {
        await this.orchestrator.restart({ automatic: true });
        const observedFailures = this.failures;
        this.failures = 0;
        this.log?.warn?.('Recovery Host restarted Coding MCP after repeated semantic tool-plane failures', {
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
  SemanticMcpHealthWatchdog,
  DEFAULT_INTERVAL_MS,
  DEFAULT_FAILURE_THRESHOLD,
  DEFAULT_RESTART_COOLDOWN_MS
};
