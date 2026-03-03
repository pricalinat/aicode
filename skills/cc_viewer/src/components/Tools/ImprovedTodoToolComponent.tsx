import React, { useState } from 'react'

interface TodoToolProps {
  toolName: string
  parameters?: any
  result?: any
  error?: string
  compact?: boolean
  metadata?: {
    icon: string
    color: string
    bgColor: string
    category: string
  }
}

interface TodoItem {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'high' | 'medium' | 'low'
}

export const ImprovedTodoToolComponent: React.FC<TodoToolProps> = ({
  toolName,
  parameters,
  result,
  error,
  compact = true,
  metadata = { icon: '📝', color: '#a855f7', bgColor: 'rgba(168, 85, 247, 0.1)', category: 'Tasks' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  const getTodoSummary = () => {
    if (error) return 'Error occurred'
    
    if (toolName === 'TodoRead') {
      if (Array.isArray(result)) {
        const count = result.length
        if (count === 0) return 'No tasks'
        const completed = result.filter((t: TodoItem) => t.status === 'completed').length
        const inProgress = result.filter((t: TodoItem) => t.status === 'in_progress').length
        return `${count} tasks (${completed} done, ${inProgress} active)`
      }
      return 'Task list read'
    }
    
    if (toolName === 'TodoWrite' && parameters?.todos) {
      const todos = parameters.todos
      const count = todos.length
      return `Updated ${count} task${count !== 1 ? 's' : ''}`
    }
    
    return 'Task operation completed'
  }

  const getToolDisplayName = () => {
    const names = {
      TodoRead: 'Read Tasks',
      TodoWrite: 'Update Tasks'
    }
    return names[toolName] || toolName
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅'
      case 'in_progress': return '🔄'
      case 'pending': return '⏳'
      default: return '📝'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#ef4444'
      case 'medium': return '#f59e0b'
      case 'low': return '#22c55e'
      default: return '#6b7280'
    }
  }

  return (
    <div style={{
      margin: '4px 0',
      fontSize: '11px',
      borderRadius: '6px',
      overflow: 'hidden',
      background: isExpanded ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
      border: `1px solid ${isExpanded ? 'rgba(255, 255, 255, 0.05)' : 'transparent'}`,
      transition: 'all 0.2s ease'
    }}>
      <div 
        onClick={toggleExpanded}
        style={{
          padding: '8px 12px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          transition: 'all 0.2s ease',
          background: isExpanded ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
          borderRadius: '6px'
        }}
        onMouseEnter={(e) => {
          if (!isExpanded) {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'
          }
        }}
        onMouseLeave={(e) => {
          if (!isExpanded) {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.01)'
          }
        }}
      >
        {/* Icon */}
        <div style={{
          width: '28px',
          height: '28px',
          background: metadata.bgColor,
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          border: `1px solid ${metadata.color}20`,
          flexShrink: 0
        }}>
          {metadata.icon}
        </div>

        {/* Todo info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600',
            color: metadata.color,
            marginBottom: '2px'
          }}>
            {getToolDisplayName()}
          </div>
          <div style={{ 
            fontSize: '11px',
            color: 'rgba(255, 255, 255, 0.6)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {getTodoSummary()}
          </div>
        </div>

        {/* Status indicators */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexShrink: 0
        }}>
          {error && (
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#ef4444'
            }} />
          )}
          <span style={{ 
            fontSize: '10px',
            color: 'rgba(255, 255, 255, 0.3)',
            transform: isExpanded ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.2s ease'
          }}>
            ▶
          </span>
        </div>
      </div>
      
      {isExpanded && (
        <div style={{ 
          padding: '0 12px 12px 12px',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)'
        }}>
          {error && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: '#ef4444',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                ⚠️ Error
              </div>
              <pre style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '11px',
                overflow: 'auto',
                margin: 0,
                color: '#ef4444',
                fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace'
              }}>
                {error}
              </pre>
            </div>
          )}
          
          {/* TodoRead - show task list */}
          {toolName === 'TodoRead' && Array.isArray(result) && result.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: 'rgba(255, 255, 255, 0.4)',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                Task List
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '4px',
                padding: '4px'
              }}>
                {result.map((todo: TodoItem, index: number) => (
                  <div key={todo.id || index} style={{
                    padding: '8px',
                    borderBottom: index < result.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '8px'
                  }}>
                    <span style={{ fontSize: '12px' }}>{getStatusIcon(todo.status)}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        fontSize: '11px',
                        color: todo.status === 'completed' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(255, 255, 255, 0.8)',
                        textDecoration: todo.status === 'completed' ? 'line-through' : 'none',
                        marginBottom: '2px'
                      }}>
                        {todo.content}
                      </div>
                      <div style={{
                        display: 'flex',
                        gap: '8px',
                        alignItems: 'center'
                      }}>
                        <span style={{
                          fontSize: '9px',
                          padding: '1px 4px',
                          background: getPriorityColor(todo.priority) + '20',
                          color: getPriorityColor(todo.priority),
                          borderRadius: '3px',
                          fontWeight: '600'
                        }}>
                          {todo.priority}
                        </span>
                        <span style={{
                          fontSize: '9px',
                          color: 'rgba(255, 255, 255, 0.4)'
                        }}>
                          {todo.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* TodoWrite - show updated tasks */}
          {toolName === 'TodoWrite' && parameters?.todos && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: 'rgba(255, 255, 255, 0.4)',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                Updated Tasks
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '4px',
                padding: '8px',
                fontSize: '11px'
              }}>
                {parameters.todos.map((todo: TodoItem, index: number) => (
                  <div key={todo.id || index} style={{
                    padding: '4px 0',
                    borderBottom: index < parameters.todos.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
                  }}>
                    <span style={{ marginRight: '8px' }}>{getStatusIcon(todo.status)}</span>
                    <span style={{
                      color: todo.status === 'completed' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(255, 255, 255, 0.8)'
                    }}>
                      {todo.content}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Empty state */}
          {toolName === 'TodoRead' && Array.isArray(result) && result.length === 0 && !error && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '4px',
              textAlign: 'center',
              color: 'rgba(255, 255, 255, 0.4)',
              fontSize: '11px'
            }}>
              No tasks in the list
            </div>
          )}
        </div>
      )}
    </div>
  )
}