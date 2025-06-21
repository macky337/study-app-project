from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship


class Question(SQLModel, table=True, extend_existing=True):
    """問題テーブル"""
    id: Optional[int] = Field(primary_key=True)
    title: str = Field(index=True)  # 問題のタイトル
    content: str  # 問題文
    explanation: Optional[str] = None  # 解説
    category: str = Field(index=True)  # カテゴリ（例：基本情報、応用情報）
    difficulty: str = Field(default="medium")  # 難易度：easy, medium, hard
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    # リレーション
    choices: List["Choice"] = Relationship(back_populates="question")
    user_answers: List["UserAnswer"] = Relationship(back_populates="question")
    
    class Config:
        from_attributes = True
