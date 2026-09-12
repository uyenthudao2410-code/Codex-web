#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryIpcClient, loadRecoveryDescriptor, isProcessAlive } = require('../electron/services/recoveryIpc');
const { readJson } = require('../electron/services/jsonStore');
const { ComponentRevisionTracker } = require('../electron/services/componentRevision');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');
const {
  bootstrapCurrentRecoveryHost,
  readBootstrapResult
} = require('../electron/services/recoveryBootstrap');
const {
  ensureRecoveryHost,
  descriptorMatchesInstallation,
  descriptorRequestOptions,
  suppressDevelopmentRecoverySupervisor
} = require('../electron/services/recoveryHostLauncher');
const { activationSourceCheckpoint: sourceCheckpointForActivation } = require('../electron/services/activationClosure');

const ACTIONS = new Set(['start', 'stop', 'replace', 'refresh', 'status', 'control-center']);
const INSTANCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
// Electron can take tens of seconds to become ready on a cold Windows
// profile.  A full refresh also has to start MCP, prove its health, start the
// tunnel, register the replacement UI, and run the exact identity census.  A
// two-minute window was shorter than the observed cold-start path and caused
// the refresh CLI to expire a perfectly valid handoff while its children were being
// replaced.  Keep the operator poll and authenticated activation deadline
// separate, but give both enough bounded room for that real startup path.
const DEFAULT_TIMEOUT_MS = 300_000;
// The CLI waits at most five minutes for process replacement, but a successful
// refresh can truthfully return VERIFYING while the real ChatGPT connector is
// still about to contact the new MCP process. Keep the durable activation
// transaction alive for a second bounded five-minute phase instead of making
// connector ACK race the process-start timeout.
const DEFAULT_REFRESH_ACTIVATION_TTL_MS = 600_000;
const MAX_REFRESH_ACTIVATION_TTL_MS = 600_000;
const DEFAULT_REFRESH_HOST_TIMEOUT_MS = 90_000;
const MAX_REFRESH_HOST_TIMEOUT_MS = 120_000;
const DEFAULT_POLL_MS = 250;
const DEFAULT_RUNTIME_READY_TIMEOUT_MS = 45_000;
const DEFAULT_EPOCH_READ_RETRY_TIMEOUT_MS = 5_000;
const REFRESH_OPERATION_ID_PATTERN = /^full-clean-refresh-[A-Za-z0-9_-]{15,127}$/;
// These are the non-terminal coordinator states that own a refresh
// transaction.  A second `npm run dev:refresh` must reconcile one of these records
// instead of forcing the old host down and attempting to create a competing
// epoch.  Keep this list aligned with ActivationEpochStore's ACTIVE_STATES;
// the local copy lets the lifecycle CLI fail closed even when its store
// implementation is loaded through a different process/checkout.
const REFRESH_ACTIVE_EPOCH_STATES = new Set([
  'PREPARING',
  'ADMISSION_CLOSED',
  'STOPPING',
  'FROZEN',
  'HANDOFF',
  'STARTING',
  'VERIFYING',
  'READY_COMMITTED'
]);
const REFRESH_TERMINAL_EPOCH_STATES = new Set(['READY', 'FAILED']);

function isFullCleanRefreshEpoch(record) {
  if (!record || typeof record !== 'object' || Array.isArray(record)) return false;
  const intent = record.request_intent;
  if (!intent || typeof intent !== 'object' || Array.isArray(intent)) return false;
  const mode = String(intent.mode || '').trim().toLowerCase();
  const metadata = intent.metadata;
  // `npm run dev:refresh` owns only the explicit process-refresh transaction.  A normal
  // accepted-code full-clean activation uses the same durable epoch state
  // machine, but its source checkpoint is a different authority and must not
  // be adopted/reconciled by this lifecycle command.
  return mode === 'full_clean_activation'
    && metadata && typeof metadata === 'object' && !Array.isArray(metadata)
    && metadata.refresh === true
    && (intent.source_checkpoint === undefined
      || intent.source_checkpoint === null
      || intent.source_checkpoint === '')
    && String(record.mode || '').trim().toLowerCase() === mode
    && record.metadata?.refresh === true
    && (record.source_checkpoint === undefined
      || record.source_checkpoint === null
      || record.source_checkpoint === '');
}

function lifecycleError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function normalizeAction(value) {
  const action = String(value || 'start').trim().toLowerCase();
  if (!ACTIONS.has(action)) {
    throw lifecycleError('DEV_UI_ACTION_INVALID', 'Usage: npm start | npm run dev | npm run dev:status | npm run dev:stop | npm run dev:replace | npm run dev:control-center');
  }
  return action;
}

function resolveElectronExecutable() {
  const executable = require('electron');
  if (typeof executable !== 'string' || !path.isAbsolute(executable)) {
    throw lifecycleError('DEV_UI_ELECTRON_UNAVAILABLE', 'The local Electron executable could not be resolved. Run npm install first.');
  }
  return executable;
}

function createDevelopmentPaths({
  appRoot = path.resolve(__dirname, '..'),
  appData = process.env.APPDATA,
  electronExecutable = resolveElectronExecutable()
} = {}) {
  const roamingRoot = String(appData || '').trim();
  if (!roamingRoot || !path.isAbsolute(roamingRoot)) {
    throw lifecycleError('DEV_UI_APPDATA_UNAVAILABLE', 'APPDATA is unavailable; the shared desktop profile cannot be resolved safely.');
  }
  return createRuntimePaths({
    dataRoot: path.join(roamingRoot, 'web-mcp-assistant'),
    appRoot,
    resourcesRoot: path.join(appRoot, 'resources'),
    runtimeMode: 'development',
    executablePath: electronExecutable
  });
}

function uiObservation(status = {}) {
  const recovery = status?.electron_ui_recovery || {};
  const revision = status?.electron_ui_revision || {};
  const alive = recovery.alive === true;
  const runningRevision = String(revision.running_revision || '').toLowerCase() || null;
  const diskRevision = String(revision.disk_revision || '').toLowerCase() || null;
  let state = 'MISSING';
  if (alive) state = runningRevision && diskRevision && runningRevision === diskRevision ? 'CURRENT' : 'STALE';
  return {
    state,
    alive,
    suppressed: recovery.suppressed === true,
    pid: Number(recovery.pid || 0) || null,
    instanceId: String(recovery.instance_id || '') || null,
    startedAtUnixMs: Number(recovery.started_at_unix_ms || 0) || null,
    runtimeMode: String(recovery.runtime_mode || '') || null,
    runningRevision,
    diskRevision,
    revisionState: String(revision.state || '') || null,
    updatePending: revision.update_pending === true
  };
}

function activationSourceCheckpoint(observation) {
  try {
    return sourceCheckpointForActivation(observation?.status, 'electron_ui');
  } catch (error) {
    const code = error?.code === 'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE'
      ? 'DEV_UI_ACTIVATION_CHECKPOINT_UNAVAILABLE'
      : error?.code === 'ACTIVATION_SOURCE_CHECKPOINT_INVALID'
        ? 'DEV_UI_ACTIVATION_CHECKPOINT_INVALID'
        : 'DEV_UI_CHECKPOINT_NOT_ACTIVATABLE';
    throw lifecycleError(code, String(error?.message || 'Electron UI activation checkpoint is invalid.'), error?.details || {});
  }
}

function unavailableObservation(error = null) {
  return {
    hostAvailable: false,
    installationMatches: null,
    descriptor: null,
    client: null,
    status: null,
    ui: uiObservation(),
    errorCode: String(error?.code || '') || null
  };
}

function knownUnavailable(error) {
  return ['ENOENT', 'RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_HOST_UNAVAILABLE', 'ECONNREFUSED'].includes(String(error?.code || ''));
}

function refreshOperationId(now = Date.now()) {
  const value = `full-clean-refresh-${Number(now).toString(36)}-${crypto.randomBytes(12).toString('hex')}`;
  if (!REFRESH_OPERATION_ID_PATTERN.test(value)) {
    throw lifecycleError('DEV_UI_REFRESH_OPERATION_INVALID', 'The full-system refresh operation identity is invalid.');
  }
  return value;
}

function refreshEpochState(record) {
  if (!record || typeof record !== 'object' || Array.isArray(record)) return '';
  // Recovery Host's IPC projection uses `state=UPDATE_INCOMPLETE` and carries
  // the durable coordinator state in `epoch_state`.  The raw store uses
  // top-level `state`; prefer an explicit terminal top-level state so stale
  // nested/projection observations can never mask durable FAILED or READY.
  const normalize = (value) => String(value || '').trim().toUpperCase().replace(/[ -]+/g, '_');
  const topLevel = normalize(record.state);
  const explicit = normalize(record.epoch_state);
  if (topLevel === 'FAILED' || topLevel === 'READY') return topLevel;
  if (explicit) return explicit;
  return topLevel;
}

function refreshEpochFailure(record, fallbackCode = 'DEV_UI_REFRESH_EPOCH_FAILED') {
  const error = record?.error && typeof record.error === 'object' ? record.error : {};
  const code = String(error.code || '').trim() || fallbackCode;
  const message = String(error.message || '').trim()
    || 'The durable activation epoch is failed and remains admission-closed.';
  return lifecycleError(code, message, {
    activation_epoch_id: String(record?.activation_epoch_id || '').trim() || null,
    operation_id: String(record?.operation_id || '').trim() || null,
    durable_error: error || null
  });
}

/**
 * Classify the current durable activation record for the refresh guard.
 *
 * `activationRecord()` intentionally remains a tolerant status fallback.  The
 * refresh mutation path calls this classifier only through the strict reader
 * so malformed/unreadable state cannot be mistaken for "no epoch".
 */
