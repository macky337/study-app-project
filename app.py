import streamlit as st
import time
from datetime import datetime

# ページ設定（最初に実行する必要がある）
st.set_page_config(
    page_title="Study Quiz App",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection with error handling
DATABASE_AVAILABLE = False
DATABASE_ERROR = None

try:
    from sqlmodel import Session
    from database.connection import engine, DATABASE_URL
    from database.operations import QuestionService, ChoiceService, UserAnswerService
    from services.question_generator import QuestionGenerator
    from services.pdf_processor import PDFProcessor
    from services.pdf_question_generator import PDFQuestionGenerator
    from services.past_question_extractor import PastQuestionExtractor
    from utils.helpers import generate_session_id, format_accuracy, get_difficulty_emoji
    
    DATABASE_AVAILABLE = engine is not None
    
except Exception as e:
    DATABASE_ERROR = str(e)
    DATABASE_AVAILABLE = False
    print(f"❌ Database connection error: {e}")
    
    # Create mock functions for demo
    def generate_session_id():
        return "demo_session"

# データベースエラーがある場合は警告を表示
if DATABASE_ERROR:
    st.error(f"⚠️ Database connection failed: {DATABASE_ERROR}")

# セッション状態の初期化
if 'session_id' not in st.session_state:
    st.session_state.session_id = generate_session_id()
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []
if 'answered_questions' not in st.session_state:
    st.session_state.answered_questions = set()
if 'quiz_choice_key' not in st.session_state:
    st.session_state.quiz_choice_key = 1

st.title("🎯 Study Quiz App")
st.markdown("資格試験対策用のクイズ学習アプリ")

# サイドバーに基本的なナビゲーションを追加
with st.sidebar:
    st.header("📚 メニュー")
    
    # ページ選択状態を管理
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 ホーム"
    
    page = st.selectbox(
        "ページを選択",
        ["🏠 ホーム", "🎲 クイズ", "📊 統計", "🔧 問題管理", "⚙️ 設定"],
        index=["🏠 ホーム", "🎲 クイズ", "📊 統計", "🔧 問題管理", "⚙️ 設定"].index(st.session_state.page),
        key="page_selector"
    )
      # ページが変更された場合、セッション状態を更新
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"**セッションID:** `{st.session_state.session_id[-8:]}`")

# 現在のページを取得
page = st.session_state.page

# データベースセッションを取得する関数
@st.cache_resource
def get_database_session():
    if DATABASE_AVAILABLE and engine:
        return Session(engine)
    else:
        return None

# Database connection status check
def check_database_status():
    if not DATABASE_AVAILABLE:
        st.error("🚨 **データベース接続エラー**")
        st.markdown("""
        **考えられる原因:**
        - Railway Variables で `DATABASE_URL` が設定されていない
        - PostgreSQL サービスが追加されていない
        - Variable Reference が正しく設定されていない
        
        **解決方法:**
        1. Railway ダッシュボードを開く
        2. Variables タブで `DATABASE_URL` を確認
        3. PostgreSQL サービスを追加（未追加の場合）
        4. Variable Reference として `${{Postgres.DATABASE_URL}}` を設定
        """)
        return False
    return True

