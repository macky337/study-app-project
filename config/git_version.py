# -*- coding: utf-8 -*-
"""
Gitコミット履歴からバージョン情報を自動生成
"""
import subprocess
import re
from datetime import datetime
from typing import Tuple, Optional

def get_git_commit_info() -> Tuple[str, str, str]:
    """
    Gitコミット履歴からバージョン情報を取得
    
    Returns:
        Tuple[version, last_updated, commit_hash]
    """
    try:
        # 最新のコミット情報を取得
        result = subprocess.run([
            'git', 'log', '-1', '--pretty=format:%H|%s|%cd', '--date=short'
        ], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
        
        if result.returncode != 0:
            return get_fallback_version()
        
        parts = result.stdout.strip().split('|')
        if len(parts) >= 3:
            commit_hash, message, date = parts[0], parts[1], parts[2]
        else:
            return get_fallback_version()
        
        # バージョン番号を決定
        version = determine_version_from_commits()
        
        return version, date, commit_hash[:8]
        
    except Exception as e:
        print(f"Git情報取得エラー: {e}")
        return get_fallback_version()

def determine_version_from_commits() -> str:
    """
    コミット履歴からバージョン番号を決定
    
    コミットメッセージのプレフィックスに基づいてバージョンを計算:
    - major: BREAKING CHANGE, major:
    - minor: feat:, feature:, minor:
    - patch: fix:, patch:, その他
    """
    try:
        # 全コミット履歴を取得
        result = subprocess.run([
            'git', 'log', '--oneline', '--pretty=format:%s'
        ], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
        
        if result.returncode != 0:
            return "1.0.0"
        
        commits = result.stdout.strip().split('\n')
        
        major, minor, patch = 1, 0, 0
        
        for commit_msg in commits:
            commit_msg = commit_msg.lower()
            
            # Major version triggers
            if any(keyword in commit_msg for keyword in [
                'breaking change', 'major:', 'breaking:'
            ]):
                major += 1
                minor = 0
                patch = 0
            # Minor version triggers
            elif any(keyword in commit_msg for keyword in [
                'feat:', 'feature:', 'minor:', 'add:', 'new:'
            ]):
                minor += 1
                patch = 0
            # Patch version triggers (default)
            else:
                patch += 1
        
        return f"{major}.{minor}.{patch}"
        
    except Exception as e:
        print(f"バージョン計算エラー: {e}")
        return "1.0.0"

def get_fallback_version() -> Tuple[str, str, str]:
    """
    Git情報が取得できない場合のフォールバック
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    return "1.0.0", current_date, "unknown"

def get_commit_count() -> int:
    """
    総コミット数を取得
    """
    try:
        result = subprocess.run([
            'git', 'rev-list', '--count', 'HEAD'
        ], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            return int(result.stdout.strip())
        else:
            return 0
            
    except Exception:
        return 0

def get_repository_info() -> dict:
    """
    リポジトリの詳細情報を取得
    """
    try:
        # ブランチ名取得
        branch_result = subprocess.run([
            'git', 'branch', '--show-current'
        ], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
        
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # リモートURL取得
        remote_result = subprocess.run([
            'git', 'remote', 'get-url', 'origin'
        ], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
        
        remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else "unknown"
        
        return {
            "branch": current_branch,
            "remote_url": remote_url,
            "commit_count": get_commit_count()
        }
        
    except Exception as e:
        print(f"リポジトリ情報取得エラー: {e}")
        return {
            "branch": "unknown",
            "remote_url": "unknown", 
            "commit_count": 0
        }

if __name__ == "__main__":
    # テスト実行
    version, date, hash_short = get_git_commit_info()
    repo_info = get_repository_info()
    
    print(f"Version: {version}")
    print(f"Last Updated: {date}")
    print(f"Commit Hash: {hash_short}")
    print(f"Branch: {repo_info['branch']}")
    print(f"Total Commits: {repo_info['commit_count']}")
