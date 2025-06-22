from typing import List, Optional
from sqlmodel import Session, select, func, delete
from datetime import datetime, timedelta
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
    ) -> Optional[Question]:
        """新しい問題を作成（例外時はエラー内容をprint）"""
        try:
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
        except Exception as e:
            print(f"❌ create_question DB保存エラー: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """IDで問題を取得"""
        question = self.session.get(Question, question_id)
        if question:
            # セッションから切り離される前に必要なデータをプリロード
            _ = question.id
            _ = question.title
            _ = question.content
            _ = question.category
            _ = question.difficulty
            _ = question.explanation
            _ = question.created_at
            _ = question.updated_at
        return question
    
    def get_questions_by_category(self, category: str) -> List[Question]:
        """カテゴリで問題を取得"""
        statement = select(Question).where(Question.category == category)
        results = self.session.exec(statement).all()
        
        # セッションから切り離される前に必要なデータをプリロード
        for question in results:
            _ = question.id
            _ = question.title
            _ = question.content
            _ = question.category
            _ = question.difficulty
            _ = question.explanation
            _ = question.created_at
            _ = question.updated_at
        
        return results
    
    def get_random_questions(self, limit: int = 10) -> List[Question]:
        """ランダムに問題を取得"""
        statement = select(Question).order_by(func.random()).limit(limit)
        results = self.session.exec(statement).all()
        
        # セッションから切り離される前に必要なデータをプリロード
        for question in results:
            # 全ての属性にアクセスして確実にロード
            _ = question.id
            _ = question.title
            _ = question.content
            _ = question.category
            _ = question.difficulty
            _ = question.explanation
            _ = question.created_at
            _ = question.updated_at
        
        return results
    
    def get_all_questions(self) -> List[Question]:
        """すべての問題を取得"""
        statement = select(Question)
        results = self.session.exec(statement).all()
        
        # セッションから切り離される前に必要なデータをプリロード
        for question in results:
            # 全ての属性にアクセスして確実にロード
            _ = question.id
            _ = question.title
            _ = question.content
            _ = question.category
            _ = question.difficulty
            _ = question.explanation
            _ = question.created_at
            _ = question.updated_at
        
        return results
    
    def get_question_count(self) -> int:
        """問題の総数を取得（効率的）"""
        statement = select(func.count(Question.id))
        result = self.session.exec(statement).one()
        return result
    
    def get_random_questions_by_category(self, category: str, limit: int = 10) -> List[Question]:
        """指定したカテゴリからランダムに問題を取得"""
        statement = select(Question).where(Question.category == category).order_by(func.random()).limit(limit)
        results = self.session.exec(statement).all()
        
        # セッションから切り離される前に必要なデータをプリロード
        for question in results:
            _ = question.id
            _ = question.title
            _ = question.content
            _ = question.category
            _ = question.difficulty
            _ = question.explanation
            _ = question.created_at
            _ = question.updated_at
        
        return results
    
    def get_all_categories(self) -> List[str]:
        """全ての問題のカテゴリを取得"""
        statement = select(Question.category).distinct()
        result = self.session.exec(statement).all()
        return [category for category in result if category]
    
    def get_categories(self) -> List[str]:
        """全ての問題のカテゴリを取得（get_all_categoriesのエイリアス）"""
        return self.get_all_categories()
    
    def get_category_statistics(self) -> dict:
        """各カテゴリの統計情報を取得"""
        statement = select(Question.category, func.count(Question.id)).group_by(Question.category)
        result = self.session.exec(statement).all()
        
        stats = {}
        for category, count in result:
            if category:  # Noneまたは空文字列を除外
                stats[category] = {
                    'count': count,
                    'category': category
                }
        
        return stats
    
    def count_questions_by_category(self, category: str) -> int:
        """指定されたカテゴリの問題数をカウント"""
        statement = select(func.count(Question.id)).where(Question.category == category)
        return self.session.exec(statement).first() or 0
    
    def get_category_stats(self) -> dict:
        """各カテゴリの問題数の統計を取得"""
        statement = select(Question.category, func.count(Question.id)).group_by(Question.category)
        result = self.session.exec(statement).all()
        
        stats = {}
        for category, count in result:
            if category:  # Noneまたは空文字列を除外
                stats[category] = count
        
        return stats
    
    def validate_question_integrity(self, question_id: int) -> dict:
        """問題の整合性を検証"""
        from services.enhanced_openai_service import EnhancedOpenAIService
        from database.operations import ChoiceService
        
        question = self.get_question_by_id(question_id)
        if not question:
            return {"valid": False, "errors": ["問題が見つかりません"]}
        
        choice_service = ChoiceService(self.session)
        choices = choice_service.get_choices_by_question(question_id)
        
        validation_result = {
            "question_id": question_id,
            "valid": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # 基本検証
        validation_result = self._validate_basic_structure(question, choices, validation_result)
        
        # AI検証（オプション）
        try:
            ai_validation = self._validate_with_ai(question, choices)
            validation_result["ai_validation"] = ai_validation
            if not ai_validation.get("coherent", True):
                validation_result["warnings"].append("AI検証: 問題と選択肢の関連性が低い可能性があります")
        except Exception as e:
            validation_result["warnings"].append(f"AI検証が利用できません: {e}")
        
        # 最終判定
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result
    
    def _validate_basic_structure(self, question, choices, validation_result):
        """基本構造の検証"""
        # 必須フィールドチェック
        if not question.title or len(question.title.strip()) < 3:
            validation_result["errors"].append("問題タイトルが短すぎます（3文字以上必要）")
        
        if not question.content or len(question.content.strip()) < 5:
            validation_result["errors"].append("問題文が短すぎます（5文字以上必要）")
        
        if not question.category or len(question.category.strip()) < 2:
            validation_result["errors"].append("カテゴリが設定されていないか短すぎます")
        
        # 選択肢チェック
        if len(choices) < 2:
            validation_result["errors"].append("選択肢が2個未満です（最低2個必要）")
        elif len(choices) > 6:
            validation_result["warnings"].append("選択肢が6個を超えています（推奨: 2-6個）")
        
        # 正解チェック
        correct_choices = [c for c in choices if c.is_correct]
        if len(correct_choices) == 0:
            validation_result["errors"].append("正解が設定されていません")
        elif len(correct_choices) > 1:
            validation_result["warnings"].append("複数の正解が設定されています")
        
        # 選択肢の重複チェック
        choice_texts = [c.text.strip().lower() for c in choices]
        if len(choice_texts) != len(set(choice_texts)):
            validation_result["warnings"].append("重複する選択肢があります")
        
        # 選択肢の長さチェック
        for i, choice in enumerate(choices):
            if len(choice.text.strip()) < 1:
                validation_result["errors"].append(f"選択肢{i+1}が空です")
            elif len(choice.text) > 200:
                validation_result["warnings"].append(f"選択肢{i+1}が長すぎます（200文字以下推奨）")
        
        validation_result["details"]["choice_count"] = len(choices)
        validation_result["details"]["correct_count"] = len(correct_choices)
        validation_result["details"]["title_length"] = len(question.title) if question.title else 0
        validation_result["details"]["content_length"] = len(question.content) if question.content else 0
        
        return validation_result
    def _validate_with_ai(self, question, choices):
        """AIを使用した高度な検証"""
        try:
            from services.enhanced_openai_service import EnhancedOpenAIService
            openai_service = EnhancedOpenAIService(model_name="gpt-4o-mini")
        except ImportError:
            # インポートエラーの場合は基本検証のみ
            return {"coherent": True, "error": "AI検証は利用できません"}
        
        # 検証用プロンプト
        choice_text = "\n".join([f"{i+1}. {choice.text}" for i, choice in enumerate(choices)])
        
        prompt = f"""以下の問題と選択肢の整合性を検証してください。

問題: {question.title}
問題文: {question.content}
カテゴリ: {question.category}

選択肢:
{choice_text}

以下の点を検証し、JSON形式で回答してください：
1. 問題文と選択肢の関連性（coherent: true/false）
2. 選択肢が問題に対して適切か（appropriate: true/false）  
3. 日本語として自然か（natural: true/false）
4. 具体的な問題点があれば指摘（issues: [])

