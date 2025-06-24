#!/usr/bin/env python3
"""
Railway対応Streamlitランチャー
環境変数による干渉を完全に回避
"""
import os
import sys
import subprocess

def clean_environment():
    """問題のある環境変数を削除・上書き"""
    
    # まず全てのPORT関連環境変数を表示
    print("Environment variables before cleanup:")
    for key, value in os.environ.items():
        if 'PORT' in key.upper():
            print(f"  {key}={value}")
    
    # 問題のある環境変数を削除
    problematic_vars = ['PORT', 'STREAMLIT_SERVER_PORT']
    for var in problematic_vars:
        if var in os.environ:
            print(f"Removing problematic environment variable: {var}={os.environ[var]}")
            del os.environ[var]
    
    # Streamlitが期待する環境変数を正しい値で設定
    os.environ['STREAMLIT_SERVER_PORT'] = '8000'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    
    print("Environment variables after cleanup:")
    for key, value in os.environ.items():
        if 'PORT' in key.upper() or 'STREAMLIT' in key.upper():
            print(f"  {key}={value}")

def launch_streamlit():
    """Streamlitを設定ファイルのみで起動"""
    print("Starting Streamlit with config file only...")
    
    # Streamlitを起動（環境変数なし、コマンドライン引数なし）
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("Railway Streamlit Launcher")
    print("=" * 50)
    
    clean_environment()
    launch_streamlit()
