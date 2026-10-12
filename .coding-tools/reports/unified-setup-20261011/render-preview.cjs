const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { app, BrowserWindow } = require('electron');

// This renders copied source with the renderer's built-in fake API. It never
// connects a preload, Recovery Host, profile, Ubuntu server or operator token.
const repo = path.resolve(__dirname, '../../..');
const stamp = process.argv[2] || '01';
if (!/^[a-z0-9-]+$/.test(stamp)) throw new Error('Invalid preview stamp');
const source = path.join(__dirname, `preview-source-${stamp}`);
const sourceFiles = [
  'index.html', 'app.js', 'styles.css', 'settings-compact.css', 'fonts.css',
  'theme-bootstrap.js', 'p5-a0.js', 'control-center.js', 'control-center.css',
  'dashboard.js', 'dashboard.css', 'app-icon.png',
  ...fs.readdirSync(path.join(repo, 'renderer/fonts')).filter((file) => file.endsWith('.woff2')).map((file) => `fonts/${file}`)
];
fs.mkdirSync(source, { recursive: true });
const frozen = sourceFiles.map((relative) => {
  const data = fs.readFileSync(path.join(repo, 'renderer', relative));
  const destination = path.join(source, relative);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, data);
  return { file: `renderer/${relative}`, bytes: data.length, sha256: crypto.createHash('sha256').update(data).digest('hex') };
});
fs.writeFileSync(path.join(__dirname, `preview-inputs-${stamp}.json`), JSON.stringify({
  kind: 'static_preview_only', observedAt: new Date().toISOString(), files: frozen,
  note: 'Fake renderer API, synthetic device/workspace/policy. No live authority or execution proof.'
}, null, 2));
app.disableHardwareAcceleration();
app.setPath('userData', path.join(os.tmpdir(), `coding-tools-unified-preview-20261011-${stamp}-${process.pid}`));
app.whenReady().then(async () => {
  const window = new BrowserWindow({ show: false, width: 1360, height: 980, useContentSize: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, backgroundThrottling: false } });
  window.webContents.session.webRequest.onBeforeRequest({ urls: ['http://*/*', 'https://*/*'] }, (_, callback) => callback({ cancel: true }));
  const consoleErrors = [];
  window.webContents.on('console-message', (_event, level, message) => { if (level >= 2) consoleErrors.push(message); });
  await window.loadFile(path.join(source, 'index.html'), { hash: 'system', query: { preview: '1', theme: 'light' } });
  await window.webContents.executeJavaScript(`new Promise((resolve, reject) => {
    const deadline = Date.now() + 5000;
    const check = () => { if (state.snapshot) resolve(); else if (Date.now() > deadline) reject(new Error('Preview snapshot missing')); else setTimeout(check, 20); };
    check();
  })`);
  await window.webContents.executeJavaScript(`
    state.snapshot.settings.executionRole = 'central_executor';
    state.snapshot.settings.controlPlaneServerUrl = 'https://example.invalid';
    state.snapshot.settings.workspace = 'E:\\\\Github\\\\Tools-Codex-web';
    state.snapshot.current_ui_runtime = { mode: 'packaged', installation_id: 'a'.repeat(64) };
    state.snapshot.recoveryHost = { electron_ui_recovery: {
      recovery_host_runtime_mode: 'packaged', recovery_host_installation_id: 'a'.repeat(64) } };
    state.snapshot.recovery_host_connection = { state: 'connected' };
    Object.assign(state.snapshot.status, { executionRole: 'central_executor', centralConnected: true,
      authorityReady: false, signalStale: false, telemetryAvailable: true, fullyReady: false,
      centralStatusReason: 'CENTRAL_AUTHORITY_UNASSIGNED' });
    renderSnapshot(state.snapshot, { forceForms: true });
    state.centralEnrollmentStatus = { fresh: true, state: 'approved', server_origin: 'https://example.invalid' };
    state.centralAuthorityStatus = { fresh: true, state: 'no_binding', dispatchable_target_count: 0, targets: [] };
    state.centralWorkspaces = [{ display_name: 'Tools-Codex-web', workspace_id: 'workspace_example',
      workspace_generation: 'generation_example', capabilities: { read: true, write: true, exec: true } }];
    state.centralWorkspaceInventoryStatus = 'loaded';
    state.centralFilePolicyStatus = 'loaded';
    state.centralFilePolicies = { file_read: {state:'unavailable'}, approved_patch: {state:'unavailable'} };
    renderCentralExecutorMode(state.snapshot);
    navigate('system');
    selectCentralWorkspace(state.centralWorkspaces[0]);
    chooseCentralWorkspacePreset('code');
    state.setupContinuation = { origin: 'https://example.invalid', device: state.snapshot.device.device_id,
      workspace_id: 'workspace_example', workspace_generation: 'generation_example',
      capabilities: {read: true, write: true, exec: true}, deadline: Date.now() + 600000 };
    state.setupContinuationMessage = 'Chờ chủ hệ thống cấp đúng thư mục trên Ubuntu. Trang này tự kiểm tra và tiếp tục khi được cấp; không cần nhập ID hoặc token.';
    renderSetupExecution();
    renderSetupState(state.snapshot);
    document.body.dataset.staticPreview = 'true';
    document.fonts.ready;
  `);
  await window.webContents.executeJavaScript('document.fonts.ready');
  const results = [];
  for (const width of [1360, 1100, 760]) {
    window.setContentSize(width, 980);
    for (const theme of ['light', 'dark']) {
      await window.webContents.executeJavaScript(`applyTheme(${JSON.stringify(theme)}); document.querySelector('.content-viewport').scrollTop = 0;`);
      await window.webContents.executeJavaScript('new Promise(resolve => setTimeout(resolve, 250))');
      await window.webContents.executeJavaScript('document.getAnimations().forEach(animation => { try { animation.finish(); } catch {} });');
      await window.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
      const metrics = await window.webContents.executeJavaScript(`(() => {
        const viewport = document.querySelector('.content-viewport');
        const page = document.querySelector('[data-page-view="system"]');
        const bounds = viewport.getBoundingClientRect();
        const outside = [...page.querySelectorAll('button, input, fieldset, .setup-step, .setup-section, #setupExecutionChecklist li')]
          .filter(el => el.getClientRects().length && (el.getBoundingClientRect().right > bounds.right + 1 || el.getBoundingClientRect().left < bounds.left - 1))
          .map(el => ({ id: el.id, class: el.className, width: el.getBoundingClientRect().width, text: el.textContent.trim().slice(0, 100) }));
        const sections = ['setupConnectionSection','setupFolderSection','setupExecutionSection'].map(id => ({
          id, height: document.getElementById(id).getBoundingClientRect().height,
          visible: document.getElementById(id).getClientRects().length > 0
        }));
        const brand = document.querySelector('.brand strong');
        return { theme: {body: document.body.dataset.theme, html: document.documentElement.dataset.theme,
          brandColor: getComputedStyle(brand).color, sidebarBackground: getComputedStyle(document.querySelector('.sidebar')).backgroundColor},
          viewport: {width: bounds.width, height: bounds.height, scrollWidth: viewport.scrollWidth,
          clientWidth: viewport.clientWidth, scrollHeight: viewport.scrollHeight}, outside, sections,
          primaryText: document.getElementById('setupContinueAction').textContent,
          setupBadge: document.getElementById('setupSummaryBadge').textContent };
      })()`);
      const captures = [];
      for (const anchor of ['top', 'setupFolderSection', 'setupExecutionSection']) {
        await window.webContents.executeJavaScript(anchor === 'top'
          ? 'document.querySelector(".content-viewport").scrollTop = 0;'
          : `document.getElementById(${JSON.stringify(anchor)}).scrollIntoView({block:'start', behavior:'instant'});`);
        await window.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
        const file = path.join(__dirname, `system-${stamp}-${width}-${theme}-${anchor}.png`);
        fs.writeFileSync(file, (await window.webContents.capturePage(undefined, { stayHidden: true })).toPNG());
        captures.push({ anchor, file });
      }
      results.push({ width, requestedTheme: theme, ...metrics, captures });
    }
  }
  const scenarioCaptures = [];
  window.setContentSize(1360, 980);
  for (const scenario of ['sandbox-unavailable', 'exec-ready']) {
    await window.webContents.executeJavaScript(`(() => {
      const previewWorkspace = selectedCentralWorkspace();
      state.centralFilePolicies = {
        file_read: {state:'enabled', workspace_id:previewWorkspace.workspace_id, workspace_generation:previewWorkspace.workspace_generation, policy_sha256:'b'.repeat(64)},
        approved_patch: {state:'enabled', workspace_id:previewWorkspace.workspace_id, workspace_generation:previewWorkspace.workspace_generation, policy_sha256:'c'.repeat(64)}
      };
      state.centralExecObservations[centralExecObservationKey(previewWorkspace)] = {
        policy: {state:${JSON.stringify(scenario === 'exec-ready' ? 'enabled' : 'unavailable')}, workspace_id:previewWorkspace.workspace_id,
          workspace_generation:previewWorkspace.workspace_generation, policy_sha256:${JSON.stringify(scenario === 'exec-ready' ? 'd'.repeat(64) : '')}},
        sandbox: ${JSON.stringify(scenario === 'exec-ready'
          ? {state:'available', backend:'windows_sandbox'}
          : {state:'unavailable', reason:'WINDOWS_SANDBOX_NOT_READY'})}
      };
      state.setupContinuation = null;
      state.setupContinuationMessage = ${JSON.stringify(scenario === 'exec-ready'
        ? 'Policy đã xác minh trong dữ liệu mô phỏng. Kết quả từng lệnh chưa được chứng minh.'
        : 'Môi trường chạy chưa sẵn sàng trong dữ liệu mô phỏng. Quyền đọc và sửa đã hiển thị riêng.')};
      renderSetupExecution();
    })()`);
    for (const theme of ['light', 'dark']) {
      await window.webContents.executeJavaScript(`applyTheme(${JSON.stringify(theme)}); document.getElementById('setupExecutionSection').scrollIntoView({block:'start',behavior:'instant'});`);
      await window.webContents.executeJavaScript('new Promise(resolve => setTimeout(resolve, 250))');
      await window.webContents.executeJavaScript('document.getAnimations().forEach(animation => { try { animation.finish(); } catch {} });');
      await window.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
      const file = path.join(__dirname, `system-${stamp}-1360-${theme}-${scenario}.png`);
      fs.writeFileSync(file, (await window.webContents.capturePage(undefined, {stayHidden:true})).toPNG());
      const states = await window.webContents.executeJavaScript(`['setupReadCheck','setupPatchCheck','setupExecCheck'].map(id => ({id,state:document.getElementById(id).dataset.state,text:document.getElementById(id).textContent}))`);
      scenarioCaptures.push({scenario, theme, file, states});
    }
  }
  fs.writeFileSync(path.join(__dirname, `layout-result-${stamp}.json`), JSON.stringify({ kind: 'static_preview_only', results, scenarioCaptures, consoleErrors: [...new Set(consoleErrors)] }, null, 2));
  process.stdout.write(JSON.stringify({ results: results.map(({width, requestedTheme, theme, outside, viewport}) => ({ width, requestedTheme, theme, outside, viewport })), scenarioCaptures, consoleErrors: [...new Set(consoleErrors)] }));
  window.destroy();
  app.quit();
}).catch(error => { process.stderr.write(String(error)); app.exit(1); });
