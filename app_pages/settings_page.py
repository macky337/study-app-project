"""
設定ページ - アプリケーション設定とデータベース管理
"""
import streamlit as st
from config.app_config import generate_session_id

def render_settings_page():
    """設定ページのメイン表示"""
    st.title("⚙️ 設定")
    
    # リアルタイムでデータベース接続をチェック
    from config.app_config import check_database_connection
    db_available, db_error = check_database_connection()
    
    # セッション管理
    render_session_management()
    
    # データベース情報
    render_database_info(db_available, db_error)
    
    # データベース管理
    if db_available:
        render_database_management()
    else:
        render_demo_settings()

def render_session_management():
    """セッション管理セクション"""
    st.markdown("### 🔧 セッション管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**現在のセッション情報**")
        if hasattr(st.session_state, 'session_id'):
            st.text(f"セッションID: {st.session_state.session_id}")
        else:
            st.text("セッションID: 未設定")
          # セッション状態の表示
        if hasattr(st.session_state, 'answered_questions'):
            st.text(f"回答済み問題数: {len(st.session_state.answered_questions)}")
        
        if hasattr(st.session_state, 'current_question'):
            current_q = st.session_state.current_question
            if current_q:
                # 辞書か SQLModel オブジェクトかを確認して安全に表示
                if isinstance(current_q, dict):
                    title = current_q.get('title', 'タイトル不明')
                else:
                    # SQLModel オブジェクトの場合は辞書に変換してからアクセス
                    try:
                        from database.connection import model_to_dict
                        current_q_dict = model_to_dict(current_q)
                        # セッション状態を辞書に更新
                        st.session_state.current_question = current_q_dict
                        title = current_q_dict.get('title', 'タイトル不明')
                    except Exception as e:
                        title = 'タイトル不明（セッションエラー）'
                        # エラーが発生した場合は current_question をクリア
                        st.session_state.current_question = None
                st.text(f"現在の問題: {title[:20]}...")
            else:
                st.text("現在の問題: なし")
    
    with col2:
        st.markdown("**セッション操作**")
        if st.button("🔄 新しいセッション開始", key="new_session"):
            # セッション状態をリセット
            st.session_state.session_id = generate_session_id()
            
            # 学習関連の状態をリセット
            reset_keys = [
                'current_question', 'show_result', 'user_answer',
                'answered_questions', 'quiz_choice_key', 'start_time'
            ]
            
            for key in reset_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("新しいセッションを開始しました！")
            st.rerun()
        
        if st.button("🗑️ セッションデータクリア", key="clear_session"):
            # セッション状態を完全にクリア
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("セッションデータをクリアしました！")
            st.rerun()

