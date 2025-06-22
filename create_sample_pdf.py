#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用サンプルPDFファイル作成スクリプト
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os


def create_sample_pdf():
    """テスト用のサンプルPDFファイルを作成"""
    
    # 日本語フォントを登録
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        font_name = 'HeiseiKakuGo-W5'
    except:
        # フォントが見つからない場合はHelveticaを使用
        font_name = 'Helvetica'
        print("⚠️ 日本語フォントが見つかりません。Helveticaを使用します。")
    
    # PDFファイルを作成
    pdf_path = "sample_questions.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # タイトル
    c.setFont(font_name, 16)
    c.drawString(50, height - 50, "情報処理技術者試験 サンプル問題")
    
    # 問題1
    y_position = height - 100
    c.setFont(font_name, 12)
    c.drawString(50, y_position, "問1 コンピュータの基本構成要素として正しいものはどれか。")
    
    y_position -= 30
    c.drawString(70, y_position, "(1) CPU、メモリ、ハードディスク")
    y_position -= 20
    c.drawString(70, y_position, "(2) CPU、メモリ、入出力装置")
    y_position -= 20
    c.drawString(70, y_position, "(3) CPU、メモリ、ネットワーク")
    y_position -= 20
    c.drawString(70, y_position, "(4) CPU、キーボード、マウス")
    
    y_position -= 30
    c.drawString(50, y_position, "正解: (2)")
    y_position -= 20
    c.drawString(50, y_position, "解説: コンピュータの基本構成要素は、CPU、メモリ、入出力装置です。")
    
    # 問題2
    y_position -= 50
    c.drawString(50, y_position, "問2 OSの役割として適切でないものはどれか。")
    
    y_position -= 30
    c.drawString(70, y_position, "(1) ハードウェアの制御")
    y_position -= 20
    c.drawString(70, y_position, "(2) アプリケーションの実行管理")
    y_position -= 20
    c.drawString(70, y_position, "(3) データの暗号化")
    y_position -= 20
    c.drawString(70, y_position, "(4) メモリの管理")
    
    y_position -= 30
    c.drawString(50, y_position, "正解: (3)")
    y_position -= 20
    c.drawString(50, y_position, "解説: データの暗号化は一般的にアプリケーションが行う機能です。")
    
    # 問題3（Q形式）
    y_position -= 50
    c.drawString(50, y_position, "Q3. データベースにおけるSQLの説明として正しいものはどれか。")
    
    y_position -= 30
    c.drawString(70, y_position, "A. 構造化照会言語")
    y_position -= 20
    c.drawString(70, y_position, "B. システム制御言語")
    y_position -= 20
    c.drawString(70, y_position, "C. 手続き型言語")
    y_position -= 20
    c.drawString(70, y_position, "D. オブジェクト指向言語")
    
    y_position -= 30
    c.drawString(50, y_position, "正解: A")
    y_position -= 20
    c.drawString(50, y_position, "解説: SQLはStructured Query Languageの略で、構造化照会言語です。")
    
    # 新しいページ
    c.showPage()
    
    # 問題4（ア・イ・ウ・エ形式）
    y_position = height - 50
    c.setFont(font_name, 12)
    c.drawString(50, y_position, "4. ネットワークプロトコルに関する問題")
    
    y_position -= 30
    c.drawString(50, y_position, "HTTPSで使用される暗号化プロトコルはどれか。")
    
    y_position -= 30
    c.drawString(70, y_position, "ア. SSL/TLS")
    y_position -= 20
    c.drawString(70, y_position, "イ. FTP")
    y_position -= 20
    c.drawString(70, y_position, "ウ. SMTP")
    y_position -= 20
    c.drawString(70, y_position, "エ. DNS")
    
    y_position -= 30
    c.drawString(50, y_position, "正解: ア")
    y_position -= 20
    c.drawString(50, y_position, "解説: HTTPSではSSL/TLSプロトコルが使用されます。")
    
    # 問題5（①②③④形式）
    y_position -= 50
    c.drawString(50, y_position, "5. プログラミング言語の特徴について")
    
    y_position -= 30
    c.drawString(50, y_position, "オブジェクト指向言語の特徴はどれか。")
    
    y_position -= 30
    c.drawString(70, y_position, "① カプセル化")
    y_position -= 20
    c.drawString(70, y_position, "② 継承")
    y_position -= 20
    c.drawString(70, y_position, "③ ポリモーフィズム")
    y_position -= 20
    c.drawString(70, y_position, "④ すべて正しい")
    
    y_position -= 30
    c.drawString(50, y_position, "正解: ④")
    y_position -= 20
    c.drawString(50, y_position, "解説: オブジェクト指向言語の三大特徴は、カプセル化、継承、")
    y_position -= 15
    c.drawString(70, y_position, "ポリモーフィズムです。")
    
    # PDFを保存
    c.save()
    
    return pdf_path


def main():
    """メイン関数"""
    print("📄 テスト用サンプルPDFファイルを作成中...")
    
    try:
        pdf_path = create_sample_pdf()
        file_size = os.path.getsize(pdf_path)
        
        print(f"✅ サンプルPDFファイルを作成しました: {pdf_path}")
        print(f"📊 ファイルサイズ: {file_size / 1024:.1f} KB")
        print(f"📝 収録問題数: 5問")
        print(f"📋 問題形式: 問1形式、Q形式、ア・イ・ウ・エ形式、①②③④形式")
        print("")
        print("🚀 このファイルをStreamlitアプリでテストできます:")
        print("   1. http://localhost:8501 にアクセス")
        print("   2. 問題管理 → PDF問題生成タブ")
        print("   3. 'PDF問題抽出' を選択")
        print(f"   4. {pdf_path} をアップロード")
        
    except Exception as e:
        print(f"❌ PDFファイル作成エラー: {e}")
        print("💡 reportlabライブラリが必要です: pip install reportlab")


if __name__ == "__main__":
    main()
