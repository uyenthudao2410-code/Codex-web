"use strict";

// A bounded file read is deliberately not an extension of the compact
// workspace-metadata bridge.  It has its own local policy, actor identity and
// receipt contract so an old metadata worker can never turn into arbitrary
// workspace access merely by accepting more arguments.

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');

const POLICY_SCHEMA_VERSION = 3;
const EXACT_POLICY_SCHEMA_VERSION = 2;
const LEGACY_POLICY_SCHEMA_VERSION = 1;
const STANDING_AUTHORITY_MODE = 'standing';
const BRIDGE_ENVELOPE_SCHEMA_VERSION = 1;
const BRIDGE_CLIENT_ID = 'electron-control-plane-file-read-bridge';
const BRIDGE_CLIENT_TYPE = 'electron';
const ACTION_TOOL_NAME = 'workspace_context';
const LOCAL_TOOL_NAME = 'read_file';
const OPERATION_KIND = 'control_plane_bounded_file_read';
const MAX_POLICY_BYTES = 16 * 1024;
const MAX_REGISTRY_BYTES = 64 * 1024;
const MAX_FILE_BYTES = 16 * 1024;
const MAX_FILE_LINES = 200;
const MAX_ALLOWED_PATHS = 32;
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const ACTION_IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/;
const SHA256_RE = /^[a-f0-9]{64}$/;

const SENSITIVE_DIRECTORY_NAMES = new Set([
  '.git', '.ssh', '.aws', '.gnupg', 'secret', 'secrets', 'credential', 'credentials'
]);
const SENSITIVE_BASENAMES = new Set([
  'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519', 'credential', 'credentials'
]);
const SENSITIVE_CONTENT_PATTERNS = Object.freeze([
  /-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----/,
  /\bsk-[A-Za-z0-9_-]{20,}\b/,
  /\bbearer\s+[A-Za-z0-9._~+/=:-]{20,}/i,
  /\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['"]?[A-Za-z0-9._~+/=:-]{16,}/im
]);

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

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function identifier(value, name, pattern = IDENTIFIER_RE, code = 'CONTROL_PLANE_FILE_READ_POLICY_INVALID') {
  const normalized = text(value);
  if (!pattern.test(normalized)) throw bridgeError(code, `${name} is invalid.`);
  return normalized;
}

function origin(value, code = 'CONTROL_PLANE_FILE_READ_POLICY_INVALID') {
  const candidate = text(value);
  let parsed;
  try { parsed = new URL(candidate); }
  catch { throw bridgeError(code, 'control-plane origin is invalid.'); }
  if (!['http:', 'https:'].includes(parsed.protocol)
    || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw bridgeError(code, 'control-plane origin must be a credential-free HTTP(S) origin.');
  }
  return parsed.origin;
}

function expiry(value, now, code) {
  const expiresAtMs = Number(value);
  if (!Number.isSafeInteger(expiresAtMs) || expiresAtMs <= now) {
    throw bridgeError(code, 'control-plane file-read authority is expired.');
  }
  return expiresAtMs;
}

function facadeContract(value, code = 'CONTROL_PLANE_FILE_READ_POLICY_INVALID') {
  if (!exactKeys(value, ['schema_version', 'profile', 'sha256'])) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  const schemaVersion = Number(value.schema_version);
  const profile = text(value.profile);
  const sha256 = text(value.sha256).toLowerCase();
  if (!Number.isSafeInteger(schemaVersion) || schemaVersion < 1 || schemaVersion > 1_000_000
    || !IDENTIFIER_RE.test(profile) || !SHA256_RE.test(sha256)) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  return Object.freeze({ schema_version: schemaVersion, profile, sha256 });
}

function relativePath(value, code = 'CONTROL_PLANE_FILE_READ_PATH_INVALID') {
  if (typeof value !== 'string') throw bridgeError(code, 'file path is invalid.');
  let bytes;
  try { bytes = Buffer.byteLength(value, 'utf8'); }
  catch { throw bridgeError(code, 'file path is invalid.'); }
  if (!value || bytes > 512 || value.startsWith('/') || value.includes('\\') || value.includes(':')
    || /[\u0000-\u001f\u007f]/.test(value)) {
    throw bridgeError(code, 'file path is invalid.');
  }
  const parts = value.split('/');
  if (parts.some((part) => !part || part === '.' || part === '..')) {
    throw bridgeError(code, 'file path is invalid.');
  }
  const lowered = parts.map((part) => part.toLowerCase());
  const basename = lowered[lowered.length - 1];
  if (lowered.some((part) => SENSITIVE_DIRECTORY_NAMES.has(part) || part.startsWith('.env'))
    || SENSITIVE_BASENAMES.has(basename)
    || ['.pem', '.key', '.p12', '.pfx'].some((extension) => basename.endsWith(extension))) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_SENSITIVE_PATH', 'file path is not permitted by the bounded read bridge.');
  }
  return value;
}