function classifyRefreshEpoch(record, now = Date.now()) {
  if (record === null || record === undefined) {
    return { kind: 'none', state: 'NONE', record: null };
  }
  if (!record || typeof record !== 'object' || Array.isArray(record)) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'The durable activation epoch could not be classified safely.',
      { reason: 'record_not_object' }
    );
  }
  const state = refreshEpochState(record);
  const epochId = String(record.activation_epoch_id || record.epoch_id || '').trim();
  const operationId = String(record.operation_id || '').trim();

  // READY is terminal only when the durable admission boundary is explicit.
  // A stale nested projection/error must not turn a valid READY/open record
  // into an expired active request.
  if (REFRESH_TERMINAL_EPOCH_STATES.has(state)) {
    if (state === 'FAILED') return { kind: 'terminal', state, epochId, operationId, record };
    const admission = String(record.admission_state || '').trim().toUpperCase();
    if (admission === 'OPEN') {
      return {
        kind: 'terminal',
        state,
        epochId,
        operationId,
        record
      };
    }
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'The durable READY activation epoch has no explicit OPEN admission boundary.',
      { activation_epoch_id: epochId || null, operation_id: operationId || null, admission_state: admission || null }
    );
  }
  if (!REFRESH_ACTIVE_EPOCH_STATES.has(state)) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      `The durable activation epoch state is unknown: ${state || 'MISSING'}.`,
      { activation_epoch_id: epochId || null, operation_id: operationId || null, state: state || null }
    );
  }
  if (!epochId || !operationId) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'An active durable activation epoch is missing its immutable identity.',
      { activation_epoch_id: epochId || null, operation_id: operationId || null, state }
    );
  }
  if (!isFullCleanRefreshEpoch(record)) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_CONFLICT',
      'An active activation epoch belongs to a non-refresh operation; npm run dev:refresh will not adopt it as a process refresh.',
      {
        activation_epoch_id: epochId || null,
        operation_id: operationId || null,
        state,
        mode: String(record.mode || '').trim() || null,
        refresh: record.metadata?.refresh === true,
        source_checkpoint_present: !(record.source_checkpoint === undefined
          || record.source_checkpoint === null
          || record.source_checkpoint === '')
      }
    );
  }
  const expiryCandidates = [
    record.expires_at_unix_ms,
    record.expiresAtUnixMs,
    record.metadata?.expires_at_unix_ms,
    record.metadata?.expiresAtUnixMs
  ];
  const rawExpiry = expiryCandidates.find((value) => value !== undefined && value !== null && value !== '');
  const expiresAtUnixMs = Number(rawExpiry);
  if (!Number.isFinite(expiresAtUnixMs) || expiresAtUnixMs <= 0) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'An active durable activation epoch is missing a finite positive expiry.',
      { activation_epoch_id: epochId, operation_id: operationId, state, expires_at_unix_ms: rawExpiry ?? null }
    );
  }
  const nowMs = Number(now);
  if (!Number.isFinite(nowMs)) {
    throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', 'The lifecycle clock is unavailable while checking the active epoch.', {
      activation_epoch_id: epochId,
      operation_id: operationId,
      state
    });
  }
  if (expiresAtUnixMs <= nowMs) {
    // Only an immutable, validated process-refresh intent reaches here.  Let
    // the official current-checkout bootstrap terminalize that stale epoch and
    // create a fresh operation; never reconcile or mutate it as still active.
    return {
      kind: 'expired',
      state,
      epochId,
      operationId,
      expiresAtUnixMs,
      record
    };
  }
  return {
    kind: 'active',
    state,
    epochId,
    operationId,
    expiresAtUnixMs,
    record
  };
}

async function readStrictRefreshEpoch(deps) {
  if (typeof deps?.activationRecordStrict !== 'function') return null;
  let record;
  try {
    // The production reader is synchronous today, but awaiting here keeps the
    // guard deterministic for a connector-backed test/store implementation.
    record = await deps.activationRecordStrict();
  } catch (error) {
    if (error?.code === 'ACTIVATION_REQUEST_EXPIRED') throw error;
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'The durable activation epoch could not be read safely before refresh.',
      { cause_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID'), cause_message: String(error?.message || '') }
    );
  }
  return classifyRefreshEpoch(record);
}

function transientEpochReadError(error) {
  if (String(error?.code || '') !== 'DEV_UI_REFRESH_EPOCH_UNCERTAIN') return false;
  return ['ACTIVATION_EPOCH_STORE_INVALID', 'EACCES', 'EBUSY', 'EPERM', 'ENOENT']
    .includes(String(error?.details?.cause_code || ''));
}

/**
 * After the supported bootstrap has crossed its process boundary, the epoch
 * writer can briefly be replacing its primary/backup projection on Windows.
 * This is not authority to ignore a bad epoch: retry only that narrow
 * read-availability class, for a short bounded window, then return the exact
 * classified record for the caller's normal operation/identity checks.
 */
async function readPostMutationRefreshEpoch(deps, operationId, phase) {
  const timeoutMs = Math.max(0, Number(deps?.epochReadRetryTimeoutMs ?? DEFAULT_EPOCH_READ_RETRY_TIMEOUT_MS));
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (true) {
    try {
      return await readStrictRefreshEpoch(deps);
    } catch (error) {
      if (!transientEpochReadError(error)) throw error;
      lastError = error;
    }
    if (Date.now() >= deadline) {
      throw lifecycleError(
        'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
        'The durable activation epoch did not become readable after the supported refresh mutation.',
        {
          operation_id: String(operationId || '').trim() || null,
          phase: String(phase || 'post_mutation').slice(0, 96),
          cause_code: String(lastError?.details?.cause_code || 'ACTIVATION_EPOCH_STORE_INVALID')
        }
      );
    }
    await deps.sleep(deps.pollMs);
  }
}

function assertSameRefreshEpoch(expected, observed, phase = 'refresh') {
  if (!expected || expected.kind !== 'active') return observed;
  if (!observed || observed.kind === 'none') {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_CHANGED',
      `The durable activation epoch disappeared during ${phase}; refusing to start a replacement refresh.`,
      { expected_activation_epoch_id: expected.epochId, expected_operation_id: expected.operationId, phase }
    );
  }
  if (observed.state === 'FAILED') throw refreshEpochFailure(observed.record);
  if (observed.epochId !== expected.epochId || observed.operationId !== expected.operationId) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_CHANGED',
      `The durable activation epoch changed during ${phase}; refusing to start a replacement refresh.`,
      {
        expected_activation_epoch_id: expected.epochId,
        observed_activation_epoch_id: observed.epochId || null,
        expected_operation_id: expected.operationId,
        observed_operation_id: observed.operationId || null,
        phase
      }
    );
  }
  if (observed.kind === 'expired') {
    throw lifecycleError(
      'ACTIVATION_REQUEST_EXPIRED',
      `The durable activation epoch expired during ${phase} and remains admission-closed.`,
      {
        activation_epoch_id: observed.epochId,
        operation_id: observed.operationId,
        expires_at_unix_ms: observed.expiresAtUnixMs,
        phase
      }
    );
  }
  return observed;
}

function refreshRuntimeState(paths) {
  try {
    const state = readJson(paths.stateFile(), {});
    return state && typeof state === 'object' ? state : {};
  } catch {
    return {};
  }
}

function activationCensus(record) {
  const verification = record?.verification;
  if (!verification || typeof verification !== 'object') return null;
  if (verification.final_census && typeof verification.final_census === 'object') {
    return verification.final_census;
  }
  if (String(verification.activation_epoch_id || '') === String(record?.activation_epoch_id || '')) {
    return verification;
  }
  return null;
}

const CONNECTOR_PENDING_FATAL_REASONS = new Set([
  'CURRENT_CONTRACT_SHA256_INVALID',
  'PROCESS_INSTANCE_ID_MISSING',
  'SERVER_INSTANCE_ID_MISSING',
  'VALIDATION_TIMESTAMP_INVALID',
  'DISCOVERY_FROM_FUTURE',
  'CONNECTOR_CONTRACT_STATUS_UNAVAILABLE',
  'CONNECTOR_CONTRACT_UNAVAILABLE',
  'STATUS_CURRENT_SHA256_MISMATCH'
]);

function connectorGateIsPending(census) {
  const validation = census?.connector_validation;
  if (!validation || typeof validation !== 'object' || Array.isArray(validation)) return false;
  if (validation.valid === true) return true;
  if (!Array.isArray(validation.reasons) || validation.reasons.length === 0) return false;
  return validation.reasons.every((reason) => (
    typeof reason === 'string' && !CONNECTOR_PENDING_FATAL_REASONS.has(reason)
  ));
}