# 選択されたページに応じた表示
if page == "🏠 ホーム":
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
        """)
        
        # データベース統計を表示
        if DATABASE_AVAILABLE:
            try:
                with get_database_session() as session:
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
                st.error(f"データベース接続エラー: {e}")
        else:
            st.warning("⚠️ データベースに接続できません")
    
    with col2:
        st.markdown("### 🚀 クイズを開始")
        if st.button("🎲 ランダムクイズ", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.session_state.user_answer = None
            # 回答済み問題リストをクリア（新しいクイズセッション開始）
            st.session_state.answered_questions.clear()
            st.session_state.page = "🎲 クイズ"  # ページを直接切り替え
            st.rerun()

elif page == "🎲 クイズ":
    st.subheader("🎲 クイズモード")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、クイズ機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
            user_answer_service = UserAnswerService(session)            # 新しい問題を取得
            if st.session_state.current_question is None:
                # 既に回答した問題を除外して取得
                max_attempts = 10
                attempt = 0
                question = None
                
                while attempt < max_attempts:
                    questions = question_service.get_random_questions(limit=5)  # 複数取得して選択
                    if questions:
                        # 未回答の問題を探す
                        for q in questions:
                            if q.id not in st.session_state.answered_questions:
                                question = q
                                break
                        
                        if question:
                            break
                        else:
                            # 全ての問題が回答済みの場合、リセット
                            if len(st.session_state.answered_questions) > 0:
                                st.session_state.answered_questions.clear()
                                st.info("🔄 全ての問題を回答しました。問題をリセットします。")
                                question = questions[0]  # 最初の問題を選択
                                break
                    attempt += 1
                
                if question:
                    st.session_state.current_question = question
                    st.session_state.user_answer = None
                    st.session_state.show_result = False
                    st.session_state.start_time = time.time()
                    st.session_state.quiz_choice_key += 1  # ラジオボタンのキーを更新
                else:
                    st.error("問題が見つかりません。")
                    st.stop()
            
            question = st.session_state.current_question
            
            # 進捗表示
            if len(st.session_state.answered_questions) > 0:
                st.info(f"📊 このセッションで回答済み: {len(st.session_state.answered_questions)}問")
            
            # 問題表示
            st.markdown(f"### {get_difficulty_emoji(question.difficulty)} {question.title}")
            st.markdown(f"**カテゴリ:** {question.category}")
            st.markdown(f"**問題:** {question.content}")
              # 選択肢を取得
            choices = choice_service.get_choices_by_question(question.id)
            
            if not st.session_state.show_result:
                # 回答フェーズ
                st.markdown("---")
                st.markdown("**選択肢を選んでください:**")
                
                choice_labels = [f"{chr(65+i)}. {choice.content}" for i, choice in enumerate(choices)]
                
                selected_idx = st.radio(
                    "回答を選択:",
                    range(len(choices)),
                    format_func=lambda x: choice_labels[x],
                    key=f"quiz_choice_{st.session_state.quiz_choice_key}"
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔍 回答する", use_container_width=True):
                        # 回答時間を計算
                        answer_time = time.time() - st.session_state.start_time
                        
                        selected_choice = choices[selected_idx]
                        is_correct = selected_choice.is_correct
                        
                        # 回答を記録
                        user_answer_service.record_answer(
                            question_id=question.id,
                            selected_choice_id=selected_choice.id,
                            is_correct=is_correct,
                            answer_time=answer_time,
                            session_id=st.session_state.session_id
                        )
                        
                        # 回答済み問題に追加
                        st.session_state.answered_questions.add(question.id)
                        
                        st.session_state.user_answer = {
                            'selected_choice': selected_choice,
                            'is_correct': is_correct,
                            'answer_time': answer_time
                        }
                        st.session_state.show_result = True
                        st.rerun()
                
                with col2:
                    if st.button("⏭️ スキップ", use_container_width=True):
                        # スキップした問題も回答済みとしてマーク（無限ループ防止）
                        st.session_state.answered_questions.add(question.id)
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.rerun()
            
            else:
                # 結果表示フェーズ
                st.markdown("---")
                user_answer = st.session_state.user_answer
                
                if user_answer['is_correct']:
                    st.success("🎉 正解です！")
                else:
                    st.error("❌ 不正解です")
                    # 正解を表示
                    correct_choice = next(c for c in choices if c.is_correct)
                    st.info(f"**正解:** {correct_choice.content}")
                
                # 解説表示
                if question.explanation:
                    st.markdown(f"**💡 解説:** {question.explanation}")
                
                # 回答時間表示                st.markdown(f"**⏱️ 回答時間:** {user_answer['answer_time']:.1f}秒")
                
                # 次の問題ボタン
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("➡️ 次の問題", use_container_width=True):
                        # 次の問題への移行
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.session_state.user_answer = None
                        st.rerun()
                
                with col2:
                    if st.button("🏠 ホームに戻る", use_container_width=True):
                        st.session_state.current_question = None
                        st.session_state.show_result = False
                        st.session_state.page = "🏠 ホーム"  # ページを直接切り替え
                        st.rerun()
    
    except Exception as e:
        st.error(f"クイズ機能でエラーが発生しました: {e}")

elif page == "📊 統計":
    st.subheader("📊 学習統計")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、統計機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            user_answer_service = UserAnswerService(session)
            
            # 全体統計
            all_stats = user_answer_service.get_user_stats()
            session_stats = user_answer_service.get_user_stats(st.session_state.session_id)
            
            st.markdown("### 📈 統計サマリー")
            
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
            
            if session_stats['total'] > 0:
                st.markdown("### 🎯 進捗")
                progress = session_stats['accuracy'] / 100
                st.progress(progress)
                st.markdown(f"現在の正答率: **{session_stats['accuracy']}%**")
    
    except Exception as e:
        st.error(f"統計機能でエラーが発生しました: {e}")

elif page == "🔧 問題管理":
    st.subheader("🔧 問題管理")
    
    if not DATABASE_AVAILABLE:
        st.error("⚠️ データベースに接続できないため、問題管理機能は利用できません。")
        st.stop()
    
    try:
        with get_database_session() as session:
            question_service = QuestionService(session)
            choice_service = ChoiceService(session)
              # タブで機能を分割
            tab1, tab2, tab3, tab4 = st.tabs(["📝 問題一覧", "🤖 AI問題生成", "📄 PDF問題生成", "📊 生成統計"])
            
            with tab1:
                st.markdown("### 📝 問題一覧・管理")
                
                # フィルター
                col1, col2, col3 = st.columns(3)
                
                # 全問題を取得してカテゴリリストを作成
                all_questions = question_service.get_random_questions(limit=1000) 
                categories = sorted(list(set(q.category for q in all_questions)))
                difficulties = ["all", "easy", "medium", "hard"]
                
                with col1:
                    selected_category = st.selectbox(
                        "カテゴリでフィルター",
                        ["all"] + categories,
                        format_func=lambda x: "すべて" if x == "all" else x
                    )
                
                with col2:
                    selected_difficulty = st.selectbox(
                        "難易度でフィルター", 
                        difficulties,
                        format_func=lambda x: {
                            "all": "すべて",
                            "easy": "初級",
                            "medium": "中級", 
                            "hard": "上級"
                        }[x]
                    )
                
                with col3:
                    per_page = st.selectbox("表示件数", [10, 20, 50, 100], index=1)
                
                # フィルター適用
                filtered_questions = all_questions
                if selected_category != "all":
                    filtered_questions = [q for q in filtered_questions if q.category == selected_category]
                if selected_difficulty != "all":
                    filtered_questions = [q for q in filtered_questions if q.difficulty == selected_difficulty]
                
                st.markdown(f"**表示中: {len(filtered_questions)}問 / 全体: {len(all_questions)}問**")
                
                # ページネーション
                total_pages = (len(filtered_questions) + per_page - 1) // per_page
                if total_pages > 1:
                    page_num = st.number_input("ページ", min_value=1, max_value=total_pages, value=1) - 1
                else:
                    page_num = 0
                
                start_idx = page_num * per_page
                end_idx = min(start_idx + per_page, len(filtered_questions))
                current_questions = filtered_questions[start_idx:end_idx]
                
                # 問題表示
                for i, question in enumerate(current_questions):
                    with st.expander(f"**{question.title}** ({question.category} / {question.difficulty})"):
                        st.markdown(f"**問題ID:** {question.id}")
                        st.markdown(f"**内容:** {question.content}")
                        
                        # 選択肢表示
                        choices = choice_service.get_choices_by_question(question.id)
                        st.markdown("**選択肢:**")
                        for j, choice in enumerate(choices):
                            correct_mark = " ✅" if choice.is_correct else ""
                            st.markdown(f"{chr(65+j)}. {choice.content}{correct_mark}")
                        
                        if question.explanation:
                            st.markdown(f"**解説:** {question.explanation}")
                          # 編集・削除ボタン
                        col1, col2, col3 = st.columns([1, 1, 3])
                        with col1:
                            if st.button(f"✏️ 編集", key=f"edit_{question.id}"):
                                st.session_state.edit_question_id = question.id
                                st.info("編集機能は今後実装予定です")
                        
                        with col2:
                            if st.button(f"🗑️ 削除", key=f"delete_{question.id}"):
                                if st.session_state.get(f"confirm_delete_{question.id}", False):
                                    # 実際に削除
                                    if question_service.delete_question(question.id):
                                        st.success(f"問題 ID {question.id} を削除しました")
                                        st.session_state[f"confirm_delete_{question.id}"] = False
                                        st.rerun()
                                    else:
                                        st.error("削除に失敗しました")
                                else:
                                    st.session_state[f"confirm_delete_{question.id}"] = True
                                    st.warning("もう一度クリックして削除を確認してください")
            
            with tab2:
                st.markdown("### 🤖 AI問題生成")
                
                # 改良された生成UI
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**生成パラメータ**")
                    
                    # 生成パラメータ
                    gen_col1, gen_col2 = st.columns(2)
                    
                    with gen_col1:
                        category = st.selectbox(
                            "カテゴリ",
                            ["基本情報技術者", "応用情報技術者", "プログラミング基礎", "データベース", 
                             "ネットワーク", "セキュリティ", "AI・機械学習", "プロジェクトマネジメント"],
                            key="gen_category_tab"
                        )
                    
                    with gen_col2:
                        difficulty = st.selectbox(
                            "難易度",
                            ["easy", "medium", "hard"],
                            format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                            key="gen_difficulty_tab"
                        )
                    
                    count = st.slider("生成数", 1, 10, 1, key="gen_count_tab")
                    
                    topic = st.text_area(
                        "特定のトピック（任意）",
                        placeholder="例:\n• オブジェクト指向プログラミング\n• データベース正規化\n• ネットワークセキュリティ",
                        height=100,
                        key="gen_topic_tab"
                    )
                    
                    # 詳細オプション
                    with st.expander("🔧 詳細オプション"):
                        include_explanation = st.checkbox("解説を含める", value=True)
                        question_length = st.selectbox(
                            "問題文の長さ",
                            ["short", "medium", "long"],
                            format_func=lambda x: {"short": "短い", "medium": "標準", "long": "詳細"}[x]
                        )
                
                with col2:
                    st.markdown("**生成履歴**")
                    if st.session_state.generation_history:
                        for entry in st.session_state.generation_history[-5:]:  # 最新5件
                            st.text(f"{entry['time']}: {entry['count']}問生成")
                    else:
                        st.text("履歴なし")
                  # 生成実行
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("🎲 問題を生成", use_container_width=True, type="primary"):
                        # プログレス表示用のコンテナ
                        progress_container = st.empty()
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            generator = QuestionGenerator(session)
                              # OpenAI接続確認
                            connection_status = generator.validate_openai_connection()
                            if not connection_status["connected"]:
                                error_message = connection_status['message']
                                
                                # クォータ超過エラーの場合、詳細な説明を追加
                                if "quota" in error_message.lower() or "insufficient_quota" in error_message.lower():
                                    st.error("❌ **OpenAI APIクォータ超過エラー**")
                                    st.markdown("""
                                    🔧 **解決方法:**
                                    1. **[OpenAI Platform](https://platform.openai.com)**にログイン
                                    2. **Billing**セクションで使用量とクレジット残高を確認
                                    3. 必要に応じてクレジットを追加購入
                                    4. または、無料クォータがリセットされるまで待機
                                    
                                    💡 **代替案:** 手動で問題を作成することも可能です（問題管理ページから）
                                    """)
                                else:
                                    st.error(f"❌ OpenAI接続エラー: {error_message}")
                                    st.info("💡 **ヒント:** OpenAI APIキーが正しく設定されているか確認してください")
                                st.stop()
                            
                            generated_ids = []
                            
                            # プログレスコールバック関数
                            def update_progress(message, progress):
                                status_text.text(message)
                                progress_bar.progress(progress)
                            
                            if count == 1:
                                # 単一問題生成
                                question_id = generator.generate_and_save_question(
                                    category=category,
                                    difficulty=difficulty,
                                    topic=topic if topic else None,
                                    progress_callback=update_progress
                                )
                                
                                if question_id:
                                    generated_ids.append(question_id)
                            else:
                                # 複数問題生成
                                topics_list = [t.strip() for t in topic.split('\n') if t.strip()] if topic else None
                                
                                generated_ids = generator.generate_and_save_multiple_questions(
                                    category=category,
                                    difficulty=difficulty,
                                    count=count,
                                    topics=topics_list,
                                    progress_callback=update_progress,
                                    delay_between_requests=1.5  # Rate limiting
                                )
                            
                            # 結果表示
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            
                            if generated_ids:
                                st.success(f"✅ {len(generated_ids)}問の問題を生成しました！")
                                
                                # 生成履歴に追加
                                st.session_state.generation_history.append({
                                    'time': datetime.now().strftime('%H:%M'),
                                    'count': len(generated_ids),
                                    'category': category,
                                    'difficulty': difficulty
                                })
                                  # 生成された問題のIDを表示
                                with st.expander("📋 生成された問題の詳細"):
                                    for i, qid in enumerate(generated_ids):
                                        st.markdown(f"### 問題 {i+1} (ID: {qid})")
                                        
                                        # 生成された問題の詳細を表示
                                        question = question_service.get_question_by_id(qid)
                                        if question:
                                            st.markdown(f"**タイトル:** {question.title}")
                                            st.markdown(f"**カテゴリ:** {question.category}")
                                            st.markdown(f"**問題:** {question.content}")
                                            if question.explanation:
                                                st.markdown(f"**解説:** {question.explanation}")
                                            st.markdown("---")
                            else:
                                st.error("❌ 問題生成に失敗しました。OpenAI APIの制限またはネットワークエラーの可能性があります。")
                        
                        except Exception as e:
                            progress_container.empty()
                            progress_bar.empty()
                            status_text.empty()
                            st.error(f"❌ エラーが発生しました: {e}")
                            st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか、PDFが読み取り可能か確認してください。")
                        
                with col2:
                    if st.button("🔄 フォームリセット"):
                        st.rerun()
            
            with tab3:
                st.markdown("### 📄 PDF問題生成")
                
                # PDFアップロードと問題生成
                try:
                    pdf_processor = PDFProcessor()
                    
                    if DATABASE_AVAILABLE:
                        pdf_generator = PDFQuestionGenerator(session)
                        past_extractor = PastQuestionExtractor(session)
                    else:
                        st.warning("⚠️ データベース接続エラーのため、問題の保存ができません。テキスト抽出のみ可能です。")
                    
                    st.markdown("""
                    **PDF教材から問題を処理**
                    
                    📚 2つのモードから選択できます：
                    - **問題生成モード**: 教材内容からAIが新しい問題を生成
                    - **過去問抽出モード**: 既存の問題・正解・解説をそのまま抽出
                    
                    🔒 **プライバシー保護**
                    - アップロードされたPDFの内容はOpenAIの学習データとして使用されません
                    - `X-OpenAI-Skip-Training: true`ヘッダーを設定して学習を無効化しています
                    - 処理完了後、PDF内容はメモリから削除されます
                    """)
                    
                    # プライバシー保護についての詳細情報
                    with st.expander("🔒 プライバシー保護の詳細"):
                        st.markdown("""
                        **データ保護対策:**
                        
                        1. **学習データ除外**: 
                           - OpenAI APIに`X-OpenAI-Skip-Training: true`ヘッダーを送信
                           - アップロードされたPDFの内容が学習データとして使用されません
                        
                        2. **一時的な処理**: 
                           - PDFの内容は問題生成/抽出のためのみに使用
                           - 処理完了後、メモリから自動的に削除
                        
                        3. **ローカル処理**: 
                           - PDFの読み込みと前処理はローカルで実行
                           - 必要最小限のテキストのみをAPIに送信
                        
                        4. **データベース保存**: 
                           - 生成/抽出された問題のみをデータベースに保存
                           - 元のPDF内容は保存されません
                        
                        ⚠️ **注意**: 著作権のあるPDFは個人学習目的でのみご利用ください。
                        """)
                    
                    
                    # 処理モード選択
                    processing_mode = st.radio(
                        "処理モードを選択",
                        ["🤖 問題生成モード", "📝 過去問抽出モード"],
                        help="問題生成：AIが新しい問題を作成 / 過去問抽出：既存の問題をそのまま利用"
                    )
                    
                    # ファイルアップロード
                    uploaded_file = st.file_uploader(
                        "PDFファイルを選択してください",
                        type=['pdf'],
                        help="最大50MBまでのPDFファイルをアップロードできます（Railway Hobby Plan対応）",
                        key="pdf_uploader"
                    )
                    
                    if uploaded_file is not None:
                        # ファイル検証
                        is_valid, message = pdf_processor.validate_file(uploaded_file)
                        
                        if not is_valid:
                            st.error(f"❌ {message}")
                            st.stop()
                        
                        # ファイル情報表示
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("ファイル名", uploaded_file.name)
                        with col2:
                            st.metric("ファイルサイズ", f"{uploaded_file.size / 1024:.1f} KB")
                        with col3:
                            st.metric("ファイル形式", "PDF")
                        
                        # 生成パラメータ
                        st.markdown("---")
                        
                        if processing_mode == "🤖 問題生成モード":
                            st.markdown("**🤖 問題生成設定**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                pdf_num_questions = st.slider("生成問題数", 1, 30, 10, key="pdf_num_questions")
                            
                            with col2:
                                pdf_difficulty = st.selectbox(
                                    "難易度",
                                    ["easy", "medium", "hard"],
                                    format_func=lambda x: {"easy": "初級", "medium": "中級", "hard": "上級"}[x],
                                    key="pdf_difficulty"
                                )
                            
                            with col3:
                                pdf_category = st.text_input("カテゴリ名", "PDF教材", key="pdf_category")
                            

                            # テキスト抽出オプション
                            with st.expander("🔧 詳細設定"):
                                extraction_method = st.selectbox(
                                    "テキスト抽出方法",
                                    ["auto", "pypdf2", "pdfplumber"],
                                    format_func=lambda x: {
                                        "auto": "自動選択（推奨）",
                                        "pypdf2": "PyPDF2（高速）",
                                        "pdfplumber": "PDFplumber（高精度）"
                                    }[x],
                                    help="自動選択では両方の方法を試して最適な結果を選択します"
                                )
                                
                                include_explanation = st.checkbox("解説を含める", value=True, key="pdf_explanation")
                                
                                preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=False)
                                # 問題生成実行
                            st.markdown("---")
                            button_label = "🎯 PDFから問題を生成"
                            
                            # プライバシー保護の確認（問題生成モード）
                            privacy_confirmed_gen = st.checkbox(
                                "🔒 プライバシー保護設定を理解し、PDFの処理に同意します",
                                help="アップロードされたPDFの内容はOpenAIの学習データとして使用されません。処理完了後、内容はメモリから削除されます。",
                                key="privacy_confirmation_gen"
                            )
                            
                        else:  # 過去問抽出モード
                            st.markdown("**📝 過去問抽出設定**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                pdf_category = st.text_input("カテゴリ名", "過去問", key="past_category")
                            
                            with col2:
                                extraction_method = st.selectbox(
                                    "テキスト抽出方法",
                                    ["auto", "pypdf2", "pdfplumber"],
                                    format_func=lambda x: {
                                        "auto": "自動選択（推奨）",
                                        "pypdf2": "PyPDF2（高速）",
                                        "pdfplumber": "PDFplumber（高精度）"
                                    }[x],
                                    key="past_extraction_method"
                                )
                            
                            with st.expander("🔧 過去問抽出の詳細設定"):
                                st.markdown("""
                                **📋 過去問抽出について:**
                                - 問題文、選択肢、正解、解説をそのまま抽出
                                - 元の内容を一切改変しません
                                - 問題番号で自動分割を試行
                                - 抽出精度を向上させるため低温度設定を使用
                                """)
                                
                                preview_text = st.checkbox("テキスト抽出結果をプレビュー", value=True, key="past_preview")
                                
                                strict_extraction = st.checkbox(
                                    "厳密抽出モード", 
                                    value=True, 
                                    help="より正確な抽出のため、温度設定を最低にします"
                                )
                                # 過去問抽出実行
                            st.markdown("---")
                            button_label = "📝 PDFから過去問を抽出"
                          # プライバシー保護の確認チェック
                        if processing_mode == "🤖 問題生成モード":
                            privacy_confirmed = st.session_state.get("privacy_confirmation_gen", False)
                        else:
                            privacy_confirmed = st.session_state.get("privacy_confirmation", False)
                        
                        if st.button(button_label, type="primary", use_container_width=True, disabled=not privacy_confirmed):
                            
                            if not privacy_confirmed:
                                st.warning("⚠️ プライバシー保護設定への同意が必要です。")
                                st.stop()
                            
                            # プログレス表示
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            try:
                                # PDFテキスト抽出
                                status_text.text("PDFからテキストを抽出中...")
                                progress_bar.progress(0.1)
                                
                                file_bytes = uploaded_file.read()
                                
                                if extraction_method == "auto":
                                    extracted_text = pdf_processor.extract_text_auto(file_bytes)
                                elif extraction_method == "pypdf2":
                                    extracted_text = pdf_processor.extract_text_pypdf2(file_bytes)
                                else:
                                    extracted_text = pdf_processor.extract_text_pdfplumber(file_bytes)
                                
                                if not extracted_text or len(extracted_text.strip()) < 50:
                                    st.error("❌ PDFからテキストを抽出できませんでした。ファイルが画像ベースのPDFまたは保護されている可能性があります。")
                                    st.stop()
                                
                                # テキストプレビュー
                                if preview_text:
                                    st.markdown("### 📖 抽出テキストプレビュー")
                                    with st.expander("抽出されたテキスト（最初の1000文字）"):
                                        st.text(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
                                
                                # テキスト統計
                                word_count = len(extracted_text.split())
                                char_count = len(extracted_text)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("抽出文字数", f"{char_count:,}")
                                with col2:
                                    st.metric("推定単語数", f"{word_count:,}")
                                
                                # プログレスコールバック関数
                                def pdf_progress_callback(message, progress):
                                    status_text.text(message)
                                    progress_bar.progress(min(progress, 0.95))
                                
                                if processing_mode == "🤖 問題生成モード":
                                    # 問題生成モード
                                    status_text.text("問題を生成中...")
                                    progress_bar.progress(0.3)
                                    
                                    generated_ids = pdf_generator.generate_questions_from_pdf(
                                        text=extracted_text,
                                        num_questions=pdf_num_questions,
                                        difficulty=pdf_difficulty,
                                        category=pdf_category,
                                        progress_callback=pdf_progress_callback
                                    )
                                    
                                    mode_text = "生成"
                                    
                                else:  # 過去問抽出モード
                                    # 過去問抽出モード
                                    status_text.text("過去問を抽出中...")
                                    progress_bar.progress(0.3)
                                    
                                    generated_ids = past_extractor.extract_past_questions_from_pdf(
                                        text=extracted_text,
                                        category=pdf_category,
                                        progress_callback=pdf_progress_callback
                                    )
                                    
                                    mode_text = "抽出"
                                
                                # 完了
                                progress_bar.progress(1.0)
                                status_text.text(f"問題{mode_text}完了！")
                                
                                if generated_ids:
                                    st.success(f"✅ {len(generated_ids)}問の問題を{mode_text}しました！")
                                    
                                    # 生成履歴に追加
                                    st.session_state.generation_history.append({
                                        'time': datetime.now().strftime('%H:%M'),
                                        'count': len(generated_ids),
                                        'category': pdf_category,
                                        'difficulty': pdf_difficulty if processing_mode == "🤖 問題生成モード" else "mixed",
                                        'source': f'PDF: {uploaded_file.name}',
                                        'mode': mode_text
                                    })
                                    
                                    # 生成された問題の詳細表示
                                    with st.expander(f"📋 {mode_text}された問題の詳細"):
                                        for i, qid in enumerate(generated_ids):
                                            st.markdown(f"### 問題 {i+1} (ID: {qid})")
                                            
                                            question = question_service.get_question_by_id(qid)
                                            if question:
                                                st.markdown(f"**タイトル:** {question.title}")
                                                st.markdown(f"**カテゴリ:** {question.category}")
                                                st.markdown(f"**問題:** {question.content}")
                                                
                                                # 選択肢表示
                                                choices = choice_service.get_choices_by_question(qid)
                                                st.markdown("**選択肢:**")
                                                for j, choice in enumerate(choices):
                                                    correct_mark = " ✅" if choice.is_correct else ""
                                                    st.markdown(f"{chr(65+j)}. {choice.content}{correct_mark}")
                                                
                                                if question.explanation:
                                                    st.markdown(f"**解説:** {question.explanation}")
                                                st.markdown("---")
                                    
                                    # クイズ開始ボタン
                                    st.markdown(f"### 🎲 {mode_text}した問題でクイズを開始")
                                    if st.button("🚀 クイズを開始", use_container_width=True):
                                        st.session_state.current_question = None
                                        st.session_state.show_result = False
                                        st.session_state.user_answer = None
                                        st.session_state.answered_questions.clear()
                                        st.session_state.page = "🎲 クイズ"
                                        st.rerun()
                                        
                                else:
                                    st.error(f"❌ 問題{mode_text}に失敗しました。")
                                    
                                    # 詳細なエラー診断情報を表示
                                    with st.expander("🔍 エラー診断情報"):
                                        st.markdown("**考えられる原因:**")
                                        st.markdown("1. **OpenAI APIキー**: APIキーが設定されていないか無効")
                                        st.markdown("2. **API制限**: 使用量制限またはレート制限に達している")
                                        st.markdown("3. **PDF内容**: テキストが正しく抽出されていない")
                                        st.markdown("4. **ネットワーク**: インターネット接続に問題がある")
                                        
                                        # APIキーの状態確認
                                        import os
                                        api_key = os.getenv("OPENAI_API_KEY")
                                        if api_key:
                                            st.success(f"✅ OpenAI APIキー: 設定済み ({api_key[:10]}...)")
                                        else:
                                            st.error("❌ OpenAI APIキー: 未設定")
                                            st.code("環境変数OPENAI_API_KEYを設定してください")
                                        
                                        # 抽出されたテキストの長さを確認
                                        st.info(f"📊 抽出されたテキスト長: {len(extracted_text)} 文字")
                                        if len(extracted_text) < 100:
                                            st.warning("⚠️ 抽出されたテキストが短すぎる可能性があります")
                                
                            except Exception as e:
                                progress_bar.empty()
                                status_text.empty()
                                st.error(f"❌ エラーが発生しました: {str(e)}")
                                
                                # 詳細なエラー情報を表示
                                with st.expander("🔍 詳細なエラー情報"):
                                    import traceback
                                    st.code(traceback.format_exc())
                                    
                                st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか、PDFが読み取り可能か確認してください。")
                        
                        else:
                            st.info("📎 PDFファイルをアップロードして問題生成を開始してください")
                            
                            # 使用例の表示
                        with st.expander("💡 使用方法とヒント"):
                            st.markdown("""
                            **🤖 問題生成モード:**
                            
                            📚 **適切なPDF:**
                            - テキストベースのPDF（画像スキャンではない）
                            - 明確な章立てや見出しがある
                            - 専門用語や概念の説明が含まれている
                            
                            🎯 **問題生成のコツ:**
                            - 5-15問程度が最適な生成数
                            - カテゴリ名を具体的に設定する
                            - 教材の難易度に合わせて設定する
                            
                            ---
                            
                            **📝 過去問抽出モード:**
                            
                            📄 **適切なPDF:**
                            - 過去問集や問題集のPDF
                            - 問題・選択肢・正解・解説が明記されたもの
                            - 問題番号で区切られた構造
                            
                            🎯 **抽出のコツ:**
                            - 厳密抽出モードを有効にする
                            - テキストプレビューで構造を確認
                            - 問題形式が統一されたPDFを使用
                            - 抽出後は必ず内容を確認
                            
                            ---
                              ⚠️ **共通注意事項:**
                            - 著作権に注意してください
                            - 個人学習目的での利用を推奨します
                            - 生成・抽出された問題は必ず内容を確認してください                            - 過去問は原文のまま利用されます
                            """)
                
                except Exception as e:
                    st.error(f"❌ PDF機能でエラーが発生しました: {e}")
                    st.info("💡 必要なライブラリがインストールされているか確認してください。")
            
            with tab4:
                st.markdown("### 📊 生成統計")
                
                try:
                    generator = QuestionGenerator(session)
                    stats = generator.get_generation_stats()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("総問題数", stats["total_questions"])
                        
                        st.markdown("**カテゴリ別問題数**")
                        if stats["categories"]:
                            for cat, count in sorted(stats["categories"].items()):
                                st.text(f"• {cat}: {count}問")
                    
                    with col2:
                        st.markdown("**難易度別問題数**")
                        if stats["difficulties"]:
                            difficulty_labels = {"easy": "初級", "medium": "中級", "hard": "上級"}
                            for diff, count in sorted(stats["difficulties"].items()):
                                label = difficulty_labels.get(diff, diff)
                                st.text(f"• {label}: {count}問")
                        
                        # 生成トレンド（セッション内）
                        if st.session_state.generation_history:
                            st.markdown("**本日の生成履歴**")
                            total_generated = sum(entry['count'] for entry in st.session_state.generation_history)
                            st.metric("本セッション生成数", total_generated)
                
                except Exception as e:
                    st.error(f"統計取得エラー: {e}")
    
    except Exception as e:
        st.error(f"問題管理機能でエラーが発生しました: {e}")

elif page == "⚙️ 設定":
    st.subheader("⚙️ 設定")
    
    st.markdown("### 🔧 アプリケーション設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**セッション管理**")
        st.text(f"現在のセッションID: {st.session_state.session_id}")
        
        if st.button("🔄 新しいセッション開始"):
            st.session_state.session_id = generate_session_id()
            st.session_state.current_question = None
            st.session_state.show_result = False
            st.success("新しいセッションを開始しました！")
            st.rerun()
    
    with col2:
        st.markdown("**データベース情報**")
        if DATABASE_AVAILABLE:
            try:
                with get_database_session() as session:
                    question_service = QuestionService(session)
                    questions = question_service.get_random_questions(limit=1000)
                    st.text(f"総問題数: {len(questions)}")
                    
                    # カテゴリ別統計
                    categories = {}
                    for q in questions:
                        categories[q.category] = categories.get(q.category, 0) + 1
                    
                    st.markdown("**カテゴリ別問題数:**")
                    for category, count in categories.items():
                        st.text(f"• {category}: {count}問")
            
            except Exception as e:
                st.error(f"データベース情報の取得に失敗: {e}")
        else:
            st.error("データベースに接続できません")

    # データベース初期化セクション
    st.markdown("---")
    st.markdown("### 🗄️ データベース管理")
    
    if DATABASE_AVAILABLE:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**データベース初期化**")
            if st.button("📝 サンプルデータ作成", help="データベースが空の場合にサンプル問題を作成します"):
                try:
                    with get_database_session() as session:
                        question_service = QuestionService(session)
                        choice_service = ChoiceService(session)
                        
                        # 既存の問題数をチェック
                        existing_questions = question_service.get_random_questions(limit=1000)
                        
                        if len(existing_questions) > 0:
                            st.warning(f"⚠️ 既に{len(existing_questions)}問の問題が存在します。")
                            if st.button("🔄 強制的にサンプルデータを追加"):
                                create_sample = True
                            else:
                                create_sample = False
                        else:
                            create_sample = True
                        
                        if create_sample:
                            with st.spinner("サンプルデータを作成中..."):
                                # サンプル問題1
                                q1 = question_service.create_question(
                                    title="プログラミング基礎 - 変数",
                                    content="Pythonで変数xに数値10を代入する正しい記述はどれですか？",
                                    category="プログラミング基礎",
                                    explanation="Pythonでは「変数名 = 値」の形式で代入を行います。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q1.id, "x = 10", True, 1)
                                choice_service.create_choice(q1.id, "x == 10", False, 2)
                                choice_service.create_choice(q1.id, "x := 10", False, 3)
                                choice_service.create_choice(q1.id, "10 = x", False, 4)
                                
                                # サンプル問題2
                                q2 = question_service.create_question(
                                    title="基本情報技術者 - データベース",
                                    content="関係データベースにおいて、テーブル間の関連を定義するために使用されるものはどれですか？",
                                    category="基本情報技術者",
                                    explanation="外部キーは、他のテーブルの主キーを参照して、テーブル間の関連を定義します。",
                                    difficulty="medium"
                                )
                                
                                choice_service.create_choice(q2.id, "主キー", False, 1)
                                choice_service.create_choice(q2.id, "外部キー", True, 2)
                                choice_service.create_choice(q2.id, "インデックス", False, 3)
                                choice_service.create_choice(q2.id, "ビュー", False, 4)
                                
                                # サンプル問題3
                                q3 = question_service.create_question(
                                    title="ネットワーク - TCP/IP",
                                    content="インターネットで使用される基本的なプロトコルスイートは何ですか？",
                                    category="ネットワーク",
                                    explanation="TCP/IPは、インターネットで使用される基本的なプロトコルスイートです。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q3.id, "HTTP", False, 1)
                                choice_service.create_choice(q3.id, "FTP", False, 2)
                                choice_service.create_choice(q3.id, "TCP/IP", True, 3)
                                choice_service.create_choice(q3.id, "SMTP", False, 4)
                                
                                # サンプル問題4
                                q4 = question_service.create_question(
                                    title="セキュリティ - 暗号化",
                                    content="公開鍵暗号方式において、データの暗号化に使用されるキーはどれですか？",
                                    category="セキュリティ",
                                    explanation="公開鍵暗号方式では、公開鍵で暗号化し、秘密鍵で復号化します。",
                                    difficulty="hard"
                                )
                                
                                choice_service.create_choice(q4.id, "秘密鍵", False, 1)
                                choice_service.create_choice(q4.id, "公開鍵", True, 2)
                                choice_service.create_choice(q4.id, "共通鍵", False, 3)
                                choice_service.create_choice(q4.id, "ハッシュ値", False, 4)
                                
                                # サンプル問題5
                                q5 = question_service.create_question(
                                    title="データベース - SQL",
                                    content="SQLにおいて、テーブルからデータを検索するために使用するコマンドはどれですか？",
                                    category="データベース",
                                    explanation="SELECT文は、データベースからデータを検索・取得するためのSQL文です。",
                                    difficulty="easy"
                                )
                                
                                choice_service.create_choice(q5.id, "INSERT", False, 1)
                                choice_service.create_choice(q5.id, "UPDATE", False, 2)
                                choice_service.create_choice(q5.id, "SELECT", True, 3)
                                choice_service.create_choice(q5.id, "DELETE", False, 4)
                                
                            st.success("✅ サンプルデータを5問作成しました！")
                            st.info("🎲 クイズページでテストしてみてください。")
                            
                except Exception as e:
                    st.error(f"❌ サンプルデータ作成に失敗: {e}")
        
        with col2:
            st.markdown("**データベース状態**")
            try:
                with get_database_session() as session:
                    question_service = QuestionService(session)
                    questions = question_service.get_random_questions(limit=1000)
                    
                    if len(questions) == 0:
                        st.warning("⚠️ データベースに問題がありません")
                        st.info("👈 左側の「サンプルデータ作成」ボタンでテスト用の問題を作成してください")
                    else:
                        st.success(f"✅ {len(questions)}問の問題が利用可能")
                        
                        # 最新の問題を表示
                        st.markdown("**最新の問題:**")
                        for i, q in enumerate(questions[-3:]):
                            st.text(f"• {q.title}")
                            
            except Exception as e:
                st.error(f"データベース状態確認エラー: {e}")
    else:
        st.error("⚠️ データベースに接続できません")

# フッター
st.markdown("---")
st.markdown("**Study Quiz App** - powered by Streamlit & Railway 🚀")
