#!/usr/bin/env python3
"""
プロジェクト内の不要ファイル分析スクリプト
"""

import os
import subprocess
from datetime import datetime

def get_file_info(filepath):
    """ファイルの情報を取得"""
    if not os.path.exists(filepath):
        return None
    
    stat = os.stat(filepath)
    size = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime)
    
    # ファイルの行数を取得
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
    except:
        lines = 0
    
    return {
        'size': size,
        'mtime': mtime,
        'lines': lines
    }

def analyze_files():
    """不要ファイルの分析"""
    print("=== 🔍 プロジェクト内の不要ファイル分析 ===\n")
    
    # 分析対象のパターン
    patterns = [
        'test_*.py',
        '*test*.py', 
        'fix_*.py',
        '*debug*.py',
        'check_*.py',
        '*cleanup*.py',
        '*temp*.py',
        '*backup*.py',
        'delete_*.py',
        'diagnose_*.py',
        'verify_*.py',
        'start_*.py',
        'run_*.py',
        'simple_*.py',
        'quick_*.py',
        'emergency_*.py'
    ]
    
    all_files = []
    
    for pattern in patterns:
        try:
            result = subprocess.run(
                ['find', '.', '-name', pattern, '-type', 'f', '!', '-path', './.venv/*', '!', '-path', './venv/*'],
                capture_output=True, text=True, cwd='.'
            )
            
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            if files:
                print(f"📁 **{pattern}** パターンのファイル:")
                for file in files:
                    info = get_file_info(file)
                    if info:
                        print(f"  - {file}")
                        print(f"    📊 サイズ: {info['size']} bytes, 行数: {info['lines']}, 更新日: {info['mtime'].strftime('%Y-%m-%d %H:%M')}")
                        all_files.append((file, info))
                print()
    
    # 削除推奨ファイルの判定
    print("🗑️  **削除推奨ファイル:**")
    
    definitely_delete = []
    maybe_delete = []
    keep_files = []
    
    for file, info in all_files:
        filename = os.path.basename(file)
        
        # 確実に削除すべきファイル
        if any(pattern in filename for pattern in [
            'temp', 'backup', '_old', '.bak', '.tmp',
            'emergency_', 'force_cleanup', 'delete_phase',
            'quick_test', 'quick_delete'
        ]):
            definitely_delete.append((file, info, "一時的なファイル/テストファイル"))
        
        # 削除を検討すべきファイル
        elif any(pattern in filename for pattern in [
            'fix_', 'check_', 'diagnose_', 'debug_',
            'test_', 'verify_', 'cleanup_'
        ]):
            # 小さいファイルや古いファイルは削除候補
            if info['lines'] < 50 or info['size'] < 2000:
                maybe_delete.append((file, info, "小さなテスト/デバッグファイル"))
            else:
                keep_files.append((file, info, "大きなファイル - 要確認"))
        
        # 起動・実行系ファイル
        elif any(pattern in filename for pattern in [
            'start_', 'run_', 'launch_', 'simple_'
        ]):
            if 'app' in filename or 'main' in filename:
                keep_files.append((file, info, "重要な起動ファイル"))
            else:
                maybe_delete.append((file, info, "代替起動ファイル"))
        
        else:
            keep_files.append((file, info, "詳細確認が必要"))
    
    print(f"🟥 **確実に削除 ({len(definitely_delete)}個):**")
    for file, info, reason in definitely_delete:
        print(f"  ❌ {file} - {reason}")
    
    print(f"\n🟡 **削除検討 ({len(maybe_delete)}個):**")
    for file, info, reason in maybe_delete:
        print(f"  ⚠️  {file} - {reason}")
    
    print(f"\n🟢 **保持推奨 ({len(keep_files)}個):**")
    for file, info, reason in keep_files:
        print(f"  ✅ {file} - {reason}")
    
    return definitely_delete, maybe_delete, keep_files

if __name__ == "__main__":
    analyze_files()
