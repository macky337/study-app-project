"""
問題表示に関する共通コンポーネント
"""
import streamlit as st
from typing import List, Tuple, Any

def display_question_header(question):
    """問題のヘッダー情報を表示"""
    # 辞書形式とSQLModelオブジェクト両方に対応
    def get_attr(obj, attr_name, default=None):
        if isinstance(obj, dict):
            return obj.get(attr_name, default)
        else:
            return getattr(obj, attr_name, default) if hasattr(obj, attr_name) else default
    
    # 問題タイトル
    title = get_attr(question, 'title')
    if title:
        st.subheader(f"📝 {title}")
    
    # 問題の詳細情報
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = get_attr(question, 'category')
        if category:
            st.info(f"📂 カテゴリ: {category}")
    
    with col2:
        difficulty = get_attr(question, 'difficulty')
        if difficulty:
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(difficulty, "🟡")
            st.info(f"{difficulty_emoji} 難易度: {difficulty}")
    
    with col3:
        question_id = get_attr(question, 'id')
        if question_id:
            st.info(f"🆔 問題ID: {question_id}")
    
    # 問題文
    content = get_attr(question, 'content')
    if content:
        st.markdown("### 📖 問題文")
        st.markdown(content)

def render_question_choices(question_content: str, choices: List[Any], key_suffix: str = "") -> Tuple[List[int], str]:
    """
    問題の選択肢を表示し、ユーザーの選択を取得
    
    Args:
        question_content: 問題文
        choices: 選択肢のリスト
        key_suffix: Streamlitコンポーネントのキー用接尾辞
    
    Returns:
        Tuple[List[int], str]: 選択されたインデックスのリスト、問題タイプ
    """
    if not choices:
        st.error("選択肢が見つかりません")
        return [], "single"
    
    # 正解の選択肢数を確認して問題タイプを判定
    correct_choices = [choice for choice in choices if getattr(choice, 'is_correct', False)]
    question_type = "multiple" if len(correct_choices) > 1 else "single"
    
    st.markdown("### 🎯 選択肢")
    
    if question_type == "multiple":
        st.info("💡 複数選択問題です。該当する選択肢をすべて選んでください。")
        selected_indices = []
        
        for i, choice in enumerate(choices):
            choice_text = getattr(choice, 'content', f"選択肢 {i+1}")
            if st.checkbox(
                f"**{chr(65+i)}.** {choice_text}",
                key=f"choice_{i}_{key_suffix}"
            ):
                selected_indices.append(i)
                
    else:
        st.info("💡 単一選択問題です。正しい選択肢を1つ選んでください。")
        choice_options = []
        for i, choice in enumerate(choices):
            choice_text = getattr(choice, 'content', f"選択肢 {i+1}")
            choice_options.append(f"**{chr(65+i)}.** {choice_text}")
        
        selected_index = st.radio(
            "選択してください:",
            range(len(choice_options)),
            format_func=lambda x: choice_options[x],
            key=f"radio_choice_{key_suffix}"
        )
        
        selected_indices = [selected_index] if selected_index is not None else []
    
    return selected_indices, question_type

def display_question_result(user_answer, question, choices: List[Any]):
    """
    問題の結果を表示
    
    Args:
        user_answer: ユーザーの回答データ
        question: 問題データ
        choices: 選択肢のリスト
    """
    if not user_answer:
        st.error("回答データが見つかりません")
        return
    
    # 結果のヘッダー
    is_correct = getattr(user_answer, 'is_correct', False)
    
    if is_correct:
        st.success("🎉 正解です！")
    else:
        st.error("❌ 不正解です")
    
    # 回答時間の表示
    if hasattr(user_answer, 'response_time_seconds'):
        response_time = user_answer.response_time_seconds
        if response_time:
            st.info(f"⏱️ 回答時間: {response_time:.1f}秒")
    
    # 選択肢の詳細表示
    st.markdown("### 📋 回答詳細")
    
    # ユーザーの選択した選択肢
    user_choices = []
    if hasattr(user_answer, 'selected_choice_ids') and user_answer.selected_choice_ids:
        user_choice_ids = user_answer.selected_choice_ids
        if isinstance(user_choice_ids, str):
            # 文字列形式の場合（例: "1,3,5"）
            try:
                user_choice_ids = [int(x.strip()) for x in user_choice_ids.split(',') if x.strip()]
            except ValueError:
                user_choice_ids = []
        user_choices = [choice for choice in choices if choice.id in user_choice_ids]
    
    # 各選択肢の表示
    for i, choice in enumerate(choices):
        choice_text = getattr(choice, 'content', f"選択肢 {i+1}")
        is_user_selected = choice in user_choices
        is_correct_choice = getattr(choice, 'is_correct', False)
        
        # アイコンの決定
        if is_correct_choice and is_user_selected:
            icon = "✅"  # 正解かつ選択済み
            color = "success"
        elif is_correct_choice and not is_user_selected:
            icon = "✅"  # 正解だが未選択
            color = "info"
        elif not is_correct_choice and is_user_selected:
            icon = "❌"  # 不正解だが選択済み
            color = "error"
        else:
            icon = "⚪"  # 不正解かつ未選択
            color = "secondary"
        
        # 選択肢の表示
        prefix = f"**{chr(65+i)}.** "
        if color == "success":
            st.success(f"{icon} {prefix}{choice_text}")
        elif color == "error":
            st.error(f"{icon} {prefix}{choice_text}")
        elif color == "info":
            st.info(f"{icon} {prefix}{choice_text}")
        else:
            st.write(f"{icon} {prefix}{choice_text}")
    
    # 解説の表示
    if hasattr(question, 'explanation') and question.explanation:
        st.markdown("### 💡 解説")
        st.markdown(question.explanation)
    
    # 正解率の表示（データベースから取得可能な場合）
    if hasattr(question, 'correct_rate') and question.correct_rate is not None:
        st.markdown(f"### 📊 この問題の正解率: {question.correct_rate:.1f}%")

def display_demo_question():
    """デモモード用の問題表示"""
    st.markdown("### 📝 デモ問題")
    st.markdown("**問題:** Pythonで使用される統合開発環境として正しいものはどれですか？")
    
    demo_choices = [
        "A. PyCharm",
        "B. Visual Studio Code", 
        "C. Jupyter Notebook",
        "D. すべて正しい"
    ]
    
    selected = st.radio("選択してください:", range(len(demo_choices)), 
                       format_func=lambda x: demo_choices[x])
    
    if st.button("回答する"):
        if selected == 3:  # "すべて正しい"
            st.success("🎉 正解です！")
            st.info("💡 PyCharm、Visual Studio Code、Jupyter Notebookはすべて、Pythonの開発に使用される統合開発環境です。")
        else:
            st.error("❌ 不正解です")
            st.info("💡 正解は「D. すべて正しい」です。これらはすべてPython開発で使用される統合開発環境です。")
