#!/bin/bash

# デプロイ前にバージョン情報を更新するスクリプト

echo "バージョン情報を更新中..."

# 現在のGit情報を取得
VERSION=$(git log --oneline | wc -l | awk '{printf "1.0.%d", $1}')
COMMIT_HASH=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_DATE=$(date +%Y-%m-%d)
COMMIT_COUNT=$(git rev-list --count HEAD)
REPOSITORY_URL=$(git remote get-url origin)

# version.jsonファイルを生成
cat > version.json << EOF
{
  "version": "$VERSION",
  "commit_hash": "$COMMIT_HASH",
  "branch": "$BRANCH",
  "build_date": "$BUILD_DATE",
  "commit_count": $COMMIT_COUNT,
  "repository_url": "$REPOSITORY_URL"
}
EOF

echo "バージョン情報が更新されました:"
cat version.json

echo "更新完了！"
