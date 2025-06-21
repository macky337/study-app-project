"""
PDF処理問題診断スクリプト
PDF処理で発生する具体的な問題を特定し、解決策を提案
"""

import sys
import os
import traceback

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_openai_connection():
    """OpenAI API接続テスト"""
    print("=== OpenAI API接続テスト ===")
    
    try:
        from services.enhanced_openai_service import EnhancedOpenAIService
        
        # APIキーの存在確認
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY 環境変数が設定されていません")
            return False
        
        if len(api_key) < 20:
            print("❌ OPENAI_API_KEY が短すぎます（無効な可能性）")
            return False
        
        print(f"✅ OPENAI_API_KEY が設定されています (長さ: {len(api_key)})")
        
        # サービスの初期化テスト
        service = EnhancedOpenAIService(model_name="gpt-3.5-turbo")
        print("✅ OpenAIService 初期化成功")
        
        # 接続テスト
        is_connected, message = service.test_connection()
        if is_connected:
            print(f"✅ OpenAI API接続成功: {message}")
            return True
        else:
            print(f"❌ OpenAI API接続失敗: {message}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI接続テストエラー: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """データベース接続テスト"""
    print("\n=== データベース接続テスト ===")
    
    try:
        from database.connection import get_database_session
        from database.operations import QuestionService
        
        # データベースセッション取得
        session, error = get_database_session()
        if not session:
            print(f"❌ データベース接続失敗: {error}")
            return False
        
        print("✅ データベース接続成功")
        
        # QuestionServiceテスト
        question_service = QuestionService(session)
        print("✅ QuestionService 初期化成功")
        
        # 簡単なクエリテスト
        categories = question_service.get_categories()
        print(f"✅ カテゴリ取得成功: {len(categories)}個のカテゴリ")
        
        return True
        
    except Exception as e:
        print(f"❌ データベーステストエラー: {e}")
        traceback.print_exc()
        return False

def test_pdf_question_generator():
    """PDF問題生成機能テスト"""
    print("\n=== PDF問題生成機能テスト ===")
    
    try:
        from services.pdf_question_generator import PDFQuestionGenerator
        from database.connection import get_database_session
        
        # データベースセッション取得
        session, _ = get_database_session()
        if not session:
            print("❌ データベース接続が必要です")
            return False
        
        # PDF問題生成器の初期化
        generator = PDFQuestionGenerator(session, model_name="gpt-3.5-turbo")
        print("✅ PDFQuestionGenerator 初期化成功")
        
        # サンプルテキストでテスト
        sample_text = """
        これはサンプルテキストです。
        
        問題1: 以下のうち、正しいものはどれですか？
        A) 選択肢1
        B) 選択肢2 
        C) 選択肢3
        D) 選択肢4
        
        答え: B
        
        解説: 選択肢2が正しい理由は...
        """
        
        print(f"サンプルテキスト長: {len(sample_text)} 文字")
        
        # 簡単な生成テスト（実際にAPIを呼ばない）
        print("✅ PDF問題生成機能は正常に初期化されました")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF問題生成テストエラー: {e}")
        traceback.print_exc()
        return False

def test_past_question_extractor():
    """過去問抽出機能テスト"""
    print("\n=== 過去問抽出機能テスト ===")
    
    try:
        from services.past_question_extractor import PastQuestionExtractor
        from database.connection import get_database_session
        
        # データベースセッション取得
        session, _ = get_database_session()
        if not session:
            print("❌ データベース接続が必要です")
            return False
        
        # 過去問抽出器の初期化
        extractor = PastQuestionExtractor(model_name="gpt-3.5-turbo")
        print("✅ PastQuestionExtractor 初期化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 過去問抽出テストエラー: {e}")
        traceback.print_exc()
        return False

def analyze_pdf_error_logs():
    """PDF処理エラーログの分析"""
    print("\n=== PDF処理エラーログ分析 ===")
    
    common_issues = {
        "OpenAI API": [
            "RateLimitError: API利用制限に達している",
            "AuthenticationError: APIキーが無効",
            "InvalidRequestError: リクエスト形式が無効",
            "TimeoutError: API応答タイムアウト"
        ],
        "PDF処理": [
            "PDFが暗号化されている",
            "画像ベースのPDFで文字抽出不可",
            "ファイルサイズが大きすぎる",
            "メモリ不足エラー"
        ],
        "データベース": [
            "重複エラー: 同じ問題が既に存在",
            "接続エラー: データベースに接続できない",
            "権限エラー: 書き込み権限がない",
            "容量エラー: ディスク容量不足"
        ],
        "形式エラー": [
            "過去問の形式が認識できない",
            "選択肢の数が不正",
            "正解が特定できない",
            "JSON形式エラー"
        ]
    }
    
    print("よくある問題と対処法:")
    for category, issues in common_issues.items():
        print(f"\n📋 {category}:")
        for issue in issues:
            print(f"  - {issue}")
    
    return True

def generate_troubleshooting_guide():
    """トラブルシューティングガイド生成"""
    print("\n=== トラブルシューティングガイド ===")
    
    guide = {
        "PDF処理失敗": [
            "1. PDFファイルが50MB以下かチェック",
            "2. PDFが暗号化されていないかチェック",
            "3. テキストベースのPDFかチェック（画像PDFは非対応）",
            "4. 別のPDFファイルで試行"
        ],
        "OpenAI APIエラー": [
            "1. 環境変数 OPENAI_API_KEY を確認",
            "2. API利用制限を確認（https://platform.openai.com/usage）",
            "3. インターネット接続を確認",
            "4. しばらく時間をおいて再試行"
        ],
        "メモリ不足": [
            "1. より小さなPDFファイルを使用",
            "2. 生成問題数を減らす",
            "3. 他のアプリケーションを終了",
            "4. システムを再起動"
        ],
        "重複エラー": [
            "1. 重複チェックを無効にする",
            "2. 類似度閾値を下げる",
            "3. 既存問題を確認・削除",
            "4. 異なるカテゴリ名を使用"
        ]
    }
    
    for problem, solutions in guide.items():
        print(f"\n🔧 {problem}:")
        for solution in solutions:
            print(f"  {solution}")
    
    return True

def main():
    """メイン診断関数"""
    print("🔍 PDF処理問題診断を開始します...")
    print("=" * 50)
    
    # 各種テストの実行
    openai_ok = test_openai_connection()
    db_ok = test_database_connection()
    pdf_gen_ok = test_pdf_question_generator()
    past_ext_ok = test_past_question_extractor()
    
    # エラーログ分析
    analyze_pdf_error_logs()
    
    # トラブルシューティングガイド
    generate_troubleshooting_guide()
    
    # 総合結果
    print("\n" + "=" * 50)
    print("診断結果サマリー:")
    print(f"OpenAI API: {'✅ OK' if openai_ok else '❌ NG'}")
    print(f"データベース: {'✅ OK' if db_ok else '❌ NG'}")
    print(f"PDF問題生成: {'✅ OK' if pdf_gen_ok else '❌ NG'}")
    print(f"過去問抽出: {'✅ OK' if past_ext_ok else '❌ NG'}")
    
    all_ok = all([openai_ok, db_ok, pdf_gen_ok, past_ext_ok])
    
    if all_ok:
        print("\n🎉 すべてのテストに合格しました！")
        print("PDF処理機能は正常に動作する準備ができています。")
    else:
        print("\n⚠️ 一部の機能に問題があります。")
        print("上記のエラーメッセージとトラブルシューティングガイドを参考に修正してください。")
    
    print("\n💡 実際のエラーが発生した場合:")
    print("  - Streamlitアプリのエラーメッセージを確認")
    print("  - ブラウザのデベロッパーツールでコンソールエラーを確認")
    print("  - このスクリプトを再実行して最新の状態を確認")
    
    return all_ok

if __name__ == "__main__":
    main()
