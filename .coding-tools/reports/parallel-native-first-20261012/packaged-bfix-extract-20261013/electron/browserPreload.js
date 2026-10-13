const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('browserAssistant', {
  openManager: (page) => ipcRenderer.invoke('manager:open', page),
  openChatGPT: () => ipcRenderer.invoke('shell:open', 'chatgpt-connectors'),
  lightweightStatus: () => ipcRenderer.invoke('app:lightweight-snapshot'),
  liveOrchestration: () => ipcRenderer.invoke('panel:live-control'),
  workspaceHub: () => ipcRenderer.invoke('workspace:hub'),
  switchWorkspace: (workspace) => ipcRenderer.invoke('workspace:switch', workspace),
  chooseAndSwitchWorkspace: () => ipcRenderer.invoke('workspace:choose-and-switch'),
  chooseAuthorizedRoot: () => ipcRenderer.invoke('workspace:choose-authorized-root'),
  onHeartbeat: (listener) => {
    const wrapped = (_event, payload) => listener(payload);
    ipcRenderer.on('runtime:heartbeat', wrapped);
    return () => ipcRenderer.removeListener('runtime:heartbeat', wrapped);
  },
  taskState: () => ipcRenderer.invoke('task-state:read'),
  pauseTask: () => ipcRenderer.invoke('task-state:pause'),
  resumeTask: () => ipcRenderer.invoke('task-state:resume'),
  stopTask: () => ipcRenderer.invoke('task-state:stop'),
  togglePanel: () => ipcRenderer.invoke('panel:toggle'),
  panelVisibility: () => ipcRenderer.invoke('panel:visibility'),
  onPanelVisibility: (listener) => {
    const wrapped = (_event, payload) => listener(payload);
    ipcRenderer.on('panel:visibility', wrapped);
    return () => ipcRenderer.removeListener('panel:visibility', wrapped);
  }
});
