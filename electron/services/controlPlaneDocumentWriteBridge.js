"use strict";

// The document-write lane is a local, standing-policy adapter.  Ubuntu may
// supply a bounded document payload and an opaque workspace target, but it can
// never supply an absolute path, an MCP credential, or a Recovery descriptor.
// The existing approved-patch policy is deliberately reused as the local
// writable-root/path authority; this module adds document-specific validation
// and digest-only receipt shaping.

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');

const {
  loadApprovedPatchBridgePolicy,
  resolveRegisteredWorkspaceRoot,
  facadeContract,
  relativePath,
  policyAllowsPath,
  digest
} = require('./controlPlaneApprovedPatchBridge');

const POLICY_SCHEMA_VERSION = 3;
const EXACT_POLICY_SCHEMA_VERSION = 2;
const STANDING_AUTHORITY_MODE = 'standing';
const BRIDGE_ENVELOPE_SCHEMA_VERSION = 1;
const BRIDGE_CLIENT_ID = 'electron-control-plane-document-bridge';
const BRIDGE_CLIENT_TYPE = 'electron';
const ACTION_TOOL_NAME = 'document_workflow';
const LOCAL_TOOL_NAME = 'document_workflow';
const OPERATION_KIND = 'control_plane_document_write';
const DOCUMENT_OPERATIONS = new Set(['document_create', 'document_convert']);
const CREATE_ACTION = 'create';
const CONVERT_ACTION = 'convert';
const MAX_CONTENT_BYTES = 256 * 1024;
const MAX_TITLE_BYTES = 256;
const MAX_RESULT_BYTES = 256 * 1024;
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const ACTION_IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/;
const TASK_ID_RE = /^task_[a-f0-9]{32}$/;
const SHA256_RE = /^[a-f0-9]{64}$/;
const TARGET_EXTENSIONS = new Set(['.docx', '.md', '.txt']);
const SOURCE_EXTENSIONS = new Set(['.pdf', '.docx', '.md', '.txt', '.csv', '.json', '.xml', '.html', '.htm']);

function bridgeError(code, message) {
  return Object.assign(new Error(message || code), { code });
}

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function pathKey(value) {
  const normalized = path.normalize(path.resolve(value));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function documentPath(value, code = 'CONTROL_PLANE_DOCUMENT_WRITE_PATH_INVALID', { source = false } = {}) {
  let candidate;
  try { candidate = relativePath(value, code); }
  catch (error) { throw bridgeError(error?.code || code, error?.message); }
  const suffix = path.posix.extname(candidate).toLowerCase();
  const allowed = source ? SOURCE_EXTENSIONS : TARGET_EXTENSIONS;
  if (!allowed.has(suffix)) {
    throw bridgeError(code, source ? 'document source format is not supported.' : 'document target format is not supported.');
  }
  return candidate;
}

function documentTitle(value, code = 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID') {
  if (typeof value !== 'string' || Buffer.byteLength(value, 'utf8') > MAX_TITLE_BYTES
    || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value)) {
    throw bridgeError(code, 'document title is invalid.');
  }
  return value;
}

function documentContent(value, code = 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID') {
  if (typeof value !== 'string' || Buffer.byteLength(value, 'utf8') > MAX_CONTENT_BYTES
    || value.includes('\0')) {
    throw bridgeError(code, 'document content is invalid.');
  }
  return value;
}

function loadDocumentWriteBridgePolicy(paths, options = {}) {
  let policy;
  try { policy = loadApprovedPatchBridgePolicy(paths, options); }
  catch (error) {
    throw bridgeError(
      String(error?.code || 'CONTROL_PLANE_DOCUMENT_WRITE_POLICY_INVALID')
        .replace('APPROVED_PATCH', 'DOCUMENT_WRITE'),
      error?.message
    );
  }
  if (![POLICY_SCHEMA_VERSION, EXACT_POLICY_SCHEMA_VERSION].includes(policy.schema_version)
    || policy.authority_mode !== STANDING_AUTHORITY_MODE) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_POLICY_INVALID', 'document write requires standing local write authority.');
  }
  return Object.freeze({ ...policy });
}

