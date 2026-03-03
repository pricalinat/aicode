#!/bin/bash

# Claude Code Viewer macOS Build Script - Signed & Notarized Version
# Apple Developer 계정으로 서명 및 공증된 DMG 빌드

set -e

# .env 파일 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env 파일을 찾을 수 없습니다!"
    echo "📝 .env 파일을 생성하고 다음 정보를 입력하세요:"
    echo "   APPLE_ID=your-email@example.com"
    echo "   APPLE_APP_SPECIFIC_PASSWORD=your-app-specific-password"
    echo "   APPLE_TEAM_ID=XXXXXXXXXX"
    exit 1
fi

# 환경 변수 확인
if [ -z "$APPLE_ID" ] || [ -z "$APPLE_APP_SPECIFIC_PASSWORD" ] || [ -z "$APPLE_TEAM_ID" ]; then
    echo "❌ 필수 환경 변수가 설정되지 않았습니다!"
    echo "📝 .env 파일에 다음 정보가 모두 있는지 확인하세요:"
    echo "   APPLE_ID=$APPLE_ID"
    echo "   APPLE_APP_SPECIFIC_PASSWORD=(설정되어 있음: $([ -z "$APPLE_APP_SPECIFIC_PASSWORD" ] && echo "아니오" || echo "예"))"
    echo "   APPLE_TEAM_ID=$APPLE_TEAM_ID"
    exit 1
fi

echo "🚀 Claude Code Viewer macOS 서명된 빌드 시작..."
echo "📧 Apple ID: $APPLE_ID"
echo "👥 Team ID: $APPLE_TEAM_ID"

# 의존성 설치
echo "📦 의존성 설치 중..."
npm ci

# 이전 빌드 정리
echo "🧹 이전 빌드 파일 정리 중..."
rm -rf dist
rm -rf release

# 프로덕션 빌드
echo "🔨 앱 빌드 중..."
npm run build

# Electron 빌드 (서명 및 공증 포함)
echo "📱 macOS DMG 생성 중 (서명 및 공증 포함)..."
npm run dist:mac

# 빌드 결과 확인
if ls release/*.dmg 1> /dev/null 2>&1; then
    echo "✅ 빌드 완료!"
    echo "📍 빌드 파일 위치:"
    ls -la release/*.dmg
    
    # 파일 크기 표시
    echo ""
    echo "📊 파일 정보:"
    du -h release/*.dmg
    
    # 서명 확인
    echo ""
    echo "🔐 코드 서명 확인:"
    codesign -dv --verbose=4 release/*.dmg 2>&1 | grep "Authority" | head -3
else
    echo "❌ 빌드 실패: DMG 파일을 찾을 수 없습니다."
    exit 1
fi

echo ""
echo "🎉 완료! 서명 및 공증된 DMG 파일이 release 폴더에 생성되었습니다."
echo "✅ 이 DMG는 다른 사용자와 공유해도 '손상됨' 경고가 나타나지 않습니다."