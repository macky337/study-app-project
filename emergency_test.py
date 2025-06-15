#!/usr/bin/env python3
"""
OpenAI API 緊急デバッグテスト
"""

import os
import json
from dotenv import load_dotenv

def emergency_test():
    """緊急テスト"""
    
    print("🚨 緊急OpenAI APIテスト")
    print("=" * 50)
    
    # 環境変数読み込み
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    print(f"✅ API Key: {api_key[:15]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # 極めてシンプルなテスト
        print("🧪 基本テスト実行中...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ 基本テスト成功: {content}")
        
        # JSONテスト
        print("🧪 JSONテスト実行中...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": 'Return only: {"status": "ok"}'}
            ],
            max_tokens=20,
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        print(f"✅ JSON応答: {content}")
        
        try:
            data = json.loads(content)
            print(f"✅ JSON解析成功: {data}")
        except:
            print(f"❌ JSON解析失敗")
        
        # プライバシーヘッダーテスト
        print("🧪 プライバシーヘッダーテスト実行中...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Test"}
            ],
            max_tokens=5,
            extra_headers={
                "X-OpenAI-Skip-Training": "true"
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ プライバシーヘッダーテスト成功: {content}")
        
        print("🎉 全てのテストが成功しました")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    emergency_test()
