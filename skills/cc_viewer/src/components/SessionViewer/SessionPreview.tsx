import React, { useState, useEffect, useRef } from 'react'
import { Message } from '@/types'
import { formatTime } from '@/utils/formatters'

interface SessionPreviewProps {
  sessionId: string
  sessionFilePath: string
  position: { x: number; y: number; width: number; height: number }
  onClose: () => void
  onMouseEnter?: () => void
}

export const SessionPreview: React.FC<SessionPreviewProps> = ({ 
  sessionId, 
  sessionFilePath, 
  position, 
  onClose,
  onMouseEnter 
}) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessionPreview()
  }, [sessionFilePath])

  const loadSessionPreview = async () => {
    try {
      setLoading(true)
      const sessionMessages = await window.api.readFile(sessionFilePath)
      
      // Filter messages with actual text content and get last 8
      const messagesWithContent = sessionMessages
        .filter((msg: Message) => {
          if (msg.type !== 'user' && msg.type !== 'assistant') return false
          
          // Check if message has actual text content
          let hasContent = false
          if (msg.message?.content) {
            if (typeof msg.message.content === 'string') {
              hasContent = msg.message.content.trim().length > 0
            } else if (Array.isArray(msg.message.content)) {
              const textContent = msg.message.content.find((item: any) => item.type === 'text')
              hasContent = textContent?.text && textContent.text.trim().length > 0
            }
          } else if (msg.content) {
            hasContent = typeof msg.content === 'string' && msg.content.trim().length > 0
          }
          
          return hasContent
        })
        .slice(-8)
      
      setMessages(messagesWithContent)
    } catch (error) {
      console.error('Error loading session preview:', error)
    } finally {
      setLoading(false)
    }
  }

  // Scroll to bottom when messages are loaded
  useEffect(() => {
    if (!loading && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
    }
  }, [loading, messages])

  // Calculate smart positioning
  const getSmartPosition = () => {
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const previewWidth = 450
    const previewHeight = 300
    
    let left = position.x
    let top = position.y + position.height // Default: below the card
    
    // Check if preview would go off right edge
    if (left + previewWidth > viewportWidth - 20) {
      left = position.x + position.width - previewWidth // Right align
    }
    
    // Check if preview would go off bottom edge
    if (top + previewHeight > viewportHeight - 20) {
      top = position.y - previewHeight // Above the card
    }
    
    // Ensure we don't go off left edge
    if (left < 20) {
      left = 20
    }
    
    // Ensure we don't go off top edge
    if (top < 20) {
      top = position.y + position.height // Force below if no room above
    }
    
    return { left, top }
  }

  const renderMessageContent = (message: Message) => {
    let content = ''
    
    if (message.message?.content) {
      if (typeof message.message.content === 'string') {
        content = message.message.content
      } else if (Array.isArray(message.message.content)) {
        const textContent = message.message.content.find((item: any) => item.type === 'text')
        content = textContent?.text || ''
      }
    } else if (message.content) {
      content = typeof message.content === 'string' ? message.content : ''
    }
    
    // Truncate long content
    return content.length > 200 ? content.substring(0, 200) + '...' : content
  }

  const smartPos = getSmartPosition()

  if (loading) {
    return (
      <div style={{
        position: 'fixed',
        left: smartPos.left,
        top: smartPos.top,
        zIndex: 2000,
        backgroundColor: 'var(--background)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '12px 16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
        fontSize: '12px',
        color: 'var(--muted-foreground)'
      }}>
        Loading preview...
      </div>
    )
  }

  return (
    <div
      style={{
        position: 'fixed',
        left: smartPos.left,
        top: smartPos.top,
        zIndex: 2000,
        backgroundColor: 'var(--background)',
        border: '2px solid var(--accent)',
        borderRadius: '8px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.08)',
        width: '450px',
        maxHeight: '300px',
        overflow: 'hidden',
        fontSize: '10px'
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onClose}
    >
      {/* Messages - matching SessionViewer design */}
      <div 
        ref={scrollContainerRef}
        style={{
          maxHeight: '300px',
          overflowY: 'auto',
          padding: '12px'
        }}
      >
        {messages.length === 0 ? (
          <div style={{
            padding: '20px',
            textAlign: 'center',
            color: 'var(--muted-foreground)',
            fontSize: '12px'
          }}>
            No messages to preview
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={message.uuid || index}
              style={{
                marginBottom: '12px',
                fontSize: '10px'
              }}
            >
              {/* Message header with dot - matching SessionViewer */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '6px',
                fontSize: '9px',
                fontWeight: 500
              }}>
                <div 
                  className={`message-dot ${message.type}`}
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    flexShrink: 0
                  }}
                />
                <span style={{
                  textTransform: 'capitalize',
                  color: 'var(--foreground)'
                }}>
                  {message.type}
                </span>
                {message.timestamp && (
                  <span style={{
                    fontSize: '8px',
                    color: 'var(--muted-foreground)',
                    fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace'
                  }}>
                    {formatTime(new Date(message.timestamp))}
                  </span>
                )}
              </div>
              
              {/* Message content - no background for user messages */}
              <div style={{
                fontSize: '10px',
                lineHeight: '1.4',
                color: 'var(--foreground)',
                wordBreak: 'break-word',
                paddingLeft: '14px' // Align with dot
              }}>
                {renderMessageContent(message)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}