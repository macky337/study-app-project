#!/usr/bin/env python3
"""
クイックGitプッシュ - 即座実行版
現在の修正（expanderネストエラー修正）をすぐにプッシュ
"""

import subprocess
import os
from datetime import datetime

def run_git_command(command):
    """Gitコマンドを実行"""
    print(f"🔄 実行: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.stdout:
            clean_output = result.stdout.replace('\x00', '').strip()
            if clean_output:
                print(clean_output)
        
        if result.returncode != 0:
            print(f"❌ エラー: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """現在の修正をプッシュ"""
    print("⚡ クイックGitプッシュ - expanderネストエラー修正")
    print("=" * 50)
    
    # コミットメッセージ
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"fix: expanderネストエラーを修正とGit自動化スクリプト改善 - {timestamp}"
    
    print(f"📝 コミットメッセージ: {commit_message}")
    print()
    
    # Git操作実行
    commands = [
        "git add .",
        f'git commit -m "{commit_message}"',
        "git push origin main"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"[{i}/3] ", end="")
        if not run_git_command(command):
            print(f"\n❌ ステップ{i}で失敗しました")
            return
        print()
    
    print("🎉 プッシュ完了！")
    print("✅ expanderネストエラー修正が正常にプッシュされました")

if __name__ == "__main__":
    main()
