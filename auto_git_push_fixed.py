#!/usr/bin/env python3
"""
Git自動プッシュスクリプト（修正版）
変更をステージング→コミット→プッシュまで自動実行
文字エンコーディング問題を修正
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
        # Windows環境でのエンコーディング問題を解決
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',  # デコードエラーを無視して置換
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.stdout:
            # 出力をクリーンアップ
            clean_output = result.stdout.replace('\x00', '').strip()
            if clean_output:
                print(clean_output)
        
        if result.stderr:
            clean_error = result.stderr.replace('\x00', '').strip()
            if clean_error:
                print(f"警告/エラー: {clean_error}")
            
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
    print("1. 自動生成 (fix: UI/UX改善とバグ修正)")
    print("2. カスタムメッセージを入力")
    
    try:
        choice = input("\n選択 (1-2): ").strip()
        
        if choice == "1":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            return f"fix: UI/UX改善とバグ修正 - {timestamp}"
        elif choice == "2":
            message = input("コミットメッセージを入力: ").strip()
            if not message:
                print("❌ 空のメッセージは使用できません")
                return get_commit_message()
            return message
        else:
            print("❌ 無効な選択です")
            return get_commit_message()
    except KeyboardInterrupt:
        print("\n\n❌ 操作がキャンセルされました")
        sys.exit(1)

def main():
    """メイン処理"""
    print("🚀 Git自動プッシュスクリプト")
    print("=" * 50)
    
    # Git状態確認
    if not run_command("git status", "Git状態確認"):
        return
    
    # 変更ファイル確認
    print("\n📁 変更されたファイル:")
    run_command("git diff --name-only", "変更ファイル確認")
    run_command("git diff --cached --name-only", "ステージ済みファイル確認")
    
    # 実行確認
    try:
        confirm = input("\n🤔 変更をコミット・プッシュしますか? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 操作がキャンセルされました")
            return
    except KeyboardInterrupt:
        print("\n\n❌ 操作がキャンセルされました")
        return
    
    # コミットメッセージ取得
    commit_message = get_commit_message()
    print(f"\n📝 使用するメッセージ: {commit_message}")
    
    # Git操作実行
    steps = [
        ("git add .", "すべての変更をステージング"),
        (f'git commit -m "{commit_message}"', "コミット作成"),
        ("git push origin main", "リモートにプッシュ")
    ]
    
    for command, description in steps:
        if not run_command(command, description):
            print(f"\n❌ {description}に失敗しました。処理を中断します。")
            return
    
    # 最終状態確認
    run_command("git status", "最終状態確認")
    print("\n🔄 最新のコミット履歴")
    print("実行: git log --oneline -5")
    print("-" * 50)
    
    # git log は特別にエンコーディング問題を回避
    try:
        result = subprocess.run(
            "git log --oneline -5", 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.stdout:
            # 特殊文字をクリーンアップ
            clean_log = result.stdout.replace('\x85', '...').replace('\x00', '')
            print(clean_log)
        print("✅ 成功")
    except Exception as e:
        print(f"コミット履歴の表示で軽微なエラー: {e}")
        print("✅ 成功")
    
    print("\n🎉 Git操作が完了しました！")
    print("✅ 変更がリモートリポジトリに正常にプッシュされました。")

if __name__ == "__main__":
    main()
