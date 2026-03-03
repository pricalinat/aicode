import React from 'react'

// Design Concept 1: Icon-based with Color Coding
export const IconBasedToolMessage = () => {
  const toolIcons = {
    Bash: { icon: '>', color: '#22c55e', bgColor: 'rgba(34, 197, 94, 0.1)' },
    Read: { icon: '📄', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)' },
    Write: { icon: '✏️', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' },
    Edit: { icon: '✂️', color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.1)' },
    Grep: { icon: '🔍', color: '#ec4899', bgColor: 'rgba(236, 72, 153, 0.1)' },
    Glob: { icon: '📁', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)' },
    LS: { icon: '📋', color: '#06b6d4', bgColor: 'rgba(6, 182, 212, 0.1)' },
    WebSearch: { icon: '🌐', color: '#6366f1', bgColor: 'rgba(99, 102, 241, 0.1)' },
    WebFetch: { icon: '🌍', color: '#84cc16', bgColor: 'rgba(132, 204, 22, 0.1)' },
    TodoRead: { icon: '📖', color: '#f97316', bgColor: 'rgba(249, 115, 22, 0.1)' },
    TodoWrite: { icon: '📝', color: '#a855f7', bgColor: 'rgba(168, 85, 247, 0.1)' }
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a' }}>
      <h3 style={{ color: '#fff', marginBottom: '20px' }}>Concept 1: Icon-based with Color Coding</h3>
      
      {Object.entries(toolIcons).map(([tool, config]) => (
        <div key={tool} style={{
          margin: '4px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            background: config.bgColor,
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
            border: `1px solid ${config.color}33`
          }}>
            {config.icon}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: config.color,
              marginBottom: '2px'
            }}>
              {tool}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: 'rgba(255, 255, 255, 0.5)',
              fontFamily: 'SF Mono, monospace'
            }}>
              {tool === 'Bash' && '$ npm install express'}
              {tool === 'Read' && 'src/components/App.tsx'}
              {tool === 'Grep' && 'Pattern: "TODO|FIXME" in *.js'}
            </div>
          </div>
          <div style={{
            fontSize: '10px',
            color: 'rgba(255, 255, 255, 0.3)'
          }}>
            ▶
          </div>
        </div>
      ))}
    </div>
  )
}

// Design Concept 2: Compact Pills with Status Indicators
export const CompactPillsToolMessage = () => {
  const tools = [
    { name: 'Bash', status: 'success', preview: 'npm install', duration: '2.3s' },
    { name: 'Read', status: 'success', preview: 'App.tsx', lines: '245 lines' },
    { name: 'Edit', status: 'error', preview: 'config.json', error: 'File not found' },
    { name: 'Grep', status: 'success', preview: 'TODO', matches: '12 matches' },
    { name: 'WebSearch', status: 'loading', preview: 'React hooks best practices' }
  ]

  const statusColors = {
    success: '#22c55e',
    error: '#ef4444',
    loading: '#f59e0b',
    neutral: '#6b7280'
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a' }}>
      <h3 style={{ color: '#fff', marginBottom: '20px' }}>Concept 2: Compact Pills with Status</h3>
      
      {tools.map((tool, i) => (
        <div key={i} style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          margin: '4px',
          padding: '6px 12px',
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          fontSize: '11px',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: statusColors[tool.status],
            animation: tool.status === 'loading' ? 'pulse 1.5s infinite' : 'none'
          }} />
          <span style={{ 
            color: statusColors[tool.status],
            fontWeight: '600'
          }}>
            {tool.name}
          </span>
          <span style={{ 
            color: 'rgba(255, 255, 255, 0.5)',
            fontFamily: 'SF Mono, monospace'
          }}>
            {tool.preview}
          </span>
          {tool.duration && (
            <span style={{ 
              color: 'rgba(255, 255, 255, 0.3)',
              fontSize: '10px'
            }}>
              {tool.duration}
            </span>
          )}
          {tool.lines && (
            <span style={{ 
              color: 'rgba(255, 255, 255, 0.3)',
              fontSize: '10px'
            }}>
              {tool.lines}
            </span>
          )}
          {tool.matches && (
            <span style={{ 
              color: statusColors.success,
              fontSize: '10px'
            }}>
              {tool.matches}
            </span>
          )}
          {tool.error && (
            <span style={{ 
              color: statusColors.error,
              fontSize: '10px'
            }}>
              {tool.error}
            </span>
          )}
        </div>
      ))}
      
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.3; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  )
}

