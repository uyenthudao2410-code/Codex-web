#!/usr/bin/env node
'use strict';

// Descriptor-hiding adapter for the separate bounded file-read lane.  Python
// never sees a Recovery IPC descriptor/token; this bridge forwards exactly one
// already admitted request and allowlists the returned projection before it can
// become a node receipt.

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
        reject(bridgeError('CONTROL_PLANE_FILE_READ_REQUEST_TOO_LARGE'));
        return;
      }
      chunks.push(Buffer.from(chunk));
    });
    input.once('error', () => reject(bridgeError('CONTROL_PLANE_FILE_READ_REQUEST_INVALID')));
    input.once('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
          throw bridgeError('CONTROL_PLANE_FILE_READ_REQUEST_INVALID');
        }
        resolve(value);
      } catch (error) {
        reject(error?.code ? error : bridgeError('CONTROL_PLANE_FILE_READ_REQUEST_INVALID'));
      }
    });
  });
}

function fileReadBridgeModule(runtime, dependencies = {}) {
  if (dependencies.fileReadBridge) return dependencies.fileReadBridge;
  const appRoot = typeof runtime?.paths?.appRoot === 'function' ? runtime.paths.appRoot() : '';
  if (!appRoot || !path.isAbsolute(appRoot)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_UNAVAILABLE');
  }
  try {
    return require(path.join(appRoot, 'electron/services/controlPlaneFileReadBridge'));
  } catch {
    throw bridgeError('CONTROL_PLANE_FILE_READ_UNAVAILABLE');
  }
}

function normalisedResult(descriptor, result, request, bridge) {
  if (!bridge || typeof bridge.normaliseFileReadResult !== 'function') {
    throw bridgeError('CONTROL_PLANE_FILE_READ_UNAVAILABLE');
  }
  let normalized;
  try {
    normalized = bridge.normaliseFileReadResult(result, request);
  } catch (error) {
    throw bridgeError(text(error?.code) || 'CONTROL_PLANE_FILE_READ_RESULT_INVALID');
  }
  return {
    schema_version: 1,
    operation_kind: normalized.operation_kind,
    installation_id: text(descriptor.installation_id) || null,
    runtime_mode: text(descriptor.runtime_mode) || null,
    action_id: normalized.action_id,
    attempt_id: normalized.attempt_id,
    local_handle: normalized.local_handle,
    file_accessed: true,
    policy_sha256: normalized.policy_sha256,
    actor: normalized.actor,
    runtime_identity: normalized.runtime_identity,
    facade_contract: normalized.facade_contract,
    file: normalized.file,
    response_sha256: normalized.response_sha256
  };
}

async function runFileReadBridge(request, {
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
    'runtime.control_plane_bounded_file_read',
    [request],
    requestOptions(descriptor)
  );
  return normalisedResult(descriptor, result, request, fileReadBridgeModule(runtime, dependencies));
}

async function runDevelopmentFileReadBridge(request, options = {}) {
  return runFileReadBridge(request, { ...options, runtimeMode: 'development' });
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  const request = await readRequest();
  const result = await runFileReadBridge(request, {
    runtimeMode: invocation.runtimeMode,
    appRoot: invocation.appRoot || undefined
  });
  process.stdout.write(`${JSON.stringify({ ok: true, result })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({ ok: false, error: { code: text(error?.code) || 'CONTROL_PLANE_FILE_READ_FAILED' } })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  bridgeError,
  readRequest,
  normalisedResult,
  runFileReadBridge,
  runDevelopmentFileReadBridge
};
