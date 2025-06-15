#!/usr/bin/env python3
"""
PDF機能の詳細テスト - ローカル実行版
指定されたPDFファイルから問題を生成してテストする
"""

import os
import sys
from datetime import datetime
import tempfile

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_processing():
    """PDF処理機能のテスト"""
    print("📄 PDF処理機能のテスト開始")
    print("=" * 50)
    
    try:
        from services.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        print("✅ PDFProcessor正常にインポート")
        
        # テストPDFファイルのパス候補
        test_paths = [
            r"c:\Users\user\OneDrive\ScanSnap\202411_(タイトル).pdf",
            # 他の可能なパス
            r"c:\Users\user\Documents\test.pdf",
            r"c:\Users\user\Desktop\test.pdf"
        ]
        
        pdf_path = None
        for path in test_paths:
            if os.path.exists(path):
                pdf_path = path
                break
        
        if not pdf_path:
            print("❌ テスト用PDFファイルが見つかりません")
            print("以下のいずれかの場所にPDFファイルを配置してください:")
            for path in test_paths:
                print(f"  - {path}")
            return False
        
        print(f"📁 使用するPDFファイル: {pdf_path}")
        print(f"📊 ファイルサイズ: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        
        # ファイル検証テスト
        print("\n--- ファイル検証テスト ---")
        with open(pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        # Streamlitのupload_file形式をシミュレート
        class MockUploadedFile:
            def __init__(self, name, size):
                self.name = name
                self.size = size
        
        mock_file = MockUploadedFile(os.path.basename(pdf_path), len(file_bytes))
        is_valid, message = processor.validate_file(mock_file)
        
        if is_valid:
            print(f"✅ ファイル検証: {message}")
        else:
            print(f"❌ ファイル検証失敗: {message}")
            return False
        
        # テキスト抽出テスト
        print("\n--- テキスト抽出テスト ---")
        
        methods = [
            ("PyPDF2", processor.extract_text_pypdf2),
            ("PDFplumber", processor.extract_text_pdfplumber),
            ("Auto", processor.extract_text_auto)
        ]
        
        results = {}
        
        for method_name, method_func in methods:
            try:
                print(f"🔄 {method_name}でテキスト抽出中...")
                extracted_text = method_func(file_bytes)
                
                if extracted_text:
                    results[method_name] = {
                        'success': True,
                        'length': len(extracted_text),
                        'words': len(extracted_text.split()),
                        'preview': extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                    }
                    print(f"✅ {method_name}: {len(extracted_text):,}文字, {len(extracted_text.split()):,}語")
                else:
                    results[method_name] = {'success': False, 'error': 'テキスト抽出失敗'}
                    print(f"❌ {method_name}: テキスト抽出失敗")
                    
            except Exception as e:
                results[method_name] = {'success': False, 'error': str(e)}
                print(f"❌ {method_name}: エラー - {e}")
        
        # 最良の結果を選択
        best_method = None
        best_text = ""
        max_length = 0
        
        for method_name, result in results.items():
            if result['success'] and result['length'] > max_length:
                max_length = result['length']
                best_method = method_name
                best_text = result['preview']
        
        if best_method:
            print(f"\n🏆 最適な抽出方法: {best_method}")
            print(f"📊 抽出テキスト統計:")
            print(f"  - 文字数: {results[best_method]['length']:,}")
            print(f"  - 語数: {results[best_method]['words']:,}")
            print(f"\n📖 テキストプレビュー:")
            print("-" * 50)
            print(best_text)
            print("-" * 50)
            return True, results[best_method]
        else:
            print("❌ すべての抽出方法が失敗しました")
            return False, None
            
    except ImportError as e:
        print(f"❌ 必要なライブラリが不足: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install PyPDF2 pdfplumber")
        return False, None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_database_connection():
    """データベース接続テスト"""
    print("\n🔗 データベース接続テスト")
    print("=" * 50)
    
    try:
        from database.connection import engine, DATABASE_URL
        from sqlmodel import Session
        
        if not engine:
            print("❌ データベースエンジンが初期化されていません")
            print(f"DATABASE_URL: {DATABASE_URL or '未設定'}")
            return False
        
        with Session(engine) as session:
            # 簡単なクエリでテスト
            result = session.execute("SELECT 1 as test").fetchone()
            if result and result[0] == 1:
                print("✅ データベース接続成功")
                return True
            else:
                print("❌ データベースクエリ失敗")
                return False
                
    except ImportError as e:
        print(f"❌ データベースライブラリが不足: {e}")
        return False
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return False

def test_openai_connection():
    """OpenAI API接続テスト"""
    print("\n🤖 OpenAI API接続テスト")
    print("=" * 50)
    
    try:
        from services.enhanced_openai_service import EnhancedOpenAIService
        
        service = EnhancedOpenAIService()
        connection_status = service.validate_openai_connection()
        
        if connection_status["connected"]:
            print("✅ OpenAI API接続成功")
            print(f"📊 利用可能モデル: {connection_status.get('model', 'N/A')}")
            return True
        else:
            print(f"❌ OpenAI API接続失敗: {connection_status['message']}")
            return False
            
    except ImportError as e:
        print(f"❌ OpenAIライブラリが不足: {e}")
        return False
    except Exception as e:
        print(f"❌ OpenAI接続エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🧪 PDF機能 完全テスト")
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 各テストを実行
    tests = [
        ("PDF処理", test_pdf_processing),
        ("データベース接続", test_database_connection),
        ("OpenAI API接続", test_openai_connection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name}でエラー: {e}")
            results[test_name] = False
        
        print()  # 空行を追加
    
    # 結果サマリー
    print("📋 テスト結果サマリー")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        if isinstance(result, tuple):
            success = result[0]
        else:
            success = result
            
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name:20s}: {status}")
        
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 すべてのテストが成功しました！")
        print("💡 Streamlitアプリを起動してPDF機能を試してください:")
        print("   streamlit run app.py")
        print("   その後、問題管理 → PDF問題生成 タブで機能をテストできます")
    else:
        print("⚠️  一部のテストが失敗しました")
        print("💡 失敗したコンポーネントを確認してください:")
        
        if not results.get("データベース接続", False):
            print("   - DATABASE_URLの設定を確認")
        
        if not results.get("OpenAI API接続", False):
            print("   - OPENAI_API_KEYの設定を確認")
        
        if not results.get("PDF処理", (False, None))[0]:
            print("   - PDFファイルのパスと形式を確認")
            print("   - 必要なライブラリのインストールを確認")

if __name__ == "__main__":
    main()
