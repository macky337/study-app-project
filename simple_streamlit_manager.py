"""
シンプルなStreamlit プロセス管理
標準ライブラリのみを使用した軽量版
"""

import os
import sys
import subprocess
import time
import json

def kill_streamlit_processes_windows():
    """WindowsでStreamlitプロセスを終了"""
    print("=== Streamlit プロセス終了 ===")
    
    try:
        # Streamlitプロセスを終了
        result = subprocess.run(
            ['taskkill', '/f', '/im', 'streamlit.exe'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ streamlit.exe プロセスを終了しました")
        else:
            print("ℹ️  streamlit.exe プロセスは見つかりませんでした")
        
        # Pythonプロセスの中からStreamlitを実行しているものを終了
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'processid,commandline', '/format:csv'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # ヘッダーをスキップ
            for line in lines:
                if 'streamlit' in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            pid = parts[-1].strip()
                            if pid.isdigit():
                                subprocess.run(['taskkill', '/f', '/pid', pid], check=False)
                                print(f"✅ Streamlit Python プロセス (PID: {pid}) を終了しました")
                        except:
                            pass
        
        # ポートを使用しているプロセスを終了
        for port in [8503, 8504, 8505]:
            try:
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if parts:
                                pid = parts[-1].strip()
                                if pid.isdigit():
                                    subprocess.run(['taskkill', '/f', '/pid', pid], check=False)
                                    print(f"✅ ポート {port} を使用していたプロセス (PID: {pid}) を終了しました")
            except Exception as e:
                print(f"ポート {port} のプロセス終了でエラー: {e}")
        
        print("✅ プロセス終了処理完了")
        
    except Exception as e:
        print(f"❌ プロセス終了エラー: {e}")

def start_streamlit_simple(port=8505):
    """Streamlitアプリをシンプルに起動"""
    print(f"\n=== Streamlit アプリ起動 (ポート {port}) ===")
    
    try:
        # app.pyの存在確認
        if not os.path.exists('app.py'):
            print("❌ app.py が見つかりません")
            current_dir = os.getcwd()
            print(f"現在のディレクトリ: {current_dir}")
            
            # ファイル一覧を表示
            files = [f for f in os.listdir('.') if f.endswith('.py')]
            print(f"Pythonファイル: {files}")
            return False
        
        print("✅ app.py が見つかりました")
        
        # Streamlitコマンドを構築
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', str(port)]
        
        print(f"実行コマンド: {' '.join(cmd)}")
        
        # 環境変数を設定（必要に応じて）
        env = os.environ.copy()
        
        # Streamlitを起動
        print("Streamlitを起動しています...")
        
        # 起動コマンドを実行
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=os.getcwd()
        )
        
        # 少し待機してプロセスの状態を確認
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ Streamlit アプリが起動しました！")
            print(f"🌐 ブラウザで http://localhost:{port} にアクセスしてください")
            print(f"📋 プロセスID: {process.pid}")
            return True
        else:
            print(f"❌ Streamlit の起動に失敗しました (終了コード: {process.returncode})")
            return False
            
    except FileNotFoundError:
        print("❌ Streamlitがインストールされていません")
        print("🔧 インストール方法: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        return False

def check_ports():
    """使用可能なポートをチェック"""
    print("\n=== ポート使用状況確認 ===")
    
    try:
        result = subprocess.run(
            ['netstat', '-an'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            used_ports = []
            for line in result.stdout.split('\n'):
                for port in [8503, 8504, 8505, 8506]:
                    if f':{port}' in line and 'LISTENING' in line:
                        used_ports.append(port)
            
            print("使用中のポート:", used_ports if used_ports else "なし")
            
            # 使用可能なポートを見つける
            available_port = None
            for port in [8505, 8506, 8507, 8508]:
                if port not in used_ports:
                    available_port = port
                    break
            
            print(f"推奨ポート: {available_port}")
            return available_port
        else:
            print("ポート情報を取得できませんでした")
            return 8505
            
    except Exception as e:
        print(f"ポートチェックエラー: {e}")
        return 8505

def show_instructions():
    """使用方法を表示"""
    print("\n" + "="*50)
    print("📋 使用方法:")
    print("  1. ブラウザが自動で開かない場合は、手動でURLにアクセス")
    print("  2. アプリを停止するには、ターミナルで Ctrl+C")
    print("  3. 問題が発生した場合は、このスクリプトを再実行")
    print("\n🔧 トラブルシューティング:")
    print("  - ポートエラー: 別のポート番号で再試行")
    print("  - モジュールエラー: pip install streamlit")
    print("  - 権限エラー: 管理者として実行")
    print("="*50)

def main():
    """メイン実行関数"""
    print("🚀 Streamlit アプリ管理ツール")
    print("="*40)
    
    # プロセス終了
    kill_streamlit_processes_windows()
    
    # 少し待機
    time.sleep(2)
    
    # 使用可能なポートを確認
    port = check_ports()
    
    # アプリ起動
    if start_streamlit_simple(port):
        show_instructions()
        
        # キーボード入力待ち
        try:
            input("\n✅ アプリが起動しました。終了するには Enter キーを押してください...")
        except KeyboardInterrupt:
            print("\n")
        
        print("アプリを終了しています...")
        kill_streamlit_processes_windows()
        print("✅ 終了完了")
        
    else:
        print("\n❌ アプリの起動に失敗しました")
        show_instructions()

if __name__ == "__main__":
    main()