function boundedInteger(value, name, maximum, code) {
  if (!Number.isSafeInteger(value) || value < 1 || value > maximum) {
    throw bridgeError(code, `${name} is invalid.`);
  }
  return value;
}

function allowedPaths(value, code = 'CONTROL_PLANE_FILE_READ_POLICY_INVALID') {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_ALLOWED_PATHS) {
    throw bridgeError(code, 'allowed_relative_paths is invalid.');
  }
  const normalized = value.map((item) => relativePath(item, code));
  if (new Set(normalized).size !== normalized.length) {
    throw bridgeError(code, 'allowed_relative_paths must not contain duplicates.');
  }
  return Object.freeze([...normalized].sort());
}

function allowedPrefixes(value, code = 'CONTROL_PLANE_FILE_READ_POLICY_INVALID') {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_ALLOWED_PATHS) {
    throw bridgeError(code, 'allowed_relative_prefixes is invalid.');
  }
  const normalized = value.map((item) => item === '.' ? '.' : relativePath(item, code));
  if (new Set(normalized).size !== normalized.length || (normalized.includes('.') && normalized.length !== 1)) {
    throw bridgeError(code, 'allowed_relative_prefixes must be distinct and canonical.');
  }
  return Object.freeze([...normalized].sort());
}

function policyAllowsPath(policy, relative) {
  if (policy.schema_version === POLICY_SCHEMA_VERSION) {
    return policy.allowed_relative_prefixes.some((prefix) =>
      prefix === '.' || relative === prefix || relative.startsWith(`${prefix}/`));
  }
  return policy.allowed_relative_paths.includes(relative);
}

function normalisePolicy(value, { now = Date.now() } = {}) {
  const schemaVersion = Number(value?.schema_version);
  const prefixes = schemaVersion === POLICY_SCHEMA_VERSION;
  const standing = prefixes || schemaVersion === EXACT_POLICY_SCHEMA_VERSION;
  const legacy = schemaVersion === LEGACY_POLICY_SCHEMA_VERSION;
  const expected = [
    'schema_version', 'enabled', 'server_origin', 'owner_id', 'device_id',
    'endpoint_id', 'workspace_id', 'workspace_generation', 'expires_at_ms',
    'facade_contract', prefixes ? 'allowed_relative_prefixes' : 'allowed_relative_paths', 'max_bytes', 'max_lines'
  ];
  if (standing) expected.push('authority_mode');
  if (!exactKeys(value, expected) || (!standing && !legacy)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_INVALID', 'control-plane file-read policy has an invalid schema.');
  }
  if (value.enabled !== true) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_DISABLED', 'control-plane file-read bridge is not locally enabled.');
  }
  const authorityMode = standing ? STANDING_AUTHORITY_MODE : 'expiring_legacy';
  if (standing && value.authority_mode !== STANDING_AUTHORITY_MODE) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_INVALID', 'standing file-read authority must declare its mode.');
  }
  const expiresAtMs = value.expires_at_ms;
  if (standing) {
    if (expiresAtMs !== null) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_INVALID', 'standing file-read authority must not carry an expiry.');
    }
  } else {
    expiry(expiresAtMs, now, 'CONTROL_PLANE_FILE_READ_POLICY_EXPIRED');
  }
  const normalised = {
    schema_version: schemaVersion,
    server_origin: origin(value.server_origin),
    owner_id: identifier(value.owner_id, 'owner_id'),
    device_id: identifier(value.device_id, 'device_id'),
    endpoint_id: identifier(value.endpoint_id, 'endpoint_id'),
    workspace_id: identifier(value.workspace_id, 'workspace_id'),
    workspace_generation: identifier(value.workspace_generation, 'workspace_generation'),
    expires_at_ms: expiresAtMs,
    facade_contract: facadeContract(value.facade_contract),
    ...(prefixes
      ? { allowed_relative_prefixes: allowedPrefixes(value.allowed_relative_prefixes) }
      : { allowed_relative_paths: allowedPaths(value.allowed_relative_paths) }),
    max_bytes: boundedInteger(value.max_bytes, 'max_bytes', MAX_FILE_BYTES, 'CONTROL_PLANE_FILE_READ_POLICY_INVALID'),
    max_lines: boundedInteger(value.max_lines, 'max_lines', MAX_FILE_LINES, 'CONTROL_PLANE_FILE_READ_POLICY_INVALID')
  };
  if (standing) normalised.authority_mode = authorityMode;
  return Object.freeze(normalised);
}

