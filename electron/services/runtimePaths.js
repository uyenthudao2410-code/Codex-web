const path = require('node:path');

function requiredRoot(value, name) {
  const text = String(value || '').trim();
  if (!text) throw new Error(`${name} is required.`);
  const resolved = path.resolve(text);
  if (!path.isAbsolute(resolved)) throw new Error(`${name} must be an absolute path.`);
  return resolved;
}

class RuntimePaths {
  constructor({ dataRoot, resourcesRoot, appRoot }) {
    this.dataRootPath = requiredRoot(dataRoot, 'dataRoot');
    this.resourcesRootPath = requiredRoot(resourcesRoot, 'resourcesRoot');
    this.appRootPath = requiredRoot(appRoot || path.dirname(this.resourcesRootPath), 'appRoot');
  }

  dataRoot() { return this.dataRootPath; }
  resourcesRoot() { return this.resourcesRootPath; }
  appRoot() { return this.appRootPath; }
  settingsFile() { return path.join(this.dataRootPath, 'settings.json'); }
  secretsFile() { return path.join(this.dataRootPath, 'secrets.bin'); }
  stateFile() { return path.join(this.dataRootPath, 'runtime-state.json'); }
  hubProxyDescriptorFile() { return path.join(this.dataRootPath, 'execution-hub-proxy.json'); }
  supervisorRequestFile() { return path.join(this.dataRootPath, 'runtime-supervisor-request.json'); }
  recoveryHostDescriptorFile() { return path.join(this.dataRootPath, 'recovery-host.json'); }
  recoveryHostLockFile() { return path.join(this.dataRootPath, 'recovery-host.lock'); }
  recoveryActionsFile() { return path.join(this.dataRootPath, 'recovery-actions.json'); }
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
  recoveryMcpScript() { return path.join(this.resourcesRootPath, 'recovery-mcp', 'recovery_mcp.py'); }
}

function createRuntimePaths(options) {
  return new RuntimePaths(options);
}

function createElectronRuntimePaths(app, processResourcesPath = process.resourcesPath) {
  if (!app) throw new Error('Electron app is required to resolve runtime paths.');
  return createRuntimePaths({
    dataRoot: app.getPath('userData'),
    appRoot: app.getAppPath(),
    resourcesRoot: app.isPackaged
      ? path.join(processResourcesPath, 'resources')
      : path.join(app.getAppPath(), 'resources')
  });
}

module.exports = { RuntimePaths, createRuntimePaths, createElectronRuntimePaths };
