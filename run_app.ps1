# Study Quiz App起動スクリプト（PowerShell版）
Write-Host "Study Quiz App起動スクリプト" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

Write-Host "Pythonの確認中..." -ForegroundColor Yellow
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Host "[エラー] Pythonが見つかりません。Pythonがインストールされ、PATHに追加されていることを確認してください。" -ForegroundColor Red
    Read-Host "終了するには何かキーを押してください..."
    exit 1
}

Write-Host "Python バージョン:" -ForegroundColor Cyan
python --version

Write-Host ""
Write-Host "仮想環境の確認中..." -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "[OK] 仮想環境がアクティブです: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "[警告] 仮想環境がアクティブではありません。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Streamlitの確認中..." -ForegroundColor Yellow
$streamlitCheck = pip show streamlit 2>$null
if (-not $streamlitCheck) {
    Write-Host "[警告] Streamlitがインストールされていません。インストールを試みます..." -ForegroundColor Yellow
    pip install streamlit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[エラー] Streamlitのインストールに失敗しました。" -ForegroundColor Red
        Read-Host "終了するには何かキーを押してください..."
        exit 1
    }
}

Write-Host ""
Write-Host "依存パッケージの確認中..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] 一部の依存パッケージのインストールに失敗しました。アプリが正常に動作しない可能性があります。" -ForegroundColor Yellow
    }
} else {
    Write-Host "[警告] requirements.txtが見つかりません。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "アプリケーションを起動しています..." -ForegroundColor Green

# 利用可能なポートを探して起動
$ports = @(8501, 8502, 8504, 8505, 8506)
$startedSuccessfully = $false

foreach ($port in $ports) {
    Write-Host "ポート $port で起動を試みています..." -ForegroundColor Yellow
    
    # ポートが使用されているかチェック
    $portInUse = netstat -an | Select-String ":$port "
    
    if (-not $portInUse) {
        Write-Host "ポート $port は利用可能です。アプリを起動します..." -ForegroundColor Green
        Write-Host "(ブラウザが自動的に開かない場合は、http://localhost:$port にアクセスしてください)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Ctrl+Cでアプリケーションを終了できます。" -ForegroundColor Cyan
        Write-Host ""
        
        # Streamlitアプリを起動
        streamlit run app.py --server.port $port
        $startedSuccessfully = $true
        break
    } else {
        Write-Host "ポート $port は既に使用されています。" -ForegroundColor Yellow
    }
}

if (-not $startedSuccessfully) {
    Write-Host "[エラー] 利用可能なポートが見つかりませんでした。手動でポートを指定してください:" -ForegroundColor Red
    Write-Host "streamlit run app.py --server.port <ポート番号>" -ForegroundColor Cyan
}
