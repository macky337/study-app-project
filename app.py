import streamlit as st
import time
from datetime import datetime
import os

# ページ設定（最初に実行する必要がある）
st.set_page_config(
    page_title="Study Quiz App",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection with enhanced error handling
DATABASE_AVAILABLE = False
DATABASE_ERROR = None

# Mock functions for demo mode
def generate_session_id():
    return "demo_session"

def format_accuracy(correct, total):
    if total == 0:
        return "0%"
    return f"{(correct/total)*100:.1f}%"

def get_difficulty_emoji(difficulty):
    emoji_map = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
    return emoji_map.get(difficulty, "🟡")

try:
    print("🔍 Initializing database connection...")
    from sqlmodel import Session
    from database.connection import engine, DATABASE_URL
    
    if engine is not None:
        print("✅ Database engine created successfully")
        
        from database.operations import QuestionService, ChoiceService, UserAnswerService
        from services.question_generator import QuestionGenerator
        from services.pdf_processor import PDFProcessor
        from services.pdf_question_generator import PDFQuestionGenerator
        from services.past_question_extractor import PastQuestionExtractor
        from utils.helpers import generate_session_id as real_generate_session_id, format_accuracy as real_format_accuracy, get_difficulty_emoji as real_get_difficulty_emoji
        
        # Override with real functions
        generate_session_id = real_generate_session_id
        format_accuracy = real_format_accuracy
        get_difficulty_emoji = real_get_difficulty_emoji
        
        DATABASE_AVAILABLE = True
        print("✅ All modules imported successfully")
    else:
        print("⚠️ Database engine is None, running in demo mode")
        DATABASE_ERROR = "Database engine could not be created"
        
except ImportError as e:
    DATABASE_ERROR = f"Module import error: {str(e)}"
    DATABASE_AVAILABLE = False
    print(f"❌ Import error: {e}")
    print("Running in demo mode without database functionality")
        
except Exception as e:
    DATABASE_ERROR = f"Database connection error: {str(e)}"
    DATABASE_AVAILABLE = False
    print(f"❌ Database connection error: {e}")
    print("Running in demo mode without database functionality")

# OpenAI API key check
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OpenAI API key found: {openai_key[:10]}...{openai_key[-4:]}")
else:
    print("⚠️ OpenAI API key not found - AI features will be limited")

# データベースエラーがある場合は警告を表示
if DATABASE_ERROR:
    st.error(f"⚠️ Database connection failed: {DATABASE_ERROR}")

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
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "すべて"  # デフォルトは全カテゴリ

st.title("🎯 Study Quiz App")
st.markdown("資格試験対策用のクイズ学習アプリ")

# サイドバーに基本的なナビゲーションを追加
with st.sidebar:
    st.header("📚 メニュー")
    
    # ページ選択状態を管理
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 ホーム"
    
    page = st.selectbox(
        "ページを選択",
        ["🏠 ホーム", "🎲 クイズ", "📊 統計", "🔧 問題管理", "⚙️ 設定"],
        index=["🏠 ホーム", "🎲 クイズ", "📊 統計", "🔧 問題管理", "⚙️ 設定"].index(st.session_state.page),
        key="page_selector"
    )
      # ページが変更された場合、セッション状態を更新
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"**セッションID:** `{st.session_state.session_id[-8:]}`")