function loadFileReadBridgePolicy(paths, { now = Date.now() } = {}) {
  const policyFile = typeof paths?.controlPlaneFileReadPolicyFile === 'function'
    ? paths.controlPlaneFileReadPolicyFile()
    : '';
  if (!policyFile || !fs.existsSync(policyFile)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_MISSING', 'control-plane file-read policy is not installed.');
  }
  let raw;
  try {
    const stat = fs.statSync(policyFile);
    if (!stat.isFile() || stat.size <= 0 || stat.size > MAX_POLICY_BYTES) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_INVALID', 'control-plane file-read policy is invalid.');
    }
    raw = JSON.parse(fs.readFileSync(policyFile, 'utf8'));
  } catch (error) {
    if (error?.code?.startsWith('CONTROL_PLANE_FILE_READ_')) throw error;
    throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_INVALID', 'control-plane file-read policy cannot be parsed.');
  }
  const policy = normalisePolicy(raw, { now });
  return Object.freeze({ ...policy, policy_sha256: digest(policy) });
}

function resolveRegisteredWorkspaceRoot(paths, policy) {
  const registryFile = typeof paths?.controlPlaneWorkspaceRegistryFile === 'function'
    ? paths.controlPlaneWorkspaceRegistryFile()
    : '';
  try {
    const stat = fs.statSync(registryFile);
    if (!registryFile || !stat.isFile() || stat.size <= 0 || stat.size > MAX_REGISTRY_BYTES) {
      throw new Error('invalid');
    }
    const registry = JSON.parse(fs.readFileSync(registryFile, 'utf8'));
    if (!registry || typeof registry !== 'object' || Array.isArray(registry)
      || registry.schema_version !== 1 || !Array.isArray(registry.entries)) {
      throw new Error('invalid');
    }
    const matches = registry.entries.filter((entry) => entry && typeof entry === 'object'
      && entry.workspace_id === policy.workspace_id
      && entry.workspace_generation === policy.workspace_generation);
    if (matches.length !== 1) throw new Error('invalid');
    const entry = matches[0];
    if (!exactKeys(entry, [
      'workspace_id', 'workspace_generation', 'canonical_path', 'display_name', 'capabilities', 'created_at_ms'
    ]) || !entry.capabilities || typeof entry.capabilities !== 'object' || Array.isArray(entry.capabilities)
      || entry.capabilities.read !== true || typeof entry.capabilities.write !== 'boolean'
      || typeof entry.capabilities.exec !== 'boolean') {
      throw new Error('invalid');
    }
    const root = entry.canonical_path;
    if (typeof root !== 'string' || !root || !path.isAbsolute(root)) {
      throw new Error('invalid');
    }
    const declared = path.resolve(root);
    const real = fs.realpathSync.native(root);
    const pathKey = (value) => {
      const normalized = path.normalize(path.resolve(value));
      return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
    };
    // The root must still exist and remain the exact canonical directory that
    // was selected locally. Never follow a symlink/reparse-point replacement
    // into a new target just because its opaque ID was once valid.
    if (pathKey(real) !== pathKey(declared) || !fs.statSync(real).isDirectory()) {
      throw new Error('invalid');
    }
    return real;
  } catch {
    throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'control-plane file-read target is not a current local workspace registration.');
  }
}

