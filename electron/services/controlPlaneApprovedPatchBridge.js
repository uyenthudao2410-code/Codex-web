"use strict";

// The approved-patch lane is deliberately independent from both compact
// workspace metadata and bounded file reads.  A policy that permits viewing a
// file must never become permission to change it merely because the two lanes
// have the same central owner/root.  This module contains only local policy,
// exact-write admission, and receipt shaping; it never opens a socket to the
// central service and it never writes the workspace directly.

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const { URL } = require('node:url');

const POLICY_SCHEMA_VERSION = 2;
const LEGACY_POLICY_SCHEMA_VERSION = 1;
const STANDING_AUTHORITY_MODE = 'standing';
const BRIDGE_ENVELOPE_SCHEMA_VERSION = 1;
const BRIDGE_CLIENT_ID = 'electron-control-plane-approved-patch-bridge';
const BRIDGE_CLIENT_TYPE = 'electron';
const ACTION_TOOL_NAME = 'agent_workflow';
const LOCAL_TOOL_NAME = 'apply_patch';
const OPERATION_KIND = 'control_plane_approved_patch';
const VALIDATION_PROFILE = 'targeted';
// Applying an owner-approved exact patch proves a local effect, not that the
// local Coding Tools workflow has passed its independent semantic acceptance
// gate. Keep that distinction explicit across the bridge boundary. A future
// local owner/controller may accept or reject the RUN only after separately
// admitted proof; this bridge must never self-accept it.
const LOCAL_SEMANTIC_ACCEPTANCE_PENDING = 'pending';
const MAX_POLICY_BYTES = 16 * 1024;
const MAX_REGISTRY_BYTES = 64 * 1024;
const MAX_PATCH_BYTES = 32 * 1024;
// The central envelope is compressed and therefore needs an independent
// decompressed cap.  This v1 lane intentionally stays much smaller than the
// local general patch parser so a tiny remote payload cannot be a memory bomb.
const MAX_EXACT_FILE_BYTES = 256 * 1024;
const MAX_ALLOWED_PATHS = 32;
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const ACTION_IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/;
const SHA256_RE = /^[a-f0-9]{64}$/;
// RUN and WAVE ids are generated locally by the canonical orchestration
// ledger. They are deliberately validated before becoming part of an opaque
// bridge handle; no caller-selected PID or process id is a control-plane
// authority token.
const ORCHESTRATION_IDENTIFIER_RE = /^[a-f0-9]{32}$/;
const TASK_ID_RE = /^task_[a-f0-9]{32}$/;
const BASE64_RE = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;

const SENSITIVE_DIRECTORY_NAMES = new Set([
  '.git', '.ssh', '.aws', '.gnupg', 'secret', 'secrets', 'credential', 'credentials'
]);
const SENSITIVE_BASENAMES = new Set([
  'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519', 'credential', 'credentials'
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

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function identifier(value, name, pattern = IDENTIFIER_RE, code = 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID') {
  const normalized = text(value);
  if (!pattern.test(normalized)) throw bridgeError(code, `${name} is invalid.`);
  return normalized;
}

function origin(value, code = 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID') {
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
    throw bridgeError(code, 'control-plane approved-patch authority is expired.');
  }
  return expiresAtMs;
}

function facadeContract(value, code = 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID') {
  if (!exactKeys(value, ['schema_version', 'profile', 'sha256'])) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  const schemaVersion = Number(value.schema_version);
  const profile = text(value.profile);
  const contractSha256 = text(value.sha256).toLowerCase();
  if (!Number.isSafeInteger(schemaVersion) || schemaVersion < 1 || schemaVersion > 1_000_000
    || !IDENTIFIER_RE.test(profile) || !SHA256_RE.test(contractSha256)) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  return Object.freeze({ schema_version: schemaVersion, profile, sha256: contractSha256 });
}

function relativePath(value, code = 'CONTROL_PLANE_APPROVED_PATCH_PATH_INVALID') {
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
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_SENSITIVE_PATH', 'file path is not permitted by the approved-patch bridge.');
  }
  return value;
}

