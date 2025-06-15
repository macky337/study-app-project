# -*- coding: utf-8 -*-
import os
from sqlmodel import create_engine, Session, SQLModel
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
        # PostgreSQL connection with proper encoding
        engine = create_engine(
            DATABASE_URL, 
            echo=False,  # Set to False in production
            pool_pre_ping=True,
            connect_args={"client_encoding": "utf8"}
        )
        print("✅ Database engine created successfully")
    except Exception as e:
        print(f"❌ Failed to create database engine: {e}")
        engine = None


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


def create_tables():
    """Create database tables"""
    from models import Question, Choice, UserAnswer
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully!")


def init_database():
    """Initialize database"""
    try:
        create_tables()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
