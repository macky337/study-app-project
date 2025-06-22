from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.question import Question


class Choice(SQLModel, table=True):
    """選択肢テーブル"""
    __tablename__ = "choice"
    
    id: Optional[int] = Field(primary_key=True)
    question_id: int = Field(foreign_key="question.id")
    content: str  # 選択肢の内容
    is_correct: bool = Field(default=False)  # 正解フラグ
    order_num: int = Field(default=1)  # 表示順序    # リレーション - 文字列参照で重複回避
    question: Optional["Question"] = Relationship(back_populates="choices")
    
    class Config:
        from_attributes = True
