#!/usr/bin/env node
'use strict';

// Descriptor-hiding adapter for the bounded exec lane. The Python node agent
// supplies one already admitted request; Recovery IPC owns the loopback
// descriptor and the Electron runtime owns MCP credentials/attestation.

const path = require('node:path');
const { parseRuntimeInvocation, resolveRuntime } = require('./recovery_runtime_adapter.cjs');

const MAX_REQUEST_BYTES = 64 * 1024;
const EXEC_RUN_IPC_TIMEOUT_MS = 330_000;

function bridgeError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
}

// This subprocess boundary intentionally repeats the IPC projection checks:
// packaged adapters must not depend on a development module or emit raw errors.
function execErrorDetails(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const details = {};
  const patterns = {
    native_error_code: /^[A-Z][A-Z0-9_]{1,95}$/,
    phase: /^(?:provision|start|exec|deprovision)$/,
    backend_error_code: /^[a-z_]{3,48}$/,
    command_id: /^[A-Za-z0-9_-][A-Za-z0-9_-]{0,159}$/,
    job_id: /^[A-Za-z0-9_-][A-Za-z0-9_-]{0,159}$/,
    job_lifecycle: /^(?:starting|running|spawn_failed|exited|failed|terminated|timed_out|quiesced|orphaned)$/
  };
  for (const [key, pattern] of Object.entries(patterns)) {
    if (typeof value[key] === 'string' && pattern.test(value[key])) details[key] = value[key];
  }
  if (Number.isSafeInteger(value.root_pid) && value.root_pid >= 0) details.root_pid = value.root_pid;
  if (typeof value.execution_started === 'boolean') details.execution_started = value.execution_started;
  const finished = value.job_finished_at;
  if (typeof finished === 'string'
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(finished)
    && Number.isFinite(Date.parse(finished))
    && new Date(finished).toISOString().slice(0, 19) === finished.slice(0, 19)) {
    details.job_finished_at = finished;
  }
  return Object.keys(details).length ? details : null;
}

function errorCorrelation(value) {
  const result = {};
  for (const key of ['action_id', 'attempt_id', 'task_id']) {
    if (typeof value?.[key] !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,159}$/.test(value[key])) return null;
    result[key] = value[key];
  }
  if (!Number.isSafeInteger(value.writer_lease_generation) || value.writer_lease_generation < 1) return null;
  result.writer_lease_generation = value.writer_lease_generation;
  return result;
}

function serializeExecBridgeError(error) {
  const code = typeof error?.code === 'string' && /^[A-Z][A-Z0-9_]{1,95}$/.test(error.code)
    ? error.code : 'CONTROL_PLANE_EXEC_FAILED';
  const result = { code };
  if (code === 'CONTROL_PLANE_EXEC_MCP_REJECTED' && error.recovery_response_received === true) {
    const correlation = errorCorrelation(error);
    if (correlation) {
      Object.assign(result, correlation, { recovery_response_received: true });
      const details = execErrorDetails(error.details);
      if (details) result.details = details;
    }
  }
  return result;
}

function readRequest(input = process.stdin) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    input.on('data', (chunk) => {
      total += Buffer.byteLength(chunk);
      if (total > MAX_REQUEST_BYTES) {
        input.destroy();
        reject(bridgeError('CONTROL_PLANE_EXEC_REQUEST_TOO_LARGE'));
        return;
      }
      chunks.push(Buffer.from(chunk));
    });
    input.once('error', () => reject(bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID')));
    input.once('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
          throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID');
        }
        resolve(value);
      } catch (error) {
        reject(error?.code ? error : bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID'));
      }
    });
  });
}

function execBridgeModule(runtime, dependencies = {}) {
  if (dependencies.execBridge) return dependencies.execBridge;
  const appRoot = typeof runtime?.paths?.appRoot === 'function' ? runtime.paths.appRoot() : '';
  if (!appRoot || !path.isAbsolute(appRoot)) throw bridgeError('CONTROL_PLANE_EXEC_UNAVAILABLE');
  try {
    return require(path.join(appRoot, 'electron/services/controlPlaneExecBridge'));
  } catch {
    throw bridgeError('CONTROL_PLANE_EXEC_UNAVAILABLE');
  }
}

