"""
過去問抽出サービス
PDFから既存の問題・選択肢・正解・解説をそのまま抽出する
"""

from typing import List, Dict, Optional, Tuple
import json
import re
from services.enhanced_openai_service import EnhancedOpenAIService


class PastQuestionExtractor:
    """過去問抽出クラス"""
    
    def __init__(self, session):
        self.session = session
        self.openai_service = EnhancedOpenAIService()
    
    def extract_past_questions_from_pdf(
        self,
        text: str,
        category: str = "過去問",
        progress_callback=None
    ) -> List[int]:
        """PDFテキストから過去問を抽出"""        
        if progress_callback:
            progress_callback("過去問PDFを分析中...", 0.1)
        
        # テキストを問題単位に分割
        questions = self._split_into_questions(text)
        
        print(f"🔍 分割結果: {len(questions)}問を検出")
        for i, q in enumerate(questions[:3]):  # 最初の3問のプレビュー
            print(f"   問題{i+1}プレビュー: {q[:100]}...")
        
        if progress_callback:
            progress_callback(f"{len(questions)}問の問題を検出しました", 0.2)
        
        generated_question_ids = []
        
        for i, question_text in enumerate(questions):
            if progress_callback:
                progress = 0.2 + (0.7 * (i + 1) / len(questions))
                progress_callback(f"問題 {i+1}/{len(questions)} を処理中...", progress)
            
            try:
                # OpenAI APIで構造化抽出
                extracted_data = self._extract_question_structure(question_text)
                
                if extracted_data:
                    # データベースに保存
                    question_id = self._save_extracted_question(
                        extracted_data, 
                        category,
                        question_number=i+1
                    )
                    
                    if question_id:
                        generated_question_ids.append(question_id)
                        
            except Exception as e:
                print(f"問題{i+1}の処理でエラー: {e}")
                continue
        
        if progress_callback:
            progress_callback("過去問抽出完了", 1.0)
        
        return generated_question_ids
    
    def _split_into_questions(self, text: str) -> List[str]:
        """テキストを問題単位に分割"""
        
        # 一般的な問題番号パターンを検索
        patterns = [
            r'問題?\s*(\d+)[.．)\s]',  # 問題1. 問題１） など
            r'第\s*(\d+)\s*問[.．\s]',  # 第1問. など
            r'Q\s*(\d+)[.．)\s]',      # Q1. Q1) など
            r'(\d+)[.．)\s]',          # 1. 1) など
        ]
        
        questions = []
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if len(matches) >= 2:  # 2問以上見つかった場合
                for i, match in enumerate(matches):
                    start_pos = match.start()
                    end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    
                    question_text = text[start_pos:end_pos].strip()
                    if len(question_text) > 50:  # 最小限の長さチェック
                        questions.append(question_text)
                
                if questions:
                    break
        
        # パターンマッチングで分割できない場合、文字数で分割
        if not questions:
            chunk_size = len(text) // max(1, len(text) // 2000)  # 2000文字程度で分割
            questions = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        return questions
    def _extract_question_structure(self, question_text: str) -> Optional[Dict]:
        """OpenAI APIで問題構造を抽出"""
        
        # 入力テキストが長すぎる場合は切り詰める（トークン制限対策）
        max_input_length = 3000  # 約750トークン相当
        if len(question_text) > max_input_length:
            question_text = question_text[:max_input_length] + "..."
            print(f"⚠️ 入力テキストを{max_input_length}文字に切り詰めました")
        
        prompt = f"""
あなたは過去問題集の専門家です。以下のテキストから、過去問の内容を正確に抽出してください。
テキストに含まれている問題文、選択肢、正解、解説をそのまま抽出し、一切改変しないでください。

【重要】必ずJSON形式で回答してください。他の形式での回答は禁止です。

【抽出ルール】
1. 問題文：そのまま抽出（問題番号は除去）
2. 選択肢：A, B, C, D または 1, 2, 3, 4 形式で抽出
3. 正解：正解の選択肢を特定
4. 解説：解説文をそのまま抽出
5. 難易度：問題の内容から推定（easy/medium/hard）

【JSON出力フォーマット】
以下の形式でのみ回答してください：

{{
    "title": "問題のタイトル（20文字以内）",
    "question": "問題文（そのまま）",
    "choices": [
        {{"text": "選択肢A", "is_correct": false}},
        {{"text": "選択肢B", "is_correct": true}},
        {{"text": "選択肢C", "is_correct": false}},
        {{"text": "選択肢D", "is_correct": false}}
    ],
    "explanation": "解説文（そのまま）",
    "difficulty": "medium"
}}

【入力テキスト】
{question_text}

【注意】JSON形式以外での回答は絶対に禁止です。必ず有効なJSONオブジェクトを返してください。
"""
        try:
            print(f"🚀 OpenAI API呼び出し開始")
            print(f"   プロンプト長: {len(prompt)} 文字")
            print(f"   入力テキスト長: {len(question_text)} 文字")
            
            response = self.openai_service.call_openai_api(
                prompt,
                max_tokens=2000,
                temperature=0.1  # 低温度で正確な抽出
            )
            
            print(f"🔍 OpenAI API Response: {response[:200]}..." if response else "❌ No response from OpenAI API")
            
            if response:
                # JSONを解析
                try:
                    data = json.loads(response)
                    print(f"✅ JSON解析成功: {data.keys()}")
                    
                    # 必須フィールドをチェック
                    required_fields = ['title', 'question', 'choices', 'explanation']
                    if all(field in data for field in required_fields):
                        # 選択肢の検証
                        if len(data['choices']) >= 2:
                            print(f"✅ データ検証成功: {len(data['choices'])}個の選択肢")
                            return data
                        else:
                            print(f"⚠️ 選択肢不足: {len(data['choices'])}個")
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        print(f"⚠️ 必須フィールド不足: {missing_fields}")
                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失敗: {e}")
                    print(f"Response content: {response[:500]}...")
                    print("🔄 フォールバック抽出を試行します")
                    # JSON解析失敗時、簡単な正規表現で抽出を試行
                    return self._fallback_extraction(question_text)
            else:
                print("❌ OpenAI APIからのレスポンスが空です")
            
        except Exception as e:
            print(f"❌ OpenAI API エラー: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_extraction(question_text)
        
        return None
    
    def _fallback_extraction(self, text: str) -> Optional[Dict]:
        """OpenAI API失敗時のフォールバック抽出"""
        
        try:
            # 簡単な正規表現パターンで抽出
            lines = text.split('\n')
            
            question_lines = []
            choices = []
            explanation_lines = []
            
            current_section = "question"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 選択肢パターンの検出
                choice_match = re.match(r'^[A-D1-4][.．)\s](.+)', line)
                if choice_match:
                    choices.append(choice_match.group(1))
                    current_section = "choices"
                    continue
                
                # 解説パターンの検出
                if re.match(r'^(解説|答え|正解|解答)[：:]', line, re.IGNORECASE):
                    current_section = "explanation"
                    explanation_lines.append(line)
                    continue
                
                # 現在のセクションに応じて追加
                if current_section == "question":
                    question_lines.append(line)
                elif current_section == "explanation":
                    explanation_lines.append(line)
            
            if question_lines and choices:
                return {
                    "title": question_lines[0][:20] + "..." if len(question_lines[0]) > 20 else question_lines[0],
                    "question": '\n'.join(question_lines),
                    "choices": [{"text": choice, "is_correct": i == 0} for i, choice in enumerate(choices)],  # 仮で最初を正解
                    "explanation": '\n'.join(explanation_lines) if explanation_lines else "解説なし",
                    "difficulty": "medium"
                }
        
        except Exception as e:
            print(f"フォールバック抽出エラー: {e}")
        
        return None
    
    def _save_extracted_question(self, data: Dict, category: str, question_number: int) -> Optional[int]:
        """抽出したデータをデータベースに保存"""
        
        try:
            from database.operations import QuestionService, ChoiceService
            
            question_service = QuestionService(self.session)
            choice_service = ChoiceService(self.session)
            
            # 問題を作成
            question = question_service.create_question(
                title=f"{category} 問題{question_number}",
                content=data['question'],
                category=category,
                explanation=data['explanation'],
                difficulty=data.get('difficulty', 'medium')
            )
            
            if question:
                # 選択肢を作成
                for i, choice_data in enumerate(data['choices']):
                    choice_service.create_choice(
                        question_id=question.id,
                        content=choice_data['text'],
                        is_correct=choice_data['is_correct'],
                        order=i + 1
                    )
                
                return question.id
        
        except Exception as e:
            print(f"データベース保存エラー: {e}")
        
        return None
