const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');

function fixture(t, options = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-activation-epoch-'));
  const dataRoot = path.join(root, 'data');
  fs.mkdirSync(dataRoot, { recursive: true });
  const paths = options.paths || { dataRoot: () => dataRoot };
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return { root, dataRoot, paths, file: path.join(dataRoot, 'activation-epoch.json') };
}

function operation(number) {
  return `operation-epoch-${String(number).padStart(8, '0')}`;
}

function epoch(number) {
  return `activation-epoch-${String(number).padStart(4, '0')}`;
}

function verificationFor(epochId, finalCensus = {}) {
  return {
    verified: true,
    activation_epoch_id: epochId,
    final_census: { pass: true, activation_epoch_id: epochId, ...finalCensus }
  };
}

test('activation epoch is durable, closes admission, and never mutates the ledger', (t) => {
  const { paths, file, root } = fixture(t);
  const ledger = path.join(root, 'ledger.sqlite3');
  fs.writeFileSync(ledger, 'canonical-ledger-sentinel', 'utf8');
  let clock = 1_700_000_000_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({
    activation_epoch_id: epoch(1),
    operation_id: operation(1),
    mode: 'full_clean_activation',
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    source_checkpoint: { checkpoint_id: 'checkpoint-epoch-0001', git_head: 'a'.repeat(40) },
    ledger_snapshot: { logical_sha256: 'b'.repeat(64), event_head: 12 },
    component_revisions: { coding_mcp: 'c'.repeat(64) },
    metadata: { reason: 'operator_restart' }
  });

  assert.equal(created.state, 'PREPARING');
  assert.equal(created.admission_state, 'CLOSED');
  assert.equal(store.admissionClosed(), true);
  assert.equal(fs.existsSync(file), true);
  assert.equal(fs.readFileSync(ledger, 'utf8'), 'canonical-ledger-sentinel');

  const reloaded = new ActivationEpochStore({ paths, now: () => clock++ });
  assert.deepEqual(reloaded.current(), created);
  assert.deepEqual(reloaded.load(created.activation_epoch_id), created);
  assert.equal(reloaded.history().length, 0);
});

test('epoch updates are forward-only and ready uses the durable two-phase commit', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_100_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(2), operation_id: operation(2) });

  const stopping = store.update(created.activation_epoch_id, { state: 'STOPPING', reason: 'old-process-stop' });
  assert.equal(stopping.state, 'STOPPING');
  assert.equal(stopping.admission_state, 'CLOSED');
  assert.throws(
    () => store.update(created.activation_epoch_id, { state: 'PREPARING' }),
    { code: 'ACTIVATION_EPOCH_STATE_REGRESSION' }
  );
  assert.throws(
    () => store.ready(created.activation_epoch_id, verificationFor(created.activation_epoch_id)),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID' }
  );
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id, {
    all_components_same_epoch: true,
    connector_acknowledged: true
  }));
  assert.equal(committed.state, 'READY_COMMITTED');
  assert.equal(committed.admission_state, 'CLOSED');
  assert.match(committed.ready_commit_digest, /^[0-9a-f]{64}$/);
  const ready = store.ready(created.activation_epoch_id, committed.ready_commit_digest);
  assert.equal(ready.state, 'READY');
  assert.equal(ready.admission_state, 'OPEN');
  assert.equal(store.admissionClosed(), false);
  assert.equal(store.ready(created.activation_epoch_id, committed.ready_commit_digest).state, 'READY');
  // Terminal records are immutable and must not consult a regressed injected
  // clock before returning their terminal/idempotent result.
  clock = 0;
  assert.equal(store.update(created.activation_epoch_id, { metadata: { ignored: true } }).state, 'READY');
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)),
    { code: 'ACTIVATION_EPOCH_TERMINAL' }
  );
  assert.throws(
    () => store.update(created.activation_epoch_id, { state: 'FAILED' }),
    { code: 'ACTIVATION_EPOCH_TERMINAL' }
  );
});

test('a central executor epoch requires its authenticated route proof instead of a direct connector acknowledgement', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_150_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({
    activation_epoch_id: epoch(201),
    operation_id: operation(201),
    metadata: {
      execution_role: 'central_executor',
      component_profile: 'central_executor_v1'
    }
  });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });

  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id, {
      connector_acknowledged: true
    })),
    { code: 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED' }
  );

  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id, {
    all_components_same_epoch: true,
    epoch_matches: true,
    workspace_matches: true,
    device_matches: true,
    revision_matches: true,
    process_identity_verified: true,
    ui_verified: true,
    recovery_plane_verified: true,
    central_route_verified: true,
    central_connected: true,
    authority_ready: true
  }));
  assert.equal(committed.state, 'READY_COMMITTED');
  assert.equal(Object.hasOwn(committed.verification.final_census, 'connector_acknowledged'), false);
});

