#!/usr/bin/env node
'use strict';

// This is a deliberately narrow bridge from the Python node client to the
// existing Recovery IPC client. It can read one sanitized MCP identity
// observation only; it does not expose the descriptor/token or any mutating
// Recovery IPC action.

const path = require('node:path');
const { createDevelopmentPaths } = require('../../scripts/dev-ui-lifecycle');
const { RecoveryIpcClient, loadRecoveryDescriptor } = require('../../electron/services/recoveryIpc');
const { descriptorMatchesInstallation, descriptorRequestOptions } = require('../../electron/services/recoveryHostLauncher');

function observerError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
}

function normalizedObservation(descriptor, observation) {
  if (!observation || typeof observation !== 'object' || Array.isArray(observation)) {
    throw observerError('MCP_IDENTITY_OBSERVATION_INVALID');
  }
  if (Number(observation.observation_schema_version || 0) !== 1
    || text(observation.observation_kind) !== 'mcp_identity_read_only'
    || text(observation.recovery_host_instance_id) !== text(descriptor.instance_id)) {
    throw observerError('MCP_IDENTITY_OBSERVATION_UNBOUND');
  }
  return {
    observation_schema_version: 1,
    installation_id: text(descriptor.installation_id) || null,
    runtime_mode: text(descriptor.runtime_mode) || null,
    recovery_host_instance_id: text(descriptor.instance_id) || null,
    observed_at: text(observation.observed_at) || null,
    mcp_process_instance_id: text(observation.mcp_process_instance_id) || null,
    mcp_server_instance_id: text(observation.mcp_server_instance_id) || null,
    activation_epoch_id: text(observation.activation_epoch_id) || null,
    current_activation_epoch_id: text(observation.current_activation_epoch_id) || null,
    tool_contract_sha256: text(observation.tool_contract_sha256) || null,
    mcp_ready: observation.mcp_ready === true,
    identity_current: observation.identity_current === true,
    ...(text(observation.error_code) ? { error_code: text(observation.error_code).slice(0, 80) } : {})
  };
}

async function observeDevelopmentRuntime({ appRoot = path.resolve(__dirname, '..', '..'), dependencies = {} } = {}) {
  const makePaths = dependencies.createDevelopmentPaths || createDevelopmentPaths;
  const readDescriptor = dependencies.loadRecoveryDescriptor || loadRecoveryDescriptor;
  const matchesInstallation = dependencies.descriptorMatchesInstallation || descriptorMatchesInstallation;
  const requestOptions = dependencies.descriptorRequestOptions || descriptorRequestOptions;
  const clientFactory = dependencies.clientFactory || ((options) => new RecoveryIpcClient(options));
  const paths = makePaths({ appRoot });
  const expectedIdentity = paths.runtimeIdentity();
  const descriptor = readDescriptor(paths);
  if (text(descriptor.runtime_mode) !== 'development' || !matchesInstallation(descriptor, expectedIdentity)) {
    throw observerError('RECOVERY_HOST_INSTALLATION_MISMATCH');
  }
  const client = clientFactory({ paths });
  const observation = await client.call('runtime.identity_observation', [], requestOptions(descriptor));
  return normalizedObservation(descriptor, observation);
}

async function main(argv = process.argv.slice(2)) {
  const index = argv.indexOf('--project-root');
  const appRoot = index >= 0 ? String(argv[index + 1] || '').trim() : path.resolve(__dirname, '..', '..');
  if (!appRoot || !path.isAbsolute(appRoot)) throw observerError('PROJECT_ROOT_INVALID');
  const observation = await observeDevelopmentRuntime({ appRoot });
  process.stdout.write(`${JSON.stringify({ ok: true, observation })}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stdout.write(`${JSON.stringify({ ok: false, error: { code: text(error?.code) || 'MCP_IDENTITY_OBSERVATION_FAILED' } })}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  normalizedObservation,
  observeDevelopmentRuntime,
  observerError
};
