"""
問題管理ページ - 問題の一覧表示、AI生成、PDF処理、重複検査
"""
import streamlit as st
import time
import datetime
from datetime import datetime

def render_question_management_page():
    """問題管理ページのメイン表示"""
    st.title("🔧 問題管理")
    
    # リアルタイムでデータベース接続をチェック
    from config.app_config import check_database_connection
    db_available, db_error = check_database_connection()
    
    if not db_available:
        st.error("⚠️ データベースに接続できないため、問題管理機能は利用できません。")
        if db_error:
            with st.expander("🔍 詳細エラー情報"):
                st.error(db_error)
        render_demo_management()
        return
    
    try:
        from database.operations import QuestionService, ChoiceService
        from database.connection import get_session_context
        
        with get_session_context() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            
            # タブで機能を分割
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📝 問題一覧", 
                "🤖 AI問題生成", 
                "📄 PDF問題生成", 
                "🔍 重複検査", 
                "📊 生成統計"
            ])
            
            with tab1:
                render_question_list_tab(question_service, choice_service)
            
            with tab2:
                render_ai_generation_tab(session)
            
            with tab3:
                render_pdf_generation_tab(session)
            
            with tab4:
                render_duplicate_check_tab(question_service)
            
            with tab5:
                render_generation_stats_tab(question_service)
                
    except Exception as e:
        st.error(f"問題管理機能でエラーが発生しました: {e}")
        render_demo_management()

def render_question_list_tab(question_service, choice_service):
    """問題一覧タブ"""
    st.markdown("### 📝 問題一覧・管理")    # 削除成功メッセージの表示（最初に表示）
    if st.session_state.get('deletion_success', False):
        deleted_info = st.session_state.get('deleted_question_info', {})
        
        # 目立つ成功メッセージ（背景色付き）
        st.markdown("""
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 10px 0;">
            <h4 style="color: #155724; margin: 0;">🎉 削除完了!</h4>
            <p style="color: #155724; margin: 5px 0;">問題ID <strong>{}</strong> 「<strong>{}</strong>」を正常に削除しました</p>
        </div>
        """.format(deleted_info.get('id', 'Unknown'), deleted_info.get('title', 'Unknown')), unsafe_allow_html=True)
        
        # 削除された問題の詳細情報
        with st.expander("🔍 削除された問題の詳細情報", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**問題ID:** {deleted_info.get('id', 'Unknown')}")
                st.markdown(f"**タイトル:** {deleted_info.get('title', 'Unknown')}")
                st.markdown(f"**カテゴリ:** {deleted_info.get('category', 'Unknown')}")
            with col2:
                st.markdown(f"**削除時刻:** {deleted_info.get('deletion_time', 'Unknown')}")
                st.markdown(f"**削除前の総問題数:** {deleted_info.get('total_before', 0)}")
                st.markdown(f"**削除後の総問題数:** {deleted_info.get('total_after', 0)}")
        
        # 数値の変化を強調表示
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 **データベース更新:** {deleted_info.get('total_before', 0)} 問 → {deleted_info.get('total_after', 0)} 問 (削除数: {deleted_info.get('deleted_count', 1)})")
        with col2:
            if st.button("✖️ 閉じる", key="close_deletion_message"):
                del st.session_state['deletion_success']
                if 'deleted_question_info' in st.session_state:
                    del st.session_state['deleted_question_info']
                st.rerun()
        
        st.markdown("---")
      # フィルター設定
    col1, col2, col3 = st.columns(3)
    
    # 全問題を取得してカテゴリリストを作成（削除後は強制再取得）
    cache_key = f"questions_cache_{st.session_state.get('deletion_success_count', 0)}"
    if cache_key not in st.session_state:
        all_questions = question_service.get_random_questions(limit=1000)
        # SQLModelオブジェクトを辞書に変換してセッション管理エラーを防止
        from database.connection import models_to_dicts
        all_questions_dicts = models_to_dicts(all_questions)
        st.session_state[cache_key] = all_questions_dicts
    else:
        all_questions_dicts = st.session_state[cache_key]
    
    categories = sorted(list(set(q['category'] for q in all_questions_dicts)))
    difficulties = ["all", "easy", "medium", "hard"]
    
    with col1:
        selected_category = st.selectbox(
            "カテゴリでフィルター",
            ["all"] + categories,
            format_func=lambda x: "すべて" if x == "all" else x,
            key="filter_category"
        )
    
    with col2:
        selected_difficulty = st.selectbox(
            "難易度でフィルター",
            difficulties,            format_func=lambda x: {
                "all": "すべて",
                "easy": "初級",
                "medium": "中級",
                "hard": "上級"
            }[x],
            key="filter_difficulty"
        )
    
    with col3:
        per_page = st.selectbox("表示件数", [10, 20, 50, 100], index=1, key="per_page")    # フィルター適用
    filtered_questions = all_questions_dicts
    if selected_category != "all":
        filtered_questions = [q for q in filtered_questions if q['category'] == selected_category]
    if selected_difficulty != "all":
        filtered_questions = [q for q in filtered_questions if q['difficulty'] == selected_difficulty]
    
    st.markdown(f"**表示中: {len(filtered_questions)}問 / 全体: {len(all_questions_dicts)}問**")
    
    # ページネーション
    total_pages = (len(filtered_questions) + per_page - 1) // per_page if filtered_questions else 1
    if total_pages > 1:
        page_num = st.number_input("ページ", min_value=1, max_value=total_pages, value=1, key="page_num") - 1
    else:
        page_num = 0
    
    start_idx = page_num * per_page
    end_idx = min(start_idx + per_page, len(filtered_questions))
    current_questions = filtered_questions[start_idx:end_idx]
    
    # 問題表示
    for i, question in enumerate(current_questions):
        with st.expander(f"**{question['title']}** ({question['category']} / {question['difficulty']})"):
            st.markdown(f"**問題ID:** {question['id']}")
            st.markdown(f"**内容:** {question['content']}")              # 選択肢表示
            choices = choice_service.get_choices_by_question_id(question['id'])
            if choices:
                st.markdown("**選択肢:**")
                # 正解の数をカウント
                correct_count = sum(1 for choice in choices if choice.is_correct)
                # 複数正解の場合はマーカーを表示
                if correct_count > 1:
                    st.markdown("🔄 **複数正解問題**")
                
                for j, choice in enumerate(choices):
                    correct_mark = " ✅" if choice.is_correct else ""
                    st.markdown(f"{chr(65+j)}. {choice.content}{correct_mark}")
            
            if question['explanation']:
                st.markdown(f"**解説:** {question['explanation']}")
              
            # 検証結果の表示（もしあれば）
            verification_key = f"verification_result_{question['id']}"
            if verification_key in st.session_state:
                verification_result = st.session_state[verification_key]
                render_verification_result(verification_result)
              # 編集・削除・検証ボタン
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"✏️ 編集", key=f"edit_{question['id']}"):
                    render_edit_question_modal(question, question_service, choice_service)
            with col2:
                render_delete_question_button(question, question_service)
            
            with col3:
                render_verify_question_button(question, choices)
                
