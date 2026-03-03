import React, { useState } from 'react'

interface WebToolProps {
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

export const ImprovedWebToolComponent: React.FC<WebToolProps> = ({
  toolName,
  parameters,
  result,
  error,
  compact = true,
  metadata = { icon: '🌐', color: '#6366f1', bgColor: 'rgba(99, 102, 241, 0.1)', category: 'Web' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  const getWebSummary = () => {
    if (error) return 'Error occurred'
    
    if (toolName === 'WebSearch' && parameters?.query) {
      return `"${parameters.query}"`
    }
    if (toolName === 'WebFetch' && parameters?.url) {
      try {
        const url = new URL(parameters.url)
        return url.hostname
      } catch {
        return parameters.url
      }
    }
    
    return 'Web operation completed'
  }

  const getToolDisplayName = () => {
    const names = {
      WebSearch: 'Web Search',
      WebFetch: 'Fetch URL'
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

        {/* Web info */}
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
            {getWebSummary()}
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
          {/* Parameters */}
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
                {toolName === 'WebSearch' ? 'Search Query' : 'Request Details'}
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '11px'
              }}>
                {toolName === 'WebSearch' && (
                  <div style={{
                    fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                    color: metadata.color
                  }}>
                    🔍 {parameters.query}
                  </div>
                )}
                {toolName === 'WebFetch' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>URL: </span>
                      <a 
                        href={parameters.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ 
                          color: metadata.color,
                          textDecoration: 'none',
                          borderBottom: `1px dotted ${metadata.color}50`
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderBottomStyle = 'solid'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderBottomStyle = 'dotted'
                        }}
                      >
                        {parameters.url}
                      </a>
                    </div>
                    {parameters.prompt && (
                      <div>
                        <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Prompt: </span>
                        <span style={{ 
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontStyle: 'italic'
                        }}>
                          {parameters.prompt}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                {parameters.allowed_domains && (
                  <div style={{ marginTop: '4px' }}>
                    <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Allowed domains: </span>
                    <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                      {parameters.allowed_domains.join(', ')}
                    </span>
                  </div>
                )}
                {parameters.blocked_domains && (
                  <div style={{ marginTop: '4px' }}>
                    <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Blocked domains: </span>
                    <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                      {parameters.blocked_domains.join(', ')}
                    </span>
                  </div>
                )}
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
                {toolName === 'WebSearch' ? 'Search Results' : 'Response'}
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '11px',
                overflow: 'auto',
                maxHeight: '300px'
              }}>
                {toolName === 'WebSearch' && Array.isArray(result) ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.map((item: any, index: number) => (
                      <div key={index} style={{
                        padding: '8px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '4px',
                        border: '1px solid rgba(255, 255, 255, 0.05)'
                      }}>
                        <div style={{
                          fontSize: '12px',
                          fontWeight: '600',
                          color: metadata.color,
                          marginBottom: '4px'
                        }}>
                          {item.title || `Result ${index + 1}`}
                        </div>
                        {item.url && (
                          <div style={{
                            fontSize: '10px',
                            color: 'rgba(255, 255, 255, 0.5)',
                            marginBottom: '4px'
                          }}>
                            {item.url}
                          </div>
                        )}
                        {item.snippet && (
                          <div style={{
                            fontSize: '11px',
                            color: 'rgba(255, 255, 255, 0.7)',
                            lineHeight: 1.4
                          }}>
                            {item.snippet}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <pre style={{
                    margin: 0,
                    fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                    color: 'rgba(255, 255, 255, 0.7)',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}