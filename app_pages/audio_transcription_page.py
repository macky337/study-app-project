# -*- coding: utf-8 -*-
"""
音声アップロードと議事録作成ページ
"""

import streamlit as st
import json
from typing import Optional, Any, Dict
from services.audio_service import AudioService
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def serialize_transcription_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """文字起こし結果をJSONシリアライズ可能な形式に変換"""
    if not result:
        return result
    
    # ディープコピーを作成
    serialized = result.copy()
    
    # TranscriptionSegmentオブジェクトが含まれている可能性があるsegmentsを処理
    if "segments" in serialized and serialized["segments"]:
        serialized_segments = []
        for segment in serialized["segments"]:
            if hasattr(segment, '__dict__'):
                # オブジェクトの場合は辞書に変換
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
                serialized_segments.append(segment_dict)
            else:
                # すでに辞書の場合はそのまま
                serialized_segments.append(segment)
        serialized["segments"] = serialized_segments
    
    # chunk_detailsも同様に処理
    if "chunk_details" in serialized and serialized["chunk_details"]:
        serialized_chunks = []
        for chunk in serialized["chunk_details"]:
            serialized_chunk = serialize_transcription_result(chunk)
            serialized_chunks.append(serialized_chunk)
        serialized["chunk_details"] = serialized_chunks
    
    return serialized

def render_audio_transcription_page():
    """音声文字起こし・議事録作成ページのレンダリング"""
    
    st.title("🎤 音声文字起こし・議事録作成")
    st.markdown("---")
    
    # セッションステートの初期化
    if 'transcription_result' not in st.session_state:
        st.session_state.transcription_result = None
    if 'audio_service' not in st.session_state:
        try:
            st.session_state.audio_service = AudioService()
        except Exception as e:
            st.error(f"音声サービスの初期化に失敗しました: {e}")
            return
    
    # タブ表示
    tab1, tab2, tab3 = st.tabs(["📤 音声アップロード", "📝 文字起こし結果", "📋 議事録作成"])
    
    with tab1:
        render_audio_upload_section()
    
    with tab2:
        render_transcription_result_section()
    
    with tab3:
        render_meeting_minutes_section()

