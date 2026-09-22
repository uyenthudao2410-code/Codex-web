"use strict";

// The central enrollment UI is only a node-identity request.  It does not
// alter executionRole, create a binding/context/policy, or receive an OpenAI
// credential.  The Ubuntu operator must still approve this request and issue
// every later authority record independently.

const fs = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');
const { normalizeDeviceIdentity } = require('./deviceIdentity');
const { run } = require('./commandRunner');

const ENROLLMENT_TIMEOUT_MS = 15_000;
const MAX_AGENT_OUTPUT_BYTES = 16 * 1024;
const ENROLLMENT_ID_PATTERN = /^enroll_[a-z0-9][a-z0-9_-]{7,127}$/;
const NODE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const CREDENTIAL_ROTATION_ID_PATTERN = /^rotate_[a-f0-9]{32}$/;
const CREDENTIAL_ROTATION_STATES = new Set(['idle', 'candidate_persisted', 'prepared', 'activated', 'promoted', 'completed', 'unknown']);
const WORKSPACE_ID_PATTERN = /^workspace_[a-f0-9]{32}$/;
const WORKSPACE_GENERATION_PATTERN = /^generation_[a-f0-9]{32}$/;
const WORKSPACE_CAPABILITY_KEYS = Object.freeze(['read', 'write', 'exec']);
const AUTHORITY_STATUS_STATES = new Set([
  'pending_operator_approval', 'no_binding', 'active', 'binding_revoked',
  'workspace_missing', 'workspace_retired', 'blocked', 'revoked', 'unknown'
]);
const AUTHORITY_BINDING_STATES = new Set(['active', 'revoked']);
const AUTHORITY_WORKSPACE_STATES = new Set(['active', 'missing', 'retired']);
const AUTHORITY_PRESENCE_STATES = new Set(['online', 'offline', 'unknown']);
const AUTHORITY_READINESS_STATES = new Set(['ready', 'degraded', 'blocked', 'unknown']);
const AUTHORITY_POLICY_STATES = new Set(['unobserved', 'enabled', 'expired_or_disabled', 'unavailable', 'unknown']);
const AUTHORITY_DISPATCH_STATES = new Set(['dispatchable', 'binding_revoked', 'node_revoked', 'workspace_missing', 'workspace_retired']);
const SAFE_ENVIRONMENT_NAMES = new Set([
  'PATH', 'SystemRoot', 'WINDIR', 'ComSpec', 'APPDATA', 'LOCALAPPDATA',
  'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'TEMP', 'TMP', 'LANG', 'LC_ALL',
  'SSL_CERT_FILE', 'SSL_CERT_DIR'
]);

function enrollmentError(code, message) {
  return Object.assign(new Error(message), { code });
}

function centralServerOrigin(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  let parsed;
  try { parsed = new URL(text); }
  catch { throw enrollmentError('CONTROL_PLANE_SERVER_URL_INVALID', 'Địa chỉ Ubuntu phải là HTTPS origin hợp lệ.'); }
  if (parsed.protocol !== 'https:' || !parsed.hostname || parsed.username || parsed.password
    || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw enrollmentError('CONTROL_PLANE_SERVER_URL_INVALID', 'Địa chỉ Ubuntu phải là HTTPS origin không có path hoặc credential.');
  }
  return parsed.origin;
}

function endpointId(deviceId) {
  const normalized = String(deviceId || '').trim().toLowerCase();
  if (!NODE_ID_PATTERN.test(normalized)) {
    throw enrollmentError('CONTROL_PLANE_DEVICE_ID_INVALID', 'Định danh thiết bị cục bộ không hợp lệ.');
  }
  return `executor-${normalized}`;
}

function centralWorkspaceId(value) {
  const workspaceId = typeof value === 'string' ? value.trim().toLowerCase() : '';
  if (!WORKSPACE_ID_PATTERN.test(workspaceId)) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_ID_INVALID', 'Workspace ID từ node không hợp lệ.');
  }
  return workspaceId;
}

function centralWorkspaceGeneration(value) {
  const workspaceGeneration = typeof value === 'string' ? value.trim().toLowerCase() : '';
  if (!WORKSPACE_GENERATION_PATTERN.test(workspaceGeneration)) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_GENERATION_INVALID', 'Workspace generation từ node không hợp lệ.');
  }
  return workspaceGeneration;
}

