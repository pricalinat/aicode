import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      readDirectory: (path: string) => Promise<any[]>
      getProjects: () => Promise<any[]>
      getSessions: (projectPath: string) => Promise<any[]>
      readFile: (path: string) => Promise<any[]>
      watchFile: (path: string) => void
      unwatchFile: (path: string) => void
      onFileChange: (callback: (path: string) => void) => void
      onDeepLinkOpen: (callback: (params: { sessionId?: string; projectPath?: string; jsonlFile?: string }) => void) => void
      onMenuAction: (callback: (action: string) => void) => void
      getHomePath: () => Promise<string>
      joinPath: (...paths: string[]) => Promise<string>
      getVersion: () => Promise<string>
    }
  }
}