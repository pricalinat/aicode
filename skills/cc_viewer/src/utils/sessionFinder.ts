import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import { execSync } from 'child_process'
import { pathToProjectName } from './projectPathUtils'

interface SessionInfo {
  sessionId: string
  projectPath: string
  jsonlFile: string
  timestamp: string
}

export class SessionFinder {
  private claudeProjectsPath: string

  constructor() {
    this.claudeProjectsPath = path.join(os.homedir(), '.claude', 'projects')
  }

  /**
   * Get current working directory
   */
  getCurrentDirectory(): string {
    try {
      return execSync('pwd', { encoding: 'utf-8' }).trim()
    } catch (error) {
      console.error('Failed to get current directory:', error)
      return process.cwd()
    }
  }

  /**
   * Find project folder matching current path
   */
  findMatchingProject(pwd: string): string | null {
    const projectName = pathToProjectName(pwd)
    const projectPath = path.join(this.claudeProjectsPath, projectName)

    if (fs.existsSync(projectPath) && fs.statSync(projectPath).isDirectory()) {
      return projectPath
    }

    // Debug - output available projects
    console.log(`Looking for project: ${pathToProjectName(pwd)}`)
    console.log('Available projects:')
    try {
      const projects = fs.readdirSync(this.claudeProjectsPath)
      projects.forEach(project => {
        if (fs.statSync(path.join(this.claudeProjectsPath, project)).isDirectory()) {
          console.log(`  - ${project}`)
        }
      })
    } catch (error) {
      console.error('Failed to list projects:', error)
    }

    return null
  }

  /**
   * Find recent session containing specific keyword
   */
  findRecentSessionWithKeyword(
    projectDir: string,
    keyword: string,
    seconds: number = 60
  ): SessionInfo | null {
    const cutoffTime = new Date(Date.now() - seconds * 1000)
    const jsonlFiles = fs.readdirSync(projectDir).filter(f => f.endsWith('.jsonl'))

    for (const jsonlFile of jsonlFiles) {
      const filePath = path.join(projectDir, jsonlFile)
      try {
        const content = fs.readFileSync(filePath, 'utf-8')
        const lines = content.split('\n').filter(line => line.trim())

        // Read file in reverse order to check recent messages first
        for (let i = lines.length - 1; i >= 0; i--) {
          try {
            const data = JSON.parse(lines[i])

            if (
              data.type === 'user' &&
              data.message &&
              typeof data.message === 'object' &&
              data.message.role === 'user'
            ) {
              const timestamp = new Date(data.timestamp)
              if (timestamp < cutoffTime) continue

              const content = data.message.content || ''
              if (
                typeof content === 'string' &&
                content.includes(`<bash-input>${keyword}`)
              ) {
                return {
                  sessionId: data.sessionId,
                  projectPath: projectDir,
                  jsonlFile: filePath,
                  timestamp: data.timestamp
                }
              }
            }
          } catch (error) {
            // Ignore JSON parsing errors
            continue
          }
        }
      } catch (error) {
        console.error(`Failed to read file ${filePath}:`, error)
      }
    }

    return null
  }

  /**
   * Find most recent active session (without keyword)
   */
  findMostRecentSession(projectDir: string): SessionInfo | null {
    const jsonlFiles = fs.readdirSync(projectDir).filter(f => f.endsWith('.jsonl'))
    let mostRecent: SessionInfo | null = null
    let mostRecentTime = new Date(0)

    for (const jsonlFile of jsonlFiles) {
      const filePath = path.join(projectDir, jsonlFile)
      try {
        const content = fs.readFileSync(filePath, 'utf-8')
        const lines = content.split('\n').filter(line => line.trim())

        // Check from last line
        for (let i = lines.length - 1; i >= 0; i--) {
          try {
            const data = JSON.parse(lines[i])
            const timestamp = new Date(data.timestamp)

            if (timestamp > mostRecentTime && data.sessionId) {
              mostRecentTime = timestamp
              mostRecent = {
                sessionId: data.sessionId,
                projectPath: projectDir,
                jsonlFile: filePath,
                timestamp: data.timestamp
              }
              break // No need to check further in this file
            }
          } catch (error) {
            continue
          }
        }
      } catch (error) {
        console.error(`Failed to read file ${filePath}:`, error)
      }
    }

    return mostRecent
  }

  /**
   * Find Claude session in current directory
   */
  findCurrentSession(options: { keyword?: string; seconds?: number } = {}): SessionInfo | null {
    const pwd = this.getCurrentDirectory()
    console.log(`Current directory: ${pwd}`)

    const projectDir = this.findMatchingProject(pwd)
    if (!projectDir) {
      console.error('No matching Claude project found for current directory')
      return null
    }

    console.log(`Found project: ${projectDir}`)

    // Search by keyword if provided, otherwise find most recent session
    if (options.keyword) {
      const session = this.findRecentSessionWithKeyword(
        projectDir,
        options.keyword,
        options.seconds || 60
      )
      if (session) {
        console.log(`Found session with keyword "${options.keyword}": ${session.sessionId}`)
        return session
      }
    }

    // If not found by keyword or no keyword provided, find most recent session
    const session = this.findMostRecentSession(projectDir)
    if (session) {
      console.log(`Found most recent session: ${session.sessionId}`)
      return session
    }

    console.error('No active session found')
    return null
  }
}