# -*- coding: utf-8 -*-
"""
OpenAI API service for question generation
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeneratedChoice(BaseModel):
    """Generated choice model"""
    content: str
    is_correct: bool


class GeneratedQuestion(BaseModel):
    """Generated question model"""
    title: str
    content: str
    explanation: str
    category: str
    difficulty: str
    choices: List[GeneratedChoice]


class OpenAIService:
    """OpenAI API service for question generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1500"))
    
    def generate_question(
        self, 
        category: str = "基本情報技術者", 
        difficulty: str = "medium",
        topic: Optional[str] = None
    ) -> Optional[GeneratedQuestion]:
        """
        Generate a quiz question using OpenAI API
        
        Args:
            category: Question category
            difficulty: Question difficulty (easy, medium, hard)
            topic: Specific topic (optional)
            
        Returns:
            GeneratedQuestion object or None if failed
        """
        
        # Create prompt
        prompt = self._create_prompt(category, difficulty, topic)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは資格試験の問題作成の専門家です。正確で教育的な問題を作成してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            question_data = json.loads(content)
            
            # Validate and create GeneratedQuestion
            return self._parse_question_data(question_data, category, difficulty)
            
        except Exception as e:
            print(f"Error generating question: {e}")
            return None
    
    def generate_multiple_questions(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        count: int = 3,
        topics: Optional[List[str]] = None
    ) -> List[GeneratedQuestion]:
        """
        Generate multiple questions
        
        Args:
            category: Question category
            difficulty: Question difficulty
            count: Number of questions to generate
            topics: List of specific topics (optional)
            
        Returns:
            List of GeneratedQuestion objects
        """
        questions = []
        
        for i in range(count):
            topic = topics[i] if topics and i < len(topics) else None
            question = self.generate_question(category, difficulty, topic)
            
            if question:
                questions.append(question)
        
        return questions
    
    def _create_prompt(self, category: str, difficulty: str, topic: Optional[str] = None) -> str:
        """Create prompt for question generation"""
        
        difficulty_map = {
            "easy": "初級レベル（基本的な知識）",
            "medium": "中級レベル（応用的な理解）", 
            "hard": "上級レベル（高度な分析力）"
        }
        
        difficulty_desc = difficulty_map.get(difficulty, "中級レベル")
        topic_instruction = f"特に「{topic}」に関する内容で" if topic else ""
        
        prompt = f"""
{category}の{difficulty_desc}の問題を1問作成してください。{topic_instruction}

以下のJSON形式で回答してください：

{{
    "title": "問題のタイトル（簡潔に）",
    "content": "問題文（具体的で明確に）",
    "explanation": "解説（正解の理由と重要なポイント）",
    "choices": [
        {{"content": "選択肢A", "is_correct": false}},
        {{"content": "選択肢B", "is_correct": true}},
        {{"content": "選択肢C", "is_correct": false}},
        {{"content": "選択肢D", "is_correct": false}}
    ]
}}

要件：
- 4択問題で正解は1つのみ
- 実際の試験に出題されそうな実践的な内容
- 間違いの選択肢も適度に紛らわしく
- 解説は学習に役立つ詳細な内容
- 日本語で作成
"""
        return prompt
    
    def _parse_question_data(
        self, 
        data: Dict, 
        category: str, 
        difficulty: str
    ) -> Optional[GeneratedQuestion]:
        """Parse question data from OpenAI response"""
        
        try:
            choices = []
            for choice_data in data.get("choices", []):
                choices.append(GeneratedChoice(
                    content=choice_data["content"],
                    is_correct=choice_data["is_correct"]
                ))
            
            # Validate that there's exactly one correct answer
            correct_count = sum(1 for choice in choices if choice.is_correct)
            if correct_count != 1:
                print(f"Warning: Expected 1 correct answer, got {correct_count}")
                return None
            
            return GeneratedQuestion(
                title=data["title"],
                content=data["content"],
                explanation=data["explanation"],
                category=category,
                difficulty=difficulty,
                choices=choices
            )
            
        except Exception as e:
            print(f"Error parsing question data: {e}")
            return None


# Test function
def test_openai_service():
    """Test the OpenAI service"""
    service = OpenAIService()
    
    print("🧪 Testing OpenAI question generation...")
    
    question = service.generate_question(
        category="プログラミング基礎",
        difficulty="easy",
        topic="変数とデータ型"
    )
    
    if question:
        print("✅ Question generated successfully!")
        print(f"Title: {question.title}")
        print(f"Content: {question.content}")
        print(f"Choices: {len(question.choices)}")
    else:
        print("❌ Failed to generate question")


if __name__ == "__main__":
    test_openai_service()
