"use strict";

// A control-plane bridge is deliberately not inferred from an enrolled node or
// a central action.  The local Recovery Host must have an explicit, expiring
// operator policy before it can make even the one read-only MCP call supported
// by this first lane.  Keep the policy outside the workspace and free of
// credentials so it can be reviewed without becoming another secret store.

const crypto = require('node:crypto');
const fs = require('node:fs');
const { MAX_COLLECTION_BYTES, selectWorkspacePolicy } = require('./controlPlanePolicyStore');
const { URL } = require('node:url');

const POLICY_SCHEMA_VERSION = 2;
const BRIDGE_CLIENT_ID = 'electron-control-plane-bridge';
const BRIDGE_CLIENT_TYPE = 'electron';
const READ_ONLY_TOOL_NAME = 'workspace_context';
const READ_ONLY_ARGUMENTS = Object.freeze({ detail: 'compact', max_entries: 1 });
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const ACTION_IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/;
const MAX_POLICY_BYTES = 16 * 1024;
const FACADE_CONTRACT_SHA256_RE = /^[a-f0-9]{64}$/;
const WORKSPACE_SUMMARY_SCHEMA_VERSION = 1;
const WORKSPACE_SUMMARY_MAX_BYTES = 8 * 1024;
const WORKSPACE_SUMMARY_TEXT_MAX = 256;
const WORKSPACE_SUMMARY_ENTRY_TYPES = new Set(['file', 'directory', 'symlink', 'other']);
const WORKSPACE_SUMMARY_PROJECT_TYPES = new Set(['unknown', 'electron', 'node', 'python', 'rust', 'go']);

function bridgeError(code, message) {
  return Object.assign(new Error(message), { code });
}

function canonicalJson(value) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return JSON.stringify(value);
  const ordered = {};
  for (const key of Object.keys(value).sort()) {
    const item = value[key];
    ordered[key] = item && typeof item === 'object' && !Array.isArray(item)
      ? JSON.parse(canonicalJson(item))
      : item;
  }
  return JSON.stringify(ordered);
}

function digest(value) {
  return crypto.createHash('sha256').update(canonicalJson(value), 'utf8').digest('hex');
}