# --- 不正な問題抽出・一括削除 ---
    st.markdown("---")
    st.markdown("### 🚨 不正な問題の抽出・一括削除")
    
    # 抽出処理中のフラグをチェック
    extraction_in_progress = st.session_state.get('extraction_in_progress', False)
    
    if st.button("🔍 不正な問題を抽出", key="extract_invalid_questions", disabled=extraction_in_progress):
        # 処理開始フラグを設定
        st.session_state['extraction_in_progress'] = True
        st.rerun()
    
    # 抽出処理中の表示
    if extraction_in_progress:
        with st.spinner("不正な問題を検索中..."):
            try:
                # 少し時間をかけて検索処理を実行
                import time
                time.sleep(0.5)  # UIの表示を確実にする
                
                invalid_questions = question_service.get_invalid_questions()
                invalid_question_ids = [q.id for q in invalid_questions]
                st.session_state['invalid_questions'] = invalid_question_ids
                
                # 処理完了フラグをクリア
                st.session_state['extraction_in_progress'] = False
                
                # 結果をセッション状態に保存
                if invalid_question_ids:
                    st.session_state['extraction_result'] = f"🔍 検索完了: {len(invalid_question_ids)} 件の不正な問題が見つかりました"
                    st.session_state['extraction_success'] = True
                else:
                    st.session_state['extraction_result'] = "✅ 不正な問題は見つかりませんでした"
                    st.session_state['extraction_success'] = True
                
                # ページを再描画して結果を表示
                st.rerun()
                
            except Exception as e:
                st.session_state['extraction_in_progress'] = False
                st.session_state['extraction_result'] = f"不正な問題の抽出中にエラーが発生しました: {e}"
                st.session_state['extraction_success'] = False
                st.rerun()
    
    # 抽出結果の表示
    if st.session_state.get('extraction_success', False):
        result_message = st.session_state.get('extraction_result', '')
        if 'エラー' in result_message:
            st.error(result_message)
        elif '見つかりませんでした' in result_message:
            st.info(result_message)
        else:
            st.success(result_message)
        
        # 結果表示後にフラグをクリア（次回用）
        if st.button("✖️ メッセージを閉じる", key="close_extraction_result"):
            st.session_state.pop('extraction_result', None)
            st.session_state.pop('extraction_success', None)
            st.rerun()
    
    # 不正な問題の一括削除UI
    invalid_ids = st.session_state.get('invalid_questions', [])
    if invalid_ids:
        try:
            invalid_questions = [q for q in question_service.get_all_questions() if q.id in invalid_ids]
            st.warning(f"不正な問題が {len(invalid_questions)} 件見つかりました。下記リストから選択して一括削除できます。")
            
            # 不正な問題の詳細表示
            with st.expander("🔍 不正な問題の詳細を確認", expanded=False):
                for q in invalid_questions:
                    st.markdown(f"**ID {q.id}:** {q.title} ({q.category})")
                    # 不正な理由も表示できるように
                    try:
                        choices = choice_service.get_choices_by_question_id(q.id)
                        if not choices or len(choices) == 0:
                            st.error("→ 理由: 選択肢が存在しません")
                        elif not any(c.is_correct for c in choices):
                            st.error("→ 理由: 正解が設定されていません")
                        elif len([c for c in choices if c.is_correct]) > 4:
                            st.warning("→ 理由: 正解が多すぎます（5個以上）")
                        else:
                            # 詳細な理由チェック
                            if not q.content or q.content.strip() == "":
                                st.error("→ 理由: 問題文が空です")
                            elif not q.explanation or str(q.explanation).strip() == "":
                                st.error("→ 理由: 解説が空です")
                            elif len(choices) > 4:
                                st.warning("→ 理由: 選択肢が多すぎます（5個以上）")
                    except Exception as e:
                        st.error(f"→ 理由チェック中にエラー: {e}")
            
            selected_ids = st.multiselect(
                "削除対象の問題IDを選択（複数選択可）",
                [q.id for q in invalid_questions],
                default=[q.id for q in invalid_questions],
                format_func=lambda x: f"ID {x} : {next((q.title for q in invalid_questions if q.id==x), '')}"
            )
            
            if selected_ids:
                st.info(f"選択中: {len(selected_ids)} 件の問題が削除対象です")
                
                if st.button("🗑️ 選択した不正な問題を一括削除", key="delete_invalid_questions"):
                    with st.spinner("削除処理中..."):
                        deleted = 0
                        failed = 0
                        for qid in selected_ids:
                            try:
                                if question_service.delete_question(qid):
                                    deleted += 1
                                else:
                                    failed += 1
                            except Exception as e:
                                st.error(f"問題ID {qid} の削除でエラー: {e}")
                                failed += 1
                        
                        if deleted > 0:
                            st.success(f"✅ {deleted}件の不正な問題を削除しました！")
                        if failed > 0:
                            st.warning(f"⚠️ {failed}件の削除に失敗しました")
                        
                        # セッション状態をクリア
                        st.session_state.pop('invalid_questions', None)
                        st.session_state.pop('extraction_result', None)
                        st.session_state.pop('extraction_success', None)
                        
                        # キャッシュをクリア
                        for key in list(st.session_state.keys()):
                            if key.startswith('questions_cache_'):
                                del st.session_state[key]
                        
                        st.rerun()
            else:
                st.info("削除する問題を選択してください")
                
        except Exception as e:
            st.error(f"不正な問題の表示中にエラーが発生しました: {e}")
    else:
        # 抽出済みでない場合の説明
        if not st.session_state.get('extraction_success', False):
            st.info("👆 上のボタンをクリックして、不正な問題（選択肢がない、正解がない等）を抽出できます")
    st.markdown("---")
    # --- ここまで不正な問題抽出 ---

