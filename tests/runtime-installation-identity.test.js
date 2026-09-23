const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  COMPONENT_SPECS,
  componentOwnsPath,
  RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS
} = require('../electron/services/componentRevision');
const { createInstallationIdentity } = require('../electron/services/runtimeIdentity');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  RecoveryIpcServer,
  RecoveryIpcClient,
  loadRecoveryDescriptor
} = require('../electron/services/recoveryIpc');

function canonicalTextSha256(file) {
  const content = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(Buffer.from(content, 'utf8')).digest('hex');
}

function runtimeFixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-runtime-identity-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const appRoot = path.join(root, 'checkout');
  const resourcesRoot = path.join(appRoot, 'resources');
  const dataRoot = path.join(root, 'data');
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(dataRoot, { recursive: true });
  return createRuntimePaths({
    dataRoot,
    appRoot,
    resourcesRoot,
    runtimeMode: 'development',
    executablePath: process.execPath
  });
}

test('runtime identity source belongs to the Recovery Host component revision', () => {
  const relative = 'electron/services/runtimeIdentity.js';
  assert.equal(componentOwnsPath('recovery_host', relative), true);
  assert.ok(COMPONENT_SPECS.recovery_host.files.includes(relative));
});

test('legacy Recovery Host bridge pins the newly added runtime identity source', () => {
  const relative = 'electron/services/runtimeIdentity.js';
  const expected = RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS[relative];
  assert.match(expected, /^[a-f0-9]{64}$/);
  assert.equal(canonicalTextSha256(path.join(__dirname, '..', relative)), expected);
});

test('installation identity contains no raw checkout path', () => {
  const root = path.resolve(__dirname, '..');
  const identity = createInstallationIdentity({
    mode: 'development',
    appRoot: root,
    resourcesRoot: path.join(root, 'resources'),
    executablePath: process.execPath
  });
  const serialized = JSON.stringify(identity);
  assert.equal(serialized.includes(root), false);
  assert.match(identity.installation_id, /^[a-f0-9]{64}$/);
});

test('a foreign Recovery Host fallback client refuses all mutating RPCs', async () => {
  const client = new RecoveryIpcClient({
    paths: {},
    readOnlyError: {
      code: 'RECOVERY_HOST_INSTALLATION_MISMATCH',
      message: 'foreign host'
    }
  });
  for (const action of ['runtime.start', 'runtime.stop', 'runtime.restart', 'client.register_ui_revision', 'runtime.control_plane_exec']) {
    await assert.rejects(client.call(action, []), {
      code: 'RECOVERY_HOST_INSTALLATION_MISMATCH',
      recoveryResponseReceived: false
    }, action);
  }
});

test('Recovery IPC descriptor publishes installation identity and binds requests to owner identity', async (t) => {
  const paths = runtimeFixture(t);
  const instanceId = 'runtime-installation-host-0001';
  const server = new RecoveryIpcServer({
    paths,
    handlers: {
      'recovery.ping': async () => ({ ready: true, pid: process.pid, instance_id: instanceId })
    },
    log: { warn() {} },
    instanceId,
    startedAt: new Date().toISOString()
  });
  t.after(() => server.stop());
  await server.start();

  const descriptor = loadRecoveryDescriptor(paths);
  const expected = paths.runtimeIdentity();
  assert.equal(descriptor.installation_id, expected.installation_id);
  assert.equal(descriptor.runtime_mode, 'development');

  const client = new RecoveryIpcClient({ paths });
  const ping = await client.ping({
    expectedOwnerPid: descriptor.owner_pid,
    expectedInstanceId: descriptor.instance_id,
    expectedInstallationId: descriptor.installation_id
  });
  assert.equal(ping.ready, true);

  await assert.rejects(
    client.ping({
      expectedOwnerPid: descriptor.owner_pid + 1,
      expectedInstanceId: descriptor.instance_id
    }),
    { code: 'RECOVERY_DESCRIPTOR_CHANGED' }
  );
});
