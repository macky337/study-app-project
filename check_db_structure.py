#!/usr/bin/env python3
"""
データベース構造の確認
"""

import sqlite3
import os

def check_database_structure():
    """データベース構造の確認"""
    print("=== データベース構造チェック ===")
    
    db_path = "study_app.db"
    
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return False
    
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 データベース内のテーブル: {len(tables)}個")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 各テーブルのスキーマを確認
        for table in tables:
            table_name = table[0]
            print(f"\n📄 テーブル '{table_name}' のスキーマ:")
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # レコード数を確認
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  📊 レコード数: {count}")
        
        conn.close()
        print("\n✅ データベース構造の確認が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    check_database_structure()
