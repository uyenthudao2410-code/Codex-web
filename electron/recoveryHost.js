const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService } = require('./services/environmentService');
const { RecoveryHost } = require('./services/recoveryHost');
const { SemanticMcpHealthWatchdog } = require('./services/mcpSemanticHealth');
const { createElectronRuntimePaths } = require('./services/runtimePaths');
const { configureRuntimePaths } = require('./paths');
const { spawnRecoveryHost, spawnElectronUi } = require('./services/recoveryHostLauncher');

function replacementArguments(argv = process.argv) {
  const old = argv.find((item) => String(item).startsWith('--replace-recovery-host='));
  const operation = argv.find((item) => String(item).startsWith('--activation-operation='));
  const epoch = argv.find((item) => String(item).startsWith('--activation-epoch-id='));
  if (!old && !operation && !epoch) return null;
  const expectedOldInstanceId = String(old || '').slice('--replace-recovery-host='.length);
  const operationId = String(operation || '').slice('--activation-operation='.length);
  const activationEpochId = String(epoch || '').slice('--activation-epoch-id='.length);
  const valid = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
  const validEpoch = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
  if ((old && !valid.test(expectedOldInstanceId))
    || (operation && !valid.test(operationId))
    || (!old && operation)
    || (old && !operation)
    || (epoch && !validEpoch.test(activationEpochId))) {
    throw Object.assign(new Error('Invalid Recovery Host replacement arguments.'), { code: 'RECOVERY_REPLACEMENT_ARGUMENTS_INVALID' });
  }
  return {
    ...(old ? { expectedOldInstanceId } : {}),
    ...(operation ? { operationId } : {}),
    ...(epoch ? { activationEpochId } : {})
  };
}

async function startRecoveryHostApplication(app) {
  const paths = createElectronRuntimePaths(app);
  configureRuntimePaths(paths);
  const settings = new SettingsStore(paths);
  const secrets = new SecretStore(paths);
  const log = new LogService(paths);
  const environment = new EnvironmentService(paths);
  let replacement;
  try { replacement = replacementArguments(); }
  catch (error) {
    log.error(error.message, { stage: 'recovery-host-replacement-arguments', code: error.code });
    app.exit(1);
    return null;
  }
  const host = new RecoveryHost({
    paths,
    settings,
    secrets,
    environment,
    log,
    replacement,
    spawnRecoveryReplacement: (options) => spawnRecoveryHost(app, undefined, options),
    spawnElectronUi: (options) => spawnElectronUi(app, undefined, options),
    exitProcess: (code) => app.exit(code)
  });

  try {
    await host.start();
  } catch (error) {
    if (error?.code === 'RECOVERY_HOST_ALREADY_RUNNING') {
      app.quit();
      return null;
    }
    log.error(error.message, { stage: 'recovery-host-start', code: error?.code || '' });
    app.exit(1);
    return null;
  }

  const semanticWatchdog = new SemanticMcpHealthWatchdog({
    settings,
    secrets,
    orchestrator: host.orchestrator,
    log,
    isSuppressed: () => !host.running || host.handoffStarted
  });
  semanticWatchdog.start();

  let shutdownStarted = false;
  app.on('before-quit', (event) => {
    if (shutdownStarted) return;
    shutdownStarted = true;
    event.preventDefault();
    semanticWatchdog.stop();
    host.stop().finally(() => app.quit());
  });
  return host;
}

module.exports = { startRecoveryHostApplication, replacementArguments };
