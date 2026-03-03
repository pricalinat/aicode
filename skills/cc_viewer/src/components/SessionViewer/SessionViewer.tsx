import React, { useEffect, useState, useRef } from 'react'
import { useAppStore } from '@/store/appStore'
import { Message, Tab } from '@/types'
import { MessageBlock } from './MessageBlock'
import { Timeline } from './Timeline'
import { ToolGroup } from './ToolGroup'
import { Copy, Check, Settings, ChevronRight } from 'lucide-react'

interface SessionViewerProps {
  tab: Tab
}

export const SessionViewer: React.FC<SessionViewerProps> = ({ tab }) => {
  const { messages, setMessages, sessionsByProject, selectProject, setActiveTab, loadSessionsForProject, createProjectTab } = useAppStore()
  const [isLive, setIsLive] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [currentMessageIndex, setCurrentMessageIndex] = useState<number | undefined>()
  const [copied, setCopied] = useState(false)
  const [isNarrow, setIsNarrow] = useState(false)
  const [sessionLoading, setSessionLoading] = useState(false)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const messageRefs = useRef<(HTMLDivElement | null)[]>([])
  const sessionMessages = messages[tab.sessionId || ''] || []
  
  // Process messages to merge tool calls and results
  const processedMessages = React.useMemo(() => {
    const result: Message[] = []
    const pendingToolCalls = new Map<string, Message>()
    
    sessionMessages.forEach((message) => {
      // Check if this is a tool invocation
      if (message.message?.content && Array.isArray(message.message.content)) {
        const toolUse = message.message.content.find((item: any) => item.type === 'tool_use')
        if (toolUse && toolUse.id) {
          // Store pending tool call
          pendingToolCalls.set(toolUse.id, message)
          return // Don't add to result yet
        }
      }
      
      // Check if this is a tool result
      if (message.message?.content && Array.isArray(message.message.content)) {
        const toolResult = message.message.content.find((item: any) => item.type === 'tool_result')
        if (toolResult && toolResult.tool_use_id && pendingToolCalls.has(toolResult.tool_use_id)) {
          // Merge with pending tool call
          const toolCall = pendingToolCalls.get(toolResult.tool_use_id)!
          const toolUse = toolCall.message.content.find((item: any) => item.type === 'tool_use')
          
          const mergedMessage: Message = {
            ...message,
            type: 'tool',
            toolName: toolUse.name,
            toolUseResult: toolResult.content,
            message: {
              ...message.message,
              content: [toolUse, toolResult]
            }
          }
          
          result.push(mergedMessage)
          pendingToolCalls.delete(toolResult.tool_use_id)
          return
        }
      }
      
      // Regular message or unmatched tool message
      result.push(message)
    })
    
    // Add any remaining pending tool calls (without results)
    pendingToolCalls.forEach((toolCall) => {
      result.push(toolCall)
    })
    
    return result
  }, [sessionMessages])
  
  // Group consecutive tool messages
  const groupedMessages = React.useMemo(() => {
    const groups: Array<{ type: 'single' | 'tool-group', messages: Message[] }> = []
    let currentToolGroup: Message[] = []
    
    processedMessages.forEach((message, index) => {
      const isToolMessage = message.type === 'tool' || 
        (message.message?.content && Array.isArray(message.message.content) && 
         message.message.content.some((item: any) => item.type === 'tool_use' || item.type === 'tool_result'))
      
      if (isToolMessage) {
        currentToolGroup.push(message)
      } else {
        // End current tool group if exists
        if (currentToolGroup.length > 0) {
          groups.push({ type: 'tool-group', messages: currentToolGroup })
          currentToolGroup = []
        }
        // Add non-tool message
        groups.push({ type: 'single', messages: [message] })
      }
    })
    
    // Don't forget the last group
    if (currentToolGroup.length > 0) {
      groups.push({ type: 'tool-group', messages: currentToolGroup })
    }
    
    return groups
  }, [processedMessages])
  
  // Find the session details - first check if sessions are loaded for this project
  const projectSessions = sessionsByProject[tab.projectPath] || []
  const session = projectSessions.find(s => s.id === tab.sessionId) || null
  
  // Load sessions for this project if not already loaded
  useEffect(() => {
    const loadSessionsIfNeeded = async () => {
      if (!sessionsByProject[tab.projectPath] && tab.sessionId && !sessionLoading) {
        setSessionLoading(true)
        setSessionError(null)
        try {
          await loadSessionsForProject(tab.projectPath)
        } catch (error) {
          console.error('Failed to load sessions:', error)
          setSessionError('Failed to load session data')
        } finally {
          setSessionLoading(false)
        }
      }
    }
    loadSessionsIfNeeded()
  }, [tab.projectPath, tab.sessionId, sessionsByProject, loadSessionsForProject, sessionLoading])
  
  console.log('[SessionViewer] Looking for session:', tab.sessionId)
  console.log('[SessionViewer] Project sessions loaded:', !!sessionsByProject[tab.projectPath])
  console.log('[SessionViewer] Found session:', session)
  
  const handleCopyCommand = () => {
    if (!session || !tab.sessionId) return
    
    const projectPath = tab.projectPath
    const sessionId = tab.sessionId
    
    // Get custom command from localStorage
    const customCommand = localStorage.getItem('claude-viewer-custom-command')
    const template = customCommand || 'cd {projectPath} && claude --resume {sessionId}'
    const command = template
      .replace('{projectPath}', projectPath)
      .replace('{sessionId}', sessionId)
    
    navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  useEffect(() => {
    if (!session) return
    
    // Load initial messages
    loadMessages()
    
    // Start watching file for changes
    window.api.watchFile(session.filePath)
    setIsLive(true)
    
    // Listen for file changes
    const handleFileChange = (changedPath: string) => {
      if (changedPath === session.filePath) {
        loadMessages()
      }
    }
    
    window.api.onFileChange(handleFileChange)
    
    return () => {
      window.api.unwatchFile(session.filePath)
      setIsLive(false)
    }
  }, [session])
  
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [sessionMessages, autoScroll])
  
  const loadMessages = async () => {
    if (!session) return
    
    try {
      const newMessages = await window.api.readFile(session.filePath)
      setMessages(tab.sessionId || '', newMessages)
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }
  
  const handleTimelineJump = (index: number) => {
    const element = messageRefs.current[index]
    if (element && containerRef.current) {
      const container = containerRef.current
      const elementTop = element.offsetTop
      const elementHeight = element.offsetHeight
      const containerHeight = container.clientHeight
      
      // Center the message in the viewport
      const scrollTop = elementTop - (containerHeight / 2) + (elementHeight / 2)
      container.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      })
      
      setCurrentMessageIndex(index)
      setAutoScroll(false)
    }
  }
  
  // Track visible messages for timeline
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    
    const handleScroll = () => {
      const containerTop = container.scrollTop
      const containerBottom = containerTop + container.clientHeight
      
      // Find the first visible message
      for (let i = 0; i < messageRefs.current.length; i++) {
        const element = messageRefs.current[i]
        if (element) {
          const elementTop = element.offsetTop
          const elementBottom = elementTop + element.offsetHeight
          
          if (elementBottom > containerTop && elementTop < containerBottom) {
            setCurrentMessageIndex(i)
            break
          }
        }
      }
    }
    
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [sessionMessages])
  
  // Track window width for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      setIsNarrow(window.innerWidth <= 720)
    }
    
    handleResize() // Check initial width
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  // Show loading state if sessions are being loaded
  if (sessionLoading) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--muted-foreground)'
      }}>
        Loading session...
      </div>
    )
  }
  
  // Show error state if there was an error loading sessions
  if (sessionError) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--destructive-foreground)',
        gap: '8px'
      }}>
        <div>Error: {sessionError}</div>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '8px 16px',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            background: 'var(--background)',
            color: 'var(--foreground)',
            cursor: 'pointer'
          }}
        >
          Reload
        </button>
      </div>
    )
  }
  
  // Show session not found if session is not available after loading
  if (!session) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--muted-foreground)'
      }}>
        Session not found
      </div>
    )
  }
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'var(--background)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 24px',
        borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--background)',
        minHeight: '48px',
        flexWrap: 'nowrap'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          minWidth: 0,
          flex: '1 1 auto',
          overflow: 'hidden'
        }}>
          <button
            onClick={() => {
              // Create or switch to project tab
              createProjectTab(tab.projectPath)
            }}
            style={{
              fontSize: '14px',
              fontWeight: 600,
              margin: 0,
              color: 'var(--foreground)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '4px',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '200px'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'var(--secondary)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'none'
            }}
            title={tab.projectName}
          >
            {tab.projectPath.split('/').pop() || 'Unknown Project'}
          </button>
          <ChevronRight size={16} style={{ color: 'var(--muted-foreground)', flexShrink: 0 }} />
          <div style={{
            fontSize: '13px',
            color: 'var(--muted-foreground)',
            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            minWidth: 0,
            flex: '1 1 auto'
          }}>
            <span style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>{tab.sessionId}</span>
              <button
                onClick={handleCopyCommand}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: copied ? 'var(--accent)' : 'var(--muted-foreground)',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = 'var(--secondary)'
                  e.currentTarget.style.color = 'var(--foreground)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'none'
                  e.currentTarget.style.color = copied ? 'var(--accent)' : 'var(--muted-foreground)'
                }}
                title="Copy resume command"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '13px',
          flexShrink: 0
        }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            color: 'var(--muted-foreground)'
          }}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              style={{ cursor: 'pointer' }}
              title="Auto-scroll"
            />
            {!isNarrow && <span style={{ marginLeft: '2px' }}>Auto-scroll</span>}
          </label>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span className={isLive ? 'status-indicator status-live' : 'status-indicator status-offline'} 
                  title={isLive ? 'Live' : 'Offline'} />
            {!isNarrow && (
              <span style={{ color: 'var(--muted-foreground)', marginLeft: '2px' }}>
                {isLive ? 'Live' : 'Offline'}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0',
          backgroundColor: 'var(--background)'
        }}
      >
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          padding: '40px 24px'
        }}>
          {groupedMessages.map((group, groupIndex) => {
            if (group.type === 'single') {
              return group.messages.map((message, index) => (
                <div 
                  key={message.uuid || `${groupIndex}-${index}`}
                  ref={el => messageRefs.current[groupIndex] = el}
                >
                  <MessageBlock message={message} />
                </div>
              ))
            } else {
              // Tool group
              return (
                <div 
                  key={`tool-group-${groupIndex}`}
                  ref={el => messageRefs.current[groupIndex] = el}
                >
                  <ToolGroup messages={group.messages} />
                </div>
              )
            }
          })}
          {sessionMessages.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: 'var(--muted-foreground)',
              marginTop: '64px'
            }}>
              No messages yet...
            </div>
          )}
        </div>
      </div>
      
      {/* Timeline minimap */}
      <div 
        style={{
          position: 'fixed',
          right: 0,
          top: '50%',
          transform: 'translateY(-50%)',
          width: '140px',
          height: '450px',
          pointerEvents: 'none',
          padding: '20px'
        }}
        onMouseEnter={(e) => {
          const timeline = e.currentTarget.querySelector('.timeline-container') as HTMLElement
          if (timeline) {
            timeline.style.opacity = '1'
            timeline.style.pointerEvents = 'auto'
            timeline.style.transform = 'translateY(-50%) translateX(0)'
          }
        }}
        onMouseLeave={(e) => {
          const timeline = e.currentTarget.querySelector('.timeline-container') as HTMLElement
          if (timeline) {
            timeline.style.opacity = '0'
            timeline.style.pointerEvents = 'none'
            timeline.style.transform = 'translateY(-50%) translateX(10px)'
          }
        }}
      >
        <Timeline 
          messages={processedMessages}
          currentIndex={currentMessageIndex}
          onJump={handleTimelineJump}
        />
      </div>
    </div>
  )
}