#!/bin/bash

# 問題のある環境変数を強制削除
unset PORT
unset STREAMLIT_SERVER_PORT

# Streamlitを設定ファイルのみで起動
echo "Starting Streamlit with config file only..."
streamlit run app.py