test('a central READY proof rejects an incomplete primary runtime snapshot', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_175_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({
    activation_epoch_id: epoch(202),
    operation_id: operation(202),
    metadata: {
      execution_role: 'central_executor',
      component_profile: 'central_executor_v1'
    }
  });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });

  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id, {
      all_components_same_epoch: true,
      epoch_matches: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      process_identity_verified: true,
      ui_verified: true,
      recovery_plane_verified: true,
      central_route_verified: true,
      central_connected: true,
      authority_ready: true,
      runtime: {
        mcpRunning: false,
        nativeAlive: false,
        componentsReady: false,
        fullyReady: false,
        updateIncomplete: true
      }
    })),
    { code: 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED' }
  );
  assert.equal(store.current().state, 'VERIFYING');
  assert.equal(store.current().admission_state, 'CLOSED');
});

test('a central pre-admission READY_COMMITTED proof permits admission-derived readiness flags', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_180_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({
    activation_epoch_id: epoch(203),
    operation_id: operation(203),
    metadata: {
      execution_role: 'central_executor',
      component_profile: 'central_executor_v1'
    }
  });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });

  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id, {
    all_components_same_epoch: true,
    epoch_matches: true,
    workspace_matches: true,
    device_matches: true,
    revision_matches: true,
    process_identity_verified: true,
    ui_verified: true,
    recovery_plane_verified: true,
    central_route_verified: true,
    central_connected: true,
    authority_ready: true,
    runtime: {
      mcpRunning: true,
      nativeAlive: true,
      componentsReady: false,
      fullyReady: false,
      updateIncomplete: false,
      tunnelRunning: false
    }
  }));

  assert.equal(committed.state, 'READY_COMMITTED');
  assert.equal(committed.admission_state, 'CLOSED');
});

test('failure is terminal, remains fail-closed, and replay is idempotent', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_200_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(3), operation_id: operation(3) });
  const failed = store.fail(created.activation_epoch_id, {
    code: 'COMPONENT_VERIFY_FAILED',
    message: 'Coding MCP reported an old epoch.',
    details: { component: 'coding_mcp' }
  });
  assert.equal(failed.state, 'FAILED');
  assert.equal(failed.admission_state, 'CLOSED');
  assert.equal(failed.error.code, 'COMPONENT_VERIFY_FAILED');
  assert.equal(store.fail(created.activation_epoch_id, 'retry is not allowed').state, 'FAILED');
  clock = 0;
  assert.equal(store.update(created.activation_epoch_id, { metadata: { ignored: true } }).state, 'FAILED');
  assert.throws(() => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)), { code: 'ACTIVATION_EPOCH_TERMINAL' });
  assert.throws(() => store.ready(created.activation_epoch_id, 'a'.repeat(64)), { code: 'ACTIVATION_EPOCH_TERMINAL' });
});

test('terminal epochs roll into bounded history and duplicate identities are rejected', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_300_000;
  const store = new ActivationEpochStore({ paths, maxHistory: 2, now: () => clock++ });
  const first = store.create({ activation_epoch_id: epoch(10), operation_id: operation(10) });
  assert.deepEqual(store.create({ activation_epoch_id: epoch(10), operation_id: operation(10) }), first);
  assert.throws(
    () => store.create({ activation_epoch_id: epoch(10), operation_id: operation(11), metadata: { changed: true } }),
    { code: 'ACTIVATION_EPOCH_ID_CONFLICT' }
  );
  store.fail(first.activation_epoch_id, { code: 'FAILED_1', message: 'one' });

  for (const number of [11, 12, 13]) {
    const current = store.create({ activation_epoch_id: epoch(number), operation_id: operation(number) });
    store.fail(current.activation_epoch_id, { code: `FAILED_${number}`, message: String(number) });
  }
  assert.equal(store.history().length, 2);
  assert.deepEqual(store.history().map((item) => item.activation_epoch_id), [epoch(12), epoch(11)]);
  assert.throws(
    () => store.update(epoch(11), { state: 'VERIFYING' }),
    { code: 'ACTIVATION_EPOCH_NOT_CURRENT' }
  );
});