def render_audio_upload_section():
    """音声アップロードセクション"""
    st.header("音声ファイルのアップロード")
    
    # サポートしているファイル形式の表示
    audio_service: AudioService = st.session_state.audio_service
    st.info(f"**サポート形式**: {', '.join(audio_service.SUPPORTED_FORMATS).upper()}")
    st.info(f"**最大ファイルサイズ**: 制限なし（大きなファイルは自動的に分割処理されます）")
    
    # ffmpegの状態チェック
    if not hasattr(audio_service, 'splitter') or audio_service.splitter is None:
        st.warning("⚠️ **注意**: ffmpegがインストールされていません。大容量ファイルは簡易分割処理になります。")
        with st.expander("ffmpegのインストール方法", expanded=False):
            st.markdown("""
            **macOS (Homebrew):**
            ```bash
            brew install ffmpeg
            ```
            
            **Ubuntu/Debian:**
            ```bash
            sudo apt update && sudo apt install ffmpeg
            ```
            
            **Windows:**
            1. [FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード
            2. PATHに追加
            
            インストール後、アプリケーションを再起動してください。
            """)
    
    # ファイルアップローダー
    uploaded_file = st.file_uploader(
        "音声ファイルを選択してください",
        type=audio_service.SUPPORTED_FORMATS,
        help="会議録音、講演、インタビューなどの音声ファイルをアップロードできます。大きなファイル（25MB以上）は自動的に分割処理されます。"
    )
    
    if uploaded_file is not None:
        st.success(f"ファイル '{uploaded_file.name}' がアップロードされました")
        
        # ファイル情報表示
        file_size = len(uploaded_file.getvalue())
        file_size_mb = file_size / (1024*1024)
        st.write(f"**ファイルサイズ**: {file_size_mb:.2f} MB")
        
        # 大きなファイルの場合は警告表示
        if file_size > audio_service.MAX_FILE_SIZE:
            if audio_service.splitter:
                st.warning(f"⚠️ ファイルサイズが{audio_service.MAX_FILE_SIZE // (1024*1024)}MBを超えています。自動的に分割処理を行います。")
            else:
                st.warning(f"⚠️ ファイルサイズが{audio_service.MAX_FILE_SIZE // (1024*1024)}MBを超えています。簡易分割処理を行います（ffmpegがインストールされていないため）。")
            
            # 音声情報を取得して表示
            try:
                with st.spinner("音声ファイルの情報を取得中..."):
                    audio_info = audio_service.get_audio_info(uploaded_file.getvalue(), uploaded_file.name)
                
                if "error" not in audio_info:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if "duration_minutes" in audio_info:
                            st.metric("音声時間（推定）", f"{audio_info['duration_minutes']:.1f}分")
                    with col2:
                        if "channels" in audio_info:
                            channel_text = "ステレオ" if audio_info['channels'] == 2 else "モノラル"
                            if "note" in audio_info:
                                channel_text += " (推定)"
                            st.metric("チャンネル", channel_text)
                    with col3:
                        if "frame_rate" in audio_info:
                            rate_text = f"{audio_info['frame_rate']}Hz"
                            if "note" in audio_info:
                                rate_text += " (推定)"
                            st.metric("サンプリングレート", rate_text)
                    
                    # 注意事項の表示
                    if "note" in audio_info:
                        st.info(f"ℹ️ {audio_info['note']}")
                    
                    # 分割予測の表示
                    if audio_service.splitter and "duration_seconds" in audio_info:
                        try:
                            strategy = audio_service.splitter.calculate_split_strategy(audio_info)
                            if strategy["needs_splitting"]:
                                st.info(f"📊 **分割予測**: 約{strategy['chunks_needed']}個のチャンクに分割されます（1チャンク約{strategy['chunk_duration_seconds']/60:.1f}分）")
                        except:
                            # 分割戦略の計算に失敗した場合
                            estimated_chunks = max(1, int(file_size_mb / 20))
                            st.info(f"📊 **簡易分割予測**: 約{estimated_chunks}個のチャンクに分割されます")
                    else:
                        # ffmpegが利用できない場合の簡易予測
                        estimated_chunks = max(1, int(file_size_mb / 20))
                        st.info(f"📊 **簡易分割予測**: 約{estimated_chunks}個のチャンクに分割されます（バイト分割）")
                        
            except Exception as e:
                st.warning(f"音声情報の取得に失敗しました: {e}")
        
        # 音声設定
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox(
                "音声の言語",
                ["ja", "en", "zh", "ko", "auto"],
                index=0,
                help="autoを選択すると自動検出されます"
            )
        
        with col2:
            use_prompt = st.checkbox("ヒントプロンプトを使用", help="特定の専門用語がある場合に精度向上")
        
        prompt_text = ""
        if use_prompt:
            prompt_text = st.text_area(
                "ヒントプロンプト",
                placeholder="専門用語、人名、会社名など、音声に含まれる可能性のある単語を入力",
                help="例：AI, 機械学習, 田中さん, 株式会社〇〇"
            )
        
        # 大きなファイルの場合の追加オプション（ffmpegが利用可能な場合のみ）
        use_custom_duration = False
        custom_duration = None
        
        if file_size > audio_service.MAX_FILE_SIZE and audio_service.splitter:
            st.subheader("🔧 分割処理オプション")
            
            col1, col2 = st.columns(2)
            with col1:
                use_custom_duration = st.checkbox(
                    "カスタム分割時間を指定", 
                    help="デフォルトの自動分割ではなく、手動で分割時間を指定します"
                )
            
            if use_custom_duration:
                with col2:
                    custom_duration = st.number_input(
                        "分割時間（分）",
                        min_value=1.0,
                        max_value=30.0,
                        value=10.0,
                        step=1.0,
                        help="各チャンクの時間を分単位で指定"
                    )
        
        # 文字起こし実行ボタン
        button_text = "🎯 文字起こし開始（分割処理）" if file_size > audio_service.MAX_FILE_SIZE else "🎯 文字起こし開始"
        
        if st.button(button_text, type="primary"):
            with st.spinner("音声を文字起こししています..."):
                try:
                    # 音声データを取得
                    audio_data = uploaded_file.getvalue()
                    
                    # 言語設定
                    lang = "ja" if language == "auto" else language
                    prompt = prompt_text if use_prompt and prompt_text else None
                    
                    # 大きなファイルの場合はカスタム分割時間を渡す
                    chunk_results = []  # 変数を初期化
                    
                    if file_size > audio_service.MAX_FILE_SIZE:
                        # 分割が必要な場合
                        if use_custom_duration and custom_duration and audio_service.splitter:
                            # カスタム分割時間を使用する場合（ffmpeg利用可能）
                            st.info("🔧 高精度音声分割機能を使用します（ffmpeg使用）")
                            chunks = audio_service.splitter.split_audio_file(
                                audio_data, 
                                uploaded_file.name, 
                                chunk_duration_minutes=custom_duration
                            )
                            
                            # 各チャンクを処理
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, chunk in enumerate(chunks):
                                status_text.text(f"チャンク {i+1}/{len(chunks)} を処理中...")
                                progress_bar.progress((i + 1) / len(chunks))
                                
                                chunk_result = audio_service._transcribe_single_audio(
                                    chunk["data"], 
                                    chunk["filename"], 
                                    lang, 
                                    prompt
                                )
                                chunk_result["chunk_info"] = {
                                    "index": chunk["chunk_index"],
                                    "start_time": chunk["start_time"],
                                    "end_time": chunk["end_time"],
                                    "duration": chunk["duration"],
                                    "filename": chunk["filename"]
                                }
                                chunk_results.append(chunk_result)
                            
                            # 結果をマージ
                            result = audio_service.splitter.merge_transcriptions(chunk_results)
                            result["processing_method"] = "custom_split_and_merge"
                            result["chunk_details"] = chunk_results
                            
                            progress_bar.empty()
                            status_text.empty()
                        else:
                            # 自動分割（ffmpeg利用可能時）または簡易分割（ffmpeg未利用時）
                            if audio_service.splitter:
                                st.info("🔧 高精度音声分割機能を使用します（ffmpeg使用）")
                            else:
                                st.info("🔧 簡易分割機能を使用します（ffmpeg未インストール）")
                            
                            # progress_callbackを定義
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            def update_progress(chunk_index, total_chunks, current_status):
                                if total_chunks > 0:
                                    progress = chunk_index / total_chunks
                                    progress_bar.progress(progress)
                                    status_text.text(f"{current_status} ({chunk_index}/{total_chunks})")
                            
                            # 分割処理パラメータの準備
                            transcription_params = {
                                "language": None if language == "auto" else language,
                                "prompt": prompt_text if use_prompt and prompt_text else None
                            }
                            
                            # 大容量音声ファイルの文字起こし
                            result = audio_service._transcribe_large_audio(
                                audio_data,
                                uploaded_file.name,
                                lang,
                                prompt
                            )
                            
                            progress_bar.empty()
                            status_text.empty()
                    else:
                        # 通常の処理（自動分割含む）
                        result = audio_service.transcribe_audio(
                            file_data=audio_data,
                            filename=uploaded_file.name,
                            language=lang,
                            prompt=prompt
                        )
                    
                    if result["success"]:
                        # 結果をシリアライズしてセッション状態に保存
                        serialized_result = serialize_transcription_result(result)
                        st.session_state.transcription_result = serialized_result
                        st.success("✅ 文字起こしが完了しました！")
                        st.balloons()
                        
                        # 処理方法の表示
                        processing_method = result.get("processing_method", "single_file")
                        if processing_method == "split_and_merge":
                            chunk_info = result.get("merge_info", {})
                            st.info(f"📊 **分割処理完了**: {chunk_info.get('successful_chunks', 0)}個のチャンクを正常に処理しました")
                        elif processing_method == "custom_split_and_merge":
                            st.info(f"📊 **カスタム分割処理完了**: {len(chunk_results)}個のチャンクを処理しました")
                        
                        # 結果のプレビュー表示
                        st.subheader("📝 文字起こし結果（プレビュー）")
                        preview_text = result["text"][:500]
                        if len(result["text"]) > 500:
                            preview_text += "..."
                        st.text_area("", preview_text, height=150, disabled=True)
                        
                        st.info("詳細は「文字起こし結果」タブで確認できます")
                    else:
                        st.error(f"❌ 文字起こしに失敗しました: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Transcription error: {e}")
                    st.error(f"❌ エラーが発生しました: {str(e)}")