# 現在のページを取得
page = st.session_state.page

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
        else:
            st.warning("⚠️ データベースに接続できません")
    
    with col2:
        st.markdown("### 🚀 クイズを開始")
        st.markdown("カテゴリを選択して問題に挑戦！")
        
        if st.button("🎲 クイズモードへ", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.session_state.user_answer = None
            # 回答済み問題リストをクリア（新しいクイズセッション開始）
            st.session_state.answered_questions.clear()
            st.session_state.page = "🎲 クイズ"  # ページを直接切り替え
            st.rerun()
            
        st.info("💡 クイズモードでは、カテゴリを選択して問題を解くことができます")

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
            
            # カテゴリ選択UI
            st.markdown("### 🎯 カテゴリ選択")
            
            try:
                # 利用可能なカテゴリを取得
                categories = question_service.get_all_categories()
                category_stats = question_service.get_category_stats()
            except Exception as category_error:
                st.error(f"❌ カテゴリ情報の取得に失敗しました: {category_error}")
                st.info("💡 データベースに問題が登録されていない可能性があります。")
                st.stop()
            
            if not categories:
                st.warning("⚠️ 問題が登録されていません。")
                st.info("💡 問題管理ページで問題を追加してください。")
                st.stop()
                # カテゴリ選択ボックス
                category_options = ["すべて"] + categories
                category_display = {
                    "すべて": f"すべて ({sum(category_stats.values())}問)"
                }            
            # カテゴリ選択ボックス
            category_options = ["すべて"] + categories
            category_display = {
                "すべて": f"すべて ({sum(category_stats.values())}問)"
            }
            
            # 各カテゴリの問題数を表示
            for cat in categories:
                count = category_stats.get(cat, 0)
                category_display[cat] = f"{cat} ({count}問)"
            
            selected_category = st.selectbox(
                "出題するカテゴリを選択してください",
                options=category_options,
                format_func=lambda x: category_display.get(x, x),
                index=category_options.index(st.session_state.selected_category) if st.session_state.selected_category in category_options else 0,
                key="category_selector"
            )
            
            # カテゴリが変更された場合の処理
            if selected_category != st.session_state.selected_category:
                st.session_state.selected_category = selected_category
                st.session_state.current_question = None  # 現在の問題をリセット
                st.session_state.show_result = False
                st.session_state.answered_questions.clear()  # 回答済み問題をリセット
                st.info(f"📚 カテゴリを「{category_display[selected_category]}」に変更しました")
                st.rerun()
            
            st.markdown("---")
            
            # 新しい問題を取得
            if st.session_state.current_question is None:
                # 既に回答した問題を除外して取得
                max_attempts = 10
                attempt = 0
                question = None
                
                while attempt < max_attempts:
                    # カテゴリに応じて問題を取得
                    if st.session_state.selected_category == "すべて":
                        questions = question_service.get_random_questions(limit=5)  # 複数取得して選択
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
                    st.session_state.quiz_choice_key += 1  # ラジオボタンのキーを更新
                else:
                    st.error("問題が見つかりません。")
                    st.stop()
            
            question = st.session_state.current_question
            
            # 進捗表示
            if len(st.session_state.answered_questions) > 0:
                st.info(f"📊 このセッションで回答済み: {len(st.session_state.answered_questions)}問")
            
            # 問題表示
            st.markdown(f"### {get_difficulty_emoji(question.difficulty)} {question.title}")
            st.markdown(f"**カテゴリ:** {question.category}")
            st.markdown(f"**問題:** {question.content}")            # 選択肢を取得
            choices = choice_service.get_choices_by_question(question.id)
              # 選択肢が存在しない場合のエラーハンドリング
            if not choices:
                st.error("❌ この問題の選択肢が見つかりません。")
                st.info("🔧 問題データに不具合があります。管理者にお知らせください。")
                st.code(f"問題ID: {question.id}, タイトル: {question.title}")
                
                # 次の問題を表示するボタン
                if st.button("➡️ 次の問題へ", use_container_width=True):
                    st.session_state.answered_questions.add(question.id)
                    st.session_state.current_question = None
                    st.session_state.show_result = False
                    st.session_state.quiz_choice_key += 1
                    st.rerun()
                st.stop()  # return の代わりに st.stop() を使用
            
            print(f"INFO: 問題ID {question.id} の選択肢数: {len(choices)}")  # デバッグログ
            
            if not st.session_state.show_result:
                # 回答フェーズ
                st.markdown("---")
                st.markdown("**選択肢を選んでください:**")
                
                # デバッグ情報表示（開発時のみ）
                if len(choices) == 0:
                    st.error("選択肢データが取得できません")
                    st.stop()
                
                choice_labels = [f"{chr(65+i)}. {choice.content}" for i, choice in enumerate(choices)]
                print(f"DEBUG: 選択肢ラベル: {choice_labels}")  # デバッグログ
                
                # 選択肢が空でないことを確認
                if not choice_labels:
                    st.error("選択肢の生成に失敗しました")
                    st.stop()
                
                selected_idx = st.radio(
                    "回答を選択:",
                    range(len(choices)),
                    format_func=lambda x: choice_labels[x] if x < len(choice_labels) else "エラー",
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
                
                # 回答時間表示                st.markdown(f"**⏱️ 回答時間:** {user_answer['answer_time']:.1f}秒")
                
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
                        st.session_state.page = "🏠 ホーム"  # ページを直接切り替え
                        st.rerun()
    
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
            choice_service = ChoiceService(session)            # タブで機能を分割
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 問題一覧", "🤖 AI問題生成", "📄 PDF問題生成", "🔍 重複検査", "📊 生成統計"])
            
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
                    gen_col1, gen_col2, gen_col3 = st.columns(3)
                    
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
                    
                    with gen_col3:
                        count = st.slider(
                            "🔢 生成問題数", 
                            min_value=1, 
                            max_value=10, 
                            value=1, 
                            key="gen_count_tab",
                            help="一度に生成する問題の数を指定してください（1-10問）"
                        )
                    
                    topic = st.text_area(
                        "特定のトピック（任意）",
                        placeholder="例:\n• オブジェクト指向プログラミング\n• データベース正規化\n• ネットワークセキュリティ",
                        height=100,
                        key="gen_topic_tab"
                    )
                    
                    # 詳細オプション
                    with st.expander("🔧 詳細オプション"):
                        # AIモデル選択
                        st.markdown("**🤖 AIモデル選択**")
                        
                        # モデル情報を定義
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
                            index=0,  # デフォルトはgpt-3.5-turbo
                            help="高品質なモデルほど高コストですが、より詳細で正確な問題を生成します"
                        )
                        
                        # モデル詳細情報
                        model_info = {
                            "gpt-3.5-turbo": {"cost": "💰 低", "quality": "⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o-mini": {"cost": "💰💰 中", "quality": "⭐⭐⭐⭐", "speed": "🚀 高速"},
                            "gpt-4o": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 標準"},
                            "gpt-4": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 低速"}
                        }
                        
                        info = model_info[selected_model]
                        st.info(f"**{model_options[selected_model]}**\n\n"
                               f"コスト: {info['cost']} | 品質: {info['quality']} | 速度: {info['speed']}")
                        
                        # 他のオプション
                        include_explanation = st.checkbox("解説を含める", value=True)
                        question_length = st.selectbox(
                            "問題文の長さ",
                            ["short", "medium", "long"],
                            format_func=lambda x: {"short": "短い", "medium": "標準", "long": "詳細"}[x]                        )
                        
                        st.markdown("---")
                        st.markdown("**🔍 重複チェック設定**")
                        
                        enable_duplicate_check = st.checkbox(
                            "重複問題チェックを有効にする",
                            value=True,
                            help="既存の問題と類似する問題の生成を防ぎます"
                        )
                        
                        if enable_duplicate_check:
                            similarity_threshold = st.slider(
                                "類似度閾値",
                                min_value=0.5,
                                max_value=1.0,
                                value=0.8,
                                step=0.05,
                                help="この値以上の類似度を持つ問題は重複として判定されます"
                            )
                            
                            max_retry_attempts = st.slider(
                                "重複時の最大再試行回数",
                                min_value=1,
                                max_value=5,
                                value=3,
                                help="重複が検出された場合の最大再生成回数"
                            )
                        else:
                            similarity_threshold = 0.8
                            max_retry_attempts = 0
                        
                        st.markdown("---")
                        st.markdown("**✅ 内容検証機能**")
                        st.info("""
                        **自動内容検証が有効です：**
                        - 📝 問題文と選択肢の関連性チェック
                        - 🔢 選択肢数の妥当性検証（2-6個推奨）
                        - ✔️ 正解設定の確認
                        - 🌍 日本語として自然かのチェック
                        - 🤖 AI による構造・内容の品質評価
                        
                        問題のある場合は自動的に再生成または警告を表示します。
                        """)
                
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
                        
                        # 選択されたモデルをログに出力
                        st.info(f"🤖 使用モデル: {selected_model} ({model_options[selected_model]})")
                        print(f"🎯 User selected model: {selected_model}")
                        
                        try:
                            generator = QuestionGenerator(session, model=selected_model)
                            
                            # OpenAI接続確認
                            st.info("🔍 OpenAI接続を確認中...")
                            connection_status = generator.validate_openai_connection()
                            
                            if not connection_status["connected"]:
                                error_message = connection_status.get('message', 'Unknown error')
                                error_type = connection_status.get('error_type', 'unknown')
                                model_name = connection_status.get('model', selected_model)
                                
                                st.error(f"❌ **OpenAI接続エラー**")
                                
                                # エラータイプ別の詳細情報
                                if error_type == "authentication":
                                    st.markdown("""
                                    🔑 **認証エラー**
                                    - APIキーが無効または期限切れです
                                    - [OpenAI Platform](https://platform.openai.com/api-keys)でAPIキーを確認してください
                                    """)
                                elif error_type == "rate_limit":
                                    st.markdown("""
                                    ⏳ **レート制限エラー**
                                    - API使用量が上限に達しています
                                    - 少し待ってから再試行するか、プランをアップグレードしてください
                                    """)
                                elif error_type == "connection":
                                    st.markdown("""
                                    🌐 **接続エラー**
                                    - インターネット接続を確認してください
                                    - ファイアウォールやプロキシの設定を確認してください
                                    """)
                                elif "quota" in error_message.lower() or "insufficient_quota" in error_message.lower():
                                    st.markdown("""
                                    💳 **クォータ超過エラー**
                                    - OpenAI APIのクレジット残高を確認してください
                                    - [OpenAI Platform](https://platform.openai.com/usage)で使用量を確認できます
                                    """)
                                else:
                                    st.markdown(f"""
                                    ⚠️ **一般エラー**
                                    - エラータイプ: `{error_type}`
                                    - 使用モデル: `{model_name}`
                                    """)
                                
                                # 詳細なエラーメッセージ
                                with st.expander("詳細なエラー情報"):
                                    st.code(error_message)
                                    st.json(connection_status)
                                
                                st.info("💡 **代替案:** 手動で問題を作成することも可能です（問題管理ページから）")
                                st.stop()
                            
                            generated_ids = []
                            # プログレスコールバック関数
                            def update_progress(message, progress):
                                status_text.text(message)
                                progress_bar.progress(progress)
                            
                            if count == 1:                                # 単一問題生成
                                question_id = generator.generate_and_save_question(
                                    category=category,
                                    difficulty=difficulty,
                                    topic=topic if topic else None,
                                    progress_callback=update_progress,
                                    enable_duplicate_check=enable_duplicate_check,
                                    enable_content_validation=True,  # 内容検証を有効化
                                    similarity_threshold=similarity_threshold,
                                    max_retry_attempts=max_retry_attempts                                )
                                
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
                                    delay_between_requests=1.5,  # Rate limiting
                                    enable_duplicate_check=enable_duplicate_check,
                                    enable_content_validation=True,  # 内容検証を有効化
                                    similarity_threshold=similarity_threshold,
                                    max_retry_attempts=max_retry_attempts
                                )
                            
                            # 結果表示
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            
                            # 共通の成功処理
                            if generated_ids:
                                progress_bar.progress(1.0)
                                status_text.text("PDF処理完了！")
                                
                                # プログレス表示を消去
                                progress_bar.empty()
                                status_text.empty()
                                
                                st.success(f"✅ {len(generated_ids)}問の問題を処理しました！")
                                
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
                                st.error(f"❌ PDF生成に失敗しました")
                        
                        except Exception as e:
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            st.error(f"❌ エラーが発生しました: {e}")
                            st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか、PDFが読み取り可能か確認してください。")                        
                with col2:
                    if st.button("🔄 フォームリセット"):
                        st.rerun()
            
            with tab3:
                st.markdown("### 📄 PDF問題生成")
                
                # PDFアップロードと問題生成
                try:
                    # PDF処理クラスの初期化
                    try:
                        pdf_processor = PDFProcessor()
                        st.success("✅ PDF処理エンジン初期化完了")
                    except Exception as processor_error:
                        st.error(f"❌ PDF処理エンジンの初期化に失敗しました: {processor_error}")
                        st.error("PDF処理に必要なライブラリ（PyPDF2, pdfplumber）が正しくインストールされていない可能性があります。")
                        st.code("pip install PyPDF2 pdfplumber", language="bash")
                        st.stop()
                    
                    # データベース接続確認
                    if DATABASE_AVAILABLE:
                        try:
                            pdf_generator = PDFQuestionGenerator(session, model_name="gpt-4o-mini")
                            past_extractor = PastQuestionExtractor(session)
                            st.success("✅ 問題生成エンジン初期化完了")
                        except Exception as gen_error:
                            st.error(f"❌ 問題生成エンジンの初期化に失敗しました: {gen_error}")
                            st.warning("⚠️ 問題生成機能が利用できません。テキスト抽出のみ実行可能です。")
                    else:
                        st.warning("⚠️ データベース接続エラーのため、問題の保存ができません。テキスト抽出のみ可能です。")
                    
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
                      # プライバシー保護についての詳細情報
                    with st.expander("🔒 プライバシー保護の詳細"):
                        st.markdown("""
                        **データ保護対策:**
                        
                        1. **学習データ除外**: 
                           - OpenAI APIに`X-OpenAI-Skip-Training: true`ヘッダーを送信
                           - アップロードされたPDFの内容が学習データとして使用されません
                           - OpenAI公式保証: ヘッダー設定時は学習に使用しない
                        
                        2. **一時的な処理**: 
                           - PDFの内容は問題生成/抽出のためのみに使用
                           - 処理完了後、メモリから自動的に削除
                           - データベースには生成された問題のみ保存
                        
                        3. **ローカル処理**: 
                           - PDFの読み込みと前処理はローカルで実行
                           - 必要最小限のテキストのみをAPIに送信
                           - 機密性の高い部分はクラウドに送信されません
                        
                        4. **技術的保証**: 
                           - 処理実行時に保護ヘッダー送信を確認表示
                           - ログで学習無効化の実行を記録
                           - 多重の保護機能で確実性を確保
                        
                        5. **法的保護**:
                           - OpenAIは契約上、ヘッダー設定時の学習使用を禁止
                           - GDPR、CCPA等の個人情報保護法に準拠
                           - エンタープライズ級のプライバシー保護
                        
                        **📊 データフロー:**
                        ```
                        PDF → ローカル抽出 → 最小限テキスト → API (学習無効) → 問題生成 → DB保存
                                                              ↓
                                                        30日後自動削除
                        ```
                        
                        ⚠️ **注意**: 著作権のあるPDFは個人学習目的でのみご利用ください。
                        
                        ✅ **結論**: PDFの内容がOpenAIの学習に使用されることはありません。
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
                        help="最大50MBまでのPDFファイルをアップロードできます（Railway Hobby Plan対応）",
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
                        
                        # 生成パラメータ
                        st.markdown("---")
                        
                        if processing_mode == "🤖 問題生成モード":
                            st.markdown("**🤖 問題生成設定**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                pdf_num_questions = st.slider(
                                    "🔢 生成問題数",
                                    min_value=1,
                                    max_value=30,
                                    value=10,
                                    key="pdf_num_questions",
                                    help="PDFから生成する問題の数を指定してください（1-30問）"
                                )
                            
                            with col2:
                                pdf_difficulty = st.selectbox(
                                    "難易度",
                                    ["easy", "medium", "hard"],
                                    format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                                    key="pdf_difficulty"
                                )
                            
                            with col3:
                                pdf_category = st.text_input("カテゴリ名", "PDF教材", key="pdf_category")
                            

                            # テキスト抽出オプション
                            with st.expander("🔧 詳細設定"):
                                # AIモデル選択
                                st.markdown("**🤖 AIモデル選択**")
                                
                                # モデル情報を定義
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
                                    index=1,  # デフォルトはgpt-4o-mini（PDF処理により適している）
                                    help="PDF処理では高品質なモデルを推奨します。複雑な教材ほど高性能モデルが効果的です",
                                    key="pdf_model_select"
                                )
                                
                                # モデル詳細情報
                                pdf_model_info = {
                                    "gpt-3.5-turbo": {"cost": "💰 低", "quality": "⭐⭐⭐", "speed": "🚀 高速", "pdf_suitability": "📄 基本"},
                                    "gpt-4o-mini": {"cost": "💰💰 中", "quality": "⭐⭐⭐⭐", "speed": "🚀 高速", "pdf_suitability": "📄 推奨"},
                                    "gpt-4o": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 標準", "pdf_suitability": "📄 最適"},
                                    "gpt-4": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 低速", "pdf_suitability": "📄 最適"}
                                }
                                
                                pdf_info = pdf_model_info[pdf_selected_model]
                                st.info(f"**{pdf_model_options[pdf_selected_model]}**\n\n"
                                       f"コスト: {pdf_info['cost']} | 品質: {pdf_info['quality']} | 速度: {pdf_info['speed']} | PDF処理: {pdf_info['pdf_suitability']}")
                                
                                st.markdown("**⚙️ 抽出・生成オプション**")
                                
                                extraction_method = st.selectbox(
                                    "テキスト抽出方法",
                                    ["auto", "pypdf2", "pdfplumber"],
                                    format_func=lambda x: {
                                        "auto": "自動選択（推奨）",
                                        "pypdf2": "PyPDF2（高速）",
                                        "pdfplumber": "PDFplumber（高精度）"
                                    }[x],
                                    help="自動選択では両方の方法を試して最適な結果を選択します"                                )
                                
                                include_explanation = st.checkbox("解説を含める", value=True, key="pdf_explanation")
                                
                                preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=False)
                                
                                # 重複チェック設定
                                st.markdown("**🔍 重複チェック設定**")
                                pdf_enable_duplicate_check = st.checkbox(
                                    "重複チェックを有効にする",
                                    value=True,
                                    help="既存の問題と重複する場合は再生成を試みます",
                                    key="pdf_enable_duplicate_check"
                                )
                                
                                if pdf_enable_duplicate_check:
                                    pdf_similarity_threshold = st.slider(
                                        "類似度閾値",
                                        min_value=0.3,
                                        max_value=0.9,
                                        value=0.7,
                                        step=0.05,
                                        help="この値より高い類似度の問題は重複とみなされます",
                                        key="pdf_similarity_threshold"
                                    )
                                    
                                    pdf_max_retry_attempts = st.slider(
                                        "最大再試行回数",
                                        min_value=1,
                                        max_value=5,
                                        value=3,
                                        help="重複が検出された場合の再生成試行回数",
                                        key="pdf_max_retry_attempts"
                                    )
                                # 問題生成実行
                            st.markdown("---")
                            button_label = "🎯 PDFから問題を生成"
                              # プライバシー保護の確認（問題生成モード）
                            privacy_confirmed_gen = st.checkbox(
                                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                                help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません。処理完了後、内容はメモリから削除されます。",
                                key="privacy_confirmation_gen"
                            )
                        
                        else:  # 過去問抽出モード
                            st.markdown("**📝 過去問抽出設定**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                pdf_category = st.text_input("カテゴリ名", "過去問", key="past_category")
                            
                            with col2:
                                # 過去問抽出でも問題数制限を追加
                                max_extract_questions = st.slider(
                                    "🔢 抽出問題数上限",
                                    min_value=1,
                                    max_value=50,
                                    value=20,
                                    key="max_extract_questions",
                                    help="PDFから抽出する問題数の上限を指定してください（1-50問）"
                                )
                            
                            with col3:
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
                            
                            with st.expander("🔧 過去問抽出の詳細設定"):
                                # AIモデル選択
                                st.markdown("**🤖 AIモデル選択**")
                                
                                # 過去問抽出用モデル選択
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
                                    help="過去問抽出では高精度モデルを推奨します。元の問題を正確に抽出するため",
                                    key="past_model_select"
                                )
                                
                                # モデル詳細情報
                                past_model_info = {
                                    "gpt-3.5-turbo": {"cost": "💰 低", "quality": "⭐⭐⭐", "speed": "🚀 高速", "extraction": "📝 基本"},
                                    "gpt-4o-mini": {"cost": "💰💰 中", "quality": "⭐⭐⭐⭐", "speed": "🚀 高速", "extraction": "📝 推奨"},
                                    "gpt-4o": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 標準", "extraction": "📝 最適"},
                                    "gpt-4": {"cost": "💰💰💰 高", "quality": "⭐⭐⭐⭐⭐", "speed": "🐢 低速", "extraction": "📝 最適"}
                                }
                                
                                past_info = past_model_info[past_selected_model]
                                st.info(f"**{past_model_options[past_selected_model]}**\n\n"
                                       f"コスト: {past_info['cost']} | 品質: {past_info['quality']} | 速度: {past_info['speed']} | 抽出精度: {past_info['extraction']}")
                                
                                st.markdown("**📋 過去問抽出について:**")
                                st.markdown("""
                                - 問題文、選択肢、正解、解説をそのまま抽出
                                - 元の内容を一切改変しません
                                - 問題番号で自動分割を試行                                - 抽出精度を向上させるため低温度設定を使用
                                """)
                                preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=True, key="past_preview")
                                
                                strict_extraction = st.checkbox(
                                    "厳密抽出モード", 
                                    value=True, 
                                    help="より正確な抽出のため、温度設定を最低にします"
                                )
                                
                                # 重複チェック設定
                                st.markdown("**🔍 重複チェック設定**")
                                past_enable_duplicate_check = st.checkbox(
                                    "重複チェックを有効にする",
                                    value=True,
                                    help="既存の問題と重複する場合はスキップまたは重複警告を表示します",
                                    key="past_enable_duplicate_check"
                                )
                                
                                if past_enable_duplicate_check:
                                    past_similarity_threshold = st.slider(
                                        "類似度閾値",
                                        min_value=0.3,
                                        max_value=0.9,
                                        value=0.7,
                                        step=0.05,
                                        help="この値より高い類似度の問題は重複とみなされます",
                                        key="past_similarity_threshold"
                                    )
                                    
                                    past_duplicate_action = st.radio(
                                        "重複時の動作",
                                        ["skip", "save_with_warning"],
                                        format_func=lambda x: {"skip": "スキップ", "save_with_warning": "警告付きで保存"}[x],
                                        help="重複問題が検出された時の処理方法",
                                        key="past_duplicate_action"
                                    )
                            
                            # 過去問抽出実行
                            st.markdown("---")
                            button_label = "📝 PDFから過去問を抽出"
                            
                            # プライバシー保護の確認（過去問抽出モード）
                            privacy_confirmed = st.checkbox(
                                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                                help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません。処理完了後、内容はメモリから削除されます。",
                                key="privacy_confirmation"
                            )                        # プライバシー保護確認の統一処理
                        if processing_mode == "🤖 問題生成モード":
                            privacy_check = st.session_state.get("privacy_confirmation_gen", False)
                        else:
                            privacy_check = st.session_state.get("privacy_confirmation", False)
                          
                        if st.button(button_label, type="primary", use_container_width=True, disabled=not privacy_check):
                            
                            if not privacy_check:
                                st.warning("⚠️ プライバシー保護設定への同意が必要です。")
                                st.stop()
                            
                            # プログレス表示
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            try:
                                # プライバシー保護の確認表示
                                st.info("PRIVACY: OpenAI学習無効化ヘッダーを設定して処理を開始します")
                                  # PDFテキスト抽出
                                status_text.text("PDFからテキストを抽出中...")
                                progress_bar.progress(0.1)
                                
                                try:
                                    # ファイルポインタを先頭に戻す
                                    uploaded_file.seek(0)
                                    file_bytes = uploaded_file.read()
                                    
                                    if not file_bytes:
                                        st.error("❌ PDFファイルの読み込みに失敗しました（空のファイル）")
                                        st.stop()
                                    
                                    # PDFファイルの基本検証
                                    if not file_bytes.startswith(b'%PDF-'):
                                        st.error("❌ 有効なPDFファイルではありません（PDFヘッダーが見つかりません）")
                                        st.stop()
                                    
                                    # ファイルサイズの確認
                                    if len(file_bytes) != uploaded_file.size:
                                        st.warning(f"⚠️ ファイルサイズが一致しません（期待: {uploaded_file.size}, 実際: {len(file_bytes)}）")
                                        
                                    st.success(f"✅ PDFファイル読み込み成功: {len(file_bytes):,} bytes")
                                    
                                except Exception as read_error:
                                    st.error(f"❌ ファイル読み込みエラー: {read_error}")
                                    st.error("ファイルが破損している可能性があります。別のPDFファイルを試してください。")
                                    st.stop()
                                
                                # テキスト抽出の実行
                                status_text.text("テキストを抽出中...")
                                progress_bar.progress(0.2)
                                
                                try:
                                    if extraction_method == "auto":
                                        extracted_text = pdf_processor.extract_text_auto(file_bytes)
                                    elif extraction_method == "pypdf2":
                                        extracted_text = pdf_processor.extract_text_pypdf2(file_bytes)
                                    else:
                                        extracted_text = pdf_processor.extract_text_pdfplumber(file_bytes)
                                    
                                    # 抽出結果の検証
                                    if not extracted_text:
                                        st.error("❌ テキスト抽出結果が空です")
                                        st.error("このPDFは画像ベースである可能性があります。OCR機能は現在サポートしていません。")
                                        st.stop()
                                    
                                    if len(extracted_text.strip()) < 50:
                                        st.error("❌ 抽出されたテキストが短すぎます")
                                        st.error("このPDFから十分なテキストを抽出できませんでした。")
                                        st.stop()
                                        
                                    st.success(f"✅ テキスト抽出成功: {len(extracted_text):,} 文字")
                                    
                                except Exception as extract_error:
                                    st.error(f"❌ テキスト抽出エラー: {extract_error}")
                                    st.error("PDFの形式が対応していない可能性があります。")
                                    
                                    # 詳細なエラー情報
                                    with st.expander("🔍 詳細なエラー情報"):
                                        st.code(f"エラータイプ: {type(extract_error).__name__}")
                                        st.code(f"エラーメッセージ: {str(extract_error)}")
                                        st.markdown("""
                                        **対処方法:**
                                        1. 別のPDFファイルを試してください
                                        2. PDFが暗号化されていないか確認してください
                                        3. PDFが画像ベースでないか確認してください
                                        4. ファイルサイズが大きすぎないか確認してください（50MB以下）
                                        """)
                                    st.stop()
                                
                                # テキストプレビュー
                                if preview_text:
                                    st.markdown("### 📖 抽出テキストプレビュー")
                                    with st.expander("抽出されたテキスト（最初の1000文字）"):
                                        st.text(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
                                
                                # テキスト統計
                                word_count = len(extracted_text.split())
                                char_count = len(extracted_text)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("抽出文字数", f"{char_count:,}")
                                with col2:
                                    st.metric("推定単語数", f"{word_count:,}")                                # プログレスコールバック関数
                                def pdf_progress_callback(message, progress):
                                    status_text.text(message)
                                    progress_bar.progress(min(progress, 0.95))
                                
                                if processing_mode == "🤖 問題生成モード":
                                    # 問題生成モード
                                    status_text.text("問題を生成中...")
                                    progress_bar.progress(0.3)
                                      # 選択されたモデルでPDFジェネレーターを再初期化
                                    pdf_generator = PDFQuestionGenerator(session, model_name=pdf_selected_model)
                                    
                                    try:
                                        st.info(f"🤖 {pdf_selected_model} を使用して問題生成を開始します...")
                                        generated_ids = pdf_generator.generate_questions_from_pdf(
                                            text=extracted_text,
                                            num_questions=pdf_num_questions,
                                            difficulty=pdf_difficulty,
                                            category=pdf_category,
                                            progress_callback=pdf_progress_callback,
                                            enable_duplicate_check=pdf_enable_duplicate_check,
                                            similarity_threshold=pdf_similarity_threshold if pdf_enable_duplicate_check else 0.7,
                                            max_retry_attempts=pdf_max_retry_attempts if pdf_enable_duplicate_check else 3
                                        )
                                        mode_text = "生成"
                                        st.success(f"✅ 問題生成完了: {len(generated_ids) if generated_ids else 0}問")
                                        
                                    except Exception as gen_error:
                                        progress_bar.empty()
                                        status_text.empty()
                                        st.error(f"❌ 問題生成エラーが発生しました")
                                        
                                        # 詳細なエラー情報
                                        with st.expander("🔍 問題生成エラーの詳細"):
                                            st.code(f"エラータイプ: {type(gen_error).__name__}")
                                            st.code(f"エラーメッセージ: {str(gen_error)}")
                                            
                                            # エラーの分類と対処法
                                            error_str = str(gen_error).lower()
                                            if 'api' in error_str or 'openai' in error_str:
                                                st.error("🔑 OpenAI APIエラーと思われます")
                                                st.markdown("""
                                                **対処方法:**
                                                - APIキーが正しく設定されているか確認
                                                - API利用制限に達していないか確認
                                                - インターネット接続を確認
                                                - しばらく時間をおいて再試行
                                                """)
                                            elif 'database' in error_str or 'sql' in error_str:
                                                st.error("💾 データベースエラーと思われます")
                                                st.markdown("""
                                                **対処方法:**
                                                - データベース接続を確認
                                                - ディスク容量を確認
                                                - アプリケーションを再起動
                                                """)
                                            elif 'memory' in error_str or 'size' in error_str:
                                                st.error("💾 メモリ不足エラーと思われます")
                                                st.markdown("""
                                                **対処方法:**
                                                - より小さなPDFファイルを使用
                                                - 生成問題数を減らす
                                                - 他のアプリケーションを終了
                                                """)
                                            else:
                                                st.error("❓ 不明なエラー")
                                                st.markdown("""
                                                **対処方法:**
                                                - アプリケーションを再起動
                                                - 別のPDFファイルで試行
                                                - システム管理者に連絡
                                                """)
                                        
                                        st.stop()
                                    
                                else:  # 過去問抽出モード
                                    # 過去問抽出モード
                                    status_text.text("過去問を抽出中...")
                                    progress_bar.progress(0.3)
                                      # 選択されたモデルで過去問抽出器を再初期化
                                    past_extractor = PastQuestionExtractor(session, model_name=past_selected_model)
                                    
                                    try:
                                        st.info(f"📝 {past_selected_model} を使用して過去問抽出を開始します...")
                                        generated_ids = past_extractor.extract_past_questions_from_pdf(
                                            text=extracted_text,
                                            category=pdf_category,
                                            max_questions=max_extract_questions,
                                            progress_callback=pdf_progress_callback,
                                            enable_duplicate_check=past_enable_duplicate_check,
                                            similarity_threshold=past_similarity_threshold if past_enable_duplicate_check else 0.7,
                                            duplicate_action=past_duplicate_action if past_enable_duplicate_check else "skip"
                                        )
                                        mode_text = "抽出"
                                        st.success(f"✅ 過去問抽出完了: {len(generated_ids) if generated_ids else 0}問")
                                        
                                    except Exception as extract_error:
                                        progress_bar.empty()
                                        status_text.empty()
                                        st.error(f"❌ 過去問抽出エラーが発生しました")
                                        
                                        # 詳細なエラー情報
                                        with st.expander("🔍 過去問抽出エラーの詳細"):
                                            st.code(f"エラータイプ: {type(extract_error).__name__}")
                                            st.code(f"エラーメッセージ: {str(extract_error)}")
                                            
                                            # エラーの分類と対処法
                                            error_str = str(extract_error).lower()
                                            if 'api' in error_str or 'openai' in error_str:
                                                st.error("🔑 OpenAI APIエラーと思われます")
                                                st.markdown("""
                                                **対処方法:**
                                                - APIキーが正しく設定されているか確認
                                                - API利用制限に達していないか確認
                                                - より高精度なモデル（gpt-4o）を試す
                                                """)
                                            elif 'format' in error_str or 'parse' in error_str:
                                                st.error("📄 PDF形式エラーと思われます")
                                                st.markdown("""
                                                **対処方法:**
                                                - 過去問の形式が標準的でない可能性があります
                                                - より構造化されたPDFを使用
                                                - 問題生成モードを試す
                                                """)
                                            elif 'duplicate' in error_str:
                                                st.warning("🔍 重複検出による処理中断")
                                                st.markdown("""
                                                **情報:**
                                                - 重複チェックにより処理が中断されました
                                                - 重複チェックを無効にして再試行
                                                - 既存の問題を確認
                                                """)
                                            else:
                                                st.error("❓ 不明なエラー")
                                                st.markdown("""
                                                **対処方法:**
                                                - 問題生成モードを試す
                                                - 別のPDFファイルで試行
                                                - システム管理者に連絡
                                                """)
                                        st.stop()
                                    
                                # 共通の成功処理
                                if generated_ids and len(generated_ids) > 0:
                                    progress_bar.progress(1.0)
                                    status_text.text("PDF処理完了！")
                                    
                                    # プログレス表示を消去
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    # mode_text変数が定義されていることを確認
                                    if 'mode_text' not in locals():
                                        mode_text = "処理"
                                    
                                    st.success(f"✅ {len(generated_ids)}問の問題を{mode_text}しました！")
                                else:
                                    # 失敗時の処理
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.error("❌ PDF処理に失敗しました")
                                    st.warning("⚠️ 問題の生成または抽出ができませんでした")
                                    
                                    # 失敗の原因分析
                                    with st.expander("🔍 失敗の原因と対処法"):
                                        st.markdown("""
                                        **考えられる原因:**
                                        1. **テキスト内容不足**: 抽出されたテキストから問題を作成できない
                                        2. **API制限**: OpenAI APIの利用制限に達している
                                        3. **重複検出**: すべての生成問題が重複と判定された
                                        4. **形式エラー**: PDFの形式が対応していない
                                        
                                        **対処方法:**
                                        - より内容の充実したPDFファイルを使用
                                        - 重複チェックを無効にして再試行
                                        - 生成問題数を減らして再試行
                                        - 別のAIモデルを選択
                                        - しばらく時間をおいて再実行
                                        """)
                                    
                                    st.stop()
                                
                                # 生成された問題がある場合の詳細処理
                                if generated_ids and len(generated_ids) > 0:
                                    
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
                                                
                                                st.markdown("---")                                    # 問題一覧への移動ボタン
                                    if st.button("📝 問題一覧で確認", type="secondary", use_container_width=True):
                                        st.info("問題一覧タブで生成された問題を確認できます")
                                else:
                                    st.error("❌ PDF処理に失敗しました")
                                    
                            except Exception as processing_error:
                                progress_bar.empty()
                                status_text.empty()
                                st.error(f"❌ PDF処理中にエラーが発生しました")
                                
                                # 詳細なエラー情報
                                with st.expander("🔍 エラーの詳細情報"):
                                    st.code(f"エラータイプ: {type(processing_error).__name__}")
                                    st.code(f"エラーメッセージ: {str(processing_error)}")
                                    
                                    # 一般的な原因と対処法
                                    st.markdown("""
                                    **考えられる原因:**
                                    1. **OpenAI APIエラー**: APIキーが無効または利用制限に達している
                                    2. **PDF形式エラー**: サポートされていないPDF形式
                                    3. **メモリ不足**: PDFファイルが大きすぎる
                                    4. **ネットワークエラー**: インターネット接続の問題
                                    5. **データベースエラー**: 問題保存時のエラー
                                    
                                    **対処方法:**
                                    - OpenAI APIキーを確認してください
                                    - より小さなPDFファイルを試してください
                                    - インターネット接続を確認してください
                                    - しばらく時間をおいて再試行してください
                                    """)
                                
                                # 診断情報の表示
                                st.info("🔧 システム診断情報:")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("データベース", "✅ 接続済み" if DATABASE_AVAILABLE else "❌ 接続失敗")
                                with col2:
                                    openai_available = 'OPENAI_API_KEY' in os.environ and os.environ['OPENAI_API_KEY']
                                    st.metric("OpenAI API", "✅ 設定済み" if openai_available else "❌ 未設定")
                                with col3:
                                    st.metric("PDFファイル", f"{uploaded_file.size / 1024:.1f} KB" if uploaded_file else "❌ なし")
                
                except Exception as tab_error:
                    st.error(f"❌ PDF機能の初期化でエラーが発生しました: {tab_error}")
                    
                    # トラブルシューティング情報
                    with st.expander("🛠️ トラブルシューティング"):
                        st.markdown("""
                        **PDF機能を利用するために必要な環境:**
                        
                        1. **必要なライブラリ**:
                        ```bash
                        pip install PyPDF2 pdfplumber streamlit
                        ```
                        
                        2. **Python環境**: Python 3.8以上
                        
                        3. **メモリ**: 最低2GB以上の空きメモリ
                        
                        4. **権限**: 一時ファイル作成権限
                        
                        **よくある問題:**
                        - `ModuleNotFoundError`: ライブラリが未インストール
                        - `PermissionError`: ファイル書き込み権限がない
                        - `MemoryError`: 利用可能メモリが不足
                        
                        **対処方法:**
                        1. 必要なライブラリを再インストール
                        2. Pythonを管理者権限で実行
                        3. より小さなPDFファイルを使用
                        4. 他のアプリケーションを終了してメモリを確保
                        """)
                    
                    st.info("💡 問題が解決しない場合は、システム管理者にお問い合わせください。")
            
            with tab4:
                st.markdown("### 🔍 重複問題検査・削除")
                
                st.markdown("""
                このツールは、データベース内の重複する可能性のある問題を検出し、削除することができます。
                """)
                
                # 検査タイプの選択
                detection_type = st.radio(
                    "検査タイプを選択してください",
                    options=["exact", "similar"],
                    format_func=lambda x: {
                        "exact": "🎯 完全重複検査（タイトル・内容が完全一致）",
                        "similar": "🔍 類似問題検査（類似度ベース）"
                    }[x],
                    help="完全重複検査は確実な重複のみ、類似問題検査は類似度で判定します"
                )
                
                if detection_type == "similar":
                    similarity_threshold = st.slider(
                        "類似度閾値", 
                        min_value=0.5, 
                        max_value=1.0, 
                        value=0.8, 
                        step=0.05,
                        help="この値以上の類似度を持つ問題を重複として検出します"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔍 重複検査を実行", use_container_width=True):
                        with st.spinner("重複問題を検査中..."):
                            try:
                                if detection_type == "exact":
                                    duplicates = question_service.find_exact_duplicate_questions()
                                else:
                                    duplicates = question_service.find_duplicate_questions(similarity_threshold)
                                
                                if duplicates:
                                    st.session_state.duplicate_groups = duplicates
                                    st.success(f"✅ {len(duplicates)}組の重複グループを検出しました")
                                else:
                                    st.info("📋 重複する問題は見つかりませんでした")
                                    st.session_state.duplicate_groups = []
                            
                            except Exception as e:
                                st.error(f"❌ 検査エラー: {e}")
                
                with col2:
                    if 'duplicate_groups' in st.session_state and st.session_state.duplicate_groups:
                        total_duplicates = sum(len(group) for group in st.session_state.duplicate_groups)
                        st.metric("検出された重複問題数", f"{total_duplicates}問")
                        st.metric("重複グループ数", f"{len(st.session_state.duplicate_groups)}組")
                
                # 重複問題の表示と削除
                if 'duplicate_groups' in st.session_state and st.session_state.duplicate_groups:
                    st.markdown("---")
                    st.markdown("### 🗂️ 検出された重複問題")
                    
                    for group_idx, duplicate_group in enumerate(st.session_state.duplicate_groups):
                        with st.expander(f"重複グループ {group_idx + 1} ({len(duplicate_group)}問)", expanded=True):
                            
                            # グループ内の問題を表示
                            for idx, question in enumerate(duplicate_group):
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    st.markdown(f"**{idx + 1}. {question.title}** (ID: {question.id})")
                                    st.markdown(f"📁 カテゴリ: {question.category}")
                                    st.markdown(f"📝 内容: {question.content[:100]}...")
                                    
                                    # 選択肢も表示
                                    choices = choice_service.get_choices_by_question(question.id)
                                    if choices:
                                        choice_text = " / ".join([f"{chr(65+i)}:{c.content[:20]}..." for i, c in enumerate(choices[:2])])
                                        st.markdown(f"🔤 選択肢: {choice_text}")
                                
                                with col2:
                                    question_selected = st.checkbox(
                                        "削除対象",
                                        key=f"delete_question_{question.id}",
                                        help=f"問題ID {question.id}を削除対象に選択"
                                    )
                                
                                with col3:
                                    if st.button(f"👁️ 詳細", key=f"detail_{question.id}"):
                                        st.session_state[f"show_detail_{question.id}"] = not st.session_state.get(f"show_detail_{question.id}", False)
                                
                                # 詳細表示
                                if st.session_state.get(f"show_detail_{question.id}", False):
                                    with st.container():
                                        st.markdown("**📋 完全な問題内容:**")
                                        st.markdown(f"**タイトル:** {question.title}")
                                        st.markdown(f"**カテゴリ:** {question.category}")
                                        st.markdown(f"**難易度:** {question.difficulty}")
                                        st.markdown(f"**問題文:** {question.content}")
                                        
                                        if choices:
                                            st.markdown("**選択肢:**")
                                            for choice_idx, choice in enumerate(choices):
                                                correct_mark = " ✅" if choice.is_correct else ""
                                                st.markdown(f"{chr(65+choice_idx)}. {choice.content}{correct_mark}")
                                        
                                        if question.explanation:
                                            st.markdown(f"**解説:** {question.explanation}")
                                
                                st.markdown("---")
                    
                    # 一括削除ボタン
                    st.markdown("### 🗑️ 選択された問題の削除")
                    
                    # 削除対象の問題IDを収集
                    selected_question_ids = []
                    for group in st.session_state.duplicate_groups:
                        for question in group:
                            if st.session_state.get(f"delete_question_{question.id}", False):
                                selected_question_ids.append(question.id)
                    
                    if selected_question_ids:
                        st.warning(f"⚠️ {len(selected_question_ids)}問が削除対象として選択されています")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🗑️ 選択された問題を削除", type="primary", use_container_width=True):
                                with st.spinner("問題を削除中..."):
                                    result = question_service.delete_multiple_questions(selected_question_ids)
                                    
                                    if result["deleted_count"] > 0:
                                        st.success(f"✅ {result['deleted_count']}問を正常に削除しました")
                                    
                                    if result["failed_ids"]:
                                        st.error(f"❌ {len(result['failed_ids'])}問の削除に失敗しました: {result['failed_ids']}")
                                    
                                    # 削除後は検査結果をクリア
                                    st.session_state.duplicate_groups = []
                                    st.rerun()
                        
                        with col2:
                            if st.button("🔄 選択をクリア", use_container_width=True):
                                # すべての選択をクリア
                                for group in st.session_state.duplicate_groups:
                                    for question in group:
                                        if f"delete_question_{question.id}" in st.session_state:
                                            st.session_state[f"delete_question_{question.id}"] = False
                                st.rerun()
                    else:
                        st.info("💡 削除したい問題にチェックを入れてください")

            with tab5:
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

    # データベース初期化セクション
    st.markdown("---")
    st.markdown("### 🗄️ データベース管理")
    
    if DATABASE_AVAILABLE:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**データベース初期化**")
            if st.button("📝 サンプルデータ作成", help="データベースが空の場合にサンプル問題を作成します"):
                try:
                    with get_database_session() as session:
                        question_service = QuestionService(session)
                        choice_service = ChoiceService(session)
                        
                        # 既存の問題数をチェック
                        existing_questions = question_service.get_random_questions(limit=1000)
                        
                        if len(existing_questions) > 0:
                            st.warning(f"⚠️ 既に{len(existing_questions)}問の問題が存在します。")
                            if st.button("🔄 強制的にサンプルデータを追加"):
                                create_sample = True
                            else:
                                create_sample = False
                        else:
                            create_sample = True
                        
                        if create_sample:
                            with st.spinner("サンプルデータを作成中..."):
                                # サンプル問題1
                                q1 = question_service.create_question(
                                    title="プログラミング基礎 - 変数",
                                    content="Pythonで変数xに数値10を代入する正しい記述はどれですか？",
                                    category="プログラミング基礎",
                                    explanation="Pythonでは「変数名 = 値」の形式で代入を行います。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q1.id, "x = 10", True, 1)
                                choice_service.create_choice(q1.id, "x == 10", False, 2)
                                choice_service.create_choice(q1.id, "x := 10", False, 3)
                                choice_service.create_choice(q1.id, "10 = x", False, 4)
                                
                                # サンプル問題2
                                q2 = question_service.create_question(
                                    title="基本情報技術者 - データベース",
                                    content="関係データベースにおいて、テーブル間の関連を定義するために使用されるものはどれですか？",
                                    category="基本情報技術者",
                                    explanation="外部キーは、他のテーブルの主キーを参照して、テーブル間の関連を定義します。",
                                    difficulty="medium"
                                )
                                
                                choice_service.create_choice(q2.id, "主キー", False, 1)
                                choice_service.create_choice(q2.id, "外部キー", True, 2)
                                choice_service.create_choice(q2.id, "インデックス", False, 3)
                                choice_service.create_choice(q2.id, "ビュー", False, 4)
                                
                                # サンプル問題3
                                q3 = question_service.create_question(
                                    title="ネットワーク - TCP/IP",
                                    content="インターネットで使用される基本的なプロトコルスイートは何ですか？",
                                    category="ネットワーク",
                                    explanation="TCP/IPは、インターネットで使用される基本的なプロトコルスイートです。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q3.id, "HTTP", False, 1)
                                choice_service.create_choice(q3.id, "FTP", False, 2)
                                choice_service.create_choice(q3.id, "TCP/IP", True, 3)
                                choice_service.create_choice(q3.id, "SMTP", False, 4)
                                
                                # サンプル問題4
                                q4 = question_service.create_question(
                                    title="セキュリティ - 暗号化",
                                    content="公開鍵暗号方式において、データの暗号化に使用されるキーはどれですか？",
                                    category="セキュリティ",
                                    explanation="公開鍵暗号方式では、公開鍵で暗号化し、秘密鍵で復号化します。",
                                    difficulty="hard"                                )
                                
                                choice_service.create_choice(q4.id, "秘密鍵", False, 1)
                                choice_service.create_choice(q4.id, "公開鍵", True, 2)
                                choice_service.create_choice(q4.id, "共通鍵", False, 3)
                                choice_service.create_choice(q4.id, "ハッシュ値", False, 4)
                                
                                # サンプル問題5
                                q5 = question_service.create_question(
                                    title="データベース - SQL",
                                    content="SQLにおいて、テーブルからデータを検索するために使用するコマンドはどれですか？",
                                    category="データベース",
                                    explanation="SELECT文は、データベースからデータを検索・取得するためのSQL文です。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q5.id, "INSERT", False, 1)
                                choice_service.create_choice(q5.id, "UPDATE", False, 2)
                                choice_service.create_choice(q5.id, "SELECT", True, 3)
                                choice_service.create_choice(q5.id, "DELETE", False, 4)
                                
                            st.success("✅ サンプルデータを5問作成しました！")
                            st.info("🎲 クイズページでテストしてみてください。")
                            
                except Exception as e:
                    st.error(f"❌ サンプルデータ作成に失敗: {e}")
        
        with col2:
            st.markdown("**データベース状態**")
            try:
                with get_database_session() as session:
                    question_service = QuestionService(session)
                    questions = question_service.get_random_questions(limit=1000)
                    
                    if len(questions) == 0:
                        st.warning("⚠️ データベースに問題がありません")
                        st.info("👈 左側の「サンプルデータ作成」ボタンでテスト用の問題を作成してください")
                    else:
                        st.success(f"✅ {len(questions)}問の問題が利用可能")
                        
                        # 最新の問題を表示
                        st.markdown("**最新の問題:**")
                        for i, q in enumerate(questions[-3:]):
                            st.text(f"• {q.title}")
                            
            except Exception as e:
                st.error(f"データベース状態確認エラー: {e}")
    else:
        st.error("⚠️ データベースに接続できません")

# フッター
st.markdown("---")
st.markdown("**Study Quiz App** - powered by Streamlit & Railway 🚀")
