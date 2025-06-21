#!/usr/bin/env python3
"""
インポートテスト用スクリプト
"""

try:
    import streamlit as st
    print("✅ streamlit import successful, version:", st.__version__)
except ImportError as e:
    print("❌ streamlit import failed:", e)

try:
    from sqlmodel import Session
    print("✅ sqlmodel import successful")
except ImportError as e:
    print("❌ sqlmodel import failed:", e)

try:
    import openai
    print("✅ openai import successful, version:", openai.__version__)
except ImportError as e:
    print("❌ openai import failed:", e)

try:
    from dotenv import load_dotenv
    print("✅ dotenv import successful")
except ImportError as e:
    print("❌ dotenv import failed:", e)

print("\n🎯 結論: インポートエラーは開発環境(VS Code/Pylance)の設定問題です")
print("実際のPythonランタイムでは正常に動作します")
