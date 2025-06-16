#!/usr/bin/env python3
"""
強制ファイル削除スクリプト
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# 削除対象ファイルリスト
files_to_delete = [
    'app_minimal.py', 'app_new.py', 'auto_git_push.py', 'auto_git_push_fixed.py',
    'check_db.py', 'check_implementation.py', 'check_model_selection.py', 'check_problem_9.py',
    'check_question_count_feature.py', 'cleanup_files.py', 'cleanup_project_files.py',
    'complete_solution_report.py', 'completion_report.py', 'create_tables_direct.py',
    'debug_enhancement_report.py', 'debug_extraction.py', 'debug_openai.py',
    'debug_simple_extraction.py', 'delete_files.py', 'delete_phase1.py',
    'delete_phase2.py', 'delete_phase3.py', 'delete_test_files.py',
    'diagnose_502_error.py', 'diagnose_choice_issue.py', 'diagnose_db.py',
    'diagnose_openai_connection.py', 'diagnose_questions.py', 'direct_delete.py',
    'emergency_test.py', 'f.read()', 'fix_choices_auto.py', 'fix_missing_choices.py',
    'fix_openai_connection.py', 'fix_question_143.py', 'fix_question_144_and_model.py',
    'fix_question_145.py', 'fix_unicode_errors.py', 'force_delete_tests.py',
    'immediate_delete.py', 'import_test.py', 'init_db.py', 'insert_sample_data.py',
    'launch_app.py', 'quick_push.py', 'quick_push_now.py', 'quick_test.py',
    'quick_test_connection.py', 'railway_minimal.py', 'railway_safe_start.py',
    'remove_test_files.py', 'setup_and_test.py', 'setup_db.py', 'start_app.bat',
    'start_app.py', 'start_app_final.bat', 'start_fixed_app.py', 'start_local.bat',
    'temp_pdf_tab.py', 'test_db.py', 'test_direct.py', 'test_extraction_fixed.py',
    'test_extraction_fixes.py', 'test_extraction_simple.py', 'test_improved_features.py',
    'test_integration_final.py', 'test_local.py', 'test_minimal.py',
    'test_past_question_extraction.py', 'test_status.py', 'verify_privacy.py',
    'debug_output.txt', 'debug_result.txt', 'test_result.txt',
    'CHOICE_FIX_REPORT.md', 'CLEANUP_REPORT.md', 'FILE_CLEANUP_STATUS.md',
    'final_fix_report.py', 'final_status_check.py', 'FINAL_TEST_REPORT.md',
    'IMPROVEMENT_LOG.md', 'improvement_summary.py', 'OPENAI_ENHANCEMENT_REPORT.md',
    'PDF_GENERATION_REPORT.md'
]

deleted_count = 0
not_found_count = 0

print("🗑️ 強制ファイル削除実行")
print("=" * 50)

for filename in files_to_delete:
    file_path = PROJECT_ROOT / filename
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"✅ 削除: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ 削除失敗: {filename} - {e}")
    else:
        not_found_count += 1

print(f"\n📊 削除結果:")
print(f"   ✅ 削除成功: {deleted_count}個")
print(f"   📄 見つからず: {not_found_count}個")

# 自分自身も削除
try:
    os.unlink(__file__)
    print(f"✅ 削除: {Path(__file__).name}")
except:
    pass
