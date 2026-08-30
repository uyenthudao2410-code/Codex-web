'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { Readable } = require('node:stream');
const { createRuntimePaths } = require('../electron/services/runtimePaths');

const {
  CHECKPOINT_FIELDS,
  DEFERRED_KIND,
  DEFERRED_DEFAULT_TTL_MS,
  DEFERRED_MAX_TTL_MS,
  DEFERRED_ACTIVATION_TTL_MS,
  DEFERRED_PREFLIGHT_RETRY_MS,
  parseCheckpoint,
  parseArgs,
  expectedComponentRevision,
  buildRequest,
  summarizeAuthority,
  readStdinJson,
  deferredOperationId,
  deferredRequestPath,
  deferredResultPath,
  deferredParentMarkerPath,
  deferredWorkerLockPath,
  buildDeferredEnvelope,
  writeDeferredRequest,
  writeDeferredResult,
  readDeferredEnvelope,
  readDeferredResult,
  readDeferredStatus,
  claimDeferredWorker,
  releaseDeferredWorkerClaim,
  waitForDeferredParentExit,
  deferredWorkerEnvironment,
  spawnDeferredWorker,
  runDeferredWorker,
  deferExecute,
  parseDeferredWorkerArgs,
  run,
  readAuthority,
  connectorAcknowledgementEligible,
  waitForReplacementReady
} = require('../scripts/full-clean-activation');

const checkpoint = {
  checkpoint_id: '653532dc7e624fb8acc212bc846162f6',
  run_id: '8b8e5b92bf814969bbd21f1577056275',
  wave_id: 'a497621109d94f67b3216c8b0c74b1cd',
  proof_fingerprint: 'd5d412b62bef86f6b3dba820127ebc5d994b2a469ac673a9d43a35fbb092e049',
  git_head: '898d57454f9a5113d8aa3f56d1650e4b3e0d6924'
};

test('full-clean command requires exactly the canonical checkpoint fields', () => {
  assert.deepEqual(parseCheckpoint(JSON.stringify(checkpoint)), checkpoint);
  assert.deepEqual(CHECKPOINT_FIELDS, [
    'checkpoint_id', 'run_id', 'wave_id', 'proof_fingerprint', 'git_head'
  ]);
  assert.throws(
    () => parseCheckpoint(JSON.stringify({ ...checkpoint, extra: true })),
    { code: 'ACTIVATION_SOURCE_CHECKPOINT_INVALID' }
  );
  assert.throws(
    () => parseCheckpoint(JSON.stringify({ ...checkpoint, proof_fingerprint: 'not-a-sha' })),
    { code: 'ACTIVATION_SOURCE_CHECKPOINT_INVALID' }
  );
});

test('full-clean command is explicit and preserves ACCEPTING state', () => {
  assert.deepEqual(parseArgs(['--status']), { execute: false, preflightOnly: true, statusOnly: true });
  assert.deepEqual(parseArgs(['--preflight']), { execute: false, preflightOnly: true, statusOnly: false });
  assert.deepEqual(parseArgs(['--execute']), { execute: true, preflightOnly: false, statusOnly: false });
  assert.throws(() => parseArgs(['--execute', '--status']), { code: 'ACTIVATION_COMMAND_ARGUMENT_INVALID' });

  const authority = {
    component: 'recovery_host',
    expectedDiskRevision: 'a'.repeat(64)
  };
  const request = buildRequest(authority, checkpoint, 1700000000000);
  assert.equal(request.component, 'recovery_host');
  assert.equal(request.full_clean_required, true);
  assert.equal(request.activation_mode, 'full_clean_activation');
  assert.equal(request.expected_disk_revision, 'a'.repeat(64));
  assert.equal(request.allow_acceptance_pending, true);
  assert.deepEqual(request.source_checkpoint, checkpoint);
  assert.equal(request.requested_at_unix_ms, 1700000000000);
  assert.equal(request.expires_at_unix_ms, 1700000055000);
  assert.throws(
    () => buildRequest(authority, checkpoint, 1700000000000, { expiresAtUnixMs: 1700000060001 }),
    { code: 'ACTIVATION_REQUEST_INVALID' }
  );
  assert.deepEqual(Object.keys(request).sort(), [
    'activation_mode',
    'allow_acceptance_pending',
    'component',
    'expected_disk_revision',
    'expires_at_unix_ms',
    'full_clean_required',
    'operation_id',
    'requested_at_unix_ms',
    'source_checkpoint'
  ]);
});

test('revision extraction prefers the authenticated Recovery Host disk revision', () => {
  const revision = 'b'.repeat(64);
  assert.equal(expectedComponentRevision({
    recoveryHost: { code_revision: { disk_revision: revision } }
  }, {}, 'recovery_host'), revision);
  assert.throws(
    () => expectedComponentRevision({}, {}, 'recovery_host'),
    { code: 'REVISION_UNAVAILABLE' }
  );
});

