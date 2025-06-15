import streamlit as st
import os

# ページ設定
st.set_page_config(
    page_title="Study Quiz App",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Study Quiz App")
st.write("Railway起動テスト中...")

# 環境変数表示
st.subheader("環境情報")
st.write(f"PORT: {os.getenv('PORT', 'Not set')}")
st.write(f"DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
st.write(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")

st.success("✅ アプリケーションが正常に起動しました！")

# データベース接続テスト
try:
    from database.connection import engine
    if engine:
        st.success("✅ データベース接続: 成功")
    else:
        st.warning("⚠️ データベース接続: 失敗（デモモードで動作）")
except Exception as e:
    st.warning(f"⚠️ データベース接続エラー: {str(e)}")

st.info("🚧 現在Railway本番環境の動作確認中です。機能は段階的に復旧予定です。")
