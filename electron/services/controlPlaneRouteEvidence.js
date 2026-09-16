const fs = require('node:fs');

// This file is a *local observation* that the same-user node agent received a
// successful authenticated heartbeat response from the Ubuntu control plane.
// It is not a node credential, execution grant, or substitute for per-action
// admission. Local action code independently checks the policy, exact runtime
// identity, and the central action envelope before it can touch a workspace.
const ROUTE_EVIDENCE_SCHEMA_VERSION = 1;
const ROUTE_EVIDENCE_KIND = 'control_plane_authenticated_heartbeat';
const ROUTE_EVIDENCE_MAX_BYTES = 8 * 1024;
const ROUTE_EVIDENCE_MAX_AGE_MS = 60_000;
const ROUTE_EVIDENCE_FUTURE_SKEW_MS = 5_000;
const IDENTIFIER_RE = /^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/;
const SHA256_RE = /^[a-f0-9]{64}$/;
const READINESS = new Set(['ready', 'degraded', 'blocked', 'unknown']);
const POLICY_STATES = new Set(['enabled', 'expired_or_disabled', 'unavailable', 'unobserved']);

function routeEvidenceResult({ connected = false, authorityReady = false, reason, evidence = null } = {}) {
  return Object.freeze({
    connected: connected === true,
    authorityReady: authorityReady === true,
    reason: String(reason || 'CENTRAL_ROUTE_EVIDENCE_INVALID'),
    evidence
  });
}

function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function origin(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  let parsed;
  try { parsed = new URL(text); }
  catch { return ''; }
  if (!['http:', 'https:'].includes(parsed.protocol)
    || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) return '';
  return parsed.origin;
}

function identifier(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  return IDENTIFIER_RE.test(text) ? text : '';
}

function policy(value, observedAtMs, now) {
  const state = typeof value.policy_state === 'string' ? value.policy_state.trim().toLowerCase() : '';
  if (!POLICY_STATES.has(state)) return null;
  const expiresAtMs = value.policy_expires_at_ms;
  const sha256 = typeof value.policy_sha256 === 'string' ? value.policy_sha256.trim().toLowerCase() : '';
  if (state === 'enabled' || state === 'expired_or_disabled') {
    if (!Number.isSafeInteger(expiresAtMs) || expiresAtMs <= 0 || !SHA256_RE.test(sha256)) return null;
    return Object.freeze({ state, expiresAtMs, sha256, authorityReady: state === 'enabled' && expiresAtMs > now && expiresAtMs > observedAtMs });
  }
  if (expiresAtMs != null || value.policy_sha256 != null) return null;
  return Object.freeze({ state, expiresAtMs: null, sha256: null, authorityReady: false });
}

function normaliseRouteEvidence(value, { now = Date.now() } = {}) {
  const expected = [
    'schema_version', 'kind', 'server_origin', 'device_id', 'endpoint_id',
    'credential_generation', 'server_last_seen_at_ms', 'observed_at_ms',
    'runtime_readiness', 'policy_state', 'policy_expires_at_ms', 'policy_sha256'
  ];
  if (!exactKeys(value, expected)
    || value.schema_version !== ROUTE_EVIDENCE_SCHEMA_VERSION
    || value.kind !== ROUTE_EVIDENCE_KIND) return null;
  const serverOrigin = origin(value.server_origin);
  const deviceId = identifier(value.device_id);
  const endpointId = identifier(value.endpoint_id);
  const observedAtMs = value.observed_at_ms;
  if (!serverOrigin || !deviceId || !endpointId
    || !Number.isSafeInteger(value.credential_generation) || value.credential_generation < 1
    || !Number.isSafeInteger(value.server_last_seen_at_ms) || value.server_last_seen_at_ms <= 0
    || !Number.isSafeInteger(observedAtMs) || observedAtMs <= 0
    || !READINESS.has(value.runtime_readiness)
    || observedAtMs > now + ROUTE_EVIDENCE_FUTURE_SKEW_MS) return null;
  const policyValue = policy(value, observedAtMs, now);
  if (!policyValue) return null;
  return Object.freeze({
    serverOrigin,
    deviceId,
    endpointId,
    credentialGeneration: value.credential_generation,
    serverLastSeenAtMs: value.server_last_seen_at_ms,
    observedAtMs,
    runtimeReadiness: value.runtime_readiness,
    policyState: policyValue.state,
    policyExpiresAtMs: policyValue.expiresAtMs,
    policySha256: policyValue.sha256,
    authorityReady: policyValue.authorityReady
  });
}

function readControlPlaneRouteEvidence(paths, { expectedDeviceId = '', now = Date.now() } = {}) {
  const deviceId = String(expectedDeviceId || '').trim().toLowerCase();
  if (!deviceId) return routeEvidenceResult({ reason: 'CENTRAL_LOCAL_DEVICE_IDENTITY_UNAVAILABLE' });
  const file = typeof paths?.controlPlaneRouteEvidenceFile === 'function'
    ? paths.controlPlaneRouteEvidenceFile() : '';
  if (!file || !fs.existsSync(file)) return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_MISSING' });
  let raw;
  try {
    const stat = fs.statSync(file);
    if (!stat.isFile() || stat.size > ROUTE_EVIDENCE_MAX_BYTES) {
      return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_INVALID' });
    }
    raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_INVALID' });
  }
  const evidence = normaliseRouteEvidence(raw, { now });
  if (!evidence) return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_INVALID' });
  if (evidence.deviceId.toLowerCase() !== deviceId) {
    return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_DEVICE_MISMATCH' });
  }
  if (now - evidence.observedAtMs > ROUTE_EVIDENCE_MAX_AGE_MS) {
    return routeEvidenceResult({ reason: 'CENTRAL_ROUTE_EVIDENCE_STALE' });
  }
  return routeEvidenceResult({
    connected: true,
    authorityReady: evidence.authorityReady,
    reason: evidence.authorityReady ? 'CENTRAL_ROUTE_READY' : 'CENTRAL_LOCAL_POLICY_NOT_READY',
    evidence
  });
}

module.exports = {
  ROUTE_EVIDENCE_SCHEMA_VERSION,
  ROUTE_EVIDENCE_KIND,
  ROUTE_EVIDENCE_MAX_AGE_MS,
  normaliseRouteEvidence,
  readControlPlaneRouteEvidence
};
