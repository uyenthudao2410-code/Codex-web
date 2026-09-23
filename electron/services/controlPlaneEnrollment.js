"use strict";

// The central enrollment UI is only a node-identity request.  It does not
// alter executionRole, create a binding/context/policy, or receive an OpenAI
// credential.  The Ubuntu operator must still approve this request and issue
// every later authority record independently.

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
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
const FULL_WORKSPACE_PREFIX_SHA256 = crypto.createHash('sha256').update('["."]').digest('hex');
const FILE_READ_LIMITS = Object.freeze({ max_bytes: 16 * 1024, max_lines: 200 });
const PATCH_LIMITS = Object.freeze({ max_patch_bytes: 32 * 1024, max_file_bytes: 256 * 1024 });
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

function assertSelectedWorkspaceRegistration(registryFile, canonicalPath, workspaceId, workspaceGeneration) {
  // The renderer lists path-free inventory. A row action must still prove the
  // newly chosen local folder belongs to that exact row before invoking the
  // path-based replacement command.
  let registry;
  try {
    const raw = fs.readFileSync(registryFile);
    if (raw.length > 64 * 1024) throw new Error('registry-too-large');
    registry = JSON.parse(raw.toString('utf8'));
  } catch {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_UNVERIFIED', 'Không thể xác minh thư mục đã chọn với inventory local.');
  }
  if (!registry || registry.schema_version !== 1 || !Array.isArray(registry.entries)
    || registry.entries.length > 64) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_UNVERIFIED', 'Inventory workspace local không hợp lệ.');
  }
  const matches = registry.entries.filter((entry) => entry && typeof entry === 'object'
    && entry.workspace_id === workspaceId && entry.workspace_generation === workspaceGeneration
    && typeof entry.canonical_path === 'string' && path.normalize(entry.canonical_path) === path.normalize(canonicalPath));
  if (matches.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH', 'Thư mục vừa chọn không khớp với workspace ở dòng này. Chưa đổi quyền nào.');
  }
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

function parsePolicyAuthorityObservation(stdout, workspaceId, workspaceGeneration) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID', 'Node authority trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID', 'Node authority không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID', 'Node authority trả về receipt không hợp lệ.'); }
  const facade = payload?.facade_contract;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'binding_count,facade_contract,observed_at_ms,operation,owner_id,runtime_mode,standing_write_enabled,workspace_generation,workspace_id'
    || payload.operation !== 'control_plane_policy_authority_observation'
    || payload.workspace_id !== workspaceId || payload.workspace_generation !== workspaceGeneration
    || !NODE_ID_PATTERN.test(String(payload.owner_id || ''))
    || !Number.isSafeInteger(payload.binding_count) || payload.binding_count < 1
    || typeof payload.standing_write_enabled !== 'boolean'
    || !Number.isSafeInteger(payload.observed_at_ms) || payload.observed_at_ms <= 0
    || payload.runtime_mode !== 'packaged'
    || !facade || typeof facade !== 'object' || Array.isArray(facade)
    || Object.keys(facade).sort().join(',') !== 'profile,schema_version,sha256'
    || !Number.isSafeInteger(facade.schema_version) || facade.schema_version < 1
    || !NODE_ID_PATTERN.test(String(facade.profile || ''))
    || !SHA256_PATTERN.test(String(facade.sha256 || '').toLowerCase())) {
    throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID', 'Node authority không đúng workspace hoặc facade hiện hành.');
  }
  return Object.freeze({
    owner_id: payload.owner_id,
    workspace_id: workspaceId,
    workspace_generation: workspaceGeneration,
    facade_contract: Object.freeze({
      schema_version: facade.schema_version,
      profile: facade.profile,
      sha256: facade.sha256.toLowerCase()
    }),
    binding_count: payload.binding_count,
    standing_write_enabled: payload.standing_write_enabled,
    observed_at_ms: payload.observed_at_ms
  });
}