function refreshRuntimeReady(runtime, state, epochId, processAlive, record = null, previous = {}) {
  const revision = runtime?.codeRevision?.codingMcp || {};
  const epochCandidates = [
    runtime?.activationEpoch?.activation_epoch_id,
    state?.nativeActivationEpochId,
    state?.tunnelActivationEpochId
  ].map((value) => String(value || '').trim()).filter(Boolean);
  const epochMatches = Boolean(epochId)
    && epochCandidates.length >= 2
    && epochCandidates.every((value) => value === epochId);
  const mcpPid = Number(state?.nativePid || 0);
  const tunnelPid = Number(state?.tunnelPid || 0);
  const census = activationCensus(record);
  const exactCensusPresent = Boolean(census
    && String(census.activation_epoch_id || '') === epochId);
  const componentCensusVerified = Boolean(census
    && String(census.activation_epoch_id || '') === epochId
    && census.process_identity_verified === true
    && census.process_identity_changed === true
    && census.tunnel_identity_changed === true
    && census.tunnel_health_verified === true
    && census.recovery_host_revision_matches === true
    && census.recovery_host_epoch_matches === true
    && census.ui_verified === true
    && census.recovery_plane_identity_changed === true
    && census.recovery_plane_epoch_matches === true
    && census.recovery_plane_verified === true
    && census.projection_rebuild_verified === true
    && census.workspace_matches === true
    && census.device_matches === true
    && census.revision_matches === true
    && census.epoch_matches === true
    && connectorGateIsPending(census));
  const previousMcpPid = Number(previous?.coding_mcp?.pid || 0);
  const previousTunnelPid = Number(previous?.coding_tunnel?.pid || 0);
  const previousRecoveryMcpPid = Number(previous?.recovery_mcp?.pid || 0);
  const previousRecoveryTunnelPid = Number(previous?.recovery_tunnel?.pid || 0);
  const previousHostPid = Number(previous?.recovery_host?.pid || 0);
  const newRecoveryMcpPid = Number(census?.recovery_mcp_pid || 0);
  const newRecoveryTunnelPid = Number(census?.recovery_tunnel_pid || 0);
  const freshPids = Boolean(
    mcpPid > 0 && tunnelPid > 0
    && (!previousMcpPid || mcpPid !== previousMcpPid)
    && (!previousTunnelPid || tunnelPid !== previousTunnelPid)
    && (!previousRecoveryMcpPid || newRecoveryMcpPid !== previousRecoveryMcpPid)
    && (!previousRecoveryTunnelPid || newRecoveryTunnelPid !== previousRecoveryTunnelPid)
    && (!previousHostPid || Number(census?.host_pid || 0) !== previousHostPid)
  );
  // finalCensus probes the Coding Tunnel after the lightweight runtime
  // snapshot. During an activation awaiting real-client discovery that
  // snapshot can still say tunnelRunning=false even though the later, exact
  // PID/epoch/control-plane probe passed. Prefer the stronger census receipt;
  // do not let the earlier observational bit turn a completed process refresh
  // into a CLI timeout.
  const tunnelRunning = exactCensusPresent
    ? census.tunnel_health_verified === true
    : runtime?.tunnelRunning === true;
  return {
    mcpRunning: runtime?.mcpRunning === true,
    tunnelRunning,
    nativeAlive: runtime?.nativeAlive === true,
    revisionMatches: Boolean(revision.running_revision && revision.disk_revision
      && revision.running_revision === revision.disk_revision),
    epochMatches,
    mcpPid: Number.isSafeInteger(mcpPid) && mcpPid > 0 ? mcpPid : null,
    tunnelPid: Number.isSafeInteger(tunnelPid) && tunnelPid > 0 ? tunnelPid : null,
    processIdentitiesPresent: Boolean(String(state?.nativeInstanceId || '').trim()
      && String(state?.tunnelInstanceId || '').trim()),
    ownedProcessesAlive: Boolean(
      mcpPid > 0 && tunnelPid > 0 && processAlive(mcpPid) && processAlive(tunnelPid)
    ),
    componentCensusVerified,
    freshPids,
    census
  };
}

function spawnElectron(executable, appRoot, args, {
  spawnProcess = spawn,
  detached = false,
  windowsHide = false,
  waitForExit = false
} = {}) {
  return new Promise((resolve, reject) => {
    const child = spawnProcess(executable, [appRoot, ...args], {
      detached,
      windowsHide,
      stdio: 'ignore',
      env: { ...process.env, WEBCODEX_PROCESS_ROLE: 'electron-ui' }
    });
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };
    child.once('error', reject);
    child.once('spawn', () => {
      if (detached) child.unref();
      if (!waitForExit) finish({ pid: Number(child.pid || 0) || null });
    });
    if (waitForExit) child.once('exit', (code) => finish({ pid: Number(child.pid || 0) || null, exitCode: Number(code || 0) }));
  });
}

