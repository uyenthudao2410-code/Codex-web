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
  assert.match(main, /toolbarHeight:\s*112/);
  assert.match(browserCss, /\.workspace-health-popover\{position:absolute/);
  assert.match(browserHtml, /id="workspaceHealthPopover"/);
  assert.match(browserHtml, /id="deviceState"/);
  assert.match(browserHtml, /id="gitState"/);
  assert.match(browserHtml, /id="addAuthorizedRootQuick"/);
  assert.match(browserHtml, /id="addWorkspace"/);
});

test('embedded ChatGPT compacts repeated tool call records without deleting their content', () => {
  const controller = read('electron/chatViewController.js');
  assert.match(controller, /scheduleChatUiEnhancements/);
  assert.match(controller, /suspendChatUiEnhancements/);
  assert.match(controller, /mcp-tool-call-hidden/);
  assert.match(controller, /Công cụ ×/);
  assert.match(controller, /data-testid\^=\\?"conversation-turn-/);
  assert.match(controller, /MutationObserver/);
  assert.match(controller, /scheduleStableRefresh\(1800\)/);
  assert.match(controller, /document\.querySelector\('main'\) \|\| document\.body/);
  assert.doesNotMatch(controller, /observe\(document\.documentElement/);
  assert.doesNotMatch(controller, /scheduleAttachmentCapture/);
  assert.doesNotMatch(controller, /mcpAutoSaved/);
  assert.doesNotMatch(controller, /__mcpAttachmentObserver/);
});

test('workspace manager exposes extra authorized roots without changing the chat top bar', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  assert.match(html, /id="authorizedRootsList"/);
  assert.match(html, /id="addAuthorizedRoot"/);
  assert.match(app, /updateAuthorizedRoots/);
});

test('package and manager identify the Coding Tools MCP 1.0 release', () => {
  const pkg = JSON.parse(read('package.json'));
  const manager = read('renderer/index.html');
  assert.equal(pkg.name, 'coding-tools-mcp');
  assert.equal(pkg.version, '1.0.0');
  assert.equal(pkg.build.productName, 'Coding Tools MCP');
  assert.equal(pkg.build.artifactName, 'coding-tools-mcp-setup-${version}.${ext}');
  assert.match(manager, /Coding Tools MCP <span>v1\.0\.0<\/span>/);
  assert.match(manager, /Coding Tools MCP · 0\.4\.3/);
});

test('settings window hides independently and reveals its shell before runtime inspection finishes', () => {
  const main = read('electron/main.js');
  const app = read('renderer/app.js');
  const compact = read('renderer/settings-compact.css');
  assert.doesNotMatch(main, /parent:\s*chatWindow/);
  assert.match(main, /managerWindow\.hide\(\)/);
  assert.match(main, /chatWindow\.show\(\)/);
  assert.match(app, /Show the settings shell immediately/);
  assert.match(compact, /grid-template-columns:200px/);
});
