const fs = require('node:fs');
const path = require('node:path');
const { app } = require('electron');
const { SettingsStore } = require('../electron/services/settingsStore');
const { SecretStore } = require('../electron/services/secretStore');
const { LogService } = require('../electron/services/logService');
const { NativeService, isAlive, P5_A0_SEED_ENV, P5_A0_SEED_SECRET } = require('../electron/services/nativeService');
const { readJson } = require('../electron/services/jsonStore');
const { configureRuntimePaths, stateFile, deviceFile } = require('../electron/paths');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { run } = require('../electron/services/commandRunner');
const { canConnect } = require('../electron/services/environmentService');
const { probeMcp } = require('../electron/services/runtimeOrchestrator');
const { readDeviceIdentity, runtimeDeviceIdentity } = require('../electron/services/deviceIdentity');
const { controlledRestartGuard, controlledRestartAppRootGuard, controlledRestartOwnerGuard, samePath } = require('../electron/services/controlledRestartGuard');

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 && index + 1 < process.argv.length ? process.argv[index + 1] : '';
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForPort(port, shouldListen, attempts = 40) {
  for (let index = 0; index < attempts; index += 1) {
    const listening = await canConnect('127.0.0.1', port, 250);
    if (listening === shouldListen) return true;
    await sleep(250);
  }
  return false;
}

function reportPath(workspace, label) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const directory = path.join(workspace, '.coding-tools', 'orchestration', 'reports', 'runtime-restarts');
  fs.mkdirSync(directory, { recursive: true });
  return path.join(directory, `runtime-restart-${label}-${stamp}.json`);
}

async function main() {
  const expectedWorkspace = argValue('--expect-workspace');
  const expectedUserData = argValue('--expect-user-data');
  const expectedAppRoot = argValue('--expect-app-root');
  const restart = process.argv.includes('--restart');
  const appRoot = path.resolve(__dirname, '..');
  const resourcesRoot = path.join(appRoot, 'resources');
  const appRootGuard = controlledRestartAppRootGuard({ expectedAppRoot, actualAppRoot: appRoot, resourcesRoot });
  if (!appRootGuard.ok) {
    console.log(JSON.stringify({
      evidence_class: 'local_controlled_restart_probe',
      captured_at: new Date().toISOString(),
      app_root: appRoot,
      expected_app_root_match: false,
      mode: restart ? 'restart' : 'probe',
      ok: false,
      error: appRootGuard.code
    }, null, 2));
    process.exitCode = 2;
    return;
  }
  const userData = app.getPath('userData');
  configureRuntimePaths(createRuntimePaths({
    dataRoot: userData,
    appRoot,
    resourcesRoot,
    runtimeMode: 'development',
    executablePath: process.execPath
  }));
  const settingsStore = new SettingsStore();
  const settings = settingsStore.load();
  const state = readJson(stateFile(), {});
  const guard = controlledRestartGuard({
    expectedWorkspace,
    expectedUserData,
    configuredWorkspace: settings.workspace,
    actualUserData: userData
  });
  const probe = {
    evidence_class: 'local_controlled_restart_probe',
    captured_at: new Date().toISOString(),
    user_data: userData,
    app_root: appRoot,
    resources_root: resourcesRoot,
    configured_workspace: settings.workspace || '',
    expected_workspace_match: Boolean(String(settings.workspace || '').trim() && String(expectedWorkspace || '').trim() && samePath(settings.workspace, expectedWorkspace)),
    expected_user_data_match: Boolean(String(userData || '').trim() && String(expectedUserData || '').trim() && samePath(userData, expectedUserData)),
    expected_app_root_match: true,
    native_pid: Number.isInteger(state.nativePid) ? state.nativePid : null,
    native_alive: isAlive(state.nativePid),
    native_port: Number(settings.mcpPort),
    tunnel_pid_present: Number.isInteger(state.tunnelPid),
    mode: restart ? 'restart' : 'probe'
  };
  if (!guard.ok) {
    probe.ok = false;
    probe.error = guard.code;
    console.log(JSON.stringify(probe, null, 2));
    process.exitCode = 2;
    return;
  }
  if (!restart) {
    probe.ok = true;
    console.log(JSON.stringify(probe, null, 2));
    return;
  }
  if (!probe.native_alive || !probe.native_pid) {
    throw new Error('Owned MCP process is not alive; refusing controlled restart.');
  }
  const device = runtimeDeviceIdentity(readDeviceIdentity(deviceFile()), state.nativeDeviceInstanceId);
  const ownerGuard = controlledRestartOwnerGuard({ state, device });
  if (!ownerGuard.ok) {
    throw Object.assign(new Error('Native MCP device ownership does not match the live product runtime.'), { code: ownerGuard.code });
  }
  const secretStore = new SecretStore();
  const externallyProvisionedP5Seed = String(process.env[P5_A0_SEED_ENV] || '');
  if (externallyProvisionedP5Seed) secretStore.set(P5_A0_SEED_SECRET, externallyProvisionedP5Seed);
  const token = secretStore.get('mcpAuthToken');
  if (!token) throw new Error('MCP auth token is unavailable in the matched Electron userData; refusing restart.');
  const p5Seed = secretStore.get(P5_A0_SEED_SECRET);
  const oldPid = probe.native_pid;
  await run('taskkill.exe', ['/PID', String(oldPid), '/F']);
  if (!(await waitForPort(settings.mcpPort, false))) {
    throw new Error(`MCP port ${settings.mcpPort} did not close after stopping owned PID ${oldPid}.`);
  }
  const native = new NativeService(new LogService(), undefined, null, device);
  const started = await native.start(settings, token, () => {}, { p5Seed });
  let ready = false;
  for (let index = 0; index < 40; index += 1) {
    if (await probeMcp(settings.mcpPort, token, settings.workspace, device.deviceId)) {
      ready = true;
      break;
    }
    await sleep(250);
  }
  const nextState = readJson(stateFile(), {});
  const result = {
    ...probe,
    ok: ready,
    old_native_pid: oldPid,
    new_native_pid: started.pid || nextState.nativePid || null,
    pid_changed: Number(started.pid || nextState.nativePid || 0) !== oldPid,
    mcp_ready: ready,
    tunnel_pid_preserved: state.tunnelPid === nextState.tunnelPid,
    completed_at: new Date().toISOString()
  };
  const target = reportPath(settings.workspace, 'mcp-only');
  fs.writeFileSync(target, JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify({ ...result, report: target }, null, 2));
  if (!ready) process.exitCode = 3;
}

app.whenReady().then(main).catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message, code: error?.code || 'CONTROLLED_RESTART_FAILED' }));
  process.exitCode = 1;
}).finally(() => {
  setTimeout(() => app.quit(), 50);
});