function createRuntimeDependencies(options = {}) {
  const paths = options.paths || createDevelopmentPaths(options);
  const expectedIdentity = paths.runtimeIdentity();
  const executable = options.electronExecutable || paths.executablePath();
  const appRoot = paths.appRoot();
  const revisions = options.revisions || new ComponentRevisionTracker({ paths, refreshIntervalMs: 0 });
  const epochStore = options.epochStore || (
    typeof paths.activationEpochFile === 'function' || typeof paths.dataRoot === 'function'
      ? new ActivationEpochStore({ paths })
      : null
  );
  const spawnProcess = options.spawnProcess || spawn;
  const sleep = options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const output = options.output || ((line) => process.stdout.write(`${line}\n`));
  const ensureHost = options.ensureRecoveryHost || ensureRecoveryHost;
  const suppressDevelopmentSupervisor = options.suppressDevelopmentSupervisor
    || suppressDevelopmentRecoverySupervisor;
  const bootstrapRecoveryHost = options.bootstrapRecoveryHost || bootstrapCurrentRecoveryHost;

  async function inspect() {
    let descriptor;
    try {
      descriptor = loadRecoveryDescriptor(paths);
    } catch (error) {
      if (knownUnavailable(error)) return unavailableObservation(error);
      throw error;
    }
    const installationMatches = descriptor.runtime_mode === 'development'
      && descriptorMatchesInstallation(descriptor, expectedIdentity);
    if (!installationMatches) {
      return {
        ...unavailableObservation(),
        hostAvailable: true,
        installationMatches: false,
        descriptor,
        errorCode: 'DEV_UI_INSTALLATION_MISMATCH'
      };
    }
    const client = new RecoveryIpcClient({ paths });
    let status;
    try {
      status = await client.status(descriptorRequestOptions(descriptor));
    } catch (error) {
      if (knownUnavailable(error)) return unavailableObservation(error);
      throw error;
    }
    return {
      hostAvailable: true,
      installationMatches: true,
      descriptor,
      client,
      status,
      ui: uiObservation(status),
      errorCode: null
    };
  }

  async function inspectRefreshTarget() {
    let descriptor;
    try {
      descriptor = loadRecoveryDescriptor(paths);
    } catch (error) {
      if (knownUnavailable(error)) return unavailableObservation(error);
      throw error;
    }
    const installationMatches = descriptor.runtime_mode === 'development'
      && descriptorMatchesInstallation(descriptor, expectedIdentity);
    if (!installationMatches) {
      return {
        ...unavailableObservation(),
        hostAvailable: true,
        installationMatches: false,
        descriptor,
        errorCode: 'DEV_UI_INSTALLATION_MISMATCH'
      };
    }
    const client = new RecoveryIpcClient({ paths });
    let status = null;
    try {
      status = await client.ping({
        ...descriptorRequestOptions(descriptor),
        timeout: Math.min(8_000, Math.max(1_500, Number(options.refreshProbeTimeoutMs || 8_000)))
      });
    } catch (error) {
      // Descriptor + exact OS identity remain sufficient mutation authority
      // for the external bootstrap. A busy old event loop is precisely one of
      // the states npm run dev:refresh must be able to replace.
      if (!['RECOVERY_REQUEST_TIMEOUT', 'ECONNRESET', 'ECONNREFUSED'].includes(String(error?.code || ''))) {
        throw error;
      }
    }
    return {
      hostAvailable: true,
      installationMatches: true,
      descriptor,
      client,
      status,
      ui: uiObservation(status || {}),
      errorCode: status ? null : 'RECOVERY_STATUS_UNAVAILABLE'
    };
  }

  async function activate(observation) {
    const diskRevision = observation?.ui?.diskRevision;
    if (!diskRevision) {
      throw lifecycleError('DEV_UI_REVISION_UNAVAILABLE', 'Electron UI disk revision is unavailable; controlled activation cannot be authorized.');
    }
    const sourceCheckpoint = activationSourceCheckpoint(observation);
    const now = Date.now();
    const request = {
      operation_id: crypto.randomBytes(18).toString('base64url'),
      component: 'electron_ui',
      requested_at_unix_ms: now,
      expires_at_unix_ms: now + 55_000,
      expected_disk_revision: diskRevision,
      allow_acceptance_pending: false,
      source_checkpoint: sourceCheckpoint
    };
    const exactHost = descriptorRequestOptions(observation.descriptor);
    const preflight = await observation.client.call('code.activation_preflight', [request], exactHost);
    if (preflight?.safe !== true) {
      throw lifecycleError(
        String(preflight?.code || 'DEV_UI_ACTIVATION_REFUSED'),
        `Electron UI activation was refused: ${String(preflight?.code || 'unsafe preflight')}`,
        { preflight }
      );
    }
    if (preflight.code === 'ALREADY_CURRENT') return { request, preflight, operation: null };
    const operation = await observation.client.call('code.activate_update', [request], exactHost);
    if (['failed', 'refused'].includes(String(operation?.state || ''))) {
      throw lifecycleError(
        String(operation?.error?.code || 'DEV_UI_ACTIVATION_FAILED'),
        String(operation?.error?.message || 'Electron UI activation failed.'),
        { operation }
      );
    }
    return { request, preflight, operation };
  }

  async function suppress(observation) {
    const instanceId = String(observation?.ui?.instanceId || '');
    if (!INSTANCE_ID_PATTERN.test(instanceId)) {
      throw lifecycleError('DEV_UI_INSTANCE_UNVERIFIED', 'The live Electron UI instance identity is unavailable or invalid.');
    }
    return observation.client.call(
      'client.suppress_ui_recovery',
      [{ instance_id: instanceId, reason: 'operator_quit' }],
      descriptorRequestOptions(observation.descriptor)
    );
  }

  async function refresh(observation) {
    if (!observation?.client || !observation?.descriptor) {
      throw lifecycleError('DEV_UI_HOST_UNAVAILABLE', 'Recovery Host is unavailable; the full-system refresh cannot be authenticated.');
    }
    const operationId = refreshOperationId();
    try {
      const supervisor = suppressDevelopmentSupervisor();
      if (supervisor?.suppressed !== true && supervisor?.reason !== 'manifest_unavailable') {
        throw lifecycleError(
          'DEV_UI_REFRESH_SUPERVISOR_UNCERTAIN',
          'The persisted development Recovery Supervisor could not be suppressed safely.',
          { reason: supervisor?.reason || 'unknown' }
        );
      }
      const requestedAtUnixMs = Date.now();
      const expectedDiskRevision = revisions.disk('recovery_host', { force: true }).revision;
      const result = await bootstrapRecoveryHost({
        app: { isPackaged: false, getAppPath: () => appRoot },
        paths,
        client: observation.client,
        descriptor: observation.descriptor,
        status: observation.status,
        operationId,
        sourceCheckpoint: null,
        expectedDiskRevision,
        refresh: true,
        forceRefresh: true,
        requestedAtUnixMs,
        // This is a full-system process refresh, not the short 55-second
        // component activation request.  The deadline must cover a cold
        // Electron bootstrap plus the replacement MCP/Tunnel/UI census.
        expiresAtUnixMs: requestedAtUnixMs + Math.min(
          MAX_REFRESH_ACTIVATION_TTL_MS,
          Math.max(
            180_000,
            Number(options.refreshActivationTtlMs || DEFAULT_REFRESH_ACTIVATION_TTL_MS)
          )
        ),
        timeoutMs: Math.min(
          MAX_REFRESH_HOST_TIMEOUT_MS,
          Math.max(5_000, Number(options.refreshHostTimeoutMs || DEFAULT_REFRESH_HOST_TIMEOUT_MS))
        ),
        spawnProcess
      });
      return { operationId, result, expectedDiskRevision };
    } catch (error) {
      throw lifecycleError(
        String(error?.code || 'DEV_UI_REFRESH_FAILED'),
        String(error?.message || 'Full-system refresh was refused by Recovery Host.'),
        {
          operation_id: operationId,
          cause_code: error?.details?.cause_code || error?.code || null,
          termination_cause_code: error?.details?.termination_cause_code || null,
          exit_code: Number.isSafeInteger(error?.details?.exit_code) ? error.details.exit_code : null
        }
      );
    }
  }

  return {
    inspect,
    inspectRefreshTarget,
    ensureRefreshHost: async () => {
      await ensureHost({
        app: { isPackaged: false, getAppPath: () => appRoot },
        paths,
        log: options.log || { warn() {}, error() {} },
        timeoutMs: Math.min(
          MAX_REFRESH_HOST_TIMEOUT_MS,
          Math.max(5_000, Number(options.refreshHostTimeoutMs || DEFAULT_REFRESH_HOST_TIMEOUT_MS))
        ),
        spawnProcess,
        sleep,
        suppressDevelopmentSupervisor
      });
      return inspectRefreshTarget();
    },
    activate,
    suppress,
    refresh,
    runtimeState: () => refreshRuntimeState(paths),
    recoveryPlaneState: () => {
      try { return readJson(paths.recoveryPlaneStateFile(), {}); } catch { return {}; }
    },
    activationRecord: () => {
      try { return epochStore?.current?.() || null; } catch { return null; }
    },
    // Mutation authority must never collapse an unreadable/malformed epoch
    // store into "no current record".  Keep this reader strict and leave the
    // tolerant activationRecord() above for read-only status fallback.
    activationRecordStrict: epochStore ? (() => epochStore.current?.() || null) : null,
    bootstrapResult: (operationId) => {
      try { return readBootstrapResult(paths, operationId) || null; } catch { return null; }
    },
    descriptor: () => {
      try { return loadRecoveryDescriptor(paths); } catch { return null; }
    },
    runtimeSnapshot: (observation) => {
      if (!observation?.client || !observation?.descriptor) return Promise.resolve(null);
      return observation.client.call(
        'runtime.lightweight_snapshot',
        [],
        descriptorRequestOptions(observation.descriptor)
      );
    },
    // `recovery.status` proves descriptor reachability, not admission.  The
    // start command must make one authenticated readiness observation and then
    // require the lightweight MCP/Tunnel projection before claiming a whole
    // development runtime is current.  Connector discovery/ACK intentionally
    // remains a separately reported external-client gate.
    runtimeReadiness: async (observation) => {
      if (!observation?.client || !observation?.descriptor) {
        return { ready: false, reason: 'recovery_host_unavailable', runtime: null, recovery: null };
      }
      let recovery;
      try {
        recovery = await observation.client.ping({
          ...descriptorRequestOptions(observation.descriptor),
          timeout: Math.min(8_000, Math.max(1_500, Number(options.runtimeReadinessProbeTimeoutMs || 5_000)))
        });
      } catch (error) {
        return {
          ready: false,
          reason: 'recovery_host_not_ready',
          runtime: null,
          recovery: null,
          error_code: String(error?.code || 'RECOVERY_REQUEST_FAILED')
        };
      }
      if (recovery?.ready !== true) {
        return {
          ready: false,
          reason: 'recovery_host_not_ready',
          runtime: null,
          recovery,
          error_code: String(recovery?.recovery_bootstrap?.error_code || recovery?.error_code || '') || null
        };
      }
      let runtime;
      try {
        runtime = await observation.client.call(
          'runtime.lightweight_snapshot',
          [],
          descriptorRequestOptions(observation.descriptor)
        );
      } catch (error) {
        return {
          ready: false,
          reason: 'runtime_snapshot_unavailable',
          runtime: null,
          recovery,
          error_code: String(error?.code || 'RECOVERY_REQUEST_FAILED')
        };
      }
      const mcpRunning = runtime?.mcpRunning === true;
      const nativeAlive = runtime?.nativeAlive === true;
      const tunnelRunning = runtime?.tunnelRunning === true;
      return {
        ready: mcpRunning && nativeAlive && tunnelRunning,
        reason: mcpRunning && nativeAlive && tunnelRunning ? 'ready' : 'runtime_components_not_ready',
        runtime,
        recovery,
        mcpRunning,
        nativeAlive,
        tunnelRunning
      };
    },
    launch: () => spawnElectron(executable, appRoot, [], { spawnProcess, detached: true, windowsHide: false }),
    signal: (action, instanceId) => {
      if (!['focus', 'stop', 'control-center'].includes(action) || !INSTANCE_ID_PATTERN.test(String(instanceId || ''))) {
        throw lifecycleError('DEV_UI_SIGNAL_INVALID', 'The Electron single-instance lifecycle signal is invalid.');
      }
      return spawnElectron(executable, appRoot, [`--dev-ui-${action}=${instanceId}`], {
        spawnProcess,
        windowsHide: true,
        waitForExit: true
      });
    },
    processAlive: options.processAlive || isProcessAlive,
    sleep,
    output,
    timeoutMs: Math.max(1_000, Number(options.timeoutMs || DEFAULT_TIMEOUT_MS)),
    runtimeReadyTimeoutMs: Math.max(0, Number(options.runtimeReadyTimeoutMs ?? DEFAULT_RUNTIME_READY_TIMEOUT_MS)),
    epochReadRetryTimeoutMs: Math.max(0, Number(options.epochReadRetryTimeoutMs ?? DEFAULT_EPOCH_READ_RETRY_TIMEOUT_MS)),
    pollMs: Math.max(25, Number(options.pollMs || DEFAULT_POLL_MS))
  };
}

function assertSameDevelopmentInstallation(observation) {
  if (observation?.hostAvailable && observation?.installationMatches === false) {
    throw lifecycleError(
      'DEV_UI_INSTALLATION_MISMATCH',
      'The live Recovery Host belongs to another checkout or installation. Refusing to signal or replace that UI.'
    );
  }
}

async function waitForObservation(deps, predicate, label) {
  const deadline = Date.now() + deps.timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    last = await deps.inspect();
    assertSameDevelopmentInstallation(last);
    if (predicate(last)) return last;
    await deps.sleep(deps.pollMs);
  }
  throw lifecycleError('DEV_UI_LIFECYCLE_TIMEOUT', `Timed out waiting for ${label}.`, {
    last_state: last?.ui?.state || 'UNKNOWN',
    last_pid: last?.ui?.pid || null,
    last_running_revision: last?.ui?.runningRevision || null,
    last_disk_revision: last?.ui?.diskRevision || null
  });
}

function exactUiStopped(observation, previousPid, processAlive) {
  if (observation?.hostAvailable === true && observation?.ui?.state === 'MISSING') {
    return !previousPid || processAlive(previousPid) === false;
  }
  return Boolean(previousPid) && processAlive(previousPid) === false;
}

async function ensureCurrent(deps, initial = null) {
  let observation = initial || await deps.inspect();
  assertSameDevelopmentInstallation(observation);
  if (!observation.hostAvailable) {
    throw lifecycleError(
      'DEV_UI_HOST_UNAVAILABLE',
      'Recovery Host is unavailable; the current Electron UI and installation cannot be proven before launch.'
    );
  }
  if (observation.ui.state === 'MISSING') {
    deps.output('DEV_UI MISSING action=launch host=current');
    await deps.launch();
    return waitForObservation(
      deps,
      (current) => current.hostAvailable && current.installationMatches === true && current.ui.state === 'CURRENT',
      'a current Electron UI registration'
    );
  }
  if (observation.ui.state === 'STALE') {
    deps.output(`DEV_UI STALE action=activate running_revision=${observation.ui.runningRevision || 'none'} disk_revision=${observation.ui.diskRevision || 'none'}`);
    await deps.activate(observation);
    observation = await waitForObservation(
      deps,
      (current) => current.ui.state === 'CURRENT',
      'controlled Electron UI activation'
    );
  }
  if (observation.ui.state !== 'CURRENT') {
    throw lifecycleError('DEV_UI_STATE_UNVERIFIED', `Electron UI state is ${observation.ui.state || 'UNKNOWN'}; current source was not proven live.`);
  }
  return observation;
}

