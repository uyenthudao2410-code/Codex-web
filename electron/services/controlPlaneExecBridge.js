'use strict';

// The control-plane exec lane is an adapter into the existing Coding Tools
// runtime.  It does not spawn a process itself and it never receives an
// absolute path or a runtime credential from Ubuntu.  The local policy and
// workspace registry are checked before the request reaches MCP; the MCP
// runtime then owns the managed Job/RUN/WAVE/process lifecycle.

const crypto = require('node:crypto');
const fs = require('node:fs');
const { MAX_COLLECTION_BYTES, selectWorkspacePolicy } = require('./controlPlanePolicyStore');
const path = require('node:path');
const { URL } = require('node:url');

const POLICY_SCHEMA_VERSION = 2;
const LEGACY_POLICY_SCHEMA_VERSION = 1;
const STANDING_AUTHORITY_MODE = 'standing';
const BRIDGE_CLIENT_ID = 'electron-control-plane-exec-bridge';
const BRIDGE_CLIENT_TYPE = 'electron';
const ACTION_TOOL_NAME = 'exec_command';
const OPERATION_KIND = 'control_plane_exec';
const MAX_POLICY_BYTES = 16 * 1024;
const MAX_REGISTRY_BYTES = 64 * 1024;
const MAX_ARGV_ITEMS = 32;
const MAX_ARGV_ITEM_BYTES = 2048;
const MAX_OUTPUT_BYTES = 64 * 1024;
const MAX_TIMEOUT_MS = 5 * 60 * 1000;
const MAX_ALLOWED_PREFIXES = 32;
const MAX_CONCURRENT = 4;
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const ACTION_IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/;
const RUNTIME_ID_RE = /^[A-Za-z0-9_.:@-]{1,256}$/;
const TASK_ID_RE = /^task_[a-f0-9]{32}$/;
const SHA256_RE = /^[a-f0-9]{64}$/;
const ORCHESTRATION_ID_RE = /^[a-f0-9]{32}$/;
// Native command IDs are URL-safe opaque tokens and may begin with '-' or '_'.
const COMMAND_ID_RE = /^[A-Za-z0-9_-][A-Za-z0-9_.:-]{2,255}$/;
const LOCAL_HANDLE_RE = /^cp_exec_[a-f0-9]{48}$/;
const EXEC_OPERATIONS = new Set(['exec_run', 'exec_poll', 'exec_stop']);
const EXEC_SIGNALS = new Set(['TERM', 'KILL', 'INT']);

function bridgeError(code, message) {
  return Object.assign(new Error(message || code), { code });
}

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function canonicalJson(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
}

function digest(value) {
  return crypto.createHash('sha256').update(canonicalJson(value), 'utf8').digest('hex');
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function text(value) { return typeof value === 'string' ? value.trim() : ''; }

function identifier(value, name, pattern = IDENTIFIER_RE, code = 'CONTROL_PLANE_EXEC_POLICY_INVALID') {
  const normalized = text(value);
  if (!pattern.test(normalized)) throw bridgeError(code, `${name} is invalid.`);
  return normalized;
}

function origin(value, code = 'CONTROL_PLANE_EXEC_POLICY_INVALID') {
  const candidate = text(value);
  let parsed;
  try { parsed = new URL(candidate); } catch { throw bridgeError(code, 'control-plane origin is invalid.'); }
  if (!['http:', 'https:'].includes(parsed.protocol)
    || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw bridgeError(code, 'control-plane origin must be a credential-free HTTP(S) origin.');
  }
  return parsed.origin;
}

function expiry(value, now, code) {
  const expiresAtMs = Number(value);
  if (!Number.isSafeInteger(expiresAtMs) || expiresAtMs <= now) {
    throw bridgeError(code, 'control-plane exec authority is expired.');
  }
  return expiresAtMs;
}

function facadeContract(value, code = 'CONTROL_PLANE_EXEC_POLICY_INVALID') {
  if (!exactKeys(value, ['schema_version', 'profile', 'sha256'])) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  const schemaVersion = Number(value.schema_version);
  const profile = text(value.profile);
  const contractSha256 = text(value.sha256).toLowerCase();
  if (!Number.isSafeInteger(schemaVersion) || schemaVersion < 1
    || schemaVersion > 1_000_000 || !IDENTIFIER_RE.test(profile) || !SHA256_RE.test(contractSha256)) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  return Object.freeze({ schema_version: schemaVersion, profile, sha256: contractSha256 });
}

function argvItem(value, code = 'CONTROL_PLANE_EXEC_REQUEST_INVALID') {
  if (typeof value !== 'string' || !value || Buffer.byteLength(value, 'utf8') > MAX_ARGV_ITEM_BYTES
    || /[\u0000-\u001f\u007f]/.test(value)
    || value !== value.trim()
    || [';', '&&', '||', '`', '$(', '|', '>', '<'].some((token) => value.includes(token))) {
    throw bridgeError(code, 'structured argv contains an unsafe argument.');
  }
  return value;
}

function argv(value, code = 'CONTROL_PLANE_EXEC_REQUEST_INVALID') {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_ARGV_ITEMS) {
    throw bridgeError(code, 'structured argv is invalid.');
  }
  const normalized = value.map((item) => argvItem(item, code));
  if (/[\\/:]/.test(normalized[0])) {
    throw bridgeError(code, 'structured executable must be a bare name.');
  }
  return Object.freeze(normalized);
}

