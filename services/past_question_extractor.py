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
        """PDFテキストから過去問を抽出（改善版）"""        
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
        successful_extractions = 0
        failed_extractions = 0
        
        # 処理する問題数を制限（大量PDFの場合）
        max_questions = min(len(questions), 20)  # 最大20問まで
        
        for i, question_text in enumerate(questions[:max_questions]):
            if progress_callback:
                progress = 0.2 + (0.7 * (i + 1) / max_questions)
                progress_callback(f"問題 {i+1}/{max_questions} を処理中...", progress)
                
            try:
                print(f"📋 問題{i+1}を処理中... (長さ: {len(question_text)}文字)")
                
                # テキストが非常に長い場合は最初の1500文字のみ使用
                if len(question_text) > 1500:
                    truncated_text = question_text[:1500]
                    print(f"⚠️ テキストを1500文字に切り詰めました")
                else:
                    truncated_text = question_text
                
                # デバッグ: 問題テキストの最初の200文字を表示
                preview_text = truncated_text[:200].replace('\n', ' ')
                print(f"   テキストプレビュー: {preview_text}...")
                
                # OpenAI APIで構造化抽出（タイムアウト付き）
                extracted_data = None
                try:
                    import time
                    start_time = time.time()
                    extracted_data = self._extract_question_structure(truncated_text)
                    elapsed = time.time() - start_time
                    print(f"⏱️ API処理時間: {elapsed:.2f}秒")
                    
                    # 30秒以上かかった場合は異常とみなす
                    if elapsed > 30:
                        print(f"⚠️ API処理時間が異常に長いです: {elapsed:.2f}秒")
                        extracted_data = None
                        
                except Exception as api_error:
                    print(f"⚠️ API呼び出しエラー: {api_error}")
                    extracted_data = None
                
                print(f"🔍 API応答結果: {'成功' if extracted_data else '失敗'}")
                
                # API失敗の場合は即座にフォールバックを使用
                if not extracted_data:
                    print(f"🔄 フォールバック抽出を実行します")
                    extracted_data = self._fallback_extraction(truncated_text)
                
                if extracted_data:
                    print(f"✅ 問題{i+1}: 抽出成功")
                    successful_extractions += 1
                    
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
                    failed_extractions += 1
                        
            except Exception as e:
                print(f"❌ 問題{i+1}の処理でエラー: {e}")
                import traceback
                print(f"   詳細: {traceback.format_exc()}")
                failed_extractions += 1
                continue
        
        # 結果サマリー
        print(f"\n📊 抽出結果サマリー:")
        print(f"   ✅ 成功: {successful_extractions}問")
        print(f"   ❌ 失敗: {failed_extractions}問")
        print(f"   💾 DB保存: {len(generated_question_ids)}問")
        
        if progress_callback:
            progress_callback(f"過去問抽出完了: {successful_extractions}問成功", 1.0)
        
        return generated_question_ids

    def _split_into_questions(self, text: str) -> List[str]:
        """テキストを問題単位に分割（改善版）"""
        
        print(f"🔍 テキスト分割開始: 総文字数 {len(text)}")
        
        # より多様な問題番号パターンを検索
        patterns = [
            r'【問\s*(\d+)】',             # 【問1】 形式
            r'問題?\s*(\d+)[.．)\s]',      # 問題1. 問題１） など
            r'第\s*(\d+)\s*問[.．\s]',     # 第1問. など
            r'Q\s*(\d+)[.．)\s]',          # Q1. Q1) など
            r'(\d+)[.．\s]',               # 1. など（より厳しく）
        ]
        
        best_questions = []
        max_questions = 0
        best_pattern = None
        
        # 各パターンを試して、最も多くの問題を検出できるパターンを選択
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            print(f"   パターン '{pattern}': {len(matches)}個のマッチ")
            
            if len(matches) >= 2:  # 2問以上見つかった場合
                questions = []
                for i, match in enumerate(matches):
                    start_pos = match.start()
                    end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    
                    question_text = text[start_pos:end_pos].strip()
                    
                    # 最小限の長さチェック（50文字以上で選択肢がある）
                    if (len(question_text) > 50 and 
                        ('①' in question_text or 'A.' in question_text or 
                         '1.' in question_text or '解説' in question_text)):
                        questions.append(question_text)
                
                if len(questions) > max_questions:
                    max_questions = len(questions)
                    best_questions = questions
                    best_pattern = pattern
                    print(f"🎯 ベストパターン更新: '{pattern}' で {len(questions)}問を検出")
        
        # 問題が見つからない場合、より柔軟な分割を試行
        if not best_questions:
            print("🔄 問題番号パターンが見つからないため、キーワード分割を試行します")
            
            # キーワードベースの分割
            split_keywords = ['問題', '【問', 'Q.', 'Question', '設問']
            for keyword in split_keywords:
                parts = text.split(keyword)
                if len(parts) > 2:
                    questions_from_keyword = []
                    for i, part in enumerate(parts[1:], 1):  # 最初の部分はスキップ
                        question_text = (keyword + part).strip()
                        if (len(question_text) > 100 and 
                            ('①' in question_text or 'A.' in question_text)):
                            questions_from_keyword.append(question_text)
                    
                    if len(questions_from_keyword) > len(best_questions):
                        best_questions = questions_from_keyword
                        print(f"📄 キーワード '{keyword}' で {len(questions_from_keyword)}問を検出")
        
        # それでも見つからない場合、段落分割を試行
        if not best_questions:
            print("🔄 段落分割を試行します")
            paragraphs = re.split(r'\n\s*\n', text)
            for p in paragraphs:
                p = p.strip()
                if (len(p) > 200 and 
                    ('?' in p or '？' in p or '①' in p or 'A.' in p) and
                    ('解説' in p or '正解' in p)):
                    best_questions.append(p)
            
            print(f"📄 段落分割で {len(best_questions)}問を検出")
        
        # 最終的にフィルタリング（質の向上）
        filtered_questions = []
        for i, q in enumerate(best_questions):
            # より厳格な品質チェック
            has_choices = ('①' in q or 'A.' in q or '1.' in q)
            has_content = len(q.strip()) > 30
            not_too_long = len(q) < 5000  # 非常に長いものは除外
            
            if has_choices and has_content and not_too_long:
                filtered_questions.append(q)
            else:
                print(f"   問題{i+1}をフィルタリング: 品質基準を満たさず")
        
        print(f"✅ 最終分割結果: {len(filtered_questions)}問 (パターン: {best_pattern})")
        
        # 最初の3問の詳細情報を表示
        for i, q in enumerate(filtered_questions[:3]):
            print(f"   問題{i+1}: {len(q)}文字, プレビュー: {q[:80].replace(chr(10), ' ')}...")
        
        return filtered_questions

    def _extract_question_structure(self, question_text: str) -> Optional[Dict]:
        """OpenAI APIで問題構造を抽出（改善版）"""          # 入力テキストが長すぎる場合は切り詰める（トークン制限対策）
        max_input_length = 1500  # より小さく設定
        if len(question_text) > max_input_length:
            question_text = question_text[:max_input_length] + "..."
            print(f"⚠️ 入力テキストを{max_input_length}文字に切り詰めました")
          # より短いプロンプト
        prompt = f"""
問題テキストから選択肢問題を抽出してください:

{question_text}

JSON形式で回答:
{{
    "title": "問題タイトル",
    "question": "問題文",
    "choices": [
        {{"text": "選択肢1", "is_correct": false}},
        {{"text": "選択肢2", "is_correct": true}},
        {{"text": "選択肢3", "is_correct": false}},
        {{"text": "選択肢4", "is_correct": false}}
    ],
    "explanation": "解説"
}}

JSONのみ返してください。"""
        try:
            print(f"🚀 OpenAI API呼び出し開始")
            print(f"   プロンプト長: {len(prompt)} 文字")
            print(f"   入力テキスト長: {len(question_text)} 文字")
            
            # API呼び出し前のタイムスタンプ
            import time
            start_time = time.time()
            
            response = self.openai_service.call_openai_api(
                prompt,
                max_tokens=1500,  # より少なく設定
                temperature=0.0   # 完全に決定的に
            )
            
            end_time = time.time()
            print(f"⏱️ API呼び出し時間: {end_time - start_time:.2f}秒")
            
            if response is None:
                print("❌ OpenAI APIからのレスポンスがNone")
                return self._fallback_extraction(question_text)
            elif response == "":
                print("❌ OpenAI APIからのレスポンスが空文字")
                return self._fallback_extraction(question_text)
            else:
                print(f"✅ OpenAI API Response受信: {len(response)}文字")
                print(f"🔍 応答の最初の500文字: {response[:500]}...")
            
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
        """OpenAI API失敗時のフォールバック抽出（大幅改善版）"""
        
        try:
            print("🔄 フォールバック抽出を開始します...")
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            question_lines = []
            choices = []
            explanation_lines = []
            correct_answer = None
            
            current_section = "question"
            
            for line in lines:
                # 選択肢パターンの検出（改良版）
                choice_patterns = [
                    r'^([①②③④])\s*(.+)',     # ①②③④ 形式
                    r'^([ABCD])[.．)\s](.+)',  # A. B. C. D. 形式
                    r'^([1234])[.．)\s](.+)',  # 1. 2. 3. 4. 形式
                ]
                
                choice_found = False
                for pattern in choice_patterns:
                    choice_match = re.match(pattern, line)
                    if choice_match:
                        choice_letter = choice_match.group(1)
                        choice_text = choice_match.group(2).strip()
                        choices.append({
                            "letter": choice_letter, 
                            "text": choice_text
                        })
                        current_section = "choices"
                        choice_found = True
                        break
                
                if choice_found:
                    continue
                
                # 正解パターンの検出（改良版）
                correct_patterns = [
                    r'(正解|答え|解答)[）：:\s]*([①②③④ABCD1234,、]+)',
                    r'\((正解|答え|解答)[）：:\s]*([①②③④ABCD1234,、]+)',
                ]
                
                for pattern in correct_patterns:
                    correct_match = re.search(pattern, line, re.IGNORECASE)
                    if correct_match:
                        correct_answer = correct_match.group(2)
                        current_section = "explanation"
                        break
                
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
                    is_correct = False
                    
                    # 複数正解の場合の処理を改善
                    if correct_answer:
                        # 複数正解（②,④ や ②、④ など）
                        correct_parts = re.split('[,、]', correct_answer.strip())
                        correct_parts = [part.strip() for part in correct_parts]
                        is_correct = choice["letter"] in correct_parts
                    
                    formatted_choices.append({
                        "text": choice["text"],
                        "is_correct": is_correct
                    })
                
                # 正解が見つからない場合、最初を正解にする
                if not any(c["is_correct"] for c in formatted_choices) and formatted_choices:
                    formatted_choices[0]["is_correct"] = True
                
                result = {
                    "title": (question_lines[0][:30] + "..." if len(question_lines[0]) > 30 else question_lines[0]),
                    "question": '\n'.join(question_lines),
                    "choices": formatted_choices,
                    "explanation": '\n'.join(explanation_lines) if explanation_lines else "解説なし",
                    "difficulty": "medium"
                }
                
                print(f"✅ フォールバック抽出成功: {len(formatted_choices)}個の選択肢")
                correct_count = sum(1 for c in formatted_choices if c["is_correct"])
                print(f"   正解数: {correct_count}個, 検出した正解: {correct_answer}")
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