function assertCurrentReceipt(observation) {
  const ui = observation.ui;
  if (!ui.alive || !ui.pid || !INSTANCE_ID_PATTERN.test(String(ui.instanceId || ''))
    || ui.runtimeMode !== 'development' || !ui.runningRevision || ui.runningRevision !== ui.diskRevision) {
    throw lifecycleError(
      'DEV_UI_CURRENT_RECEIPT_INCOMPLETE',
      'Electron UI reported CURRENT without complete PID/instance/mode/revision postflight. Activate the Recovery Host source first.'
    );
  }
  return observation;
}

function runtimeReason(value) {
  const normalized = String(value || '').trim().toLowerCase();
  return /^[a-z0-9][a-z0-9_-]{0,127}$/.test(normalized) ? normalized : 'runtime_readiness_unverified';
}

function reportUiCurrent(deps, observation, action, runtime = null) {
  const ui = assertCurrentReceipt(observation).ui;
  deps.output([
    'DEV_UI UI_CURRENT',
    `action=${action}`,
    `pid=${ui.pid || 'unknown'}`,
    `instance=${ui.instanceId || 'unknown'}`,
    `mode=${ui.runtimeMode || 'unknown'}`,
    `running_revision=${ui.runningRevision || 'unknown'}`,
    `disk_revision=${ui.diskRevision || 'unknown'}`,
    `runtime=${runtime?.ready === true ? 'ready' : 'unavailable'}`,
    `reason=${runtimeReason(runtime?.reason)}`
  ].join(' '));
  return observation;
}

function reportCurrent(deps, observation, action, runtime) {
  if (runtime?.ready !== true) {
    throw lifecycleError(
      'DEV_UI_RUNTIME_UNAVAILABLE',
      'Electron UI is current, but the Recovery Host runtime postflight is unavailable.',
      { reason: runtimeReason(runtime?.reason) }
    );
  }
  const ui = assertCurrentReceipt(observation).ui;
  deps.output([
    'DEV_UI CURRENT',
    `action=${action}`,
    `pid=${ui.pid || 'unknown'}`,
    `instance=${ui.instanceId || 'unknown'}`,
    `mode=${ui.runtimeMode || 'unknown'}`,
    `running_revision=${ui.runningRevision || 'unknown'}`,
    `disk_revision=${ui.diskRevision || 'unknown'}`,
    'runtime=ready',
    `mcp_running=${runtime.mcpRunning === true ? 'true' : 'false'}`,
    `native_alive=${runtime.nativeAlive === true ? 'true' : 'false'}`,
    `tunnel_running=${runtime.tunnelRunning === true ? 'true' : 'false'}`
  ].join(' '));
  return observation;
}

async function runtimePostflight(deps, initial) {
  if (typeof deps.runtimeReadiness !== 'function') {
    return {
      observation: initial,
      runtime: { ready: false, reason: 'runtime_readiness_unavailable', error_code: null }
    };
  }
  const deadline = Date.now() + Math.max(0, Number(deps.runtimeReadyTimeoutMs || 0));
  let observation = initial;
  let runtime = null;
  while (true) {
    assertSameDevelopmentInstallation(observation);
    if (!observation?.hostAvailable || observation?.ui?.state !== 'CURRENT') {
      return {
        observation,
        runtime: {
          ready: false,
          reason: observation?.hostAvailable ? 'ui_postflight_lost_current' : 'recovery_host_unavailable',
          error_code: observation?.errorCode || null
        }
      };
    }
    try {
      runtime = await deps.runtimeReadiness(observation);
    } catch (error) {
      runtime = {
        ready: false,
        reason: 'runtime_readiness_unavailable',
        error_code: String(error?.code || 'RECOVERY_REQUEST_FAILED')
      };
    }
    if (runtime?.ready === true || Date.now() >= deadline) return { observation, runtime };
    await deps.sleep(deps.pollMs);
    observation = await deps.inspect();
  }
}

function throwRuntimeUnavailable(deps, observation, action, runtime) {
  const reason = runtimeReason(runtime?.reason);
  reportUiCurrent(deps, observation, action, runtime);
  deps.output([
    'DEV_UI RUNTIME_UNAVAILABLE',
    `action=${action}`,
    `reason=${reason}`,
    `error_code=${String(runtime?.error_code || '') || 'none'}`,
    `mcp_running=${runtime?.mcpRunning === true ? 'true' : 'false'}`,
    `native_alive=${runtime?.nativeAlive === true ? 'true' : 'false'}`,
    `tunnel_running=${runtime?.tunnelRunning === true ? 'true' : 'false'}`
  ].join(' '));
  throw lifecycleError(
    'DEV_UI_RUNTIME_UNAVAILABLE',
    `Electron UI is current but the Recovery Host runtime is unavailable: ${reason}.`,
    {
      reason,
      error_code: String(runtime?.error_code || '') || null,
      mcp_running: runtime?.mcpRunning === true,
      native_alive: runtime?.nativeAlive === true,
      tunnel_running: runtime?.tunnelRunning === true
    }
  );
}

async function statusLifecycle(deps) {
  const observation = await deps.inspect();
  const ui = observation?.ui || uiObservation();
  const host = observation?.hostAvailable === true ? 'available' : 'unavailable';
  const installation = observation?.installationMatches === true ? 'current'
    : observation?.installationMatches === false ? 'mismatch' : 'unknown';
  let runtime = null;
  if (observation?.hostAvailable === true
    && observation?.installationMatches === true
    && typeof deps.runtimeSnapshot === 'function') {
    try {
      runtime = await deps.runtimeSnapshot(observation);
    } catch (error) {
      if (String(error?.code || '') !== 'RECOVERY_REQUEST_TIMEOUT'
        || typeof deps.activationRecord !== 'function') throw error;
      // A cold activation census can keep the Recovery Host event loop busy
      // longer than the ordinary IPC read timeout.  Status is read-only, so
      // fall back to the durable epoch's most recent verified runtime
      // projection instead of reporting the whole host as unavailable.
      const census = activationCensus(deps.activationRecord());
      runtime = census?.runtime && typeof census.runtime === 'object'
        ? census.runtime : null;
    }
  }
  const connectorState = String(runtime?.connectorContractState || 'UNAVAILABLE');
  const connectorRefreshRequired = typeof runtime?.connectorRefreshRequired === 'boolean'
    ? String(runtime.connectorRefreshRequired)
    : 'unknown';
  const connectorAckPending = typeof runtime?.connectorAcknowledgementPending === 'boolean'
    ? String(runtime.connectorAcknowledgementPending)
    : 'unknown';
  const connectorCurrentSha = String(runtime?.toolContract?.sha256 || '') || 'none';
  const connectorAckSha = String(runtime?.connectorContractAcknowledgedSha256 || '') || 'none';
  const connectorRediscoveredAt = String(runtime?.connectorRediscoveredAt || '') || 'none';
  const connectorFreshnessMode = String(runtime?.connectorFreshnessMode || '') || 'none';
  const connectorCompatibilityAcknowledgedAt = String(runtime?.connectorCompatibilityAcknowledgedAt || '') || 'none';
  const mcpRevision = runtime?.codeRevision?.codingMcp && typeof runtime.codeRevision.codingMcp === 'object'
    ? runtime.codeRevision.codingMcp
    : {};
  const booleanStatus = (value) => typeof value === 'boolean' ? String(value) : 'unknown';
  const connectorRediscovered = booleanStatus(runtime?.connectorRediscovered);
  const snapshotAgeMs = Number.isFinite(runtime?.snapshotAgeMs) ? String(runtime.snapshotAgeMs) : 'none';
  deps.output([
    'DEV_UI STATUS',
    `state=${ui.state || 'UNKNOWN'}`,
    `host=${host}`,
    `installation=${installation}`,
    `pid=${ui.pid || 'none'}`,
    `instance=${ui.instanceId || 'none'}`,
    `mode=${ui.runtimeMode || 'none'}`,
    `running_revision=${ui.runningRevision || 'none'}`,
    `disk_revision=${ui.diskRevision || 'none'}`,
    `update_pending=${ui.updatePending === true ? 'true' : 'false'}`,
    'revision_scope=electron_ui',
    `mcp_revision_state=${String(mcpRevision.state || '') || 'unknown'}`,
    `mcp_running_revision=${String(mcpRevision.running_revision || '') || 'none'}`,
    `mcp_disk_revision=${String(mcpRevision.disk_revision || '') || 'none'}`,
    `mcp_update_pending=${booleanStatus(mcpRevision.update_pending)}`,
    `mcp_revision_checked_at=${String(mcpRevision.checked_at || '') || 'none'}`,
    `components_ready=${booleanStatus(runtime?.componentsReady)}`,
    `fully_ready=${booleanStatus(runtime?.fullyReady)}`,
    `runtime_update_incomplete=${booleanStatus(runtime?.updateIncomplete)}`,
    `runtime_telemetry_available=${booleanStatus(runtime?.telemetryAvailable)}`,
    `runtime_signal_stale=${booleanStatus(runtime?.signalStale)}`,
    `runtime_snapshot_source=${String(runtime?.snapshotSource || '') || 'none'}`,
    `runtime_snapshot_age_ms=${snapshotAgeMs}`,
    `connector_state=${connectorState}`,
    `connector_rediscovered=${connectorRediscovered}`,
    `connector_rediscovered_at=${connectorRediscoveredAt}`,
    `connector_freshness_mode=${connectorFreshnessMode}`,
    `connector_compatibility_acknowledged_at=${connectorCompatibilityAcknowledgedAt}`,
    `connector_refresh_required=${connectorRefreshRequired}`,
    `connector_ack_pending=${connectorAckPending}`,
    `connector_current_sha=${connectorCurrentSha}`,
    `connector_ack_sha=${connectorAckSha}`,
    `error_code=${observation?.errorCode || 'none'}`
  ].join(' '));
  return observation;
}

