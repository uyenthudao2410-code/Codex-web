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

const ACTIONS = new Set(['start', 'stop', 'replace', 'refresh', 'status']);
const INSTANCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const DEFAULT_TIMEOUT_MS = 120_000;
const DEFAULT_POLL_MS = 250;
const REFRESH_OPERATION_ID_PATTERN = /^full-clean-refresh-[A-Za-z0-9_-]{15,127}$/;

function lifecycleError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function normalizeAction(value) {
  const action = String(value || 'start').trim().toLowerCase();
  if (!ACTIONS.has(action)) {
    throw lifecycleError('DEV_UI_ACTION_INVALID', 'Usage: npm start | npm run dev | npm run dev:status | npm run dev:stop | npm run dev:replace');
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
      // the states npm start must be able to replace.
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
        expiresAtUnixMs: requestedAtUnixMs + Math.min(120_000, Math.max(60_000, Number(options.timeoutMs || DEFAULT_TIMEOUT_MS))),
        timeoutMs: 15_000,
        spawnProcess
      });
      return { operationId, result, expectedDiskRevision };
    } catch (error) {
      throw lifecycleError(
        String(error?.code || 'DEV_UI_REFRESH_FAILED'),
        String(error?.message || 'Full-system refresh was refused by Recovery Host.'),
        { operation_id: operationId, cause_code: error?.code || null }
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
        timeoutMs: Math.min(20_000, Math.max(5_000, Number(options.refreshHostTimeoutMs || 15_000))),
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
    launch: () => spawnElectron(executable, appRoot, [], { spawnProcess, detached: true, windowsHide: false }),
    signal: (action, instanceId) => {
      if (!['focus', 'stop'].includes(action) || !INSTANCE_ID_PATTERN.test(String(instanceId || ''))) {
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

function reportCurrent(deps, observation, action) {
  const ui = assertCurrentReceipt(observation).ui;
  deps.output([
    'DEV_UI CURRENT',
    `action=${action}`,
    `pid=${ui.pid || 'unknown'}`,
    `instance=${ui.instanceId || 'unknown'}`,
    `mode=${ui.runtimeMode || 'unknown'}`,
    `running_revision=${ui.runningRevision || 'unknown'}`,
    `disk_revision=${ui.diskRevision || 'unknown'}`
  ].join(' '));
  return observation;
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
    runtime = await deps.runtimeSnapshot(observation);
  }
  const connectorState = String(runtime?.connectorContractState || 'UNAVAILABLE');
  const connectorRediscovered = runtime?.connectorRediscovered === true;
  const connectorRefreshRequired = typeof runtime?.connectorRefreshRequired === 'boolean'
    ? String(runtime.connectorRefreshRequired)
    : 'unknown';
  const connectorAckPending = typeof runtime?.connectorAcknowledgementPending === 'boolean'
    ? String(runtime.connectorAcknowledgementPending)
    : 'unknown';
  const connectorCurrentSha = String(runtime?.toolContract?.sha256 || '') || 'none';
  const connectorAckSha = String(runtime?.connectorContractAcknowledgedSha256 || '') || 'none';
  const connectorRediscoveredAt = String(runtime?.connectorRediscoveredAt || '') || 'none';
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
    `connector_state=${connectorState}`,
    `connector_rediscovered=${connectorRediscovered ? 'true' : 'false'}`,
    `connector_rediscovered_at=${connectorRediscoveredAt}`,
    `connector_refresh_required=${connectorRefreshRequired}`,
    `connector_ack_pending=${connectorAckPending}`,
    `connector_current_sha=${connectorCurrentSha}`,
    `connector_ack_sha=${connectorAckSha}`,
    `error_code=${observation?.errorCode || 'none'}`
  ].join(' '));
  return observation;
}

async function startLifecycle(deps) {
  const observation = await ensureCurrent(deps);
  if (observation.ui.instanceId) await deps.signal('focus', observation.ui.instanceId);
  const verified = await deps.inspect();
  assertSameDevelopmentInstallation(verified);
  if (verified.ui.state !== 'CURRENT') {
    throw lifecycleError('DEV_UI_POSTFLIGHT_FAILED', 'Electron UI lost current-source status after the focus signal.');
  }
  return reportCurrent(deps, verified, 'start');
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
    return reportCurrent(deps, started, 'replace');
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
  deps.output(`DEV_UI REPLACED previous_pid=${previousPid} previous_instance=${previousInstanceId} new_pid=${replacement.ui.pid || 'unknown'} new_instance=${replacement.ui.instanceId} mode=${replacement.ui.runtimeMode || 'unknown'} running_revision=${replacement.ui.runningRevision} disk_revision=${replacement.ui.diskRevision}`);
  return replacement;
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

async function refreshLifecycle(deps) {
  let before = typeof deps.inspectRefreshTarget === 'function'
    ? await deps.inspectRefreshTarget()
    : await deps.inspect();
  assertSameDevelopmentInstallation(before);
  if (!before.hostAvailable || !before.client || !before.descriptor) {
    if (typeof deps.ensureRefreshHost !== 'function') {
      throw lifecycleError(
        'DEV_UI_HOST_UNAVAILABLE',
        'Recovery Host is unavailable and npm start has no authenticated bootstrap path.'
      );
    }
    deps.output('DEV_UI REFRESH bootstrap=RecoveryHost source=current-checkout');
    before = await deps.ensureRefreshHost();
    assertSameDevelopmentInstallation(before);
    if (!before?.hostAvailable || !before?.client || !before?.descriptor) {
      throw lifecycleError(
        'DEV_UI_HOST_BOOTSTRAP_FAILED',
        'npm start could not establish an authenticated current-checkout Recovery Host before refresh.'
      );
    }
  }
  const previousHostInstance = String(before.descriptor.instance_id || '').trim();
  const previousUiInstance = String(before.ui?.instanceId || '').trim();
  const beforeState = typeof deps.runtimeState === 'function' ? deps.runtimeState() : {};
  const beforeRecoveryPlane = typeof deps.recoveryPlaneState === 'function'
    ? deps.recoveryPlaneState() : {};
  const previous = previousRefreshIdentities(before, beforeState, beforeRecoveryPlane);
  deps.output([
    'DEV_UI REFRESH',
    'action=full_clean',
    `previous_host=${previousHostInstance || 'unknown'}`,
    `previous_ui=${previousUiInstance || 'none'}`,
    'services=RecoveryHost,CodingMCP,CodingTunnel,RecoveryMCP,RecoveryTunnel,ElectronUI'
  ].join(' '));

  const request = await deps.refresh(before);
  let epochId = String(
    request?.result?.activation_epoch_id
      || request?.result?.activationEpochId
      || request?.activation_epoch_id
      || ''
  ).trim();
  let replacementDescriptor = null;
  if (!epochId && typeof deps.activationRecord === 'function') {
    const deadline = Date.now() + deps.timeoutMs;
    while (Date.now() < deadline) {
      const record = deps.activationRecord();
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
  if (typeof deps.activationRecord !== 'function') {
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
  let lastObservation = replacement;
  let lastRecord = null;
  while (Date.now() < deadline) {
    lastRecord = typeof deps.activationRecord === 'function' ? deps.activationRecord() : null;
    replacementDescriptor = typeof deps.descriptor === 'function'
      ? (deps.descriptor() || replacementDescriptor) : replacementDescriptor;
    try {
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
      const exactCensusRequired = typeof deps.activationRecord === 'function';
      const activationRecordCurrent = !exactCensusRequired || Boolean(lastRecord
        && String(lastRecord.operation_id || '') === String(request?.operationId || '')
        && String(lastRecord.activation_epoch_id || '') === epochId
        && ['VERIFYING', 'READY'].includes(String(lastRecord.state || '')));
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
        const durableReady = lastRecord?.state === 'READY' && lastRecord?.admission_state === 'OPEN';
        const admission = durableReady || (!exactCensusRequired
          && lastRuntime?.activationEpoch?.admission_open === true)
          ? 'open' : 'closed';
        const fullyReady = exactCensusRequired
          ? durableReady
          : lastRuntime?.fullyReady === true;
        const activation = String(lastRecord?.state || (fullyReady ? 'READY' : 'VERIFYING'));
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
          ui: lastObservation?.ui || { state: 'CURRENT', instanceId: uiInstance },
          refresh: request,
          epochId,
          runtime: lastRuntime,
          runtimeState: lastState,
          activationRecord: lastRecord,
          readiness
        };
      }
    } catch {
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
    process.stderr.write(`DEV_UI ERROR code=${code} message=${String(error?.message || error)}\n`);
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
  stopLifecycle,
  replaceLifecycle,
  refreshLifecycle,
  runLifecycle,
  lifecycleError,
  refreshOperationId,
  refreshRuntimeReady
};
