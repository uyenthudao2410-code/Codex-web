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

test('epoch updates are forward-only and ready requires explicit final verification', (t) => {
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
    () => store.ready(created.activation_epoch_id, { activation_epoch_id: created.activation_epoch_id }),
    { code: 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED' }
  );

  const ready = store.ready(created.activation_epoch_id, {
    verified: true,
    activation_epoch_id: created.activation_epoch_id,
    final_census: { all_components_same_epoch: true, connector_acknowledged: true }
  });
  assert.equal(ready.state, 'READY');
  assert.equal(ready.admission_state, 'OPEN');
  assert.equal(store.admissionClosed(), false);
  assert.equal(store.ready(created.activation_epoch_id, { verified: false }).state, 'READY');
  assert.throws(
    () => store.update(created.activation_epoch_id, { state: 'FAILED' }),
    { code: 'ACTIVATION_EPOCH_TERMINAL' }
  );
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
  assert.throws(() => store.ready(created.activation_epoch_id, { verified: true }), { code: 'ACTIVATION_EPOCH_TERMINAL' });
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

test('expiry and owner evidence are durable and stale active epochs remain blocking', (t) => {
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
    (error) => error.code === 'ACTIVATION_EPOCH_ACTIVE' && error.details.stale === true
  );
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

test('READY requires a bound final census and a completed stop phase', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_900_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(44), operation_id: operation(44) });
  assert.throws(
    () => store.ready(created.activation_epoch_id, { verified: true, activation_epoch_id: created.activation_epoch_id }),
    { code: 'ACTIVATION_EPOCH_READY_STATE_INVALID' }
  );
  store.update(created.activation_epoch_id, { state: 'STOPPING' });
  assert.throws(
    () => store.ready(created.activation_epoch_id, { verified: true, activation_epoch_id: created.activation_epoch_id }),
    { code: 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED' }
  );
  assert.throws(
    () => store.ready(created.activation_epoch_id, {
      verified: true,
      activation_epoch_id: created.activation_epoch_id,
      final_census: { pass: true, activation_epoch_id: epoch(45) }
    }),
    { code: 'ACTIVATION_EPOCH_ID_MISMATCH' }
  );
  const ready = store.ready(created.activation_epoch_id, {
    verified: true,
    activation_epoch_id: created.activation_epoch_id,
    final_census: { pass: true, activation_epoch_id: created.activation_epoch_id }
  });
  assert.equal(ready.state, 'READY');
  assert.equal(ready.admission_state, 'OPEN');
  assert.equal(ready.verification.verified_at !== undefined, true);
});

test('READY refuses a direct VERIFYING jump without durable STOPPING evidence', (t) => {
  const { paths } = fixture(t);
  let clock = 1_700_000_950_000;
  const store = new ActivationEpochStore({ paths, now: () => clock++ });
  const created = store.create({ activation_epoch_id: epoch(45), operation_id: operation(45) });
  store.update(created.activation_epoch_id, { state: 'VERIFYING', reason: 'skipped-stop' });
  assert.throws(
    () => store.ready(created.activation_epoch_id, {
      verified: true,
      activation_epoch_id: created.activation_epoch_id,
      final_census: { pass: true, activation_epoch_id: created.activation_epoch_id }
    }),
    { code: 'ACTIVATION_EPOCH_READY_STATE_INVALID' }
  );
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
  const ready = store.ready(created.activation_epoch_id, {
    verified: true,
    activation_epoch_id: created.activation_epoch_id,
    final_census: { pass: true, activation_epoch_id: created.activation_epoch_id }
  });
  assert.equal(ready.state, 'READY');
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
