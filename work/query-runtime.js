const { createDevelopmentPaths } = require('../scripts/dev-ui-lifecycle');
const { loadRecoveryDescriptor, RecoveryIpcClient } = require('../electron/services/recoveryIpc');
const { descriptorRequestOptions } = require('../electron/services/recoveryHostLauncher');

(async () => {
  const paths = createDevelopmentPaths();
  const descriptor = loadRecoveryDescriptor(paths);
  const client = new RecoveryIpcClient({ paths });
  const options = descriptorRequestOptions(descriptor);
  for (const action of ['runtime.activation_epoch_status', 'runtime.lightweight_snapshot', 'logs.read']) {
    try {
      const result = await client.call(action, action === 'logs.read' ? [200] : [], options);
      console.log(`ACTION ${action} ${JSON.stringify(result)}`);
    } catch (error) {
      console.log(`ERR ${action} ${error.code || ''} ${error.message || error} ${JSON.stringify(error.details || {})}`);
    }
  }
})();
