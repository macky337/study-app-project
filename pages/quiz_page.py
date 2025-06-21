"""
クイズ機能のページ
"""
import streamlit as st
import time
from config.app_config import DATABASE_AVAILABLE
from components.question_components import render_question_choices, display_question_header, display_question_result

def quiz_page():
    """クイズページのメイン関数"""
    # リアルタイムでデータベース接続をチェック
    from config.app_config import check_database_connection
    db_available, db_error = check_database_connection()
    
    if not db_available:
        st.warning("⚠️ データベースに接続できません。デモモードでクイズを表示しています。")
        from components.question_components import display_demo_question
        display_demo_question()
        return
    
    # Database operations import
    from database.operations import QuestionService, ChoiceService, UserAnswerService
    from database.connection import get_session_context
    
    # セッション管理
    with get_session_context() as session:
        question_service = QuestionService(session)
        choice_service = ChoiceService(session)
        user_answer_service = UserAnswerService(session)
        
        # メインレイアウト
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_quiz_stats(question_service, user_answer_service)
        
        with col2:
            display_quiz_controls(question_service)
        
        # 問題表示
        if st.session_state.current_question is None:
            get_new_question(question_service)
        
        if st.session_state.current_question:
            display_current_question(question_service, choice_service, user_answer_service)

def display_quiz_stats(question_service, user_answer_service):
    """クイズ統計情報を表示"""
    st.subheader("📚 学習支援ツール")
    st.markdown("""
    このアプリは効率的な学習をサポートする機能を提供します：
    - 🎯 様々なカテゴリのクイズに挑戦
    - 📊 学習進捗の追跡
    - 📑 PDFからの問題自動生成
    - 🤖 AIによる問題自動生成
    """)
    
    try:
        # 問題数を取得
        total_questions = len(question_service.get_random_questions(limit=1000))
        
        # セッション統計を取得
        stats = user_answer_service.get_user_stats(st.session_state.session_id)
        
        st.markdown("### 📊 統計情報")
        col1_1, col1_2, col1_3 = st.columns(3)
        
        with col1_1:
            st.metric("総問題数", total_questions)
        with col1_2:
            st.metric("回答済み", stats['total'])
        with col1_3:
            st.metric("正答率", f"{stats['accuracy']}%")
    except Exception as e:
        print(f"エラー発生: {e}")
        st.error(f"データベース接続エラー: {e}")

def display_quiz_controls(question_service):
    """クイズコントロールを表示"""
    st.markdown("### 🚀 クイズを開始")
    st.markdown("カテゴリを選択して問題に挑戦！")
    
    # カテゴリ選択
    try:
        categories = question_service.get_all_categories()
        category_options = ["すべて"] + categories
    except Exception as category_error:
        st.error(f"❌ カテゴリ情報の取得に失敗しました: {category_error}")
        category_options = ["すべて"]
    
    selected_category = st.selectbox("カテゴリ", category_options)
    st.session_state.selected_category = selected_category
    
    if st.button("🎲 クイズモードへ", use_container_width=True):
        st.session_state.current_question = None
        st.session_state.show_result = False
        st.rerun()

def get_new_question(question_service):
    """新しい問題を取得"""
    # 既に回答した問題を除外して取得
    max_attempts = 10
    attempt = 0
    question = None
    
    while attempt < max_attempts:
        # 毎回attemptをインクリメントして無限ループを防止
        attempt += 1
        
        # カテゴリに応じて問題を取得
        if st.session_state.selected_category == "すべて":
            questions = question_service.get_random_questions(limit=5)
        else:
            questions = question_service.get_random_questions_by_category(
                st.session_state.selected_category, limit=5
            )
        
        if questions:
            # 未回答の問題を探す
            for q in questions:
                if q.id not in st.session_state.answered_questions:
                    question = q
                    break
            
            if question:
                break
            else:                # 全ての問題が回答済みの場合、リセット
                if len(st.session_state.answered_questions) > 0:
                    st.session_state.answered_questions.clear()
                    st.info("🔄 全ての問題を回答しました。問題をリセットします。")
                    question = questions[0]
                    break
    
    if question:
        # SQLModelオブジェクトを辞書に変換してセッションに格納
        from database.connection import model_to_dict
        st.session_state.current_question = model_to_dict(question)
        st.session_state.user_answer = None
        st.session_state.show_result = False
        st.session_state.start_time = time.time()
        st.session_state.quiz_choice_key += 1
    else:
        st.error("問題が見つかりません。")
        st.stop()

