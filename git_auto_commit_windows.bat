@echo off
rem Windows専用 Git自動化バッチファイル
rem エンコーディング問題完全対応版

chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo 🤖 Windows版 Git自動化フロー開始
echo ==============================

cd /d "c:\Users\user\Documents\GitHub\study-app-project"

python auto_git_flow_windows.py

echo.
echo ✅ Git操作完了
echo ==============================
pause
