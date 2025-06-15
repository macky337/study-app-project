"""
PDF処理サービス
PDFからテキストを抽出し、問題生成用に処理する
"""

import io
import tempfile
import os
from typing import List, Dict, Optional, Tuple
import PyPDF2
import pdfplumber
import streamlit as st


class PDFProcessor:
    """PDF処理クラス"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB (Railway Hobby Plan対応)
        self.allowed_extensions = ['.pdf']
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """アップロードファイルの検証"""
        if uploaded_file is None:
            return False, "ファイルが選択されていません"
        
        # ファイルサイズチェック
        if uploaded_file.size > self.max_file_size:
            return False, f"ファイルサイズが大きすぎます (最大: {self.max_file_size // (1024*1024)}MB)"
        
        # 拡張子チェック
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in self.allowed_extensions:
            return False, f"サポートされていないファイル形式です。PDF形式のみ対応しています"
        
        return True, "OK"
    
    def extract_text_pypdf2(self, file_bytes: bytes) -> str:
        """PyPDF2を使用してテキストを抽出"""
        try:
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip()
        except Exception as e:
            st.error(f"PyPDF2でのテキスト抽出に失敗: {e}")
            return ""
    
    def extract_text_pdfplumber(self, file_bytes: bytes) -> str:
        """pdfplumberを使用してテキストを抽出（より高精度）"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
            
            text = ""
            with pdfplumber.open(tmp_file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
            
            return text.strip()
        except Exception as e:
            st.error(f"pdfplumberでのテキスト抽出に失敗: {e}")
            return ""
    
    def extract_text_auto(self, file_bytes: bytes) -> str:
        """自動選択でテキストを抽出（複数方法を試行して最適な結果を選択）"""
        results = {}
        
        # PyPDF2で試行
        try:
            pypdf2_text = self.extract_text_pypdf2(file_bytes)
            results['pypdf2'] = {
                'text': pypdf2_text,
                'length': len(pypdf2_text),
                'quality': self._assess_text_quality(pypdf2_text)
            }
        except Exception as e:
            results['pypdf2'] = {'text': '', 'length': 0, 'quality': 0, 'error': str(e)}
        
        # pdfplumberで試行
        try:
            pdfplumber_text = self.extract_text_pdfplumber(file_bytes)
            results['pdfplumber'] = {
                'text': pdfplumber_text,
                'length': len(pdfplumber_text),
                'quality': self._assess_text_quality(pdfplumber_text)
            }
        except Exception as e:
            results['pdfplumber'] = {'text': '', 'length': 0, 'quality': 0, 'error': str(e)}
        
        # 最適な結果を選択
        best_method = None
        best_score = 0
        
        for method, result in results.items():
            if 'error' not in result:
                # スコア計算: 品質 * 0.7 + 長さ正規化 * 0.3
                length_score = min(result['length'] / 1000, 1.0)  # 1000文字で正規化
                total_score = result['quality'] * 0.7 + length_score * 0.3
                
                if total_score > best_score:
                    best_score = total_score
                    best_method = method
        
        if best_method:
            return results[best_method]['text']
        else:
            # 両方失敗した場合、エラーメッセージを含む空文字列を返す
            return ""
    
    def _assess_text_quality(self, text: str) -> float:
        """テキストの品質を評価（0.0-1.0）"""
        if not text:
            return 0.0
        
        quality_score = 0.0
        
        # 基本的な文字数チェック
        if len(text) > 100:
            quality_score += 0.3
        
        # 日本語文字の存在チェック
        japanese_chars = sum(1 for char in text if ord(char) > 0x3000)
        if japanese_chars > 0:
            quality_score += 0.3
        
        # 英数字の存在チェック
        ascii_chars = sum(1 for char in text if char.isalnum())
        if ascii_chars > 0:
            quality_score += 0.2
        
        # 構造的要素の存在チェック（改行、句読点など）
        structural_chars = text.count('\n') + text.count('。') + text.count('.') + text.count('、')
        if structural_chars > 5:
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    def extract_text(self, uploaded_file) -> str:
        """PDFからテキストを抽出（複数方法を試行）"""
        file_bytes = uploaded_file.read()
        
        # まずpdfplumberで試行（より高精度）
        text = self.extract_text_pdfplumber(file_bytes)
        
        # pdfplumberで失敗した場合、PyPDF2で試行
        if not text or len(text.strip()) < 100:
            st.warning("pdfplumberでの抽出が不十分です。PyPDF2で再試行します...")
            text = self.extract_text_pypdf2(file_bytes)
        
        return text
    
    def preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        if not text:
            return ""
        
        # 基本的なクリーニング
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # 空行や短すぎる行をスキップ
            if len(line) < 3:
                continue
            # ページ番号らしき行をスキップ
            if line.isdigit() and len(line) <= 3:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def split_into_chunks(self, text: str, chunk_size: int = 3000) -> List[str]:
        """長いテキストをチャンクに分割"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def get_text_info(self, text: str) -> Dict[str, any]:
        """テキストの情報を取得"""
        if not text:
            return {
                'char_count': 0,
                'word_count': 0,
                'line_count': 0,
                'estimated_pages': 0
            }
        
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        estimated_pages = max(1, char_count // 2000)  # 大まかなページ数推定
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'line_count': line_count,
            'estimated_pages': estimated_pages
        }


def create_pdf_upload_section():
    """PDFアップロードセクションのUI"""
    st.markdown("### 📄 PDFから問題生成")
    st.markdown("PDFファイルをアップロードして、内容から自動的に問題を生成します。")
    
    # PDF処理インスタンス
    pdf_processor = PDFProcessor()
    
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "PDFファイルを選択",
        type=['pdf'],
        help="最大10MBまでのPDFファイルをアップロードできます"
    )
    
    if uploaded_file is not None:
        # ファイル検証
        is_valid, message = pdf_processor.validate_file(uploaded_file)
        
        if not is_valid:
            st.error(f"❌ {message}")
            return None, None
        
        # ファイル情報表示
        file_details = {
            "ファイル名": uploaded_file.name,
            "ファイルサイズ": f"{uploaded_file.size / 1024:.1f} KB"
        }
        
        with st.expander("📋 ファイル情報"):
            for key, value in file_details.items():
                st.text(f"{key}: {value}")
        
        # テキスト抽出
        if st.button("📖 テキストを抽出", use_container_width=True):
            with st.spinner("PDFからテキストを抽出中..."):
                extracted_text = pdf_processor.extract_text(uploaded_file)
                
                if extracted_text:
                    # テキスト前処理
                    processed_text = pdf_processor.preprocess_text(extracted_text)
                    
                    # テキスト情報
                    text_info = pdf_processor.get_text_info(processed_text)
                    
                    st.success("✅ テキスト抽出が完了しました！")
                    
                    # 情報表示
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("文字数", f"{text_info['char_count']:,}")
                    with col2:
                        st.metric("単語数", f"{text_info['word_count']:,}")
                    with col3:
                        st.metric("行数", f"{text_info['line_count']:,}")
                    with col4:
                        st.metric("推定ページ数", text_info['estimated_pages'])
                    
                    # テキストプレビュー
                    with st.expander("📄 抽出されたテキスト（プレビュー）"):
                        preview_text = processed_text[:1000] + "..." if len(processed_text) > 1000 else processed_text
                        st.text_area(
                            "テキスト内容",
                            value=preview_text,
                            height=200,
                            disabled=True
                        )
                    
                    return processed_text, text_info
                else:
                    st.error("❌ テキストの抽出に失敗しました。ファイルが破損しているか、テキストが含まれていない可能性があります。")
                    return None, None
    
    return None, None
