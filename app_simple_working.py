import streamlit as st
import time
import datetime
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ページ設定
st.set_page_config(
    page_title="Study Quiz App - Simple Version",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Study Quiz App - Simple Version")

st.info("これはStudy Quiz Appのシンプルバージョンです。インデントエラーを修正しました。")

# セッション状態の初期化
if 'count' not in st.session_state:
    st.session_state.count = 0

# カウントアップボタン
if st.button("テスト: アプリが正常に動作しています"):
    st.session_state.count += 1
    st.success(f"✅ アプリは正常に動作しています! (カウント: {st.session_state.count})")

# サンプルのクイズ問題
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

# 元のコードの問題点を説明
st.markdown("---")
st.subheader("🛠️ 元のコードの問題点")
st.markdown("""
1. **インデントエラー**: 多くの箇所でインデントの深さに一貫性がなく、Pythonの構文エラーが発生していました。
2. **無限ループの問題**: 問題取得ループで適切に`attempt`変数がインクリメントされていなかったため、特定の条件下で無限ループになっていました。
3. **try-exceptブロックの構造**: 一部のtry-exceptブロックが正しく構成されていませんでした。
""")

# 修正済みのコード例を表示
st.subheader("✅ 修正済みコード例")
fixed_code = """
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
"""
st.code(fixed_code, language="python")

# データベース統計表示の正しい構造
st.subheader("📊 データベース統計表示の正しい構造")
db_code = """
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
"""
st.code(db_code, language="python")

# 復旧手順
st.markdown("---")
st.subheader("🔄 完全バージョンの復旧手順")
st.markdown("""
元の完全なアプリケーションを正しいバージョンに復元するには、以下の手順に従ってください：

1. 修正済みのバックアップファイル`app.py.true_final_fix.backup`を元に、必要なインデント修正を加えて復元
2. 各try-exceptブロックの構造を確認し修正
3. 無限ループになりうる箇所（特に問題取得ループ）を上記のコード例を参考に修正

または、プロジェクトリポジトリの修正済みバージョンを使用してください。
""")

# 日時表示
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"---\n**現在の日時:** {current_time}")
