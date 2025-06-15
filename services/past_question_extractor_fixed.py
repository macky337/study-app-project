"""
過去問抽出サービス（改善版）
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
                print(f"📋 問題{i+1}を処理中... (長さ: {len(question_text)}文字)")
                extracted_data = self._extract_question_structure(question_text)
                
                if extracted_data:
                    print(f"✅ 問題{i+1}: 抽出成功")
                    # データベースに保存
                    question_id = self._save_extracted_question(
                        extracted_data, 
                        category,
                        question_number=i+1
                    )
                    
                    if question_id:
                        generated_question_ids.append(question_id)
                        print(f"💾 問題{i+1}: DB保存成功 (ID: {question_id})")
                    else:
                        print(f"❌ 問題{i+1}: DB保存失敗")
                else:
                    print(f"❌ 問題{i+1}: 抽出失敗 - データが不正またはAPI応答なし")
                        
            except Exception as e:
                print(f"❌ 問題{i+1}の処理でエラー: {e}")
                import traceback
                print(f"   詳細: {traceback.format_exc()}")
                continue
        
        if progress_callback:
            progress_callback("過去問抽出完了", 1.0)
        
        return generated_question_ids

    def _split_into_questions(self, text: str) -> List[str]:
        """テキストを問題単位に分割（改善版）"""
        
        # より多様な問題番号パターンを検索
        patterns = [
            r'【問\s*(\d+)】',             # 【問1】 形式
            r'問題?\s*(\d+)[.．)\s]',      # 問題1. 問題１） など
            r'第\s*(\d+)\s*問[.．\s]',     # 第1問. など
            r'Q\s*(\d+)[.．)\s]',          # Q1. Q1) など
            r'(\d+)[.．)\s]',              # 1. 1) など
        ]
        
        best_questions = []
        max_questions = 0
        
        # 各パターンを試して、最も多くの問題を検出できるパターンを選択
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if len(matches) >= 2:  # 2問以上見つかった場合
                questions = []
                for i, match in enumerate(matches):
                    start_pos = match.start()
                    end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    
                    question_text = text[start_pos:end_pos].strip()
                    if len(question_text) > 100:  # 最小限の長さチェック（より厳しく）
                        questions.append(question_text)
                
                if len(questions) > max_questions:
                    max_questions = len(questions)
                    best_questions = questions
                    print(f"🔍 パターン '{pattern}' で {len(questions)}問を検出")
        
        # 問題が見つからない場合、段落分割を試行
        if not best_questions:
            print("🔄 問題番号パターンが見つからないため、段落分割を試行します")
            paragraphs = re.split(r'\n\s*\n', text)
            for p in paragraphs:
                p = p.strip()
                if len(p) > 200 and ('?' in p or '？' in p or 'A.' in p or 'A.' in p):
                    best_questions.append(p)
            
            print(f"📄 段落分割で {len(best_questions)}問を検出")
        
        print(f"✅ 最終分割結果: {len(best_questions)}問")
        return best_questions

    def _extract_question_structure(self, question_text: str) -> Optional[Dict]:
        """OpenAI APIで問題構造を抽出（改善版）"""        
        # 入力テキストが長すぎる場合は切り詰める（トークン制限対策）
        max_input_length = 2000  # 約500トークン相当
        if len(question_text) > max_input_length:
            question_text = question_text[:max_input_length] + "..."
            print(f"⚠️ 入力テキストを{max_input_length}文字に切り詰めました")
        
        # シンプルなプロンプト
        prompt = f"""
以下のテキストから問題を抽出してJSONで返してください。

テキスト:
{question_text}

以下の形式のJSONで返してください:
{{
    "title": "問題タイトル（20文字以内）",
    "question": "問題文",
    "choices": [
        {{"text": "選択肢A", "is_correct": false}},
        {{"text": "選択肢B", "is_correct": false}},
        {{"text": "選択肢C", "is_correct": false}},
        {{"text": "選択肢D", "is_correct": true}}
    ],
    "explanation": "解説",
    "difficulty": "medium"
}}

