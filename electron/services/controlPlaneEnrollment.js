"use strict";

// Initial enrollment requires operator approval. Once paired, the local owner
// can select a registered folder within the existing bounded shared authority.
// Credentials and absolute workspace paths stay on this node.

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { canonicalPathKey, pathTraversesReparsePoint } = require('./pathSemantics');
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
const EXEC_POLICY_LIMITS = Object.freeze({ max_timeout_ms: 300_000, max_output_bytes: 65_536 });
const EXEC_ARGV_PREFIXES = Object.freeze([
  Object.freeze(['git']),
  Object.freeze(['node']),
  Object.freeze(['npm']),
  Object.freeze(['npx']),
  Object.freeze(['python']),
  Object.freeze(['python3']),
  Object.freeze(['dotnet'])
]);
const EXEC_PREFIXES_SHA256 = crypto.createHash('sha256')
  .update(JSON.stringify(EXEC_ARGV_PREFIXES)).digest('hex');
const EXECUTION_MODES = new Set(['native_first', 'native_only', 'isolated']);
const NATIVE_ARGV_PREFIXES = Object.freeze([]);
const MXC_EXEC_SHA256 = '6049c64723af1173c3739dc6cd6b2f33f6c021bb2832c4216233cba7f71aee9a';
const MXC_BASE_CONTAINER_PROBE_TIMEOUT_MS = 8_000;
const MXC_CHILD_PROCESS_PROBE_TIMEOUT_MS = 45_000;
const MXC_WINDOWS_SANDBOX_PROBE_TIMEOUT_MS = 360_000;
const MXC_WSB_SOURCE_COMMIT = 'cbe1774364ea2ec846f56ab744e43a416f751420';
const MXC_WSB_LOCAL_PATCH_SHA256 = '6b460ad92fbe61923e54fc307b7f4bc05cfc34bf8643e33a49b581735733c579';
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