test('store corruption fails closed and atomic writes preserve the prior valid snapshot', (t) => {
  const { paths, file } = fixture(t);
  let clock = 1_700_000_400_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(20), operation_id: operation(20) });
  store.update(created.activation_epoch_id, { state: 'FROZEN' });
  const backup = `${file}.bak`;
  assert.equal(fs.existsSync(backup), true);
  const previous = JSON.parse(fs.readFileSync(backup, 'utf8'));
  assert.equal(previous.current.activation_epoch_id, created.activation_epoch_id);
  assert.equal(previous.current.state, 'PREPARING');

  fs.rmSync(backup, { force: true });
  fs.writeFileSync(file, '{ definitely-not-json', 'utf8');
  assert.throws(() => store.load(), { code: 'ACTIVATION_EPOCH_STORE_INVALID' });
});

test('custom activationEpochFile path is honored without requiring RuntimePaths changes', (t) => {
  const { dataRoot } = fixture(t);
  const customFile = path.join(dataRoot, 'nested', 'epoch-state.json');
  const paths = { dataRoot: () => dataRoot, activationEpochFile: () => customFile };
  const store = new ActivationEpochStore({ paths, now: () => 1_700_000_500_000 });
  store.create({ activation_epoch_id: epoch(30), operation_id: operation(30) });
  assert.equal(fs.existsSync(customFile), true);
  assert.equal(fs.existsSync(path.join(dataRoot, 'activation-epoch.json')), false);
});

test('a corrupt primary never falls back to an older READY backup', (t) => {
  const { paths, file } = fixture(t);
  let clock = 1_700_000_600_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(40), operation_id: operation(40) });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  // The backup is valid but intentionally represents an older snapshot.  A
  // malformed primary must not silently resurrect it as an OPEN authority.
  const backup = `${file}.bak`;
  assert.equal(fs.existsSync(backup), true);
  fs.writeFileSync(file, '{not-json', 'utf8');
  assert.throws(() => new ActivationEpochStore({ paths }).current(), { code: 'ACTIVATION_EPOCH_STORE_INVALID' });
});

test('create boundary durably expires the current active epoch before admitting another', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_700_000;
  const expiry = clock + 5;
  const store = new ActivationEpochStore({ paths, now: () => clock });
  const created = store.create({
    activation_epoch_id: epoch(41),
    operation_id: operation(41),
    owner_instance_id: 'owner-epoch-00000001',
    owner_pid: process.pid,
    expires_at_unix_ms: expiry
  });
  const reloaded = new ActivationEpochStore({ paths, now: () => clock });
  assert.equal(reloaded.current().owner_instance_id, 'owner-epoch-00000001');
  assert.equal(reloaded.current().owner_pid, process.pid);
  assert.equal(reloaded.current().expires_at_unix_ms, expiry);
  assert.equal(reloaded.isStale(created.activation_epoch_id, expiry - 1), false);
  assert.equal(reloaded.isStale(created.activation_epoch_id, expiry), true);
  clock = expiry;
  assert.throws(
    () => reloaded.create({ activation_epoch_id: epoch(42), operation_id: operation(42) }),
    { code: 'ACTIVATION_REQUEST_EXPIRED' }
  );
  const failed = reloaded.current();
  assert.equal(failed.activation_epoch_id, created.activation_epoch_id);
  assert.equal(failed.state, 'FAILED');
  assert.equal(failed.admission_state, 'CLOSED');
  assert.equal(failed.error.code, 'ACTIVATION_REQUEST_EXPIRED');
});

test('update expiry is durable and late proof cannot resurrect the epoch', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_750_000;
  const expiry = clock + 10;
  const store = new ActivationEpochStore({ paths, now: () => clock });
  const created = store.create({ activation_epoch_id: epoch(421), operation_id: operation(421), expires_at_unix_ms: expiry });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  clock = expiry;
  assert.throws(() => store.update(created.activation_epoch_id, { state: 'VERIFYING' }), { code: 'ACTIVATION_REQUEST_EXPIRED' });
  assert.equal(store.current().state, 'FAILED');
  assert.equal(store.current().admission_state, 'CLOSED');
  assert.equal(store.current().error.code, 'ACTIVATION_REQUEST_EXPIRED');
  assert.equal(store.update(created.activation_epoch_id, { verification: verificationFor(created.activation_epoch_id) }).state, 'FAILED');
  assert.throws(() => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)), { code: 'ACTIVATION_EPOCH_TERMINAL' });
  assert.equal(store.current().state, 'FAILED');
});

test('commitReady expires exact VERIFYING durably at the deadline', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_760_000;
  const expiry = clock + 10;
  const store = new ActivationEpochStore({ paths, now: () => clock });
  const created = store.create({ activation_epoch_id: epoch(422), operation_id: operation(422), expires_at_unix_ms: expiry });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  clock = expiry;
  assert.throws(() => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)), { code: 'ACTIVATION_REQUEST_EXPIRED' });
  assert.equal(store.current().state, 'FAILED');
  assert.equal(store.current().error.code, 'ACTIVATION_REQUEST_EXPIRED');
});

