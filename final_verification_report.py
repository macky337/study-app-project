#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Study Quiz App - 機能検証総合レポート
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数読み込み
load_dotenv()


def check_database_connection():
    """データベース接続チェック"""
    try:
        from database.connection import get_database_session
        with get_database_session() as session:
            return True, "データベース接続成功"
    except Exception as e:
        return False, f"データベース接続エラー: {e}"


def check_ai_generation_import():
    """AI問題生成機能のインポートチェック"""
    try:
        from services.question_generator import EnhancedQuestionGenerator
        return True, "QuestionGeneratorインポート成功"
    except Exception as e:
        return False, f"QuestionGeneratorインポートエラー: {e}"


def check_pdf_generation_import():
    """PDF問題生成機能のインポートチェック"""
    try:
        from services.pdf_question_generator import PDFQuestionGenerator
        return True, "PDFQuestionGeneratorインポート成功"
    except Exception as e:
        return False, f"PDFQuestionGeneratorインポートエラー: {e}"


def check_openai_setup():
    """OpenAI設定チェック"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEYが設定されていません"
    elif len(api_key) < 20:
        return False, f"OPENAI_API_KEYが短すぎます (長さ: {len(api_key)}文字)"
    else:
        return True, f"OPENAI_API_KEY設定済み (長さ: {len(api_key)}文字)"


def check_database_data():
    """データベースのデータ確認"""
    try:
        from database.connection import get_database_session
        from database.operations import QuestionService, ChoiceService
        
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            
            # 問題数の確認
            all_questions = question_service.get_all_questions()
            question_count = len(all_questions)
            
            # カテゴリ確認
            categories = set()
            integrity_issues = 0
            
            for question in all_questions:
                categories.add(question.category)
                choices = choice_service.get_choices_by_question_id(question.id)
                
                # 整合性チェック
                if not choices:
                    integrity_issues += 1
                elif not any(choice.is_correct for choice in choices):
                    integrity_issues += 1
            
            category_count = len(categories)
            integrity_rate = ((question_count - integrity_issues) / question_count * 100) if question_count > 0 else 0
            
            return True, f"問題数: {question_count}件, カテゴリ数: {category_count}, 整合性: {integrity_rate:.1f}%"
            
    except Exception as e:
        return False, f"データベースデータ確認エラー: {e}"


def check_required_packages():
    """必要パッケージのチェック"""
    try:
        required_packages = [
            'streamlit', 'sqlmodel', 'openai', 'dotenv',
            'PyPDF2', 'pdfplumber', 'backoff', 'psycopg2'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                if package == 'psycopg2':
                    import psycopg2
                elif package == 'dotenv':
                    from dotenv import load_dotenv
                else:
                    __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return False, f"不足パッケージ: {', '.join(missing_packages)}"
        else:
            return True, f"必要パッケージ確認済み ({len(required_packages)}個)"
            
    except Exception as e:
        return False, f"パッケージチェックエラー: {e}"


def main():
    """メイン関数"""
    print("=" * 80)
    print("🔬 Study Quiz App - 機能検証総合レポート")
    print("=" * 80)
    
    checks = [
        ("🔗 データベース接続", check_database_connection),
        ("📦 必要パッケージ", check_required_packages),
        ("🤖 AI問題生成機能", check_ai_generation_import),
        ("📄 PDF問題生成機能", check_pdf_generation_import),
        ("🔑 OpenAI設定", check_openai_setup),
        ("📊 データベースデータ", check_database_data),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}を確認中...")
        try:
            success, message = check_func()
            if success:
                print(f"✅ {message}")
                results.append((name, True, message))
            else:
                print(f"❌ {message}")
                results.append((name, False, message))
        except Exception as e:
            print(f"❌ チェック実行エラー: {e}")
            results.append((name, False, f"チェック実行エラー: {e}"))
    
    # サマリー
    print("\n" + "=" * 80)
    print("📋 検証結果サマリー")
    print("=" * 80)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    for name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
    
    print(f"\n📊 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 すべての機能が正常に動作しています！")
        print("💡 Streamlit UI (http://localhost:8501) で各機能をお試しください")
    else:
        print("⚠️  一部の機能に問題があります。上記の詳細を確認してください")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
