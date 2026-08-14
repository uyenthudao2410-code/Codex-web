function tomlString(value) {
  return JSON.stringify(String(value ?? ''));
}

function buildCodexDesktopMcpConfig({ pythonCommand, prefixArgs = [], pythonPath, descriptorPath }) {
  const command = String(pythonCommand || '').trim();
  const modulePath = String(pythonPath || '').trim();
  const descriptor = String(descriptorPath || '').trim();
  if (!command) throw new Error('Python command is required for Codex Desktop MCP config.');
  if (!modulePath) throw new Error('PYTHONPATH is required for Codex Desktop MCP config.');
  if (!descriptor) throw new Error('Execution Hub proxy descriptor path is required.');
  const args = [
    ...prefixArgs.map((item) => String(item)),
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
