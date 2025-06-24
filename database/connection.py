# -*- coding: utf-8 -*-
import os
from sqlmodel import create_engine, Session, SQLModel, text
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# グローバル変数でエンジンの初期化状態を管理
_engine_initialized = False
_initialization_lock = False

class DatabaseRegistry:
    """シングルトンパターンでデータベース初期化の重複を防ぐ"""
    _instance = None
    _models_imported = False
    _metadata_cleared = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def ensure_models_imported(self):
        """モデルを一度だけインポート（重複定義を完全回避）"""
        if self._models_imported:
            return True
            
        try:
            from sqlmodel import SQLModel
            
            # 一度だけメタデータをクリア
            if not self._metadata_cleared:
                SQLModel.metadata.clear()
                self._metadata_cleared = True
                print("🔄 SQLModel metadata cleared (database singleton)")
            
            # モデルをインポートしてSQLModelメタデータに登録
            from models.question import Question
            from models.choice import Choice  
            from models.user_answer import UserAnswer
            
            self._models_imported = True
            print("✅ Models imported successfully (database singleton)")
            return True
            
        except Exception as e:
            print(f"❌ Model import error: {e}")
            return False

# シングルトンインスタンスを作成
_db_registry = DatabaseRegistry()

# Database URL with multiple fallbacks
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PUBLIC_URL") or 
    os.getenv("POSTGRES_URL") or
    os.getenv("DATABASE_PRIVATE_URL")
)

# デバッグ情報の出力を簡素化（起動高速化）
if not DATABASE_URL:
    print("⚠️  WARNING: No database URL found. Running in demo mode.")
    DATABASE_URL = None
    engine = None
    _engine_initialized = True
