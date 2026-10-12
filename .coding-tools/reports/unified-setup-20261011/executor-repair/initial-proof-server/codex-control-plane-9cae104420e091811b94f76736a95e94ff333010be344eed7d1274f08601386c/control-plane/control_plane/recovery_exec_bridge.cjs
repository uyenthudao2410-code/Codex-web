#!/usr/bin/env node
'use strict';

// Descriptor-hiding adapter for the bounded exec lane. The Python node agent
// supplies one already admitted request; Recovery IPC owns the loopback
// descriptor and the Electron runtime owns MCP credentials/attestation.

const path = require('node:path');
const { parseRuntimeInvocation, resolveRuntime } = require('./recovery_runtime_adapter.cjs');

const MAX_REQUEST_BYTES = 64 * 1024;

function bridgeError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
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
  const result = await client.call(
    'runtime.control_plane_exec',
    [request],
    requestOptions(descriptor)
  );
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
    process.stdout.write(`${JSON.stringify({ ok: false, error: { code: text(error?.code) || 'CONTROL_PLANE_EXEC_FAILED' }})}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  bridgeError,
  readRequest,
  normalisedResult,
  runExecBridge,
  runDevelopmentExecBridge
};
