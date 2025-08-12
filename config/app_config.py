"""
アプリケーション設定ファイル
"""
import streamlit as st
import logging
import os

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# グローバル変数
_models_loaded = False

def is_railway_environment():
    """Railway環境で実行されているかを判定"""
    return 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_PROJECT_ID' in os.environ

def is_production_environment():
    """本番環境で実行されているかを判定"""
    return is_railway_environment() or os.environ.get('STREAMLIT_ENV') == 'production'

def get_server_config():
    """環境に応じたサーバー設定を取得"""
    if is_railway_environment():
        return {
            'port': int(os.environ.get('PORT', 8080)),
            'address': '0.0.0.0',
            'headless': True,
            'cors': True
        }
    else:
        return {
            'port': 8501,
            'address': 'localhost',
            'headless': False,
            'cors': False
        }

# アプリケーションのページリスト
PAGES = [
    "🏠 ホーム",
    "🎲 学習",
    "📊 統計", 
    "🔧 問題管理",
    "🎤 音声・議事録",
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

class ModelRegistry:
    """シングルトンパターンでモデルの重複登録を防ぐ"""
    _instance = None
    _models_loaded = False
    _registry_cleared = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def ensure_models_loaded(self):
        """モデルを一度だけ読み込む（完全な重複定義回避）"""
        if self._models_loaded:
            print("✅ Models already loaded, skipping...")
            return True
            
        try:
            from sqlmodel import SQLModel
            
            # 一度だけメタデータをクリア
            if not self._registry_cleared:
                SQLModel.metadata.clear()
                self._registry_cleared = True
                print("🔄 SQLModel metadata cleared (singleton)")
            
            # モデルを直接インポート（確実に登録）
            from models.question import Question
            from models.choice import Choice  
            from models.user_answer import UserAnswer
            
            # 手動でメタデータに強制登録
            Question.metadata = SQLModel.metadata
            Choice.metadata = SQLModel.metadata
            UserAnswer.metadata = SQLModel.metadata
            
            # 登録確認
            table_names = [table.name for table in SQLModel.metadata.tables.values()]
            expected_tables = ['question', 'choice', 'user_answer']
            
            all_registered = True
            for table_name in expected_tables:
                if table_name not in table_names:
                    print(f"⚠️ Table '{table_name}' not found in metadata")
                    all_registered = False
                else:
                    print(f"✅ Table '{table_name}' registered successfully")
            
            if all_registered:
                self._models_loaded = True
                print("✅ All models loaded and verified successfully (singleton)")
                return True
            else:
                # テーブルが見つからない場合も続行（SQLではテーブル作成される）
                self._models_loaded = True
                print("⚠️ Some tables not in metadata, but proceeding with SQL table creation")
                return True
                
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            return False

# シングルトンインスタンスを作成
_model_registry = ModelRegistry()

def ensure_models_loaded():
    """グローバル関数でモデル読み込みを呼び出し"""
    return _model_registry.ensure_models_loaded()

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
