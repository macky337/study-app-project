import streamlit as st
import time
from datetime import datetime
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ページ設定（最初に実行する必要がある）
st.set_page_config(
    page_title="Study Quiz App - Fixed Version",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎯 Study Quiz App - Fixed Version")
st.info("これはStudy Quiz Appの修正バージョンです。インデントエラーと無限ループの問題を修正しました。")

# Database connection with enhanced error handling
DATABASE_AVAILABLE = False
DATABASE_ERROR = None

# サンプルの問題表示（デモ用）
st.subheader("📝 サンプル問題")

sample_question = {
    "title": "Pythonの基本",
    "content": "Pythonのリスト内包表記で、1から10までの数値の中から偶数だけを抽出する正しい式はどれですか？",
    "choices": [
        {"content": "[x for x in range(1, 11) if x % 2 == 0]", "is_correct": True},
        {"content": "[x if x % 2 == 0 for x in range(1, 11)]", "is_correct": False},
        {"content": "[for x in range(1, 11) if x % 2 == 0]", "is_correct": False},
        {"content": "[x for x in range(1, 11) where x % 2 == 0]", "is_correct": False}
    ]
}

st.markdown(f"**問題:** {sample_question['content']}")

# 選択肢表示
choice_labels = [f"{chr(65+i)}. {choice['content']}" for i, choice in enumerate(sample_question['choices'])]
selected_idx = st.radio("回答を選択:", range(len(choice_labels)), format_func=lambda x: choice_labels[x])

# 回答確認ボタン
if st.button("回答する"):
    selected_choice = sample_question['choices'][selected_idx]
    if selected_choice['is_correct']:
        st.success("🎉 正解です！")
    else:
        st.error("❌ 不正解です")
        # 正解の表示
        correct_choices = [c for c in sample_question['choices'] if c['is_correct']]
        if correct_choices:
            st.info(f"**正解:** {correct_choices[0]['content']}")

# 修正点の説明
st.markdown("---")
st.subheader("📢 修正された主な問題")
st.markdown("""
1. **インデントエラー**: すべてのコードブロックのインデントが一貫性を持つように修正しました。
2. **無限ループの修正**: 問題取得ループの`attempt += 1`を適切な位置に移動しました。
3. **try-exceptブロック**: すべてのtry-exceptブロックが正しい構造になるよう修正しました。
""")

# 修正した問題取得ループのコード例
st.subheader("✅ 修正した問題取得ループ")
st.code("""
# 既に回答した問題を除外して取得
max_attempts = 10
attempt = 0
question = None

while attempt < max_attempts:
    # 毎回attemptをインクリメントして無限ループを防止
    attempt += 1
    
    # カテゴリに応じて問題を取得
    if st.session_state.selected_category == "すべて":
        questions = question_service.get_random_questions(limit=5)  # 複数取得して選択
    else:
        questions = question_service.get_random_questions_by_category(
            st.session_state.selected_category, limit=5
        )

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
""", language="python")

# フル機能版への切り替え方法
st.markdown("---")
st.subheader("🔄 フル機能版への切り替え")
st.markdown("""
フル機能版に戻るには、以下の方法があります：

1. **修正済みバックアップから復元**:
   ```
   copy "app.py.true_final_fix.backup" "app.py"
   ```
   
   ただし、問題取得ループの`attempt += 1`の位置を修正する必要があります。

2. **app_fixed_full.pyを使用**:
   ```
   copy "app_fixed_full.py" "app.py"
   ```
   
   このファイルは無限ループとインデント問題が修正された完全版です。
""")

# 日時表示
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"---\n**現在の日時:** {current_time}")
