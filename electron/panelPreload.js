const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('panelAssistant', {
  close: () => ipcRenderer.invoke('panel:toggle'),
  orchestration: () => ipcRenderer.invoke('panel:live-control'),
  health: () => ipcRenderer.invoke('app:lightweight-snapshot'),
  workspace: () => ipcRenderer.invoke('workspace:hub'),
  pauseTask: (runId) => ipcRenderer.invoke('panel:task-control', 'pause', runId),
  resumeTask: (runId) => ipcRenderer.invoke('panel:task-control', 'resume', runId),
  stopTask: (runId) => ipcRenderer.invoke('panel:task-control', 'stop', runId),
  handoff: (payload) => ipcRenderer.invoke('panel:handoff', payload),
  transferController: (payload) => ipcRenderer.invoke('panel:transfer-controller', payload),
  copyCodexConfig: () => ipcRenderer.invoke('panel:copy-codex-config')
});
