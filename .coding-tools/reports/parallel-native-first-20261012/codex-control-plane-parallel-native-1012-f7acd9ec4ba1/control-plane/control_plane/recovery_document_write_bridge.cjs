#!/usr/bin/env node
'use strict';

// Descriptor-hiding adapter for the structured document-write lane.  The
// Python node agent supplies one already admitted, bounded request; Recovery
// IPC owns its descriptor and the Electron runtime owns the MCP credential and
// exact workspace binding.  Only a digest-only result crosses back.

const path = require('node:path');
const { parseRuntimeInvocation, resolveRuntime } = require('./recovery_runtime_adapter.cjs');

// The document content contract permits 256 KiB.  Keep enough headroom for
// the JSON envelope, UTF-8 escaping and correlation metadata while still
// bounding the descriptor-hiding subprocess input.
const MAX_REQUEST_BYTES = 512 * 1024;

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
        reject(bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_TOO_LARGE'));
        return;
      }
      chunks.push(Buffer.from(chunk));
    });
    input.once('error', () => reject(bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID')));
    input.once('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
          throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID');
        }
        resolve(value);
      } catch (error) {
        reject(error?.code ? error : bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID'));
      }
    });
  });
}

function documentWriteBridgeModule(runtime, dependencies = {}) {
  if (dependencies.documentWriteBridge) return dependencies.documentWriteBridge;
  const appRoot = typeof runtime?.paths?.appRoot === 'function' ? runtime.paths.appRoot() : '';
  if (!appRoot || !path.isAbsolute(appRoot)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE');
  }
  try {
    return require(path.join(appRoot, 'electron/services/controlPlaneDocumentWriteBridge'));
  } catch {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE');
  }
}

function normalisedResult(descriptor, result, request, bridge) {
  if (!bridge || typeof bridge.normaliseDocumentWriteResult !== 'function') {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE');
  }
  let normalized;
  try {
    normalized = bridge.normaliseDocumentWriteResult(result, request);
  } catch (error) {
    throw bridgeError(text(error?.code) || 'CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID');
  }
  return {
    schema_version: 1,
    operation_kind: normalized.operation_kind,
    local_handle: normalized.local_handle,
    action_id: normalized.action_id,
    attempt_id: normalized.attempt_id,
    task_id: normalized.task_id,
    writer_lease_generation: normalized.writer_lease_generation,
    operation: normalized.operation,
    target: normalized.target,
    source: normalized.source,
    result: normalized.result,
    actor: normalized.actor,
    policy_sha256: normalized.policy_sha256,
    facade_contract: normalized.facade_contract,
    runtime_identity: normalized.runtime_identity,
    response_sha256: normalized.response_sha256
  };
}

async function runDocumentWriteBridge(request, {
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
    'runtime.control_plane_document_write',
    [request],
    requestOptions(descriptor)
  );
  return normalisedResult(
    descriptor,
    result,
    request,
    documentWriteBridgeModule(runtime, dependencies)
  );
}

async function runDevelopmentDocumentWriteBridge(request, options = {}) {
  return runDocumentWriteBridge(request, { ...options, runtimeMode: 'development' });
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  const request = await readRequest();
  const result = await runDocumentWriteBridge(request, {
    runtimeMode: invocation.runtimeMode,
    appRoot: invocation.appRoot || undefined
  });
  process.stdout.write(`${JSON.stringify({ ok: true, result })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({
      ok: false,
      error: { code: text(error?.code) || 'CONTROL_PLANE_DOCUMENT_WRITE_FAILED' }
    })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  MAX_REQUEST_BYTES,
  bridgeError,
  readRequest,
  normalisedResult,
  runDocumentWriteBridge,
  runDevelopmentDocumentWriteBridge
};
