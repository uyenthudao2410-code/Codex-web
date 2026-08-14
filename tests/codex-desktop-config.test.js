const test = require('node:test');
const assert = require('node:assert/strict');
const { buildCodexDesktopMcpConfig } = require('../electron/services/codexDesktopConfig');

test('Codex Desktop config uses thin proxy and contains no runtime bearer or workspace authority', () => {
  const result = buildCodexDesktopMcpConfig({
    pythonCommand: 'C:\\Python311\\python.exe',
    prefixArgs: ['-X', 'utf8'],
    pythonPath: 'E:\\DEV\\Tools-Codex-web\\resources\\coding-tools-mcp\\python_vendor;E:\\DEV\\Tools-Codex-web\\resources\\coding-tools-mcp',
    descriptorPath: 'C:\\Users\\user\\AppData\\Roaming\\web-mcp-assistant\\execution-hub-proxy.json'
  });
  assert.equal(result.mode, 'single_runtime_proxy');
  assert.equal(result.containsBearer, false);
  assert.match(result.toml, /\[mcp_servers\.coding-tools\]/);
  assert.match(result.toml, /coding_tools_mcp\.hub_proxy_stdio/);
  assert.match(result.toml, /execution-hub-proxy\.json/);
  assert.match(result.toml, /PYTHONPATH/);
  assert.match(result.toml, /"-X", "utf8", "-m"/);
  assert.doesNotMatch(result.toml, /AUTH_TOKEN|Bearer|mcpAuthToken|--workspace|--permission-mode/);
  assert.doesNotMatch(result.toml, /coding_tools_mcp"\s*,\s*"--stdio/);
});

test('Codex Desktop config fails closed when a required local path is missing', () => {
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: '', pythonPath: 'x', descriptorPath: 'y' }), /Python command/);
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: 'python.exe', pythonPath: '', descriptorPath: 'y' }), /PYTHONPATH/);
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: 'python.exe', pythonPath: 'x', descriptorPath: '' }), /descriptor/);
});
