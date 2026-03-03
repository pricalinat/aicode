import { FSWatcher, watch } from 'chokidar'
import { BrowserWindow } from 'electron'

interface WatcherInfo {
  watcher: FSWatcher
  windows: Set<BrowserWindow>
}

const watchers = new Map<string, WatcherInfo>()

export function watchFile(filePath: string, window: BrowserWindow): void {
  const existingWatcher = watchers.get(filePath)
  
  if (existingWatcher) {
    // Add this window to the existing watcher
    existingWatcher.windows.add(window)
    
    // Clean up closed windows
    for (const win of existingWatcher.windows) {
      if (win.isDestroyed()) {
        existingWatcher.windows.delete(win)
      }
    }
  } else {
    // Create new watcher
    const watcher = watch(filePath, {
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 300,
        pollInterval: 100
      }
    })
    
    const windows = new Set<BrowserWindow>([window])
    
    watcher.on('change', () => {
      // Send to all windows watching this file
      for (const win of windows) {
        if (!win.isDestroyed()) {
          win.webContents.send('fs:fileChanged', filePath)
        } else {
          windows.delete(win)
        }
      }
    })
    
    watcher.on('error', (error) => {
      console.error(`Error watching file ${filePath}:`, error)
    })
    
    watchers.set(filePath, { watcher, windows })
  }
}

export function unwatchFile(filePath: string, window?: BrowserWindow): void {
  const watcherInfo = watchers.get(filePath)
  if (watcherInfo) {
    if (window) {
      // Remove specific window
      watcherInfo.windows.delete(window)
      
      // If no more windows are watching, close the watcher
      if (watcherInfo.windows.size === 0) {
        watcherInfo.watcher.close()
        watchers.delete(filePath)
      }
    } else {
      // Remove all watchers for this file
      watcherInfo.watcher.close()
      watchers.delete(filePath)
    }
  }
}

export function unwatchAll(): void {
  for (const watcherInfo of watchers.values()) {
    watcherInfo.watcher.close()
  }
  watchers.clear()
}

export function unwatchAllForWindow(window: BrowserWindow): void {
  for (const [filePath, watcherInfo] of watchers.entries()) {
    watcherInfo.windows.delete(window)
    
    // If no more windows are watching, close the watcher
    if (watcherInfo.windows.size === 0) {
      watcherInfo.watcher.close()
      watchers.delete(filePath)
    }
  }
}