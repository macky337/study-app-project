#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple connection test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Environment Check:")
print(f"   OPENAI_API_KEY: {'✅ Found' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
print(f"   DATABASE_URL: {'✅ Found' if os.getenv('DATABASE_URL') else '❌ Missing'}")

# Test database connection
try:
    print("\n🔗 Testing database connection...")
    from sqlmodel import create_engine, Session, SQLModel, text
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL, echo=False)
        
        with Session(engine) as session:
            result = session.exec(text("SELECT 1")).fetchone()
            print(f"✅ Database connection successful: {result}")
            
            # Check if tables exist
            tables = session.exec(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            print(f"📊 Tables found: {[t[0] for t in tables]}")
            
    else:
        print("❌ No DATABASE_URL found")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test imports
print("\n📦 Testing module imports:")
modules = [
    'streamlit',
    'openai', 
    'database.operations',
    'services.past_question_extractor',
    'models.question'
]

for module in modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {e}")

print("\n🎯 Status: Ready for final testing")
print("💡 Next: Run 'streamlit run app.py' to start the application")