function argvPrefixes(value, code = 'CONTROL_PLANE_EXEC_POLICY_INVALID', allowEmpty = false) {
  if (!Array.isArray(value) || value.length < (allowEmpty ? 0 : 1) || value.length > MAX_ALLOWED_PREFIXES) {
    throw bridgeError(code, 'allowed_argv_prefixes is invalid.');
  }
  const normalized = value.map((prefix) => {
    const item = argv(prefix, code);
    return Object.freeze([...item]);
  });
  const serialized = normalized.map((item) => JSON.stringify(item));
  if (new Set(serialized).size !== serialized.length) {
    throw bridgeError(code, 'allowed_argv_prefixes must not contain duplicates.');
  }
  return Object.freeze(normalized);
}

function normalisePolicy(value, { now = Date.now(), allowExpired = false } = {}) {
  const schemaVersion = Number(value?.schema_version);
  const standing = schemaVersion === POLICY_SCHEMA_VERSION;
  const legacy = schemaVersion === LEGACY_POLICY_SCHEMA_VERSION;
  const expected = [
    'schema_version', 'enabled', 'server_origin', 'owner_id', 'device_id',
    'endpoint_id', 'workspace_id', 'workspace_generation', 'expires_at_ms',
    'facade_contract', 'allowed_argv_prefixes', 'max_timeout_ms', 'max_output_bytes', 'max_concurrent'
  ];
  if (standing) expected.push('authority_mode');
  for (const key of ['execution_mode', 'native_argv_prefixes']) {
    if (standing && Object.hasOwn(value, key)) expected.push(key);
  }
  if (!exactKeys(value, expected) || (!standing && !legacy)) {
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'control-plane exec policy has an invalid schema.');
  }
  if (value.enabled !== true) throw bridgeError('CONTROL_PLANE_EXEC_DISABLED', 'control-plane exec bridge is disabled.');
  const authorityMode = standing ? text(value.authority_mode) : 'expiring_legacy';
  if (standing && authorityMode !== STANDING_AUTHORITY_MODE) {
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'control-plane exec authority mode is invalid.');
  }
  const maxTimeout = Number(value.max_timeout_ms);
  const maxOutput = Number(value.max_output_bytes);
  const maxConcurrent = Number(value.max_concurrent);
  const routing = {};
  if (Object.hasOwn(value, 'execution_mode')) {
    if (!['native_first', 'native_only', 'isolated'].includes(value.execution_mode)) {
      throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'control-plane execution mode is invalid.');
    }
    routing.execution_mode = value.execution_mode;
  }
  if (Object.hasOwn(value, 'native_argv_prefixes')) {
    routing.native_argv_prefixes = argvPrefixes(value.native_argv_prefixes, 'CONTROL_PLANE_EXEC_POLICY_INVALID', true);
  }
  if (!Number.isSafeInteger(maxTimeout) || maxTimeout < 1 || maxTimeout > MAX_TIMEOUT_MS
    || !Number.isSafeInteger(maxOutput) || maxOutput < 1024 || maxOutput > MAX_OUTPUT_BYTES
    || !Number.isSafeInteger(maxConcurrent) || maxConcurrent < 1 || maxConcurrent > MAX_CONCURRENT) {
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'control-plane exec policy limits are invalid.');
  }
  const expiresAtMs = value.expires_at_ms;
  if (standing) {
    if (expiresAtMs !== null) {
      throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'standing exec authority must not carry an expiry.');
    }
  } else {
    if (!Number.isSafeInteger(Number(expiresAtMs)) || Number(expiresAtMs) <= 0
      || (!allowExpired && Number(expiresAtMs) <= now)) {
      throw bridgeError('CONTROL_PLANE_EXEC_POLICY_EXPIRED', 'control-plane exec authority is expired.');
    }
  }
  return Object.freeze({
    schema_version: schemaVersion,
    enabled: true,
    authority_mode: authorityMode,
    server_origin: origin(value.server_origin),
    owner_id: identifier(value.owner_id, 'owner_id'),
    device_id: identifier(value.device_id, 'device_id'),
    endpoint_id: identifier(value.endpoint_id, 'endpoint_id'),
    workspace_id: identifier(value.workspace_id, 'workspace_id'),
    workspace_generation: identifier(value.workspace_generation, 'workspace_generation'),
    expires_at_ms: standing ? null : Number(expiresAtMs),
    facade_contract: facadeContract(value.facade_contract),
    allowed_argv_prefixes: argvPrefixes(value.allowed_argv_prefixes),
    max_timeout_ms: maxTimeout,
    max_output_bytes: maxOutput,
    max_concurrent: maxConcurrent,
    ...routing
  });
}

