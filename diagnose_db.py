#!/usr/bin/env python3
"""
データベース接続診断ツール
"""

def diagnose_database():
    """データベース接続を診断"""
    
    print("🔍 データベース接続診断")
    print("=" * 50)
    
    # 環境変数チェック
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("📋 環境変数チェック:")
    db_vars = [
        "DATABASE_URL",
        "DATABASE_PUBLIC_URL", 
        "POSTGRES_URL",
        "OPENAI_API_KEY"
    ]
    
    for var in db_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        if value:
            # 重要な情報をマスク
            if "api" in var.lower():
                display_value = value[:10] + "..." if len(value) > 10 else value
            elif "url" in var.lower() or "database" in var.lower():
                display_value = value[:20] + "..." if len(value) > 20 else value
            else:
                display_value = value
            print(f"   {status} {var}: {display_value}")
        else:
            print(f"   {status} {var}: 未設定")
    
    # データベース接続テスト
    print(f"\n🔌 データベース接続テスト:")
    
    try:
        from database.connection import engine, DATABASE_URL
        
        if engine:
            print("✅ データベースエンジン作成成功")
            print(f"   データベースURL: {DATABASE_URL[:30]}...")
            
            # 接続テスト
            try:
                with engine.connect() as conn:
                    result = conn.execute("SELECT 1 as test")
                    test_value = result.fetchone()[0]
                    if test_value == 1:
                        print("✅ データベース接続テスト成功")
                    else:
                        print("❌ データベース接続テスト失敗")
            except Exception as e:
                print(f"❌ データベース接続エラー: {e}")
        else:
            print("❌ データベースエンジンの作成に失敗")
            
    except Exception as e:
        print(f"❌ データベースモジュールのインポートエラー: {e}")
        import traceback
        traceback.print_exc()
    
    # モデル接続テスト
    print(f"\n📊 データベースモデルテスト:")
    
    try:
        from sqlmodel import Session
        from database.operations import QuestionService
        
        with Session(engine) as session:
            question_service = QuestionService(session)
            
            # テーブル存在確認
            try:
                questions = question_service.get_all_questions()
                print(f"✅ 問題テーブルアクセス成功: {len(questions)}問")
            except Exception as e:
                print(f"❌ 問題テーブルアクセスエラー: {e}")
                
    except Exception as e:
        print(f"❌ データベース操作エラー: {e}")
    
    print(f"\n🎯 診断完了")


if __name__ == "__main__":
    diagnose_database()
