from typing import Optional
from sqlmodel import SQLModel, Field


class Choice(SQLModel, table=True):
    """選択肢テーブル"""
    __tablename__ = "choice"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    content: str  # 選択肢の内容
    is_correct: bool = Field(default=False)  # 正解フラグ
    order_num: int = Field(default=1)  # 表示順序
    
    class Config:
        from_attributes = True
