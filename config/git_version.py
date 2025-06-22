# -*- coding: utf-8 -*-
"""
Gitコミット履歴からバージョン情報を自動生成
"""
import subprocess
import os
import re
from datetime import datetime
from typing import Tuple, Optional

# プロジェクトルートを設定 (config/git_version.py の親フォルダ)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_git_commit_info() -> Tuple[str, str, str]:
    """
    Gitコミット履歴からバージョン情報を取得
    
    Returns:
        Tuple[version, last_updated, commit_hash]
    """
    # 本番環境チェック（.gitフォルダが存在しない、またはgitコマンドが使用できない場合）
    git_dir = os.path.join(PROJECT_ROOT, '.git')
    if not os.path.exists(git_dir):
        return get_production_fallback_version()
    
    try:
        # Gitコマンドの存在確認
        git_check = subprocess.run(
            ['git', '--version'],
            capture_output=True, text=True, timeout=3, cwd=PROJECT_ROOT
        )
        if git_check.returncode != 0:
            return get_production_fallback_version()
        
        # コミットハッシュ取得
        res_hash = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5, cwd=PROJECT_ROOT
        )
        commit_hash = res_hash.stdout.strip() if res_hash.returncode == 0 else 'unknown'
        
        # 最新コミット日付取得
        res_date = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=short'],
            capture_output=True, text=True, timeout=5, cwd=PROJECT_ROOT
        )
        date = res_date.stdout.strip() if res_date.returncode == 0 else datetime.now().strftime('%Y-%m-%d')
        
        # バージョン番号を決定
        version = determine_version_from_commits()
        return version, date, commit_hash
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
        return get_production_fallback_version()
    except Exception as e:
        return get_production_fallback_version()

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
        result = subprocess.run(
            ['git', 'log', '--oneline', '--pretty=format:%s'],
            capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore', cwd=PROJECT_ROOT
        )
        
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

def get_production_fallback_version() -> Tuple[str, str, str]:
    """
    本番環境用のフォールバック（環境変数やビルド情報を使用）
    """
    import os
    import json
    
    # まず version.json ファイルからの読み取りを試行
    version_file = os.path.join(PROJECT_ROOT, 'version.json')
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                return (
                    version_data.get('version', '1.0.0'),
                    version_data.get('build_date', datetime.now().strftime("%Y-%m-%d")),
                    version_data.get('commit_hash', 'prod')
                )
        except (json.JSONDecodeError, KeyError, IOError):
            pass
    
    # 環境変数からバージョン情報を取得（Railway, Heroku等で設定可能）
    version = os.environ.get('APP_VERSION', '1.0.0')
    commit_hash = os.environ.get('RAILWAY_GIT_COMMIT_SHA', os.environ.get('HEROKU_SLUG_COMMIT', 'prod'))[:7]
    deploy_date = os.environ.get('DEPLOY_DATE', datetime.now().strftime("%Y-%m-%d"))
    
    return version, deploy_date, commit_hash

def get_production_repo_info() -> dict:
    """
    本番環境用のリポジトリ情報
    """
    import os
    import json
    
    # まず version.json ファイルからの読み取りを試行
    version_file = os.path.join(PROJECT_ROOT, 'version.json')
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                return {
                    "branch": version_data.get('branch', 'main'),
                    "remote_url": version_data.get('repository_url', 'https://github.com/macky337/study-app-project.git'),
                    "commit_count": version_data.get('commit_count', 0)
                }
        except (json.JSONDecodeError, KeyError, IOError):
            pass
    
    # 環境変数からブランチ情報を取得
    branch = os.environ.get('RAILWAY_GIT_BRANCH', os.environ.get('HEROKU_BRANCH', 'main'))
    remote_url = os.environ.get('REPOSITORY_URL', 'https://github.com/macky337/study-app-project.git')
    
    return {
        "branch": branch,
        "remote_url": remote_url,
        "commit_count": 0  # 本番環境では取得困難
    }

def get_commit_count() -> int:
    """
    総コミット数を取得
    """
    # 本番環境チェック
    git_dir = os.path.join(PROJECT_ROOT, '.git')
    if not os.path.exists(git_dir):
        return 0
        
    try:
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore', cwd=PROJECT_ROOT
        )
        
        if result.returncode == 0:
            return int(result.stdout.strip())
        else:
            return 0
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError, ValueError):
        return 0
    except Exception:
        return 0

def get_repository_info() -> dict:
    """
    リポジトリの詳細情報を取得
    """
    # 本番環境チェック
    git_dir = os.path.join(PROJECT_ROOT, '.git')
    if not os.path.exists(git_dir):
        return get_production_repo_info()
        
    try:
        # Gitコマンドの存在確認
        git_check = subprocess.run(
            ['git', '--version'],
            capture_output=True, text=True, timeout=3, cwd=PROJECT_ROOT
        )
        if git_check.returncode != 0:
            return get_production_repo_info()
            
        # ブランチ名取得
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore', cwd=PROJECT_ROOT
        )
        
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        # リモートURL取得
        remote_result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore', cwd=PROJECT_ROOT
        )
        
        remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else "unknown"
        
        commit_count = get_commit_count()
        
        return {
            "branch": current_branch,
            "remote_url": remote_url,
            "commit_count": commit_count
        }
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
        return get_production_repo_info()
    except Exception as e:
        return get_production_repo_info()

if __name__ == "__main__":
    # テスト実行
    version, date, hash_short = get_git_commit_info()
    repo_info = get_repository_info()
    
    print(f"Version: {version}")
    print(f"Last Updated: {date}")
    print(f"Commit Hash: {hash_short}")
    print(f"Branch: {repo_info['branch']}")
    print(f"Total Commits: {repo_info['commit_count']}")
