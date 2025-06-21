#!/usr/bin/env python3
"""
Railway用起動スクリプト
環境変数に基づいてStreamlitアプリを起動
"""

import os
import subprocess
import sys

def main():
    """Railway環境でStreamlitアプリを起動"""
    
    # 環境変数から設定を取得
    port = os.getenv('PORT', '8080')
    
    print("🚀 Starting Study Quiz App for Railway (Hobby Plan)")
    print("=" * 60)
    print(f"  - Port: {port}")
    print(f"  - DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
    print(f"  - OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    print(f"  - Plan: Railway Hobby Plan (Enhanced resources)")
    print(f"  - PDF Support: Up to 50MB files")
    print("=" * 60)
    
    # Streamlitコマンドを構築
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        # Streamlitアプリを起動
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 App stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
