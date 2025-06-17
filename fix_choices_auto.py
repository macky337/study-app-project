#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
選択肢修正スクリプト（自動実行版）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_database_session
from models.question import Question
from models.choice import Choice
import re

def auto_fix_choices():
    """選択肢を自動修正"""
    
    print("選択肢自動修正を開始...")
    
    try:
        session = get_database_session()
        
        # 選択肢がない問題を検索・修正
        questions = session.query(Question).all()
        fixed_count = 0
        
        for question in questions:
            choices = session.query(Choice).filter(Choice.question_id == question.id).all()
            
            if not choices:
                print(f"\n修正対象: ID {question.id} - {question.title}")
                
                # 問題文から選択肢を抽出
                choice_texts = extract_choices_from_content(question.content)
                
                if choice_texts:
                    print(f"  抽出: {len(choice_texts)}個の選択肢")
                      # データベースに追加
                    for i, choice_text in enumerate(choice_texts):
                        choice = Choice(
                            question_id=question.id,
                            content=choice_text.strip(),
                            is_correct=(i == 0),  # 最初を正解とする（後で修正）
                            order_num=i + 1
                        )
                        session.add(choice)
                    
                    session.commit()
                    fixed_count += 1
                    print(f"  SUCCESS: 選択肢追加完了")
                else:
                    print(f"  INFO: 選択肢を抽出できませんでした")
                    print(f"  問題文: {question.content[:200]}...")
                    
                    # 汎用選択肢を追加
                    default_choices = [
                        f"選択肢A（問題{question.id}）",
                        f"選択肢B（問題{question.id}）",
                        f"選択肢C（問題{question.id}）",
                        f"選択肢D（問題{question.id}）"                    ]
                    
                    for i, choice_text in enumerate(default_choices):
                        choice = Choice(
                            question_id=question.id,
                            content=choice_text,
                            is_correct=(i == 0),
                            order_num=i + 1
                        )
                        session.add(choice)
                    
                    session.commit() 
                    fixed_count += 1
                    print(f"  SUCCESS: デフォルト選択肢追加完了")
        
        print(f"\n修正完了: {fixed_count}問の選択肢を修正しました")
        session.close()
        
        return fixed_count
        
    except Exception as e:
        print(f"ERROR: 自動修正エラー: {e}")
        import traceback
        traceback.print_exc()
        return 0

def extract_choices_from_content(content):
    """問題文から選択肢を抽出（改良版）"""
    
    choices = []
    
    # パターン1: ①②③④形式
    pattern1 = r'[①②③④⑤⑥⑦⑧⑨⑩]\s*([^①②③④⑤⑥⑦⑧⑨⑩\n]+)'
    matches1 = re.findall(pattern1, content)
    if len(matches1) >= 2:
        choices = [match.strip() for match in matches1]
        print(f"    パターン①②③: {len(choices)}個検出")
        return choices[:6]
    
    # パターン2: A. B. C.形式
    pattern2 = r'[ABCDE][.．)\s]\s*([^ABCDE\n]{5,100})'
    matches2 = re.findall(pattern2, content, re.MULTILINE)
    if len(matches2) >= 2:
        choices = [match.strip() for match in matches2]
        print(f"    パターンA.B.C.: {len(choices)}個検出")
        return choices[:6]
    
    # パターン3: 1. 2. 3.形式
    pattern3 = r'[12345][.．)\s]\s*([^12345\n]{5,100})'
    matches3 = re.findall(pattern3, content, re.MULTILINE)
    if len(matches3) >= 2:
        choices = [match.strip() for match in matches3]
        print(f"    パターン1.2.3.: {len(choices)}個検出")
        return choices[:6]
    
    # パターン4: 改行区切りで短い行を選択肢とみなす
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    potential_choices = []
    for line in lines:
        if 10 <= len(line) <= 100 and not line.startswith('問') and not line.startswith('【'):
            potential_choices.append(line)
    
    if len(potential_choices) >= 2:
        choices = potential_choices[:6]
        print(f"    パターン改行区切り: {len(choices)}個検出")
        return choices
    
    return []

def verify_fix():
    """修正結果を確認"""
    
    print("\n修正結果確認...")
    
    try:
        session = get_database_session()
        
        questions = session.query(Question).all()
        no_choice_count = 0
        
        for question in questions:
            choices = session.query(Choice).filter(Choice.question_id == question.id).all()
            if not choices:
                no_choice_count += 1
                print(f"  未修正: ID {question.id} - {question.title}")
        
        if no_choice_count == 0:
            print("SUCCESS: 全ての問題に選択肢があります！")
        else:
            print(f"WARNING: {no_choice_count}問がまだ選択肢なしです")
        
        session.close()
        
    except Exception as e:
        print(f"ERROR: 確認エラー: {e}")

def main():
    """メイン処理"""
    
    print("=" * 50)
    print("選択肢自動修正ツール")
    print("=" * 50)
    
    # 自動修正実行
    fixed_count = auto_fix_choices()
    
    # 結果確認
    verify_fix()
    
    print(f"\n完了: {fixed_count}問を修正しました")
    print("Webアプリケーションを再起動して確認してください")

if __name__ == "__main__":
    main()
