#!/usr/bin/env node
'use strict';

// This narrow subprocess bridge exists so the Python node agent never reads a
// Recovery IPC descriptor or its bearer token. It can forward exactly one
// pre-admitted, read-only control-plane action and emits only the safe receipt
// projection returned by Recovery Host.

const path = require('node:path');
const { parseRuntimeInvocation, resolveRuntime } = require('./recovery_runtime_adapter.cjs');

const MAX_REQUEST_BYTES = 64 * 1024;
const LOCAL_HANDLE_PATTERN = /^cp_ro_[a-f0-9]{48}$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const IDENTIFIER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const WORKSPACE_SUMMARY_SCHEMA_VERSION = 1;
const WORKSPACE_SUMMARY_MAX_BYTES = 8 * 1024;
const WORKSPACE_SUMMARY_TEXT_MAX = 256;
const WORKSPACE_SUMMARY_ENTRY_TYPES = new Set(['file', 'directory', 'symlink', 'other']);
const WORKSPACE_SUMMARY_PROJECT_TYPES = new Set(['unknown', 'electron', 'node', 'python', 'rust', 'go']);

function bridgeError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
}

function canonicalJson(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`;
  return `{${Object.keys(value).sort().map((key) => (
    `${JSON.stringify(key)}:${canonicalJson(value[key])}`
  )).join(',')}}`;
}

function digest(value) {
  return require('node:crypto').createHash('sha256').update(canonicalJson(value), 'utf8').digest('hex');
}

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function summaryText(value, { allowEmpty = false, maxLength = WORKSPACE_SUMMARY_TEXT_MAX } = {}) {
  if (typeof value !== 'string' || value.length > maxLength || /[\u0000-\u001f\u007f]/.test(value)
    || (!allowEmpty && !value)) throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
  return value;
}

function workspaceSummary(value) {
  if (!exactKeys(value, ['schema_version', 'project', 'entries', 'entries_truncated', 'git'])
    || value.schema_version !== WORKSPACE_SUMMARY_SCHEMA_VERSION
    || !exactKeys(value.project, ['type', 'name', 'version'])
    || !WORKSPACE_SUMMARY_PROJECT_TYPES.has(value.project.type)
    || !Array.isArray(value.entries) || value.entries.length > 1
    || typeof value.entries_truncated !== 'boolean'
    || !exactKeys(value.git, ['is_repo', 'branch', 'changed_count', 'truncated'])
    || typeof value.git.is_repo !== 'boolean'
    || !Number.isSafeInteger(value.git.changed_count) || value.git.changed_count < 0 || value.git.changed_count > 100_000
    || typeof value.git.truncated !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
  }
  const entries = value.entries.map((entry) => {
    if (!exactKeys(entry, ['name', 'type', 'size_bytes', 'is_hidden', 'is_ignored'])
      || !WORKSPACE_SUMMARY_ENTRY_TYPES.has(entry.type)
      || !Number.isSafeInteger(entry.size_bytes) || entry.size_bytes < 0
      || typeof entry.is_hidden !== 'boolean' || typeof entry.is_ignored !== 'boolean') {
      throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
    }
    const name = summaryText(entry.name);
    if (/[\\/]/.test(name) || name === '.' || name === '..') throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
    return { name, type: entry.type, size_bytes: entry.size_bytes, is_hidden: entry.is_hidden, is_ignored: entry.is_ignored };
  });
  const summary = {
    schema_version: WORKSPACE_SUMMARY_SCHEMA_VERSION,
    project: {
      type: value.project.type,
      name: summaryText(value.project.name),
      version: summaryText(value.project.version, { allowEmpty: true, maxLength: 128 })
    },
    entries,
    entries_truncated: value.entries_truncated,
    git: {
      is_repo: value.git.is_repo,
      branch: summaryText(value.git.branch, { allowEmpty: true }),
      changed_count: value.git.changed_count,
      truncated: value.git.truncated
    }
  };
  if (Buffer.byteLength(canonicalJson(summary), 'utf8') > WORKSPACE_SUMMARY_MAX_BYTES) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID');
  }
  return summary;
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
  const summary = workspaceSummary(result?.workspace_summary);
  const summarySha256 = text(result?.workspace_summary_sha256).toLowerCase();
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
    || !SHA256_PATTERN.test(text(result.response_sha256).toLowerCase())
    || !SHA256_PATTERN.test(summarySha256) || summarySha256 !== digest(summary)) {
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
    workspace_summary: summary,
    workspace_summary_sha256: summarySha256,
    response_sha256: text(result.response_sha256).toLowerCase()
  };
}

async function runReadOnlyBridge(request, { runtimeMode = 'development', appRoot = path.resolve(__dirname, '..', '..'), adapterDirectory, dependencies = {} } = {}) {
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
    'runtime.control_plane_read_only_workspace_context',
    [request],
    requestOptions(descriptor)
  );
  return normalisedResult(descriptor, result);
}

async function runDevelopmentReadOnlyBridge(request, options = {}) {
  return runReadOnlyBridge(request, { ...options, runtimeMode: 'development' });
}

async function main(argv = process.argv.slice(2)) {
  const invocation = parseRuntimeInvocation(argv);
  const request = await readRequest();
  const result = await runReadOnlyBridge(request, {
    runtimeMode: invocation.runtimeMode,
    appRoot: invocation.appRoot || undefined
  });
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
  workspaceSummary,
  canonicalJson,
  normalisedResult,
  runReadOnlyBridge,
  runDevelopmentReadOnlyBridge
};
