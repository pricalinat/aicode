import { app } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import { execSync } from 'child_process'

export function installCLI() {
  try {
    // Check if CLI is installed
    const cliInstalled = fs.existsSync('/usr/local/bin/ccviewer')
    
    if (cliInstalled) {
      // If already installed, check version
      const installedTarget = fs.readlinkSync('/usr/local/bin/ccviewer')
      const expectedSource = path.join(app.getPath('exe'), '..', '..', 'Resources', 'cli', 'claude-viewer-cli.js')
      
      if (installedTarget === expectedSource) {
        console.log('CLI already installed and up to date')
        return
      }
    }

    // CLI source path
    const cliSource = app.isPackaged
      ? path.join(process.resourcesPath, 'cli', 'claude-viewer-cli.js')
      : path.join(__dirname, '..', 'cli', 'claude-viewer-cli.js')

    if (!fs.existsSync(cliSource)) {
      console.error('CLI source not found:', cliSource)
      return
    }

    // Create /usr/local/bin directory
    try {
      execSync('mkdir -p /usr/local/bin', { stdio: 'ignore' })
    } catch (e) {
      console.error('Failed to create /usr/local/bin:', e)
    }

    // Remove existing symbolic links
    if (fs.existsSync('/usr/local/bin/ccviewer')) {
      try {
        fs.unlinkSync('/usr/local/bin/ccviewer')
      } catch (e) {
        console.error('Failed to remove existing CLI:', e)
      }
    }
    if (fs.existsSync('/usr/local/bin/claude-viewer')) {
      try {
        fs.unlinkSync('/usr/local/bin/claude-viewer')
      } catch (e) {
        console.error('Failed to remove old CLI:', e)
      }
    }

    // Create new symbolic link
    try {
      fs.symlinkSync(cliSource, '/usr/local/bin/ccviewer')
      console.log('CLI installed successfully')
      
      // Notify user (optional)
      const { dialog } = require('electron')
      dialog.showMessageBox({
        type: 'info',
        title: 'CLI Installed',
        message: 'ccviewer command has been installed.\nYou can now use it in Claude CLI.',
        buttons: ['OK']
      })
    } catch (e) {
      console.error('Failed to create CLI symlink:', e)
      
      // If permission issue, guide user for manual installation
      const { dialog } = require('electron')
      dialog.showMessageBox({
        type: 'warning',
        title: 'CLI Installation',
        message: 'Could not automatically install CLI command.\nPlease run the following in terminal:\n\nsudo ln -s "' + cliSource + '" /usr/local/bin/ccviewer',
        buttons: ['OK']
      })
    }
  } catch (error) {
    console.error('Error during CLI installation:', error)
  }
}