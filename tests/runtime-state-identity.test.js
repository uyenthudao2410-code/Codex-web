const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { runtimeStateHasLiveManagedProcess } = require('../electron/services/fullCleanActivation');
const { NativeService, requireExactStoredProcessIdentity } = require('../electron/services/nativeService');
const { TunnelService } = require('../electron/services/tunnelService');
const { RecoveryPlaneService } = require('../electron/services/recoveryPlaneService');
const { observeProcessIdentityAsync } = require('../electron/services/processIdentity');

const OLD_TOKEN = '134323501116672840';
const NEW_TOKEN = '134331475810000000';
const DEVICE = {
  version: 1,
  device_id: '12345678-1234-4123-8123-123456789abc',
  display_name: 'Relocated profile test',
  created_at: '2026-09-06T00:00:00.000Z'
};
const FOREIGN_DEVICE = '87654321-4321-4321-8321-cba987654321';
const live = (token = NEW_TOKEN, pid = process.pid) => ({ state: 'live', pid, process_start_token: token });

function fixture(t, state) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-relocated-state-'));
  const file = path.join(root, 'runtime-state.json');
  fs.writeFileSync(file, JSON.stringify(state));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return { file, paths: { stateFile: () => file, recoveryPlaneStateFile: () => file } };
}

for (const prefix of ['native', 'tunnel']) {
  test(`stopped-runtime census ignores a verified recycled ${prefix} PID without editing state`, async (t) => {
    const { file, paths } = fixture(t, { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: OLD_TOKEN });
    const before = fs.readFileSync(file, 'utf8');
    assert.equal(await runtimeStateHasLiveManagedProcess(paths, async () => live()), false);
    assert.equal(fs.readFileSync(file, 'utf8'), before);
    assert.doesNotThrow(() => process.kill(process.pid, 0));
  });

  test(`stopped-runtime census still blocks the exact live ${prefix} owner`, async (t) => {
    const { paths } = fixture(t, { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: NEW_TOKEN });
    assert.equal(await runtimeStateHasLiveManagedProcess(paths, async () => live()), true);
  });

  test(`stopped-runtime census fails closed on unverified ${prefix} identity`, async (t) => {
    const { file, paths } = fixture(t, { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: OLD_TOKEN });
    const before = fs.readFileSync(file, 'utf8');
    await assert.rejects(async () => runtimeStateHasLiveManagedProcess(paths, async () => ({ state: 'unavailable' })),
      { code: `${prefix.toUpperCase()}_PROCESS_IDENTITY_UNVERIFIED` });
    assert.equal(fs.readFileSync(file, 'utf8'), before);
  });
}

test('stored identity distinguishes a replaced process from unavailable or malformed evidence', async () => {
  const receipt = { pid: process.pid, processStartToken: OLD_TOKEN };
  assert.equal(await requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => live() }), null);
  assert.equal(await requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => ({ state: 'absent', pid: process.pid }) }), null);
  for (const observed of [live(null), live(NEW_TOKEN, process.pid + 1), { state: 'unavailable' }]) {
    await assert.rejects(requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => observed }),
      { code: 'PROCESS_PROCESS_IDENTITY_UNVERIFIED' });
  }
  await assert.rejects(requireExactStoredProcessIdentity({ ...receipt, processStartToken: null }, { processIdentityObserver: async () => live() }),
    { code: 'PROCESS_PROCESS_IDENTITY_UNVERIFIED' });
  await assert.rejects(requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => { throw new Error('probe unavailable'); } }),
    { code: 'PROCESS_PROCESS_IDENTITY_UNVERIFIED' });
});

test('stopped-runtime census checks the tunnel even when the native PID was recycled', async (t) => {
  const { paths } = fixture(t, { nativePid: process.pid, nativeProcessStartToken: OLD_TOKEN, tunnelPid: process.pid, tunnelProcessStartToken: NEW_TOKEN });
  assert.equal(await runtimeStateHasLiveManagedProcess(paths, async () => live()), true);
});