test('authority summary exposes identity and epoch without secrets', () => {
  const summary = summarizeAuthority({
    component: 'recovery_host',
    expectedDiskRevision: 'c'.repeat(64),
    workspace: 'E:\\DEV\\Codex-web',
    status: {
      pid: 1234,
      instance_id: 'instance-1234567890',
      device_id: 'device-id',
      device_instance_id: 'device-instance-id',
      activation_epoch: { activation_epoch_id: 'epoch-1234', state: 'READY', admission_open: true }
    }
  });
  assert.equal(summary.workspace, 'E:\\DEV\\Codex-web');
  assert.equal(summary.recovery_host.activation_epoch_id, 'epoch-1234');
  assert.equal(summary.recovery_host.admission_open, true);
  assert.equal(Object.hasOwn(summary, 'token'), false);
});

test('checkpoint can be supplied over structured stdin', async () => {
  const stream = Readable.from([JSON.stringify(checkpoint)]);
  assert.equal(await readStdinJson(stream), JSON.stringify(checkpoint));
});

function tempPaths() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'full-clean-deferred-'));
  const paths = createRuntimePaths({
    dataRoot: path.join(root, 'data'),
    resourcesRoot: path.join(root, 'resources'),
    appRoot: root,
    executablePath: process.execPath,
    runtimeMode: 'development'
  });
  return { root, paths };
}

