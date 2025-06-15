#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正後のenhanced_openai_service.pyのテスト
"""

try:
    print("🧪 Testing fixed enhanced_openai_service.py...")
    
    # Import test
    from services.enhanced_openai_service import EnhancedOpenAIService
    print("✅ Import successful")
    
    # Instance creation test  
    service = EnhancedOpenAIService()
    print("✅ Instance creation successful")
    
    # Check methods exist
    assert hasattr(service, 'call_openai_api'), "call_openai_api method missing"
    assert hasattr(service, 'generate_question'), "generate_question method missing"
    assert hasattr(service, 'test_connection'), "test_connection method missing"
    print("✅ All methods exist")
    
    print("\n🎉 All tests passed! The syntax error has been fixed.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