def render_database_info(db_available: bool, db_error: str = None):
    """データベース情報セクション"""
    st.markdown("---")
    st.markdown("### 🗄️ データベース情報")
    
    if not db_available:
        st.error("❌ データベースに接続できません")
        st.markdown("""
        **データベース接続エラーの原因:**
        - データベースサーバーが起動していない
        - 接続設定（URL、ユーザー名、パスワード）が間違っている
        - ネットワーク接続の問題        """)
        
        if db_error:
            with st.expander("🔍 詳細エラー情報"):
                st.error(db_error)
        return
    
    try:
        from database.operations import QuestionService, UserAnswerService
        from database.connection import get_session_context, models_to_dicts
        
        # セッション内でデータを取得し、すぐに辞書に変換
        with get_session_context() as session:
            question_service = QuestionService(session)
            user_answer_service = UserAnswerService(session)
            
            # 基本統計情報を取得し、辞書に変換
            questions_models = question_service.get_random_questions(limit=1000)
            questions = models_to_dicts(questions_models)
            
            # 回答統計を取得
            try:
                all_stats = user_answer_service.get_user_stats()
                total_answers = all_stats.get('total', 0)
            except:
                total_answers = 0
        
        # セッション終了後に辞書データを使用
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総問題数", len(questions))
        
        with col2:
            categories = len(set(q['category'] for q in questions))
            st.metric("カテゴリ数", categories)
        
        with col3:
            st.metric("総回答数", total_answers)
        
        # カテゴリ別統計
        if questions:
            st.markdown("### 📚 カテゴリ別問題数")
            
            categories = {}
            difficulties = {}
            
            for q in questions:
                categories[q['category']] = categories.get(q['category'], 0) + 1
                difficulties[q['difficulty']] = difficulties.get(q['difficulty'], 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**カテゴリ別:**")
                for category, count in sorted(categories.items()):
                    st.markdown(f"• {category}: {count}問")
            
            with col2:
                st.markdown("**難易度別:**")
                for difficulty, count in sorted(difficulties.items()):
                    difficulty_name = {
                        "easy": "初級",
                        "medium": "中級",
                        "hard": "上級"
                    }.get(difficulty, difficulty)
                    st.markdown(f"• {difficulty_name}: {count}問")
            
    except Exception as e:
        st.error(f"データベース情報の取得に失敗しました: {e}")

def render_database_management():
    """データベース管理セクション"""
    st.markdown("---")
    st.markdown("### 🛠️ データベース管理")
    
    # リアルタイムでデータベース接続をチェック
    from config.app_config import check_database_connection
    db_available, db_error = check_database_connection()
    
    if not db_available:
        st.warning("データベースが利用できないため、管理機能は使用できません。")
        return
    
    try:
        from database.operations import QuestionService, ChoiceService
        from database.connection import get_session_context, models_to_dicts
        
        col1, col2 = st.columns(2)
        
        with col1:
            render_sample_data_creation()
        
        with col2:
            render_database_status()
                
    except Exception as e:
        st.error(f"データベース管理機能でエラーが発生しました: {e}")

def render_sample_data_creation():
    """サンプルデータ作成"""
    st.markdown("**📝 サンプルデータ作成**")
    
    try:
        from database.operations import QuestionService
        from database.connection import get_session_context
        
        # 既存の問題数をチェック
        with get_session_context() as session:
            question_service = QuestionService(session)
            existing_questions = question_service.get_random_questions(limit=1000)
            existing_count = len(existing_questions)
        
        if existing_count > 0:
            st.info(f"現在 {existing_count}問の問題が存在します")
            
            if st.button("🔄 サンプルデータを追加", key="add_sample_data"):
                create_sample_data()
        else:
            st.warning("データベースに問題がありません")
            if st.button("📝 サンプルデータを作成", key="create_sample_data"):
                create_sample_data()
    except Exception as e:
        st.error(f"サンプルデータ作成でエラー: {e}")

def create_sample_data():
    """サンプルデータの実際の作成"""
    try:
        from database.operations import QuestionService, ChoiceService
        from database.connection import get_session_context
        
        with st.spinner("サンプルデータを作成中..."):
            sample_questions = [
                {
                    "title": "プログラミング基礎 - 変数",
                    "content": "Pythonで変数xに数値10を代入する正しい記述はどれですか？",
                    "category": "プログラミング基礎",
                    "explanation": "Pythonでは「変数名 = 値」の形式で代入を行います。",
                    "difficulty": "easy",
                    "choices": [
                        ("x = 10", True),
                        ("x == 10", False),
                        ("x := 10", False),
                        ("10 = x", False)
                    ]
                },
                {
                    "title": "基本情報技術者 - データベース",
                    "content": "関係データベースにおいて、テーブル間の関連を定義するために使用されるものはどれですか？",
                    "category": "基本情報技術者",
                    "explanation": "外部キーは、他のテーブルの主キーを参照して、テーブル間の関連を定義します。",
                    "difficulty": "medium",
                    "choices": [
                        ("主キー", False),
                        ("外部キー", True),
                        ("インデックス", False),
                        ("ビュー", False)
                    ]
                },
                {
                    "title": "ネットワーク - TCP/IP",
                    "content": "インターネットで使用される基本的なプロトコルスイートは何ですか？",
                    "category": "ネットワーク",
                    "explanation": "TCP/IPは、インターネットで使用される基本的なプロトコルスイートです。",
                    "difficulty": "easy",
                    "choices": [
                        ("HTTP", False),
                        ("FTP", False),
                        ("TCP/IP", True),
                        ("SMTP", False)
                    ]
                },
                {
                    "title": "セキュリティ - 暗号化",
                    "content": "公開鍵暗号方式において、データの暗号化に使用されるキーはどれですか？",
                    "category": "セキュリティ",
                    "explanation": "公開鍵暗号方式では、公開鍵で暗号化し、秘密鍵で復号化します。",
                    "difficulty": "hard",
                    "choices": [
                        ("秘密鍵", False),
                        ("公開鍵", True),
                        ("共通鍵", False),
                        ("ハッシュ値", False)
                    ]
                },
                {
                    "title": "データベース - SQL",
                    "content": "SQLにおいて、テーブルからデータを検索するために使用するコマンドはどれですか？",
                    "category": "データベース",
                    "explanation": "SELECT文は、データベースからデータを検索・取得するためのSQL文です。",
                    "difficulty": "easy",
                    "choices": [
                        ("INSERT", False),
                        ("UPDATE", False),
                        ("SELECT", True),
                        ("DELETE", False)
                    ]
                }
            ]
            
            created_count = 0
            
            with get_session_context() as session:
                question_service = QuestionService(session)
                choice_service = ChoiceService(session)
                
                for q_data in sample_questions:
                    # 問題を作成
                    question = question_service.create_question(
                        title=q_data["title"],
                        content=q_data["content"],
                        category=q_data["category"],
                        explanation=q_data["explanation"],
                        difficulty=q_data["difficulty"]
                    )
                    
                    # 選択肢を作成
                    for i, (choice_content, is_correct) in enumerate(q_data["choices"]):
                        choice_service.create_choice(
                            question_id=question.id,
                            content=choice_content,
                            is_correct=is_correct,
                            order_num=i + 1
                        )
                    
                    created_count += 1
            
            st.success(f"✅ {created_count}問のサンプルデータを作成しました！")
            st.info("🎲 学習ページでテストしてみてください。")
            
    except Exception as e:
        st.error(f"❌ サンプルデータ作成に失敗しました: {e}")

def render_database_status():
    """データベース状態表示"""
    st.markdown("**🔍 データベース状態**")
    
    try:
        from database.operations import QuestionService
        from database.connection import get_session_context, models_to_dicts
        
        # セッション内でデータを取得し、すぐに辞書に変換
        with get_session_context() as session:
            question_service = QuestionService(session)
            questions_models = question_service.get_random_questions(limit=1000)
            questions = models_to_dicts(questions_models)
        
        # セッション終了後に辞書データを使用
        if len(questions) == 0:
            st.warning("⚠️ データベースに問題がありません")
            st.info("左側の「サンプルデータ作成」ボタンでテスト用の問題を作成してください")
        else:
            st.success(f"✅ {len(questions)}問の問題が利用可能")
            
            # 最新の問題を表示
            st.markdown("**最新の問題:**")
            recent_questions = sorted(questions, key=lambda x: x['id'], reverse=True)[:3]
            
            for q in recent_questions:
                st.markdown(f"• {q['title']} ({q['category']})")
    
    except Exception as e:
        st.error(f"データベース状態確認エラー: {e}")

def render_demo_settings():
    """デモモード用の設定表示"""
    st.info("🔄 デモモードで設定を表示しています。")
    
    st.markdown("### 🔧 アプリケーション情報")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**現在の状態:**")
        st.text("モード: デモモード")
        st.text("データベース: 未接続")
        st.text("セッション: アクティブ")
    
    with col2:
        st.markdown("**統計情報:**")
        st.text("利用可能問題: デモ用問題")
        st.text("カテゴリ: 基本情報技術者など")
        st.text("難易度: 初級〜上級")
    
    if st.button("🔄 デモリセット", key="demo_reset"):
        st.success("デモ状態をリセットしました！")
        st.rerun()
