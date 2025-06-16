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
    
    def __init__(self, session: Session, model: str = "gpt-3.5-turbo"):
        print(f"🔧 QuestionGenerator initializing with model: {model}")
        self.session = session
        self.question_service = QuestionService(session)
        self.choice_service = ChoiceService(session)
        try:
            print(f"🤖 Creating EnhancedOpenAIService with model: {model}")
            self.openai_service = EnhancedOpenAIService(model=model)
            print(f"✅ OpenAI service created successfully with model: {self.openai_service.model}")
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
            )              # Create choices
            print(f"💾 Saving {len(generated_question.choices)} choices for question {question.id}")
            for i, choice in enumerate(generated_question.choices):
                print(f"   💾 Saving choice {i+1}: {choice.content[:50]}... (correct: {choice.is_correct})")
                saved_choice = self.choice_service.create_choice(
                    question_id=question.id,
                    content=choice.content,
                    is_correct=choice.is_correct,
                    order_num=i + 1
                )
                print(f"   ✅ Choice saved with ID: {saved_choice.id}")
            
            # Verify choices were saved
            saved_choices = self.choice_service.get_choices_by_question_id(question.id)
            print(f"🔍 Verification: Found {len(saved_choices)} saved choices")
            if len(saved_choices) != len(generated_question.choices):
                print(f"⚠️ Warning: Expected {len(generated_question.choices)} choices, but {len(saved_choices)} were saved")
                print(f"Generated choices: {[c.content for c in generated_question.choices]}")
                print(f"Saved choices: {[c.content for c in saved_choices]}")
            elif len(saved_choices) == 0:
                print("🔧 No choices found - adding fallback choices")
                # フォールバック選択肢を追加
                fallback_choices = self._create_fallback_choices(generated_question.content, generated_question.category)
                for i, choice_content in enumerate(fallback_choices, 1):
                    is_correct = (i == 1)  # 最初の選択肢を正解とする
                    self.choice_service.create_choice(
                        question_id=question.id,
                        content=choice_content,
                        is_correct=is_correct,
                        order_num=i
                    )
                    print(f"   🔧 Fallback choice {i}: {choice_content} (correct: {is_correct})")
                print("✅ Fallback choices added")
            else:
                print(f"✅ Successfully saved {len(saved_choices)} choices for question {question.id}")
            
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
            print("Validating OpenAI connection...")
            connected = self.openai_service.test_connection()
            
            if connected:
                print("OpenAI connection validation successful")
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "connected": True,
                    "usage_info": self.openai_service.get_usage_info()
                }
            else:
                print("OpenAI connection validation failed")
                return {
                    "status": "error",
                    "message": "Connection failed",
                    "connected": False
                }
                
        except Exception as e:
            print(f"OpenAI connection validation error: {e}")
            return {
                "status": "error", 
                "message": f"Connection failed: {str(e)}",
                "connected": False
            }
    
    def _create_fallback_choices(self, question_content: str, category: str) -> List[str]:
        """選択肢が生成されなかった場合のフォールバック選択肢を作成"""
        
        # カテゴリ別の一般的な選択肢パターン
        fallback_patterns = {
            "基本情報技術者": [
                "選択肢A",
                "選択肢B", 
                "選択肢C",
                "選択肢D"
            ],
            "データベース": [
                "SQL",
                "NoSQL",
                "インデックス",
                "ビュー"
            ],
            "ネットワーク": [
                "TCP/IP",
                "HTTP",
                "DNS",
                "DHCP"
            ]
        }
        
        # カテゴリに応じたフォールバック選択肢を返す
        if category in fallback_patterns:
            return fallback_patterns[category]
        else:
            return fallback_patterns["基本情報技術者"]
    

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
