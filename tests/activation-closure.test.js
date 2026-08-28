const test = require('node:test');
const assert = require('node:assert/strict');
const {
  computeActivationClosure,
  activationSourceCheckpoint
} = require('../electron/services/activationClosure');
const { RecoveryHost, activationClosureProjection } = require('../electron/services/recoveryHost');

const CHECKPOINT = 'checkpoint-closure-0001';
const RUN = 'run-closure-0001';
const WAVE = 'wave-closure-0001';
const OPERATION = 'operation-closure-0001';
const PROOF = 'a'.repeat(64);
const HEAD = 'b'.repeat(40);
const REVISION = 'c'.repeat(64);
const CONTRACT = 'd'.repeat(64);

function lifecycleCounts(overrides = {}) {
  return {
    active_tool_calls: 0,
    active_commands: 0,
    starting_commands: 0,
    active_background_operations: 0,
    active_managed_processes: 0,
    foreign_heavy_processes: 0,
    active_agent_lanes: 0,
    threshold_sensitive_stale_candidates: 0,
    owned_codex_sidecar_residues: 0,
    ...overrides
  };
}

function lifecycle(overrides = {}) {
  return {
    schema_version: 1,
    operation_id: OPERATION,
    clean: true,
    code: 'READY',
    reason: 'idle',
    observed_at: '2026-08-25T08:00:01.000Z',
    canonical_lifecycle_observed: true,
    source_checkpoint_verified: true,
    fence_released: true,
    fenced: false,
    fence_operation_id: null,
    counts: lifecycleCounts(),
    unexplained_active_runs: 0,
    unbound_live_resource_residues: 0,
    ...overrides
  };
}

function acceptedReceipt(overrides = {}) {
  return {
    path: 'electron/services/recoveryHost.js',
    state: 'file',
    sha256: 'e'.repeat(64),
    size_bytes: 123,
    receipt_kind: 'task_modified_file',
    run_id: RUN,
    wave_id: WAVE,
    restart_safe: true,
    content_addressed: true,
    ...overrides
  };
}

function postflight(overrides = {}) {
  return {
    schema_version: 2,
    operation_id: OPERATION,
    source_checkpoint_id: CHECKPOINT,
    run_id: RUN,
    wave_id: WAVE,
    component: 'recovery_host',
    old_instance_state: 'RUNNING',
    old_instance_id: 'instance-old-closure-0001',
    new_instance_id: 'instance-new-closure-0001',
    already_current: false,
    expected_revision: REVISION,
    running_revision: REVISION,
    disk_revision: REVISION,
    revision_contract: 'current',
    started_at: '2026-08-25T08:00:00.000Z',
    completed_at: '2026-08-25T08:00:01.000Z',
    postflight_verified: true,
    health_verified: true,
    lifecycle_decision: lifecycle(),
    ...overrides
  };
}

function acceptedCode(overrides = {}) {
  return {
    schema_version: 1,
    source_checkpoint_id: CHECKPOINT,
    run_id: RUN,
    wave_id: WAVE,
    proof_fingerprint: PROOF,
    accepted_head: HEAD,
    source_accepted: true,
    accepted_receipts_complete: true,
    activation_eligible: true,
    eligibility_code: 'ACTIVATABLE',
    affected_components: ['recovery_host'],
    affected_components_valid: true,
    component_receipts_valid: true,
    component_receipts: { recovery_host: [acceptedReceipt()] },
    postflight_receipts: { recovery_host: postflight() },
    components_current: true,
    lifecycle_clean: true,
    lifecycle_decision: lifecycle(),
    ...overrides
  };
}

function zeroTargetAcceptedCode(overrides = {}) {
  return acceptedCode({
    proof_fingerprint: '',
    affected_components: [],
    component_receipts: {},
    postflight_receipts: {},
    components_current: true,
    ...overrides
  });
}

function revisions(overrides = {}) {
  return {
    recovery_host: {
      running_revision: REVISION,
      disk_revision: REVISION,
      update_pending: false,
      ...overrides
    }
  };
}

