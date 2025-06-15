# -*- coding: utf-8 -*-
import os
from sqlmodel import create_engine, Session, SQLModel, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL with multiple fallbacks
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PUBLIC_URL") or 
    os.getenv("POSTGRES_URL") or
    os.getenv("DATABASE_PRIVATE_URL")
)

print(f"🔍 Environment variables check:")
print(f"   DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'}")
print(f"   DATABASE_PUBLIC_URL: {'✅ Set' if os.getenv('DATABASE_PUBLIC_URL') else '❌ Not set'}")
print(f"   POSTGRES_URL: {'✅ Set' if os.getenv('POSTGRES_URL') else '❌ Not set'}")

if not DATABASE_URL:
    # Show all available environment variables for debugging
    available_vars = [var for var in os.environ.keys() if 'DATABASE' in var.upper() or 'POSTGRES' in var.upper()]
    print(f"   Database-related env vars: {available_vars}")
    
    # Temporary fallback - create a mock engine for development
    print("⚠️  WARNING: No database URL found. Creating mock connection.")
    print("   Please configure DATABASE_URL in Railway Variables.")    
    # Don't raise error immediately - let the app start and show a user-friendly message
    DATABASE_URL = None
    engine = None
else:
    try:
        # PostgreSQL connection with proper encoding and SSL settings
        connect_args = {
            "client_encoding": "utf8",
            "sslmode": "require"  # Railway requires SSL
        }
        
        engine = create_engine(
            DATABASE_URL, 
            echo=False,  # Set to False in production
            pool_pre_ping=True,
            connect_args=connect_args        )
          # Test the connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            
            # Create tables using direct SQL to avoid SQLModel conflicts
            try:
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
                print("✅ Database tables ensured to exist")
            except Exception as table_error:
                print(f"⚠️ Table creation warning: {table_error}")
                # Continue anyway - tables might already exist
        
        print("✅ Database engine created and connection tested successfully")
    except Exception as e:
        print(f"❌ Failed to create database engine: {e}")
        print(f"   Database URL format: {'postgresql://...' if DATABASE_URL and 'postgresql://' in DATABASE_URL else 'Invalid or missing'}")
        engine = None


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


def create_tables():
    """Create database tables"""
    try:
        # Clear any existing metadata to avoid conflicts
        SQLModel.metadata.clear()
        
        # Import models to register them with SQLModel
        from models.question import Question
        from models.choice import Choice
        from models.user_answer import UserAnswer
        
        # Create tables only if they don't exist
        SQLModel.metadata.create_all(engine, checkfirst=True)
        print("✅ Database tables created successfully!")
        return True
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
