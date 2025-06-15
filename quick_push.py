#!/usr/bin/env python3
"""
Git クイックプッシュスクリプト
事前定義されたメッセージで即座にpushまで実行
"""

import subprocess
import sys
import os
from datetime import datetime

def quick_push():
    """クイックプッシュ実行"""
    
    # 現在のディレクトリがGitリポジトリかチェック
    if not os.path.exists('.git'):
        print("❌ エラー: 現在のディレクトリはGitリポジトリではありません。")
        return False
    
    # タイムスタンプ付きコミットメッセージ
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"fix: Streamlit expander nesting error resolution ({timestamp})"
    
    commands = [
        ("git add .", "ファイルをステージング"),
        (f'git commit -m "{commit_message}"', "変更をコミット"),
        ("git push origin main", "リモートにプッシュ")
    ]
    
    print("🚀 Git クイックプッシュ開始")
    print("=" * 50)
    
    for cmd, desc in commands:
        print(f"\n🔄 {desc}...")
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                print(f"✅ {desc} 完了")
                if result.stdout.strip():
                    print(result.stdout)
            else:
                print(f"❌ {desc} 失敗")
                if result.stderr:
                    print(f"エラー: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ {desc} でエラー: {e}")
            return False
    
    print("\n🎉 すべてのGit操作が完了しました!")
    return True

if __name__ == "__main__":
    try:
        success = quick_push()
        if success:
            print("✅ リモートリポジトリへのプッシュが完了しました。")
        else:
            print("❌ 操作が失敗しました。")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  操作がキャンセルされました。")
        sys.exit(1)