// Policy fingerprints intentionally retain their established canonical form.
// The compact relay crosses JavaScript, a CJS subprocess, and Python; unlike
// the policy form it must recursively canonicalise objects *inside arrays* so
// all three boundaries can independently prove the same summary bytes.
function canonicalWorkspaceSummaryJson(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => canonicalWorkspaceSummaryJson(item)).join(',')}]`;
  return `{${Object.keys(value).sort().map((key) => (
    `${JSON.stringify(key)}:${canonicalWorkspaceSummaryJson(value[key])}`
  )).join(',')}}`;
}

function workspaceSummaryDigest(value) {
  return crypto.createHash('sha256').update(canonicalWorkspaceSummaryJson(value), 'utf8').digest('hex');
}

function summaryText(value, field, { allowEmpty = false, maxLength = WORKSPACE_SUMMARY_TEXT_MAX } = {}) {
  if (typeof value !== 'string' || value.length > maxLength || /[\u0000-\u001f\u007f]/.test(value)
    || (!allowEmpty && !value)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', `${field} is invalid.`);
  }
  return value;
}

function compactWorkspaceSummary(value) {
  // The local MCP response contains an absolute workspace path and may gain
  // additional fields over time.  This is the only allowlisted projection
  // that may leave the node after an explicit read-only admission.  It is
  // deliberately metadata-only: no file contents, task text, symlink target,
  // absolute path, IPC identity secret, or arbitrary local response field.
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace response has an invalid compact shape.');
  }
  // ``workspace`` is required for the caller's local target check but must
  // never be copied to the central result.
  if (typeof value.workspace !== 'string' || !value.workspace) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace response does not identify its local target.');
  }
  const project = value.project;
  if (!exactKeys(project, ['type', 'name', 'version'])
    || !WORKSPACE_SUMMARY_PROJECT_TYPES.has(project.type)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace project summary is invalid.');
  }
  const entries = value.entries;
  if (!Array.isArray(entries) || entries.length > READ_ONLY_ARGUMENTS.max_entries || typeof value.entries_truncated !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace entry summary is invalid.');
  }
  const safeEntries = entries.map((entry) => {
    if (!exactKeys(entry, ['name', 'path', 'type', 'size_bytes', 'modified', 'is_hidden', 'is_ignored'])
      || !WORKSPACE_SUMMARY_ENTRY_TYPES.has(entry.type)
      || !Number.isSafeInteger(entry.size_bytes) || entry.size_bytes < 0
      || typeof entry.is_hidden !== 'boolean' || typeof entry.is_ignored !== 'boolean') {
      throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace entry summary is invalid.');
    }
    const name = summaryText(entry.name, 'workspace entry name');
    const relativePath = summaryText(entry.path, 'workspace entry path');
    // The fixed local request lists exactly the root.  Accept neither nested
    // nor platform-absolute paths, so an MCP regression cannot disclose a
    // different local root through this small relay.
    if (relativePath !== name || /[\\/]/.test(name) || name === '.' || name === '..') {
      throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace entry is not rooted at the admitted workspace.');
    }
    return Object.freeze({
      name,
      type: entry.type,
      size_bytes: entry.size_bytes,
      is_hidden: entry.is_hidden,
      is_ignored: entry.is_ignored,
    });
  });
  const git = value.git;
  if (!exactKeys(git, ['is_repo', 'branch', 'changed_count', 'truncated'])
    || typeof git.is_repo !== 'boolean'
    || !Number.isSafeInteger(git.changed_count) || git.changed_count < 0 || git.changed_count > 100_000
    || typeof git.truncated !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace Git summary is invalid.');
  }
  const summary = {
    schema_version: WORKSPACE_SUMMARY_SCHEMA_VERSION,
    project: {
      type: project.type,
      name: summaryText(project.name, 'workspace project name'),
      version: summaryText(project.version, 'workspace project version', { allowEmpty: true, maxLength: 128 }),
    },
    entries: safeEntries,
    entries_truncated: value.entries_truncated,
    git: {
      is_repo: git.is_repo,
      branch: summaryText(git.branch == null ? '' : git.branch, 'workspace Git branch', { allowEmpty: true }),
      changed_count: git.changed_count,
      truncated: git.truncated,
    },
  };
  return normaliseWorkspaceSummary(summary);
}

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function normaliseWorkspaceSummary(value) {
  if (!exactKeys(value, ['schema_version', 'project', 'entries', 'entries_truncated', 'git'])
    || value.schema_version !== WORKSPACE_SUMMARY_SCHEMA_VERSION
    || !exactKeys(value.project, ['type', 'name', 'version'])
    || !WORKSPACE_SUMMARY_PROJECT_TYPES.has(value.project.type)
    || !Array.isArray(value.entries) || value.entries.length > READ_ONLY_ARGUMENTS.max_entries
    || typeof value.entries_truncated !== 'boolean'
    || !exactKeys(value.git, ['is_repo', 'branch', 'changed_count', 'truncated'])
    || typeof value.git.is_repo !== 'boolean'
    || !Number.isSafeInteger(value.git.changed_count) || value.git.changed_count < 0 || value.git.changed_count > 100_000
    || typeof value.git.truncated !== 'boolean') {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace relay summary is invalid.');
  }
  const entries = value.entries.map((entry) => {
    if (!exactKeys(entry, ['name', 'type', 'size_bytes', 'is_hidden', 'is_ignored'])
      || !WORKSPACE_SUMMARY_ENTRY_TYPES.has(entry.type)
      || !Number.isSafeInteger(entry.size_bytes) || entry.size_bytes < 0
      || typeof entry.is_hidden !== 'boolean' || typeof entry.is_ignored !== 'boolean') {
      throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace relay summary is invalid.');
    }
    const name = summaryText(entry.name, 'workspace entry name');
    if (/[\\/]/.test(name) || name === '.' || name === '..') {
      throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace relay entry is invalid.');
    }
    return Object.freeze({ name, type: entry.type, size_bytes: entry.size_bytes, is_hidden: entry.is_hidden, is_ignored: entry.is_ignored });
  });
  const summary = {
    schema_version: WORKSPACE_SUMMARY_SCHEMA_VERSION,
    project: {
      type: value.project.type,
      name: summaryText(value.project.name, 'workspace project name'),
      version: summaryText(value.project.version, 'workspace project version', { allowEmpty: true, maxLength: 128 }),
    },
    entries,
    entries_truncated: value.entries_truncated,
    git: {
      is_repo: value.git.is_repo,
      branch: summaryText(value.git.branch, 'workspace Git branch', { allowEmpty: true }),
      changed_count: value.git.changed_count,
      truncated: value.git.truncated,
    },
  };
  if (Buffer.byteLength(canonicalWorkspaceSummaryJson(summary), 'utf8') > WORKSPACE_SUMMARY_MAX_BYTES) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_RESULT_INVALID', 'workspace summary exceeds its bounded relay size.');
  }
  return Object.freeze({ ...summary, project: Object.freeze(summary.project), entries: Object.freeze(entries), git: Object.freeze(summary.git) });
}

function identifier(value, name, pattern = IDENTIFIER_RE) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!pattern.test(text)) throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', `${name} is invalid.`);
  return text;
}

function origin(value, code = 'CONTROL_PLANE_BRIDGE_POLICY_INVALID') {
  const text = typeof value === 'string' ? value.trim() : '';
  let parsed;
  try { parsed = new URL(text); }
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
    throw bridgeError(code, 'control-plane read-only authority is expired.');
  }
  return expiresAtMs;
}

function facadeContract(value, code = 'CONTROL_PLANE_BRIDGE_POLICY_INVALID') {
  if (!exactKeys(value, ['schema_version', 'profile', 'sha256'])) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  const schemaVersion = Number(value.schema_version);
  const profile = typeof value.profile === 'string' ? value.profile.trim() : '';
  const sha256 = typeof value.sha256 === 'string' ? value.sha256.trim().toLowerCase() : '';
  if (!Number.isSafeInteger(schemaVersion) || schemaVersion < 1 || schemaVersion > 1_000_000
    || !IDENTIFIER_RE.test(profile)
    || !FACADE_CONTRACT_SHA256_RE.test(sha256)) {
    throw bridgeError(code, 'control-plane facade contract is invalid.');
  }
  return Object.freeze({ schema_version: schemaVersion, profile, sha256 });
}

function normalisePolicy(value, { now = Date.now() } = {}) {
  const expected = [
    'schema_version', 'enabled', 'server_origin', 'owner_id', 'device_id',
    'endpoint_id', 'workspace_id', 'workspace_generation', 'expires_at_ms', 'facade_contract'
  ];
  if (!exactKeys(value, expected)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only policy has an invalid schema.');
  }
  if (Number(value.schema_version) !== POLICY_SCHEMA_VERSION) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only policy version is unsupported.');
  }
  if (value.enabled !== true) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_DISABLED', 'control-plane read-only bridge is not locally enabled.');
  }
  return Object.freeze({
    schema_version: POLICY_SCHEMA_VERSION,
    server_origin: origin(value.server_origin),
    owner_id: identifier(value.owner_id, 'owner_id'),
    device_id: identifier(value.device_id, 'device_id'),
    endpoint_id: identifier(value.endpoint_id, 'endpoint_id'),
    workspace_id: identifier(value.workspace_id, 'workspace_id'),
    workspace_generation: identifier(value.workspace_generation, 'workspace_generation'),
    expires_at_ms: expiry(value.expires_at_ms, now, 'CONTROL_PLANE_BRIDGE_POLICY_EXPIRED'),
    facade_contract: facadeContract(value.facade_contract)
  });
}

function loadReadOnlyBridgePolicy(paths, { target = null, now = Date.now() } = {}) {
  const policyFile = typeof paths?.controlPlaneReadOnlyPolicyFile === 'function'
    ? paths.controlPlaneReadOnlyPolicyFile()
    : '';
  if (!policyFile || !fs.existsSync(policyFile)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_MISSING', 'control-plane read-only bridge policy is not installed.');
  }
  let raw;
  try {
    const stat = fs.statSync(policyFile);
    if (!stat.isFile() || stat.size > MAX_COLLECTION_BYTES) {
      throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only bridge policy is invalid.');
    }
    raw = JSON.parse(fs.readFileSync(policyFile, 'utf8'));
  } catch (error) {
    if (error?.code?.startsWith('CONTROL_PLANE_BRIDGE_')) throw error;
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only bridge policy cannot be parsed.');
  }
  const policy = normalisePolicy(selectWorkspacePolicy(raw, target, { code: 'CONTROL_PLANE_BRIDGE_POLICY_INVALID', maxPolicyBytes: MAX_POLICY_BYTES }), { now });
  return Object.freeze({ ...policy, policy_sha256: digest(policy) });
}

function sameArguments(value) {
  return exactKeys(value, Object.keys(READ_ONLY_ARGUMENTS))
    && value.detail === READ_ONLY_ARGUMENTS.detail
    && value.max_entries === READ_ONLY_ARGUMENTS.max_entries;
}

function admitReadOnlyBridgeRequest(policy, request, { now = Date.now() } = {}) {
  const expected = [
    'server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id',
    'workspace_generation', 'context_id', 'binding_id', 'action_id', 'attempt_id',
    'tool_name', 'arguments', 'expires_at_ms', 'facade_contract'
  ];
  if (!exactKeys(request, expected)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_REQUEST_INVALID', 'control-plane bridge request has an invalid schema.');
  }
  const candidate = {
    server_origin: origin(request.server_origin, 'CONTROL_PLANE_BRIDGE_REQUEST_INVALID'),
    owner_id: identifier(request.owner_id, 'owner_id'),
    device_id: identifier(request.device_id, 'device_id'),
    endpoint_id: identifier(request.endpoint_id, 'endpoint_id'),
    workspace_id: identifier(request.workspace_id, 'workspace_id'),
    workspace_generation: identifier(request.workspace_generation, 'workspace_generation'),
    context_id: identifier(request.context_id, 'context_id', ACTION_IDENTIFIER_RE),
    binding_id: identifier(request.binding_id, 'binding_id', ACTION_IDENTIFIER_RE),
    action_id: identifier(request.action_id, 'action_id', ACTION_IDENTIFIER_RE),
    attempt_id: identifier(request.attempt_id, 'attempt_id', ACTION_IDENTIFIER_RE),
    tool_name: typeof request.tool_name === 'string' ? request.tool_name : '',
    arguments: request.arguments,
    expires_at_ms: expiry(request.expires_at_ms, now, 'CONTROL_PLANE_BRIDGE_REQUEST_EXPIRED'),
    facade_contract: facadeContract(request.facade_contract, 'CONTROL_PLANE_BRIDGE_REQUEST_INVALID')
  };
  if (candidate.expires_at_ms > policy.expires_at_ms) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_EXPIRED', 'control-plane action outlives the local read-only policy.');
  }
  for (const field of ['server_origin', 'owner_id', 'device_id', 'endpoint_id', 'workspace_id', 'workspace_generation']) {
    if (candidate[field] !== policy[field]) {
      throw bridgeError('CONTROL_PLANE_BRIDGE_TARGET_MISMATCH', `control-plane bridge ${field} does not match local policy.`);
    }
  }
  if (canonicalJson(candidate.facade_contract) !== canonicalJson(policy.facade_contract)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_CONTRACT_MISMATCH', 'control-plane facade contract does not match local policy.');
  }
  if (candidate.tool_name !== READ_ONLY_TOOL_NAME || !sameArguments(candidate.arguments)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_TOOL_DENIED', 'control-plane bridge only admits compact workspace_context.');
  }
  return Object.freeze({
    schema_version: POLICY_SCHEMA_VERSION,
    operation_kind: 'control_plane_read_only_workspace_context',
    ...candidate,
    arguments: { ...READ_ONLY_ARGUMENTS },
    policy_sha256: policy.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE }
  });
}

module.exports = {
  POLICY_SCHEMA_VERSION,
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  READ_ONLY_TOOL_NAME,
  READ_ONLY_ARGUMENTS,
  WORKSPACE_SUMMARY_SCHEMA_VERSION,
  facadeContract,
  loadReadOnlyBridgePolicy,
  admitReadOnlyBridgeRequest,
  compactWorkspaceSummary,
  normaliseWorkspaceSummary,
  normalisePolicy,
  canonicalJson,
  digest,
  canonicalWorkspaceSummaryJson,
  workspaceSummaryDigest
};
