import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  // File system operations
  readDirectory: (path: string) => ipcRenderer.invoke('fs:readDirectory', path),
  getProjects: () => ipcRenderer.invoke('fs:getProjects'),
  getSessions: (projectPath: string) => ipcRenderer.invoke('fs:getSessions', projectPath),
  readFile: (path: string) => ipcRenderer.invoke('fs:readFile', path),
  watchFile: (path: string) => {
    ipcRenderer.send('fs:watchFile', path)
  },
  unwatchFile: (path: string) => {
    ipcRenderer.send('fs:unwatchFile', path)
  },
  
  // File change events
  onFileChange: (callback: (path: string) => void) => {
    ipcRenderer.on('fs:fileChanged', (_, path) => callback(path))
  },
  
  // Deep link events
  onDeepLinkOpen: (callback: (params: { sessionId?: string; projectPath?: string; jsonlFile?: string }) => void) => {
    ipcRenderer.on('deep-link-open', (_, params) => callback(params))
  },
  
  // Menu events
  onMenuAction: (callback: (action: string) => void) => {
    const events = ['menu-new-tab', 'menu-close-tab', 'menu-toggle-sidebar', 'menu-zoom-in', 'menu-zoom-out', 'menu-zoom-reset']
    
    // Create wrapped callbacks to identify them later
    const wrappedCallbacks = new Map<string, () => void>()
    
    events.forEach(event => {
      const wrappedCallback = () => callback(event.replace('menu-', ''))
      wrappedCallbacks.set(event, wrappedCallback)
      ipcRenderer.on(event, wrappedCallback)
    })
    
    // Return cleanup function
    return () => {
      events.forEach(event => {
        const wrappedCallback = wrappedCallbacks.get(event)
        if (wrappedCallback) {
          ipcRenderer.removeListener(event, wrappedCallback)
        }
      })
    }
  },
  
  // Path utilities
  getHomePath: () => ipcRenderer.invoke('path:getHome'),
  joinPath: (...paths: string[]) => ipcRenderer.invoke('path:join', ...paths),
  
  // App info
  getVersion: () => ipcRenderer.invoke('app:getVersion')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}