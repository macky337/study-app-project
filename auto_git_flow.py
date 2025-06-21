#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git自動化フロースクリプト
コミット・プッシュを自動化し、プロジェクトの変更を管理します
"""

import os
import subprocess
import sys
import locale
from datetime import datetime
from pathlib import Path

def run_command(command, capture_output=True):
    """コマンドを実行し、結果を返す"""
    try:
        # Windows環境のエンコーディング問題を解決
        import locale
        system_encoding = locale.getpreferredencoding()
        
        # Windows cmd.exeでの日本語対応
        if os.name == 'nt':
            # Windowsの場合、chcp 65001でUTF-8に設定してからコマンド実行
            full_command = f'chcp 65001 >nul 2>&1 && {command}'
        else:
            full_command = command
        
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=capture_output,
            text=True,
            encoding='utf-8' if os.name == 'nt' else system_encoding,
            errors='replace',  # エラー文字は置換
            cwd=Path(__file__).parent
        )
        if capture_output:
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            return result.returncode == 0, stdout, stderr
        else:
            return result.returncode == 0, "", ""
    except UnicodeDecodeError as e:
        # エンコーディングエラーの場合、cp932で再試行
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                encoding='cp932',
                errors='replace',
                cwd=Path(__file__).parent
            )
            if capture_output:
                stdout = result.stdout.strip() if result.stdout else ""
                stderr = result.stderr.strip() if result.stderr else ""
                return result.returncode == 0, stdout, stderr
            else:
                return result.returncode == 0, "", ""
        except Exception as e2:
            return False, "", f"Encoding error: {str(e)} / {str(e2)}"
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """Gitステータスを確認"""
    print("🔍 Gitステータス確認中...")
    
    # Git初期化確認
    success, _, _ = run_command("git status")
    if not success:
        print("❌ Gitリポジトリが初期化されていません")
        return False
    
    # 変更されたファイルを確認
    success, output, _ = run_command("git status --porcelain")
    if success:
        if output:
            print("📝 変更されたファイル:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
            return True
        else:
            print("✅ 変更されたファイルはありません")
            return False
    else:
        print("❌ Gitステータスの確認に失敗しました")
        return False

def add_files():
    """ファイルをステージング"""
    print("📦 ファイルをステージング中...")
    
    # 全ファイルを追加
    success, output, error = run_command("git add .")
    if success:
        print("✅ ファイルをステージングしました")
        return True
    else:
        print(f"❌ ステージングに失敗: {error}")
        return False

def create_commit_message():
    """コミットメッセージを生成"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 変更の種類を検出
    success, output, _ = run_command("git diff --cached --name-only")
    if success and output:
        files = output.split('\n')
        
        # ファイルの種類を分析
        py_files = [f for f in files if f.endswith('.py')]
        config_files = [f for f in files if f.endswith(('.txt', '.md', '.yml', '.yaml', '.json', '.env'))]
        
        if py_files and config_files:
            commit_type = "feat+config"
            description = "コード機能追加・設定更新"
        elif py_files:
            commit_type = "feat"
            description = "機能追加・改善"
        elif config_files:
            commit_type = "config"
            description = "設定・ドキュメント更新"
        else:
            commit_type = "update"
            description = "プロジェクト更新"
    else:
        commit_type = "update"
        description = "プロジェクト更新"
    
    return f"{commit_type}: {description} ({timestamp})"

def commit_changes():
    """変更をコミット"""
    print("💾 変更をコミット中...")
    
    message = create_commit_message()
    print(f"   コミットメッセージ: {message}")
    
    success, output, error = run_command(f'git commit -m "{message}"')
    if success:
        print("✅ コミットが完了しました")
        return True
    else:
        print(f"❌ コミットに失敗: {error}")
        return False

def push_changes():
    """変更をプッシュ"""
    print("🚀 リモートリポジトリにプッシュ中...")
    
    # リモートブランチを確認
    success, output, _ = run_command("git branch -r")
    if success and "origin/" in output:
        # 現在のブランチを取得
        success, branch, _ = run_command("git branch --show-current")
        if success and branch:
            success, output, error = run_command(f"git push origin {branch}")
            if success:
                print("✅ プッシュが完了しました")
                return True
            else:
                print(f"❌ プッシュに失敗: {error}")
                # 初回プッシュの場合
                if "upstream" in error:
                    print("🔄 上流ブランチを設定してプッシュ中...")
                    success, _, error = run_command(f"git push -u origin {branch}")
                    if success:
                        print("✅ 上流ブランチ設定付きプッシュが完了しました")
                        return True
                    else:
                        print(f"❌ 上流ブランチ設定付きプッシュに失敗: {error}")
                return False
        else:
            print("❌ 現在のブランチを取得できませんでした")
            return False
    else:
        print("⚠️ リモートリポジトリが設定されていません")
        print("💡 リモートリポジトリを追加するには:")
        print("   git remote add origin <リポジトリURL>")
        return False

def show_final_status():
    """最終状況を表示"""
    print("\n" + "="*50)
    print("📊 最終Git状況:")
    
    # 最新のコミット情報
    success, output, _ = run_command("git log -1 --oneline")
    if success:
        print(f"   最新コミット: {output}")
    
    # リモート同期状況
    success, output, _ = run_command("git status -b --porcelain")
    if success:
        lines = output.split('\n')
        for line in lines:
            if line.startswith('##'):
                print(f"   ブランチ状況: {line[2:].strip()}")
                break
    
    print("="*50)

def main():
    """メイン実行フロー"""
    print("🤖 Git自動化フロー開始")
    print("="*50)
    
    # 1. Git状況確認
    if not check_git_status():
        print("\n❌ 処理を中断します")
        return False
    
    # 2. ファイルステージング
    if not add_files():
        return False
    
    # 3. コミット実行
    if not commit_changes():
        return False
    
    # 4. プッシュ実行
    if not push_changes():
        print("⚠️ プッシュに失敗しましたが、ローカルコミットは完了しています")
    
    # 5. 最終状況表示
    show_final_status()
    
    print("\n🎉 Git自動化フローが完了しました！")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)
