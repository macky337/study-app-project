@echo off
echo 既存のStreamlitプロセスを終了中...
taskkill /F /IM streamlit.exe 2>nul
timeout /t 2 /nobreak >nul

echo Streamlitアプリを起動中...
start cmd /k "streamlit run app.py"

echo ✅ Streamlitアプリが新しいウィンドウで起動されました
echo 🌐 ブラウザで http://localhost:8501 にアクセスしてください
pause
