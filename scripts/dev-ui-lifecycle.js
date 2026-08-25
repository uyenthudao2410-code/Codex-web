#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryIpcClient, loadRecoveryDescriptor, isProcessAlive } = require('../electron/services/recoveryIpc');
const {
  descriptorMatchesInstallation,
  descriptorRequestOptions
} = require('../electron/services/recoveryHostLauncher');
const { activationSourceCheckpoint: sourceCheckpointForActivation } = require('../electron/services/activationClosure');

const ACTIONS = new Set(['start', 'stop', 'replace', 'status']);
const INSTANCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const DEFAULT_TIMEOUT_MS = 35_000;
const DEFAULT_POLL_MS = 250;

function lifecycleError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function normalizeAction(value) {
  const action = String(value || 'start').trim().toLowerCase();
  if (!ACTIONS.has(action)) {
    throw lifecycleError('DEV_UI_ACTION_INVALID', 'Usage: npm run dev | npm run dev:status | npm run dev:stop | npm run dev:replace');
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
  const spawnProcess = options.spawnProcess || spawn;
  const sleep = options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const output = options.output || ((line) => process.stdout.write(`${line}\n`));

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

  return {
    inspect,
    activate,
    suppress,
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

async function runLifecycle(action, dependencies = null) {
  const normalized = normalizeAction(action);
  const deps = dependencies || createRuntimeDependencies();
  if (normalized === 'status') return statusLifecycle(deps);
  if (normalized === 'stop') return stopLifecycle(deps);
  if (normalized === 'replace') return replaceLifecycle(deps);
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
  runLifecycle,
  lifecycleError
};
