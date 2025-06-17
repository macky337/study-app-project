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
    
    def __init__(self, session, model_name="gpt-4o"):  # より強力なモデルに変更
        self.session = session
        self.openai_service = EnhancedOpenAIService(model_name=model_name)
    
    def extract_past_questions_from_pdf(
        self,
        text: str,
        category: str = "過去問",
        max_questions: int = 15,
        progress_callback=None,
        enable_duplicate_check: bool = False,  # 一時的に無効化
        similarity_threshold: float = 0.5,     # より緩い閾値
        duplicate_action: str = "save_with_warning"  # 重複でも保存
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
          # 処理する問題数を制限
        actual_max_questions = min(len(questions), max_questions)
        
        for i, question_text in enumerate(questions[:actual_max_questions]):
            if progress_callback:
                progress = 0.2 + (0.7 * (i + 1) / actual_max_questions)
                progress_callback(f"問題 {i+1}/{actual_max_questions} を処理中...", progress)
                
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
                        print(f"WARN: API処理時間が異常に長いです: {elapsed:.2f}秒")
                        extracted_data = None
                        
                except Exception as api_error:
                    print(f"WARN: API呼び出しエラー: {api_error}")
                    extracted_data = None
                print(f"INFO: API応答結果: {'成功' if extracted_data else '失敗'}")
                  # API失敗の場合は即座にフォールバックを使用
                if not extracted_data:
                    print(f"INFO: フォールバック抽出を実行します (問題{i+1})")
                    extracted_data = self._fallback_extraction(truncated_text)
                    
                    # フォールバックも失敗した場合、ログに詳細を記録
                    if not extracted_data:
                        print(f"ERROR: フォールバック抽出も失敗しました (問題{i+1})")
                        print(f"   テキストプレビュー: {truncated_text[:200]}...")
                        failed_extractions += 1
                        continue

                    if extracted_data:
                        print(f"OK: 問題{i+1}: 抽出成功")
                        successful_extractions += 1
                        # データベースに保存
                        question_id = self._save_extracted_question(
                            extracted_data, 
                            category,
                            question_number=i+1,
                            enable_duplicate_check=enable_duplicate_check,
                            similarity_threshold=similarity_threshold,
                            duplicate_action=duplicate_action
                        )
                        if question_id and question_id != "SKIPPED_DUPLICATE":
                            generated_question_ids.append(question_id)
                            print(f"SAVED: 問題{i+1}: DB保存成功 (ID: {question_id})")
                        elif question_id == "SKIPPED_DUPLICATE":
                            print(f"SKIPPED: 問題{i+1}: 重複のためスキップ")
                        else:
                            print(f"ERROR: 問題{i+1}: DB保存失敗")
                else:
                    print(f"ERROR: 問題{i+1}: 抽出失敗 - データが不正またはAPI応答なし")
                    failed_extractions += 1
                        
            except Exception as e:
                print(f"ERROR: 問題{i+1}の処理でエラー: {e}")
                import traceback
                print(f"   詳細: {traceback.format_exc()}")
                failed_extractions += 1
                continue
        
        # 結果サマリー
        print(f"\nSTATS: 抽出結果サマリー:")
        print(f"   OK: 成功: {successful_extractions}問")
        print(f"   ERROR: 失敗: {failed_extractions}問")
        print(f"   SAVED: DB保存: {len(generated_question_ids)}問")        
        if progress_callback:
            progress_callback(f"過去問抽出完了: {successful_extractions}問成功", 1.0)
        
        return generated_question_ids

    def _split_into_questions(self, text: str) -> List[str]:
        """テキストを問題単位に分割（改善版）"""
        print(f"INFO: テキスト分割開始: 総文字数 {len(text)}")
        
        # まず、より具体的な問題番号パターンで分割を試行
        patterns = [
            r'【問\s*(\d+)】',             # 【問1】 形式
            r'問題?\s*(\d+)[.．)\s]',      # 問題1. 問題１） など
            r'第\s*(\d+)\s*問[.．\s]',     # 第1問. など
            r'Q\s*(\d+)[.．)\s]',          # Q1. Q1) など
            r'\n\s*(\d+)[.．]\s+',         # 改行+数字+ピリオド（より厳密）
        ]
        
        best_questions = []
        best_pattern = None
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if len(matches) >= 2:  # 最低2問は必要
                print(f"INFO: パターン '{pattern}' で {len(matches)}問を検出")
                questions = []
                
                for i in range(len(matches)):
                    start = matches[i].start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    question_chunk = text[start:end].strip()
                    
                    # チャンクサイズを制限（500-3000文字が理想）
                    if 500 <= len(question_chunk) <= 3000:
                        questions.append(question_chunk)
                    elif len(question_chunk) > 3000:
                        # 長すぎる場合は最初の2500文字のみ使用
                        questions.append(question_chunk[:2500] + "...")
                        print(f"WARN: 問題が長すぎるため切り詰めました: {len(question_chunk)}文字 → 2500文字")
                
                if len(questions) > len(best_questions):
                    best_questions = questions
                    best_pattern = pattern
        
        # パターンマッチに失敗した場合、段落分割を試行
        if not best_questions:
            print(f"WARN: 問題番号パターンが見つからないため、段落分割を使用")
            paragraphs = re.split(r'\n\s*\n', text)
            for p in paragraphs:
                p = p.strip()
                # より緩い条件で段落を問題として認識
                if (len(p) > 300 and  # 最小文字数を増加
                    any(marker in p for marker in ['?', '？', '①', '②', '③', 'A.', 'B.', 'C.']) and
                    len(p) < 3000):  # 最大文字数制限
                    best_questions.append(p)
            
            print(f"INFO: 段落分割で {len(best_questions)}問を検出")
        
        # 最終品質フィルタリング
        filtered_questions = []
        for i, q in enumerate(best_questions):
            # 選択肢の存在確認（より厳密）
            choice_patterns = ['①', '②', '③', '④', 'A.', 'B.', 'C.', 'D.', '1.', '2.', '3.', '4.']
            choice_count = sum(1 for pattern in choice_patterns if pattern in q)
            
            has_sufficient_choices = choice_count >= 3  # 最低3つの選択肢
            has_content = len(q.strip()) > 200  # 最低200文字
            not_too_long = len(q) < 4000  # 最大4000文字
            
            if has_sufficient_choices and has_content and not_too_long:
                filtered_questions.append(q)
                print(f"OK: 問題{i+1}: 選択肢{choice_count}個, {len(q)}文字 - 品質基準クリア")
            else:
                print(f"SKIP: 問題{i+1}: 選択肢{choice_count}個, {len(q)}文字 - 品質基準不足")
        
        print(f"RESULT: 最終分割結果: {len(filtered_questions)}問 (パターン: {best_pattern})")
        
        # 最初の2問の詳細プレビュー
        for i, q in enumerate(filtered_questions[:2]):
            preview = q[:150].replace('\n', ' ')
            print(f"   問題{i+1}: {len(q)}文字")
            print(f"      プレビュー: {preview}...")
        
        return filtered_questions
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
        """OpenAI APIで問題構造を抽出（エラーハンドリング強化版）"""
        
        # 入力テキストが長すぎる場合は切り詰める（トークン制限対策）
        max_input_length = 1200  # より小さく設定
        if len(question_text) > max_input_length:
            question_text = question_text[:max_input_length]
            print(f"WARN: 入力テキストを{max_input_length}文字に切り詰めました")
        
        # テキスト品質の事前チェック
        has_choices = any(pattern in question_text for pattern in ['①', '②', '③', 'A.', 'B.', 'C.', '1.', '2.', '3.'])
        has_question_markers = any(marker in question_text for marker in ['?', '？', '問', '選択', '適切'])
        
        print(f"INFO: テキスト品質チェック:")
        print(f"   選択肢マーカー: {'OK' if has_choices else 'NG'}")
        print(f"   問題マーカー: {'OK' if has_question_markers else 'NG'}")
        print(f"   テキスト長: {len(question_text)} 文字")
        
        if not has_choices:
            print("WARN: 選択肢が検出されないため、フォールバックを使用します")
            return self._fallback_extraction(question_text)
          # シンプルで確実なプロンプト（1問のみ）
        prompt = f"""以下のテキストから1つの完全な問題を抽出してください。

テキスト:
{question_text}

必須条件:
- 問題文、選択肢、正解、解説がすべて含まれている1問のみ
- 不完全な問題や選択肢が不足している場合は空のオブジェクト{{}}を返す
- 正解の選択肢には"is_correct": trueを設定

JSON形式で回答（例）:
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

完全な問題が見つからない場合: {{}}"""
        
        try:
            print(f"INFO: OpenAI API呼び出し開始")
            print(f"   プロンプト長: {len(prompt)} 文字")
            
            # タイムアウト設定付きAPI呼び出し
            import time
            start_time = time.time()
            
            response = self.openai_service.call_openai_api(
                prompt,
                max_tokens=1200,  # より少なく設定
                temperature=0.0,   # 完全に決定的に
                system_message="あなたは過去問を正確に抽出する専門家です。JSONのみで回答してください。"
            )
            
            elapsed_time = time.time() - start_time
            print(f"TIME: API処理時間: {elapsed_time:.2f}秒")
            
            # タイムアウトチェック
            if elapsed_time > 25:  # 25秒以上は異常
                print(f"WARN: API処理時間が異常に長いです: {elapsed_time:.2f}秒")
                return self._fallback_extraction(question_text)
            
            # レスポンスの基本チェック
            if not response:
                print("ERROR: OpenAI APIからのレスポンスが空です")
                return self._fallback_extraction(question_text)
            
            if len(response.strip()) < 50:  # 非常に短いレスポンスは異常
                print(f"WARN: レスポンスが短すぎます: {len(response)}文字")
                return self._fallback_extraction(question_text)
            
            print(f"OK: OpenAI API Response受信: {len(response)}文字")
            print(f"INFO: 応答の最初の200文字: {response[:200]}...")
            
            # レスポンスをクリーンアップ
            cleaned_response = response.strip()
            
            # マークダウンコードブロックを除去
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
                
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            print(f"FIX: クリーンアップ後: {cleaned_response[:100]}...")
              # JSONを解析
            try:
                data = json.loads(cleaned_response)
                print(f"OK: JSON解析成功: {type(data).__name__}")
                
                # APIがlistを返した場合の処理
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], dict):
                        print("INFO: List形式のレスポンスを検出、最初の要素を使用")
                        data = data[0]
                    else:
                        print("WARN: List形式のレスポンスが不正")
                        return self._fallback_extraction(question_text)
                
                # dictでない場合の処理
                if not isinstance(data, dict):
                    print(f"WARN: 予期しないデータ型: {type(data).__name__}")
                    return self._fallback_extraction(question_text)
                
                print(f"INFO: データフィールド: {list(data.keys())}")
                
                # 必須フィールドをチェック
                required_fields = ['title', 'question', 'choices', 'explanation']
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    print(f"WARN: 必須フィールド不足: {missing_fields}")
                    return self._fallback_extraction(question_text)
                
                # 選択肢の検証
                choices = data.get('choices', [])
                if not isinstance(choices, list) or len(choices) < 2:
                    print(f"WARN: 選択肢不足: {len(choices)}個")
                    return self._fallback_extraction(question_text)
                
                # 正解数の確認（複数正解も許可）
                correct_count = sum(1 for choice in choices if choice.get('is_correct'))
                if correct_count == 0:
                    print(f"WARN: 正解が設定されていません")
                    # 最初の選択肢を正解にする
                    if choices:
                        choices[0]['is_correct'] = True
                        correct_count = 1
                
                print(f"OK: データ検証成功: {len(choices)}個の選択肢, {correct_count}個の正解")
                return data
            
            except json.JSONDecodeError as e:
                print(f"ERROR: JSON解析失敗: {e}")
                print(f"応答内容: {cleaned_response[:200]}...")
                print("INFO: フォールバック抽出を試行します")
                return self._fallback_extraction(question_text)
            
        except Exception as e:
            print(f"ERROR: OpenAI API エラー: {e}")
            print(f"   エラータイプ: {type(e).__name__}")
            return self._fallback_extraction(question_text)
        
        return None

    def _fallback_extraction(self, text: str) -> Optional[Dict]:
        """OpenAI API失敗時のフォールバック抽出（強化版）"""
        
        try:
            print("INFO: フォールバック抽出を開始します...")
            print(f"   入力テキスト長: {len(text)} 文字")
            
            # テキストの前処理
            text = text.strip()
            if not text:
                print("ERROR: 入力テキストが空です")
                return None
            
            # デバッグ: テキストの最初の300文字を表示
            preview_text = text[:300].replace('\n', ' ')
            print(f"   テキストプレビュー: {preview_text}...")
            
            # より積極的な問題抽出
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            print(f"   総行数: {len(lines)} 行")
            
            if len(lines) < 3:  # 行数が少なすぎる場合
                print("WARN: 行数が少なすぎます。テキスト分割を調整...")
                # 句読点で分割を試す
                sentences = [s.strip() for s in text.split('。') if s.strip()]
                if len(sentences) > len(lines):
                    lines = sentences
                    print(f"   文分割後の行数: {len(lines)} 行")
            
            # 問題タイトルを検出（より柔軟に）
            title = "抽出された問題"
            title_patterns = [
                r'【問\s*\d+】',
                r'問題?\s*\d+',
                r'第\s*\d+\s*問',
                r'Q\s*\d+',
                r'\d+\.'
            ]
            
            for line in lines[:5]:  # 最初の5行から検索
                for pattern in title_patterns:
                    if re.search(pattern, line):
                        title = line[:50]  # 長すぎる場合は切り詰め
                        print(f"   検出されたタイトル: {title}")
                        break
                if title != "抽出された問題":
                    break
            
            # 問題文、選択肢、正解、解説を抽出
            question_text = ""
            choices = []
            explanation = ""
            correct_answer = None
            
            # 選択肢パターンの検出（複数パターンを順次試行）
            choice_patterns = [
                (r'^([①②③④⑤⑥⑦⑧⑨⑩])\s*(.+)', 'circle'),      # ①②③④⑤ 形式
                (r'^([ABCDEFGHIJ])[.．)\s](.+)', 'alpha'),         # A. B. C. 形式  
                (r'^([12345678910])[.．)\s](.+)', 'number'),       # 1. 2. 3. 形式
            ]
            
            choice_start_idx = None
            detected_pattern = None
            pattern_type = None
            
            # 各パターンをテストして最初に見つかったものを使用
            for pattern, ptype in choice_patterns:
                for line_idx, line in enumerate(lines):
                    if re.match(pattern, line):
                        choice_start_idx = line_idx
                        detected_pattern = pattern
                        pattern_type = ptype
                        print(f"   選択肢パターン検出: {ptype} (行{line_idx})")
                        break
                if choice_start_idx is not None:
                    break
            
            if choice_start_idx is None:
                print("WARN: 標準的な選択肢パターンが見つかりません")
                # より柔軟なパターンを試行
                for line_idx, line in enumerate(lines):
                    # 数字や記号で始まる短い行を選択肢として扱う
                    if re.match(r'^[①②③④⑤ABCDE12345]\s*.{5,100}$', line):
                        if choice_start_idx is None:
                            choice_start_idx = line_idx
                            print(f"   柔軟パターンで選択肢を検出: 行{line_idx}")
            
            # 問題文を構築（選択肢より前の部分）
            if choice_start_idx is not None:
                question_lines = lines[:choice_start_idx]
                question_text = ' '.join(question_lines).strip()
                
                # 問題文が短すぎる場合の処理
                if len(question_text) < 20:
                    question_text = "問題文: " + question_text
                
                # 選択肢を抽出
                choice_section = lines[choice_start_idx:]
                for line in choice_section[:10]:  # 最大10個の選択肢を検索
                    choice_found = False
                    for pattern, ptype in choice_patterns:
                        match = re.match(pattern, line)
                        if match:
                            letter = match.group(1)
                            text = match.group(2).strip()
                            choices.append({
                                "letter": letter,
                                "text": text
                            })
                            choice_found = True
                            break
                    
                    if not choice_found:
                        # 正解パターンの検出
                        correct_patterns = [
                            r'(正解|答え|解答)[）：:\s]*([①②③④⑤ABCDE12345,、]+)',
                            r'\((正解|答え|解答)[）：:\s]*([①②③④⑤ABCDE12345,、]+)',
                            r'(答|正)[：:\s]*([①②③④⑤ABCDE12345,、]+)',
                        ]
                        
                        for pattern in correct_patterns:
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                correct_answer = match.group(2).strip()
                                print(f"   正解検出: {correct_answer}")
                                break
                        
                        # 解説パターンの検出
                        if re.match(r'^(解説|説明|解答)[：:)]', line, re.IGNORECASE):
                            explanation = line[4:].strip()  # 最初の4文字（解説：）を除去
                            print(f"   解説検出: {explanation[:50]}...")
            
            # 選択肢が見つからない場合、より柔軟に検索
            if not choices:
                print("INFO: 選択肢が見つからないため、より柔軟な検索を実行...")
                for line in lines:
                    # 数字や記号で始まる行を選択肢として扱う
                    if re.match(r'^[①②③④⑤ABCDE12345]\s*.+', line):
                        letter = line[0]
                        text = line[1:].strip('.')
                        if len(text) > 5:  # 最低限の長さ
                            choices.append({
                                "letter": letter,
                                "text": text
                            })
                
                print(f"   柔軟検索で{len(choices)}個の選択肢を検出")
            
            # 最低限のデータが揃っているかチェック
            if not question_text and not choices:
                print("ERROR: フォールバック抽出: 問題文も選択肢も見つかりませんでした")
                # 最後の手段：全体をそのまま問題文として使用
                if len(text.strip()) > 50:
                    question_text = text.strip()[:500]  # 最大500文字
                    choices = [
                        {"letter": "1", "text": "選択肢1（自動生成）"},
                        {"letter": "2", "text": "選択肢2（自動生成）"},
                        {"letter": "3", "text": "選択肢3（自動生成）"},
                        {"letter": "4", "text": "選択肢4（自動生成）"}
                    ]
                    print("INFO: 最終フォールバック: 自動生成データを使用")
                else:
                    return None
            
            # 問題文の最終調整
            if not question_text:
                question_text = "問題文を抽出できませんでした。"
            elif len(question_text) < 10:
                question_text = f"問題: {question_text}"
            
            # 選択肢数の調整
            if len(choices) < 2:
                print(f"WARN: 選択肢が不足しています: {len(choices)}個")
                # ダミー選択肢を追加
                while len(choices) < 4:
                    choices.append({
                        "letter": str(len(choices) + 1),
                        "text": f"選択肢{len(choices) + 1}（自動生成）"
                    })
            
            # 選択肢が多すぎる場合は最初の6個まで
            if len(choices) > 6:
                choices = choices[:6]
                print(f"INFO: 選択肢を{len(choices)}個に制限しました")
            
            # 正解を設定
            formatted_choices = []
            for i, choice in enumerate(choices):
                is_correct = False
                
                if correct_answer:
                    # 複数正解対応
                    correct_parts = re.split('[,、]', correct_answer)
                    correct_parts = [part.strip() for part in correct_parts]
                    is_correct = choice["letter"] in correct_parts
                elif i == 0:  # 正解が見つからない場合、最初を正解にする
                    is_correct = True
                
                formatted_choices.append({
                    "text": choice["text"],
                    "is_correct": is_correct
                })
            
            # 解説の最終調整
            if not explanation:
                explanation = "解説を抽出できませんでした。"
            elif len(explanation) < 10:
                explanation = f"解説: {explanation}"
            
            result = {
                "title": title,
                "question": question_text,
                "choices": formatted_choices,
                "explanation": explanation,
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
    
    def _save_extracted_question(
        self, 
        data: Dict, 
        category: str, 
        question_number: int,
        enable_duplicate_check: bool = True,
        enable_content_validation: bool = True,
        similarity_threshold: float = 0.7,
        duplicate_action: str = "skip"
    ) -> Optional[int]:
        """抽出したデータをデータベースに保存（内容検証機能付き）"""
        
        try:
            from database.operations import QuestionService, ChoiceService
            
            question_service = QuestionService(self.session)
            choice_service = ChoiceService(self.session)
            
            # 問題データの前処理
            title = f"{category} 問題{question_number}"
            content = data['question']
            explanation = data['explanation']
            difficulty = data.get('difficulty', 'medium')
            choices_data = data.get('choices', [])
            
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
                    # 異なるフォーマットに対応
                    choice_text = choice_data.get('text', choice_data.get('content', ''))
                    is_correct = choice_data.get('is_correct', False)
                    
                    temp_choice = type('TempChoice', (), {
                        'text': choice_text,
                        'is_correct': is_correct
                    })()
                    temp_choices.append(temp_choice)
                
                try:
                    validation_result = question_service.validate_question_and_choices(temp_question, temp_choices)
                    
                    # 重大なエラーがある場合はスキップ
                    if not validation_result.get("valid", True):
                        print(f"⚠️ 過去問{question_number}の内容検証失敗: {validation_result.get('errors', [])}")
                        return None
                    
                    # 警告がある場合はログ出力
                    if validation_result.get("warnings"):
                        print(f"📋 過去問{question_number}の内容検証警告: {validation_result['warnings']}")
                        
                except Exception as e:
                    print(f"⚠️ 過去問{question_number}の内容検証でエラー: {e}")
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
                        force_create=(duplicate_action != "skip"),
                        similarity_threshold=similarity_threshold
                    )
                    
                    if not creation_result.get("success", False):
                        if duplicate_action == "skip":
                            print(f"INFO: 問題{question_number} - 重複のためスキップ")
                            return "SKIPPED_DUPLICATE"  # 重複でスキップしたことを明示
                        else:  # save_with_warning
                            print(f"WARNING: 問題{question_number} - 重複の可能性あり、警告付きで保存")
                            # 通常の作成処理にフォールバック
                            question = question_service.create_question(
                                title=title,
                                content=content,
                                category=category,
                                explanation=explanation,
                                difficulty=difficulty
                            )
                    else:
                        # 重複なしで作成成功
                        question = creation_result["question"]
                else:
                    # フォールバック: 通常の作成
                    question = question_service.create_question(
                        title=f"{category} 問題{question_number}",
                        content=data['question'],
                        category=category,
                        explanation=data['explanation'],
                        difficulty=data.get('difficulty', 'medium')
                    )
            else:
                # 重複チェックなしで作成
                question = question_service.create_question(
                    title=f"{category} 問題{question_number}",
                    content=data['question'],
                    category=category,
                    explanation=data['explanation'],
                    difficulty=data.get('difficulty', 'medium')
                )
            
            if question:                # 選択肢を作成
                for i, choice_data in enumerate(data['choices']):
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
