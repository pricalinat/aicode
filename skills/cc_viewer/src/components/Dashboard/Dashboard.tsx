import React from 'react'
import { useAppStore } from '@/store/appStore'
import { Folder, FileText } from 'lucide-react'
import { RecentSessions } from '../RecentSessions/RecentSessions'

export const Dashboard: React.FC = () => {
  const { projects } = useAppStore()
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'auto',
      background: 'var(--background)'
    }}>
      <div style={{
        flex: 1,
        maxWidth: '1200px',
        width: '100%',
        margin: '0 auto',
        padding: '48px'
      }}>
        <RecentSessions limit={50} showProjectInfo={true} />
      </div>
    </div>
  )
}