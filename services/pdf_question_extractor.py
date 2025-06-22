"""
PDF問題抽出サービス
PDFから既存の問題・選択肢・解答・解説を抽出して問題を作成する
"""

from typing import List, Dict, Optional, Tuple
import re
import json
from dataclasses import dataclass


@dataclass
class ExtractedQuestion:
    """抽出された問題データ"""
    title: str
    content: str
    choices: List[Dict[str, any]]  # [{"content": str, "is_correct": bool}]
    explanation: str
    difficulty: str = "medium"
    
    
class PDFQuestionExtractor:
    """PDF問題抽出クラス"""
    
    def __init__(self, session):
        self.session = session
    
    def extract_questions_from_pdf(
        self,
        text: str,
        category: str = "PDF教材",
        max_questions: int = None,
        progress_callback=None,
        enable_duplicate_check: bool = True,
        similarity_threshold: float = 0.8
    ) -> List[int]:
        """PDFテキストから問題を抽出してデータベースに保存"""
        
        if progress_callback:
            progress_callback("PDFテキストを解析中...", 0.1)
        
        # 問題を抽出
        extracted_questions = self._extract_questions(text)
        
        if not extracted_questions:
            print("PDF内に問題が見つかりませんでした")
            return []
        
        # 最大問題数が指定されている場合は制限
        if max_questions and len(extracted_questions) > max_questions:
            extracted_questions = extracted_questions[:max_questions]
            print(f"📝 最大問題数制限により {max_questions} 問に制限しました")
        
        if progress_callback:
            progress_callback(f"{len(extracted_questions)}個の問題を検出しました", 0.3)
        
        # データベースに保存
        saved_question_ids = []
        
        for i, question in enumerate(extracted_questions):
            if progress_callback:
                progress = 0.3 + (0.6 * (i + 1) / len(extracted_questions))
                progress_callback(f"問題 {i+1}/{len(extracted_questions)} を保存中...", progress)
            
            try:
                question_id = self._save_question_to_db(
                    question, category, "medium",  # デフォルト難易度
                    enable_duplicate_check, similarity_threshold
                )
                if question_id:
                    saved_question_ids.append(question_id)
                    print(f"✅ 問題 {i+1} 保存完了 (ID: {question_id})")
                else:
                    print(f"⚠️ 問題 {i+1} スキップ（重複または保存エラー）")
            except Exception as e:
                print(f"❌ 問題 {i+1} 保存エラー: {e}")
                continue
        
        if progress_callback:
            progress_callback(f"完了！ {len(saved_question_ids)}個の問題を保存しました", 1.0)
        
        return saved_question_ids
    
    def _extract_questions(self, text: str) -> List[ExtractedQuestion]:
        """テキストから問題を抽出"""
        
        questions = []
        
        # 複数の抽出パターンを試行
        patterns = [
            self._extract_pattern_mixed,  # 混在パターン（新追加）
            self._extract_pattern1,  # 問題番号形式（問1、問2、等）
            self._extract_pattern2,  # Qxx形式（Q1、Q2、等）
            self._extract_pattern3,  # 番号形式（1.、2.、等）
            self._extract_pattern4,  # 全般的なパターン
        ]
        
        for pattern_func in patterns:
            try:
                extracted = pattern_func(text)
                if extracted:
                    questions.extend(extracted)
                    print(f"✅ パターン '{pattern_func.__name__}' で {len(extracted)} 個の問題を抽出")
            except Exception as e:
                print(f"⚠️ パターン '{pattern_func.__name__}' でエラー: {e}")
                continue
        
        # 重複を除去
        unique_questions = self._remove_duplicates(questions)
        print(f"📊 抽出結果: {len(questions)} 個 → 重複除去後 {len(unique_questions)} 個")
        
        return unique_questions
    
    def _extract_pattern1(self, text: str) -> List[ExtractedQuestion]:
        """問1、問2形式の問題を抽出"""
        
        questions = []
        
        # 問題の区切りパターン
        question_pattern = r'問\s*(\d+)[.．、\s]*([^問]+?)(?=問\s*\d+|$)'
        matches = re.findall(question_pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            question_num, question_content = match
            
            try:
                extracted = self._parse_question_content(question_content, f"問{question_num}")
                if extracted:
                    questions.append(extracted)
            except Exception as e:
                print(f"問{question_num}の解析エラー: {e}")
                continue
        
        return questions
    
    def _extract_pattern2(self, text: str) -> List[ExtractedQuestion]:
        """Q1、Q2形式の問題を抽出"""
        
        questions = []
        
        # Q形式のパターン
        question_pattern = r'Q\s*(\d+)[.．\s]*([^Q]+?)(?=Q\s*\d+|$)'
        matches = re.findall(question_pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            question_num, question_content = match
            
            try:
                extracted = self._parse_question_content(question_content, f"Q{question_num}")
                if extracted:
                    questions.append(extracted)
            except Exception as e:
                print(f"Q{question_num}の解析エラー: {e}")
                continue
        
        return questions
    
    def _extract_pattern3(self, text: str) -> List[ExtractedQuestion]:
        """1.、2.形式の問題を抽出"""
        
        questions = []
        
        # 番号形式のパターン
        question_pattern = r'(\d+)[.．\s]+([^0-9]+?)(?=\d+[.．]|$)'
        matches = re.findall(question_pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            question_num, question_content = match
            
            # 短すぎる場合はスキップ
            if len(question_content.strip()) < 50:
                continue
            
            try:
                extracted = self._parse_question_content(question_content, f"問題{question_num}")
                if extracted:
                    questions.append(extracted)
            except Exception as e:
                print(f"問題{question_num}の解析エラー: {e}")
                continue
        
        return questions
    
    def _extract_pattern4(self, text: str) -> List[ExtractedQuestion]:
        """一般的なパターンで問題を抽出"""
        
        questions = []
        
        # 選択肢パターンを含む段落を問題として抽出
        # (1)(2)(3)(4) または ア、イ、ウ、エ または A、B、C、D パターン
        choice_patterns = [
            r'\([1-4]\)',  # (1)(2)(3)(4)
            r'[ア-エ]',     # ア、イ、ウ、エ
            r'[A-D]',      # A、B、C、D
            r'[①-④]',      # ①②③④
        ]
        
        for pattern in choice_patterns:
            # このパターンの選択肢を含む段落を抽出
            paragraphs = text.split('\n\n')
            
            for i, paragraph in enumerate(paragraphs):
                if len(re.findall(pattern, paragraph)) >= 3:  # 3つ以上の選択肢がある
                    try:
                        extracted = self._parse_question_content(paragraph, f"問題{i+1}")
                        if extracted and len(extracted.choices) >= 3:
                            questions.append(extracted)
                    except Exception as e:
                        continue
        
        return questions
    
    def _parse_question_content(self, content: str, title: str) -> Optional[ExtractedQuestion]:
        """問題内容を解析して構造化"""
        
        content = content.strip()
        
        # 問題文と選択肢を分離
        question_text, choices, explanation = self._separate_question_parts(content)
        
        if not question_text or len(choices) < 2:
            return None
        
        return ExtractedQuestion(
            title=title,
            content=question_text,
            choices=choices,
            explanation=explanation,
            difficulty="medium"
        )
    
    def _separate_question_parts(self, content: str) -> Tuple[str, List[Dict], str]:
        """問題内容を問題文、選択肢、解説に分離"""
        
        # 選択肢のパターンを検索
        choice_patterns = [
            (r'\(([1-4])\)\s*([^\n\r\(]+)', 'number'),  # (1) 選択肢
            (r'([ア-エ])[.．\s]*([^\n\r]+)', 'katakana'),  # ア. 選択肢
            (r'([A-D])[.．\s]*([^\n\r]+)', 'alphabet'),   # A. 選択肢
            (r'([①-④])\s*([^\n\r]+)', 'circle_number'),  # ① 選択肢
        ]
        
        choices = []
        question_text = content
        explanation = ""
        
        for pattern, pattern_type in choice_patterns:
            matches = re.findall(pattern, content)
            if len(matches) >= 2:  # 2つ以上の選択肢が見つかった
                choices = []
                for match in matches:
                    choice_text = match[1].strip()
                    if choice_text:
                        choices.append({
                            "content": choice_text,
                            "is_correct": False  # 初期値、後で正解を特定
                        })
                
                # 問題文から選択肢部分を除去
                choice_section_start = content.find(matches[0][0])
                if choice_section_start > 0:
                    question_text = content[:choice_section_start].strip()
                
                break
        
        # 正解を特定
        if choices:
            correct_answer = self._find_correct_answer(content)
            if correct_answer:
                self._mark_correct_choice(choices, correct_answer, pattern_type if 'pattern_type' in locals() else 'number')
        
        # 解説を抽出
        explanation = self._extract_explanation(content)
        
        return question_text, choices, explanation
    
    def _find_correct_answer(self, content: str) -> Optional[str]:
        """正解を特定（複数正解にも対応）"""
        
        # 複数正解パターン
        multiple_correct_patterns = [
            r'正解[：:]\s*([1-6ア-オA-F①-⑥、・,\s]+)',
            r'答え[：:]\s*([1-6ア-オA-F①-⑥、・,\s]+)',
            r'解答[：:]\s*([1-6ア-オA-F①-⑥、・,\s]+)',
            r'正答[：:]\s*([1-6ア-オA-F①-⑥、・,\s]+)',
        ]
        
        for pattern in multiple_correct_patterns:
            match = re.search(pattern, content)
            if match:
                answer_text = match.group(1)
                # 複数の正解が含まれているかチェック
                if any(separator in answer_text for separator in ['、', '・', ',', 'と']):
                    return answer_text  # 複数正解として返す
                else:
                    return answer_text.strip()  # 単一正解
        
        # 単一正解パターン（従来通り）
        single_correct_patterns = [
            r'\[([1-6ア-オA-F①-⑥])\]',
            r'（([1-6ア-オA-F①-⑥])）',
        ]
        
        for pattern in single_correct_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _mark_correct_choice(self, choices: List[Dict], correct_answer: str, pattern_type: str):
        """正解の選択肢をマーク（複数正解対応）"""
        
        # 複数正解の場合を処理
        if any(separator in correct_answer for separator in ['、', '・', ',', 'と']):
            # 複数正解を分割
            separators = ['、', '・', ',', 'と']
            correct_answers = [correct_answer]
            
            for sep in separators:
                temp = []
                for ans in correct_answers:
                    temp.extend(ans.split(sep))
                correct_answers = temp
            
            # 各正解をクリーンアップ
            correct_answers = [ans.strip() for ans in correct_answers if ans.strip()]
            
            # 各正解について選択肢をマーク
            for correct in correct_answers:
                correct_index = self._get_choice_index(correct, pattern_type)
                if correct_index is not None and 0 <= correct_index < len(choices):
                    choices[correct_index]["is_correct"] = True
        else:
            # 単一正解の場合
            correct_index = self._get_choice_index(correct_answer, pattern_type)
            if correct_index is not None and 0 <= correct_index < len(choices):
                choices[correct_index]["is_correct"] = True
            else:
                # 正解が特定できない場合は最初の選択肢を正解にする
                if choices:
                    choices[0]["is_correct"] = True
    
    def _get_choice_index(self, correct_answer: str, pattern_type: str) -> Optional[int]:
        """正解文字から選択肢インデックスを取得"""
        
        if pattern_type == 'number':
            try:
                return int(correct_answer) - 1
            except:
                return None
        elif pattern_type == 'katakana':
            katakana_map = {'ア': 0, 'イ': 1, 'ウ': 2, 'エ': 3, 'オ': 4}
            return katakana_map.get(correct_answer)
        elif pattern_type == 'alphabet':
            alphabet_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5}
            return alphabet_map.get(correct_answer.upper())
        elif pattern_type == 'circle_number':
            circle_map = {'①': 0, '②': 1, '③': 2, '④': 3, '⑤': 4, '⑥': 5}
            return circle_map.get(correct_answer)
        
        return None
    
    def _extract_explanation(self, content: str) -> str:
        """解説を抽出"""
        
        explanation_patterns = [
            r'解説[：:\s]*([^問Q\n\r]+)',
            r'説明[：:\s]*([^問Q\n\r]+)',
            r'解答解説[：:\s]*([^問Q\n\r]+)',
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _remove_duplicates(self, questions: List[ExtractedQuestion]) -> List[ExtractedQuestion]:
        """重複する問題を除去（改善版）"""
        
        unique_questions = []
        seen_contents = set()
        seen_choice_sets = set()
        
        for question in questions:
            # 問題文の最初の50文字で重複判定
            content_key = question.content[:50].strip()
            
            # 選択肢の組み合わせでも重複判定
            choice_set = tuple(sorted([choice["content"][:30] for choice in question.choices]))
            
            # 問題文または選択肢が重複していない場合のみ追加
            if content_key not in seen_contents and choice_set not in seen_choice_sets:
                # さらに、問題文が選択肢と同じでないかチェック
                is_question_text_valid = True
                for choice in question.choices:
                    if question.content.strip() == choice["content"].strip():
                        is_question_text_valid = False
                        break
                
                if is_question_text_valid and len(question.content.strip()) > 10:
                    seen_contents.add(content_key)
                    seen_choice_sets.add(choice_set)
                    unique_questions.append(question)
        
        return unique_questions
    
    def _save_question_to_db(
        self,
        question: ExtractedQuestion,
        category: str,
        difficulty: str,
        enable_duplicate_check: bool,
        similarity_threshold: float
    ) -> Optional[int]:
        """問題をデータベースに保存"""
        
        try:
            from database.operations import QuestionService, ChoiceService
            
            question_service = QuestionService(self.session)
            choice_service = ChoiceService(self.session)
            
            # 重複チェック
            if enable_duplicate_check:
                duplicate_check = question_service.check_duplicate_before_creation(
                    title=question.title,
                    content=question.content,
                    category=category,
                    similarity_threshold=similarity_threshold
                )
                if duplicate_check["is_duplicate"]:
                    print(f"類似問題が既に存在するためスキップ: {question.title} (類似度: {duplicate_check['highest_similarity']:.2f})")
                    return None
            
            # 問題を保存
            saved_question = question_service.create_question(
                title=question.title,
                content=question.content,
                category=category,
                difficulty=difficulty,
                explanation=question.explanation
            )
            
            # 選択肢を保存
            for i, choice in enumerate(question.choices):
                choice_service.create_choice(
                    question_id=saved_question.id,
                    content=choice["content"],
                    is_correct=choice["is_correct"],
                    order_num=i + 1
                )
            
            return saved_question.id
            
        except Exception as e:
            print(f"DB保存エラー: {e}")
            return None
    
    def _extract_pattern_mixed(self, text: str) -> List[ExtractedQuestion]:
        """混在パターンで問題を抽出（PDFから抽出された複雑なテキスト用）"""
        
        questions = []
        
        # 選択肢を含む段落を検出してそれぞれを問題として処理
        lines = text.split('\n')
        current_question = []
        question_count = 0
        
        # 選択肢のパターンを定義（より柔軟に）
        choice_patterns = [
            r'^[A-F][.．\s]',  # A. B. C. D. E. F.
            r'^[ア-オ][.．\s]',  # ア. イ. ウ. エ. オ.
            r'^\([1-6]\)',      # (1) (2) (3) (4) (5) (6)
            r'^[①-⑥]',         # ① ② ③ ④ ⑤ ⑥
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 選択肢のパターンを検出
            is_choice = any(re.match(pattern, line) for pattern in choice_patterns)
            
            if is_choice:
                current_question.append(line)
            else:
                # 選択肢以外の行
                if current_question:  # 既に選択肢が蓄積されている場合
                    # 現在の問題を処理
                    if len(current_question) >= 3:  # 3つ以上の選択肢がある
                        question_text = self._find_question_text(lines, i - len(current_question) - 5, i - len(current_question))
                        if question_text:
                            try:
                                # 解説用の後続行を拡張（正解・解説を含む可能性）
                                explanation_candidates = lines[i:i+20]  # より多くの行を含める
                                extracted = self._create_question_from_parts(
                                    question_text, 
                                    current_question, 
                                    f"問題 {question_count + 1}",
                                    explanation_candidates  
                                )
                                if extracted:
                                    questions.append(extracted)
                                    question_count += 1
                            except Exception as e:
                                print(f"問題解析エラー: {e}")
                    
                    current_question = []
                else:
                    # 新しい問題の開始の可能性
                    if len(line) > 20 and ('か。' in line or '？' in line or 'どれか' in line):
                        # 問題文らしい行を検出
                        pass
        
        # 最後の問題を処理
        if current_question and len(current_question) >= 3:
            question_text = self._find_question_text(lines, len(lines) - len(current_question) - 5, len(lines) - len(current_question))
            if question_text:
                try:
                    extracted = self._create_question_from_parts(
                        question_text, 
                        current_question, 
                        f"問題 {question_count + 1}",
                        []
                    )
                    if extracted:
                        questions.append(extracted)
                except Exception as e:
                    print(f"最後の問題解析エラー: {e}")
        
        return questions
    
    def _find_question_text(self, lines: List[str], start_idx: int, end_idx: int) -> str:
        """指定範囲から問題文を検索（解説も含む）"""
        
        start_idx = max(0, start_idx)
        end_idx = min(len(lines), end_idx)
        
        question_candidates = []
        
        # 問題文候補を検索
        for i in range(start_idx, end_idx):
            line = lines[i].strip()
            if len(line) > 20 and any(keyword in line for keyword in ['か。', '？', 'どれか', '正しい', '適切', '説明', '選べ']):
                question_candidates.append(line)
        
        if question_candidates:
            return question_candidates[-1]  # 最後（最も近い）候補を選択
        
        # 候補がない場合は、前の行から適当な長さの文を探す
        for i in range(end_idx - 1, start_idx - 1, -1):
            line = lines[i].strip()
            if len(line) > 15:
                return line
        
        return ""
    
    def _create_question_from_parts(self, question_text: str, choice_lines: List[str], title: str, explanation_lines: List[str]) -> Optional[ExtractedQuestion]:
        """問題文、選択肢、解説から問題オブジェクトを作成"""
        
        if not question_text or len(choice_lines) < 2:
            return None
        
        # 選択肢を解析
        choices = []
        choice_letters = []
        
        for line in choice_lines:
            line = line.strip()
            
            # 選択肢のパターンマッチング
            for pattern, letter_type in [
                (r'^([A-F])[.．\s]+(.+)', 'alphabet'),
                (r'^([ア-オ])[.．\s]+(.+)', 'katakana'),
                (r'^\(([1-6])\)\s*(.+)', 'number'),
                (r'^([①-⑥])\s*(.+)', 'circle'),
            ]:
                match = re.match(pattern, line)
                if match:
                    letter = match.group(1)
                    content = match.group(2).strip()
                    if content:
                        choices.append({
                            "content": content,
                            "is_correct": False
                        })
                        choice_letters.append((letter, letter_type))
                    break
        
        if len(choices) < 2:
            return None
        
        # 解説を抽出
        explanation = ""
        explanation_text = ""
        if explanation_lines:
            explanation_text = ' '.join(line.strip() for line in explanation_lines[:10])  # より多くの行を確認
            explanation = self._extract_explanation(explanation_text)
        
        # 正解を特定（解説部分も含めて検索）
        all_text = question_text + ' ' + ' '.join(choice_lines) + ' ' + explanation_text
        correct_answer = self._find_correct_answer(all_text)
        
        if correct_answer and choice_letters:
            self._mark_correct_choice_advanced(choices, choice_letters, correct_answer)
        else:
            # 正解が特定できない場合でも、問題テキスト内に正解情報があるかチェック
            question_correct = self._find_correct_answer(question_text)
            if question_correct and choice_letters:
                self._mark_correct_choice_advanced(choices, choice_letters, question_correct)
            elif choices:
                # それでも見つからない場合は最初の選択肢を正解にする
                choices[0]["is_correct"] = True
        
        return ExtractedQuestion(
            title=title,
            content=question_text,
            choices=choices,
            explanation=explanation,
            difficulty="medium"
        )
    
    def _mark_correct_choice_advanced(self, choices: List[Dict], choice_letters: List[Tuple[str, str]], correct_answer: str):
        """高度な正解マーキング（複数正解対応）"""
        
        # 複数正解の場合を処理
        if any(separator in correct_answer for separator in ['、', '・', ',', 'と']):
            # 複数正解を分割
            separators = ['、', '・', ',', 'と']
            correct_answers = [correct_answer]
            
            for sep in separators:
                temp = []
                for ans in correct_answers:
                    temp.extend(ans.split(sep))
                correct_answers = temp
            
            # 各正解をクリーンアップ
            correct_answers = [ans.strip() for ans in correct_answers if ans.strip()]
            
            # 各正解について選択肢をマーク
            for correct in correct_answers:
                for i, (letter, letter_type) in enumerate(choice_letters):
                    if self._is_correct_match(letter, letter_type, correct) and i < len(choices):
                        choices[i]["is_correct"] = True
        else:
            # 単一正解の場合
            for i, (letter, letter_type) in enumerate(choice_letters):
                if self._is_correct_match(letter, letter_type, correct_answer) and i < len(choices):
                    choices[i]["is_correct"] = True
                    break
    
    def _is_correct_match(self, letter: str, letter_type: str, correct_answer: str) -> bool:
        """選択肢と正解の一致判定"""
        
        correct_answer = correct_answer.strip()
        
        if letter_type == 'alphabet' and correct_answer.upper() == letter.upper():
            return True
        elif letter_type == 'katakana' and correct_answer == letter:
            return True
        elif letter_type == 'number' and correct_answer == letter:
            return True
        elif letter_type == 'circle':
            circle_map = {'①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5', '⑥': '6'}
            if correct_answer == circle_map.get(letter):
                return True
            # 逆マッピングも試す
            reverse_circle_map = {'1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥'}
            if correct_answer == letter or reverse_circle_map.get(correct_answer) == letter:
                return True
        
        return False
