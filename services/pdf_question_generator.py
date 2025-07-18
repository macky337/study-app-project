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
        model: str = "gpt-4o-mini",
        include_explanation: bool = True,
        progress_callback=None,
        enable_duplicate_check: bool = True,
        similarity_threshold: float = 0.7,
        max_retry_attempts: int = 3,
        allow_multiple_correct: bool = False
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
                    chunk, current_questions, difficulty, category, model, include_explanation,
                    enable_duplicate_check, similarity_threshold, max_retry_attempts, allow_multiple_correct
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
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 100]
    
    def _split_by_sections(self, text: str) -> List[str]:
        """セクションで分割"""
        # 見出しパターンを検出
        section_patterns = [
            r'\n\s*[第\d]+[章節条項]\s*[^\n]*\n',  # 第1章、第1節など
            r'\n\s*\d+\.\s*[^\n]*\n',  # 1. タイトル
            r'\n\s*[A-Z]+\.\s*[^\n]*\n',  # A. タイトル
            r'\n\s*【[^】]+】\s*\n',  # 【タイトル】
            r'\n\s*■[^\n]*\n',  # ■タイトル
            r'\n\s*#+\s*[^\n]*\n'  # Markdown見出し
        ]
        
        # まず、見出しで分割を試行
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) > 1:
                sections = []
                last_end = 0
                for match in matches:
                    if last_end < match.start():
                        sections.append(text[last_end:match.start()].strip())
                    last_end = match.end()
                if last_end < len(text):
                    sections.append(text[last_end:].strip())
                return [s for s in sections if len(s.strip()) > 50]
        
        # 見出しが見つからない場合は段落で分割
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if len(p.strip()) > 50]
    
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
        category: str,
        model: str = "gpt-4o-mini",
        include_explanation: bool = True,
        enable_duplicate_check: bool = True,
        similarity_threshold: float = 0.7,
        max_retry_attempts: int = 3,
        allow_multiple_correct: bool = False
    ) -> List[int]:
        """チャンクから問題を生成"""
        
        # 指定されたモデルでOpenAIサービスを初期化
        openai_service = EnhancedOpenAIService(model_name=model)
        
        # 解説を含めるかどうかでプロンプトを調整
        explanation_instruction = "詳細な解説を含める" if include_explanation else "解説は不要"
        explanation_field = '"explanation": "正解の理由と解説"' if include_explanation else '"explanation": ""'
        
        # 複数正解に関する指示を調整
        multiple_correct_instruction = "問題によっては複数の正解が可能です" if allow_multiple_correct else "必ず1つの正解と3つの不正解を含む"
        
        prompt = f"""
以下のテキストを基に、{num_questions}個の4択問題を作成してください。

【テキスト内容】
{chunk}

【要求事項】
- 難易度: {difficulty}
- カテゴリ: {category}
- 各問題は4つの選択肢を持つ
- {multiple_correct_instruction}
- 実際のテキスト内容に基づいた問題を作成
- 問題は理解度を測るものにする
- {explanation_instruction}

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
            {explanation_field}
        }}
    ]
}}

JSONのみを出力し、他の文字は含めないでください。
"""

        try:
            # OpenAI APIで問題生成
            response = openai_service.generate_completion(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            # JSONパース
            if not response or response.strip() == "":
                print("OpenAI APIから空のレスポンスを受信しました")
                return []
            
            # レスポンスのクリーニング（マークダウンコードブロックなどを除去）
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            print(f"APIレスポンス（最初の200文字）: {cleaned_response[:200]}...")
            
            questions_data = json.loads(cleaned_response)
            
            # 問題をDBに保存
            question_ids = []
            for q_data in questions_data.get('questions', []):
                question_id = self._save_question_to_db(
                    q_data, category, difficulty,
                    enable_duplicate_check, True,  # enable_content_validation=True
                    similarity_threshold, max_retry_attempts
                )
                if question_id:
                    question_ids.append(question_id)
            
            return question_ids
            
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"レスポンス内容: {response[:500] if response else 'None'}...")
            return []
        except Exception as e:
            print(f"問題生成でエラーが発生しました: {e}")
            print(f"レスポンス: {response[:200] if response else 'None'}...")
            return []

    def _save_question_to_db(
        self,
        question_data: Dict,
        category: str,
        difficulty: str,
        enable_duplicate_check: bool,
        enable_content_validation: bool,
        similarity_threshold: float,
        max_retry_attempts: int
    ) -> Optional[int]:
        """問題をデータベースに保存"""
        
        try:
            from database.operations import QuestionService, ChoiceService
            
            question_service = QuestionService(self.session)
            choice_service = ChoiceService(self.session)
              # 重複チェック
            if enable_duplicate_check:
                duplicate_check = question_service.check_duplicate_before_creation(
                    title=question_data.get('title', '無題'),
                    content=question_data['content'],
                    category=category,
                    similarity_threshold=similarity_threshold
                )
                if duplicate_check["is_duplicate"]:
                    print(f"類似問題が既に存在するためスキップ: {question_data.get('title', '無題')} (類似度: {duplicate_check['highest_similarity']:.2f})")
                    return None
              # 問題を保存
            question = question_service.create_question(
                title=question_data.get('title', '無題'),
                content=question_data['content'],
                category=category,
                difficulty=difficulty,
                explanation=question_data.get('explanation', '')
            )
            
            if not question:
                return None
            
            question_id = question.id
            
            # 選択肢を保存
            for order, choice in enumerate(question_data['choices']):
                choice_service.create_choice(
                    question_id=question_id,
                    content=choice['text'],
                    is_correct=choice['is_correct'],
                    order_num=order + 1
                )
            return question_id
        
        except Exception as e:
            print(f"DB保存エラー: {e}")
            return None