#!/usr/bin/env python3
"""
過去問抽出のテスト
"""

def test_question_extraction():
    """過去問抽出のテスト"""
    
    print("🧪 過去問抽出機能のテスト")
    print("=" * 50)
    
    # サンプルテキスト（簡単な問題形式）
    sample_text = """
問題1. 次のうち、Pythonの基本データ型でないものはどれか。

A. int
B. float  
C. string
D. array

解説：Pythonの基本データ型は int, float, str, bool です。array は標準のデータ型ではありません。
正解：D

問題2. 次のうち、正しいPythonの変数名はどれか。

A. 2variable
B. variable-name
C. variable_name
D. class

解説：Pythonの変数名は文字またはアンダースコアで始まり、予約語は使用できません。
正解：C
"""
    
    print(f"📝 サンプルテキスト長: {len(sample_text)} 文字")
    
    try:
        # 過去問抽出サービスをテスト
        from services.past_question_extractor import PastQuestionExtractor
        
        # ダミーセッション（テスト用）
        class DummySession:
            pass
        
        extractor = PastQuestionExtractor(DummySession())
        
        # 問題分割のテスト
        questions = extractor._split_into_questions(sample_text)
        print(f"✅ 問題分割結果: {len(questions)}問を検出")
        
        for i, q in enumerate(questions):
            print(f"   問題{i+1}: {q[:100]}...")
        
        # 1つの問題でOpenAI API呼び出しをテスト（実際のAPIキーが必要）
        if questions and len(questions) > 0:
            print(f"\n🚀 OpenAI API抽出テスト（問題1）")
            try:
                result = extractor._extract_question_structure(questions[0])
                if result:
                    print("✅ 抽出成功!")
                    print(f"   タイトル: {result.get('title', 'なし')}")
                    print(f"   問題文: {result.get('question', '')[:100]}...")
                    print(f"   選択肢数: {len(result.get('choices', []))}")
                    print(f"   解説: {result.get('explanation', '')[:100]}...")
                else:
                    print("❌ 抽出失敗")
            except Exception as e:
                print(f"❌ API呼び出しエラー: {e}")
                print("💡 OpenAI APIキーが設定されていない可能性があります")
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n💡 トラブルシューティング:")
    print("1. OpenAI APIキーが正しく設定されているか確認")
    print("2. 入力テキストに適切な問題形式が含まれているか確認") 
    print("3. ネットワーク接続が正常か確認")
    print("4. OpenAI APIの使用量制限に達していないか確認")

if __name__ == "__main__":
    test_question_extraction()
