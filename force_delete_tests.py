#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_*ファイルの物理削除スクリプト
"""

import os
import sys

def force_delete_test_files():
    """test_*ファイルを強制削除"""
    
    print("🗑️ test_*ファイルの物理削除を実行します")
    print("=" * 50)
    
    # 削除対象のtest_*ファイルリスト
    test_files = [
        "test_extraction.py",
        "test_fallback.py", 
        "test_fix.py",
        "test_imports.py",
        "test_improved_extraction.py",
        "test_openai.py",
        "test_openai_simple.py",
        "test_pdf_full.py",
        "test_pdf_function.py", 
        "test_pdf_processor.py",
        "test_privacy.py",
        "test_streamlit.py",
        "test_streamlit_startup.py"
    ]
    
    deleted_count = 0
    not_found_count = 0
    error_count = 0
    
    for filename in test_files:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ 削除成功: {filename}")
                deleted_count += 1
            except PermissionError:
                print(f"❌ 権限エラー: {filename}")
                error_count += 1
            except Exception as e:
                print(f"❌ 削除エラー: {filename} - {e}")
                error_count += 1
        else:
            print(f"⚠️ ファイル未発見: {filename}")
            not_found_count += 1
    
    print(f"\n📊 削除結果:")
    print(f"   ✅ 削除成功: {deleted_count}ファイル")
    print(f"   ⚠️ 未発見: {not_found_count}ファイル")
    print(f"   ❌ エラー: {error_count}ファイル")
    
    # 削除後の確認
    remaining_test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
    if remaining_test_files:
        print(f"\n⚠️ 残存test_*ファイル:")
        for f in remaining_test_files:
            print(f"   - {f}")
    else:
        print(f"\n🎉 すべてのtest_*ファイルが削除されました！")
    
    return deleted_count

if __name__ == "__main__":
    force_delete_test_files()