function resolveDirectRegisteredFile(workspaceRoot, relative) {
  if (typeof workspaceRoot !== 'string' || !path.isAbsolute(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace is invalid.');
  }
  const filePath = relativePath(relative, 'CONTROL_PLANE_FILE_READ_PATH_DENIED');
  let root;
  try { root = fs.realpathSync.native(workspaceRoot); }
  catch { throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace is unavailable.'); }
  const pathKey = (value) => {
    const normalized = path.normalize(path.resolve(value));
    return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
  };
  if (pathKey(root) !== pathKey(workspaceRoot) || !fs.statSync(root).isDirectory()) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace has changed.');
  }
  const target = path.resolve(root, ...filePath.split('/'));
  if (!pathKey(target).startsWith(`${pathKey(root)}${path.sep}`)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_PATH_DENIED', 'file path escapes the registered workspace.');
  }
  const parts = filePath.split('/');
  let cursor = root;
  for (const [index, part] of parts.entries()) {
    cursor = path.join(cursor, part);
    let stat;
    let real;
    try {
      stat = fs.lstatSync(cursor);
      real = fs.realpathSync.native(cursor);
    } catch {
      throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_MISSING', 'file-read target is unavailable.');
    }
    if (stat.isSymbolicLink() || pathKey(real) !== pathKey(cursor)) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_REPARSE_DENIED', 'file-read path contains a reparse point.');
    }
    const final = index === parts.length - 1;
    if (final ? !stat.isFile() : !stat.isDirectory()) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_INVALID', 'file-read path is not a direct regular file.');
    }
  }
  return target;
}

