#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プロジェクトの最終クリーンアップスクリプト
内容検証・重複チェック機能の実装完了後の不要ファイル削除
"""

import os
import shutil
from pathlib import Path

# プロジェクトルート
project_root = Path(__file__).parent

def get_final_cleanup_files():
    """最終クリーンアップ対象のファイルリスト"""
    return [
        # 不要なアプリファイル
        "app_minimal.py",
        "app_new.py",
        
        # デバッグファイル
        "debug_extraction.py",
        "debug_openai.py",
        "debug_simple_extraction.py",
        "debug_output.txt",
        "debug_result.txt",
        "debug_enhancement_report.py",
        
        # 修正用ファイル
        "fix_choices_auto.py",
        "fix_missing_choices.py",
        "fix_openai_connection.py",
        "fix_question_143.py",
        "fix_question_144_and_model.py",
        "fix_question_145.py",
        "fix_unicode_errors.py",
        
        # 診断ファイル
        "diagnose_502_error.py",
        "diagnose_choice_issue.py",
        "diagnose_db.py",
        "diagnose_openai_connection.py",
        "diagnose_questions.py",
        
        # 確認ファイル
        "check_db.py",
        "check_implementation.py",
        "check_model_selection.py",
        "check_problem_9.py",
        "check_question_count_feature.py",
        
        # 一時ファイル
        "temp_pdf_tab.py",
        "emergency_test.py",
        "import_test.py",
        "launch_app.py",
        
        # テストファイル群
        "test_category_selection.py",
        "test_db.py",
        "test_delete_question.py",
        "test_direct.py",
        "test_duplicate_detection.py",
        "test_enhanced_service.py",
        "test_extraction_fixed.py",
        "test_extraction_fixes.py",
        "test_extraction_simple.py",
        "test_final_features.py",
        "test_improved_features.py",
        "test_integration_final.py",
        "test_local.py",
        "test_minimal.py",
        "test_past_question_extraction.py",
        "test_pdf_services.py",
        "test_question_management.py",
        "test_result.txt",
        "test_status.py",
        
        # 削除・クリーンアップ用ファイル
        "delete_files.py",
        "delete_phase1.py",
        "delete_phase2.py",
        "delete_phase3.py",
        "delete_test_files.py",
        "direct_delete.py",
        "force_delete_tests.py",
        "immediate_delete.py",
        "remove_test_files.py",
        "cleanup_files.py",
        "cleanup_project_files.py",
        "final_cleanup.py",
        "force_cleanup.py",
        
        # 自動化スクリプト
        "auto_git_push.py",
        "auto_git_push_fixed.py",
        "quick_push.py",
        "quick_push_now.py",
        "quick_test.py",
        "quick_test_connection.py",
        
        # 起動スクリプト（重複）
        "start_fixed_app.py",
        "start_railway.py",
        "start_with_check.py",
        "railway_debug.py",
        "railway_minimal.py",
        "railway_safe_start.py",
        
        # 設定・初期化スクリプト
        "create_tables_direct.py",
        "init_db.py",
        "insert_sample_data.py",
        "setup_and_test.py",
        "setup_db.py",
        
        # レポート・サマリーファイル
        "complete_solution_report.py",
        "completion_report.py",
        "final_fix_report.py",
        "final_status_check.py",
        "improvement_summary.py",
        
        # 検証スクリプト
        "verify_privacy.py",
        
        # ファイル処理用
        "f.read()",
        "=",
        
        # 今回作成したテストファイル
        "test_openai_connection.py",
        "quick_openai_test.py",
        "test_openai.bat",
        "start_app_debug.bat"
    ]

def final_cleanup():
    """最終クリーンアップ実行"""
    print("🧹 最終プロジェクトクリーンアップ開始")
    print("=" * 50)
    
    files_to_delete = get_final_cleanup_files()
    
    deleted_count = 0
    failed_count = 0
    
    for file_name in files_to_delete:
        file_path = project_root / file_name
        
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"✅ 削除: {file_name}")
                    deleted_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    print(f"✅ 削除（ディレクトリ）: {file_name}")
                    deleted_count += 1
            except Exception as e:
                print(f"❌ 削除失敗: {file_name} - {e}")
                failed_count += 1
        else:
            print(f"⚪ スキップ（存在しない）: {file_name}")
    
    print("\n" + "=" * 50)
    print("📊 最終クリーンアップ結果:")
    print(f"   削除成功: {deleted_count} ファイル")
    print(f"   削除失敗: {failed_count} ファイル")
    print(f"   対象ファイル: {len(files_to_delete)} ファイル")
    
    if failed_count == 0:
        print("\n🎉 すべてのファイルが正常に削除されました！")
    else:
        print(f"\n⚠️ {failed_count} ファイルの削除に失敗しました")
    
    # 残りのファイルを確認
    print("\n📋 残存する主要ファイル:")
    important_files = [
        "app.py",
        "requirements.txt",
        "README.md",
        "LICENSE",
        ".env",
        ".gitignore",
        "Procfile",
        "start.sh",
        "start_app.bat",
        "start_app.py",
        "start_local.bat",
        "start_app_final.bat"
    ]
    
    for file_name in important_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} (存在しない)")
    
    print("\n📁 ディレクトリ構造:")
    print(f"   ✅ database/")
    print(f"   ✅ models/")
    print(f"   ✅ services/")
    print(f"   ✅ utils/")
    print(f"   ✅ pages/ (使用されていない可能性)")

if __name__ == "__main__":
    # 確認プロンプト
    print("⚠️  注意: このスクリプトは多数のファイルを削除します。")
    print("🔍 削除対象: テスト、デバッグ、修正用、一時ファイルなど")
    print("✅ 保持対象: app.py, database/, models/, services/, utils/, 設定ファイル")
    
    response = input("\n続行しますか？ (y/N): ")
    if response.lower() == 'y':
        final_cleanup()
    else:
        print("❌ クリーンアップをキャンセルしました")
