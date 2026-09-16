#!/usr/bin/env node
'use strict';

// Resolve the one local Recovery IPC client context used by the control-plane
// node helper.  Development and installed Electron use distinct installation
// identities; this adapter never guesses one from a workspace path.

const fs = require('node:fs');
const path = require('node:path');

function adapterError(code) {
  return Object.assign(new Error(code), { code });
}

function text(value) {
  return String(value || '').trim();
}

function argumentValue(argv, name) {
  const values = [];
  for (let index = 0; index < argv.length; index += 1) {
    const value = String(argv[index] || '');
    if (value === name) values.push(String(argv[index + 1] || ''));
    else if (value.startsWith(`${name}=`)) values.push(value.slice(name.length + 1));
  }
  if (values.length > 1) throw adapterError('RUNTIME_ADAPTER_ARGUMENT_INVALID');
  return text(values[0]);
}

function parseRuntimeInvocation(argv = process.argv.slice(2)) {
  const runtimeMode = text(argumentValue(argv, '--runtime-mode') || 'development').toLowerCase();
  if (!['development', 'packaged'].includes(runtimeMode)) {
    throw adapterError('RUNTIME_ADAPTER_MODE_INVALID');
  }
  const appRoot = argumentValue(argv, '--project-root');
  if (runtimeMode === 'packaged' && appRoot) {
    throw adapterError('RUNTIME_ADAPTER_PACKAGED_ROOT_FORBIDDEN');
  }
  if (runtimeMode === 'development' && appRoot && !path.isAbsolute(appRoot)) {
    throw adapterError('PROJECT_ROOT_INVALID');
  }
  return { runtimeMode, appRoot: appRoot || null };
}

function developmentRuntime({ appRoot, dependencies = {} } = {}) {
  const lifecycle = dependencies.lifecycle || require('../../scripts/dev-ui-lifecycle');
  const ipc = dependencies.ipc || require('../../electron/services/recoveryIpc');
  const launcher = dependencies.launcher || require('../../electron/services/recoveryHostLauncher');
  const makePaths = dependencies.createDevelopmentPaths || lifecycle.createDevelopmentPaths;
  const root = appRoot || path.resolve(__dirname, '..', '..');
  return {
    mode: 'development',
    paths: makePaths({ appRoot: root }),
    RecoveryIpcClient: dependencies.RecoveryIpcClient || ipc.RecoveryIpcClient,
    loadRecoveryDescriptor: dependencies.loadRecoveryDescriptor || ipc.loadRecoveryDescriptor,
    descriptorMatchesInstallation: dependencies.descriptorMatchesInstallation || launcher.descriptorMatchesInstallation,
    descriptorRequestOptions: dependencies.descriptorRequestOptions || launcher.descriptorRequestOptions
  };
}

function packagedRuntime({ adapterDirectory = __dirname, dependencies = {} } = {}) {
  const resourcesRoot = path.resolve(adapterDirectory, '..');
  const appRoot = path.resolve(resourcesRoot, '..', 'app.asar');
  const appData = text(dependencies.appData || process.env.APPDATA);
  const executablePath = text(dependencies.executablePath || process.execPath);
  if (!appData || !path.isAbsolute(appData) || !executablePath || !path.isAbsolute(executablePath)) {
    throw adapterError('RUNTIME_ADAPTER_PACKAGED_ENVIRONMENT_INVALID');
  }
  if (!fs.existsSync(resourcesRoot) || !fs.existsSync(appRoot)) {
    throw adapterError('RUNTIME_ADAPTER_PACKAGED_LAYOUT_INVALID');
  }
  const runtimePaths = dependencies.runtimePaths || (dependencies.createRuntimePaths
    ? null : require(path.join(appRoot, 'electron/services/runtimePaths')));
  const ipc = dependencies.ipc || ((dependencies.RecoveryIpcClient && dependencies.loadRecoveryDescriptor)
    ? null : require(path.join(appRoot, 'electron/services/recoveryIpc')));
  const launcher = dependencies.launcher || ((dependencies.descriptorMatchesInstallation && dependencies.descriptorRequestOptions)
    ? null : require(path.join(appRoot, 'electron/services/recoveryHostLauncher')));
  const makePaths = dependencies.createRuntimePaths || runtimePaths.createRuntimePaths;
  return {
    mode: 'packaged',
    paths: makePaths({
      dataRoot: path.join(appData, 'web-mcp-assistant'),
      resourcesRoot,
      appRoot,
      runtimeMode: 'packaged',
      executablePath
    }),
    RecoveryIpcClient: dependencies.RecoveryIpcClient || ipc.RecoveryIpcClient,
    loadRecoveryDescriptor: dependencies.loadRecoveryDescriptor || ipc.loadRecoveryDescriptor,
    descriptorMatchesInstallation: dependencies.descriptorMatchesInstallation || launcher.descriptorMatchesInstallation,
    descriptorRequestOptions: dependencies.descriptorRequestOptions || launcher.descriptorRequestOptions
  };
}

function resolveRuntime(options = {}) {
  const mode = text(options.runtimeMode || 'development').toLowerCase();
  if (mode === 'development') return developmentRuntime(options);
  if (mode === 'packaged') return packagedRuntime(options);
  throw adapterError('RUNTIME_ADAPTER_MODE_INVALID');
}

module.exports = {
  adapterError,
  argumentValue,
  parseRuntimeInvocation,
  developmentRuntime,
  packagedRuntime,
  resolveRuntime
};
