import React from 'react'
import { Folder } from 'lucide-react'
import { useAppStore } from '@/store/appStore'

interface ProjectListProps {
  searchQuery?: string
}

export const ProjectList: React.FC<ProjectListProps> = ({ searchQuery = '' }) => {
  const { projects, selectedProjectPath, selectProject, setSessions, setSessionsForProject, setActiveTab, createProjectTab, tabs } = useAppStore()
  
  // Filter projects based on search query
  const filteredProjects = projects.filter(project => {
    const projectName = project.name.toLowerCase()
    const query = searchQuery.toLowerCase()
    return projectName.includes(query)
  })
  
  const handleProjectClick = async (project: any) => {
    selectProject(project.name) // Use real path for UI state
    try {
      const sessions = await window.api.getSessions(project.path) // Use Claude path for API
      setSessions(sessions)
      setSessionsForProject(project.name, sessions) // Use real path as key
      
      // Create a project tab to show session list
      createProjectTab(project.name) // Use real path for tab
    } catch (error) {
      console.error('[ProjectList] Failed to load sessions for project:', project.name)
      console.error('[ProjectList] Error:', error.message)
      console.error('[ProjectList] Project path:', project.path)
      
      // Still set empty sessions to prevent loading state issues
      setSessions([])
      setSessionsForProject(project.name, [])
    }
  }
  
  return (
    <div>
      {filteredProjects.map((project) => (
        <div
          key={project.path}
          onClick={() => handleProjectClick(project)}
          style={{
            padding: '12px 16px',
            margin: '4px 0',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease',
            background: selectedProjectPath === project.name ? 'var(--secondary)' : 'transparent',
            border: selectedProjectPath === project.name ? '1px solid var(--border)' : '1px solid transparent'
          }}
          className="project-item"
        >
          <div style={{
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--foreground)',
            marginBottom: '4px'
          }}>
            {project.name.split('/').pop() || project.name}
          </div>
          <div style={{
            fontSize: '11px',
            color: 'var(--muted-foreground)',
            marginBottom: '2px',
            opacity: 0.7,
            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {project.name}
          </div>
          <div style={{
            fontSize: '12px',
            color: 'var(--muted-foreground)'
          }}>
            {project.sessionCount} sessions
          </div>
        </div>
      ))}
    </div>
  )
}