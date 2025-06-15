import streamlit as st
import time
from datetime import datetime

# Database connection with error handling
try:
    from sqlmodel import Session
    from database.connection import engine, DATABASE_URL
    from database.operations import QuestionService, ChoiceService, UserAnswerService
    from services.question_generator import QuestionGenerator
    from utils.helpers import generate_session_id, format_accuracy, get_difficulty_emoji
    DATABASE_AVAILABLE = engine is not None
except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    DATABASE_AVAILABLE = False
    # Create mock functions for demo
    def generate_session_id():
        return "demo_session"

# ページ設定
st.set_page_config(
    page_title="Study Quiz App",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'session_id' not in st.session_state:
    st.session_state.session_id = generate_session_id()
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []
if 'answered_questions' not in st.session_state:
    st.session_state.answered_questions = set()
if 'quiz_choice_key' not in st.session_state:
    st.session_state.quiz_choice_key = 1

st.title("🎯 Study Quiz App")
st.markdown("資格試験対策用のクイズ学習アプリ")

# サイドバーに基本的なナビゲーションを追加
with st.sidebar:
    st.header("📚 メニュー")
    page = st.selectbox(
        "ページを選択",
        ["🏠 ホーム", "🎲 クイズ", "📊 統計", "🔧 問題管理", "⚙️ 設定"]
    )
    
    st.markdown("---")
    st.markdown(f"**セッションID:** `{st.session_state.session_id[-8:]}`")

# データベースセッションを取得する関数
@st.cache_resource
def get_database_session():
    if DATABASE_AVAILABLE and engine:
        return Session(engine)
    else:
        return None

# Database connection status check
def check_database_status():
    if not DATABASE_AVAILABLE:
        st.error("🚨 **データベース接続エラー**")
        st.markdown("""
        **考えられる原因:**
        - Railway Variables で `DATABASE_URL` が設定されていない
        - PostgreSQL サービスが追加されていない
        - Variable Reference が正しく設定されていない
        
        **解決方法:**
        1. Railway ダッシュボードを開く
        2. Variables タブで `DATABASE_URL` を確認
        3. PostgreSQL サービスを追加（未追加の場合）
        4. Variable Reference として `${{Postgres.DATABASE_URL}}` を設定
        """)
        return False
    return True

# 選択されたページに応じた表示
if page == "🏠 ホーム":
    st.subheader("🎯 Study Quiz App へようこそ！")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📋 このアプリについて
        資格試験対策用の学習支援ツールです。
        
        **主な機能:**
        - 📝 資格試験問題のクイズ出題
        - 🎲 ランダムまたはカテゴリ別出題
        - ⏱️ 回答時間の測定
        - 📊 学習履歴と統計の管理
        - 🔄 間違えた問題の復習
        - 🤖 AI による問題自動生成
        """)
        
        # データベース統計を表示
        if DATABASE_AVAILABLE:
            try:
                with get_database_session() as session:
                    question_service = QuestionService(session)
                    user_answer_service = UserAnswerService(session)
                    
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
                st.error(f"データベース接続エラー: {e}")
        else:            st.warning("⚠️ データベースに接続できません")
    
    with col2:
        st.markdown("### 🚀 クイズを開始")
        if st.button("🎲 ランダムクイズ", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.session_state.user_answer = None
            # 回答済み問題リストをクリア（新しいクイズセッション開始）
            st.session_state.answered_questions.clear()
            st.success("サイドバーから「🎲 クイズ」を選択してください！")

elif page == "🎲 クイズ":
    st.subheader("🎲 クイズモード")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、クイズ機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            user_answer_service = UserAnswerService(session)
              # 新しい問題を取得
            if st.session_state.current_question is None:
                # 既に回答した問題を除外して取得
                max_attempts = 10
                attempt = 0
                question = None
                
                while attempt < max_attempts:
                    questions = question_service.get_random_questions(limit=5)  # 複数取得して選択
                    if questions:
                        # 未回答の問題を探す
                        for q in questions:
                            if q.id not in st.session_state.answered_questions:
                                question = q
                                break
                        
                        if question:
                            break
                        else:
                            # 全ての問題が回答済みの場合、リセット
                            if len(st.session_state.answered_questions) > 0:
                                st.session_state.answered_questions.clear()
                                st.info("🔄 全ての問題を回答しました。問題をリセットします。")
                                question = questions[0]  # 最初の問題を選択
                                break
                    attempt += 1
                
                if question:
                    st.session_state.current_question = question
                    st.session_state.user_answer = None
                    st.session_state.show_result = False
                    st.session_state.start_time = time.time()
                    st.session_state.quiz_choice_key += 1  # ラジオボタンのキーを更新                else:
                    st.error("問題が見つかりません。")
                    st.stop()
            
            question = st.session_state.current_question
            
            # 進捗表示
            if len(st.session_state.answered_questions) > 0:
                st.info(f"📊 このセッションで回答済み: {len(st.session_state.answered_questions)}問")
            
            # 問題表示
            st.markdown(f"### {get_difficulty_emoji(question.difficulty)} {question.title}")
            st.markdown(f"**カテゴリ:** {question.category}")
            st.markdown(f"**問題:** {question.content}")
            
            # 選択肢を取得
            choices = choice_service.get_choices_by_question(question.id)
            
            if not st.session_state.show_result:                # 回答フェーズ
                st.markdown("---")
                st.markdown("**選択肢を選んでください:**")
                
                choice_labels = [f"{chr(65+i)}. {choice.content}" for i, choice in enumerate(choices)]
                
                selected_idx = st.radio(
                    "回答を選択:",
                    range(len(choices)),
                    format_func=lambda x: choice_labels[x],
                    key=f"quiz_choice_{st.session_state.quiz_choice_key}"
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔍 回答する", use_container_width=True):
                        # 回答時間を計算
                        answer_time = time.time() - st.session_state.start_time
                        
                        selected_choice = choices[selected_idx]
                        is_correct = selected_choice.is_correct
                          # 回答を記録
                        user_answer_service.record_answer(
                            question_id=question.id,
                            selected_choice_id=selected_choice.id,
                            is_correct=is_correct,
                            answer_time=answer_time,
                            session_id=st.session_state.session_id
                        )
                          # 回答済み問題に追加
                        st.session_state.answered_questions.add(question.id)
                        
                        st.session_state.user_answer = {
                            'selected_choice': selected_choice,
                            'is_correct': is_correct,
                            'answer_time': answer_time
                        }
                        st.session_state.show_result = True
                        st.rerun()
                
                with col2:
                    if st.button("⏭️ スキップ", use_container_width=True):
                        # スキップした問題も回答済みとしてマーク（無限ループ防止）
                        st.session_state.answered_questions.add(question.id)
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.rerun()
            
            else:
                # 結果表示フェーズ
                st.markdown("---")
                user_answer = st.session_state.user_answer
                
                if user_answer['is_correct']:
                    st.success("🎉 正解です！")
                else:
                    st.error("❌ 不正解です")
                    # 正解を表示
                    correct_choice = next(c for c in choices if c.is_correct)
                    st.info(f"**正解:** {correct_choice.content}")
                
                # 解説表示
                if question.explanation:
                    st.markdown(f"**💡 解説:** {question.explanation}")
                
                # 回答時間表示
                st.markdown(f"**⏱️ 回答時間:** {user_answer['answer_time']:.1f}秒")
                  # 次の問題ボタン
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("➡️ 次の問題", use_container_width=True):
                        # 次の問題への移行
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.session_state.user_answer = None
                        st.rerun()
                
                with col2:
                    if st.button("🏠 ホームに戻る", use_container_width=True):
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.success("サイドバーから「🏠 ホーム」を選択してください！")
    
    except Exception as e:
        st.error(f"クイズ機能でエラーが発生しました: {e}")

elif page == "📊 統計":
    st.subheader("📊 学習統計")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、統計機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            user_answer_service = UserAnswerService(session)
            
            # 全体統計
            all_stats = user_answer_service.get_user_stats()
            session_stats = user_answer_service.get_user_stats(st.session_state.session_id)
            
            st.markdown("### 📈 統計サマリー")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🌍 全体統計")
                st.metric("総回答数", all_stats['total'])
                st.metric("正解数", all_stats['correct'])
                st.metric("正答率", f"{all_stats['accuracy']}%")
            
            with col2:
                st.markdown("#### 👤 セッション統計")
                st.metric("セッション回答数", session_stats['total'])
                st.metric("セッション正解数", session_stats['correct'])
                st.metric("セッション正答率", f"{session_stats['accuracy']}%")
            
            if session_stats['total'] > 0:
                st.markdown("### 🎯 進捗")
                progress = session_stats['accuracy'] / 100
                st.progress(progress)
                st.markdown(f"現在の正答率: **{session_stats['accuracy']}%**")
    
    except Exception as e:
        st.error(f"統計機能でエラーが発生しました: {e}")

elif page == "🔧 問題管理":
    st.subheader("🔧 問題管理")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、問題管理機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            
            # タブで機能を分割
            tab1, tab2, tab3 = st.tabs(["📝 問題一覧", "🤖 AI問題生成", "📊 生成統計"])
            
            with tab1:
                st.markdown("### 📝 問題一覧・管理")
                
                # フィルター
                col1, col2, col3 = st.columns(3)
                
                # 全問題を取得してカテゴリリストを作成
                all_questions = question_service.get_random_questions(limit=1000) 
                categories = sorted(list(set(q.category for q in all_questions)))
                difficulties = ["all", "easy", "medium", "hard"]
                
                with col1:
                    selected_category = st.selectbox(
                        "カテゴリでフィルター",
                        ["all"] + categories,
                        format_func=lambda x: "すべて" if x == "all" else x
                    )
                
                with col2:
                    selected_difficulty = st.selectbox(
                        "難易度でフィルター", 
                        difficulties,
                        format_func=lambda x: {
                            "all": "すべて",
                            "easy": "初級",
                            "medium": "中級", 
                            "hard": "上級"
                        }[x]
                    )
                
                with col3:
                    per_page = st.selectbox("表示件数", [10, 20, 50, 100], index=1)
                
                # フィルター適用
                filtered_questions = all_questions
                if selected_category != "all":
                    filtered_questions = [q for q in filtered_questions if q.category == selected_category]
                if selected_difficulty != "all":
                    filtered_questions = [q for q in filtered_questions if q.difficulty == selected_difficulty]
                
                st.markdown(f"**表示中: {len(filtered_questions)}問 / 全体: {len(all_questions)}問**")
                
                # ページネーション
                total_pages = (len(filtered_questions) + per_page - 1) // per_page
                if total_pages > 1:
                    page_num = st.number_input("ページ", min_value=1, max_value=total_pages, value=1) - 1
                else:
                    page_num = 0
                
                start_idx = page_num * per_page
                end_idx = min(start_idx + per_page, len(filtered_questions))
                current_questions = filtered_questions[start_idx:end_idx]
                
                # 問題表示
                for i, question in enumerate(current_questions):
                    with st.expander(f"**{question.title}** ({question.category} / {question.difficulty})"):
                        st.markdown(f"**問題ID:** {question.id}")
                        st.markdown(f"**内容:** {question.content}")
                        
                        # 選択肢表示
                        choices = choice_service.get_choices_by_question(question.id)
                        st.markdown("**選択肢:**")
                        for j, choice in enumerate(choices):
                            correct_mark = " ✅" if choice.is_correct else ""
                            st.markdown(f"{chr(65+j)}. {choice.content}{correct_mark}")
                        
                        if question.explanation:
                            st.markdown(f"**解説:** {question.explanation}")
                          # 編集・削除ボタン
                        col1, col2, col3 = st.columns([1, 1, 3])
                        with col1:
                            if st.button(f"✏️ 編集", key=f"edit_{question.id}"):
                                st.session_state.edit_question_id = question.id
                                st.info("編集機能は今後実装予定です")
                        
                        with col2:
                            if st.button(f"🗑️ 削除", key=f"delete_{question.id}"):
                                if st.session_state.get(f"confirm_delete_{question.id}", False):
                                    # 実際に削除
                                    if question_service.delete_question(question.id):
                                        st.success(f"問題 ID {question.id} を削除しました")
                                        st.session_state[f"confirm_delete_{question.id}"] = False
                                        st.rerun()
                                    else:
                                        st.error("削除に失敗しました")
                                else:
                                    st.session_state[f"confirm_delete_{question.id}"] = True
                                    st.warning("もう一度クリックして削除を確認してください")
            
            with tab2:
                st.markdown("### 🤖 AI問題生成")
                
                # 改良された生成UI
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**生成パラメータ**")
                    
                    # 生成パラメータ
                    gen_col1, gen_col2 = st.columns(2)
                    
                    with gen_col1:
                        category = st.selectbox(
                            "カテゴリ",
                            ["基本情報技術者", "応用情報技術者", "プログラミング基礎", "データベース", 
                             "ネットワーク", "セキュリティ", "AI・機械学習", "プロジェクトマネジメント"],
                            key="gen_category_tab"
                        )
                    
                    with gen_col2:
                        difficulty = st.selectbox(
                            "難易度",
                            ["easy", "medium", "hard"],
                            format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                            key="gen_difficulty_tab"
                        )
                    
                    count = st.slider("生成数", 1, 10, 1, key="gen_count_tab")
                    
                    topic = st.text_area(
                        "特定のトピック（任意）",
                        placeholder="例:\n• オブジェクト指向プログラミング\n• データベース正規化\n• ネットワークセキュリティ",
                        height=100,
                        key="gen_topic_tab"
                    )
                    
                    # 詳細オプション
                    with st.expander("🔧 詳細オプション"):
                        include_explanation = st.checkbox("解説を含める", value=True)
                        question_length = st.selectbox(
                            "問題文の長さ",
                            ["short", "medium", "long"],
                            format_func=lambda x: {"short": "短い", "medium": "標準", "long": "詳細"}[x]
                        )
                
                with col2:
                    st.markdown("**生成履歴**")
                    if st.session_state.generation_history:
                        for entry in st.session_state.generation_history[-5:]:  # 最新5件
                            st.text(f"{entry['time']}: {entry['count']}問生成")
                    else:
                        st.text("履歴なし")
                  # 生成実行
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("🎲 問題を生成", use_container_width=True, type="primary"):
                        # プログレス表示用のコンテナ
                        progress_container = st.empty()
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            generator = QuestionGenerator(session)
                            
                            # OpenAI接続確認
                            connection_status = generator.validate_openai_connection()
                            if not connection_status["connected"]:
                                st.error(f"❌ OpenAI接続エラー: {connection_status['message']}")
                                st.stop()
                            
                            generated_ids = []
                            
                            # プログレスコールバック関数
                            def update_progress(message, progress):
                                status_text.text(message)
                                progress_bar.progress(progress)
                            
                            if count == 1:
                                # 単一問題生成
                                question_id = generator.generate_and_save_question(
                                    category=category,
                                    difficulty=difficulty,
                                    topic=topic if topic else None,
                                    progress_callback=update_progress
                                )
                                
                                if question_id:
                                    generated_ids.append(question_id)
                            else:
                                # 複数問題生成
                                topics_list = [t.strip() for t in topic.split('\n') if t.strip()] if topic else None
                                
                                generated_ids = generator.generate_and_save_multiple_questions(
                                    category=category,
                                    difficulty=difficulty,
                                    count=count,
                                    topics=topics_list,
                                    progress_callback=update_progress,
                                    delay_between_requests=1.5  # Rate limiting
                                )
                            
                            # 結果表示
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            
                            if generated_ids:
                                st.success(f"✅ {len(generated_ids)}問の問題を生成しました！")
                                
                                # 生成履歴に追加
                                st.session_state.generation_history.append({
                                    'time': datetime.now().strftime('%H:%M'),
                                    'count': len(generated_ids),
                                    'category': category,
                                    'difficulty': difficulty
                                })
                                
                                # 生成された問題のIDを表示
                                with st.expander("📋 生成された問題の詳細"):
                                    for i, qid in enumerate(generated_ids):
                                        st.text(f"問題 {i+1}: ID {qid}")
                                        
                                        # 生成された問題の詳細を表示
                                        question = question_service.get_question_by_id(qid)
                                        if question:
                                            st.markdown(f"**タイトル:** {question.title}")
                                            st.markdown(f"**カテゴリ:** {question.category}")
                                            with st.expander(f"問題内容を表示 (ID: {qid})"):
                                                st.markdown(f"**問題:** {question.content}")
                                                if question.explanation:
                                                    st.markdown(f"**解説:** {question.explanation}")
                            else:
                                st.error("❌ 問題生成に失敗しました。OpenAI APIの制限またはネットワークエラーの可能性があります。")
                        
                        except Exception as e:
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            st.error(f"❌ エラーが発生しました: {e}")
                            st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか確認してください。")
                        
                with col2:
                    if st.button("🔄 フォームリセット"):
                        st.rerun()
            
            with tab3:
                st.markdown("### 📊 生成統計")
                
                try:
                    generator = QuestionGenerator(session)
                    stats = generator.get_generation_stats()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("総問題数", stats["total_questions"])
                        
                        st.markdown("**カテゴリ別問題数**")
                        if stats["categories"]:
                            for cat, count in sorted(stats["categories"].items()):
                                st.text(f"• {cat}: {count}問")
                    
                    with col2:
                        st.markdown("**難易度別問題数**")
                        if stats["difficulties"]:
                            difficulty_labels = {"easy": "初級", "medium": "中級", "hard": "上級"}
                            for diff, count in sorted(stats["difficulties"].items()):
                                label = difficulty_labels.get(diff, diff)
                                st.text(f"• {label}: {count}問")
                        
                        # 生成トレンド（セッション内）
                        if st.session_state.generation_history:
                            st.markdown("**本日の生成履歴**")
                            total_generated = sum(entry['count'] for entry in st.session_state.generation_history)
                            st.metric("本セッション生成数", total_generated)
                
                except Exception as e:
                    st.error(f"統計取得エラー: {e}")
    
    except Exception as e:
        st.error(f"問題管理機能でエラーが発生しました: {e}")

elif page == "⚙️ 設定":
    st.subheader("⚙️ 設定")
    
    st.markdown("### 🔧 アプリケーション設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**セッション管理**")
        st.text(f"現在のセッションID: {st.session_state.session_id}")
        
        if st.button("🔄 新しいセッション開始"):
            st.session_state.session_id = generate_session_id()
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.success("新しいセッションを開始しました！")
            st.rerun()
    
    with col2:
        st.markdown("**データベース情報**")
        if DATABASE_AVAILABLE:
            try:
                with get_database_session() as session:
                    question_service = QuestionService(session)
                    questions = question_service.get_random_questions(limit=1000)
                    st.text(f"総問題数: {len(questions)}")
                    
                    # カテゴリ別統計
                    categories = {}
                    for q in questions:
                        categories[q.category] = categories.get(q.category, 0) + 1
                    
                    st.markdown("**カテゴリ別問題数:**")
                    for category, count in categories.items():
                        st.text(f"• {category}: {count}問")
            
            except Exception as e:
                st.error(f"データベース情報の取得に失敗: {e}")
        else:
            st.error("データベースに接続できません")

# フッター
st.markdown("---")
st.markdown("**Study Quiz App** - powered by Streamlit & Railway 🚀")
