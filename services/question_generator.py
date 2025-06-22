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
        progress_callback: Optional[callable] = None,
        enable_duplicate_check: bool = True,
        enable_content_validation: bool = True,
        similarity_threshold: float = 0.8,
        max_retry_attempts: int = 3,
        allow_multiple_correct: bool = False
    ) -> Optional[int]:
        """
        Generate a question using OpenAI and save to database with progress callback, duplicate checking and content validation
        
        Args:
            category: 問題カテゴリ
            difficulty: 難易度
            topic: 特定のトピック
            progress_callback: 進捗コールバック関数
            enable_duplicate_check: 重複チェックを有効にするか
            enable_content_validation: 内容検証を有効にするか
            similarity_threshold: 類似度閾値
            max_retry_attempts: 重複時の最大再試行回数
            allow_multiple_correct: 複数正解を許可するか
        
        Returns:
            Question ID if successful, None if failed
        """
        
        if not self.openai_service:
            print("OpenAI service not available")
            return None
        
        retry_count = 0
        validation_retry_count = 0
        max_validation_retries = 2
        
        while retry_count <= max_retry_attempts:
            if progress_callback:
                if retry_count == 0:
                    progress_callback("AI問題を生成中...", 0.1)
                else:
                    progress_callback(f"類似問題検出 - 再生成中... ({retry_count}/{max_retry_attempts})", 0.1 + retry_count * 0.2)
            
            # Generate question using OpenAI
            generated_question = self.openai_service.generate_question(
                category=category,
                difficulty=difficulty,
                topic=topic,
                allow_multiple_correct=allow_multiple_correct
            )
            
            if not generated_question:
                if progress_callback:
                    progress_callback("問題生成に失敗しました", 0.0)
                return None
            
            # 内容検証（有効な場合）
            if enable_content_validation:
                if progress_callback:
                    progress_callback("問題内容を検証中...", 0.3)
                
                # 一時的な問題と選択肢を作成して検証
                temp_question = type('TempQuestion', (), {
                    'title': generated_question.title,
                    'content': generated_question.content,
                    'category': generated_question.category,
                    'explanation': generated_question.explanation,
                    'difficulty': generated_question.difficulty
                })()
                
                temp_choices = []
                for choice in generated_question.choices:
                    temp_choice = type('TempChoice', (), {
                        'text': choice.content,
                        'is_correct': choice.is_correct
                    })()
                    temp_choices.append(temp_choice)
                
                try:
                    validation_result = self.question_service.validate_question_and_choices(temp_question, temp_choices)
                    
                    # 重大なエラーがある場合は再生成
                    if not validation_result["valid"]:
                        print(f"⚠️ 内容検証失敗: {validation_result['errors']}")
                        if validation_retry_count < max_validation_retries:
                            validation_retry_count += 1
                            if progress_callback:
                                progress_callback(f"内容不正 - 再生成中... ({validation_retry_count}/{max_validation_retries})", 0.2)
                            continue
                        else:
                            # 最大検証再試行回数に達した場合は警告付きで継続
                            print(f"🔄 内容検証の最大再試行回数に達しました。警告付きで作成します。")
                            if progress_callback:
                                progress_callback("内容検証を継続...", 0.35)
                    
                    # 警告がある場合はログ出力
                    if validation_result["warnings"]:
                        print(f"📋 内容検証警告: {validation_result['warnings']}")
                        
                except Exception as e:
                    print(f"⚠️ 内容検証でエラー: {e}")
                    # 検証エラーの場合は継続
            
            # 重複チェック（有効な場合）
            if enable_duplicate_check:
                if progress_callback:
                    progress_callback("重複チェック中...", 0.4)
                
                duplicate_check = self.question_service.check_duplicate_before_creation(
                    title=generated_question.title,
                    content=generated_question.content,
                    category=generated_question.category,
                    similarity_threshold=similarity_threshold
                )
                
                # 高い類似度が検出された場合
                if duplicate_check["is_duplicate"]:
                    print(f"⚠️ 重複検出 (類似度: {duplicate_check['highest_similarity']:.2f}): {generated_question.title}")
                    
                    if retry_count < max_retry_attempts:
                        retry_count += 1
                        # より具体的なトピックで再生成を試みる
                        if topic:
                            topic = f"{topic} (異なる観点)"
                        else:
                            topic = f"{category} の別の側面"
                        continue
                    else:
                        # 最大試行回数に達した場合は警告付きで作成
                        if progress_callback:
                            progress_callback("類似問題ですが作成を継続...", 0.6)
                        print(f"🔄 最大再試行回数に達しました。類似問題として作成します。")
            
            # 問題作成実行
            if progress_callback:
                progress_callback("データベースに保存中...", 0.7)
            
            try:
                # 重複チェック付きで問題作成
                creation_result = self.question_service.create_question_with_duplicate_check(
                    title=generated_question.title,
                    content=generated_question.content,
                    category=generated_question.category,
                    explanation=generated_question.explanation,
                    difficulty=generated_question.difficulty,
                    force_create=True,  # 再試行後は強制作成
                    similarity_threshold=similarity_threshold
                )
                
                if not creation_result["success"]:
                    if progress_callback:
                        progress_callback(f"作成失敗: {creation_result['message']}", 0.0)
                    return None
                
                question = creation_result["question"]
                
                # Create choices
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
                
                # 重複チェック結果をログ出力
                if enable_duplicate_check and creation_result["duplicate_check"]["highest_similarity"] > 0.5:
                    print(f"📊 重複チェック結果: {creation_result['message']}")
                    if creation_result["duplicate_check"]["similar_questions"]:
                        print(f"🔍 類似問題数: {len(creation_result['duplicate_check']['similar_questions'])}")
                
                if progress_callback:
                    progress_callback("問題作成完了！", 1.0)
                
                print(f"✅ Question created successfully with ID: {question.id}")
                return question.id
                
            except Exception as e:
                print(f"❌ Error saving question: {e}")
                if progress_callback:
                    progress_callback(f"保存エラー: {e}", 0.0)
                return None
        
        # すべての試行が失敗した場合
        if progress_callback:
            progress_callback("問題生成に失敗しました", 0.0)
        return None
    
    def generate_and_save_multiple_questions(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        count: int = 3,
        topics: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None,
        delay_between_requests: float = 1.0,
        enable_duplicate_check: bool = True,
        enable_content_validation: bool = True,
        similarity_threshold: float = 0.8,
        max_retry_attempts: int = 3,
        allow_multiple_correct: bool = False
    ) -> List[int]:
        """
        Generate multiple questions and save to database with progress tracking, duplicate checking and content validation
        
        Args:
            enable_duplicate_check: 重複チェックを有効にするか
            enable_content_validation: 内容検証を有効にするか
            similarity_threshold: 類似度閾値
            max_retry_attempts: 重複時の最大再試行回数
        
        Returns:
            List of question IDs that were successfully created
        """
        
        if not self.openai_service:
            if progress_callback:
                progress_callback("OpenAI service not available", 0.0)
            return []
        
        question_ids = []
        successful_count = 0
        
        for i in range(count):
            if progress_callback:
                progress = (i / count)
                if enable_duplicate_check:
                    progress_callback(f"問題 {i+1}/{count} を生成中（重複チェック有効）...", progress)
                else:
                    progress_callback(f"問題 {i+1}/{count} を生成中...", progress)
            topic = topics[i] if topics and i < len(topics) else None
            
            question_id = self.generate_and_save_question(
                category=category,
                difficulty=difficulty,
                topic=topic,
                progress_callback=None,  # 個別の進捗は表示しない
                enable_duplicate_check=enable_duplicate_check,
                enable_content_validation=enable_content_validation,
                similarity_threshold=similarity_threshold,
                max_retry_attempts=max_retry_attempts,
                allow_multiple_correct=allow_multiple_correct
            )
            
            if question_id:
                question_ids.append(question_id)
                successful_count += 1
                print(f"✅ Generated question {i+1}/{count}: ID {question_id}")
            else:
                print(f"❌ Failed to generate question {i+1}/{count}")
            
            # 最後の問題でない場合は待機
            if i < count - 1:
                import time
                time.sleep(delay_between_requests)
            
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
            print("🔍 Validating OpenAI connection...")
            test_result = self.openai_service.test_connection()
            
            if test_result.get("success", False):
                print("✅ OpenAI connection validation successful")
                return {
                    "status": "success",
                    "message": test_result.get("message", "Connection successful"),
                    "connected": True,
                    "model": test_result.get("model", "unknown"),
                    "usage_info": self.openai_service.get_usage_info()
                }
            else:
                error_message = test_result.get("error", "Connection failed")
                error_type = test_result.get("error_type", "unknown")
                
                print(f"❌ OpenAI connection validation failed: {error_message}")
                return {
                    "status": "error",
                    "message": error_message,
                    "connected": False,
                    "error_type": error_type,
                    "model": test_result.get("model", "unknown")
                }
        except Exception as e:
            error_message = f"Connection validation error: {e}"
            print(f"❌ {error_message}")
            return {
                "status": "error",
                "message": error_message,
                "connected": False,
                "error_type": "validation_error"
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


# Backward compatibility alias
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