回答形式:
{{
  "coherent": true/false,
  "appropriate": true/false,
  "natural": true/false,
  "issues": ["問題点1", "問題点2"]
}}"""

        try:
            response = openai_service.generate_response(prompt, temperature=0.1)
            
            # JSON解析を試行
            import json
            import re
            
            # JSON部分を抽出
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"error": "AI応答からJSON形式を抽出できませんでした"}
                
        except Exception as e:
            return {"error": f"AI検証エラー: {e}"}
    
    def delete_question(self, question_id: int) -> bool:
        """問題を削除（関連する選択肢・回答も削除）- 改良版"""
        try:
            print(f"🔍 削除開始: 問題ID {question_id}")
            
            # 問題を取得
            question = self.session.get(Question, question_id)
            if not question:
                print(f"❌ 問題が見つかりません: ID {question_id}")
                return False
            
            print(f"✅ 問題を発見: {question.title}")
            
            # 最初にユーザー回答を削除（外部キー制約のため）
            print("🔄 関連回答履歴を削除中...")
            answer_delete_stmt = delete(UserAnswer).where(UserAnswer.question_id == question_id)
            answer_result = self.session.exec(answer_delete_stmt)
            deleted_answers = answer_result.rowcount if hasattr(answer_result, 'rowcount') else 0
            print(f"✅ {deleted_answers}個の回答履歴を削除")
            
            # 次に選択肢を削除
            print("🔄 関連選択肢を削除中...")
            choice_delete_stmt = delete(Choice).where(Choice.question_id == question_id)
            choice_result = self.session.exec(choice_delete_stmt)
            deleted_choices = choice_result.rowcount if hasattr(choice_result, 'rowcount') else 0
            print(f"✅ {deleted_choices}個の選択肢を削除")
            
            # 問題を削除
            print("🔄 問題本体を削除中...")
            self.session.delete(question)
            
            # コミット
            self.session.commit()
            print(f"✅ 問題ID {question_id} の削除完了")
            
            # 削除確認
            verification = self.session.get(Question, question_id)
            if verification is None:
                print(f"🔍 削除確認: 問題ID {question_id} は正常に削除されました")
                return True
            else:
                print(f"⚠️ 削除確認: 問題ID {question_id} がまだ存在しています")
                return False
            
        except Exception as e:
            print(f"❌ 問題削除エラー: {e}")
            import traceback
            print(f"📝 詳細エラー: {traceback.format_exc()}")
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
            print(f"[DEBUG] create_question_with_duplicate_check: 重複判定で作成拒否: {duplicate_check['recommendation']}")
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
            print(f"[DEBUG] create_question_with_duplicate_check: 例外発生: {e}")
            import traceback
            print(traceback.format_exc())
            return {
                "success": False,
                "question": None,
                "duplicate_check": duplicate_check,
                "message": f"作成エラー: {e}"
            }
        
    def validate_question_and_choices(self, question, choices) -> dict:
        """
        問題と選択肢の妥当性を検証
        
        Args:
            question: 問題オブジェクト（一時的なオブジェクトでも可）
            choices: 選択肢のリスト
            
        Returns:
            dict: {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "details": dict
            }
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # 問題の基本検証
        if not hasattr(question, 'title') or not question.title or len(question.title.strip()) < 3:
            validation_result["errors"].append("問題タイトルが短すぎます（3文字以上必要）")
        
        if not hasattr(question, 'content') or not question.content or len(question.content.strip()) < 5:
            validation_result["errors"].append("問題文が短すぎます（5文字以上必要）")
        
        if not hasattr(question, 'category') or not question.category or len(question.category.strip()) < 2:
            validation_result["errors"].append("カテゴリが設定されていないか短すぎます")
        
        # 選択肢の基本検証
        if not choices or len(choices) < 2:
            validation_result["errors"].append("選択肢が2個未満です（最低2個必要）")
        elif len(choices) > 6:
            validation_result["warnings"].append("選択肢が6個を超えています（推奨: 2-6個）")
        
        if choices:
            # 正解の検証
            correct_choices = []
            for choice in choices:
                if hasattr(choice, 'is_correct') and choice.is_correct:
                    correct_choices.append(choice)
            
            if len(correct_choices) == 0:
                validation_result["errors"].append("正解が設定されていません")
            elif len(correct_choices) > 1:
                validation_result["warnings"].append("複数の正解が設定されています")
            
            # 選択肢の内容検証
            choice_texts = []
            for i, choice in enumerate(choices):
                choice_text = getattr(choice, 'text', getattr(choice, 'content', ''))
                if not choice_text or len(choice_text.strip()) < 1:
                    validation_result["errors"].append(f"選択肢{i+1}が空です")
                elif len(choice_text) > 200:
                    validation_result["warnings"].append(f"選択肢{i+1}が長すぎます（200文字以下推奨）")
                
                choice_texts.append(choice_text.strip().lower())
            
            # 選択肢の重複チェック
            if len(choice_texts) != len(set(choice_texts)):
                validation_result["warnings"].append("重複する選択肢があります")
            
            # 詳細情報を設定
            validation_result["details"]["choice_count"] = len(choices)
            validation_result["details"]["correct_count"] = len(correct_choices)
        
        # 問題の詳細情報を設定
        if hasattr(question, 'title') and question.title:
            validation_result["details"]["title_length"] = len(question.title)
        if hasattr(question, 'content') and question.content:
            validation_result["details"]["content_length"] = len(question.content)
        
        # 最終判定
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result

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
    
    def get_category_stats(self, session_id: Optional[str] = None) -> dict:
        """カテゴリ別の統計を取得"""
        try:
            from sqlmodel import func, text
            
            statement = (
                select(
                    Question.category,
                    func.count(UserAnswer.id).label('total_answers'),
                    func.sum(text("CASE WHEN useranswer.is_correct THEN 1 ELSE 0 END")).label('correct_answers')
                )
                .join(Question, UserAnswer.question_id == Question.id)
            )
            
            if session_id:
                statement = statement.where(UserAnswer.session_id == session_id)
            
            statement = statement.group_by(Question.category)
            
            results = self.session.exec(statement).all()
            
            category_stats = {}
            for result in results:
                category = result[0]
                total = int(result[1]) if result[1] is not None else 0
                correct = int(result[2]) if result[2] is not None else 0
                accuracy = (correct / total * 100) if total > 0 else 0.0
                
                category_stats[category] = {
                    "total": total,
                    "correct": correct,
                    "accuracy": round(accuracy, 2)
                }
            
            return category_stats
        except Exception as e:
            print(f"カテゴリ別統計取得エラー: {e}")
            # エラー時はセッションをロールバック
            try:
                self.session.rollback()
            except:
                pass
            return {}
    
    def get_daily_stats(self, session_id: Optional[str] = None, days: int = 30) -> dict:
        """日別の統計を取得"""
        try:
            from sqlmodel import func, text
            from datetime import datetime, timedelta
            
            # 過去N日間の日付範囲を設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            statement = (
                select(
                    func.date(UserAnswer.answered_at).label('date'),
                    func.count(UserAnswer.id).label('total_answers'),
                    func.sum(text("CASE WHEN useranswer.is_correct THEN 1 ELSE 0 END")).label('correct_answers')
                )
                .where(UserAnswer.answered_at >= start_date)
                .where(UserAnswer.answered_at <= end_date)
            )
            
            if session_id:
                statement = statement.where(UserAnswer.session_id == session_id)
            
            statement = statement.group_by(func.date(UserAnswer.answered_at)).order_by(func.date(UserAnswer.answered_at))
            
            results = self.session.exec(statement).all()
            
            daily_stats = {}
            for result in results:
                date = str(result[0])
                total = int(result[1]) if result[1] is not None else 0
                correct = int(result[2]) if result[2] is not None else 0
                accuracy = (correct / total * 100) if total > 0 else 0.0
                
                daily_stats[date] = {
                    "total": total,
                    "correct": correct,
                    "accuracy": round(accuracy, 2)
                }
            
            return daily_stats
        except Exception as e:
            print(f"日別統計取得エラー: {e}")
            # エラー時はセッションをロールバック
            try:
                self.session.rollback()
            except:
                pass
            return {}
    
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