function admitFileReadBridgeRequest(policy, request, { now = Date.now() } = {}) {
  const expected = [
    'server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id',
    'workspace_generation', 'context_id', 'binding_id', 'action_id', 'attempt_id',
    'tool_name', 'operation', 'path', 'start_line', 'max_lines', 'max_bytes',
    'expires_at_ms', 'facade_contract'
  ];
  if (!exactKeys(request, expected)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_REQUEST_INVALID', 'control-plane file-read request has an invalid schema.');
  }
  const candidate = {
    server_origin: origin(request.server_origin, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    owner_id: identifier(request.owner_id, 'owner_id', IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    device_id: identifier(request.device_id, 'device_id', IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    endpoint_id: identifier(request.endpoint_id, 'endpoint_id', IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    workspace_id: identifier(request.workspace_id, 'workspace_id', IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    workspace_generation: identifier(request.workspace_generation, 'workspace_generation', IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    context_id: identifier(request.context_id, 'context_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    binding_id: identifier(request.binding_id, 'binding_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    action_id: identifier(request.action_id, 'action_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    attempt_id: identifier(request.attempt_id, 'attempt_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    tool_name: request.tool_name,
    operation: request.operation,
    path: relativePath(request.path, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    start_line: boundedInteger(request.start_line, 'start_line', 1_000_000, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    max_lines: boundedInteger(request.max_lines, 'max_lines', MAX_FILE_LINES, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    max_bytes: boundedInteger(request.max_bytes, 'max_bytes', MAX_FILE_BYTES, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'),
    expires_at_ms: expiry(request.expires_at_ms, now, 'CONTROL_PLANE_FILE_READ_REQUEST_EXPIRED'),
    facade_contract: facadeContract(request.facade_contract, 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID')
  };
  if (candidate.tool_name !== ACTION_TOOL_NAME || candidate.operation !== 'read_file') {
    throw bridgeError('CONTROL_PLANE_FILE_READ_TOOL_DENIED', 'control-plane file-read bridge only admits its bounded read_file action.');
  }
  if (policy.expires_at_ms != null && candidate.expires_at_ms > policy.expires_at_ms) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_POLICY_EXPIRED', 'control-plane action outlives the local file-read policy.');
  }
  for (const field of ['server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id', 'workspace_generation']) {
    if (candidate[field] !== policy[field]) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_MISMATCH', `control-plane file-read ${field} does not match local policy.`);
    }
  }
  if (canonicalJson(candidate.facade_contract) !== canonicalJson(policy.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_CONTRACT_MISMATCH', 'control-plane facade contract does not match local policy.');
  }
  if (!policyAllowsPath(policy, candidate.path)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_PATH_DENIED', 'file path is not explicitly admitted by the local policy.');
  }
  if (candidate.max_bytes > policy.max_bytes || candidate.max_lines > policy.max_lines) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_LIMIT_DENIED', 'file-read limits exceed the local policy.');
  }
  return Object.freeze({
    schema_version: BRIDGE_ENVELOPE_SCHEMA_VERSION,
    operation_kind: OPERATION_KIND,
    ...candidate,
    policy_sha256: policy.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE }
  });
}

function fileContentDigest(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function containsSensitiveFileContent(value) {
  return typeof value === 'string' && SENSITIVE_CONTENT_PATTERNS.some((pattern) => pattern.test(value));
}

function outputLineCount(content) {
  // This mirrors Python's ``str.splitlines()`` for the text shape returned by
  // the local read_file tool.  In particular, a trailing newline terminates a
  // line rather than adding a phantom empty line to the count.
  if (!content) return 0;
  const breaks = content.match(/\r\n|[\n\v\f\r\x1c-\x1e\x85\u2028\u2029]/g);
  const count = breaks ? breaks.length : 0;
  return /(?:\r\n|[\n\v\f\r\x1c-\x1e\x85\u2028\u2029])$/.test(content) ? count : count + 1;
}

function normaliseFileReadResult(value, admission) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID', 'control-plane file-read result is invalid.');
  }
  const identity = value.runtime_identity;
  const actor = value.actor;
  const file = value.file;
  if (!identity || typeof identity !== 'object' || Array.isArray(identity)
    || !file || typeof file !== 'object' || Array.isArray(file)
    || value.schema_version !== 1 || value.operation_kind !== OPERATION_KIND
    || value.file_accessed !== true || value.action_id !== admission.action_id || value.attempt_id !== admission.attempt_id
    || actor?.client_id !== BRIDGE_CLIENT_ID || actor?.client_type !== BRIDGE_CLIENT_TYPE
    || !/^cp_fr_[a-f0-9]{48}$/.test(text(value.local_handle))
    || !SHA256_RE.test(text(value.policy_sha256).toLowerCase())
    // Recovery Host carries the local policy digest in its admitted request.
    // The descriptor-hiding CJS adapter deliberately receives the narrower
    // Python request without that field, so retain compatibility there while
    // still fencing a direct Recovery Host result at the first boundary.
    || (typeof admission?.policy_sha256 === 'string'
      && text(value.policy_sha256).toLowerCase() !== admission.policy_sha256.toLowerCase())
    || canonicalJson(facadeContract(value.facade_contract, 'CONTROL_PLANE_FILE_READ_RESULT_CONTRACT_INVALID')) !== canonicalJson(admission.facade_contract)
    || !SHA256_RE.test(text(value.response_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID', 'control-plane file-read result is invalid.');
  }
  for (const field of ['activation_epoch_id', 'process_instance_id', 'server_instance_id']) {
    if (!IDENTIFIER_RE.test(text(identity[field]))) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_IDENTITY_INVALID', 'runtime identity is invalid.');
    }
  }
  if (!SHA256_RE.test(text(identity.tool_contract_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_IDENTITY_INVALID', 'runtime identity is invalid.');
  }
  if (!exactKeys(file, [
    'path', 'content', 'content_sha256', 'encoding', 'start_line', 'end_line',
    'total_lines', 'total_bytes', 'bytes_read', 'truncated', 'next_start_line'
  ])) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID', 'file projection is invalid.');
  }
  const filePath = relativePath(file.path, 'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID');
  const content = file.content;
  if (filePath !== admission.path || typeof content !== 'string' || file.encoding !== 'utf-8'
    || Buffer.byteLength(content, 'utf8') > admission.max_bytes
    || text(file.content_sha256).toLowerCase() !== fileContentDigest(content)
    || containsSensitiveFileContent(content)) {
    throw bridgeError(
      containsSensitiveFileContent(content) ? 'CONTROL_PLANE_FILE_READ_SENSITIVE_CONTENT' : 'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID',
      'file projection is invalid.'
    );
  }
  const integerFields = ['start_line', 'end_line', 'total_lines', 'total_bytes', 'bytes_read'];
  if (integerFields.some((field) => !Number.isSafeInteger(file[field]) || file[field] < 0)
    || file.start_line !== admission.start_line
    || file.bytes_read !== Buffer.byteLength(content, 'utf8')
    || file.bytes_read > admission.max_bytes
    || file.total_bytes < file.bytes_read
    || file.total_lines < file.end_line
    || typeof file.truncated !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID', 'file projection is invalid.');
  }
  const contentLines = outputLineCount(content);
  const requestedEnd = Math.min(file.total_lines, admission.start_line + admission.max_lines - 1);
  const outOfRange = file.total_lines < admission.start_line;
  if (contentLines > admission.max_lines
    || (!outOfRange && (file.end_line < admission.start_line || file.end_line > requestedEnd
      || contentLines > file.end_line - admission.start_line + 1))
    || (outOfRange && (file.end_line !== file.total_lines || content !== '' || contentLines !== 0))) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID', 'file projection has invalid line bounds.');
  }
  const hasRemainingLines = file.end_line < file.total_lines;
  if ((file.truncated && hasRemainingLines && file.next_start_line !== file.end_line + 1)
    || ((!file.truncated || !hasRemainingLines) && file.next_start_line !== null)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID', 'file projection continuation is invalid.');
  }
  const safeFile = {
    path: filePath,
    content,
    content_sha256: text(file.content_sha256).toLowerCase(),
    encoding: 'utf-8',
    start_line: file.start_line,
    end_line: file.end_line,
    total_lines: file.total_lines,
    total_bytes: file.total_bytes,
    bytes_read: file.bytes_read,
    truncated: file.truncated,
    next_start_line: file.next_start_line
  };
  // The MCP response can contain presentation metadata and future fields. Bind
  // the receipt only to the exact allowlisted projection that may leave the
  // Windows node, never to the raw structured response.
  if (text(value.response_sha256).toLowerCase() !== digest(safeFile)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_RESULT_DIGEST_INVALID', 'file projection integrity is invalid.');
  }
  return Object.freeze({
    schema_version: 1,
    operation_kind: OPERATION_KIND,
    file_accessed: true,
    local_handle: text(value.local_handle),
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    policy_sha256: text(value.policy_sha256).toLowerCase(),
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    runtime_identity: {
      activation_epoch_id: text(identity.activation_epoch_id),
      process_instance_id: text(identity.process_instance_id),
      server_instance_id: text(identity.server_instance_id),
      tool_contract_sha256: text(identity.tool_contract_sha256).toLowerCase()
    },
    facade_contract: facadeContract(value.facade_contract, 'CONTROL_PLANE_FILE_READ_RESULT_CONTRACT_INVALID'),
    file: safeFile,
    response_sha256: digest(safeFile)
  });
}

module.exports = {
  POLICY_SCHEMA_VERSION,
  EXACT_POLICY_SCHEMA_VERSION,
  LEGACY_POLICY_SCHEMA_VERSION,
  STANDING_AUTHORITY_MODE,
  BRIDGE_ENVELOPE_SCHEMA_VERSION,
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  ACTION_TOOL_NAME,
  LOCAL_TOOL_NAME,
  OPERATION_KIND,
  MAX_FILE_BYTES,
  MAX_FILE_LINES,
  bridgeError,
  canonicalJson,
  digest,
  facadeContract,
  relativePath,
  normalisePolicy,
  policyAllowsPath,
  loadFileReadBridgePolicy,
  resolveRegisteredWorkspaceRoot,
  resolveDirectRegisteredFile,
  admitFileReadBridgeRequest,
  fileContentDigest,
  containsSensitiveFileContent,
  outputLineCount,
  normaliseFileReadResult
};
