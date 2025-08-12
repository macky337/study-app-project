# -*- coding: utf-8 -*-
"""
音声ファイル処理と文字起こしサービス
OpenAI Whisper APIを使用した音声認識機能
"""

import os
import tempfile
import json
from typing import Dict, Optional, List, Any
from openai import OpenAI
from dotenv import load_dotenv
import logging

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

# 音声分割ツールのインポート
try:
    from .audio_splitter import AudioSplitter
    SPLITTER_AVAILABLE = True
except ImportError:
    try:
        from audio_splitter import AudioSplitter
        SPLITTER_AVAILABLE = True
    except ImportError:
        SPLITTER_AVAILABLE = False
        AudioSplitter = None

# Load environment variables
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioService:
    """音声ファイル処理と文字起こしサービス"""
    
    # サポートする音声ファイル形式
    SUPPORTED_FORMATS = [
        'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'
    ]
    
    # 最大ファイルサイズ（25MB - OpenAI Whisperの制限）
    MAX_FILE_SIZE = 25 * 1024 * 1024
    
    def __init__(self):
        """サービスの初期化"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # 音声分割ツールの初期化
        if SPLITTER_AVAILABLE and AudioSplitter is not None:
            self.splitter = AudioSplitter()
            logger.info("AudioSplitter initialized")
        else:
            self.splitter = None
            logger.warning("AudioSplitter not available - large file processing will be limited")
        
        logger.info("AudioService initialized successfully")
    
    def validate_audio_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """音声ファイルの検証"""
        try:
            # ファイルサイズチェック
            if len(file_data) > self.MAX_FILE_SIZE:
                return {
                    "valid": False,
                    "error": f"ファイルサイズが大きすぎます。最大{self.MAX_FILE_SIZE // (1024*1024)}MBまでです。"
                }
            
            # ファイル拡張子チェック
            file_extension = filename.lower().split('.')[-1]
            if file_extension not in self.SUPPORTED_FORMATS:
                return {
                    "valid": False,
                    "error": f"サポートされていないファイル形式です。対応形式: {', '.join(self.SUPPORTED_FORMATS)}"
                }
            
            return {
                "valid": True,
                "size": len(file_data),
                "format": file_extension
            }
            
        except Exception as e:
            logger.error(f"Audio file validation error: {e}")
            return {
                "valid": False,
                "error": f"ファイル検証中にエラーが発生しました: {str(e)}"
            }
    
    def convert_to_supported_format(self, file_data: bytes, original_format: str) -> bytes:
        """音声ファイルをサポート形式に変換"""
        if not PYDUB_AVAILABLE:
            raise Exception("pydubライブラリがインストールされていません。音声変換機能は利用できません。")
            
        try:
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(suffix=f".{original_format}") as temp_input:
                temp_input.write(file_data)
                temp_input.flush()
                
                # AudioSegmentで読み込み
                if AudioSegment is not None:
                    audio = AudioSegment.from_file(temp_input.name)
                    
                    # MP3形式で出力
                    with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_output:
                        audio.export(temp_output.name, format="mp3")
                        temp_output.seek(0)
                        return temp_output.read()
                else:
                    raise Exception("AudioSegmentが利用できません")
                    
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            raise Exception(f"音声ファイルの変換に失敗しました: {str(e)}")
    
    def get_audio_info(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """音声ファイルの詳細情報を取得（フォールバック対応）"""
        try:
            if self.splitter:
                try:
                    return self.splitter.get_audio_info(file_data, filename)
                except Exception as e:
                    # ffmpegが利用できない場合のフォールバック
                    logger.warning(f"Advanced audio info extraction failed: {e}")
                    return self._get_basic_audio_info(file_data, filename)
            else:
                return self._get_basic_audio_info(file_data, filename)
        except Exception as e:
            logger.error(f"Audio info extraction error: {e}")
            return {
                "error": f"音声情報の取得に失敗しました: {str(e)}",
                "file_size_mb": len(file_data) / (1024 * 1024),
                "format": filename.split('.')[-1].lower()
            }
    
    def _get_basic_audio_info(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """基本的な音声情報のみを返す（ffmpeg不要）"""
        file_size_mb = len(file_data) / (1024 * 1024)
        file_format = filename.split('.')[-1].lower()
        
        # ファイルサイズから大まかな音声時間を推定（目安のみ）
        # MP3の場合、約1MB = 1分程度（128kbps想定）
        estimated_duration_minutes = file_size_mb * 1.0  # 大まかな推定
        
        return {
            "file_size_mb": file_size_mb,
            "format": file_format,
            "duration_minutes": estimated_duration_minutes,
            "duration_seconds": estimated_duration_minutes * 60,
            "channels": 2,  # 推定値
            "frame_rate": 44100,  # 推定値
            "note": "ffmpegがインストールされていないため推定値を表示しています"
        }
    
    def transcribe_audio(
        self, 
        file_data: bytes, 
        filename: str,
        language: str = "ja",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """音声ファイルを文字起こし（大きなファイルは自動分割）"""
        try:
            logger.info(f"Starting transcription for file: {filename}")
            
            # ファイル検証
            validation = self.validate_audio_file(file_data, filename)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # ファイルサイズが制限を超える場合は分割処理
            if len(file_data) > self.MAX_FILE_SIZE:
                return self._transcribe_large_audio(file_data, filename, language, prompt)
            
            # 通常サイズのファイルの処理
            return self._transcribe_single_audio(file_data, filename, language, prompt)
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "success": False,
                "error": f"文字起こし中にエラーが発生しました: {str(e)}"
            }
    
    def _transcribe_single_audio(
        self, 
        file_data: bytes, 
        filename: str,
        language: str = "ja",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """単一音声ファイルの文字起こし"""
        try:
            # ファイル検証
            validation = self.validate_audio_file(file_data, filename)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # 一時ファイルを作成してWhisper APIに送信
            with tempfile.NamedTemporaryFile(suffix=f".{validation['format']}") as temp_file:
                temp_file.write(file_data)
                temp_file.flush()
                
                # OpenAI Whisper APIで文字起こし
                with open(temp_file.name, "rb") as audio_file:
                    # プロンプトがNoneの場合は含めない
                    kwargs = {
                        "model": "whisper-1",
                        "file": audio_file,
                        "language": language,
                        "response_format": "verbose_json",
                        "extra_headers": {"X-OpenAI-Skip-Training": "true"}
                    }
                    if prompt is not None:
                        kwargs["prompt"] = prompt
                    
                    transcript = self.client.audio.transcriptions.create(**kwargs)
                
                logger.info("プライバシー保護: OpenAI学習無効化ヘッダー送信完了 (Whisper API)")
                
                # segmentsが存在する場合は辞書形式に変換
                segments_dict = None
                if hasattr(transcript, 'segments') and transcript.segments:
                    segments_dict = []
                    for segment in transcript.segments:
                        segment_dict = {
                            "id": getattr(segment, 'id', None),
                            "start": getattr(segment, 'start', None),
                            "end": getattr(segment, 'end', None),
                            "text": getattr(segment, 'text', ''),
                            "tokens": getattr(segment, 'tokens', None),
                            "temperature": getattr(segment, 'temperature', None),
                            "avg_logprob": getattr(segment, 'avg_logprob', None),
                            "compression_ratio": getattr(segment, 'compression_ratio', None),
                            "no_speech_prob": getattr(segment, 'no_speech_prob', None)
                        }
                        segments_dict.append(segment_dict)
                
                return {
                    "success": True,
                    "text": transcript.text,
                    "language": getattr(transcript, 'language', 'ja'),
                    "duration": getattr(transcript, 'duration', None),
                    "segments": segments_dict,
                    "processing_method": "single_file"
                }
                
        except Exception as e:
            logger.error(f"Single audio transcription error: {e}")
            return {
                "success": False,
                "error": f"音声ファイルの文字起こしに失敗しました: {str(e)}"
            }
    
    def _transcribe_large_audio(
        self, 
        file_data: bytes, 
        filename: str,
        language: str = "ja",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """大きな音声ファイルの分割文字起こし（フォールバック対応）"""
        try:
            if not self.splitter:
                return {
                    "success": False,
                    "error": "音声分割機能が利用できません。大きなファイルは処理できません。"
                }
            
            logger.info(f"Large file detected ({len(file_data) / (1024*1024):.2f}MB). Starting split processing.")
            
            try:
                # 音声ファイルを分割
                chunks = self.splitter.split_audio_file(file_data, filename)
                logger.info(f"Audio split into {len(chunks)} chunks")
            except Exception as split_error:
                logger.warning(f"Advanced splitting failed: {split_error}")
                # フォールバック: 時間ベースの簡易分割
                return self._simple_time_based_split(file_data, filename, language, prompt)
            
            # 各チャンクを文字起こし
            chunk_results = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk['filename']}")
                
                chunk_result = self._transcribe_single_audio(
                    chunk["data"], 
                    chunk["filename"], 
                    language, 
                    prompt
                )
                
                # チャンク情報を追加
                chunk_result["chunk_info"] = {
                    "index": chunk["chunk_index"],
                    "start_time": chunk["start_time"],
                    "end_time": chunk["end_time"],
                    "duration": chunk["duration"],
                    "filename": chunk["filename"]
                }
                
                chunk_results.append(chunk_result)
                
                if chunk_result["success"]:
                    logger.info(f"Chunk {i+1} transcribed successfully")
                else:
                    logger.warning(f"Chunk {i+1} transcription failed: {chunk_result.get('error', 'Unknown error')}")
            
            # 結果をマージ
            merged_result = self.splitter.merge_transcriptions(chunk_results)
            
            if merged_result["success"]:
                merged_result["processing_method"] = "split_and_merge"
                merged_result["chunk_details"] = chunk_results
                logger.info(f"Large file transcription completed. Processed {merged_result['chunks_processed']}/{merged_result['total_chunks']} chunks successfully.")
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Large audio transcription error: {e}")
            return {
                "success": False,
                "error": f"大きな音声ファイルの処理に失敗しました: {str(e)}"
            }
    
    def _simple_time_based_split(
        self, 
        file_data: bytes, 
        filename: str,
        language: str = "ja",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """簡易的な時間ベース分割（ffmpeg不要）"""
        try:
            logger.info("Using simple time-based splitting (ffmpeg not available)")
            
            # ファイルサイズから分割数を推定
            file_size_mb = len(file_data) / (1024 * 1024)
            max_chunk_size_mb = 20  # 20MB以下
            estimated_chunks = max(1, int(file_size_mb / max_chunk_size_mb))
            
            if estimated_chunks == 1:
                # 分割不要
                return self._transcribe_single_audio(file_data, filename, language, prompt)
            
            # バイト単位で均等分割
            chunk_size = len(file_data) // estimated_chunks
            chunks = []
            
            for i in range(estimated_chunks):
                start_byte = i * chunk_size
                end_byte = start_byte + chunk_size if i < estimated_chunks - 1 else len(file_data)
                
                chunk_data = file_data[start_byte:end_byte]
                chunk_filename = f"{filename.rsplit('.', 1)[0]}_chunk_{i+1:02d}.{filename.split('.')[-1]}"
                
                # 各チャンクを文字起こし
                chunk_result = self._transcribe_single_audio(
                    chunk_data, 
                    chunk_filename, 
                    language, 
                    prompt
                )
                
                chunk_result["chunk_info"] = {
                    "index": i,
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                    "filename": chunk_filename,
                    "method": "byte_split"
                }
                
                chunks.append(chunk_result)
                logger.info(f"Simple chunk {i+1}/{estimated_chunks} processed")
            
            # 結果を簡易マージ
            successful_chunks = [c for c in chunks if c.get("success", False)]
            if not successful_chunks:
                return {
                    "success": False,
                    "error": "すべてのチャンクの処理に失敗しました"
                }
            
            # テキストを結合
            combined_text = " ".join([c.get("text", "") for c in successful_chunks])
            
            return {
                "success": True,
                "text": combined_text,
                "language": successful_chunks[0].get("language", "ja"),
                "processing_method": "simple_byte_split",
                "chunks_processed": len(successful_chunks),
                "total_chunks": len(chunks),
                "chunk_details": chunks,
                "note": "ffmpegが利用できないため、簡易的なバイト分割を使用しました"
            }
            
        except Exception as e:
            logger.error(f"Simple time-based splitting error: {e}")
            return {
                "success": False,
                "error": f"簡易分割処理に失敗しました: {str(e)}"
            }
    
    def create_meeting_minutes(
        self, 
        transcribed_text: str,
        meeting_title: str = "",
        participants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """文字起こしテキストから議事録を生成"""
        try:
            logger.info("Creating meeting minutes from transcribed text")
            
            # 議事録生成用のプロンプト
            prompt = self._create_minutes_prompt(transcribed_text, meeting_title, participants)
            
            # OpenAI APIで議事録を生成
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは会議の議事録作成の専門家です。音声から文字起こしされたテキストを基に、整理された議事録を作成してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"},
                # プライバシー保護
                extra_headers={
                    "X-OpenAI-Skip-Training": "true"
                }
            )
            
            logger.info("プライバシー保護: OpenAI学習無効化ヘッダー送信完了 (議事録生成)")
            
            # レスポンスをJSONとしてパース
            content = response.choices[0].message.content
            if content is None:
                raise Exception("OpenAI APIからの応答が空です")
            
            minutes_data = json.loads(content)
            
            return {
                "success": True,
                "minutes": minutes_data
            }
            
        except Exception as e:
            logger.error(f"Meeting minutes creation error: {e}")
            return {
                "success": False,
                "error": f"議事録作成中にエラーが発生しました: {str(e)}"
            }
    
    def _create_minutes_prompt(
        self, 
        transcribed_text: str, 
        meeting_title: str, 
        participants: Optional[List[str]]
    ) -> str:
        """議事録生成用のプロンプトを作成"""
        participants_text = ""
        if participants:
            participants_text = f"参加者: {', '.join(participants)}"
        
        prompt = f"""
