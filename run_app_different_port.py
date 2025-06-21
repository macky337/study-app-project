import subprocess
import sys
import os
import time

def run_streamlit_on_different_port(port=8507):
    """
    指定したポートでStreamlitアプリケーションを実行します
    """
    print(f"🚀 ポート {port} でStreamlitアプリケーションを起動します...")
    
    # コマンドを組み立て
    command = f"streamlit run app.py --server.port={port}"
    
    try:
        # サブプロセスとして実行
        process = subprocess.Popen(command, shell=True)
        
        # 少し待機してブラウザが開くのを待つ
        time.sleep(2)
        
        print(f"✅ アプリケーションがポート {port} で起動しました")
        print(f"🌐 ブラウザで http://localhost:{port} を開いてアクセスしてください")
        
        # プロセスが終了するまで待機
        process.wait()
        
    except KeyboardInterrupt:
        # Ctrl+Cが押された場合
        print("\n⚠️ ユーザーによって中断されました")
        process.terminate()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
        
    return True

if __name__ == "__main__":
    # コマンドライン引数からポートを取得（指定されていない場合はデフォルト値を使用）
    port = 8507
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"⚠️ 無効なポート番号です: {sys.argv[1]}")
            print(f"🔄 デフォルトポート {port} を使用します")
    
    run_streamlit_on_different_port(port)
