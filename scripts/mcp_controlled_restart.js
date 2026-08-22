const fs = require('node:fs');
const path = require('node:path');
const { app } = require('electron');
const { SettingsStore } = require('../electron/services/settingsStore');
const { SecretStore } = require('../electron/services/secretStore');
const { LogService } = require('../electron/services/logService');
const { NativeService, isAlive } = require('../electron/services/nativeService');
const { readJson } = require('../electron/services/jsonStore');
const { stateFile } = require('../electron/paths');
const { run } = require('../electron/services/commandRunner');
const { canConnect } = require('../electron/services/environmentService');
const { probeMcp } = require('../electron/services/runtimeOrchestrator');
const { controlledRestartGuard, samePath } = require('../electron/services/controlledRestartGuard');

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
  const directory = path.join(workspace, 'resources', 'coding-tools-mcp', 'benchmarks', 'reports');
  fs.mkdirSync(directory, { recursive: true });
  return path.join(directory, `runtime-restart-${label}-${stamp}.json`);
}

async function main() {
  const expectedWorkspace = argValue('--expect-workspace');
  const expectedUserData = argValue('--expect-user-data');
  const restart = process.argv.includes('--restart');
  const settingsStore = new SettingsStore();
  const settings = settingsStore.load();
  const state = readJson(stateFile(), {});
  const userData = app.getPath('userData');
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
    configured_workspace: settings.workspace || '',
    expected_workspace_match: Boolean(String(settings.workspace || '').trim() && String(expectedWorkspace || '').trim() && samePath(settings.workspace, expectedWorkspace)),
    expected_user_data_match: Boolean(String(userData || '').trim() && String(expectedUserData || '').trim() && samePath(userData, expectedUserData)),
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
  const token = new SecretStore().get('mcpAuthToken');
  if (!token) throw new Error('MCP auth token is unavailable in the matched Electron userData; refusing restart.');
  const oldPid = probe.native_pid;
  await run('taskkill.exe', ['/PID', String(oldPid), '/F']);
  if (!(await waitForPort(settings.mcpPort, false))) {
    throw new Error(`MCP port ${settings.mcpPort} did not close after stopping owned PID ${oldPid}.`);
  }
  const native = new NativeService(new LogService());
  const started = await native.start(settings, token, () => {});
  let ready = false;
  for (let index = 0; index < 40; index += 1) {
    if (await probeMcp(settings.mcpPort, token, settings.workspace)) {
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
  console.error(JSON.stringify({ ok: false, error: error.message, code: 'CONTROLLED_RESTART_FAILED' }));
  process.exitCode = 1;
}).finally(() => {
  setTimeout(() => app.quit(), 50);
});