以下の音声文字起こしテキストを基に、構造化された議事録を作成してください。

会議タイトル: {meeting_title if meeting_title else "未指定"}
{participants_text}

文字起こしテキスト:
{transcribed_text}

以下のJSON形式で議事録を作成してください:

{{
    "meeting_title": "会議のタイトル",
    "date": "今日の日付（YYYY-MM-DD形式）",
    "participants": ["参加者1", "参加者2"],
    "summary": "会議の概要（2-3文で）",
    "agenda_items": [
        {{
            "topic": "議題1",
            "discussion": "議論内容の要約",
            "decisions": ["決定事項1", "決定事項2"],
            "action_items": [
                {{
                    "task": "タスク内容",
                    "assignee": "担当者",
                    "deadline": "期限（もしあれば）"
                }}
            ]
        }}
    ],
    "next_steps": ["次のステップ1", "次のステップ2"],
    "next_meeting": "次回会議の予定（もしあれば）"
}}

重要：
- 文字起こしから読み取れる内容のみを記載
- 推測や追加情報は含めない
- 話者が特定できる場合は参加者に含める
- 具体的な決定事項やアクションアイテムを明確に抽出
"""
        return prompt

# テスト用関数
def test_audio_service():
    """AudioServiceのテスト"""
    try:
        service = AudioService()
        print("✅ AudioService initialized successfully")
        return True
    except Exception as e:
        print(f"❌ AudioService initialization failed: {e}")
        return False

if __name__ == "__main__":
    test_audio_service()
