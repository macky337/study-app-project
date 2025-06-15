from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class Choice(SQLModel, table=True):
    """選択肢テーブル"""
    id: Optional[int] = Field(primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    content: str  # 選択肢の内容
    is_correct: bool = Field(default=False)  # 正解フラグ
    order_num: int = Field(default=1)  # 表示順序
    
    # リレーション
    question: Optional["Question"] = Relationship(back_populates="choices")
    
    class Config:
        from_attributes = True
