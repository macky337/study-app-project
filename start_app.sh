#!/bin/bash

# Study Quiz App - 起動スクリプト
# 音声分割機能付きのアプリケーションを起動

echo "🎯 Study Quiz App を起動しています..."
echo ""

# 仮想環境のパスを設定
VENV_PATH="/Users/nori/projects/study-app-project/.venv"
PYTHON_PATH="$VENV_PATH/bin/python"

# 仮想環境の存在確認
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ エラー: 仮想環境が見つかりません"
    echo "   パス: $PYTHON_PATH"
    echo "   仮想環境を作成してから再実行してください"
    exit 1
fi

echo "✅ 仮想環境を確認しました"

# 必要なパッケージの確認
echo "📦 必要なパッケージを確認中..."
$PYTHON_PATH -c "
import streamlit
import openai
import pydub
print('✅ 基本パッケージ: OK')
print('✅ OpenAI: OK') 
print('✅ pydub (音声処理): OK')
"

if [ $? -ne 0 ]; then
    echo "❌ エラー: 必要なパッケージが不足しています"
    echo "   requirements.txtからインストールしてください:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "🚀 アプリケーションを起動中..."
echo "📱 ブラウザでアクセス: http://localhost:8501"
echo "🎤 新機能: 音声文字起こし・議事録作成機能が利用可能です"
echo ""
echo "💡 停止するには Ctrl+C を押してください"
echo ""

# Streamlitアプリケーションを起動
$PYTHON_PATH -m streamlit run app.py \
    --server.address localhost \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
