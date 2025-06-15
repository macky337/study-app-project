#!/usr/bin/env python3
"""
Streamlitアプリ起動スクリプト
"""

import subprocess
import sys
import os

def start_streamlit():
    """Streamlitアプリを起動"""
    
    print("🚀 Streamlitアプリを起動中...")
    
    # カレントディレクトリを確認
    current_dir = os.getcwd()
    print(f"📁 現在のディレクトリ: {current_dir}")
    
    # app.pyの存在確認
    app_path = os.path.join(current_dir, "app.py")
    if os.path.exists(app_path):
        print("✅ app.py が見つかりました")
    else:
        print("❌ app.py が見つかりません")
        return
    
    # Streamlit起動
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
        print(f"🔧 実行コマンド: {' '.join(cmd)}")
        
        # バックグラウンドで起動
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ Streamlitプロセス開始 (PID: {process.pid})")
        print("📊 ブラウザで http://localhost:8501 を開いてください")
        print("⏹️ 終了するには Ctrl+C を押してください")
        
        # 少し待ってから出力をチェック
        import time
        time.sleep(3)
        
        # プロセスがまだ実行中かチェック
        if process.poll() is None:
            print("🎉 Streamlitアプリが正常に起動しました")
        else:
            print("❌ Streamlitアプリの起動に失敗しました")
            stdout, stderr = process.communicate()
            if stdout:
                print(f"標準出力: {stdout}")
            if stderr:
                print(f"エラー出力: {stderr}")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")


if __name__ == "__main__":
    start_streamlit()
