function tomlString(value) {
  return JSON.stringify(String(value ?? ''));
}

function hasUtf8Flag(args) {
  return args.some((item, index) => item === '-Xutf8' || (item === '-X' && args[index + 1] === 'utf8'));
}

// On Windows, Python's text-mode stdout follows the locale ANSI codepage,
// which corrupts the proxy's UTF-8 JSON-RPC responses when Codex Desktop
// spawns it (observed live 2026-10-23: initialize payload broken at the
// first non-ASCII byte). Force UTF-8 mode for the proxy interpreter so the
// generated config works without a hand edit. Caller prefix args (e.g. the
// py.exe "-3" selector) stay first so launcher flags keep their position.
function effectivePrefixArgs(prefixArgs, platform) {
  const normalized = prefixArgs.map((item) => String(item));
  if (platform !== 'win32' || hasUtf8Flag(normalized)) return normalized;
  return [...normalized, '-X', 'utf8'];
}

function buildCodexDesktopMcpConfig({ pythonCommand, prefixArgs = [], pythonPath, descriptorPath, platform = process.platform }) {
  const command = String(pythonCommand || '').trim();
  const modulePath = String(pythonPath || '').trim();
  const descriptor = String(descriptorPath || '').trim();
  if (!command) throw new Error('Python command is required for Codex Desktop MCP config.');
  if (!modulePath) throw new Error('PYTHONPATH is required for Codex Desktop MCP config.');
  if (!descriptor) throw new Error('Execution Hub proxy descriptor path is required.');
  const args = [
    ...effectivePrefixArgs(prefixArgs, String(platform || '')),
    '-m',
    'coding_tools_mcp.hub_proxy_stdio',
    '--descriptor',
    descriptor
  ];
  const toml = [
    '[mcp_servers.coding-tools]',
    `command = ${tomlString(command)}`,
    `args = [${args.map(tomlString).join(', ')}]`,
    `env = { PYTHONPATH = ${tomlString(modulePath)} }`,
    ''
  ].join('\n');
  return {
    toml,
    command,
    args,
    descriptorPath: descriptor,
    mode: 'single_runtime_proxy',
    containsBearer: false
  };
}

module.exports = { buildCodexDesktopMcpConfig, tomlString };
