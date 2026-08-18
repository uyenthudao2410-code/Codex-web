(() => {
  const params = new URLSearchParams(location.search);
  const requested = params.get('theme');
  const theme = requested === 'light' ? 'light' : 'dark';
  document.body.dataset.theme = theme;
  document.documentElement.dataset.theme = theme;

  // Static UI previews are opt-in. In the packaged Electron manager, a missing
  // preload bridge must fail closed instead of letting app.js silently create
  // a healthy-looking preview runtime.
  if (!window.mcpAssistant && params.get('preview') !== '1') {
    const settings = {
      workspace: '', permissionMode: 'safe', toolMode: 'smart',
      mcpPort: 18766, healthPort: 18082, proxyMode: 'auto', proxyUrl: '', tunnelId: '',
      recoveryMcpPort: 18767, recoveryHealthPort: 18083, recoveryTunnelId: '',
      theme, startWithWindows: false, progressReportSeconds: 90, keepRunningOnClose: true,
      autoStartServices: false, firstRunCompleted: true, guideProgress: {}, authorizedRoots: []
    };
    const snapshot = {
      settings,
      secrets: { runtimeApiKey: false, mcpAuthToken: false },
      environment: {
        python: { installed: false, version: '' },
        proxy: { mode: 'auto', configured: false, reachable: false, source: 'error', url: '' },
        tunnelClient: { installed: false },
        workspace: { configured: false, exists: false },
        ports: { mcpListening: false, tunnelListening: false }
      },
      status: {
        busy: false,
        runtimeRunning: false,
        tunnelRunning: false,
        fullyReady: false,
        ipcUnavailable: true,
        signalStale: true,
        failureKind: 'ipc_unavailable',
        localMcpUrl: 'http://127.0.0.1:18766/mcp',
        tunnelUiUrl: 'http://127.0.0.1:18082/ui'
      },
      device: null,
      recoveryHost: null
    };
    const ok = (data) => Promise.resolve({ ok: true, data });
    const fail = () => Promise.resolve({ ok: false, error: 'Electron IPC/preload bridge is unavailable.' });
    const noopSubscription = () => () => {};

    window.mcpAssistant = {
      snapshot: () => ok(snapshot),
      orchestration: fail,
      chooseWorkspace: fail,
      switchWorkspace: fail,
      updateAuthorizedRoots: fail,
      taskState: () => ok({ exists: false, state: null }),
      clearTaskState: fail,
      pauseTask: fail,
      resumeTask: fail,
      stopTask: fail,
      taskHistory: () => ok([]),
      performanceTrace: () => ok(null),
      clearPerformanceTrace: fail,
      inspectBuild: fail,
      runBuild: fail,
      inspectHealth: fail,
      repairHealth: fail,
      closeManager: () => { window.close(); return ok(true); },
      saveSettings: fail,
      saveRuntimeKey: fail,
      removeRuntimeKey: fail,
      regenerateMcpToken: fail,
      start: fail,
      stop: fail,
      restart: fail,
      activationPreflight: fail,
      activateUpdate: fail,
      activationStatus: fail,
      acknowledgeConnectorContract: fail,
      logs: () => ok([{ time: new Date().toISOString(), level: 'error', message: 'Electron IPC/preload bridge is unavailable.' }]),
      clearLogs: fail,
      openExternal: fail,
      installPython: fail,
      detectProxy: fail,
      clearChatSession: fail,
      onProgress: noopSubscription,
      onLog: noopSubscription,
      onStatus: noopSubscription,
      onHeartbeat: noopSubscription,
      onBuildProgress: noopSubscription
    };
  }
})();