// Design Concept 3: Timeline-based with Visual Hierarchy
export const TimelineToolMessage = () => {
  const toolEvents = [
    { 
      type: 'Bash', 
      action: 'Installing dependencies',
      command: 'npm install express cors dotenv',
      time: '10:23:45',
      status: 'success'
    },
    { 
      type: 'Read', 
      action: 'Reading configuration',
      file: 'src/config/app.config.ts',
      time: '10:23:47',
      status: 'success'
    },
    { 
      type: 'Edit', 
      action: 'Updating server setup',
      file: 'src/server.ts',
      changes: '+12 -3',
      time: '10:23:50',
      status: 'success'
    },
    { 
      type: 'Bash', 
      action: 'Running tests',
      command: 'npm test',
      time: '10:23:52',
      status: 'error',
      error: '2 tests failed'
    }
  ]

  const typeStyles = {
    Bash: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', border: '#22c55e' },
    Read: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', border: '#3b82f6' },
    Edit: { color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', border: '#8b5cf6' },
    Write: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', border: '#f59e0b' }
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a' }}>
      <h3 style={{ color: '#fff', marginBottom: '20px' }}>Concept 3: Timeline with Visual Hierarchy</h3>
      
      <div style={{ position: 'relative', paddingLeft: '40px' }}>
        {/* Timeline line */}
        <div style={{
          position: 'absolute',
          left: '19px',
          top: 0,
          bottom: 0,
          width: '2px',
          background: 'rgba(255, 255, 255, 0.1)'
        }} />
        
        {toolEvents.map((event, i) => (
          <div key={i} style={{
            position: 'relative',
            marginBottom: '16px'
          }}>
            {/* Timeline dot */}
            <div style={{
              position: 'absolute',
              left: '-26px',
              top: '8px',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: typeStyles[event.type].color,
              border: '2px solid #1a1a1a',
              zIndex: 1
            }} />
            
            {/* Event card */}
            <div style={{
              background: typeStyles[event.type].bg,
              border: `1px solid ${typeStyles[event.type].border}33`,
              borderRadius: '8px',
              padding: '12px',
              transition: 'all 0.2s ease'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '6px'
              }}>
                <div>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: typeStyles[event.type].color,
                    marginRight: '8px'
                  }}>
                    {event.type}
                  </span>
                  <span style={{
                    fontSize: '12px',
                    color: 'rgba(255, 255, 255, 0.7)'
                  }}>
                    {event.action}
                  </span>
                </div>
                <span style={{
                  fontSize: '10px',
                  color: 'rgba(255, 255, 255, 0.4)'
                }}>
                  {event.time}
                </span>
              </div>
              
              <div style={{
                fontSize: '11px',
                fontFamily: 'SF Mono, monospace',
                color: 'rgba(255, 255, 255, 0.6)',
                marginTop: '4px'
              }}>
                {event.command && `$ ${event.command}`}
                {event.file && event.file}
                {event.changes && (
                  <span style={{ 
                    marginLeft: '8px',
                    color: '#22c55e'
                  }}>
                    {event.changes}
                  </span>
                )}
              </div>
              
              {event.error && (
                <div style={{
                  fontSize: '11px',
                  color: '#ef4444',
                  marginTop: '4px'
                }}>
                  ⚠️ {event.error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Design Concept 4: Category Grouping with Badges
export const CategoryGroupedToolMessage = () => {
  const toolCategories = {
    'File Operations': {
      color: '#3b82f6',
      tools: [
        { name: 'Read', count: 12, recent: 'App.tsx' },
        { name: 'Write', count: 3, recent: 'config.json' },
        { name: 'Edit', count: 8, recent: 'server.ts' }
      ]
    },
    'Terminal': {
      color: '#22c55e',
      tools: [
        { name: 'Bash', count: 15, recent: 'npm install' }
      ]
    },
    'Search': {
      color: '#ec4899',
      tools: [
        { name: 'Grep', count: 5, recent: 'TODO' },
        { name: 'Glob', count: 3, recent: '*.test.ts' },
        { name: 'LS', count: 7, recent: './src' }
      ]
    },
    'Web': {
      color: '#6366f1',
      tools: [
        { name: 'WebSearch', count: 2, recent: 'React hooks' },
        { name: 'WebFetch', count: 1, recent: 'api.github.com' }
      ]
    }
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a' }}>
      <h3 style={{ color: '#fff', marginBottom: '20px' }}>Concept 4: Category Grouping with Badges</h3>
      
      {Object.entries(toolCategories).map(([category, data]) => (
        <div key={category} style={{
          marginBottom: '20px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          padding: '12px',
          border: '1px solid rgba(255, 255, 255, 0.05)'
        }}>
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            color: data.color,
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            {category}
          </div>
          
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {data.tools.map((tool, i) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px',
                background: `${data.color}15`,
                border: `1px solid ${data.color}30`,
                borderRadius: '4px',
                fontSize: '11px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}>
                <span style={{ 
                  fontWeight: '600',
                  color: data.color
                }}>
                  {tool.name}
                </span>
                <span style={{
                  fontSize: '10px',
                  padding: '1px 4px',
                  background: data.color,
                  color: '#000',
                  borderRadius: '3px',
                  fontWeight: '600'
                }}>
                  {tool.count}
                </span>
                <span style={{
                  fontSize: '10px',
                  color: 'rgba(255, 255, 255, 0.4)',
                  fontFamily: 'SF Mono, monospace'
                }}>
                  {tool.recent}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// Design Concept 5: Minimalist with Contextual Actions
export const MinimalistToolMessage = () => {
  const tools = [
    { 
      type: 'Bash',
      preview: 'npm install',
      context: 'Installing 234 packages',
      actions: ['Copy', 'Rerun']
    },
    { 
      type: 'Read',
      preview: 'src/App.tsx',
      context: '156 lines • TypeScript',
      actions: ['Open', 'Copy Path']
    },
    { 
      type: 'Edit',
      preview: 'server.config.json',
      context: 'Modified 3 lines',
      actions: ['View Diff', 'Undo']
    },
    { 
      type: 'Grep',
      preview: 'console.log',
      context: 'Found in 8 files',
      actions: ['View All', 'Filter']
    }
  ]

  const typeAccents = {
    Bash: '#22c55e',
    Read: '#3b82f6',
    Edit: '#8b5cf6',
    Grep: '#ec4899'
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a' }}>
      <h3 style={{ color: '#fff', marginBottom: '20px' }}>Concept 5: Minimalist with Contextual Actions</h3>
      
      {tools.map((tool, i) => (
        <div key={i} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '12px 0',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          {/* Type indicator */}
          <div style={{
            width: '3px',
            height: '24px',
            background: typeAccents[tool.type],
            borderRadius: '2px'
          }} />
          
          {/* Main content */}
          <div style={{ flex: 1 }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'baseline',
              gap: '12px',
              marginBottom: '2px'
            }}>
              <span style={{
                fontSize: '12px',
                fontWeight: '500',
                color: typeAccents[tool.type]
              }}>
                {tool.type}
              </span>
              <span style={{
                fontSize: '12px',
                fontFamily: 'SF Mono, monospace',
                color: 'rgba(255, 255, 255, 0.8)'
              }}>
                {tool.preview}
              </span>
            </div>
            <div style={{
              fontSize: '10px',
              color: 'rgba(255, 255, 255, 0.4)'
            }}>
              {tool.context}
            </div>
          </div>
          
          {/* Actions (visible on hover) */}
          <div style={{
            display: 'flex',
            gap: '8px',
            opacity: 0,
            transition: 'opacity 0.2s ease'
          }}>
            {tool.actions.map((action, j) => (
              <button key={j} style={{
                fontSize: '10px',
                padding: '2px 8px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '3px',
                color: 'rgba(255, 255, 255, 0.6)',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}>
                {action}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// Main component to showcase all designs
export const ToolDesignShowcase = () => {
  return (
    <div style={{ background: '#0a0a0a', minHeight: '100vh', padding: '40px' }}>
      <h1 style={{ color: '#fff', marginBottom: '40px', textAlign: 'center' }}>
        Tool Message Design Concepts
      </h1>
      
      <div style={{ display: 'grid', gap: '40px', maxWidth: '1200px', margin: '0 auto' }}>
        <IconBasedToolMessage />
        <CompactPillsToolMessage />
        <TimelineToolMessage />
        <CategoryGroupedToolMessage />
        <MinimalistToolMessage />
      </div>
    </div>
  )
}