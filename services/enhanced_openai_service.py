# -*- coding: utf-8 -*-
"""
Enhanced OpenAI service with better error handling and rate limiting
"""

import os
import openai
from openai import OpenAI
import time
import json
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class GeneratedChoice:
    """Generated choice data structure"""
    content: str
    is_correct: bool


@dataclass 
class GeneratedQuestion:
    """Generated question data structure"""
    title: str
    content: str
    category: str
    explanation: str
    difficulty: str
    choices: List[GeneratedChoice]


class EnhancedOpenAIService:
    """Enhanced OpenAI service with better error handling"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def generate_question(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        topic: Optional[str] = None,
        question_type: str = "multiple_choice",
        language: str = "japanese"
    ) -> Optional[GeneratedQuestion]:
        """
        Generate a question with enhanced options and error handling
        """
        
        prompt = self._create_enhanced_prompt(
            category=category,
            difficulty=difficulty,
            topic=topic,
            question_type=question_type,
            language=language
        )
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "あなたは資格試験問題作成の専門家です。正確で教育的な問題を作成してください。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.7,
                    response_format={"type": "json_object"},
                    # プライバシー保護: データの学習を無効化
                    extra_headers={
                        "X-OpenAI-Skip-Training": "true"
                    }
                )
                
                content = response.choices[0].message.content
                question_data = json.loads(content)
                
                return self._parse_question_response(question_data, category, difficulty)
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit exceeded. Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Rate limit exceeded after {self.max_retries} attempts: {e}")
                    return None
                    
            except openai.APIError as e:
                print(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
        
        return None
    
    def _create_enhanced_prompt(
        self,
        category: str,
        difficulty: str,
        topic: Optional[str],
        question_type: str,
        language: str
    ) -> str:
        """Create an enhanced prompt with more specific instructions"""
        
        difficulty_instructions = {
            "easy": "初心者向けの基本的な概念を問う問題",
            "medium": "中級者向けの実践的な問題", 
            "hard": "上級者向けの応用・発展問題"
        }
        
        topic_instruction = f"特に「{topic}」に関連する内容で" if topic else ""
        
        prompt = f"""
{category}の{difficulty_instructions[difficulty]}を作成してください。
{topic_instruction}

以下の条件に従って、JSON形式で回答してください：

**条件:**
1. 問題文は具体的で実践的な内容にする
2. 選択肢は4つ作成する
3. 正解は1つのみ
4. 間違いの選択肢も教育的価値があるものにする
5. 解説は詳しく、なぜその答えが正しいかを説明する
6. 難易度「{difficulty}」に適した問題レベルにする

**JSON形式:**
{{
    "title": "問題のタイトル（簡潔に）",
    "content": "問題文（具体的で明確に）",
    "explanation": "詳細な解説（なぜその答えが正しいかを含む）",
    "choices": [
        {{"content": "選択肢1", "is_correct": true}},
        {{"content": "選択肢2", "is_correct": false}},
        {{"content": "選択肢3", "is_correct": false}},
        {{"content": "選択肢4", "is_correct": false}}
    ]
}}

必ずvalid JSONを返してください。
"""
        return prompt
    
    def _parse_question_response(
        self, 
        question_data: Dict, 
        category: str, 
        difficulty: str
    ) -> Optional[GeneratedQuestion]:
        """Parse the response from OpenAI into a GeneratedQuestion object"""
        
        try:
            # Validate required fields
            required_fields = ["title", "content", "explanation", "choices"]
            for field in required_fields:
                if field not in question_data:
                    print(f"Missing required field: {field}")
                    return None
            
            # Validate choices
            choices_data = question_data["choices"]
            if not isinstance(choices_data, list) or len(choices_data) != 4:
                print("Choices must be a list of exactly 4 items")
                return None
            
            # Check for exactly one correct answer
            correct_count = sum(1 for choice in choices_data if choice.get("is_correct", False))
            if correct_count != 1:
                print(f"Must have exactly 1 correct answer, found {correct_count}")
                return None
            
            # Create choices
            choices = []
            for choice_data in choices_data:
                if "content" not in choice_data:
                    print("Choice missing content field")
                    return None
                
                choices.append(GeneratedChoice(
                    content=choice_data["content"],
                    is_correct=choice_data.get("is_correct", False)
                ))
            
            return GeneratedQuestion(
                title=question_data["title"],
                content=question_data["content"],
                category=category,
                explanation=question_data["explanation"],
                difficulty=difficulty,
                choices=choices
            )
            
        except Exception as e:
            print(f"Error parsing question response: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test the OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_usage_info(self) -> Dict:
        """Get API usage information (placeholder for future implementation)"""
        return {
            "model": self.model,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
    
    def call_openai_api(
        self,
        prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
        system_message: str = "あなたは資格試験問題作成の専門家です。正確で教育的な問題を作成してください。"
    ) -> Optional[str]:
        """
        汎用的なOpenAI API呼び出しメソッド
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    # プライバシー保護: PDFデータの学習を無効化
                    extra_headers={
                        "X-OpenAI-Skip-Training": "true"
                    }
                )
                
                return response.choices[0].message.content
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit exceeded. Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Rate limit exceeded after {self.max_retries} attempts: {e}")
                    return None
                    
            except openai.APIError as e:
                print(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"OpenAI API error after {self.max_retries} attempts: {e}")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
        
        return None


def test_enhanced_openai_service():
    """Test the enhanced OpenAI service"""
    try:
        service = EnhancedOpenAIService()
        
        print("🧪 Testing Enhanced OpenAI Service...")
        
        # Test connection
        if service.test_connection():
            print("✅ API connection successful")
        else:
            print("❌ API connection failed")
            return
        
        # Test question generation
        question = service.generate_question(
            category="プログラミング基礎",
            difficulty="easy",
            topic="変数とデータ型"
        )
        
        if question:
            print("✅ Question generation successful")
            print(f"Title: {question.title}")
            print(f"Category: {question.category}")
            print(f"Difficulty: {question.difficulty}")
        else:
            print("❌ Question generation failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_enhanced_openai_service()
