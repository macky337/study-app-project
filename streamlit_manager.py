"""
Streamlit プロセス管理ユーティリティ
ポート競合の解決とアプリの安全な再起動
"""

import os
import sys
import subprocess
import time
import psutil
import signal

def find_streamlit_processes():
    """Streamlitプロセスを検索"""
    streamlit_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # プロセス名または コマンドラインにstreamlitが含まれるプロセスを検索
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('streamlit' in arg.lower() for arg in cmdline):
                    streamlit_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return streamlit_processes

def find_processes_using_port(port):
    """指定されたポートを使用しているプロセスを検索"""
    processes = []
    
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    return processes

def kill_process_safely(proc, timeout=5):
    """プロセスを安全に終了"""
    try:
        print(f"プロセス終了中: PID {proc.pid}, Name: {proc.name()}")
        
        # まず丁寧に終了を試す
        proc.terminate()
        
        # 少し待つ
        try:
            proc.wait(timeout=timeout)
            print(f"プロセス {proc.pid} は正常に終了しました")
            return True
        except psutil.TimeoutExpired:
            # タイムアウトした場合は強制終了
            print(f"プロセス {proc.pid} のタイムアウト。強制終了します...")
            proc.kill()
            proc.wait(timeout=timeout)
            print(f"プロセス {proc.pid} を強制終了しました")
            return True
            
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"プロセス終了エラー: {e}")
        return False

def cleanup_streamlit_processes():
    """Streamlitプロセスをクリーンアップ"""
    print("=== Streamlit プロセス クリーンアップ ===")
    
    # Streamlitプロセスを検索
    streamlit_procs = find_streamlit_processes()
    
    if not streamlit_procs:
        print("実行中のStreamlitプロセスは見つかりませんでした")
    else:
        print(f"{len(streamlit_procs)}個のStreamlitプロセスが見つかりました:")
        for proc in streamlit_procs:
            print(f"  PID: {proc.pid}, Name: {proc.name()}")
        
        # プロセスを終了
        for proc in streamlit_procs:
            kill_process_safely(proc)
    
    # ポート8503, 8504, 8505を使用しているプロセスもチェック
    for port in [8503, 8504, 8505]:
        port_procs = find_processes_using_port(port)
        if port_procs:
            print(f"\nポート {port} を使用しているプロセス:")
            for proc in port_procs:
                print(f"  PID: {proc.pid}, Name: {proc.name()}")
                kill_process_safely(proc)

def start_streamlit_app(port=8505):
    """Streamlitアプリを起動"""
    print(f"\n=== Streamlit アプリ起動 (ポート {port}) ===")
    
    try:
        # 現在のディレクトリがプロジェクトルートかチェック
        if not os.path.exists('app.py'):
            print("❌ app.py が見つかりません。正しいディレクトリで実行してください。")
            return False
        
        # Streamlitを起動
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', str(port)]
        
        print(f"実行コマンド: {' '.join(cmd)}")
        print("Streamlitを起動しています...")
        
        # バックグラウンドで起動
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 少し待ってプロセスが正常に開始されたかチェック
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ Streamlit アプリが正常に起動しました")
            print(f"🌐 ブラウザで http://localhost:{port} にアクセスしてください")
            
            # 初期ログを表示
            try:
                # 非ブロッキングで出力を読み取り
                import select
                import sys
                
                print("\n--- 起動ログ ---")
                start_time = time.time()
                while time.time() - start_time < 5:  # 5秒間ログを表示
                    if process.stdout and process.stdout.readable():
                        output = process.stdout.readline()
                        if output:
                            print(output.strip())
                    time.sleep(0.1)
                
            except Exception as log_error:
                print(f"ログ表示エラー: {log_error}")
            
            return True
        else:
            # プロセスが終了している場合
            stdout, stderr = process.communicate()
            print(f"❌ Streamlit の起動に失敗しました")
            print(f"Exit code: {process.returncode}")
            if stdout:
                print(f"STDOUT: {stdout}")
            if stderr:
                print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ アプリ起動エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Streamlit プロセス管理ツール")
    print("=" * 40)
    
    # 既存プロセスのクリーンアップ
    cleanup_streamlit_processes()
    
    # 少し待機
    time.sleep(2)
    
    # アプリを起動
    if start_streamlit_app():
        print("\n🎉 アプリケーションの起動が完了しました！")
        print("\n💡 使用方法:")
        print("  - ブラウザが自動的に開かない場合は、手動でURLにアクセスしてください")
        print("  - アプリを停止するには Ctrl+C を押してください")
        print("  - このスクリプトを再実行すると既存プロセスを終了して再起動します")
        
        # プロセスが実行中の間は待機
        try:
            print("\nStreamlitアプリが実行中です。終了するには Ctrl+C を押してください...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n終了シグナルを受信しました。プロセスをクリーンアップしています...")
            cleanup_streamlit_processes()
            print("✅ クリーンアップ完了")
    else:
        print("\n❌ アプリケーションの起動に失敗しました")
        print("\n🔧 トラブルシューティング:")
        print("  1. 必要なライブラリがインストールされているか確認: pip install streamlit")
        print("  2. app.py ファイルが存在するか確認")
        print("  3. Python環境が正しく設定されているか確認")
        print("  4. 管理者権限で実行してみてください")

if __name__ == "__main__":
    main()