function canonicalWorkspacePath(value) {
  const selected = typeof value === 'string' ? value.trim() : '';
  if (!selected || selected.includes('\0')) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_PATH_INVALID', 'Thư mục local không hợp lệ.');
  }
  let canonical;
  try {
    canonical = fs.realpathSync.native(selected);
    if (!fs.statSync(canonical).isDirectory()) throw new Error('not-directory');
  } catch {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_PATH_INVALID', 'Thư mục local không tồn tại hoặc không còn truy cập được.');
  }
  if (!path.isAbsolute(canonical)) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_PATH_INVALID', 'Thư mục local phải là đường dẫn tuyệt đối.');
  }
  return canonical;
}

function workspaceDisplayName(canonicalPath) {
  const basename = path.basename(canonicalPath) || canonicalPath;
  if (!basename || basename.length > 120 || /[\x00-\x1f]/.test(basename)) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_DISPLAY_NAME_INVALID', 'Tên hiển thị thư mục local không hợp lệ.');
  }
  return basename;
}

function normalizeWorkspaceCapabilities(value = undefined) {
  const candidate = value === undefined
    ? { read: true, write: false, exec: false }
    : value;
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)
    || Object.keys(candidate).sort().join(',') !== WORKSPACE_CAPABILITY_KEYS.slice().sort().join(',')) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_CAPABILITIES_INVALID', 'Capability workspace phải có đúng read, write và exec.');
  }
  const capabilities = {};
  for (const name of WORKSPACE_CAPABILITY_KEYS) {
    if (typeof candidate[name] !== 'boolean') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_CAPABILITIES_INVALID', 'Capability workspace phải là boolean.');
    }
    capabilities[name] = candidate[name];
  }
  if (capabilities.read !== true) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_READ_REQUIRED', 'Workspace phải giữ capability read.');
  }
  return Object.freeze(capabilities);
}

function safeEnrollmentEnvironment(source = process.env) {
  const result = {};
  for (const name of SAFE_ENVIRONMENT_NAMES) {
    if (typeof source?.[name] === 'string' && source[name]) result[name] = source[name];
  }
  return result;
}

function parseEnrollmentResult(stdout, expectedDeviceId) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'device_id,enrollment_id,state'
    || !ENROLLMENT_ID_PATTERN.test(String(payload.enrollment_id || ''))
    || String(payload.device_id || '').toLowerCase() !== String(expectedDeviceId || '').toLowerCase()
    || !['pending_operator_approval', 'approved'].includes(payload.state)) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID', 'Node enrollment receipt không đúng target hoặc trạng thái.');
  }
  return Object.freeze({
    enrollment_id: String(payload.enrollment_id),
    device_id: String(payload.device_id).toLowerCase(),
    state: payload.state
  });
}

function parseEnrollmentStatusResult(stdout, expectedDeviceId) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID', 'Node enrollment status trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID', 'Node enrollment status không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID', 'Node enrollment status trả về receipt không hợp lệ.'); }
  const legacyKeys = ['credential_generation', 'device_id', 'enrollment_id', 'error_code', 'fresh', 'observed_at_ms', 'state'].sort().join(',');
  const enrichedKeys = [...legacyKeys.split(','), 'server_origin'].sort().join(',');
  const payloadKeys = Object.keys(payload || {}).sort().join(',');
  const hasServerOrigin = payloadKeys === enrichedKeys;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || ![legacyKeys, enrichedKeys].includes(payloadKeys)
    || String(payload.device_id || '').toLowerCase() !== String(expectedDeviceId || '').toLowerCase()
    || (payload.enrollment_id !== null && !ENROLLMENT_ID_PATTERN.test(String(payload.enrollment_id || '')))
    || !['unconfigured', 'request_sent', 'pending_operator_approval', 'approved', 'revoked', 'unknown'].includes(payload.state)
    || typeof payload.fresh !== 'boolean'
    || (payload.credential_generation !== null && (!Number.isSafeInteger(payload.credential_generation) || payload.credential_generation < 1))
    || (payload.observed_at_ms !== null && (!Number.isSafeInteger(payload.observed_at_ms) || payload.observed_at_ms <= 0))
    || (payload.error_code !== null && !/^[A-Z0-9_]{3,96}$/.test(String(payload.error_code)))
    || (hasServerOrigin && payload.server_origin !== null && typeof payload.server_origin !== 'string')) {
    throw enrollmentError('CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID', 'Node enrollment status không đúng target hoặc trạng thái.');
  }
  let serverOrigin = null;
  if (hasServerOrigin && payload.server_origin !== null) {
    try { serverOrigin = centralServerOrigin(payload.server_origin); }
    catch { throw enrollmentError('CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID', 'Node enrollment status có origin không hợp lệ.'); }
  }
  const result = {
    device_id: String(payload.device_id).toLowerCase(),
    enrollment_id: payload.enrollment_id === null ? null : String(payload.enrollment_id),
    state: payload.state,
    credential_generation: payload.credential_generation,
    fresh: payload.fresh,
    observed_at_ms: payload.observed_at_ms,
    error_code: payload.error_code
  };
  if (hasServerOrigin) result.server_origin = serverOrigin;
  return Object.freeze(result);
}

