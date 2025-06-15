#!/usr/bin/env python3
"""
OpenAI API接続テスト
"""

import sys
import os

# プロジェクトディレクトリを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 OpenAI API接続テスト開始")
    
    # 環境変数の読み込みテスト
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI APIキー: 設定済み ({api_key[:10]}...)")
    else:
        print("❌ OpenAI APIキー: 未設定")
        sys.exit(1)
    
    # EnhancedOpenAIServiceのテスト
    from services.enhanced_openai_service import EnhancedOpenAIService
    
    service = EnhancedOpenAIService()
    print("✅ EnhancedOpenAIService: インスタンス化成功")
    
    # 接続テスト
    if hasattr(service, 'test_connection'):
        result = service.test_connection()
        if result:
            print("✅ OpenAI API: 接続成功")
        else:
            print("❌ OpenAI API: 接続失敗")
    
    # 簡単なAPI呼び出しテスト
    if hasattr(service, 'call_openai_api'):
        print("🔍 API呼び出しテスト中...")
        response = service.call_openai_api(
            "こんにちは", 
            max_tokens=50, 
            temperature=0.5
        )
        if response:
            print(f"✅ API呼び出し成功: {response[:50]}...")
        else:
            print("❌ API呼び出し失敗")
    else:
        print("⚠️ call_openai_apiメソッドが存在しません")
    
    print("\n🎯 OpenAI APIテスト完了")
    
except Exception as e:
    print(f"❌ テストエラー: {e}")
    import traceback
    traceback.print_exc()
