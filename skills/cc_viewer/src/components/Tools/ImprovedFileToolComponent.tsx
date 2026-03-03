import React, { useState } from 'react'

interface FileToolProps {
  toolName: 'Read' | 'Edit' | 'Write' | 'MultiEdit'
  filePath: string
  content?: any
  error?: string
  compact?: boolean
  metadata?: {
    icon: string
    color: string
    bgColor: string
    category: string
  }
}

export const ImprovedFileToolComponent: React.FC<FileToolProps> = ({
  toolName,
  filePath,
  content,
  error,
  compact = true,
  metadata = { icon: '📄', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)', category: 'File Operations' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  const getFileName = (path: string) => {
    return path.split('/').pop() || path
  }

  const getFileDir = (path: string) => {
    const parts = path.split('/')
    return parts.slice(0, -1).join('/')
  }

  const getFileExtension = (path: string) => {
    const name = getFileName(path)
    const parts = name.split('.')
    return parts.length > 1 ? parts.pop() : ''
  }

  // Get operation summary
  const getOperationSummary = () => {
    if (toolName === 'Read') {
      if (typeof content === 'string') {
        const lines = content.split('\n').length
        return `${lines} lines`
      }
      return 'File read'
    }
    if (toolName === 'Write') {
      return 'File created'
    }
    if (toolName === 'Edit') {
      return 'File modified'
    }
    if (toolName === 'MultiEdit') {
      if (Array.isArray(content)) {
        return `${content.length} edits`
      }
      return 'Multiple edits'
    }
    return ''
  }

  const getToolDisplayName = () => {
    const names = {
      Read: 'Read File',
      Write: 'Write File',
      Edit: 'Edit File',
      MultiEdit: 'Multi-Edit'
    }
    return names[toolName] || toolName
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

        {/* File info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '2px'
          }}>
            <span style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: metadata.color
            }}>
              {getToolDisplayName()}
            </span>
            <span style={{
              fontSize: '10px',
              padding: '1px 6px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '3px',
              color: 'rgba(255, 255, 255, 0.5)',
              fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace'
            }}>
              .{getFileExtension(filePath)}
            </span>
          </div>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px'
          }}>
            <span style={{
              fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
              color: 'rgba(255, 255, 255, 0.7)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {getFileName(filePath)}
            </span>
            <span style={{
              fontSize: '10px',
              color: 'rgba(255, 255, 255, 0.4)'
            }}>
              • {getOperationSummary()}
            </span>
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
          {/* File path section */}
          <div style={{ marginTop: '12px' }}>
            <div style={{ 
              fontSize: '10px', 
              color: 'rgba(255, 255, 255, 0.4)',
              marginBottom: '6px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontWeight: '600'
            }}>
              File Path
            </div>
            <div style={{
              fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
              fontSize: '11px',
              color: 'var(--foreground)',
              background: 'rgba(0, 0, 0, 0.2)',
              padding: '6px 10px',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <span>
                <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>{getFileDir(filePath)}/</span>
                <span style={{ color: metadata.color }}>{getFileName(filePath)}</span>
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigator.clipboard.writeText(filePath)
                }}
                style={{
                  padding: '2px 6px',
                  fontSize: '10px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '3px',
                  color: 'rgba(255, 255, 255, 0.6)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'
                  e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
                  e.currentTarget.style.color = 'rgba(255, 255, 255, 0.6)'
                }}
              >
                Copy Path
              </button>
            </div>
          </div>
          
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
                fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                whiteSpace: 'pre-wrap'
              }}>
                {error}
              </pre>
            </div>
          )}
          
          {content && !error && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: 'rgba(255, 255, 255, 0.4)',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                {toolName === 'Read' ? 'Content' : 
                 toolName === 'MultiEdit' ? 'Edits' : 'Changes'}
              </div>
              
              {toolName === 'MultiEdit' && Array.isArray(content) ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {content.map((edit: any, index: number) => (
                    <div key={index} style={{
                      background: 'rgba(0, 0, 0, 0.2)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                      borderRadius: '4px',
                      padding: '8px',
                      fontSize: '11px'
                    }}>
                      <div style={{
                        fontSize: '10px',
                        color: metadata.color,
                        marginBottom: '4px',
                        fontWeight: '600'
                      }}>
                        Edit {index + 1}
                      </div>
                      {edit.old_string && (
                        <div style={{ marginBottom: '4px' }}>
                          <span style={{ color: '#ef4444', marginRight: '4px' }}>-</span>
                          <span style={{ 
                            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                            color: 'rgba(255, 255, 255, 0.6)'
                          }}>
                            {edit.old_string.substring(0, 50)}
                            {edit.old_string.length > 50 ? '...' : ''}
                          </span>
                        </div>
                      )}
                      {edit.new_string && (
                        <div>
                          <span style={{ color: '#22c55e', marginRight: '4px' }}>+</span>
                          <span style={{ 
                            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                            color: 'rgba(255, 255, 255, 0.6)'
                          }}>
                            {edit.new_string.substring(0, 50)}
                            {edit.new_string.length > 50 ? '...' : ''}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <pre style={{
                  background: 'rgba(0, 0, 0, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  padding: '8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  overflow: 'auto',
                  margin: 0,
                  fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                  color: 'rgba(255, 255, 255, 0.7)',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '400px',
                  lineHeight: 1.4
                }}>
                  {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}