function liveArgs(overrides = {}) {
  return {
    acceptedCode: acceptedCode(),
    componentRevisions: revisions(),
    connectorContractState: 'UNCHANGED_ACKNOWLEDGED',
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false,
    connectorRediscoveredAt: null,
    connectorCurrentSha256: CONTRACT,
    connectorAcknowledgedSha256: CONTRACT,
    runtimeFullyReady: true,
    runtimeRunning: true,
    tunnelRunning: true,
    observedAt: '2026-08-25T08:00:02.000Z',
    ...overrides
  };
}

test('LIVE_CLOSED requires one exact accepted checkpoint plus canonical accepted and postflight receipts', () => {
  const closure = computeActivationClosure(liveArgs());
  assert.equal(closure.closure_state, 'LIVE_CLOSED');
  assert.equal(closure.component_receipts_valid, true);
  assert.equal(closure.postflight_receipts_valid, true);
  assert.equal(closure.components_current, true);
  assert.equal(closure.connector_contract_current, true);
  assert.equal(closure.release_state, 'NOT_RELEASED');
  assert.equal(closure.production_state, 'NOT_CLAIMED');
});

test('different connector SHA cannot close through the retired compatibility state', () => {
  const closure = computeActivationClosure(liveArgs({
    connectorContractState: 'COMPATIBLE_ACKNOWLEDGED',
    connectorRediscoveredAt: null,
    connectorCurrentSha256: 'b'.repeat(64),
    connectorAcknowledgedSha256: 'a'.repeat(64)
  }));
  assert.equal(closure.connector_contract_current, false);
  assert.equal(closure.closure_state, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(closure.connector_rediscovered_at, null);
  assert.notEqual(closure.connector_current_sha256, closure.connector_acknowledged_sha256);
});

test('manual activation authority maps only the exact eligible Recovery Host closure checkpoint', () => {
  const closure = acceptedCode();
  const hostStatus = {
    auto_activation: { closure_input: closure }
  };
  const sourceCheckpoint = activationSourceCheckpoint(hostStatus, 'recovery_host');
  assert.deepEqual(sourceCheckpoint, {
    checkpoint_id: CHECKPOINT,
    run_id: RUN,
    wave_id: WAVE,
    proof_fingerprint: PROOF,
    git_head: HEAD
  });
  assert.deepEqual(activationSourceCheckpoint(hostStatus), sourceCheckpoint);
  assert.equal(Object.hasOwn(sourceCheckpoint, 'postflight_receipts'), false);
});

test('manual activation authority rejects missing, ineligible, malformed, or noncanonical closure input', () => {
  assert.throws(() => activationSourceCheckpoint({}, 'recovery_host'), {
    code: 'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE'
  });
  const invalidClosures = [
    { schema_version: 99 },
    { source_accepted: false },
    { accepted_receipts_complete: false },
    { component_receipts_valid: false },
    { activation_eligible: false },
    { eligibility_code: 'SOURCE_DRIFT' },
    { affected_components_valid: false },
    { affected_components: ['coding_mcp'] },
    { affected_components: ['recovery_host', 'recovery_host'] },
    { affected_components: ['electron_ui', 'recovery_host'] },
    { affected_components: ['unknown_component'] }
  ];
  for (const overrides of invalidClosures) {
    const closure = acceptedCode(overrides);
    assert.throws(() => activationSourceCheckpoint({ auto_activation: { closure_input: closure } }, 'recovery_host'), {
      code: 'ACTIVATION_SOURCE_CHECKPOINT_NOT_ELIGIBLE'
    });
  }
  for (const overrides of [
    { source_checkpoint_id: ` ${CHECKPOINT}` },
    { run_id: ` ${RUN}` },
    { wave_id: `${WAVE} ` },
    { proof_fingerprint: PROOF.toUpperCase() },
    { accepted_head: HEAD.toUpperCase() }
  ]) {
    const closure = acceptedCode(overrides);
    assert.throws(() => activationSourceCheckpoint({ auto_activation: { closure_input: closure } }, 'recovery_host'), {
      code: 'ACTIVATION_SOURCE_CHECKPOINT_INVALID'
    });
  }
  const postflightCannotRepairSource = acceptedCode({
    component_receipts_valid: false,
    postflight_receipts: { recovery_host: postflight() }
  });
  assert.throws(
    () => activationSourceCheckpoint({ auto_activation: { closure_input: postflightCannotRepairSource } }, 'recovery_host'),
    { code: 'ACTIVATION_SOURCE_CHECKPOINT_NOT_ELIGIBLE' }
  );
});

test('minimal or operation-mismatched postflight cannot close activation', () => {
  const minimal = acceptedCode({
    postflight_receipts: { recovery_host: {
      source_checkpoint_id: CHECKPOINT,
      run_id: RUN,
      wave_id: WAVE,
      component: 'recovery_host',
      expected_revision: REVISION,
      running_revision: REVISION,
      disk_revision: REVISION,
      postflight_verified: true
    } }
  });
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: minimal })).closure_state, 'POSTFLIGHT_RECEIPTS_INVALID');
  const wrongOperation = acceptedCode({
    postflight_receipts: { recovery_host: postflight({ operation_id: 'operation-closure-other' }) }
  });
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: wrongOperation })).closure_state, 'POSTFLIGHT_RECEIPTS_INVALID');
});

