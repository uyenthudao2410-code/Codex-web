const path = require('node:path');
const { createInstallationIdentity } = require('./runtimeIdentity');

function requiredRoot(value, name) {
  const text = String(value || '').trim();
  if (!text) throw new Error(`${name} is required.`);
  const resolved = path.resolve(text);
  if (!path.isAbsolute(resolved)) throw new Error(`${name} must be an absolute path.`);
  return resolved;
}

function optionalArtifactId(value, name) {
  const text = String(value || '').trim();
  if (!text) return '';
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/.test(text)) {
    throw Object.assign(new Error(`${name} is invalid.`), { code: 'RUNTIME_ARTIFACT_ID_INVALID' });
  }
  return text;
}

class RuntimePaths {
  constructor({ dataRoot, resourcesRoot, appRoot, runtimeMode = 'development', executablePath = process.execPath }) {
    this.dataRootPath = requiredRoot(dataRoot, 'dataRoot');
    this.resourcesRootPath = requiredRoot(resourcesRoot, 'resourcesRoot');
    this.appRootPath = requiredRoot(appRoot || path.dirname(this.resourcesRootPath), 'appRoot');
    this.executablePathValue = requiredRoot(executablePath, 'executablePath');
    this.runtimeModeValue = runtimeMode === 'packaged' ? 'packaged' : 'development';
    this.runtimeIdentityValue = createInstallationIdentity({
      mode: this.runtimeModeValue,
      appRoot: this.appRootPath,
      resourcesRoot: this.resourcesRootPath,
      executablePath: this.executablePathValue
    });
  }

  dataRoot() { return this.dataRootPath; }
  resourcesRoot() { return this.resourcesRootPath; }
  appRoot() { return this.appRootPath; }
  executablePath() { return this.executablePathValue; }
  runtimeMode() { return this.runtimeModeValue; }
  runtimeIdentity() { return this.runtimeIdentityValue; }
  deviceFile() { return path.join(this.dataRootPath, 'device.json'); }
  settingsFile() { return path.join(this.dataRootPath, 'settings.json'); }
  secretsFile() { return path.join(this.dataRootPath, 'secrets.bin'); }
  stateFile() { return path.join(this.dataRootPath, 'runtime-state.json'); }
  hubProxyDescriptorFile() { return path.join(this.dataRootPath, 'execution-hub-proxy.json'); }
  supervisorRequestFile() { return path.join(this.dataRootPath, 'runtime-supervisor-request.json'); }
  recoveryHostDescriptorFile() { return path.join(this.dataRootPath, 'recovery-host.json'); }
  recoveryHostLockFile() { return path.join(this.dataRootPath, 'recovery-host.lock'); }
  // A stale Recovery Host cannot safely execute a full-clean request.  The
  // bootstrap envelope is a small, integrity-bound control-plane handoff used
  // to start the current checkout before the activation coordinator runs.  It
  // intentionally lives beside (and never replaces) the durable activation
  // epoch, settings, identity, or orchestration ledger.
  recoveryHostBootstrapFile(operationId = '') {
    const suffix = optionalArtifactId(operationId, 'Recovery Host bootstrap operation ID');
    return path.join(this.dataRootPath, suffix
      ? `recovery-host-bootstrap.${suffix}.json`
      : 'recovery-host-bootstrap.json');
  }
  recoveryHostBootstrapResultFile(operationId = '') {
    const suffix = optionalArtifactId(operationId, 'Recovery Host bootstrap result operation ID');
    return path.join(this.dataRootPath, suffix
      ? `recovery-host-bootstrap.${suffix}.result.json`
      : 'recovery-host-bootstrap.result.json');
  }
  recoveryActionsFile() { return path.join(this.dataRootPath, 'recovery-actions.json'); }
  // Activation epochs are durable control-plane state.  Keep this separate
  // from runtime-state.json and, critically, from the workspace's canonical
  // orchestration ledger: a clean activation rotates process identity without
  // deleting or rewriting durable task truth.
  activationEpochFile() { return path.join(this.dataRootPath, 'activation-epoch.json'); }
  acceptedCodeActivationFile() { return path.join(this.dataRootPath, 'accepted-code-activation.json'); }
  // Keep break-glass process identity outside primary runtime-state.json so host adoption cannot erase it.
  recoveryPlaneStateFile() { return path.join(this.dataRootPath, 'recovery-plane-state.json'); }
  logFile() { return path.join(this.dataRootPath, 'logs', 'assistant.log'); }
  mcpLogFile() { return path.join(this.dataRootPath, 'logs', 'mcp.log'); }
  tunnelLogFile() { return path.join(this.dataRootPath, 'logs', 'tunnel.log'); }
  recoveryMcpLogFile() { return path.join(this.dataRootPath, 'logs', 'recovery-mcp.log'); }
  recoveryTunnelLogFile() { return path.join(this.dataRootPath, 'logs', 'recovery-tunnel.log'); }
  tunnelExecutable() { return path.join(this.resourcesRootPath, 'tools', 'tunnel-client.exe'); }
  portablePython() { return path.join(this.resourcesRootPath, 'native-python', 'python.exe'); }
  tunnelCodexAppServerLauncher() { return path.join(this.resourcesRootPath, 'tunnel-client', 'codex_app_server_launcher.py'); }
  recoveryMcpScript() { return path.join(this.resourcesRootPath, 'recovery-mcp', 'recovery_mcp.py'); }
}

function createRuntimePaths(options) {
  return new RuntimePaths(options);
}

function createElectronRuntimePaths(app, processResourcesPath = process.resourcesPath, executablePath = process.execPath) {
  if (!app) throw new Error('Electron app is required to resolve runtime paths.');
  return createRuntimePaths({
    dataRoot: app.getPath('userData'),
    appRoot: app.getAppPath(),
    resourcesRoot: app.isPackaged
      ? path.join(processResourcesPath, 'resources')
      : path.join(app.getAppPath(), 'resources'),
    runtimeMode: app.isPackaged ? 'packaged' : 'development',
    executablePath
  });
}

module.exports = { RuntimePaths, createRuntimePaths, createElectronRuntimePaths };
