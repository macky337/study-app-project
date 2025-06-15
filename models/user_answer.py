from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class UserAnswer(SQLModel, table=True, extend_existing=True):
    """ユーザー回答履歴テーブル"""
    id: Optional[int] = Field(primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    selected_choice_id: int = Field(foreign_key="choice.id")
    is_correct: bool  # 正解・不正解
    answer_time: float = Field(default=0.0)  # 回答時間（秒）
    answered_at: datetime = Field(default_factory=datetime.now)
    
    # 学習セッション情報
    session_id: Optional[str] = None  # セッションID
    user_id: Optional[str] = None  # 将来のユーザー管理用
    
    # リレーション
    question: Optional["Question"] = Relationship(back_populates="user_answers")
    
    class Config:
        from_attributes = True
