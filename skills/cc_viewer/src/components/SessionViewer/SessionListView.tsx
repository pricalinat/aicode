import React, { useState, useRef, useEffect } from 'react'
import { Clock, DollarSign, MessageSquare, Folder } from 'lucide-react'
import { useAppStore } from '@/store/appStore'
import { formatTime, formatDate, formatCurrency } from '@/utils/formatters'
import { SessionPreview } from './SessionPreview'

interface SessionListViewProps {
  projectPath?: string
}

export const SessionListView: React.FC<SessionListViewProps> = ({ projectPath }) => {
  const { sessions, sessionsByProject, selectedSessionId, selectSession, addTab, projects, selectedProjectPath, loadSessionsForProject } = useAppStore()
  const [hoveredSession, setHoveredSession] = useState<string | null>(null)
  const [previewPosition, setPreviewPosition] = useState({ x: 0, y: 0, width: 0, height: 0 })
  const hoverTimeoutRef = useRef<NodeJS.Timeout>()
  const [showSessionPreview, setShowSessionPreview] = useState(true)
  
  // Load session preview setting and listen for changes
  useEffect(() => {
    const loadSetting = () => {
      const savedPreviewSetting = localStorage.getItem('claude-viewer-show-session-preview')
      setShowSessionPreview(savedPreviewSetting !== 'false') // Default to true
    }
    
    // Initial load
    loadSetting()
    
    // Listen for storage changes from settings modal
    const handleStorageChange = () => {
      loadSetting()
    }
    
    window.addEventListener('storage', handleStorageChange)
    // Also listen for custom event for same-window updates
    window.addEventListener('sessionPreviewSettingChanged', handleStorageChange)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('sessionPreviewSettingChanged', handleStorageChange)
    }
  }, [])
  
  // Load sessions when projectPath changes
  useEffect(() => {
    if (projectPath && !sessionsByProject[projectPath]) {
      loadSessionsForProject(projectPath)
    }
  }, [projectPath, sessionsByProject, loadSessionsForProject])
  
  // Use projectPath prop if provided (for project tabs), otherwise use selectedProjectPath (for sidebar)
  const currentProjectPath = projectPath || selectedProjectPath
  const selectedProject = projects.find(p => p.name === currentProjectPath)
  
  const handleSessionClick = async (session: any) => {
    selectSession(session.id)
    
    if (selectedProject) {
      addTab(session, selectedProject)
    }
  }

  const handleMouseEnter = (session: any, event: React.MouseEvent) => {
    if (!showSessionPreview) return // Don't show preview if disabled
    
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }
    
    // Show preview immediately (no delay)
    const rect = event.currentTarget.getBoundingClientRect()
    setPreviewPosition({
      x: rect.left,
      y: rect.top,
      width: rect.width,
      height: rect.height
    })
    setHoveredSession(session.id)
  }

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }
    
    // Longer delay to allow moving to preview
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredSession(null)
    }, 200)
  }

  const handlePreviewClose = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }
    
    // Immediate close when leaving preview area
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredSession(null)
    }, 100)
  }

  const handlePreviewEnter = () => {
    // Cancel any pending close when mouse enters preview
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }
  }

  // Use sessions from sessionsByProject based on current project path
  const projectSessions = currentProjectPath && sessionsByProject[currentProjectPath] 
    ? sessionsByProject[currentProjectPath] 
    : sessions

  const sessionsByDate = projectSessions.reduce((acc, session) => {
    const dateKey = session.startTime 
      ? formatDate(new Date(session.startTime))
      : 'Unknown Date'
    
    if (!acc[dateKey]) acc[dateKey] = []
    acc[dateKey].push(session)
    return acc
  }, {} as Record<string, typeof projectSessions>)
  
  // Sort sessions within each date group by startTime (most recent first)
  Object.keys(sessionsByDate).forEach(dateKey => {
    sessionsByDate[dateKey].sort((a, b) => {
      const timeA = a.startTime ? new Date(a.startTime).getTime() : 0
      const timeB = b.startTime ? new Date(b.startTime).getTime() : 0
      return timeB - timeA // Descending order (most recent first)
    })
  })
  
  // Sort dates with custom logic for Today, Yesterday, etc.
  const getDatePriority = (dateStr: string): number => {
    if (dateStr === 'Today') return 0
    if (dateStr === 'Yesterday') return 1
    if (dateStr.includes('days ago')) {
      const days = parseInt(dateStr.split(' ')[0])
      return 1 + days
    }
    if (dateStr === 'Unknown Date') return 10000
    // For actual dates, calculate days from now
    const date = new Date(dateStr)
    const now = new Date()
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
    return 100 + diffInDays
  }
  
  const sortedDateKeys = Object.keys(sessionsByDate).sort((a, b) => {
    return getDatePriority(a) - getDatePriority(b)
  })

  if (!selectedProject || !currentProjectPath) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: 'var(--muted-foreground)',
        textAlign: 'center'
      }}>
        <Folder size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
          Select a Project
        </h2>
        <p style={{ fontSize: '14px' }}>
          Choose a project from the sidebar to view its sessions
        </p>
      </div>
    )
  }

  return (
    <div style={{
      padding: '24px',
      height: '100%',
      overflow: 'auto'
    }}>
      <div style={{
        marginBottom: '24px',
        borderBottom: '1px solid var(--border)',
        paddingBottom: '16px'
      }}>
        <h1 style={{
          fontSize: '24px',
          fontWeight: 700,
          marginBottom: '4px',
          color: 'var(--foreground)'
        }}>
          {selectedProject.name.split('/').pop() || selectedProject.name}
        </h1>
        <div style={{
          fontSize: '13px',
          color: 'var(--muted-foreground)',
          marginBottom: '8px',
          fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
          opacity: 0.8
        }}>
          {selectedProject.name}
        </div>
        <p style={{
          fontSize: '14px',
          color: 'var(--muted-foreground)'
        }}>
          {projectSessions.length} sessions
        </p>
      </div>

      <div>
        {sortedDateKeys.map(date => (
          <div key={date} style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontSize: '16px',
              fontWeight: 600,
              color: 'var(--foreground)',
              marginBottom: '16px',
              padding: '8px 0',
              borderBottom: '1px solid var(--border)'
            }}>
              {date}
            </h3>
            
            <div style={{
              display: 'grid',
              gap: '12px',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
            }}>
              {sessionsByDate[date].map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSessionClick(session)}
                  onMouseEnter={(e) => {
                    handleMouseEnter(session, e)
                    e.currentTarget.style.borderColor = 'var(--accent)'
                    e.currentTarget.style.background = 'var(--secondary)'
                  }}
                  onMouseLeave={(e) => {
                    handleMouseLeave()
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.background = selectedSessionId === session.id ? 'var(--secondary)' : 'var(--background)'
                  }}
                  style={{
                    padding: '16px',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    background: selectedSessionId === session.id ? 'var(--secondary)' : 'var(--background)'
                  }}
                  className="session-card"
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '12px'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: 'var(--foreground)'
                    }}>
                      <Clock size={14} />
                      {session.mtime && formatTime(new Date(session.mtime))}
                    </div>
                    <span style={{ 
                      fontSize: '12px', 
                      color: 'var(--muted-foreground)',
                      fontFamily: 'monospace',
                      background: 'var(--secondary)',
                      padding: '2px 6px',
                      borderRadius: '4px'
                    }}>
                      {session.id.substring(0, 8)}
                    </span>
                  </div>
                  
                  {session.preview && (
                    <div style={{
                      fontSize: '13px',
                      color: 'var(--muted-foreground)',
                      marginBottom: '12px',
                      lineHeight: '1.5',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      opacity: 0.8
                    }}>
                      {session.preview}
                    </div>
                  )}
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    fontSize: '12px',
                    color: 'var(--muted-foreground)'
                  }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MessageSquare size={12} />
                      {session.messageCount} msgs
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <DollarSign size={12} />
                      {formatCurrency(session.totalCost)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Session Preview Overlay */}
      {hoveredSession && showSessionPreview && (
        <SessionPreview
          sessionId={hoveredSession}
          sessionFilePath={sessions.find(s => s.id === hoveredSession)?.filePath || ''}
          position={previewPosition}
          onClose={handlePreviewClose}
          onMouseEnter={handlePreviewEnter}
        />
      )}
    </div>
  )
}