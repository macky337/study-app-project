#!/usr/bin/env python3
"""
PDF機能のテストスクリプト
指定されたPDFファイルから問題を生成する
"""

import os
import sys
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.pdf_processor import PDFProcessor
    from services.pdf_question_generator import PDFQuestionGenerator
    from sqlmodel import Session
    from database.connection import engine
    from database.operations import QuestionService, ChoiceService
    
    def test_pdf_generation():
        """PDF問題生成のテスト"""
        
        # PDFファイルパス（テスト用）
        pdf_path = r"c:\Users\user\OneDrive\ScanSnap\202411_(タイトル).pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDFファイルが見つかりません: {pdf_path}")
            print("別のPDFファイルパスを指定してください")
            return False
        
        print(f"📄 PDFファイルを処理中: {pdf_path}")
        print(f"ファイルサイズ: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        
        # PDF処理
        processor = PDFProcessor()
        
        try:
            # ファイルを読み込み
            with open(pdf_path, 'rb') as f:
                file_bytes = f.read()
            
            print("📖 テキスト抽出中...")
            extracted_text = processor.extract_text_auto(file_bytes)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                print("❌ PDFからテキストを抽出できませんでした")
                return False
            
            print(f"✅ テキスト抽出完了")
            print(f"抽出文字数: {len(extracted_text):,}")
            print(f"推定単語数: {len(extracted_text.split()):,}")
            
            # 抽出テキストのプレビュー
            print("\n--- 抽出テキストプレビュー（最初の500文字） ---")
            print(extracted_text[:500])
            print("...\n")
            
            # データベース接続確認
            if not engine:
                print("❌ データベースに接続できません")
                return False
            
            print("🔗 データベース接続OK")
            
            # 問題生成
            with Session(engine) as session:
                generator = PDFQuestionGenerator(session)
                
                def progress_callback(message, progress):
                    print(f"進捗 {progress*100:.0f}%: {message}")
                
                print("🤖 問題生成開始...")
                generated_ids = generator.generate_questions_from_pdf(
                    text=extracted_text,
                    num_questions=3,  # テスト用に3問
                    difficulty="medium",
                    category="PDFテスト教材",
                    progress_callback=progress_callback
                )
                
                if generated_ids:
                    print(f"✅ {len(generated_ids)}問の問題を生成しました！")
                    
                    # 生成された問題の詳細表示
                    question_service = QuestionService(session)
                    choice_service = ChoiceService(session)
                    
                    for i, qid in enumerate(generated_ids):
                        print(f"\n=== 問題 {i+1} (ID: {qid}) ===")
                        
                        question = question_service.get_question_by_id(qid)
                        if question:
                            print(f"タイトル: {question.title}")
                            print(f"カテゴリ: {question.category}")
                            print(f"問題: {question.content}")
                            
                            # 選択肢表示
                            choices = choice_service.get_choices_by_question(qid)
                            print("選択肢:")
                            for j, choice in enumerate(choices):
                                correct_mark = " ✅" if choice.is_correct else ""
                                print(f"  {chr(65+j)}. {choice.content}{correct_mark}")
                            
                            if question.explanation:
                                print(f"解説: {question.explanation}")
                    
                    return True
                else:
                    print("❌ 問題生成に失敗しました")
                    return False
                    
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        print("📚 PDF問題生成テスト開始")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        success = test_pdf_generation()
        
        print("="*50)
        if success:
            print("✅ テスト完了: 問題生成に成功しました！")
            print("💡 Streamlitアプリの「🔧 問題管理」→「📄 PDF問題生成」タブで同様の機能が利用できます")
        else:
            print("❌ テスト失敗: エラーを確認してください")

except ImportError as e:
    print(f"❌ 必要なライブラリが不足しています: {e}")
    print("以下のコマンドでインストールしてください:")
    print("pip install PyPDF2 pdfplumber python-multipart sqlmodel psycopg2-binary openai streamlit")
