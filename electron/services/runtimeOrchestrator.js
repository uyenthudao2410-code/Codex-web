const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {
  NativeService,
  isAlive,
  runtimeFingerprint,
  P5_A0_SEED_SECRET,
  normalizeActivationGate,
  ACTIVATION_GATE_CLOSED
} = require('./nativeService');
const { TunnelService } = require('./tunnelService');
const { validateRuntimeSettings, mergeRecentWorkspaces, normalizeWorkspacePath, workspaceKey } = require('./config');
const { canConnect } = require('./environmentService');
const { resolveProxy } = require('./proxyService');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic } = require('./jsonStore');
const { ComponentRevisionTracker } = require('./componentRevision');
const { ActivationEpochStore } = require('./activationEpoch');
const { run } = require('./commandRunner');
const { runtimeDeviceIdentity, classifyStoredDeviceOwner } = require('./deviceIdentity');
const { CONNECTOR_ATTESTATION_HEADER, connectorAttestationHeader } = require('./connectorAttestation');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  READ_ONLY_TOOL_NAME,
  READ_ONLY_ARGUMENTS,
  compactWorkspaceSummary,
  digest: controlPlaneBridgeDigest,
  workspaceSummaryDigest
} = require('./controlPlaneReadOnlyBridge');
const { readControlPlaneRouteEvidence } = require('./controlPlaneRouteEvidence');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

// `runtimeIdentity().mode` answers where Electron was loaded from
// (development or packaged).  This role answers who owns the OpenAI ingress.
// Keep this normalization local to the lifecycle boundary so a malformed or
// legacy settings file can never silently opt a device into central control.
function executionRole(settings) {
  return settings?.executionRole === 'central_executor' ? 'central_executor' : 'direct_legacy';
}

// A local executor being healthy and a centrally-authorized action being
// allowed are deliberately separate facts.  In particular, a node must never
// report a fake local Tunnel/connector just to make the old direct readiness
// badge green.  The central route handshake and per-action authority are added
// by the node enrollment wave; until then their truthful state is false.
function runtimeReadiness({
  role,
  mcpRunning,
  nativeAlive,
  tunnelRunning,
  epochReady,
  revisionReady,
  connectorReady,
  activationIncomplete,
  revisionDrift,
  centralConnected = false,
  authorityReady = false,
  centralRouteReason = ''
}) {
  const normalizedRole = role === 'central_executor' ? 'central_executor' : 'direct_legacy';
  const localReady = Boolean(mcpRunning && nativeAlive && epochReady && revisionReady);
  const directComponentsReady = Boolean(mcpRunning && tunnelRunning && epochReady && revisionReady);
  if (normalizedRole === 'central_executor') {
    return {
      executionRole: normalizedRole,
      localReady,
      directReady: false,
      centralConnected: Boolean(centralConnected),
      authorityReady: Boolean(authorityReady),
      componentsReady: localReady,
      fullyReady: Boolean(localReady && centralConnected && authorityReady),
      updateIncomplete: Boolean(activationIncomplete || revisionDrift),
      centralStatusReason: !localReady
        ? 'LOCAL_EXECUTOR_NOT_READY'
        : (!centralConnected
            ? (String(centralRouteReason || '').trim() || 'CENTRAL_ROUTE_NOT_CONFIGURED')
            : (!authorityReady ? 'CENTRAL_LOCAL_POLICY_NOT_READY' : null))
    };
  }
  return {
    executionRole: normalizedRole,
    localReady,
    directReady: Boolean(directComponentsReady && connectorReady),
    centralConnected: false,
    authorityReady: false,
    componentsReady: directComponentsReady,
    fullyReady: Boolean(directComponentsReady && connectorReady),
    updateIncomplete: Boolean(activationIncomplete || revisionDrift || !connectorReady),
    centralStatusReason: null
  };
}

function assertActivationDeadline(expiresAtUnixMs, boundary, processMutated = false) {
  const expiresAt = Number(expiresAtUnixMs || 0);
  if (expiresAt > 0 && Date.now() >= expiresAt) {
    throw Object.assign(new Error('Activation request expired before process mutation.'), {
      code: 'ACTIVATION_REQUEST_EXPIRED',
      details: { boundary, process_mutated: processMutated }
    });
  }
}

const MAX_DEFERRED_RECOVERIES = 6;
const MAX_SUPERVISOR_REQUEST_AGE_MS = 60_000;
const READY_COMMIT_DIGEST_PATTERN = /^[0-9a-f]{64}$/;
const EOCL_EXACT_ID_PATTERN = /^[0-9a-f]{32}$/;
const OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const SUPERVISOR_RESTART_REASON_MAX_CHARS = 1024;
const EXACT_STALE_RUN_REASON_PREFIX = 'exact_stale_runs:';
const EXACT_STALE_RUN_ID_PATTERN = /^[a-f0-9]{32}$/;
const EXACT_STALE_RUN_MAX_IDS = 64;
const CONTROL_PLANE_READ_ONLY_TIMEOUT_MS = 15_000;

function exactStaleRunMaintenanceReason(value) {
  if (typeof value !== 'string' || !value.startsWith(EXACT_STALE_RUN_REASON_PREFIX)) return false;
  const rawIds = value.slice(EXACT_STALE_RUN_REASON_PREFIX.length);
  const runIds = rawIds ? rawIds.split(',') : [];
  return runIds.length >= 1
    && runIds.length <= EXACT_STALE_RUN_MAX_IDS
    && new Set(runIds).size === runIds.length
    && runIds.every((runId) => EXACT_STALE_RUN_ID_PATTERN.test(runId));
}

function validSupervisorRestartReason(value) {
  if (value == null) return true;
  if (typeof value !== 'string') return false;
  if (value.startsWith(EXACT_STALE_RUN_REASON_PREFIX)) return exactStaleRunMaintenanceReason(value);
  return value.length <= SUPERVISOR_RESTART_REASON_MAX_CHARS;
}

function validSupervisorRestartTarget(request, settings) {
  const raw = request?.target_workspace;
  if (raw == null || raw === '') return true;
  if (typeof raw !== 'string') return false;
  if (!exactStaleRunMaintenanceReason(request?.reason)) {
    return workspaceKey(raw) === workspaceKey(settings.workspace);
  }
  return [settings.workspace, ...(Array.isArray(settings.authorizedRoots) ? settings.authorizedRoots : [])]
    .some((candidate) => workspaceKey(candidate) === workspaceKey(raw));
}

function validSupervisorRestartRequest(request, settings, now = Date.now()) {
  if (!request || typeof request !== 'object' || Array.isArray(request)) return false;
  const ticketId = request.ticket_id;
  const requestedAt = request.requested_at_unix_ms;
  const notBefore = request.not_before_unix_ms;
  const expiresAt = request.expires_at_unix_ms;
  return request.version === 1
    && request.action === 'restart'
    && typeof ticketId === 'string'
    && OPERATION_ID_PATTERN.test(ticketId)
    && ticketId.trim() === ticketId
    && typeof request.operation_id === 'string'
    && request.operation_id === ticketId
    && request.activation_mode === 'full_clean_activation'
    && request.full_clean_required === true
    && typeof request.workspace === 'string'
    && workspaceKey(request.workspace) === workspaceKey(settings.workspace)
    && validSupervisorRestartTarget(request, settings)
    && typeof request.process_instance_id === 'string'
    && request.process_instance_id.trim() === request.process_instance_id
    && request.process_instance_id.length > 0
    && typeof request.server_instance_id === 'string'
    && request.server_instance_id.trim() === request.server_instance_id
    && request.server_instance_id.length > 0
    && typeof request.tool_contract_sha256 === 'string'
    && READY_COMMIT_DIGEST_PATTERN.test(request.tool_contract_sha256)
    && (request.allow_acceptance_pending == null || typeof request.allow_acceptance_pending === 'boolean')
    && validSupervisorRestartReason(request.reason)
    && Number.isSafeInteger(requestedAt)
    && Number.isSafeInteger(notBefore)
    && Number.isSafeInteger(expiresAt)
    && requestedAt > 0
    && requestedAt <= now + 5000
    && now - requestedAt <= MAX_SUPERVISOR_REQUEST_AGE_MS
    && requestedAt < notBefore
    && notBefore < expiresAt
    && expiresAt - requestedAt <= MAX_SUPERVISOR_REQUEST_AGE_MS
    // Expiry is an exact fail-closed boundary: at `now === expiresAt` the
    // ticket is already expired and must not be claimed or replayed.
    && expiresAt > now;
}

function readSupervisorRestartRequest(file, settings, now = Date.now()) {
  let raw = '';
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch (error) {
    if (error?.code === 'ENOENT') return { state: 'absent', file };
    return { state: 'unknown', file, error };
  }
  let request = null;
  try {
    request = JSON.parse(raw);
  } catch (error) {
    return { state: 'invalid', file, error };
  }
  return validSupervisorRestartRequest(request, settings, now)
    ? { state: 'valid', file, request, ready: now >= request.not_before_unix_ms }
    : { state: 'invalid', file, request };
}

const DETERMINISTIC_MCP_HEALTH_FAILURES = new Set([
  'auth_token_missing',
  'http_unauthorized',
  'workspace_mismatch',
  'device_mismatch',
  'protocol_mismatch',
  'invalid_json'
]);
// A retained canonical ledger census is intentionally stronger than a cheap
// liveness probe and can exceed three seconds on a healthy workspace. Keep the
// activation observation bounded without turning a valid census into a false
// MCP timeout. The separate health probe remains short and independently live.
const MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS = 15_000;
// The MCP health endpoint is intentionally lock-light, but it still runs in
// the same Python process as workspace tools.  Under a real connector load the
// interpreter may not get scheduled within a 1.2s probe window even though the
// endpoint is healthy (the access log then shows a delayed HTTP 200).  A short
// false-negative here makes the Recovery Host start a destructive soft
// recovery, which is precisely the failure mode this watchdog is meant to
// avoid.  Keep the probe bounded while allowing normal Windows/Python
// scheduling jitter and one in-flight read-only tool call to drain.
const MCP_HEALTH_TIMEOUT_MS = 5_000;
// Keep connector receipt validation aligned with the full-clean admission
// gate.  A small clock skew is tolerated, but a receipt materially from the
// future is not evidence of a client having contacted this runtime yet.
const CONNECTOR_DISCOVERY_FUTURE_SKEW_MS = 1_000;

function mcpHealthFailure(kind, details = {}) {
  return {
    kind,
    deterministic: DETERMINISTIC_MCP_HEALTH_FAILURES.has(kind),
    ...details
  };
}

function readMcpHealthObservation(port, token, expectedWorkspace = '', expectedDeviceId = '', expectedActivationEpochId = '', options = {}) {
  return new Promise((resolve) => {
    const requestedTimeout = Number(options.timeoutMs || MCP_HEALTH_TIMEOUT_MS);
    const timeoutMs = Number.isFinite(requestedTimeout)
      ? Math.max(MCP_HEALTH_TIMEOUT_MS, Math.min(Math.trunc(requestedTimeout), MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS))
      : MCP_HEALTH_TIMEOUT_MS;
    let settled = false;
    const finish = (health, failure = null) => {
      if (settled) return;
      settled = true;
      resolve({ health, failure });
    };
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/health',
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
      timeout: timeoutMs
    }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (body.length < 65536) body += chunk; });
      response.on('end', () => {
        const statusCode = Number(response.statusCode || 0);
        if (statusCode !== 200) {
          const kind = [401, 403].includes(statusCode)
            ? 'http_unauthorized'
            : ([404, 405].includes(statusCode) ? 'protocol_mismatch' : 'http_error');
          finish(null, mcpHealthFailure(kind, { statusCode }));
          return;
        }
        let payload;
        try {
          payload = JSON.parse(body);
        } catch {
          finish(null, mcpHealthFailure('invalid_json'));
          return;
        }
        if (!payload || typeof payload !== 'object' || Array.isArray(payload) || typeof payload.ready !== 'boolean') {
          finish(null, mcpHealthFailure('protocol_mismatch'));
          return;
        }
        if (payload.ready !== true) {
          finish(null, mcpHealthFailure('not_ready'));
          return;
        }
        const workspaceMatches = !expectedWorkspace
          || workspaceKey(payload.workspace) === workspaceKey(expectedWorkspace);
        if (!workspaceMatches) {
          finish(null, mcpHealthFailure('workspace_mismatch'));
          return;
        }
        const deviceMatches = !expectedDeviceId
          || String(payload.device_id || '').toLowerCase() === String(expectedDeviceId).toLowerCase();
        if (!deviceMatches) {
          finish(null, mcpHealthFailure('device_mismatch'));
          return;
        }
        const epochMatches = !expectedActivationEpochId
          || String(payload.activation_epoch_id || '').trim() === String(expectedActivationEpochId).trim();
        if (!epochMatches) {
          finish(null, mcpHealthFailure('activation_epoch_mismatch', {
            expectedActivationEpochId: String(expectedActivationEpochId).trim(),
            observedActivationEpochId: String(payload.activation_epoch_id || '').trim() || null
          }));
          return;
        }
        finish(payload, null);
      });
    });
    request.on('timeout', () => {
      request.destroy();
      finish(null, mcpHealthFailure('timeout'));
    });
    request.on('error', (error) => finish(null, mcpHealthFailure('transport_error', {
      errorCode: String(error?.code || '') || null
    })));
    request.end();
  });
}

function readMcpHealth(port, token, expectedWorkspace = '', expectedDeviceId = '', expectedActivationEpochId = '', options = {}) {
  return readMcpHealthObservation(port, token, expectedWorkspace, expectedDeviceId, expectedActivationEpochId, options)
    .then(({ health }) => health);
}

async function probeMcp(port, token, expectedWorkspace = '', expectedDeviceId = '', expectedActivationEpochId = '') {
  return Boolean(await readMcpHealth(port, token, expectedWorkspace, expectedDeviceId, expectedActivationEpochId));
}

function parseGitStatusPorcelainV2(value) {
  const lines = String(value || '').split(/\r?\n/).filter(Boolean);
  let branch = null;
  let head = null;
  let repo = false;
  let dirty = false;
  for (const line of lines) {
    if (line.startsWith('# branch.head ')) { repo = true; const raw = line.slice('# branch.head '.length).trim(); branch = raw && raw !== '(detached)' ? raw : 'detached'; }
    else if (line.startsWith('# branch.oid ')) { repo = true; const raw = line.slice('# branch.oid '.length).trim(); if (/^[0-9a-f]{40,64}$/i.test(raw)) head = raw.toLowerCase(); }
    else if (!line.startsWith('#')) dirty = true;
  }
  return { available: repo, branch, head, head_short: head ? head.slice(0, 8) : null, dirty: repo ? dirty : null };
}

function parseLoopbackListenerPid(value, port) {
  const target = `127.0.0.1:${Number(port)}`;
  const matches = new Set();
  for (const line of String(value || '').split(/\r?\n/)) {
    const fields = line.trim().split(/\s+/);
    if (fields.length < 5 || String(fields[0]).toUpperCase() !== 'TCP') continue;
    if (fields[1] !== target || String(fields[3]).toUpperCase() !== 'LISTENING') continue;
    const pid = Number(fields[4]);
    if (Number.isInteger(pid) && pid > 0) matches.add(pid);
  }
  return matches.size === 1 ? [...matches][0] : null;
}

async function loopbackListenerPid(port) {
  const result = await run('netstat.exe', ['-ano', '-p', 'tcp'], { allowFailure: true, timeoutMs: 3000 });
  if (result.code !== 0) return null;
  return parseLoopbackListenerPid(result.stdout, port);
}

function activationPreflightProof(token, operationId) {
  const value = String(operationId || '').trim();
  if (!value) return '';
  return crypto.createHmac('sha256', String(token || ''))
    .update(`coding-tools-mcp-activation-preflight:${value}`, 'utf8')
    .digest('hex');
}

function readMcpActivationPreflight(port, token, options = {}) {
  return new Promise((resolve, reject) => {
    const operationId = String(options?.operationId || '').trim();
    const headers = { Authorization: `Bearer ${token}` };
    if (operationId) {
      headers['X-Coding-Tools-Activation-Operation'] = operationId;
      headers['X-Coding-Tools-Activation-Proof'] = activationPreflightProof(token, operationId);
    }
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/activation',
      method: 'GET',
      headers,
      timeout: MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS
    }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (body.length < 65536) body += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = body ? JSON.parse(body) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || typeof parsed.safe !== 'boolean') {
          reject(Object.assign(new Error('Coding MCP activation preflight is unavailable.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
          return;
        }
        const workspace = String(parsed.workspace || '').trim();
        if (!workspace) {
          reject(Object.assign(new Error('Coding MCP activation preflight omitted workspace identity.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
          return;
        }
        resolve({ ...parsed, workspace });
      });
    });
    request.on('timeout', () => request.destroy(Object.assign(new Error('Coding MCP activation preflight timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.on('error', (error) => reject(Object.assign(error, { code: error.code || 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.end();
  });
}


function switchMcpWorkspace(port, token, workspace) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ workspace });
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/workspace',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS
    }, (response) => {
      let payload = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (payload.length < 65536) payload += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = payload ? JSON.parse(payload) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || parsed.ready !== true) {
          reject(new Error(parsed.error || `Chuyển đổi workspace MCP thất bại (HTTP ${response.statusCode})`));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian chuyển đổi workspace MCP')); });
    request.on('error', reject);
    request.end(body);
  });
}

function setMcpAuthorizedRoots(port, token, roots) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ roots });
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/roots',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 5000
    }, (response) => {
      let payload = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (payload.length < 65536) payload += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = payload ? JSON.parse(payload) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || parsed.ready !== true) {
          reject(new Error(parsed.error || `Cập nhật thư mục ủy quyền MCP thất bại (HTTP ${response.statusCode})`));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian cập nhật thư mục ủy quyền MCP')); });
    request.on('error', reject);
    request.end(body);
  });
}

