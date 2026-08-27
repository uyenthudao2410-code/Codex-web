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
