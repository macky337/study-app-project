#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超シンプルGit自動化スクリプト
Windows環境での確実な動作を保証
"""

import os
import subprocess
from datetime import datetime

def simple_git_commit():
    """シンプルなGitコミット実行"""
    print("🤖 シンプルGit自動化開始")
    
    try:
        # 現在のディレクトリを変更
        os.chdir(r"c:\Users\user\Documents\GitHub\study-app-project")
        
        # 1. ファイル追加
        print("📦 ファイル追加中...")
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ ファイル追加失敗: {result.stderr}")
            return False
        print("✅ ファイル追加完了")
        
        # 2. コミット実行
        print("💾 コミット中...")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"fix: Windows環境エンコーディング問題修正 ({timestamp})"
        
        result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, text=True)
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                print("ℹ️ コミットする変更がありません")
                return True
            else:
                print(f"❌ コミット失敗: {result.stderr}")
                return False
        print("✅ コミット完了")
        
        # 3. プッシュ実行
        print("🚀 プッシュ中...")
        result = subprocess.run(['git', 'push'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ プッシュ失敗: {result.stderr}")
            print("ℹ️ ローカルコミットは完了しています")
        else:
            print("✅ プッシュ完了")
        
        print("🎉 Git操作完了！")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    simple_git_commit()
    input("Press Enter to exit...")
