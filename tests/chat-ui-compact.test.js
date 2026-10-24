const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('0.3.3 keeps the top chrome height unchanged and exposes quick authorized-root access', () => {
  const browserCss = read('renderer/browser.css');
  const browserHtml = read('renderer/browser.html');
  const main = read('electron/main.js');
  assert.match(browserCss, /\.browser-toolbar\{[^}]*height:112px/);
  assert.match(main, /const TOOLBAR_HEIGHT = 112/);
  assert.match(browserCss, /\.workspace-health-popover\{position:absolute/);
  assert.match(browserHtml, /id="workspaceHealthPopover"/);
  assert.match(browserHtml, /id="deviceState"/);
  assert.match(browserHtml, /id="gitState"/);
  assert.match(browserHtml, /id="addAuthorizedRootQuick"/);
  assert.match(browserHtml, /id="addWorkspace"/);
});

test('executor hub opens the official ChatGPT page in the system browser without a webview', () => {
  const html = read('renderer/browser.html');
  const preload = read('electron/browserPreload.js');
  const main = read('electron/main.js');
  assert.match(html, /id="openChatGPTButton"/);
  assert.match(html, /ChatGPT mở trong trình duyệt chính thức/);
  assert.match(preload, /openChatGPT: \(\) => ipcRenderer\.invoke\('shell:open', 'chatgpt-connectors'\)/);
  assert.match(main, /'chatgpt-connectors': 'https:\/\/chatgpt\.com\/\#settings\/Connectors'/);
  assert.match(main, /shell\.openExternal\(urls\[target\]\)/);
  assert.equal(fs.existsSync(path.join(root, 'electron/chatViewController.js')), false);
  assert.equal(fs.existsSync(path.join(root, 'electron/services/chatEvaluationJournal.js')), false);
  assert.equal(fs.existsSync(path.join(root, 'electron/services/chatConversationAccess.js')), false);
  assert.match(main, /openManagerWindow/);
  assert.doesNotMatch(main, /new ChatViewController|executeJavaScript/);
  assert.doesNotMatch(preload, /chat:navigate|chat:status|chat:clear-session|chat:state|chat:download/);
  assert.doesNotMatch(`${html}\n${main}`, /chatgpt\.com\/backend-api|persist:chatgpt-session/);
});

test('workspace manager exposes extra authorized roots alongside the external ChatGPT handoff', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  assert.match(html, /id="authorizedRootsList"/);
  assert.match(html, /id="addAuthorizedRoot"/);
  assert.match(app, /updateAuthorizedRoots/);
  assert.match(read('renderer/browser.html'), /id="addAuthorizedRootQuick"/);
});

test('central workspace receipts remain successful when a later UI refresh is unavailable', () => {
  const app = read('renderer/app.js');
  assert.match(app, /async function refreshCentralWorkspaceUiAfterCommit\(\)/);
  assert.match(app, /await refreshCentralWorkspaceUiAfterCommit\(\);/);
  assert.match(app, /Thay đổi đã được ghi nhận/);
  assert.match(app, /state\.centralWorkspaces = null/);
});

test('package and manager identify the Coding Tools MCP 1.0.7 release', () => {
  const pkg = JSON.parse(read('package.json'));
  const manager = read('renderer/index.html');
  const pyproject = read('resources/coding-tools-mcp/pyproject.toml');
  const pythonPackage = read('resources/coding-tools-mcp/coding_tools_mcp/__init__.py');
  const pythonMetadata = read('resources/coding-tools-mcp/coding_tools_mcp.egg-info/PKG-INFO');
  assert.equal(pkg.name, 'coding-tools-mcp');
  assert.equal(pkg.version, '1.0.7');
  assert.equal(pkg.build.productName, 'Coding Tools MCP');
  assert.equal(pkg.build.artifactName, 'coding-tools-mcp-setup-${version}.${ext}');
  assert.match(manager, /Coding Tools MCP <span>v1\.0\.7<\/span>/);
  assert.match(manager, /Coding Tools MCP · 1\.0\.7/);
  assert.match(pyproject, /^version = "1\.0\.7"$/m);
  assert.match(pythonPackage, /^__version__ = "1\.0\.7"$/m);
  assert.match(pythonMetadata, /^Version: 1\.0\.7\r?$/m);
});

test('settings window hides independently and reveals its shell before runtime inspection finishes', () => {
  const main = read('electron/main.js');
  const app = read('renderer/app.js');
  const compact = read('renderer/settings-compact.css');
  assert.doesNotMatch(main, /parent:\s*chatWindow/);
  assert.match(main, /(?:managerWindow|openingWindow|chatWindow)\.hide\(\)/);
  assert.match(main, /chatWindow\.show\(\)/);
  assert.match(app, /Show the app shell immediately/);
  assert.match(compact, /grid-template-columns:200px/);
});
