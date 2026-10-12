const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { app, BrowserWindow } = require('electron');
const repo = path.resolve(__dirname, '../../..');
app.disableHardwareAcceleration();
// Chromium creates an OS-protected encryption key even in an offline preview.
// Keep this disposable browser profile outside repository evidence.
app.setPath('userData', path.join(os.tmpdir(), 'coding-tools-folder-preview-20261011-01a12874'));
app.whenReady().then(async () => {
  const window = new BrowserWindow({ show: false, width: 1100, height: 1050,
    webPreferences: { contextIsolation: true, nodeIntegration: false } });
  await window.loadFile(path.join(repo, 'renderer/index.html'), { hash: 'workspace' });
  await window.webContents.executeJavaScript(`
    state.snapshot.settings.executionRole = 'central_executor';
    state.snapshot.settings.controlPlaneServerUrl = 'https://example.invalid';
    state.snapshot.current_ui_runtime = { mode: 'packaged', installation_id: 'a'.repeat(64) };
    state.snapshot.recoveryHost = { electron_ui_recovery: {
      recovery_host_runtime_mode: 'packaged', recovery_host_installation_id: 'a'.repeat(64) } };
    state.snapshot.recovery_host_connection = { state: 'connected' };
    state.centralEnrollmentStatus = { fresh: true, state: 'approved' };
    state.centralAuthorityStatus = { fresh: true, state: 'active', targets: [{
      workspace_id: 'workspace_example', workspace_generation: 'generation_example',
      dispatch_state: 'dispatchable', presence_state: 'online', readiness: 'ready', policy_state: 'enabled'
    }] };
    state.centralWorkspaces = [{ display_name: 'Tools-Codex-web', workspace_id: 'workspace_example',
      workspace_generation: 'generation_example', capabilities: {read: true, write: false, exec: false}},
      { display_name: 'Candidate', workspace_id: 'workspace_candidate', workspace_generation: 'generation_candidate',
        capabilities: {read: true, write: false, exec: false}}];
    state.centralWorkspaceInventoryStatus = 'loaded';
    state.centralFilePolicyStatus = 'loaded';
    state.centralFilePolicies = {file_read: {state:'enabled', workspace_id:'workspace_example',
      workspace_generation:'generation_example', policy_sha256:'b'.repeat(64)}};
    renderCentralExecutorMode(state.snapshot);
    navigate('workspace');
    selectCentralWorkspace(state.centralWorkspaces[0]);
    chooseCentralWorkspacePreset('code');
    document.querySelector('.content-viewport').scrollTop = 0;
    document.fonts.ready;
  `);
  const results = [];
  for (const width of [1100, 760]) {
    window.setSize(width, 1050);
    await window.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    const evidence = await window.webContents.executeJavaScript(`(() => {
      const panel = document.querySelector('#centralExecutorWorkspaceRegistration');
      const bounds = panel.getBoundingClientRect();
      const overflow = [...panel.querySelectorAll('button, fieldset, .central-workspace-row')]
        .filter(el => el.getBoundingClientRect().right > bounds.right + 1).map(el => el.id || el.className);
      return {overflow, apply: document.querySelector('#registerControlPlaneWorkspace').textContent,
        disabled: document.querySelector('#registerControlPlaneWorkspace').disabled,
        status: document.querySelector('#controlPlaneWorkspaceRegistrationStatus').textContent};
    })()`);
    const file = path.join(__dirname, `permissions-${width}.png`);
    fs.writeFileSync(file, (await window.webContents.capturePage(undefined, { stayHidden: true })).toPNG());
    results.push({ width, ...evidence, file });
  }
  fs.writeFileSync(path.join(__dirname, 'layout-result.json'), JSON.stringify(results, null, 2));
  process.stdout.write(JSON.stringify(results));
  window.destroy();
  app.quit();
}).catch(error => { process.stderr.write(String(error)); app.exit(1); });