function parseAuthorityStatusResult(stdout, expectedDeviceId) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status trả về receipt không hợp lệ.'); }
  const expectedKeys = 'device_id,dispatchable_target_count,error_code,fresh,node_display_name,observed_at_ms,state,target_count,targets,workspace_count';
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== expectedKeys
    || String(payload.device_id || '').toLowerCase() !== String(expectedDeviceId || '').toLowerCase()
    || typeof payload.fresh !== 'boolean'
    || !AUTHORITY_STATUS_STATES.has(String(payload.state || '').toLowerCase())
    || (payload.node_display_name !== null && (typeof payload.node_display_name !== 'string' || !payload.node_display_name || payload.node_display_name.length > 120))
    || !Number.isSafeInteger(payload.workspace_count) || payload.workspace_count < 0
    || !Number.isSafeInteger(payload.target_count) || payload.target_count < 0
    || !Number.isSafeInteger(payload.dispatchable_target_count) || payload.dispatchable_target_count < 0
    || !Array.isArray(payload.targets) || payload.targets.length !== payload.target_count || payload.targets.length > 64
    || (payload.observed_at_ms !== null && (!Number.isSafeInteger(payload.observed_at_ms) || payload.observed_at_ms <= 0))
    || (payload.error_code !== null && !/^[A-Z0-9_]{3,96}$/.test(String(payload.error_code)))) {
    throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status không đúng target hoặc trạng thái.');
  }
  const targets = payload.targets.map((target) => {
    const legacyTargetKeys = ['binding_state', 'capabilities', 'dispatch_blockers', 'dispatch_state', 'node_display_name', 'policy_state', 'presence_state', 'readiness', 'workspace_display_name', 'workspace_state'].sort().join(',');
    const enrichedTargetKeys = [...legacyTargetKeys.split(','), 'workspace_generation', 'workspace_id'].sort().join(',');
    const targetKeys = Object.keys(target || {}).sort().join(',');
    const enriched = targetKeys === enrichedTargetKeys;
    if (!target || typeof target !== 'object' || Array.isArray(target)
      || ![legacyTargetKeys, enrichedTargetKeys].includes(targetKeys)
      || typeof target.node_display_name !== 'string' || !target.node_display_name || target.node_display_name.length > 120
      || typeof target.workspace_display_name !== 'string' || !target.workspace_display_name || target.workspace_display_name.length > 120
      || (enriched && (typeof target.workspace_id !== 'string' || !NODE_ID_PATTERN.test(target.workspace_id)
        || typeof target.workspace_generation !== 'string' || !NODE_ID_PATTERN.test(target.workspace_generation)))
      || !AUTHORITY_BINDING_STATES.has(String(target.binding_state || '').toLowerCase())
      || !AUTHORITY_WORKSPACE_STATES.has(String(target.workspace_state || '').toLowerCase())
      || !AUTHORITY_PRESENCE_STATES.has(String(target.presence_state || '').toLowerCase())
      || !AUTHORITY_READINESS_STATES.has(String(target.readiness || '').toLowerCase())
      || !AUTHORITY_POLICY_STATES.has(String(target.policy_state || '').toLowerCase())
      || !AUTHORITY_DISPATCH_STATES.has(String(target.dispatch_state || '').toLowerCase())
      || !Array.isArray(target.dispatch_blockers)
      || target.dispatch_blockers.some((item) => !AUTHORITY_DISPATCH_STATES.has(String(item || '').toLowerCase()))) {
      throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status có target không hợp lệ.');
    }
    let capabilities;
    try { capabilities = normalizeWorkspaceCapabilities(target.capabilities); }
    catch { throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status có capability không hợp lệ.'); }
    const normalized = {
      node_display_name: target.node_display_name,
      workspace_display_name: target.workspace_display_name,
      capabilities,
      binding_state: String(target.binding_state).toLowerCase(),
      workspace_state: String(target.workspace_state).toLowerCase(),
      presence_state: String(target.presence_state).toLowerCase(),
      readiness: String(target.readiness).toLowerCase(),
      policy_state: String(target.policy_state).toLowerCase(),
      dispatch_state: String(target.dispatch_state).toLowerCase(),
      dispatch_blockers: Object.freeze(target.dispatch_blockers.map((item) => String(item).toLowerCase()))
    };
    if (enriched) {
      normalized.workspace_id = String(target.workspace_id);
      normalized.workspace_generation = String(target.workspace_generation);
    }
    return Object.freeze(normalized);
  });
  const dispatchable = targets.filter((target) => target.dispatch_state === 'dispatchable').length;
  if (dispatchable !== payload.dispatchable_target_count) {
    throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID', 'Node authority status đếm target không nhất quán.');
  }
  return Object.freeze({
    device_id: String(payload.device_id).toLowerCase(),
    state: String(payload.state).toLowerCase(),
    node_display_name: payload.node_display_name,
    workspace_count: payload.workspace_count,
    target_count: payload.target_count,
    dispatchable_target_count: payload.dispatchable_target_count,
    targets: Object.freeze(targets),
    fresh: payload.fresh,
    observed_at_ms: payload.observed_at_ms,
    error_code: payload.error_code
  });
}

