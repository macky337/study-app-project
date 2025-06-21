import subprocess
import os
import sys
import time

def kill_streamlit_processes():
    """Streamlitプロセスを終了します"""
    try:
        print("既存のStreamlitプロセスを終了しています...")
        # Windowsの場合
        subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq streamlit"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("✅ 既存のStreamlitプロセスを終了しました")
        # 少し待機
        time.sleep(2)
    except Exception as e:
        print(f"プロセス終了中にエラーが発生しました: {e}")

def run_streamlit_app(port=8501):
    """Streamlitアプリを指定したポートで起動します"""
    # カレントディレクトリをプロジェクトフォルダに変更
    os.chdir(r"c:\Users\user\Documents\GitHub\study-app-project")
    
    print(f"🚀 ポート {port} でStreamlitアプリを起動しています...")
    command = f"streamlit run app.py --server.port={port}"
    
    try:
        # 新しいコマンドプロンプトウィンドウでStreamlitを起動
        subprocess.Popen(f"start cmd /k {command}", shell=True)
        print(f"✅ アプリケーションがポート {port} で起動しました")
        print(f"🌐 ブラウザで http://localhost:{port} を開いてアクセスしてください")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    # 既存のStreamlitプロセスを終了
    kill_streamlit_processes()
    
    # ポート指定（引数から取得、なければデフォルト値）
    port = 8501
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"⚠️ 無効なポート番号です: {sys.argv[1]}")
            print(f"🔄 デフォルトポート {port} を使用します")
    
    # アプリを起動
    run_streamlit_app(port)
    
    print("\n✨ スクリプトの実行が完了しました。")
    print("📝 別のコマンドプロンプトウィンドウでStreamlitが起動しています。")
    print("⚠️ 終了する場合は、そのウィンドウを閉じてください。")
