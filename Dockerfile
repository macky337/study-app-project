# ベースイメージ (Railway用に修正済み)
FROM python:3.11-slim

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

# アプリ起動コマンド (Railway対応: 固定ポート使用)
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]