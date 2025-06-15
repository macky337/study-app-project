#!/usr/bin/env python3
"""
PDFProcessor の extract_text_auto メソッドのテスト
"""

try:
    from services.pdf_processor import PDFProcessor
    
    # インスタンスを作成
    processor = PDFProcessor()
    
    # メソッドの存在を確認
    if hasattr(processor, 'extract_text_auto'):
        print("✅ extract_text_auto メソッドが存在します")
        
        # メソッドの詳細を確認
        method = getattr(processor, 'extract_text_auto')
        print(f"メソッドの型: {type(method)}")
        print(f"メソッドのドキュメント: {method.__doc__}")
        
    else:
        print("❌ extract_text_auto メソッドが存在しません")
        print("利用可能なメソッド:")
        for attr in dir(processor):
            if not attr.startswith('_'):
                print(f"  - {attr}")
                
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
