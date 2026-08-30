const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const {
  buildTunnelProcessEnvironment,
  CODEX_APP_SERVER_COMMAND_ENV,
  CODEX_APP_SERVER_CMD_ENV,
  CODEX_APP_SERVER_ARGS_ENV,
  CODEX_APP_SERVER_CWD_ENV
} = require('../electron/services/tunnelProcessEnvironment');

const root = path.resolve(__dirname, '..');
const portablePython = path.join(root, 'resources', 'native-python', 'python.exe');
const pythonw = path.join(root, 'resources', 'native-python', 'pythonw.exe');
const launcher = path.join(root, 'resources', 'tunnel-client', 'codex_app_server_launcher.py');

test('Windows tunnel children use the bundled hidden Codex app-server bridge', () => {
  const env = buildTunnelProcessEnvironment({
    portablePython: () => portablePython,
    tunnelCodexAppServerLauncher: () => launcher
  }, {
    PATH: process.env.PATH,
    [CODEX_APP_SERVER_COMMAND_ENV]: 'ambient-shell-command-must-not-win',
    [CODEX_APP_SERVER_CMD_ENV]: 'ambient-command-must-not-win'
  });

  if (process.platform !== 'win32') {
    assert.equal(env[CODEX_APP_SERVER_COMMAND_ENV], 'ambient-shell-command-must-not-win');
    return;
  }
  assert.equal(env[CODEX_APP_SERVER_COMMAND_ENV], '');
  assert.equal(env[CODEX_APP_SERVER_CMD_ENV], pythonw);
  assert.equal(env[CODEX_APP_SERVER_ARGS_ENV], '-u codex_app_server_launcher.py');
  assert.equal(env[CODEX_APP_SERVER_CWD_ENV], path.dirname(launcher));
});

test('managed Windows tunnel launch fails closed when the hidden bridge is missing', () => {
  if (process.platform !== 'win32') return;
  assert.throws(() => buildTunnelProcessEnvironment({
    portablePython: () => portablePython,
    tunnelCodexAppServerLauncher: () => path.join(os.tmpdir(), 'missing-codex-app-server-launcher.py')
  }, process.env), { code: 'TUNNEL_CODEX_BRIDGE_LAUNCHER_MISSING' });
});

test('bundled pythonw bridge preserves app-server stdio while hiding its console child', async (t) => {
  if (process.platform !== 'win32') return;
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-hidden-codex-bridge-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  fs.writeFileSync(path.join(temp, 'codex.cmd'), '@echo off\r\nmore\r\n', 'utf8');
  const child = spawn(pythonw, ['-u', launcher], {
    cwd: path.dirname(launcher),
    windowsHide: true,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {
      ...process.env,
      PATH: `${temp}${path.delimiter}${process.env.PATH || ''}`
    }
  });
  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => { stdout += chunk; });
  child.stderr.on('data', (chunk) => { stderr += chunk; });
  child.stdin.end('bridge-pipe-ok');
  const code = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', resolve);
  });
  assert.equal(code, 0, stderr);
  assert.match(stdout, /bridge-pipe-ok/);
  assert.equal(stderr, '');
  const source = fs.readFileSync(launcher, 'utf8');
  assert.match(source, /creationflags=CREATE_NO_WINDOW/);
  assert.doesNotMatch(source, /shell=True|WScript|Start-Process/i);
});