function resolveRegisteredDocumentWorkspaceRoot(paths, policy) {
  try { return resolveRegisteredWorkspaceRoot(paths, policy); }
  catch (error) {
    throw bridgeError(
      String(error?.code || 'CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_REGISTRY_REQUIRED')
        .replace('APPROVED_PATCH', 'DOCUMENT_WRITE'),
      error?.message
    );
  }
}

function admitDocumentWriteBridgeRequest(policy, request, { now = Date.now() } = {}) {
  const expected = [
    'server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id',
    'workspace_generation', 'context_id', 'binding_id', 'action_id', 'attempt_id',
    'task_id', 'writer_lease_generation', 'authority_mode', 'tool_name', 'operation',
    'target', 'source', 'title', 'content', 'content_sha256', 'overwrite',
    'intent_digest', 'admission_reference', 'expires_at_ms', 'policy_sha256',
    'facade_contract'
  ];
  if (!exactKeys(request, expected)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID', 'document write request schema is invalid.');
  }
  const candidate = {
    server_origin: text(request.server_origin),
    owner_id: text(request.owner_id),
    device_id: text(request.device_id),
    endpoint_id: text(request.endpoint_id),
    workspace_id: text(request.workspace_id),
    workspace_generation: text(request.workspace_generation),
    context_id: text(request.context_id),
    binding_id: text(request.binding_id),
    action_id: text(request.action_id),
    attempt_id: text(request.attempt_id),
    task_id: text(request.task_id),
    writer_lease_generation: request.writer_lease_generation,
    authority_mode: text(request.authority_mode),
    tool_name: request.tool_name,
    operation: request.operation,
    target: documentPath(request.target, 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID'),
    source: request.source == null ? null : documentPath(request.source, 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID', { source: true }),
    title: documentTitle(request.title),
    content: documentContent(request.content),
    content_sha256: text(request.content_sha256).toLowerCase(),
    overwrite: request.overwrite,
    intent_digest: text(request.intent_digest).toLowerCase(),
    admission_reference: text(request.admission_reference),
    expires_at_ms: request.expires_at_ms,
    policy_sha256: text(request.policy_sha256).toLowerCase(),
    facade_contract: facadeContract(request.facade_contract, 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID')
  };
  if (!['http:', 'https:'].includes(new URL(candidate.server_origin).protocol)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID', 'document write origin is invalid.');
  }
  if (!IDENTIFIER_RE.test(candidate.owner_id) || !IDENTIFIER_RE.test(candidate.device_id)
    || !IDENTIFIER_RE.test(candidate.endpoint_id) || !IDENTIFIER_RE.test(candidate.workspace_id)
    || !IDENTIFIER_RE.test(candidate.workspace_generation)
    || !ACTION_IDENTIFIER_RE.test(candidate.context_id) || !ACTION_IDENTIFIER_RE.test(candidate.binding_id)
    || !ACTION_IDENTIFIER_RE.test(candidate.action_id) || !ACTION_IDENTIFIER_RE.test(candidate.attempt_id)
    || !TASK_ID_RE.test(candidate.task_id)
    || !Number.isSafeInteger(candidate.writer_lease_generation)
    || candidate.writer_lease_generation < 1 || candidate.writer_lease_generation > 1_000_000_000
    || candidate.authority_mode !== STANDING_AUTHORITY_MODE
    || candidate.tool_name !== ACTION_TOOL_NAME
    || !DOCUMENT_OPERATIONS.has(candidate.operation)
    || !SHA256_RE.test(candidate.content_sha256)
    || sha256(Buffer.from(candidate.content, 'utf8')) !== candidate.content_sha256
    || !SHA256_RE.test(candidate.intent_digest)
    || candidate.admission_reference !== `mcp_document_write:${candidate.intent_digest}`
    || !Number.isSafeInteger(candidate.expires_at_ms) || candidate.expires_at_ms <= now
    || !SHA256_RE.test(candidate.policy_sha256)
    || candidate.policy_sha256 !== policy.policy_sha256
    || typeof candidate.overwrite !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID', 'document write request values are invalid.');
  }
  if (candidate.operation === 'document_create') {
    if (candidate.source !== null) throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID', 'document create cannot carry a source.');
  } else if (candidate.source === null || pathKey(candidate.source) === pathKey(candidate.target)
    || path.posix.extname(candidate.target).toLowerCase() !== '.docx') {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID', 'document conversion source/target is invalid.');
  }
  if (candidate.server_origin !== policy.server_origin || candidate.owner_id !== policy.owner_id
    || candidate.device_id !== policy.device_id || candidate.endpoint_id !== policy.endpoint_id
    || candidate.workspace_id !== policy.workspace_id || candidate.workspace_generation !== policy.workspace_generation) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_TARGET_MISMATCH', 'document write target does not match local policy.');
  }
  if (canonicalContract(candidate.facade_contract) !== canonicalContract(policy.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_CONTRACT_MISMATCH', 'document write facade contract does not match local policy.');
  }
  if (!policyAllowsPath(policy, candidate.target)
    || (candidate.source !== null && !policyAllowsPath(policy, candidate.source))) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_PATH_DENIED', 'document path is not admitted by local policy.');
  }
  return Object.freeze({
    schema_version: BRIDGE_ENVELOPE_SCHEMA_VERSION,
    operation_kind: OPERATION_KIND,
    ...candidate,
    policy_sha256: policy.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE }
  });
}

function canonicalContract(value) {
  return JSON.stringify({
    schema_version: value.schema_version,
    profile: value.profile,
    sha256: value.sha256
  });
}

function resolveDocumentTarget(workspaceRoot, admission, { source = false } = {}) {
  if (typeof workspaceRoot !== 'string' || !path.isAbsolute(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_MISMATCH', 'document workspace is invalid.');
  }
  let root;
  try { root = fs.realpathSync.native(workspaceRoot); }
  catch { throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_MISMATCH', 'document workspace is unavailable.'); }
  if (!fs.statSync(root).isDirectory() || pathKey(root) !== pathKey(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_MISMATCH', 'document workspace changed.');
  }
  const relative = source ? admission.source : admission.target;
  const target = path.resolve(root, ...relative.split('/'));
  const prefix = `${pathKey(root)}${path.sep}`;
  if (!pathKey(target).startsWith(prefix)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_PATH_DENIED', 'document path escapes workspace.');
  }
  const parts = relative.split('/');
  let cursor = root;
  for (const [index, part] of parts.entries()) {
    cursor = path.join(cursor, part);
    const final = index === parts.length - 1;
    let stat;
    let real;
    try {
      stat = fs.lstatSync(cursor);
      real = fs.realpathSync.native(cursor);
    } catch (error) {
      if (error?.code === 'ENOENT' && final && !source) return target;
      throw bridgeError(source ? 'CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_MISSING' : 'CONTROL_PLANE_DOCUMENT_WRITE_TARGET_INVALID', 'document path is unavailable.');
    }
    if (stat.isSymbolicLink() || pathKey(real) !== pathKey(cursor)) {
      throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REPARSE_DENIED', 'document path contains a reparse point.');
    }
    if (final ? !stat.isFile() : !stat.isDirectory()) {
      throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_REPARSE_DENIED', 'document path is not a direct regular file.');
    }
  }
  return target;
}

function verifyDocumentTarget(workspaceRoot, admission) {
  const absolute = resolveDocumentTarget(workspaceRoot, admission);
  let raw;
  try { raw = fs.readFileSync(absolute); }
  catch { throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID', 'document result is unavailable.'); }
  if (!raw.length || raw.length > MAX_RESULT_BYTES) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID', 'document result size is invalid.');
  }
  return {
    target: admission.target,
    size: raw.length,
    sha256: sha256(raw),
    format: path.posix.extname(admission.target).slice(1).toLowerCase()
  };
}

function normaliseDocumentWriteResult(value, admission) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || value.schema_version !== BRIDGE_ENVELOPE_SCHEMA_VERSION
    || value.operation_kind !== OPERATION_KIND
    || value.action_id !== admission.action_id
    || value.attempt_id !== admission.attempt_id
    || value.task_id !== admission.task_id
    || value.writer_lease_generation !== admission.writer_lease_generation
    || value.operation !== admission.operation
    || value.target !== admission.target
    || value.source !== admission.source
    || value.actor?.client_id !== BRIDGE_CLIENT_ID
    || value.actor?.client_type !== BRIDGE_CLIENT_TYPE
    || !/^cp_doc_[a-f0-9]{48}$/.test(text(value.local_handle))
    || !SHA256_RE.test(text(value.policy_sha256).toLowerCase())
    || value.policy_sha256.toLowerCase() !== admission.policy_sha256
    || canonicalContract(value.facade_contract) !== canonicalContract(admission.facade_contract)
    || !value.runtime_identity || typeof value.runtime_identity !== 'object'
    || !IDENTIFIER_RE.test(text(value.runtime_identity.activation_epoch_id))
    || !IDENTIFIER_RE.test(text(value.runtime_identity.process_instance_id))
    || !IDENTIFIER_RE.test(text(value.runtime_identity.server_instance_id))
    || !SHA256_RE.test(text(value.runtime_identity.tool_contract_sha256).toLowerCase())
    || !value.result || typeof value.result !== 'object' || Array.isArray(value.result)
    || value.result.target !== admission.target
    || !Number.isSafeInteger(value.result.size) || value.result.size < 1 || value.result.size > MAX_RESULT_BYTES
    || !SHA256_RE.test(text(value.result.sha256).toLowerCase())
    || !/^[a-z0-9]{1,16}$/.test(text(value.result.format).toLowerCase())) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID', 'document write receipt is invalid.');
  }
  const safeResult = {
    operation: admission.operation,
    target: admission.target,
    source: admission.source,
    size: value.result.size,
    sha256: text(value.result.sha256).toLowerCase(),
    format: text(value.result.format).toLowerCase()
  };
  if (text(value.response_sha256).toLowerCase() !== digest(safeResult)) {
    throw bridgeError('CONTROL_PLANE_DOCUMENT_WRITE_RESULT_DIGEST_INVALID', 'document receipt integrity is invalid.');
  }
  return Object.freeze({
    schema_version: BRIDGE_ENVELOPE_SCHEMA_VERSION,
    operation_kind: OPERATION_KIND,
    local_handle: text(value.local_handle),
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    task_id: admission.task_id,
    writer_lease_generation: admission.writer_lease_generation,
    operation: admission.operation,
    target: admission.target,
    source: admission.source,
    result: safeResult,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    policy_sha256: admission.policy_sha256,
    facade_contract: facadeContract(value.facade_contract, 'CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID'),
    runtime_identity: {
      activation_epoch_id: text(value.runtime_identity.activation_epoch_id),
      process_instance_id: text(value.runtime_identity.process_instance_id),
      server_instance_id: text(value.runtime_identity.server_instance_id),
      tool_contract_sha256: text(value.runtime_identity.tool_contract_sha256).toLowerCase()
    },
    response_sha256: digest(safeResult)
  });
}

module.exports = {
  POLICY_SCHEMA_VERSION,
  EXACT_POLICY_SCHEMA_VERSION,
  STANDING_AUTHORITY_MODE,
  BRIDGE_ENVELOPE_SCHEMA_VERSION,
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  ACTION_TOOL_NAME,
  LOCAL_TOOL_NAME,
  OPERATION_KIND,
  MAX_CONTENT_BYTES,
  MAX_TITLE_BYTES,
  MAX_RESULT_BYTES,
  bridgeError,
  digest,
  loadDocumentWriteBridgePolicy,
  resolveRegisteredDocumentWorkspaceRoot,
  admitDocumentWriteBridgeRequest,
  resolveDocumentTarget,
  verifyDocumentTarget,
  normaliseDocumentWriteResult
};
