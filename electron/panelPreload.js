const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('panelAssistant', {
  close: () => ipcRenderer.invoke('panel:toggle'),
  orchestration: () => ipcRenderer.invoke('panel:live-control'),
  health: () => ipcRenderer.invoke('app:lightweight-snapshot'),
  workspace: () => ipcRenderer.invoke('workspace:hub'),
  pauseTask: () => ipcRenderer.invoke('panel:task-control', 'pause'),
  resumeTask: () => ipcRenderer.invoke('panel:task-control', 'resume'),
  stopTask: () => ipcRenderer.invoke('panel:task-control', 'stop'),
  handoff: (payload) => ipcRenderer.invoke('panel:handoff', payload),
  transferController: (payload) => ipcRenderer.invoke('panel:transfer-controller', payload),
  copyCodexConfig: () => ipcRenderer.invoke('panel:copy-codex-config')
});
