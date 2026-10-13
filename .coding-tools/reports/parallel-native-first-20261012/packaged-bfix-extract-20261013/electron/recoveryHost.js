const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService } = require('./services/environmentService');
const { RecoveryHost } = require('./services/recoveryHost');
const { SemanticMcpHealthWatchdog } = require('./services/mcpSemanticHealth');
const { createElectronRuntimePaths } = require('./services/runtimePaths');
const { configureRuntimePaths } = require('./paths');
const { spawnRecoveryHost, spawnElectronUi } = require('./services/recoveryHostLauncher');
const { readBootstrapEnvelope, writeBootstrapResult } = require('./services/recoveryBootstrap');

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

function bootstrapArguments(argv = process.argv) {
  const values = (Array.isArray(argv) ? argv : [])
    .filter((item) => String(item || '').startsWith('--recovery-bootstrap='));
  if (!values.length) return null;
  if (values.length !== 1) throw Object.assign(new Error('Recovery Host bootstrap arguments are ambiguous.'), { code: 'RECOVERY_BOOTSTRAP_ARGUMENTS_INVALID' });
  const operationId = String(values[0]).slice('--recovery-bootstrap='.length).trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/.test(operationId)) {
    throw Object.assign(new Error('Invalid Recovery Host bootstrap operation identity.'), { code: 'RECOVERY_BOOTSTRAP_ARGUMENTS_INVALID' });
  }
  return { operationId };
}

async function startRecoveryHostApplication(app) {
  const paths = createElectronRuntimePaths(app);
  configureRuntimePaths(paths);
  const settings = new SettingsStore(paths);
  const secrets = new SecretStore(paths);
  const log = new LogService(paths);
  const environment = new EnvironmentService(paths);
  let replacement;
  let bootstrap;
  try { replacement = replacementArguments(); }
  catch (error) {
    log.error(error.message, { stage: 'recovery-host-replacement-arguments', code: error.code });
    app.exit(1);
    return null;
  }
  try {
    bootstrap = bootstrapArguments();
    if (bootstrap) bootstrap = readBootstrapEnvelope(paths, { bootstrapId: bootstrap.operationId });
  } catch (error) {
    if (bootstrap?.operationId) {
      try {
        writeBootstrapResult(paths, {
          operation_id: bootstrap.operationId,
          state: error?.code === 'RECOVERY_BOOTSTRAP_EXPIRED' ? 'expired' : 'failed',
          error: { code: error?.code || 'RECOVERY_BOOTSTRAP_INVALID', message: error?.message || String(error) }
        });
      } catch { /* preserve the bootstrap validation failure */ }
    }
    log.error(error.message, { stage: 'recovery-host-bootstrap-arguments', code: error.code || '' });
    app.exit(1);
    return null;
  }
  if (bootstrap && replacement) {
    const error = Object.assign(new Error('Recovery Host bootstrap and replacement arguments cannot be combined.'), {
      code: 'RECOVERY_BOOTSTRAP_ARGUMENTS_INVALID'
    });
    try {
      writeBootstrapResult(paths, {
        operation_id: bootstrap.operation_id,
        state: 'failed',
        error: { code: error.code, message: error.message }
      });
    } catch { /* preserve the argument failure */ }
    log.error(error.message, { stage: 'recovery-host-bootstrap-arguments', code: error.code });
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
    bootstrap,
    // Always bind replacement launches to the executable that belongs to this
    // checkout.  A detached Node worker may have `process.execPath` set to
    // node.exe; silently using that path would start the wrong runtime instead
    // of a real Electron Recovery Host.
    spawnRecoveryReplacement: (options) => spawnRecoveryHost(app, undefined, {
      ...options,
      executablePath: paths.executablePath()
    }),
    spawnElectronUi: (options) => spawnElectronUi(app, undefined, {
      ...options,
      executablePath: paths.executablePath()
    }),
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
    isSuppressed: () => {
      if (!host.running || host.handoffStarted || host.bootstrapBlocksAdmission?.()) return true;
      try {
        const epoch = host.fullCleanActivation?.current?.();
        return Boolean(epoch && epoch.state !== 'READY');
      } catch { return true; }
    }
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

module.exports = { startRecoveryHostApplication, replacementArguments, bootstrapArguments };
