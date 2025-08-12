# -*- coding: utf-8 -*-
"""
音声ファイル分割ツール
大きな音声ファイルを小さなチャンクに分割してWhisper APIの制限に対応
"""

import os
import tempfile
import math
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
from pydub.utils import make_chunks
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioSplitter:
    """音声ファイル分割クラス"""
    
    # OpenAI Whisperの制限
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    
    # 安全マージンを考慮した推奨最大サイズ（20MB）
    RECOMMENDED_MAX_SIZE = 20 * 1024 * 1024
    
    # 分割時の重複時間（秒） - 音声の途切れを防ぐため
    OVERLAP_SECONDS = 2
    
    def __init__(self):
        """分割ツールの初期化"""
        logger.info("AudioSplitter initialized")
    
    def get_audio_info(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """音声ファイルの情報を取得"""
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}") as temp_file:
                temp_file.write(file_data)
                temp_file.flush()
                
                audio = AudioSegment.from_file(temp_file.name)
                
                return {
                    "duration_seconds": len(audio) / 1000.0,
                    "duration_minutes": len(audio) / 60000.0,
                    "file_size_mb": len(file_data) / (1024 * 1024),
                    "channels": audio.channels,
                    "frame_rate": audio.frame_rate,
                    "sample_width": audio.sample_width,
                    "format": filename.split('.')[-1].lower()
                }
        except Exception as e:
            logger.error(f"Audio info extraction error: {e}")
            raise Exception(f"音声ファイルの情報取得に失敗しました: {str(e)}")
    
    def calculate_split_strategy(self, audio_info: Dict[str, Any]) -> Dict[str, Any]:
        """分割戦略の計算"""
        file_size_mb = audio_info["file_size_mb"]
        duration_seconds = audio_info["duration_seconds"]
        
        if file_size_mb <= (self.RECOMMENDED_MAX_SIZE / (1024 * 1024)):
            return {
                "needs_splitting": False,
                "chunks_needed": 1,
                "chunk_duration_seconds": duration_seconds,
                "estimated_chunk_size_mb": file_size_mb
            }
        
        # 必要な分割数を計算
        chunks_needed = math.ceil(file_size_mb / (self.RECOMMENDED_MAX_SIZE / (1024 * 1024)))
        
        # 重複を考慮した分割時間を計算
        base_chunk_duration = duration_seconds / chunks_needed
        chunk_duration_with_overlap = base_chunk_duration + self.OVERLAP_SECONDS
        
        # 推定チャンクサイズ
        estimated_chunk_size_mb = file_size_mb / chunks_needed
        
        return {
            "needs_splitting": True,
            "chunks_needed": chunks_needed,
            "chunk_duration_seconds": base_chunk_duration,
            "chunk_duration_with_overlap": chunk_duration_with_overlap,
            "estimated_chunk_size_mb": estimated_chunk_size_mb,
            "overlap_seconds": self.OVERLAP_SECONDS
        }
    
    def split_audio_file(
        self, 
        file_data: bytes, 
        filename: str,
        chunk_duration_minutes: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """音声ファイルを分割"""
        try:
            logger.info(f"Starting audio splitting for file: {filename}")
            
            # 音声情報を取得
            audio_info = self.get_audio_info(file_data, filename)
            logger.info(f"Audio info: {audio_info}")
            
            # 分割戦略を計算
            if chunk_duration_minutes is None:
                strategy = self.calculate_split_strategy(audio_info)
            else:
                chunk_duration_seconds = chunk_duration_minutes * 60
                chunks_needed = math.ceil(audio_info["duration_seconds"] / chunk_duration_seconds)
                strategy = {
                    "needs_splitting": chunks_needed > 1,
                    "chunks_needed": chunks_needed,
                    "chunk_duration_seconds": chunk_duration_seconds,
                    "overlap_seconds": self.OVERLAP_SECONDS
                }
            
            logger.info(f"Split strategy: {strategy}")
            
            if not strategy["needs_splitting"]:
                return [{
                    "chunk_index": 0,
                    "start_time": 0,
                    "end_time": audio_info["duration_seconds"],
                    "duration": audio_info["duration_seconds"],
                    "data": file_data,
                    "filename": filename,
                    "size_mb": audio_info["file_size_mb"]
                }]
            
            # 音声ファイルを読み込み
            with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}") as temp_file:
                temp_file.write(file_data)
                temp_file.flush()
                
                audio = AudioSegment.from_file(temp_file.name)
                
                chunks = []
                chunk_duration_ms = int(strategy["chunk_duration_seconds"] * 1000)
                overlap_ms = int(strategy["overlap_seconds"] * 1000)
                
                for i in range(strategy["chunks_needed"]):
                    start_ms = i * chunk_duration_ms
                    end_ms = min((i + 1) * chunk_duration_ms + overlap_ms, len(audio))
                    
                    # 最後のチャンクの場合は重複を減らす
                    if i == strategy["chunks_needed"] - 1:
                        end_ms = len(audio)
                    
                    chunk_audio = audio[start_ms:end_ms]
                    
                    # チャンクをMP3形式で出力
                    with tempfile.NamedTemporaryFile(suffix=".mp3") as chunk_temp:
                        chunk_audio.export(chunk_temp.name, format="mp3", bitrate="128k")
                        chunk_temp.seek(0)
                        chunk_data = chunk_temp.read()
                    
                    chunk_info = {
                        "chunk_index": i,
                        "start_time": start_ms / 1000.0,
                        "end_time": end_ms / 1000.0,
                        "duration": (end_ms - start_ms) / 1000.0,
                        "data": chunk_data,
                        "filename": f"{filename.rsplit('.', 1)[0]}_chunk_{i+1:02d}.mp3",
                        "size_mb": len(chunk_data) / (1024 * 1024),
                        "has_overlap": i > 0 or i < strategy["chunks_needed"] - 1
                    }
                    
                    chunks.append(chunk_info)
                    logger.info(f"Created chunk {i+1}/{strategy['chunks_needed']}: {chunk_info['filename']} ({chunk_info['size_mb']:.2f}MB)")
                
                return chunks
                
        except Exception as e:
            logger.error(f"Audio splitting error: {e}")
            raise Exception(f"音声ファイルの分割に失敗しました: {str(e)}")
    
    def merge_transcriptions(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分割された音声の文字起こし結果をマージ"""
        try:
            if not chunk_results:
                raise ValueError("マージする結果がありません")
            
            # 成功した結果のみを抽出
            successful_results = [result for result in chunk_results if result.get("success", False)]
            
            if not successful_results:
                return {
                    "success": False,
                    "error": "すべてのチャンクの文字起こしに失敗しました"
                }
            
            # テキストをマージ
            merged_text = ""
            total_duration = 0
            all_segments = []
            current_time_offset = 0
            
            for i, result in enumerate(successful_results):
                chunk_text = result.get("text", "")
                chunk_duration = result.get("duration", 0)
                chunk_segments = result.get("segments", [])
                
                # 重複除去のための処理（簡易版）
                if i > 0 and merged_text and chunk_text:
                    # 前のチャンクの最後の文と現在のチャンクの最初の文を比較
                    last_sentences = merged_text.strip().split('。')[-2:]  # 最後の2文
                    first_sentences = chunk_text.strip().split('。')[:2]   # 最初の2文
                    
                    # 重複している可能性がある場合は調整
                    if len(last_sentences) > 0 and len(first_sentences) > 0:
                        if last_sentences[-1] in chunk_text[:100]:  # 簡易的な重複チェック
                            # 重複部分をスキップ
                            sentences = chunk_text.split('。')
                            if len(sentences) > 1:
                                chunk_text = '。'.join(sentences[1:])
                
                merged_text += (" " if merged_text else "") + chunk_text
                total_duration += chunk_duration
                
                # セグメント情報もマージ（時間オフセット調整）
                if chunk_segments:
                    for segment in chunk_segments:
                        adjusted_segment = segment.copy()
                        if 'start' in adjusted_segment:
                            adjusted_segment['start'] += current_time_offset
                        if 'end' in adjusted_segment:
                            adjusted_segment['end'] += current_time_offset
                        all_segments.append(adjusted_segment)
                
                current_time_offset += chunk_duration
            
            # 言語の決定（最も多く出現した言語）
            languages = [result.get("language", "ja") for result in successful_results]
            most_common_language = max(set(languages), key=languages.count)
            
            return {
                "success": True,
                "text": merged_text.strip(),
                "language": most_common_language,
                "duration": total_duration,
                "segments": all_segments,
                "chunks_processed": len(successful_results),
                "total_chunks": len(chunk_results),
                "merge_info": {
                    "successful_chunks": len(successful_results),
                    "failed_chunks": len(chunk_results) - len(successful_results),
                    "chunk_languages": languages
                }
            }
            
        except Exception as e:
            logger.error(f"Transcription merging error: {e}")
            return {
                "success": False,
                "error": f"文字起こし結果のマージに失敗しました: {str(e)}"
            }

# テスト用関数
def test_audio_splitter():
    """AudioSplitterのテスト"""
    try:
        splitter = AudioSplitter()
        print("✅ AudioSplitter initialized successfully")
        
        # ダミーの音声情報でテスト
        test_audio_info = {
            "duration_seconds": 3600,  # 1時間
            "file_size_mb": 100,       # 100MB
            "channels": 2,
            "frame_rate": 44100
        }
        
        strategy = splitter.calculate_split_strategy(test_audio_info)
        print(f"✅ Split strategy calculated: {strategy}")
        
        return True
    except Exception as e:
        print(f"❌ AudioSplitter test failed: {e}")
        return False

if __name__ == "__main__":
    test_audio_splitter()
