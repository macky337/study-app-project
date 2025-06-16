# PDF問題生成タブの新しい実装

def create_pdf_tab(tab3, session, question_service, choice_service):
    """PDF問題生成タブを作成"""
    with tab3:
        st.markdown("### 📄 PDF問題生成")
        
        # PDFアップロードと問題生成
        try:
            from services.pdf_processor import PDFProcessor
            from services.pdf_question_generator import PDFQuestionGenerator
            from services.past_question_extractor import PastQuestionExtractor
            
            pdf_processor = PDFProcessor()
            
            if session:
                # デフォルトモデルで初期化（後で選択モデルで再初期化）
                pdf_generator = PDFQuestionGenerator(session, model_name="gpt-4o-mini")
                past_extractor = PastQuestionExtractor(session, model_name="gpt-4o-mini")
            else:
                st.warning("⚠️ データベース接続エラーのため、問題の保存ができません。")
                return
            
            st.markdown("""
            **PDF教材から問題を処理**
            
            📚 2つのモードから選択できます：
            - **問題生成モード**: 教材内容からAIが新しい問題を生成
            - **過去問抽出モード**: 既存の問題・正解・解説をそのまま抽出
            
            🔒 **プライバシー保護**
            - アップロードされたPDFの内容はOpenAIの学習データとして使用されません
            - `X-OpenAI-Skip-Training: true`ヘッダーを設定して学習を無効化しています
            - 処理完了後、PDF内容はメモリから削除されます
            """)
            
            # 処理モード選択
            processing_mode = st.radio(
                "処理モードを選択",
                ["🤖 問題生成モード", "📝 過去問抽出モード"],
                help="問題生成：AIが新しい問題を作成 / 過去問抽出：既存の問題をそのまま利用"
            )
            
            # ファイルアップロード
            uploaded_file = st.file_uploader(
                "PDFファイルを選択してください",
                type=['pdf'],
                help="最大50MBまでのPDFファイルをアップロードできます",
                key="pdf_uploader"
            )
            
            if uploaded_file is not None:
                # ファイル検証
                is_valid, message = pdf_processor.validate_file(uploaded_file)
                
                if not is_valid:
                    st.error(f"❌ {message}")
                    st.stop()
                
                # ファイル情報表示
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("ファイル名", uploaded_file.name)
                with col2:
                    st.metric("ファイルサイズ", f"{uploaded_file.size / 1024:.1f} KB")
                with col3:
                    st.metric("ファイル形式", "PDF")
                
                st.markdown("---")
                
                if processing_mode == "🤖 問題生成モード":
                    # 問題生成設定
                    st.markdown("**🤖 問題生成設定**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        pdf_num_questions = st.slider("生成問題数", 1, 30, 10, key="pdf_num_questions")
                    
                    with col2:
                        pdf_difficulty = st.selectbox(
                            "難易度",
                            ["easy", "medium", "hard"],
                            format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                            key="pdf_difficulty"
                        )
                    
                    with col3:
                        pdf_category = st.text_input("カテゴリ名", "PDF教材", key="pdf_category")
                    
                    # 詳細設定
                    with st.expander("🔧 詳細設定"):
                        # AIモデル選択
                        st.markdown("**🤖 AIモデル選択**")
                        
                        pdf_model_options = {
                            "gpt-3.5-turbo": "GPT-3.5 Turbo (高速・経済的)",
                            "gpt-4o-mini": "GPT-4o Mini (高品質・バランス)",
                            "gpt-4o": "GPT-4o (最高品質)",
                            "gpt-4": "GPT-4 (最高品質・詳細)"
                        }
                        
                        pdf_selected_model = st.selectbox(
                            "使用するAIモデル",
                            options=list(pdf_model_options.keys()),
                            format_func=lambda x: pdf_model_options[x],
                            index=1,  # デフォルトはgpt-4o-mini
                            help="PDF処理では高品質なモデルを推奨します",
                            key="pdf_model_select"
                        )
                        
                        # モデル詳細情報
                        pdf_model_info = {
                            "gpt-3.5-turbo": {"cost": "💰 低", "quality": "⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o-mini": {"cost": "💰💰 中", "quality": "⭐⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 標準"},
                            "gpt-4": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 低速"}
                        }
                        
                        pdf_info = pdf_model_info[pdf_selected_model]
                        st.info(f"**{pdf_model_options[pdf_selected_model]}**\n\n"
                               f"コスト: {pdf_info['cost']} | 品質: {pdf_info['quality']} | 速度: {pdf_info['speed']}")
                        
                        # その他のオプション
                        extraction_method = st.selectbox(
                            "テキスト抽出方法",
                            ["auto", "pypdf2", "pdfplumber"],
                            format_func=lambda x: {
                                "auto": "自動選択（推奨）",
                                "pypdf2": "PyPDF2（高速）",
                                "pdfplumber": "PDFplumber（高精度）"
                            }[x]
                        )
                        
                        include_explanation = st.checkbox("解説を含める", value=True, key="pdf_explanation")
                        preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=False)
                    
                    # プライバシー確認
                    privacy_confirmed = st.checkbox(
                        "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                        help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません。",
                        key="privacy_confirmation_gen"
                    )
                    
                    button_label = "🎯 PDFから問題を生成"
                    
                else:  # 過去問抽出モード
                    st.markdown("**📝 過去問抽出設定**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        pdf_category = st.text_input("カテゴリ名", "過去問", key="past_category")
                    
                    with col2:
                        extraction_method = st.selectbox(
                            "テキスト抽出方法",
                            ["auto", "pypdf2", "pdfplumber"],
                            format_func=lambda x: {
                                "auto": "自動選択（推奨）",
                                "pypdf2": "PyPDF2（高速）",
                                "pdfplumber": "PDFplumber（高精度）"
                            }[x],
                            key="past_extraction_method"
                        )
                    
                    # 詳細設定
                    with st.expander("🔧 過去問抽出の詳細設定"):
                        # AIモデル選択
                        st.markdown("**🤖 AIモデル選択**")
                        
                        past_model_options = {
                            "gpt-3.5-turbo": "GPT-3.5 Turbo (高速・経済的)",
                            "gpt-4o-mini": "GPT-4o Mini (高品質・バランス)",
                            "gpt-4o": "GPT-4o (最高品質)",
                            "gpt-4": "GPT-4 (最高品質・詳細)"
                        }
                        
                        past_selected_model = st.selectbox(
                            "使用するAIモデル",
                            options=list(past_model_options.keys()),
                            format_func=lambda x: past_model_options[x],
                            index=1,  # デフォルトはgpt-4o-mini
                            help="過去問抽出では高精度モデルを推奨します",
                            key="past_model_select"
                        )
                        
                        # モデル詳細情報
                        past_model_info = {
                            "gpt-3.5-turbo": {"cost": "💰 低", "quality": "⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o-mini": {"cost": "💰💰 中", "quality": "⭐⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 標準"},
                            "gpt-4": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 低速"}
                        }
                        
                        past_info = past_model_info[past_selected_model]
                        st.info(f"**{past_model_options[past_selected_model]}**\n\n"
                               f"コスト: {past_info['cost']} | 品質: {past_info['quality']} | 速度: {past_info['speed']}")
                        
                        st.markdown("**📋 過去問抽出について:**")
                        st.markdown("""
                        - 問題文、選択肢、正解、解説をそのまま抽出
                        - 元の内容を一切改変しません
                        - 問題番号で自動分割を試行
                        - 抽出精度を向上させるため低温度設定を使用
                        """)
                        
                        preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=True, key="past_preview")
                        strict_extraction = st.checkbox("厳密抽出モード", value=True, help="より正確な抽出のため、温度設定を最低にします")
                    
                    # プライバシー確認
                    privacy_confirmed = st.checkbox(
                        "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                        help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません。",
                        key="privacy_confirmation_extract"
                    )
                    
                    button_label = "📝 PDFから過去問を抽出"
                
                # 処理実行
                st.markdown("---")
                if st.button(button_label, type="primary", use_container_width=True, disabled=not privacy_confirmed):
                    
                    if not privacy_confirmed:
                        st.warning("⚠️ プライバシー保護設定への同意が必要です。")
                        st.stop()
                    
                    # プログレス表示
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # プライバシー保護の確認表示
                        st.info("🔒 OpenAI学習無効化ヘッダーを設定して処理を開始します")
                        
                        # PDFテキスト抽出
                        status_text.text("PDFからテキストを抽出中...")
                        progress_bar.progress(0.1)
                        
                        file_bytes = uploaded_file.read()
                        if not file_bytes:
                            st.error("ERROR: PDFファイルの読み込みに失敗しました")
                            st.stop()
                        
                        # テキスト抽出の実行
                        if extraction_method == "auto":
                            extracted_text = pdf_processor.extract_text_auto(file_bytes)
                        elif extraction_method == "pypdf2":
                            extracted_text = pdf_processor.extract_text_pypdf2(file_bytes)
                        else:
                            extracted_text = pdf_processor.extract_text_pdfplumber(file_bytes)
                        
                        if not extracted_text or len(extracted_text.strip()) < 50:
                            st.error("ERROR: PDFからテキストを抽出できませんでした。")
                            st.stop()
                        
                        # テキストプレビュー
                        if preview_text:
                            st.markdown("### 📖 抽出テキストプレビュー")
                            with st.expander("抽出されたテキスト（最初の1000文字）"):
                                st.text(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
                        
                        # プログレスコールバック関数
                        def pdf_progress_callback(message, progress):
                            status_text.text(message)
                            progress_bar.progress(min(progress, 0.95))
                        
                        if processing_mode == "🤖 問題生成モード":
                            # 選択されたモデルでPDFジェネレーターを再初期化
                            pdf_generator = PDFQuestionGenerator(session, model_name=pdf_selected_model)
                            
                            # 問題生成実行
                            status_text.text("問題を生成中...")
                            progress_bar.progress(0.3)
                            
                            generated_ids = pdf_generator.generate_questions_from_pdf(
                                text=extracted_text,
                                num_questions=pdf_num_questions,
                                difficulty=pdf_difficulty,
                                category=pdf_category,
                                progress_callback=pdf_progress_callback
                            )
                            mode_text = "生成"
                            
                        else:  # 過去問抽出モード
                            # 選択されたモデルで過去問抽出器を再初期化
                            past_extractor = PastQuestionExtractor(session, model_name=past_selected_model)
                            
                            # 過去問抽出実行
                            status_text.text("過去問を抽出中...")
                            progress_bar.progress(0.3)
                            
                            generated_ids = past_extractor.extract_past_questions_from_pdf(
                                text=extracted_text,
                                category=pdf_category,
                                progress_callback=pdf_progress_callback
                            )
                            mode_text = "抽出"
                        
                        # 成功処理
                        if generated_ids:
                            progress_bar.progress(1.0)
                            status_text.text(f"PDF{mode_text}完了！")
                            
                            # プログレス表示を消去
                            progress_bar.empty()
                            status_text.empty()
                            
                            st.success(f"✅ {len(generated_ids)}問の問題を{mode_text}しました！")
                            
                            # 統計情報表示
                            total_choices = 0
                            for qid in generated_ids:
                                choices = choice_service.get_choices_by_question(qid)
                                total_choices += len(choices)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("問題数", len(generated_ids))
                            with col2:
                                st.metric("選択肢数", total_choices)
                            with col3:
                                avg_choices = total_choices / len(generated_ids) if generated_ids else 0
                                st.metric("平均選択肢数", f"{avg_choices:.1f}")
                            
                            # 生成された問題の詳細表示
                            with st.expander("📋 生成された問題の詳細", expanded=True):
                                for i, qid in enumerate(generated_ids):
                                    st.markdown(f"### 問題 {i+1} (ID: {qid})")
                                    
                                    # 問題の詳細を表示
                                    question = question_service.get_question_by_id(qid)
                                    if question:
                                        st.markdown(f"**タイトル:** {question.title}")
                                        st.markdown(f"**カテゴリ:** {question.category}")
                                        st.markdown(f"**難易度:** {question.difficulty}")
                                        st.markdown(f"**問題文:** {question.content}")
                                        
                                        # 選択肢を表示
                                        choices = choice_service.get_choices_by_question(qid)
                                        if choices:
                                            st.markdown("**選択肢:**")
                                            choice_labels = ['A', 'B', 'C', 'D', 'E', 'F']
                                            for idx, choice in enumerate(sorted(choices, key=lambda x: x.order_num)):
                                                label = choice_labels[idx] if idx < len(choice_labels) else str(idx + 1)
                                                correct_mark = " ✅" if choice.is_correct else ""
                                                st.markdown(f"{label}. {choice.content}{correct_mark}")
                                        else:
                                            st.warning("⚠️ 選択肢が見つかりませんでした")
                                        
                                        # 解説表示
                                        if question.explanation:
                                            st.markdown(f"**解説:** {question.explanation}")
                                        else:
                                            st.info("解説は生成されませんでした")
                                        
                                        st.markdown("---")
                            
                            # 問題一覧への移動ボタン
                            if st.button("📝 問題一覧で確認", type="secondary", use_container_width=True):
                                st.info("問題一覧タブで生成された問題を確認できます")
                        else:
                            st.error(f"❌ PDF{mode_text}に失敗しました")
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ エラーが発生しました: {str(e)}")
                        st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか確認してください。")
        
        except Exception as e:
            st.error(f"❌ PDF機能でエラーが発生しました: {e}")
            st.info("💡 必要なライブラリがインストールされているか確認してください。")
