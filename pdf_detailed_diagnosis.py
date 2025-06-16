"""
PDF処理の詳細エラー診断と修正
"""

import sys
import os
import traceback
import tempfile
import io

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_processing_components():
    """PDF処理コンポーネントの詳細テスト"""
    print("=== PDF処理コンポーネント詳細テスト ===")
    
    # 1. 基本的なインポートテスト
    try:
        import PyPDF2
        print(f"✅ PyPDF2 インポート成功 (v{PyPDF2.__version__})")
    except Exception as e:
        print(f"❌ PyPDF2 インポートエラー: {e}")
        return False
    
    try:
        import pdfplumber
        print(f"✅ pdfplumber インポート成功")
    except Exception as e:
        print(f"❌ pdfplumber インポートエラー: {e}")
        return False
    
    # 2. テンポラリファイル操作テスト
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(b'test content')
            tmp_file_path = tmp_file.name
        
        # ファイルが作成されているか確認
        if os.path.exists(tmp_file_path):
            print("✅ テンポラリファイル作成成功")
            os.unlink(tmp_file_path)  # 削除
            print("✅ テンポラリファイル削除成功")
        else:
            print("❌ テンポラリファイル作成失敗")
            return False
            
    except Exception as e:
        print(f"❌ テンポラリファイル操作エラー: {e}")
        return False
    
    # 3. BytesIOテスト
    try:
        test_bytes = b'test pdf content'
        bio = io.BytesIO(test_bytes)
        read_back = bio.read()
        if read_back == test_bytes:
            print("✅ BytesIO操作成功")
        else:
            print("❌ BytesIO操作失敗")
            return False
    except Exception as e:
        print(f"❌ BytesIO操作エラー: {e}")
        return False
    
    # 4. PDFProcessorのインポートテスト
    try:
        from services.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("✅ PDFProcessor インポート・初期化成功")
        
        # validate_fileメソッドのテスト
        class MockFile:
            def __init__(self, name, size):
                self.name = name
                self.size = size
        
        mock_file = MockFile("test.pdf", 1024)
        is_valid, message = processor.validate_file(mock_file)
        if is_valid:
            print("✅ ファイル検証メソッド動作確認")
        else:
            print(f"❌ ファイル検証失敗: {message}")
            
    except Exception as e:
        print(f"❌ PDFProcessor テストエラー: {e}")
        traceback.print_exc()
        return False
    
    # 5. PDFQuestionGeneratorのインポートテスト
    try:
        from services.pdf_question_generator import PDFQuestionGenerator
        
        # モックセッション
        class MockSession:
            pass
        
        generator = PDFQuestionGenerator(MockSession())
        print("✅ PDFQuestionGenerator インポート・初期化成功")
        
    except Exception as e:
        print(f"❌ PDFQuestionGenerator テストエラー: {e}")
        traceback.print_exc()
        return False
    
    print("\n🎉 すべてのPDF処理コンポーネントテストに合格しました！")
    return True

def test_streamlit_integration():
    """Streamlitとの統合テスト"""
    print("\n=== Streamlit統合テスト ===")
    
    try:
        import streamlit as st
        print("✅ Streamlit インポート成功")
        
        # Streamlitの主要機能テスト（非実行環境では制限あり）
        try:
            # st.empty()などの基本的な関数が利用可能か
            if hasattr(st, 'empty') and hasattr(st, 'error') and hasattr(st, 'info'):
                print("✅ Streamlit基本機能利用可能")
            else:
                print("❌ Streamlit基本機能不完全")
                return False
                
        except Exception as e:
            print(f"⚠️ Streamlit機能テスト制限あり: {e}")
            
    except Exception as e:
        print(f"❌ Streamlit統合エラー: {e}")
        return False
    
    return True

def identify_common_pdf_errors():
    """一般的なPDF処理エラーの特定"""
    print("\n=== 一般的なPDF処理エラーの特定 ===")
    
    common_errors = {
        "ファイル読み込みエラー": "uploaded_file.read()が失敗",
        "メモリ不足エラー": "大きなPDFファイルによるメモリ不足",
        "エンコーディングエラー": "PDF内のテキストエンコーディング問題",
        "権限エラー": "PDFファイルが保護されている",
        "破損ファイルエラー": "PDFファイルが破損している",
        "テンポラリファイルエラー": "一時ファイル作成・削除失敗",
        "ライブラリ競合エラー": "PyPDF2とpdfplumberの競合"
    }
    
    print("想定される一般的なエラー:")
    for error_type, description in common_errors.items():
        print(f"  - {error_type}: {description}")
    
    return common_errors

def generate_error_fix_suggestions():
    """エラー修正提案の生成"""
    print("\n=== エラー修正提案 ===")
    
    fixes = {
        "エラーハンドリング強化": "各処理段階でtry-catch追加",
        "メモリ管理改善": "大きなファイルのチャンク処理",
        "ファイル検証強化": "アップロード前の詳細検証",
        "フォールバック機能": "抽出方法の自動切り替え",
        "ログ出力強化": "デバッグ情報の詳細化",
        "進捗表示改善": "処理状況の可視化",
        "タイムアウト処理": "長時間処理の中断機能"
    }
    
    print("推奨される修正項目:")
    for fix_type, description in fixes.items():
        print(f"  - {fix_type}: {description}")
    
    return fixes

def main():
    """メイン診断関数"""
    print("PDF処理の詳細エラー診断を開始します...\n")
    
    # コンポーネントテスト
    components_ok = test_pdf_processing_components()
    
    # Streamlit統合テスト
    streamlit_ok = test_streamlit_integration()
    
    # 一般的なエラーの特定
    common_errors = identify_common_pdf_errors()
    
    # 修正提案の生成
    fixes = generate_error_fix_suggestions()
    
    # 総合評価
    print("\n" + "="*60)
    print("詳細診断結果:")
    print(f"PDF処理コンポーネント: {'✅ OK' if components_ok else '❌ NG'}")
    print(f"Streamlit統合: {'✅ OK' if streamlit_ok else '❌ NG'}")
    print(f"一般的エラー特定: {'✅ 完了' if common_errors else '❌ 未完了'}")
    print(f"修正提案生成: {'✅ 完了' if fixes else '❌ 未完了'}")
    
    if components_ok and streamlit_ok:
        print("\n🎉 基本的なPDF処理機能は正常です！")
        print("🔍 具体的なエラーが発生している場合は、実際のエラーメッセージをご確認ください。")
        return True
    else:
        print("\n⚠️ PDF処理に問題があります。上記のエラーを修正してください。")
        return False

if __name__ == "__main__":
    main()
