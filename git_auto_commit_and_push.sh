#!/bin/bash
# 変更内容から自動コミットメッセージを生成し、develop/main両方にpushし、developに戻る
# 使い方：ターミナルで./git_auto_commit_and_push.shを実行

set -e

# 変更がなければ終了
if git diff --quiet && git diff --cached --quiet; then
  echo "コミット対象の変更がありません。"
  exit 0
fi

# 変更ファイル一覧取得
CHANGED_FILES=$(git status --short)

# コミットメッセージ自動生成
COMMIT_MSG="auto: 変更ファイル\n$CHANGED_FILES"

echo "コミットメッセージ:"
echo "$COMMIT_MSG"

git add -A
git commit -m "$COMMIT_MSG"

# developにpush
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin $CURRENT_BRANCH

# mainにもpush（develop→mainマージ＆push）
git fetch origin main
git checkout main
git merge $CURRENT_BRANCH --no-edit
git push origin main

git checkout develop
echo "developブランチに戻りました。"
