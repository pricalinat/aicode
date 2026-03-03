import React, { useState, useRef, useEffect } from 'react'
import { ChevronRight, PanelLeftClose } from 'lucide-react'
import { ProjectList } from '../ProjectList/ProjectList'
import { SessionList } from '../SessionList/SessionList'
import { useAppStore } from '@/store/appStore'

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, toggleSidebar, selectedProjectPath, sidebarWidth, setSidebarWidth } = useAppStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [isResizing, setIsResizing] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return
      
      const newWidth = e.clientX
      if (newWidth > 200 && newWidth < 500) {
        setSidebarWidth(newWidth)
      }
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    
    if (isResizing) {
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, setSidebarWidth])
  
  if (sidebarCollapsed) {
    return (
      <button
        onClick={toggleSidebar}
        style={{
          position: 'fixed',
          left: '80px',
          top: '8px',
          zIndex: 10,
          width: '24px',
          height: '24px',
          borderRadius: '6px',
          background: 'var(--secondary)',
          border: '1px solid var(--border)',
          color: 'var(--muted-foreground)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease'
        }}
        className="btn-icon"
        title="Open sidebar (⌘B)"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>
    )
  }
  
  return (
    <>
      <aside 
        ref={sidebarRef}
        className="sidebar" 
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          width: `${sidebarWidth}px`,
          display: 'flex',
          flexDirection: 'column',
          zIndex: 10,
          background: 'var(--background)',
          borderRight: '1px solid var(--border)'
        }}>
      {/* Traffic light area + header */}
      <div style={{
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '80px', // Space for traffic lights
        paddingRight: '12px',
        borderBottom: '1px solid var(--border)',
        fontSize: '13px',
        fontWeight: 500,
        color: 'var(--foreground)'
      }}>
        <span>Projects</span>
        <button
          onClick={toggleSidebar}
          style={{
            marginLeft: 'auto',
            background: 'none',
            border: 'none',
            color: 'var(--muted-foreground)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Close sidebar (⌘B)"
        >
          <PanelLeftClose size={14} />
        </button>
      </div>
      
      {/* Search area */}
      <div style={{
        padding: '12px',
        borderBottom: '1px solid var(--border)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'var(--secondary)',
          borderRadius: '6px',
          fontSize: '13px'
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            type="text"
            placeholder="Search projects"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'none',
              border: 'none',
              outline: 'none',
              width: '100%',
              fontSize: '13px',
              color: 'var(--foreground)'
            }}
          />
        </div>
      </div>
      
      {/* Project list */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        padding: '8px'
      }}>
        <ProjectList searchQuery={searchQuery} />
      </div>
    </aside>
    
    {/* Resize handle */}
    <div
      onMouseDown={() => setIsResizing(true)}
      style={{
        position: 'fixed',
        left: `${sidebarWidth - 2}px`,
        top: 0,
        bottom: 0,
        width: '4px',
        cursor: 'col-resize',
        zIndex: 11,
        background: isResizing ? 'var(--accent)' : 'transparent',
        transition: 'background 0.2s'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'var(--accent)'
      }}
      onMouseLeave={(e) => {
        if (!isResizing) {
          e.currentTarget.style.background = 'transparent'
        }
      }}
    />
    </>
  )
}