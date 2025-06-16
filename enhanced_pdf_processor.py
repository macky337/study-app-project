"""
PDF処理エラー修正パッチ
主要なPDF処理エラーを修正し、安定性を向上させる
"""

import io
import tempfile
import os
from typing import List, Dict, Optional, Tuple
import PyPDF2
import pdfplumber
import streamlit as st
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedPDFProcessor:
    """改良されたPDF処理クラス - エラーハンドリング強化版"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB (Railway Hobby Plan対応)
        self.allowed_extensions = ['.pdf']
        self.max_pages = 100  # 最大処理ページ数制限
        
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """強化されたファイル検証"""
        try:
            if uploaded_file is None:
                return False, "ファイルが選択されていません"
            
            # ファイルサイズチェック
            if uploaded_file.size > self.max_file_size:
                return False, f"ファイルサイズが大きすぎます (最大: {self.max_file_size // (1024*1024)}MB)"
            
            # 最小ファイルサイズチェック
            if uploaded_file.size < 100:
                return False, "ファイルが小さすぎます。有効なPDFファイルを選択してください"
            
            # 拡張子チェック
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension not in self.allowed_extensions:
                return False, f"サポートされていないファイル形式です。PDF形式のみ対応しています"
            
            # ファイル名の基本チェック
            if not uploaded_file.name or len(uploaded_file.name.strip()) == 0:
                return False, "無効なファイル名です"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"ファイル検証エラー: {e}")
            return False, f"ファイル検証中にエラーが発生しました: {str(e)}"
    
    def safe_file_read(self, uploaded_file) -> Tuple[bool, bytes, str]:
        """安全なファイル読み込み"""
        try:
            # ファイルポインタを先頭に戻す
            uploaded_file.seek(0)
            
            # ファイルを読み込み
            file_bytes = uploaded_file.read()
            
            # 読み込み結果の検証
            if not file_bytes:
                return False, b'', "ファイルの読み込みに失敗しました（空のファイル）"
            
            if len(file_bytes) != uploaded_file.size:
                return False, b'', f"ファイルサイズが一致しません（期待: {uploaded_file.size}, 実際: {len(file_bytes)}）"
            
            # PDFファイルの基本的なマジックナンバーチェック
            if not file_bytes.startswith(b'%PDF-'):
                return False, b'', "有効なPDFファイルではありません（PDFヘッダーが見つかりません）"
            
            return True, file_bytes, "OK"
            
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {e}")
            return False, b'', f"ファイル読み込み中にエラーが発生しました: {str(e)}"
    
    def extract_text_pypdf2_safe(self, file_bytes: bytes) -> Tuple[bool, str, str]:
        """安全なPyPDF2テキスト抽出"""
        try:
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # PDFの基本情報チェック
            if not pdf_reader.pages:
                return False, "", "PDFにページが見つかりません"
            
            num_pages = len(pdf_reader.pages)
            if num_pages > self.max_pages:
                return False, "", f"ページ数が多すぎます（最大: {self.max_pages}ページ, 実際: {num_pages}ページ）"
            
            # 暗号化チェック
            if pdf_reader.is_encrypted:
                return False, "", "暗号化されたPDFは対応していません"
            
            text = ""
            processed_pages = 0
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    processed_pages += 1
                    
                    # 進捗チェック（大きなファイル対応）
                    if processed_pages % 10 == 0:
                        logger.info(f"PyPDF2: {processed_pages}/{num_pages} ページ処理完了")
                        
                except Exception as page_error:
                    logger.warning(f"PyPDF2: ページ {i+1} の処理中にエラー: {page_error}")
                    continue
            
            extracted_text = text.strip()
            
            if not extracted_text:
                return False, "", "テキストを抽出できませんでした（画像ベースのPDFの可能性）"
            
            return True, extracted_text, "OK"
            
        except Exception as e:
            logger.error(f"PyPDF2テキスト抽出エラー: {e}")
            return False, "", f"PyPDF2でのテキスト抽出に失敗: {str(e)}"
    
    def extract_text_pdfplumber_safe(self, file_bytes: bytes) -> Tuple[bool, str, str]:
        """安全なpdfplumberテキスト抽出"""
        temp_file_path = None
        try:
            # 一時ファイル作成
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_bytes)
                temp_file_path = tmp_file.name
            
            # ファイルが正常に作成されたか確認
            if not os.path.exists(temp_file_path):
                return False, "", "一時ファイルの作成に失敗しました"
            
            text = ""
            processed_pages = 0
            
            with pdfplumber.open(temp_file_path) as pdf:
                # PDFの基本情報チェック
                if not pdf.pages:
                    return False, "", "PDFにページが見つかりません"
                
                num_pages = len(pdf.pages)
                if num_pages > self.max_pages:
                    return False, "", f"ページ数が多すぎます（最大: {self.max_pages}ページ, 実際: {num_pages}ページ）"
                
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        processed_pages += 1
                        
                        # 進捗チェック
                        if processed_pages % 10 == 0:
                            logger.info(f"pdfplumber: {processed_pages}/{num_pages} ページ処理完了")
                            
                    except Exception as page_error:
                        logger.warning(f"pdfplumber: ページ {i+1} の処理中にエラー: {page_error}")
                        continue
            
            extracted_text = text.strip()
            
            if not extracted_text:
                return False, "", "テキストを抽出できませんでした（画像ベースのPDFの可能性）"
            
            return True, extracted_text, "OK"
            
        except Exception as e:
            logger.error(f"pdfplumberテキスト抽出エラー: {e}")
            return False, "", f"pdfplumberでのテキスト抽出に失敗: {str(e)}"
        finally:
            # 一時ファイルの確実な削除
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"一時ファイルを削除しました: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"一時ファイルの削除に失敗: {cleanup_error}")
    
    def extract_text_with_fallback(self, file_bytes: bytes) -> Tuple[bool, str, str, Dict]:
        """フォールバック機能付きテキスト抽出"""
        results = {
            'methods_tried': [],
            'errors': [],
            'success_method': None,
            'text_quality': 0
        }
        
        # 方法1: pdfplumberで試行（通常はより高精度）
        success, text, message = self.extract_text_pdfplumber_safe(file_bytes)
        results['methods_tried'].append('pdfplumber')
        
        if success and text:
            quality = self._assess_text_quality(text)
            results['success_method'] = 'pdfplumber'
            results['text_quality'] = quality
            
            # 品質が十分であれば終了
            if quality > 0.5:
                return True, text, "pdfplumberで高品質抽出成功", results
        else:
            results['errors'].append(f"pdfplumber: {message}")
        
        # 方法2: PyPDF2で試行
        success2, text2, message2 = self.extract_text_pypdf2_safe(file_bytes)
        results['methods_tried'].append('pypdf2')
        
        if success2 and text2:
            quality2 = self._assess_text_quality(text2)
            
            # 既存の結果と比較
            if quality2 > results['text_quality']:
                results['success_method'] = 'pypdf2'
                results['text_quality'] = quality2
                return True, text2, "PyPDF2で高品質抽出成功", results
            elif results['success_method'] is None:
                results['success_method'] = 'pypdf2'
                results['text_quality'] = quality2
                return True, text2, "PyPDF2で抽出成功", results
        else:
            results['errors'].append(f"pypdf2: {message2}")
        
        # 両方失敗した場合
        if results['success_method'] is None:
            combined_errors = "; ".join(results['errors'])
            return False, "", f"すべての抽出方法が失敗: {combined_errors}", results
        
        # 品質の低い結果でも何らかの抽出に成功した場合
        return True, text if results['success_method'] == 'pdfplumber' else text2, f"{results['success_method']}で低品質抽出", results
    
    def _assess_text_quality(self, text: str) -> float:
        """テキストの品質評価（改良版）"""
        if not text:
            return 0.0
        
        quality_score = 0.0
        
        # 基本的な長さチェック
        if len(text) > 100:
            quality_score += 0.2
        if len(text) > 500:
            quality_score += 0.1
        if len(text) > 1000:
            quality_score += 0.1
        
        # 文字種の多様性チェック
        japanese_chars = sum(1 for char in text if ord(char) > 0x3000)
        if japanese_chars > 0:
            quality_score += 0.2
        
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 256)
        if english_chars > 0:
            quality_score += 0.1
        
        # 構造的要素のチェック
        structural_score = 0
        structural_score += min(text.count('\n') / 10, 0.1)  # 改行
        structural_score += min(text.count('。') / 5, 0.1)   # 句点
        structural_score += min(text.count('.') / 5, 0.05)   # ピリオド
        structural_score += min(text.count('、') / 10, 0.05)  # 読点
        
        quality_score += structural_score
        
        # 無意味な文字の割合チェック（品質を下げる）
        meaningless_chars = sum(1 for char in text if char in '□■◇◆○●△▲▽▼')
        if meaningless_chars > len(text) * 0.1:
            quality_score -= 0.2
        
        return min(quality_score, 1.0)
    
    def process_pdf_safely(self, uploaded_file):
        """安全なPDF処理の統合メソッド"""
        results = {
            'success': False,
            'text': '',
            'error_message': '',
            'file_info': {},
            'extraction_info': {},
            'warnings': []
        }
        
        try:
            # ステップ1: ファイル検証
            is_valid, validation_message = self.validate_file(uploaded_file)
            if not is_valid:
                results['error_message'] = f"ファイル検証失敗: {validation_message}"
                return results
            
            # ファイル情報の記録
            results['file_info'] = {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'size_mb': round(uploaded_file.size / (1024 * 1024), 2)
            }
            
            # ステップ2: ファイル読み込み
            read_success, file_bytes, read_message = self.safe_file_read(uploaded_file)
            if not read_success:
                results['error_message'] = f"ファイル読み込み失敗: {read_message}"
                return results
            
            # ステップ3: テキスト抽出
            extract_success, extracted_text, extract_message, extraction_details = self.extract_text_with_fallback(file_bytes)
            
            results['extraction_info'] = extraction_details
            
            if not extract_success:
                results['error_message'] = f"テキスト抽出失敗: {extract_message}"
                return results
            
            # ステップ4: テキストの後処理
            processed_text = self.preprocess_text(extracted_text)
            
            # 最終的な品質チェック
            final_quality = self._assess_text_quality(processed_text)
            if final_quality < 0.1:
                results['warnings'].append("抽出されたテキストの品質が低い可能性があります")
            
            # 成功時の結果設定
            results['success'] = True
            results['text'] = processed_text
            results['error_message'] = extract_message
            results['extraction_info']['final_quality'] = final_quality
            results['extraction_info']['char_count'] = len(processed_text)
            results['extraction_info']['word_count'] = len(processed_text.split())
            
            return results
            
        except Exception as e:
            logger.error(f"PDF処理中の予期しないエラー: {e}")
            results['error_message'] = f"処理中にエラーが発生しました: {str(e)}"
            return results
    
    def preprocess_text(self, text: str) -> str:
        """テキストの前処理（改良版）"""
        if not text:
            return ""
        
        # 基本的なクリーニング
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 空行や短すぎる行をスキップ
            if len(line) < 2:
                continue
                
            # ページ番号らしき行をスキップ
            if line.isdigit() and len(line) <= 3:
                continue
                
            # ヘッダー・フッターらしき行をスキップ
            if len(line) < 10 and (line.startswith('第') or line.endswith('章') or line.endswith('節')):
                continue
            
            cleaned_lines.append(line)
        
        # 結合
        result = '\n'.join(cleaned_lines)
        
        # 過度な空白の削除
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)  # 3つ以上の改行を2つに
        result = re.sub(r' {2,}', ' ', result)      # 2つ以上のスペースを1つに
        
        return result.strip()


# 使用例とテスト関数
def test_enhanced_pdf_processor():
    """改良されたPDF処理のテスト"""
    processor = EnhancedPDFProcessor()
    
    # ダミーファイルでのテスト
    class MockFile:
        def __init__(self, name, size, content=b'%PDF-1.4\ntest content'):
            self.name = name
            self.size = size
            self._content = content
            self._position = 0
        
        def read(self):
            return self._content
        
        def seek(self, position):
            self._position = position
    
    # テスト実行
    test_file = MockFile("test.pdf", 1024)
    is_valid, message = processor.validate_file(test_file)
    
    print(f"ファイル検証: {'✅' if is_valid else '❌'} {message}")
    
    return processor

if __name__ == "__main__":
    # テスト実行
    test_enhanced_pdf_processor()
    print("Enhanced PDF Processor テスト完了")