def render_transcription_result_section():
    """文字起こし結果セクション"""
    st.header("文字起こし結果")
    
    if st.session_state.transcription_result is None:
        st.info("まず音声ファイルをアップロードして文字起こしを行ってください")
        return
    
    # セッション状態のデータを安全に取得
    try:
        result = st.session_state.transcription_result
        # JSONシリアライゼーションテスト
        import json
        json.dumps(result)
    except (TypeError, ValueError) as e:
        st.error("⚠️ 文字起こし結果にシリアライゼーション問題があります。再度文字起こしを実行してください。")
        # 問題のあるデータをクリア
        st.session_state.transcription_result = None
        if st.button("🔄 セッションデータをクリア"):
            st.rerun()
        return
    except Exception as e:
        st.error(f"文字起こし結果の読み込み中にエラーが発生しました: {e}")
        return
    
    # 結果の表示続行
    result = st.session_state.transcription_result
    
    # 処理方法の表示
    processing_method = result.get("processing_method", "single_file")
    if processing_method in ["split_and_merge", "custom_split_and_merge"]:
        st.success("🔧 大きなファイルを分割して処理しました")
        
        # 分割処理の詳細
        if "merge_info" in result:
            merge_info = result["merge_info"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("処理チャンク数", f"{merge_info.get('successful_chunks', 0)}/{merge_info.get('successful_chunks', 0) + merge_info.get('failed_chunks', 0)}")
            with col2:
                st.metric("処理方法", "自動分割" if processing_method == "split_and_merge" else "カスタム分割")
            with col3:
                if merge_info.get('failed_chunks', 0) > 0:
                    st.metric("失敗チャンク", merge_info['failed_chunks'], delta_color="inverse")
    
    # 結果の詳細表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("言語", result.get("language", "不明"))
    with col2:
        duration = result.get("duration")
        if duration:
            st.metric("音声長", f"{duration:.1f}秒")
    with col3:
        text_length = len(result["text"])
        st.metric("文字数", f"{text_length:,}文字")
    
    # 文字起こしテキスト表示
    st.subheader("📄 文字起こしテキスト")
    st.text_area(
        "",
        result["text"],
        height=400,
        help="このテキストをコピーして他のアプリケーションで使用できます"
    )
    
    # ダウンロードボタン
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 テキストファイルとしてダウンロード",
            data=result["text"],
            file_name="transcription.txt",
            mime="text/plain"
        )
    
    with col2:
        # JSON形式でのダウンロード
        json_data = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            "📊 詳細データ（JSON）をダウンロード",
            data=json_data,
            file_name="transcription_data.json",
            mime="application/json"
        )
    
    # 分割処理の詳細情報
    if processing_method in ["split_and_merge", "custom_split_and_merge"] and "chunk_details" in result:
        with st.expander("🔍 分割処理の詳細情報", expanded=False):
            chunk_details = result["chunk_details"]
            
            st.write(f"**処理されたチャンク数**: {len(chunk_details)}")
            
            for i, chunk_result in enumerate(chunk_details):
                if chunk_result.get("success", False):
                    chunk_info = chunk_result.get("chunk_info", {})
                    st.write(f"**チャンク {i+1}** ({chunk_info.get('filename', 'unknown')})")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        start_time = chunk_info.get('start_time', 0)
                        end_time = chunk_info.get('end_time', 0)
                        st.write(f"時間: {start_time/60:.1f}分 - {end_time/60:.1f}分")
                    with col2:
                        duration = chunk_info.get('duration', 0)
                        st.write(f"長さ: {duration/60:.1f}分")
                    with col3:
                        text_len = len(chunk_result.get("text", ""))
                        st.write(f"文字数: {text_len}文字")
                    
                    # チャンクのテキストプレビュー
                    preview = chunk_result.get("text", "")[:200]
                    if len(chunk_result.get("text", "")) > 200:
                        preview += "..."
                    st.text(preview)
                    st.markdown("---")
                else:
                    st.error(f"チャンク {i+1}: {chunk_result.get('error', '処理に失敗しました')}")
    
    # セグメント情報があれば表示
    elif result.get("segments"):
        with st.expander("🔍 詳細セグメント情報", expanded=False):
            for i, segment in enumerate(result["segments"][:10]):  # 最初の10セグメントのみ表示
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                text = segment.get("text", "")
                st.write(f"**{start_time:.1f}s - {end_time:.1f}s**: {text}")
            
            if len(result["segments"]) > 10:
                st.info(f"他に{len(result['segments']) - 10}個のセグメントがあります")

