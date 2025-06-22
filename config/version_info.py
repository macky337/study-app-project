# -*- coding: utf-8 -*-
"""
アプリケーションバージョン情報管理
"""
from datetime import datetime
from database.connection import engine
from contextlib import contextmanager
import streamlit as st

# アプリケーション情報
APP_VERSION = "1.0.249"
LAST_UPDATED = "2025-06-14"
APP_NAME = "Study Quiz App"

def get_app_info():
    """アプリケーション情報を取得"""
    return {
        "version": APP_VERSION,
        "last_updated": LAST_UPDATED,
        "app_name": APP_NAME,
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M")
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
    st.caption(f"最終更新: {app_info['last_updated']}")
    
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
