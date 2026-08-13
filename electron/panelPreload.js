const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('panelAssistant', {
  close: () => ipcRenderer.invoke('panel:toggle'),
  orchestration: () => ipcRenderer.invoke('panel:orchestration'),
  health: () => ipcRenderer.invoke('app:lightweight-snapshot'),
  workspace: () => ipcRenderer.invoke('workspace:hub'),
  pauseTask: () => ipcRenderer.invoke('task-state:pause'),
  resumeTask: () => ipcRenderer.invoke('task-state:resume'),
  stopTask: () => ipcRenderer.invoke('task-state:stop'),
  handoff: (payload) => ipcRenderer.invoke('panel:handoff', payload)
});
