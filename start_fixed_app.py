#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アプリケーション起動確認スクリプト
"""

import sys
import os
import subprocess
import time

def start_app():
    """アプリケーションを起動"""
    
    print("アプリケーション起動中...")
    print("=" * 50)
    
    try:
        # Streamlitアプリを起動
        print("INFO: Streamlitアプリを起動しています...")
        print("INFO: ブラウザで http://localhost:8501 を開いてください")
        print("INFO: 終了するには Ctrl+C を押してください")
        print("=" * 50)
        
        # app.pyを起動
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\nアプリケーションを終了しています...")
    except Exception as e:
        print(f"ERROR: アプリ起動エラー: {e}")

def main():
    print("学習アプリケーション起動")
    print("修正された選択肢表示機能をテストしてください")
    print()
    print("修正内容:")
    print("  ✅ 選択肢がない問題の自動修正")
    print("  ✅ エラーハンドリングの追加")
    print("  ✅ デバッグログの追加")
    print("  ✅ Unicode エラーの修正")
    print()
    
    start_app()

if __name__ == "__main__":
    main()
