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

# データベース接続変数
DATABASE_AVAILABLE = False
DATABASE_ERROR = None
_db_initialized = False  # 初期化フラグ
_models_loaded = False  # モデル読み込みフラグ

def ensure_models_loaded():
    """モデルを一度だけ読み込む"""
    global _models_loaded
    if not _models_loaded:
        try:
            # SQLModelのメタデータをクリア
            from sqlmodel import SQLModel
            SQLModel.metadata.clear()
            
            # モデルをインポート
            from models.question import Question
            from models.choice import Choice
            from models.user_answer import UserAnswer
            
            _models_loaded = True
            print("📦 Models loaded successfully")
        except Exception as e:
            print(f"⚠️ Model loading error: {e}")

def check_database_connection():
    """リアルタイムでデータベース接続状態をチェック"""
    try:
        # モデルが確実に読み込まれるように
        ensure_models_loaded()
        
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
    """データベース接続を初期化"""
    global DATABASE_AVAILABLE, DATABASE_ERROR, _db_initialized
      # 既に初期化済みの場合はスキップ
    if _db_initialized:
        return DATABASE_AVAILABLE, DATABASE_ERROR
    
    try:
        print("🔍 Initializing database connection...")
        
        # モデルを事前に読み込み
        ensure_models_loaded()
        
        from database.connection import engine, DATABASE_URL
        
        if engine is not None:
            print("✅ Database engine created successfully")
            
            # Test database connection with a simple query
            with engine.connect() as connection:
                from sqlmodel import text
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                print("✅ Database connection test successful")
            
            DATABASE_AVAILABLE = True
            DATABASE_ERROR = None
            print("✅ Database connection established successfully")
            
            # Try to import optional modules (don't fail if they don't exist)
            try:
                from database.operations import QuestionService, ChoiceService, UserAnswerService
                print("✅ Database operations imported successfully")
            except ImportError as import_err:
                print(f"⚠️ Optional database operations import failed: {import_err}")
                # Continue anyway - basic connection is working
            
            try:
                from utils.helpers import generate_session_id as real_generate_session_id, format_accuracy as real_format_accuracy, get_difficulty_emoji as real_get_difficulty_emoji
                # Override with real functions
                global generate_session_id, format_accuracy, get_difficulty_emoji
                generate_session_id = real_generate_session_id
                format_accuracy = real_format_accuracy
                get_difficulty_emoji = real_get_difficulty_emoji
                print("✅ Helper functions imported successfully")
            except ImportError as helper_err:
                print(f"⚠️ Helper functions import failed: {helper_err}")
                # Use mock functions - they're already defined above
            
        else:
            raise Exception("Database engine is None")
            
    except ImportError as e:
        DATABASE_ERROR = f"Module import error: {str(e)}"
        DATABASE_AVAILABLE = False
        print(f"❌ Import error: {e}")
        print("Running in demo mode without database functionality")
        
    except Exception as e:
        DATABASE_ERROR = f"Database connection error: {str(e)}"
        DATABASE_AVAILABLE = False
        print(f"❌ Database connection error: {e}")
        print("Running in demo mode without database functionality")
    
    _db_initialized = True
    return DATABASE_AVAILABLE, DATABASE_ERROR
