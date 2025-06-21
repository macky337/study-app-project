"""
統計ページ - 学習進捗と統計情報の表示
"""
import streamlit as st
from config.app_config import DATABASE_AVAILABLE

def render_statistics_page():
    """統計ページのメイン表示"""
    st.title("📊 学習統計")
    
    # リアルタイムでデータベース接続をチェック
    from config.app_config import check_database_connection
    db_available, db_error = check_database_connection()
    
    if not db_available:
        st.warning("⚠️ データベースに接続できないため、統計機能は利用できません。")
        render_demo_statistics()
        return
    
    try:
        from database.operations import UserAnswerService
        from database.connection import get_session_context
        
        with get_session_context() as session:
            user_answer_service = UserAnswerService(session)
            
            # 統計情報を取得・表示
            display_main_statistics(user_answer_service)
            
    except Exception as e:
        st.error(f"統計機能でエラーが発生しました: {e}")
        render_demo_statistics()

def display_main_statistics(user_answer_service):
    """メイン統計情報の表示"""
    
    # 全体統計とセッション統計を取得
    all_stats = user_answer_service.get_user_stats()
    session_stats = user_answer_service.get_user_stats(st.session_state.session_id)
    
    st.markdown("### 📈 統計サマリー")
    
    # 統計情報を2列で表示
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
    
    # プログレスバーを表示
    if session_stats['total'] > 0:
        st.markdown("### 🎯 進捗")
        progress = session_stats['accuracy'] / 100
        st.progress(progress)
        st.markdown(f"現在の正答率: **{session_stats['accuracy']}%**")
    
    # 詳細統計情報
    display_detailed_statistics(user_answer_service)

def display_detailed_statistics(user_answer_service):
    """詳細統計情報の表示"""
    st.markdown("### 📊 詳細統計")
    
    # カテゴリ別統計
    try:
        category_stats = user_answer_service.get_category_stats()
        if category_stats:
            st.markdown("#### 📚 カテゴリ別成績")
            
            for category, stats in category_stats.items():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{category}**")
                
                with col2:
                    st.markdown(f"回答数: {stats['total']}")
                
                with col3:
                    accuracy = stats['accuracy'] if stats['total'] > 0 else 0
                    st.markdown(f"正答率: {accuracy:.1f}%")
                    
                    # プログレスバー
                    progress = accuracy / 100
                    st.progress(progress)
    
    except Exception as e:
        st.warning(f"カテゴリ別統計の取得でエラーが発生しました: {e}")
    
    # 時系列統計
    display_timeline_statistics(user_answer_service)

def display_timeline_statistics(user_answer_service):
    """時系列統計の表示"""
    st.markdown("#### 📈 時系列統計")
    
    try:
        # 過去7日間の統計
        daily_stats = user_answer_service.get_daily_stats(days=7)
        
        if daily_stats:
            # 簡単なチャート表示
            dates = list(daily_stats.keys())
            accuracies = [stats['accuracy'] for stats in daily_stats.values()]
            
            if dates and accuracies:
                st.line_chart(dict(zip(dates, accuracies)))
            else:
                st.info("まだ十分なデータがありません。")
        else:
            st.info("時系列データがありません。")
    
    except Exception as e:
        st.warning(f"時系列統計の取得でエラーが発生しました: {e}")

def render_demo_statistics():
    """デモモード用の統計表示"""
    st.info("🔄 デモモードで統計を表示しています。")
    
    # デモ用の統計データ
    demo_stats = {
        'total_questions': 50,
        'correct_answers': 35,
        'accuracy': 70.0,
        'session_questions': 10,
        'session_correct': 8,
        'session_accuracy': 80.0
    }
    
    st.markdown("### 📈 統計サマリー（デモ）")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌍 全体統計")
        st.metric("総回答数", demo_stats['total_questions'])
        st.metric("正解数", demo_stats['correct_answers'])
        st.metric("正答率", f"{demo_stats['accuracy']:.1f}%")
    
    with col2:
        st.markdown("#### 👤 セッション統計")
        st.metric("セッション回答数", demo_stats['session_questions'])
        st.metric("セッション正解数", demo_stats['session_correct'])
        st.metric("セッション正答率", f"{demo_stats['session_accuracy']:.1f}%")
    
    # プログレスバー
    st.markdown("### 🎯 進捗")
    progress = demo_stats['session_accuracy'] / 100
    st.progress(progress)
    st.markdown(f"現在の正答率: **{demo_stats['session_accuracy']:.1f}%**")
    
    # デモ用チャート
    st.markdown("#### 📈 学習進捗（デモ）")
    demo_chart_data = {
        '月': 65,
        '火': 72,
        '水': 68,
        '木': 75,
        '金': 80,
        '土': 78,
        '日': 82
    }
    st.line_chart(demo_chart_data)
