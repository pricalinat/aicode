import React, { useState } from 'react'

interface BaseToolProps {
  toolName: string
  parameters?: any
  result?: any
  error?: string
  compact?: boolean
  children?: React.ReactNode
  metadata?: {
    icon: string
    color: string
    bgColor: string
    category: string
  }
}

export const ImprovedBaseToolComponent: React.FC<BaseToolProps> = ({
  toolName,
  parameters,
  result,
  error,
  compact = true,
  children,
  metadata = { icon: '⚙️', color: '#6b7280', bgColor: 'rgba(107, 114, 128, 0.1)', category: 'Other' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  return (
    <div style={{
      margin: '4px 0',
      fontSize: '11px',
      borderRadius: '6px',
      overflow: 'hidden',
      background: isExpanded ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
      border: 'none',
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
        {/* Icon container */}
        <div style={{
          width: '28px',
          height: '28px',
          background: metadata.bgColor,
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          border: 'none',
          flexShrink: 0
        }}>
          {metadata.icon}
        </div>

        {/* Tool info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600',
            color: metadata.color,
            marginBottom: '1px'
          }}>
            {toolName}
          </div>
          {!isExpanded && (
            <div style={{ 
              fontSize: '10px', 
              color: 'rgba(255, 255, 255, 0.4)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {error ? 'Error occurred' : 'Click to expand'}
            </div>
          )}
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
          borderTop: '1px solid rgba(255, 255, 255, 0.03)'
        }}>
          {children || (
            <>
              {parameters && (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ 
                    fontSize: '10px', 
                    color: 'rgba(255, 255, 255, 0.4)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    fontWeight: '600'
                  }}>
                    Parameters
                  </div>
                  <pre style={{
                    background: 'rgba(0, 0, 0, 0.2)',
                    border: 'none',
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    overflow: 'auto',
                    margin: 0,
                    fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                    color: 'rgba(255, 255, 255, 0.7)'
                  }}>
                    {JSON.stringify(parameters, null, 2)}
                  </pre>
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
                    ⚠️ Error
                  </div>
                  <pre style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: 'none',
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
              
              {result && (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ 
                    fontSize: '10px', 
                    color: 'rgba(255, 255, 255, 0.4)',
                    marginBottom: '6px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    fontWeight: '600'
                  }}>
                    Result
                  </div>
                  <pre style={{
                    background: 'rgba(0, 0, 0, 0.2)',
                    border: 'none',
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    overflow: 'auto',
                    margin: 0,
                    fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                    color: 'rgba(255, 255, 255, 0.7)',
                    maxHeight: '300px'
                  }}>
                    {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}