function parseStandingFilePolicyInstallResult(stdout, kind) {
  if (!['file_read', 'approved_patch'].includes(kind)) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID', 'Lane file policy không hợp lệ.');
  }
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID', 'Node file policy trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID', 'Node file policy không trả về đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID', 'Node file policy trả về receipt không hợp lệ.'); }
  const read = kind === 'file_read';
  const expectedKeys = read
    ? 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,max_bytes,max_lines,operation,policy_sha256,runtime_mode,windows_acl_verified'
    : 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,max_file_bytes,max_patch_bytes,operation,policy_sha256,runtime_mode,validation_profile,windows_acl_verified';
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== expectedKeys
    || payload.operation !== (read ? 'control_plane_file_read_policy_installed' : 'control_plane_approved_patch_policy_installed')
    || payload.enabled !== true || payload.authority_mode !== 'standing' || payload.expires_at_ms !== null
    || payload.allowed_prefix_count !== 1 || payload.allowed_prefixes_sha256 !== FULL_WORKSPACE_PREFIX_SHA256
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || payload.runtime_mode !== 'packaged' || payload.windows_acl_verified !== false
    || (read && (payload.max_bytes !== FILE_READ_LIMITS.max_bytes || payload.max_lines !== FILE_READ_LIMITS.max_lines))
    || (!read && (payload.max_patch_bytes !== PATCH_LIMITS.max_patch_bytes
      || payload.max_file_bytes !== PATCH_LIMITS.max_file_bytes || payload.validation_profile !== 'targeted'))) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID', 'Node file policy receipt không xác nhận đúng phạm vi workspace đã chọn.');
  }
  return Object.freeze({
    kind,
    authority_mode: 'standing',
    policy_sha256: payload.policy_sha256.toLowerCase(),
    windows_acl_verified: false
  });
}

function parseStandingFilePolicyObservation(stdout, kind) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy observation vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy không trả về đúng một observation.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy observation không hợp lệ.'); }
  const read = kind === 'file_read';
  if (!['file_read', 'approved_patch'].includes(kind)
    || !payload || typeof payload !== 'object' || Array.isArray(payload)
    || payload.operation !== (read ? 'control_plane_file_read_policy_observation' : 'control_plane_approved_patch_policy_observation')
    || payload.runtime_mode !== 'packaged' || payload.windows_acl_verified !== false) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy observation không đúng lane.');
  }
  if (payload.state === 'unavailable') {
    if (Object.keys(payload).sort().join(',') !== 'operation,reason,runtime_mode,state,windows_acl_verified'
      || !/^[A-Z0-9_]{3,96}$/.test(String(payload.reason || ''))) {
      throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy unavailable observation không hợp lệ.');
    }
    return Object.freeze({ state: 'unavailable', reason: payload.reason });
  }
  const expectedKeys = read
    ? 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,max_bytes,max_lines,operation,policy_sha256,runtime_mode,state,windows_acl_verified,workspace_generation,workspace_id'
    : 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,max_file_bytes,max_patch_bytes,operation,policy_sha256,runtime_mode,state,validation_profile,windows_acl_verified,workspace_generation,workspace_id';
  const standing = payload.authority_mode === 'standing';
  if ((standing && Object.keys(payload).sort().join(',') !== expectedKeys)
    || !['enabled', 'expired_or_disabled'].includes(payload.state)
    || !WORKSPACE_ID_PATTERN.test(String(payload.workspace_id || ''))
    || !WORKSPACE_GENERATION_PATTERN.test(String(payload.workspace_generation || ''))
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())) {
    throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID', 'Node file policy observation không đúng target.');
  }
  const active = standing && payload.state === 'enabled' && payload.enabled === true
    && payload.expires_at_ms === null && payload.allowed_prefix_count === 1
    && payload.allowed_prefixes_sha256 === FULL_WORKSPACE_PREFIX_SHA256
    && (read
      ? payload.max_bytes === FILE_READ_LIMITS.max_bytes && payload.max_lines === FILE_READ_LIMITS.max_lines
      : payload.max_patch_bytes === PATCH_LIMITS.max_patch_bytes
        && payload.max_file_bytes === PATCH_LIMITS.max_file_bytes && payload.validation_profile === 'targeted');
  return Object.freeze({
    state: active ? 'enabled' : 'not_current_standing',
    enabled: payload.enabled === true,
    workspace_id: payload.workspace_id,
    workspace_generation: payload.workspace_generation,
    policy_sha256: payload.policy_sha256.toLowerCase()
  });
}