function loadExecBridgePolicy(paths, { target = null, now = Date.now(), allowExpired = false } = {}) {
  const policyFile = typeof paths?.controlPlaneExecPolicyFile === 'function'
    ? paths.controlPlaneExecPolicyFile() : '';
  if (!policyFile || !fs.existsSync(policyFile)) {
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_MISSING', 'control-plane exec policy is not installed.');
  }
  let raw;
  try {
    const stat = fs.statSync(policyFile);
    if (!stat.isFile() || stat.size <= 0 || stat.size > MAX_COLLECTION_BYTES) throw new Error('invalid');
    raw = JSON.parse(fs.readFileSync(policyFile, 'utf8'));
  } catch (error) {
    if (error?.code?.startsWith('CONTROL_PLANE_EXEC_')) throw error;
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_INVALID', 'control-plane exec policy cannot be parsed.');
  }
  const policy = normalisePolicy(selectWorkspacePolicy(raw, target, { code: 'CONTROL_PLANE_EXEC_POLICY_INVALID', maxPolicyBytes: MAX_POLICY_BYTES }), { now, allowExpired });
  // Keep the cross-language policy fingerprint aligned with node_agent.py.
  // `enabled` is an admission gate, not part of the authority projection;
  // changing it to false must disable the policy rather than create a second
  // authority identity that could be mistaken for an admitted request.
  const admittedProjection = { ...policy };
  delete admittedProjection.enabled;
  return Object.freeze({ ...policy, policy_sha256: digest(admittedProjection) });
}

