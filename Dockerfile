# ベースイメージ (Railway用 - 設定ファイル依存版)
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

# アプリ起動コマンド - Pythonランチャー使用で環境変数を完全制御
CMD ["python", "launcher.py"]