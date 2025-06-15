# -*- coding: utf-8 -*-
"""
Enhanced question generation and management service
"""

from typing import List, Optional
from sqlmodel import Session
from database.operations import QuestionService, ChoiceService
from services.enhanced_openai_service import EnhancedOpenAIService, GeneratedQuestion
import time


class EnhancedQuestionGenerator:
    """Enhanced service for generating and managing AI-generated questions"""
    
    def __init__(self, session: Session):
        self.session = session
        self.question_service = QuestionService(session)
        self.choice_service = ChoiceService(session)
        try:
            self.openai_service = EnhancedOpenAIService()
        except Exception as e:
            print(f"Warning: OpenAI service initialization failed: {e}")
            self.openai_service = None
    
    def generate_and_save_question(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        topic: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Optional[int]:
        """
        Generate a question using OpenAI and save to database with progress callback
        
        Returns:
            Question ID if successful, None if failed
        """
        
        if not self.openai_service:
            print("OpenAI service not available")
            return None
        
        if progress_callback:
            progress_callback("AI問題を生成中...", 0.1)
        
        # Generate question using OpenAI
        generated_question = self.openai_service.generate_question(
            category=category,
            difficulty=difficulty,
            topic=topic
        )
        
        if not generated_question:
            if progress_callback:
                progress_callback("問題生成に失敗しました", 0.0)
            return None
        
        if progress_callback:
            progress_callback("データベースに保存中...", 0.7)
        
        # Save question to database
        try:
            # Create question
            question = self.question_service.create_question(
                title=generated_question.title,
                content=generated_question.content,
                category=generated_question.category,
                explanation=generated_question.explanation,
                difficulty=generated_question.difficulty
            )
            
            # Create choices
            for i, choice in enumerate(generated_question.choices):
                self.choice_service.create_choice(
                    question_id=question.id,
                    content=choice.content,
                    is_correct=choice.is_correct,
                    order_num=i + 1
                )
            
            if progress_callback:
                progress_callback("問題生成完了！", 1.0)
            
            return question.id
            
        except Exception as e:
            print(f"Error saving generated question: {e}")
            if progress_callback:
                progress_callback(f"保存エラー: {e}", 0.0)
            return None
    
    def generate_and_save_multiple_questions(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        count: int = 3,
        topics: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None,
        delay_between_requests: float = 1.0
    ) -> List[int]:
        """
        Generate multiple questions and save to database with progress tracking
        
        Returns:
            List of question IDs that were successfully created
        """
        
        if not self.openai_service:
            if progress_callback:
                progress_callback("OpenAI service not available", 0.0)
            return []
        
        question_ids = []
        
        for i in range(count):
            if progress_callback:
                progress = (i / count)
                progress_callback(f"問題 {i+1}/{count} を生成中...", progress)
            
            topic = topics[i] if topics and i < len(topics) else None
            
            question_id = self.generate_and_save_question(
                category=category,
                difficulty=difficulty,
                topic=topic
            )
            
            if question_id:
                question_ids.append(question_id)
                print(f"✅ Generated question {i+1}/{count}: ID {question_id}")
            else:
                print(f"❌ Failed to generate question {i+1}/{count}")
            
            # Rate limiting - add delay between requests
            if i < count - 1 and delay_between_requests > 0:
                time.sleep(delay_between_requests)
        
        if progress_callback:
            progress_callback(f"生成完了: {len(question_ids)}/{count}問成功", 1.0)
        
        return question_ids
    
    def get_generation_stats(self) -> dict:
        """Get enhanced statistics about generated questions"""
        
        # Get all questions (this is a simple implementation)
        all_questions = self.question_service.get_random_questions(limit=1000)
        
        stats = {
            "total_questions": len(all_questions),
            "categories": {},
            "difficulties": {},
            "openai_available": self.openai_service is not None
        }
        
        # Count by category and difficulty
        for question in all_questions:
            # Category stats
            if question.category not in stats["categories"]:
                stats["categories"][question.category] = 0
            stats["categories"][question.category] += 1
            
            # Difficulty stats
            if question.difficulty not in stats["difficulties"]:
                stats["difficulties"][question.difficulty] = 0
            stats["difficulties"][question.difficulty] += 1
        
        return stats
    
    def validate_openai_connection(self) -> dict:
        """Validate OpenAI connection and return status"""
        if not self.openai_service:
            return {
                "status": "error",
                "message": "OpenAI service not initialized",
                "connected": False
            }
        
        try:
            connected = self.openai_service.test_connection()
            return {
                "status": "success" if connected else "error",
                "message": "Connection successful" if connected else "Connection failed",
                "connected": connected,
                "usage_info": self.openai_service.get_usage_info()
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "connected": False
            }


# Backward compatibility - create an alias
QuestionGenerator = EnhancedQuestionGenerator


def test_enhanced_question_generator():
    """Test the enhanced question generator"""
    from database.connection import engine
    
    print("🧪 Testing Enhanced Question Generator...")
    
    with Session(engine) as session:
        generator = EnhancedQuestionGenerator(session)
        
        # Test connection validation
        connection_status = generator.validate_openai_connection()
        print(f"Connection status: {connection_status}")
        
        if connection_status["connected"]:
            # Generate single question with progress callback
            def progress_callback(message, progress):
                print(f"Progress: {progress:.1%} - {message}")
            
            question_id = generator.generate_and_save_question(
                category="テスト用",
                difficulty="easy",
                topic="プログラミング基礎",
                progress_callback=progress_callback
            )
            
            if question_id:
                print(f"✅ Successfully generated question with ID: {question_id}")
            else:
                print("❌ Failed to generate question")
        else:
            print("⚠️ OpenAI connection not available for testing")


if __name__ == "__main__":
    test_enhanced_question_generator()


if __name__ == "__main__":
    test_enhanced_question_generator()
