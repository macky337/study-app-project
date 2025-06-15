#!/usr/bin/env python3
"""
Git自動プッシュスクリプト
変更をステージング→コミット→プッシュまで自動実行
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """コマンドを実行し、結果を表示"""
    print(f"\n🔄 {description}")
    print(f"実行: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"警告/エラー: {result.stderr}")
            
        if result.returncode != 0:
            print(f"❌ コマンドが失敗しました (終了コード: {result.returncode})")
            return False
        else:
            print("✅ 成功")
            return True
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def get_commit_message():
    """コミットメッセージを生成または入力"""
    print("\n📝 コミットメッセージを選択してください:")
    print("1. 自動生成メッセージを使用")
    print("2. カスタムメッセージを入力")
    
    choice = input("\n選択 (1 or 2): ").strip()
    
    if choice == "2":
        custom_message = input("\nコミットメッセージを入力してください: ").strip()
        if custom_message:
            return custom_message
    
    # 自動生成メッセージ
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"fix: Streamlit expander nesting error and UI improvements ({timestamp})"

def check_git_status():
    """Git状態を確認"""
    print("\n📊 現在のGit状態を確認中...")
    
    # 変更があるかチェック
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if not result.stdout.strip():
        print("ℹ️  変更がありません。プッシュのみ実行します。")
        return False
    else:
        print(f"📝 変更されたファイル:")
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
        return True

def main():
    """メイン処理"""
    print("🚀 Git自動プッシュスクリプト")
    print("=" * 50)
    
    # 現在のディレクトリがGitリポジトリかチェック
    if not os.path.exists('.git'):
        print("❌ エラー: 現在のディレクトリはGitリポジトリではありません。")
        sys.exit(1)
    
    # Git状態確認
    has_changes = check_git_status()
    
    if has_changes:
        # 1. git add .
        if not run_command("git add .", "すべての変更をステージング"):
            sys.exit(1)
        
        # 2. コミットメッセージ取得
        commit_message = get_commit_message()
        
        # 3. git commit
        commit_cmd = f'git commit -m "{commit_message}"'
        if not run_command(commit_cmd, "変更をコミット"):
            sys.exit(1)
    
    # 4. git push
    if not run_command("git push origin main", "リモートリポジトリにプッシュ"):
        sys.exit(1)
    
    # 5. 最終状態確認
    print("\n" + "=" * 50)
    run_command("git status", "最終状態確認")
    run_command("git log --oneline -5", "最新のコミット履歴")
    
    print("\n🎉 Git操作が完了しました！")
    print("✅ 変更がリモートリポジトリに正常にプッシュされました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作がキャンセルされました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)
