"""
Railway対応: Flask版Study Quiz App
Streamlitの代替として一時的に使用
"""
print("=" * 80)
print("FLASK APP STARTING - NOT STREAMLIT!")
print("If you see Streamlit errors, Railway is ignoring the Dockerfile")
print("=" * 80)

from flask import Flask, render_template_string, request, redirect, url_for, session
import os
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Quiz App - Railway対応版</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }
        .status {
            background-color: #e8f5e8;
            border: 1px solid #4caf50;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .error {
            background-color: #ffeaea;
            border: 1px solid #f44336;
            color: #d32f2f;
        }
        .success {
            background-color: #e8f5e8;
            border: 1px solid #4caf50;
            color: #2e7d32;
        }
        .info {
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            color: #1976d2;
        }
        .nav {
            margin: 20px 0;
            text-align: center;
        }
        .nav a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .nav a:hover {
            background-color: #2980b9;
        }
        .debug-info {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Study Quiz App</h1>
            <p>Railway対応版 - デプロイメント確認用</p>
        </div>
        
        <div class="nav">
            <a href="{{ url_for('home') }}">🏠 ホーム</a>
            <a href="{{ url_for('debug') }}">🔧 デバッグ情報</a>
            <a href="{{ url_for('status') }}">📊 ステータス</a>
        </div>
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """ホームページ"""
    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="status success">
        <h2>✅ Railway デプロイメント成功！</h2>
        <p>Study Quiz Appが正常にRailway上で動作しています。</p>
    </div>
    
    <div class="status info">
        <h3>📋 アプリケーション情報</h3>
        <ul>
            <li><strong>アプリ名:</strong> Study Quiz App</li>
            <li><strong>バージョン:</strong> Railway対応版</li>
            <li><strong>フレームワーク:</strong> Flask (Streamlit代替)</li>
            <li><strong>ポート:</strong> {{ port }}</li>
            <li><strong>ステータス:</strong> 正常稼働中</li>
        </ul>
    </div>
    
    <div class="status info">
        <h3>🚀 次のステップ</h3>
        <p>FlaskでのRailwayデプロイメントが成功したことが確認できました。</p>
        <p>これで、StreamlitでもRailwayでの正常動作が期待できます。</p>
        <ol>
            <li>このFlask版が正常に動作することを確認</li>
            <li>Streamlit版の修正を完了</li>
            <li>本来のStreamlitアプリに戻す</li>
        </ol>
    </div>
    
    <div class="status">
        <h3>🔄 Streamlit版への復帰方法</h3>
        <p>以下のコマンドでStreamlit版に戻すことができます：</p>
        <pre>git checkout main
git pull origin main</pre>
    </div>
    {% endblock %}
    """
    
    return render_template_string(HTML_TEMPLATE + content, 
                                port=os.environ.get('PORT', '8000'))

@app.route('/debug')
def debug():
    """デバッグ情報"""
    # 環境変数を取得
    env_vars = []
    for key in sorted(os.environ.keys()):
        value = os.environ[key]
        if len(value) > 100:
            value = value[:97] + "..."
        env_vars.append(f"{key}={value}")
    
    content = f"""
    {{% extends "base.html" %}}
    {{% block content %}}
    <div class="status">
        <h2>🔧 デバッグ情報</h2>
        <p>Railwayでの実行環境の詳細情報</p>
    </div>
    
    <div class="debug-info">
        <h3>📊 システム情報</h3>
        <p><strong>Python版:</strong> {sys.version}</p>
        <p><strong>作業ディレクトリ:</strong> {os.getcwd()}</p>
        <p><strong>PID:</strong> {os.getpid()}</p>
    </div>
    
    <div class="debug-info">
        <h3>🌍 環境変数 ({len(env_vars)} 個)</h3>
        <pre>{'<br>'.join(env_vars)}</pre>
    </div>
    
    <div class="debug-info">
        <h3>🚨 PORT関連変数</h3>
        <pre>{'<br>'.join([f"{k}={v}" for k, v in os.environ.items() if 'PORT' in k.upper()])}</pre>
    </div>
    {{% endblock %}}
    """
    
    return render_template_string(HTML_TEMPLATE + content)

@app.route('/status')
def status():
    """ステータス確認"""
    
    # データベース接続テスト
    db_status = "未実装（Flask版のため）"
    try:
        # ここで実際のデータベース接続をテストできます
        pass
    except Exception as e:
        db_status = f"エラー: {e}"
    
    content = f"""
    {{% extends "base.html" %}}
    {{% block content %}}
    <div class="status success">
        <h2>📊 アプリケーションステータス</h2>
    </div>
    
    <div class="status info">
        <h3>🌐 ネットワーク</h3>
        <p><strong>ポート:</strong> {os.environ.get('PORT', '8000')}</p>
        <p><strong>アドレス:</strong> 0.0.0.0</p>
        <p><strong>プロトコル:</strong> HTTP</p>
    </div>
    
    <div class="status">
        <h3>🗄️ データベース</h3>
        <p><strong>ステータス:</strong> {db_status}</p>
    </div>
    
    <div class="status">
        <h3>🔧 アプリケーション</h3>
        <p><strong>フレームワーク:</strong> Flask {getattr(__import__('flask'), '__version__', 'Unknown')}</p>
        <p><strong>デバッグモード:</strong> {app.debug}</p>
        <p><strong>環境:</strong> {os.environ.get('FLASK_ENV', 'production')}</p>
    </div>
    {{% endblock %}}
    """
    
    return render_template_string(HTML_TEMPLATE + content)

if __name__ == '__main__':
    # ポート設定
    port = int(os.environ.get('PORT', 8000))
    
    # デバッグ情報を出力
    logger.info("=" * 60)
    logger.info("FLASK STUDY QUIZ APP STARTING")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Environment variables with 'PORT': {[f'{k}={v}' for k, v in os.environ.items() if 'PORT' in k.upper()]}")
    logger.info("=" * 60)
    
    # アプリ起動
    app.run(host='0.0.0.0', port=port, debug=False)
