#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick database setup and test script
"""

import os
import sys

# 現在のディレクトリを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """データベース接続とデータ確認"""
    try:
        from database.connection import engine
        from database.operations import QuestionService
        from sqlmodel import Session
        
        print("🔍 Checking database connection...")
        
        if not engine:
            print("❌ Database engine not available")
            return False
        
        with Session(engine) as session:
            question_service = QuestionService(session)
            questions = question_service.get_random_questions(limit=5)
            
            print(f"📊 Found {len(questions)} questions in database")
            
            if questions:
                print("📝 Sample questions:")
                for i, q in enumerate(questions[:3]):
                    print(f"  {i+1}. {q.title} ({q.category}, {q.difficulty})")
                return True
            else:
                print("⚠️ No questions found in database")
                return False
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def create_quick_sample():
    """クイックサンプルデータの作成"""
    try:
        from database.connection import engine, create_tables
        from database.operations import QuestionService, ChoiceService
        from sqlmodel import Session
        
        print("🔧 Creating tables...")
        create_tables()
        
        print("📝 Creating sample questions...")
        
        with Session(engine) as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            
            # サンプル問題1
            q1 = question_service.create_question(
                title="プログラミング基礎 - 変数",
                content="Pythonで変数xに数値10を代入する正しい記述はどれですか？",
                category="プログラミング基礎",
                explanation="Pythonでは「変数名 = 値」の形式で代入を行います。",
                difficulty="easy"
            )
            
            choice_service.create_choice(q1.id, "x = 10", True, 1)
            choice_service.create_choice(q1.id, "x == 10", False, 2)
            choice_service.create_choice(q1.id, "x := 10", False, 3)
            choice_service.create_choice(q1.id, "10 = x", False, 4)
            
            # サンプル問題2
            q2 = question_service.create_question(
                title="基本情報技術者 - データベース",
                content="関係データベースにおいて、テーブル間の関連を定義するために使用されるものはどれですか？",
                category="基本情報技術者",
                explanation="外部キーは、他のテーブルの主キーを参照して、テーブル間の関連を定義します。",
                difficulty="medium"
            )
            
            choice_service.create_choice(q2.id, "主キー", False, 1)
            choice_service.create_choice(q2.id, "外部キー", True, 2)
            choice_service.create_choice(q2.id, "インデックス", False, 3)
            choice_service.create_choice(q2.id, "ビュー", False, 4)
            
            # サンプル問題3
            q3 = question_service.create_question(
                title="ネットワーク - TCP/IP",
                content="インターネットで使用される基本的なプロトコルスイートは何ですか？",
                category="ネットワーク",
                explanation="TCP/IPは、インターネットで使用される基本的なプロトコルスイートです。",
                difficulty="easy"
            )
            
            choice_service.create_choice(q3.id, "HTTP", False, 1)
            choice_service.create_choice(q3.id, "FTP", False, 2)
            choice_service.create_choice(q3.id, "TCP/IP", True, 3)
            choice_service.create_choice(q3.id, "SMTP", False, 4)
            
            print(f"✅ Created 3 sample questions successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def main():
    """メイン実行"""
    print("🎯 Quick Database Setup")
    print("=" * 40)
    
    # 1. データベーステスト
    if test_database():
        print("✅ Database has questions - ready to use!")
    else:
        print("⚠️ Database empty - creating sample data...")
        
        # 2. サンプルデータ作成
        if create_quick_sample():
            print("\n🔍 Testing again...")
            if test_database():
                print("✅ Sample data created successfully!")
            else:
                print("❌ Still no data found")
        else:
            print("❌ Failed to create sample data")
    
    print("\n" + "=" * 40)
    print("🚀 Ready to run: streamlit run app.py")

if __name__ == "__main__":
    main()