def render_ai_generation_tab(session):
    """AI問題生成タブ"""
    st.markdown("### 🤖 AI問題生成")
    try:
        from services.question_generator import EnhancedQuestionGenerator as QuestionGenerator
        from database.operations import QuestionService
        # --- カテゴリ一覧取得 ---
        if 'ai_categories' not in st.session_state:
            question_service = QuestionService(session)
            db_categories = question_service.get_all_categories()
            # デフォルトカテゴリも含める（重複排除）
            default_categories = [
                "基本情報技術者", "応用情報技術者", "プログラミング基礎", "データベース",
                "ネットワーク", "セキュリティ", "AI・機械学習", "プロジェクトマネジメント"
            ]
            categories = list(dict.fromkeys(default_categories + db_categories))
            st.session_state['ai_categories'] = categories
        categories = st.session_state['ai_categories']

        # --- 新規カテゴリ追加UI ---
        with st.expander("🆕 新しいカテゴリを追加する"):
            new_category = st.text_input("新規カテゴリ名", key="new_ai_category")
            if st.button("カテゴリを追加", key="add_ai_category_btn"):
                if new_category and new_category not in categories:
                    st.session_state['ai_categories'].append(new_category)
                    st.success(f"カテゴリ『{new_category}』を追加しました！")
                elif new_category in categories:
                    st.warning("すでに存在するカテゴリです")
                else:
                    st.warning("カテゴリ名を入力してください")

        # 生成パラメータ設定
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**生成パラメータ**")
            gen_col1, gen_col2, gen_col3 = st.columns(3)
            with gen_col1:
                category = st.selectbox(
                    "カテゴリ",
                    categories,
                    key="ai_category"
                )
            with gen_col2:
                difficulty = st.selectbox(
                    "難易度",
                    ["easy", "medium", "hard"],
                    format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                    key="ai_difficulty"
                )
            with gen_col3:
                count = st.slider("生成問題数", min_value=1, max_value=10, value=1, key="ai_count")
            topic = st.text_area(
                "特定のトピック（任意）",
                placeholder="例: オブジェクト指向プログラミング、データベース正規化",
                height=100,
                key="ai_topic"
            )
            # 詳細オプション
            with st.expander("🔧 詳細オプション"):
                model_options = {
                    "gpt-3.5-turbo": "GPT-3.5 Turbo (高速・経済的)",
                    "gpt-4o-mini": "GPT-4o Mini (高品質・バランス)",
                    "gpt-4o": "GPT-4o (最高品質)",
                    "gpt-4": "GPT-4 (最高品質・詳細)"
                }
                selected_model = st.selectbox(
                    "使用するAIモデル",
                    options=list(model_options.keys()),
                    format_func=lambda x: model_options[x],
                    index=0,
                    key="ai_model"
                )
                include_explanation = st.checkbox("解説を含める", value=True, key="ai_explanation")
                enable_duplicate_check = st.checkbox("重複チェックを有効にする", value=True, key="ai_duplicate_check")
                allow_multiple_correct = st.checkbox("複数正解問題を生成可能にする", value=False, 
                                                  help="チェックすると複数の正解を持つ問題が生成される可能性があります。チェックしない場合は1つの正解のみの問題が生成されます。", 
                                                  key="ai_multiple_correct")
        with col2:
            st.markdown("**生成履歴**")
            if 'generation_history' in st.session_state and st.session_state.generation_history:
                for entry in st.session_state.generation_history[-5:]:
                    st.text(f"{entry['time']}: {entry['count']}問生成")
            else:
                st.text("履歴なし")
          # 生成実行
        if st.button("🎲 問題を生成", type="primary", use_container_width=True, key="generate_ai"):
            with st.spinner("問題を生成中..."):
                try:
                    generator = QuestionGenerator(session, model=selected_model)
                    
                    # 生成実行
                    if count == 1:
                        question_id = generator.generate_and_save_question(
                            category=category,
                            difficulty=difficulty,
                            topic=topic if topic else None,
                            allow_multiple_correct=allow_multiple_correct
                        )
                        generated_ids = [question_id] if question_id else []
                    else:
                        topics_list = [t.strip() for t in topic.split('\n') if t.strip()] if topic else None
                        generated_ids = generator.generate_and_save_multiple_questions(
                            category=category,
                            difficulty=difficulty,
                            count=count,
                            topics=topics_list,
                            allow_multiple_correct=allow_multiple_correct
                        )
                    
                    if generated_ids:
                        st.success(f"✅ {len(generated_ids)}問の問題を生成しました！")
                        
                        # 生成された問題の詳細表示
                        with st.expander("📋 生成された問題の詳細", expanded=True):
                            from database.operations import QuestionService, ChoiceService
                            question_service = QuestionService(session)
                            choice_service = ChoiceService(session)
                            
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
                                        # 正解の数をカウント
                                        correct_count = sum(1 for choice in choices if choice.is_correct)
                                        # 複数正解の場合はマーカーを表示
                                        if correct_count > 1:
                                            st.markdown("🔄 **複数正解問題**")
                                        
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
                            if st.button("📝 問題一覧で確認", type="secondary", use_container_width=True, key="ai_view_list"):
                                st.info("問題一覧タブで生成された問題を確認できます")
                        
                        # 生成履歴に追加
                        if 'generation_history' not in st.session_state:
                            st.session_state.generation_history = []
                        
                        import datetime
                        st.session_state.generation_history.append({
                            'time': datetime.datetime.now().strftime('%H:%M:%S'),
                            'count': len(generated_ids),
                            'category': category,
                            'difficulty': difficulty
                        })
                    else:
                        st.error("問題の生成に失敗しました")
                        
                except Exception as e:
                    st.error(f"問題生成でエラーが発生しました: {e}")
                    
    except ImportError:
        st.error("AI問題生成機能が利用できません（QuestionGeneratorがインポートできません）")

def render_pdf_generation_tab(session):
    """PDF問題生成・抽出タブ"""
    st.markdown("### 📄 PDF問題処理")
    
    # 処理方法の選択
    processing_method = st.radio(
        "処理方法を選択してください",
        options=[
            "📄 PDF問題抽出（既存問題の抽出）",
            "🤖 AI問題生成（PDF内容基準）"
        ],
        help="📄 抽出: PDFから既存の問題・選択肢・解答を読み取り\n🤖 生成: PDFの内容を参考にAIが新しい問題を作成",
        key="pdf_processing_method"
    )
    
    st.markdown("---")
    
    if processing_method == "📄 PDF問題抽出（既存問題の抽出）":
        render_pdf_extraction_section(session)
    else:
        render_pdf_ai_generation_section(session)


