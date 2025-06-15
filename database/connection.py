# -*- coding: utf-8 -*-
import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL with fallback and debugging
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"🔍 Environment variables check:")
print(f"   DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ Not set'}")

if not DATABASE_URL:
    # Try alternative environment variable names
    DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("POSTGRES_URL")
    if DATABASE_URL:
        print(f"   Found alternative URL: ✅")
    else:
        print(f"   Available env vars: {list(os.environ.keys())}")
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please check Railway Variables configuration."
        )

# Create engine
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
    raise


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
