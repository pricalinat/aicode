import React, { useState } from 'react'

interface BashToolProps {
  command: string
  description?: string
  output?: string
  error?: string
  compact?: boolean
  metadata?: {
    icon: string
    color: string
    bgColor: string
    category: string
  }
}

export const ImprovedBashToolComponent: React.FC<BashToolProps> = ({
  command,
  description,
  output,
  error,
  compact = true,
  metadata = { icon: '>', color: '#22c55e', bgColor: 'rgba(34, 197, 94, 0.1)', category: 'Terminal' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  // Extract command preview
  const getCommandPreview = (cmd: string) => {
    if (cmd.length > 40) {
      return cmd.substring(0, 40) + '...'
    }
    return cmd
  }

  // Determine status
  const status = error ? 'error' : 'success'
  const statusColor = error ? '#ef4444' : metadata.color

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
        {/* Terminal icon */}
        <div style={{
          width: '28px',
          height: '28px',
          background: metadata.bgColor,
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
          fontWeight: 'bold',
          color: metadata.color,
          border: `1px solid ${metadata.color}20`,
          flexShrink: 0
        }}>
          {metadata.icon}
        </div>

        {/* Command info */}
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
              color: statusColor
            }}>
              Terminal
            </span>
            {description && !isExpanded && (
              <span style={{
                fontSize: '10px',
                color: 'rgba(255, 255, 255, 0.5)',
                fontStyle: 'italic'
              }}>
                {description}
              </span>
            )}
          </div>
          <div style={{ 
            fontSize: '11px', 
            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
            color: 'rgba(255, 255, 255, 0.6)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            $ {getCommandPreview(command)}
          </div>
        </div>

        {/* Status indicators */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexShrink: 0
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: statusColor
          }} />
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
          {/* Command section */}
          <div style={{ marginTop: '12px' }}>
            <div style={{ 
              fontSize: '10px', 
              color: 'rgba(255, 255, 255, 0.4)',
              marginBottom: '6px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontWeight: '600'
            }}>
              Command
            </div>
            <div style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '8px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
              color: metadata.color,
              position: 'relative',
              overflow: 'auto'
            }}>
              <span style={{ color: 'rgba(255, 255, 255, 0.4)', marginRight: '8px' }}>$</span>
              {command}
              {/* Copy button */}
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigator.clipboard.writeText(command)
                }}
                style={{
                  position: 'absolute',
                  top: '6px',
                  right: '6px',
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
                Copy
              </button>
            </div>
          </div>

          {description && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: 'rgba(255, 255, 255, 0.4)',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                Description
              </div>
              <div style={{ 
                fontSize: '11px', 
                color: 'rgba(255, 255, 255, 0.6)',
                fontStyle: 'italic'
              }}>
                {description}
              </div>
            </div>
          )}
          
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
                ⚠️ Error Output
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
                whiteSpace: 'pre-wrap',
                maxHeight: '200px'
              }}>
                {error}
              </pre>
            </div>
          )}
          
          {output && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                fontSize: '10px', 
                color: 'rgba(255, 255, 255, 0.4)',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '600'
              }}>
                Output
              </div>
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
                maxHeight: '300px',
                lineHeight: 1.4
              }}>
                {output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}