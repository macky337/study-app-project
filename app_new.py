"""
Study Quiz App - メインアプリケーション
ファイル分割後のルーターとして機能
"""
import streamlit as st
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

# 設定とページのインポート
try:
    from config.app_config import initialize_database, initialize_session_state, PAGES
    from pages.quiz_page import quiz_page
    from pages.statistics_page import render_statistics_page
    from pages.question_management_page import render_question_management_page
    from pages.settings_page import render_settings_page
except ImportError as e:
    st.error(f"必要なモジュールのインポートに失敗しました: {e}")
    st.stop()

# データベース接続の初期化
try:
    DATABASE_AVAILABLE, DATABASE_ERROR = initialize_database()
except Exception as e:
    DATABASE_AVAILABLE = False
    DATABASE_ERROR = str(e)
    st.error(f"データベース初期化エラー: {e}")

# セッション状態の初期化
initialize_session_state()

# メインページのタイトル
st.title("🎯 Study Quiz App")

# サイドバーでページ選択
with st.sidebar:
    st.title("📚 メニュー")
    
    # ページ選択
    selected_page = st.selectbox(
        "ページを選択",
        PAGES,
        key="page_selector"
    )
    
    st.markdown("---")
    
    # データベース状態表示
    if DATABASE_AVAILABLE:
        st.success("✅ データベース接続中")
    else:
        st.error("❌ データベース未接続")
        if DATABASE_ERROR:
            with st.expander("🔍 エラー詳細"):
                st.error(DATABASE_ERROR)
      # セッション情報表示
    if hasattr(st.session_state, 'session_id'):
        st.markdown(f"**セッション:** `{st.session_state.session_id[-8:]}`")

def render_home_page():
    """ホームページの表示"""
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
        - 📄 PDFからの問題抽出
        """)
        
        # データベース統計を表示
        if DATABASE_AVAILABLE:
            try:
                from database.operations import QuestionService, UserAnswerService
                from database.connection import get_session_context
                
                with get_session_context() as session:
                    question_service = QuestionService(session)
                    user_answer_service = UserAnswerService(session)
                    
                    # 基本統計を取得
                    questions = question_service.get_random_questions(limit=1000)
                    stats = user_answer_service.get_user_stats(st.session_state.session_id)
                    
                    st.markdown("### 📊 統計情報")
                    col1_1, col1_2, col1_3 = st.columns(3)
                    
                    with col1_1:
                        st.metric("総問題数", len(questions))
                    with col1_2:
                        st.metric("回答済み", stats.get('total', 0))
                    with col1_3:
                        st.metric("正答率", f"{stats.get('accuracy', 0)}%")
                        
            except Exception as e:
                st.warning(f"統計情報の取得に失敗しました: {e}")
        else:
            st.warning("⚠️ データベースに接続できません（デモモードで動作中）")
    
    with col2:
        st.markdown("### 🚀 クイズを開始")
        st.markdown("カテゴリを選択して問題に挑戦！")
        
        if st.button("🎲 クイズモードへ", use_container_width=True, key="start_quiz"):
            # クイズ関連のセッション状態をリセット
            quiz_reset_keys = [
                'current_question', 'show_result', 'user_answer',
                'answered_questions', 'quiz_choice_key', 'start_time'
            ]
            
            for key in quiz_reset_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
            
        st.info("💡 クイズモードでは、カテゴリを選択して問題を解くことができます")
        
        # 簡単な操作ガイド
        st.markdown("### 📖 使い方")
        st.markdown("""
        1. **🎲 クイズ**: 問題を解いて学習
        2. **📊 統計**: 学習進捗を確認
        3. **🔧 問題管理**: 問題の追加・編集
        4. **⚙️ 設定**: アプリの設定変更
        """)

# 選択されたページに応じて表示
try:
    if selected_page == "🏠 ホーム":
        render_home_page()
    elif selected_page == "🎲 クイズ":
        quiz_page()
    elif selected_page == "📊 統計":
        render_statistics_page()
    elif selected_page == "🔧 問題管理":
        render_question_management_page()
    elif selected_page == "⚙️ 設定":
        render_settings_page()
    else:
        st.error(f"不明なページが選択されました: {selected_page}")

except Exception as e:
    st.error(f"ページの表示でエラーが発生しました: {e}")
    logging.error(f"Page rendering error: {e}")
