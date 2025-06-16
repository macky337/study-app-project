#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題143の選択肢確認と修正
"""

import os
import sys
import sqlite3
from datetime import datetime

def check_question_143():
    """問題143の詳細確認"""
    
    print("🔍 問題143の詳細確認")
    print("=" * 50)
    
    db_path = "study_app.db"
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 問題143の詳細確認
        cursor.execute("""
            SELECT id, title, question_text, category, explanation, created_at
            FROM questions 
            WHERE id = 143
        """)
        
        question = cursor.fetchone()
        if question:
            q_id, title, content, category, explanation, created_at = question
            print(f"✅ 問題 {q_id}: {title}")
            print(f"   カテゴリ: {category}")
            print(f"   問題文: {content}")
            print(f"   解説: {explanation}")
            print(f"   作成日時: {created_at}")
            
            # 選択肢確認
            cursor.execute("""
                SELECT id, choice_text, is_correct, order_num
                FROM choices 
                WHERE question_id = ?
                ORDER BY order_num
            """, (143,))
            
            choices = cursor.fetchall()
            if choices:
                print(f"\n✅ 選択肢（{len(choices)}個）:")
                for choice in choices:
                    choice_id, choice_text, is_correct, order_num = choice
                    status = "✅ 正解" if is_correct else "   "
                    print(f"   {status} {order_num}. {choice_text}")
            else:
                print("\n❌ 選択肢がありません")
                
                # 選択肢を追加
                print("\n🔧 選択肢を追加します...")
                choices_to_add = [
                    {"content": "IPアドレス", "is_correct": True},
                    {"content": "MACアドレス", "is_correct": False},
                    {"content": "ホスト名", "is_correct": False},
                    {"content": "ポート番号", "is_correct": False}
                ]
                
                for i, choice in enumerate(choices_to_add, 1):
                    cursor.execute("""
                        INSERT INTO choices (question_id, choice_text, is_correct, order_num, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        143,
                        choice["content"],
                        choice["is_correct"],
                        i,
                        datetime.now().isoformat()
                    ))
                    
                    status = "✅ 正解" if choice["is_correct"] else "   "
                    print(f"   {status} {i}. {choice['content']}")
                
                conn.commit()
                print("✅ 選択肢を追加しました")
        else:
            print("❌ 問題143が見つかりません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def check_recent_questions():
    """最近の問題の選択肢状況確認"""
    
    print(f"\n📊 最近の問題の選択肢状況")
    print("=" * 50)
    
    db_path = "study_app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 最新10問の選択肢状況
        cursor.execute("""
            SELECT q.id, q.title, COUNT(c.id) as choice_count
            FROM questions q
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
            ORDER BY q.id DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            q_id, title, choice_count = row
            status = "✅" if choice_count > 0 else "❌"
            print(f"   {status} Q{q_id}: {title[:50]}... ({choice_count} 選択肢)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    print("🚨 問題143の選択肢修正")
    print("=" * 60)
    
    # 問題143の確認と修正
    check_question_143()
    
    # 最近の問題確認
    check_recent_questions()
    
    print(f"\n💡 次のステップ:")
    print("1. Streamlitアプリでクイズを実行")
    print("2. 問題143が選択肢付きで表示されることを確認")

if __name__ == "__main__":
    main()