function parsePatchPolicyDisableResult(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_PATCH_POLICY_DISABLE_OUTPUT_INVALID', 'Node patch policy disable vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  let payload;
  try { if (lines.length === 1) payload = JSON.parse(lines[0]); }
  catch { /* rejected below */ }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'enabled,operation,policy_sha256,runtime_mode,windows_acl_verified'
    || payload.operation !== 'control_plane_approved_patch_policy_disabled'
    || payload.enabled !== false || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || payload.runtime_mode !== 'packaged' || payload.windows_acl_verified !== false) {
    throw enrollmentError('CONTROL_PLANE_PATCH_POLICY_DISABLE_OUTPUT_INVALID', 'Node chưa xác nhận đã tắt patch policy cũ.');
  }
  return Object.freeze({ enabled: false, policy_sha256: payload.policy_sha256.toLowerCase() });
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
    // Electron's packaged appRoot is app.asar, a file. Child processes need
    // the physical installation directory for both cwd and --project-root.
    this.agentProjectRoot = paths.runtimeMode() === 'packaged'
      ? path.dirname(paths.executablePath())
      : paths.appRoot();
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
      '--project-root', this.agentProjectRoot,
      '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ];
    if (replaceExisting) args.push('--replace');
    let result;
    try {
      result = await this.runner(python, args, {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_POLICY_INSTALL_FAILED');
      throw enrollmentError(code, 'Không thể đồng bộ read-only policy đã được Ubuntu cấp cho workspace này.');
    }
    return parseReadOnlyPolicyInstallResult(result?.stdout);
  }

  async installStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration, allowWrite = false, replaceExisting = false } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_FILE_POLICY_PACKAGED_REQUIRED', 'Quyền đọc/sửa file chỉ cài từ candidate packaged đã được xác minh.');
    }
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    if (typeof allowWrite !== 'boolean' || typeof replaceExisting !== 'boolean') {
      throw enrollmentError('CONTROL_PLANE_FILE_POLICY_REQUEST_INVALID', 'Lựa chọn quyền file cục bộ không hợp lệ.');
    }
    const workspace = (await this.listWorkspaces()).find((item) => item.workspace_id === normalizedWorkspaceId
      && item.workspace_generation === normalizedWorkspaceGeneration);
    if (!workspace || workspace.capabilities.read !== true || (allowWrite && workspace.capabilities.write !== true)) {
      throw enrollmentError('CONTROL_PLANE_FILE_POLICY_WORKSPACE_NOT_CURRENT', 'Workspace local chưa được đăng ký với capability đọc/ghi tương ứng.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_FILE_POLICY_RUNTIME_MISSING', `${label} đóng gói cho file policy không sẵn sàng.`);
      }
    }
    const shared = [
      '--config', config,
      '--workspace-registry', registry,
      '--workspace-id', normalizedWorkspaceId,
      '--workspace-generation', normalizedWorkspaceGeneration,
    ];
    const runtime = [
      '--project-root', this.agentProjectRoot,
      '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ];
    const runAgent = async (operation, args) => {
      try {
        const result = await this.runner(python, ['-I', agent, operation, ...args], {
          cwd: this.agentProjectRoot,
          env: safeEnrollmentEnvironment(this.environment),
          timeoutMs: ENROLLMENT_TIMEOUT_MS
        });
        return result?.stdout;
      } catch (error) {
        throw enrollmentError(String(error?.code || 'CONTROL_PLANE_FILE_POLICY_INSTALL_FAILED'),
          `Không thể hoàn tất ${operation} cho workspace đã chọn.`);
      }
    };
    const authority = parsePolicyAuthorityObservation(await runAgent('inspect-policy-authority', [...shared, ...runtime]),
      normalizedWorkspaceId, normalizedWorkspaceGeneration);
    if (allowWrite && authority.standing_write_enabled !== true) {
      throw enrollmentError('CONTROL_PLANE_PATCH_POLICY_NOT_ADMITTED', 'Ubuntu chưa bật quyền sửa file đứng lâu dài cho connector này.');
    }
    const policyArgs = [
      ...shared,
      '--owner-id', authority.owner_id,
      '--facade-schema-version', String(authority.facade_contract.schema_version),
      '--facade-profile', authority.facade_contract.profile,
      '--facade-sha256', authority.facade_contract.sha256,
      '--allowed-relative-prefix', '.',
      '--confirm-install',
      ...(replaceExisting ? ['--replace'] : []),
      ...runtime
    ];
    // There is one local patch policy slot per node. Retire any old write
    // authority before switching the active file target, including when the
    // selected workspace will be read-only. A failure stops before the new
    // read policy is installed; it never leaves old write authority hidden.
    const before = await this.inspectStandingWorkspaceFilePolicies();
    if (before.approved_patch.enabled === true) {
      parsePatchPolicyDisableResult(await runAgent('disable-approved-patch-policy', [
        '--confirm-disable', ...runtime
      ]));
    }
    const fileRead = parseStandingFilePolicyInstallResult(await runAgent('install-file-read-policy', [
      ...policyArgs,
      '--max-bytes', String(FILE_READ_LIMITS.max_bytes),
      '--max-lines', String(FILE_READ_LIMITS.max_lines)
    ]), 'file_read');
    if (!allowWrite) return Object.freeze({ state: 'read_only', workspace_id: normalizedWorkspaceId,
      workspace_generation: normalizedWorkspaceGeneration, file_read: fileRead, approved_patch: null });
    try {
      const patch = parseStandingFilePolicyInstallResult(await runAgent('install-approved-patch-policy', [
        ...policyArgs,
        '--max-patch-bytes', String(PATCH_LIMITS.max_patch_bytes),
        '--max-file-bytes', String(PATCH_LIMITS.max_file_bytes)
      ]), 'approved_patch');
      return Object.freeze({ state: 'read_and_patch', workspace_id: normalizedWorkspaceId,
        workspace_generation: normalizedWorkspaceGeneration, file_read: fileRead, approved_patch: patch });
    } catch (error) {
      // An explicit partial receipt is more truthful than hiding a successful
      // read-policy replacement behind a generic IPC failure. The previous
      // patch policy was already disabled above; a malformed new receipt may
      // still leave unknown local state, so the UI must re-observe it.
      return Object.freeze({ state: 'read_only_partial', workspace_id: normalizedWorkspaceId,
        workspace_generation: normalizedWorkspaceGeneration, file_read: fileRead, approved_patch: null,
        error_code: String(error?.code || 'CONTROL_PLANE_PATCH_POLICY_INSTALL_FAILED') });
    }
  }

  async inspectStandingWorkspaceFilePolicies() {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_FILE_POLICY_PACKAGED_REQUIRED', 'Kiểm tra quyền file chỉ khả dụng từ candidate packaged.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_FILE_POLICY_RUNTIME_MISSING', `${label} đóng gói cho file policy không sẵn sàng.`);
      }
    }
    const observe = async (kind, command) => {
      let result;
      try {
        result = await this.runner(python, [
          '-I', agent, command,
          '--project-root', this.agentProjectRoot,
          '--node', this.paths.executablePath(),
          '--runtime-mode', 'packaged'
        ], {
          cwd: this.agentProjectRoot,
          env: safeEnrollmentEnvironment(this.environment),
          timeoutMs: ENROLLMENT_TIMEOUT_MS
        });
      } catch {
        throw enrollmentError('CONTROL_PLANE_FILE_POLICY_OBSERVATION_FAILED', 'Không thể kiểm tra quyền file local.');
      }
      return parseStandingFilePolicyObservation(result?.stdout, kind);
    };
    const [fileRead, approvedPatch] = await Promise.all([
      observe('file_read', 'inspect-file-read-policy'),
      observe('approved_patch', 'inspect-approved-patch-policy')
    ]);
    return Object.freeze({ file_read: fileRead, approved_patch: approvedPatch });
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
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
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_RETIRE_FAILED');
      throw enrollmentError(code, 'Không thể thu hồi workspace local tại Ubuntu.');
    }
    return parseWorkspaceRetirementResult(result?.stdout);
  }

  async replaceWorkspace({ workspacePath, workspaceId, workspaceGeneration, capabilities: requestedCapabilities } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Thay capability workspace Ubuntu chỉ chạy từ candidate packaged đã được xác minh.');
    }
    const canonicalPath = canonicalWorkspacePath(workspacePath);
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    assertSelectedWorkspaceRegistration(
      this.paths.controlPlaneWorkspaceRegistryFile(), canonicalPath,
      normalizedWorkspaceId, normalizedWorkspaceGeneration
    );
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
        '--expected-workspace-id', normalizedWorkspaceId,
        '--expected-workspace-generation', normalizedWorkspaceGeneration,
        '--display-name', displayName,
        '--capability-read',
        ...(capabilities.write ? ['--capability-write'] : []),
        ...(capabilities.exec ? ['--capability-exec'] : []),
        '--confirm-replace',
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      const code = String(error?.code || 'CONTROL_PLANE_WORKSPACE_REPLACE_FAILED');
      throw enrollmentError(code, 'Không thể thay capability workspace local với Ubuntu.');
    }
    const receipt = parseWorkspaceReplacementResult(result?.stdout);
    if (receipt.workspace_id !== normalizedWorkspaceId
      || receipt.old_workspace_generation !== normalizedWorkspaceGeneration) {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_REPLACE_TARGET_MISMATCH', 'Receipt replacement không đúng workspace đã chọn; cần đối soát trước khi tiếp tục.');
    }
    return receipt;
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
  parsePolicyAuthorityObservation,
  parseStandingFilePolicyInstallResult,
  parseStandingFilePolicyObservation,
  parseWorkspaceRegistrationResult,
  parseWorkspaceListResult,
  parseWorkspaceRetirementResult,
  parseWorkspaceReplacementResult,
  ControlPlaneEnrollmentService
};
