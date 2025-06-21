@echo off
chcp 65001 >nul 2>&1
echo 🤖 Git自動化フロー開始
echo ==============================
cd /d "c:\Users\user\Documents\GitHub\study-app-project"
set PYTHONIOENCODING=utf-8
python auto_git_flow.py
echo.
echo ✅ Git操作完了
pause
