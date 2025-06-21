#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Connection Issue Quick Fix
"""

import os

def check_and_fix_openai_connection():
    """OpenAI接続問題の確認と修正"""
    
    print("🔧 OpenAI Connection Quick Fix")
    print("=" * 50)
    
    # .env ファイルの確認
    if os.path.exists('.env'):
        print("✅ .env file found")
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'OPENAI_API_KEY=' in content:
            # API key の行を抽出
            for line in content.split('\n'):
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1]
                    if api_key and len(api_key) > 20:
                        print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
                        
                        # API key の形式確認
                        if api_key.startswith('sk-'):
                            print("✅ API key format looks correct")
                        else:
                            print("⚠️ API key format might be incorrect (should start with 'sk-')")
                    else:
                        print("❌ API key appears to be empty or too short")
                    break
        else:
            print("❌ OPENAI_API_KEY not found in .env file")
    else:
        print("❌ .env file not found")
    
    # 環境変数の確認
    print("\n🔍 Environment Variable Check:")
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        print(f"✅ Environment OPENAI_API_KEY: {env_key[:10]}...{env_key[-4:]}")
    else:
        print("❌ OPENAI_API_KEY not loaded as environment variable")
    
    # 解決策の提案
    print("\n💡 Troubleshooting Steps:")
    print("1. Restart the Streamlit app: streamlit run app.py")
    print("2. Check internet connection")
    print("3. Verify OpenAI API status: https://status.openai.com/")
    print("4. Check API key billing: https://platform.openai.com/account/billing")
    
    print("\n🎯 Quick Test Command:")
    print("python -c \"import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'Not found')\"")

if __name__ == "__main__":
    check_and_fix_openai_connection()
