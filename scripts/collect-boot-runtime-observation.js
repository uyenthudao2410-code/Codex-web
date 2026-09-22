// Read-only Recovery IPC adapter. Never manufactures a client/reboot receipt.
const path = require('node:path');
const { createDevelopmentPaths } = require('./dev-ui-lifecycle');
const { RecoveryIpcClient, loadRecoveryDescriptor } = require('../electron/services/recoveryIpc');

const opaque = (v) => typeof v === 'string' && /^[A-Za-z0-9._:-]{1,256}$/.test(v) ? v : null;
const sha = (v) => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v) ? v : null;
const number = (v) => Number.isSafeInteger(v) && v > 0 ? v : null;
const bool = (v) => typeof v === 'boolean' ? v : null;
const workspaceKey = (v) => typeof v === 'string' && path.isAbsolute(v)
  ? (process.platform === 'win32' ? path.resolve(v).toLowerCase() : path.resolve(v)) : null;
const revision = (v) => ({ running_revision: sha(v?.running_revision), disk_revision: sha(v?.disk_revision), update_pending: bool(v?.update_pending) });
const failure = (code) => ({ schema_version: 1, kind: 'boot_runtime_observation', status: 'NOT_PROVEN',
  failure_code: code, authority_granted: false, live_accepted: false });

async function collectBootRuntimeObservation({ expectedWorkspace, expectedClient, paths, client, readDescriptor, now = Date.now } = {}) {
  const expected = workspaceKey(expectedWorkspace);
  if (!expected) return failure('EXPLICIT_WORKSPACE_REQUIRED');
  try {
    paths = paths || createDevelopmentPaths();
    client = client || new RecoveryIpcClient({ paths });
    readDescriptor = readDescriptor || (() => loadRecoveryDescriptor(paths));
    const descriptor = readDescriptor();
    const options = {
      expectedOwnerPid: number(descriptor.owner_pid), expectedInstanceId: opaque(descriptor.instance_id),
      expectedOwnerProcessStartToken: opaque(descriptor.owner_process_start_token), timeout: 5000
    };
    if (!options.expectedOwnerPid || !options.expectedInstanceId || !options.expectedOwnerProcessStartToken) {
      return failure('HOST_IDENTITY_UNPROVEN');
    }
    const status = await client.call('recovery.status', [], options);
    if (status?.pid !== descriptor.owner_pid || status?.instance_id !== descriptor.instance_id
      || status?.process_start_token !== descriptor.owner_process_start_token) return failure('HOST_IDENTITY_CHANGED');
    const runtime = await client.call('runtime.lightweight_snapshot', [], options);
    if (workspaceKey(runtime?.device?.workspace) !== expected) return failure('WORKSPACE_TARGET_MISMATCH');
    const identity = await client.call('runtime.identity_observation', [], options);
    const after = readDescriptor();
    if (after.owner_pid !== descriptor.owner_pid || after.instance_id !== descriptor.instance_id
      || after.owner_process_start_token !== descriptor.owner_process_start_token
      || identity?.recovery_host_instance_id !== descriptor.instance_id) return failure('HOST_IDENTITY_CHANGED');
    if (identity.observation_schema_version !== 1 || identity.observation_kind !== 'mcp_identity_read_only') {
      return failure('IDENTITY_OBSERVATION_UNSUPPORTED');
    }
    const epoch = runtime.activationEpoch || {};
    if (!opaque(epoch.activation_epoch_id) || identity.current_activation_epoch_id !== epoch.activation_epoch_id
      || status.activation_epoch?.activation_epoch_id !== epoch.activation_epoch_id) return failure('EPOCH_CHANGED_DURING_READ');
    const collectedAt = now();
    const runtimeAt = number(runtime.snapshotObservedAtUnixMs);
    const hostAt = number(status.snapshot_observed_at_unix_ms);
    const identityAt = typeof identity.observed_at === 'string' ? Date.parse(identity.observed_at) : NaN;
    const fresh = (at) => number(collectedAt) && number(at) && at <= collectedAt && collectedAt - at <= 30_000;
    const freshSources = fresh(runtimeAt) && fresh(hostAt) && fresh(identityAt)
      && runtime.telemetryAvailable === true && runtime.signalStale === false && runtime.snapshotBusy === false;
    const observedRuntime = {};
    for (const key of ['mcpRunning', 'nativeAlive', 'tunnelRunning', 'componentsReady', 'fullyReady',
      'localReady', 'centralConnected', 'authorityReady', 'updateIncomplete', 'connectorRediscovered',
      'connectorRefreshRequired', 'connectorCompatibilityAcknowledged']) observedRuntime[key] = bool(runtime[key]);
    const read = identity.workspace_read;
    // Explicit target + request correlation are required. Never adopt the latest
    // contact from another workspace/chat just because the Host is shared.
    const readMatches = freshSources && identity.identity_current === true && read?.source === 'attested_mcp_contact'
      && read.completed === true && read.workspace_accessed === true && fresh(read.observed_at_ms)
      && ['device_id', 'endpoint_id', 'workspace_id', 'request_id'].every((key) => opaque(expectedClient?.[key]) && read[key] === expectedClient[key])
      && number(expectedClient?.workspace_generation) && read.workspace_generation === expectedClient.workspace_generation
      && read.process_instance_id === identity.mcp_process_instance_id && read.server_instance_id === identity.mcp_server_instance_id
      && read.activation_epoch_id === epoch.activation_epoch_id && read.contract_sha256 === identity.tool_contract_sha256;
    const clientRead = readMatches ? Object.fromEntries(['request_id', 'device_id', 'endpoint_id', 'workspace_id',
      'workspace_generation', 'process_instance_id', 'server_instance_id', 'activation_epoch_id',
      'contract_sha256', 'observed_at_ms'].map((key) => [key, read[key]])) : null;
    if (clientRead) Object.assign(clientRead, { tool: 'workspace_context', ok: true, completed: true,
      workspace_accessed: true, delivery_confirmed: false });
    return {
      schema_version: 1, kind: 'boot_runtime_observation',
      status: freshSources ? 'OBSERVED' : 'STALE_OR_INCOMPLETE',
      collected_at_ms: number(collectedAt), observed_at_ms: runtimeAt,
      source_times: { host_ms: hostAt, runtime_ms: runtimeAt, identity_ms: number(identityAt) },
      source: 'authenticated_recovery_ipc', workspace_matched: true,
      authority_granted: false, live_accepted: false,
      host: { pid: descriptor.owner_pid, instance_id: descriptor.instance_id,
        process_start_token: descriptor.owner_process_start_token,
        runtime_mode: ['development', 'packaged'].includes(descriptor.runtime_mode) ? descriptor.runtime_mode : null },
      device_id: opaque(runtime.device?.device_id),
      revisions: { recovery_host: revision(status.code_revision), coding_mcp: revision(runtime.codeRevision?.codingMcp) },
      runtime: {
        ...observedRuntime,
        executionRole: ['direct_legacy', 'central_executor'].includes(runtime.executionRole) ? runtime.executionRole : null,
        process_instance_id: opaque(identity.mcp_process_instance_id), server_instance_id: opaque(identity.mcp_server_instance_id),
        identity_current: bool(identity.identity_current), identity_activation_epoch_id: opaque(identity.activation_epoch_id),
        activationEpoch: { activation_epoch_id: opaque(epoch.activation_epoch_id), operation_id: opaque(epoch.operation_id),
          state: opaque(epoch.state), admission_open: bool(epoch.admission_open) },
        toolContract: { sha256: sha(runtime.toolContract?.sha256) }, identity_contract_sha256: sha(identity.tool_contract_sha256),
        connectorContractState: opaque(runtime.connectorContractState),
        connectorContractAcknowledgedSha256: sha(runtime.connectorContractAcknowledgedSha256)
      },
      client: clientRead,
      missing_evidence: [...(clientRead ? [] : ['REAL_CLIENT_WORKSPACE_READ']), 'CLIENT_DELIVERY_CONFIRMATION', 'CLIENT_DISCOVERY_PROVENANCE', 'BOOT_BEFORE_AFTER',
        'PACKAGE_EXECUTABLE_SUPERVISOR_HASHES', 'CENTRAL_BINDING_POLICY_RECEIPT', 'ATTEMPT_HISTORY_STARTUP_INTENT'],
      note: 'OBSERVED means readback only, not ready/accepted. This partial observation is not a schema-v2 reboot receipt.'
    };
  } catch (error) {
    // Do not echo server messages, descriptors, headers, credentials or paths.
    const safeCode = typeof error?.code === 'string' && /^(RECOVERY|HOST|WORKSPACE)_[A-Z_]{1,80}$/.test(error.code)
      ? error.code : 'RECOVERY_READ_FAILED';
    return failure(safeCode);
  }
}