test('postflight receipt from another checkpoint cannot close the accepted checkpoint', () => {
  const source = acceptedCode({
    postflight_receipts: { recovery_host: postflight({ source_checkpoint_id: 'checkpoint-closure-other' }) }
  });
  const closure = computeActivationClosure(liveArgs({ acceptedCode: source }));
  assert.equal(closure.postflight_receipts_valid, false);
  assert.equal(closure.closure_state, 'POSTFLIGHT_RECEIPTS_INVALID');
});

test('accepted component receipt provenance and coverage are mandatory', () => {
  const missing = computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ component_receipts: {} }) }));
  assert.equal(missing.component_receipts_valid, false);
  assert.equal(missing.closure_state, 'ACCEPTED_RECEIPTS_INVALID');
  const wrongWave = acceptedCode({ component_receipts: { recovery_host: [acceptedReceipt({ wave_id: 'wave-other-0001' })] } });
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: wrongWave })).closure_state, 'ACCEPTED_RECEIPTS_INVALID');
});

test('running revision drift keeps closure open even when durable postflight was verified', () => {
  const closure = computeActivationClosure(liveArgs({
    componentRevisions: revisions({ running_revision: 'f'.repeat(64), update_pending: true })
  }));
  assert.equal(closure.components_current, false);
  assert.equal(closure.closure_state, 'COMPONENTS_NOT_CURRENT');
});

test('Recovery Host legacy revision bridge closes when verified postflight matches live running and disk revision', () => {
  const source = acceptedCode({
    postflight_receipts: {
      recovery_host: postflight({
        expected_revision: '9'.repeat(64),
        running_revision: REVISION,
        disk_revision: REVISION,
        revision_contract: 'recovery_host_legacy_v1_without_device_identity'
      })
    }
  });
  const closure = computeActivationClosure(liveArgs({ acceptedCode: source }));
  assert.equal(closure.postflight_receipts_valid, true);
  assert.equal(closure.components_current, true);
  assert.equal(closure.closure_state, 'LIVE_CLOSED');
});

test('Recovery Host legacy revision bridge rejects unknown contracts and live revision drift', () => {
  const legacy = postflight({
    expected_revision: '9'.repeat(64),
    running_revision: REVISION,
    disk_revision: REVISION,
    revision_contract: 'recovery_host_legacy_v1_without_device_identity'
  });
  const unknownContract = computeActivationClosure(liveArgs({
    acceptedCode: acceptedCode({
      postflight_receipts: { recovery_host: { ...legacy, revision_contract: 'tampered-contract' } }
    })
  }));
  assert.equal(unknownContract.closure_state, 'POSTFLIGHT_RECEIPTS_INVALID');

  const liveDrift = computeActivationClosure(liveArgs({
    acceptedCode: acceptedCode({ postflight_receipts: { recovery_host: legacy } }),
    componentRevisions: revisions({
      running_revision: '8'.repeat(64),
      disk_revision: '8'.repeat(64)
    })
  }));
  assert.equal(liveDrift.postflight_receipts_valid, true);
  assert.equal(liveDrift.components_current, false);
  assert.equal(liveDrift.closure_state, 'COMPONENTS_NOT_CURRENT');
});

