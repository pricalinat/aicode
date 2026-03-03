#!/bin/bash

# Developer ID 인증서를 위한 CSR 생성 스크립트

echo "🔑 Generating Certificate Signing Request (CSR)..."

# CSR 정보
COUNTRY="KR"
STATE="Seoul"
CITY="Seoul"
ORGANIZATION="Byungwook Choi"
COMMON_NAME="Developer ID Application"
EMAIL="esc5221@gmail.com"

# CSR 생성
openssl req -new -newkey rsa:2048 -nodes \
  -keyout DeveloperID.key \
  -out DeveloperID.csr \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/CN=$COMMON_NAME/emailAddress=$EMAIL"

echo "✅ CSR generated: DeveloperID.csr"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://developer.apple.com/account/resources/certificates/add"
echo "2. Select 'Developer ID Application'"
echo "3. Upload DeveloperID.csr"
echo "4. Download the certificate"
echo "5. Double-click to install in Keychain"
echo ""
echo "⚠️  Keep DeveloperID.key safe - you'll need it!"