function pathKey(value) {
  const normalized = path.normalize(path.resolve(value));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function resolveRegisteredWorkspaceRoot(paths, policy) {
  const registryFile = typeof paths?.controlPlaneWorkspaceRegistryFile === 'function'
    ? paths.controlPlaneWorkspaceRegistryFile() : '';
  try {
    const stat = fs.statSync(registryFile);
    if (!registryFile || !stat.isFile() || stat.size <= 0 || stat.size > MAX_REGISTRY_BYTES) throw new Error('invalid');
    const registry = JSON.parse(fs.readFileSync(registryFile, 'utf8'));
    if (!registry || typeof registry !== 'object' || Array.isArray(registry)
      || registry.schema_version !== 1 || !Array.isArray(registry.entries)) throw new Error('invalid');
    const matches = registry.entries.filter((entry) => entry && typeof entry === 'object'
      && entry.workspace_id === policy.workspace_id
      && entry.workspace_generation === policy.workspace_generation);
    if (matches.length !== 1) throw new Error('invalid');
    const entry = matches[0];
    if (!exactKeys(entry, ['workspace_id', 'workspace_generation', 'canonical_path', 'display_name', 'capabilities', 'created_at_ms'])
      || !entry.capabilities || typeof entry.capabilities !== 'object' || Array.isArray(entry.capabilities)
      || entry.capabilities.exec !== true || typeof entry.capabilities.read !== 'boolean'
      || typeof entry.capabilities.write !== 'boolean') throw new Error('invalid');
    if (typeof entry.canonical_path !== 'string' || !path.isAbsolute(entry.canonical_path)) throw new Error('invalid');
    const declared = path.resolve(entry.canonical_path);
    const real = fs.realpathSync.native(entry.canonical_path);
    if (pathKey(real) !== pathKey(declared) || !fs.statSync(real).isDirectory()) throw new Error('invalid');
    return real;
  } catch {
    throw bridgeError('CONTROL_PLANE_EXEC_WORKSPACE_REGISTRY_REQUIRED', 'control-plane exec target is not a current local workspace registration.');
  }
}

function admitExecBridgeRequest(policy, request, { now = Date.now() } = {}) {
  const expected = [
    'server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id',
    'workspace_generation', 'context_id', 'binding_id', 'action_id', 'attempt_id',
    'task_id', 'writer_lease_generation', 'tool_name', 'operation', 'argv', 'cwd',
    'timeout_ms', 'max_output_bytes', 'expires_at_ms', 'facade_contract',
    'command_id', 'job_id', 'local_handle', 'consumer_id', 'yield_time_ms',
    'signal', 'wait_ms', 'run_id', 'wave_id'
  ];
  if (!exactKeys(request, expected)) throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'control-plane exec request has an invalid schema.');
  const candidate = {
    server_origin: origin(request.server_origin, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    owner_id: identifier(request.owner_id, 'owner_id', IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    device_id: identifier(request.device_id, 'device_id', IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    endpoint_id: identifier(request.endpoint_id, 'endpoint_id', IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    workspace_id: identifier(request.workspace_id, 'workspace_id', IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    workspace_generation: identifier(request.workspace_generation, 'workspace_generation', IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    context_id: identifier(request.context_id, 'context_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    binding_id: identifier(request.binding_id, 'binding_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    action_id: identifier(request.action_id, 'action_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    attempt_id: identifier(request.attempt_id, 'attempt_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    task_id: identifier(request.task_id, 'task_id', TASK_ID_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    writer_lease_generation: Number(request.writer_lease_generation),
    tool_name: request.tool_name,
    operation: request.operation,
    argv: argv(request.argv),
    cwd: typeof request.cwd === 'string' ? request.cwd : '',
    timeout_ms: Number(request.timeout_ms),
    max_output_bytes: Number(request.max_output_bytes),
    expires_at_ms: Number(request.expires_at_ms),
    facade_contract: facadeContract(request.facade_contract, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    command_id: request.command_id == null ? null : identifier(request.command_id, 'command_id', COMMAND_ID_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    job_id: request.job_id == null ? null : identifier(request.job_id, 'job_id', COMMAND_ID_RE, 'CONTROL_PLANE_EXEC_REQUEST_INVALID'),
    local_handle: request.local_handle == null ? null : text(request.local_handle),
    consumer_id: request.consumer_id == null ? null : text(request.consumer_id),
    yield_time_ms: request.yield_time_ms == null ? null : Number(request.yield_time_ms),
    signal: request.signal == null ? null : text(request.signal).toUpperCase(),
    wait_ms: request.wait_ms == null ? null : Number(request.wait_ms),
    run_id: request.run_id == null ? null : text(request.run_id),
    wave_id: request.wave_id == null ? null : text(request.wave_id)
  };
  if (candidate.tool_name !== ACTION_TOOL_NAME || !EXEC_OPERATIONS.has(candidate.operation)) {
    throw bridgeError('CONTROL_PLANE_EXEC_TOOL_DENIED', 'control-plane exec bridge operation is not admitted.');
  }
  if (!Number.isSafeInteger(candidate.writer_lease_generation) || candidate.writer_lease_generation < 1) {
    throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'writer lease generation is invalid.');
  }
  if (!Number.isSafeInteger(candidate.expires_at_ms) || candidate.expires_at_ms <= 0
    || (candidate.operation === 'exec_run' && candidate.expires_at_ms <= now)) {
    throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_EXPIRED', 'control-plane exec request is expired.');
  }
  if (!Number.isSafeInteger(candidate.timeout_ms) || candidate.timeout_ms < 1 || candidate.timeout_ms > MAX_TIMEOUT_MS
    || !Number.isSafeInteger(candidate.max_output_bytes) || candidate.max_output_bytes < 1024 || candidate.max_output_bytes > MAX_OUTPUT_BYTES) {
    throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec limits are invalid.');
  }
  if (candidate.cwd && (candidate.cwd.startsWith('/') || candidate.cwd.includes('\\') || candidate.cwd.includes(':')
    || candidate.cwd.split('/').some((part) => !part || part === '.' || part === '..'))) {
    throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec cwd is invalid.');
  }
  if (policy.expires_at_ms != null && candidate.expires_at_ms > policy.expires_at_ms) {
    throw bridgeError('CONTROL_PLANE_EXEC_POLICY_EXPIRED', 'exec action outlives local policy.');
  }
  for (const field of ['server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id', 'workspace_generation']) {
    if (candidate[field] !== policy[field]) throw bridgeError('CONTROL_PLANE_EXEC_TARGET_MISMATCH', `control-plane exec ${field} does not match local policy.`);
  }
  if (candidate.timeout_ms > policy.max_timeout_ms || candidate.max_output_bytes > policy.max_output_bytes) {
    throw bridgeError('CONTROL_PLANE_EXEC_LIMIT_DENIED', 'exec request exceeds local policy limits.');
  }
  if (canonicalJson(candidate.facade_contract) !== canonicalJson(policy.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_EXEC_CONTRACT_MISMATCH', 'control-plane facade contract does not match local policy.');
  }
  if (!policy.allowed_argv_prefixes.some((prefix) => prefix.length <= candidate.argv.length
      && prefix.every((item, index) => item === candidate.argv[index]))) {
    throw bridgeError('CONTROL_PLANE_EXEC_ALLOWLIST_DENIED', 'exec argv is not explicitly admitted by local policy.');
  }
  if (candidate.operation === 'exec_run') {
    if (candidate.command_id !== null || candidate.job_id !== null || candidate.local_handle !== null
      || candidate.consumer_id !== null || candidate.signal !== null || candidate.wait_ms !== null
      || candidate.yield_time_ms !== null || candidate.run_id !== null || candidate.wave_id !== null) {
      throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec_run must not carry a control handle.');
    }
  } else {
    if (!candidate.command_id || !candidate.job_id || !LOCAL_HANDLE_RE.test(candidate.local_handle || '')
      || !candidate.consumer_id || candidate.consumer_id.length > 128
      || !Number.isSafeInteger(candidate.yield_time_ms) || candidate.yield_time_ms < 0 || candidate.yield_time_ms > 30_000) {
      throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec control handle is invalid.');
    }
    if (candidate.run_id == null || candidate.wave_id == null
      || candidate.run_id.length > 128 || candidate.wave_id.length > 128) {
      throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec control orchestration identity is invalid.');
    }
    if (candidate.operation === 'exec_poll') {
      if (candidate.signal !== null || candidate.wait_ms !== null) {
        throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec_poll must not carry stop controls.');
      }
    } else if (!EXEC_SIGNALS.has(candidate.signal)
      || !Number.isSafeInteger(candidate.wait_ms) || candidate.wait_ms < 0 || candidate.wait_ms > 30_000) {
      throw bridgeError('CONTROL_PLANE_EXEC_REQUEST_INVALID', 'exec_stop controls are invalid.');
    }
  }
  return Object.freeze({
    schema_version: POLICY_SCHEMA_VERSION,
    operation_kind: OPERATION_KIND,
    ...candidate,
    execution_mode: policy.execution_mode || 'native_first',
    native_argv_prefixes: policy.native_argv_prefixes || [],
    policy_sha256: policy.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE }
  });
}

function executionMetadata(value) {
  const keys = ['execution_backend', 'isolation_level', 'policy_decision'];
  const present = keys.filter((key) => Object.hasOwn(value, key));
  if (!present.length) return {};
  if (present.length !== keys.length
    || !(value.execution_backend === 'native' && value.isolation_level === 'process_container'
      && ['native_safe_command', 'native_explicit_approval'].includes(value.policy_decision))
      && !(value.execution_backend === 'isolated' && value.isolation_level === 'hypervisor'
        && ['isolated_unapproved_command', 'isolated_preferred'].includes(value.policy_decision))
      && !(value.execution_backend === 'local' && value.isolation_level === 'host_user'
        && value.policy_decision === 'operator_local')) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_METADATA_INVALID');
  }
  return Object.fromEntries(keys.map((key) => [key, value[key]]));
}

function normaliseExecResult(value, admission) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('CONTROL_PLANE_EXEC_RESULT_INVALID');
  const status = text(value.status).toLowerCase();
  if (!['running', 'exited', 'terminated', 'timeout', 'stopped', 'reconciled_terminal'].includes(status)) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_INVALID');
  }
  if (text(value.operation_kind) !== OPERATION_KIND
    || text(value.action_id) !== admission.action_id
    || text(value.attempt_id) !== admission.attempt_id
    || text(value.task_id) !== admission.task_id
    || Number(value.writer_lease_generation) !== admission.writer_lease_generation) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID');
  }
  const localHandle = text(value.local_handle) || text(admission.local_handle);
  const commandId = text(value.command_id) || text(admission.command_id);
  const jobId = text(value.job_id) || text(admission.job_id);
  if (!LOCAL_HANDLE_RE.test(localHandle) || !COMMAND_ID_RE.test(commandId) || !COMMAND_ID_RE.test(jobId)) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID');
  }
  if (admission.command_id && commandId !== admission.command_id) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID');
  }
  if (admission.job_id && jobId !== admission.job_id) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID');
  }
  const runtimeIdentity = value.runtime_identity;
  if (!runtimeIdentity || typeof runtimeIdentity !== 'object' || Array.isArray(runtimeIdentity)
    || !RUNTIME_ID_RE.test(text(runtimeIdentity.activation_epoch_id))
    || !RUNTIME_ID_RE.test(text(runtimeIdentity.process_instance_id))
    || !RUNTIME_ID_RE.test(text(runtimeIdentity.server_instance_id))
    || !SHA256_RE.test(text(runtimeIdentity.tool_contract_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_IDENTITY_INVALID');
  }
  if (canonicalJson(value.facade_contract) !== canonicalJson(admission.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_CONTRACT_CHANGED');
  }
  const output = {
    status,
    exit_code: value.exit_code == null ? null : Number(value.exit_code),
    stdout: typeof value.stdout === 'string' ? value.stdout : '',
    stderr: typeof value.stderr === 'string' ? value.stderr : '',
    truncated: value.truncated === true,
    timed_out: value.timed_out === true,
    command_id: commandId,
    job_id: jobId,
    run_id: text(value.run_id) || text(admission.run_id),
    wave_id: text(value.wave_id) || text(admission.wave_id),
    output_refs: value.output_refs && typeof value.output_refs === 'object' ? value.output_refs : null,
    ...executionMetadata(value)
  };
  if ((output.stdout.length + output.stderr.length) > admission.max_output_bytes * 2) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_TOO_LARGE');
  }
  if (status !== 'running' && status !== 'reconciled_terminal'
    && (!Number.isSafeInteger(output.exit_code) || output.exit_code < -255 || output.exit_code > 255)) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_INVALID');
  }
  const responseSha256 = sha256(Buffer.from(canonicalJson(output), 'utf8'));
  if (text(value.response_sha256).toLowerCase() !== responseSha256) {
    throw bridgeError('CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID');
  }
  return Object.freeze({
    schema_version: 1,
    operation_kind: OPERATION_KIND,
    local_handle: localHandle,
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    task_id: admission.task_id,
    writer_lease_generation: admission.writer_lease_generation,
    policy_sha256: admission.policy_sha256,
    actor: { ...admission.actor },
    facade_contract: { ...admission.facade_contract },
    runtime_identity: {
      activation_epoch_id: text(runtimeIdentity.activation_epoch_id),
      process_instance_id: text(runtimeIdentity.process_instance_id),
      server_instance_id: text(runtimeIdentity.server_instance_id),
      tool_contract_sha256: text(runtimeIdentity.tool_contract_sha256).toLowerCase()
    },
    command_id: commandId,
    job_id: jobId,
    status,
    exit_code: output.exit_code,
    stdout: output.stdout,
    stderr: output.stderr,
    truncated: output.truncated,
    timed_out: output.timed_out,
    run_id: output.run_id,
    wave_id: output.wave_id,
    output_refs: output.output_refs,
    ...executionMetadata(output),
    response_sha256: responseSha256
  });
}

module.exports = {
  POLICY_SCHEMA_VERSION,
  LEGACY_POLICY_SCHEMA_VERSION,
  STANDING_AUTHORITY_MODE,
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  ACTION_TOOL_NAME,
  OPERATION_KIND,
  digest,
  normalisePolicy,
  loadExecBridgePolicy,
  resolveRegisteredWorkspaceRoot,
  admitExecBridgeRequest,
  executionMetadata,
  normaliseExecResult
};
