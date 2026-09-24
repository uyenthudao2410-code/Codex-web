const test = require('node:test');
const assert = require('node:assert/strict');

const {
  parseMxcSandboxProbe,
  parseMxcChildProcessProbe,
  parseMxcWindowsSandboxChildProcessProbe
} = require('../electron/services/controlPlaneEnrollment');

test('MXC capability probe does not stand in for the nested-process runtime probe', () => {
  const base = parseMxcSandboxProbe(JSON.stringify({
    tier: 'base-container',
    needsDaclAugmentation: false,
    probes: {
      baseContainerApiPresent: true,
      baseContainerSupportsDenyPaths: true
    },
    warnings: []
  }));
  assert.equal(base.state, 'available');

  assert.deepEqual(parseMxcChildProcessProbe(JSON.stringify({
    probe: 'mxc_nested_process_v1', available: true, reason: null
  })), { available: true, reason: null });
  assert.deepEqual(parseMxcChildProcessProbe(JSON.stringify({
    probe: 'mxc_nested_process_v1', available: false,
    reason: 'WINDOWS_CHILD_PROCESS_ENOENT'
  })), { available: false, reason: 'WINDOWS_CHILD_PROCESS_ENOENT' });
  assert.throws(() => parseMxcChildProcessProbe(JSON.stringify({
    probe: 'mxc_nested_process_v1', available: false, reason: 'permission denied'
  })), { code: 'CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID' });

  assert.deepEqual(parseMxcWindowsSandboxChildProcessProbe(JSON.stringify({
    probe: 'mxc_wsb_child_process_v1', available: true, reason: null
  })), { available: true, reason: null });
  assert.deepEqual(parseMxcWindowsSandboxChildProcessProbe(JSON.stringify({
    probe: 'mxc_wsb_child_process_v1', available: false, reason: 'SANDBOX_TEARDOWN_UNCONFIRMED'
  })), { available: false, reason: 'SANDBOX_TEARDOWN_UNCONFIRMED' });
  assert.throws(() => parseMxcWindowsSandboxChildProcessProbe(JSON.stringify({
    probe: 'mxc_wsb_child_process_v1', available: false, reason: 'access denied'
  })), { code: 'CONTROL_PLANE_EXEC_SANDBOX_PROBE_INVALID' });
});