function boundedInteger(value, name, maximum, code) {
  if (!Number.isSafeInteger(value) || value < 1 || value > maximum) {
    throw bridgeError(code, `${name} is invalid.`);
  }
  return value;
}

function allowedPaths(value, code = 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID') {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_ALLOWED_PATHS) {
    throw bridgeError(code, 'allowed_relative_paths is invalid.');
  }
  const normalized = value.map((item) => relativePath(item, code));
  if (new Set(normalized).size !== normalized.length) {
    throw bridgeError(code, 'allowed_relative_paths must not contain duplicates.');
  }
  return Object.freeze([...normalized].sort());
}

function normalisePolicy(value, { now = Date.now() } = {}) {
  const schemaVersion = Number(value?.schema_version);
  const standing = schemaVersion === POLICY_SCHEMA_VERSION;
  const legacy = schemaVersion === LEGACY_POLICY_SCHEMA_VERSION;
  const expected = [
    'schema_version', 'enabled', 'server_origin', 'owner_id', 'device_id',
    'endpoint_id', 'workspace_id', 'workspace_generation', 'expires_at_ms',
    'facade_contract', 'allowed_relative_paths', 'max_patch_bytes',
    'max_file_bytes', 'validation_profile'
  ];
  if (standing) expected.push('authority_mode');
  if (!exactKeys(value, expected) || (!standing && !legacy)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'control-plane approved-patch policy has an invalid schema.');
  }
  if (value.enabled !== true) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_DISABLED', 'control-plane approved-patch bridge is not locally enabled.');
  }
  if (value.validation_profile !== VALIDATION_PROFILE) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'control-plane approved-patch validation profile is invalid.');
  }
  const authorityMode = standing ? STANDING_AUTHORITY_MODE : 'expiring_legacy';
  if (standing && value.authority_mode !== STANDING_AUTHORITY_MODE) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'standing approved-patch authority must declare its mode.');
  }
  const expiresAtMs = value.expires_at_ms;
  if (standing) {
    if (expiresAtMs !== null) {
      throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'standing approved-patch authority must not carry an expiry.');
    }
  } else {
    expiry(expiresAtMs, now, 'CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED');
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
    allowed_relative_paths: allowedPaths(value.allowed_relative_paths),
    max_patch_bytes: boundedInteger(value.max_patch_bytes, 'max_patch_bytes', MAX_PATCH_BYTES, 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID'),
    max_file_bytes: boundedInteger(value.max_file_bytes, 'max_file_bytes', MAX_EXACT_FILE_BYTES, 'CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID'),
    validation_profile: VALIDATION_PROFILE
  };
  if (standing) normalised.authority_mode = authorityMode;
  return Object.freeze(normalised);
}

function loadApprovedPatchBridgePolicy(paths, { now = Date.now() } = {}) {
  const policyFile = typeof paths?.controlPlaneApprovedPatchPolicyFile === 'function'
    ? paths.controlPlaneApprovedPatchPolicyFile()
    : '';
  if (!policyFile || !fs.existsSync(policyFile)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING', 'control-plane approved-patch policy is not installed.');
  }
  let raw;
  try {
    const stat = fs.statSync(policyFile);
    if (!stat.isFile() || stat.size <= 0 || stat.size > MAX_POLICY_BYTES) {
      throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'control-plane approved-patch policy is invalid.');
    }
    raw = JSON.parse(fs.readFileSync(policyFile, 'utf8'));
  } catch (error) {
    if (error?.code?.startsWith('CONTROL_PLANE_APPROVED_PATCH_')) throw error;
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID', 'control-plane approved-patch policy cannot be parsed.');
  }
  const policy = normalisePolicy(raw, { now });
  return Object.freeze({ ...policy, policy_sha256: digest(policy) });
}

