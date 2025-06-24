#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用問題をデータベースに追加するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import QuestionService, ChoiceService
from database.connection import get_session

def add_test_question():
    """テスト用の問題を追加"""
    
    # セッションを取得
    session = get_session()
    question_service = QuestionService(session)
    choice_service = ChoiceService(session)
    
    try:
        # テスト問題を作成
        question = question_service.create_question(
            title="コンピュータの基本構成",
            content="コンピュータの基本構成要素として正しいものはどれか。",
            category="プログラミング",
            difficulty="easy",
            explanation="コンピュータの基本構成要素は、CPU、メモリ、入出力装置です。ハードディスクは記憶装置の一種であり、ネットワークは通信手段、キーボード・マウスは入力装置です。"
        )
        
        print(f"✅ 問題を作成しました: ID={question.id}")
        
        # 選択肢を作成
        choices_data = [
            ("CPU、メモリ、ハードディスク", False),
            ("CPU、メモリ、入出力装置", True),
            ("CPU、メモリ、ネットワーク", False),
            ("CPU、キーボード、マウス", False)
        ]
        
        for i, (content, is_correct) in enumerate(choices_data):
            choice = choice_service.create_choice(
                question_id=question.id,
                content=content,
                is_correct=is_correct,
                order_num=i + 1
            )
            print(f"✅ 選択肢を作成しました: {content} (正答: {is_correct})")
        
        print(f"\n🎉 テスト問題の追加が完了しました！")
        print(f"📋 問題ID: {question.id}")
        print(f"📝 タイトル: {question.title}")
        print(f"📂 カテゴリ: {question.category}")
        print(f"🔧 難易度: {question.difficulty}")
        
        return question.id
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        session.close()

def main():
    """メイン関数"""
    print("🚀 テスト用問題をデータベースに追加中...")
    question_id = add_test_question()
    
    if question_id:
        print(f"\n✨ 成功！ブラウザでhttp://localhost:8502にアクセスして編集機能をテストしてください。")
        print(f"   問題管理ページで問題ID {question_id} の編集ボタンをクリックしてください。")
    else:
        print(f"\n❌ 問題の追加に失敗しました。")

if __name__ == "__main__":
    main()