function parseCredentialRotationResult(stdout, expectedDeviceId) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_OUTPUT_INVALID', 'Node rotation trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_OUTPUT_INVALID', 'Node rotation không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_OUTPUT_INVALID', 'Node rotation trả về receipt không hợp lệ.'); }
  const expectedKeys = 'current_generation,device_id,error_code,fresh,next_generation,rotation_id,state';
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== expectedKeys
    || String(payload.device_id || '').toLowerCase() !== String(expectedDeviceId || '').toLowerCase()
    || typeof payload.fresh !== 'boolean'
    || !CREDENTIAL_ROTATION_STATES.has(String(payload.state || '').toLowerCase())
    || (payload.rotation_id !== null && !CREDENTIAL_ROTATION_ID_PATTERN.test(String(payload.rotation_id || '')))
    || (payload.current_generation !== null
      && (!Number.isSafeInteger(payload.current_generation) || payload.current_generation < 1))
    || (payload.next_generation !== null
      && (!Number.isSafeInteger(payload.next_generation) || payload.next_generation < 1))
    || (payload.current_generation !== null && payload.next_generation !== null
      && payload.next_generation !== payload.current_generation + 1)
    || (payload.error_code !== null && !/^[A-Z0-9_]{3,96}$/.test(String(payload.error_code)))) {
    throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_OUTPUT_INVALID', 'Node rotation receipt không đúng target hoặc trạng thái.');
  }
  return Object.freeze({
    device_id: String(payload.device_id).toLowerCase(),
    rotation_id: payload.rotation_id === null ? null : String(payload.rotation_id),
    state: String(payload.state).toLowerCase(),
    current_generation: payload.current_generation,
    next_generation: payload.next_generation,
    fresh: payload.fresh,
    error_code: payload.error_code
  });
}

function parseReadOnlyPolicyInstallResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'enabled,expires_at_ms,operation,policy_sha256,runtime_mode,windows_acl_verified'
    || payload.operation !== 'control_plane_read_only_policy_installed'
    || payload.enabled !== true
    || !Number.isSafeInteger(payload.expires_at_ms) || payload.expires_at_ms <= Date.now()
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || payload.runtime_mode !== 'packaged'
    || payload.windows_acl_verified !== false) {
    throw enrollmentError('CONTROL_PLANE_POLICY_OUTPUT_INVALID', 'Node policy receipt không đúng trạng thái read-only đã xác nhận.');
  }
  return Object.freeze({
    enabled: true,
    expires_at_ms: payload.expires_at_ms,
    policy_sha256: String(payload.policy_sha256).toLowerCase(),
    runtime_mode: 'packaged',
    windows_acl_verified: false
  });
}

function parseWorkspaceRegistrationResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID', 'Node workspace trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID', 'Node workspace không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID', 'Node workspace trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'capabilities,display_name,replayed,state,workspace_generation,workspace_id'
    || !WORKSPACE_ID_PATTERN.test(String(payload.workspace_id || ''))
    || !WORKSPACE_GENERATION_PATTERN.test(String(payload.workspace_generation || ''))
    || typeof payload.display_name !== 'string' || !payload.display_name || payload.display_name.length > 120
    || payload.state !== 'registered' || typeof payload.replayed !== 'boolean') {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID', 'Node workspace receipt không đúng target hoặc capability local.');
  }
  let capabilities;
  try { capabilities = normalizeWorkspaceCapabilities(payload.capabilities); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID', 'Node workspace receipt không đúng capability local.'); }
  return Object.freeze({
    workspace_id: payload.workspace_id,
    workspace_generation: payload.workspace_generation,
    display_name: payload.display_name,
    capabilities,
    replayed: payload.replayed,
    state: 'registered'
  });
}

function parseWorkspaceListResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).join(',') !== 'workspaces'
    || !Array.isArray(payload.workspaces) || payload.workspaces.length > 64) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace inventory không hợp lệ.');
  }
  const seen = new Set();
  const workspaces = payload.workspaces.map((entry) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)
      || Object.keys(entry).sort().join(',') !== 'capabilities,display_name,workspace_generation,workspace_id'
      || typeof entry.display_name !== 'string' || !entry.display_name || entry.display_name.length > 120
      ) {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace inventory không đúng schema.');
    }
    let capabilities;
    try { capabilities = normalizeWorkspaceCapabilities(entry.capabilities); }
    catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace inventory không đúng capability local.'); }
    const workspace_id = centralWorkspaceId(entry.workspace_id);
    const workspace_generation = centralWorkspaceGeneration(entry.workspace_generation);
    const identity = `${workspace_id}:${workspace_generation}`;
    if (seen.has(identity)) {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID', 'Node workspace inventory có target trùng.');
    }
    seen.add(identity);
    return Object.freeze({
      workspace_id,
      workspace_generation,
      display_name: entry.display_name,
      capabilities
    });
  });
  return Object.freeze(workspaces);
}

function parseWorkspaceRetirementResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID', 'Node workspace trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID', 'Node workspace không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID', 'Node workspace trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'capabilities,display_name,replayed,state,workspace_generation,workspace_id'
    || payload.state !== 'retired' || typeof payload.replayed !== 'boolean'
    || typeof payload.display_name !== 'string' || !payload.display_name || payload.display_name.length > 120) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID', 'Node workspace retirement receipt không hợp lệ.');
  }
  let capabilities;
  try { capabilities = normalizeWorkspaceCapabilities(payload.capabilities); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID', 'Node workspace retirement capability không hợp lệ.'); }
  return Object.freeze({
    workspace_id: centralWorkspaceId(payload.workspace_id),
    workspace_generation: centralWorkspaceGeneration(payload.workspace_generation),
    display_name: payload.display_name,
    capabilities,
    replayed: payload.replayed,
    state: 'retired'
  });
}

function parseWorkspaceReplacementResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID', 'Node workspace replacement trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID', 'Node workspace replacement không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID', 'Node workspace replacement trả về receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'capabilities,display_name,old_workspace_generation,replayed,state,workspace_generation,workspace_id'
    || payload.state !== 'replaced' || typeof payload.replayed !== 'boolean'
    || typeof payload.display_name !== 'string' || !payload.display_name || payload.display_name.length > 120) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID', 'Node workspace replacement receipt không đúng trạng thái.');
  }
  let capabilities;
  try { capabilities = normalizeWorkspaceCapabilities(payload.capabilities); }
  catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID', 'Node workspace replacement capability không hợp lệ.'); }
  return Object.freeze({
    workspace_id: centralWorkspaceId(payload.workspace_id),
    old_workspace_generation: centralWorkspaceGeneration(payload.old_workspace_generation),
    workspace_generation: centralWorkspaceGeneration(payload.workspace_generation),
    display_name: payload.display_name,
    capabilities,
    replayed: payload.replayed,
    state: 'replaced'
  });
}