function controlMcpActivation(port, token, payload) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/activation',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS
    }, (response) => {
      let responseBody = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (responseBody.length < 65536) responseBody += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = responseBody ? JSON.parse(responseBody) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200) {
          reject(Object.assign(new Error(String(parsed.error || 'Coding MCP activation preflight failed.')), {
            code: String(parsed.code || 'ORCHESTRATION_STATE_UNCERTAIN'),
            details: parsed.details || parsed
          }));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => request.destroy(Object.assign(new Error('Coding MCP activation preflight timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.on('error', (error) => reject(Object.assign(error, { code: error.code || 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.end(body);
  });
}

class RuntimeOrchestrator {
  constructor({ settings, secrets, environment, log, emitProgress = () => {}, emitStatus = () => {}, paths = defaultPaths, revisionTracker = null, deviceIdentity = null, deviceInstanceId = '', activationEpochId = '', fullCleanActivation = null, resolveFullCleanSourceCheckpoint = null, listenerPidProbe = null }) {
    this.settingsStore = settings;
    this.secrets = secrets;
    this.environment = environment;
    this.log = log;
    this.emitProgress = emitProgress;
    this.emitStatus = emitStatus;
    this.paths = paths;
    // Production uses the Windows loopback listener probe.  Keep a narrowly
    // scoped seam for lifecycle proofs; it never changes the default owner
    // check or exposes a renderer-controlled override.
    this.listenerPidProbe = typeof listenerPidProbe === 'function' ? listenerPidProbe : null;
    this.revisions = revisionTracker || new ComponentRevisionTracker({ paths });
    this.activationEpochStore = (() => { try { return new ActivationEpochStore({ paths }); } catch { return null; } })();
    this.activationEpochId = String(activationEpochId || '').trim() || (() => {
      try { return String(this.activationEpochStore?.current?.()?.activation_epoch_id || '').trim(); } catch { return ''; }
    })();
    // One secret is shared only by an MCP process launched by this
    // orchestrator and the managed Coding Tunnel bound to that exact process.
    // Do not invent an apparently usable secret when adopting an already
    // running MCP after a Recovery Host restart: without the original secret
    // a Tunnel-only repair must fail closed and request a full-clean
    // activation instead of emitting an attestation the MCP cannot verify.
    this.connectorAttestationSecret = '';
    this.connectorAttestationBinding = null;
    this.fullCleanActivation = fullCleanActivation;
    this.resolveFullCleanSourceCheckpoint = typeof resolveFullCleanSourceCheckpoint === 'function'
      ? resolveFullCleanSourceCheckpoint : null;
    this.device = (deviceIdentity || deviceInstanceId) ? runtimeDeviceIdentity(deviceIdentity, deviceInstanceId) : null;
    this.native = new NativeService(log, paths, this.revisions, this.device);
    this.tunnel = new TunnelService(log, paths, this.device);
    this.gitStatusCache = null;
    this.gitStatusCacheAt = 0;
    this.gitStatusWorkspace = '';
    this.gitStatusRefreshInFlight = null;
    this.gitStatusRefreshWorkspace = '';
    this.busy = false;
    this.snapshotCache = null;
    this.snapshotCacheAt = 0;
    this.snapshotInFlight = null;
    this.heartbeatFailures = 0;
    this.heartbeatFailureKind = '';
    this.recovering = false;
    this.recoveryAttempts = 0;
    this.nextRecoveryAt = 0;
    this.autoRecoveryBlocked = false;
    this.lastStartFailure = '';
    this.deferredRecoveryCount = 0;
    this.heartbeatFailureSince = 0;
    this.lastRecoveryAt = 0;
    this.lastHealthyAt = 0;
    this.accumulatedDowntimeMs = 0;
    this.lastMcpHealthFailure = null;
  }

  setActivationEpoch(activationEpochId = '') {
    this.activationEpochId = String(activationEpochId || '').trim();
    return this.activationEpochId || null;
  }

  rotateConnectorAttestationSecret() {
    this.connectorAttestationSecret = crypto.randomBytes(32).toString('base64url');
    this.connectorAttestationBinding = null;
    return this.connectorAttestationSecret;
  }

  connectorAttestationForHealth(health, { establish = false, secret = this.connectorAttestationSecret } = {}) {
    const key = String(secret || '').trim();
    const binding = {
      activationEpochId: String(health?.activation_epoch_id || this.activationEpochId || '').trim(),
      processInstanceId: String(health?.process_instance_id || '').trim(),
      serverInstanceId: String(health?.instance_id || health?.server_instance_id || '').trim(),
      contractSha256: String(health?.tool_contract?.sha256 || '').trim().toLowerCase()
    };
    if (!key || !binding.processInstanceId || !binding.serverInstanceId
      || !/^[0-9a-f]{64}$/.test(binding.contractSha256)) {
      throw Object.assign(new Error('Coding Tools MCP did not expose a complete managed connector-attestation identity.'), {
        code: 'CONNECTOR_ATTESTATION_IDENTITY_UNAVAILABLE'
      });
    }
    if (establish) {
      this.connectorAttestationSecret = key;
      this.connectorAttestationBinding = { ...binding };
    } else {
      const active = this.connectorAttestationBinding;
      const matches = active
        && Object.keys(binding).every((field) => String(active[field] || '') === String(binding[field] || ''));
      if (!matches) {
        throw Object.assign(new Error('The current Recovery Host does not own the connector attestation for this Coding MCP process; full-clean activation is required.'), {
          code: 'CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE'
        });
      }
    }
    return { secret: key, ...binding };
  }

  setFullCleanActivation(coordinator) {
    this.fullCleanActivation = coordinator || null;
    return this.fullCleanActivation;
  }

  setFullCleanSourceCheckpointResolver(resolver) {
    this.resolveFullCleanSourceCheckpoint = typeof resolver === 'function' ? resolver : null;
    return this.resolveFullCleanSourceCheckpoint;
  }

  activationEpochStatus() {
    if (!this.activationEpochStore || typeof this.activationEpochStore.current !== 'function') {
      return {
        activation_epoch_id: null,
        operation_id: null,
        state: 'UPDATE_INCOMPLETE',
        admission_open: false,
        update_incomplete: true,
        error_code: 'ACTIVATION_EPOCH_STORE_UNAVAILABLE'
      };
    }
    let record = null;
    try { record = this.activationEpochStore.current() || null; } catch (error) {
      return { activation_epoch_id: null, state: 'UPDATE_INCOMPLETE', admission_open: false, update_incomplete: true, error_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID') };
    }
    if (!record) return { activation_epoch_id: null, operation_id: null, state: 'NONE', admission_open: true, update_incomplete: false };
    const id = String(record.activation_epoch_id || '');
    const admissionOpen = record.state === 'READY' && record.admission_state === 'OPEN';
    return {
      activation_epoch_id: id || null,
      operation_id: String(record.operation_id || '').trim() || null,
      state: admissionOpen ? 'READY' : 'UPDATE_INCOMPLETE',
      epoch_state: record.state,
      admission_open: admissionOpen,
      update_incomplete: !admissionOpen,
      ready_commit_digest: String(record.ready_commit_digest || '') || null,
      expires_at_unix_ms: Number(record.expires_at_unix_ms || 0) || null,
      ready_at: record.ready_at || null,
      error: record.error || null
    };
  }

  /**
   * Determine whether a deferred supervisor operation has a durable epoch
   * binding.  This is deliberately tri-state: an unreadable epoch store is
   * not evidence that no epoch exists, so callers must retain the fence and
   * keep admission closed rather than reopening on uncertainty.
   */
  activationEpochBinding(operationId) {
    const id = String(operationId || '').trim();
    if (!id) return { known: false, bound: false, operation_id: null };
    try {
      if (!this.activationEpochStore || typeof this.activationEpochStore.load !== 'function') {
        return { known: false, bound: false, operation_id: id, reason: 'epoch_store_unavailable' };
      }
      const snapshot = this.activationEpochStore.load();
      const records = [
        snapshot?.current,
        ...(Array.isArray(snapshot?.history) ? snapshot.history : [])
      ].filter((item) => item && typeof item === 'object');
      const bound = records.find((item) => String(item.operation_id || '').trim() === id) || null;
      return {
        known: true,
        bound: Boolean(bound),
        operation_id: id,
        activation_epoch_id: bound?.activation_epoch_id || null,
        epoch_state: bound?.state || null
      };
    } catch (error) {
      return {
        known: false,
        bound: false,
        operation_id: id,
        reason: 'epoch_store_read_failed',
        error_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID')
      };
    }
  }

  assertActivationRevisionContinuity() {
    const state = readJson(this.paths.stateFile(), {});
    let record = null;
    try { record = this.activationEpochStore?.current?.() || null; } catch (error) {
      throw Object.assign(new Error('Activation epoch revision continuity cannot be verified.'), {
        code: 'UPDATE_INCOMPLETE',
        details: { error_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID') }
      });
    }
    // A stopped legacy runtime may retain its last nativeCodeRevision in the
    // JSON projection. That historical value is not a currently loaded
    // revision and must not brick the first explicit activation after an
    // upgrade. Only a live owned PID participates in the continuity check;
    // durable READY epoch evidence remains authoritative when present.
    const nativeRevision = isAlive(state.nativePid)
      ? String(state.nativeCodeRevision || '').trim()
      : '';
    const candidates = [
      nativeRevision,
      String(record?.verification?.final_census?.running_revision || '').trim(),
      String(record?.verification?.final_census?.disk_revision || '').trim(),
      String(record?.component_revisions?.coding_mcp?.disk_revision || '').trim()
    ].filter(Boolean);
    const expected = [...new Set(candidates)];
    if (expected.length > 1) {
      throw Object.assign(new Error('Persisted Coding MCP revision evidence disagrees; a full-clean activation is required.'), {
        code: 'UPDATE_INCOMPLETE',
        details: { expected_revisions: expected, activation_epoch_id: record?.activation_epoch_id || null }
      });
    }
    if (record?.state === 'READY' && expected.length === 0) {
      throw Object.assign(new Error('The READY activation epoch has no Coding MCP revision proof.'), {
        code: 'UPDATE_INCOMPLETE',
        details: { activation_epoch_id: record.activation_epoch_id }
      });
    }
    if (expected.length === 0) return { verified: false, expected_revision: null, disk_revision: null };
    let diskRevision = '';
    try { diskRevision = String(this.revisions.disk('coding_mcp', { force: true }).revision || '').trim(); }
    catch (error) {
      throw Object.assign(new Error('Coding MCP disk revision is unavailable; refusing a non-transactional process start.'), {
        code: 'UPDATE_INCOMPLETE',
        details: { error_code: String(error?.code || 'REVISION_UNAVAILABLE'), expected_revision: expected[0] }
      });
    }
    if (!diskRevision || diskRevision !== expected[0]) {
      throw Object.assign(new Error('Coding MCP source changed; soft recovery cannot load a new revision under the existing activation epoch.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: record?.activation_epoch_id || null,
          expected_revision: expected[0],
          disk_revision: diskRevision || null,
          full_clean_activation_required: true
        }
      });
    }
    return { verified: true, expected_revision: expected[0], disk_revision: diskRevision };
  }

  assertSoftRecoveryAllowed() {
    const epoch = this.activationEpochStatus();
    if (epoch.update_incomplete === true) {
      throw Object.assign(new Error('Soft recovery is suppressed while a full-clean activation epoch is incomplete.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: epoch.activation_epoch_id || null,
          epoch_state: epoch.epoch_state || epoch.state || null,
          admission_open: false,
          full_clean_activation_required: true
        }
      });
    }
    return epoch;
  }

  /**
   * Validate the durable epoch before any MCP process replacement mutation.
   *
   * READY/OPEN is terminal in ActivationEpochStore: it can only be reached by
   * committing the exact READY proof and has no supported transition back to a
   * closed/re-verifying state.  Starting a new MCP process under that epoch
   * would therefore create a closed child that can never be reopened by
   * completeActivationEpoch().  Refuse that path before touching MCP or Tunnel
   * and require a new full-clean activation epoch instead.
   *
   * The same check binds an epoch-bearing launch to the durable current record.
   * This prevents a stale in-memory activationEpochId from creating a closed
   * process after the epoch store was cleared/replaced.  Empty/empty remains
   * the legacy no-epoch launch contract.
   */
  assertMcpReplacementAllowed({ activationEpochId = '', operation = 'mcp_replacement' } = {}) {
    const durable = this.activationEpochStatus();
    const requestedEpochId = String(activationEpochId || '').trim();
    const durableEpochId = String(durable.activation_epoch_id || '').trim();
    const hasRequestedEpoch = Boolean(requestedEpochId);
    const hasDurableEpoch = Boolean(durableEpochId);
    // NONE is the only legitimate empty durable state. An unreadable,
    // unavailable, or invalid epoch store also projects an empty id, but that
    // uncertainty is not authority to take the legacy no-epoch mutation path.
    if (!hasDurableEpoch && durable.update_incomplete === true) {
      throw Object.assign(new Error('Durable activation authority is unavailable; refusing Coding MCP replacement.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: requestedEpochId || null,
          current_activation_epoch_id: null,
          epoch_state: durable.epoch_state || durable.state || null,
          error_code: durable.error_code || null,
          admission_open: false,
          full_clean_activation_required: true,
          replacement_operation: String(operation || 'mcp_replacement')
        }
      });
    }
    if (hasRequestedEpoch !== hasDurableEpoch
      || (hasRequestedEpoch && requestedEpochId !== durableEpochId)) {
      throw Object.assign(new Error('The requested MCP replacement is not bound to the current durable activation epoch.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: requestedEpochId || null,
          current_activation_epoch_id: durableEpochId || null,
          epoch_state: durable.epoch_state || durable.state || null,
          admission_open: durable.admission_open === true,
          full_clean_activation_required: true,
          replacement_operation: String(operation || 'mcp_replacement')
        }
      });
    }
    const epochState = String(durable.epoch_state || durable.state || '').trim().toUpperCase();
    if (hasDurableEpoch && ['READY_COMMITTED', 'READY', 'FAILED'].includes(epochState)) {
      throw Object.assign(new Error('A committed or terminal activation cannot replace Coding MCP in place; start a new full-clean activation epoch.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: durableEpochId,
          epoch_state: epochState,
          admission_open: durable.admission_open === true,
          full_clean_activation_required: true,
          replacement_operation: String(operation || 'mcp_replacement')
        }
      });
    }
    return durable;
  }

  async completeActivationEpoch(activationEpochId, readyCommitDigest) {
    const id = String(activationEpochId || '').trim();
    if (!id) throw Object.assign(new Error('Activation epoch is required.'), { code: 'ACTIVATION_EPOCH_ID_REQUIRED' });
    const digest = String(readyCommitDigest || '').trim();
    if (!READY_COMMIT_DIGEST_PATTERN.test(digest)) {
      throw Object.assign(new Error('Activation ready commit digest is invalid.'), {
        code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID'
      });
    }
    // Validate the durable current epoch before mutating the in-memory
    // expectation.  A stale/foreign completion request must not poison the
    // orchestrator so that subsequent health checks start rejecting the real
    // active process.
    const durableRecord = this.activationEpochStore?.current?.() || null;
    const durable = this.activationEpochStatus();
    if (!durable.activation_epoch_id || durable.activation_epoch_id !== id
      || !durableRecord || durableRecord.activation_epoch_id !== id) {
      throw Object.assign(new Error('The activation epoch is not the current durable epoch.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: id,
          current_activation_epoch_id: durable.activation_epoch_id || null
        }
      });
    }
    if (durableRecord.state !== 'READY_COMMITTED'
      || String(durableRecord.ready_commit_digest || '') !== digest
      || String(durableRecord.admission_state || '') !== 'CLOSED') {
      throw Object.assign(new Error('Coding MCP admission requires the exact durable READY_COMMITTED proof.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: id,
          epoch_state: durableRecord.state || null,
          admission_state: durableRecord.admission_state || null,
          ready_commit_digest_matches: String(durableRecord.ready_commit_digest || '') === digest
        }
      });
    }
    const expiresAtUnixMs = Number(durableRecord.expires_at_unix_ms || 0);
    if (!Number.isSafeInteger(expiresAtUnixMs) || expiresAtUnixMs <= 0 || Date.now() >= expiresAtUnixMs) {
      throw Object.assign(new Error('Activation request expired before Coding MCP admission could open.'), {
        code: 'ACTIVATION_REQUEST_EXPIRED',
        details: { activation_epoch_id: id, expires_at_unix_ms: expiresAtUnixMs || null }
      });
    }
    this.setActivationEpoch(id);
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token || !(await this.native.status(settings, { activationEpochId: id }))) {
      throw Object.assign(new Error('Coding MCP replacement is not running for the requested activation epoch.'), { code: 'UPDATE_INCOMPLETE' });
    }
    // The durable commit is necessary but not sufficient: Tunnel/UI/Recovery
    // Plane identities can regress after the final census and before this
    // external mutation.  FullCleanActivation owns those component proofs, so
    // ask it to re-census the exact committed tuple at the last safe point.
    // The callback is read-only and admission remains CLOSED on every error.
    if (typeof this.fullCleanActivation?.revalidateBeforeAdmission === 'function') {
      const revalidation = await this.fullCleanActivation.revalidateBeforeAdmission({
        activationEpochId: id,
        readyCommitDigest: digest,
        expiresAtUnixMs
      });
      if (!revalidation || revalidation.valid !== true
        || String(revalidation.activation_epoch_id || '') !== id
        || String(revalidation.ready_commit_digest || '') !== digest) {
        throw Object.assign(new Error('Committed component identities changed before Coding MCP admission.'), {
          code: 'UPDATE_INCOMPLETE',
          details: {
            activation_epoch_id: id,
            ready_commit_digest: digest,
            revalidation: revalidation || null
          }
        });
      }
    }
    const result = await controlMcpActivation(settings.mcpPort, token, {
      action: 'complete_epoch',
      activation_epoch_id: id,
      ready_commit_digest: digest,
      expires_at_unix_ms: expiresAtUnixMs
    });
    if (result?.ok !== true
      || result?.admission_open !== true
      || String(result?.activation_epoch_id || '') !== id
      || String(result?.ready_commit_digest || '') !== digest
      || Number(result?.expires_at_unix_ms || 0) !== expiresAtUnixMs) {
      throw Object.assign(new Error('Coding MCP did not acknowledge the exact durable activation commit.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: id,
          ready_commit_digest: digest,
          observed: result || null
        }
      });
    }
    this.invalidateSnapshot();
    return result;
  }

  async closeActivationEpoch(activationEpochId, readyCommitDigest = '') {
    const id = String(activationEpochId || '').trim();
    if (!id) throw Object.assign(new Error('Activation epoch is required.'), { code: 'ACTIVATION_EPOCH_ID_REQUIRED' });
    const durable = this.activationEpochStatus();
    if (!durable.activation_epoch_id || durable.activation_epoch_id !== id) {
      throw Object.assign(new Error('The activation epoch is not the current durable epoch.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: id,
          current_activation_epoch_id: durable.activation_epoch_id || null
        }
      });
    }
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    const durableRecord = this.activationEpochStore?.current?.() || null;
    const digest = String(readyCommitDigest || durableRecord?.ready_commit_digest || '').trim();
    if (digest && !READY_COMMIT_DIGEST_PATTERN.test(digest)) {
      throw Object.assign(new Error('Activation ready commit digest is invalid.'), {
        code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID'
      });
    }
    // Closing is the rollback/fail-closed path after an admission transition.
    // Do not skip the exact control request merely because the persisted PID
    // projection is temporarily unavailable; the MCP endpoint can still be
    // reachable, and a mismatched process will reject the exact epoch without
    // being mutated.
    if (!token) return { ok: false, admission_open: false, activation_epoch_id: id, code: 'MCP_AUTH_UNAVAILABLE' };
    const result = await controlMcpActivation(settings.mcpPort, token, {
      action: 'close_epoch',
      activation_epoch_id: id,
      ...(digest ? { ready_commit_digest: digest } : {})
    });
    this.invalidateSnapshot();
    return result;
  }

  progress(step, percent, message) {
    this.emitProgress({ step, percent, message, time: new Date().toISOString() });
    this.log.info(message, { step, percent });
  }

  invalidateSnapshot() {
    this.snapshotCacheAt = 0;
  }

  publishSnapshot(snapshot, reason = 'refresh') {
    const signature = (value) => JSON.stringify(value ? { settings: value.settings, secrets: value.secrets, environment: value.environment, status: value.status } : null);
    const previous = signature(this.snapshotCache);
    this.snapshotCache = snapshot;
    this.snapshotCacheAt = Date.now();
    if (previous !== signature(snapshot)) this.emitStatus({ reason, snapshot });
    return snapshot;
  }

  endFailureStreak(now = Date.now()) {
    if (this.heartbeatFailureSince > 0) {
      this.accumulatedDowntimeMs += Math.max(0, now - this.heartbeatFailureSince);
      this.heartbeatFailureSince = 0;
    }
  }

  recoveryStatus() {
    return {
      recovering: this.recovering,
      failures: this.heartbeatFailures,
      failureKind: this.heartbeatFailureKind,
      recoveryAttempts: this.recoveryAttempts,
      nextRecoveryAt: this.nextRecoveryAt,
      recoveryBlocked: this.autoRecoveryBlocked,
      lastStartFailure: this.lastStartFailure,
      deferredRecoveryCount: this.deferredRecoveryCount,
      lastFailureAt: this.heartbeatFailureSince > 0 ? new Date(this.heartbeatFailureSince).toISOString() : null,
      lastRecoveryAt: this.lastRecoveryAt > 0 ? new Date(this.lastRecoveryAt).toISOString() : null,
      lastHealthyAt: this.lastHealthyAt > 0 ? new Date(this.lastHealthyAt).toISOString() : null,
      downtimeMs: this.accumulatedDowntimeMs,
      failureElapsedMs: this.heartbeatFailureSince > 0 ? Math.max(0, Date.now() - this.heartbeatFailureSince) : 0,
      mcpHealthFailureKind: this.lastMcpHealthFailure?.kind || null,
      mcpHealthFailureDeterministic: this.lastMcpHealthFailure?.deterministic === true
    };
  }

  async _probeGitStatus(target) {
    let status = { available: false, branch: null, head: null, head_short: null, dirty: null };
    try {
      const git = process.platform === 'win32' ? 'git.exe' : 'git';
      const result = await run(git, ['-C', target, 'status', '--porcelain=v2', '--branch', '--untracked-files=normal'], { allowFailure: true, timeoutMs: 2000 });
      if (result.code === 0) status = parseGitStatusPorcelainV2(result.stdout);
    } catch {}
    return status;
  }

  _refreshGitStatus(target) {
    if (this.gitStatusRefreshInFlight && this.gitStatusRefreshWorkspace === target) {
      return this.gitStatusRefreshInFlight;
    }
    let refresh;
    refresh = this._probeGitStatus(target)
      .catch(() => ({ available: false, branch: null, head: null, head_short: null, dirty: null }))
      .then((status) => {
        if (this.gitStatusRefreshInFlight === refresh && this.gitStatusRefreshWorkspace === target) {
          this.gitStatusCache = status;
          this.gitStatusCacheAt = Date.now();
          this.gitStatusWorkspace = target;
        }
        return status;
      })
      .finally(() => {
        if (this.gitStatusRefreshInFlight === refresh) {
          this.gitStatusRefreshInFlight = null;
          this.gitStatusRefreshWorkspace = '';
        }
      });
    this.gitStatusRefreshInFlight = refresh;
    this.gitStatusRefreshWorkspace = target;
    return refresh;
  }

  async gitStatus(workspace) {
    const target = String(workspace || '').trim();
    if (!target) return { available: false, branch: null, head: null, head_short: null, dirty: null };
    if (this.gitStatusCache && this.gitStatusWorkspace === target) {
      if (Date.now() - this.gitStatusCacheAt >= 10_000) void this._refreshGitStatus(target);
      return this.gitStatusCache;
    }
    return this._refreshGitStatus(target);
  }

  deviceProjection(settings, { mcpHealth = null, nativeAlive = false, tunnelRunning = false, git = null } = {}) {
    if (!this.device) return null;
    const role = executionRole(settings);
    return {
      scope: 'current_device_only',
      registry: 'local',
      device_id: this.device.deviceId,
      device_instance_id: this.device.deviceInstanceId,
      display_name: this.device.displayName,
      online: true,
      workspace: String(settings?.workspace || ''),
      execution_role: role,
      coding: {
        mcp_running: Boolean(mcpHealth),
        native_alive: Boolean(nativeAlive),
        // A stale direct-Tunnel setting must not make a central executor look
        // as if it exposes or manages a second OpenAI ingress.
        tunnel_running: role === 'direct_legacy' && Boolean(tunnelRunning),
        tunnel_managed: role === 'direct_legacy',
        tunnel_id: role === 'direct_legacy' ? (String(settings?.tunnelId || '') || null) : null,
        endpoint_device_instance_id: String(mcpHealth?.device_instance_id || '') || null,
        ownership: 'device_id'
      },
      git: git || { available: false, branch: null, head: null, head_short: null, dirty: null }
    };
  }

  centralRouteEvidence(settings, now = Date.now()) {
    if (executionRole(settings) !== 'central_executor') return null;
    return readControlPlaneRouteEvidence(this.paths, {
      expectedDeviceId: this.device?.deviceId || '',
      now
    });
  }

  async preflightLegacyDeviceMigration(probes = {}) {
    if (!this.device) return { required: false, nativePid: null, tunnelPid: null };
    const settings = this.settingsStore.load();
    const state = readJson(this.paths.stateFile(), {});
    const plan = { required: false, nativePid: null, tunnelPid: null };
    const listenerPid = probes.listenerPid || loopbackListenerPid;

    if (isAlive(Number(state.nativePid))) {
      const ownership = classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId);
      if (ownership === 'foreign') {
        throw Object.assign(new Error('Legacy migration refused because Coding MCP belongs to another device.'), { code: 'NATIVE_PROCESS_FOREIGN_DEVICE' });
      }
      if (ownership === 'legacy') {
        const token = await this.ensureToken();
        const healthProbe = probes.mcpHealth || readMcpHealth;
        const [health, ownerPid] = await Promise.all([
          healthProbe(settings.mcpPort, token, settings.workspace, ''),
          listenerPid(settings.mcpPort)
        ]);
        const exactState = state.nativeFingerprint === runtimeFingerprint(settings)
          && workspaceKey(state.nativeWorkspace || '') === workspaceKey(settings.workspace)
          && Number(state.nativePort) === Number(settings.mcpPort);
        const healthDeviceId = String(health?.device_id || '').toLowerCase();
        if (!exactState || Number(ownerPid) !== Number(state.nativePid) || !health
          || (healthDeviceId && healthDeviceId !== this.device.deviceId.toLowerCase())) {
          throw Object.assign(new Error('Legacy Coding MCP ownership could not be proven for this install.'), { code: 'NATIVE_LEGACY_MIGRATION_UNVERIFIED' });
        }
        plan.nativePid = Number(state.nativePid);
        plan.required = true;
      }
    }

    if (isAlive(Number(state.tunnelPid))) {
      const ownership = classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId);
      if (ownership === 'foreign') {
        throw Object.assign(new Error('Legacy migration refused because Coding Tunnel belongs to another device.'), { code: 'TUNNEL_PROCESS_FOREIGN_DEVICE' });
      }
      if (ownership === 'legacy') {
        const ownerPid = await listenerPid(settings.healthPort);
        let healthy = false;
        if (Number(ownerPid) === Number(state.tunnelPid)) {
          if (probes.tunnelHealth) healthy = await probes.tunnelHealth(settings, Number(state.tunnelPid));
          else {
            const result = await run(this.paths.tunnelExecutable(), [
              'health', '--port', String(settings.healthPort), '--pid', String(state.tunnelPid),
              '--require-control-plane-poll', '--json'
            ], { allowFailure: true, timeoutMs: 3000 });
            healthy = result.code === 0;
          }
        }
        if (!healthy) {
          throw Object.assign(new Error('Legacy Coding Tunnel ownership could not be proven for this install.'), { code: 'TUNNEL_LEGACY_MIGRATION_UNVERIFIED' });
        }
        plan.tunnelPid = Number(state.tunnelPid);
        plan.required = true;
      }
    }

    if (plan.required) {
      if (!this.secrets.get('runtimeApiKey')) throw Object.assign(new Error('Runtime API Key is required before legacy device migration.'), { code: 'LEGACY_MIGRATION_RUNTIME_KEY_MISSING' });
      if (!settings.tunnelId) throw Object.assign(new Error('Tunnel ID is required before legacy device migration.'), { code: 'LEGACY_MIGRATION_TUNNEL_ID_MISSING' });
    }
    return plan;
  }

  async applyLegacyDeviceMigration(plan) {
    if (!plan?.required || !this.device) return false;
    updateJsonAtomic(this.paths.stateFile(), (value) => {
      const next = { ...value };
      if (plan.nativePid) {
        if (Number(value.nativePid) !== Number(plan.nativePid)
          || classifyStoredDeviceOwner(value.nativeDeviceId, this.device.deviceId) !== 'legacy') {
          throw Object.assign(new Error('Coding MCP changed after legacy migration preflight.'), { code: 'LEGACY_MIGRATION_STATE_CHANGED' });
        }
        next.nativeDeviceId = this.device.deviceId;
        next.nativeDeviceInstanceId = this.device.deviceInstanceId;
      }
      if (plan.tunnelPid) {
        if (Number(value.tunnelPid) !== Number(plan.tunnelPid)
          || classifyStoredDeviceOwner(value.tunnelDeviceId, this.device.deviceId) !== 'legacy') {
          throw Object.assign(new Error('Coding Tunnel changed after legacy migration preflight.'), { code: 'LEGACY_MIGRATION_STATE_CHANGED' });
        }
        next.tunnelDeviceId = this.device.deviceId;
        next.tunnelDeviceInstanceId = this.device.deviceInstanceId;
      }
      return next;
    });
    this.log.info('Legacy primary runtime ownership proven; restarting with device identity', {
      nativePid: plan.nativePid || null,
      tunnelPid: plan.tunnelPid || null,
      deviceId: this.device.deviceId
    });
    await this.restart({ automatic: true });
    return true;
  }

  codingMcpRevisionStatus(options = {}) {
    try {
      if (typeof this.native?.revisionStatus === 'function') return this.native.revisionStatus(options);
    } catch { /* revision awareness must never take down lifecycle supervision */ }
    return {
      running_revision: null,
      disk_revision: null,
      update_pending: null,
      state: 'unavailable',
      error_code: 'REVISION_UNAVAILABLE'
    };
  }

  async ensureToken() {
    let token = this.secrets.get('mcpAuthToken');
    if (!token) {
      token = crypto.randomBytes(32).toString('base64url');
      this.secrets.set('mcpAuthToken', token);
    }
    return token;
  }

  p5A0Seed() {
    return String(this.secrets.get(P5_A0_SEED_SECRET) || '');
  }

  async prepareCodeActivation({ operationId, expiresAtUnixMs, allowAcceptancePending = false, sourceCheckpoint = null }) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token || !(await this.native.status(settings))) {
      throw Object.assign(new Error('Coding Tools MCP is not running under this Recovery Host.'), { code: 'COMPONENT_STOPPED' });
    }
    return controlMcpActivation(settings.mcpPort, token, {
      action: 'prepare',
      operation_id: operationId,
      expires_at_unix_ms: expiresAtUnixMs,
      workspace: settings.workspace,
      allow_acceptance_pending: allowAcceptancePending === true,
      ...(sourceCheckpoint && typeof sourceCheckpoint === 'object' ? { source_checkpoint: sourceCheckpoint } : {})
    });
  }

  async inspectCodeActivation(options = {}) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token || !(await this.native.status(settings))) {
      return { safe: true, code: 'COMPONENT_STOPPED', reason: 'coding_mcp_stopped', workspace: settings.workspace };
    }
    const result = await readMcpActivationPreflight(settings.mcpPort, token, options);
    if (workspaceKey(result.workspace) !== workspaceKey(settings.workspace)) {
      throw Object.assign(new Error('Coding MCP activation preflight returned another workspace.'), { code: 'WORKSPACE_MISMATCH' });
    }
    return result;
  }

  async verifyCodeActivation(operationId, sourceCheckpoint, allowAcceptancePending = false) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token) throw Object.assign(new Error('Coding Tools MCP is not running under this Recovery Host.'), { code: 'COMPONENT_STOPPED' });
    const result = await controlMcpActivation(settings.mcpPort, token, {
      action: 'verify',
      operation_id: String(operationId || ''),
      workspace: settings.workspace,
      source_checkpoint: sourceCheckpoint && typeof sourceCheckpoint === 'object' ? sourceCheckpoint : null,
      allow_acceptance_pending: allowAcceptancePending === true
    });
    if (workspaceKey(result.workspace) !== workspaceKey(settings.workspace)) {
      throw Object.assign(new Error('Coding MCP activation verification returned another workspace.'), { code: 'WORKSPACE_MISMATCH' });
    }
    return result;
  }

  async currentMcpHealth(options = {}) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    const observation = token
      ? await readMcpHealthObservation(
        settings.mcpPort,
        token,
        settings.workspace,
        this.device?.deviceId || '',
        this.activationEpochId,
        options
      )
      : { health: null, failure: mcpHealthFailure('auth_token_missing') };
    this.lastMcpHealthFailure = observation.failure;
    return observation.health;
  }

  async controlPlaneReadOnlyWorkspaceContext(admission = {}) {
    // This method intentionally owns the local MCP token and attestation.  A
    // central node never receives either credential and cannot select a client
    // identity, tool name, or workspace path.
    const actionId = String(admission.action_id || '').trim();
    const attemptId = String(admission.attempt_id || '').trim();
    const policySha256 = String(admission.policy_sha256 || '').trim().toLowerCase();
    const facadeContract = admission.facade_contract;
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/.test(actionId)
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/.test(attemptId)
      || !/^[a-f0-9]{64}$/.test(policySha256)
      || admission.tool_name !== READ_ONLY_TOOL_NAME
      || !facadeContract
      || typeof facadeContract !== 'object'
      || Array.isArray(facadeContract)
      || Object.keys(facadeContract).sort().join(',') !== 'profile,schema_version,sha256'
      || !Number.isSafeInteger(facadeContract.schema_version)
      || facadeContract.schema_version < 1
      || typeof facadeContract.profile !== 'string'
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/.test(facadeContract.profile)
      || typeof facadeContract.sha256 !== 'string'
      || !/^[a-f0-9]{64}$/.test(facadeContract.sha256)) {
      throw Object.assign(new Error('Control-plane read-only bridge admission is invalid.'), {
        code: 'CONTROL_PLANE_BRIDGE_ADMISSION_INVALID'
      });
    }
    const settings = this.settingsStore.load();
    if (!normalizeWorkspacePath(settings.workspace)) {
      throw Object.assign(new Error('Control-plane bridge has no exact local workspace.'), {
        code: 'CONTROL_PLANE_BRIDGE_WORKSPACE_UNAVAILABLE'
      });
    }
    const token = this.secrets.get('mcpAuthToken');
    if (!token) {
      throw Object.assign(new Error('Coding Tools MCP authentication is unavailable.'), {
        code: 'MCP_AUTH_UNAVAILABLE'
      });
    }
    const health = await this.currentMcpHealth({ timeoutMs: CONTROL_PLANE_READ_ONLY_TIMEOUT_MS });
    if (!health?.ready || !health?.tool_contract?.sha256) {
      throw Object.assign(new Error('Coding Tools MCP is not ready for the control-plane read-only bridge.'), {
        code: 'CONTROL_PLANE_BRIDGE_RUNTIME_UNREADY'
      });
    }
    const attestation = this.connectorAttestationForHealth(health);
    const attestationValue = connectorAttestationHeader({
      secret: attestation.secret,
      clientId: BRIDGE_CLIENT_ID,
      clientType: BRIDGE_CLIENT_TYPE,
      activationEpochId: attestation.activationEpochId,
      processInstanceId: attestation.processInstanceId,
      serverInstanceId: attestation.serverInstanceId,
      contractSha256: attestation.contractSha256
    });
    const requestFingerprint = controlPlaneBridgeDigest({
      action_id: actionId,
      attempt_id: attemptId,
      policy_sha256: policySha256,
      facade_contract: facadeContract
    });
    const body = JSON.stringify({
      jsonrpc: '2.0',
      id: `control-plane-read-only-${requestFingerprint.slice(0, 24)}`,
      method: 'tools/call',
      params: {
        name: READ_ONLY_TOOL_NAME,
        arguments: { ...READ_ONLY_ARGUMENTS },
        _meta: {
          'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': {
            name: 'coding-tools-control-plane-read-only-bridge',
            version: '1'
          }
        }
      }
    });
    return new Promise((resolve, reject) => {
      const request = http.request({
        host: '127.0.0.1',
        port: settings.mcpPort,
        path: '/mcp',
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
          'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': 'tools/call',
          'Mcp-Name': READ_ONLY_TOOL_NAME,
          'X-Coding-Tools-Client-Id': BRIDGE_CLIENT_ID,
          'X-Coding-Tools-Client-Type': BRIDGE_CLIENT_TYPE,
          [CONNECTOR_ATTESTATION_HEADER]: attestationValue
        },
        timeout: CONTROL_PLANE_READ_ONLY_TIMEOUT_MS
      }, (response) => {
        let responseBody = '';
        response.setEncoding('utf8');
        response.on('data', (chunk) => {
          if (responseBody.length <= 1024 * 1024) responseBody += chunk;
        });
        response.on('end', () => {
          let parsed;
          try { parsed = responseBody ? JSON.parse(responseBody) : {}; }
          catch {
            reject(Object.assign(new Error('Coding Tools MCP returned invalid JSON for the control-plane bridge.'), {
              code: 'CONTROL_PLANE_BRIDGE_RESPONSE_INVALID'
            }));
            return;
          }
          const structured = parsed?.result?.structuredContent || parsed?.result || null;
          const errorMessage = parsed?.error?.message
            || (parsed?.result?.isError ? structured?.error?.message || parsed?.result?.content?.[0]?.text : '');
          if (Number(response.statusCode || 0) !== 200 || errorMessage) {
            reject(Object.assign(new Error(String(errorMessage || `Coding Tools MCP rejected the control-plane bridge (HTTP ${response.statusCode}).`)), {
              code: 'CONTROL_PLANE_BRIDGE_MCP_REJECTED'
            }));
            return;
          }
          const workspace = normalizeWorkspacePath(structured?.workspace);
          if (!workspace || workspaceKey(workspace) !== workspaceKey(settings.workspace)) {
            reject(Object.assign(new Error('Coding Tools MCP returned a workspace outside the local bridge policy target.'), {
              code: 'CONTROL_PLANE_BRIDGE_WORKSPACE_MISMATCH'
            }));
            return;
          }
          let workspaceSummary;
          try {
            workspaceSummary = compactWorkspaceSummary(structured);
          } catch (error) {
            reject(Object.assign(new Error('Coding Tools MCP returned an unsafe workspace relay summary.'), {
              code: error?.code || 'CONTROL_PLANE_BRIDGE_RESULT_INVALID'
            }));
            return;
          }
          const localHandle = `cp_ro_${controlPlaneBridgeDigest({
            policy_sha256: policySha256,
            action_id: actionId,
            attempt_id: attemptId,
            process_instance_id: attestation.processInstanceId,
            server_instance_id: attestation.serverInstanceId,
            contract_sha256: attestation.contractSha256,
            facade_contract: facadeContract
          }).slice(0, 48)}`;
          resolve({
            schema_version: 1,
            operation_kind: 'control_plane_read_only_workspace_context',
            local_handle: localHandle,
            action_id: actionId,
            attempt_id: attemptId,
            workspace_accessed: true,
            actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
            policy_sha256: policySha256,
            facade_contract: {
              schema_version: facadeContract.schema_version,
              profile: facadeContract.profile,
              sha256: facadeContract.sha256
            },
            runtime_identity: {
              // This is the result contract consumed by Recovery Host and the
              // descriptor-hiding node bridge.  Keep the field names aligned
              // with that per-action contract; ``mcp_*`` names belong to the
              // separate identity-observation projection.
              process_instance_id: attestation.processInstanceId,
              server_instance_id: attestation.serverInstanceId,
              activation_epoch_id: attestation.activationEpochId,
              tool_contract_sha256: attestation.contractSha256
            },
            workspace_summary: workspaceSummary,
            workspace_summary_sha256: workspaceSummaryDigest(workspaceSummary),
            response_sha256: controlPlaneBridgeDigest(structured)
          });
        });
      });
      request.on('timeout', () => request.destroy(Object.assign(
        new Error('Control-plane read-only bridge timed out.'),
        { code: 'CONTROL_PLANE_BRIDGE_TIMEOUT' }
      )));
      request.on('error', (error) => reject(Object.assign(error, {
        code: error.code || 'CONTROL_PLANE_BRIDGE_TRANSPORT_FAILED'
      })));
      request.end(body);
    });
  }

  async recordExecutionControlCenterProgress(observation = {}) {
    const runId = String(observation.run_id || observation.runId || '').trim().toLowerCase();
    const waveId = String(observation.wave_id || observation.waveId || '').trim().toLowerCase();
    const snapshotFingerprint = String(
      observation.snapshot_fingerprint || observation.snapshotFingerprint || ''
    ).trim().toLowerCase();
    if (!EOCL_EXACT_ID_PATTERN.test(runId)
      || !EOCL_EXACT_ID_PATTERN.test(waveId)
      || !READY_COMMIT_DIGEST_PATTERN.test(snapshotFingerprint)) {
      throw Object.assign(new Error('Execution Control Center observation identity is invalid.'), {
        code: 'CONTROL_CENTER_OBSERVATION_INVALID'
      });
    }
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token) {
      throw Object.assign(new Error('Coding Tools MCP authentication is unavailable.'), {
        code: 'MCP_AUTH_UNAVAILABLE'
      });
    }
    const health = await this.currentMcpHealth({ timeoutMs: MCP_HEALTH_TIMEOUT_MS });
    if (!health?.ready || !health?.tool_contract?.sha256) {
      throw Object.assign(new Error('Coding Tools MCP health identity is unavailable.'), {
        code: 'ORCHESTRATION_STATE_UNCERTAIN'
      });
    }
    const attestation = this.connectorAttestationForHealth(health);
    const attestationValue = connectorAttestationHeader({
      secret: attestation.secret,
      clientId: 'electron-control-center',
      clientType: 'electron',
      activationEpochId: attestation.activationEpochId,
      processInstanceId: attestation.processInstanceId,
      serverInstanceId: attestation.serverInstanceId,
      contractSha256: attestation.contractSha256
    });
    const body = JSON.stringify({
      jsonrpc: '2.0',
      id: `control-center-observation-${snapshotFingerprint.slice(0, 16)}`,
      method: 'tools/call',
      params: {
        name: 'task_control',
        arguments: {
          action: 'observation',
          run_id: runId,
          wave_id: waveId,
          observation_span: {
            span_id: `execution-control-center:${snapshotFingerprint}`,
            stage: 'report_visible',
            source: 'electron_execution_control_center',
            measurement: 'observed_control_center_progress',
            clock_domain: `execution-control-center:${snapshotFingerprint}`,
            start_ms: 0,
            end_ms: 0,
            observer_plane: 'execution_control_center'
          }
        },
        _meta: {
          'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-control-center', version: '1' }
        }
      }
    });
    return new Promise((resolve, reject) => {
      const request = http.request({
        host: '127.0.0.1',
        port: settings.mcpPort,
        path: '/mcp',
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
          'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': 'tools/call',
          'Mcp-Name': 'task_control',
          'X-Coding-Tools-Client-Id': 'electron-control-center',
          'X-Coding-Tools-Client-Type': 'electron',
          [CONNECTOR_ATTESTATION_HEADER]: attestationValue
        },
        timeout: MCP_HEALTH_TIMEOUT_MS
      }, (response) => {
        let responseBody = '';
        response.setEncoding('utf8');
        response.on('data', (chunk) => { if (responseBody.length < 1024 * 1024) responseBody += chunk; });
        response.on('end', () => {
          let parsed;
          try { parsed = responseBody ? JSON.parse(responseBody) : {}; }
          catch {
            reject(Object.assign(new Error('Coding Tools MCP returned invalid JSON for the Control Center observation.'), {
              code: 'CONTROL_CENTER_OBSERVATION_RESPONSE_INVALID'
            }));
            return;
          }
          const structured = parsed?.result?.structuredContent || parsed?.result || null;
          const errorMessage = parsed?.error?.message
            || (parsed?.result?.isError ? structured?.error?.message || parsed?.result?.content?.[0]?.text : '');
          if (Number(response.statusCode || 0) !== 200 || errorMessage) {
            reject(Object.assign(new Error(String(errorMessage || `Coding Tools MCP rejected the Control Center observation (HTTP ${response.statusCode}).`)), {
              code: 'CONTROL_CENTER_OBSERVATION_REJECTED'
            }));
            return;
          }
          if (!structured?.control_center_receipt) {
            reject(Object.assign(new Error('Coding Tools MCP did not return an attested Control Center receipt.'), {
              code: 'CONTROL_CENTER_OBSERVATION_NOT_ATTESTED'
            }));
            return;
          }
          resolve(structured);
        });
      });
      request.on('timeout', () => request.destroy(Object.assign(
        new Error('Execution Control Center observation timed out.'),
        { code: 'CONTROL_CENTER_OBSERVATION_TIMEOUT' }
      )));
      request.on('error', (error) => reject(Object.assign(error, {
        code: error.code || 'CONTROL_CENTER_OBSERVATION_TRANSPORT_FAILED'
      })));
      request.end(body);
    });
  }

  async cancelCodeActivation(operationId, { strict = false } = {}) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token) {
      if (strict) throw Object.assign(new Error('Coding Tools MCP activation fence could not be reached.'), { code: 'ACTIVATION_FENCE_RELEASE_FAILED' });
      return false;
    }
    try {
      const result = await controlMcpActivation(settings.mcpPort, token, { action: 'cancel', operation_id: operationId });
      if (result.cancelled === true) return true;
      if (strict) throw Object.assign(new Error('Coding Tools MCP did not confirm activation fence release.'), { code: 'ACTIVATION_FENCE_RELEASE_FAILED' });
      return false;
    } catch (error) {
      if (strict) throw Object.assign(error, { code: String(error?.code || 'ACTIVATION_FENCE_RELEASE_FAILED') });
      return false;
    }
  }

  async activateCodingMcpUpdate(expectedRevision, options = {}) {
    // A controlled source/revision activation is a full-system transaction in
    // the production Recovery Host.  Keep an explicit private bypass for the
    // coordinator's legacy/unit harnesses, but never let a public direct call
    // silently preserve Tunnel/UI/Recovery processes at an old epoch.
    if (options._fullCleanInternal !== true
      && options.automatic !== true
      && options.mode !== 'soft_recovery'
      && this.fullCleanActivation?.restart) {
      return this.fullCleanActivation.restart({
        ...options,
        expectedDiskRevision: expectedRevision,
        reason: options.reason || 'coding_mcp_revision_activation'
      });
    }
    const launchActivationEpochId = String(options.activationEpochId || this.activationEpochId || '').trim();
    this.assertMcpReplacementAllowed({
      activationEpochId: launchActivationEpochId,
      operation: 'coding_mcp_revision_activation'
    });
    // Do not change the shared health identity for a call that cannot acquire
    // lifecycle ownership. There are no awaits between this check, binding,
    // and setting busy, so another local lifecycle call cannot interleave.
    if (this.busy || this.recovering) {
      throw Object.assign(new Error('Runtime lifecycle is already busy.'), { code: 'RUNTIME_BUSY' });
    }
    // Bind an explicitly supplied epoch only after the durable replacement
    // guard has accepted it.  This keeps the health/liveness probes and the
    // child launch on one exact epoch even when a Recovery Host instance was
    // reconstructed with a stale or empty in-memory binding.
    if (launchActivationEpochId && launchActivationEpochId !== this.activationEpochId) {
      this.setActivationEpoch(launchActivationEpochId);
    }
    // Soft recovery must never silently load source bytes from a newer
    // revision under the old activation epoch. Check continuity before any
    // stop/spawn mutation; a mismatch is a typed UPDATE_INCOMPLETE refusal and
    // leaves the existing runtime state untouched for an explicit full-clean
    // activation.
    if (options.automatic === true || options.mode === 'soft_recovery') {
      this.assertSoftRecoveryAllowed();
      this.assertActivationRevisionContinuity();
    }
    this.busy = true;
    let replacementStarted = false;
    try {
      const expiresAtUnixMs = Number(options.expiresAtUnixMs || 0);
      const settings = this.settingsStore.load();
      this.validate(settings);
      const centralExecutor = executionRole(settings) === 'central_executor';
      const token = await this.ensureToken();
      const diskRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      if (diskRevision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP source revision changed before activation.'), { code: 'REVISION_CHANGED' });
      }
      const oldState = readJson(this.paths.stateFile(), {});
      const oldHealth = await this.currentMcpHealth();
      if (!oldHealth) throw Object.assign(new Error('Coding MCP health identity is unavailable.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
      // Managed Coding Tunnel attestation is bound to the exact MCP
      // process/server tuple and secret. Resolve every prerequisite before
      // stopping MCP, so the component-scoped fallback either refreshes that
      // dependent Tunnel or refuses without mutation.
      let tunnelLaunch = null;
      if (String(settings.tunnelId || '').trim()) {
        const runtimeApiKey = this.secrets.get('runtimeApiKey');
        if (!runtimeApiKey) {
          throw Object.assign(new Error('Coding Tunnel attestation cannot be rebound without the Runtime API Key.'), {
            code: 'CONNECTOR_ATTESTATION_REBIND_UNAVAILABLE'
          });
        }
        const proxy = await resolveProxy(settings);
        if (settings.proxyMode === 'manual' && !proxy.reachable) {
          throw Object.assign(new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}.`), {
            code: 'CONNECTOR_ATTESTATION_REBIND_UNAVAILABLE'
          });
        }
        tunnelLaunch = { runtimeApiKey, proxy };
      }
      assertActivationDeadline(expiresAtUnixMs, 'before_native_stop', false);
      await this.native.stop();
      assertActivationDeadline(expiresAtUnixMs, 'before_native_start', true);
      const connectorAttestationSecret = this.rotateConnectorAttestationSecret();
      const started = await this.native.start(settings, token, this.progress.bind(this), {
        expectedCodeRevision: expectedRevision,
        expiresAtUnixMs,
        activationProcessMutated: true,
        p5Seed: this.p5A0Seed(),
        activationEpochId: launchActivationEpochId,
        activationGate: launchActivationEpochId ? ACTIVATION_GATE_CLOSED : '',
        connectorAttestationSecret
      });
      replacementStarted = true;
      let health = null;
      for (let index = 0; index < 35; index += 1) {
        health = await this.currentMcpHealth();
        if (health?.code_revision === expectedRevision) break;
        if (!(await this.native.status(settings, { activationEpochId: launchActivationEpochId }))) {
          throw Object.assign(new Error('Coding MCP exited during activation.'), { code: 'ACTIVATION_HEALTH_FAILED' });
        }
        await wait(1000);
      }
      if (!health || health.code_revision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP did not report the expected code revision after restart.'), { code: 'REVISION_VERIFICATION_FAILED' });
      }
      const oldProcessInstanceId = String(oldHealth.process_instance_id || '');
      const newProcessInstanceId = String(health.process_instance_id || '');
      const oldServerInstanceId = String(oldHealth.instance_id || '');
      const newServerInstanceId = String(health.instance_id || '');
      if (!oldProcessInstanceId || !newProcessInstanceId || oldProcessInstanceId === newProcessInstanceId
        || !oldServerInstanceId || !newServerInstanceId || oldServerInstanceId === newServerInstanceId) {
        throw Object.assign(new Error('Coding MCP restart did not produce a new verified process identity.'), { code: 'ACTIVATION_IDENTITY_UNCHANGED' });
      }
      const verifiedDiskRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      if (verifiedDiskRevision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP source revision changed while activation was in progress.'), {
          code: 'REVISION_CHANGED_DURING_ACTIVATION',
          details: { expected_revision: expectedRevision, disk_revision: verifiedDiskRevision }
        });
      }
      // The Recovery Host must retain an exact binding for every central MCP
      // it owns. A central executor does not launch a node Tunnel, but its
      // local read-only bridge still authenticates to loopback MCP with this
      // binding. Preserve the legacy no-Tunnel direct activation path, which
      // intentionally does not require a connector identity.
      const connectorAttestation = (centralExecutor || tunnelLaunch)
        ? this.connectorAttestationForHealth(health, {
          establish: true,
          secret: connectorAttestationSecret
        })
        : null;
      let tunnelStarted = null;
      if (tunnelLaunch) {
        tunnelStarted = await this.tunnel.start(
          { ...settings, effectiveProxyUrl: tunnelLaunch.proxy.resolvedUrl },
          tunnelLaunch.runtimeApiKey,
          token,
          this.progress.bind(this),
          {
            activationEpochId: launchActivationEpochId,
            connectorAttestation
          }
        );
      }
      const currentState = readJson(this.paths.stateFile(), {});
      this.invalidateSnapshot();
      return {
        old_instance_id: oldProcessInstanceId,
        new_instance_id: newProcessInstanceId,
        old_server_instance_id: oldServerInstanceId,
        new_server_instance_id: newServerInstanceId,
        old_supervisor_instance_id: String(oldState.nativeInstanceId || '') || null,
        new_supervisor_instance_id: String(started.instanceId || '') || null,
        old_revision: String(oldState.nativeCodeRevision || oldHealth.code_revision || '') || null,
        new_revision: health.code_revision,
        health_verified: true,
        disk_revision_verified: true,
        old_tunnel_pid: Number(oldState.tunnelPid || 0) || null,
        tunnel_pid: Number(currentState.tunnelPid || tunnelStarted?.pid || 0) || null,
        tunnel_preserved: false,
        tunnel_attestation_refreshed: Boolean(tunnelLaunch)
      };
    } catch (error) {
      if (replacementStarted) await this.native.stop().catch(() => false);
      throw error;
    } finally {
      this.busy = false;
    }
  }

  isManuallyStopped() {
    return readJson(this.paths.stateFile(), {}).manualStop === true;
  }

  setManualStop(value) {
    updateJsonAtomic(this.paths.stateFile(), (state) => ({
      ...state,
      manualStop: Boolean(value),
      intentChangedAt: new Date().toISOString()
    }));
  }

  connectorContractStatus(toolContract, discovery = null, contact = null, activationBootstrap = null, runtimeIdentity = null) {
    const nowUnixMs = Date.now();
    const currentSha256 = String(toolContract?.sha256 || '').trim();
    const activationEpochId = String(this.activationEpochId || '').trim();
    const schemaVersion = Number(toolContract?.schema_version || 0);
    const profile = String(toolContract?.profile || '').trim();
    const compatiblePredecessors = new Set(
      (Array.isArray(toolContract?.compatible_predecessor_sha256) ? toolContract.compatible_predecessor_sha256 : [])
        .map((value) => String(value || '').trim().toLowerCase())
        .filter((value) => /^[0-9a-f]{64}$/.test(value))
    );
    const runtimeState = readJson(this.paths.stateFile(), {});
    const acknowledgedSha256 = String(runtimeState.chatgptToolContractSha256 || '').trim();
    const acknowledgedSchemaVersion = Number(runtimeState.chatgptToolContractSchemaVersion || 0);
    const acknowledgedProfile = String(runtimeState.chatgptToolContractProfile || '').trim();
    const rediscoveredSha256 = String(discovery?.contract_sha256 || '').trim();
    const observedAt = String(discovery?.observed_at || '').trim();
    const observedAtUnixMs = Date.parse(observedAt);
    const observedAtValid = Boolean(observedAt && Number.isFinite(observedAtUnixMs));
    const observedAtCurrent = Boolean(
      observedAtValid && observedAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS
    );
    const discoveryProcessInstanceId = String(discovery?.process_instance_id || '').trim();
    const discoveryServerInstanceId = String(discovery?.server_instance_id || '').trim();
    const expectedProcessInstanceId = String(runtimeIdentity?.process_instance_id || '').trim();
    const expectedServerInstanceId = String(runtimeIdentity?.instance_id || runtimeIdentity?.server_instance_id || '').trim();
    const expectedActivationEpochId = String(runtimeIdentity?.activation_epoch_id || '').trim();
    // Detached status helpers remain backwards-compatible for diagnostics,
    // while every live projection supplies the health identity and therefore
    // refuses to display a receipt from another process/server tuple.
    const runtimeIdentityMatches = (processInstanceId, serverInstanceId, epochId = '') => Boolean(
      !runtimeIdentity
      || (
        expectedProcessInstanceId
        && expectedServerInstanceId
        && processInstanceId === expectedProcessInstanceId
        && serverInstanceId === expectedServerInstanceId
        && (!expectedActivationEpochId || epochId === expectedActivationEpochId)
      )
    );
    const rediscovered = Boolean(
      currentSha256
      && discovery?.current_contract_observed === true
      && String(discovery?.identity_source || '').trim() === 'attested_transport'
      && discovery?.attestation_verified === true
      && rediscoveredSha256 === currentSha256
      && (!activationEpochId
        || String(discovery?.activation_epoch_id || '').trim() === activationEpochId)
      && discoveryProcessInstanceId
      && discoveryServerInstanceId
      && runtimeIdentityMatches(
        discoveryProcessInstanceId,
        discoveryServerInstanceId,
        String(discovery?.activation_epoch_id || '').trim()
      )
      && observedAtCurrent
    );
    const contractChanged = Boolean(currentSha256 && currentSha256 !== acknowledgedSha256);
    const contactSha256 = String(contact?.contract_sha256 || '').trim();
    const contactObservedAt = String(contact?.observed_at || '').trim();
    const contactObservedAtUnixMs = Date.parse(contactObservedAt);
    const contactObservedAtValid = Boolean(contactObservedAt && Number.isFinite(contactObservedAtUnixMs));
    const contactCurrent = Boolean(
      currentSha256
      && contact?.current_contract_contact === true
      && String(contact?.identity_source || '').trim() === 'attested_transport'
      && contact?.attestation_verified === true
      && String(contact?.method || '') === 'tools/call'
      && contactSha256 === currentSha256
      && contactObservedAtValid
      && contactObservedAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS
      && String(contact?.process_instance_id || '').trim()
      && String(contact?.server_instance_id || '').trim()
      && runtimeIdentityMatches(
        String(contact?.process_instance_id || '').trim(),
        String(contact?.server_instance_id || '').trim(),
        String(contact?.activation_epoch_id || '').trim()
      )
    );
    const bootstrapObservedAt = String(activationBootstrap?.observed_at || '').trim();
    const bootstrapObservedAtUnixMs = Date.parse(bootstrapObservedAt);
    const bootstrapObservedAtValid = Boolean(bootstrapObservedAt && Number.isFinite(bootstrapObservedAtUnixMs));
    const bootstrapCurrent = Boolean(
      currentSha256
      && activationEpochId
      && activationBootstrap?.current_contract_contact === true
      && String(activationBootstrap?.identity_source || '').trim() === 'attested_transport'
      && activationBootstrap?.attestation_verified === true
      && String(activationBootstrap?.method || '') === 'tools/call'
      && String(activationBootstrap?.tool_name || '') === 'workspace_context'
      && String(activationBootstrap?.client_type || '') === 'chatweb'
      && String(activationBootstrap?.client_id || '').trim()
      && activationBootstrap?.workspace_accessed === false
      && String(activationBootstrap?.contract_sha256 || '').trim() === currentSha256
      && String(activationBootstrap?.activation_epoch_id || '').trim()
        === activationEpochId
      && bootstrapObservedAtValid
      && bootstrapObservedAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS
      && String(activationBootstrap?.process_instance_id || '').trim()
      && String(activationBootstrap?.server_instance_id || '').trim()
      && runtimeIdentityMatches(
        String(activationBootstrap?.process_instance_id || '').trim(),
        String(activationBootstrap?.server_instance_id || '').trim(),
        String(activationBootstrap?.activation_epoch_id || '').trim()
      )
    );
    const acknowledgedBoundaryKnown = acknowledgedSchemaVersion > 0 && Boolean(acknowledgedProfile);
    const sameCompatibilityBoundary = Boolean(
      !acknowledgedBoundaryKnown
      || (
        schemaVersion > 0
        && profile
        && acknowledgedSchemaVersion === schemaVersion
        && acknowledgedProfile === profile
      )
    );
    const declaredCompatiblePredecessor = Boolean(
      contractChanged
      && acknowledgedSha256
      && compatiblePredecessors.has(acknowledgedSha256.toLowerCase())
    );
    const compatibilityEligible = Boolean(
      contractChanged
      && !rediscovered
      && declaredCompatiblePredecessor
      && sameCompatibilityBoundary
      && (contactCurrent || bootstrapCurrent)
    );
    const sameContractBootstrapEligible = Boolean(
      !contractChanged
      && currentSha256
      && acknowledgedSha256 === currentSha256
      && sameCompatibilityBoundary
      && bootstrapCurrent
    );
    const storedCompatibilityPredecessor = String(
      runtimeState.chatgptToolContractCompatibilityPredecessorSha256 || ''
    ).trim().toLowerCase();
    const storedCompatibilitySource = String(runtimeState.chatgptToolContractCompatibilitySource || '').trim();
    const storedCompatibilityAt = String(runtimeState.chatgptToolContractCompatibilityAt || '').trim();
    const storedCompatibilityPredecessorValid = storedCompatibilitySource === 'exact_current_contract_activation_bootstrap'
      ? storedCompatibilityPredecessor === currentSha256.toLowerCase()
      : (storedCompatibilitySource === 'declared_exact_predecessor_activation_bootstrap'
        && compatiblePredecessors.has(storedCompatibilityPredecessor));
    const compatibilityAcknowledged = Boolean(
      !contractChanged
      && !rediscovered
      && bootstrapCurrent
      && storedCompatibilityPredecessorValid
      && storedCompatibilityAt === bootstrapObservedAt
      && String(runtimeState.chatgptToolContractCompatibilityContactSha256 || '').trim() === currentSha256
      && String(runtimeState.chatgptToolContractCompatibilityProcessInstanceId || '').trim()
        === String(activationBootstrap?.process_instance_id || '').trim()
      && String(runtimeState.chatgptToolContractCompatibilityServerInstanceId || '').trim()
        === String(activationBootstrap?.server_instance_id || '').trim()
      && String(runtimeState.chatgptToolContractCompatibilityActivationEpochId || '').trim()
        === activationEpochId
    );
    let contractState = 'UNAVAILABLE';
    if (currentSha256) {
      if (!contractChanged) {
        contractState = rediscovered ? 'CURRENT_ACKNOWLEDGED'
          : compatibilityAcknowledged ? 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
            : sameContractBootstrapEligible ? 'UNCHANGED_COMPATIBLE_NEEDS_ACK'
              : 'UNCHANGED_ACKNOWLEDGED';
      } else if (rediscovered) {
        contractState = 'CHANGED_DISCOVERED_NEEDS_ACK';
      } else if (compatibilityEligible) {
        contractState = 'CHANGED_COMPATIBLE_NEEDS_ACK';
      } else {
        contractState = 'CHANGED_NEEDS_DISCOVERY';
      }
    }
    return {
      available: Boolean(currentSha256),
      schemaVersion,
      profile,
      currentSha256,
      acknowledgedSha256,
      acknowledgedSchemaVersion,
      acknowledgedProfile,
      rediscovered,
      rediscoveredSha256,
      rediscoveredAt: rediscovered ? observedAt : null,
      contractState,
      contractChanged,
      backwardCompatible: compatibilityEligible,
      compatibilityEligible,
      sameContractBootstrapEligible,
      compatibilityAcknowledged,
      compatibilitySource: compatibilityEligible
        ? (bootstrapCurrent
          ? 'declared_exact_predecessor_activation_bootstrap'
          : 'declared_exact_predecessor_live_contact')
        : sameContractBootstrapEligible ? 'exact_current_contract_activation_bootstrap'
        : compatibilityAcknowledged ? storedCompatibilitySource : null,
      compatibilityAcknowledgedAt: compatibilityAcknowledged ? storedCompatibilityAt : null,
      compatibilityMetadataBackfillPending: Boolean(compatibilityEligible && !acknowledgedBoundaryKnown),
      contactCurrent,
      contactSha256,
      contactObservedAt: contactCurrent ? contactObservedAt : null,
      contactProcessInstanceId: contactCurrent ? String(contact?.process_instance_id || '') : null,
      contactServerInstanceId: contactCurrent ? String(contact?.server_instance_id || '') : null,
      bootstrapCurrent,
      bootstrapObservedAt: bootstrapCurrent ? bootstrapObservedAt : null,
      bootstrapProcessInstanceId: bootstrapCurrent ? String(activationBootstrap?.process_instance_id || '') : null,
      bootstrapServerInstanceId: bootstrapCurrent ? String(activationBootstrap?.server_instance_id || '') : null,
      bootstrapActivationEpochId: bootstrapCurrent ? String(activationBootstrap?.activation_epoch_id || '') : null,
      // A changed exact SHA still requires real discovery unless this exact
      // server-declared predecessor has separate current-process ChatWeb contact.
      refreshRequired: Boolean(contractChanged && !rediscovered && !compatibilityEligible),
      acknowledgementPending: Boolean(
        (contractChanged && (rediscovered || compatibilityEligible))
        // A real current-process discovery is stronger than a retained
        // no-workspace compatibility bootstrap. Do not leave a fully
        // rediscovered matching contract pending merely because the previous
        // epoch also has bootstrap evidence that was never persisted as the
        // chosen acknowledgement mode.
        || (sameContractBootstrapEligible && !compatibilityAcknowledged && !rediscovered)
      )
    };
  }

  // Persist only a status that has already been validated against a complete
  // current health receipt by acknowledgeExactConnectorDiscovery().  Keeping
  // this write separate from the public hash/sync helpers prevents a caller
  // from manufacturing a strict-looking receipt out of an unbound
  // tools/list/contact fragment.
  _persistConnectorContractAcknowledgement(status) {
    if (!status || status.available !== true) {
      throw Object.assign(new Error('Coding Tools MCP chưa cung cấp tool contract fingerprint để xác nhận.'), {
        code: 'CONNECTOR_CONTRACT_UNAVAILABLE'
      });
    }
    if (!status.rediscovered && !status.compatibilityEligible && !status.sameContractBootstrapEligible) {
      throw Object.assign(new Error('ChatGPT chưa đọc lại tools/list và chưa có compatible cached-client receipt hợp lệ cho tool contract hiện tại.'), {
        code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
      });
    }
    updateJsonAtomic(this.paths.stateFile(), (state) => {
      const next = {
        ...state,
        chatgptToolContractSha256: status.currentSha256,
        chatgptToolContractSchemaVersion: status.schemaVersion,
        chatgptToolContractProfile: status.profile,
        chatgptToolContractAcknowledgedAt: new Date().toISOString()
      };
      if (status.rediscovered) {
        next.chatgptToolContractRediscoveredAt = status.rediscoveredAt;
        next.chatgptToolContractRediscoveredSha256 = status.currentSha256;
        delete next.chatgptToolContractCompatibilityAt;
        delete next.chatgptToolContractCompatibilitySource;
        delete next.chatgptToolContractCompatibilityPredecessorSha256;
        delete next.chatgptToolContractCompatibilityContactSha256;
        delete next.chatgptToolContractCompatibilityProcessInstanceId;
        delete next.chatgptToolContractCompatibilityServerInstanceId;
        delete next.chatgptToolContractCompatibilityActivationEpochId;
      } else {
        delete next.chatgptToolContractRediscoveredAt;
        delete next.chatgptToolContractRediscoveredSha256;
        next.chatgptToolContractCompatibilityAt = status.bootstrapCurrent
          ? status.bootstrapObservedAt : status.contactObservedAt;
        next.chatgptToolContractCompatibilitySource = status.compatibilitySource;
        next.chatgptToolContractCompatibilityPredecessorSha256 = status.contractChanged
          ? status.acknowledgedSha256 : status.currentSha256;
        next.chatgptToolContractCompatibilityContactSha256 = status.currentSha256;
        next.chatgptToolContractCompatibilityProcessInstanceId = status.bootstrapCurrent
          ? status.bootstrapProcessInstanceId : status.contactProcessInstanceId;
        next.chatgptToolContractCompatibilityServerInstanceId = status.bootstrapCurrent
          ? status.bootstrapServerInstanceId : status.contactServerInstanceId;
        if (status.bootstrapCurrent) {
          next.chatgptToolContractCompatibilityActivationEpochId = status.bootstrapActivationEpochId;
        } else {
          delete next.chatgptToolContractCompatibilityActivationEpochId;
        }
      }
      return next;
    });
  }

  acknowledgeConnectorContractHash(toolContract, discovery = null, contact = null, activationBootstrap = null) {
    const status = this.connectorContractStatus(toolContract, discovery, contact, activationBootstrap);
    if (!status.available) throw new Error('Coding Tools MCP chưa cung cấp tool contract fingerprint để xác nhận.');
    if (!status.contractChanged && (!status.sameContractBootstrapEligible || status.compatibilityAcknowledged)) return status;
    if (!status.rediscovered && !status.compatibilityEligible && !status.sameContractBootstrapEligible) {
      throw Object.assign(new Error('ChatGPT chưa đọc lại tools/list và chưa có compatible cached-client receipt hợp lệ cho tool contract hiện tại.'), {
        code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
      });
    }
    // This legacy helper intentionally has no health authority (ready,
    // activation epoch, process identity and server identity).  It may report
    // status, but it must never persist a pending acknowledgement.  The only
    // mutating path is acknowledgeExactConnectorDiscovery(health).
    throw Object.assign(new Error('Connector acknowledgement requires an exact current-process health receipt; use acknowledgeExactConnectorDiscovery().'), {
      code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
    });
  }

  connectorContractFreshness(health, contractStatus) {
    const nowUnixMs = Date.now();
    const currentSha256 = String(health?.tool_contract?.sha256 || '').trim();
    const processInstanceId = String(health?.process_instance_id || '').trim();
    const serverInstanceId = String(health?.instance_id || health?.server_instance_id || '').trim();
    const activationEpochId = String(health?.activation_epoch_id || '').trim();
    const baseReady = Boolean(
      health?.ready === true
      && READY_COMMIT_DIGEST_PATTERN.test(currentSha256.toLowerCase())
      && processInstanceId
      && serverInstanceId
      && activationEpochId
      && activationEpochId === String(this.activationEpochId || '').trim()
      && contractStatus?.available === true
      && contractStatus.currentSha256 === currentSha256
      && contractStatus.acknowledgedSha256 === currentSha256
      && contractStatus.refreshRequired === false
      && contractStatus.acknowledgementPending === false
      && contractStatus.contractChanged === false
    );
    if (!baseReady) return { ready: false, mode: null };

    const discovery = health.connector_tool_discovery;
    const rediscoveredAt = String(discovery?.observed_at || '').trim();
    const rediscoveredAtUnixMs = Date.parse(rediscoveredAt);
    if (contractStatus.contractState === 'CURRENT_ACKNOWLEDGED'
      && contractStatus.rediscovered === true
      && discovery?.current_contract_observed === true
      && String(discovery.identity_source || '').trim() === 'attested_transport'
      && discovery?.attestation_verified === true
      && String(discovery.contract_sha256 || '').trim() === currentSha256
      && String(discovery.process_instance_id || '').trim() === processInstanceId
      && String(discovery.server_instance_id || '').trim() === serverInstanceId
      && String(discovery.activation_epoch_id || '').trim() === activationEpochId
      && rediscoveredAt
      && rediscoveredAt === String(contractStatus.rediscoveredAt || '').trim()
      && Number.isFinite(rediscoveredAtUnixMs)
      && rediscoveredAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS) {
      return { ready: true, mode: 'current_process_discovery', observedAt: rediscoveredAt };
    }

    const bootstrap = health.connector_activation_bootstrap;
    const compatibilityAt = String(bootstrap?.observed_at || '').trim();
    const compatibilityAtUnixMs = Date.parse(compatibilityAt);
    if (contractStatus.contractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
      && contractStatus.compatibilityAcknowledged === true
      && contractStatus.bootstrapCurrent === true
      && bootstrap?.current_contract_contact === true
      && String(bootstrap.identity_source || '').trim() === 'attested_transport'
      && bootstrap?.attestation_verified === true
      && String(bootstrap.client_type || '') === 'chatweb'
      && String(bootstrap.client_id || '').trim()
      && String(bootstrap.method || '') === 'tools/call'
      && String(bootstrap.tool_name || '') === 'workspace_context'
      && bootstrap.workspace_accessed === false
      && String(bootstrap.contract_sha256 || '').trim() === currentSha256
      && String(bootstrap.process_instance_id || '').trim() === processInstanceId
      && String(bootstrap.server_instance_id || '').trim() === serverInstanceId
      && String(bootstrap.activation_epoch_id || '').trim() === activationEpochId
      && compatibilityAt
      && compatibilityAt === String(contractStatus.compatibilityAcknowledgedAt || '').trim()
      && Number.isFinite(compatibilityAtUnixMs)
      && compatibilityAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS) {
      return {
        ready: true,
        mode: 'compatible_activation_bootstrap',
        observedAt: compatibilityAt
      };
    }
    return { ready: false, mode: null };
  }

  acknowledgeExactConnectorDiscovery(health, { activationEpochId = '', nowUnixMs = Date.now() } = {}) {
    const expectedEpochId = String(activationEpochId || this.activationEpochId || '').trim();
    const observedEpochId = String(health?.activation_epoch_id || '').trim();
    const processInstanceId = String(health?.process_instance_id || '').trim();
    const serverInstanceId = String(health?.instance_id || health?.server_instance_id || '').trim();
    const contractSha256 = String(health?.tool_contract?.sha256 || '').trim().toLowerCase();
    const discovery = health?.connector_tool_discovery;
    const discoveryObservedAt = String(discovery?.observed_at || '').trim();
    const discoveryObservedAtUnixMs = Date.parse(discoveryObservedAt);
    const activationBootstrap = health?.connector_activation_bootstrap;
    const bootstrapObservedAt = String(activationBootstrap?.observed_at || '').trim();
    const bootstrapObservedAtUnixMs = Date.parse(bootstrapObservedAt);
    const baseExact = Boolean(
      health?.ready === true
      && expectedEpochId
      && observedEpochId === expectedEpochId
      && processInstanceId
      && serverInstanceId
      && READY_COMMIT_DIGEST_PATTERN.test(contractSha256)
      && Number.isSafeInteger(nowUnixMs) && nowUnixMs > 0
    );
    const exactDiscovery = Boolean(
      baseExact
      && discovery && typeof discovery === 'object' && !Array.isArray(discovery)
      && discovery.current_contract_observed === true
      && String(discovery.identity_source || '').trim() === 'attested_transport'
      && discovery.attestation_verified === true
      && String(discovery.contract_sha256 || '').trim().toLowerCase() === contractSha256
      && String(discovery.process_instance_id || '').trim() === processInstanceId
      && String(discovery.server_instance_id || '').trim() === serverInstanceId
      && String(discovery.activation_epoch_id || '').trim() === observedEpochId
      && Number.isFinite(discoveryObservedAtUnixMs)
      && discoveryObservedAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS
    );
    const exactCompatibilityBootstrap = Boolean(
      baseExact
      && activationBootstrap && typeof activationBootstrap === 'object' && !Array.isArray(activationBootstrap)
      && activationBootstrap.current_contract_contact === true
      && String(activationBootstrap.identity_source || '').trim() === 'attested_transport'
      && activationBootstrap.attestation_verified === true
      && String(activationBootstrap.client_type || '') === 'chatweb'
      && String(activationBootstrap.client_id || '').trim()
      && String(activationBootstrap.method || '') === 'tools/call'
      && String(activationBootstrap.tool_name || '') === 'workspace_context'
      && activationBootstrap.workspace_accessed === false
      && String(activationBootstrap.contract_sha256 || '').trim().toLowerCase() === contractSha256
      && String(activationBootstrap.process_instance_id || '').trim() === processInstanceId
      && String(activationBootstrap.server_instance_id || '').trim() === serverInstanceId
      && String(activationBootstrap.activation_epoch_id || '').trim() === expectedEpochId
      && Number.isFinite(bootstrapObservedAtUnixMs)
      && bootstrapObservedAtUnixMs <= nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS
    );
    if (!exactDiscovery && !exactCompatibilityBootstrap) {
      throw Object.assign(new Error('Connector acknowledgement requires exact current-process discovery or a no-workspace compatibility bootstrap for this activation epoch.'), {
        code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
      });
    }
    const before = this.connectorContractStatus(
      health.tool_contract,
      discovery,
      health.connector_client_contact,
      activationBootstrap,
      health
    );
    const alreadyCurrent = exactDiscovery
      ? before.contractState === 'CURRENT_ACKNOWLEDGED' && before.rediscovered === true
      : before.contractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
        && before.compatibilityAcknowledged === true;
    if (!before.acknowledgementPending && alreadyCurrent) return before;
    const eligibleState = exactDiscovery
      ? before.contractState === 'CHANGED_DISCOVERED_NEEDS_ACK' && before.rediscovered === true
      : ['CHANGED_COMPATIBLE_NEEDS_ACK', 'UNCHANGED_COMPATIBLE_NEEDS_ACK'].includes(before.contractState)
        && before.bootstrapCurrent === true;
    if (!eligibleState
      || before.refreshRequired !== false
      || before.acknowledgementPending !== true) {
      throw Object.assign(new Error('Connector contract is not eligible for exact current-process discovery/bootstrap acknowledgement.'), {
        code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
      });
    }
    this._persistConnectorContractAcknowledgement(before);
    const acknowledged = this.connectorContractStatus(
      health.tool_contract,
      discovery,
      health.connector_client_contact,
      activationBootstrap,
      health
    );
    const expectedState = exactDiscovery ? 'CURRENT_ACKNOWLEDGED' : 'CURRENT_COMPATIBLE_ACKNOWLEDGED';
    const freshnessCommitted = exactDiscovery
      ? acknowledged.rediscovered === true
      : acknowledged.compatibilityAcknowledged === true
        && acknowledged.bootstrapCurrent === true
        && acknowledged.compatibilityAcknowledgedAt === bootstrapObservedAt;
    if (acknowledged.contractState !== expectedState
      || acknowledged.currentSha256 !== contractSha256
      || acknowledged.acknowledgedSha256 !== contractSha256
      || !freshnessCommitted
      || acknowledged.refreshRequired !== false
      || acknowledged.acknowledgementPending !== false) {
      throw Object.assign(new Error('Connector acknowledgement did not commit the exact current contract receipt.'), {
        code: 'CONNECTOR_ACKNOWLEDGEMENT_INCOMPLETE'
      });
    }
    this.invalidateSnapshot();
    return acknowledged;
  }

  synchronizeConnectorContract(toolContract, discovery = null, contact = null, activationBootstrap = null) {
    const status = this.connectorContractStatus(toolContract, discovery, contact, activationBootstrap);
    if (!status.acknowledgementPending) return status;
    // Synchronization is retained as a read/status convenience for callers
    // that already have an acknowledged contract.  A pending state has no
    // complete health authority, so fail closed instead of persisting a
    // receipt assembled from detached connector evidence.
    throw Object.assign(new Error('Connector synchronization requires an exact current-process health receipt; use acknowledgeExactConnectorDiscovery().'), {
      code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
    });
  }

  async acknowledgeConnectorContract() {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    // Bind connector acknowledgement to the same process/activation epoch
    // that the orchestrator currently owns.  A persisted contract receipt or
    // a healthy MCP from the retired epoch must never be sufficient to open
    // the new activation gate.
    const health = token
      ? await readMcpHealth(
        settings.mcpPort,
        token,
        settings.workspace,
        this.device?.deviceId || '',
        this.activationEpochId || ''
      )
      : null;
    if (!health?.tool_contract) throw new Error('Coding Tools MCP chưa chạy hoặc chưa cung cấp tool contract fingerprint.');
    this.acknowledgeExactConnectorDiscovery(health, {
      activationEpochId: this.activationEpochId,
      nowUnixMs: Date.now()
    });
    this.invalidateSnapshot();
    return this.snapshot({ force: true, reason: 'connector-contract-acknowledged' });
  }

  pendingSupervisorRestartRequest() {
    if (this.busy || this.recovering) return null;
    const pendingFile = this.paths.supervisorRequestFile();
    const processingFile = `${pendingFile}.processing`;
    const settings = this.settingsStore.load();
    const now = Date.now();
    for (const file of [processingFile, pendingFile]) {
      const observation = readSupervisorRestartRequest(file, settings, now);
      if (observation.state === 'absent') continue;
      if (observation.state === 'unknown') {
        this.log.warn('Không thể đọc chắc chắn yêu cầu restart supervisor; giữ journal để fail closed', {
          file,
          code: observation.error?.code || 'SUPERVISOR_REQUEST_READ_UNCERTAIN'
        });
        return { uncertain: true, file, processing: file === processingFile };
      }
      if (observation.state === 'invalid') {
        fs.rmSync(file, { force: true });
        fs.rmSync(`${file}.bak`, { force: true });
        this.log.warn('Đã loại bỏ yêu cầu restart supervisor không hợp lệ hoặc đã hết hạn', {
          ticketId: observation.request?.ticket_id || '',
          workspace: observation.request?.workspace || ''
        });
        continue;
      }
      if (!observation.ready) return null;
      return {
        file,
        request: observation.request,
        processing: file === processingFile,
        pendingFile,
        processingFile
      };
    }
    return null;
  }

  claimSupervisorRestartRequest() {
    const pending = this.pendingSupervisorRestartRequest();
    if (!pending || pending.uncertain) return null;
    if (pending.processing) return pending;
    if (fs.existsSync(pending.processingFile)) return null;
    try {
      fs.renameSync(pending.file, pending.processingFile);
    } catch (error) {
      this.log.warn('Không thể claim durable supervisor restart journal; sẽ thử lại mà không xóa ticket', {
        file: pending.file,
        code: error?.code || 'SUPERVISOR_REQUEST_CLAIM_FAILED'
      });
      return null;
    }
    return { ...pending, file: pending.processingFile, processing: true };
  }

  finalizeSupervisorRestartRequest(claimed) {
    if (!claimed?.file) return;
    fs.rmSync(claimed.file, { force: true });
    fs.rmSync(`${claimed.file}.bak`, { force: true });
  }

  async serviceSupervisorRestartRequest() {
    const pending = this.claimSupervisorRestartRequest();
    if (!pending) return null;
    const ticketId = String(pending.request.ticket_id);
    this.log.info('Recovery Host supervisor đã nhận yêu cầu restart từ Coding Tools MCP', { ticketId });
    try {
      const health = await this.currentMcpHealth();
      const ticketContractSha256 = String(pending.request.tool_contract_sha256 || '').trim().toLowerCase();
      const healthContractSha256 = String(health?.tool_contract?.sha256 || '').trim().toLowerCase();
      if (!health
        || health.process_instance_id !== pending.request.process_instance_id
        || health.instance_id !== pending.request.server_instance_id
        || !READY_COMMIT_DIGEST_PATTERN.test(ticketContractSha256)
        || healthContractSha256 !== ticketContractSha256) {
        throw Object.assign(new Error('Supervisor restart ticket no longer matches the running MCP instance.'), { code: 'STALE_RESTART_TICKET' });
      }
      if (!this.fullCleanActivation || typeof this.fullCleanActivation.restart !== 'function') {
        throw Object.assign(new Error('Full clean activation is unavailable for the supervisor restart ticket.'), {
          code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE'
        });
      }
      const maintenanceRefresh = exactStaleRunMaintenanceReason(pending.request.reason);
      const maintenanceWorkspace = maintenanceRefresh
        ? String(pending.request.target_workspace || this.settingsStore.load().workspace || '')
        : '';
      if (!maintenanceRefresh && typeof this.resolveFullCleanSourceCheckpoint !== 'function') {
        throw Object.assign(new Error('The supervisor restart ticket has no Recovery Host accepted-code checkpoint authority.'), {
          code: 'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE'
        });
      }
      // Ordinary code/revision restarts resolve authority only from the current
      // authenticated Recovery Host closure. Exact stale-run maintenance is a
      // process refresh: it carries no source authority and FullCleanActivation's
      // stopped-runtime census/snapshot/hash-chain guards own that mutation.
      const sourceCheckpoint = maintenanceRefresh ? null : await this.resolveFullCleanSourceCheckpoint();
      const expectedRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      const result = await this.fullCleanActivation.restart({
        operationId: ticketId,
        ...(maintenanceRefresh
          ? { refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null }
          : { sourceCheckpoint }),
        expectedDiskRevision: expectedRevision,
        // The supervisor ticket expiry is only the fail-closed admission/claim
        // window. Once a fresh ticket has been claimed, FullCleanActivation
        // owns its separate bounded end-to-end deadline for handoff, cold
        // startup, connector readiness, and final postflight.
        allowAcceptancePending: pending.request.allow_acceptance_pending === true,
        reason: pending.request.reason || 'task_control_restart_runtime',
        ...(maintenanceRefresh ? { maintenanceWorkspace } : {})
      });
      const binding = this.activationEpochBinding(ticketId);
      if (!binding.known || !binding.bound) {
        throw Object.assign(new Error('Full-clean activation returned without a durable epoch bound to the supervisor operation.'), {
          code: 'ACTIVATION_EPOCH_BINDING_UNVERIFIED'
        });
      }
      this.finalizeSupervisorRestartRequest(pending);
      const ready = result?.full_clean_activation === true
        && result?.state === 'READY'
        && result?.admission_open === true
        && result?.fully_ready === true;
      return {
        ticketId,
        operationId: ticketId,
        status: ready ? 'completed' : 'accepted',
        component: 'full_system',
        activation_mode: maintenanceRefresh ? 'full_clean_refresh' : 'full_clean_activation',
        result
      };
    } catch (error) {
      // The MCP fence is installed before this deferred ticket is consumed.
      // If Recovery Host failed before FullCleanActivation could create a
      // durable epoch, release exactly this operation's fence so the old
      // process is not left draining until TTL.  Once an epoch is bound (even
      // FAILED/CLOSED), never reopen admission or cancel its operation fence;
      // the durable epoch is the source of truth and must remain fail-closed.
      const binding = this.activationEpochBinding(ticketId);
      const retryAfterToolReturn = String(error?.code || '') === 'RUNTIME_BUSY'
        && Date.now() < Number(pending.request.expires_at_unix_ms || 0);
      let requestFinalized = false;
      if (binding.known && binding.bound) {
        this.finalizeSupervisorRestartRequest(pending);
        requestFinalized = true;
      } else if (retryAfterToolReturn) {
        this.log?.info?.('Supervisor restart journal remains claimed until the initiating tool call leaves admission', {
          ticketId,
          code: 'RUNTIME_BUSY'
        });
      } else if (binding.known && !binding.bound) {
        try {
          const cancelled = await this.cancelCodeActivation(ticketId, { strict: true });
          if (cancelled === true || (cancelled === false && error?.code === 'STALE_RESTART_TICKET')) {
            this.finalizeSupervisorRestartRequest(pending);
            requestFinalized = true;
          }
        } catch (cleanupError) {
          this.log?.warn?.('Không thể giải phóng activation fence sau khi supervisor restart thất bại; giữ trạng thái fail-closed', {
            ticketId,
            code: cleanupError?.code || 'ACTIVATION_FENCE_RELEASE_FAILED'
          });
        }
      } else if (!binding.known) {
        this.log?.warn?.('Không thể xác định durable activation epoch sau khi supervisor restart thất bại; không mở admission', {
          ticketId,
          reason: binding.reason || 'epoch_store_uncertain',
          code: binding.error_code || ''
        });
      }
      this.log.error(error.message, { stage: 'supervisor-restart-request', ticketId });
      return {
        ticketId,
        operationId: ticketId,
        status: retryAfterToolReturn ? 'deferred' : 'failed',
        activation_mode: 'full_clean_activation',
        request_retained: !requestFinalized,
        error: {
          code: String(error?.code || 'SUPERVISOR_RESTART_FAILED'),
          message: String(error?.message || error)
        }
      };
    }
  }

  validate(settings) {
    if (!settings.workspace || !fs.existsSync(settings.workspace)) throw new Error('Vui lòng chọn một thư mục làm việc hợp lệ.');
    validateRuntimeSettings(settings);
  }

  async start(options = {}) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ triển khai đang chạy.');
    const automatic = options.automatic === true;
    const launchActivationEpochId = String(options.activationEpochId || this.activationEpochId || '').trim();
    const normalizedActivationGate = normalizeActivationGate(launchActivationEpochId, options.activationGate);
    const durableEpoch = this.assertMcpReplacementAllowed({
      activationEpochId: launchActivationEpochId,
      operation: automatic ? 'automatic_runtime_start' : 'runtime_start'
    });
    if (durableEpoch.update_incomplete === true) {
      const internalReplacement = automatic
        && options.fullClean === true
        && normalizedActivationGate === ACTIVATION_GATE_CLOSED
        && launchActivationEpochId === String(durableEpoch.activation_epoch_id || '').trim();
      if (!internalReplacement) {
        throw Object.assign(new Error('Runtime activation is incomplete; only the epoch-bound closed-gate replacement may start processes.'), {
          code: 'UPDATE_INCOMPLETE',
          details: {
            activation_epoch_id: durableEpoch.activation_epoch_id || null,
            epoch_state: durableEpoch.epoch_state || durableEpoch.state || null,
            admission_open: false
          }
        });
      }
    }
    if (options.fullClean !== true) this.assertActivationRevisionContinuity();
    if (options.activationEpochId) this.setActivationEpoch(options.activationEpochId);
    if (!automatic) {
      this.autoRecoveryBlocked = false;
      this.lastStartFailure = '';
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
    }
    this.busy = true;
    try {
      const settings = this.settingsStore.load();
      this.validate(settings);
      const centralExecutor = executionRole(settings) === 'central_executor';
      // Central nodes own only their loopback MCP credential.  They must not
      // read a Runtime API Key or require a primary Tunnel ID: those belong to
      // the Ubuntu root ingress, not to a Windows/local executor.
      const runtimeApiKey = centralExecutor ? '' : this.secrets.get('runtimeApiKey');
      if (!centralExecutor && !runtimeApiKey) throw new Error('Vui lòng lưu Runtime API Key trong "Cấu hình triển khai" trước.');
      if (!centralExecutor && !settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
      const token = await this.ensureToken();

      this.progress('preflight', 8, 'Đang kiểm tra thư mục làm việc, môi trường chạy và cổng');
      const env = await this.environment.inspect(settings, { forceProxy: !centralExecutor });
      if (!centralExecutor && !env.tunnelClient.installed) throw new Error('Thiếu tệp thực thi OpenAI tunnel-client.');
      if (!env.python.installed) {
        throw new Error('Môi trường runtime portable chưa sẵn sàng, phiên bản phát triển cần Python 3.11+; bản phát hành sẽ tích hợp sẵn Python.');
      }

      let proxy = null;
      if (!centralExecutor) {
        this.progress('proxy-detect', 14, 'Đang kiểm tra kết nối trực tiếp, Proxy hệ thống Windows và cổng Proxy cục bộ');
        proxy = await resolveProxy(settings);
        if (settings.proxyMode === 'manual' && !proxy.reachable) {
          throw new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}. Vui lòng khởi động phần mềm proxy, thay đổi cổng hoặc chuyển sang tự động phát hiện.`);
        }
        const proxyLabel = proxy.resolvedUrl || 'Kết nối trực tiếp';
        this.log.info('Hoàn tất kiểm tra tuyến đường mạng', { mode: settings.proxyMode, source: proxy.source, route: proxyLabel, reachable: proxy.reachable });
        this.progress('proxy-ready', 16, proxy.reachable ? `Tuyến đường mạng khả dụng: ${proxyLabel}` : 'Chưa xác minh được tuyến đường mạng khả dụng, sẽ tiếp tục thử kết nối trực tiếp và giữ nhật ký chẩn đoán');
      } else {
        this.progress('local-executor-preflight', 16, 'Chế độ executor trung tâm: chỉ khởi động MCP cục bộ, không dùng OpenAI Tunnel hay Runtime API Key của máy này');
      }

      this.progress('runtime-stop-old', 18, 'Đang dọn dẹp các instance chạy cũ từ lần khởi động trước');
      await this.tunnel.stop();
      await this.native.stop().catch(() => false);
      if (await canConnect('127.0.0.1', settings.mcpPort, 350)) {
        throw new Error(`Cổng cục bộ ${settings.mcpPort} đang bị ứng dụng khác chiếm dụng. Trợ lý sẽ không cưỡng chế chấm dứt tiến trình không xác định, vui lòng thay đổi cổng MCP trong trang "Thư mục làm việc".`);
      }
      if (!centralExecutor && await canConnect('127.0.0.1', settings.healthPort, 350)) {
        throw new Error(`Cổng cục bộ ${settings.healthPort} đang bị ứng dụng khác chiếm dụng. Trợ lý sẽ không cưỡng chế chấm dứt tiến trình không xác định, vui lòng thay đổi cổng bảng điều khiển Tunnel.`);
      }

      const connectorAttestationSecret = this.rotateConnectorAttestationSecret();
      await this.native.start(settings, token, this.progress.bind(this), {
        p5Seed: this.p5A0Seed(),
        activationEpochId: launchActivationEpochId,
        activationGate: normalizedActivationGate,
        activationAllowAcceptancePending: options.activationAllowAcceptancePending === true,
        activationExpiresAtUnixMs: Number(options.expiresAtUnixMs || 0) || 0,
        connectorAttestationSecret
      });

      this.progress('mcp-health', 64, 'Đang xác minh Coding Tools MCP');
      let ready = false;
      for (let index = 0; index < 35; index += 1) {
        if (await probeMcp(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '', launchActivationEpochId)) { ready = true; break; }
        if (!(await this.native.status(settings, { activationEpochId: launchActivationEpochId }))) {
          throw new Error('Tiến trình Coding Tools MCP đã thoát sớm. Vui lòng xem mcp.log trong nhật ký vận hành để biết lỗi khởi động chi tiết.');
        }
        await wait(1000);
      }
      if (!ready) throw new Error('Coding Tools MCP không vượt qua kiểm tra sức khỏe trong thời gian quy định.');

      // Central executors have no node Tunnel, yet the Recovery Host still
      // needs this per-process binding to authorize the Ubuntu read-only
      // bridge.  Establish it immediately after the exact MCP health check
      // for both execution roles; only Tunnel launch remains direct-only.
      const attestationHealth = await this.currentMcpHealth({ timeoutMs: 5000 });
      const connectorAttestation = this.connectorAttestationForHealth(attestationHealth, {
        establish: true,
        secret: connectorAttestationSecret
      });
      if (!centralExecutor) {
        await this.tunnel.start({ ...settings, effectiveProxyUrl: proxy.resolvedUrl }, runtimeApiKey, token, this.progress.bind(this), {
          activationEpochId: launchActivationEpochId,
          connectorAttestation
        });
      }
      this.setManualStop(false);
      this.autoRecoveryBlocked = false;
      this.lastStartFailure = '';
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.lastRecoveryAt = Date.now();
      this.lastHealthyAt = Date.now();
      this.progress(
        centralExecutor ? 'local-executor-ready' : 'complete',
        100,
        centralExecutor
          ? 'Coding Tools MCP cục bộ đã sẵn sàng; chờ ghép nối và quyền action từ Ubuntu.'
          : 'Triển khai hoàn tất, cả MCP và OpenAI Tunnel đều đang chạy'
      );
      this.invalidateSnapshot();
      return await this.snapshot({ force: true, reason: 'started' });
    } catch (error) {
      this.autoRecoveryBlocked = true;
      this.lastStartFailure = error.message;
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = Date.now();
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      await this.tunnel.stop().catch(() => false);
      await this.native.stop().catch(() => false);
      this.invalidateSnapshot();
      this.log.error(error.message, { stage: 'start' });
      this.emitProgress({ step: 'failed', percent: 100, message: error.message, time: new Date().toISOString() });
      throw error;
    } finally {
      this.busy = false;
    }
  }

  async stop(options = {}) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    this.busy = true;
    try {
      if (options.manual !== false) this.setManualStop(true);
      this.progress('stop-tunnel', 25, 'Đang dừng OpenAI Tunnel');
      await this.tunnel.stop();
      this.progress('stop-runtime', 65, 'Đang dừng Coding Tools MCP');
      await this.native.stop().catch(() => false);
      this.progress('stopped', 100, 'Tất cả các dịch vụ do trợ lý khởi động đã dừng');
      this.invalidateSnapshot();
      return await this.snapshot({ force: true, reason: 'stopped' });
    } finally {
      this.busy = false;
    }
  }

  async restart(options = {}) {
    if (options.automatic !== true) {
      if (this.fullCleanActivation?.restart) return this.fullCleanActivation.restart(options);
      throw Object.assign(new Error('Operator restart requires the Recovery Host full-clean activation coordinator.'), {
        code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE'
      });
    }
    const launchActivationEpochId = String(options.activationEpochId || this.activationEpochId || '').trim();
    const durableEpoch = this.assertMcpReplacementAllowed({
      activationEpochId: launchActivationEpochId,
      operation: 'automatic_runtime_restart'
    });
    if (durableEpoch.update_incomplete === true) {
      throw Object.assign(new Error('Runtime activation is incomplete; soft recovery is suppressed until a full-clean epoch reaches READY.'), {
        code: 'UPDATE_INCOMPLETE',
        details: {
          activation_epoch_id: durableEpoch.activation_epoch_id || null,
          epoch_state: durableEpoch.epoch_state || durableEpoch.state || null,
          admission_open: false
        }
      });
    }
    this.assertActivationRevisionContinuity();
    await this.stop({ manual: false });
    return this.start({ ...options, mode: options.mode || 'soft_recovery' });
  }

  async switchWorkspace(nextWorkspace) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    const previous = this.settingsStore.load();
    const workspace = normalizeWorkspacePath(nextWorkspace);
    if (!workspace || !fs.existsSync(workspace) || !fs.statSync(workspace).isDirectory()) {
      throw new Error('Vui lòng chọn một thư mục làm việc hợp lệ.');
    }

    const recentWorkspaces = mergeRecentWorkspaces(previous.recentWorkspaces, workspace);
    if (workspaceKey(previous.workspace) === workspaceKey(workspace)) {
      if (JSON.stringify(recentWorkspaces) !== JSON.stringify(previous.recentWorkspaces || [])) {
        this.settingsStore.save({ recentWorkspaces });
      }
      return this.snapshot({ force: true, reason: 'workspace-reselected' });
    }

    this.busy = true;
    let runtimeWasRunning = false;
    try {
      runtimeWasRunning = await this.native.status();
    } catch {
      runtimeWasRunning = false;
    }

    if (!runtimeWasRunning) {
      this.settingsStore.save({ workspace, recentWorkspaces });
      this.progress('workspace-saved', 100, 'Thư mục làm việc đã lưu, sẽ có hiệu lực ở lần khởi động dịch vụ tiếp theo');
      this.busy = false;
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'workspace-saved' });
    }

    const token = await this.ensureToken();
    try {
      this.progress('workspace-switch', 20, 'Đang chuyển đổi nóng thư mục làm việc MCP');
      await switchMcpWorkspace(previous.mcpPort, token, workspace);
      const next = this.settingsStore.save({ workspace, recentWorkspaces });
      await this.native.markWorkspace(next);
      this.progress('workspace-health', 80, 'Đang xác minh thư mục làm việc mới');
      const ready = await probeMcp(next.mcpPort, token, workspace, this.device?.deviceId || '');
      if (!ready) throw new Error('Thư mục làm việc mới không khớp với thư mục thực tế của MCP.');
      this.progress('workspace-complete', 100, 'Đã chuyển thư mục làm việc, cả MCP và Tunnel đều không cần khởi động lại');
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'workspace-switched' });
    } catch (error) {
      this.log.error(error.message, { stage: 'workspace-switch', rollback: previous.workspace });
      try {
        await switchMcpWorkspace(previous.mcpPort, token, previous.workspace);
        this.settingsStore.save(previous);
        await this.native.markWorkspace(previous);
      } catch (rollbackError) {
        this.log.error(rollbackError.message, { stage: 'workspace-rollback' });
      }
      throw new Error(`Chuyển đổi thư mục làm việc thất bại: ${error.message}`);
    } finally {
      this.busy = false;
    }
  }

  async updateAuthorizedRoots(roots) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    const previous = this.settingsStore.load();
    const normalized = (Array.isArray(roots) ? roots : [])
      .map(normalizeWorkspacePath)
      .filter((item) => item && fs.existsSync(item) && fs.statSync(item).isDirectory())
      .filter((item, index, all) => all.findIndex((other) => workspaceKey(other) === workspaceKey(item)) === index)
      .filter((item) => workspaceKey(item) !== workspaceKey(previous.workspace))
      .slice(0, 32);
    this.busy = true;
    try {
      const runtimeWasRunning = await this.native.status().catch(() => false);
      if (runtimeWasRunning) {
        const token = await this.ensureToken();
        await setMcpAuthorizedRoots(previous.mcpPort, token, normalized);
      }
      const saved = this.settingsStore.save({ authorizedRoots: normalized });
      if (runtimeWasRunning) await this.native.markWorkspace(saved);
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'authorized-roots-updated' });
    } finally {
      this.busy = false;
    }
  }

  async lightweightSnapshot(options = {}) {
    const settings = this.settingsStore.load();
    const suppliedMcpHealth = Object.prototype.hasOwnProperty.call(options, 'mcpHealth');
    const [mcpHealth, nativeObservation, tunnelRunning, git] = await Promise.all([
      suppliedMcpHealth ? Promise.resolve(options.mcpHealth) : this.currentMcpHealth(options),
      this.native.status(settings, {
        activationEpochId: this.activationEpochId || '',
        returnIdentity: true
      }).catch(() => false),
      this.tunnel.status(settings, { activationEpochId: this.activationEpochId || '' }).catch(() => false),
      this.gitStatus(settings.workspace)
    ]);
    const nativeAlive = Boolean(nativeObservation);
    const verifiedProcessIdentity = nativeObservation && typeof nativeObservation === 'object'
      ? nativeObservation : null;
    const mcpRunning = Boolean(mcpHealth);
    const connectorContract = this.connectorContractStatus(
      mcpHealth?.tool_contract || null,
      mcpHealth?.connector_tool_discovery || null,
      mcpHealth?.connector_client_contact || null,
      mcpHealth?.connector_activation_bootstrap || null,
      mcpHealth
    );
    const connectorFreshness = this.connectorContractFreshness(mcpHealth, connectorContract);
    const activationEpoch = this.activationEpochStatus();
    const epochReady = activationEpoch.admission_open === true;
    const codeRevision = this.codingMcpRevisionStatus(verifiedProcessIdentity
      ? { verifiedProcessIdentity }
      : {});
    const revisionDrift = Boolean(
      codeRevision.update_pending === true
      || (codeRevision.running_revision && codeRevision.disk_revision
        && codeRevision.running_revision !== codeRevision.disk_revision)
    );
    const revisionReady = codeRevision.state !== 'unavailable' && !revisionDrift;
    const connectorReady = connectorFreshness.ready === true;
    const centralRoute = this.centralRouteEvidence(settings);
    const readiness = runtimeReadiness({
      role: executionRole(settings),
      mcpRunning,
      nativeAlive,
      tunnelRunning,
      epochReady,
      revisionReady,
      connectorReady,
      activationIncomplete: activationEpoch.update_incomplete === true,
      revisionDrift,
      centralConnected: centralRoute?.connected === true,
      authorityReady: centralRoute?.authorityReady === true,
      centralRouteReason: centralRoute?.reason || ''
    });
    return {
      workspace: settings.workspace,
      mcpRunning,
      nativeAlive,
      tunnelRunning,
      ...readiness,
      centralRoute: centralRoute?.evidence ? {
        serverOrigin: centralRoute.evidence.serverOrigin,
        endpointId: centralRoute.evidence.endpointId,
        credentialGeneration: centralRoute.evidence.credentialGeneration,
        observedAtMs: centralRoute.evidence.observedAtMs,
        runtimeReadiness: centralRoute.evidence.runtimeReadiness,
        policyState: centralRoute.evidence.policyState,
        policyExpiresAtMs: centralRoute.evidence.policyExpiresAtMs
      } : null,
      connectorReady,
      activationEpoch,
      device: this.deviceProjection(settings, { mcpHealth, nativeAlive, tunnelRunning, git }),
      toolContract: connectorContract.available ? {
        schemaVersion: connectorContract.schemaVersion,
        profile: connectorContract.profile,
        sha256: connectorContract.currentSha256
      } : null,
      connectorContractAcknowledgedSha256: connectorContract.acknowledgedSha256,
      connectorContractState: connectorContract.contractState,
      connectorRefreshRequired: connectorContract.refreshRequired,
      connectorAcknowledgementPending: connectorContract.acknowledgementPending,
      connectorRediscovered: connectorContract.rediscovered,
      connectorRediscoveredAt: connectorContract.rediscoveredAt,
      connectorBootstrapObservedAt: connectorContract.bootstrapObservedAt,
      connectorCompatibilityAcknowledged: connectorContract.compatibilityAcknowledged,
      connectorCompatibilityAcknowledgedAt: connectorContract.compatibilityAcknowledgedAt,
      connectorFreshnessMode: connectorFreshness.mode,
      codeRevision: { codingMcp: codeRevision },
      ...this.recoveryStatus()
    };
  }

  async recoverTunnelOnly() {
    this.assertSoftRecoveryAllowed();
    this.assertActivationRevisionContinuity();
    const settings = this.settingsStore.load();
    if (executionRole(settings) === 'central_executor') {
      throw Object.assign(new Error('Central executor nodes do not run a local OpenAI Tunnel; recover the Ubuntu route or node pairing instead.'), {
        code: 'CENTRAL_EXECUTOR_TUNNEL_DISABLED'
      });
    }
    const runtimeApiKey = this.secrets.get('runtimeApiKey');
    if (!runtimeApiKey) throw new Error('Vui lòng lưu Runtime API Key trong "Cấu hình triển khai" trước.');
    if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    const token = await this.ensureToken();
    const proxy = await resolveProxy(settings);
    if (settings.proxyMode === 'manual' && !proxy.reachable) {
      throw new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}.`);
    }
    const health = await this.currentMcpHealth({ timeoutMs: 5000 });
    const connectorAttestation = this.connectorAttestationForHealth(health);
    await this.tunnel.start(
      { ...settings, effectiveProxyUrl: proxy.resolvedUrl },
      runtimeApiKey,
      token,
      this.progress.bind(this),
      {
        activationEpochId: this.activationEpochId || '',
        connectorAttestation
      }
    );
    this.log.info('OpenAI Tunnel đã được khôi phục mà không khởi động lại Coding Tools MCP');
    this.invalidateSnapshot();
  }

  async recoverMcpOnly(options = {}) {
    this.assertSoftRecoveryAllowed();
    const settings = this.settingsStore.load();
    this.validate(settings);
    const centralExecutor = executionRole(settings) === 'central_executor';
    const runtimeApiKey = centralExecutor ? '' : this.secrets.get('runtimeApiKey');
    if (!centralExecutor && !runtimeApiKey) throw new Error('Vui lòng lưu Runtime API Key trong "Cấu hình triển khai" trước.');
    if (!centralExecutor && !settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    const token = await this.ensureToken();
    let proxy = null;
    if (!centralExecutor) {
      proxy = await resolveProxy(settings);
      if (settings.proxyMode === 'manual' && !proxy.reachable) {
        throw new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}.`);
      }
    }
    const before = readJson(this.paths.stateFile(), {});
    const continuity = this.assertActivationRevisionContinuity();
    const expectedRevision = continuity.verified === true
      ? String(continuity.expected_revision || '').trim() : '';
    const oldNativePid = Number(before.nativePid || 0);
    const tunnelPid = Number(before.tunnelPid || 0);

    if (isAlive(oldNativePid) && options.replaceLiveOwned !== true) {
      throw Object.assign(new Error('Coding MCP process is still alive; refusing dead-process recovery.'), {
        code: 'MCP_PROCESS_STILL_ALIVE'
      });
    }
    const launchActivationEpochId = String(options.activationEpochId || this.activationEpochId || '').trim();
    const normalizedActivationGate = normalizeActivationGate(launchActivationEpochId, options.activationGate);
    this.assertMcpReplacementAllowed({
      activationEpochId: launchActivationEpochId,
      operation: options.replaceLiveOwned === true ? 'mcp_hung_process_replacement' : 'mcp_process_recovery'
    });
    // Bind the per-call launch identity only after the durable epoch guard has
    // accepted it.  Recovery callers may supply an explicit epoch while this
    // Recovery Host still carries a stale/empty in-memory value; subsequent
    // health and attestation checks must observe the exact identity that was
    // sent to NativeService/TunnelService.  Keep the legacy no-epoch path
    // untouched so an empty launch identity does not become a new binding.
    if (launchActivationEpochId && launchActivationEpochId !== this.activationEpochId) {
      this.setActivationEpoch(launchActivationEpochId);
    }
    if (centralExecutor) {
      // Completing a direct-to-central handoff must not leave an owned legacy
      // Tunnel running beside the Ubuntu ingress.  This is an owned-service
      // stop, never a port/PID kill of an unknown process.
      await this.tunnel.stop();
    }
    if (isAlive(oldNativePid)) {
      // Semantic recovery may replace a persistently hung process, but only
      // through NativeService's exact PID + process-start-token authority.
      await this.native.stop();
    }
    if (await canConnect('127.0.0.1', settings.mcpPort, 350)) {
      throw Object.assign(new Error(`Cổng cục bộ ${settings.mcpPort} đang bị tiến trình khác chiếm dụng; từ chối nhận hoặc dừng tiến trình không xác định.`), {
        code: 'MCP_PORT_IN_USE'
      });
    }

    let started = null;
    try {
      const connectorAttestationSecret = this.rotateConnectorAttestationSecret();
      started = await this.native.start(settings, token, this.progress.bind(this), {
        p5Seed: this.p5A0Seed(),
        activationEpochId: launchActivationEpochId,
        activationGate: normalizedActivationGate,
        connectorAttestationSecret,
        ...(expectedRevision ? { expectedCodeRevision: expectedRevision } : {})
      });
      let health = null;
      let ownedPid = 0;
      for (let index = 0; index < 35; index += 1) {
        const state = readJson(this.paths.stateFile(), {});
        ownedPid = Number(state.nativePid || 0);
        health = await this.currentMcpHealth();
        if (health && ownedPid > 0 && isAlive(ownedPid)
          && (!expectedRevision || String(health.code_revision || '') === expectedRevision)
          && await (this.listenerPidProbe || loopbackListenerPid)(settings.mcpPort) === ownedPid) break;
        health = null;
        if (!(await this.native.status(settings, { activationEpochId: launchActivationEpochId }))) {
          throw Object.assign(new Error('Coding Tools MCP exited during MCP-only recovery.'), { code: 'MCP_RECOVERY_PROCESS_EXITED' });
        }
        await wait(1000);
      }
      if (!health || ownedPid <= 0) {
        throw Object.assign(new Error('Coding Tools MCP did not pass exact identity and listener ownership checks during MCP-only recovery.'), {
          code: 'MCP_RECOVERY_NOT_READY'
        });
      }
      if (expectedRevision) {
        const postDiskRevision = String(this.revisions.disk('coding_mcp', { force: true }).revision || '').trim();
        if (postDiskRevision !== expectedRevision) {
          throw Object.assign(new Error('Coding MCP source changed during soft recovery; replacement remains stopped pending full-clean activation.'), {
            code: 'REVISION_CHANGED_DURING_RECOVERY',
            details: { expected_revision: expectedRevision, disk_revision: postDiskRevision || null }
          });
        }
      }
      // A replacement MCP always needs a new local attestation binding.  The
      // binding is also consumed by central-executor read-only relay calls,
      // even though that role intentionally never starts a node Tunnel.
      const connectorAttestation = this.connectorAttestationForHealth(health, {
        establish: true,
        secret: connectorAttestationSecret
      });
      let tunnelStarted = null;
      if (!centralExecutor) {
        // The managed Tunnel carries a static attestation bound to the exact MCP
        // process/server tuple. Replacing MCP therefore invalidates the old
        // Tunnel header even when the public contract is unchanged. Refresh only
        // this dependent Tunnel (not Recovery Host/UI/recovery plane) so soft
        // recovery remains scoped while connector provenance stays usable.
        tunnelStarted = await this.tunnel.start(
          { ...settings, effectiveProxyUrl: proxy.resolvedUrl },
          runtimeApiKey,
          token,
          this.progress.bind(this),
          {
            activationEpochId: launchActivationEpochId,
            connectorAttestation
          }
        );
      }
      const after = readJson(this.paths.stateFile(), {});
      this.log.info(centralExecutor
        ? 'Coding Tools MCP local executor đã được khôi phục mà không khởi động OpenAI Tunnel tại node'
        : 'Coding Tools MCP và attestation phụ thuộc của Coding Tunnel đã được khôi phục', {
        oldPid: oldNativePid || null,
        newPid: ownedPid,
        oldTunnelPid: tunnelPid || null,
        newTunnelPid: Number(after.tunnelPid || tunnelStarted?.pid || 0) || null
      });
      this.invalidateSnapshot();
      return {
        old_pid: oldNativePid || null,
        new_pid: ownedPid,
        old_tunnel_pid: tunnelPid || null,
        tunnel_pid: Number(after.tunnelPid || tunnelStarted?.pid || 0) || null,
        tunnel_preserved: false,
        tunnel_attestation_refreshed: !centralExecutor,
        central_executor: centralExecutor,
        health_verified: true
      };
    } catch (error) {
      if (started && started.reused !== true) await this.native.stop().catch(() => false);
      this.invalidateSnapshot();
      throw error;
    }
  }

  async supervise() {
    const supervisorRequest = await this.serviceSupervisorRestartRequest();
    if (supervisorRequest) {
      return { ...(await this.lightweightSnapshot()), supervisorRequest };
    }
    const status = await this.lightweightSnapshot();
    // Connector rediscovery/ACK is part of aggregate readiness but is not a
    // component-health failure.  Keep the watchdog on the component-only
    // projection so an UPDATE_INCOMPLETE connector gate never triggers a
    // needless Tunnel or MCP soft recovery.
    const componentsReady = status.componentsReady === true
      || (status.componentsReady == null && status.fullyReady === true);
    if (componentsReady) {
      const wasFailing = this.heartbeatFailures > 0 || this.recovering || this.heartbeatFailureSince > 0;
      this.endFailureStreak();
      if (wasFailing) this.lastRecoveryAt = Date.now();
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      this.lastHealthyAt = Date.now();
      return { ...status, ...this.recoveryStatus() };
    }
    const runtimeState = readJson(this.paths.stateFile(), {});
    const expectedRunning = runtimeState.manualStop === false
      && Boolean(runtimeState.nativePid || runtimeState.tunnelPid || this.settingsStore.load().autoStartServices);
    if (this.busy || this.recovering || this.isManuallyStopped() || !expectedRunning) return status;
    if (this.autoRecoveryBlocked) {
      return { ...status, recoveryBlocked: true, lastStartFailure: this.lastStartFailure };
    }
    const deterministicHealthFailure = Boolean(
      status.nativeAlive
      && !status.mcpRunning
      && status.mcpHealthFailureDeterministic === true
      && status.mcpHealthFailureKind
    );
    if (deterministicHealthFailure) {
      const failureKind = `mcp_health_${status.mcpHealthFailureKind}`;
      if (failureKind !== this.heartbeatFailureKind) {
        this.endFailureStreak();
        this.heartbeatFailureKind = failureKind;
        this.heartbeatFailures = 0;
        this.recoveryAttempts = 0;
        this.nextRecoveryAt = 0;
        this.deferredRecoveryCount = 0;
        this.heartbeatFailureSince = Date.now();
      }
      if (this.heartbeatFailureSince === 0) this.heartbeatFailureSince = Date.now();
      this.heartbeatFailures += 1;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      return {
        ...status,
        ...this.recoveryStatus(),
        recovering: false,
        recoveryBlocked: true,
        recoveryDeferred: true,
        recoveryReason: 'mcp_health_deterministic_mismatch',
        mcpHealthFailureKind: status.mcpHealthFailureKind,
        mcpHealthFailureDeterministic: status.mcpHealthFailureDeterministic === true
      };
    }
    const centralExecutor = status.executionRole === 'central_executor';
    const failureKind = centralExecutor
      ? (status.mcpRunning ? 'mcp_native_identity_unavailable' : (status.nativeAlive ? 'mcp_health_unavailable' : 'mcp_process_exited'))
      : (status.mcpRunning ? 'tunnel_unavailable' : (status.nativeAlive ? 'mcp_health_unavailable' : 'mcp_process_exited'));
    if (failureKind !== this.heartbeatFailureKind) {
      this.endFailureStreak();
      this.heartbeatFailureKind = failureKind;
      this.heartbeatFailures = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      this.heartbeatFailureSince = Date.now();
    }
    if (this.heartbeatFailureSince === 0) this.heartbeatFailureSince = Date.now();
    this.heartbeatFailures += 1;
    if (this.heartbeatFailures < 3 || Date.now() < this.nextRecoveryAt) {
      return { ...status, ...this.recoveryStatus() };
    }

    this.recovering = true;
    this.recoveryAttempts += 1;
    const delay = Math.min(60000, 2000 * (2 ** Math.min(this.recoveryAttempts - 1, 5)));
    this.nextRecoveryAt = Date.now() + delay;
    this.log.warn('Kiểm tra sức khỏe giao thức runtime thất bại liên tiếp, bắt đầu tự động khôi phục', {
      failures: this.heartbeatFailures,
      attempt: this.recoveryAttempts,
      mcpRunning: status.mcpRunning,
      nativeAlive: status.nativeAlive,
      tunnelRunning: status.tunnelRunning
    });
    try {
      if (!centralExecutor && status.mcpRunning) {
        await this.recoverTunnelOnly();
      } else if (status.nativeAlive) {
        this.deferredRecoveryCount += 1;
        if (this.deferredRecoveryCount >= MAX_DEFERRED_RECOVERIES) {
          this.log.warn('Coding Tools MCP không trả lời health check sau nhiều chu kỳ mặc dù process còn sống; buộc khởi động lại để thoát khỏi trạng thái treo', {
            failures: this.heartbeatFailures,
            deferredRecoveryCount: this.deferredRecoveryCount,
            attempt: this.recoveryAttempts
          });
          this.deferredRecoveryCount = 0;
          await this.recoverMcpOnly({ replaceLiveOwned: true, reason: 'hung_mcp_soft_recovery' });
        } else {
          this.log.warn('Coding Tools MCP không trả lời health check nhưng process vẫn còn sống; hoãn restart để không cắt tool call đang chạy', {
            failures: this.heartbeatFailures,
            deferredRecoveryCount: this.deferredRecoveryCount,
            maxDeferredRecoveries: MAX_DEFERRED_RECOVERIES,
            attempt: this.recoveryAttempts
          });
          return {
            ...status,
            ...this.recoveryStatus(),
            recovering: false,
            recoveryDeferred: true,
            deferredRecoveryCount: this.deferredRecoveryCount,
            recoveryReason: 'mcp_process_alive_health_unavailable'
          };
        }
      } else {
        await this.recoverMcpOnly();
      }
      this.endFailureStreak();
      this.lastRecoveryAt = Date.now();
      this.lastHealthyAt = Date.now();
      this.heartbeatFailures = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
    } catch (error) {
      const fullCleanRequired = error?.code === 'UPDATE_INCOMPLETE'
        && error?.details?.full_clean_activation_required === true;
      if (fullCleanRequired) {
        this.autoRecoveryBlocked = true;
        this.lastStartFailure = error.message;
        this.nextRecoveryAt = 0;
        this.deferredRecoveryCount = 0;
      }
      this.log.error(error.message, {
        stage: 'automatic-recovery',
        retryAfterMs: fullCleanRequired ? 0 : delay,
        recoveryBlocked: fullCleanRequired,
        errorCode: String(error?.code || '') || null
      });
    } finally {
      this.recovering = false;
    }
    return this.lightweightSnapshot();
  }

  async snapshot(options = {}) {
    const force = options.force === true;
    if (!force && this.snapshotCache && Date.now() - this.snapshotCacheAt < 15000) return this.snapshotCache;
    if (!force && this.snapshotInFlight) return this.snapshotInFlight;
    this.snapshotInFlight = this._collectSnapshot(options.reason || 'refresh');
    try { return await this.snapshotInFlight; }
    finally { this.snapshotInFlight = null; }
  }

  async _collectSnapshot(reason) {
    const settings = this.settingsStore.load();
    const environment = await this.environment.inspect(settings);
    const [health, tunnelRunning, git] = await Promise.all([
      this.currentMcpHealth(),
      this.tunnel.status(settings, { activationEpochId: this.activationEpochId || '' }).catch(() => false),
      this.gitStatus(settings.workspace)
    ]);
    const runtimeRunning = Boolean(health);
    const connectorContract = this.connectorContractStatus(
      health?.tool_contract || null,
      health?.connector_tool_discovery || null,
      health?.connector_client_contact || null,
      health?.connector_activation_bootstrap || null,
      health
    );
    const connectorFreshness = this.connectorContractFreshness(health, connectorContract);
    const nativeAlive = await this.native.status().catch(() => false);
    const activationEpoch = this.activationEpochStatus();
    const epochReady = activationEpoch.admission_open === true;
    const codeRevision = this.codingMcpRevisionStatus();
    const revisionDrift = Boolean(
      codeRevision.update_pending === true
      || (codeRevision.running_revision && codeRevision.disk_revision
        && codeRevision.running_revision !== codeRevision.disk_revision)
    );
    const revisionReady = codeRevision.state !== 'unavailable' && !revisionDrift;
    const connectorReady = connectorFreshness.ready === true;
    const centralRoute = this.centralRouteEvidence(settings);
    const readiness = runtimeReadiness({
      role: executionRole(settings),
      mcpRunning: runtimeRunning,
      nativeAlive,
      tunnelRunning,
      epochReady,
      revisionReady,
      connectorReady,
      activationIncomplete: activationEpoch.update_incomplete === true,
      revisionDrift,
      centralConnected: centralRoute?.connected === true,
      authorityReady: centralRoute?.authorityReady === true,
      centralRouteReason: centralRoute?.reason || ''
    });
    return this.publishSnapshot({
      settings,
      secrets: this.secrets.status(),
      environment,
      device: this.deviceProjection(settings, { mcpHealth: health, nativeAlive, tunnelRunning, git }),
      status: {
        busy: this.busy,
        runtimeRunning,
        tunnelRunning,
        ...readiness,
        centralRoute: centralRoute?.evidence ? {
          serverOrigin: centralRoute.evidence.serverOrigin,
          endpointId: centralRoute.evidence.endpointId,
          credentialGeneration: centralRoute.evidence.credentialGeneration,
          observedAtMs: centralRoute.evidence.observedAtMs,
          runtimeReadiness: centralRoute.evidence.runtimeReadiness,
          policyState: centralRoute.evidence.policyState,
          policyExpiresAtMs: centralRoute.evidence.policyExpiresAtMs
        } : null,
        connectorReady,
        activationEpoch,
        localMcpUrl: `http://127.0.0.1:${settings.mcpPort}/mcp`,
        tunnelUiUrl: `http://127.0.0.1:${settings.healthPort}/ui`,
        manuallyStopped: this.isManuallyStopped(),
        toolContract: connectorContract.available ? {
          schemaVersion: connectorContract.schemaVersion,
          profile: connectorContract.profile,
          sha256: connectorContract.currentSha256
        } : null,
        connectorContractAcknowledgedSha256: connectorContract.acknowledgedSha256,
        connectorContractState: connectorContract.contractState,
        connectorRefreshRequired: connectorContract.refreshRequired,
        connectorAcknowledgementPending: connectorContract.acknowledgementPending,
        connectorRediscovered: connectorContract.rediscovered,
        connectorRediscoveredAt: connectorContract.rediscoveredAt,
        connectorBootstrapObservedAt: connectorContract.bootstrapObservedAt,
        connectorCompatibilityAcknowledged: connectorContract.compatibilityAcknowledged,
        connectorCompatibilityAcknowledgedAt: connectorContract.compatibilityAcknowledgedAt,
        connectorFreshnessMode: connectorFreshness.mode,
        codeRevision: { codingMcp: codeRevision },
        ...this.recoveryStatus()
      }
    }, reason);
  }
}

module.exports = { RuntimeOrchestrator, executionRole, runtimeReadiness, probeMcp, readMcpHealth, readMcpHealthObservation, readMcpActivationPreflight, activationPreflightProof, parseGitStatusPorcelainV2, parseLoopbackListenerPid, loopbackListenerPid, setMcpAuthorizedRoots };
