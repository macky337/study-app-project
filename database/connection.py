# -*- coding: utf-8 -*-
import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
if DATABASE_URL:
    # PostgreSQL connection with proper encoding
    engine = create_engine(
        DATABASE_URL, 
        echo=True,
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"}
    )
else:
    raise ValueError("DATABASE_URL environment variable is not set")


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
