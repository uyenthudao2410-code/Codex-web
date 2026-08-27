const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { EventEmitter } = require('node:events');

const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { SettingsStore } = require('../electron/services/settingsStore');
const {
  createInstallationIdentity,
  sameInstallationIdentity
} = require('../electron/services/runtimeIdentity');
const {
  ensureRecoveryHost,
  descriptorMatchesInstallation,
  retireStaleDevelopmentRecoveryHost
} = require('../electron/services/recoveryHostLauncher');

const STALE_PROCESS_START_TOKEN = '133801234567890123';
const CURRENT_PROCESS_START_TOKEN = '133801234567890999';

function makeRoot(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-dev-checkout-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

function makeCheckout(root, name) {
  const appRoot = path.join(root, name);
  const resourcesRoot = path.join(appRoot, 'resources');
  fs.mkdirSync(resourcesRoot, { recursive: true });
  return { appRoot, resourcesRoot };
}

function identity(checkout, mode = 'development') {
  return createInstallationIdentity({
    mode,
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    executablePath: process.execPath
  });
}

test('development installation identity follows the canonical checkout, not machine-specific spelling', (t) => {
  const root = makeRoot(t);
  const checkoutA = makeCheckout(root, 'checkout-a');
  const checkoutB = makeCheckout(root, 'checkout-b');
  const aliasA = path.join(root, 'nested', '..', 'checkout-a');
  const aliasResourcesA = path.join(aliasA, 'resources');

  const a = identity(checkoutA);
  const aAlias = createInstallationIdentity({
    mode: 'development',
    appRoot: aliasA,
    resourcesRoot: aliasResourcesA,
    executablePath: process.execPath
  });
  const b = identity(checkoutB);
  const packagedA = identity(checkoutA, 'packaged');

  assert.equal(a.mode, 'development');
  assert.equal(a.installation_id.length, 64);
  assert.equal(a.installation_id, aAlias.installation_id, 'equivalent canonical checkout aliases must keep one identity');
  assert.notEqual(a.installation_id, b.installation_id, 'moving to another checkout root must produce another dev authority');
  assert.notEqual(a.installation_id, packagedA.installation_id, 'packaged and development authority must never collapse together');
  assert.equal(sameInstallationIdentity(a, aAlias), true);
  assert.equal(sameInstallationIdentity(a, b), false);
});

test('RuntimePaths publishes a distinct installation identity when the dev checkout relocates', (t) => {
  const root = makeRoot(t);
  const checkoutA = makeCheckout(root, 'checkout-a');
  const checkoutB = makeCheckout(root, 'checkout-b');
  const dataRoot = path.join(root, 'shared-appdata');
  fs.mkdirSync(dataRoot, { recursive: true });

  const pathsA = createRuntimePaths({
    dataRoot,
    appRoot: checkoutA.appRoot,
    resourcesRoot: checkoutA.resourcesRoot,
    runtimeMode: 'development',
    executablePath: process.execPath
  });
  const pathsB = createRuntimePaths({
    dataRoot,
    appRoot: checkoutB.appRoot,
    resourcesRoot: checkoutB.resourcesRoot,
    runtimeMode: 'development',
    executablePath: process.execPath
  });

  assert.equal(pathsA.dataRoot(), pathsB.dataRoot(), 'AppData can legitimately remain shared across dev checkout moves');
  assert.notEqual(pathsA.runtimeIdentity().installation_id, pathsB.runtimeIdentity().installation_id);
});

test('development settings never persist Windows autostart for a checkout path', (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const dataRoot = path.join(root, 'data');
  fs.mkdirSync(dataRoot, { recursive: true });
  const paths = createRuntimePaths({
    dataRoot,
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    runtimeMode: 'development',
    executablePath: process.execPath
  });
  fs.writeFileSync(paths.settingsFile(), JSON.stringify({ configVersion: 6, startWithWindows: true }), 'utf8');
  const store = new SettingsStore(paths);

  assert.equal(store.load().startWithWindows, false);
  assert.equal(store.save({ startWithWindows: true }).startWithWindows, false);
  assert.equal(JSON.parse(fs.readFileSync(paths.settingsFile(), 'utf8')).startWithWindows, false);
});

test('packaged settings preserve explicit Windows autostart choice', (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'package-current');
  const dataRoot = path.join(root, 'data');
  fs.mkdirSync(dataRoot, { recursive: true });
  const paths = createRuntimePaths({
    dataRoot,
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    runtimeMode: 'packaged',
    executablePath: process.execPath
  });
  const store = new SettingsStore(paths);
  assert.equal(store.save({ startWithWindows: true }).startWithWindows, true);
  assert.equal(store.load().startWithWindows, true);
});

test('legacy or another-checkout Recovery Host never matches the current dev checkout', (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const expected = identity(checkout);

  assert.equal(descriptorMatchesInstallation({
    installation_id: expected.installation_id,
    runtime_mode: expected.mode
  }, expected), true);
  assert.equal(descriptorMatchesInstallation({
    installation_id: 'a'.repeat(64),
    runtime_mode: 'development'
  }, expected), false);
  assert.equal(descriptorMatchesInstallation({ owner_pid: 123, instance_id: 'legacy-host-0000001' }, expected), false);
});

