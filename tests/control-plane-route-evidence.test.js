const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const {
  ROUTE_EVIDENCE_KIND,
  readControlPlaneRouteEvidence
} = require('../electron/services/controlPlaneRouteEvidence');

function fixture(t, evidence) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-central-route-'));
  const file = path.join(root, 'control-plane-route-evidence.json');
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(file, JSON.stringify(evidence), 'utf8');
  return { controlPlaneRouteEvidenceFile: () => file };
}

function evidence(now, patch = {}) {
  return {
    schema_version: 1,
    kind: ROUTE_EVIDENCE_KIND,
    server_origin: 'https://svhome.tail0e4032.ts.net',
    device_id: '426f21c3-7a90-4275-9cb0-1b4c5de34a11',
    endpoint_id: 'endpoint-office-central-0001',
    credential_generation: 1,
    server_last_seen_at_ms: now - 10,
    observed_at_ms: now - 10,
    runtime_readiness: 'ready',
    policy_state: 'enabled',
    policy_expires_at_ms: now + 60_000,
    policy_sha256: 'a'.repeat(64),
    ...patch
  };
}

test('authenticated route evidence can make a central executor ready without a Windows tunnel', (t) => {
  const now = 1_700_000_000_000;
  const route = readControlPlaneRouteEvidence(fixture(t, evidence(now)), {
    expectedDeviceId: '426f21c3-7a90-4275-9cb0-1b4c5de34a11',
    now
  });
  assert.equal(route.connected, true);
  assert.equal(route.authorityReady, true);
  assert.equal(route.reason, 'CENTRAL_ROUTE_READY');
  assert.equal(route.evidence.serverOrigin, 'https://svhome.tail0e4032.ts.net');
  assert.equal(route.evidence.endpointId, 'endpoint-office-central-0001');
  assert.equal(JSON.stringify(route).includes('node_secret'), false);
});

test('route evidence is fail-closed for stale, copied, or non-authorizing data', (t) => {
  const now = 1_700_000_000_000;
  const stale = readControlPlaneRouteEvidence(fixture(t, evidence(now, { observed_at_ms: now - 60_001 })), {
    expectedDeviceId: '426f21c3-7a90-4275-9cb0-1b4c5de34a11',
    now
  });
  assert.equal(stale.connected, false);
  assert.equal(stale.reason, 'CENTRAL_ROUTE_EVIDENCE_STALE');

  const copied = readControlPlaneRouteEvidence(fixture(t, evidence(now)), {
    expectedDeviceId: '6f7cc67b-71e9-4f14-b7e4-1d92915d6790',
    now
  });
  assert.equal(copied.connected, false);
  assert.equal(copied.reason, 'CENTRAL_ROUTE_EVIDENCE_DEVICE_MISMATCH');

  const noPolicy = readControlPlaneRouteEvidence(fixture(t, evidence(now, {
    policy_state: 'unavailable',
    policy_expires_at_ms: null,
    policy_sha256: null
  })), {
    expectedDeviceId: '426f21c3-7a90-4275-9cb0-1b4c5de34a11',
    now
  });
  assert.equal(noPolicy.connected, true);
  assert.equal(noPolicy.authorityReady, false);
  assert.equal(noPolicy.reason, 'CENTRAL_LOCAL_POLICY_NOT_READY');
});