function pathKey(value) {
  const normalized = path.normalize(path.resolve(value));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function resolveRegisteredWorkspaceRoot(paths, policy) {
  const registryFile = typeof paths?.controlPlaneWorkspaceRegistryFile === 'function'
    ? paths.controlPlaneWorkspaceRegistryFile()
    : '';
  try {
    if (!registryFile) throw new Error('invalid');
    const stat = fs.statSync(registryFile);
    if (!stat.isFile() || stat.size <= 0 || stat.size > MAX_REGISTRY_BYTES) throw new Error('invalid');
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
      || entry.capabilities.write !== true || typeof entry.capabilities.read !== 'boolean'
      || typeof entry.capabilities.exec !== 'boolean') {
      throw new Error('invalid');
    }
    const root = entry.canonical_path;
    if (typeof root !== 'string' || !root || !path.isAbsolute(root)) throw new Error('invalid');
    const declared = path.resolve(root);
    const real = fs.realpathSync.native(root);
    if (pathKey(real) !== pathKey(declared) || !fs.statSync(real).isDirectory()) throw new Error('invalid');
    return real;
  } catch {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_REGISTRY_REQUIRED', 'control-plane approved-patch target is not a current local writable workspace registration.');
  }
}

function exactApprovedPatchEnvelope(value, {
  expectedPath,
  expectedPreimageSha256,
  expectedPatchSha256,
  maxPatchBytes = MAX_PATCH_BYTES,
  maxFileBytes = MAX_EXACT_FILE_BYTES,
  code = 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'
} = {}) {
  if (typeof value !== 'string') throw bridgeError(code, 'approved patch envelope is invalid.');
  const expectedPathValue = relativePath(expectedPath, code);
  const preimage = text(expectedPreimageSha256).toLowerCase();
  const patchDigest = text(expectedPatchSha256).toLowerCase();
  if (!SHA256_RE.test(preimage) || !SHA256_RE.test(patchDigest)) {
    throw bridgeError(code, 'approved patch hashes are invalid.');
  }
  let encoded;
  try { encoded = Buffer.from(value, 'utf8'); }
  catch { throw bridgeError(code, 'approved patch envelope is invalid.'); }
  if (!encoded.length || encoded.length > maxPatchBytes || encoded.length > MAX_PATCH_BYTES
    || value.includes('\0') || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value)
    || sha256(encoded) !== patchDigest) {
    throw bridgeError(code, 'approved patch envelope is invalid.');
  }
  const normalized = value.replace(/\r\n/g, '\n');
  if (normalized.includes('\r')) throw bridgeError(code, 'approved patch envelope has ambiguous line framing.');
  const lines = normalized.split('\n');
  if (lines.length && lines[lines.length - 1] === '') lines.pop();
  if (lines.length < 5 || lines[0] !== '*** Begin Patch' || lines[lines.length - 1] !== '*** End Patch'
    || lines[1] !== `*** Write Exact File: ${expectedPathValue}` || !lines[2].startsWith('@@ ')) {
    throw bridgeError(code, 'approved patch envelope must contain one exact existing-file write.');
  }
  const metadata = {};
  for (const token of lines[2].slice(3).split(' ')) {
    const separator = token.indexOf('=');
    const key = separator > 0 ? token.slice(0, separator) : '';
    const metadataValue = separator > 0 ? token.slice(separator + 1).toLowerCase() : '';
    if (!key || !metadataValue || Object.prototype.hasOwnProperty.call(metadata, key)) {
      throw bridgeError(code, 'approved patch metadata is invalid.');
    }
    metadata[key] = metadataValue;
  }
  if (!exactKeys(metadata, ['encoding', 'preimage_sha256', 'postimage_sha256'])
    || metadata.encoding !== 'zlib-base64' || metadata.preimage_sha256 !== preimage
    || !SHA256_RE.test(metadata.postimage_sha256)) {
    throw bridgeError(code, 'approved patch metadata is invalid.');
  }
  const chunks = lines.slice(3, -1);
  if (!chunks.length || chunks.some((line) => !line.startsWith('+'))) {
    throw bridgeError(code, 'approved patch payload is invalid.');
  }
  const base64 = chunks.map((line) => line.slice(1)).join('');
  if (!base64 || !BASE64_RE.test(base64)) {
    throw bridgeError(code, 'approved patch payload is invalid.');
  }
  const compressed = Buffer.from(base64, 'base64');
  if (!compressed.length || compressed.toString('base64') !== base64) {
    throw bridgeError(code, 'approved patch payload is invalid.');
  }
  let postimage;
  try {
    postimage = zlib.inflateSync(compressed, { maxOutputLength: maxFileBytes + 1 });
  } catch {
    throw bridgeError(code, 'approved patch payload is invalid.');
  }
  if (postimage.length > maxFileBytes || sha256(postimage) !== metadata.postimage_sha256) {
    throw bridgeError(code, 'approved patch payload is invalid.');
  }
  // Coding Tools MCP accepts only exact UTF-8 content for Write Exact File.
  // Verify it here as well, before the request can cross into its local server.
  const decoded = postimage.toString('utf8');
  if (!Buffer.from(decoded, 'utf8').equals(postimage)) {
    throw bridgeError(code, 'approved patch payload is not valid UTF-8.');
  }
  return Object.freeze({
    postimage_sha256: metadata.postimage_sha256,
    postimage_bytes: postimage.length
  });
}

