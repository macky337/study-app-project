@echo off
echo Streamlitプロセスを終了しています...

REM Streamlitプロセスを強制終了
taskkill /f /im streamlit.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq *streamlit*" 2>nul

REM ポート8503を使用しているプロセスを特定して終了
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8503') do (
    echo ポート8503を使用しているプロセス ID: %%a
    taskkill /f /pid %%a 2>nul
)

REM 少し待機
timeout /t 2 /nobreak >nul

echo Streamlitアプリを起動しています...
cd /d "%~dp0"
streamlit run app.py --server.port 8505

pause