test('ready expires a durable READY_COMMITTED epoch and keeps admission closed', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_770_000;
  const expiry = clock + 10;
  const store = new ActivationEpochStore({ paths, now: () => clock });
  const created = store.create({ activation_epoch_id: epoch(423), operation_id: operation(423), expires_at_unix_ms: expiry });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id));
  clock = expiry;
  assert.throws(() => store.ready(created.activation_epoch_id, committed.ready_commit_digest), { code: 'ACTIVATION_REQUEST_EXPIRED' });
  assert.equal(store.current().state, 'FAILED');
  assert.equal(store.current().admission_state, 'CLOSED');
  assert.equal(store.current().error.code, 'ACTIVATION_REQUEST_EXPIRED');
});

test('creation fingerprint binds revision and identity evidence, not only operation metadata', (t) => {
  const { paths } = fixture(t);
  const store = new ActivationEpochStore({ paths, now: () => 1_700_000_800_000 });
  store.create({
    activation_epoch_id: epoch(43),
    operation_id: operation(43),
    component_revisions: { coding_mcp: 'a'.repeat(64) },
    component_evidence: { coding_mcp: { process_instance_id: 'old-process-00000001' } }
  });
  assert.throws(
    () => store.create({
      activation_epoch_id: epoch(43),
      operation_id: operation(43),
      component_revisions: { coding_mcp: 'b'.repeat(64) },
      component_evidence: { coding_mcp: { process_instance_id: 'old-process-00000002' } }
    }),
    { code: 'ACTIVATION_EPOCH_ID_CONFLICT' }
  );
});

test('commitReady requires exact VERIFYING, durable STOPPING, and a bound final census', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_900_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(44), operation_id: operation(44) });
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_STATE_INVALID' }
  );
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_STATE_INVALID' }
  );
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, {
      verified: true,
      activation_epoch_id: created.activation_epoch_id
    }),
    { code: 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED' }
  );
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, {
      verified: true,
      activation_epoch_id: created.activation_epoch_id,
      final_census: { pass: true, activation_epoch_id: epoch(45) }
    }),
    { code: 'ACTIVATION_EPOCH_ID_MISMATCH' }
  );
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id));
  const ready = store.ready(created.activation_epoch_id, committed.ready_commit_digest);
  assert.equal(ready.state, 'READY');
  assert.equal(ready.admission_state, 'OPEN');
  assert.equal(ready.verification.verified_at !== undefined, true);
});

test('commitReady refuses a direct VERIFYING jump without durable STOPPING evidence', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_950_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(45), operation_id: operation(45) });
  store.update(created.activation_epoch_id, { state: 'VERIFYING', reason: 'skipped-stop' });
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id)),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_STATE_INVALID' }
  );
});

test('READY_COMMITTED requires commitReady and exact commit replay is idempotent', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_955_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(451), operation_id: operation(451) });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  assert.throws(
    () => store.update(created.activation_epoch_id, { state: 'READY_COMMITTED' }),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_REQUIRED' }
  );
  const proof = verificationFor(created.activation_epoch_id);
  const committed = store.commitReady(created.activation_epoch_id, proof);
  assert.deepEqual(store.commitReady(created.activation_epoch_id, proof), committed);
  assert.throws(
    () => store.commitReady(created.activation_epoch_id, { ...proof, proof_variant: 'different' }),
    { code: 'ACTIVATION_EPOCH_READY_COMMIT_CONFLICT' }
  );
});