test('a denied PID liveness probe is not treated as proof that the process exited', async (t) => {
  t.mock.method(process, 'kill', () => { throw Object.assign(new Error('access denied'), { code: 'EPERM' }); });
  const receipt = { pid: process.pid, processStartToken: NEW_TOKEN };
  assert.deepEqual(await requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => live() }),
    { pid: process.pid, process_start_token: NEW_TOKEN });
  await assert.rejects(requireExactStoredProcessIdentity(receipt, { processIdentityObserver: async () => ({ state: 'unavailable', pid: process.pid }) }),
    { code: 'PROCESS_PROCESS_IDENTITY_UNVERIFIED' });
});

test('stopped-runtime census does not probe empty or invalid PIDs', async (t) => {
  const { paths } = fixture(t, { nativePid: 0, tunnelPid: -1 });
  assert.equal(await runtimeStateHasLiveManagedProcess(paths, async () => { throw new Error('invalid PID must not be probed'); }), false);
});

test('stopped-runtime census uses the real OS start token without mutating a relocated profile', {
  skip: !['win32', 'linux'].includes(process.platform)
}, async (t) => {
  const observed = await observeProcessIdentityAsync(process.pid);
  assert.equal(observed.state, 'live');
  const stale = (BigInt(observed.process_start_token) + 1n).toString();
  const { file, paths } = fixture(t, { nativePid: process.pid, nativeProcessStartToken: stale });
  const before = fs.readFileSync(file, 'utf8');
  assert.equal(await runtimeStateHasLiveManagedProcess(paths), false);
  assert.equal(fs.readFileSync(file, 'utf8'), before);
  fs.writeFileSync(file, JSON.stringify({ nativePid: process.pid, nativeProcessStartToken: observed.process_start_token }));
  assert.equal(await runtimeStateHasLiveManagedProcess(paths), true);
});

for (const [prefix, Service] of [['native', NativeService], ['tunnel', TunnelService]]) {
  function service(paths, observer, terminated) {
    const device = { deviceId: DEVICE.device_id, deviceInstanceId: 'relocated-instance-0001' };
    const options = { processIdentityObserver: observer, exactProcessTerminator: async (identity) => terminated.push(identity) };
    // Both services take the runtime device envelope used by the orchestrator.
    return Service === NativeService
      ? new Service({ info() {} }, paths, { status() { return {}; } }, device, options)
      : new Service({ info() {} }, paths, device, options);
  }

  test(`${prefix} reconciles only the stale receipt from another installation, never its recycled PID`, async (t) => {
    const state = { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: OLD_TOKEN, [`${prefix}DeviceId`]: FOREIGN_DEVICE, untouched: 'preserve' };
    const { file, paths } = fixture(t, state);
    const terminated = [];
    const runtime = service(paths, async () => live(), terminated);
    assert.equal(await runtime.ownedIdentity(state), null, 'cold-start ownership must ignore the retired process');
    assert.equal(await runtime.stop(), false);
    assert.deepEqual(terminated, []);
    const after = JSON.parse(fs.readFileSync(file, 'utf8'));
    assert.equal(after[`${prefix}Pid`], null);
    assert.equal(after[`${prefix}ProcessStartToken`], null);
    assert.equal(after.untouched, 'preserve');
    assert.doesNotThrow(() => process.kill(process.pid, 0));
  });

  test(`${prefix} stale receipt cleanup preserves a concurrent replacement`, async (t) => {
    const state = { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: OLD_TOKEN };
    const { file, paths } = fixture(t, state);
    const replacement = { ...state, [`${prefix}ProcessStartToken`]: NEW_TOKEN };
    const terminated = [];
    const runtime = service(paths, async () => { fs.writeFileSync(file, JSON.stringify(replacement)); return live(); }, terminated);
    await assert.rejects(runtime.stop(), { code: `${prefix.toUpperCase()}_PROCESS_STATE_CHANGED` });
    assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), replacement);
    assert.deepEqual(terminated, []);
  });

  test(`${prefix} still rejects an exact live owner from another device`, async (t) => {
    const state = { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: NEW_TOKEN, [`${prefix}DeviceId`]: FOREIGN_DEVICE };
    const { file, paths } = fixture(t, state);
    const terminated = [];
    const runtime = service(paths, async () => live(), terminated);
    await assert.rejects(runtime.stop(), { code: `${prefix.toUpperCase()}_PROCESS_FOREIGN_DEVICE` });
    assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), state);
    assert.deepEqual(terminated, []);
  });
}

