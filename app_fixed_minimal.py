import streamlit as st
import time
from datetime import datetime
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    from database.connection import engine, DATABASE_URL, get_session_context, safe_database_operation

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
                with get_session_context() as session:
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
                print(f"エラー発生: {e}")
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
        with get_session_context() as session:
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
                    
                    # 毎回attemptをインクリメントして無限ループを防止
                    attempt += 1

                    if not questions:
                        # 問題が取得できなかった場合は次のループへ
                        continue

                    # 未回答の問題を探す
                    for q in questions:
                        if q.id not in st.session_state.answered_questions:
                            question = q
                            break

                    if question:
                        # 問題が見つかったらループを抜ける
                        break
                    elif len(st.session_state.answered_questions) > 0:
                        # 全ての問題が回答済みの場合、リセット
                        st.session_state.answered_questions.clear()
                        st.info("🔄 全ての問題を回答しました。問題をリセットします。")
                        if questions:  # 念のためチェック
                            question = questions[0]  # 最初の問題を選択
                            break

                if question:
                    # セッション外でも使えるようにIDのみ保存
                    st.session_state.current_question_id = question.id
                    st.session_state.current_question_title = question.title
                    st.session_state.current_question_content = question.content
                    st.session_state.current_question_category = question.category
                    st.session_state.current_question_difficulty = question.difficulty
                    st.session_state.current_question_explanation = question.explanation

                    # 選択肢情報も取得して保存
                    choices = choice_service.get_choices_by_question(question.id)
                    st.session_state.current_choices = [
                        {"id": c.id, "content": c.content, "is_correct": c.is_correct, "order_num": c.order_num}
                        for c in choices
                    ]

                    st.session_state.user_answer = None
                    st.session_state.show_result = False
                    st.session_state.start_time = time.time()
                    st.session_state.quiz_choice_key += 1  # ラジオボタンのキーを更新
                else:
                    st.error("問題が見つかりません。")
                    st.stop()
            
            # 保存した情報から問題を表示（セッションセーフ）
            question_id = st.session_state.current_question_id
            question_title = st.session_state.current_question_title
            question_content = st.session_state.current_question_content
            question_category = st.session_state.current_question_category
            question_difficulty = st.session_state.current_question_difficulty

            # 進捗表示
            if len(st.session_state.answered_questions) > 0:
                st.info(f"📊 このセッションで回答済み: {len(st.session_state.answered_questions)}問")

            # 問題表示
            st.markdown(f"### {get_difficulty_emoji(question_difficulty)} {question_title}")
            st.markdown(f"**カテゴリ:** {question_category}")
            st.markdown(f"**問題:** {question_content}")

            # 問題タイプの判断（問題文に「すべて選べ」「複数選べ」などの表現があるか）
            is_multiple_choice = False
            multiple_choice_indicators = ["すべて選べ", "複数選べ", "全て選べ", "複数の選択肢", "複数回答"]
            for indicator in multiple_choice_indicators:
                if indicator in question_content:
                    is_multiple_choice = True
                    break

            # 正解の選択肢の数を確認（2つ以上が正解なら複数選択問題と判断）
            correct_choices_count = sum(1 for c in st.session_state.current_choices if c["is_correct"])
            if correct_choices_count > 1:
                is_multiple_choice = True

            # 問題が複数選択問題と判断された場合、その旨を表示
            if is_multiple_choice:
                st.info("💡 この問題は複数の選択肢を選ぶ問題です。該当するものをすべて選択してください。")

            # 保存された選択肢情報を使用
            choices = st.session_state.current_choices

            # 選択肢が存在しない場合のエラーハンドリング
            if not choices:
                st.error("❌ この問題の選択肢が見つかりません。")
                st.info("🔧 問題データに不具合があります。管理者にお知らせください。")
                st.code(f"問題ID: {question_id}, タイトル: {question_title}")

                # 次の問題を表示するボタン
                if st.button("➡️ 次の問題へ", use_container_width=True):
                    st.session_state.answered_questions.add(question_id)
                    st.session_state.current_question_id = None
                    st.session_state.show_result = False
                    st.session_state.quiz_choice_key += 1
                    st.rerun()
                st.stop()  # return の代わりに st.stop() を使用

            print(f"INFO: 問題ID {question_id} の選択肢数: {len(choices)}")  # デバッグログ

            if not st.session_state.show_result:
                # 回答フェーズ
                st.markdown("---")
                st.markdown("**選択肢を選んでください:**")

                # デバッグ情報表示（開発時のみ）
                if len(choices) == 0:
                    st.error("選択肢データが取得できません")
                    st.stop()

                choice_labels = [f"{chr(65+i)}. {choice['content']}" for i, choice in enumerate(choices)]
                print(f"DEBUG: 選択肢ラベル: {choice_labels}")  # デバッグログ
                
                # 選択肢が空でないことを確認
                if not choice_labels:
                    st.error("選択肢の生成に失敗しました")
                    st.stop()

                # 問題タイプに応じて入力方法を切り替え
                if is_multiple_choice:
                    # 複数選択の場合はチェックボックス
                    selected_indices = []
                    for i, label in enumerate(choice_labels):
                        if st.checkbox(label, key=f"quiz_choice_checkbox_{st.session_state.quiz_choice_key}_{i}"):
                            selected_indices.append(i)

                    # 選択された選択肢があるかチェック
                    if not selected_indices and st.button("🔍 回答する", use_container_width=True):
                        st.warning("⚠️ 選択肢を少なくとも1つ選んでください")
                        st.stop()
                else:
                    # 単一選択の場合はラジオボタン
                    selected_idx = st.radio(
                        "回答を選択:",
                        range(len(choices)),
                        format_func=lambda x: choice_labels[x] if x < len(choice_labels) else "エラー",
                        key=f"quiz_choice_{st.session_state.quiz_choice_key}"
                    )
                    selected_indices = [selected_idx]
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔍 回答する", use_container_width=True):
                        # 回答時間を計算
                        answer_time = time.time() - st.session_state.start_time

                        # 複数選択の場合
                        if is_multiple_choice:
                            # 選択された選択肢が一つもない場合は警告
                            if not selected_indices:
                                st.warning("⚠️ 選択肢を少なくとも1つ選んでください")
                                st.stop()

                            # 選択された選択肢と正解の選択肢を比較
                            selected_choices = [choices[idx] for idx in selected_indices]
                            correct_choices = [c for c in choices if c["is_correct"]]

                            # 完全に一致した場合のみ正解
                            selected_correct_ids = set(c["id"] for c in selected_choices if c["is_correct"])
                            all_correct_ids = set(c["id"] for c in correct_choices)

                            is_all_correct = selected_correct_ids == all_correct_ids
                            is_no_wrong = all(c["is_correct"] for c in selected_choices)

                            is_correct = is_all_correct and is_no_wrong

                            # 選択肢情報をセーブ
                            choice_data_list = [
                                {
                                    'id': c["id"],
                                    'content': c["content"],
                                    'is_correct': c["is_correct"]
                                } for c in selected_choices
                            ]

                            # データベースに記録（最初の選択肢のみ）
                            if selected_choices:
                                first_choice = selected_choices[0]
                                user_answer_service.record_answer(
                                    question_id=question_id,
                                    selected_choice_id=first_choice["id"],
                                    is_correct=is_correct,
                                    answer_time=answer_time,
                                    session_id=st.session_state.session_id
                                )

                            # セッション情報にすべての選択肢を保存
                            st.session_state.user_answer = {
                                'selected_choices': choice_data_list,
                                'is_correct': is_correct,
                                'answer_time': answer_time,
                                'is_multiple_choice': True
                            }
                        else:
                            # 単一選択の場合（既存のコード）
                            selected_choice = choices[selected_indices[0]]
                            is_correct = selected_choice["is_correct"]

                            # 回答をセッション内で記録
                            user_answer_service.record_answer(
                                question_id=question_id,
                                selected_choice_id=selected_choice["id"],
                                is_correct=is_correct,
                                answer_time=answer_time,
                                session_id=st.session_state.session_id
                            )

                            # 選択肢情報をセーブ
                            choice_data = {
                                'id': selected_choice["id"],
                                'content': selected_choice["content"],
                                'is_correct': is_correct
                            }

                            st.session_state.user_answer = {
                                'selected_choice': choice_data,
                                'is_correct': is_correct,
                                'answer_time': answer_time,
                                'is_multiple_choice': False
                            }

                        # 回答済み問題に追加
                        st.session_state.answered_questions.add(question_id)
                        st.session_state.show_result = True
                        st.rerun()

                with col2:
                    if st.button("⏭️ スキップ", use_container_width=True):
                        # スキップした問題も回答済みとしてマーク（無限ループ防止）
                        st.session_state.answered_questions.add(question_id)
                        st.session_state.current_question_id = None
                        st.session_state.show_result = False
                        st.rerun()

            else:
                # 結果表示フェーズ
                st.markdown("---")
                user_answer = st.session_state.user_answer

                # 複数選択問題と単一選択問題で表示を分ける
                is_multiple_choice = user_answer.get('is_multiple_choice', False)

                if user_answer['is_correct']:
                    st.success("🎉 正解です！")
                else:
                    st.error("❌ 不正解です")
                    # 正解の選択肢を表示（セッションに保存されている情報から）
                    correct_choices = [c for c in st.session_state.current_choices if c["is_correct"]]

                    if is_multiple_choice:
                        st.info("**正解の選択肢:**")
                        for correct in correct_choices:
                            st.info(f"- {correct['content']}")

                        # 選択した選択肢を表示
                        st.markdown("**あなたの選択:**")
                        selected_choices = user_answer.get('selected_choices', [])
                        for choice in selected_choices:
                            icon = "✅" if choice['is_correct'] else "❌"
                            st.markdown(f"- {icon} {choice['content']}")
                    else:
                        # 単一選択問題の場合
                        if correct_choices:
                            st.info(f"**正解:** {correct_choices[0]['content']}")
                        else:
                            st.warning("正解情報を取得できませんでした")

                # 解説表示（セッションに保存されている情報から）
                explanation = st.session_state.current_question_explanation
                if explanation:
                    st.markdown(f"**💡 解説:** {explanation}")

                # 回答時間表示
                st.markdown(f"**⏱️ 回答時間:** {user_answer['answer_time']:.1f}秒")

                # 次の問題ボタン
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("➡️ 次の問題", use_container_width=True):
                        # 次の問題への移行
                        st.session_state.current_question_id = None
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
        print(f"エラー発生: {e}")
        st.error(f"クイズ機能でエラーが発生しました: {e}")
