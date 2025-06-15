from typing import List, Optional
from sqlmodel import Session, select, func
from models import Question, Choice, UserAnswer


class QuestionService:
    """問題関連の操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_question(
        self, 
        title: str, 
        content: str, 
        category: str,
        explanation: Optional[str] = None,
        difficulty: str = "medium"
    ) -> Question:
        """新しい問題を作成"""
        question = Question(
            title=title,
            content=content,
            category=category,
            explanation=explanation,
            difficulty=difficulty
        )
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question
    
    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """IDで問題を取得"""
        return self.session.get(Question, question_id)
    
    def get_questions_by_category(self, category: str) -> List[Question]:
        """カテゴリで問題を取得"""
        statement = select(Question).where(Question.category == category)
        return self.session.exec(statement).all()
    
    def get_random_questions(self, limit: int = 10) -> List[Question]:
        """ランダムに問題を取得"""
        statement = select(Question).order_by(func.random()).limit(limit)
        return self.session.exec(statement).all()
    
    def update_question(
        self,
        question_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        explanation: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> Optional[Question]:
        """問題を更新"""
        question = self.get_question_by_id(question_id)
        if not question:
            return None
        
        if title is not None:
            question.title = title
        if content is not None:
            question.content = content
        if category is not None:
            question.category = category
        if explanation is not None:
            question.explanation = explanation
        if difficulty is not None:
            question.difficulty = difficulty
        
        self.session.commit()
        self.session.refresh(question)
        return question
    
    def delete_question(self, question_id: int) -> bool:
        """問題を削除（関連する選択肢と回答も削除）"""
        question = self.get_question_by_id(question_id)
        if not question:
            return False
        
        # 関連する選択肢を削除
        choices_statement = select(Choice).where(Choice.question_id == question_id)
        choices = self.session.exec(choices_statement).all()
        for choice in choices:
            self.session.delete(choice)
        
        # 関連するユーザー回答を削除
        answers_statement = select(UserAnswer).where(UserAnswer.question_id == question_id)
        answers = self.session.exec(answers_statement).all()
        for answer in answers:
            self.session.delete(answer)
        
        # 問題本体を削除
        self.session.delete(question)
        self.session.commit()
        return True


class ChoiceService:
    """選択肢関連の操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_choice(
        self, 
        question_id: int, 
        content: str, 
        is_correct: bool = False,
        order_num: int = 1
    ) -> Choice:
        """新しい選択肢を作成"""
        choice = Choice(
            question_id=question_id,
            content=content,
            is_correct=is_correct,
            order_num=order_num
        )
        self.session.add(choice)
        self.session.commit()
        self.session.refresh(choice)
        return choice
    
    def get_choices_by_question(self, question_id: int) -> List[Choice]:
        """問題IDで選択肢を取得"""
        statement = select(Choice).where(Choice.question_id == question_id).order_by(Choice.order_num)
        return self.session.exec(statement).all()
    
    def update_choice(
        self,
        choice_id: int,
        content: Optional[str] = None,
        is_correct: Optional[bool] = None,
        order_num: Optional[int] = None
    ) -> Optional[Choice]:
        """選択肢を更新"""
        choice = self.session.get(Choice, choice_id)
        if not choice:
            return None
        
        if content is not None:
            choice.content = content
        if is_correct is not None:
            choice.is_correct = is_correct
        if order_num is not None:
            choice.order_num = order_num
        
        self.session.commit()
        self.session.refresh(choice)
        return choice
    
    def delete_choice(self, choice_id: int) -> bool:
        """選択肢を削除"""
        choice = self.session.get(Choice, choice_id)
        if not choice:
            return False
        
        self.session.delete(choice)
        self.session.commit()
        return True


class UserAnswerService:
    """ユーザー回答関連の操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def record_answer(
        self, 
        question_id: int, 
        selected_choice_id: int, 
        is_correct: bool,
        answer_time: float = 0.0,
        session_id: Optional[str] = None
    ) -> UserAnswer:
        """回答を記録"""
        user_answer = UserAnswer(
            question_id=question_id,
            selected_choice_id=selected_choice_id,
            is_correct=is_correct,
            answer_time=answer_time,
            session_id=session_id
        )
        self.session.add(user_answer)
        self.session.commit()
        self.session.refresh(user_answer)
        return user_answer
    
    def get_user_stats(self, session_id: Optional[str] = None) -> dict:
        """ユーザーの統計を取得"""
        statement = select(UserAnswer)
        if session_id:
            statement = statement.where(UserAnswer.session_id == session_id)
        
        answers = self.session.exec(statement).all()
        
        if not answers:
            return {"total": 0, "correct": 0, "accuracy": 0.0}
        
        total = len(answers)
        correct = sum(1 for answer in answers if answer.is_correct)
        accuracy = (correct / total) * 100 if total > 0 else 0.0
        
        return {
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 2)
        }