function parseArguments(args) {
  const fields = {
    '--workspace': 'expectedWorkspace', '--device-id': 'device_id', '--endpoint-id': 'endpoint_id',
    '--workspace-id': 'workspace_id', '--workspace-generation': 'workspace_generation', '--request-hash': 'request_id'
  };
  const values = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = fields[args[i]];
    if (!key || Object.hasOwn(values, key) || typeof args[i + 1] !== 'string' || !args[i + 1]) throw new Error('INVALID_ARGUMENTS');
    values[key] = args[i + 1];
  }
  if (!workspaceKey(values.expectedWorkspace)) throw new Error('EXPLICIT_WORKSPACE_REQUIRED');
  const result = { expectedWorkspace: values.expectedWorkspace };
  const clientKeys = ['device_id', 'endpoint_id', 'workspace_id', 'workspace_generation', 'request_id'];
  if (clientKeys.some((key) => Object.hasOwn(values, key))) {
    if (!['device_id', 'endpoint_id', 'workspace_id'].every((key) => opaque(values[key]))
      || !/^[1-9][0-9]*$/.test(values.workspace_generation || '')
      || !number(Number(values.workspace_generation)) || !/^[a-f0-9]{64}$/.test(values.request_id || '')) {
      throw new Error('EXACT_CLIENT_CORRELATION_REQUIRED');
    }
    result.expectedClient = Object.fromEntries(clientKeys.map((key) => [key, values[key]]));
    result.expectedClient.workspace_generation = Number(values.workspace_generation);
    result.expectedClient.request_id = `rpc-${values.request_id}`;
  }
  return result;
}

async function main(args, { collect = collectBootRuntimeObservation, output = (value) => process.stdout.write(JSON.stringify(value) + '\n') } = {}) {
  let parsed;
  try { parsed = parseArguments(args); }
  catch { output(failure('INVALID_CORRELATION_ARGUMENTS')); return 2; }
  const result = await collect(parsed);
  output(result);
  // A successfully read runtime is not a successfully correlated client.
  if (parsed.expectedClient && !result.client) return 1;
  return result.status === 'OBSERVED' ? 0 : 1;
}

if (require.main === module) main(process.argv.slice(2)).then((code) => { process.exitCode = code; });
module.exports = { collectBootRuntimeObservation, parseArguments, main };
