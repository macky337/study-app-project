# ベースイメージ (Railway用 - Flask版強制実行 v3.0)
FROM python:3.11-slim

# キャッシュバスター: 2025-06-24-22:22
RUN echo "Force rebuild at $(date)" > /tmp/build_time

# PostgreSQLクライアントツールをインストール
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ作成
WORKDIR /app

# 依存パッケージコピー＆インストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体コピー
COPY . .

# Streamlitのポート開放 (固定ポート8000)
EXPOSE 8000

# Flask版確認
RUN echo "This container will run Flask app, not Streamlit" > /tmp/app_type

# アプリ起動コマンド - Flask版で確実に動作させる (v3.0)
CMD ["sh", "-c", "echo 'Starting Flask app...' && python flask_app.py"]