def render_pdf_extraction_section(session):
    """PDF問題抽出セクション"""
    st.markdown("### 📄 PDF問題抽出")
    st.markdown("**過去問PDFから既存の問題・選択肢・解答・解説を抽出して問題を作成します**")
    
    try:
        from services.pdf_processor import PDFProcessor
        from services.pdf_question_extractor import PDFQuestionExtractor
        
        # PDFファイルアップロード
        uploaded_file = st.file_uploader(
            "過去問PDFファイルを選択してください",
            type=['pdf'],
            help="最大50MBまでのPDFファイルをアップロードできます",
            key="pdf_uploader"
        )
        
        if uploaded_file is not None:
            # ファイル情報表示
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ファイル名", uploaded_file.name)
            with col2:
                st.metric("ファイルサイズ", f"{uploaded_file.size / 1024:.1f} KB")
            with col3:
                st.metric("ファイル形式", "PDF")            # 抽出パラメータ（PDF抽出用）
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pdf_category = st.text_input(
                    "問題カテゴリ",
                    value="PDF教材",
                    help="抽出された問題に設定するカテゴリ",
                    key="pdf_extract_category"
                )
            
            with col2:
                max_questions = st.number_input(
                    "最大抽出問題数",
                    min_value=1, max_value=100, value=20,
                    help="抽出する問題の最大数（制限なしの場合は大きな数値に設定）",
                    key="pdf_max_questions"
                )
            
            with col3:
                enable_unlimited = st.checkbox(
                    "制限なし",
                    value=False,
                    help="チェックすると全ての問題を抽出します",
                    key="pdf_unlimited"
                )
              # 詳細オプション
            with st.expander("🔧 詳細オプション"):
                col1, col2 = st.columns(2)
                with col1:
                    similarity_threshold = st.slider(
                        "重複判定閾値",
                        min_value=0.5, max_value=1.0, value=0.8, step=0.05,
                        help="この値より高い類似度の問題は重複として判定されます",
                        key="pdf_extract_similarity"
                    )
                with col2:
                    enable_duplicate_check = st.checkbox(
                        "重複チェックを有効にする", 
                        value=True,
                        help="既存問題との重複をチェックしてスキップします",
                        key="pdf_extract_duplicate_check"
                    )
            
            # プライバシー保護の確認
            privacy_confirmed = st.checkbox(
                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                help="PDFファイルはローカルで処理され、外部に送信されません",
                key="pdf_privacy"            )
            
            if st.button("🎯 PDFから問題を抽出", disabled=not privacy_confirmed, key="extract_pdf"):
                if not privacy_confirmed:
                    st.warning("⚠️ プライバシー保護設定への同意が必要です")
                    return
                
                with st.spinner("PDFから問題を抽出中..."):
                    try:
                        # PDF処理と問題抽出
                        pdf_processor = PDFProcessor()
                        pdf_extractor = PDFQuestionExtractor(session)
                        
                        # テキスト抽出
                        uploaded_file.seek(0)
                        file_bytes = uploaded_file.read()
                        extracted_text = pdf_processor.extract_text_auto(file_bytes)
                        
                        if not extracted_text:
                            st.error("PDFからテキストを抽出できませんでした")
                            return
                        
                        # テキストのプレビュー表示
                        with st.expander("📖 抽出されたテキスト（最初の500文字）"):
                            st.text(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                        
                        # 進捗表示用コンテナ
                        progress_container = st.empty()
                        
                        def progress_callback(message, progress):
                            progress_container.progress(progress, text=message)                        # 問題抽出実行
                        final_max_questions = None if enable_unlimited else max_questions
                        
                        extracted_ids = pdf_extractor.extract_questions_from_pdf(
                            text=extracted_text,
                            category=pdf_category,
                            max_questions=final_max_questions,
                            progress_callback=progress_callback,
                            enable_duplicate_check=enable_duplicate_check,
                            similarity_threshold=similarity_threshold
                        )
                        
                        progress_container.empty()
                        
                        if extracted_ids:
                            st.success(f"✅ {len(extracted_ids)}問の問題を抽出・保存しました！")
                            
                            # 抽出された問題の詳細表示
                            with st.expander("📋 抽出された問題の詳細", expanded=True):
                                from database.operations import QuestionService, ChoiceService
                                question_service = QuestionService(session)
                                choice_service = ChoiceService(session)
                                
                                for i, qid in enumerate(extracted_ids):
                                    st.markdown(f"### 問題 {i+1} (ID: {qid})")
                                    
                                    # 問題の詳細を表示
                                    question = question_service.get_question_by_id(qid)
                                    if question:
                                        st.markdown(f"**タイトル:** {question.title}")
                                        st.markdown(f"**カテゴリ:** {question.category}")
                                        st.markdown(f"**難易度:** {question.difficulty}")
                                        st.markdown(f"**問題文:** {question.content}")
                                        
                                        # 選択肢を表示
                                        choices = choice_service.get_choices_by_question_id(qid)
                                        if choices:
                                            st.markdown("**選択肢:**")
                                            # 正解の数をカウント
                                            correct_count = sum(1 for choice in choices if choice.is_correct)
                                            
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
                                            st.info("解説は抽出されませんでした")
                                        
                                        st.markdown("---")
                        else:
                            st.warning("PDFから問題を抽出できませんでした。問題の形式を確認してください。")
                            st.markdown("**対応している問題形式:**")
                            st.markdown("- 問1、問2...形式")
                            st.markdown("- Q1、Q2...形式") 
                            st.markdown("- 1.、2.、...形式")
                            st.markdown("- 選択肢：(1)(2)(3)(4)、ア/イ/ウ/エ、A/B/C/D、①②③④")
                    
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
                        print(f"PDF抽出エラー: {e}")
        
        else:
            st.info("PDFファイルをアップロードしてください")
            st.markdown("**PDF問題抽出について:**")
            st.markdown("- 過去問PDFから既存の問題・選択肢・解答・解説を自動抽出")
            st.markdown("- 複数の問題形式に対応（問1形式、Q1形式、番号形式等）")
            st.markdown("- 重複チェック機能で既存問題との重複を防止")
            st.markdown("- ローカル処理でプライバシー保護")
    
    except ImportError as e:
        st.error(f"必要なライブラリがインストールされていません: {e}")
    except Exception as e:
        st.error(f"PDF問題抽出機能でエラーが発生しました: {e}")

def render_pdf_ai_generation_section(session):
    """PDF内容基準AI問題生成セクション"""
    st.markdown("### 🤖 AI問題生成（PDF内容基準）")
    st.markdown("**PDFの内容を参考にして、AIが新しい問題を生成します**")
    
    try:
        from services.pdf_processor import PDFProcessor
        from services.pdf_question_generator import PDFQuestionGenerator
        
        # PDFファイルアップロード
        uploaded_file = st.file_uploader(
            "参考資料PDFファイルを選択してください",
            type=['pdf'],
            help="最大50MBまでのPDFファイルをアップロードできます",
            key="pdf_ai_uploader"
        )
        
        if uploaded_file is not None:
            # ファイル情報表示
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ファイル名", uploaded_file.name)
            with col2:
                st.metric("ファイルサイズ", f"{uploaded_file.size / 1024:.1f} KB")
            with col3:
                st.metric("ファイル形式", "PDF")
            
            # 生成パラメータ
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pdf_num_questions = st.slider("生成問題数", min_value=1, max_value=30, value=5, key="pdf_ai_questions")
            
            with col2:
                pdf_difficulty = st.selectbox(
                    "難易度",
                    ["easy", "medium", "hard"],
                    format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                    index=1,
                    key="pdf_ai_difficulty"
                )
            
            with col3:
                pdf_category = st.text_input("カテゴリ名", "PDF教材", key="pdf_ai_category")
            
            # 詳細オプション
            with st.expander("🔧 詳細オプション"):
                model_options = {
                    "gpt-3.5-turbo": "GPT-3.5 Turbo (高速・経済的)",
                    "gpt-4o-mini": "GPT-4o Mini (高品質・バランス)",
                    "gpt-4o": "GPT-4o (最高品質)",
                    "gpt-4": "GPT-4 (最高品質・詳細)"
                }
                
                pdf_selected_model = st.selectbox(
                    "使用するAIモデル",
                    options=list(model_options.keys()),
                    format_func=lambda x: model_options[x],
                    index=1,
                    key="pdf_ai_model"
                )
                
                pdf_include_explanation = st.checkbox("解説を含める", value=True, key="pdf_ai_explanation")
                pdf_allow_multiple_correct = st.checkbox(
                    "複数正解問題を生成可能にする", 
                    value=False,
                    help="チェックすると複数の正解を持つ問題が生成される可能性があります",
                    key="pdf_ai_multiple_correct"
                )
            
            # プライバシー保護の確認
            privacy_confirmed = st.checkbox(
                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません",
                key="pdf_ai_privacy"
            )
            
            if st.button("🎯 AIで問題を生成", disabled=not privacy_confirmed, key="generate_pdf_ai"):
                if not privacy_confirmed:
                    st.warning("⚠️ プライバシー保護設定への同意が必要です")
                    return
                
                with st.spinner("AIが問題を生成中..."):
                    try:
                        # PDF処理と問題生成
                        pdf_processor = PDFProcessor()
                        pdf_generator = PDFQuestionGenerator(session, model_name=pdf_selected_model)
                        
                        # テキスト抽出
                        uploaded_file.seek(0)
                        file_bytes = uploaded_file.read()
                        extracted_text = pdf_processor.extract_text_auto(file_bytes)
                        
                        if not extracted_text:
                            st.error("PDFからテキストを抽出できませんでした")
                            return
                        
                        # テキストのプレビュー表示
                        with st.expander("📖 抽出されたテキスト（最初の500文字）"):
                            st.text(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                        
                        # 進捗表示用コンテナ
                        progress_container = st.empty()
                        
                        def progress_callback(message, progress):
                            progress_container.progress(progress, text=message)
                        
                        # AI問題生成実行
                        generated_ids = pdf_generator.generate_questions_from_pdf(
                            text=extracted_text,
                            num_questions=pdf_num_questions,
                            difficulty=pdf_difficulty,
                            category=pdf_category,
                            model=pdf_selected_model,
                            include_explanation=pdf_include_explanation,
                            progress_callback=progress_callback,
                            allow_multiple_correct=pdf_allow_multiple_correct
                        )
                        
                        progress_container.empty()
                        
                        if generated_ids:
                            st.success(f"✅ {len(generated_ids)}問の問題を生成しました！")
                            
                            # 生成された問題の詳細表示
                            with st.expander("📋 生成された問題の詳細", expanded=True):
                                from database.operations import QuestionService, ChoiceService
                                question_service = QuestionService(session)
                                choice_service = ChoiceService(session)
                                
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
                                        choices = choice_service.get_choices_by_question_id(qid)
                                        if choices:
                                            st.markdown("**選択肢:**")
                                            # 正解の数をカウント
                                            correct_count = sum(1 for choice in choices if choice.is_correct)
                                            # 複数正解の場合はマーカーを表示
                                            if correct_count > 1:
                                                st.markdown("🔄 **複数正解問題**")
                                        
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
                        else:
                            st.error("問題の生成に失敗しました")
                    
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
                        print(f"PDF AI生成エラー: {e}")
        
        else:
            st.info("PDFファイルをアップロードしてください")
    
    except ImportError as e:
        st.error(f"必要なライブラリがインストールされていません: {e}")
    except Exception as e:
        st.error(f"PDF AI問題生成機能でエラーが発生しました: {e}")

def render_duplicate_check_tab(question_service):
    """重複検査タブ"""
    st.markdown("### 🔍 重複検査")
    
    st.info("重複検査機能は今後実装予定です")
    
    # 統計情報の表示を停止（エラー回避のため）
    # try:
    #     all_questions = question_service.get_random_questions(limit=1000)
    #     st.metric("総問題数", len(all_questions))
    #     categories = {}
    #     for q in all_questions:
    #         categories[q.category] = categories.get(q.category, 0) + 1
    #     if categories:
    #         st.markdown("**カテゴリ別問題数:**")
    #         for category, count in sorted(categories.items()):
    #             st.markdown(f"- {category}: {count}問")
    # except Exception as e:
    #     st.error(f"統計情報の取得でエラーが発生しました: {e}")


def render_generation_stats_tab(question_service):
    """生成統計タブ"""
    st.markdown("### 📊 生成統計")
    
    st.info("現在、統計情報の表示は一時的に停止しています（エラー回避のため）")
    # 統計情報の表示を停止（エラー回避のため）
    # try:
    #     all_questions = question_service.get_random_questions(limit=1000)
    #     # 基本統計
    #     col1, col2, col3 = st.columns(3)
    #     with col1:
    #         st.metric("総問題数", len(all_questions))
    #     with col2:
    #         categories = len(set(q.category for q in all_questions))
    #         st.metric("カテゴリ数", categories)
    #     with col3:
    #         difficulties = len(set(q.difficulty for q in all_questions))
    #         st.metric("難易度数", difficulties)
    #     # カテゴリ別統計
    #     if all_questions:
    #         st.markdown("### 📚 カテゴリ別統計")
    #         category_stats = {}
    #         difficulty_stats = {}
    #         for q in all_questions:
    #             category_stats[q.category] = category_stats.get(q.category, 0) + 1
    #             difficulty_stats[q.difficulty] = difficulty_stats.get(q.difficulty, 0) + 1
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             st.markdown("**カテゴリ別分布:**")
    #             for category, count in sorted(category_stats.items()):
    #                 percentage = (count / len(all_questions)) * 100
    #                 st.markdown(f"- {category}: {count}問 ({percentage:.1f}%)")
    #         with col2:
    #             st.markdown("**難易度別分布:**")
    #             for difficulty, count in sorted(difficulty_stats.items()):
    #                 percentage = (count / len(all_questions)) * 100
    #                 difficulty_name = {"easy": "初級", "medium": "中級", "hard": "上級"}.get(difficulty, difficulty)
    #                 st.markdown(f"- {difficulty_name}: {count}問 ({percentage:.1f}%)")
    # except Exception as e:
    #     st.error(f"統計情報の取得でエラーが発生しました: {e}")

def render_demo_management():
    """デモモード用の問題管理表示"""
    st.info("🔄 デモモードで問題管理を表示しています。")
    
    # デモ用の統計情報
    st.markdown("### 📊 問題統計（デモ）")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("総問題数", 150)
    
    with col2:
        st.metric("カテゴリ数", 8)
    
    with col3:
        st.metric("生成済み問題", 45)
    
    # デモ用の問題一覧
    st.markdown("### 📝 問題例（デモ）")
    
    demo_questions = [
        {"title": "プログラミング基礎1", "category": "プログラミング", "difficulty": "easy"},
        {"title": "データベース設計", "category": "データベース", "difficulty": "medium"},
        {"title": "ネットワーク理論", "category": "ネットワーク", "difficulty": "hard"}
    ]
    
    for i, q in enumerate(demo_questions):
        with st.expander(f"{q['title']} ({q['category']} / {q['difficulty']})"):
            st.markdown("**デモ問題:** これはデモ用の問題です。")
            st.markdown("**選択肢:**")
            st.markdown("A. 選択肢1")
            st.markdown("B. 選択肢2 ✅")
            st.markdown("C. 選択肢3")
            st.markdown("D. 選択肢4")

def render_delete_question_button(question, question_service):
    """強化された削除ボタンとモーダル"""
    delete_button_key = f"delete_{question['id']}"
    modal_key = f"delete_modal_{question['id']}"
    confirm_key = f"confirm_delete_{question['id']}"
      # 削除ボタン
    if st.button(f"🗑️ 削除", key=delete_button_key):
        st.session_state[modal_key] = True
    
    # 削除確認モーダル
    if st.session_state.get(modal_key, False):
        with st.container():
            st.markdown("---")
            st.markdown("### ⚠️ 問題削除の確認")
              # 削除対象の情報を強調表示
            with st.container():
                st.error("**🚨 注意: この操作は取り消すことができません**")
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown("**問題ID:**")
                    st.markdown("**タイトル:**")
                    st.markdown("**カテゴリ:**")
                    st.markdown("**難易度:**")
                
                with col2:
                    st.markdown(f"`{question['id']}`")
                    st.markdown(f"`{question['title']}`")
                    st.markdown(f"`{question['category']}`")
                    st.markdown(f"`{question['difficulty']}`")
                
                st.warning("**削除される内容:**")
                st.markdown("- ✅ 問題本文")
                st.markdown("- ✅ すべての選択肢")
                st.markdown("- ✅ 解説")
                st.markdown("- ✅ 関連する回答履歴")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("❌ キャンセル", key=f"cancel_{question['id']}"):
                    st.session_state[modal_key] = False
                    st.session_state[confirm_key] = False
                    st.rerun()
            
            with col2:
                if st.button("🗑️ 削除実行", key=f"confirm_{question['id']}", type="primary"):
                    # 削除前の存在確認
                    try:
                        existing_question = question_service.get_question_by_id(question['id'])
                        if not existing_question:
                            st.error(f"❌ 問題ID {question['id']} がデータベースに見つかりません")
                            st.session_state[modal_key] = False
                            st.rerun()
                            return
                    except Exception as check_error:
                        st.error(f"❌ 問題存在確認エラー: {check_error}")
                        st.session_state[modal_key] = False
                        st.rerun()
                        return
                    
                    # 削除前の状態確認
                    pre_delete_count = question_service.get_question_count()
                      # 削除実行（改良版）
                    with st.spinner("削除処理中..."):
                        try:
                            # トランザクション的に削除を実行
                            deletion_success = question_service.delete_question(question['id'])
                            
                            # 削除結果の検証
                            if deletion_success:
                                # 削除確認：問題が実際に削除されたかチェック
                                verification_check = question_service.get_question_by_id(question['id'])
                                if verification_check is None:
                                    # 削除成功
                                    deletion_success = True
                                else:
                                    # 削除失敗（まだ存在している）
                                    deletion_success = False
                            
                        except Exception as delete_error:
                            st.error(f"削除処理中にエラーが発生しました: {delete_error}")
                            deletion_success = False
                    
                    if deletion_success:
                        # 削除後の状態確認
                        post_delete_count = question_service.get_question_count()
                        
                        # 即座に削除成功メッセージを表示
                        st.toast(f"✅ 問題ID {question['id']} を削除しました", icon="✅")
                          # セッション状態に削除成功情報を保存（複数ページロードで保持）
                        st.session_state['deletion_success'] = True
                        st.session_state['deletion_success_count'] = st.session_state.get('deletion_success_count', 0) + 1
                        st.session_state['deleted_question_info'] = {
                            'id': question['id'],
                            'title': question['title'],
                            'category': question['category'],
                            'total_before': pre_delete_count,
                            'total_after': post_delete_count,
                            'deleted_count': pre_delete_count - post_delete_count,
                            'deletion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 即座に削除成功メッセージを表示
                        st.success(f"✅ **削除完了!** 問題ID {question['id']} 「{question['title']}」を削除しました")
                        st.info(f"📊 問題数: {pre_delete_count} → {post_delete_count} (-{pre_delete_count - post_delete_count})")
                        
                        # データベースからの削除確認
                        try:
                            deleted_question = question_service.get_question_by_id(question['id'])
                            if deleted_question is None:
                                st.success("🔍 **データベース確認:** 問題はデータベースから完全に削除されました")
                            else:
                                st.warning("⚠️ **データベース確認:** 問題がまだデータベースに存在している可能性があります")
                        except Exception:
                            st.success("🔍 **データベース確認:** 問題は正常に削除されました")
                          # セッション状態のクリア                        st.session_state[modal_key] = False
                        st.session_state[confirm_key] = False
                        
                        # キャッシュをクリアして最新データを強制取得
                        for key in list(st.session_state.keys()):
                            if key.startswith('questions_cache_') or key.startswith('delete_modal_'):
                                del st.session_state[key]
                        
                        # 削除成功の即座表示（rerunの前に）
                        st.success("🎉 削除が完了しました！ページを更新します...")
                        
                        # 祝福エフェクト
                        # st.balloons()
                        
                        # 短い待機後にページリロード
                        import time
                        time.sleep(0.5)  # 短縮
                        st.rerun()
                    else:
                        st.error("❌ **削除に失敗しました**")
                        st.error("詳細なエラー情報は、コンソールログを確認してください")
                          # デバッグ情報の表示（expanderを避けてコンテナで表示）
                        st.markdown("---")
                        st.markdown("🔍 **デバッグ情報:**")
                        st.markdown(f"**削除対象の問題ID:** {question['id']}")
                        st.markdown("**可能な原因:**")
                        st.markdown("- 問題がデータベースに存在しない")
                        st.markdown("- 外部キー制約エラー")
                        st.markdown("- データベース接続エラー")
                        st.markdown("- 権限不足")
                        
                        # 問題の存在確認
                        try:
                            existing_question = question_service.get_question_by_id(question['id'])
                            if existing_question:
                                st.info("✅ 問題はデータベースに存在しています")
                            else:
                                st.warning("⚠️ 問題がデータベースに見つかりません")
                        except Exception as debug_error:
                            st.error(f"デバッグチェックエラー: {debug_error}")
                        
                        st.session_state[modal_key] = False
            
            with col3:
                st.markdown("")  # スペース用
            
            st.markdown("---")

def render_edit_question_modal(question, question_service, choice_service):
    """強化された編集モーダル"""
    edit_modal_key = f"edit_modal_{question['id']}"
    # 編集モーダルの表示
    st.session_state[edit_modal_key] = True
    if st.session_state.get(edit_modal_key, False):
        with st.container():
            st.markdown("---")
            st.info("### ✏️ 問題の編集")
            # 現在の問題情報をフォームで表示
            with st.form(f"edit_form_{question['id']}"):
                st.markdown(f"**問題ID:** {question['id']}")
                # 編集可能フィールド
                new_title = st.text_input("タイトル", value=question.get('title', ''))
                new_content = st.text_area("問題文", value=question.get('content', ''), height=100)
                new_category = st.selectbox(
                    "カテゴリ", 
                    ["プログラミング", "データベース", "ネットワーク", "セキュリティ", "その他"],
                    index=0 if question.get('category') == "プログラミング" else 0
                )
                new_difficulty = st.selectbox(
                    "難易度",
                    ["easy", "medium", "hard"],
                    index=["easy", "medium", "hard"].index(question.get('difficulty', 'medium'))
                )
                new_explanation = st.text_area("解説", value=question.get('explanation', ''), height=80)
                
                # 選択肢の編集
                st.markdown("**選択肢:**")
                new_choices = []
                correct_answers = []
                
                try:
                    choices = choice_service.get_choices_by_question_id(question['id'])
                    # 既存の選択肢を表示・編集
                    for i, choice in enumerate(choices):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            choice_content = st.text_input(
                                f"選択肢 {chr(65+i)}",
                                value=choice.content if choice.content else "",
                                key=f"choice_{question['id']}_{i}"
                            )
                            new_choices.append(choice_content)
                        with col2:
                            is_correct = st.checkbox(
                                "正答",
                                value=choice.is_correct,
                                key=f"correct_{question['id']}_{i}"
                            )
                            correct_answers.append(is_correct)
                    
                    # 不足している選択肢を追加（最低4つ）
                    existing_count = len(choices)
                    for i in range(existing_count, 4):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            choice_content = st.text_input(
                                f"選択肢 {chr(65+i)}",
                                value="",
                                key=f"choice_{question['id']}_{i}"
                            )
                            new_choices.append(choice_content)
                        with col2:
                            is_correct = st.checkbox(
                                "正答",
                                value=False,
                                key=f"correct_{question['id']}_{i}"
                            )
                            correct_answers.append(is_correct)
                
                except Exception as e:
                    st.warning(f"選択肢の読み込みエラー: {e}")
                    # デフォルトの選択肢を作成
                    for i in range(4):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            choice_content = st.text_input(
                                f"選択肢 {chr(65+i)}",
                                value="",
                                key=f"choice_{question['id']}_{i}"
                            )
                            new_choices.append(choice_content)
                        with col2:
                            is_correct = st.checkbox(
                                "正答",
                                value=False,
                                key=f"correct_{question['id']}_{i}"
                            )
                            correct_answers.append(is_correct)
                
                # 保存・キャンセルボタン
                submitted = st.form_submit_button("💾 保存", type="primary")
                cancelled = st.form_submit_button("❌ キャンセル")
                
                if submitted:
                    st.write("🚀 保存ボタンが押されました")
                    print(f"デバッグ: 保存処理開始 - 問題ID: {question['id']}")
                    print(f"デバッグ: new_title='{new_title}'")
                    print(f"デバッグ: new_content='{new_content}'")
                    print(f"デバッグ: new_category='{new_category}'")
                    print(f"デバッグ: new_difficulty='{new_difficulty}'")
                    print(f"デバッグ: new_explanation='{new_explanation}'")
                    print(f"デバッグ: new_choices={new_choices}")
                    print(f"デバッグ: correct_answers={correct_answers}")
                    
                    correct_count = sum(correct_answers)
                    st.write(f"正答チェック数: {correct_count}")
                    
                    # 最低限の入力チェック
                    if not new_title.strip():
                        st.error("問題タイトルを入力してください")
                        st.stop()
                    
                    if not new_content.strip():
                        st.error("問題内容を入力してください")
                        st.stop()
                    
                    if correct_count != 1:
                        st.error("正答は1つだけ選択してください")
                        st.stop()
                      # 空でない選択肢の数をチェック
                    non_empty_choices = [choice for choice in new_choices if choice.strip()]
                    if len(non_empty_choices) < 2:
                        st.error("選択肢は最低2つ入力してください")
                        st.stop()
                    
                    try:
                        # 問題本体の更新
                        update_data = {
                            'title': new_title,
                            'content': new_content,
                            'category': new_category,
                            'difficulty': new_difficulty,
                            'explanation': new_explanation
                        }
                        print(f"🔄 問題更新データ: {update_data}")
                        question_success = question_service.update_question(question['id'], update_data)
                        print(f"問題更新結果: {question_success}")
                        
                        if not question_success:
                            st.error("問題の更新に失敗しました")
                            print(f"❌ 問題ID {question['id']} の更新に失敗")
                            st.stop()
                        
                        # 選択肢の更新処理を改善
                        existing_choices = choice_service.get_choices_by_question_id(question['id'])
                        choice_update_success = True
                        
                        # 既存の選択肢を削除
                        deletion_success = True
                        for choice in existing_choices:
                            if not choice_service.delete_choice(choice.id):
                                deletion_success = False
                                print(f"選択肢ID {choice.id} の削除に失敗しました")
                        
                        if not deletion_success:
                            st.warning("一部の選択肢の削除に失敗しましたが、処理を続行します")
                        
                        # 全ての選択肢を最初から作り直す
                        created_choices = []
                        for i, choice_content in enumerate(new_choices):
                            if choice_content.strip():  # 空でない場合のみ作成
                                is_correct_for_choice = correct_answers[i] if i < len(correct_answers) else False
                                try:
                                    new_choice = choice_service.create_choice(
                                        question_id=question['id'],
                                        content=choice_content.strip(),
                                        is_correct=is_correct_for_choice,
                                        order_num=i + 1
                                    )
                                    if new_choice:
                                        created_choices.append(new_choice)
                                        print(f"✓ 選択肢作成成功: {new_choice.id} - {choice_content[:20]}")
                                    else:
                                        choice_update_success = False
                                        print(f"✗ 選択肢作成失敗: {choice_content[:20]}")
                                except Exception as ce:
                                    choice_update_success = False
                                    print(f"選択肢作成エラー: {ce}")
                        
                        # 少なくとも1つの選択肢が作成されたか確認
                        if not created_choices:
                            st.error("選択肢の作成に失敗しました")
                            st.stop()
                        
                        # 保存成功処理
                        if choice_update_success:
                            st.success("✅ 問題と選択肢の更新が完了しました！")
                            print(f"✅ 問題ID {question['id']} の編集が正常に完了しました")
                            
                            # 編集モーダルを閉じる前に成功フラグを設定
                            st.session_state["edit_success"] = True
                            st.session_state["edited_question_id"] = question['id']
                            
                            # キャッシュをクリア
                            for key in list(st.session_state.keys()):
                                if key.startswith('questions_cache_'):
                                    del st.session_state[key]
                            

                            # 編集モーダルを閉じる
                            st.session_state[edit_modal_key] = False
                            

                            # 確実にページを再読み込み
                            time.sleep(0.5)  # 短い待機で状態変更を確実に
                            st.experimental_rerun()  # 推奨される方法でリロード
                        else:
                            # 一部の選択肢が作成されたが全てではない場合
                            if created_choices:
                                st.warning(f"⚠️ {len(created_choices)}個の選択肢が作成されましたが、一部の選択肢の保存に失敗しました")
                                st.info("部分的に保存された変更を確認してください")
                                # 部分的な成功でもモーダルを閉じて再読み込み
                                st.session_state[edit_modal_key] = False
                                st.experimental_rerun()
                            else:
                                st.error("❌ 選択肢の保存に完全に失敗しました")
                        
                    except Exception as e:
                        st.error(f"編集エラー: {e}")
                        print(f"編集エラーの詳細: {e}")  # デバッグ用
                if cancelled:
                    st.session_state[edit_modal_key] = False
                    st.rerun()
            st.markdown("---")

def render_verify_question_button(question, choices):
    """問題検証ボタンの表示（モデル選択付き）"""
    model_key = f"verification_model_{question['id']}"
    model_options = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4o",
        "gpt-4o-mini"
    ]
    # モデル選択UI
    selected_model = st.selectbox(
        "AIモデルを選択",
        model_options,
        key=model_key,
        index=0,
        help="検証に使用するOpenAIモデルを選択してください"
    )

    verification_in_progress_key = f"verification_in_progress_{question['id']}"
    verification_in_progress = st.session_state.get(verification_in_progress_key, False)
    
    if st.button(
        f"🔍 検証", 
        key=f"verify_{question['id']}", 
        disabled=verification_in_progress,
        help="OpenAI APIで問題の品質・整合性を検証します"
    ):
        # 検証処理開始
        st.session_state[verification_in_progress_key] = True
        st.rerun()
    
    # 検証処理中の表示
    if verification_in_progress:
        with st.spinner("🔍 AI検証中..."):
            try:
                # OpenAI APIで検証
                from services.enhanced_openai_service import EnhancedOpenAIService
                # セッションからモデル取得（なければデフォルト）
                model_name = st.session_state.get(model_key, "gpt-3.5-turbo")
                openai_service = EnhancedOpenAIService(model=model_name)
                
                # 選択肢データを構築
                choices_data = []
                if choices:
                    for i, choice in enumerate(choices):
                        choices_data.append({
                            'content': choice.content,
                            'is_correct': choice.is_correct
                        })
                
                # 検証実行
                question_data = {
                    'id': question['id'],
                    'title': question['title'],
                    'content': question['content'],
                    'category': question.get('category', ''),
                    'difficulty': question.get('difficulty', 'medium'),
                    'explanation': question.get('explanation', '')
                }
                
                # 検証を実行
                verification_result = openai_service.verify_question_quality(
                    question_data=question_data,
                    choices_data=choices_data
                )
                
                # 結果をセッション状態に保存
                verification_key = f"verification_result_{question['id']}"
                st.session_state[verification_key] = verification_result
                
                # 処理完了フラグをクリア
                st.session_state[verification_in_progress_key] = False
                st.rerun()
                
            except Exception as e:
                st.error(f"検証中にエラーが発生しました: {e}")
                print(f"検証エラー: {e}")
                st.session_state[verification_in_progress_key] = False
                st.rerun()

def render_verification_result(verification_result):
    """検証結果の表示"""
    if not verification_result:
        return
    
    # 結果に応じたスタイル設定
    is_valid = verification_result.get('is_valid', None)
    score = verification_result.get('score', 0)
    issues = verification_result.get('issues', [])
    recommendation = verification_result.get('recommendation', '不明')
    details = verification_result.get('details', '')
      # スコアとis_validに応じた表示
    if is_valid is None:
        st.error("🚨 **検証結果: エラー**")
    elif score is None:
        st.warning("⚠️ **検証結果: 判定不可**")
    elif score >= 8:
        st.success(f"✅ **検証結果: 優秀** (スコア: {score}/10)")
    elif score >= 6:
        st.info(f"👍 **検証結果: 良好** (スコア: {score}/10)")
    elif score >= 4:
        st.warning(f"⚠️ **検証結果: 要改善** (スコア: {score}/10)")
    else:
        st.error(f"❌ **検証結果: 不良** (スコア: {score}/10)")
    
    # 推奨アクション
    if recommendation:
        if recommendation == "削除推奨":
            st.error(f"🗑️ **推奨アクション:** {recommendation}")
        elif recommendation == "修正推奨":
            st.warning(f"✏️ **推奨アクション:** {recommendation}")
        elif recommendation == "問題なし":
            st.success(f"✅ **推奨アクション:** {recommendation}")
        else:
            st.info(f"📋 **推奨アクション:** {recommendation}")
    
    # 問題点があれば表示
    if issues:
        with st.expander("⚠️ 検出された問題点", expanded=score < 6):
            for issue in issues:
                st.markdown(f"• {issue}")
    
    # 詳細説明があれば表示
    if details and details != '詳細な評価結果が取得できませんでした':
        with st.expander("📋 詳細分析", expanded=False):
            st.markdown(details)
    
    # 結果をクリアするボタン
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        # 問題IDを取得（セッション状態のキーから）
        question_id = None
        for key in st.session_state.keys():
            if key.startswith("verification_result_") and st.session_state[key] == verification_result:
                question_id = key.replace("verification_result_", "")
                break
        
        if question_id and st.button("✖️ 結果を閉じる", key=f"close_verification_{question_id}"):
            # セッション状態から削除
            verification_key = f"verification_result_{question_id}"
            if verification_key in st.session_state:
                del st.session_state[verification_key]
            st.rerun()
            if verification_key in st.session_state:
                del st.session_state[verification_key]
            st.rerun()