def display_current_question(question_service, choice_service, user_answer_service):
    """現在の問題を表示"""
    question = st.session_state.current_question
    
    # 進捗表示
    if len(st.session_state.answered_questions) > 0:
        st.info(f"📊 このセッションで回答済み: {len(st.session_state.answered_questions)}問")
    
    # 問題表示
    display_question_header(question)
    
    # 選択肢を取得（辞書形式のquestionから id を取得）
    question_id = question['id'] if isinstance(question, dict) else question.id
    choices = choice_service.get_choices_by_question(question_id)
    
    # 選択肢が存在しない場合のエラーハンドリング
    if not choices:
        st.error("❌ この問題の選択肢が見つかりません。")
        st.info("🔧 問題データに不具合があります。管理者にお知らせください。")
        question_title = question['title'] if isinstance(question, dict) else question.title
        st.code(f"問題ID: {question_id}, タイトル: {question_title}")
        
        if st.button("➡️ 次の問題へ", use_container_width=True):
            st.session_state.answered_questions.add(question_id)
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.session_state.quiz_choice_key += 1
            st.rerun()
        st.stop()
    
    if not st.session_state.show_result:
        # 回答フェーズ
        st.markdown("---")
        
        # 問題タイプに応じた選択肢コンポーネントの表示
        question_content = question['content'] if isinstance(question, dict) else question.content
        selected_indices, question_type = render_question_choices(
            question_content, choices, key_suffix=str(st.session_state.quiz_choice_key)
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔍 回答する", use_container_width=True):
                handle_answer_submission(selected_indices, question_type, choices, user_answer_service, question)
        
        with col2:
            if st.button("⏭️ スキップ", use_container_width=True):
                handle_skip_question(question)
    
    else:
        # 結果表示フェーズ
        st.markdown("---")
        user_answer = st.session_state.user_answer
        display_question_result(user_answer, question, choices)
        
        # 次の問題ボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➡️ 次の問題", use_container_width=True):
                st.session_state.current_question = None
                st.session_state.show_result = False
                st.rerun()
        
        with col2:
            if st.button("📊 統計を見る", use_container_width=True):
                st.session_state.current_question = None
                st.session_state.show_result = False
                st.rerun()

def handle_answer_submission(selected_indices, question_type, choices, user_answer_service, question):
    """回答提出を処理"""
    # 選択肢が選ばれているかチェック
    if not selected_indices:
        st.error("❌ 選択肢を選んでください。")
        st.stop()
    
    # 回答時間を計算
    answer_time = time.time() - st.session_state.start_time
    
    # 問題IDを取得（辞書形式対応）
    question_id = question['id'] if isinstance(question, dict) else question.id
    
    # 選択肢のIDと正答判定
    if question_type == 'multiple':
        selected_choice_ids = [choices[i].id for i in selected_indices]
        # 複数選択の正答判定
        selected_correct = all(choices[i].is_correct for i in selected_indices)
        all_correct_selected = all(i in selected_indices for i, choice in enumerate(choices) if choice.is_correct)
        is_correct = selected_correct and all_correct_selected and len(selected_indices) > 0
        record_choice_id = selected_choice_ids[0] if selected_choice_ids else None
    else:
        # 単一選択の場合は、選択された選択肢が正解かどうかを直接チェック
        selected_choice_id = choices[selected_indices[0]].id
        is_correct = choices[selected_indices[0]].is_correct
        record_choice_id = selected_choice_id
        
        # デバッグ情報
        print(f"選択された選択肢: {selected_indices[0]}, 内容: {choices[selected_indices[0]].content}")
        print(f"正解フラグ: {is_correct}, 選択肢ID: {selected_choice_id}")
      # 回答を記録
    user_answer_service.record_answer(
        question_id=question_id,
        selected_choice_id=record_choice_id,
        is_correct=is_correct,
        answer_time=answer_time,
        session_id=st.session_state.session_id
    )
    
    # 回答済み問題に追加
    st.session_state.answered_questions.add(question_id)
    
    # セッション状態に回答情報を保存
    if question_type == 'multiple':
        st.session_state.user_answer = {
            'selected_choice': selected_choice_ids,
            'is_correct': is_correct,
            'answer_time': answer_time,
            'question_type': 'multiple'
        }
    else:
        # デバッグ情報
        print(f"単一選択の回答を記録します: 選択肢ID={selected_choice_id}, 正解={is_correct}")
        st.session_state.user_answer = {
            'selected_choice': selected_choice_id,
            'is_correct': is_correct,
            'answer_time': answer_time,
            'question_type': 'single'
        }
    st.session_state.show_result = True
    st.rerun()

def handle_skip_question(question):
    """問題スキップを処理"""
    question_id = question['id'] if isinstance(question, dict) else question.id
    st.session_state.answered_questions.add(question_id)
    st.session_state.current_question = None
    st.session_state.show_result = False
    st.rerun()
