#!/usr/bin/env node
'use strict';

// Descriptor-hiding adapter for the separate approved-patch lane. Python sees
// only one sealed request and one allowlisted receipt; Recovery IPC descriptor
// credentials, local workspace roots, local idempotency keys, and patch bytes
// never cross this boundary back into the node agent or Ubuntu receipt store.

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
        reject(bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_TOO_LARGE'));
        return;
      }
      chunks.push(Buffer.from(chunk));
    });
    input.once('error', () => reject(bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID')));
    input.once('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
          throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID');
        }
        resolve(value);
      } catch (error) {
        reject(error?.code ? error : bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'));
      }
    });
  });
}

function approvedPatchBridgeModule(runtime, dependencies = {}) {
  if (dependencies.approvedPatchBridge) return dependencies.approvedPatchBridge;
  const appRoot = typeof runtime?.paths?.appRoot === 'function' ? runtime.paths.appRoot() : '';
  if (!appRoot || !path.isAbsolute(appRoot)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE');
  }
  try {
    return require(path.join(appRoot, 'electron/services/controlPlaneApprovedPatchBridge'));
  } catch {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE');
  }
}

function normalisedResult(descriptor, result, request, bridge) {
  if (!bridge || typeof bridge.normaliseApprovedPatchResult !== 'function') {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE');
  }
  let normalized;
  try {
    normalized = bridge.normaliseApprovedPatchResult(result, request);
  } catch (error) {
    throw bridgeError(text(error?.code) || 'CONTROL_PLANE_APPROVED_PATCH_RESULT_INVALID');
  }
  return {
    schema_version: 1,
    operation_kind: normalized.operation_kind,
    installation_id: text(descriptor.installation_id) || null,
    runtime_mode: text(descriptor.runtime_mode) || null,
    action_id: normalized.action_id,
    attempt_id: normalized.attempt_id,
    local_handle: normalized.local_handle,
    patch_applied: true,
    local_semantic_acceptance: normalized.local_semantic_acceptance,
    policy_sha256: normalized.policy_sha256,
    actor: normalized.actor,
    runtime_identity: normalized.runtime_identity,
    facade_contract: normalized.facade_contract,
    file: normalized.file,
    response_sha256: normalized.response_sha256
  };
}

async function runApprovedPatchBridge(request, {
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
    'runtime.control_plane_approved_patch',
    [request],
    requestOptions(descriptor)
  );
  return normalisedResult(descriptor, result, request, approvedPatchBridgeModule(runtime, dependencies));
}

async function runDevelopmentApprovedPatchBridge(request, options = {}) {
  return runApprovedPatchBridge(request, { ...options, runtimeMode: 'development' });
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  const request = await readRequest();
  const result = await runApprovedPatchBridge(request, {
    runtimeMode: invocation.runtimeMode,
    appRoot: invocation.appRoot || undefined
  });
  process.stdout.write(`${JSON.stringify({ ok: true, result })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({ ok: false, error: { code: text(error?.code) || 'CONTROL_PLANE_APPROVED_PATCH_FAILED' } })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  bridgeError,
  readRequest,
  normalisedResult,
  runApprovedPatchBridge,
  runDevelopmentApprovedPatchBridge
};
