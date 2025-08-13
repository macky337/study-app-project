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
    
    # 議事録作成用プロンプトテンプレート
    PROMPT_TEMPLATES = {
        "standard": {
            "name": "標準議事録",
            "description": "一般的なビジネス会議に適した形式",
            "prompt": """以下は、会議または打ち合わせの文字起こしデータです。
この内容を基に、わかりやすく整理された議事録を作成してください。

【要件】
1. 冒頭に「会議概要」として日付・場所・参加者を記載（わかる範囲で）。
2. 「決定事項」と「未決事項」に分けて箇条書きで明記。
3. 決定事項は、具体的な日時・場所・金額・担当者などを可能な限り詳細に。
4. 「議論内容」では、重要なやり取りの経緯や背景説明を時系列で簡潔にまとめる。
5. 必要に応じて「次回までの宿題」「補足事項」も追加。
6. 無関係な雑談や重複は削除し、重要情報を残す。
7. 全体を読みやすい段落・箇条書き形式で整える。

【出力形式例】

---
# 議事録

**会議概要**  
- 日時：YYYY年MM月DD日  
- 場所：〇〇  
- 参加者：〇〇

**決定事項**  
- ○月○日 18:00 通夜開始（会場：〇〇）  
- ○月○日 14:30 火葬（場所：〇〇火葬場）  
- 遺体は低温庫保管、ドライアイス不使用  
- 式後の食事は4名分お持ち帰り弁当（業者：〇〇）

**未決事項**  
- 会葬返礼品の有無  
- 〇〇の搬送ルート確定

**議論内容**  
1. 式の日程と読経のタイミングについて議論し、住職の都合で12日に読経実施案が有力とされた。  
2. 遺体保管方法として低温庫利用を決定。ドライアイスは肌変色のリスクから使用しない方針。  
3. 祭壇は白木に洋花を配置し、棺内にも花を入れる案が採用された。  
4. …（続く）

**次回までの宿題**  
- 搬送ルートを運転担当と再確認  
- 香典返し対応の可否を確定

---

**重要: 必ずJSON形式で出力してください。**

【文字起こしデータ】
{transcription_text}"""
        },
        "simple": {
            "name": "シンプル議事録",
            "description": "要点のみを簡潔にまとめた形式",
            "prompt": """以下の会議文字起こしデータから、要点のみを簡潔にまとめた議事録を作成してください。

【要件】
- 決定事項と次のアクションを明確に
- 不要な詳細は省略
- 読みやすい箇条書き形式

【出力形式】
## 議事録

### 決定事項
- 項目1
- 項目2

### アクションアイテム
- [ ] タスク1 (担当者、期限)
- [ ] タスク2 (担当者、期限)

### その他
- 補足事項

**重要: 必ずJSON形式で出力してください。**

【文字起こしデータ】
{transcription_text}"""
        },
        "detailed": {
            "name": "詳細議事録",
            "description": "詳細な議論内容を含む包括的な形式",
            "prompt": """以下の会議文字起こしデータから、詳細で包括的な議事録を作成してください。

【要件】
1. 会議の背景と目的を明記
2. 参加者の発言を時系列で整理
3. 議論のプロセスと根拠を詳細に記録
4. 決定に至った経緯を明確に
5. リスクや懸念事項も含める
6. フォローアップ計画を具体的に

【出力形式】
# 議事録

## 1. 会議概要
- 日時：
- 参加者：
- 目的：

## 2. 議論詳細
### 2.1 議題1
- 背景：
- 主な議論：
- 懸念事項：

### 2.2 議題2
...

## 3. 決定事項
1. 決定内容（根拠、影響範囲を含む）
2. ...

## 4. アクションプラン
| タスク | 担当者 | 期限 | 優先度 |
|--------|--------|------|--------|
| | | | |

## 5. 次回会議
- 日程：
- 議題：

**重要: 必ずJSON形式で出力してください。**

【文字起こしデータ】
{transcription_text}"""
        },
        "agile": {
            "name": "アジャイル・スタンドアップ",
            "description": "アジャイル開発のスタンドアップ会議向け",
            "prompt": """以下のスタンドアップ会議の文字起こしデータから、アジャイル形式の議事録を作成してください。

【要件】
- 各メンバーの進捗を整理
- ブロッカーと課題を明確に
- 次のスプリントへのアクション

【出力形式】
# スタンドアップ議事録

## 日時・参加者
- 日時：
- 参加者：

## メンバー別進捗

### [メンバー名1]
- **昨日完了したこと：**
- **今日する予定：**
- **ブロッカー・課題：**

### [メンバー名2]
...

## チーム全体
- **スプリント進捗：**
- **リスク・課題：**
- **次のアクション：**

**重要: 必ずJSON形式で出力してください。**

【文字起こしデータ】
{transcription_text}"""
        }
    }
    
    # 利用可能なGPTモデル（議事録生成用）
    AVAILABLE_MODELS = {
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "description": "高速・低コスト（推奨）",
            "input_cost_per_1m": 0.15,  # USD per 1M tokens
            "output_cost_per_1m": 0.6,
            "max_tokens": 128000,
            "recommended_for": "一般的な議事録作成"
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "高品質・中コスト",
            "input_cost_per_1m": 2.50,
            "output_cost_per_1m": 10.0,
            "max_tokens": 128000,
            "recommended_for": "重要な会議・詳細な分析"
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo", 
            "description": "バランス型",
            "input_cost_per_1m": 10.0,
            "output_cost_per_1m": 30.0,
            "max_tokens": 128000,
            "recommended_for": "複雑な議事録作成"
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "最低コスト",
            "input_cost_per_1m": 0.50,
            "output_cost_per_1m": 1.50,
            "max_tokens": 16385,
            "recommended_for": "シンプルな議事録"
        }
    }
    
    def __init__(self):
        """サービスの初期化"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Railway環境でのメモリ制限を考慮してファイルサイズを調整
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT'):
            self.MAX_FILE_SIZE = 20 * 1024 * 1024  # Railway環境では20MBに制限
            logger.info("Railway environment detected: File size limit set to 20MB")
        
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
        participants: Optional[List[str]] = None,
        model: str = "gpt-4o-mini",
        custom_prompt: Optional[str] = None,
        prompt_template: str = "standard"
    ) -> Dict[str, Any]:
        """文字起こしテキストから議事録を生成
        
        Args:
            transcribed_text: 文字起こしされたテキスト
            meeting_title: 会議タイトル
            participants: 参加者リスト
            model: 使用するGPTモデル（デフォルト: gpt-4o-mini）
            custom_prompt: カスタムプロンプト（指定時はこれを優先）
            prompt_template: プロンプトテンプレート名（デフォルト: standard）
        """
        try:
            # 入力テキストの検証
            if not transcribed_text or transcribed_text.strip() == "":
                return {
                    "success": False,
                    "error": "文字起こしテキストが空です。"
                }
            
            # モデルの検証
            if model not in self.AVAILABLE_MODELS:
                logger.warning(f"Unknown model {model}, falling back to gpt-4o-mini")
                model = "gpt-4o-mini"
            
            logger.info(f"Creating meeting minutes using model: {model}")
            
            # プロンプトの決定（カスタムプロンプト優先）
            if custom_prompt and custom_prompt.strip():
                # カスタムプロンプトを使用
                try:
                    prompt = custom_prompt.format(transcription_text=transcribed_text)
                    logger.info("Using custom prompt for meeting minutes")
                except KeyError as e:
                    logger.warning(f"Custom prompt format error: {e}")
                    # フォールバック処理
                    prompt = custom_prompt + f"\n\n【文字起こしデータ】\n{transcribed_text}"
            else:
                # テンプレートプロンプトを使用
                if prompt_template in self.PROMPT_TEMPLATES:
                    template = self.PROMPT_TEMPLATES[prompt_template]
                    try:
                        prompt = template["prompt"].format(transcription_text=transcribed_text)
                        logger.info(f"Using template prompt: {template['name']}")
                    except KeyError as e:
                        logger.warning(f"Template prompt format error: {e}")
                        # フォールバック処理
                        prompt = template["prompt"] + f"\n\n【文字起こしデータ】\n{transcribed_text}"
                else:
                    # フォールバック: 従来のプロンプト
                    prompt = self._create_minutes_prompt(transcribed_text, meeting_title, participants)
                    logger.info("Using legacy prompt format")
            
            # OpenAI APIで議事録を生成
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは会議の議事録作成の専門家です。音声から文字起こしされたテキストを基に、整理された議事録をJSON形式で作成してください。"
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
            
            # 使用量とコストの計算
            usage = response.usage
            model_info = self.AVAILABLE_MODELS[model]
            
            if usage:
                input_cost = (usage.prompt_tokens / 1_000_000) * model_info["input_cost_per_1m"]
                output_cost = (usage.completion_tokens / 1_000_000) * model_info["output_cost_per_1m"]
                total_cost = input_cost + output_cost
                
                cost_info = {
                    "model_used": model,
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "estimated_cost_usd": round(total_cost, 4),
                    "cost_breakdown": {
                        "input_cost": round(input_cost, 4),
                        "output_cost": round(output_cost, 4)
                    }
                }
                logger.info(f"Cost info: ${total_cost:.4f} USD ({usage.total_tokens} tokens)")
            else:
                cost_info = {
                    "model_used": model,
                    "estimated_cost_usd": "unavailable"
                }
            
            # レスポンスをJSONとしてパース
            content = response.choices[0].message.content
            if content is None:
                raise Exception("OpenAI APIからの応答が空です")
            
            minutes_data = json.loads(content)
            
            return {
                "success": True,
                "minutes": minutes_data,
                "cost_info": cost_info
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

    @classmethod
    def estimate_cost(cls, text_length: int, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """テキスト長に基づいてコストを概算
        
        Args:
            text_length: 入力テキストの文字数
            model: 使用予定のモデル
            
        Returns:
            コスト概算情報
        """
        if model not in cls.AVAILABLE_MODELS:
            model = "gpt-4o-mini"
        
        model_info = cls.AVAILABLE_MODELS[model]
        
        # 概算トークン数 (日本語は約2.5文字=1トークン、英語は約4文字=1トークン)
        estimated_input_tokens = int(text_length / 2.5)  # 日本語メインと仮定
        estimated_output_tokens = 1000  # 議事録出力の平均的なトークン数
        
        input_cost = (estimated_input_tokens / 1_000_000) * model_info["input_cost_per_1m"]
        output_cost = (estimated_output_tokens / 1_000_000) * model_info["output_cost_per_1m"]
        total_cost = input_cost + output_cost
        
        return {
            "model": model,
            "model_name": model_info["name"],
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "cost_breakdown": {
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4)
            },
            "text_length": text_length
        }

    @classmethod
    def get_model_info(cls, model: str = None) -> Dict[str, Any]:
        """モデル情報を取得
        
        Args:
            model: 特定のモデル名（Noneの場合は全モデル情報）
            
        Returns:
            モデル情報
        """
        if model:
            return cls.AVAILABLE_MODELS.get(model, {})
        return cls.AVAILABLE_MODELS

    @classmethod
    def get_prompt_templates(cls) -> Dict[str, Dict[str, str]]:
        """プロンプトテンプレート情報を取得
        
        Returns:
            プロンプトテンプレート情報
        """
        return cls.PROMPT_TEMPLATES

    @classmethod
    def get_prompt_template(cls, template_name: str) -> Optional[Dict[str, str]]:
        """特定のプロンプトテンプレートを取得
        
        Args:
            template_name: テンプレート名
            
        Returns:
            プロンプトテンプレート情報
        """
        return cls.PROMPT_TEMPLATES.get(template_name)

if __name__ == "__main__":
    test_audio_service()
