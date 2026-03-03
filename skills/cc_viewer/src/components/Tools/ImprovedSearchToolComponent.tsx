import React, { useState } from 'react'

interface SearchToolProps {
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

export const ImprovedSearchToolComponent: React.FC<SearchToolProps> = ({
  toolName,
  parameters,
  result,
  error,
  compact = true,
  metadata = { icon: '🔍', color: '#ec4899', bgColor: 'rgba(236, 72, 153, 0.1)', category: 'Search' }
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  const getSearchSummary = () => {
    if (error) return 'Error occurred'
    
    if (Array.isArray(result)) {
      const count = result.length
      if (count === 0) return 'No matches found'
      if (count === 1) return '1 match found'
      return `${count} matches found`
    }
    
    if (toolName === 'Grep' && parameters?.pattern) {
      return `Pattern: "${parameters.pattern}"`
    }
    if (toolName === 'Glob' && parameters?.pattern) {
      return `Pattern: ${parameters.pattern}`
    }
    if (toolName === 'LS' && parameters?.path) {
      return `Path: ${parameters.path}`
    }
    
    return 'Search completed'
  }

  const getToolDisplayName = () => {
    const names = {
      Grep: 'Search Content',
      Glob: 'Find Files',
      LS: 'List Directory'
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

        {/* Search info */}
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
            {getSearchSummary()}
          </div>
        </div>

        {/* Status indicators */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexShrink: 0
        }}>
          {!error && Array.isArray(result) && result.length > 0 && (
            <span style={{
              fontSize: '10px',
              padding: '2px 6px',
              background: metadata.color,
              color: '#000',
              borderRadius: '10px',
              fontWeight: '600'
            }}>
              {result.length}
            </span>
          )}
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
          {/* Search parameters */}
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
                Search Parameters
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace'
              }}>
                {toolName === 'Grep' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Pattern: </span>
                      <span style={{ color: metadata.color }}>"{parameters.pattern}"</span>
                    </div>
                    {parameters.include && (
                      <div>
                        <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Include: </span>
                        <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{parameters.include}</span>
                      </div>
                    )}
                    {parameters.path && (
                      <div>
                        <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Path: </span>
                        <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{parameters.path}</span>
                      </div>
                    )}
                  </div>
                )}
                {toolName === 'Glob' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Pattern: </span>
                      <span style={{ color: metadata.color }}>{parameters.pattern}</span>
                    </div>
                    {parameters.path && (
                      <div>
                        <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Path: </span>
                        <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{parameters.path}</span>
                      </div>
                    )}
                  </div>
                )}
                {toolName === 'LS' && (
                  <div>
                    <span style={{ color: 'rgba(255, 255, 255, 0.4)' }}>Path: </span>
                    <span style={{ color: metadata.color }}>{parameters.path}</span>
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
          
          {Array.isArray(result) && result.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ 
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '6px'
              }}>
                <div style={{ 
                  fontSize: '10px', 
                  color: 'rgba(255, 255, 255, 0.4)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  fontWeight: '600'
                }}>
                  Results
                </div>
                <div style={{
                  fontSize: '10px',
                  color: metadata.color
                }}>
                  {result.length} {result.length === 1 ? 'match' : 'matches'}
                </div>
              </div>
              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                {result.slice(0, 100).map((item: string, index: number) => (
                  <div key={index} style={{ 
                    padding: '6px 8px',
                    borderBottom: index < result.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    color: 'rgba(255, 255, 255, 0.7)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.9)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent'
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.7)'
                  }}
                  >
                    <span style={{ 
                      color: 'rgba(255, 255, 255, 0.3)',
                      marginRight: '8px',
                      fontSize: '10px'
                    }}>
                      {index + 1}.
                    </span>
                    {item}
                  </div>
                ))}
                {result.length > 100 && (
                  <div style={{
                    padding: '6px 8px',
                    color: 'rgba(255, 255, 255, 0.4)',
                    fontSize: '10px',
                    textAlign: 'center',
                    fontStyle: 'italic'
                  }}>
                    ... and {result.length - 100} more results
                  </div>
                )}
              </div>
            </div>
          )}
          
          {Array.isArray(result) && result.length === 0 && !error && (
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
              No results found
            </div>
          )}
        </div>
      )}
    </div>
  )
}