test('canonical empty proof closes only a valid zero-target checkpoint', () => {
  const closure = computeActivationClosure(liveArgs({ acceptedCode: zeroTargetAcceptedCode() }));
  assert.equal(closure.checkpoint_identity_valid, true);
  assert.deepEqual(closure.affected_components, []);
  assert.equal(closure.lifecycle_clean, true);
  assert.equal(closure.closure_state, 'LIVE_CLOSED');

  const mutationBearing = computeActivationClosure(liveArgs({
    acceptedCode: acceptedCode({ proof_fingerprint: '' })
  }));
  assert.equal(mutationBearing.checkpoint_identity_valid, false);
  assert.equal(mutationBearing.closure_state, 'CHECKPOINT_IDENTITY_INVALID');
});

test('unchanged acknowledgement needs matching SHA and no refresh, while changed acknowledgement needs timestamp', () => {
  assert.equal(computeActivationClosure(liveArgs()).closure_state, 'LIVE_CLOSED');
  assert.equal(computeActivationClosure(liveArgs({ connectorRefreshRequired: true })).closure_state, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(computeActivationClosure(liveArgs({ connectorAcknowledgementPending: true })).closure_state, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(computeActivationClosure(liveArgs({ connectorAcknowledgedSha256: 'f'.repeat(64) })).closure_state, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(computeActivationClosure(liveArgs({
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    connectorRediscoveredAt: null
  })).closure_state, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(computeActivationClosure(liveArgs({
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    connectorRediscoveredAt: '2026-08-25T08:00:00.000Z'
  })).closure_state, 'LIVE_CLOSED');
  assert.equal(computeActivationClosure(liveArgs({
    connectorContractState: 'CURRENT_COMPATIBLE_ACKNOWLEDGED',
    connectorRediscoveredAt: null
  })).closure_state, 'LIVE_CLOSED');
});

test('unknown, duplicate, or unordered affected components fail closed', () => {
  for (const affected of [
    ['recovery_host', 'unknown_component'],
    ['recovery_host', 'recovery_host'],
    ['electron_ui', 'recovery_host'],
    [' recovery_host']
  ]) {
    const closure = computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ affected_components: affected }) }));
    assert.equal(closure.affected_components_valid, false);
    assert.equal(closure.closure_state, 'AFFECTED_COMPONENTS_INVALID');
  }
});

test('closure checkpoint identity is strict and is never normalized into authority', () => {
  for (const overrides of [
    { source_checkpoint_id: ` ${CHECKPOINT}` },
    { run_id: `${RUN} ` },
    { wave_id: ` ${WAVE}` },
    { proof_fingerprint: PROOF.toUpperCase() },
    { accepted_head: HEAD.toUpperCase() }
  ]) {
    const closure = computeActivationClosure(liveArgs({ acceptedCode: acceptedCode(overrides) }));
    assert.equal(closure.checkpoint_identity_valid, false);
    assert.equal(closure.closure_state, 'CHECKPOINT_IDENTITY_INVALID');
  }
});

test('postflight receipts must use the checkpoint-keyed component object contract', () => {
  const source = acceptedCode({ postflight_receipts: [postflight()] });
  const closure = computeActivationClosure(liveArgs({ acceptedCode: source }));
  assert.equal(closure.postflight_receipts_valid, false);
  assert.equal(closure.closure_state, 'POSTFLIGHT_RECEIPTS_INVALID');
});

