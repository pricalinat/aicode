#!/bin/bash

# Claude Code Viewer CLI 설치 스크립트

echo "Installing Claude Code Viewer CLI..."

# 현재 디렉토리
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 의존성 설치
echo "Installing dependencies..."
npm install

# 실행 권한 부여
chmod +x "$SCRIPT_DIR/claude-viewer"
chmod +x "$SCRIPT_DIR/claude-viewer.ts"

# 심볼릭 링크 생성
echo "Creating symlink..."
if [ -L "/usr/local/bin/claude-viewer" ]; then
    echo "Removing existing symlink..."
    rm /usr/local/bin/claude-viewer
fi

ln -s "$SCRIPT_DIR/claude-viewer" /usr/local/bin/claude-viewer

echo "Installation complete!"
echo ""
echo "You can now use 'claude-viewer' command inside Claude CLI."
echo "Make sure to build and install the Electron app first."