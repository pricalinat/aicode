import { existsSync } from 'fs'
import { join, resolve, sep } from 'path'

// Map for caching
const pathCache = new Map<string, string>()

/**
 * Restore Claude project folder name to actual file system path
 * Example: -Users-lullu-mainpy-claude-code-web → /Users/lullu/mainpy/claude-code-web
 * Windows: C--Users-username-project → C:\Users\username\project
 * 
 * Algorithm:
 * - Windows: Extract drive letter and replace '--' with '\' 
 * - Unix: Start by replacing the first '-' with path separator, then for each '-',
 *   check if directory exists when replaced with path separator
 */
export function resolveProjectPath(projectName: string): string {
  // Check cache
  if (pathCache.has(projectName)) {
    return pathCache.get(projectName)!
  }

  // Empty string or only '-' case
  if (!projectName || projectName === '-') {
    const result = resolve(sep)
    pathCache.set(projectName, result)
    return result
  }

  // Check if this is a Windows project folder (starts with drive letter)
  const isWindowsProjectFolder = /^[A-Za-z]--/.test(projectName)
  
  // Unix project folders start with '-', Windows folders start with drive letter
  if (!projectName.startsWith('-') && !isWindowsProjectFolder) {
    // Already in path format
    pathCache.set(projectName, projectName)
    return projectName
  }

  // Handle Windows project folders (e.g., "C--Users-username-project")
  if (isWindowsProjectFolder) {
    // Extract drive letter and remaining path
    const driveMatch = projectName.match(/^([A-Za-z])--(.+)$/)
    if (driveMatch) {
      const [, driveLetter, pathPart] = driveMatch
      // Replace -- with :\ first, then replace remaining - with \
      // This may have false positives but gives more readable paths
      let windowsPath = `${driveLetter.toUpperCase()}--${pathPart}`
      windowsPath = windowsPath.replace(/--/, ':\\').replace(/-/g, '\\')
      const result = windowsPath
      pathCache.set(projectName, result)
      return result
    }
  }

  // Array to construct result path
  const parts: string[] = []
  
  // Remove first '-' as it represents root (Unix paths only)
  let remaining = projectName.substring(1)
  
  // Handle empty directory names (starting with --)
  while (remaining.startsWith('-')) {
    // Consecutive '-' means empty directory
    parts.push('')
    remaining = remaining.substring(1)
  }
  
  // Path constructed so far
  let currentPath = sep
  
  while (remaining.length > 0) {
    // Find next '-' position
    let nextDashIndex = remaining.indexOf('-')
    
    if (nextDashIndex === -1) {
      // If no more '-', treat the rest as one part
      parts.push(remaining)
      currentPath = join(currentPath, remaining)
      break
    }
    
    // Check path when '-' is replaced with path separator
    const possiblePart = remaining.substring(0, nextDashIndex)
    const possiblePathAsSlash = join(currentPath, possiblePart)
    
    // Also check path when '-' is replaced with '_'
    const possiblePathAsUnderscore = join(currentPath, possiblePart.replace(/-/g, '_'))
    
    // Resolve paths to handle Windows drive letters and normalize
    const resolvedPathAsSlash = resolve(possiblePathAsSlash)
    const resolvedPathAsUnderscore = resolve(possiblePathAsUnderscore)
    
    if (existsSync(resolvedPathAsSlash)) {
      // If directory exists, separate with path separator
      parts.push(possiblePart)
      currentPath = possiblePathAsSlash
      remaining = remaining.substring(nextDashIndex + 1)
    } else if (existsSync(resolvedPathAsUnderscore)) {
      // If exists when replaced with '_', process with '_'
      parts.push(possiblePart.replace(/-/g, '_'))
      currentPath = possiblePathAsUnderscore
      remaining = remaining.substring(nextDashIndex + 1)
    } else {
      // If directory doesn't exist, include up to next '-' as one part
      // Example: claude-code-web case
      let foundValid = false
      let searchIndex = nextDashIndex + 1
      
      while (searchIndex < remaining.length) {
        const nextSearchIndex = remaining.indexOf('-', searchIndex)
        if (nextSearchIndex === -1) {
          // Search to the end
          const testPart = remaining
          const testPath = join(currentPath, testPart)
          const testPartWithUnderscore = testPart.replace(/-/g, '_')
          const testPathWithUnderscore = join(currentPath, testPartWithUnderscore)
          
          // Resolve paths for Windows compatibility
          const resolvedTestPath = resolve(testPath)
          const resolvedTestPathWithUnderscore = resolve(testPathWithUnderscore)
          
          if (existsSync(resolvedTestPath)) {
            parts.push(testPart)
            currentPath = testPath
            remaining = ''
            foundValid = true
          } else if (existsSync(resolvedTestPathWithUnderscore)) {
            parts.push(testPartWithUnderscore)
            currentPath = testPathWithUnderscore
            remaining = ''
            foundValid = true
          }
          break
        }
        
        // Test including up to next '-'
        const testPart = remaining.substring(0, nextSearchIndex)
        const testPath = join(currentPath, testPart)
        
        // Also test path with '_'
        const testPartWithUnderscore = testPart.replace(/-/g, '_')
        const testPathWithUnderscore = join(currentPath, testPartWithUnderscore)
        
        // Resolve paths for Windows compatibility  
        const resolvedTestPath = resolve(testPath)
        const resolvedTestPathWithUnderscore = resolve(testPathWithUnderscore)
        
        if (existsSync(resolvedTestPath)) {
          parts.push(testPart)
          currentPath = testPath
          remaining = remaining.substring(nextSearchIndex + 1)
          foundValid = true
          break
        } else if (existsSync(resolvedTestPathWithUnderscore)) {
          parts.push(testPartWithUnderscore)
          currentPath = testPathWithUnderscore
          remaining = remaining.substring(nextSearchIndex + 1)
          foundValid = true
          break
        }
        
        searchIndex = nextSearchIndex + 1
      }
      
      if (!foundValid) {
        // If nothing matches, treat the whole as one
        parts.push(remaining)
        currentPath = join(currentPath, remaining)
        break
      }
    }
  }
  
  // Use the currentPath as the result since it's already built correctly
  const result = currentPath
  
  // Save to cache
  pathCache.set(projectName, result)
  
  return result
}

/**
 * Clear cache
 */
export function clearPathCache(): void {
  pathCache.clear()
}

/**
 * Check cache status (for debugging)
 */
export function getPathCacheSize(): number {
  return pathCache.size
}

/**
 * Get cached path for specific project (for debugging)
 */
export function getCachedPath(projectName: string): string | undefined {
  return pathCache.get(projectName)
}