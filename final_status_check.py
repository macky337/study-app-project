#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終動作確認スクリプト
PDFアップロード→問題抽出→クイズ表示の流れを総合的にテスト
"""

import os
import sys
import sqlite3
from datetime import datetime

def check_database_status():
    """データベースの状態を確認"""
    print("=== DATABASE STATUS CHECK ===")
    
    db_path = "study_app.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables found: {[t[0] for t in tables]}")
        
        # 各テーブルのレコード数確認
        for table in ['questions', 'choices', 'user_answers']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📈 {table}: {count} records")
            except sqlite3.OperationalError as e:
                print(f"❌ Error checking {table}: {e}")
        
        # 選択肢がある問題の確認
        cursor.execute("""
            SELECT q.id, q.question_text, COUNT(c.id) as choice_count
            FROM questions q
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
            ORDER BY q.id DESC
            LIMIT 5
        """)
        
        print("\n📋 Recent questions with choice counts:")
        for row in cursor.fetchall():
            question_id, question_text, choice_count = row
            status = "✅" if choice_count > 0 else "❌"
            question_preview = question_text[:50] + "..." if len(question_text) > 50 else question_text
            print(f"  {status} Q{question_id}: {choice_count} choices - {question_preview}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_key_files():
    """重要なファイルの存在確認"""
    print("\n=== KEY FILES CHECK ===")
    
    key_files = [
        "app.py",
        "services/past_question_extractor.py",
        "services/enhanced_openai_service.py",
        "database/operations.py",
        "models/choice.py",
        "requirements.txt"
    ]
    
    all_files_exist = True
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND!")
            all_files_exist = False
    
    return all_files_exist

def check_environment():
    """環境変数の確認"""
    print("\n=== ENVIRONMENT CHECK ===")
    
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {'*' * 10}{openai_key[-4:]}")
    else:
        print("❌ OPENAI_API_KEY not found!")
    
    return bool(openai_key)

def test_import_modules():
    """重要なモジュールのインポートテスト"""
    print("\n=== MODULE IMPORT TEST ===")
    
    modules_to_test = [
        'streamlit',
        'openai',
        'sqlite3',
        'PyPDF2',
        'database.operations',
        'services.past_question_extractor',
        'services.enhanced_openai_service'
    ]
    
    import_success = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            import_success = False
    
    return import_success

def main():
    print(f"🔍 Final Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 各チェックを実行
    db_ok = check_database_status()
    files_ok = check_key_files()
    env_ok = check_environment()
    import_ok = test_import_modules()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL SUMMARY:")
    print(f"   Database Status: {'✅ OK' if db_ok else '❌ ERROR'}")
    print(f"   Key Files: {'✅ OK' if files_ok else '❌ ERROR'}")
    print(f"   Environment: {'✅ OK' if env_ok else '❌ ERROR'}")
    print(f"   Module Imports: {'✅ OK' if import_ok else '❌ ERROR'}")
    
    overall_status = all([db_ok, files_ok, env_ok, import_ok])
    if overall_status:
        print("\n🎉 All checks passed! Ready for final testing.")
        print("💡 Next steps:")
        print("   1. Run: streamlit run app.py")
        print("   2. Upload a PDF file")
        print("   3. Extract questions")
        print("   4. Take the quiz")
    else:
        print("\n⚠️ Some issues found. Please resolve them before testing.")
    
    return overall_status

if __name__ == "__main__":
    main()
