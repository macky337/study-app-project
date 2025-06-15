#!/usr/bin/env python3
"""
過去問抽出の緊急修正版
フォールバック機能を強化
"""

def test_question_fallback():
    """フォールバック抽出のテスト"""
    
    print("🔧 フォールバック抽出テスト")
    print("=" * 50)
    
    # 実際のPDFテキストのサンプル
    sample_text = """
【問1】
名刺の交換マナーについて､適切なものをすべて選べ。
① いすに座っている時に名刺交換が始まったら､すぐに立ち上がりテーブル越しに名刺を差し出し､交換する
② 名刺は文字に指がかからないように持ち､名刺の文字が相手に向くようにして差し出す
③ 相手の名刺を受け取る際は片手で受け取り､すぐに名刺入れにしまう
④ 名刺交換の際には､役職が高い方から渡していく
(正解）②,④
(解説）①名刺交換はテーブル越しには行わない｡テーブルを回り込み相手の正面に立って交換する。
③受け取る際は原則両手で受け取り､すぐにはしまわずにしばらく手元に置いて確認する。
"""
    
    print(f"📝 テストテキスト: {len(sample_text)}文字")
    
    import re
    
    try:
        # フォールバック抽出の実装
        lines = [line.strip() for line in sample_text.split('\n') if line.strip()]
        
        question_lines = []
        choices = []
        explanation_lines = []
        correct_answer = None
        
        current_section = "question"
        
        print(f"📋 処理する行数: {len(lines)}")
        
        for line_num, line in enumerate(lines):
            print(f"行{line_num+1}: {line[:50]}...")
            
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
                    print(f"   ✅ 選択肢検出: {choice_letter} - {choice_text[:30]}...")
                    break
            
            if choice_found:
                continue
            
            # 正解パターンの検出（改良版）
            correct_patterns = [
                r'(正解|答え|解答)[）：:\s]*([①②③④ABCD1234])',
                r'\((正解|答え|解答)[）：:\s]*([①②③④ABCD1234])',
            ]
            
            for pattern in correct_patterns:
                correct_match = re.search(pattern, line, re.IGNORECASE)
                if correct_match:
                    correct_answer = correct_match.group(2)
                    current_section = "explanation"
                    print(f"   ✅ 正解検出: {correct_answer}")
                    break
            
            # 解説パターンの検出
            if re.match(r'^(解説|説明)[：:]', line, re.IGNORECASE):
                current_section = "explanation"
                explanation_lines.append(line)
                print(f"   ✅ 解説開始")
                continue
            
            # 現在のセクションに応じて追加
            if current_section == "question":
                question_lines.append(line)
                print(f"   📝 問題文追加")
            elif current_section == "explanation":
                explanation_lines.append(line)
                print(f"   📖 解説追加")
        
        print(f"\n📊 抽出結果:")
        print(f"   問題文: {len(question_lines)}行")
        print(f"   選択肢: {len(choices)}個")
        print(f"   正解: {correct_answer}")
        print(f"   解説: {len(explanation_lines)}行")
        
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
            
            # 正解が見つからない場合、②④形式の場合は複数正解に対応
            if not any(c["is_correct"] for c in formatted_choices) and correct_answer:
                # 複数正解の場合（②,④など）
                if ',' in correct_answer or '、' in correct_answer:
                    correct_parts = re.split('[,、]', correct_answer)
                    for choice in formatted_choices:
                        if choice["letter"] in correct_parts:
                            choice["is_correct"] = True
                else:
                    # 単一正解が見つからない場合、最初を正解にする
                    formatted_choices[0]["is_correct"] = True
            
            result = {
                "title": (question_lines[0][:30] + "..." if len(question_lines[0]) > 30 else question_lines[0]),
                "question": '\n'.join(question_lines),
                "choices": formatted_choices,
                "explanation": '\n'.join(explanation_lines) if explanation_lines else "解説なし",
                "difficulty": "medium"
            }
            
            print(f"\n✅ フォールバック抽出成功!")
            print(f"タイトル: {result['title']}")
            print(f"問題: {result['question'][:100]}...")
            print(f"選択肢数: {len(result['choices'])}")
            for i, choice in enumerate(result['choices']):
                status = "⭐" if choice['is_correct'] else "  "
                print(f"  {status} {i+1}: {choice['text'][:50]}...")
            print(f"解説: {result['explanation'][:100]}...")
            
            return result
        else:
            print(f"❌ フォールバック抽出失敗")
            return None
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_question_fallback()
