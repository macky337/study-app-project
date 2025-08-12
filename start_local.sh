#!/bin/bash

# Study Quiz App 起動スクリプト
# 使用方法: ./start_local.sh

echo "🎯 Study Quiz App を起動しています..."

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境の有効化確認
if [ ! -d ".venv" ]; then
    echo "❌ 仮想環境が見つかりません。setup.shを先に実行してください。"
    exit 1
fi

# 必要な環境変数の確認
if [ ! -f ".env" ]; then
    echo "⚠️  .envファイルが見つかりません。OPENAI_API_KEYを設定してください。"
fi

# Streamlitアプリの起動
echo "🚀 アプリケーションを起動中..."
echo "📱 ブラウザでアクセス: http://localhost:8501"
echo "🎤 新機能: 音声文字起こし・議事録作成機能が利用可能です"
echo ""
echo "💡 停止するには Ctrl+C を押してください"
echo ""

.venv/bin/python -m streamlit run app.py \
    --server.address localhost \
    --server.port 8501 \
    --browser.gatherUsageStats false \
    --theme.base light
