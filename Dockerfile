# ベースイメージ (Railway用 - Procfile削除版)
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

# 環境変数を強制的に無効化してからStreamlit起動
ENV PORT=
ENV STREAMLIT_SERVER_PORT=

# Streamlitのポート開放 (固定ポート8000)
EXPOSE 8000

# アプリ起動コマンド - 環境変数を明示的にクリアしてから実行
CMD ["sh", "-c", "unset PORT && unset STREAMLIT_SERVER_PORT && streamlit run app.py --server.port=8000 --server.address=0.0.0.0"]