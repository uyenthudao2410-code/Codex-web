const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const CANARY_VERSION = 'opencode-flash-canary-v1';
const FLASH_MODEL = 'opencode-go/deepseek-v4-flash';
const CANARY_TOKEN_BUDGET = 4096;
const CANARY_PROMPT = 'Read package.json only. Reply with exactly the value of its top-level name field and nothing else. Do not modify files.';
const ELIGIBLE_STATES = new Set(['ROUTED', 'EXECUTING', 'PROVING', 'ACCEPTING']);
const TERMINAL_STATES = new Set(['completed', 'failed', 'cancelled', 'timed_out']);

class CanaryError extends Error {
  constructor(code, message, details = {}) {
    super(String(message || code || 'Execution Hub provider canary failed'));
    this.name = 'CanaryError';
    this.code = String(code || 'CANARY_FAILED');
    this.details = details && typeof details === 'object' ? details : {};
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function safeText(value, max = 300) {
  return String(value ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
}

function normalizeWorkspace(value) {
  const resolved = path.resolve(String(value || '').trim());
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

function isElectronEntrypoint({ versions = process.versions, argv = process.argv, filename = __filename } = {}) {
  if (!versions?.electron || !Array.isArray(argv) || !argv[1]) return false;
  return normalizeWorkspace(argv[1]) === normalizeWorkspace(filename);
}

function configureElectronAppContext(app, appData = process.env.APPDATA) {
  const root = safeText(appData, 2000);
  if (!root) throw new CanaryError('APPDATA_UNAVAILABLE', 'Windows APPDATA is unavailable.');
  const dataRoot = path.join(root, 'web-mcp-assistant');
  // Keep the legacy data root so version 1.0 reuses the managed runtime state.
  app.setName('Coding Tools MCP');
  app.setPath('userData', dataRoot);
  return dataRoot;
}

function deriveRequestId(runId, waveId) {
  return `flash-canary-${crypto.createHash('sha256').update(`${CANARY_VERSION}\0${runId}\0${waveId}`, 'utf8').digest('hex').slice(0, 32)}`;
}

function requestJson({ port, token, method = 'GET', requestPath, body, timeoutMs = 5000 }) {
  return new Promise((resolve, reject) => {
    const encoded = body === undefined ? null : Buffer.from(JSON.stringify(body), 'utf8');
    const request = http.request({
      hostname: '127.0.0.1',
      port: Number(port),
      path: requestPath,
      method,
      timeout: timeoutMs,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
        ...(encoded ? { 'Content-Type': 'application/json', 'Content-Length': String(encoded.length) } : {})
      }
    }, (response) => {
      const chunks = [];
      let total = 0;
      response.on('data', (chunk) => {
        total += chunk.length;
        if (total <= 1024 * 1024) chunks.push(chunk);
      });
      response.on('end', () => {
        if (total > 1024 * 1024) {
          reject(new CanaryError('CONTROL_RESPONSE_TOO_LARGE', 'Execution Hub control response exceeded the canary limit.'));
          return;
        }
        let parsed = {};
        try { parsed = chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}; }
        catch {
          reject(new CanaryError('CONTROL_RESPONSE_INVALID', 'Execution Hub control response was not valid JSON.', { status: response.statusCode }));
          return;
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new CanaryError(
            safeText(parsed.code || `HTTP_${response.statusCode}`, 120),
            safeText(parsed.message || parsed.error || 'Execution Hub control request failed.'),
            { status: response.statusCode }
          ));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => request.destroy(new CanaryError('CONTROL_TIMEOUT', 'Execution Hub control request timed out.')));
    request.on('error', (error) => reject(error instanceof CanaryError ? error : new CanaryError('CONTROL_UNAVAILABLE', 'Execution Hub control endpoint is unavailable.')));
    if (encoded) request.write(encoded);
    request.end();
  });
}

function validateContext(snapshot, expectedWorkspace) {
  const runId = safeText(snapshot?.resume_packet?.run_id || snapshot?.run_id, 256);
  const waveId = safeText(snapshot?.resume_packet?.wave_id, 256);
  const state = safeText(snapshot?.resume_packet?.orchestration_state, 40).toUpperCase();
  const runStatus = safeText(snapshot?.run?.status, 40).toLowerCase();
  const observedWorkspace = safeText(snapshot?.runtime?.workspace || snapshot?.workspace, 2000);
  if (!runId || !waveId || runStatus !== 'active' || !ELIGIBLE_STATES.has(state)) {
    throw new CanaryError('PROVIDER_CANARY_CONTEXT_UNAVAILABLE', 'Provider canary requires the current active task-projected orchestration wave in an eligible state.', { state });
  }
  if (observedWorkspace && normalizeWorkspace(observedWorkspace) !== normalizeWorkspace(expectedWorkspace)) {
    throw new CanaryError('PROVIDER_CANARY_WORKSPACE_MISMATCH', 'Execution Hub runtime workspace does not match the canary workspace.');
  }
  return { runId, waveId, state };
}

function validateHealth(health, expectedWorkspace) {
  const observedWorkspace = safeText(health?.workspace, 2000);
  const toolProfile = safeText(health?.tool_profile, 80);
  const toolCount = Number(health?.tool_count);
  const instanceId = safeText(health?.instance_id, 256);
  if (health?.ready !== true) {
    throw new CanaryError('PROVIDER_CANARY_RUNTIME_NOT_READY', 'Execution Hub MCP runtime is not ready.');
  }
  if (!observedWorkspace || normalizeWorkspace(observedWorkspace) !== normalizeWorkspace(expectedWorkspace)) {
    throw new CanaryError('PROVIDER_CANARY_WORKSPACE_MISMATCH', 'Live Execution Hub MCP workspace does not match the canary workspace.');
  }
  if (toolProfile !== 'smart-v3' || toolCount !== 8) {
    throw new CanaryError('PROVIDER_CANARY_CONTRACT_MISMATCH', 'Live Execution Hub MCP tool contract does not match Smart-v3 / 8 tools.', { tool_profile: toolProfile, tool_count: toolCount });
  }
  if (!instanceId) {
    throw new CanaryError('PROVIDER_CANARY_INSTANCE_MISSING', 'Live Execution Hub MCP instance identity is unavailable.');
  }
  return { workspace: observedWorkspace, toolProfile, toolCount, instanceId };
}

function matchingUsageEvent(snapshot, delegationId) {
  const events = Array.isArray(snapshot?.usage_events) ? snapshot.usage_events : [];
  return events.find((item) => safeText(item?.delegation_id, 256) === delegationId) || null;
}

function sanitizedSummary({ context, dispatch, usage }) {
  const usageFields = usage?.usage || {};
  const measurement = usage?.measurement || {};
  const cost = usage?.cost || {};
  const timing = usage?.timing || {};
  return {
    ok: true,
    canary_version: CANARY_VERSION,
    run_id: context.runId,
    wave_id: context.waveId,
    dispatch_id: safeText(dispatch?.dispatch_id, 256),
    delegation_id: safeText(dispatch?.delegation_id, 256),
    model: safeText(usage?.model || dispatch?.model, 160),
    status: safeText(usage?.status || dispatch?.status, 40),
    usage: {
      input_tokens: Number(usageFields.input_tokens || 0),
      cached_input_tokens: Number(usageFields.cached_input_tokens || 0),
      uncached_input_tokens: Number(usageFields.uncached_input_tokens || 0),
      output_tokens: Number(usageFields.output_tokens || 0),
      reasoning_output_tokens: Number(usageFields.reasoning_output_tokens || 0),
      cache_read_tokens: Number(usageFields.cache_read_tokens || 0),
      cache_write_tokens: Number(usageFields.cache_write_tokens || 0)
    },
    cost: {
      provider_cost: cost.provider_cost === null || cost.provider_cost === undefined ? null : Number(cost.provider_cost),
      kind: safeText(cost.kind, 80)
    },
    timing: {
      provider_ms: timing.provider_ms === null || timing.provider_ms === undefined ? null : Number(timing.provider_ms)
    },
    measurement: {
      usage: safeText(measurement.usage, 80),
      cost: safeText(measurement.cost, 80),
      provider_timing: safeText(measurement.provider_timing, 80)
    },
    read_only_enforced: true
  };
}

async function preflightFlashCanary({ port, token, workspace, request = requestJson }) {
  if (!token) throw new CanaryError('MCP_BEARER_UNAVAILABLE', 'Execution Hub MCP bearer is unavailable.');
  if (!Number.isInteger(Number(port)) || Number(port) < 1 || Number(port) > 65535) throw new CanaryError('MCP_PORT_INVALID', 'Execution Hub MCP port is invalid.');
  if (!workspace) throw new CanaryError('WORKSPACE_UNAVAILABLE', 'Execution Hub workspace is unavailable.');

  const health = validateHealth(await request({ port, token, requestPath: '/__control/health' }), workspace);
  const initial = await request({ port, token, requestPath: '/__control/orchestration' });
  const context = validateContext(initial, workspace);
  return {
    context,
    health,
    summary: {
      ok: true,
      preflight: true,
      canary_version: CANARY_VERSION,
      run_id: context.runId,
      wave_id: context.waveId,
      orchestration_state: context.state,
      runtime_instance_id: health.instanceId,
      workspace_match: true,
      tool_profile: health.toolProfile,
      tool_count: health.toolCount,
      provider_dispatches: 0,
      read_only_enforced: true
    }
  };
}

async function runFlashCanary({ port, token, workspace, request = requestJson, sleepFn = sleep, timeoutMs = 45000, telemetryWaitMs = 15000, pollMs = 500 }) {
  const { context } = await preflightFlashCanary({ port, token, workspace, request });
  const requestId = deriveRequestId(context.runId, context.waveId);
  const started = await request({
    port,
    token,
    method: 'POST',
    requestPath: '/__control/hub',
    timeoutMs: 10000,
    body: {
      action: 'provider_dispatch',
      client_id: 'electron-panel',
      client_type: 'electron',
      client_name: 'execution-hub-provider-canary',
      client_version: CANARY_VERSION,
      model: FLASH_MODEL,
      prompt: CANARY_PROMPT,
      token_budget: CANARY_TOKEN_BUDGET,
      timeout_ms: timeoutMs,
      request_id: requestId
    }
  });
  let dispatch = started?.dispatch || {};
  if (!dispatch.dispatch_id || !dispatch.delegation_id || dispatch.model !== FLASH_MODEL) {
    throw new CanaryError('PROVIDER_CANARY_DISPATCH_INVALID', 'Provider dispatch did not return the expected Flash correlation identity.');
  }

  const deadline = Date.now() + timeoutMs + 10000;
  while (!TERMINAL_STATES.has(String(dispatch.status || ''))) {
    if (Date.now() >= deadline) throw new CanaryError('PROVIDER_CANARY_OBSERVE_TIMEOUT', 'Provider dispatch did not reach a terminal state within the canary deadline.');
    await sleepFn(pollMs);
    const observed = await request({
      port,
      token,
      method: 'POST',
      requestPath: '/__control/hub',
      timeoutMs: 10000,
      body: {
        action: 'provider_observe',
        client_id: 'electron-panel',
        client_type: 'electron',
        client_name: 'execution-hub-provider-canary',
        client_version: CANARY_VERSION,
        dispatch_id: dispatch.dispatch_id
      }
    });
    dispatch = observed?.dispatch || dispatch;
  }

  if (dispatch.status !== 'completed') {
    throw new CanaryError('PROVIDER_CANARY_TERMINAL_FAILURE', 'OpenCode Flash canary reached a non-success terminal state.', {
      status: safeText(dispatch.status, 40),
      error_class: safeText(dispatch.error_class, 120)
    });
  }

  const telemetryDeadline = Date.now() + telemetryWaitMs;
  let usage = null;
  while (!usage && Date.now() < telemetryDeadline) {
    const snapshot = await request({ port, token, requestPath: '/__control/orchestration' });
    usage = matchingUsageEvent(snapshot, safeText(dispatch.delegation_id, 256));
    if (!usage) await sleepFn(Math.min(500, pollMs));
  }
  if (!usage) throw new CanaryError('PROVIDER_CANARY_TELEMETRY_MISSING', 'Provider completed but no correlated UsageEvent arrived within the telemetry window.');
  if (usage.model !== FLASH_MODEL || usage.measurement?.usage !== 'measured' || usage.measurement?.cost !== 'measured' || typeof usage.cost?.provider_cost !== 'number') {
    throw new CanaryError('PROVIDER_CANARY_MEASUREMENT_INVALID', 'Correlated UsageEvent is missing exact model, measured usage, or measured provider cost.');
  }
  return sanitizedSummary({ context, dispatch, usage });
}

function loadElectronControlState({ app, safeStorage }) {
  const dataRoot = app.getPath('userData');
  const settingsPath = path.join(dataRoot, 'settings.json');
  const secretsPath = path.join(dataRoot, 'secrets.bin');
  if (!safeStorage.isEncryptionAvailable()) throw new CanaryError('SAFE_STORAGE_UNAVAILABLE', 'Electron safeStorage encryption is unavailable.');
  let settings;
  let secrets;
  try { settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8')); }
  catch { throw new CanaryError('SETTINGS_UNAVAILABLE', 'Execution Hub settings are unavailable.'); }
  try { secrets = JSON.parse(safeStorage.decryptString(fs.readFileSync(secretsPath))); }
  catch { throw new CanaryError('SECRETS_UNAVAILABLE', 'Execution Hub secrets could not be decrypted.'); }
  const workspace = path.resolve(String(settings.workspace || ''));
  if (normalizeWorkspace(workspace) !== normalizeWorkspace(process.cwd())) throw new CanaryError('PROVIDER_CANARY_WORKSPACE_MISMATCH', 'Current working directory does not match the Electron-managed workspace.');
  return { port: Number(settings.mcpPort), workspace, token: String(secrets.mcpAuthToken || '') };
}

async function electronMain() {
  const { app, safeStorage } = require('electron');
  try {
    configureElectronAppContext(app);
    await app.whenReady();
    const control = loadElectronControlState({ app, safeStorage });
    const summary = process.argv.includes('--preflight')
      ? (await preflightFlashCanary(control)).summary
      : await runFlashCanary(control);
    process.stdout.write(`${JSON.stringify(summary)}\n`);
    app.exit(0);
  } catch (error) {
    const safe = error instanceof CanaryError ? error : new CanaryError('PROVIDER_CANARY_FAILED', 'OpenCode Flash canary failed unexpectedly.');
    process.stderr.write(`${JSON.stringify({ ok: false, code: safe.code, message: safeText(safe.message), details: safe.details })}\n`);
    app.exit(1);
  }
}

if (isElectronEntrypoint()) electronMain();

module.exports = {
  CANARY_VERSION,
  CANARY_TOKEN_BUDGET,
  FLASH_MODEL,
  CANARY_PROMPT,
  CanaryError,
  configureElectronAppContext,
  deriveRequestId,
  isElectronEntrypoint,
  matchingUsageEvent,
  preflightFlashCanary,
  requestJson,
  runFlashCanary,
  safeText,
  sanitizedSummary,
  validateContext,
  validateHealth
};
