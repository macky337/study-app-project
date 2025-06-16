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
    
    def get_random_questions_by_category(self, category: str, limit: int = 10) -> List[Question]:
        """指定したカテゴリからランダムに問題を取得"""
        statement = select(Question).where(Question.category == category).order_by(func.random()).limit(limit)
        return self.session.exec(statement).all()
    
    def get_all_categories(self) -> List[str]:
        """データベースに存在するすべてのカテゴリを取得"""
        statement = select(Question.category).distinct()
        categories = self.session.exec(statement).all()
        return sorted([cat for cat in categories if cat])  # Noneを除外してソート
    
    def get_category_stats(self) -> dict:
        """カテゴリごとの問題数を取得"""
        statement = select(Question.category, func.count(Question.id)).group_by(Question.category)
        results = self.session.exec(statement).all()
        return {category: count for category, count in results if category}
    
    def find_duplicate_questions(self, similarity_threshold: float = 0.8) -> List[List[Question]]:
        """重複する可能性のある問題を検出"""
        from difflib import SequenceMatcher
        
        all_questions = self.session.exec(select(Question)).all()
        duplicates = []
        processed_ids = set()
        
        for i, question1 in enumerate(all_questions):
            if question1.id in processed_ids:
                continue
                
            similar_questions = [question1]
            
            for j, question2 in enumerate(all_questions[i+1:], i+1):
                if question2.id in processed_ids:
                    continue
                
                # タイトルの類似度をチェック
                title_similarity = SequenceMatcher(None, question1.title.lower(), question2.title.lower()).ratio()
                
                # 内容の類似度をチェック
                content_similarity = SequenceMatcher(None, question1.content.lower(), question2.content.lower()).ratio()
                
                # 同じカテゴリで、タイトルまたは内容が類似している場合
                if (question1.category == question2.category and 
                    (title_similarity >= similarity_threshold or content_similarity >= similarity_threshold)):
                    similar_questions.append(question2)
                    processed_ids.add(question2.id)
            
            if len(similar_questions) > 1:
                duplicates.append(similar_questions)
                for q in similar_questions:
                    processed_ids.add(q.id)
        
        return duplicates
    
    def find_exact_duplicate_questions(self) -> List[List[Question]]:
        """完全に重複する問題を検出（タイトルと内容が完全一致）"""
        statement = select(Question).order_by(Question.title, Question.content)
        all_questions = self.session.exec(statement).all()
        
        duplicates = []
        current_group = []
        
        for i, question in enumerate(all_questions):
            if i == 0:
                current_group = [question]
            else:
                prev_question = all_questions[i-1]
                # タイトルと内容が完全一致する場合
                if (question.title.strip().lower() == prev_question.title.strip().lower() and
                    question.content.strip().lower() == prev_question.content.strip().lower()):
                    if len(current_group) == 1 and current_group[0].id != prev_question.id:
                        current_group = [prev_question, question]
                    elif current_group[-1].id != prev_question.id:
                        current_group.append(prev_question)
                    current_group.append(question)
                else:
                    if len(current_group) > 1:
                        duplicates.append(current_group)
                    current_group = [question]
        
        # 最後のグループもチェック
        if len(current_group) > 1:
            duplicates.append(current_group)
        
        return duplicates
    
    def delete_question(self, question_id: int) -> bool:
        """問題を削除（関連する選択肢・回答も削除）"""
        try:
            # 問題を取得
            question = self.session.get(Question, question_id)
            if not question:
                return False
            
            # 関連する選択肢を削除
            choice_service = ChoiceService(self.session)
            choices = choice_service.get_choices_by_question(question_id)
            for choice in choices:
                choice_service.delete_choice(choice.id)
            
            # 関連するユーザー回答を削除
            user_answer_service = UserAnswerService(self.session)
            user_answers = user_answer_service.get_answers_by_question(question_id)
            for answer in user_answers:
                user_answer_service.delete_answer(answer.id)
            
            # 問題を削除
            self.session.delete(question)
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"問題削除エラー: {e}")
            self.session.rollback()
            return False
    
    def delete_multiple_questions(self, question_ids: List[int]) -> dict:
        """複数の問題を一括削除"""
        deleted_count = 0
        failed_ids = []
        
        for question_id in question_ids:
            if self.delete_question(question_id):
                deleted_count += 1
            else:
                failed_ids.append(question_id)
        
        return {
            "deleted_count": deleted_count,
            "failed_ids": failed_ids,
            "total_requested": len(question_ids)
        }
    
    def check_duplicate_before_creation(
        self, 
        title: str, 
        content: str, 
        category: str,
        similarity_threshold: float = 0.8
    ) -> dict:
        """
        新規問題作成前の重複チェック
        
        Returns:
            dict: {
                "is_duplicate": bool,
                "similar_questions": List[Question],
                "highest_similarity": float,
                "recommendation": str
            }
        """
        from difflib import SequenceMatcher
        
        # 同一カテゴリの既存問題を取得
        existing_questions = self.get_questions_by_category(category)
        
        if not existing_questions:
            return {
                "is_duplicate": False,
                "similar_questions": [],
                "highest_similarity": 0.0,
                "recommendation": "新規作成OK（同カテゴリの問題なし）"
            }
        
        similar_questions = []
        highest_similarity = 0.0
        
        title_lower = title.strip().lower()
        content_lower = content.strip().lower()
        
        for existing_q in existing_questions:
            existing_title_lower = existing_q.title.strip().lower()
            existing_content_lower = existing_q.content.strip().lower()
            
            # タイトルの類似度
            title_similarity = SequenceMatcher(None, title_lower, existing_title_lower).ratio()
            
            # 内容の類似度
            content_similarity = SequenceMatcher(None, content_lower, existing_content_lower).ratio()
            
            # より高い類似度を採用
            max_similarity = max(title_similarity, content_similarity)
            
            if max_similarity > highest_similarity:
                highest_similarity = max_similarity
            
            # 閾値を超える場合は類似問題として記録
            if max_similarity >= similarity_threshold:
                similar_questions.append({
                    "question": existing_q,
                    "title_similarity": title_similarity,
                    "content_similarity": content_similarity,
                    "max_similarity": max_similarity
                })
        
        # 完全重複チェック（より厳密）
        is_exact_duplicate = any(
            title_lower == q.title.strip().lower() and content_lower == q.content.strip().lower()
            for q in existing_questions
        )
        
        # 推奨アクション決定
        if is_exact_duplicate:
            recommendation = "❌ 完全重複 - 作成を中止することを強く推奨"
        elif highest_similarity >= 0.9:
            recommendation = "⚠️ 高類似度 - 内容を確認して調整を推奨"
        elif highest_similarity >= similarity_threshold:
            recommendation = "💡 類似問題あり - 差別化を検討"
        else:
            recommendation = "✅ 新規作成OK"
        
        return {
            "is_duplicate": is_exact_duplicate or highest_similarity >= 0.9,
            "similar_questions": similar_questions,
            "highest_similarity": highest_similarity,
            "recommendation": recommendation
        }
    
    def create_question_with_duplicate_check(
        self,
        title: str,
        content: str,
        category: str,
        explanation: Optional[str] = None,
        difficulty: str = "medium",
        force_create: bool = False,
        similarity_threshold: float = 0.8
    ) -> dict:
        """
        重複チェック付きの問題作成
        
        Returns:
            dict: {
                "success": bool,
                "question": Question or None,
                "duplicate_check": dict,
                "message": str
            }
        """
        # 重複チェック実行
        duplicate_check = self.check_duplicate_before_creation(
            title, content, category, similarity_threshold
        )
        
        # 強制作成フラグがない場合、重複度が高いと作成拒否
        if not force_create and duplicate_check["is_duplicate"]:
            return {
                "success": False,
                "question": None,
                "duplicate_check": duplicate_check,
                "message": f"重複問題検出: {duplicate_check['recommendation']}"
            }
        
        # 問題作成実行
        try:
            question = self.create_question(
                title=title,
                content=content,
                category=category,
                explanation=explanation,
                difficulty=difficulty
            )
            
            message = "✅ 問題を正常に作成しました"
            if duplicate_check["highest_similarity"] > 0.5:
                message += f" (類似度: {duplicate_check['highest_similarity']:.2f})"
            
            return {
                "success": True,
                "question": question,
                "duplicate_check": duplicate_check,
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "question": None,
                "duplicate_check": duplicate_check,
                "message": f"作成エラー: {e}"
            }
        

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
    
    def get_choices_by_question_id(self, question_id: int) -> List[Choice]:
        """問題IDで選択肢を取得（エイリアス）"""
        return self.get_choices_by_question(question_id)
    
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
    
    def get_answers_by_question(self, question_id: int) -> List[UserAnswer]:
        """指定した問題のユーザー回答を取得"""
        statement = select(UserAnswer).where(UserAnswer.question_id == question_id)
        return self.session.exec(statement).all()
    
    def delete_answer(self, answer_id: int) -> bool:
        """ユーザー回答を削除"""
        try:
            answer = self.session.get(UserAnswer, answer_id)
            if answer:
                self.session.delete(answer)
                self.session.commit()
                return True
            return False
        except Exception as e:
            print(f"回答削除エラー: {e}")
            self.session.rollback()
            return False
