const test = require('node:test');
const assert = require('node:assert/strict');
const { validateConnectorReadyGate } = require('../electron/services/fullCleanActivation');

const SHA_CURRENT = '6'.repeat(64);
const SHA_ACKED = 'c'.repeat(64);
const BINDING_A = 'a'.repeat(64);
const BINDING_B = 'b'.repeat(64);
const NOW = Date.now();
const OBSERVED_AT = new Date(NOW - 1000).toISOString();

function bootstrapFixture(overrides = {}) {
  return {
    current_contract_contact: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    client_type: 'chatweb',
    client_id: 'chatweb-matrix-1',
    method: 'tools/call',
    tool_name: 'workspace_context',
    workspace_accessed: false,
    contract_sha256: SHA_CURRENT,
    process_instance_id: 'proc-matrix-1',
    server_instance_id: 'srv-matrix-1',
    activation_epoch_id: 'activation-matrix-1',
    observed_at: OBSERVED_AT,
    workspace_binding_id: BINDING_A,
    workspace_generation: 3,
    ...overrides
  };
}

function healthFixture(bootstrapOverrides, healthOverrides = {}) {
  const bootstrap = bootstrapOverrides === null ? null : bootstrapFixture(bootstrapOverrides);
  return {
    process_instance_id: 'proc-matrix-1',
    instance_id: 'srv-matrix-1',
    activation_epoch_id: 'activation-matrix-1',
    tool_contract: { sha256: SHA_CURRENT, compatible_predecessor_sha256: [SHA_ACKED] },
    workspace_binding_id: BINDING_A,
    workspace_generation: 3,
    connector_activation_bootstrap: bootstrap,
    ...healthOverrides
  };
}

function compatibleStatusFixture(overrides = {}) {
  return {
    available: true,
    currentSha256: SHA_CURRENT,
    acknowledgedSha256: SHA_ACKED,
    contractState: 'CHANGED_COMPATIBLE_NEEDS_ACK',
    refreshRequired: false,
    acknowledgementPending: true,
    contractChanged: true,
    bootstrapCurrent: true,
    compatibilitySource: 'declared_exact_predecessor_activation_bootstrap',
    rediscovered: false,
    compatibilityAcknowledged: false,
    ...overrides
  };
}

function reasons(health, status) {
  return validateConnectorReadyGate({ health, contractStatus: status, nowUnixMs: NOW }).reasons;
}

test('connector gate accepts a matching workspace binding', () => {
  const found = reasons(healthFixture(), compatibleStatusFixture());
  assert.ok(!found.includes('CONNECTOR_BINDING_MISMATCH'), `unexpected mismatch in ${found.join(',')}`);
});

test('connector gate reports a binding mismatch on workspace switch', () => {
  const found = reasons(
    healthFixture({ workspace_binding_id: BINDING_B, workspace_generation: 4 }),
    compatibleStatusFixture()
  );
  assert.ok(found.includes('CONNECTOR_BINDING_MISMATCH'), `missing mismatch in ${found.join(',')}`);
});

test('connector gate skips the binding check when either side predates binding metadata', () => {
  const health = healthFixture();
  delete health.workspace_binding_id;
  const bootstrap = { ...health.connector_activation_bootstrap };
  delete bootstrap.workspace_binding_id;
  delete bootstrap.workspace_generation;
  health.connector_activation_bootstrap = bootstrap;
  const found = reasons(health, compatibleStatusFixture());
  assert.ok(!found.includes('CONNECTOR_BINDING_MISMATCH'), `unexpected mismatch in ${found.join(',')}`);
});

test('connector gate reports a generation-only mismatch', () => {
  const found = reasons(
    healthFixture({ workspace_generation: 9 }),
    compatibleStatusFixture()
  );
  assert.ok(found.includes('CONNECTOR_BINDING_MISMATCH'), `missing mismatch in ${found.join(',')}`);
});
