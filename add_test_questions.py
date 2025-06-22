#!/usr/bin/env python3
"""
テスト問題追加スクリプト
整合性チェック機能をテストするための問題を追加します。
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_test_questions():
    """テスト用の問題（正常・不正両方）を追加"""
    print("🧪 テスト問題追加ツール")
    print("=" * 50)
    
    try:
        # データベース接続
        from config.app_config import check_database_connection, ensure_models_loaded
        from database.operations import QuestionService, ChoiceService
        from database.connection import get_session_context
        
        db_available, db_error = check_database_connection()
        if not db_available:
            print(f"❌ データベース接続エラー: {db_error}")
            return False
        
        ensure_models_loaded()
        
        with get_session_context() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            
            test_questions = [
                # 正常な問題
                {
                    "title": "正常な問題1",
                    "content": "Pythonでリストを作成する正しい構文は？",
                    "explanation": "角括弧[]を使用してリストを作成します。",
                    "category": "プログラミング",
                    "difficulty": "easy",
                    "choices": [
                        ("list = []", True),
                        ("list = {}", False),
                        ("list = ()", False),
                        ("list = <>", False)
                    ]
                },
                
                # 問題文が空
                {
                    "title": "問題文が空",
                    "content": "",  # 問題: 空の問題文
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "medium",
                    "choices": [
                        ("選択肢1", True),
                        ("選択肢2", False),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                },
                
                # 解説が空
                {
                    "title": "解説が空の問題",
                    "content": "これは正常な問題文です。",
                    "explanation": "",  # 問題: 空の解説
                    "category": "テスト",
                    "difficulty": "hard",
                    "choices": [
                        ("選択肢1", True),
                        ("選択肢2", False),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                },
                
                # 正解がない
                {
                    "title": "正解がない問題",
                    "content": "この問題には正解がありません。",
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "medium",
                    "choices": [
                        ("選択肢1", False),  # 問題: 全て不正解
                        ("選択肢2", False),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                },
                
                # 正解が複数
                {
                    "title": "正解が複数の問題",
                    "content": "この問題には複数の正解があります。",
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "hard",
                    "choices": [
                        ("選択肢1", True),   # 問題: 複数正解
                        ("選択肢2", True),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                },
                
                # 選択肢が5つ以上
                {
                    "title": "選択肢が多すぎる問題",
                    "content": "この問題には選択肢が多すぎます。",
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "medium",
                    "choices": [
                        ("選択肢1", False),
                        ("選択肢2", True),
                        ("選択肢3", False),
                        ("選択肢4", False),
                        ("選択肢5", False),  # 問題: 5つ以上の選択肢
                        ("選択肢6", False)
                    ]
                },
                
                # 文字化けのある問題
                {
                    "title": "文字化け問題",
                    "content": "この問題にはｱｲｳｴｵの文字化けがあります。",  # 問題: 半角カタカナ
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "easy",
                    "choices": [
                        ("選択肢1", True),
                        ("選択肢2", False),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                },
                
                # 不要なパターンのある問題
                {
                    "title": "不要パターン問題",
                    "content": "1 【問1】この問題文には不要なパターンがあります。",  # 問題: 【問○】パターン
                    "explanation": "これは正常な解説です。",
                    "category": "テスト",
                    "difficulty": "medium",
                    "choices": [
                        ("選択肢1", True),
                        ("選択肢2", False),
                        ("選択肢3", False),
                        ("選択肢4", False)
                    ]
                }
            ]
            
            print(f"📝 {len(test_questions)} 個のテスト問題を追加中...")
            
            added_count = 0
            for i, question_data in enumerate(test_questions, 1):
                try:
                    # 問題を作成
                    question = question_service.create_question(
                        title=question_data["title"],
                        content=question_data["content"],
                        explanation=question_data["explanation"],
                        category=question_data["category"],
                        difficulty=question_data["difficulty"]
                    )
                    
                    if question:
                        # 選択肢を追加
                        for choice_content, is_correct in question_data["choices"]:
                            choice_service.create_choice(
                                question_id=question.id,
                                content=choice_content,
                                is_correct=is_correct
                            )
                        
                        print(f"  ✅ 問題 {i}: {question_data['title']}")
                        added_count += 1
                    else:
                        print(f"  ❌ 問題 {i}: 作成失敗")
                        
                except Exception as e:
                    print(f"  ❌ 問題 {i}: エラー - {e}")
            
            print(f"\n📊 結果:")
            print(f"  ✅ 追加成功: {added_count} 件")
            print(f"  ❌ 追加失敗: {len(test_questions) - added_count} 件")
            
            return True
            
    except Exception as e:
        print(f"❌ テスト問題追加中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_test_questions()
    sys.exit(0 if success else 1)
