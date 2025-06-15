#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway最小起動スクリプト
可能な限りシンプルにStreamlitを起動
"""

import os
import sys
import subprocess

def main():
    print("🚀 Railway Minimal Start")
    
    # 環境変数確認
    port = os.getenv('PORT', '8080')
    print(f"Port: {port}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python: {sys.executable}")
    
    # ファイル存在確認
    if not os.path.exists('app.py'):
        print("❌ app.py not found")
        sys.exit(1)
    
    print("✅ app.py found")
      # Streamlit起動
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app_minimal.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # execで現在のプロセスを置き換え（Railway推奨）
        os.execvp(sys.executable, cmd)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
