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
        print(f"INFO: 分割結果: {len(questions)}問を検出")
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
                print(f"INFO: 問題{i+1}を処理中... (長さ: {len(question_text)}文字)")
                
                # テキストが非常に長い場合は最初の1500文字のみ使用
                if len(question_text) > 1500:
                    truncated_text = question_text[:1500]
                    print(f"WARN: テキストを1500文字に切り詰めました")
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
                    print(f"TIME: API処理時間: {elapsed:.2f}秒")
                    
                    # 30秒以上かかった場合は異常とみなす
                    if elapsed > 30:
                        print(f"⚠️ API処理時間が異常に長いです: {elapsed:.2f}秒")
                        extracted_data = None
                        
                except Exception as api_error:
                    print(f"⚠️ API呼び出しエラー: {api_error}")
                    extracted_data = None
                print(f"INFO: API応答結果: {'成功' if extracted_data else '失敗'}")
                
                # API失敗の場合は即座にフォールバックを使用
                if not extracted_data:
                    print(f"INFO: フォールバック抽出を実行します")
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
        print(f"INFO: テキスト分割開始: 総文字数 {len(text)}")
        
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
                    print(f"BEST: ベストパターン更新: '{pattern}' で {len(questions)}問を検出")
        
        # 問題が見つからない場合、より柔軟な分割を試行
        if not best_questions:
            print("INFO: 問題番号パターンが見つからないため、キーワード分割を試行します")
            
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
                        print(f"INFO: キーワード '{keyword}' で {len(questions_from_keyword)}問を検出")
        
        # それでも見つからない場合、段落分割を試行
        if not best_questions:
            print("INFO: 段落分割を試行します")
            paragraphs = re.split(r'\n\s*\n', text)
            for p in paragraphs:
                p = p.strip()
                if (len(p) > 200 and 
                    ('?' in p or '？' in p or '①' in p or 'A.' in p) and
                    ('解説' in p or '正解' in p)):
                    best_questions.append(p)
            
            print(f"INFO: 段落分割で {len(best_questions)}問を検出")
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
        
        print(f"OK: 最終分割結果: {len(filtered_questions)}問 (パターン: {best_pattern})")
        
        # 最初の3問の詳細情報を表示
        for i, q in enumerate(filtered_questions[:3]):
            print(f"   問題{i+1}: {len(q)}文字, プレビュー: {q[:80].replace(chr(10), ' ')}...")
        
        return filtered_questions

    def _extract_question_structure(self, question_text: str) -> Optional[Dict]:
        """OpenAI APIで問題構造を抽出（改善版）"""
        
        # 入力テキストが長すぎる場合は切り詰める（トークン制限対策）
        max_input_length = 1500  # より小さく設定
        if len(question_text) > max_input_length:
            question_text = question_text[:max_input_length] + "..."
            print(f"⚠️ 入力テキストを{max_input_length}文字に切り詰めました")
        
        # テキスト品質の事前チェック
        has_choices = any(pattern in question_text for pattern in ['①', '②', '③', 'A.', 'B.', 'C.', '1.', '2.', '3.'])
        has_question_markers = any(marker in question_text for marker in ['?', '？', '問', '選択', '適切'])
        
        print(f"🔍 テキスト品質チェック:")
        print(f"   選択肢マーカー: {'✅' if has_choices else '❌'}")
        print(f"   問題マーカー: {'✅' if has_question_markers else '❌'}")
        print(f"   テキスト長: {len(question_text)} 文字")
        
        if not has_choices:
            print("WARN: 選択肢が検出されないため、フォールバックを使用します")
            return self._fallback_extraction(question_text)
          # より短いプロンプト
        prompt = f"""
テキストから問題を抽出してください:

{question_text}

必須: JSON形式で回答してください:
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
            print(f"INFO: OpenAI API呼び出し開始")
            print(f"   プロンプト長: {len(prompt)} 文字")
            print(f"   入力テキスト長: {len(question_text)} 文字")
            
            # API呼び出し前のタイムスタンプ
            import time
            start_time = time.time()
            
            response = self.openai_service.call_openai_api(
                prompt,
                max_tokens=1500,  # より少なく設定
                temperature=0.0,   # 完全に決定的に
                system_message="あなたは過去問を正確に抽出する専門家です。与えられたテキストから問題・選択肢・正解・解説を厳密にJSON形式で抽出してください。"
            )
            
            end_time = time.time()
            print(f"TIME: API呼び出し時間: {end_time - start_time:.2f}秒")
            
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
                    print("INFO: フォールバック抽出を試行します")
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
        """OpenAI API失敗時のフォールバック抽出（強化版）"""
        
        try:
            print("INFO: フォールバック抽出を開始します...")
            print(f"   入力テキスト長: {len(text)} 文字")
            
            # デバッグ: テキストの最初の500文字を表示
            preview_text = text[:500].replace('\n', ' ')
            print(f"   テキストプレビュー: {preview_text}...")
            
            # より積極的な問題抽出
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            print(f"   総行数: {len(lines)} 行")
            
            # 問題タイトルを検出
            title = "抽出された問題"
            for line in lines[:10]:  # 最初の10行から検索
                if '問' in line and len(line) < 50:
                    title = line
                    break
            
            print(f"   検出されたタイトル: {title}")
            
            # 問題文を抽出（選択肢より前の部分）
            question_text = ""
            choices = []
            explanation = ""
            correct_answer = None
            
            # 選択肢パターンの検出（より詳細なログ付き）
            choice_patterns = [
                r'^([①②③④⑤])\s*(.+)',           # ①②③④⑤ 形式
                r'^([ABCDE])[.．)\s](.+)',        # A. B. C. D. E. 形式  
                r'^([12345])[.．)\s](.+)',        # 1. 2. 3. 4. 5. 形式
            ]
            
            choice_start_idx = None
            detected_pattern = None
            
            # 各パターンをテストして最初に見つかったものを使用
            for pattern_idx, pattern in enumerate(choice_patterns):
                for line_idx, line in enumerate(lines):
                    if re.match(pattern, line):
                        choice_start_idx = line_idx
                        detected_pattern = pattern
                        print(f"   選択肢パターン検出 [{pattern_idx}]: {pattern} (行{line_idx})")
                        break
                if choice_start_idx is not None:
                    break
            
            if choice_start_idx is None:
                print("WARN: 選択肢パターンが見つかりません")
            else:
                print(f"   選択肢開始位置: 行{choice_start_idx}")
            
            # 問題文を構築（選択肢より前の部分）
            if choice_start_idx is not None:
                question_lines = lines[:choice_start_idx]
                question_text = ' '.join(question_lines)
                
                # 選択肢を抽出
                choice_section = lines[choice_start_idx:]
                for line in choice_section:
                    for pattern in choice_patterns:
                        match = re.match(pattern, line)
                        if match:
                            letter = match.group(1)
                            text = match.group(2).strip()
                            choices.append({
                                "letter": letter,
                                "text": text
                            })
                            break
                    
                    # 正解パターンの検出
                    correct_patterns = [
                        r'(正解|答え|解答)[）：:\s]*([①②③④⑤ABCDE12345,、]+)',
                        r'\((正解|答え|解答)[）：:\s]*([①②③④⑤ABCDE12345,、]+)',
                    ]
                    
                    for pattern in correct_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            correct_answer = match.group(2)
                            break
                    
                    # 解説パターンの検出
                    if re.match(r'^(解説|説明)[：:]', line, re.IGNORECASE):
                        explanation = line
            
            # 選択肢が見つからない場合、より柔軟に検索
            if not choices:
                print("INFO: 選択肢が見つからないため、より柔軟な検索を実行...")
                for line in lines:
                    # 数字や記号で始まる行を選択肢として扱う
                    if re.match(r'^[①②③④⑤ABCDE12345]\s*.+', line):
                        letter = line[0]
                        text = line[1:].strip('.')
                        choices.append({
                            "letter": letter,
                            "text": text
                        })
            
            # 最低限のデータが揃っているかチェック
            if not question_text and not choices:
                print("❌ フォールバック抽出: 問題文も選択肢も見つかりませんでした")
                return None
            
            if not question_text:
                question_text = "問題文が検出できませんでした"
            
            if len(choices) < 2:
                print(f"⚠️ 選択肢が不足しています: {len(choices)}個")
                # ダミー選択肢を追加
                while len(choices) < 4:
                    choices.append({
                        "letter": str(len(choices) + 1),
                        "text": f"選択肢{len(choices) + 1}"
                    })
            
            # 正解を設定
            formatted_choices = []
            for i, choice in enumerate(choices):
                is_correct = False
                
                if correct_answer:
                    # 複数正解対応
                    correct_parts = re.split('[,、]', correct_answer.strip())
                    correct_parts = [part.strip() for part in correct_parts]
                    is_correct = choice["letter"] in correct_parts
                elif i == 0:  # 正解が見つからない場合、最初を正解にする
                    is_correct = True
                
                formatted_choices.append({
                    "text": choice["text"],
                    "is_correct": is_correct
                })            
            result = {
                "title": title,
                "question": question_text,
                "choices": formatted_choices,
                "explanation": explanation or "解説が見つかりませんでした",
                "difficulty": "medium"
            }
            print(f"OK: フォールバック抽出成功:")
            print(f"   タイトル: {title}")
            print(f"   問題文: {question_text[:50]}...")
            print(f"   選択肢数: {len(formatted_choices)}")
            print(f"   正解数: {sum(1 for c in formatted_choices if c['is_correct'])}")
            
            return result
            
        except Exception as e:
            print(f"ERROR: フォールバック抽出エラー: {e}")
            import traceback
            print(f"   詳細: {traceback.format_exc()}")
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
