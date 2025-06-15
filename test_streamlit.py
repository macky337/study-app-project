#!/usr/bin/env python3  
"""
Streamlit app test runner
"""

import subprocess
import sys
import time
import os

def run_streamlit_test():
    """Streamlitアプリを起動して基本的なエラーをチェック"""
    
    try:
        print("🧪 Streamlitアプリテスト開始")
        
        # streamlit config show で設定を表示
        print("\n📋 Streamlit設定:")
        result = subprocess.run(
            ["python", "-m", "streamlit", "config", "show"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Streamlit設定正常")
        else:
            print(f"⚠️ Streamlit設定エラー: {result.stderr}")
        
        # app.pyの基本的な構文チェック
        print("\n🔍 app.py構文チェック:")
        result = subprocess.run(
            ["python", "-m", "py_compile", "app.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ app.py構文正常")
        else:
            print(f"❌ app.py構文エラー: {result.stderr}")
            return False
        
        # Streamlitアプリの構文チェック（dry run的な実行）
        print("\n🏃 Streamlitアプリドライラン:")
        result = subprocess.run(
            ["python", "-c", "import app; print('App import successful')"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("✅ アプリインポート成功")
        else:
            print(f"❌ アプリインポートエラー: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return False
        
        print("\n🎯 基本テスト完了 - アプリは正常に動作する準備ができています")
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ テストタイムアウト")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = run_streamlit_test()
    if success:
        print("\n✅ アプリは起動可能な状態です")
        print("起動するには: streamlit run app.py")
    else:
        print("\n❌ アプリの修正が必要です")
        sys.exit(1)