test('ready is digest-only, canonical, exact-match, and replay-safe', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_957_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(452), operation_id: operation(452) });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id));
  const mismatch = `${committed.ready_commit_digest[0] === '0' ? '1' : '0'}${committed.ready_commit_digest.slice(1)}`;
  assert.throws(() => store.ready(created.activation_epoch_id), { code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID' });
  assert.throws(() => store.ready(created.activation_epoch_id, verificationFor(created.activation_epoch_id)), { code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID' });
  assert.throws(() => store.ready(created.activation_epoch_id, 'A'.repeat(64)), { code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID' });
  assert.throws(() => store.ready(created.activation_epoch_id, 'abc'), { code: 'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID' });
  assert.throws(() => store.ready(created.activation_epoch_id, mismatch), { code: 'ACTIVATION_EPOCH_READY_COMMIT_CONFLICT' });
  const ready = store.ready(created.activation_epoch_id, committed.ready_commit_digest);
  assert.equal(ready.state, 'READY');
  assert.deepEqual(store.ready(created.activation_epoch_id, committed.ready_commit_digest), ready);
  assert.throws(() => store.ready(created.activation_epoch_id, mismatch), { code: 'ACTIVATION_EPOCH_READY_COMMIT_CONFLICT' });
});

test('a semantically corrupt backup blocks an otherwise readable primary', (t) => {
  const { paths, file } = fixture(t);
  const store = new ActivationEpochStore({ paths, now: () => 1_700_000_960_000 });
  store.create({ activation_epoch_id: epoch(48), operation_id: operation(48) });
  // Keep JSON syntax valid but violate the durable snapshot contract.  The
  // backup is evidence, not an alternate authority, so it must not be ignored.
  fs.writeFileSync(`${file}.bak`, JSON.stringify({ version: 1, current: {}, history: [] }), 'utf8');
  assert.throws(() => store.current(), { code: 'ACTIVATION_EPOCH_STORE_INVALID' });
});

test('transition compaction preserves STOPPING evidence for long activations', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_970_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(49), operation_id: operation(49) });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  for (let index = 0; index < 70; index += 1) {
    store.update(created.activation_epoch_id, { reason: `checkpoint-${index}` });
  }
  const current = store.current();
  assert.equal(current.transitions.some((transition) => transition.state === 'STOPPING'), true);
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id));
  const ready = store.ready(created.activation_epoch_id, committed.ready_commit_digest);
  assert.equal(ready.state, 'READY');
});

test('record normalization binds ready commit digest to canonical proof and permits legacy READY without it', (t) => {
  const bound = fixture(t);
  let clock = 1_700_000_975_000;
  const store = new ActivationEpochStore({ paths: bound.paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(50), operation_id: operation(50) });
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  store.update(created.activation_epoch_id, { state: 'VERIFYING' });
  const committed = store.commitReady(created.activation_epoch_id, verificationFor(created.activation_epoch_id));
  store.ready(created.activation_epoch_id, committed.ready_commit_digest);
  const tampered = JSON.parse(fs.readFileSync(bound.file, 'utf8'));
  tampered.current.verification.final_census.tampered = true;
  fs.writeFileSync(bound.file, JSON.stringify(tampered), 'utf8');
  assert.throws(() => store.current(), { code: 'ACTIVATION_EPOCH_STORE_INVALID' });

  const legacy = fixture(t);
  clock = 1_700_000_976_000;
  const legacyStore = new ActivationEpochStore({ paths: legacy.paths, now: () => clock++ });
  const legacyCreated = legacyStore.create({ activation_epoch_id: epoch(51), operation_id: operation(51) });
  legacyStore.update(legacyCreated.activation_epoch_id, { state: 'STOPPING' });
  legacyStore.update(legacyCreated.activation_epoch_id, { state: 'VERIFYING' });
  const legacyCommit = legacyStore.commitReady(legacyCreated.activation_epoch_id, verificationFor(legacyCreated.activation_epoch_id));
  legacyStore.ready(legacyCreated.activation_epoch_id, legacyCommit.ready_commit_digest);
  const snapshot = JSON.parse(fs.readFileSync(legacy.file, 'utf8'));
  snapshot.current.ready_commit_digest = null;
  snapshot.current.transitions = snapshot.current.transitions.filter((transition) => transition.state !== 'READY_COMMITTED');
  fs.writeFileSync(legacy.file, JSON.stringify(snapshot), 'utf8');
  const loaded = new ActivationEpochStore({ paths: legacy.paths, now: () => clock++ }).current();
  assert.equal(loaded.state, 'READY');
  assert.equal(loaded.ready_commit_digest, null);
});

test('mutating operations use a bounded interprocess lock and expose CAS conflicts', (t) => {
  const { paths, file } = fixture(t);
  const lockFile = `${file}.lock`;
  fs.mkdirSync(path.dirname(lockFile), { recursive: true });
  fs.writeFileSync(lockFile, JSON.stringify({ version: 1, pid: process.pid, token: 'held-by-test', acquired_at_unix_ms: Date.now() }), 'utf8');
  const store = new ActivationEpochStore({ paths, lockTimeoutMs: 40 });
  assert.throws(() => store.create({ activation_epoch_id: epoch(46), operation_id: operation(46) }), { code: 'ACTIVATION_EPOCH_LOCK_TIMEOUT' });
  fs.rmSync(lockFile, { force: true });
  const created = store.create({ activation_epoch_id: epoch(47), operation_id: operation(47) });
  assert.throws(() => store.update(created.activation_epoch_id, { state: 'STOPPING', expected_revision: created.revision - 1 }), { code: 'ACTIVATION_EPOCH_CONFLICT' });
});
