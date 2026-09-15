#!/usr/bin/env node
'use strict';

// This narrow subprocess bridge exists so the Python node agent never reads a
// Recovery IPC descriptor or its bearer token. It can forward exactly one
// pre-admitted, read-only control-plane action and emits only the safe receipt
// projection returned by Recovery Host.

const path = require('node:path');
const { createDevelopmentPaths } = require('../../scripts/dev-ui-lifecycle');
const { RecoveryIpcClient, loadRecoveryDescriptor } = require('../../electron/services/recoveryIpc');
const { descriptorMatchesInstallation, descriptorRequestOptions } = require('../../electron/services/recoveryHostLauncher');

const MAX_REQUEST_BYTES = 64 * 1024;
const LOCAL_HANDLE_PATTERN = /^cp_ro_[a-f0-9]{48}$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const IDENTIFIER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;

function bridgeError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
}

function facadeContract(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || Object.keys(value).sort().join(',') !== 'profile,schema_version,sha256'
    || !Number.isSafeInteger(value.schema_version) || value.schema_version < 1
    || !IDENTIFIER_PATTERN.test(text(value.profile))
    || !SHA256_PATTERN.test(text(value.sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
  }
  return {
    schema_version: value.schema_version,
    profile: text(value.profile),
    sha256: text(value.sha256).toLowerCase()
  };
}

function readRequest(input = process.stdin) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    input.on('data', (chunk) => {
      total += Buffer.byteLength(chunk);
      if (total > MAX_REQUEST_BYTES) {
        input.destroy();
        reject(bridgeError('CONTROL_PLANE_BRIDGE_REQUEST_TOO_LARGE'));
        return;
      }
      chunks.push(Buffer.from(chunk));
    });
    input.once('error', () => reject(bridgeError('CONTROL_PLANE_BRIDGE_REQUEST_INVALID')));
    input.once('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('CONTROL_PLANE_BRIDGE_REQUEST_INVALID');
        resolve(value);
      } catch (error) {
        reject(error?.code ? error : bridgeError('CONTROL_PLANE_BRIDGE_REQUEST_INVALID'));
      }
    });
  });
}

function normalisedResult(descriptor, result) {
  const identity = result?.runtime_identity;
  const actor = result?.actor;
  const contract = facadeContract(result?.facade_contract);
  const processInstanceId = text(identity?.process_instance_id);
  const serverInstanceId = text(identity?.server_instance_id);
  const activationEpochId = text(identity?.activation_epoch_id);
  const contractSha256 = text(identity?.tool_contract_sha256).toLowerCase();
  if (!result || typeof result !== 'object' || Array.isArray(result)
    || Number(result.schema_version) !== 1
    || text(result.operation_kind) !== 'control_plane_read_only_workspace_context'
    || result.workspace_accessed !== true
    || !LOCAL_HANDLE_PATTERN.test(text(result.local_handle))
    || text(result.action_id).length < 8
    || text(result.attempt_id).length < 8
    || text(result.policy_sha256).length !== 64
    || !SHA256_PATTERN.test(text(result.policy_sha256).toLowerCase())
    || text(actor?.client_id) !== 'electron-control-plane-bridge'
    || text(actor?.client_type) !== 'electron'
    || !processInstanceId || !serverInstanceId || !activationEpochId || !SHA256_PATTERN.test(contractSha256)
    || !SHA256_PATTERN.test(text(result.response_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
  }
  return {
    schema_version: 1,
    operation_kind: 'control_plane_read_only_workspace_context',
    installation_id: text(descriptor.installation_id) || null,
    runtime_mode: text(descriptor.runtime_mode) || null,
    action_id: text(result.action_id),
    attempt_id: text(result.attempt_id),
    local_handle: text(result.local_handle),
    workspace_accessed: true,
    policy_sha256: text(result.policy_sha256).toLowerCase(),
    actor: { client_id: 'electron-control-plane-bridge', client_type: 'electron' },
    runtime_identity: {
      activation_epoch_id: activationEpochId,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      tool_contract_sha256: contractSha256
    },
    facade_contract: contract,
    response_sha256: text(result.response_sha256).toLowerCase()
  };
}

async function runDevelopmentReadOnlyBridge(request, { appRoot = path.resolve(__dirname, '..', '..'), dependencies = {} } = {}) {
  const makePaths = dependencies.createDevelopmentPaths || createDevelopmentPaths;
  const readDescriptor = dependencies.loadRecoveryDescriptor || loadRecoveryDescriptor;
  const matchesInstallation = dependencies.descriptorMatchesInstallation || descriptorMatchesInstallation;
  const requestOptions = dependencies.descriptorRequestOptions || descriptorRequestOptions;
  const clientFactory = dependencies.clientFactory || ((options) => new RecoveryIpcClient(options));
  const paths = makePaths({ appRoot });
  const expectedIdentity = paths.runtimeIdentity();
  const descriptor = readDescriptor(paths);
  if (text(descriptor.runtime_mode) !== 'development' || !matchesInstallation(descriptor, expectedIdentity)) {
    throw bridgeError('RECOVERY_HOST_INSTALLATION_MISMATCH');
  }
  const client = clientFactory({ paths });
  const result = await client.call(
    'runtime.control_plane_read_only_workspace_context',
    [request],
    requestOptions(descriptor)
  );
  return normalisedResult(descriptor, result);
}

async function main(argv = process.argv.slice(2)) {
  const index = argv.indexOf('--project-root');
  const appRoot = index >= 0 ? String(argv[index + 1] || '').trim() : path.resolve(__dirname, '..', '..');
  if (!appRoot || !path.isAbsolute(appRoot)) throw bridgeError('PROJECT_ROOT_INVALID');
  const request = await readRequest();
  const result = await runDevelopmentReadOnlyBridge(request, { appRoot });
  process.stdout.write(`${JSON.stringify({ ok: true, result })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({ ok: false, error: { code: text(error?.code) || 'CONTROL_PLANE_BRIDGE_FAILED' } })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  bridgeError,
  readRequest,
  facadeContract,
  normalisedResult,
  runDevelopmentReadOnlyBridge
};
