import React from 'react'
import { ImprovedBaseToolComponent } from './ImprovedBaseToolComponent'
import { ImprovedBashToolComponent } from './ImprovedBashToolComponent'
import { ImprovedFileToolComponent } from './ImprovedFileToolComponent'
import { ImprovedSearchToolComponent } from './ImprovedSearchToolComponent'
import { ImprovedWebToolComponent } from './ImprovedWebToolComponent'
import { ImprovedTodoToolComponent } from './ImprovedTodoToolComponent'

interface ToolRendererProps {
  toolName: string
  parameters?: any
  result?: any
  error?: string
  compact?: boolean
}

// Tool metadata for consistent styling
export const TOOL_METADATA = {
  // Terminal tools
  Bash: { 
    icon: '>', 
    color: '#22c55e', 
    bgColor: 'rgba(34, 197, 94, 0.1)',
    category: 'Terminal'
  },
  
  // File operation tools
  Read: { 
    icon: '📄', 
    color: '#3b82f6', 
    bgColor: 'rgba(59, 130, 246, 0.1)',
    category: 'File Operations'
  },
  Write: { 
    icon: '✏️', 
    color: '#f59e0b', 
    bgColor: 'rgba(245, 158, 11, 0.1)',
    category: 'File Operations'
  },
  Edit: { 
    icon: '✂️', 
    color: '#8b5cf6', 
    bgColor: 'rgba(139, 92, 246, 0.1)',
    category: 'File Operations'
  },
  MultiEdit: { 
    icon: '📝', 
    color: '#a855f7', 
    bgColor: 'rgba(168, 85, 247, 0.1)',
    category: 'File Operations'
  },
  
  // Search tools
  Grep: { 
    icon: '🔍', 
    color: '#ec4899', 
    bgColor: 'rgba(236, 72, 153, 0.1)',
    category: 'Search'
  },
  Glob: { 
    icon: '📁', 
    color: '#10b981', 
    bgColor: 'rgba(16, 185, 129, 0.1)',
    category: 'Search'
  },
  LS: { 
    icon: '📋', 
    color: '#06b6d4', 
    bgColor: 'rgba(6, 182, 212, 0.1)',
    category: 'Search'
  },
  
  // Web tools
  WebSearch: { 
    icon: '🌐', 
    color: '#6366f1', 
    bgColor: 'rgba(99, 102, 241, 0.1)',
    category: 'Web'
  },
  WebFetch: { 
    icon: '🌍', 
    color: '#84cc16', 
    bgColor: 'rgba(132, 204, 22, 0.1)',
    category: 'Web'
  },
  
  // Task management tools
  TodoRead: { 
    icon: '📖', 
    color: '#f97316', 
    bgColor: 'rgba(249, 115, 22, 0.1)',
    category: 'Tasks'
  },
  TodoWrite: { 
    icon: '📝', 
    color: '#a855f7', 
    bgColor: 'rgba(168, 85, 247, 0.1)',
    category: 'Tasks'
  },
  
  // Notebook tools
  NotebookRead: { 
    icon: '📓', 
    color: '#14b8a6', 
    bgColor: 'rgba(20, 184, 166, 0.1)',
    category: 'Notebook'
  },
  NotebookEdit: { 
    icon: '📝', 
    color: '#0ea5e9', 
    bgColor: 'rgba(14, 165, 233, 0.1)',
    category: 'Notebook'
  },
  
  // Default for unknown tools
  Default: { 
    icon: '⚙️', 
    color: '#6b7280', 
    bgColor: 'rgba(107, 114, 128, 0.1)',
    category: 'Other'
  }
}

export const ImprovedToolRenderer: React.FC<ToolRendererProps> = ({
  toolName,
  parameters,
  result,
  error,
  compact = true
}) => {
  // Get tool metadata
  const metadata = TOOL_METADATA[toolName] || TOOL_METADATA.Default

  // Bash/Terminal tools
  if (toolName === 'Bash') {
    return (
      <ImprovedBashToolComponent
        command={parameters?.command || ''}
        description={parameters?.description}
        output={result?.output || result}
        error={error}
        compact={compact}
        metadata={metadata}
      />
    )
  }

  // File operation tools
  if (['Read', 'Edit', 'Write', 'MultiEdit'].includes(toolName)) {
    return (
      <ImprovedFileToolComponent
        toolName={toolName as 'Read' | 'Edit' | 'Write' | 'MultiEdit'}
        filePath={parameters?.file_path || parameters?.filePath || 'Unknown'}
        content={
          toolName === 'Read' 
            ? result?.output || result 
            : parameters?.content || parameters?.new_string || parameters?.edits || 'File modified'
        }
        error={error}
        compact={compact}
        metadata={metadata}
      />
    )
  }

  // Search tools (Grep, Glob, LS)
  if (['Grep', 'Glob', 'LS'].includes(toolName)) {
    return (
      <ImprovedSearchToolComponent
        toolName={toolName}
        parameters={parameters}
        result={result}
        error={error}
        compact={compact}
        metadata={metadata}
      />
    )
  }

  // Web tools
  if (['WebSearch', 'WebFetch'].includes(toolName)) {
    return (
      <ImprovedWebToolComponent
        toolName={toolName}
        parameters={parameters}
        result={result}
        error={error}
        compact={compact}
        metadata={metadata}
      />
    )
  }

  // Todo tools
  if (['TodoRead', 'TodoWrite'].includes(toolName)) {
    return (
      <ImprovedTodoToolComponent
        toolName={toolName}
        parameters={parameters}
        result={result}
        error={error}
        compact={compact}
        metadata={metadata}
      />
    )
  }

  // Default fallback for unknown tools
  return (
    <ImprovedBaseToolComponent
      toolName={toolName}
      parameters={parameters}
      result={result}
      error={error}
      compact={compact}
      metadata={metadata}
    />
  )
}