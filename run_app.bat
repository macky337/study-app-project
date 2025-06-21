@echo off
echo Study Quiz App起動スクリプト
echo =========================
echo.

echo Pythonの確認中...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [エラー] Pythonが見つかりません。Pythonがインストールされ、PATHに追加されていることを確認してください。
    goto :end
)

echo Streamlitの確認中...
pip show streamlit >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [警告] Streamlitがインストールされていません。インストールを試みます...
    pip install streamlit
    if %ERRORLEVEL% NEQ 0 (
        echo [エラー] Streamlitのインストールに失敗しました。
        goto :end
    )
)

echo 依存パッケージの確認中...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [警告] 一部の依存パッケージのインストールに失敗しました。アプリが正常に動作しない可能性があります。
)

echo.
echo アプリケーションを起動しています...
echo (ブラウザが自動的に開かない場合は、http://localhost:8501 にアクセスしてください)
echo.
echo Ctrl+Cでアプリケーションを終了できます。
echo.

streamlit run app.py

:end
echo.
echo 終了するには何かキーを押してください...
pause >nul