function normalisedResult(descriptor, result, request, bridge) {
  if (!bridge || typeof bridge.normaliseExecResult !== 'function') {
    throw bridgeError('CONTROL_PLANE_EXEC_UNAVAILABLE');
  }
  let normalized;
  try {
    // RecoveryHost has already admitted the request against the local policy
    // and returns the policy digest in its allowlisted result.  The raw node
    // request intentionally does not carry that digest or the trusted actor
    // projection, so re-normalise with only those two fields bridged from the
    // authenticated Recovery result.  Never forward a caller-supplied actor.
    const admission = {
      ...request,
      policy_sha256: result?.policy_sha256,
      actor: { client_id: 'electron-control-plane-exec-bridge', client_type: 'electron' }
    };
    normalized = bridge.normaliseExecResult(result, admission);
  } catch (error) {
    throw bridgeError(text(error?.code) || 'CONTROL_PLANE_EXEC_RESULT_INVALID');
  }
  return {
    schema_version: 1,
    operation_kind: normalized.operation_kind,
    installation_id: text(descriptor.installation_id) || null,
    runtime_mode: text(descriptor.runtime_mode) || null,
    action_id: normalized.action_id,
    attempt_id: normalized.attempt_id,
    task_id: normalized.task_id,
    writer_lease_generation: normalized.writer_lease_generation,
    local_handle: normalized.local_handle,
    policy_sha256: normalized.policy_sha256,
    actor: normalized.actor,
    runtime_identity: normalized.runtime_identity,
    facade_contract: normalized.facade_contract,
    command_id: normalized.command_id,
    job_id: normalized.job_id,
    status: normalized.status,
    exit_code: normalized.exit_code,
    stdout: normalized.stdout,
    stderr: normalized.stderr,
    truncated: normalized.truncated,
    timed_out: normalized.timed_out,
    run_id: normalized.run_id,
    wave_id: normalized.wave_id,
    output_refs: normalized.output_refs,
    ...(normalized.execution_backend ? {
      execution_backend: normalized.execution_backend,
      isolation_level: normalized.isolation_level,
      policy_decision: normalized.policy_decision
    } : {}),
    response_sha256: normalized.response_sha256
  };
}

async function runExecBridge(request, {
  runtimeMode = 'development',
  appRoot = path.resolve(__dirname, '..', '..'),
  adapterDirectory,
  dependencies = {}
} = {}) {
  const runtime = resolveRuntime({ runtimeMode, appRoot, adapterDirectory, dependencies });
  const {
    paths,
    RecoveryIpcClient,
    loadRecoveryDescriptor,
    descriptorMatchesInstallation,
    descriptorRequestOptions
  } = runtime;
  const readDescriptor = dependencies.loadRecoveryDescriptor || loadRecoveryDescriptor;
  const matchesInstallation = dependencies.descriptorMatchesInstallation || descriptorMatchesInstallation;
  const requestOptions = dependencies.descriptorRequestOptions || descriptorRequestOptions;
  const clientFactory = dependencies.clientFactory || ((options) => new RecoveryIpcClient(options));
  const expectedIdentity = paths.runtimeIdentity();
  const descriptor = readDescriptor(paths);
  if (text(descriptor.runtime_mode) !== runtime.mode || !matchesInstallation(descriptor, expectedIdentity)) {
    throw bridgeError('RECOVERY_HOST_INSTALLATION_MISMATCH');
  }
  const client = clientFactory({ paths });
  let result;
  try {
    result = await client.call(
      'runtime.control_plane_exec',
      [request],
      {
        ...requestOptions(descriptor),
        // Cold Sandbox setup completes before exec_run can return a job handle.
        ...(request.operation === 'exec_run' ? { timeout: EXEC_RUN_IPC_TIMEOUT_MS } : {})
      }
    );
  } catch (error) {
    if (error?.code === 'CONTROL_PLANE_EXEC_MCP_REJECTED' && error.recoveryResponseReceived === true) {
      const correlation = errorCorrelation(request);
      const details = execErrorDetails(error.details);
      throw Object.assign(bridgeError('CONTROL_PLANE_EXEC_MCP_REJECTED'), {
        ...(correlation ? { ...correlation, recovery_response_received: true } : {}),
        ...(details ? { details } : {})
      });
    }
    throw error;
  }
  return normalisedResult(descriptor, result, request, execBridgeModule(runtime, dependencies));
}

async function runDevelopmentExecBridge(request, options = {}) {
  return runExecBridge(request, { ...options, runtimeMode: 'development' });
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  const request = await readRequest();
  const result = await runExecBridge(request, {
    runtimeMode: invocation.runtimeMode,
    appRoot: invocation.appRoot || undefined
  });
  process.stdout.write(`${JSON.stringify({ ok: true, result })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({ ok: false, error: serializeExecBridgeError(error) })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  bridgeError,
  readRequest,
  normalisedResult,
  serializeExecBridgeError,
  runExecBridge,
  runDevelopmentExecBridge
};