for (const deviceId of [FOREIGN_DEVICE, null]) {
test(`Recovery Plane reconciles recycled MCP, Tunnel and candidate receipts (${deviceId ? 'foreign' : 'legacy'} device)`, async (t) => {
  const prefixes = ['recoveryMcp', 'recoveryTunnel', 'recoveryTunnelCandidate'];
  const state = { untouched: 'preserve' };
  for (const prefix of prefixes) Object.assign(state, { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: OLD_TOKEN, [`${prefix}DeviceId`]: deviceId });
  const { file, paths } = fixture(t, state);
  const terminated = [];
  const runtime = new RecoveryPlaneService({ paths, deviceIdentity: DEVICE, deviceInstanceId: 'relocated-instance-0001', processIdentityObserver: async () => live(), exactProcessTerminator: async (identity) => terminated.push(identity) });
  const migration = await runtime.preflightLegacyOwnershipMigration({}, 'unused', {
    mcpHealth: async () => { throw new Error('must not contact a recycled PID'); },
    tunnelReady: async () => { throw new Error('must not contact a recycled PID'); }
  });
  assert.equal(migration.required, false);
  assert.equal(await runtime.stop(), true);
  assert.deepEqual(terminated, []);
  const after = JSON.parse(fs.readFileSync(file, 'utf8'));
  for (const prefix of prefixes) {
    assert.equal(after[`${prefix}Pid`], null);
    assert.equal(after[`${prefix}ProcessStartToken`], null);
  }
  assert.equal(after.untouched, 'preserve');
  assert.doesNotThrow(() => process.kill(process.pid, 0));
});
}

test('Recovery Plane stale receipt cleanup preserves a concurrent replacement', async (t) => {
  const state = { recoveryMcpPid: process.pid, recoveryMcpProcessStartToken: OLD_TOKEN };
  const { file, paths } = fixture(t, state);
  const replacement = { ...state, recoveryMcpProcessStartToken: NEW_TOKEN };
  const terminated = [];
  const runtime = new RecoveryPlaneService({ paths, processIdentityObserver: async () => {
    fs.writeFileSync(file, JSON.stringify(replacement));
    return live();
  }, exactProcessTerminator: async (identity) => terminated.push(identity) });
  await assert.rejects(runtime.stop(), { code: 'RECOVERY_PROCESS_STATE_CHANGED' });
  assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), replacement);
  assert.deepEqual(terminated, []);
});

test('Recovery migration still rejects exact live foreign-device owners', async (t) => {
  for (const prefix of ['recoveryMcp', 'recoveryTunnel', 'recoveryTunnelCandidate']) {
    const state = { [`${prefix}Pid`]: process.pid, [`${prefix}ProcessStartToken`]: NEW_TOKEN, [`${prefix}DeviceId`]: FOREIGN_DEVICE };
    const { file, paths } = fixture(t, state);
    const runtime = new RecoveryPlaneService({ paths, deviceIdentity: DEVICE, deviceInstanceId: 'relocated-instance-0001', processIdentityObserver: async () => live() });
    await assert.rejects(runtime.preflightLegacyOwnershipMigration({}, 'unused'),
      { code: prefix === 'recoveryMcp' ? 'RECOVERY_MCP_FOREIGN_DEVICE' : 'RECOVERY_TUNNEL_FOREIGN_DEVICE' });
    assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), state);
  }
});
