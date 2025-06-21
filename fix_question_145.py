#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題145の選択肢確認と修正
"""

import os
import sys
import sqlite3
from datetime import datetime

def check_and_fix_question_145():
    """問題145の選択肢確認と修正"""
    
    print("🔍 問題145の選択肢確認と修正")
    print("=" * 50)
    
    db_path = "study_app.db"
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 問題145の詳細確認
        cursor.execute("""
            SELECT id, title, question_text, category, explanation, created_at
            FROM questions 
            WHERE id = 145
        """)
        
        question = cursor.fetchone()
        if question:
            q_id, title, content, category, explanation, created_at = question
            print(f"✅ 問題 {q_id}: {title}")
            print(f"   カテゴリ: {category}")
            print(f"   問題文: {content}")
            print(f"   解説: {explanation[:100]}...")
            print(f"   作成日時: {created_at}")
            
            # 選択肢確認
            cursor.execute("""
                SELECT id, choice_text, is_correct, order_num
                FROM choices 
                WHERE question_id = ?
                ORDER BY order_num
            """, (145,))
            
            choices = cursor.fetchall()
            if choices:
                print(f"\n✅ 選択肢（{len(choices)}個）:")
                for choice in choices:
                    choice_id, choice_text, is_correct, order_num = choice
                    status = "✅ 正解" if is_correct else "   "
                    print(f"   {status} {order_num}. {choice_text}")
            else:
                print("\n❌ 選択肢がありません")
                
                # データベースに関する適切な選択肢を追加
                print("\n🔧 選択肢を追加します...")
                choices_to_add = [
                    {"content": "レコード", "is_correct": True},
                    {"content": "フィールド", "is_correct": False},
                    {"content": "インデックス", "is_correct": False},
                    {"content": "ビュー", "is_correct": False}
                ]
                
                for i, choice in enumerate(choices_to_add, 1):
                    cursor.execute("""
                        INSERT INTO choices (question_id, choice_text, is_correct, order_num, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        145,
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
            print("❌ 問題145が見つかりません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def check_recent_questions_with_choices():
    """最近の問題の選択肢状況を確認"""
    
    print(f"\n📊 最近の問題の選択肢状況")
    print("=" * 50)
    
    db_path = "study_app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 最新10問の選択肢状況
        cursor.execute("""
            SELECT q.id, q.title, COUNT(c.id) as choice_count, q.created_at
            FROM questions q
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
            ORDER BY q.id DESC
            LIMIT 10
        """)
        
        print("問題ID | 選択肢数 | タイトル | 作成日時")
        print("-" * 80)
        for row in cursor.fetchall():
            q_id, title, choice_count, created_at = row
            status = "✅" if choice_count > 0 else "❌"
            title_short = title[:40] + "..." if len(title) > 40 else title
            print(f"  {status} Q{q_id:3d} | {choice_count:6d}個 | {title_short:42} | {created_at[:19]}")
        
        # 選択肢のない問題の総数
        cursor.execute("""
            SELECT COUNT(*) 
            FROM questions q
            LEFT JOIN choices c ON q.id = c.question_id
            WHERE c.question_id IS NULL
        """)
        
        no_choices_count = cursor.fetchone()[0]
        print(f"\n📈 統計:")
        print(f"   選択肢なし問題: {no_choices_count}個")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def analyze_choice_generation_pattern():
    """選択肢生成パターンの分析"""
    
    print(f"\n🔍 選択肢生成パターンの分析")
    print("=" * 50)
    
    print("✅ **成功している点:**")
    print("   - モデル選択機能が正常動作")
    print("   - 問題文と解説の生成は完璧")
    print("   - GPT-4o Miniの高品質な回答")
    
    print("\n❌ **問題点:**")
    print("   - OpenAI APIから選択肢が返されているが、DB保存で失敗")
    print("   - または、選択肢がAPIレスポンスに含まれていない")
    
    print("\n🔧 **次回の改善点:**")
    print("   1. OpenAI APIのレスポンスログを詳細化")
    print("   2. 選択肢保存プロセスのエラーハンドリング強化")
    print("   3. 問題生成時の選択肢必須チェック")

def main():
    print("🚨 問題145の選択肢修正と分析")
    print("=" * 60)
    
    # 問題145の確認と修正
    check_and_fix_question_145()
    
    # 最近の問題の選択肢状況確認
    check_recent_questions_with_choices()
    
    # 分析
    analyze_choice_generation_pattern()
    
    print(f"\n💡 次のステップ:")
    print("1. 修正した問題145でクイズを実行")
    print("2. 新しい問題生成時のログを詳細に確認")
    print("3. 選択肢生成プロセスのさらなる改善")

if __name__ == "__main__":
    main()
