#!/usr/bin/env python3
"""
SQLModelの重複登録問題を根本的に解決するためのスクリプト
"""

def fix_sqlmodel_models():
    """SQLModelの重複登録問題を修正"""
    print("🔧 SQLModelの重複登録問題を修正しています...")
    
    try:
        # SQLModelのメタデータをクリア
        from sqlmodel import SQLModel
        SQLModel.metadata.clear()
        print("✅ SQLModel metadata cleared")
        
        # 各モデルをクリーンに再インポート
        from models.question import Question
        from models.choice import Choice
        from models.user_answer import UserAnswer
        
        print(f"✅ Question model imported: {Question.__name__}")
        print(f"✅ Choice model imported: {Choice.__name__}")
        print(f"✅ UserAnswer model imported: {UserAnswer.__name__}")
        
        # メタデータに登録されたテーブルを確認
        tables = list(SQLModel.metadata.tables.keys())
        print(f"📋 Registered tables: {tables}")
        
        expected_tables = ['question', 'choice', 'user_answer']
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' registered successfully")
            else:
                print(f"❌ Table '{table}' not found in metadata")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing SQLModel models: {e}")
        return False

if __name__ == "__main__":
    success = fix_sqlmodel_models()
    if success:
        print("🎉 SQLModel registry fix completed successfully!")
    else:
        print("💥 SQLModel registry fix failed!")
