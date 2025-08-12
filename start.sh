#!/bin/bash

# Railway環境の判定
if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$PORT" ]; then
    echo "Starting in Railway environment..."
    echo "PORT=${PORT:-8080}"
    streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true
else
    echo "Starting in local environment..."
    # ローカル環境では問題のある環境変数を削除
    unset STREAMLIT_SERVER_PORT
    streamlit run app.py
fi
