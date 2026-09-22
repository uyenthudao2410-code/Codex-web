const test = require('node:test');
const assert = require('node:assert/strict');

const { HealthService } = require('../electron/services/healthService');

test('health repair uses explicit soft recovery and cannot activate newer source', async () => {
  const current = {
    workspace: 'E:\\workspace',
    tunnelId: 'tunnel_primary',
    mcpPort: 18766,
    healthPort: 18082
  };
  const restartCalls = [];
  const service = new HealthService({
    settings: {
      load: () => ({ ...current }),
      save: (patch) => Object.assign(current, patch)
    },
    secrets: {
      status: () => ({ mcpAuthToken: true, runtimeApiKey: true })
    },
    environment: {
      inspect: async () => ({
        workspace: { exists: true },
        python: { installed: true, version: '3.12' },
        tunnelClient: { installed: true },
        ports: { mcpListening: true, tunnelListening: true }
      })
    },
    orchestrator: {
      native: { status: async () => true },
      tunnel: { status: async () => true },
      activationEpochId: 'epoch-current',
      restart: async (options) => { restartCalls.push(options); }
    }
  });

  const result = await service.repair();

  assert.deepEqual(restartCalls, [{
    automatic: true,
    mode: 'soft_recovery',
    reason: 'health_repair'
  }]);
  assert.equal(result.unresolved.length, 0);
  assert.equal(result.actions.includes('Đã khởi động lại MCP và Tunnel'), true);
});

test('central health does not require a Windows Runtime Key, Tunnel or Tunnel port', async () => {
  const current = {
    executionRole: 'central_executor',
    workspace: 'E:\\workspace',
    mcpPort: 18766,
    healthPort: 18082
  };
  let tunnelProbeCalls = 0;
  const service = new HealthService({
    settings: { load: () => ({ ...current }), save: (patch) => Object.assign(current, patch) },
    secrets: { status: () => ({ mcpAuthToken: true, runtimeApiKey: false }) },
    environment: {
      inspect: async () => ({
        workspace: { exists: true },
        python: { installed: true, version: '3.12' },
        tunnelClient: { installed: false },
        ports: { mcpListening: true, tunnelListening: false }
      })
    },
    orchestrator: {
      native: { status: async () => true },
      tunnel: { status: async () => { tunnelProbeCalls += 1; return false; } },
      snapshot: async () => ({ status: { centralConnected: true, authorityReady: true, centralStatusReason: null } })
    }
  });

  const result = await service.inspect();

  assert.equal(result.healthy, true);
  assert.equal(result.executionRole, 'central_executor');
  assert.equal(tunnelProbeCalls, 0);
  assert.deepEqual(result.checks.map((item) => item.id), ['workspace', 'runtime', 'mcp-port', 'mcp', 'control-plane-route']);
  assert.equal(result.checks.find((item) => item.id === 'control-plane-route').ok, true);
});

test('central repair reports missing Ubuntu authority without restarting or inventing direct credentials', async () => {
  const current = {
    executionRole: 'central_executor',
    workspace: 'E:\\workspace',
    mcpPort: 18766,
    healthPort: 18082
  };
  const restartCalls = [];
  const service = new HealthService({
    settings: { load: () => ({ ...current }), save: (patch) => Object.assign(current, patch) },
    secrets: { status: () => ({ mcpAuthToken: true, runtimeApiKey: false }) },
    environment: {
      inspect: async () => ({
        workspace: { exists: true },
        python: { installed: true, version: '3.12' },
        tunnelClient: { installed: false },
        ports: { mcpListening: true, tunnelListening: false }
      })
    },
    orchestrator: {
      native: { status: async () => true },
      tunnel: { status: async () => { throw new Error('must not probe central tunnel'); } },
      snapshot: async () => ({ status: { centralConnected: false, authorityReady: false, centralStatusReason: 'LOCAL_EXECUTOR_NOT_READY' } }),
      restart: async (options) => restartCalls.push(options)
    }
  });

  const result = await service.repair();

  assert.equal(restartCalls.length, 0);
  assert.deepEqual(result.unresolved, ['Hoàn tất pairing và quyền trên Ubuntu']);
  assert.equal(result.checks.some((item) => item.id === 'runtime-key'), false);
  assert.equal(result.checks.some((item) => item.id === 'tunnel-id'), false);
});
