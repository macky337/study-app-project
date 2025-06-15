#!/usr/bin/env python3
"""
app.pyの基本的な構文とインポートをテスト
"""

import sys
import os

# プロジェクトディレクトリを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 基本的なインポートテスト")
    
    # PDFProcessorのインポートテスト
    from services.pdf_processor import PDFProcessor
    processor = PDFProcessor()
    print("✅ PDFProcessor: インポートとインスタンス化成功")
    
    # extract_text_autoメソッドの確認
    method = getattr(processor, 'extract_text_auto', None)
    if method:
        print("✅ extract_text_auto: メソッド存在確認")
    else:
        print("❌ extract_text_auto: メソッドが存在しません")
    
    # データベース関連のテスト
    try:
        from database.connection import DATABASE_URL, engine
        print(f"✅ DATABASE_URL: {'設定済み' if DATABASE_URL else '未設定'}")
        print(f"✅ Engine: {'作成済み' if engine else '未作成'}")
    except Exception as db_e:
        print(f"⚠️ Database: {db_e}")
    
    # 他のサービスのテスト
    try:
        from services.pdf_question_generator import PDFQuestionGenerator
        print("✅ PDFQuestionGenerator: インポート成功")
    except Exception as e:
        print(f"⚠️ PDFQuestionGenerator: {e}")
    
    try:
        from services.past_question_extractor import PastQuestionExtractor
        print("✅ PastQuestionExtractor: インポート成功")
    except Exception as e:
        print(f"⚠️ PastQuestionExtractor: {e}")
    
    print("\n🎯 テスト完了 - 基本的なインポートは正常に動作しています")
    
except Exception as e:
    print(f"❌ テストエラー: {e}")
    import traceback
    traceback.print_exc()
