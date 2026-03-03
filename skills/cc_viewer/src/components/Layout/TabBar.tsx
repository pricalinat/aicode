import React, { useState } from 'react'
import { X, Plus, Sun, Moon, BarChart3, Folder, Settings, PanelLeft } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useAppStore } from '@/store/appStore'
import { SettingsModal } from '../Settings/SettingsModal'

export const TabBar: React.FC = () => {
  const { tabs, activeTabId, setActiveTab, removeTab, sidebarCollapsed, sidebarWidth, toggleSidebar, ensureDashboardTab } = useAppStore()
  const { theme, setTheme } = useTheme()
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  
  const handleNewTab = () => {
    // Create or switch to dashboard tab
    ensureDashboardTab()
  }
  
  return (
    <div className="tab-bar" style={{
      position: 'fixed',
      top: 0,
      left: sidebarCollapsed ? 0 : `${sidebarWidth}px`,
      right: 0,
      transition: 'left 0.2s ease',
      zIndex: 20
    }}>
      <div style={{
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '12px',
        paddingRight: '12px',
        fontSize: '13px',
        WebkitAppRegion: 'drag'
      } as React.CSSProperties}>
        {/* Spacer for traffic lights on macOS - only when sidebar is collapsed */}
        {sidebarCollapsed && (
          <div style={{ width: '68px', flexShrink: 0 }} />
        )}
        
        {sidebarCollapsed && (
          <button
            className="btn-icon"
            style={{ 
              padding: '6px', 
              marginRight: '8px',
              WebkitAppRegion: 'no-drag'
            } as React.CSSProperties}
            onClick={toggleSidebar}
            title="Show sidebar (Cmd+B)"
          >
            <PanelLeft size={16} />
          </button>
        )}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
          WebkitAppRegion: 'no-drag',
          overflow: 'hidden'
        } as React.CSSProperties}>
          {tabs.map((tab) => {
            const tabCount = tabs.length
            const maxWidth = tabCount > 6 ? 180 : tabCount > 4 ? 200 : 240
            const minWidth = 120
            
            const getTabLabel = () => {
              if (tab.type === 'dashboard') return 'Dashboard'
              if (tab.type === 'project') {
                const projectDisplayName = tab.projectPath.split('/').pop() || 'Project'
                return projectDisplayName
              }
              if (tab.type === 'session') {
                // For session tabs, show format: "projectName / sessionName"
                // projectPath is the full path, so just get the last part
                const projectDisplayName = tab.projectPath.split('/').pop() || 'Unknown'
                return `${projectDisplayName} / ${tab.sessionName || 'Session'}`
              }
              return 'Unknown'
            }
            
            const getTabIcon = () => {
              if (tab.type === 'dashboard') return <BarChart3 size={14} />
              if (tab.type === 'project') return <Folder size={14} />
              return null
            }
            
            return (
              <button
                key={tab.id}
                className={`tab ${activeTabId === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  '--tab-min-width': `${minWidth}px`,
                  '--tab-max-width': `${maxWidth}px`
                } as React.CSSProperties}
                title={tab.type === 'project' ? tab.projectPath : tab.sessionName || 'Session'}
              >
                {getTabIcon()}
                <span className="tab-label">
                  {getTabLabel()}
                </span>
                {tabs.length > 1 && (
                  <X 
                    size={14} 
                    className="tab-close"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeTab(tab.id)
                    }}
                  />
                )}
              </button>
            )
          })}
          {tabs.length < 10 && (
            <button
              className="btn-icon"
              style={{ padding: '6px' }}
              onClick={handleNewTab}
              title="New tab"
            >
              <Plus size={16} />
            </button>
          )}
        </div>
        
        {/* Spacer for draggable area */}
        <div style={{ flex: 1 }} />
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          WebkitAppRegion: 'no-drag'
        } as React.CSSProperties}>
          <button
            className="btn-icon"
            onClick={() => setIsSettingsOpen(true)}
            title="Settings"
          >
            <Settings size={16} />
          </button>
          <button
            className="btn-icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
      
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  )
}