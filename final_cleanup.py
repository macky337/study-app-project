#!/usr/bin/env python3
"""
最終的なファイル一括削除スクリプト
確実に不要なファイルを削除
"""

import os
import shutil
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path.cwd()

def force_delete_files():
    """不要ファイルを強制削除"""
    
    # 削除対象ファイル（確実に不要）
    files_to_delete = [
        # 古いアプリファイル
        'app_minimal.py', 'app_new.py',
        
        # Git自動化スクリプト
        'auto_git_push.py', 'auto_git_push_fixed.py',
        
        # チェック・検証スクリプト
        'check_db.py', 'check_implementation.py', 'check_model_selection.py',
        'check_problem_9.py', 'check_question_count_feature.py',
        
        # レポートファイル
        'CHOICE_FIX_REPORT.md', 'CLEANUP_REPORT.md', 'complete_solution_report.py',
        'completion_report.py', 'FILE_CLEANUP_STATUS.md', 'final_fix_report.py',
        'final_status_check.py', 'FINAL_TEST_REPORT.md', 'IMPROVEMENT_LOG.md',
        'OPENAI_ENHANCEMENT_REPORT.md', 'PDF_GENERATION_REPORT.md',
        
        # セットアップ・初期化スクリプト
        'create_tables_direct.py', 'init_db.py', 'insert_sample_data.py',
        'setup_and_test.py', 'setup_db.py',
        
        # 削除・クリーンアップスクリプト
        'direct_delete.py', 'force_delete_tests.py', 'force_cleanup.py',
        'immediate_delete.py', 'remove_test_files.py',
        
        # 修正スクリプト
        'fix_choices_auto.py', 'fix_missing_choices.py', 'fix_openai_connection.py',
        'fix_question_143.py', 'fix_question_144_and_model.py', 'fix_question_145.py',
        'fix_unicode_errors.py',
        
        # テストファイル（古い）
        'import_test.py',
        
        # 起動スクリプト（古い）
        'launch_app.py', 'start_app.py', 'start_fixed_app.py',
        'start_app.bat', 'start_app_final.bat', 'start_local.bat',
        
        # クイック系スクリプト
        'quick_push.py', 'quick_push_now.py', 'quick_test.py', 'quick_test_connection.py',
        
        # Railway関連（古い）
        'railway_minimal.py', 'railway_safe_start.py',
        
        # 一時ファイル
        'temp_pdf_tab.py', 'f.read()',
        
        # 出力ファイル
        'debug_output.txt', 'debug_result.txt', 'test_result.txt',
        
        # 不明ファイル
        '=',
    ]
    
    # services内の不要ファイル
    services_files_to_delete = [
        'services/past_question_extractor_fixed.py',
        'services/past_question_extractor_backup.py',
        'services/past_question_extractor.py.bak',
    ]
    
    deleted_files = []
    failed_files = []
    
    print("🗑️ 最終一括削除を実行")
    print("=" * 60)
    
    # ルートディレクトリのファイル削除
    for filename in files_to_delete:
        file_path = PROJECT_ROOT / filename
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    deleted_files.append(filename)
                    print(f"✅ 削除: {filename}")
                else:
                    print(f"⚠️ スキップ (ディレクトリ): {filename}")
            except Exception as e:
                failed_files.append(f"{filename}: {e}")
                print(f"❌ 削除失敗: {filename} - {e}")
    
    # servicesディレクトリ内のファイル削除
    for filepath in services_files_to_delete:
        file_path = PROJECT_ROOT / filepath
        if file_path.exists():
            try:
                file_path.unlink()
                deleted_files.append(filepath)
                print(f"✅ 削除: {filepath}")
            except Exception as e:
                failed_files.append(f"{filepath}: {e}")
                print(f"❌ 削除失敗: {filepath} - {e}")
    
    # __pycache__ディレクトリを削除
    print(f"\n🧹 __pycache__ ディレクトリの削除...")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for dirname in dirs[:]:  # スライスコピーを作成して安全に削除
            if dirname == '__pycache__':
                pycache_path = Path(root) / dirname
                try:
                    shutil.rmtree(pycache_path)
                    print(f"✅ 削除: {pycache_path.relative_to(PROJECT_ROOT)}")
                except Exception as e:
                    print(f"❌ 削除失敗: {pycache_path} - {e}")
    
    print(f"\n📊 削除結果:")
    print(f"   ✅ 削除成功: {len(deleted_files)}個")
    print(f"   ❌ 削除失敗: {len(failed_files)}個")
    
    if failed_files:
        print(f"\n❌ 削除に失敗したファイル:")
        for failed in failed_files:
            print(f"   - {failed}")
    
    return deleted_files, failed_files

def show_remaining_files():
    """残存ファイルを表示"""
    print(f"\n📁 残存ファイル一覧:")
    print("=" * 60)
    
    important_files = []
    test_files = []
    other_files = []
    
    for item in PROJECT_ROOT.iterdir():
        if item.is_file():
            filename = item.name
            if filename.startswith('.'):
                continue
            elif filename in ['app.py', 'requirements.txt', 'Procfile', 'README.md', 'LICENSE']:
                important_files.append(filename)
            elif filename.startswith('test_'):
                test_files.append(filename)
            else:
                other_files.append(filename)
    
    print(f"🚀 重要ファイル ({len(important_files)}個):")
    for filename in sorted(important_files):
        print(f"   ✅ {filename}")
    
    print(f"\n🧪 テストファイル ({len(test_files)}個):")
    for filename in sorted(test_files):
        print(f"   🧪 {filename}")
    
    print(f"\n📄 その他のファイル ({len(other_files)}個):")
    for filename in sorted(other_files):
        print(f"   📄 {filename}")
    
    # ディレクトリ表示
    print(f"\n📁 ディレクトリ:")
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            print(f"   📁 {item.name}/")

if __name__ == "__main__":
    deleted_files, failed_files = force_delete_files()
    show_remaining_files()
    
    print(f"\n🎉 最終整理完了！")
    print(f"削除成功: {len(deleted_files)}個")
    
    if failed_files:
        print(f"⚠️ 手動削除が必要: {len(failed_files)}個")
    
    # 自分自身も削除
    try:
        Path(__file__).unlink()
        print(f"✅ 最終削除: {Path(__file__).name}")
    except:
        print(f"⚠️ 手動削除してください: {Path(__file__).name}")
