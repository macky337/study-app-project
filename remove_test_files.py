#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_*ファイルの物理削除
"""

import os
import glob

def delete_test_files():
    """test_*ファイルを物理削除"""
    
    print("🗑️ test_*ファイルの物理削除を実行します...")
    print("=" * 50)
    
    # test_で始まるPythonファイルを検索
    test_files = glob.glob("test_*.py")
    
    if not test_files:
        print("📁 test_*ファイルは見つかりませんでした")
        return
    
    print(f"🔍 {len(test_files)}個のtest_ファイルを発見:")
    for file in test_files:
        print(f"   - {file}")
    
    print("\n🗑️ ファイル削除を開始...")
    deleted_count = 0
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"✅ 削除成功: {file}")
                deleted_count += 1
            else:
                print(f"⚠️ ファイルが存在しません: {file}")
        except PermissionError:
            print(f"❌ 権限エラー: {file} (ファイルが使用中の可能性)")
        except Exception as e:
            print(f"❌ 削除失敗: {file} - {e}")
    
    print(f"\n📊 削除結果: {deleted_count}/{len(test_files)}個のファイルを削除")
    
    # 削除後の確認
    remaining_files = glob.glob("test_*.py")
    if remaining_files:
        print(f"⚠️ {len(remaining_files)}個のファイルが残っています:")
        for file in remaining_files:
            print(f"   - {file}")
    else:
        print("✅ すべてのtest_*ファイルが削除されました")

if __name__ == "__main__":
    delete_test_files()