class ControlPlaneEnrollmentService {
  constructor({ paths, runner = run, environment = process.env } = {}) {
    if (!paths || typeof paths.runtimeMode !== 'function' || typeof paths.portablePython !== 'function'
      || typeof paths.controlPlaneNodeAgent !== 'function' || typeof paths.controlPlaneNodeConfigFile !== 'function'
      || typeof paths.controlPlaneWorkspaceRegistryFile !== 'function'
      || typeof paths.appRoot !== 'function' || typeof paths.executablePath !== 'function') {
      throw new TypeError('ControlPlaneEnrollmentService requires complete runtime paths.');
    }
    this.paths = paths;
    this.runner = runner;
    this.environment = environment;
  }

  async request({ serverUrl, deviceIdentity } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_ENROLLMENT_PACKAGED_REQUIRED', 'Pairing chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const origin = centralServerOrigin(serverUrl);
    const identity = normalizeDeviceIdentity(deviceIdentity);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_ENROLLMENT_RUNTIME_MISSING', `${label} đóng gói cho pairing không sẵn sàng.`);
      }
    }
    const endpoint = endpointId(identity.device_id);
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'request-enrollment',
        '--config', config,
        '--server-url', origin,
        '--device-id', identity.device_id,
        '--endpoint-id', endpoint,
        '--display-name', identity.display_name,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_ENROLLMENT_FAILED');
      throw enrollmentError(code, 'Không thể gửi yêu cầu pairing tới Ubuntu.');
    }
    const receipt = parseEnrollmentResult(result?.stdout, identity.device_id);
    return Object.freeze({
      ...receipt,
      server_origin: origin,
      endpoint_id: endpoint,
      display_name: identity.display_name
    });
  }

  async reconcileEnrollment({ deviceIdentity } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_ENROLLMENT_PACKAGED_REQUIRED', 'Kiểm tra pairing chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const identity = normalizeDeviceIdentity(deviceIdentity);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_ENROLLMENT_RUNTIME_MISSING', `${label} đóng gói cho kiểm tra pairing không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'reconcile-enrollment',
        '--config', config,
        '--device-id', identity.device_id,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_ENROLLMENT_RECONCILE_FAILED');
      throw enrollmentError(code, 'Không thể kiểm tra trạng thái pairing với Ubuntu.');
    }
    return parseEnrollmentStatusResult(result?.stdout, identity.device_id);
  }

  async rotateCredential({ deviceIdentity } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_PACKAGED_REQUIRED', 'Đổi credential chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const identity = normalizeDeviceIdentity(deviceIdentity);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_CREDENTIAL_ROTATION_RUNTIME_MISSING', `${label} đóng gói cho đổi credential không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'rotate-credential',
        '--config', config,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_CREDENTIAL_ROTATION_FAILED');
      throw enrollmentError(code, 'Không thể đổi credential node với Ubuntu.');
    }
    return parseCredentialRotationResult(result?.stdout, identity.device_id);
  }

  async reconcileAuthorityStatus({ deviceIdentity } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_PACKAGED_REQUIRED', 'Kiểm tra liên kết tài khoản chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const identity = normalizeDeviceIdentity(deviceIdentity);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_AUTHORITY_STATUS_RUNTIME_MISSING', `${label} đóng gói cho kiểm tra liên kết tài khoản không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'reconcile-authority-status',
        '--config', config,
        '--device-id', identity.device_id,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_AUTHORITY_STATUS_FAILED');
      throw enrollmentError(code, 'Không thể kiểm tra liên kết tài khoản và target với Ubuntu.');
    }
    return parseAuthorityStatusResult(result?.stdout, identity.device_id);
  }

  async installReadOnlyPolicyAssignment({ workspaceId, workspaceGeneration, replaceExisting = false } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_POLICY_PACKAGED_REQUIRED', 'Policy read-only chỉ cài từ candidate packaged đã được xác minh.');
    }
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    if (typeof replaceExisting !== 'boolean') {
      throw enrollmentError('CONTROL_PLANE_POLICY_REPLACE_INVALID', 'Lựa chọn thay thế policy cục bộ không hợp lệ.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_POLICY_RUNTIME_MISSING', `${label} đóng gói cho read-only policy không sẵn sàng.`);
      }
    }
    const args = [
      '-I', agent, 'install-read-only-policy-from-assignment',
      '--config', config,
      '--workspace-registry', this.paths.controlPlaneWorkspaceRegistryFile(),
      '--workspace-id', normalizedWorkspaceId,
      '--workspace-generation', normalizedWorkspaceGeneration,
      '--confirm-install',
      '--project-root', this.paths.appRoot(),
      '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ];
    if (replaceExisting) args.push('--replace');
    let result;
    try {
      result = await this.runner(python, args, {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_POLICY_INSTALL_FAILED');
      throw enrollmentError(code, 'Không thể đồng bộ read-only policy đã được Ubuntu cấp cho workspace này.');
    }
    return parseReadOnlyPolicyInstallResult(result?.stdout);
  }

  async registerWorkspace({ workspacePath, capabilities: requestedCapabilities } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Đăng ký workspace Ubuntu chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const canonicalPath = canonicalWorkspacePath(workspacePath);
    const displayName = workspaceDisplayName(canonicalPath);
    const capabilities = normalizeWorkspaceCapabilities(requestedCapabilities);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_WORKSPACE_RUNTIME_MISSING', `${label} đóng gói cho workspace registration không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'register-workspace',
        '--config', config,
        '--workspace-registry', registry,
        '--workspace-path', canonicalPath,
        '--display-name', displayName,
        '--capability-read',
        ...(capabilities.write ? ['--capability-write'] : []),
        ...(capabilities.exec ? ['--capability-exec'] : []),
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_REGISTRATION_FAILED');
      throw enrollmentError(code, 'Không thể đăng ký workspace local với Ubuntu.');
    }
    return parseWorkspaceRegistrationResult(result?.stdout);
  }

  async listWorkspaces() {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Danh sách workspace Ubuntu chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_WORKSPACE_RUNTIME_MISSING', `${label} đóng gói cho workspace inventory không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'list-workspaces',
        '--config', config,
        '--workspace-registry', registry,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_LIST_FAILED');
      throw enrollmentError(code, 'Không thể đọc inventory workspace local.');
    }
    return parseWorkspaceListResult(result?.stdout);
  }

  async retireWorkspace({ workspaceId, workspaceGeneration } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Thu hồi workspace Ubuntu chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_WORKSPACE_RUNTIME_MISSING', `${label} đóng gói cho workspace retirement không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'retire-workspace',
        '--config', config,
        '--workspace-registry', registry,
        '--workspace-id', normalizedWorkspaceId,
        '--workspace-generation', normalizedWorkspaceGeneration,
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_RETIRE_FAILED');
      throw enrollmentError(code, 'Không thể thu hồi workspace local tại Ubuntu.');
    }
    return parseWorkspaceRetirementResult(result?.stdout);
  }

  async replaceWorkspace({ workspacePath, capabilities: requestedCapabilities } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Thay capability workspace Ubuntu chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const canonicalPath = canonicalWorkspacePath(workspacePath);
    const displayName = workspaceDisplayName(canonicalPath);
    const capabilities = normalizeWorkspaceCapabilities(requestedCapabilities);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_WORKSPACE_RUNTIME_MISSING', `${label} đóng gói cho workspace replacement không sẵn sàng.`);
      }
    }
    let result;
    try {
      result = await this.runner(python, [
        '-I', agent, 'replace-workspace',
        '--config', config,
        '--workspace-registry', registry,
        '--workspace-path', canonicalPath,
        '--display-name', displayName,
        '--capability-read',
        ...(capabilities.write ? ['--capability-write'] : []),
        ...(capabilities.exec ? ['--capability-exec'] : []),
        '--confirm-replace',
        '--project-root', this.paths.appRoot(),
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.paths.appRoot(),
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_REPLACE_FAILED');
      throw enrollmentError(code, 'Không thể thay capability workspace local với Ubuntu.');
    }
    return parseWorkspaceReplacementResult(result?.stdout);
  }
}

module.exports = {
  ENROLLMENT_TIMEOUT_MS,
  MAX_AGENT_OUTPUT_BYTES,
  centralServerOrigin,
  centralWorkspaceId,
  centralWorkspaceGeneration,
  normalizeWorkspaceCapabilities,
  canonicalWorkspacePath,
  workspaceDisplayName,
  endpointId,
  safeEnrollmentEnvironment,
  parseEnrollmentResult,
  parseEnrollmentStatusResult,
  parseAuthorityStatusResult,
  parseCredentialRotationResult,
  parseReadOnlyPolicyInstallResult,
  parseWorkspaceRegistrationResult,
  parseWorkspaceListResult,
  parseWorkspaceRetirementResult,
  parseWorkspaceReplacementResult,
  ControlPlaneEnrollmentService
};
