#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway起動診断スクリプト
本番環境でのエラー原因を特定
"""

import os
import sys
import traceback

print("🔍 Railway起動診断開始")
print("=" * 50)

# 環境変数チェック
def check_environment():
    """環境変数をチェック"""
    print("📋 環境変数チェック:")
    
    required_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'PORT']
    optional_vars = ['DATABASE_PUBLIC_URL', 'POSTGRES_URL']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: 設定済み ({value[:20]}...)")
        else:
            print(f"   ❌ {var}: 未設定")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: 設定済み ({value[:20]}...)")
        else:
            print(f"   ⚠️ {var}: 未設定")

# インポートテスト
def test_imports():
    """重要なモジュールのインポートテスト"""
    print("\n📦 インポートテスト:")
    
    test_modules = [
        ('streamlit', 'Streamlit'),
        ('sqlmodel', 'SQLModel'), 
        ('openai', 'OpenAI'),
        ('dotenv', 'python-dotenv'),
        ('psycopg2', 'PostgreSQL adapter')
    ]
    
    for module, name in test_modules:
        try:
            __import__(module)
            print(f"   ✅ {name}: OK")
        except ImportError as e:
            print(f"   ❌ {name}: エラー - {e}")

# データベース接続テスト
def test_database():
    """データベース接続テスト"""
    print("\n🗄️ データベース接続テスト:")
    
    try:
        from database.connection import engine, DATABASE_URL
        
        if not DATABASE_URL:
            print("   ❌ DATABASE_URL が設定されていません")
            return False
            
        if not engine:
            print("   ❌ データベースエンジンの作成に失敗")
            return False
            
        # 接続テスト
        from sqlmodel import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("   ✅ データベース接続: OK")
            return True
            
    except Exception as e:
        print(f"   ❌ データベース接続エラー: {e}")
        traceback.print_exc()
        return False

# アプリケーションインポートテスト
def test_app_import():
    """app.pyのインポートテスト"""
    print("\n🎯 アプリケーションインポートテスト:")
    
    try:
        import app
        print("   ✅ app.py: インポート成功")
        return True
    except Exception as e:
        print(f"   ❌ app.py: インポートエラー - {e}")
        traceback.print_exc()
        return False

def main():
    """診断メイン処理"""
    
    try:
        check_environment()
        test_imports()
        test_database()
        test_app_import()
        
        print("\n🎉 診断完了")
        
        # Streamlit起動を試行
        print("\n🚀 Streamlit起動を試行...")
        
        port = os.getenv('PORT', '8080')
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", port,
            "--server.address", "0.0.0.0", 
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ]
        
        import subprocess
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        print(f"\n❌ 診断中にエラー発生: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
