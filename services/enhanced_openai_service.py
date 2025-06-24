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
import backoff

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
    
    # Available models
    AVAILABLE_MODELS = {
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "高速で経済的、日常的な問題生成に適している",
            "cost": "低",
            "quality": "良"
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini", 
            "description": "GPT-4の軽量版、高品質で経済的",
            "cost": "中",
            "quality": "優"
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "最高品質の問題生成、複雑な内容に対応",
            "cost": "高",
            "quality": "最優"
        },
        "gpt-4": {
            "name": "GPT-4",
            "description": "高品質な問題生成、詳細な解説",
            "cost": "高",
            "quality": "最優"
        }
    }
    
    def __init__(self, model: str = "gpt-3.5-turbo", model_name: str = None):
        print("Initializing EnhancedOpenAIService...")
        
        # Use model_name if provided, otherwise use model parameter
        selected_model = model_name if model_name is not None else model
        
        # Check API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("ERROR: OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        print(f"API Key found: {self.api_key[:10]}...{self.api_key[-4:]}")
        
        # Validate and set model
        if selected_model not in self.AVAILABLE_MODELS:
            print(f"Warning: Model {selected_model} not in available models, using gpt-3.5-turbo")
            selected_model = "gpt-3.5-turbo"
        
        self.model = selected_model
        print(f"Using model: {self.model} ({self.AVAILABLE_MODELS[self.model]['name']})")
        
        # Initialize OpenAI client with enhanced connection settings
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=60.0,  # 60秒のタイムアウト
                max_retries=3,  # 内蔵リトライ機能
                base_url="https://api.openai.com/v1"  # 明示的なエンドポイント
            )
            print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize OpenAI client: {e}")
            raise ConnectionError(f"Failed to initialize OpenAI client: {e}")
        
        self.max_retries = 5  # リトライ回数を増加
        self.retry_delay = 2.0  # 初期遅延を増加
    
    def generate_question(
        self,
        category: str = "基本情報技術者",
        difficulty: str = "medium",
        topic: Optional[str] = None,
        question_type: str = "multiple_choice",
        language: str = "japanese",
        allow_multiple_correct: bool = False
    ) -> Optional[GeneratedQuestion]:
        """
        Generate a question with enhanced options and error handling
        
        Args:
            category: 問題カテゴリ
            difficulty: 難易度
            topic: 特定のトピック（オプション）
            question_type: 問題タイプ
            language: 言語
            allow_multiple_correct: 複数の正解を許可するかどうか
        """
        
        prompt = self._create_enhanced_prompt(
            category=category,
            difficulty=difficulty,
            topic=topic,
            question_type=question_type,
            language=language,
            allow_multiple_correct=allow_multiple_correct
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
                
                # プライバシー保護の確認ログ
                print("PRIVACY: OpenAI学習無効化ヘッダー送信完了")
                
                content = response.choices[0].message.content
                print(f"🤖 OpenAI Raw Response Length: {len(content)} characters")
                print(f"🤖 OpenAI Raw Response Preview: {content[:200]}...")
                
                try:
                    question_data = json.loads(content)
                    print(f"📋 Parsed JSON keys: {list(question_data.keys())}")
                    if 'choices' in question_data:
                        print(f"📋 Choices found in response: {len(question_data['choices'])} items")
                        for i, choice in enumerate(question_data['choices'][:2]):  # 最初の2つのみ表示
                            print(f"   Choice {i+1}: {choice}")
                    else:
                        print("❌ No 'choices' key found in OpenAI response!")
                        print(f"Available keys: {list(question_data.keys())}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"Raw content: {content}")
                    return None
                
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
        language: str,
        allow_multiple_correct: bool = False
    ) -> str:
        """Create an enhanced prompt with more specific instructions"""
        
        difficulty_instructions = {
            "easy": "初心者向けの基本的な概念を問う問題",
            "medium": "中級者向けの実践的な問題", 
            "hard": "上級者向けの応用・発展問題"
        }
        
        topic_instruction = f"特に「{topic}」に関連する内容で" if topic else ""
        
        # 複数正解設定に基づいた指示
        correct_answer_instruction = "3. 正解は複数ある場合もあります" if allow_multiple_correct else "3. 正解は必ず1つのみ"
        
        prompt = f"""
{category}の{difficulty_instructions[difficulty]}を作成してください。
{topic_instruction}

以下の条件に従って、JSON形式で回答してください：

**条件:**
1. 問題文は具体的で実践的な内容にする
2. 選択肢は必ず4つ作成する（この条件は絶対に守ってください）
{correct_answer_instruction}
4. 間違いの選択肢も教育的価値があるものにする
5. 解説は詳しく、なぜその答えが正しいかを説明する
6. 難易度「{difficulty}」に適した問題レベルにする

**重要: 選択肢は必ず4つ作成してください。これは必須要件です。**

**JSON形式（必ずこの形式で回答）:**
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

**注意事項:**
- choicesキーは必ず含めてください
- 4つの選択肢は必須です
- 各選択肢にはcontentとis_correctを必ず含めてください
- 必ずvalid JSONを返してください
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
            print(f"Parsing OpenAI response: {question_data}")
            
            # Validate required fields
            required_fields = ["title", "content", "explanation", "choices"]
            for field in required_fields:
                if field not in question_data:
                    print(f"❌ Missing required field: {field}")
                    print(f"Available fields: {list(question_data.keys())}")
                    return None
            
            print("✅ All required fields present")
            
            # Validate choices
            choices_data = question_data["choices"]
            if not isinstance(choices_data, list):
                print(f"❌ Choices is not a list: {type(choices_data)}")
                return None
                
            if len(choices_data) != 4:
                print(f"❌ Expected 4 choices, got {len(choices_data)}")
                return None
            
            print(f"✅ Found {len(choices_data)} choices")
            
            # Check for exactly one correct answer
            correct_count = sum(1 for choice in choices_data if choice.get("is_correct", False))
            if correct_count != 1:
                print(f"❌ Must have exactly 1 correct answer, found {correct_count}")
                print(f"Choices: {choices_data}")
                return None
            
            print("✅ Exactly one correct answer found")
            
            # Create choices
            choices = []
            for i, choice_data in enumerate(choices_data):
                if "content" not in choice_data:
                    print(f"❌ Choice {i} missing content field")
                    return None
                
                choices.append(GeneratedChoice(
                    content=choice_data["content"],
                    is_correct=choice_data.get("is_correct", False)
                ))
                
                print(f"✅ Choice {i+1}: {choice_data['content'][:50]}... (correct: {choice_data.get('is_correct', False)})")
            
            result = GeneratedQuestion(
                title=question_data["title"],
                content=question_data["content"],
                category=category,
                explanation=question_data["explanation"],
                difficulty=difficulty,
                choices=choices
            )
            
            print(f"✅ Question parsed successfully: {result.title}")
            return result
            
        except Exception as e:
            print(f"Error parsing question response: {e}")
            return None
    
    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError),
        max_tries=5,
        max_time=120
    )
    def test_connection(self) -> Dict[str, any]:
        """Test the OpenAI API connection with enhanced error handling and retries"""
        try:
            print(f"🔍 Testing OpenAI API connection with model: {self.model}")
            print(f"   API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
            
            # まずネットワーク接続をテスト
            print("🌐 Testing network connectivity to api.openai.com...")
            try:
                import socket
                socket.create_connection(("api.openai.com", 443), timeout=10)
                print("✅ Network connectivity OK")
            except Exception as network_error:
                print(f"❌ Network connectivity failed: {network_error}")
                return {
                    "success": False,
                    "error": f"ネットワーク接続エラー: {network_error}",
                    "error_type": "network",
                    "model": self.model
                }
            
            # Test with a simple request
            print("🤖 Sending test request to OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection - respond with 'OK'"}],
                max_tokens=10,
                timeout=15
            )
            
            if response and response.choices:
                response_content = response.choices[0].message.content
                print(f"✅ OpenAI API connection test successful: {response_content}")
                return {
                    "success": True,
                    "message": "接続成功",
                    "model": self.model,
                    "response": response_content[:50] if response_content else "Empty response"
                }
            else:
                print("⚠️ Connection successful but no response")
                return {
                    "success": False,
                    "error": "No response from API",
                    "model": self.model
                }
                
        except openai.APIConnectionError as e:
            error_msg = f"API接続エラー: ネットワーク接続を確認してください - {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "connection",
                "model": self.model
            }
        except openai.RateLimitError as e:
            error_msg = f"レート制限エラー: 少し待ってから再試行してください - {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "rate_limit",
                "model": self.model
            }
        except openai.AuthenticationError as e:
            error_msg = f"認証エラー: APIキーが無効または期限切れです - {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "authentication",
                "model": self.model
            }
        except openai.BadRequestError as e:
            error_msg = f"リクエストエラー: モデル名またはパラメータが無効です - {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "bad_request",
                "model": self.model
            }
        except openai.APITimeoutError as e:
            error_msg = f"タイムアウトエラー: API応答が遅すぎます - {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "timeout",
                "model": self.model
            }
        except Exception as e:
            error_msg = f"予期しないエラー: {type(e).__name__}: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unknown",
                "model": self.model
            }
    
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
                
                # プライバシー保護の確認ログ  
                print("プライバシー保護: OpenAI学習無効化ヘッダー送信完了 (汎用API)")
                
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
                print(f"ERROR: OpenAI API error on attempt {attempt + 1}: {e}")
                print(f"   エラータイプ: {type(e).__name__}")
                print(f"   エラー詳細: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"ERROR: OpenAI API error after {self.max_retries} attempts: {e}")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"ERROR: JSON decode error on attempt {attempt + 1}: {e}")
                print(f"   JSON解析失敗の可能性があります")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"ERROR: Unexpected error on attempt {attempt + 1}: {e}")
                print(f"   エラータイプ: {type(e).__name__}")
                import traceback
                print(f"   スタックトレース: {traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return None
        
        return None

    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError),
        max_tries=3,
        factor=2
    )
    def verify_question_quality(self, question_data: dict, choices_data: list) -> dict:
        """
        問題の品質・整合性をOpenAI APIで検証
        
        Args:
            question_data: 問題データ (id, title, content, explanation等)
            choices_data: 選択肢データ (list of {content, is_correct})
            
        Returns:
            dict: {
                'is_valid': bool,      # 問題が有効かどうか
                'score': int,          # 品質スコア (1-10)
                'issues': list,        # 問題点のリスト
                'recommendation': str, # 推奨アクション
                'details': str         # 詳細な説明
            }
        """
        try:
            print(f"🔍 問題検証開始: ID {question_data.get('id', 'unknown')}")
            
            # 選択肢情報の整理
            choices_text = []
            correct_choices = []
            
            for i, choice in enumerate(choices_data):
                letter = chr(65 + i)  # A, B, C, D...
                choices_text.append(f"{letter}. {choice['content']}")
                if choice['is_correct']:
                    correct_choices.append(f"{letter}")
            
            choices_str = "\n".join(choices_text)
            correct_str = "、".join(correct_choices) if correct_choices else "なし"
            
            # 検証用プロンプト
            verification_prompt = f"""
あなたはクイズ問題の品質管理専門家です。以下の問題を客観的に評価してください。

問題ID: {question_data.get('id', '不明')}
タイトル: {question_data.get('title', '不明')}
カテゴリ: {question_data.get('category', '不明')}
難易度: {question_data.get('difficulty', '不明')}

問題文:
{question_data.get('content', '')}

選択肢:
{choices_str}

正解: {correct_str}

解説:
{question_data.get('explanation', 'なし')}

以下の観点で評価してください：
1. 問題文が明確で理解しやすいか
2. 選択肢が適切で重複がないか
3. 正解が論理的に正しいか
4. 正解が選択肢の中に含まれているか
5. 解説が正解と一致しているか
6. 全体として問題として成立しているか

評価結果をJSON形式で返してください：
{{
    "is_valid": true/false,
    "score": 1-10の整数,
    "issues": ["問題点1", "問題点2", ...],
    "recommendation": "削除推奨/修正推奨/問題なし",
    "details": "詳細な説明"
}}
"""

            # API呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはクイズ問題の品質管理専門家です。問題を客観的に評価し、JSON形式で結果を返してください。"
                    },
                    {
                        "role": "user", 
                        "content": verification_prompt
                    }
                ],
                temperature=0.1,  # 一貫性のため低温度
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"📝 検証結果取得: {len(result_text)} 文字")
            
            # JSON形式の結果をパース
            try:
                # JSON部分を抽出（```json ブロックがある場合）
                if "```json" in result_text:
                    json_start = result_text.find("```json") + 7
                    json_end = result_text.find("```", json_start)
                    result_text = result_text[json_start:json_end].strip()
                elif "```" in result_text:
                    json_start = result_text.find("```") + 3
                    json_end = result_text.rfind("```")
                    result_text = result_text[json_start:json_end].strip()
                
                result = json.loads(result_text)
                
                # 結果の検証と補完
                if not isinstance(result, dict):
                    raise ValueError("結果がdict形式ではありません")
                
                # 必須フィールドの確認と補完
                result.setdefault('is_valid', True)
                result.setdefault('score', 5)
                result.setdefault('issues', [])
                result.setdefault('recommendation', '判定不明')
                result.setdefault('details', '詳細な評価結果が取得できませんでした')
                
                # スコアの正規化
                if not isinstance(result['score'], int) or result['score'] < 1 or result['score'] > 10:
                    result['score'] = 5
                
                print(f"✅ 検証完了: スコア {result['score']}/10, 有効性: {result['is_valid']}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析エラー: {e}")
                # フォールバック: テキスト解析
                return self._parse_verification_fallback(result_text)
                
        except openai.RateLimitError as e:
            print(f"⚠️ Rate limit error in verification: {e}")
            return {
                'is_valid': None,
                'score': None,
                'issues': ['API利用制限に達しました'],
                'recommendation': '後で再試行',
                'details': 'OpenAI APIの利用制限により検証できませんでした。しばらく待ってから再試行してください。'
            }
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return {
                'is_valid': None,
                'score': None,
                'issues': [f'検証エラー: {str(e)}'],
                'recommendation': '手動確認推奨',
                'details': f'問題の検証中にエラーが発生しました: {str(e)}'
            }
    
    def _parse_verification_fallback(self, text: str) -> dict:
        """JSON解析に失敗した場合のフォールバック解析"""
        try:
            # テキストから情報を抽出
            is_valid = 'false' not in text.lower() and '削除' not in text
            
            # スコアを抽出
            score = 5
            for line in text.split('\n'):
                if 'score' in line.lower() or 'スコア' in line:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        score = min(10, max(1, int(numbers[0])))
                        break
            
            # 問題点を抽出
            issues = []
            if '問題' in text or 'エラー' in text:
                issues.append('品質に問題がある可能性があります')
            
            return {
                'is_valid': is_valid,
                'score': score,
                'issues': issues,
                'recommendation': '削除推奨' if not is_valid else '要確認',
                'details': text[:200] + '...' if len(text) > 200 else text
            }
        except:
            return {
                'is_valid': None,
                'score': None,
                'issues': ['解析エラー'],
                'recommendation': '手動確認推奨',
                'details': '検証結果の解析に失敗しました'
            }

    # ...existing code...
def test_enhanced_openai_service():
    """Test the enhanced OpenAI service"""
    try:
        service = EnhancedOpenAIService()
        
        print("🧪 Testing Enhanced OpenAI Service...")
        
        # Test connection
        if service.test_connection():
            print("OK: API connection successful")
        else:
            print("ERROR: API connection failed")
            return
        
        # Test question generation
        question = service.generate_question(
            category="プログラミング基礎",
            difficulty="easy",
            topic="変数とデータ型"
        )
        
        if question:
            print("OK: Question generation successful")
            print(f"Title: {question.title}")
            print(f"Category: {question.category}")
            print(f"Difficulty: {question.difficulty}")
        else:
            print("ERROR: Question generation failed")
            
    except Exception as e:
        print(f"ERROR: Test failed: {e}")


if __name__ == "__main__":
    test_enhanced_openai_service()
