# Study Quiz App - Railway対応版
FROM python:3.11-slim

# PostgreSQLクライアントとffmpegをインストール
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ作成
WORKDIR /app

# 依存パッケージコピー＆インストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体コピー
COPY . .

# ポート設定（Railway環境では$PORTが自動設定される）
EXPOSE $PORT

# Streamlitアプリ起動（Railway環境対応）
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true