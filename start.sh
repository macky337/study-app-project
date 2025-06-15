#!/bin/bash
# Railway用の起動スクリプト

# 環境変数からポート番号を取得（デフォルト: 8080）
PORT=${PORT:-8080}

echo "🚀 Starting Streamlit app on port $PORT"
echo "📋 Environment check:"
echo "  - PORT: $PORT"
echo "  - DATABASE_URL: ${DATABASE_URL:+Set}"
echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:+Set}"

# Streamlitアプリを起動
streamlit run app.py \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false
