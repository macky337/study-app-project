"""
アプリケーション設定ファイル
"""
import streamlit as st
import logging

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# アプリケーションのページリスト
PAGES = [
    "🏠 ホーム",
    "🎲 クイズ",
    "📊 統計", 
    "🔧 問題管理",
    "⚙️ 設定"
]

# ページ設定
def configure_page():
    st.set_page_config(
        page_title="Study Quiz App",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def hide_streamlit_navigation():
    """Streamlitのマルチページナビゲーションを非表示にする"""
    hide_streamlit_style = """
    <style>
    /* Streamlitのマルチページナビゲーションを完全に非表示 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* サイドバーの不要なナビゲーション要素を非表示 */
    .css-1d391kg {
        display: none !important;
    }
    
    /* ページリンク全体を非表示 */
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* ナビゲーションリストを非表示 */
    ul[data-testid="stSidebarNavItems"] {
        display: none !important;
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# データベース接続変数
DATABASE_AVAILABLE = False
DATABASE_ERROR = None
_db_initialized = False  # 初期化フラグ
_models_loaded = False  # モデル読み込みフラグ

def ensure_models_loaded():
    """モデルを一度だけ読み込む（重複定義を回避）"""
    global _models_loaded
    if not _models_loaded:
        try:
            # 既存のモデルインポートをチェック
            import sys
            
            # モデルが既にインポート済みの場合はスキップ
            if ('models.question' in sys.modules and 
                'models.choice' in sys.modules and 
                'models.user_answer' in sys.modules):
                print("✅ Models already loaded, skipping reload")
                _models_loaded = True
                return
            
            # モデルを直接インポート（クリア処理なし）
            try:
                from models.question import Question
                print("✅ Question model imported")
            except Exception as e:
                print(f"❌ Question model import failed: {e}")
                raise
                
            try:
                from models.choice import Choice  
                print("✅ Choice model imported")
            except Exception as e:
                print(f"❌ Choice model import failed: {e}")
                raise
                
            try:
                from models.user_answer import UserAnswer
                print("✅ UserAnswer model imported")
            except Exception as e:
                print(f"❌ UserAnswer model import failed: {e}")
                raise
            
            _models_loaded = True
            print("✅ Models loaded successfully")
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            _models_loaded = False
            raise

def check_database_connection():
    """リアルタイムでデータベース接続状態をチェック"""
    try:
        from database.connection import engine
        if engine is not None:
            with engine.connect() as conn:
                from sqlmodel import text
                conn.execute(text("SELECT 1"))
            return True, None
        else:
            return False, "Database engine is None"
    except Exception as e:
        return False, str(e)

# Mock functions for demo mode
def generate_session_id():
    return "demo_session"

def format_accuracy(correct, total):
    if total == 0:
        return "0%"
    return f"{(correct/total)*100:.1f}%"

def get_difficulty_emoji(difficulty):
    emoji_map = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
    return emoji_map.get(difficulty, "🟡")

# セッション状態の初期化
def initialize_session_state():
    """セッション状態を初期化"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = generate_session_id()
    
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False
    
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = None
    
    if 'quiz_choice_key' not in st.session_state:
        st.session_state.quiz_choice_key = 0
    
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = "すべて"
    
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 ホーム"

# データベース接続処理
def initialize_database():
    """データベース接続を初期化（高速化版）"""
    global DATABASE_AVAILABLE, DATABASE_ERROR, _db_initialized
    
    # 既に初期化済みの場合はスキップ
    if _db_initialized:
        return DATABASE_AVAILABLE, DATABASE_ERROR
    
    try:
        from database.connection import engine, ensure_tables_with_sqlmodel
        
        if engine is not None:
            DATABASE_AVAILABLE = True
            DATABASE_ERROR = None
            print("✅ Database connection ready")
            
            # テーブルを確実に作成
            ensure_tables_with_sqlmodel()
        else:
            raise Exception("Database engine is None")
            
    except Exception as e:
        DATABASE_ERROR = f"Database connection error: {str(e)}"
        DATABASE_AVAILABLE = False
        print(f"❌ Database error: {e}")
    
    _db_initialized = True
    return DATABASE_AVAILABLE, DATABASE_ERROR
