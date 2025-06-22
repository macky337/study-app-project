#!/usr/bin/env python3
"""
削除機能の簡単なテスト
"""

import sqlite3
import os

def test_delete_functionality():
    """削除機能のテスト"""
    print("=== 削除機能テスト開始 ===")
    
    db_path = "study_app.db"
    
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return False
    
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 問題数をカウント
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_count = cursor.fetchone()[0]
        print(f"📊 総問題数: {total_count}")
        
        # カテゴリー別問題数
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM questions 
            GROUP BY category 
            ORDER BY category
        """)
        categories = cursor.fetchall()
        
        print("\n📈 カテゴリー別問題数:")
        for category, count in categories:
            print(f"  - {category}: {count}問")
        
        # 最新の5問を表示
        cursor.execute("""
            SELECT id, title, category, difficulty 
            FROM questions 
            ORDER BY id DESC 
            LIMIT 5
        """)
        recent_questions = cursor.fetchall()
        
        print("\n📝 最新の5問:")
        for q_id, title, category, difficulty in recent_questions:
            print(f"  ID {q_id}: {title[:30]}... ({category}, {difficulty})")
        
        conn.close()
        print("\n✅ データベースの状態確認が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    test_delete_functionality()