async function startLifecycle(deps) {
  const initial = await deps.inspect();
  assertSameDevelopmentInstallation(initial);
  // Start is also the supported cold-start entry point. Reuse full-clean's
  // exact installation/census/epoch guards, rather than creating children
  // under a terminal READY record from a previous process or Windows boot.
  const hostAbsent = !initial.hostAvailable
    && ['ENOENT', 'RECOVERY_DESCRIPTOR_STALE'].includes(initial.errorCode);
  let runtimeAbsent = false;
  if (initial.hostAvailable && typeof deps.runtimeSnapshot === 'function') {
    // A failed observation is not absence and must not trigger a refresh.
    const runtime = await deps.runtimeSnapshot(initial).catch(() => null);
    const state = typeof deps.runtimeState === 'function' ? deps.runtimeState() : null;
    runtimeAbsent = Boolean(state && state.manualStop !== true && typeof deps.processAlive === 'function'
      && runtime?.telemetryAvailable === true && runtime?.signalStale === false
      && runtime?.snapshotBusy !== true && runtime?.busy !== true && runtime?.recovering !== true
      && runtime?.mcpRunning === false && runtime?.nativeAlive === false && runtime?.tunnelRunning === false
      && (!state.nativePid || deps.processAlive(state.nativePid) === false)
      && (!state.tunnelPid || deps.processAlive(state.tunnelPid) === false));
  }
  if (hostAbsent || runtimeAbsent) {
    deps.output(`DEV_UI START action=cold_start reason=${hostAbsent ? 'host_absent' : 'runtime_stopped'} lifecycle=full_clean`);
    return refreshLifecycle(deps);
  }
  const observation = await ensureCurrent(deps, initial);
  if (observation.ui.instanceId) await deps.signal('focus', observation.ui.instanceId);
  const verified = await deps.inspect();
  assertSameDevelopmentInstallation(verified);
  if (verified.ui.state !== 'CURRENT') {
    throw lifecycleError('DEV_UI_POSTFLIGHT_FAILED', 'Electron UI lost current-source status after the focus signal.');
  }
  const postflight = await runtimePostflight(deps, verified);
  if (postflight.runtime?.ready !== true) {
    return throwRuntimeUnavailable(deps, postflight.observation, 'start', postflight.runtime);
  }
  return reportCurrent(deps, postflight.observation, 'start', postflight.runtime);
}

async function controlCenterLifecycle(deps) {
  const observation = await ensureCurrent(deps);
  assertCurrentReceipt(observation);
  await deps.signal('control-center', observation.ui.instanceId);
  const verified = await deps.inspect();
  assertSameDevelopmentInstallation(verified);
  if (verified.ui.state !== 'CURRENT' || verified.ui.instanceId !== observation.ui.instanceId) {
    throw lifecycleError(
      'DEV_UI_CONTROL_CENTER_POSTFLIGHT_FAILED',
      'Electron Control Center did not retain the exact current UI instance after the guarded open signal.'
    );
  }
  deps.output(`DEV_UI CONTROL_CENTER action=open pid=${verified.ui.pid || 'unknown'} instance=${verified.ui.instanceId} running_revision=${verified.ui.runningRevision} disk_revision=${verified.ui.diskRevision}`);
  return verified;
}

async function stopLifecycle(deps) {
  let observation = await deps.inspect();
  assertSameDevelopmentInstallation(observation);
  if (!observation.hostAvailable) {
    throw lifecycleError(
      'DEV_UI_HOST_UNAVAILABLE',
      'Recovery Host is unavailable; the exact Electron UI instance cannot be proven stopped.'
    );
  }
  if (observation.ui.state === 'MISSING') {
    deps.output('DEV_UI STOPPED action=stop services=preserved reason=ui_not_running');
    return observation;
  }
  if (observation.ui.state === 'STALE') observation = await ensureCurrent(deps, observation);
  assertCurrentReceipt(observation);
  if (!observation.ui.instanceId || !observation.ui.pid || !deps.processAlive(observation.ui.pid)) {
    throw lifecycleError('DEV_UI_INSTANCE_UNVERIFIED', 'The registered Electron UI process is not alive under the reported exact PID.');
  }
  await deps.suppress(observation);
  await deps.signal('stop', observation.ui.instanceId);
  const previousPid = observation.ui.pid;
  const stopped = await waitForObservation(
    deps,
    (current) => exactUiStopped(current, previousPid, deps.processAlive),
    'the exact Electron UI process to exit'
  );
  deps.output(`DEV_UI STOPPED action=stop previous_pid=${observation.ui.pid} previous_instance=${observation.ui.instanceId} services=preserved`);
  return stopped;
}

async function replaceLifecycle(deps) {
  let observation = await deps.inspect();
  assertSameDevelopmentInstallation(observation);
  if (!observation.hostAvailable || observation.ui.state === 'MISSING') {
    const started = await ensureCurrent(deps, observation);
    const postflight = await runtimePostflight(deps, started);
    if (postflight.runtime?.ready !== true) {
      return throwRuntimeUnavailable(deps, postflight.observation, 'replace', postflight.runtime);
    }
    return reportCurrent(deps, postflight.observation, 'replace', postflight.runtime);
  }

  observation = await ensureCurrent(deps, observation);
  assertCurrentReceipt(observation);
  const previousInstanceId = observation.ui.instanceId;
  const previousPid = observation.ui.pid;
  if (!previousInstanceId || !previousPid || !deps.processAlive(previousPid)) {
    throw lifecycleError('DEV_UI_INSTANCE_UNVERIFIED', 'The current Electron UI handler could not be bound to a live exact process.');
  }

  await deps.suppress(observation);
  await deps.signal('stop', previousInstanceId);
  await waitForObservation(
    deps,
    (current) => exactUiStopped(current, previousPid, deps.processAlive),
    'the current Electron UI handler to stop'
  );
  await deps.launch();
  const replacement = await waitForObservation(
    deps,
    (current) => current.ui.state === 'CURRENT'
      && Boolean(current.ui.instanceId)
      && current.ui.instanceId !== previousInstanceId,
    'a new current Electron UI instance'
  );
  assertCurrentReceipt(replacement);
  const postflight = await runtimePostflight(deps, replacement);
  if (postflight.runtime?.ready !== true) {
    return throwRuntimeUnavailable(deps, postflight.observation, 'replace', postflight.runtime);
  }
  deps.output(`DEV_UI REPLACED previous_pid=${previousPid} previous_instance=${previousInstanceId} new_pid=${replacement.ui.pid || 'unknown'} new_instance=${replacement.ui.instanceId} mode=${replacement.ui.runtimeMode || 'unknown'} running_revision=${replacement.ui.runningRevision} disk_revision=${replacement.ui.diskRevision}`);
  return postflight.observation;
}

function previousRefreshIdentities(observation, runtimeState = {}, recoveryPlaneState = {}) {
  return {
    recovery_host: {
      pid: Number(observation?.descriptor?.owner_pid || 0) || null,
      instance_id: String(observation?.descriptor?.instance_id || '') || null
    },
    electron_ui: {
      pid: Number(observation?.ui?.pid || 0) || null,
      instance_id: String(observation?.ui?.instanceId || '') || null
    },
    coding_mcp: {
      pid: Number(runtimeState?.nativePid || 0) || null,
      instance_id: String(runtimeState?.nativeInstanceId || '') || null
    },
    coding_tunnel: {
      pid: Number(runtimeState?.tunnelPid || 0) || null,
      instance_id: String(runtimeState?.tunnelInstanceId || '') || null
    },
    recovery_mcp: {
      pid: Number(recoveryPlaneState?.recoveryMcpPid || 0) || null,
      instance_id: String(recoveryPlaneState?.recoveryMcpInstanceId || '') || null
    },
    recovery_tunnel: {
      pid: Number(recoveryPlaneState?.recoveryTunnelPid || 0) || null,
      instance_id: String(recoveryPlaneState?.recoveryTunnelInstanceId || '') || null
    }
  };
}

