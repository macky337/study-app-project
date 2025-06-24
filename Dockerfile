# Study Quiz App - Railway対応版
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

# Streamlitのポート開放
EXPOSE 8080

# Streamlitアプリ起動
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]