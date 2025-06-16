#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題144の選択肢追加とモデル選択問題の修正
"""

import os
import sys
import sqlite3
from datetime import datetime

def fix_question_144():
    """問題144に選択肢を追加"""
    
    print("🔧 問題144の選択肢追加")
    print("=" * 50)
    
    db_path = "study_app.db"
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 問題144の確認
        cursor.execute("""
            SELECT id, title, question_text, explanation
            FROM questions 
            WHERE id = 144
        """)
        
        question = cursor.fetchone()
        if question:
            q_id, title, content, explanation = question
            print(f"✅ 問題 {q_id}: {title}")
            print(f"   問題文: {content}")
            
            # 既存選択肢を削除
            cursor.execute("DELETE FROM choices WHERE question_id = ?", (144,))
            
            # 変数の定義に関する適切な選択肢を追加
            choices_to_add = [
                {"content": "データを格納するための名前付きの記憶場所", "is_correct": True},
                {"content": "プログラムで使用する関数やメソッドの名前", "is_correct": False},
                {"content": "プログラムの実行順序を制御する命令", "is_correct": False},
                {"content": "データの型を定義するためのキーワード", "is_correct": False}
            ]
            
            print(f"\n📝 選択肢を追加中...")
            for i, choice in enumerate(choices_to_add, 1):
                cursor.execute("""
                    INSERT INTO choices (question_id, choice_text, is_correct, order_num, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    144,
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
            print("❌ 問題144が見つかりません")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def check_model_selection_issue():
    """モデル選択問題の診断"""
    
    print(f"\n🔍 モデル選択問題の診断")
    print("=" * 50)
    
    print("問題分析:")
    print("- UIで gpt-4o-mini を選択")
    print("- しかし実際は gpt-3.5-turbo が使用されている")
    
    print("\n考えられる原因:")
    print("1. サービス初期化時にデフォルトモデルで上書きされている")
    print("2. モデルパラメータが正しく渡されていない")
    print("3. Streamlitのセッション管理の問題")
    
    print("\n修正方針:")
    print("1. OpenAIサービス初期化のログを詳細化")
    print("2. モデル選択の渡し方を確認")
    print("3. セッション状態でモデル選択を管理")

def main():
    print("🚨 問題144修正 + モデル選択問題診断")
    print("=" * 60)
    
    # 問題144の選択肢修正
    fix_question_144()
    
    # モデル選択問題の診断
    check_model_selection_issue()
    
    print(f"\n💡 次のステップ:")
    print("1. モデル選択のコード修正")
    print("2. アプリ再起動")
    print("3. 動作確認")

if __name__ == "__main__":
    main()