重要: JSONのみ返してください。他の文章は不要です。
"""
        try:
            print(f"🚀 OpenAI API呼び出し開始")
            print(f"   プロンプト長: {len(prompt)} 文字")
            print(f"   入力テキスト長: {len(question_text)} 文字")
            
            response = self.openai_service.call_openai_api(
                prompt,
                max_tokens=1500,  # より少なく設定
                temperature=0.0   # 完全に決定的に
            )
            
            print(f"🔍 OpenAI API Response: {response[:500]}..." if response else "❌ No response from OpenAI API")
            
            if response:
                # レスポンスをクリーンアップ
                cleaned_response = response.strip()
                
                # マークダウンコードブロックを除去
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                cleaned_response = cleaned_response.strip()
                
                print(f"🔧 クリーンアップ後: {cleaned_response[:200]}...")
                
                # JSONを解析
                try:
                    data = json.loads(cleaned_response)
                    print(f"✅ JSON解析成功: {list(data.keys())}")
                    
                    # 必須フィールドをチェック
                    required_fields = ['title', 'question', 'choices', 'explanation']
                    missing_fields = [f for f in required_fields if f not in data]
                    
                    if missing_fields:
                        print(f"⚠️ 必須フィールド不足: {missing_fields}")
                        return self._fallback_extraction(question_text)
                    
                    # 選択肢の検証
                    if not isinstance(data.get('choices'), list) or len(data['choices']) < 2:
                        print(f"⚠️ 選択肢不足: {len(data.get('choices', []))}個")
                        return self._fallback_extraction(question_text)
                    
                    # 正解が1つだけあることを確認
                    correct_count = sum(1 for choice in data['choices'] if choice.get('is_correct'))
                    if correct_count != 1:
                        print(f"⚠️ 正解数異常: {correct_count}個（1個である必要があります）")
                        # 最初の選択肢を正解にする
                        for i, choice in enumerate(data['choices']):
                            choice['is_correct'] = (i == 0)
                    
                    print(f"✅ データ検証成功: {len(data['choices'])}個の選択肢")
                    return data
                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失敗: {e}")
                    print(f"Response content: {cleaned_response[:300]}...")
                    print("🔄 フォールバック抽出を試行します")
                    return self._fallback_extraction(question_text)
            else:
                print("❌ OpenAI APIからのレスポンスが空です")
                return self._fallback_extraction(question_text)
            
        except Exception as e:
            print(f"❌ OpenAI API エラー: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_extraction(question_text)
        
        return None

    def _fallback_extraction(self, text: str) -> Optional[Dict]:
        """OpenAI API失敗時のフォールバック抽出（改善版）"""
        
        try:
            print("🔄 フォールバック抽出を開始します...")
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            question_lines = []
            choices = []
            explanation_lines = []
            correct_answer = None
            
            current_section = "question"
            
            for line in lines:                
                # 選択肢パターンの検出（より幅広く）
                choice_match = re.match(r'^([A-D1-4])[.．)\s](.+)', line)
                if choice_match:
                    choice_letter = choice_match.group(1)
                    choice_text = choice_match.group(2).strip()
                    choices.append({
                        "letter": choice_letter, 
                        "text": choice_text
                    })
                    current_section = "choices"
                    continue
                
                # 正解パターンの検出
                correct_match = re.search(r'(正解|答え|解答)[：:\s]*([A-D1-4])', line, re.IGNORECASE)
                if correct_match:
                    correct_answer = correct_match.group(2)
                    current_section = "explanation"
                    continue
                
                # 解説パターンの検出
                if re.match(r'^(解説|説明)[：:]', line, re.IGNORECASE):
                    current_section = "explanation"
                    explanation_lines.append(line)
                    continue
                
                # 現在のセクションに応じて追加
                if current_section == "question":
                    question_lines.append(line)
                elif current_section == "explanation":
                    explanation_lines.append(line)
            
            # データの整理
            if question_lines and choices:
                # 正解を設定
                formatted_choices = []
                for choice in choices:
                    is_correct = choice["letter"] == correct_answer
                    formatted_choices.append({
                        "text": choice["text"],
                        "is_correct": is_correct
                    })
                
                # 正解が見つからない場合、最初を正解にする
                if not any(c["is_correct"] for c in formatted_choices):
                    formatted_choices[0]["is_correct"] = True
                
                result = {
                    "title": (question_lines[0][:30] + "..." if len(question_lines[0]) > 30 else question_lines[0]),
                    "question": '\n'.join(question_lines),
                    "choices": formatted_choices,
                    "explanation": '\n'.join(explanation_lines) if explanation_lines else "解説なし",
                    "difficulty": "medium"
                }
                
                print(f"✅ フォールバック抽出成功: {len(formatted_choices)}個の選択肢")
                return result
            else:
                print(f"❌ フォールバック抽出失敗: 問題={len(question_lines)}, 選択肢={len(choices)}")
        
        except Exception as e:
            print(f"❌ フォールバック抽出エラー: {e}")
        
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
