#!/usr/bin/env python3
"""
簡単なテスト問題追加スクリプト（APIキー不要）
データベースの基本機能をテストします。
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_simple_test_questions():
    """APIキー不要でテスト用の問題を追加"""
    print("🧪 簡単なテスト問題追加ツール")
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
                
                # 正常な問題2
                {
                    "title": "正常な問題2",
                    "content": "変数の命名規則として正しいものは？",
                    "explanation": "変数名は文字またはアンダースコアで始まり、数字、文字、アンダースコアを含むことができます。",
                    "category": "プログラミング",
                    "difficulty": "medium",
                    "choices": [
                        ("1variable", False),
                        ("variable_1", True),
                        ("variable-1", False),
                        ("variable 1", False)
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
                    
                    if question and hasattr(question, 'id'):
                        # 選択肢を追加
                        for order, (choice_content, is_correct) in enumerate(question_data["choices"], 1):
                            choice_service.create_choice(
                                question_id=question.id,
                                content=choice_content,
                                is_correct=is_correct,
                                order_num=order
                            )
                        
                        print(f"  ✅ 問題 {i}: {question_data['title']} (ID: {question.id})")
                        added_count += 1
                    else:
                        print(f"  ❌ 問題 {i}: 作成失敗 - questionオブジェクトが無効")
                        
                except Exception as e:
                    print(f"  ❌ 問題 {i}: エラー - {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"\n📊 結果:")
            print(f"  ✅ 追加成功: {added_count} 件")
            print(f"  ❌ 追加失敗: {len(test_questions) - added_count} 件")
            
            return added_count > 0
            
    except Exception as e:
        print(f"❌ テスト問題追加中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_simple_test_questions()
    sys.exit(0 if success else 1)