test('schema, receipt, eligibility, lifecycle, source-current and readiness gates remain separate', () => {
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ schema_version: 99 }) })).closure_state, 'CLOSURE_SCHEMA_UNSUPPORTED');
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ accepted_receipts_complete: false }) })).closure_state, 'RECEIPT_INCOMPLETE');
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ activation_eligible: false, eligibility_code: 'SOURCE_DRIFT' }) })).closure_state, 'SOURCE_DRIFT');
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ lifecycle_clean: false }) })).closure_state, 'LIFECYCLE_NOT_QUIESCENT');
  assert.equal(computeActivationClosure(liveArgs({ acceptedCode: acceptedCode({ components_current: false }) })).closure_state, 'COMPONENTS_NOT_CURRENT');
  assert.equal(computeActivationClosure(liveArgs({ runtimeFullyReady: true, runtimeRunning: false, tunnelRunning: true })).closure_state, 'RUNTIME_NOT_READY');
  assert.equal(computeActivationClosure(liveArgs({ runtimeFullyReady: true, runtimeRunning: true, tunnelRunning: false })).closure_state, 'RUNTIME_NOT_READY');
});

test('declared clean lifecycle cannot hide active work, unexplained runs, residue, or an incomplete census', () => {
  for (const lifecycleOverride of [
    { counts: lifecycleCounts({ active_commands: 4 }) },
    { counts: lifecycleCounts({ active_agent_lanes: 1 }) },
    { unexplained_active_runs: 3 },
    { unbound_live_resource_residues: 2 },
    { counts: {} }
  ]) {
    const contradictoryLifecycle = lifecycle(lifecycleOverride);
    const source = acceptedCode({
      lifecycle_decision: contradictoryLifecycle,
      postflight_receipts: {
        recovery_host: postflight({ lifecycle_decision: contradictoryLifecycle })
      }
    });
    const closure = computeActivationClosure(liveArgs({ acceptedCode: source }));
    assert.notEqual(closure.closure_state, 'LIVE_CLOSED');
    assert.equal(closure.lifecycle_clean, false);
  }
});

test('Recovery Host projection uses fresh component revision and contradictory runtime status cannot close', () => {
  const source = acceptedCode();
  const runtime = {
    status: {
      runtimeRunning: true,
      tunnelRunning: true,
      fullyReady: true,
      connectorContractState: 'UNCHANGED_ACKNOWLEDGED',
      connectorRefreshRequired: false,
      connectorAcknowledgementPending: false,
      connectorRediscoveredAt: null,
      connectorContractAcknowledgedSha256: CONTRACT,
      toolContract: { sha256: CONTRACT },
      codeRevision: { codingMcp: { running_revision: 'f'.repeat(64), disk_revision: 'f'.repeat(64), update_pending: false } }
    }
  };
  const closure = activationClosureProjection({
    autoActivation: { closure_input: source },
    recoveryHostRevision: revisions().recovery_host,
    codingMcpRevision: {},
    runtime
  });
  assert.equal(closure.closure_state, 'LIVE_CLOSED');
  const contradictory = activationClosureProjection({
    autoActivation: { closure_input: source },
    recoveryHostRevision: revisions().recovery_host,
    runtime: { status: { ...runtime.status, runtimeRunning: false } }
  });
  assert.equal(contradictory.closure_state, 'RUNTIME_NOT_READY');

  const host = {
    hostStatus: () => ({
      auto_activation: { closure_input: source },
      code_revision: revisions().recovery_host,
      electron_ui_revision: {},
      recovery_plane: null
    }),
    settings: { load: () => ({}) },
    deviceIdentity: { device_id: 'device-closure-0001', display_name: 'Closure device' },
    deviceInstanceId: 'device-instance-closure-0001',
    orchestrator: { codingMcpRevisionStatus: () => ({}) },
    bootstrapBlocksAdmission: () => false,
    running: true
  };
  const decorated = RecoveryHost.prototype.decorate.call(host, runtime);
  assert.equal(decorated.status.activationClosure.closure_state, 'LIVE_CLOSED');
  assert.equal(decorated.activationClosure.closure_state, 'LIVE_CLOSED');
  assert.equal(decorated.recoveryHost.activation_closure.closure_state, 'LIVE_CLOSED');
});
