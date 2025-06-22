"""
Study Quiz App - メインアプリケーション
ファイル分割後のルーターとして機能

"""
import streamlit as st
import logging

# ロギング設定（最小限に変更）
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

# 設定とページのインポート
try:
    from config.app_config import initialize_database, initialize_session_state, PAGES, configure_page
    from config.version_info import render_system_info
    from app_pages.quiz_page import quiz_page
    from app_pages.statistics_page import render_statistics_page
    from app_pages.question_management_page import render_question_management_page
    from app_pages.settings_page import render_settings_page
    
    # ページ設定（最初に実行する必要がある）
    configure_page()
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
    # ページ選択（デフォルトインデックスを管理）
    if 'current_page' not in st.session_state:
        st.session_state.current_page = PAGES[0]
    default_index = PAGES.index(st.session_state.current_page)
    # selectboxのkeyをcurrent_pageにして自動更新
    selected_page = st.selectbox(
        "ページを選択",
        PAGES,
        index=default_index,
        key="current_page"    )
    
    st.markdown("---")
    
    # システム情報をサイドバー下部に表示
    render_system_info()

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
        """)          # データベース統計を表示
        db_available, db_error = check_database_connection()
        if db_available:
            try:
                # モデルを安全に読み込み
                from config.app_config import ensure_models_loaded
                ensure_models_loaded()
                
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
    current_page = st.session_state.current_page
    
    # デバッグ情報表示
    st.sidebar.markdown(f"**現在のページ:** {current_page}")
    
    if current_page == "🏠 ホーム":
        render_home_page()
    elif current_page == "🎲 クイズ":
        quiz_page()
    elif current_page == "📊 統計":
        render_statistics_page()
    elif current_page == "🔧 問題管理":
        render_question_management_page()
    elif current_page == "⚙️ 設定":
        render_settings_page()
    else:
        st.error(f"不明なページが選択されました: {current_page}")
        render_home_page()  # フォールバック

except Exception as e:
    st.error(f"ページの表示でエラーが発生しました: {e}")
    logging.error(f"Page rendering error: {e}")
    # エラーが発生した場合はホームページを表示
    try:
        render_home_page()
    except Exception as fallback_error:
        st.error(f"ホームページの表示にも失敗しました: {fallback_error}")
        st.markdown("### ⚠️ システムエラー")
        st.markdown("アプリケーションの起動に問題があります。ページを再読み込みしてください。")