def render_meeting_minutes_section():
    """議事録作成セクション"""
    st.header("議事録作成")
    
    if st.session_state.transcription_result is None:
        st.info("まず音声ファイルをアップロードして文字起こしを行ってください")
        return
    
    transcription_text = st.session_state.transcription_result["text"]
    
    st.subheader("📋 議事録設定")
    
    # 議事録の設定
    col1, col2 = st.columns(2)
    with col1:
        meeting_title = st.text_input(
            "会議タイトル",
            placeholder="例：週次チーム会議、プロジェクト進捗確認"
        )
    
    with col2:
        participants_input = st.text_input(
            "参加者（カンマ区切り）",
            placeholder="例：田中, 佐藤, 山田"
        )
    
    # 参加者リスト作成
    participants = None
    if participants_input:
        participants = [p.strip() for p in participants_input.split(",") if p.strip()]
    
    # 文字起こしテキストのプレビュー
    st.subheader("📝 文字起こしテキスト（プレビュー）")
    preview_text = transcription_text[:1000]
    if len(transcription_text) > 1000:
        preview_text += "..."
    st.text_area("", preview_text, height=200, disabled=True)
    
    # 議事録生成ボタン
    if st.button("📋 議事録を生成", type="primary"):
        with st.spinner("議事録を生成しています..."):
            try:
                audio_service: AudioService = st.session_state.audio_service
                
                result = audio_service.create_meeting_minutes(
                    transcribed_text=transcription_text,
                    meeting_title=meeting_title,
                    participants=participants
                )
                
                if result["success"]:
                    st.success("✅ 議事録の生成が完了しました！")
                    
                    minutes = result["minutes"]
                    
                    # 議事録表示
                    st.subheader("📋 生成された議事録")
                    
                    # 基本情報
                    st.markdown(f"### {minutes.get('meeting_title', '会議議事録')}")
                    st.write(f"**日付**: {minutes.get('date', '未指定')}")
                    
                    if minutes.get('participants'):
                        st.write(f"**参加者**: {', '.join(minutes['participants'])}")
                    
                    # 概要
                    if minutes.get('summary'):
                        st.subheader("📌 会議概要")
                        st.write(minutes['summary'])
                    
                    # 議題別内容
                    if minutes.get('agenda_items'):
                        st.subheader("📋 議事内容")
                        for i, item in enumerate(minutes['agenda_items'], 1):
                            with st.expander(f"議題 {i}: {item.get('topic', '未設定')}", expanded=True):
                                if item.get('discussion'):
                                    st.write("**議論内容:**")
                                    st.write(item['discussion'])
                                
                                if item.get('decisions'):
                                    st.write("**決定事項:**")
                                    for decision in item['decisions']:
                                        st.write(f"• {decision}")
                                
                                if item.get('action_items'):
                                    st.write("**アクションアイテム:**")
                                    for action in item['action_items']:
                                        task = action.get('task', '')
                                        assignee = action.get('assignee', '未指定')
                                        deadline = action.get('deadline', '未指定')
                                        st.write(f"• **{task}** (担当: {assignee}, 期限: {deadline})")
                    
                    # 次のステップ
                    if minutes.get('next_steps'):
                        st.subheader("🔄 次のステップ")
                        for step in minutes['next_steps']:
                            st.write(f"• {step}")
                    
                    if minutes.get('next_meeting'):
                        st.subheader("📅 次回会議")
                        st.write(minutes['next_meeting'])
                    
                    # ダウンロードボタン
                    st.subheader("💾 ダウンロード")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # マークダウン形式でダウンロード
                        markdown_content = format_minutes_as_markdown(minutes)
                        st.download_button(
                            "📄 議事録（Markdown）をダウンロード",
                            data=markdown_content,
                            file_name="meeting_minutes.md",
                            mime="text/markdown"
                        )
                    
                    with col2:
                        # JSON形式でダウンロード
                        json_content = json.dumps(minutes, ensure_ascii=False, indent=2)
                        st.download_button(
                            "📊 議事録（JSON）をダウンロード",
                            data=json_content,
                            file_name="meeting_minutes.json",
                            mime="application/json"
                        )
                    
                else:
                    st.error(f"❌ 議事録生成に失敗しました: {result['error']}")
                    
            except Exception as e:
                logger.error(f"Meeting minutes creation error: {e}")
                st.error(f"❌ エラーが発生しました: {str(e)}")

