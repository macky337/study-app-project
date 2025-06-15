#!/usr/bin/env python3
"""
過去問抽出の詳細デバッグ
"""

import os
import json
from dotenv import load_dotenv

def test_question_structure_extraction():
    """問題構造抽出の詳細テスト"""
    
    print("🔍 過去問構造抽出の詳細デバッグ")
    print("=" * 60)
    
    # サンプル問題テキスト
    sample_question = """
問題1. 次のうち、Pythonの基本データ型でないものはどれか。

A. int
B. float  
C. string
D. array

解説：Pythonの基本データ型は int, float, str, bool です。array は標準のデータ型ではありません。
正解：D
"""
    
    print(f"📝 サンプル問題:")
    print(sample_question)
    print(f"文字数: {len(sample_question)}")
    
    # OpenAI APIで構造化抽出をテスト
    try:
        from openai import OpenAI
        
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 構造化抽出プロンプト
        prompt = f"""
以下の過去問テキストから、問題の構造を解析してJSON形式で出力してください。

【入力テキスト】
{sample_question}

【出力形式】
以下のJSON形式で返してください：
{{
    "title": "問題のタイトル（簡潔に）",
    "question": "問題文", 
    "choices": [
        {{"text": "選択肢1", "is_correct": false}},
        {{"text": "選択肢2", "is_correct": false}},
        {{"text": "選択肢3", "is_correct": false}},
        {{"text": "選択肢4", "is_correct": true}}
    ],
    "explanation": "解説文",
    "difficulty": "easy"
}}

【注意】JSON形式以外での回答は絶対に禁止です。必ず有効なJSONオブジェクトを返してください。
"""
        
        print(f"\n🚀 OpenAI API呼び出し開始")
        print(f"プロンプト長: {len(prompt)} 文字")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは過去問解析の専門家です。必ずJSON形式で回答してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"\n📋 API応答:")
        print(content)
        print(f"応答長: {len(content)} 文字")
        
        # JSON解析テスト
        print(f"\n🔍 JSON解析テスト")
        try:
            data = json.loads(content)
            print(f"✅ JSON解析成功")
            print(f"フィールド: {list(data.keys())}")
            
            # データ検証
            required_fields = ['title', 'question', 'choices', 'explanation']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print(f"⚠️ 不足フィールド: {missing_fields}")
            else:
                print(f"✅ 必須フィールド完全")
                
            # 選択肢検証
            if 'choices' in data and isinstance(data['choices'], list):
                print(f"✅ 選択肢数: {len(data['choices'])}個")
                correct_count = sum(1 for choice in data['choices'] if choice.get('is_correct'))
                print(f"✅ 正解数: {correct_count}個")
            else:
                print(f"❌ 選択肢形式エラー")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失敗: {e}")
            print(f"応答の最初の100文字: {repr(content[:100])}")
            
            # フォールバック抽出テスト
            print(f"\n🔄 フォールバック抽出テスト")
            fallback_result = test_fallback_extraction(sample_question)
            if fallback_result:
                print(f"✅ フォールバック抽出成功")
                print(json.dumps(fallback_result, ensure_ascii=False, indent=2))
            else:
                print(f"❌ フォールバック抽出失敗")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()


def test_fallback_extraction(text: str):
    """フォールバック抽出のテスト"""
    
    import re
    
    try:
        lines = text.split('\n')
        
        question_lines = []
        choices = []
        explanation_lines = []
        
        current_section = "question"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 選択肢パターンの検出
            choice_match = re.match(r'^[A-D1-4][.．)\s](.+)', line)
            if choice_match:
                choices.append(choice_match.group(1))
                current_section = "choices"
                continue
            
            # 解説パターンの検出
            if re.match(r'^(解説|答え|正解|解答)[：:]', line, re.IGNORECASE):
                current_section = "explanation"
                explanation_lines.append(line)
                continue
            
            # 現在のセクションに応じて追加
            if current_section == "question":
                question_lines.append(line)
            elif current_section == "explanation":
                explanation_lines.append(line)
        
        if question_lines and choices:
            return {
                "title": question_lines[0][:20] + "..." if len(question_lines[0]) > 20 else question_lines[0],
                "question": '\n'.join(question_lines),
                "choices": [{"text": choice, "is_correct": i == 0} for i, choice in enumerate(choices)],
                "explanation": '\n'.join(explanation_lines) if explanation_lines else "解説なし",
                "difficulty": "medium"
            }
    
    except Exception as e:
        print(f"フォールバック抽出エラー: {e}")
    
    return None


if __name__ == "__main__":
    test_question_structure_extraction()
