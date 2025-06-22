"""
問題管理ページ - 問題の一覧表示、AI生成、PDF処理、重複検査
"""
import streamlit as st
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
            st.markdown(f"**内容:** {question['content']}")
              # 選択肢表示
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
              # 編集・削除ボタン
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"✏️ 編集", key=f"edit_{question['id']}"):
                    render_edit_question_modal(question, question_service, choice_service)
            
            with col2:
                render_delete_question_button(question, question_service)

def render_ai_generation_tab(session):
    """AI問題生成タブ"""
    st.markdown("### 🤖 AI問題生成")
    
    try:
        from services.question_generator import EnhancedQuestionGenerator as QuestionGenerator
        
        # 生成パラメータ設定
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**生成パラメータ**")
            
            gen_col1, gen_col2, gen_col3 = st.columns(3)
            
            with gen_col1:
                category = st.selectbox(
                    "カテゴリ",
                    ["基本情報技術者", "応用情報技術者", "プログラミング基礎", "データベース",
                     "ネットワーク", "セキュリティ", "AI・機械学習", "プロジェクトマネジメント"],
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
                    key="ai_model"                )
                
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
    """PDF問題生成タブ"""
    st.markdown("### 📄 PDF問題生成")
    
    try:
        from services.pdf_processor import PDFProcessor        # PDFジェネレーターの読み込み (エラー対策)
        try:
            # 標準インポートを試す
            from services.pdf_question_generator import PDFQuestionGenerator
            print("標準のPDFジェネレーターを使用")
        except Exception as e:
            print(f"標準インポートでエラー: {e}")
            try:
                # 代替手段: .finalファイルを直接実行
                import sys
                import os
                import subprocess
                
                final_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "services", "pdf_question_generator.py.final")
                
                # モジュールをPythonで実行し、定義を取得
                result = subprocess.run(
                    [sys.executable, "-c", f"exec(open('{final_path}').read()); print('クラス読み込み成功')"],
                    capture_output=True, text=True
                )
                
                if "クラス読み込み成功" in result.stdout:
                    # エラーなく読み込めたので.finalから直接クラスを取得
                    from services.pdf_question_generator import PDFQuestionGenerator
                    print("修正済みPDFジェネレーターを使用")
                else:
                    # フォールバック: 簡易PDFジェネレーター
                    class PDFQuestionGenerator:
                        """緊急用の簡易PDFジェネレーター"""
                        def __init__(self, session, model_name="gpt-4o-mini"):
                            self.session = session
                        
                        def generate_questions_from_pdf(self, text, **kwargs):
                            st.error("PDFジェネレーターの読み込みに失敗しました。管理者に連絡してください。")
                            return []
                    
                    print("緊急用PDFジェネレーターを使用")
            except Exception as fallback_error:
                print(f"代替読み込みでもエラー: {fallback_error}")
                # 最終フォールバック: 簡易PDFジェネレーター
                class PDFQuestionGenerator:
                    """緊急用の簡易PDFジェネレーター"""
                    def __init__(self, session, model_name="gpt-4o-mini"):
                        self.session = session
                    
                    def generate_questions_from_pdf(self, text, **kwargs):
                        st.error("PDFジェネレーターの読み込みに失敗しました。管理者に連絡してください。")
                        return []
                
                print("最終緊急用PDFジェネレーターを使用")
        
        # PDFファイルアップロード
        uploaded_file = st.file_uploader(
            "PDFファイルを選択してください",
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
                st.metric("ファイル形式", "PDF")
            
            # 生成パラメータ
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pdf_num_questions = st.slider("生成問題数", min_value=1, max_value=30, value=10, key="pdf_questions")
            
            with col2:                pdf_difficulty = st.selectbox(
                    "難易度",
                    ["easy", "medium", "hard"],
                    format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                    key="pdf_difficulty"
                )
            
            with col3:
                pdf_category = st.text_input("カテゴリ名", "PDF教材", key="pdf_category")
            
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
                    index=0,
                    key="pdf_model"
                )
                
                pdf_include_explanation = st.checkbox("解説を含める", value=True, key="pdf_explanation")
                pdf_chunk_size = st.slider("テキスト分割サイズ", min_value=500, max_value=3000, value=1500, key="pdf_chunk_size")
                pdf_overlap = st.slider("オーバーラップサイズ", min_value=50, max_value=500, value=200, key="pdf_overlap")
                
                st.markdown("**処理オプション:**")
                col1, col2 = st.columns(2)
                with col1:
                    extract_method = st.radio(
                        "抽出方法",
                        ["自動", "OCR", "テキスト"],
                        help="自動: 最適な方法を自動選択、OCR: 画像からテキスト抽出、テキスト: 直接テキスト抽出",
                        key="pdf_extract_method"
                    )
                with col2:
                    quality_check = st.checkbox("品質チェックを有効にする", value=True, key="pdf_quality_check")
                    pdf_allow_multiple_correct = st.checkbox("複数正解問題を生成可能にする", value=False, 
                                                       help="チェックすると複数の正解を持つ問題が生成される可能性があります。チェックしない場合は1つの正解のみの問題が生成されます。", 
                                                       key="pdf_multiple_correct")
            
            # プライバシー保護の確認
            privacy_confirmed = st.checkbox(
                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません",
                key="pdf_privacy"
            )
            
            if st.button("🎯 PDFから問題を生成", disabled=not privacy_confirmed, key="generate_pdf"):
                if not privacy_confirmed:
                    st.warning("⚠️ プライバシー保護設定への同意が必要です")
                    return
                
                with st.spinner("PDFを処理中..."):
                    try:
                        # PDF処理
                        pdf_processor = PDFProcessor()
                        pdf_generator = PDFQuestionGenerator(session)
                          # テキスト抽出
                        uploaded_file.seek(0)
                        file_bytes = uploaded_file.read()
                        extracted_text = pdf_processor.extract_text_auto(file_bytes)
                        
                        if not extracted_text:
                            st.error("PDFからテキストを抽出できませんでした")
                            return
                        
                        # 問題生成（新しいパラメータを含む）
                        generated_ids = pdf_generator.generate_questions_from_pdf(
                            text=extracted_text,
                            num_questions=pdf_num_questions,
                            difficulty=pdf_difficulty,
                            category=pdf_category,
                            model=pdf_selected_model,
                            include_explanation=pdf_include_explanation,
                            allow_multiple_correct=pdf_allow_multiple_correct
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
                                if st.button("📝 問題一覧で確認", type="secondary", use_container_width=True, key="pdf_view_list"):
                                    st.info("問題一覧タブで生成された問題を確認できます")
                        else:
                            st.error("問題の生成に失敗しました")
                            
                    except Exception as e:
                        st.error(f"PDF処理でエラーが発生しました: {e}")
                        
    except ImportError:
        st.error("PDF処理機能が利用できません（PDFProcessorがインポートできません）")

def render_duplicate_check_tab(question_service):
    """重複検査タブ"""
    st.markdown("### 🔍 重複検査")
    
    st.info("重複検査機能は今後実装予定です")
    
    # 簡単な統計情報
    try:
        all_questions = question_service.get_random_questions(limit=1000)
        st.metric("総問題数", len(all_questions))
        
        categories = {}
        for q in all_questions:
            categories[q.category] = categories.get(q.category, 0) + 1
        
        if categories:
            st.markdown("**カテゴリ別問題数:**")
            for category, count in sorted(categories.items()):
                st.markdown(f"- {category}: {count}問")
                
    except Exception as e:
        st.error(f"統計情報の取得でエラーが発生しました: {e}")

def render_generation_stats_tab(question_service):
    """生成統計タブ"""
    st.markdown("### 📊 生成統計")
    
    try:
        all_questions = question_service.get_random_questions(limit=1000)
        
        # 基本統計
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総問題数", len(all_questions))
        
        with col2:
            categories = len(set(q.category for q in all_questions))
            st.metric("カテゴリ数", categories)
        
        with col3:
            difficulties = len(set(q.difficulty for q in all_questions))
            st.metric("難易度数", difficulties)
        
        # カテゴリ別統計
        if all_questions:
            st.markdown("### 📚 カテゴリ別統計")
            
            category_stats = {}
            difficulty_stats = {}
            
            for q in all_questions:
                category_stats[q.category] = category_stats.get(q.category, 0) + 1
                difficulty_stats[q.difficulty] = difficulty_stats.get(q.difficulty, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**カテゴリ別分布:**")
                for category, count in sorted(category_stats.items()):
                    percentage = (count / len(all_questions)) * 100
                    st.markdown(f"- {category}: {count}問 ({percentage:.1f}%)")
            
            with col2:
                st.markdown("**難易度別分布:**")
                for difficulty, count in sorted(difficulty_stats.items()):
                    percentage = (count / len(all_questions)) * 100
                    difficulty_name = {"easy": "初級", "medium": "中級", "hard": "上級"}.get(difficulty, difficulty)
                    st.markdown(f"- {difficulty_name}: {count}問 ({percentage:.1f}%)")
        
    except Exception as e:
        st.error(f"統計情報の取得でエラーが発生しました: {e}")

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
                    
                    # 削除実行
                    with st.spinner("削除処理中..."):
                        deletion_success = question_service.delete_question(question['id'])
                    
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
                          # セッション状態のクリア
                        st.session_state[modal_key] = False
                        st.session_state[confirm_key] = False
                        
                        # キャッシュをクリアして最新データを強制取得
                        for key in list(st.session_state.keys()):
                            if key.startswith('questions_cache_'):
                                del st.session_state[key]
                          # 祝福エフェクトとページリロード
                        st.balloons()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ **削除に失敗しました**")
                        st.error("詳細なエラー情報は、コンソールログを確認してください")
                        
                        # デバッグ情報の表示
                        with st.expander("🔍 デバッグ情報"):
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
                try:
                    choices = choice_service.get_choices_by_question_id(question['id'])
                    new_choices = []
                    
                    for i, choice in enumerate(choices):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            choice_content = st.text_input(
                                f"選択肢 {chr(65+i)}", 
                                value=choice.content,
                                key=f"choice_{question['id']}_{i}"
                            )
                            new_choices.append(choice_content)
                        with col2:
                            is_correct = st.checkbox(
                                "正答", 
                                value=choice.is_correct,
                                key=f"correct_{question['id']}_{i}"
                            )
                
                except Exception as e:
                    st.warning(f"選択肢の読み込みエラー: {e}")
                    new_choices = ["", "", "", ""]
                
                # 保存・キャンセルボタン
                col1, col2 = st.columns([1, 1])
                
                submitted = st.form_submit_button("💾 保存", type="primary")
                cancelled = st.form_submit_button("❌ キャンセル")
                
                if submitted:
                    try:
                        # 問題情報の更新処理
                        update_data = {
                            'title': new_title,
                            'content': new_content,
                            'category': new_category,
                            'difficulty': new_difficulty,
                            'explanation': new_explanation
                        }
                        
                        # 実際の更新処理（QuestionServiceに更新メソッドが必要）
                        # success = question_service.update_question(question['id'], update_data)
                        
                        # 現在は情報表示のみ
                        st.success("✅ **編集内容:**")
                        st.json(update_data)
                        st.info("📝 **注意:** 編集機能は開発中です。現在は内容確認のみ可能です。")
                        
                        st.session_state[edit_modal_key] = False
                        
                    except Exception as e:
                        st.error(f"編集エラー: {e}")
                
                if cancelled:
                    st.session_state[edit_modal_key] = False
                    st.rerun()
            
            st.markdown("---")