function previousRefreshIdentitiesFromRecord(record) {
  const evidence = record?.component_evidence;
  if (!evidence || typeof evidence !== 'object' || Array.isArray(evidence)) {
    throw lifecycleError(
      'DEV_UI_REFRESH_EPOCH_UNCERTAIN',
      'Active refresh reconciliation has no immutable component identity evidence.',
      { activation_epoch_id: String(record?.activation_epoch_id || '') || null }
    );
  }
  const hasOwn = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const normalizePid = (value, label, { required = false } = {}) => {
    if (value === undefined) {
      if (required) throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence is missing ${label}.`, { component: label });
      return null;
    }
    if (value === null || value === '') return null;
    const pid = Number(value);
    if (!Number.isSafeInteger(pid) || pid <= 0) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence has an invalid ${label}.`, { component: label, pid: value });
    }
    return pid;
  };
  const normalizeId = (value, label, { required = false } = {}) => {
    if (value === undefined) {
      if (required) throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence is missing ${label}.`, { component: label });
      return null;
    }
    if (value === null || value === '') return null;
    const id = String(value).trim();
    if (!id) return null;
    if (id.length > 256) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence has an invalid ${label}.`, { component: label });
    }
    return id;
  };
  const pair = (component, value, idKeys = ['instance_id']) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence for ${component} is missing or malformed.`, { component });
    }
    // FullCleanActivation serializes an explicit null for an absent process;
    // requiring both keys to be present distinguishes that observation from a
    // truncated/tampered evidence object.
    if (!hasOwn(value, 'pid')) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence for ${component} is missing pid.`, { component });
    }
    if (!idKeys.some((key) => hasOwn(value, key))) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence for ${component} is missing instance identity.`, { component });
    }
    const pid = normalizePid(value.pid, `${component}.pid`);
    let id = null;
    for (const key of idKeys) {
      if (!hasOwn(value, key)) continue;
      const candidate = normalizeId(value[key], `${component}.${key}`);
      if (candidate) {
        // A Coding MCP evidence object legitimately carries several distinct
        // identities (process/server/supervisor).  Validate every supplied
        // value, but use the first role-specific identity as the baseline;
        // they are not aliases that must compare equal.
        if (!id) id = candidate;
      }
    }
    // A process identity without its corresponding PID (or vice versa) is
    // ambiguous: it cannot prove that the replacement is fresh.
    if ((pid && !id) || (!pid && id)) {
      throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', `Component evidence for ${component} has an incomplete process identity pair.`, { component });
    }
    return { pid, instance_id: id };
  };

  const result = {
    recovery_host: pair('recovery_host', evidence.recovery_host),
    electron_ui: pair('electron_ui', evidence.electron_ui),
    coding_mcp: pair('coding_mcp', evidence.coding_mcp, [
      'instance_id', 'process_instance_id', 'server_instance_id', 'supervisor_instance_id'
    ]),
    coding_tunnel: pair('coding_tunnel', evidence.coding_tunnel),
    recovery_mcp: pair('recovery_mcp', evidence.recovery_mcp, ['instance_id', 'process_instance_id']),
    recovery_tunnel: pair('recovery_tunnel', evidence.recovery_tunnel, ['instance_id', 'process_instance_id'])
  };
  return result;
}

function sameRefreshIdentityBaseline(left, right) {
  try { return JSON.stringify(left) === JSON.stringify(right); } catch { return false; }
}

async function refreshLifecycle(deps) {
  // Read the durable epoch before touching the Recovery Host.  A previous
  // invocation may have already crossed the stop/handoff boundary; forcing a
  // second bootstrap in that window can tear down the replacement and then be
  // rejected by ActivationEpochStore as ACTIVATION_EPOCH_ACTIVE.
  const strictEpochGuard = typeof deps.activationRecordStrict === 'function';
  const guardedEpoch = strictEpochGuard ? await readStrictRefreshEpoch(deps) : null;
  let reconcileEpoch = guardedEpoch?.kind === 'active' ? guardedEpoch : null;
  let reconcilePrevious = reconcileEpoch
    ? previousRefreshIdentitiesFromRecord(reconcileEpoch.record)
    : null;

  let before = typeof deps.inspectRefreshTarget === 'function'
    ? await deps.inspectRefreshTarget()
    : await deps.inspect();
  assertSameDevelopmentInstallation(before);
  if (!before.hostAvailable || !before.client || !before.descriptor) {
    if (typeof deps.ensureRefreshHost !== 'function') {
      throw lifecycleError(
        'DEV_UI_HOST_UNAVAILABLE',
        'Recovery Host is unavailable and npm run dev:refresh has no authenticated bootstrap path.'
      );
    }
    deps.output('DEV_UI REFRESH bootstrap=RecoveryHost source=current-checkout');
    before = await deps.ensureRefreshHost();
    assertSameDevelopmentInstallation(before);
    if (!before?.hostAvailable || !before?.client || !before?.descriptor) {
      throw lifecycleError(
        'DEV_UI_HOST_BOOTSTRAP_FAILED',
        'npm run dev:refresh could not establish an authenticated current-checkout Recovery Host before refresh.'
      );
    }
  }
  // Re-read immediately before any full-clean mutation.  If another process
  // created an active epoch while the host was being inspected/bootstrapped,
  // reconcile that transaction rather than asking the old host to start a
  // second one.  If an epoch was active at entry, disappearance/change is a
  // hard continuity failure, never evidence that a replacement is safe.
  if (strictEpochGuard) {
    const beforeMutationEpoch = await readStrictRefreshEpoch(deps);
    if (reconcileEpoch) {
      const observed = assertSameRefreshEpoch(reconcileEpoch, beforeMutationEpoch, 'preflight');
      if (!sameRefreshIdentityBaseline(reconcilePrevious, previousRefreshIdentitiesFromRecord(observed.record))) {
        throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', 'The active refresh epoch identity evidence changed during reconciliation.', {
          activation_epoch_id: reconcileEpoch.epochId,
          operation_id: reconcileEpoch.operationId
        });
      }
    } else if (beforeMutationEpoch?.kind === 'active') {
      reconcileEpoch = beforeMutationEpoch;
      reconcilePrevious = previousRefreshIdentitiesFromRecord(reconcileEpoch.record);
    }
  }

  const beforeState = typeof deps.runtimeState === 'function' ? deps.runtimeState() : {};
  const beforeRecoveryPlane = typeof deps.recoveryPlaneState === 'function'
    ? deps.recoveryPlaneState() : {};
  const previous = reconcileEpoch
    ? reconcilePrevious
    : previousRefreshIdentities(before, beforeState, beforeRecoveryPlane);
  const previousHostInstance = String(previous?.recovery_host?.instance_id || before.descriptor.instance_id || '').trim();
  const previousUiInstance = String(previous?.electron_ui?.instance_id || before.ui?.instanceId || '').trim();

  let request;
  if (reconcileEpoch) {
    deps.output([
      'DEV_UI REFRESH RECONCILE',
      'action=full_clean',
      `epoch=${reconcileEpoch.epochId}`,
      `operation=${reconcileEpoch.operationId}`,
      `state=${reconcileEpoch.state}`
    ].join(' '));
    request = {
      operationId: reconcileEpoch.operationId,
      operation_id: reconcileEpoch.operationId,
      activation_epoch_id: reconcileEpoch.epochId,
      reconciled: true,
      result: { activation_epoch_id: reconcileEpoch.epochId, operation_id: reconcileEpoch.operationId }
    };
  } else {
    deps.output([
      'DEV_UI REFRESH',
      'action=full_clean',
      `previous_host=${previousHostInstance || 'unknown'}`,
      `previous_ui=${previousUiInstance || 'none'}`,
      'services=RecoveryHost,CodingMCP,CodingTunnel,RecoveryMCP,RecoveryTunnel,ElectronUI'
    ].join(' '));
    request = await deps.refresh(before);
  }
  let epochId = String(
    request?.result?.activation_epoch_id
      || request?.result?.activationEpochId
      || request?.activation_epoch_id
      || ''
  ).trim();
  const hasEpochReader = typeof deps.activationRecord === 'function' || strictEpochGuard;
  let replacementDescriptor = null;
  if (!epochId && hasEpochReader) {
    const deadline = Date.now() + deps.timeoutMs;
    while (Date.now() < deadline) {
      const classified = strictEpochGuard
        ? await readPostMutationRefreshEpoch(deps, request?.operationId, 'locating_refresh_epoch')
        : null;
      // A current terminal record from the predecessor operation can remain
      // visible for a short handoff window while the bootstrap host creates
      // the new durable epoch.  It is not evidence that this request failed;
      // only a FAILED record carrying this request's exact operation may abort
      // the lookup.  The operation/epoch identity remains the authority.
      const requestedOperationId = String(request?.operationId || '').trim();
      if (classified?.kind === 'terminal'
        && classified.state === 'FAILED'
        && (!requestedOperationId || classified.operationId === requestedOperationId)) {
        throw refreshEpochFailure(classified.record);
      }
      if (classified?.kind === 'active'
        && request?.operationId
        && classified.operationId !== String(request.operationId)) {
        throw lifecycleError('DEV_UI_REFRESH_EPOCH_CHANGED', 'A different active activation operation appeared while locating the refresh epoch.', {
          expected_operation_id: String(request.operationId),
          observed_operation_id: classified.operationId,
          observed_activation_epoch_id: classified.epochId
        });
      }
      const record = strictEpochGuard ? classified?.record : deps.activationRecord();
      const descriptor = typeof deps.descriptor === 'function' ? deps.descriptor() : null;
      if (record
        && String(record.operation_id || '') === String(request?.operationId || '')
        && String(record.activation_epoch_id || '')
        && descriptor
        && String(descriptor.instance_id || '') !== previousHostInstance
        && String(descriptor.activation_epoch_id || '') === String(record.activation_epoch_id || '')) {
        epochId = String(record.activation_epoch_id);
        replacementDescriptor = descriptor;
        break;
      }
      const bootstrap = typeof deps.bootstrapResult === 'function'
        ? deps.bootstrapResult(request?.operationId) : null;
      if (bootstrap && ['failed', 'expired'].includes(String(bootstrap.state || ''))) {
        throw lifecycleError(
          String(bootstrap.error?.code || 'DEV_UI_REFRESH_BOOTSTRAP_FAILED'),
          String(bootstrap.error?.message || 'Recovery Host refresh bootstrap failed.'),
          { operation_id: request?.operationId || null, bootstrap }
        );
      }
      await deps.sleep(deps.pollMs);
    }
  }
  if (!epochId) {
    throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNAVAILABLE',
      'Recovery Host refresh did not expose a durable activation epoch.',
      { operation_id: request?.operationId || null });
  }

  let replacement = null;
  if (!hasEpochReader) {
    replacement = await waitForObservation(
      deps,
      (current) => current.hostAvailable
        && current.installationMatches === true
        && String(current.descriptor?.instance_id || '') !== previousHostInstance
        && String(current.descriptor?.activation_epoch_id || '') === epochId
        && current.ui.state === 'CURRENT'
        && Boolean(current.ui.instanceId)
        && current.ui.instanceId !== previousUiInstance,
      'the replacement Recovery Host and Electron UI for the refresh epoch'
    );
    replacementDescriptor = replacement.descriptor;
  }

  const deadline = Date.now() + deps.timeoutMs;
  let lastRuntime = null;
  let lastState = null;
  let lastObservation = replacement || before;
  let lastRecord = null;
  while (Date.now() < deadline) {
    if (reconcileEpoch && strictEpochGuard) {
      // Continuity checks deliberately sit outside the broad transient IPC
      // catch below.  An epoch disappearing, changing identity, expiring, or
      // entering FAILED is a durable error—not a descriptor gap to poll over.
      const observedEpoch = await readPostMutationRefreshEpoch(
        deps,
        reconcileEpoch.operationId,
        'refresh_postflight_continuity'
      );
      const continuous = assertSameRefreshEpoch(reconcileEpoch, observedEpoch, 'postflight');
      if (!sameRefreshIdentityBaseline(reconcilePrevious, previousRefreshIdentitiesFromRecord(continuous.record))) {
        throw lifecycleError('DEV_UI_REFRESH_EPOCH_UNCERTAIN', 'The active refresh epoch identity evidence changed during postflight.', {
          activation_epoch_id: reconcileEpoch.epochId,
          operation_id: reconcileEpoch.operationId
        });
      }
      lastRecord = continuous.record;
    } else {
      lastRecord = typeof deps.activationRecord === 'function' ? deps.activationRecord() : null;
    }
    replacementDescriptor = typeof deps.descriptor === 'function'
      ? (deps.descriptor() || replacementDescriptor) : replacementDescriptor;
    try {
      if (reconcileEpoch) {
        // During a handoff the durable census can briefly lag the new host.
        // Refresh the read-only observation so runtimeSnapshot/UI identity are
        // taken from the replacement client when available; never use this
        // observation as the old-identity baseline (that came from the epoch
        // evidence above).
        const inspectFn = typeof deps.inspectRefreshTarget === 'function'
          ? deps.inspectRefreshTarget : deps.inspect;
        if (typeof inspectFn === 'function') {
          const observed = await inspectFn();
          assertSameDevelopmentInstallation(observed);
          if (observed?.hostAvailable && observed?.descriptor) {
            lastObservation = observed;
            replacementDescriptor = observed.descriptor || replacementDescriptor;
          }
        }
      }
      const census = activationCensus(lastRecord);
      if (census?.runtime) lastRuntime = census.runtime;
      else if (lastObservation?.client && typeof deps.runtimeSnapshot === 'function') {
        lastRuntime = await deps.runtimeSnapshot(lastObservation);
      }
      lastState = typeof deps.runtimeState === 'function' ? deps.runtimeState() : {};
      const readiness = refreshRuntimeReady(
        lastRuntime, lastState, epochId, deps.processAlive, lastRecord, previous
      );
      const uiInstance = String(readiness.census?.ui_instance_id
        || lastObservation?.ui?.instanceId || '').trim();
      const hostCurrent = Boolean(replacementDescriptor
        && String(replacementDescriptor.instance_id || '') !== previousHostInstance
        && String(replacementDescriptor.activation_epoch_id || '') === epochId);
      const exactCensusRequired = hasEpochReader;
      const activationRecordCurrent = !exactCensusRequired || Boolean(lastRecord
        && String(lastRecord.operation_id || '') === String(request?.operationId || '')
        && String(lastRecord.activation_epoch_id || '') === epochId
        && ['VERIFYING', 'READY'].includes(refreshEpochState(lastRecord)));
      if (hostCurrent
        && activationRecordCurrent
        && uiInstance
        && uiInstance !== previousUiInstance
        && readiness.mcpRunning
        && readiness.tunnelRunning
        && readiness.nativeAlive
        && readiness.revisionMatches
        && readiness.epochMatches
        && readiness.processIdentitiesPresent
        && readiness.ownedProcessesAlive
        && (!exactCensusRequired || (readiness.componentCensusVerified && readiness.freshPids))) {
        const durableReady = refreshEpochState(lastRecord) === 'READY'
          && String(lastRecord?.admission_state || '').toUpperCase() === 'OPEN';
        const admission = durableReady || (!exactCensusRequired
          && lastRuntime?.activationEpoch?.admission_open === true)
          ? 'open' : 'closed';
        const fullyReady = exactCensusRequired
          ? durableReady
          : lastRuntime?.fullyReady === true;
        const activation = String(refreshEpochState(lastRecord) || (fullyReady ? 'READY' : 'VERIFYING'));
        const connectorState = String(lastRuntime?.connectorContractState || 'UNAVAILABLE');
        const connector = fullyReady && admission === 'open' ? 'ready' : 'pending';
        deps.output([
          'DEV_UI REFRESHED',
          'action=full_clean',
          `epoch=${epochId}`,
          `activation=${activation}`,
          `host=${replacementDescriptor.instance_id}`,
          `ui=${uiInstance}`,
          `mcp_pid=${readiness.mcpPid || 'unknown'}`,
          `tunnel_pid=${readiness.tunnelPid || 'unknown'}`,
          `mcp=${readiness.mcpRunning ? 'ready' : 'stopped'}`,
          `tunnel=${readiness.tunnelRunning ? 'ready' : 'stopped'}`,
          `admission=${admission}`,
          `fully_ready=${fullyReady ? 'true' : 'false'}`,
          `connector=${connector}`,
          `connector_state=${connectorState}`
        ].join(' '));
        return {
          ...(lastObservation || {}),
          descriptor: replacementDescriptor,
          ui: lastObservation?.ui && String(lastObservation.ui.instanceId || '').trim() === uiInstance
            ? lastObservation.ui
            : {
              ...(lastObservation?.ui || {}),
              state: 'CURRENT',
              alive: true,
              instanceId: uiInstance
            },
          refresh: request,
          epochId,
          runtime: lastRuntime,
          runtimeState: lastState,
          activationRecord: lastRecord,
          readiness
        };
      }
    } catch (error) {
      if (String(error?.code || '').startsWith('DEV_UI_REFRESH_EPOCH_')
        || String(error?.code || '') === 'DEV_UI_INSTALLATION_MISMATCH') {
        throw error;
      }
      // Replacement creates a short descriptor/IPC gap.  Keep polling while
      // preserving the exact identity predicates above; no green state is
      // inferred from a transient port or process alone.
    }
    await deps.sleep(deps.pollMs);
  }
  throw lifecycleError(
    'DEV_UI_REFRESH_POSTFLIGHT_FAILED',
    'Full-system refresh did not prove fresh Recovery Host, MCP, Tunnel, UI and activation-epoch identities.',
    {
      operation_id: request?.operationId || null,
      activation_epoch_id: epochId,
      host_instance_id: replacementDescriptor?.instance_id || lastObservation?.descriptor?.instance_id || null,
      ui_instance_id: lastRecord ? activationCensus(lastRecord)?.ui_instance_id : lastObservation?.ui?.instanceId || null,
      runtime: lastRuntime,
      runtime_state: lastState,
      activation_record: lastRecord
    }
  );
}

async function runLifecycle(action, dependencies = null) {
  const normalized = normalizeAction(action);
  const deps = dependencies || createRuntimeDependencies();
  if (normalized === 'status') return statusLifecycle(deps);
  if (normalized === 'control-center') return controlCenterLifecycle(deps);
  if (normalized === 'stop') return stopLifecycle(deps);
  if (normalized === 'replace') return replaceLifecycle(deps);
  if (normalized === 'refresh') return refreshLifecycle(deps);
  return startLifecycle(deps);
}

async function main(argv = process.argv.slice(2)) {
  try {
    await runLifecycle(normalizeAction(argv[0]));
  } catch (error) {
    const code = String(error?.code || 'DEV_UI_LIFECYCLE_FAILED');
    const cause = String(error?.details?.cause_code || '');
    const exit = error?.details?.exit_code;
    const diagnostics = `${/^[A-Z][A-Z0-9_]{0,119}$/.test(cause) ? ` cause_code=${cause}` : ''}${Number.isSafeInteger(exit) ? ` exit_code=${exit}` : ''}`;
    process.stderr.write(`DEV_UI ERROR code=${code}${diagnostics} message=${String(error?.message || error)}\n`);
    process.exitCode = 1;
  }
}

if (require.main === module) void main();

module.exports = {
  ACTIONS,
  INSTANCE_ID_PATTERN,
  normalizeAction,
  createDevelopmentPaths,
  createRuntimeDependencies,
  uiObservation,
  unavailableObservation,
  activationSourceCheckpoint,
  assertCurrentReceipt,
  exactUiStopped,
  statusLifecycle,
  ensureCurrent,
  startLifecycle,
  controlCenterLifecycle,
  stopLifecycle,
  replaceLifecycle,
  refreshLifecycle,
  runLifecycle,
  lifecycleError,
  refreshOperationId,
  refreshRuntimeReady,
  classifyRefreshEpoch,
  previousRefreshIdentitiesFromRecord,
  readPostMutationRefreshEpoch
};
