#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースセットアップとアプリ起動テスト
"""

import os
import sys

def setup_database():
    """データベースをセットアップ"""
    print("🔧 Setting up database...")
    
    try:
        from database.connection import engine
        from sqlmodel import SQLModel
        
        if engine is None:
            print("❌ Engine is None")
            return False
            
        # テーブル作成
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_app_startup():
    """アプリケーションの起動テスト"""
    print("🚀 Testing application startup...")
    
    try:
        # 重要なモジュールのインポートテスト
        from database.operations import QuestionService, ChoiceService, UserAnswerService
        from services.past_question_extractor import PastQuestionExtractor
        from services.enhanced_openai_service import EnhancedOpenAIService
        
        print("✅ All critical modules imported successfully")
        
        # OpenAI API キーの確認
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            print("✅ OpenAI API key found")
        else:
            print("⚠️ OpenAI API key not found - will use demo mode")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False

def main():
    print("🔍 Database Setup and App Test")
    print("=" * 40)
    
    # データベースセットアップ
    db_setup = setup_database()
    
    # アプリ起動テスト
    app_test = test_app_startup()
    
    print("\n" + "=" * 40)
    print("📊 RESULTS:")
    print(f"   Database Setup: {'✅ OK' if db_setup else '❌ FAILED'}")
    print(f"   App Startup: {'✅ OK' if app_test else '❌ FAILED'}")
    
    if db_setup and app_test:
        print("\n🎉 Ready to start the application!")
        print("💡 Run: streamlit run app.py")
    else:
        print("\n⚠️ Issues found. Please check the errors above.")

if __name__ == "__main__":
    main()
