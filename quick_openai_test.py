#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI接続の迅速テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def quick_openai_test():
    """迅速なOpenAI接続テスト"""
    print("🚀 OpenAI接続テスト開始")
    print("=" * 40)
    
    # 1. 環境変数チェック
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return False
    
    print(f"✅ APIキー: {api_key[:10]}...{api_key[-4:]}")
    
    # 2. 基本的なOpenAI接続テスト
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("🔄 API接続テスト中...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        if response and response.choices:
            print(f"✅ 接続成功: {response.choices[0].message.content}")
            return True
        else:
            print("❌ 接続失敗: レスポンスなし")
            return False
            
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        return False

def test_enhanced_service():
    """EnhancedOpenAIServiceテスト"""
    print("\n🔧 EnhancedOpenAIServiceテスト")
    print("=" * 40)
    
    try:
        from services.enhanced_openai_service import EnhancedOpenAIService
        
        service = EnhancedOpenAIService()
        print(f"✅ Service initialized with model: {service.model}")
        
        # 接続テスト
        result = service.test_connection()
        print(f"テスト結果: {result}")
        
        if result.get("success"):
            print("✅ EnhancedOpenAIService接続成功")
            return True
        else:
            print(f"❌ EnhancedOpenAIService接続失敗: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ EnhancedOpenAIService初期化失敗: {e}")
        return False

if __name__ == "__main__":
    # 基本テスト
    basic_success = quick_openai_test()
    
    # サービステスト
    service_success = test_enhanced_service()
    
    print("\n" + "=" * 40)
    print("📊 結果サマリー")
    print(f"   基本テスト: {'✅ 成功' if basic_success else '❌ 失敗'}")
    print(f"   サービステスト: {'✅ 成功' if service_success else '❌ 失敗'}")
    
    if basic_success and service_success:
        print("\n🎉 全テスト成功！")
    else:
        print("\n⚠️ 問題が検出されました。")
        print("💡 以下を確認してください:")
        print("   - インターネット接続")
        print("   - OpenAI APIキーの有効性")
        print("   - OpenAIアカウントのクレジット残高")
