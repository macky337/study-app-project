#!/usr/bin/env python3
"""
ローカル開発用PostgreSQL設定スクリプト
Railway本番環境がない場合のローカル開発環境セットアップ
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_local_postgres():
    """ローカルPostgreSQL設定のガイド"""
    print("🐘 ローカルPostgreSQL設定ガイド")
    print("=" * 50)
    
    print("""
### オプション1: Docker Compose (推奨)

1. docker-compose.yml を作成:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: studyapp
      POSTGRES_PASSWORD: password123
      POSTGRES_DB: study_quiz
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

2. 起動:
```bash
docker-compose up -d
```

3. .env ファイルを更新:
```
DATABASE_URL=postgresql://studyapp:password123@localhost:5432/study_quiz
```

### オプション2: ローカルPostgreSQLインストール

macOS (Homebrew):
```bash
brew install postgresql
brew services start postgresql
createdb study_quiz
```

### オプション3: Railway実際のデータベースURL使用

1. Railway Dashboard にアクセス
2. プロジェクト → Variables タブ
3. DATABASE_URL をコピー
4. .env ファイルに設定

### オプション4: デモモードで動作確認

現在は DATABASE_URL が正しく設定されていないため、
デモモードで動作しています。基本的な機能はテスト可能です。
""")

def check_database_options():
    """利用可能なデータベースオプションをチェック"""
    print("\n🔍 データベースオプション確認")
    print("-" * 30)
    
    # Docker確認
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker利用可能")
        else:
            print("❌ Docker未インストール")
    except FileNotFoundError:
        print("❌ Docker未インストール")
    
    # PostgreSQL確認
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL利用可能")
        else:
            print("❌ PostgreSQL未インストール")
    except FileNotFoundError:
        print("❌ PostgreSQL未インストール")
    
    # 現在の設定確認
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if "postgresql://" in db_url:
            print(f"📊 現在の設定: PostgreSQL ({db_url[:50]}...)")
        elif "sqlite://" in db_url:
            print(f"📊 現在の設定: SQLite ({db_url})")
        else:
            print(f"📊 現在の設定: その他 ({db_url[:50]}...)")
    else:
        print("❌ DATABASE_URL未設定（デモモードで動作）")

def main():
    setup_local_postgres()
    check_database_options()
    
    print(f"\n🚀 次のステップ:")
    print(f"1. 上記のいずれかの方法でPostgreSQLを設定")
    print(f"2. .env ファイルのDATABASE_URLを更新")
    print(f"3. アプリを再起動")
    print(f"4. 問題管理ページで整合性チェックをテスト")

if __name__ == "__main__":
    main()
