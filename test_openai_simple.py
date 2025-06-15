#!/usr/bin/env python3
"""
OpenAI API 単体テスト（過去問抽出用）
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

def test_openai_extraction():
    """OpenAI APIを使った過去問抽出の単体テスト"""
    
    print("🔍 OpenAI API 過去問抽出テスト")
    print("=" * 50)
    
    # 環境変数読み込み
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # サンプル問題
    sample_question = """
【問1】
名刺の交換マナーについて、適切なものをすべて選べ。
① いすに座っている時に名刺交換が始まったら、すぐに立ち上がりテーブル越しに名刺を差し出し、交換する
② 名刺は文字に指がかからないように持ち、名刺の文字が相手に向くようにして差し出す
③ 相手の名刺を受け取る際は片手で受け取り、すぐに名刺入れにしまう
④ 名刺交換の際には、役職が高い方から渡していく
(正解）②,④
(解説）①名刺交換はテーブル越しには行わない。テーブルを回り込み相手の正面に立って交換する。
③受け取る際は原則両手で受け取り、すぐにはしまわずにしばらく手元に置いて確認する。
"""
    
    print(f"📝 テスト問題: {len(sample_question)}文字")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # シンプルなプロンプト
        prompt = f"""
以下のテキストから問題を抽出してJSONで返してください。

テキスト:
{sample_question}

以下の形式のJSONで返してください:
{{
    "title": "問題タイトル（20文字以内）",
    "question": "問題文",
    "choices": [
        {{"text": "選択肢A", "is_correct": false}},
        {{"text": "選択肢B", "is_correct": false}},
        {{"text": "選択肢C", "is_correct": false}},
        {{"text": "選択肢D", "is_correct": true}}
    ],
    "explanation": "解説",
    "difficulty": "medium"
}}

重要: JSONのみ返してください。他の文章は不要です。
"""
        
        print(f"🚀 OpenAI API呼び出し開始")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは過去問解析の専門家です。必ずJSON形式で回答してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.0,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ API応答成功")
        print(f"📋 応答内容: {len(content)}文字")
        print(f"応答: {content}")
        
        # JSONパース
        try:
            # クリーンアップ
            cleaned_content = content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            data = json.loads(cleaned_content)
            print(f"✅ JSON解析成功")
            print(f"フィールド: {list(data.keys())}")
            
            if 'choices' in data:
                print(f"選択肢数: {len(data['choices'])}")
                for i, choice in enumerate(data['choices']):
                    status = "⭐" if choice.get('is_correct') else "  "
                    print(f"  {status} {i+1}: {choice.get('text', 'N/A')[:50]}...")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失敗: {e}")
            print(f"クリーンアップ後: {cleaned_content[:200]}...")
        
        print(f"✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_openai_extraction()
