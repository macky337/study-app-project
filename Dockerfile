# ベースイメージ
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

# Streamlitのポートを開放
EXPOSE 8000

# アプリ起動コマンド
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]