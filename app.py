import streamlit as st
import time
from datetime import datetime
from sqlmodel import Session
from database.connection import engine
from database.operations import QuestionService, ChoiceService, UserAnswerService
from utils.helpers import generate_session_id, format_accuracy, get_difficulty_emoji

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

st.title("🎯 Study Quiz App")
st.markdown("資格試験対策用のクイズ学習アプリ")

# サイドバーに基本的なナビゲーションを追加
with st.sidebar:
    st.header("📚 メニュー")
    page = st.selectbox(
        "ページを選択",
        ["🏠 ホーム", "🎲 クイズ", "📊 統計", "⚙️ 設定"]
    )
    
    st.markdown("---")
    st.markdown(f"**セッションID:** `{st.session_state.session_id[-8:]}`")

# データベースセッションを取得する関数
@st.cache_resource
def get_database_session():
    return Session(engine)

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
        """)
        
        # データベース統計を表示
        try:
            with get_database_session() as session:
                question_service = QuestionService(session)
                user_answer_service = UserAnswerService(session)
                
                # 問題数を取得
                total_questions = len(question_service.get_random_questions(limit=1000))
                
                # セッション統計を取得
                stats = user_answer_service.get_user_stats(st.session_state.session_id)
                
                st.markdown("### � 統計情報")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("総問題数", total_questions)
                with col2:
                    st.metric("回答済み", stats['total'])
                with col3:
                    st.metric("正答率", f"{stats['accuracy']}%")
                    
        except Exception as e:
            st.error(f"データベース接続エラー: {e}")
    
    with col2:
        st.markdown("### 🚀 クイズを開始")
        if st.button("🎲 ランダムクイズ", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.show_result = False
            # クイズページに切り替え（手動でサイドバーから選択してもらう）
            st.success("サイドバーから「🎲 クイズ」を選択してください！")

elif page == "🎲 クイズ":
    st.subheader("🎲 クイズモード")
    
    try:
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            user_answer_service = UserAnswerService(session)
            
            # 新しい問題を取得
            if st.session_state.current_question is None:
                questions = question_service.get_random_questions(limit=1)
                if questions:
                    st.session_state.current_question = questions[0]
                    st.session_state.user_answer = None
                    st.session_state.show_result = False
                    st.session_state.start_time = time.time()
                else:
                    st.error("問題が見つかりません。")
                    st.stop()
            
            question = st.session_state.current_question
            
            # 問題表示
            st.markdown(f"### {get_difficulty_emoji(question.difficulty)} {question.title}")
            st.markdown(f"**カテゴリ:** {question.category}")
            st.markdown(f"**問題:** {question.content}")
            
            # 選択肢を取得
            choices = choice_service.get_choices_by_question(question.id)
            
            if not st.session_state.show_result:
                # 回答フェーズ
                st.markdown("---")
                st.markdown("**選択肢を選んでください:**")
                
                choice_labels = [f"{chr(65+i)}. {choice.content}" for i, choice in enumerate(choices)]
                
                selected_idx = st.radio(
                    "回答を選択:",
                    range(len(choices)),
                    format_func=lambda x: choice_labels[x],
                    key="quiz_choice"
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
                        
                        st.session_state.user_answer = {
                            'selected_choice': selected_choice,
                            'is_correct': is_correct,
                            'answer_time': answer_time
                        }
                        st.session_state.show_result = True
                        st.rerun()
                
                with col2:
                    if st.button("⏭️ スキップ", use_container_width=True):
                        st.session_state.current_question = None
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
                        st.session_state.current_question = None
                        st.rerun()
                
                with col2:
                    if st.button("🏠 ホームに戻る", use_container_width=True):
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        # ホームページに切り替え（手動でサイドバーから選択してもらう）
                        st.success("サイドバーから「🏠 ホーム」を選択してください！")
    
    except Exception as e:
        st.error(f"クイズ機能でエラーが発生しました: {e}")

elif page == "📊 統計":
    st.subheader("📊 学習統計")
    
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

# フッター
st.markdown("---")
st.markdown("**Study Quiz App** - powered by Streamlit & Railway 🚀")