function admitApprovedPatchBridgeRequest(policy, request, { now = Date.now() } = {}) {
  const expected = [
    'server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id',
    'workspace_generation', 'context_id', 'binding_id', 'action_id', 'attempt_id',
    'task_id', 'writer_lease_generation',
    'tool_name', 'operation', 'permission_request_id', 'permission_digest',
    'intent_digest', 'path', 'preimage_sha256', 'patch_sha256', 'patch_envelope',
    'validation_profile', 'expires_at_ms', 'facade_contract'
  ];
  // Standing policy is a distinct local authority.  Keep the mode in the
  // sealed request so an owner-review action cannot be relayed through a
  // standing policy (or vice versa), while preserving the legacy owner-review
  // request shape for existing callers and fixtures.
  const standing = policy?.authority_mode === STANDING_AUTHORITY_MODE;
  if (standing) expected.push('authority_mode');
  if (!exactKeys(request, expected)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID', 'control-plane approved-patch request has an invalid schema.');
  }
  const candidate = {
    server_origin: origin(request.server_origin, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    owner_id: identifier(request.owner_id, 'owner_id', IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    device_id: identifier(request.device_id, 'device_id', IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    endpoint_id: identifier(request.endpoint_id, 'endpoint_id', IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    workspace_id: identifier(request.workspace_id, 'workspace_id', IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    workspace_generation: identifier(request.workspace_generation, 'workspace_generation', IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    context_id: identifier(request.context_id, 'context_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    binding_id: identifier(request.binding_id, 'binding_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    action_id: identifier(request.action_id, 'action_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    attempt_id: identifier(request.attempt_id, 'attempt_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    task_id: identifier(request.task_id, 'task_id', TASK_ID_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    writer_lease_generation: Number(request.writer_lease_generation),
    tool_name: request.tool_name,
    operation: request.operation,
    permission_request_id: identifier(request.permission_request_id, 'permission_request_id', ACTION_IDENTIFIER_RE, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    permission_digest: text(request.permission_digest).toLowerCase(),
    intent_digest: text(request.intent_digest).toLowerCase(),
    path: relativePath(request.path, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID'),
    preimage_sha256: text(request.preimage_sha256).toLowerCase(),
    patch_sha256: text(request.patch_sha256).toLowerCase(),
    patch_envelope: request.patch_envelope,
    validation_profile: request.validation_profile,
    expires_at_ms: expiry(request.expires_at_ms, now, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_EXPIRED'),
    facade_contract: facadeContract(request.facade_contract, 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID')
  };
  if (standing && request.authority_mode !== STANDING_AUTHORITY_MODE) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TOOL_DENIED', 'standing approved-patch requests must declare standing authority.');
  }
  if (!standing && Object.prototype.hasOwnProperty.call(request, 'authority_mode')) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TOOL_DENIED', 'owner-review approved-patch requests cannot declare standing authority.');
  }
  if (standing) candidate.authority_mode = STANDING_AUTHORITY_MODE;
  if (candidate.tool_name !== ACTION_TOOL_NAME || candidate.operation !== LOCAL_TOOL_NAME
    || candidate.validation_profile !== VALIDATION_PROFILE || !SHA256_RE.test(candidate.permission_digest)
    || !SHA256_RE.test(candidate.intent_digest) || !SHA256_RE.test(candidate.preimage_sha256)
    || !SHA256_RE.test(candidate.patch_sha256)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TOOL_DENIED', 'control-plane approved-patch bridge only admits an exact approved apply_patch action.');
  }
  if (!Number.isSafeInteger(candidate.writer_lease_generation)
    || candidate.writer_lease_generation < 1 || candidate.writer_lease_generation > 1_000_000_000) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID', 'writer lease generation is invalid.');
  }
  if (policy.expires_at_ms != null && candidate.expires_at_ms > policy.expires_at_ms) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED', 'control-plane action outlives the local approved-patch policy.');
  }
  for (const field of ['server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id', 'workspace_generation']) {
    if (candidate[field] !== policy[field]) {
      throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TARGET_MISMATCH', `control-plane approved-patch ${field} does not match local policy.`);
    }
  }
  if (canonicalJson(candidate.facade_contract) !== canonicalJson(policy.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH', 'control-plane facade contract does not match local policy.');
  }
  if (!policy.allowed_relative_paths.includes(candidate.path)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED', 'file path is not explicitly admitted by the local approved-patch policy.');
  }
  const patch = exactApprovedPatchEnvelope(candidate.patch_envelope, {
    expectedPath: candidate.path,
    expectedPreimageSha256: candidate.preimage_sha256,
    expectedPatchSha256: candidate.patch_sha256,
    maxPatchBytes: policy.max_patch_bytes,
    maxFileBytes: policy.max_file_bytes
  });
  return Object.freeze({
    schema_version: BRIDGE_ENVELOPE_SCHEMA_VERSION,
    operation_kind: OPERATION_KIND,
    ...candidate,
    postimage_sha256: patch.postimage_sha256,
    postimage_bytes: patch.postimage_bytes,
    max_file_bytes: policy.max_file_bytes,
    policy_sha256: policy.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE }
  });
}

function resolveExactRegisteredPatchTarget(workspaceRoot, admission) {
  if (typeof workspaceRoot !== 'string' || !path.isAbsolute(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH', 'control-plane approved-patch workspace is invalid.');
  }
  const root = fs.realpathSync.native(workspaceRoot);
  if (!fs.statSync(root).isDirectory() || pathKey(root) !== pathKey(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH', 'control-plane approved-patch workspace has changed.');
  }
  const relative = relativePath(admission?.path, 'CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED');
  const target = path.resolve(root, ...relative.split('/'));
  const rootPrefix = `${pathKey(root)}${path.sep}`;
  if (!pathKey(target).startsWith(rootPrefix)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED', 'approved patch path escapes the local workspace.');
  }
  let stat;
  let realTarget;
  try {
    stat = fs.lstatSync(target);
    realTarget = fs.realpathSync.native(target);
  } catch {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TARGET_MISSING', 'approved patch target does not exist locally.');
  }
  if (!stat.isFile() || stat.isSymbolicLink() || pathKey(realTarget) !== pathKey(target)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_REPARSE_DENIED', 'approved patch target is not a direct regular workspace file.');
  }
  let current;
  try { current = fs.readFileSync(realTarget); }
  catch { throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TARGET_MISSING', 'approved patch target cannot be read locally.'); }
  if (!Number.isSafeInteger(admission?.max_file_bytes) || current.length > admission.max_file_bytes) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_FILE_TOO_LARGE', 'approved patch target exceeds local policy size.');
  }
  if (sha256(current) !== admission.preimage_sha256) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH', 'approved patch preimage no longer matches the local file.');
  }
  const decoded = current.toString('utf8');
  if (!Buffer.from(decoded, 'utf8').equals(current)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TARGET_ENCODING_INVALID', 'approved patch target is not valid UTF-8.');
  }
  return Object.freeze({
    absolute_path: realTarget,
    preimage_sha256: admission.preimage_sha256,
    postimage_sha256: admission.postimage_sha256,
    postimage_bytes: admission.postimage_bytes
  });
}

function verifyExactRegisteredPatchPostimage(workspaceRoot, admission) {
  if (typeof workspaceRoot !== 'string' || !path.isAbsolute(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH', 'control-plane approved-patch workspace is invalid.');
  }
  const root = fs.realpathSync.native(workspaceRoot);
  if (!fs.statSync(root).isDirectory() || pathKey(root) !== pathKey(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH', 'control-plane approved-patch workspace has changed.');
  }
  const relative = relativePath(admission?.path, 'CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED');
  const target = path.resolve(root, ...relative.split('/'));
  const rootPrefix = `${pathKey(root)}${path.sep}`;
  if (!pathKey(target).startsWith(rootPrefix)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED', 'approved patch path escapes the local workspace.');
  }
  let stat;
  let realTarget;
  let current;
  try {
    stat = fs.lstatSync(target);
    realTarget = fs.realpathSync.native(target);
    current = fs.readFileSync(realTarget);
  } catch {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POSTIMAGE_MISSING', 'approved patch postimage is unavailable locally.');
  }
  if (!stat.isFile() || stat.isSymbolicLink() || pathKey(realTarget) !== pathKey(target)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_REPARSE_DENIED', 'approved patch target is not a direct regular workspace file.');
  }
  if (current.length !== admission.postimage_bytes || current.length > admission.max_file_bytes
    || sha256(current) !== admission.postimage_sha256) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_POSTIMAGE_MISMATCH', 'approved patch postimage does not match the local file.');
  }
  const decoded = current.toString('utf8');
  if (!Buffer.from(decoded, 'utf8').equals(current)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_TARGET_ENCODING_INVALID', 'approved patch target is not valid UTF-8.');
  }
  return Object.freeze({
    absolute_path: realTarget,
    postimage_sha256: admission.postimage_sha256,
    postimage_bytes: current.length
  });
}

function normaliseApprovedPatchWorkflowResult(value, {
  path: expectedPath,
  idempotency_key: expectedIdempotencyKey
} = {}) {
  // ``agent_workflow`` is the local write primitive for this bridge.  Its
  // response can contain a full local task/report, so this validator returns
  // only the canonical correlation needed to bind the external receipt.  The
  // raw patch, local root, task report, and idempotency key remain local.
  const invalid = () => {
    throw bridgeError(
      'CONTROL_PLANE_APPROVED_PATCH_MCP_RESULT_INVALID',
      'control-plane approved-patch local workflow result is invalid.'
    );
  };
  const expectedFile = relativePath(expectedPath, 'CONTROL_PLANE_APPROVED_PATCH_MCP_RESULT_INVALID');
  const expectedKey = text(expectedIdempotencyKey);
  if (!expectedKey || !value || typeof value !== 'object' || Array.isArray(value)) invalid();

  const record = value.idempotency;
  if (!record || typeof record !== 'object' || Array.isArray(record)
    || record.operation !== 'agent_workflow' || record.status !== 'completed'
    || text(record.idempotency_key) !== expectedKey) {
    invalid();
  }
  const runId = text(record.run_id).toLowerCase();
  const waveId = text(record.wave_id).toLowerCase();
  const requestHash = text(record.request_hash).toLowerCase();
  if (!ORCHESTRATION_IDENTIFIER_RE.test(runId)
    || !ORCHESTRATION_IDENTIFIER_RE.test(waveId)
    || !SHA256_RE.test(requestHash)
    || value.durable_idempotency !== true
    || value.workflow !== 'custom'
    || value.phase !== 'execute') {
    invalid();
  }

  const summary = record.summary;
  if (!summary || typeof summary !== 'object' || Array.isArray(summary)
    || summary.execution_ok !== true || summary.execution_status !== 'passed'
    || text(summary.run_id).toLowerCase() !== runId
    || text(summary.wave_id).toLowerCase() !== waveId
    || summary.orchestration_state !== 'ACCEPTING') {
    invalid();
  }

  if (value.deduplicated === true) {
    return Object.freeze({
      run_id: runId,
      wave_id: waveId,
      idempotency_request_hash: requestHash,
      local_semantic_acceptance: LOCAL_SEMANTIC_ACCEPTANCE_PENDING,
      deduplicated: true
    });
  }
  if (value.deduplicated != null && value.deduplicated !== false) invalid();

  const orchestration = value.orchestration;
  const execution = value.execution;
  if (!orchestration || typeof orchestration !== 'object' || Array.isArray(orchestration)
    || text(orchestration.run_id).toLowerCase() !== runId
    || text(orchestration.wave_id).toLowerCase() !== waveId
    || orchestration.orchestration_state !== 'ACCEPTING'
    || !execution || typeof execution !== 'object' || Array.isArray(execution)
    || execution.ok !== true || execution.status !== 'passed') {
    invalid();
  }
  const exactUpdate = (files) => Array.isArray(files)
    && files.length === 1
    && files[0]
    && typeof files[0] === 'object'
    && !Array.isArray(files[0])
    && files[0].path === expectedFile
    && files[0].operation === 'update';
  const patchResults = execution.patch_results;
  if (!exactUpdate(execution.affected_files)
    || !Array.isArray(patchResults) || patchResults.length !== 1
    || !patchResults[0] || typeof patchResults[0] !== 'object'
    || Array.isArray(patchResults[0])
    || patchResults[0].dry_run !== false || patchResults[0].clean !== true
    || !exactUpdate(patchResults[0].affected_files)) {
    invalid();
  }
  return Object.freeze({
    run_id: runId,
    wave_id: waveId,
    idempotency_request_hash: requestHash,
    local_semantic_acceptance: LOCAL_SEMANTIC_ACCEPTANCE_PENDING,
    deduplicated: false
  });
}

function normaliseApprovedPatchResult(value, admission) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID', 'control-plane approved-patch result is invalid.');
  }
  const identity = value.runtime_identity;
  const actor = value.actor;
  const file = value.file;
  if (!identity || typeof identity !== 'object' || Array.isArray(identity)
    || !file || typeof file !== 'object' || Array.isArray(file)
    || value.schema_version !== 1 || value.operation_kind !== OPERATION_KIND
    || value.patch_applied !== true || value.action_id !== admission.action_id || value.attempt_id !== admission.attempt_id
    || value.task_id !== admission.task_id
    || !Number.isSafeInteger(value.writer_lease_generation)
    || value.writer_lease_generation !== admission.writer_lease_generation
    || !ORCHESTRATION_IDENTIFIER_RE.test(text(value.run_id).toLowerCase())
    || !ORCHESTRATION_IDENTIFIER_RE.test(text(value.wave_id).toLowerCase())
    || value.local_semantic_acceptance !== LOCAL_SEMANTIC_ACCEPTANCE_PENDING
    || actor?.client_id !== BRIDGE_CLIENT_ID || actor?.client_type !== BRIDGE_CLIENT_TYPE
    || !/^cp_ap_[a-f0-9]{48}$/.test(text(value.local_handle))
    || !SHA256_RE.test(text(value.policy_sha256).toLowerCase())
    || (typeof admission?.policy_sha256 === 'string'
      && text(value.policy_sha256).toLowerCase() !== admission.policy_sha256.toLowerCase())
    || canonicalJson(facadeContract(value.facade_contract, 'CONTROL_PLANE_APPROVED_PATCH_RESULT_CONTRACT_INVALID')) !== canonicalJson(admission.facade_contract)
    || !SHA256_RE.test(text(value.response_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID', 'control-plane approved-patch result is invalid.');
  }
  for (const field of ['activation_epoch_id', 'process_instance_id', 'server_instance_id']) {
    if (!IDENTIFIER_RE.test(text(identity[field]))) {
      throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_IDENTITY_INVALID', 'runtime identity is invalid.');
    }
  }
  if (!SHA256_RE.test(text(identity.tool_contract_sha256).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_IDENTITY_INVALID', 'runtime identity is invalid.');
  }
  if (!exactKeys(file, ['path', 'preimage_sha256', 'postimage_sha256', 'bytes_written'])) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID', 'approved-patch file receipt is invalid.');
  }
  const filePath = relativePath(file.path, 'CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID');
  const preimage = text(file.preimage_sha256).toLowerCase();
  const postimage = text(file.postimage_sha256).toLowerCase();
  if (filePath !== admission.path || preimage !== admission.preimage_sha256
    || postimage !== admission.postimage_sha256 || !SHA256_RE.test(preimage)
    || !SHA256_RE.test(postimage) || !Number.isSafeInteger(file.bytes_written)
    || file.bytes_written !== admission.postimage_bytes || file.bytes_written < 0
    || file.bytes_written > admission.max_file_bytes) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID', 'approved-patch file receipt is invalid.');
  }
  const safeFile = {
    path: filePath,
    preimage_sha256: preimage,
    postimage_sha256: postimage,
    bytes_written: file.bytes_written
  };
  if (text(value.response_sha256).toLowerCase() !== digest(safeFile)) {
    throw bridgeError('CONTROL_PLANE_APPROVED_PATCH_RESULT_DIGEST_INVALID', 'approved-patch receipt integrity is invalid.');
  }
  return Object.freeze({
    schema_version: 1,
    operation_kind: OPERATION_KIND,
    patch_applied: true,
    local_semantic_acceptance: LOCAL_SEMANTIC_ACCEPTANCE_PENDING,
    local_handle: text(value.local_handle),
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    task_id: admission.task_id,
    writer_lease_generation: admission.writer_lease_generation,
    run_id: text(value.run_id).toLowerCase(),
    wave_id: text(value.wave_id).toLowerCase(),
    policy_sha256: text(value.policy_sha256).toLowerCase(),
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    runtime_identity: {
      activation_epoch_id: text(identity.activation_epoch_id),
      process_instance_id: text(identity.process_instance_id),
      server_instance_id: text(identity.server_instance_id),
      tool_contract_sha256: text(identity.tool_contract_sha256).toLowerCase()
    },
    facade_contract: facadeContract(value.facade_contract, 'CONTROL_PLANE_APPROVED_PATCH_RESULT_CONTRACT_INVALID'),
    file: safeFile,
    response_sha256: digest(safeFile)
  });
}

module.exports = {
  POLICY_SCHEMA_VERSION,
  LEGACY_POLICY_SCHEMA_VERSION,
  STANDING_AUTHORITY_MODE,
  BRIDGE_ENVELOPE_SCHEMA_VERSION,
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  ACTION_TOOL_NAME,
  LOCAL_TOOL_NAME,
  OPERATION_KIND,
  VALIDATION_PROFILE,
  LOCAL_SEMANTIC_ACCEPTANCE_PENDING,
  MAX_PATCH_BYTES,
  MAX_EXACT_FILE_BYTES,
  bridgeError,
  canonicalJson,
  digest,
  facadeContract,
  relativePath,
  normalisePolicy,
  loadApprovedPatchBridgePolicy,
  resolveRegisteredWorkspaceRoot,
  exactApprovedPatchEnvelope,
  admitApprovedPatchBridgeRequest,
  resolveExactRegisteredPatchTarget,
  verifyExactRegisteredPatchPostimage,
  normaliseApprovedPatchWorkflowResult,
  normaliseApprovedPatchResult
};
