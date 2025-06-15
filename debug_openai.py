#!/usr/bin/env python3
"""
OpenAI API接続の詳細デバッグ
"""

import os
from dotenv import load_dotenv

def test_openai_basic():
    """基本的なOpenAI接続テスト"""
    
    print("🔍 OpenAI API 詳細デバッグ")
    print("=" * 50)
    
    # 環境変数読み込み
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔑 API Key 状態: {'設定済み' if api_key else '未設定'}")
    if api_key:
        print(f"   Key プレフィックス: {api_key[:10]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        print("✅ OpenAIクライアント初期化成功")
        
        # 基本テスト
        print("\n🧪 基本API呼び出しテスト")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, respond with just 'OK'"}
            ],
            max_tokens=10,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ API応答成功: {content}")
        
        # 日本語テスト
        print("\n🧪 日本語API呼び出しテスト")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "こんにちは。「OK」とだけ返答してください。"}
            ],
            max_tokens=10,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ 日本語API応答成功: {content}")
        
        # JSON応答テスト
        print("\n🧪 JSON応答テスト")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": '必ずJSON形式で {"status": "OK"} と返答してください。'}
            ],
            max_tokens=50,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ JSON応答テスト: {content}")
        
        # JSON解析テスト
        import json
        try:
            parsed = json.loads(content)
            print(f"✅ JSON解析成功: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失敗: {e}")
            print(f"   原文: {repr(content)}")
        
        print("\n✅ すべてのテストが完了しました")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_openai_basic()
