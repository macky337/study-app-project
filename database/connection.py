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
_models_imported = False

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
            
            # PostgreSQL connection with proper encoding and SSL settings
            connect_args = {
                "client_encoding": "utf8",
                "sslmode": "require"  # Railway requires SSL
            }
            
            engine = create_engine(
                DATABASE_URL, 
                echo=False,  # Set to False in production
                pool_pre_ping=True,
                connect_args=connect_args,
                pool_timeout=5,  # 5秒タイムアウト（高速化）
                pool_recycle=1800,  # 30分で接続をリサイクル
                pool_size=2,  # 小さなプールサイズで起動高速化
                max_overflow=3  # オーバーフロー制限
            )
            
            print("✅ Database engine created successfully")
            
            # 軽量な接続テスト
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                    print("✅ Database connection test successful")
            except Exception as test_error:
                print(f"⚠️ Database connection test failed: {test_error}")
                # 接続テストが失敗してもエンジンは作成済みなので続行
            
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
                            CREATE TABLE IF NOT EXISTS useranswer (
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
    """Create database tables"""
    global _models_imported
    
    try:
        # Import models to register them with SQLModel (only once)
        if not _models_imported:
            try:
                # Clear metadata to avoid duplicate definitions
                SQLModel.metadata.clear()
                
                from models.question import Question
                from models.choice import Choice  
                from models.user_answer import UserAnswer
                _models_imported = True
                print("📦 Models imported successfully")
            except ImportError as e:
                print(f"⚠️ Model import warning: {e}")
        
        # Create tables only if they don't exist
        if engine is not None:
            SQLModel.metadata.create_all(engine, checkfirst=True)
            print("✅ Database tables created successfully!")
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


def init_database():
    """Initialize database"""
    try:
        result = create_tables()
        return result
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
