import React from 'react'
import { Clock, DollarSign, MessageSquare } from 'lucide-react'
import { useAppStore } from '@/store/appStore'
import { formatTime, formatDate, formatCurrency } from '@/utils/formatters'

export const SessionList: React.FC = () => {
  const { sessions, selectedSessionId, selectSession, createSessionTab, selectedProjectPath, projects } = useAppStore()
  
  
  const handleSessionClick = async (session: any) => {
    selectSession(session.id)
    
    if (selectedProjectPath) {
      // Find the project to get the resolved name
      const project = projects.find(p => p.path === selectedProjectPath)
      const resolvedPath = project?.name || selectedProjectPath
      createSessionTab(session.id, resolvedPath, session.id.substring(0, 8))
    }
  }
  
  const sessionsByDate = sessions.reduce((acc, session) => {
    // Use mtime for grouping by date
    const dateKey = session.mtime 
      ? formatDate(new Date(session.mtime))
      : 'Unknown Date'
    
    
    if (!acc[dateKey]) acc[dateKey] = []
    acc[dateKey].push(session)
    return acc
  }, {} as Record<string, typeof sessions>)
  
  // Sort sessions within each date group by mtime (most recent first)
  Object.keys(sessionsByDate).forEach(dateKey => {
    sessionsByDate[dateKey].sort((a, b) => {
      const timeA = a.mtime ? new Date(a.mtime).getTime() : 0
      const timeB = b.mtime ? new Date(b.mtime).getTime() : 0
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
  
  const sortedDates = Object.keys(sessionsByDate).sort((a, b) => {
    const priorityA = getDatePriority(a)
    const priorityB = getDatePriority(b)
    return priorityA - priorityB
  })
  
  
  return (
    <div style={{ padding: '4px' }}>
      {sortedDates.map((date) => (
        <div key={date} style={{ marginBottom: '12px' }}>
          <div style={{
            padding: '8px 12px',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--muted-foreground)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            {date}
          </div>
          {sessionsByDate[date].map((session) => (
            <div
              key={session.id}
              className={`session-item ${selectedSessionId === session.id ? 'active' : ''}`}
              onClick={() => handleSessionClick(session)}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '4px'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  fontWeight: 500
                }}>
                  <Clock size={12} />
                  {session.mtime && formatTime(new Date(session.mtime))}
                </div>
                <span style={{ 
                  fontSize: '11px', 
                  color: 'var(--muted-foreground)',
                  fontFamily: 'monospace'
                }}>
                  {session.id.substring(0, 8)}
                </span>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                fontSize: '11px',
                color: 'var(--muted-foreground)'
              }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <MessageSquare size={10} />
                  {session.messageCount} msgs
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <DollarSign size={10} />
                  {formatCurrency(session.totalCost)}
                </span>
              </div>
              {session.preview && (
                <div style={{
                  fontSize: '12px',
                  color: 'var(--muted-foreground)',
                  marginTop: '8px',
                  lineHeight: '1.4',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  opacity: 0.7
                }}>
                  {session.preview}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}