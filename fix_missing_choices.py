#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
選択肢がない問題に選択肢を追加するスクリプト
"""

import os
import sys
import sqlite3
from datetime import datetime

def add_choices_to_questions():
    """選択肢がない問題に選択肢を追加"""
    
    print("🔧 選択肢追加スクリプト")
    print("=" * 50)
    
    db_path = "study_app.db"
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 選択肢がない問題を特定（特に最新の問題140, 141）
        target_questions = [
            {
                "id": 140,
                "choices": [
                    {"content": "MACアドレス", "is_correct": False},
                    {"content": "IPアドレス", "is_correct": True},
                    {"content": "ポート番号", "is_correct": False},
                    {"content": "ホスト名", "is_correct": False}
                ]
            },
            {
                "id": 141,
                "choices": [
                    {"content": "JavaScript Object Notation", "is_correct": True},
                    {"content": "Java Standard Object Network", "is_correct": False},
                    {"content": "JavaScript Online Navigation", "is_correct": False},
                    {"content": "Java Serialized Object Node", "is_correct": False}
                ]
            }
        ]
        
        for question_data in target_questions:
            question_id = question_data["id"]
            
            # 問題が存在するか確認
            cursor.execute("SELECT title FROM questions WHERE id = ?", (question_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"⚠️ 問題 {question_id} が見つかりません")
                continue
                
            title = result[0]
            print(f"\n📝 問題 {question_id}: {title}")
            
            # 既存の選択肢を削除
            cursor.execute("DELETE FROM choices WHERE question_id = ?", (question_id,))
            print(f"   🗑️ 既存選択肢を削除")
            
            # 新しい選択肢を追加
            for i, choice in enumerate(question_data["choices"], 1):
                cursor.execute("""
                    INSERT INTO choices (question_id, choice_text, is_correct, order_num, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    question_id,
                    choice["content"],
                    choice["is_correct"],
                    i,
                    datetime.now().isoformat()
                ))
                
                status = "✅ 正解" if choice["is_correct"] else "   "
                print(f"   {status} {i}. {choice['content']}")
        
        # 変更をコミット
        conn.commit()
        print(f"\n✅ 選択肢の追加が完了しました")
        
        # 結果確認
        print(f"\n📊 結果確認:")
        for question_data in target_questions:
            question_id = question_data["id"]
            cursor.execute("""
                SELECT COUNT(*) FROM choices WHERE question_id = ?
            """, (question_id,))
            
            choice_count = cursor.fetchone()[0]
            print(f"   問題 {question_id}: {choice_count} 個の選択肢")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def verify_all_questions():
    """全問題の選択肢状況を確認"""
    
    print(f"\n🔍 全問題の選択肢確認")
    print("=" * 50)
    
    db_path = "study_app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 選択肢なし問題の確認
        cursor.execute("""
            SELECT q.id, q.title, COUNT(c.id) as choice_count
            FROM questions q
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
            HAVING choice_count = 0
            ORDER BY q.id DESC
            LIMIT 5
        """)
        
        no_choices = cursor.fetchall()
        if no_choices:
            print("❌ 選択肢なし問題:")
            for row in no_choices:
                q_id, title, count = row
                print(f"   Q{q_id}: {title}")
        else:
            print("✅ 選択肢なし問題はありません")
        
        # 最新問題の確認
        print(f"\n📋 最新問題（ID: 140, 141）:")
        for q_id in [140, 141]:
            cursor.execute("""
                SELECT q.title, COUNT(c.id) as choice_count
                FROM questions q
                LEFT JOIN choices c ON q.id = c.question_id
                WHERE q.id = ?
                GROUP BY q.id
            """, (q_id,))
            
            result = cursor.fetchone()
            if result:
                title, choice_count = result
                status = "✅" if choice_count > 0 else "❌"
                print(f"   {status} Q{q_id}: {title} ({choice_count} 選択肢)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    print("🚨 選択肢修正スクリプト")
    print("=" * 60)
    
    # 選択肢を追加
    add_choices_to_questions()
    
    # 結果確認
    verify_all_questions()
    
    print(f"\n🎯 完了!")
    print("💡 Streamlitアプリでクイズを試してみてください")

if __name__ == "__main__":
    main()
