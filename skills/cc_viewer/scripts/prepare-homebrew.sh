#!/bin/bash

# Homebrew formula 준비 스크립트

echo "🍺 Preparing Homebrew formula..."

# GitHub 사용자명 입력
read -p "Enter your GitHub username: " GITHUB_USER

# 버전 확인
VERSION=$(node -p "require('./package.json').version")
echo "📦 Version: $VERSION"

# DMG 파일 빌드 (macOS에서만)
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "🔨 Building DMG..."
  npm run dist:mac
  
  # SHA256 계산
  DMG_FILE="dist/claude-code-viewer-${VERSION}.dmg"
  if [ -f "$DMG_FILE" ]; then
    SHA256=$(shasum -a 256 "$DMG_FILE" | awk '{print $1}')
    echo "✅ SHA256: $SHA256"
  else
    echo "❌ DMG file not found"
    exit 1
  fi
fi

# Formula 템플릿 업데이트
FORMULA_FILE="Formula/claude-code-viewer.rb"
sed -i.bak "s/YOUR_USERNAME/$GITHUB_USER/g" "$FORMULA_FILE"
sed -i.bak "s/REPLACE_WITH_ACTUAL_SHA256/$SHA256/g" "$FORMULA_FILE"
rm "${FORMULA_FILE}.bak"

echo "✅ Formula updated!"
echo ""
echo "📋 Next steps:"
echo "1. Create a GitHub release with tag v$VERSION"
echo "2. Upload the DMG file to the release"
echo "3. Create homebrew-tap repository on GitHub"
echo "4. Copy Formula/claude-code-viewer.rb to the tap repository"
echo "5. Users can install with: brew tap $GITHUB_USER/tap && brew install claude-code-viewer"