#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特定問題の選択肢確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_database_session
from models.question import Question
from models.choice import Choice

def check_specific_question():
    """特定の問題（問題9/問8）をチェック"""
    
    print("特定問題チェック: 問題9 / 問8")
    print("=" * 50)
    
    try:
        session = get_database_session()
        
        # 問題8または問題9に関連する問題を検索
        questions = session.query(Question).filter(
            Question.content.like('%問8%') | 
            Question.content.like('%問題8%') |
            Question.content.like('%企業の農業参入%')
        ).all()
        
        print(f"該当問題数: {len(questions)}問")
        
        for question in questions:
            print(f"\n問題 ID: {question.id}")
            print(f"タイトル: {question.title}")
            print(f"カテゴリ: {question.category}")
            print(f"問題文: {question.content}")
              # 選択肢取得
            choices = session.query(Choice).filter(
                Choice.question_id == question.id
            ).order_by(Choice.order_num).all()
            
            print(f"選択肢数: {len(choices)}個")
            
            if choices:
                for i, choice in enumerate(choices):
                    status = "✓正解" if choice.is_correct else " 不正解"
                    print(f"  {chr(65+i)}. {choice.content} ({status})")
            else:
                print("  ERROR: 選択肢がありません！")
                
                # 問題文から選択肢を抽出してみる
                print("  問題文から選択肢抽出を試行...")
                import re
                
                # ①②③④形式を検索
                pattern1 = r'[①②③④⑤]\s*([^①②③④⑤\n]+)'
                matches = re.findall(pattern1, question.content)
                
                if matches:
                    print(f"  抽出候補: {len(matches)}個")
                    for j, match in enumerate(matches):
                        print(f"    {j+1}. {match.strip()}")
                    
                    # 選択肢を自動追加
                    print("  選択肢をデータベースに追加中...")
                    for j, match in enumerate(matches):
                        choice = Choice(
                            question_id=question.id,
                            content=match.strip(),
                            is_correct=(j == 0),  # 最初を正解とする
                            order_num=j + 1
                        )
                        session.add(choice)
                    
                    session.commit()
                    print("  SUCCESS: 選択肢追加完了")
                else:
                    print("  WARNING: 選択肢を抽出できませんでした")
        
        session.close()
        
    except Exception as e:
        print(f"ERROR: チェックエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    check_specific_question()

if __name__ == "__main__":
    main()
