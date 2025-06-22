# -*- coding: utf-8 -*-
"""
アプリケーションバージョン情報管理（Git自動生成）
"""
from datetime import datetime
from database.connection import engine
from contextlib import contextmanager
import streamlit as st

APP_NAME = "Study Quiz App"

def get_app_info():
    """アプリケーション情報を取得（Git情報から自動生成）"""
    try:
        from config.git_version import get_git_commit_info, get_repository_info
        
        # Git情報を取得
        version, last_updated, commit_hash = get_git_commit_info()
        repo_info = get_repository_info()
        
        return {
            "version": version,
            "last_updated": last_updated,
            "app_name": APP_NAME,
            "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit_hash": commit_hash,
            "branch": repo_info.get("branch", "unknown"),
            "commit_count": repo_info.get("commit_count", 0)
        }
    except Exception as e:
        # Git情報取得に失敗した場合のフォールバック
        print(f"Git情報取得エラー: {e}")
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "app_name": APP_NAME,
            "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit_hash": "unknown",
            "branch": "unknown",
            "commit_count": 0
        }

def get_database_status():
    """データベース接続状況を取得"""
    try:
        if engine is None:
            return {
                "status": "disconnected",
                "message": "デモモード",
                "icon": "⚠️",
                "color": "orange"
            }
        
        # 軽量な接続テスト
        from sqlmodel import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "message": "接続中",
                "icon": "✅",
                "color": "green"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"エラー: {str(e)[:50]}...",
            "icon": "❌", 
            "color": "red"
        }

def render_system_info():
    """システム情報をサイドバーに表示"""
    st.markdown("### 📱 システム情報")
    
    # アプリ情報
    app_info = get_app_info()
    
    # バージョン情報をコンパクトに表示
    st.markdown(f"**{app_info['app_name']}** v{app_info['version']}")
    st.caption(f"最終更新: {app_info['last_updated']} (#{app_info['commit_count']})")
    
    # データベース状況をステータスバッジ風に表示
    db_status = get_database_status()
    
    # ステータスに応じて色分け
    if db_status['status'] == 'connected':
        st.success(f"{db_status['icon']} DB {db_status['message']}")
    elif db_status['status'] == 'disconnected':
        st.warning(f"{db_status['icon']} DB {db_status['message']}")
    else:
        st.error(f"{db_status['icon']} DB {db_status['message']}")
    
    # 詳細情報の展開オプション
    with st.expander("🔍 詳細情報", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**アプリ**")
            st.caption(f"コミット: {app_info['commit_hash']}")
            st.caption(f"ブランチ: {app_info['branch']}")
            st.caption(f"現在時刻: {app_info['current_date']}")
            if hasattr(st.session_state, 'session_id'):
                st.caption(f"セッション: {st.session_state.session_id[-8:]}")
        
        with col2:
            st.markdown("**環境**")
            import platform
            st.caption(f"Python: {platform.python_version()}")
            st.caption(f"OS: {platform.system()}")
        
        # データベース詳細
        if db_status['status'] == 'error':
            st.markdown("**エラー詳細:**")
            st.code(db_status['message'], language=None)
