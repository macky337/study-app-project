#!/bin/bash

# ブラウザでアプリを開く
echo "🌐 ブラウザでStudy Quiz Appを開いています..."

# macOSの場合
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8501
# Linuxの場合
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:8501
# Windowsの場合
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    start http://localhost:8501
else
    echo "📱 以下のURLをブラウザで開いてください:"
    echo "http://localhost:8501"
fi
