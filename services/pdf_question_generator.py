"""
PDF問題生成サービス
PDFテキストから複数選択問題を生成する
"""

from typing import List, Dict, Optional
import json
import re
from services.enhanced_openai_service import EnhancedOpenAIService


class PDFQuestionGenerator:
    """PDF問題生成クラス"""
    
    def __init__(self, session, model_name="gpt-4o-mini"):
        self.session = session
        self.openai_service = EnhancedOpenAIService(model_name=model_name)
    
    def generate_questions_from_pdf(
        self,
        text: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        category: str = "PDF教材",
        progress_callback=None,
        enable_duplicate_check: bool = True,
        similarity_threshold: float = 0.7,
        max_retry_attempts: int = 3
    ) -> List[int]:
        """PDFテキストから問題を生成"""
        
        if progress_callback:
            progress_callback("PDFテキストを分析中...", 0.1)
        
        # テキストをチャンクに分割
        chunks = self._split_text_into_chunks(text, max_chunk_size=3000)
        
        if progress_callback:
            progress_callback(f"テキストを{len(chunks)}個のセクションに分割しました", 0.2)
        
        generated_question_ids = []
        questions_per_chunk = max(1, num_questions // len(chunks))
        
        for i, chunk in enumerate(chunks):
            if len(generated_question_ids) >= num_questions:
                break
            
            if progress_callback:
                progress = 0.2 + (0.7 * (i + 1) / len(chunks))
                progress_callback(f"セクション {i+1}/{len(chunks)} から問題生成中...", progress)
            
            # このチャンクから生成する問題数を決定
            remaining_questions = num_questions - len(generated_question_ids)
            remaining_chunks = len(chunks) - i
            current_questions = min(questions_per_chunk, remaining_questions, 
                                   max(1, remaining_questions // remaining_chunks))
            
            try:
                chunk_questions = self._generate_questions_from_chunk(
                    chunk, current_questions, difficulty, category,
                    enable_duplicate_check, similarity_threshold, max_retry_attempts
                )
                generated_question_ids.extend(chunk_questions)
            except Exception as e:
                print(f"チャンク{i+1}の問題生成でエラー: {e}")
                continue
        
        if progress_callback:
            progress_callback("問題生成完了！", 1.0)
        
        return generated_question_ids[:num_questions]  # 指定数に制限
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 3000) -> List[str]:
        """テキストを意味のあるチャンクに分割"""
        
        # セクション分割（見出しや段落で分割）
        sections = self._split_by_sections(text)
        
        chunks = []
        current_chunk = ""
        
        for section in sections:
            # セクションが大きすぎる場合は文で分割
            if len(section) > max_chunk_size:
                sentences = self._split_by_sentences(section)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence
            else:
                if len(current_chunk) + len(section) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = section
                else:
                    current_chunk += "\n\n" + section
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 100]  # 短すぎるチャンクを除外
    
    def _split_by_sections(self, text: str) -> List[str]:
        """見出しや段落でテキストを分割"""
        # 一般的な見出しパターンで分割
        section_patterns = [
            r'\n\s*第?\d+[章節条項]\s*[^\n]*\n',  # 第1章、第1節など
            r'\n\s*\d+\.\s*[^\n]*\n',           # 1. タイトル
            r'\n\s*[A-Z][^\n]{10,50}\n',        # 大文字で始まる見出し
            r'\n\s*[\u3042-\u3096\u30A1-\u30FA\u4e00-\u9faf]{5,30}\n'  # 日本語見出し
        ]
        
        # まず大きな段落で分割
        paragraphs = re.split(r'\n\s*\n\s*\n', text)
        
        # 段落が長すぎる場合はさらに分割
        sections = []
        for paragraph in paragraphs:
            if len(paragraph) > 1500:
                # 見出しパターンで分割を試みる
                for pattern in section_patterns:
                    if re.search(pattern, paragraph):
                        subsections = re.split(pattern, paragraph)
                        sections.extend([s for s in subsections if len(s.strip()) > 50])
                        break
                else:
                    sections.append(paragraph)
            else:
                sections.append(paragraph)
        
        return [s.strip() for s in sections if len(s.strip()) > 50]
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """文で分割"""
        # 日本語と英語の文末を検出
        sentence_endings = r'[。！？\.\!\?]\s*'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _generate_questions_from_chunk(
        self,
        chunk: str,
        num_questions: int,
        difficulty: str,
        category: str
    ) -> List[int]:
        """チャンクから問題を生成"""
        
        prompt = f"""
以下のテキストを基に、{num_questions}個の4択問題を作成してください。

【テキスト内容】
{chunk}

【要求事項】
- 難易度: {difficulty}
- カテゴリ: {category}
- 各問題は4つの選択肢を持つ
- 必ず1つの正解と3つの不正解を含む
- 実際のテキスト内容に基づいた問題を作成
- 問題は理解度を測るものにする

【出力形式】（JSON形式で回答）
{{
    "questions": [
        {{
            "title": "問題のタイトル",
            "content": "問題文",
            "choices": [
                {{"text": "選択肢A", "is_correct": false}},
                {{"text": "選択肢B", "is_correct": true}},
                {{"text": "選択肢C", "is_correct": false}},
                {{"text": "選択肢D", "is_correct": false}}
            ],
            "explanation": "正解の理由と解説"
        }}
    ]
}}

JSONのみを出力し、他の文字は含めないでください。
"""

        try:
            response = self.openai_service.generate_completion(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            # JSONパース
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                questions_data = json.loads(json_str)
            else:
                raise ValueError("有効なJSONが見つかりません")
              # データベースに保存
            question_ids = []
            for q_data in questions_data.get('questions', []):
                question_id = self._save_question_to_db(q_data, category, difficulty)
                if question_id:
                    question_ids.append(question_id)
            
            return question_ids
            
        except Exception as e:
            print(f"問題生成エラー: {e}")
            return []
    
    def _save_question_to_db(
        self, 
        question_data: Dict, 
        category: str,
        difficulty: str,
        enable_duplicate_check: bool = True,
        enable_content_validation: bool = True,
        similarity_threshold: float = 0.7,
        max_retry_attempts: int = 3
    ) -> Optional[int]:
        """生成された問題をデータベースに保存（内容検証機能付き）"""
        try:
            from database.operations import QuestionService, ChoiceService
            
            question_service = QuestionService(self.session)
            choice_service = ChoiceService(self.session)
            
            # 問題データの前処理
            title = question_data.get('title', 'PDF生成問題')
            content = question_data['content']
            explanation = question_data.get('explanation', '')
            choices_data = question_data.get('choices', [])
            
            # 内容検証（有効な場合）
            if enable_content_validation:
                # 一時的な問題と選択肢を作成して検証
                temp_question = type('TempQuestion', (), {
                    'title': title,
                    'content': content,
                    'category': category,
                    'explanation': explanation,
                    'difficulty': difficulty
                })()
                
                temp_choices = []
                for choice_data in choices_data:
                    temp_choice = type('TempChoice', (), {
                        'text': choice_data.get('content', choice_data.get('text', '')),
                        'is_correct': choice_data.get('is_correct', False)
                    })()
                    temp_choices.append(temp_choice)
                
                try:
                    validation_result = question_service.validate_question_and_choices(temp_question, temp_choices)
                    
                    # 重大なエラーがある場合はスキップ
                    if not validation_result.get("valid", True):
                        print(f"⚠️ PDF問題の内容検証失敗: {validation_result.get('errors', [])}")
                        return None
                    
                    # 警告がある場合はログ出力
                    if validation_result.get("warnings"):
                        print(f"📋 PDF問題の内容検証警告: {validation_result['warnings']}")
                        
                except Exception as e:
                    print(f"⚠️ PDF問題の内容検証でエラー: {e}")
                    # 検証エラーの場合は継続
            
            # 重複チェック
            if enable_duplicate_check:
                # 重複チェック付きで問題を作成
                if hasattr(question_service, 'create_question_with_duplicate_check'):
                    creation_result = question_service.create_question_with_duplicate_check(
                        title=title,
                        content=content,
                        category=category,
                        explanation=explanation,
                        difficulty=difficulty,
                        force_create=False,  # 重複の場合は作成しない
                        similarity_threshold=similarity_threshold                    )
                    
                    if not creation_result.get("success", False):
                        print(f"INFO: 重複のためスキップ - {creation_result.get('message', 'Unknown reason')}")
                        return None
                    
                    question = creation_result["question"]
                else:
                    # フォールバック: 通常の作成
                    question = question_service.create_question(
                        title=title,
                        content=content,
                        category=category,
                        explanation=explanation,
                        difficulty=difficulty
                    )
            else:
                # 重複チェックなしで作成
                question = question_service.create_question(
                    title=title,
                    content=content,
                    category=category,
                    explanation=explanation,
                    difficulty=difficulty
                )
            
            # 選択肢を作成
            choices = question_data.get('choices', [])
            for i, choice_data in enumerate(choices):
                choice_service.create_choice(
                    question_id=question.id,
                    content=choice_data['text'],
                    is_correct=choice_data['is_correct'],
                    order_num=i + 1
                )
            
            return question.id
            
        except Exception as e:
            print(f"データベース保存エラー: {e}")
            return None
    
    def validate_openai_connection(self) -> Dict[str, any]:
        """OpenAI接続確認"""
        return self.openai_service.test_connection()