else:
    if not _engine_initialized and not _initialization_lock:
        _initialization_lock = True
        try:
            print(f"🔗 Connecting to database...")
            
            # PostgreSQL connection settings - adjust for Docker environment
            connect_args = {
                "client_encoding": "utf8"
            }
            
            # Only require SSL for production/cloud databases
            if "railway" in DATABASE_URL.lower() or "amazonaws" in DATABASE_URL.lower():
                connect_args["sslmode"] = "require"
            else:
                # For local/Docker databases, don't require SSL
                connect_args["sslmode"] = "prefer"
            
            engine = create_engine(
                DATABASE_URL, 
                echo=False,  # Set to False in production
                pool_pre_ping=True,
                connect_args=connect_args,
                pool_timeout=10,  # 10秒タイムアウト（Docker用に延長）
                pool_recycle=1800,  # 30分で接続をリサイクル
                pool_size=2,  # 小さなプールサイズで起動高速化
                max_overflow=3  # オーバーフロー制限
            )
            
            print("✅ Database engine created successfully")
            
            # リトライ機能付きの接続テスト
            import time
            max_retries = 30  # 最大30回リトライ（60秒）
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    with engine.connect() as connection:
                        connection.execute(text("SELECT 1"))
                        print("✅ Database connection test successful")
                        break
                except Exception as test_error:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"❌ Database connection failed after {max_retries} retries: {test_error}")
                        # 接続失敗でもエンジンは保持（後でリトライ可能）
                        break
                    else:
                        print(f"⏳ Database connection attempt {retry_count}/{max_retries} failed, retrying in 2 seconds...")
                        time.sleep(2)
            
            # テーブル作成は別スレッドで実行（非ブロッキング）
            import threading
            def create_tables_async():
                try:
                    with engine.connect() as connection:
                        connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS question (
                                id SERIAL PRIMARY KEY,
                                title VARCHAR NOT NULL,
                                content TEXT NOT NULL,
                                explanation TEXT,
                                category VARCHAR NOT NULL,
                                difficulty VARCHAR DEFAULT 'medium',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP
                            );
                        """))
                        
                        connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS choice (
                                id SERIAL PRIMARY KEY,
                                question_id INTEGER REFERENCES question(id) ON DELETE CASCADE,
                                content TEXT NOT NULL,
                                is_correct BOOLEAN DEFAULT FALSE,
                                order_num INTEGER DEFAULT 1
                            );
                        """))
                        
                        connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS user_answer (
                                id SERIAL PRIMARY KEY,
                                question_id INTEGER REFERENCES question(id) ON DELETE CASCADE,
                                selected_choice_id INTEGER REFERENCES choice(id) ON DELETE CASCADE,
                                is_correct BOOLEAN NOT NULL,
                                answer_time FLOAT DEFAULT 0.0,
                                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                session_id VARCHAR,
                                user_id VARCHAR
                            );
                        """))
                        
                        connection.commit()
                        print("✅ Database tables ensured to exist (async)")
                except Exception as table_error:
                    print(f"⚠️ Table creation warning (async): {table_error}")
            
            # バックグラウンドでテーブル作成
            table_thread = threading.Thread(target=create_tables_async, daemon=True)
            table_thread.start()
            
            print("✅ Database engine created and connection tested successfully")
            _engine_initialized = True
        except Exception as e:
            print(f"❌ Failed to create database engine: {e}")
            print(f"   Database URL format: {'postgresql://...' if DATABASE_URL and 'postgresql://' in DATABASE_URL else 'Invalid or missing'}")
            engine = None
        finally:
            _initialization_lock = False
    elif _engine_initialized:
        # Engine already initialized, skip
        pass


def get_database_session():
    """安全なDBセッション生成（都度使い捨て）"""
    if engine is None:
        raise RuntimeError("DBエンジンが初期化されていません")
    return Session(engine)


@contextmanager
def get_session_context():
    """
    データベースセッションのコンテキストマネージャー
    使用例:
        with get_session_context() as session:
            # データベース操作
            result = session.query(Question).all()
    """
    if engine is None:
        raise RuntimeError("データベースエンジンが初期化されていません。DATABASE_URLを確認してください。")
    
    session = Session(engine)
    try:
        yield session
        session.commit()
        # セッション終了前にオブジェクトを確実にロード
        session.expunge_all()  # セッションからオブジェクトを切り離し
    except Exception as e:
        session.rollback()
        print(f"❌ Database session error: {e}")
        raise
    finally:
        session.close()


def model_to_dict(model):
    """SQLModelオブジェクトを辞書に変換してセッション依存を回避"""
    if model is None:
        return None
    
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        result[column.name] = value
    return result

def models_to_dicts(models):
    """SQLModelオブジェクトのリストを辞書のリストに変換"""
    return [model_to_dict(model) for model in models if model is not None]

def safe_database_operation(operation_func):
    """
    データベース操作を安全に実行するデコレータ
    """
    def wrapper(*args, **kwargs):
        try:
            with get_session_context() as session:
                return operation_func(session, *args, **kwargs)
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
            return None
    return wrapper


def create_tables():
    """Create database tables using singleton pattern"""
    
    try:
        # シングルトンでモデルインポートを管理
        if not _db_registry.ensure_models_imported():
            print("❌ Failed to import models")
            return False
        
        # Create tables only if they don't exist
        if engine is not None:
            from sqlmodel import SQLModel
            SQLModel.metadata.create_all(engine, checkfirst=True)
            print("✅ Tables created successfully with SQLModel.create_all")
            return True
        else:
            print("❌ Database engine is not available")
            return False
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        # Try alternative approach - direct table creation
        try:
            print("🔄 Attempting alternative table creation...")
            # This will skip if tables already exist
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS question (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        content TEXT NOT NULL,
                        explanation TEXT,
                        category VARCHAR NOT NULL,
                        difficulty VARCHAR DEFAULT 'medium',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    );
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS choice (
                        id SERIAL PRIMARY KEY,
                        question_id INTEGER REFERENCES question(id),
                        content TEXT NOT NULL,
                        is_correct BOOLEAN DEFAULT FALSE,
                        order_num INTEGER DEFAULT 1
                    );
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS useranswer (
                        id SERIAL PRIMARY KEY,
                        question_id INTEGER REFERENCES question(id),
                        selected_choice_id INTEGER REFERENCES choice(id),
                        is_correct BOOLEAN NOT NULL,
                        answer_time FLOAT DEFAULT 0.0,
                        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id VARCHAR,
                        user_id VARCHAR
                    );
                """))
                conn.commit()
            print("✅ Database tables created via SQL!")
            return True
        except Exception as sql_error:
            print(f"❌ Alternative table creation also failed: {sql_error}")
            return False


def ensure_tables_with_sqlmodel():
    """SQLModelを使ってテーブルを確実に作成（シングルトンパターン）"""
    if engine is None:
        print("❌ Cannot create tables: engine is None")
        return False
    try:
        # シングルトンでモデルインポートを管理
        if not _db_registry.ensure_models_imported():
            print("❌ Failed to import models for table creation")
            return False
        
        # SQLModelのcreate_allでテーブル作成
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
        print("✅ Tables created successfully with SQLModel.create_all (singleton)")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables with SQLModel: {e}")
        return False


def init_database():
    """Initialize database"""
    try:
        result = create_tables()
        return result
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
