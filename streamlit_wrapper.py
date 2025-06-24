#!/usr/bin/env python3
"""
Railway対応の最終的なStreamlitラッパー
環境変数を完全に無視してStreamlitを起動
"""
import os
import sys
import subprocess
import signal

def kill_handler(signum, frame):
    """シグナルハンドラー"""
    print("Received termination signal, shutting down...")
    sys.exit(0)

def clean_environment():
    """環境変数を完全にクリーンアップ"""
    print("=" * 60)
    print("RAILWAY STREAMLIT WRAPPER")
    print("=" * 60)
    
    # 全環境変数を表示
    print("\n[DEBUG] All environment variables:")
    for key in sorted(os.environ.keys()):
        value = os.environ[key]
        if len(value) > 80:
            value = value[:77] + "..."
        print(f"  {key}={value}")
    
    # PORT関連変数を削除
    port_vars = []
    for key in list(os.environ.keys()):
        if 'PORT' in key.upper():
            port_vars.append(f"{key}={os.environ[key]}")
            del os.environ[key]
    
    if port_vars:
        print(f"\n[CLEANUP] Removed variables: {', '.join(port_vars)}")
    
    print("\n[SETUP] Setting up clean environment...")
    
def start_streamlit():
    """Streamlitを環境変数なしで起動"""
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGTERM, kill_handler)
    signal.signal(signal.SIGINT, kill_handler)
    
    # 環境変数をクリーンアップ
    clean_environment()
    
    # Streamlitを固定ポートで起動
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8000",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    print(f"\n[LAUNCH] Starting Streamlit with command:")
    print(f"  {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # 新しいプロセスとして起動
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # リアルタイムでログを出力
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()
        
        proc.wait()
        
    except KeyboardInterrupt:
        print("\nReceived interrupt, terminating...")
        proc.terminate()
        proc.wait()
    except Exception as e:
        print(f"\nError starting Streamlit: {e}")
        return 1
    
    return proc.returncode

if __name__ == "__main__":
    exit_code = start_streamlit()
    sys.exit(exit_code)
