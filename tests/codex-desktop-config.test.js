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

test('Codex Desktop config forces UTF-8 mode on Windows when the caller passes no prefix args (packaged portable Python)', () => {
  const result = buildCodexDesktopMcpConfig({
    pythonCommand: 'E:\\DEV\\Codex-web\\dist\\app\\win-unpacked\\resources\\resources\\native-python\\python.exe',
    prefixArgs: [],
    pythonPath: 'E:\\DEV\\Codex-web\\dist\\app\\win-unpacked\\resources\\resources\\coding-tools-mcp\\python_vendor;E:\\DEV\\Codex-web\\dist\\app\\win-unpacked\\resources\\resources\\coding-tools-mcp',
    descriptorPath: 'C:\\Users\\user\\AppData\\Roaming\\web-mcp-assistant\\execution-hub-proxy.json',
    platform: 'win32'
  });
  assert.deepEqual(result.args.slice(0, 4), ['-X', 'utf8', '-m', 'coding_tools_mcp.hub_proxy_stdio']);
  assert.match(result.toml, /args = \["-X", "utf8", "-m", "coding_tools_mcp\.hub_proxy_stdio", "--descriptor", /);
});

test('Codex Desktop config appends UTF-8 mode after launcher prefix args on Windows (py.exe selector stays first)', () => {
  const result = buildCodexDesktopMcpConfig({
    pythonCommand: 'py.exe',
    prefixArgs: ['-3'],
    pythonPath: 'E:\\DEV\\Tools-Codex-web\\resources\\coding-tools-mcp',
    descriptorPath: 'C:\\Users\\user\\AppData\\Roaming\\web-mcp-assistant\\execution-hub-proxy.json',
    platform: 'win32'
  });
  assert.deepEqual(result.args.slice(0, 5), ['-3', '-X', 'utf8', '-m', 'coding_tools_mcp.hub_proxy_stdio']);
});

test('Codex Desktop config does not duplicate the UTF-8 flag when the caller already supplies it', () => {
  const result = buildCodexDesktopMcpConfig({
    pythonCommand: 'C:\\Python311\\python.exe',
    prefixArgs: ['-X', 'utf8'],
    pythonPath: 'E:\\DEV\\Tools-Codex-web\\resources\\coding-tools-mcp',
    descriptorPath: 'C:\\Users\\user\\AppData\\Roaming\\web-mcp-assistant\\execution-hub-proxy.json',
    platform: 'win32'
  });
  assert.equal(result.args.filter((item) => item === '-X').length, 1);
  assert.deepEqual(result.args.slice(0, 4), ['-X', 'utf8', '-m', 'coding_tools_mcp.hub_proxy_stdio']);
});

test('Codex Desktop config leaves prefix args untouched off Windows', () => {
  const result = buildCodexDesktopMcpConfig({
    pythonCommand: '/usr/bin/python3',
    prefixArgs: [],
    pythonPath: '/opt/codex-web/resources/coding-tools-mcp',
    descriptorPath: '/home/user/.config/web-mcp-assistant/execution-hub-proxy.json',
    platform: 'linux'
  });
  assert.deepEqual(result.args.slice(0, 3), ['-m', 'coding_tools_mcp.hub_proxy_stdio', '--descriptor']);
});

test('Codex Desktop config fails closed when a required local path is missing', () => {
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: '', pythonPath: 'x', descriptorPath: 'y' }), /Python command/);
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: 'python.exe', pythonPath: '', descriptorPath: 'y' }), /PYTHONPATH/);
  assert.throws(() => buildCodexDesktopMcpConfig({ pythonCommand: 'python.exe', pythonPath: 'x', descriptorPath: '' }), /descriptor/);
});