test('dev relocation stops old primary runtime and terminates only the authenticated stale Recovery Host PID', async (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const expected = identity(checkout);
  const stale = {
    version: 1,
    host: '127.0.0.1',
    port: 18766,
    token: 'x'.repeat(43),
    owner: 'recovery-host',
    owner_pid: 42420,
    owner_process_start_token: STALE_PROCESS_START_TOKEN,
    instance_id: 'stale-recovery-host-0001',
    installation_id: 'a'.repeat(64),
    runtime_mode: 'development'
  };
  const calls = { stop: [], terminate: [] };
  let alive = true;

  const result = await retireStaleDevelopmentRecoveryHost({
    client: { stop: async (options) => { calls.stop.push(options); return { stopped: true }; } },
    paths: {},
    expectedIdentity: expected,
    descriptor: stale,
    log: { warn() {} },
    readDescriptor: () => stale,
    processIdentityObserver: async (pid) => alive
      ? { state: 'live', pid, process_start_token: STALE_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    terminateProcess: (identity) => { calls.terminate.push(identity); alive = false; },
    sleep: async () => {},
    timeoutMs: 1000
  });

  assert.deepEqual(calls.stop, [{ manual: false }]);
  assert.deepEqual(calls.terminate, [{
    pid: stale.owner_pid,
    process_start_token: STALE_PROCESS_START_TOKEN
  }]);
  assert.equal(result.retired, true);
  assert.equal(alive, false);
});

test('ensureRecoveryHost replaces checkout A with checkout B instead of attaching the stale host', async (t) => {
  const root = makeRoot(t);
  const checkoutA = makeCheckout(root, 'checkout-a');
  const checkoutB = makeCheckout(root, 'checkout-b');
  const expected = identity(checkoutB);
  const stale = {
    version: 1,
    host: '127.0.0.1',
    port: 18766,
    token: 'x'.repeat(43),
    owner: 'recovery-host',
    owner_pid: 42420,
    owner_process_start_token: STALE_PROCESS_START_TOKEN,
    instance_id: 'stale-recovery-host-0001',
    installation_id: identity(checkoutA).installation_id,
    runtime_mode: 'development'
  };
  const current = {
    ...stale,
    owner_pid: 42421,
    owner_process_start_token: CURRENT_PROCESS_START_TOKEN,
    instance_id: 'current-recovery-host-001',
    installation_id: expected.installation_id
  };
  let phase = 'stale';
  let oldAlive = true;
  const calls = { stop: 0, terminate: [], spawn: 0 };
  const client = {
    ping: async () => {
      const active = phase === 'stale' ? stale : current;
      return {
        ready: true,
        pid: active.owner_pid,
        process_start_token: active.owner_process_start_token,
        instance_id: active.instance_id
      };
    },
    stop: async (options) => { assert.deepEqual(options, { manual: false }); calls.stop += 1; return { stopped: true }; }
  };
  const fakeSpawn = () => {
    calls.spawn += 1;
    phase = 'current';
    const child = new EventEmitter();
    child.pid = current.owner_pid;
    child.unref = () => {};
    process.nextTick(() => child.emit('spawn'));
    return child;
  };
  const paths = { runtimeIdentity: () => expected };

  const result = await ensureRecoveryHost({
    app: { isPackaged: false, getAppPath: () => checkoutB.appRoot },
    paths,
    log: { warn() {}, error() {} },
    timeoutMs: 1000,
    spawnProcess: fakeSpawn,
    clientFactory: () => client,
    readDescriptor: () => phase === 'stale' ? stale : current,
    processIdentityObserver: async (pid) => {
      if (pid === stale.owner_pid) {
        return oldAlive
          ? { state: 'live', pid, process_start_token: STALE_PROCESS_START_TOKEN }
          : { state: 'absent', pid, process_start_token: null };
      }
      return { state: 'live', pid, process_start_token: CURRENT_PROCESS_START_TOKEN };
    },
    terminateProcess: (identity) => { calls.terminate.push(identity); oldAlive = false; },
    sleep: async () => {}
  });

  assert.equal(result, client);
  assert.equal(calls.stop, 1);
  assert.deepEqual(calls.terminate, [{
    pid: stale.owner_pid,
    process_start_token: STALE_PROCESS_START_TOKEN
  }]);
  assert.equal(calls.spawn, 1);
});

test('dev relocation fails closed if Recovery Host owner changes after runtime shutdown', async (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const expected = identity(checkout);
  const stale = {
    owner_pid: 42420,
    owner_process_start_token: STALE_PROCESS_START_TOKEN,
    instance_id: 'stale-recovery-host-0001',
    installation_id: 'a'.repeat(64),
    runtime_mode: 'development'
  };
  let terminated = false;

  await assert.rejects(
    retireStaleDevelopmentRecoveryHost({
      client: { stop: async () => ({ stopped: true }) },
      paths: {},
      expectedIdentity: expected,
      descriptor: stale,
      log: { warn() {} },
      readDescriptor: () => ({ ...stale, owner_pid: 42421, instance_id: 'different-owner-00001' }),
      terminateProcess: () => { terminated = true; },
      processIdentityObserver: async (pid) => ({
        state: 'live',
        pid,
        process_start_token: STALE_PROCESS_START_TOKEN
      }),
      sleep: async () => {},
      timeoutMs: 1000
    }),
    { code: 'RECOVERY_HOST_DEV_HANDOFF_TARGET_CHANGED' }
  );
  assert.equal(terminated, false);
});

test('packaged runtime never auto-takes over another installation', async (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'package-current');
  const expected = identity(checkout, 'packaged');
  let stopped = false;
  let terminated = false;

  await assert.rejects(
    retireStaleDevelopmentRecoveryHost({
      client: { stop: async () => { stopped = true; } },
      paths: {},
      expectedIdentity: expected,
      descriptor: {
        owner_pid: 42420,
        instance_id: 'other-package-host-001',
        installation_id: 'a'.repeat(64),
        runtime_mode: 'packaged'
      },
      terminateProcess: () => { terminated = true; }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(stopped, false);
  assert.equal(terminated, false);
});