test('deferred envelope is canonical, installation-bound, and tamper-evident', () => {
  const { root, paths } = tempPaths();
  try {
    const now = 1_700_000_000_000;
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: now,
      expiresAtUnixMs: now + 55_000,
      parentPid: process.pid + 1000
    });
    assert.equal(envelope.kind, DEFERRED_KIND);
    assert.equal(envelope.operation_id, operationId);
    assert.equal(envelope.parent_marker, deferredParentMarkerPath(paths, operationId));
    const files = writeDeferredRequest(paths, envelope);
    const loaded = readDeferredEnvelope(paths, files.requestPath);
    assert.deepEqual(loaded.source_checkpoint, checkpoint);
    assert.equal(loaded.result_path, deferredResultPath(paths, operationId));
    const tampered = JSON.parse(fs.readFileSync(files.requestPath, 'utf8'));
    tampered.source_checkpoint = { ...tampered.source_checkpoint, git_head: 'a'.repeat(40) };
    fs.writeFileSync(files.requestPath, JSON.stringify(tampered), 'utf8');
    assert.throws(() => readDeferredEnvelope(paths, files.requestPath), { code: 'DEFERRED_REQUEST_INTEGRITY_FAILED' });
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred request persistence removes only its new marker when request write fails', () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: now,
      parentPid: process.pid + 1000
    });
    let writes = 0;
    assert.throws(() => writeDeferredRequest(paths, envelope, {
      writeJson(target, value) {
        writes += 1;
        if (writes === 2) throw Object.assign(new Error('injected request write failure'), { code: 'EIO' });
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.writeFileSync(target, JSON.stringify(value), 'utf8');
      }
    }), { code: 'EIO' });
    assert.equal(writes, 2);
    assert.equal(fs.existsSync(deferredParentMarkerPath(paths, operationId)), false);
    assert.equal(fs.existsSync(deferredRequestPath(paths, operationId)), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred status reports a queued operation as pending and never fully ready', () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({ paths, checkpoint, operationId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    writeDeferredRequest(paths, envelope);
    const status = readDeferredStatus(paths, operationId, now + 1);
    assert.equal(status.state, 'pending');
    assert.equal(status.activation_pending, true);
    assert.equal(status.fully_ready, false);
    assert.equal(status.expired, false);
    assert.equal(status.parent_boundary_closed, false);
    assert.equal(status.worker_running, false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred terminal result is atomic and immutable across duplicate writers', () => {
  const { root, paths } = tempPaths();
  try {
    const operationId = deferredOperationId(Date.now());
    writeDeferredResult(paths, operationId, {
      state: 'completed',
      result: { activation_epoch_id: 'epoch-first', fully_ready: true }
    });
    const first = readDeferredResult(paths, operationId);
    writeDeferredResult(paths, operationId, {
      state: 'failed',
      error: { code: 'LATE_DUPLICATE', message: 'must not overwrite', details: {} }
    });
    const second = readDeferredResult(paths, operationId);
    assert.deepEqual(second, first);
    assert.equal(second.state, 'completed');
    assert.equal(second.result.activation_epoch_id, 'epoch-first');
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred queue TTL covers the full-clean budget but remains bounded', () => {
  const { root, paths } = tempPaths();
  try {
    const now = 1_700_000_000_000;
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({ paths, checkpoint, operationId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    assert.equal(envelope.expires_at_unix_ms - now, DEFERRED_DEFAULT_TTL_MS);
    assert.ok(DEFERRED_DEFAULT_TTL_MS > 120_000, 'queue must cover the service default plus handoff overhead');
    assert.ok(DEFERRED_MAX_TTL_MS >= DEFERRED_DEFAULT_TTL_MS);
    assert.ok(DEFERRED_ACTIVATION_TTL_MS < DEFERRED_DEFAULT_TTL_MS, 'wire request remains bounded independently');
    assert.throws(() => buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId: deferredOperationId(now + 1),
      requestedAtUnixMs: now,
      expiresAtUnixMs: now + DEFERRED_MAX_TTL_MS + 1,
      parentPid: process.pid + 1000
    }), { code: 'DEFERRED_REQUEST_INVALID' });
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred parent barrier requires both PID exit and marker removal', async () => {
  const marker = { nonce: 'b'.repeat(36) };
  let aliveChecks = 0;
  let markerChecks = 0;
  let waits = 0;
  await waitForDeferredParentExit({
    parentPid: 12345,
    parentMarker: 'marker.json',
    parentMarkerNonce: marker.nonce,
    timeoutMs: 1000,
    pollMs: 10,
    graceMs: 0,
    isAlive: () => { aliveChecks += 1; return aliveChecks < 3; },
    readFile: () => { markerChecks += 1; return markerChecks < 4 ? marker : null; },
    waitFn: async () => { waits += 1; }
  });
  assert.ok(aliveChecks >= 3);
  assert.ok(markerChecks >= 4);
  assert.ok(waits >= 1);
});

test('deferred parent barrier fails closed when marker changes', async () => {
  await assert.rejects(
    waitForDeferredParentExit({
      parentPid: 12345,
      parentMarker: 'marker.json',
      parentMarkerNonce: 'c'.repeat(36),
      timeoutMs: 100,
      isAlive: () => false,
      readFile: () => ({ nonce: 'd'.repeat(36) }),
      waitFn: async () => {}
    }),
    { code: 'DEFERRED_PARENT_MARKER_INVALID' }
  );
});

test('detached worker waits for the post-tool boundary before contacting Recovery Host', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: now,
      // The durable queue may wait through the parent tool boundary and
      // coordinator handoff. The worker rebases the authenticated wire
      // request to the post-boundary clock and caps it independently at the
      // Recovery Host request contract.
      expiresAtUnixMs: now + DEFERRED_DEFAULT_TTL_MS,
      parentPid: process.pid + 1000
    });
    const files = writeDeferredRequest(paths, envelope);
    let activationCalls = 0;
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      waitParent: async () => { activationCalls += 1; fs.rmSync(files.markerPath, { force: true }); },
      now: () => now + 1,
      runActivation: async (options, env) => {
        assert.equal(options.operationId, operationId);
        assert.equal(options.now, now + 1);
        assert.equal(options.expiresAtUnixMs, now + 1 + DEFERRED_ACTIVATION_TTL_MS);
        assert.equal(options.timeoutMs, 120_000);
        assert.equal(JSON.parse(env.FULL_CLEAN_SOURCE_CHECKPOINT_JSON).checkpoint_id, checkpoint.checkpoint_id);
        return {
          ok: true,
          mode: 'execute',
          activation_epoch_id: 'epoch-test',
          fully_ready: true,
          replacement: {
            ready: true,
            state: 'READY',
            admission_open: true,
            fully_ready: true
          }
        };
      }
    });
    assert.equal(result.state, 'completed');
    assert.equal(activationCalls, 1);
    const persisted = readDeferredResult(paths, operationId);
    assert.equal(persisted.state, 'completed');
    assert.equal(persisted.result.activation_epoch_id, 'epoch-test');
    const resultFile = deferredResultPath(paths, operationId);
    const tamperedResult = JSON.parse(fs.readFileSync(resultFile, 'utf8'));
    tamperedResult.state = 'failed';
    fs.writeFileSync(resultFile, JSON.stringify(tamperedResult), 'utf8');
    assert.equal(readDeferredResult(paths, operationId), null);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('detached worker retries only the same preflight-busy operation after the MCP call boundary', async () => {
  const { root, paths } = tempPaths();
  try {
    const startedAt = Date.now();
    let clock = startedAt + 1;
    const operationId = deferredOperationId(startedAt);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: startedAt,
      expiresAtUnixMs: startedAt + DEFERRED_DEFAULT_TTL_MS,
      parentPid: process.pid + 1000
    });
    const files = writeDeferredRequest(paths, envelope);
    const activationOptions = [];
    let attempts = 0;
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      now: () => clock,
      waitParent: async () => { fs.rmSync(files.markerPath, { force: true }); },
      waitRetry: async (ms) => {
        assert.equal(ms, DEFERRED_PREFLIGHT_RETRY_MS);
        clock += ms;
      },
      runActivation: async (options) => {
        attempts += 1;
        activationOptions.push({
          operationId: options.operationId,
          now: options.now,
          expiresAtUnixMs: options.expiresAtUnixMs
        });
        if (attempts === 1) {
          throw Object.assign(new Error('initiating MCP call is still active'), {
            code: 'RUNTIME_BUSY',
            details: { preflight: { safe: false, code: 'RUNTIME_BUSY' } }
          });
        }
        return {
          ok: true,
          fully_ready: true,
          activation_epoch_id: 'epoch-post-tool-retry',
          replacement: { ready: true, state: 'READY', admission_open: true, fully_ready: true }
        };
      }
    });
    assert.equal(result.state, 'completed');
    assert.equal(attempts, 2);
    assert.deepEqual(activationOptions[1], activationOptions[0], 'retry must preserve one authenticated operation payload');
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('detached worker never retries a busy error after preflight', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({ paths, checkpoint, operationId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    const files = writeDeferredRequest(paths, envelope);
    let attempts = 0;
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      now: () => now + 1,
      waitParent: async () => { fs.rmSync(files.markerPath, { force: true }); },
      waitRetry: async () => { throw new Error('post-preflight error must not retry'); },
      runActivation: async () => {
        attempts += 1;
        throw Object.assign(new Error('coordinator became busy after mutation'), { code: 'RUNTIME_BUSY' });
      }
    });
    assert.equal(result.state, 'failed');
    assert.equal(result.error.code, 'RUNTIME_BUSY');
    assert.equal(attempts, 1);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('duplicate deferred workers are single-flight and cannot contact Recovery Host twice', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: now,
      parentPid: process.pid + 1000
    });
    const files = writeDeferredRequest(paths, envelope);
    let releaseBoundary;
    let boundaryEntered;
    const boundary = new Promise((resolve) => { releaseBoundary = resolve; });
    const entered = new Promise((resolve) => { boundaryEntered = resolve; });
    let activationCalls = 0;
    const first = runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      now: () => now + 1,
      waitParent: async () => {
        boundaryEntered();
        await boundary;
        fs.rmSync(files.markerPath, { force: true });
      },
      runActivation: async () => {
        activationCalls += 1;
        return {
          ok: true,
          fully_ready: true,
          activation_epoch_id: 'epoch-single-flight',
          replacement: { ready: true, state: 'READY', admission_open: true, fully_ready: true }
        };
      }
    });
    await entered;
    assert.equal(fs.existsSync(deferredWorkerLockPath(paths, operationId)), true);
    const duplicate = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      now: () => now + 2,
      waitParent: async () => { throw new Error('duplicate crossed the boundary'); },
      runActivation: async () => { activationCalls += 1; return { ok: true }; }
    });
    assert.equal(duplicate.ok, false);
    assert.equal(duplicate.code, 'DEFERRED_WORKER_ALREADY_RUNNING');
    assert.equal(readDeferredResult(paths, operationId), null);
    releaseBoundary();
    const completed = await first;
    assert.equal(completed.state, 'completed');
    assert.equal(activationCalls, 1);
    assert.equal(fs.existsSync(deferredWorkerLockPath(paths, operationId)), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('dead worker ownership stays fail-closed and is never removed or taken over', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({ paths, checkpoint, operationId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    const files = writeDeferredRequest(paths, envelope);
    const abandoned = claimDeferredWorker(paths, envelope, {
      pid: Number.MAX_SAFE_INTEGER,
      now
    });
    const lockBefore = fs.readFileSync(abandoned.lock_path, 'utf8');
    let activationCalls = 0;
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      runActivation: async () => { activationCalls += 1; return { ok: true }; }
    });
    assert.equal(result.ok, false);
    assert.equal(result.code, 'DEFERRED_WORKER_ABANDONED');
    assert.equal(activationCalls, 0);
    assert.equal(fs.existsSync(abandoned.lock_path), true);
    assert.equal(fs.readFileSync(abandoned.lock_path, 'utf8'), lockBefore);
    assert.equal(readDeferredResult(paths, operationId), null);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('worker claim is operation-bound and rejects a copied foreign lock', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const firstId = deferredOperationId(now);
    const secondId = deferredOperationId(now + 1);
    const firstEnvelope = buildDeferredEnvelope({ paths, checkpoint, operationId: firstId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    const secondEnvelope = buildDeferredEnvelope({ paths, checkpoint, operationId: secondId, requestedAtUnixMs: now + 1, parentPid: process.pid + 1001 });
    const claim = claimDeferredWorker(paths, firstEnvelope, { pid: process.pid, now });
    const secondFiles = writeDeferredRequest(paths, secondEnvelope);
    fs.copyFileSync(claim.lock_path, deferredWorkerLockPath(paths, secondId));
    let called = false;
    const result = await runDeferredWorker(secondFiles.requestPath, {
      paths,
      runActivation: async () => { called = true; return { ok: true }; }
    });
    assert.equal(result.ok, false);
    assert.equal(result.code, 'DEFERRED_WORKER_LOCK_INVALID');
    assert.equal(called, false);
    assert.equal(readDeferredResult(paths, secondId), null);
    assert.equal(releaseDeferredWorkerClaim(claim), true);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('worker records UPDATE_INCOMPLETE when replacement readiness is not fully proven', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({ paths, checkpoint, operationId, requestedAtUnixMs: now, parentPid: process.pid + 1000 });
    const files = writeDeferredRequest(paths, envelope);
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      now: () => now + 1,
      waitParent: async () => { fs.rmSync(files.markerPath, { force: true }); },
      runActivation: async () => ({
        ok: true,
        fully_ready: false,
        activation_epoch_id: 'epoch-incomplete',
        replacement: { ready: false, state: 'VERIFYING', admission_open: false, fully_ready: false }
      })
    });
    assert.equal(result.state, 'failed');
    assert.equal(result.error.code, 'UPDATE_INCOMPLETE');
    const persisted = readDeferredResult(paths, operationId);
    assert.equal(persisted.state, 'failed');
    assert.equal(persisted.error.code, 'UPDATE_INCOMPLETE');
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('deferred worker records expiry without invoking activation', async () => {
  const { root, paths } = tempPaths();
  try {
    const now = Date.now();
    const operationId = deferredOperationId(now);
    const envelope = buildDeferredEnvelope({
      paths,
      checkpoint,
      operationId,
      requestedAtUnixMs: now - 55_000,
      expiresAtUnixMs: now - 1,
      parentPid: process.pid + 1000
    });
    const files = writeDeferredRequest(paths, envelope);
    fs.rmSync(files.markerPath, { force: true });
    let called = false;
    const result = await runDeferredWorker(files.requestPath, {
      paths,
      env: {},
      runActivation: async () => { called = true; return { ok: true }; },
      now: () => now
    });
    assert.equal(result.state, 'expired');
    assert.equal(result.error.code, 'ACTIVATION_REQUEST_EXPIRED');
    assert.equal(called, false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('detached worker launch is explicitly detached and inherits no caller output stream', async () => {
  let captured = null;
  const child = {
    pid: 4321,
    once(event, handler) { if (event === 'spawn') queueMicrotask(handler); return this; },
    unref() { this.unrefCalled = true; }
  };
  const launched = await spawnDeferredWorker('C:\\runtime\\request.json', {
    cwd: 'C:\\runtime',
    env: { SAMPLE: 'ok' },
    spawnProcess: (...args) => { captured = args; return child; }
  });
  assert.equal(launched.pid, 4321);
  assert.equal(child.unrefCalled, true);
  assert.equal(captured[0], process.execPath);
  assert.deepEqual(captured[1].slice(1, 2), ['--deferred-worker']);
  assert.equal(captured[2].detached, true);
  assert.equal(captured[2].windowsHide, true);
  assert.deepEqual(captured[2].stdio, 'ignore');
  assert.equal(captured[2].env.FULL_CLEAN_DEFERRED_WORKER, '1');
  assert.equal(Object.hasOwn(captured[2].env, 'OPENAI_API_KEY'), false);
  assert.equal(Object.hasOwn(captured[2].env, 'NODE_OPTIONS'), false);
});

test('deferred worker environment strips ambient credential and loader variables', () => {
  const safe = deferredWorkerEnvironment({
    APPDATA: 'C:\\Users\\operator\\AppData\\Roaming',
    PATH: 'C:\\Windows',
    OPENAI_API_KEY: 'redacted',
    CODING_TOOLS_MCP_AUTH_TOKEN: 'redacted',
    FOO_PASSWORD: 'redacted',
    NODE_OPTIONS: '--require evil-loader',
    FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(checkpoint)
  });
  assert.equal(safe.APPDATA, 'C:\\Users\\operator\\AppData\\Roaming');
  assert.equal(safe.PATH, 'C:\\Windows');
  assert.equal(safe.FULL_CLEAN_DEFERRED_WORKER, '1');
  assert.equal(Object.hasOwn(safe, 'OPENAI_API_KEY'), false);
  assert.equal(Object.hasOwn(safe, 'CODING_TOOLS_MCP_AUTH_TOKEN'), false);
  assert.equal(Object.hasOwn(safe, 'FOO_PASSWORD'), false);
  assert.equal(Object.hasOwn(safe, 'NODE_OPTIONS'), false);
  assert.equal(Object.hasOwn(safe, 'FULL_CLEAN_SOURCE_CHECKPOINT_JSON'), false);
});

test('execute command queues instead of synchronously self-calling the active MCP tool', async () => {
  const { root, paths } = tempPaths();
  const descriptor = {
    version: 1,
    host: '127.0.0.1',
    port: 43123,
    token: crypto.randomBytes(32).toString('base64url'),
    owner: 'recovery-host',
    owner_pid: process.pid,
    instance_id: 'instance-deferred-command-0001',
    installation_id: paths.runtimeIdentity().installation_id,
    runtime_mode: paths.runtimeIdentity().mode
  };
  fs.mkdirSync(paths.dataRoot(), { recursive: true });
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(descriptor), 'utf8');
  const fakeChild = {
    pid: 6789,
    once(event, handler) { if (event === 'spawn') queueMicrotask(handler); return this; },
    unref() {}
  };
  try {
    const queued = await deferExecute({
      paths,
      checkpoint,
      env: {},
      now: Date.now(),
      spawnProcess: () => fakeChild
    });
    assert.equal(queued.ok, true);
    assert.equal(queued.mode, 'deferred');
    assert.equal(queued.activation_pending, true);
    assert.equal(queued.fully_ready, false);
    assert.equal(queued.expires_at_unix_ms - queued.requested_at_unix_ms, DEFERRED_DEFAULT_TTL_MS);
    assert.equal(queued.worker_pid, 6789);
    assert.match(queued.request_path, /full-clean-activation/);
    assert.equal(fs.existsSync(queued.request_path), true);
    assert.equal(fs.existsSync(deferredResultPath(paths, queued.operation_id)), false);
    fs.rmSync(queued.request_path, { force: true });
    fs.rmSync(deferredParentMarkerPath(paths, queued.operation_id), { force: true });
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('internal worker argv is not accepted as a public activation mode', () => {
  assert.deepEqual(parseDeferredWorkerArgs(['--deferred-worker', 'C:\\x\\request.json']), {
    requestPath: 'C:\\x\\request.json'
  });
  assert.equal(parseDeferredWorkerArgs(['--execute']), null);
  assert.throws(() => parseArgs(['--deferred-worker', 'request.json']), { code: 'ACTIVATION_COMMAND_ARGUMENT_INVALID' });
});

function fakeAuthority({ current = true, revision = 'a'.repeat(64) } = {}) {
  return {
    status: {
      activation_epoch: { activation_epoch_id: 'old-epoch', state: 'READY', admission_open: true },
      runtime: { fully_ready: true }
    },
    snapshot: {},
    workspace: 'E:\\DEV\\Codex-web',
    component: 'recovery_host',
    expectedDiskRevision: revision,
    freshness: {
      current,
      stale: !current,
      capability: {
        available: current,
        contract_version: 1,
        state: current ? 'current' : 'stale',
        running_revision: current ? revision : 'b'.repeat(64),
        disk_revision: current ? revision : 'b'.repeat(64)
      }
    }
  };
}

function fakeContext(paths, descriptor, clientCall = async () => ({})) {
  return {
    paths,
    descriptor,
    client: { call: clientCall },
    requestOptions: { expectedOwnerPid: descriptor.owner_pid, expectedInstanceId: descriptor.instance_id }
  };
}

test('replacement connector ACK eligibility accepts exact discovery or compatibility bootstrap snapshots', () => {
  const startedAt = Date.now();
  const epochId = 'epoch-connector-eligibility-0001';
  const descriptor = {
    activation_epoch_id: epochId,
    started_at: new Date(startedAt).toISOString()
  };
  const base = {
    activationEpoch: { activation_epoch_id: epochId },
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: true,
    toolContract: { sha256: 'c'.repeat(64) }
  };
  const strict = {
    ...base,
    connectorContractState: 'CHANGED_DISCOVERED_NEEDS_ACK',
    connectorRediscovered: true,
    connectorRediscoveredAt: new Date(startedAt + 1_000).toISOString()
  };
  const compatible = {
    ...base,
    connectorContractState: 'UNCHANGED_COMPATIBLE_NEEDS_ACK',
    connectorRediscovered: false,
    connectorBootstrapObservedAt: new Date(startedAt + 1_000).toISOString()
  };

  assert.equal(connectorAcknowledgementEligible(strict, descriptor, epochId, startedAt), true);
  assert.equal(connectorAcknowledgementEligible(compatible, descriptor, epochId, startedAt), true);
  assert.equal(connectorAcknowledgementEligible({
    ...compatible,
    connectorBootstrapObservedAt: new Date(startedAt - 1_000).toISOString()
  }, descriptor, epochId, startedAt), false);
  assert.equal(connectorAcknowledgementEligible({
    ...compatible,
    connectorRediscovered: true
  }, descriptor, epochId, startedAt), false);
});

test('replacement connector ACK waits for fresh current-epoch discovery and runs once', async () => {
  const { root, paths } = tempPaths();
  try {
    const startedAt = Date.now();
    const initialDescriptor = {
      instance_id: 'old-instance-connector-0001',
      owner_pid: 1001,
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    const replacementDescriptor = {
      ...initialDescriptor,
      instance_id: 'new-instance-connector-0001',
      owner_pid: 1002,
      activation_epoch_id: 'epoch-connector-0001',
      started_at: new Date(startedAt).toISOString()
    };
    let poll = 0;
    let ackCalls = 0;
    const runtimeSnapshot = (discovered, ready) => ({
      activationEpoch: { activation_epoch_id: 'epoch-connector-0001' },
      connectorRediscovered: discovered,
      connectorRefreshRequired: !discovered,
      connectorAcknowledgementPending: discovered,
      connectorContractState: discovered ? 'CHANGED_DISCOVERED_NEEDS_ACK' : 'UNAVAILABLE',
      connectorRediscoveredAt: discovered ? new Date(startedAt + 1_000).toISOString() : null,
      toolContract: { sha256: 'c'.repeat(64) },
      fullyReady: ready
    });
    const result = await waitForReplacementReady(
      paths,
      initialDescriptor,
      'epoch-connector-0001',
      5_000,
      {
        operationId: 'full-clean-cli-connector-0001',
        notBeforeUnixMs: startedAt,
        now: () => startedAt + poll,
        waitFn: async () => { poll += 1; },
        loadDescriptor: () => replacementDescriptor,
        readBootstrapResultFn: () => null,
        clientFactory: () => ({
          status: async () => {
            poll += 1;
            const ready = poll >= 5;
            return {
              activation_epoch: {
                activation_epoch_id: 'epoch-connector-0001',
                operation_id: 'full-clean-cli-connector-0001',
                state: ready ? 'READY' : 'VERIFYING',
                admission_open: ready
              },
              runtime: { fully_ready: ready }
            };
          },
          call: async (action) => {
            if (action === 'runtime.lightweight_snapshot') return runtimeSnapshot(poll >= 3, poll >= 5);
            if (action === 'runtime.acknowledge_connector_contract') {
              ackCalls += 1;
              return { acknowledged: true };
            }
            throw new Error(`unexpected action ${action}`);
          }
        })
      }
    );
    assert.equal(result.ready, true);
    assert.equal(result.connectorAckAttempted, true);
    assert.equal(ackCalls, 1);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('unchanged connector contract never receives an ACK', async () => {
  const { root, paths } = tempPaths();
  try {
    const startedAt = Date.now();
    const initialDescriptor = { instance_id: 'old-instance-unchanged-0001', owner_pid: 1001 };
    const replacementDescriptor = {
      ...initialDescriptor,
      instance_id: 'new-instance-unchanged-0001',
      owner_pid: 1002,
      activation_epoch_id: 'epoch-unchanged-0001',
      started_at: new Date(startedAt).toISOString(),
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    let now = startedAt;
    let ackCalls = 0;
    const result = await waitForReplacementReady(paths, initialDescriptor, 'epoch-unchanged-0001', 1_000, {
      operationId: 'full-clean-cli-unchanged-0001',
      notBeforeUnixMs: startedAt,
      now: () => now,
      waitFn: async () => { now += 2_000; },
      loadDescriptor: () => replacementDescriptor,
      readBootstrapResultFn: () => null,
      clientFactory: () => ({
        status: async () => ({
          activation_epoch: {
            activation_epoch_id: 'epoch-unchanged-0001',
            operation_id: 'full-clean-cli-unchanged-0001',
            state: 'VERIFYING',
            admission_open: false
          },
          runtime: { fully_ready: false }
        }),
        call: async (action) => {
          if (action === 'runtime.lightweight_snapshot') return {
            activationEpoch: { activation_epoch_id: 'epoch-unchanged-0001' },
            connectorRediscovered: true,
            connectorRefreshRequired: false,
            connectorAcknowledgementPending: false,
            connectorContractState: 'UNCHANGED_ACKNOWLEDGED',
            connectorRediscoveredAt: new Date(startedAt + 1_000).toISOString(),
            toolContract: { sha256: 'd'.repeat(64) }
          };
          if (action === 'runtime.acknowledge_connector_contract') ackCalls += 1;
          return {};
        }
      })
    });
    assert.equal(result.ready, false);
    assert.equal(result.connectorAckAttempted, false);
    assert.equal(ackCalls, 0);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('stale Recovery Host bootstraps current checkout without legacy preflight or activation', async () => {
  const { root, paths } = tempPaths();
  try {
    const revision = 'e'.repeat(64);
    const descriptor = {
      instance_id: 'old-instance-bootstrap-0001',
      owner_pid: 1001,
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    const context = fakeContext(paths, descriptor, async (action) => {
      if (action === 'code.activation_preflight' || action === 'code.activate_update') {
        throw new Error(`legacy activation action was called: ${action}`);
      }
      return {};
    });
    const operationId = 'full-clean-cli-bootstrap-test-0001';
    let bootstrapArgs = null;
    const result = await run({
      argv: ['--execute'],
      context,
      operationId,
      now: 1_700_000_000_000,
      timeoutMs: 120_000,
      readAuthorityFn: async () => fakeAuthority({ current: false, revision }),
      bootstrapCurrentRecoveryHostFn: async (args) => {
        bootstrapArgs = args;
        return { required: true, stale: true, pid: 2002 };
      },
      waitForReplacementOperationFn: async (pathsArg, descriptorArg, opArg) => {
        assert.equal(pathsArg, paths);
        assert.equal(descriptorArg, descriptor);
        assert.equal(opArg, operationId);
        return {
          operation: { operation_id: operationId, activation_epoch_id: 'epoch-bootstrap-0001' },
          activationEpochId: 'epoch-bootstrap-0001',
          descriptor: { ...descriptor, instance_id: 'new-instance-bootstrap-0001', owner_pid: 2002 }
        };
      },
      waitForReplacementReadyFn: async (pathsArg, descriptorArg, epochArg, timeoutArg, optionsArg) => {
        assert.equal(pathsArg, paths);
        assert.equal(descriptorArg, descriptor);
        assert.equal(epochArg, 'epoch-bootstrap-0001');
        assert.equal(timeoutArg, 120_000);
        assert.equal(optionsArg.operationId, operationId);
        return {
          ready: true,
          connectorAckAttempted: true,
          descriptor: { ...descriptor, instance_id: 'new-instance-bootstrap-0001', owner_pid: 2002 },
          status: {
            activation_epoch: { activation_epoch_id: 'epoch-bootstrap-0001', state: 'READY', admission_open: true },
            runtime: { fully_ready: true }
          }
        };
      }
    }, { FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(checkpoint) });
    assert.equal(result.ok, true);
    assert.equal(result.bootstrap_required, true);
    assert.equal(result.recovery_host_bootstrapped, true);
    assert.equal(result.preflight, null);
    assert.equal(result.fully_ready, true);
    assert.equal(bootstrapArgs.operationId, operationId);
    assert.deepEqual(bootstrapArgs.sourceCheckpoint, checkpoint);
    assert.equal(bootstrapArgs.expectedDiskRevision, revision);
    assert.equal(bootstrapArgs.app.isPackaged, false);
    assert.equal(bootstrapArgs.app.getAppPath(), root);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('stale preflight reports bootstrap_required without mutating or killing the old host', async () => {
  const { root, paths } = tempPaths();
  try {
    const descriptor = {
      instance_id: 'old-instance-preflight-0001',
      owner_pid: 1001,
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    const context = fakeContext(paths, descriptor, async (action) => {
      throw new Error(`unexpected stale-host RPC: ${action}`);
    });
    let bootstrapCalls = 0;
    const result = await run({
      argv: ['--preflight'],
      context,
      operationId: 'full-clean-cli-preflight-test-0001',
      now: 1_700_000_000_000,
      readAuthorityFn: async () => fakeAuthority({ current: false }),
      bootstrapCurrentRecoveryHostFn: async () => { bootstrapCalls += 1; }
    }, { FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(checkpoint) });
    assert.equal(result.ok, true);
    assert.equal(result.mode, 'preflight');
    assert.equal(result.bootstrap_required, true);
    assert.equal(result.preflight.code, 'RECOVERY_BOOTSTRAP_REQUIRED');
    assert.equal(bootstrapCalls, 0);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('response loss after activate_update is reconciled once through exact replacement operation', async () => {
  const { root, paths } = tempPaths();
  try {
    const descriptor = {
      instance_id: 'old-instance-response-0001',
      owner_pid: 1001,
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    let activateCalls = 0;
    const context = fakeContext(paths, descriptor, async (action) => {
      if (action === 'code.activation_preflight') return { safe: true };
      if (action === 'code.activate_update') {
        activateCalls += 1;
        throw Object.assign(new Error('old host exited after accepting activation'), { code: 'ECONNRESET' });
      }
      throw new Error(`unexpected action ${action}`);
    });
    const operationId = 'full-clean-cli-response-loss-0001';
    let operationWaits = 0;
    const result = await run({
      argv: ['--execute'],
      context,
      operationId,
      now: 1_700_000_000_000,
      timeoutMs: 120_000,
      readAuthorityFn: async () => fakeAuthority({ current: true }),
      waitForReplacementOperationFn: async (...args) => {
        operationWaits += 1;
        assert.equal(args[2], operationId);
        return {
          operation: { operation_id: operationId, activation_epoch_id: 'epoch-response-0001' },
          activationEpochId: 'epoch-response-0001',
          descriptor: { ...descriptor, instance_id: 'new-instance-response-0001', owner_pid: 2002 }
        };
      },
      waitForReplacementReadyFn: async (...args) => {
        assert.equal(args[2], 'epoch-response-0001');
        assert.equal(args[4].operationId, operationId);
        return {
          ready: true,
          connectorAckAttempted: false,
          descriptor: { ...descriptor, instance_id: 'new-instance-response-0001', owner_pid: 2002 },
          status: {
            activation_epoch: { activation_epoch_id: 'epoch-response-0001', state: 'READY', admission_open: true },
            runtime: { fully_ready: true }
          }
        };
      }
    }, { FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(checkpoint) });
    assert.equal(activateCalls, 1);
    assert.equal(operationWaits, 1);
    assert.equal(result.activation_response_recovered, true);
    assert.equal(result.activation_epoch_id, 'epoch-response-0001');
    assert.equal(result.fully_ready, true);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('local checkout hash outranks a self-reported old-host revision', async () => {
  const { root, paths } = tempPaths();
  try {
    const localRevision = 'f'.repeat(64);
    const oldRevision = '1'.repeat(64);
    const descriptor = {
      instance_id: 'old-instance-hash-0001',
      owner_pid: 1001,
      installation_id: paths.runtimeIdentity().installation_id,
      runtime_mode: paths.runtimeIdentity().mode
    };
    const context = {
      paths,
      descriptor,
      client: {
        status: async () => ({
          full_clean_activation: {
            available: true,
            contract_version: 1,
            state: 'current',
            running_revision: oldRevision,
            disk_revision: oldRevision
          }
        }),
        call: async (action) => {
          if (action === 'runtime.snapshot') return { workspace: root };
          return {};
        }
      },
      requestOptions: {}
    };
    let assessedExpected = null;
    const authority = await readAuthority(context, {
      hashComponentRevisionFn: () => ({ revision: localRevision }),
      assessRecoveryHostFreshnessFn: (input) => {
        assessedExpected = input.expectedDiskRevision;
        return {
          current: input.status.full_clean_activation.running_revision === input.expectedDiskRevision,
          stale: true,
          capability: { available: true, state: 'current', contract_version: 1, running_revision: oldRevision, disk_revision: oldRevision }
        };
      }
    });
    assert.equal(assessedExpected, localRevision);
    assert.equal(authority.expectedDiskRevision, localRevision);
    assert.equal(authority.freshness.current, false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
