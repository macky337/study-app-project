#!/usr/bin/env python3
"""
Streamlitアプリ起動チェック
PDF機能が正常に動作するか確認
"""

import subprocess
import sys
import os
import webbrowser
import time

def check_dependencies():
    """必要な依存関係をチェック"""
    print("📦 依存関係チェック中...")
    
    required_packages = [
        'streamlit',
        'PyPDF2', 
        'pdfplumber',
        'sqlmodel',
        'psycopg2',
        'openai'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未インストール)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  不足しているパッケージ: {', '.join(missing)}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    print("✅ すべての依存関係が満たされています")
    return True

def start_streamlit():
    """Streamlitアプリを起動"""
    print("\n🚀 Streamlitアプリを起動中...")
    
    try:
        # ポート8501でStreamlitを起動
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ]
        
        print("コマンド:", " ".join(cmd))
        print("\n" + "="*50)
        print("🌐 アプリURL: http://localhost:8501")
        print("📋 PDF機能テスト手順:")
        print("1. ブラウザでアプリが開きます")
        print("2. 左サイドバーから「🔧 問題管理」を選択") 
        print("3. 「📄 PDF問題生成」タブをクリック")
        print("4. PDFファイルをアップロード")
        print("5. 設定を調整して「🎯 PDFから問題を生成」")
        print("\n⚠️  アプリを停止するには Ctrl+C を押してください")
        print("="*50)
        
        # 2秒後にブラウザを開く
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:8501')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Streamlit起動
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
    except KeyboardInterrupt:
        print("\n👋 アプリを停止しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\n💡 手動でアプリを起動してください:")
        print("streamlit run app.py")

def main():
    """メイン実行"""
    print("🧪 PDF機能付きStudy Quiz App - 起動チェック")
    print("="*50)
    
    # 依存関係チェック
    if not check_dependencies():
        print("\n❌ 依存関係が不足しています。インストール後に再実行してください。")
        return
    
    # 環境変数チェック
    print("\n🔧 環境変数チェック...")
    env_vars = ['DATABASE_URL', 'OPENAI_API_KEY']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 設定済み")
        else:
            print(f"⚠️  {var}: 未設定")
    
    print("\n💡 注意: 環境変数が未設定でも一部機能は動作します")
    
    # PDFファイル存在チェック
    print("\n📄 PDFファイルチェック...")
    test_paths = [
        r"c:\Users\user\OneDrive\ScanSnap\202411_(タイトル).pdf",
        r"c:\Users\user\Documents\*.pdf",
        r"c:\Users\user\Desktop\*.pdf"
    ]
    
    pdf_found = False
    for path in test_paths:
        if '*' in path:
            import glob
            files = glob.glob(path)
            if files:
                print(f"✅ PDFファイルを発見: {files[0]}")
                pdf_found = True
                break
        elif os.path.exists(path):
            print(f"✅ PDFファイルを発見: {path}")
            pdf_found = True
            break
    
    if not pdf_found:
        print("⚠️  テスト用PDFファイルが見つかりません")
        print("任意のPDFファイルを準備してアプリ内でアップロードしてください")
    
    # Streamlit起動確認
    print("\n🚀 Streamlitアプリを起動しますか？")
    response = input("起動する場合は Enter を押してください (q で終了): ")
    
    if response.lower() != 'q':
        start_streamlit()
    else:
        print("👋 終了します")

if __name__ == "__main__":
    main()
