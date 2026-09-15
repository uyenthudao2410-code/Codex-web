"use strict";

// A control-plane bridge is deliberately not inferred from an enrolled node or
// a central action.  The local Recovery Host must have an explicit, expiring
// operator policy before it can make even the one read-only MCP call supported
// by this first lane.  Keep the policy outside the workspace and free of
// credentials so it can be reviewed without becoming another secret store.

const crypto = require('node:crypto');
const fs = require('node:fs');
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

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
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

function loadReadOnlyBridgePolicy(paths, { now = Date.now() } = {}) {
  const policyFile = typeof paths?.controlPlaneReadOnlyPolicyFile === 'function'
    ? paths.controlPlaneReadOnlyPolicyFile()
    : '';
  if (!policyFile || !fs.existsSync(policyFile)) {
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_MISSING', 'control-plane read-only bridge policy is not installed.');
  }
  let raw;
  try {
    const stat = fs.statSync(policyFile);
    if (!stat.isFile() || stat.size > MAX_POLICY_BYTES) {
      throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only bridge policy is invalid.');
    }
    raw = JSON.parse(fs.readFileSync(policyFile, 'utf8'));
  } catch (error) {
    if (error?.code?.startsWith('CONTROL_PLANE_BRIDGE_')) throw error;
    throw bridgeError('CONTROL_PLANE_BRIDGE_POLICY_INVALID', 'control-plane read-only bridge policy cannot be parsed.');
  }
  const policy = normalisePolicy(raw, { now });
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
  facadeContract,
  loadReadOnlyBridgePolicy,
  admitReadOnlyBridgeRequest,
  normalisePolicy,
  canonicalJson,
  digest
};
