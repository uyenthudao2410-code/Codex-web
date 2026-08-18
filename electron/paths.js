const { createElectronRuntimePaths } = require('./services/runtimePaths');

let resolved = null;

function current() {
  if (!resolved) {
    const { app } = require('electron');
    resolved = createElectronRuntimePaths(app);
  }
  return resolved;
}

function configureRuntimePaths(paths) {
  resolved = paths;
  return resolved;
}

module.exports = {
  configureRuntimePaths,
  appRoot: () => current().appRoot(),
  resourcesRoot: () => current().resourcesRoot(),
  dataRoot: () => current().dataRoot(),
  executablePath: () => current().executablePath(),
  runtimeMode: () => current().runtimeMode(),
  runtimeIdentity: () => current().runtimeIdentity(),
  deviceFile: () => current().deviceFile(),
  settingsFile: () => current().settingsFile(),
  secretsFile: () => current().secretsFile(),
  stateFile: () => current().stateFile(),
  hubProxyDescriptorFile: () => current().hubProxyDescriptorFile(),
  supervisorRequestFile: () => current().supervisorRequestFile(),
  recoveryHostDescriptorFile: () => current().recoveryHostDescriptorFile(),
  recoveryHostLockFile: () => current().recoveryHostLockFile(),
  recoveryActionsFile: () => current().recoveryActionsFile(),
  logFile: () => current().logFile(),
  mcpLogFile: () => current().mcpLogFile(),
  tunnelLogFile: () => current().tunnelLogFile(),
  tunnelExecutable: () => current().tunnelExecutable(),
  portablePython: () => current().portablePython()
};
