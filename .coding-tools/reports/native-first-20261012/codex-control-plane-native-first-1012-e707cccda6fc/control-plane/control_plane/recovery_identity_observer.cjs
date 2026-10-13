#!/usr/bin/env node
'use strict';

// This is a deliberately narrow bridge from the Python node client to the
// existing Recovery IPC client. It can read one sanitized MCP identity
// observation only; it does not expose the descriptor/token or any mutating
// Recovery IPC action.

const path = require('node:path');
const { parseRuntimeInvocation, resolveRuntime } = require('./recovery_runtime_adapter.cjs');

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
    observation_kind: 'mcp_identity_read_only',
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

function exactRecoveryHost(descriptor, status) {
  return Number(status?.pid || 0) === Number(descriptor?.owner_pid || 0)
    && text(status?.instance_id) === text(descriptor?.instance_id)
    && text(status?.process_start_token) === text(descriptor?.owner_process_start_token);
}

function normalizedRuntimeStatus(descriptor, status) {
  const runtime = status?.runtime;
  const epoch = status?.activation_epoch;
  const centralExecutor = runtime?.execution_role === 'central_executor';
  const routeReady = centralExecutor
    ? runtime?.central_connected === true
      && runtime?.authority_ready === true
      && runtime?.central_status_reason == null
    : runtime?.connector_ready === true
      && runtime?.connector_ack_sha_matches === true;
  const strictReady = exactRecoveryHost(descriptor, status)
    && text(descriptor?.runtime_mode) === 'packaged'
    && text(status?.state) === 'healthy'
    && status?.full_clean_activation?.available === true
    && epoch?.admission_open === true
    && epoch?.update_incomplete === false
    && runtime?.fully_ready === true
    && runtime?.update_incomplete === false
    && routeReady;
  return {
    observation_schema_version: 1,
    observation_kind: 'recovery_runtime_read_only',
    installation_id: text(descriptor?.installation_id) || null,
    runtime_mode: text(descriptor?.runtime_mode) || null,
    recovery_host_instance_id: text(descriptor?.instance_id) || null,
    strict_ready: strictReady,
    ...(strictReady ? {} : { error_code: 'PACKAGED_RUNTIME_UNREADY' })
  };
}

async function observeRuntime({ runtimeMode = 'development', appRoot = path.resolve(__dirname, '..', '..'), adapterDirectory, dependencies = {} } = {}) {
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
    throw observerError('RECOVERY_HOST_INSTALLATION_MISMATCH');
  }
  const client = clientFactory({ paths });
  const observation = await client.call('runtime.identity_observation', [], requestOptions(descriptor));
  return normalizedObservation(descriptor, observation);
}

async function observeDevelopmentRuntime(options = {}) {
  return observeRuntime({ ...options, runtimeMode: 'development' });
}

async function observePackagedRuntimeStatus({ adapterDirectory, dependencies = {} } = {}) {
  const runtime = resolveRuntime({ runtimeMode: 'packaged', adapterDirectory, dependencies });
  const {
    paths,
    RecoveryIpcClient,
    loadRecoveryDescriptor,
    descriptorMatchesInstallation,
    descriptorRequestOptions
  } = runtime;
  const descriptor = (dependencies.loadRecoveryDescriptor || loadRecoveryDescriptor)(paths);
  if (text(descriptor.runtime_mode) !== 'packaged'
    || !(dependencies.descriptorMatchesInstallation || descriptorMatchesInstallation)(descriptor, paths.runtimeIdentity())) {
    throw observerError('RECOVERY_HOST_INSTALLATION_MISMATCH');
  }
  const client = (dependencies.clientFactory || ((options) => new RecoveryIpcClient(options)))({ paths });
  const status = await client.status((dependencies.descriptorRequestOptions || descriptorRequestOptions)(descriptor));
  return normalizedRuntimeStatus(descriptor, status);
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  if (argv.includes('--runtime-status')) {
    if (invocation.runtimeMode !== 'packaged') throw observerError('RUNTIME_ADAPTER_MODE_INVALID');
    const status = await observePackagedRuntimeStatus();
    process.stdout.write(`${JSON.stringify({ ok: true, status })}\n`);
    return;
  }
  const observation = await observeRuntime({ runtimeMode: invocation.runtimeMode, appRoot: invocation.appRoot || undefined });
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
  normalizedRuntimeStatus,
  exactRecoveryHost,
  observeRuntime,
  observeDevelopmentRuntime,
  observePackagedRuntimeStatus,
  observerError
};
