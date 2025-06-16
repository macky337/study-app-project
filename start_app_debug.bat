@echo off
echo 🚀 Study Quiz App 起動中...
cd /d "c:\Users\user\Documents\GitHub\study-app-project"

echo 🔍 Python環境確認中...
py --version

echo 🔍 依存関係確認中...
py -m pip list | findstr streamlit
py -m pip list | findstr openai

echo 🚀 Streamlitアプリ起動...
py -m streamlit run app.py --server.port 8501 --server.address localhost

pause
