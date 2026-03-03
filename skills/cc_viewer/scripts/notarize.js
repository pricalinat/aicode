const { notarize } = require('@electron/notarize');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env.notarize') });

exports.default = async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;
  
  // Only notarize on macOS
  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  
  console.log('Starting notarization process...');
  console.log(`App: ${appOutDir}/${appName}.app`);
  console.log('Environment variables check:');
  console.log('APPLE_ID:', process.env.APPLE_ID ? 'Set' : 'Not set');
  console.log('APPLE_APP_SPECIFIC_PASSWORD:', process.env.APPLE_APP_SPECIFIC_PASSWORD ? 'Set' : 'Not set');
  console.log('APPLE_TEAM_ID:', process.env.APPLE_TEAM_ID ? 'Set' : 'Not set');
  
  try {
    await notarize({
      appBundleId: 'com.mainpy.claude-code-viewer',
      appPath: `${appOutDir}/${appName}.app`,
      appleId: process.env.APPLE_ID,
      appleIdPassword: process.env.APPLE_APP_SPECIFIC_PASSWORD,
      teamId: process.env.APPLE_TEAM_ID
    });
    
    console.log('Notarization completed successfully!');
  } catch (error) {
    console.error('Notarization failed:', error);
    throw error;
  }
};