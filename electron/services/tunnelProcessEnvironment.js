const fs = require('node:fs');
const path = require('node:path');

const CODEX_APP_SERVER_COMMAND_ENV = 'TUNNEL_CLIENT_CODEX_APP_SERVER_COMMAND';
const CODEX_APP_SERVER_CMD_ENV = 'TUNNEL_CLIENT_CODEX_APP_SERVER_CMD';
const CODEX_APP_SERVER_ARGS_ENV = 'TUNNEL_CLIENT_CODEX_APP_SERVER_ARGS';
const CODEX_APP_SERVER_CWD_ENV = 'TUNNEL_CLIENT_CODEX_APP_SERVER_CWD';

function requiredFile(file, code, message) {
  const resolved = path.resolve(String(file || ''));
  if (!path.isAbsolute(resolved) || !fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
    throw Object.assign(new Error(message), { code, path: resolved });
  }
  return resolved;
}

function buildTunnelProcessEnvironment(paths, sourceEnv = process.env) {
  const env = { ...sourceEnv };
  if (process.platform !== 'win32') return env;

  // Lightweight test/embedding path objects may intentionally omit the
  // bundled Admin UI bridge. RuntimePaths always exposes both methods and is
  // therefore fail-closed when either packaged resource is missing.
  if (typeof paths?.portablePython !== 'function'
    || typeof paths?.tunnelCodexAppServerLauncher !== 'function') return env;

  const portablePython = requiredFile(
    paths.portablePython(),
    'TUNNEL_CODEX_BRIDGE_PYTHON_MISSING',
    'Bundled Python runtime for the hidden tunnel Codex bridge is missing.'
  );
  const pythonw = requiredFile(
    path.join(path.dirname(portablePython), 'pythonw.exe'),
    'TUNNEL_CODEX_BRIDGE_PYTHONW_MISSING',
    'Bundled pythonw runtime for the hidden tunnel Codex bridge is missing.'
  );
  const launcher = requiredFile(
    paths.tunnelCodexAppServerLauncher(),
    'TUNNEL_CODEX_BRIDGE_LAUNCHER_MISSING',
    'Hidden tunnel Codex bridge launcher is missing.'
  );

  // tunnel-client starts its optional Admin UI Codex bridge automatically.
  // On Windows the default `codex.cmd` path creates a console before the
  // bridge can serve requests. Route only that fixed child through pythonw;
  // the Python launcher preserves the bridge's stdio pipes and applies
  // CREATE_NO_WINDOW to cmd.exe/codex. Clear the shell-command override so an
  // ambient value cannot take precedence over this managed launch contract.
  env[CODEX_APP_SERVER_COMMAND_ENV] = '';
  env[CODEX_APP_SERVER_CMD_ENV] = pythonw;
  env[CODEX_APP_SERVER_ARGS_ENV] = `-u ${path.basename(launcher)}`;
  env[CODEX_APP_SERVER_CWD_ENV] = path.dirname(launcher);
  return env;
}

module.exports = {
  buildTunnelProcessEnvironment,
  CODEX_APP_SERVER_COMMAND_ENV,
  CODEX_APP_SERVER_CMD_ENV,
  CODEX_APP_SERVER_ARGS_ENV,
  CODEX_APP_SERVER_CWD_ENV
};