def format_minutes_as_markdown(minutes: dict) -> str:
    """議事録をMarkdown形式でフォーマット"""
    content = []
    
    # タイトル
    content.append(f"# {minutes.get('meeting_title', '会議議事録')}")
    content.append("")
    
    # 基本情報
    content.append("## 基本情報")
    content.append(f"- **日付**: {minutes.get('date', '未指定')}")
    
    if minutes.get('participants'):
        content.append(f"- **参加者**: {', '.join(minutes['participants'])}")
    content.append("")
    
    # 概要
    if minutes.get('summary'):
        content.append("## 会議概要")
        content.append(minutes['summary'])
        content.append("")
    
    # 議事内容
    if minutes.get('agenda_items'):
        content.append("## 議事内容")
        for i, item in enumerate(minutes['agenda_items'], 1):
            content.append(f"### {i}. {item.get('topic', '未設定')}")
            
            if item.get('discussion'):
                content.append("**議論内容:**")
                content.append(item['discussion'])
                content.append("")
            
            if item.get('decisions'):
                content.append("**決定事項:**")
                for decision in item['decisions']:
                    content.append(f"- {decision}")
                content.append("")
            
            if item.get('action_items'):
                content.append("**アクションアイテム:**")
                for action in item['action_items']:
                    task = action.get('task', '')
                    assignee = action.get('assignee', '未指定')
                    deadline = action.get('deadline', '未指定')
                    content.append(f"- **{task}** (担当: {assignee}, 期限: {deadline})")
                content.append("")
    
    # 次のステップ
    if minutes.get('next_steps'):
        content.append("## 次のステップ")
        for step in minutes['next_steps']:
            content.append(f"- {step}")
        content.append("")
    
    if minutes.get('next_meeting'):
        content.append("## 次回会議")
        content.append(minutes['next_meeting'])
    
    return "\n".join(content)