function executionPolicySelection(executionMode = 'native_first', nativeArgvPrefixes = NATIVE_ARGV_PREFIXES) {
  if (!EXECUTION_MODES.has(executionMode) || !Array.isArray(nativeArgvPrefixes)
    || nativeArgvPrefixes.length > 16
    || nativeArgvPrefixes.some((prefix, index) => !Array.isArray(prefix) || prefix.length < 1 || prefix.length > 8
      || prefix.some((arg) => typeof arg !== 'string' || !arg || arg !== arg.trim()
        || Buffer.byteLength(arg, 'utf8') > 256 || Buffer.from(arg, 'utf8').toString('utf8') !== arg
        || /[\x00-\x1f\x7f;`|><]/.test(arg) || ['&&', '$('].some((token) => arg.includes(token)))
      || !EXEC_ARGV_PREFIXES.some(([tool]) => tool === prefix[0])
      || nativeArgvPrefixes.slice(0, index).some((previous) => JSON.stringify(previous) === JSON.stringify(prefix)))) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_REQUEST_INVALID', 'Chế độ chạy hoặc allowlist native không hợp lệ.');
  }
  const prefixes = nativeArgvPrefixes.map((prefix) => [...prefix]);
  return { execution_mode: executionMode, native_argv_prefixes: prefixes };
}

function observedExecutionPolicy(payload, code) {
  const fields = ['execution_mode', 'native_argv_prefixes'];
  if (fields.every((key) => !Object.hasOwn(payload, key))) {
    return { execution_mode: 'native_first', native_argv_prefixes: [] };
  }
  if (!fields.every((key) => Object.hasOwn(payload, key))) {
    throw enrollmentError(code, 'Policy chạy chưa trả về chế độ và allowlist native hợp lệ.');
  }
  try { return executionPolicySelection(payload.execution_mode, payload.native_argv_prefixes); }
  catch { throw enrollmentError(code, 'Policy chạy chưa trả về chế độ và allowlist native hợp lệ.'); }
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
    && typeof entry.canonical_path === 'string' && canonicalPathKey(entry.canonical_path) === canonicalPathKey(canonicalPath));
  if (matches.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH', 'Thư mục vừa chọn không khớp với workspace ở dòng này. Chưa đổi quyền nào.');
  }
}

function registeredWorkspacePath(registryFile, workspaceId, workspaceGeneration) {
  let registry;
  try {
    const raw = fs.readFileSync(registryFile);
    if (raw.length > 64 * 1024) throw new Error('registry-too-large');
    registry = JSON.parse(raw.toString('utf8'));
  } catch {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_UNVERIFIED', 'Không thể xác minh đường dẫn local của workspace đã chọn.');
  }
  if (!registry || registry.schema_version !== 1 || !Array.isArray(registry.entries)
    || registry.entries.length > 64) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_UNVERIFIED', 'Inventory workspace local không hợp lệ.');
  }
  const matches = registry.entries.filter((entry) => entry && typeof entry === 'object'
    && entry.workspace_id === workspaceId && entry.workspace_generation === workspaceGeneration
    && typeof entry.canonical_path === 'string' && entry.canonical_path.trim());
  if (matches.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH', 'Workspace đã chọn không khớp duy nhất một đường dẫn local đã đăng ký.');
  }
  const canonicalPath = canonicalWorkspacePath(matches[0].canonical_path);
  const storedPath = path.normalize(matches[0].canonical_path);
  const currentPath = path.normalize(canonicalPath);
  const spellingDiffers = (process.platform === 'win32' ? storedPath.toLowerCase() : storedPath) !==
    (process.platform === 'win32' ? currentPath.toLowerCase() : currentPath);
  // A spelling difference alone is not drift: registry entries written under
  // an 8.3 short name (runner TEMP) legitimately differ from the live long
  // form. Drift is a spelling difference PLUS a reparse point in the stored
  // path, meaning the registered directory was replaced (renamed + junction
  // planted). 8.3 components are not reparse points, so the walk passes them.
  if (spellingDiffers && pathTraversesReparsePoint(matches[0].canonical_path)) {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH', 'Đường dẫn workspace local đã thay đổi so với inventory đã đăng ký.');
  }
  return canonicalPath;
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
    || Object.keys(payload).sort().join(',') !== 'binding_count,exec_binding_count,exec_enabled,facade_contract,observed_at_ms,operation,owner_id,runtime_mode,server_observed_at_ms,standing_write_enabled,workspace_generation,workspace_id'
    || payload.operation !== 'control_plane_policy_authority_observation'
    || payload.workspace_id !== workspaceId || payload.workspace_generation !== workspaceGeneration
    || !NODE_ID_PATTERN.test(String(payload.owner_id || ''))
    || !Number.isSafeInteger(payload.binding_count) || payload.binding_count < 1
    || typeof payload.standing_write_enabled !== 'boolean'
    || typeof payload.exec_enabled !== 'boolean'
    || !Number.isSafeInteger(payload.exec_binding_count) || payload.exec_binding_count < 0
    || payload.exec_binding_count > payload.binding_count
    || !Number.isSafeInteger(payload.observed_at_ms) || payload.observed_at_ms <= 0
    || !Number.isSafeInteger(payload.server_observed_at_ms) || payload.server_observed_at_ms <= 0
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
    exec_enabled: payload.exec_enabled,
    exec_binding_count: payload.exec_binding_count,
    observed_at_ms: payload.observed_at_ms,
    server_observed_at_ms: payload.server_observed_at_ms
  });
}

function parseMxcSandboxProbe(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'MXC sandbox probe vượt giới hạn.');
  }
  let payload;
  try { payload = JSON.parse(output); }
  catch { throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'MXC sandbox probe không phải JSON hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || typeof payload.tier !== 'string'
    || typeof payload.needsDaclAugmentation !== 'boolean'
    || !payload.probes || typeof payload.probes !== 'object' || Array.isArray(payload.probes)
    || typeof payload.probes.baseContainerApiPresent !== 'boolean'
    || typeof payload.probes.baseContainerSupportsDenyPaths !== 'boolean'
    || !Array.isArray(payload.warnings)
    || payload.warnings.some((item) => typeof item !== 'string')) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'MXC sandbox probe thiếu trường bắt buộc.');
  }
  const available = payload.tier === 'base-container'
    && payload.needsDaclAugmentation === false
    && payload.probes.baseContainerApiPresent === true
    && payload.probes.baseContainerSupportsDenyPaths === true
    && payload.warnings.length === 0;
  return Object.freeze({
    state: available ? 'available' : 'unavailable',
    tier: payload.tier,
    dacl_fallback: payload.needsDaclAugmentation,
    base_container_api: payload.probes.baseContainerApiPresent,
    deny_paths_supported: payload.probes.baseContainerSupportsDenyPaths,
    reason: available ? null : 'WINDOWS_BASE_CONTAINER_UNAVAILABLE'
  });
}

function parseMxcChildProcessProbe(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Nested-process probe vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Nested-process probe không trả đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Nested-process probe receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'available,probe,reason'
    || payload.probe !== 'mxc_nested_process_v1'
    || typeof payload.available !== 'boolean'
    || (payload.available && payload.reason !== null)
    || (!payload.available && !/^[A-Z0-9_]{3,96}$/.test(String(payload.reason || '')))) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Nested-process probe receipt thiếu trường hoặc sai định dạng.');
  }
  return Object.freeze({ available: payload.available, reason: payload.reason });
}

function parseMxcWindowsSandboxChildProcessProbe(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Windows Sandbox child probe vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Windows Sandbox child probe không trả đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Windows Sandbox child probe receipt không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).sort().join(',') !== 'available,probe,reason'
    || payload.probe !== 'mxc_wsb_child_process_v1'
    || typeof payload.available !== 'boolean'
    || (payload.available && payload.reason !== null)
    || (!payload.available && !/^[A-Z0-9_]{2,96}$/.test(String(payload.reason || '')))) {
    throw enrollmentError('CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID', 'Windows Sandbox child probe receipt sai schema.');
  }
  return Object.freeze({ available: payload.available, reason: payload.reason });
}

function verifyMxcWindowsSandboxCandidate(resourcesRoot) {
  const directory = path.join(path.resolve(resourcesRoot), 'tools', 'mxc-windows-sandbox');
  const expectedBinaryNames = [
    'wxc-exec.exe',
    'wxc-windows-sandbox-daemon.exe',
    'wxc-windows-sandbox-guest.exe'
  ];
  let provenance;
  try {
    provenance = JSON.parse(fs.readFileSync(path.join(directory, 'mxc-windows-sandbox.provenance.json'), 'utf8'));
  } catch {
    throw enrollmentError('MXC_WSB_PROVENANCE_INVALID', 'Provenance của MXC Windows Sandbox candidate không đọc được.');
  }
  const expectedProvenanceKeys = 'authenticode,backend,binaries,build_profile,component,distribution,experimental,license,lifecycle,local_patch_file,local_patch_sha256,mxc_crate_version,rustc,schema_version,source_commit,source_commit_signature,source_repository,target';
  if (!provenance || typeof provenance !== 'object' || Array.isArray(provenance)
    || Object.keys(provenance).sort().join(',') !== expectedProvenanceKeys
    || provenance.component !== 'Microsoft MXC Windows Sandbox state-aware candidate'
    || provenance.source_repository !== 'https://github.com/microsoft/mxc'
    || provenance.source_commit !== MXC_WSB_SOURCE_COMMIT
    || provenance.local_patch_file !== 'scripts/patches/mxc-windows-sandbox-c-drive-share.patch'
    || provenance.local_patch_sha256 !== MXC_WSB_LOCAL_PATCH_SHA256
    || provenance.source_commit_signature !== 'unsigned'
    || provenance.mxc_crate_version !== '0.8.0'
    || provenance.schema_version !== '0.10.0-alpha'
    || provenance.backend !== 'windows_sandbox'
    || provenance.lifecycle !== 'state-aware'
    || provenance.experimental !== true
    || provenance.build_profile !== 'release'
    || provenance.target !== 'x86_64-pc-windows-msvc'
    || provenance.authenticode !== 'unsigned-local-source-build'
    || provenance.distribution !== 'development-candidate-only'
    || provenance.license !== 'MIT'
    || typeof provenance.rustc !== 'string'
    || Object.keys(provenance.binaries || {}).sort().join(',') !== expectedBinaryNames.slice().sort().join(',')) {
    throw enrollmentError('MXC_WSB_PROVENANCE_INVALID', 'Provenance của MXC Windows Sandbox candidate không khớp source/contract đã ghim.');
  }
  const hashes = {};
  for (const name of expectedBinaryNames) {
    const file = path.join(directory, name);
    let metadata;
    let digest;
    try {
      metadata = fs.statSync(file);
      if (!metadata.isFile()) throw new Error('not-file');
      digest = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    } catch {
      throw enrollmentError('MXC_WSB_BINARY_MISSING', 'Thiếu binary của MXC Windows Sandbox candidate.');
    }
    const receipt = provenance.binaries[name];
    if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)
      || Object.keys(receipt).sort().join(',') !== 'sha256,size_bytes'
      || !SHA256_PATTERN.test(String(receipt.sha256 || ''))
      || !Number.isSafeInteger(receipt.size_bytes) || receipt.size_bytes <= 0
      || metadata.size !== receipt.size_bytes || digest !== receipt.sha256) {
      throw enrollmentError('MXC_WSB_BINARY_HASH_MISMATCH', 'Hash của MXC Windows Sandbox candidate không khớp provenance build đã ghim.');
    }
    hashes[name] = digest;
  }
  return Object.freeze({
    directory,
    hashes: Object.freeze(hashes),
    source_commit: MXC_WSB_SOURCE_COMMIT,
    local_patch_sha256: MXC_WSB_LOCAL_PATCH_SHA256
  });
}

function parseExecPolicyInstallResult(stdout, workspaceId, workspaceGeneration, selection = executionPolicySelection()) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID', 'Node exec policy trả về dữ liệu vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID', 'Node exec policy không trả đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID', 'Node exec policy receipt không hợp lệ.'); }
  const expectedKeys = 'allowed_argv_prefix_count,allowed_argv_prefixes_sha256,authority_mode,enabled,execution,expires_at_ms,max_concurrent,max_output_bytes,max_timeout_ms,operation,policy_sha256,runtime_mode,workspace_generation,workspace_id';
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).filter((key) => !['execution_mode', 'native_argv_prefixes'].includes(key)).sort().join(',') !== expectedKeys
    || payload.operation !== 'control_plane_exec_policy_installed'
    || payload.execution !== 'exec_policy_installed'
    || payload.enabled !== true || payload.authority_mode !== 'standing' || payload.expires_at_ms !== null
    || payload.workspace_id !== workspaceId || payload.workspace_generation !== workspaceGeneration
    || payload.allowed_argv_prefix_count !== EXEC_ARGV_PREFIXES.length
    || payload.allowed_argv_prefixes_sha256 !== EXEC_PREFIXES_SHA256
    || payload.max_timeout_ms !== EXEC_POLICY_LIMITS.max_timeout_ms
    || payload.max_output_bytes !== EXEC_POLICY_LIMITS.max_output_bytes
    || payload.max_concurrent !== 2
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || payload.runtime_mode !== 'packaged') {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID', 'Node exec policy receipt không đúng workspace, generation hoặc allowlist đã chọn.');
  }
  const execution = observedExecutionPolicy(payload, 'CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID');
  if (execution.execution_mode !== selection.execution_mode
    || JSON.stringify(execution.native_argv_prefixes) !== JSON.stringify(selection.native_argv_prefixes)) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID', 'Exec policy receipt không khớp chế độ hoặc allowlist native đã chọn.');
  }
  return Object.freeze({
    state: 'enabled',
    workspace_id: workspaceId,
    workspace_generation: workspaceGeneration,
    policy_sha256: payload.policy_sha256.toLowerCase(),
    allowed_argv_prefix_count: payload.allowed_argv_prefix_count,
    allowed_argv_prefixes_sha256: payload.allowed_argv_prefixes_sha256,
    ...execution
  });
}

function parseObservedPolicyFacade(value, code) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || Object.keys(value).sort().join(',') !== 'profile,schema_version,sha256'
    || !Number.isSafeInteger(value.schema_version) || value.schema_version < 1
    || !NODE_ID_PATTERN.test(String(value.profile || ''))
    || !SHA256_PATTERN.test(String(value.sha256 || ''))) {
    throw enrollmentError(code, 'Policy local chưa trả về facade contract hợp lệ.');
  }
  return Object.freeze({ schema_version: value.schema_version, profile: value.profile, sha256: value.sha256 });
}

function parseExecPolicyObservation(stdout) {
  const output = String(stdout || '');
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy observation vượt giới hạn.');
  }
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length !== 1) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy observation không trả đúng một receipt.');
  }
  let payload;
  try { payload = JSON.parse(lines[0]); }
  catch { throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy observation không hợp lệ.'); }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)
    || payload.operation !== 'control_plane_exec_policy_observation'
    || payload.execution !== 'exec_policy_inspected' || payload.runtime_mode !== 'packaged') {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy observation không đúng lane.');
  }
  if (payload.state === 'unavailable') {
    if (Object.keys(payload).sort().join(',') !== 'execution,operation,reason,runtime_mode,state'
      || !/^[A-Z0-9_]{3,96}$/.test(String(payload.reason || ''))) {
      throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy unavailable receipt không hợp lệ.');
    }
    return Object.freeze({ state: 'unavailable', reason: payload.reason });
  }
  const expectedKeys = 'allowed_argv_prefix_count,allowed_argv_prefixes_sha256,authority_mode,enabled,execution,expires_at_ms,facade_contract,max_concurrent,max_output_bytes,max_timeout_ms,operation,policy_sha256,runtime_mode,state,workspace_generation,workspace_id';
  if (Object.keys(payload).filter((key) => !['execution_mode', 'native_argv_prefixes'].includes(key)).sort().join(',') !== expectedKeys
    || !['enabled', 'disabled'].includes(payload.state)
    || !['standing', 'expiring_legacy'].includes(payload.authority_mode)
    || !WORKSPACE_ID_PATTERN.test(String(payload.workspace_id || ''))
    || !WORKSPACE_GENERATION_PATTERN.test(String(payload.workspace_generation || ''))
    || !SHA256_PATTERN.test(String(payload.policy_sha256 || '').toLowerCase())
    || !Number.isSafeInteger(payload.allowed_argv_prefix_count) || payload.allowed_argv_prefix_count < 1
    || !SHA256_PATTERN.test(String(payload.allowed_argv_prefixes_sha256 || '').toLowerCase())
    || !Number.isSafeInteger(payload.max_timeout_ms) || !Number.isSafeInteger(payload.max_output_bytes)
    || !Number.isSafeInteger(payload.max_concurrent)) {
    throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID', 'Exec policy observation không đúng target hoặc allowlist.');
  }
  const currentStanding = payload.state === 'enabled' && payload.enabled === true
    && payload.authority_mode === 'standing' && payload.expires_at_ms === null
    && payload.allowed_argv_prefix_count === EXEC_ARGV_PREFIXES.length
    && payload.allowed_argv_prefixes_sha256 === EXEC_PREFIXES_SHA256
    && payload.max_timeout_ms === EXEC_POLICY_LIMITS.max_timeout_ms
    && payload.max_output_bytes === EXEC_POLICY_LIMITS.max_output_bytes
    && payload.max_concurrent === 2;
  return Object.freeze({
    state: currentStanding ? 'enabled' : 'not_current_standing',
    enabled: payload.enabled === true,
    workspace_id: payload.workspace_id,
    workspace_generation: payload.workspace_generation,
    facade_contract: parseObservedPolicyFacade(payload.facade_contract, 'CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID'),
    policy_sha256: payload.policy_sha256.toLowerCase(),
    allowed_argv_prefix_count: payload.allowed_argv_prefix_count,
    allowed_argv_prefixes_sha256: payload.allowed_argv_prefixes_sha256,
    ...observedExecutionPolicy(payload, 'CONTROL_PLANE_EXEC_POLICY_OBSERVATION_INVALID')
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
    ? 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,facade_contract,max_bytes,max_lines,operation,policy_sha256,runtime_mode,state,windows_acl_verified,workspace_generation,workspace_id'
    : 'allowed_prefix_count,allowed_prefixes_sha256,authority_mode,enabled,expires_at_ms,facade_contract,max_file_bytes,max_patch_bytes,operation,policy_sha256,runtime_mode,state,validation_profile,windows_acl_verified,workspace_generation,workspace_id';
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
    facade_contract: parseObservedPolicyFacade(payload.facade_contract, 'CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID'),
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

function parseWorkspaceActivationResult(stdout, workspaceId, workspaceGeneration) {
  const output = String(stdout || '');
  const lines = output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  let payload;
  try { if (lines.length === 1) payload = JSON.parse(lines[0]); } catch { /* rejected below */ }
  // No-pilot contract: the binding receipt carries only device, workspace,
  // binding and state. Stale pilot fields (pilot_decision_id, expires_at_ms)
  // and the legacy replayed flag, when present in an old response, are
  // ignored, never required and never stored. Any other extra field is
  // still rejected so path/secret material cannot smuggle through.
  const required = ['binding_id', 'device_id', 'state', 'workspace_generation', 'workspace_id'];
  const allowedExtra = new Set(['pilot_decision_id', 'expires_at_ms', 'replayed']);
  if (Buffer.byteLength(output, 'utf8') > MAX_AGENT_OUTPUT_BYTES
    || !payload || typeof payload !== 'object' || Array.isArray(payload)
    || Object.keys(payload).some((key) => !required.includes(key) && !allowedExtra.has(key))
    || !required.every((key) => Object.hasOwn(payload, key))
    || payload.workspace_id !== workspaceId || payload.workspace_generation !== workspaceGeneration
    || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(String(payload.device_id || ''))
    || !/^bind_[0-9a-f]{32}$/.test(String(payload.binding_id || ''))
    || payload.state !== 'active') {
    throw enrollmentError('CONTROL_PLANE_WORKSPACE_ACTIVATION_OUTPUT_INVALID', 'Biên nhận liên kết không khớp thư mục đã chọn. Cần đối soát trước khi tiếp tục.');
  }
  return Object.freeze({
    device_id: payload.device_id,
    workspace_id: payload.workspace_id,
    workspace_generation: payload.workspace_generation,
    binding_id: payload.binding_id,
    state: 'active'
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
  constructor({ paths, runner = run, environment = process.env, experimentalWindowsSandbox = false,
    getExecutionMode = () => 'sandboxed' } = {}) {
    if (!paths || typeof paths.runtimeMode !== 'function' || typeof paths.portablePython !== 'function'
      || typeof paths.controlPlaneNodeAgent !== 'function' || typeof paths.controlPlaneNodeConfigFile !== 'function'
      || typeof paths.controlPlaneWorkspaceRegistryFile !== 'function'
      || typeof paths.appRoot !== 'function' || typeof paths.executablePath !== 'function') {
      throw new TypeError('ControlPlaneEnrollmentService requires complete runtime paths.');
    }
    this.paths = paths;
    this.runner = runner;
    this.environment = environment;
    this.experimentalWindowsSandbox = experimentalWindowsSandbox === true;
    if (typeof getExecutionMode !== 'function') throw new TypeError('getExecutionMode must be a function.');
    this.getExecutionMode = getExecutionMode;
    // Electron's packaged appRoot is app.asar, a file. Child processes need
    // the physical installation directory for both cwd and --project-root.
    this.agentProjectRoot = paths.runtimeMode() === 'packaged'
      ? path.dirname(paths.executablePath())
      : paths.appRoot();
    this.mxcSandboxProbeCache = new Map();
    this.mxcSandboxProbesInFlight = new Map();
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
    // Replace only this exact generation. Other registered workspaces retain
    // their policies and can continue serving their already bound tasks.
    const before = await this.inspectStandingWorkspaceFilePolicies({
      workspaceId: normalizedWorkspaceId, workspaceGeneration: normalizedWorkspaceGeneration
    });
    if (before.approved_patch.enabled === true) {
      parsePatchPolicyDisableResult(await runAgent('disable-approved-patch-policy', [
        '--workspace-id', normalizedWorkspaceId,
        '--workspace-generation', normalizedWorkspaceGeneration,
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

  async runPackagedNodeAgent(operation, args = []) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_AGENT_PACKAGED_REQUIRED', 'Node-agent authority chỉ chạy từ bản packaged.');
    }
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    for (const [label, file] of [['Python', python], ['node agent', agent]]) {
      try {
        if (!fs.statSync(file).isFile()) throw new Error('missing');
      } catch {
        throw enrollmentError('CONTROL_PLANE_AGENT_RUNTIME_MISSING', label + ' đóng gói không sẵn sàng.');
      }
    }
    try {
      return await this.runner(python, [
        '-I', agent, operation, ...args,
        '--project-root', this.agentProjectRoot,
        '--node', this.paths.executablePath(),
        '--runtime-mode', 'packaged'
      ], {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: ENROLLMENT_TIMEOUT_MS
      });
    } catch (error) {
      throw enrollmentError(
        String(error?.code || 'CONTROL_PLANE_AGENT_FAILED'),
        'Không thể hoàn tất ' + operation + ' bằng node-agent packaged.'
      );
    }
  }

  async inspectLocalExecPolicy({ workspaceId, workspaceGeneration } = {}) {
    const target = workspaceId == null && workspaceGeneration == null ? [] : [
      '--workspace-id', centralWorkspaceId(workspaceId),
      '--workspace-generation', centralWorkspaceGeneration(workspaceGeneration)
    ];
    const result = await this.runPackagedNodeAgent('inspect-exec-policy', target);
    return parseExecPolicyObservation(result?.stdout);
  }

  async inspectCurrentPolicyAuthority(policy) {
    const result = await this.runPackagedNodeAgent('inspect-policy-authority', [
      '--config', this.paths.controlPlaneNodeConfigFile(),
      '--workspace-registry', this.paths.controlPlaneWorkspaceRegistryFile(),
      '--workspace-id', policy.workspace_id,
      '--workspace-generation', policy.workspace_generation
    ]);
    const authority = parsePolicyAuthorityObservation(result?.stdout, policy.workspace_id, policy.workspace_generation);
    const age = Date.now() - authority.observed_at_ms;
    if (age < 0 || age >= 60_000) {
      throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_STALE', 'Chưa xác minh facade contract hiện hành của Ubuntu.');
    }
    return authority;
  }

  async inspectMxcWindowsSandbox({ resourcesRoot, canonicalRoot, binaryHash, probeSandbox = true } = {}) {
    if (this.experimentalWindowsSandbox !== true) return null;
    const windowsRoot = String(this.environment.SystemRoot || this.environment.WINDIR || 'C:\\Windows');
    const windowsSandboxExecutable = path.join(windowsRoot, 'System32', 'WindowsSandbox.exe');
    if (process.platform !== 'win32' || !fs.existsSync(windowsSandboxExecutable)) return null;

    let candidate;
    try { candidate = verifyMxcWindowsSandboxCandidate(resourcesRoot); }
    catch (error) {
      return Object.freeze({
        state: 'unavailable',
        backend: 'windows_sandbox',
        reason: String(error?.code || 'MXC_WSB_CANDIDATE_INVALID'),
        binary_sha256: binaryHash,
        release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
      });
    }

    const cacheKey = `${canonicalRoot}|${Object.values(candidate.hashes).join(':')}`;
    const cached = this.mxcSandboxProbeCache.get(cacheKey);
    if (cached && cached.expires_at_ms > Date.now()) return cached.result;
    for (const [key, entry] of this.mxcSandboxProbeCache) {
      if (!entry || entry.expires_at_ms <= Date.now()) this.mxcSandboxProbeCache.delete(key);
    }
    if (!probeSandbox) return Object.freeze({
      state: 'not_checked', backend: 'windows_sandbox', reason: 'SANDBOX_PROBE_REQUIRED'
    });
    const inFlight = this.mxcSandboxProbesInFlight.get(cacheKey);
    if (inFlight) return inFlight;

    const python = this.paths.portablePython();
    const packageRoot = path.join(resourcesRoot, 'coding-tools-mcp');
    try {
      if (!fs.statSync(python).isFile() || !fs.statSync(packageRoot).isDirectory()) throw new Error('missing');
    } catch {
      return Object.freeze({
        state: 'unavailable',
        backend: 'windows_sandbox',
        reason: 'NESTED_PROCESS_PROBE_RUNTIME_MISSING',
        binary_sha256: candidate.hashes['wxc-exec.exe'],
        source_commit: candidate.source_commit,
        release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
      });
    }
    const probeCode = [
      'import json,sys;',
      `sys.path.insert(0,${JSON.stringify(packageRoot)});`,
      'from coding_tools_mcp.windows_mxc_state_aware import probe_mxc_windows_sandbox_child_process;',
      `print(json.dumps(probe_mxc_windows_sandbox_child_process(${JSON.stringify(canonicalRoot)}),separators=(',',':')))`
    ].join('');
    const pendingProbe = (async () => {
      let childProbeResult;
      try {
        childProbeResult = await this.runner(python, ['-B', '-I', '-c', probeCode], {
          cwd: this.agentProjectRoot,
          env: safeEnrollmentEnvironment(this.environment),
          timeoutMs: MXC_WINDOWS_SANDBOX_PROBE_TIMEOUT_MS
        });
      } catch (error) {
        return Object.freeze({
          state: 'unavailable',
          backend: 'windows_sandbox',
          reason: String(error?.code || 'MXC_WSB_CHILD_PROCESS_PROBE_FAILED'),
          binary_sha256: candidate.hashes['wxc-exec.exe'],
          source_commit: candidate.source_commit,
          release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
        });
      }
      try {
        const childProbe = parseMxcWindowsSandboxChildProcessProbe(childProbeResult?.stdout);
        const observation = Object.freeze({
          state: childProbe.available ? 'available' : 'unavailable',
          backend: 'windows_sandbox',
          child_process_spawn: childProbe.available,
          reason: childProbe.available ? null : childProbe.reason,
          binary_sha256: candidate.hashes['wxc-exec.exe'],
          source_commit: candidate.source_commit,
          release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
        });
        if (childProbe.available) {
          this.mxcSandboxProbeCache.set(cacheKey, {
            expires_at_ms: Date.now() + (5 * 60_000),
            result: observation
          });
        }
        return observation;
      } catch (error) {
        return Object.freeze({
          state: 'unavailable',
          backend: 'windows_sandbox',
          reason: String(error?.code || 'MXC_WSB_CHILD_PROCESS_PROBE_INVALID'),
          binary_sha256: candidate.hashes['wxc-exec.exe'],
          source_commit: candidate.source_commit,
          release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
        });
      }
    })();
    this.mxcSandboxProbesInFlight.set(cacheKey, pendingProbe);
    try { return await pendingProbe; }
    finally {
      if (this.mxcSandboxProbesInFlight.get(cacheKey) === pendingProbe) this.mxcSandboxProbesInFlight.delete(cacheKey);
    }
  }

  async inspectMxcSandbox({ workspaceRoot, probeSandbox = true, backend = 'auto', capabilityOnly = false } = {}) {
    if (!['packaged', 'development'].includes(this.paths.runtimeMode())) {
      return Object.freeze({ state: 'unavailable', reason: 'SUPPORTED_RUNTIME_REQUIRED' });
    }
    if (typeof workspaceRoot !== 'string' || !workspaceRoot.trim()) {
      return Object.freeze({ state: 'unavailable', reason: 'WORKSPACE_SELECTION_REQUIRED' });
    }
    let canonicalRoot;
    try { canonicalRoot = canonicalWorkspacePath(workspaceRoot); }
    catch (error) {
      return Object.freeze({ state: 'unavailable', reason: String(error?.code || 'WORKSPACE_SELECTION_INVALID') });
    }
    const resourcesRoot = typeof this.paths.resourcesRoot === 'function'
      ? this.paths.resourcesRoot()
      : path.join(path.dirname(this.paths.executablePath()), 'resources', 'resources');
    const executable = path.join(resourcesRoot, 'tools', 'wxc-exec.exe');
    let binaryHash;
    try {
      if (!fs.statSync(executable).isFile()) throw new Error('missing');
      binaryHash = crypto.createHash('sha256').update(fs.readFileSync(executable)).digest('hex');
    } catch {
      return Object.freeze({ state: 'unavailable', reason: 'MXC_EXECUTOR_MISSING' });
    }
    if (binaryHash !== MXC_EXEC_SHA256) {
      return Object.freeze({ state: 'unavailable', reason: 'MXC_EXECUTOR_HASH_MISMATCH' });
    }
    const windowsSandboxProbe = backend === 'process_container' ? null : await this.inspectMxcWindowsSandbox({
      resourcesRoot,
      canonicalRoot,
      binaryHash,
      probeSandbox
    });
    if (windowsSandboxProbe) return windowsSandboxProbe;
    const cacheKey = `${canonicalRoot}|${binaryHash}${capabilityOnly ? '|capability' : ''}`;
    const cached = this.mxcSandboxProbeCache.get(cacheKey);
    if (cached && cached.expires_at_ms > Date.now()) return cached.result;
    if (!probeSandbox) return Object.freeze({
      state: 'not_checked', backend: 'process_container', reason: 'SANDBOX_PROBE_REQUIRED'
    });
    let result;
    try {
      result = await this.runner(executable, ['--experimental', '--probe'], {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: MXC_BASE_CONTAINER_PROBE_TIMEOUT_MS
      });
    } catch (error) {
      return Object.freeze({ state: 'unavailable', reason: String(error?.code || 'MXC_SANDBOX_PROBE_FAILED') });
    }
    let baseProbe;
    try {
      baseProbe = parseMxcSandboxProbe(result?.stdout);
    } catch (error) {
      return Object.freeze({ state: 'unavailable', reason: String(error?.code || 'MXC_SANDBOX_PROBE_INVALID') });
    }
    if (baseProbe.state !== 'available') {
      return Object.freeze({ ...baseProbe, binary_sha256: binaryHash, release: 'microsoft-mxc-v0.8.0' });
    }
    if (capabilityOnly) {
      const observation = Object.freeze({ ...baseProbe, backend: 'process_container',
        capability_verified: true, execution_verified: false,
        binary_sha256: binaryHash, release: 'microsoft-mxc-v0.8.0' });
      this.mxcSandboxProbeCache.set(cacheKey, { expires_at_ms: Date.now() + 5 * 60_000, result: observation });
      return observation;
    }
    const python = this.paths.portablePython();
    const packageRoot = path.join(resourcesRoot, 'coding-tools-mcp');
    try {
      if (!fs.statSync(python).isFile() || !fs.statSync(packageRoot).isDirectory()) throw new Error('missing');
    } catch {
      return Object.freeze({
        ...baseProbe,
        state: 'unavailable',
        reason: 'NESTED_PROCESS_PROBE_RUNTIME_MISSING',
        binary_sha256: binaryHash,
        release: 'microsoft-mxc-v0.8.0'
      });
    }
    const probeCode = [
      'import json,sys;',
      `sys.path.insert(0,${JSON.stringify(packageRoot)});`,
      'from coding_tools_mcp.windows_mxc_sandbox import probe_mxc_child_process;',
      `print(json.dumps(probe_mxc_child_process(${JSON.stringify(canonicalRoot)}),separators=(',',':')))`
    ].join('');
    let childProbeResult;
    try {
      childProbeResult = await this.runner(python, ['-B', '-I', '-c', probeCode], {
        cwd: this.agentProjectRoot,
        env: safeEnrollmentEnvironment(this.environment),
        timeoutMs: MXC_CHILD_PROCESS_PROBE_TIMEOUT_MS
      });
    } catch (error) {
      return Object.freeze({
        ...baseProbe,
        state: 'unavailable',
        reason: String(error?.code || 'NESTED_PROCESS_PROBE_FAILED'),
        binary_sha256: binaryHash,
        release: 'microsoft-mxc-v0.8.0'
      });
    }
    try {
      const childProbe = parseMxcChildProcessProbe(childProbeResult?.stdout);
      const wsbCandidate = process.platform === 'win32' && backend !== 'process_container'
        ? (() => { try { return verifyMxcWindowsSandboxCandidate(resourcesRoot); } catch { return null; } })()
        : null;
      const windowsSandboxExecutable = path.join(
        String(this.environment.SystemRoot || this.environment.WINDIR || 'C:\\Windows'),
        'System32',
        'WindowsSandbox.exe'
      );
      const baseContainerRootPathFailure = new Set([
        'WINDOWS_WORKSPACE_REALPATH_EPERM',
        'WINDOWS_CWD_REALPATH_EPERM'
      ]).has(childProbe.reason);
      if (!childProbe.available && wsbCandidate && !fs.existsSync(windowsSandboxExecutable)
        && baseContainerRootPathFailure) {
        return Object.freeze({
          ...baseProbe,
          state: 'unavailable',
          backend: 'windows_sandbox',
          child_process_spawn: false,
          reason: 'WINDOWS_SANDBOX_NOT_READY',
          binary_sha256: wsbCandidate.hashes['wxc-exec.exe'],
          source_commit: wsbCandidate.source_commit,
          release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
        });
      }
      const observation = Object.freeze({
        ...baseProbe,
        state: childProbe.available ? 'available' : 'unavailable',
        child_process_spawn: childProbe.available,
        reason: childProbe.available ? null : childProbe.reason,
        binary_sha256: binaryHash,
        release: 'microsoft-mxc-v0.8.0'
      });
      if (childProbe.available) this.mxcSandboxProbeCache.set(cacheKey, {
        expires_at_ms: Date.now() + (5 * 60_000), result: observation
      });
      return observation;
    } catch (error) {
      return Object.freeze({
        ...baseProbe,
        state: 'unavailable',
        reason: String(error?.code || 'MXC_CHILD_PROCESS_PROBE_INVALID'),
        binary_sha256: binaryHash,
        release: 'microsoft-mxc-v0.8.0'
      });
    }
  }

  async inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, probeSandbox = false, executionMode } = {}) {
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    const workspaceRoot = registeredWorkspacePath(
      this.paths.controlPlaneWorkspaceRegistryFile(),
      normalizedWorkspaceId,
      normalizedWorkspaceGeneration
    );
    const policyResult = await this.inspectLocalExecPolicy({
      workspaceId: normalizedWorkspaceId, workspaceGeneration: normalizedWorkspaceGeneration
    }).then(
      (policy) => policy,
      (error) => Object.freeze({
        state: 'unavailable',
        reason: String(error?.code || 'EXEC_POLICY_OBSERVATION_UNAVAILABLE')
      })
    );
    const mode = executionMode || policyResult.execution_mode || 'native_first';
    if (!EXECUTION_MODES.has(mode)) throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_REQUEST_INVALID', 'Chế độ chạy không hợp lệ.');
    const runtimeMode = this.getExecutionMode();
    if (!['local', 'sandboxed'].includes(runtimeMode)) {
      throw enrollmentError('CONTROL_PLANE_EXECUTION_MODE_INVALID', 'Chế độ thực thi local hoặc sandboxed không hợp lệ.');
    }
    let sandbox;
    if (runtimeMode === 'local') {
      sandbox = Object.freeze({ state: 'not_required', backend: 'host_user', reason: 'OPERATOR_LOCAL_EXECUTION' });
    } else {
      const observedSandbox = await this.inspectMxcSandbox({ workspaceRoot, probeSandbox: probeSandbox === true,
        backend: mode === 'isolated' ? 'auto' : 'process_container', capabilityOnly: mode !== 'isolated' });
      sandbox = Object.freeze({ backend: mode === 'isolated' ? 'windows_sandbox' : 'process_container',
        ...observedSandbox,
        ...(mode !== 'isolated' && observedSandbox.state === 'not_checked' ? { reason: 'NATIVE_CAPABILITY_NOT_CHECKED' } : {}) });
    }
    let policy = policyResult;
    if (policy.state === 'enabled') {
      try {
        if (policy.workspace_id !== normalizedWorkspaceId || policy.workspace_generation !== normalizedWorkspaceGeneration) {
          throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_TARGET_MISMATCH', 'Policy chạy chưa khớp thư mục đã chọn.');
        }
        const authority = await this.inspectCurrentPolicyAuthority(policy);
        if (authority.exec_enabled !== true || authority.exec_binding_count < 1) {
          throw enrollmentError('CONTROL_PLANE_EXEC_NOT_ADMITTED', 'Ubuntu chưa bật quyền chạy lệnh cho binding này.');
        }
        policy = Object.freeze({ ...policy, current_facade_contract: authority.facade_contract,
          authority_observed_at_ms: authority.observed_at_ms });
      } catch (error) {
        policy = Object.freeze({ ...policy, current_facade_contract: null, authority_observed_at_ms: null,
          reason: String(error?.code || 'CONTROL_PLANE_POLICY_AUTHORITY_UNAVAILABLE') });
      }
    }
    return Object.freeze({ policy, sandbox, execution_mode: mode });
  }

  async installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, replaceExisting = false, probeSandbox = false,
    executionMode = 'native_first', nativeArgvPrefixes = NATIVE_ARGV_PREFIXES } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_PACKAGED_REQUIRED', 'Exec policy chỉ cài từ candidate packaged đã xác minh.');
    }
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    if (typeof replaceExisting !== 'boolean' || typeof probeSandbox !== 'boolean') {
      throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_REQUEST_INVALID', 'Lựa chọn cài exec policy không hợp lệ.');
    }
    const selection = executionPolicySelection(executionMode, nativeArgvPrefixes);
    const runtimeMode = this.getExecutionMode();
    if (!['local', 'sandboxed'].includes(runtimeMode)) {
      throw enrollmentError('CONTROL_PLANE_EXECUTION_MODE_INVALID', 'Chế độ thực thi local hoặc sandboxed không hợp lệ.');
    }
    const workspace = (await this.listWorkspaces()).find((item) =>
      item.workspace_id === normalizedWorkspaceId && item.workspace_generation === normalizedWorkspaceGeneration);
    if (!workspace || workspace.capabilities.read !== true || workspace.capabilities.exec !== true) {
      throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_WORKSPACE_NOT_CURRENT', 'Workspace đã chọn chưa đăng ký capability exec.');
    }
    const workspaceRoot = registeredWorkspacePath(
      this.paths.controlPlaneWorkspaceRegistryFile(),
      normalizedWorkspaceId,
      normalizedWorkspaceGeneration
    );
    const shared = [
      '--config', this.paths.controlPlaneNodeConfigFile(),
      '--workspace-registry', this.paths.controlPlaneWorkspaceRegistryFile(),
      '--workspace-id', normalizedWorkspaceId,
      '--workspace-generation', normalizedWorkspaceGeneration
    ];
    const authorityResult = await this.runPackagedNodeAgent('inspect-policy-authority', shared);
    const authority = parsePolicyAuthorityObservation(
      authorityResult?.stdout, normalizedWorkspaceId, normalizedWorkspaceGeneration
    );
    const authorityAge = Date.now() - authority.observed_at_ms;
    if (authorityAge < 0 || authorityAge >= 60_000) {
      throw enrollmentError('CONTROL_PLANE_POLICY_AUTHORITY_STALE', 'Chưa xác minh facade contract hiện hành của Ubuntu.');
    }
    if (authority.exec_enabled !== true || authority.exec_binding_count < 1) {
      throw enrollmentError('CONTROL_PLANE_EXEC_NOT_ADMITTED', 'Ubuntu chưa bật quyền chạy lệnh cho binding này.');
    }
    const native = executionMode !== 'isolated';
    // The pinned ProcessContainer capability probe only inspects OS support.
    // It starts no workspace program or Windows Sandbox VM.
    let sandbox = runtimeMode === 'local'
      ? Object.freeze({ state: 'not_required', backend: 'host_user', reason: 'OPERATOR_LOCAL_EXECUTION' })
      : await this.inspectMxcSandbox({ workspaceRoot, probeSandbox: native ? true : probeSandbox,
        backend: native ? 'process_container' : 'auto', capabilityOnly: native });
    if (runtimeMode === 'sandboxed' && (sandbox.state === 'unavailable' || (probeSandbox && sandbox.state !== 'available'))) {
      throw enrollmentError(
        sandbox.reason || 'SANDBOX_UNAVAILABLE',
        'Backend chạy lệnh chưa được xác minh; exec policy chưa được cài.'
      );
    }
    if (runtimeMode === 'sandboxed' && native && (sandbox.state !== 'available' || sandbox.backend !== 'process_container'
      || sandbox.capability_verified !== true)) {
      throw enrollmentError('WINDOWS_NATIVE_RUNNER_UNAVAILABLE', 'ProcessContainer chưa xác minh capability; quyền native chưa được cài.');
    }
    if (runtimeMode === 'sandboxed' && !native && probeSandbox && sandbox.backend !== 'windows_sandbox') {
      throw enrollmentError('WINDOWS_SANDBOX_REQUIRED', 'Chế độ cách ly cần backend Windows Sandbox đã xác minh.');
    }
    if (runtimeMode === 'sandboxed' && !native && !probeSandbox) {
      const windowsSandboxExecutable = path.join(
        String(this.environment.SystemRoot || this.environment.WINDIR || 'C:\\Windows'),
        'System32',
        'WindowsSandbox.exe'
      );
      if (process.platform !== 'win32' || this.experimentalWindowsSandbox !== true
        || !fs.existsSync(windowsSandboxExecutable)) {
        throw enrollmentError('WINDOWS_SANDBOX_REQUIRED', 'Windows Sandbox chưa được cài để chạy lệnh cách ly.');
      }
      const resourcesRoot = typeof this.paths.resourcesRoot === 'function'
        ? this.paths.resourcesRoot()
        : path.join(path.dirname(this.paths.executablePath()), 'resources', 'resources');
      const candidate = verifyMxcWindowsSandboxCandidate(resourcesRoot);
      try {
        if (!fs.statSync(this.paths.portablePython()).isFile()
          || !fs.statSync(path.join(resourcesRoot, 'coding-tools-mcp')).isDirectory()) throw new Error('missing');
      } catch {
        throw enrollmentError('NESTED_PROCESS_PROBE_RUNTIME_MISSING', 'Runtime chạy lệnh cách ly chưa sẵn sàng.');
      }
      if (!['not_checked', 'available'].includes(sandbox.state) || sandbox.backend !== 'windows_sandbox') {
        throw enrollmentError('WINDOWS_SANDBOX_REQUIRED', 'Backend Windows Sandbox chưa được xác minh.');
      }
      sandbox = Object.freeze({
        state: 'not_checked', backend: 'windows_sandbox', reason: 'SANDBOX_PROBE_REQUIRED',
        binary_sha256: candidate.hashes['wxc-exec.exe'],
        source_commit: candidate.source_commit,
        release: `microsoft-mxc-source-${MXC_WSB_SOURCE_COMMIT.slice(0, 7)}-0.10.0-alpha-experimental`
      });
    }
    const runtime = [
      '--project-root', this.agentProjectRoot,
      '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ];
    const installArgs = [
      ...shared,
      '--owner-id', authority.owner_id,
      '--facade-schema-version', String(authority.facade_contract.schema_version),
      '--facade-profile', authority.facade_contract.profile,
      '--facade-sha256', authority.facade_contract.sha256,
      ...EXEC_ARGV_PREFIXES.flatMap((prefix) => ['--allowed-argv-prefix', JSON.stringify(prefix)]),
      '--execution-mode', selection.execution_mode,
      ...selection.native_argv_prefixes.flatMap((prefix) => ['--native-argv-prefix', JSON.stringify(prefix)]),
      '--max-timeout-ms', String(EXEC_POLICY_LIMITS.max_timeout_ms),
      '--max-output-bytes', String(EXEC_POLICY_LIMITS.max_output_bytes),
      '--confirm-install',
      ...(replaceExisting ? ['--replace'] : []),
      ...runtime
    ];
    const install = await this.runPackagedNodeAgent('install-exec-policy', installArgs);
    const installed = parseExecPolicyInstallResult(install?.stdout, normalizedWorkspaceId, normalizedWorkspaceGeneration, selection);
    const observed = await this.inspectLocalExecPolicy({
      workspaceId: normalizedWorkspaceId, workspaceGeneration: normalizedWorkspaceGeneration
    });
    if (observed.state !== 'enabled'
      || observed.workspace_id !== normalizedWorkspaceId
      || observed.workspace_generation !== normalizedWorkspaceGeneration
      || observed.policy_sha256 !== installed.policy_sha256
      || observed.allowed_argv_prefixes_sha256 !== EXEC_PREFIXES_SHA256
      || observed.execution_mode !== selection.execution_mode
      || JSON.stringify(observed.native_argv_prefixes) !== JSON.stringify(selection.native_argv_prefixes)) {
      throw enrollmentError('CONTROL_PLANE_EXEC_POLICY_OBSERVATION_MISMATCH', 'Exec policy sau cài không khớp workspace, generation hoặc allowlist.');
    }
    return Object.freeze({ ...installed, sandbox });
  }

  async inspectStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration } = {}) {
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
    const target = workspaceId == null && workspaceGeneration == null ? [] : [
      '--workspace-id', centralWorkspaceId(workspaceId),
      '--workspace-generation', centralWorkspaceGeneration(workspaceGeneration)
    ];
    const observe = async (kind, command) => {
      let result;
      try {
        result = await this.runner(python, [
          '-I', agent, command, ...target,
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
      const policy = parseStandingFilePolicyObservation(result?.stdout, kind);
      if (target.length && policy.state === 'enabled'
        && (policy.workspace_id !== workspaceId || policy.workspace_generation !== workspaceGeneration)) {
        throw enrollmentError('CONTROL_PLANE_FILE_POLICY_TARGET_MISMATCH', 'Policy file chưa khớp thư mục đã chọn.');
      }
      return policy;
    };
    const [fileRead, approvedPatch] = await Promise.all([
      observe('file_read', 'inspect-file-read-policy'),
      observe('approved_patch', 'inspect-approved-patch-policy')
    ]);
    // Reuse one authenticated observation when both exact file policies
    // belong to the same registered generation. Installed/enabled alone does
    // not prove that their pinned facade still matches the current server.
    const authorities = new Map();
    const current = async (policy, allowWrite = false) => {
      if (policy.state !== 'enabled') return policy;
      const key = `${policy.workspace_id}:${policy.workspace_generation}`;
      try {
        if (!authorities.has(key)) authorities.set(key, this.inspectCurrentPolicyAuthority(policy));
        const authority = await authorities.get(key);
        if (allowWrite && authority.standing_write_enabled !== true) {
          throw enrollmentError('CONTROL_PLANE_PATCH_POLICY_NOT_ADMITTED', 'Ubuntu chưa bật quyền sửa file cho connector này.');
        }
        return Object.freeze({ ...policy, current_facade_contract: authority.facade_contract,
          authority_observed_at_ms: authority.observed_at_ms });
      } catch (error) {
        return Object.freeze({ ...policy, current_facade_contract: null, authority_observed_at_ms: null,
          reason: String(error?.code || 'CONTROL_PLANE_POLICY_AUTHORITY_UNAVAILABLE') });
      }
    };
    const [currentRead, currentPatch] = await Promise.all([current(fileRead), current(approvedPatch, true)]);
    return Object.freeze({ file_read: currentRead, approved_patch: currentPatch });
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

  registeredWorkspaceRoot({ workspaceId, workspaceGeneration } = {}) {
    return registeredWorkspacePath(this.paths.controlPlaneWorkspaceRegistryFile(),
      centralWorkspaceId(workspaceId), centralWorkspaceGeneration(workspaceGeneration));
  }

  // Ensure-binding: the node agent returns the binding created at
  // registration. confirmActivate is only the local folder-pick
  // confirmation; there is no pilot decision or expiry in this receipt.
  async activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate = false } = {}) {
    if (this.paths.runtimeMode() !== 'packaged') {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED', 'Kích hoạt thư mục chỉ chạy từ ứng dụng đóng gói đã xác minh.');
    }
    if (confirmActivate !== true) {
      throw enrollmentError('CONTROL_PLANE_WORKSPACE_ACTIVATION_CONFIRMATION_REQUIRED', 'Chủ máy cần xác nhận thư mục trước khi kích hoạt.');
    }
    const id = centralWorkspaceId(workspaceId);
    const generation = centralWorkspaceGeneration(workspaceGeneration);
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    const workspacePath = registeredWorkspacePath(registry, id, generation);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    for (const file of [python, agent]) {
      try { if (!fs.statSync(file).isFile()) throw new Error('missing'); }
      catch { throw enrollmentError('CONTROL_PLANE_WORKSPACE_RUNTIME_MISSING', 'Node agent đóng gói chưa sẵn sàng.'); }
    }
    const result = await this.runner(python, [
      '-I', agent, 'activate-workspace',
      '--config', this.paths.controlPlaneNodeConfigFile(),
      '--workspace-registry', registry,
      '--workspace-id', id, '--workspace-generation', generation, '--confirm-activate',
      '--project-root', this.agentProjectRoot, '--node', this.paths.executablePath(),
      '--runtime-mode', 'packaged'
    ], {
      cwd: this.agentProjectRoot, env: safeEnrollmentEnvironment(this.environment), timeoutMs: ENROLLMENT_TIMEOUT_MS
    });
    const receipt = parseWorkspaceActivationResult(result?.stdout, id, generation);
    // This canonical path is local display data; it never crosses the node API.
    assertSelectedWorkspaceRegistration(registry, workspacePath, id, generation);
    return Object.freeze({ ...receipt, workspace_path: workspacePath });
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
    return Object.freeze(parseWorkspaceListResult(result?.stdout).map((workspace) => Object.freeze({
      ...workspace,
      workspace_path: registeredWorkspacePath(registry, workspace.workspace_id, workspace.workspace_generation)
    })));
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
    const normalizedWorkspaceId = centralWorkspaceId(workspaceId);
    const normalizedWorkspaceGeneration = centralWorkspaceGeneration(workspaceGeneration);
    // An existing row already identifies one node-private root. Resolve that
    // exact registration locally instead of making the owner pick it again;
    // an explicitly supplied path still has to match the selected row.
    const registry = this.paths.controlPlaneWorkspaceRegistryFile();
    const canonicalPath = workspacePath === undefined
      ? registeredWorkspacePath(registry, normalizedWorkspaceId, normalizedWorkspaceGeneration)
      : canonicalWorkspacePath(workspacePath);
    assertSelectedWorkspaceRegistration(
      registry, canonicalPath,
      normalizedWorkspaceId, normalizedWorkspaceGeneration
    );
    const displayName = workspaceDisplayName(canonicalPath);
    const capabilities = normalizeWorkspaceCapabilities(requestedCapabilities);
    const python = this.paths.portablePython();
    const agent = this.paths.controlPlaneNodeAgent();
    const config = this.paths.controlPlaneNodeConfigFile();
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
  parseMxcSandboxProbe,
  parseMxcChildProcessProbe,
  parseMxcWindowsSandboxChildProcessProbe,
  verifyMxcWindowsSandboxCandidate,
  parseStandingFilePolicyInstallResult,
  parseStandingFilePolicyObservation,
  parseWorkspaceRegistrationResult,
  parseWorkspaceActivationResult,
  parseWorkspaceListResult,
  parseWorkspaceRetirementResult,
  parseWorkspaceReplacementResult,
  ControlPlaneEnrollmentService
};
