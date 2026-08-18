const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  createInstallationIdentity,
  sameInstallationIdentity
} = require('../electron/services/runtimeIdentity');
const {
  descriptorMatchesInstallation,
  retireStaleDevelopmentRecoveryHost
} = require('../electron/services/recoveryHostLauncher');

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

test('development installation identity follows the canonical checkout, not machine-specific spelling', (t) => {
  const root = makeRoot(t);
  const checkoutA = makeCheckout(root, 'checkout-a');
  const checkoutB = makeCheckout(root, 'checkout-b');
  const aliasA = path.join(root, 'nested', '..', 'checkout-a');
  const aliasResourcesA = path.join(aliasA, 'resources');

  const a = createInstallationIdentity({
    mode: 'development',
    appRoot: checkoutA.appRoot,
    resourcesRoot: checkoutA.resourcesRoot,
    executablePath: process.execPath
  });
  const aAlias = createInstallationIdentity({
    mode: 'development',
    appRoot: aliasA,
    resourcesRoot: aliasResourcesA,
    executablePath: process.execPath
  });
  const b = createInstallationIdentity({
    mode: 'development',
    appRoot: checkoutB.appRoot,
    resourcesRoot: checkoutB.resourcesRoot,
    executablePath: process.execPath
  });
  const packagedA = createInstallationIdentity({
    mode: 'packaged',
    appRoot: checkoutA.appRoot,
    resourcesRoot: checkoutA.resourcesRoot,
    executablePath: process.execPath
  });

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

test('legacy or another-checkout Recovery Host never matches the current dev checkout', (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const expected = createInstallationIdentity({
    mode: 'development',
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    executablePath: process.execPath
  });

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
  const expected = createInstallationIdentity({
    mode: 'development',
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    executablePath: process.execPath
  });
  const stale = {
    version: 1,
    host: '127.0.0.1',
    port: 18766,
    token: 'x'.repeat(43),
    owner: 'recovery-host',
    owner_pid: 42420,
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
    terminateProcess: (pid) => { calls.terminate.push(pid); alive = false; },
    processAlive: () => alive,
    sleep: async () => {},
    timeoutMs: 1000
  });

  assert.deepEqual(calls.stop, [{ manual: false }]);
  assert.deepEqual(calls.terminate, [stale.owner_pid]);
  assert.equal(result.retired, true);
  assert.equal(alive, false);
});

test('dev relocation fails closed if Recovery Host owner changes after runtime shutdown', async (t) => {
  const root = makeRoot(t);
  const checkout = makeCheckout(root, 'checkout-current');
  const expected = createInstallationIdentity({
    mode: 'development',
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    executablePath: process.execPath
  });
  const stale = {
    owner_pid: 42420,
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
      processAlive: () => true,
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
  const expected = createInstallationIdentity({
    mode: 'packaged',
    appRoot: checkout.appRoot,
    resourcesRoot: checkout.resourcesRoot,
    executablePath: process.execPath
  });
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
