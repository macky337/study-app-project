import streamlit as st

st.title("Study App Project - MVP")
st.write("これは MVP 版です。ここにクイズ UI が載ります。")

# サイドバーに基本的なナビゲーションを追加
with st.sidebar:
    st.header("メニュー")
    page = st.selectbox(
        "ページを選択",
        ["ホーム", "問題作成", "クイズ", "学習履歴"]
    )

# 選択されたページに応じた表示
if page == "ホーム":
    st.subheader("🎯 Study App へようこそ！")
    st.markdown("""
    このアプリは資格試験対策用の学習支援ツールです。
    
    **主な機能:**
    - 📝 問題・選択肢・解説の登録
    - 🎲 ランダムクイズ出題
    - 📊 学習履歴の管理
    - 🔄 間違えた問題の復習
    """)
    
elif page == "問題作成":
    st.subheader("📝 問題作成")
    st.info("問題作成機能は準備中です。")
    
elif page == "クイズ":
    st.subheader("🎲 クイズ")
    st.info("クイズ機能は準備中です。")
    
elif page == "学習履歴":
    st.subheader("📊 学習履歴")
    st.info("学習履歴機能は準備中です。")

# フッター
st.markdown("---")
st.markdown("**Study App Project** - powered by Streamlit 🚀")
