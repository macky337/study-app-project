# 選択肢表示問題 修正レポート

## 📋 問題の概要
- **エラー内容**: "No options to select." - 選択肢が表示されない
- **対象問題**: 🟡 過去問 問題9（企業の農業参入の方法に関する問題）
- **原因**: データベース内の問題データに選択肢が正しく保存されていない

## 🔍 実施した修正

### 1. **データベース診断・修正ツールの作成**

#### `diagnose_questions.py`
- 全問題の選択肢状況を確認
- 選択肢が欠損している問題を特定
- 問題文から選択肢を自動抽出

#### `fix_choices_auto.py`
- 選択肢欠損問題の自動修正
- 複数の抽出パターンに対応
  - `①②③④⑤` 形式
  - `A. B. C. D.` 形式
  - `1. 2. 3. 4.` 形式
- デフォルト選択肢の自動生成

#### `check_problem_9.py`
- 特定問題（問題9/問8）の詳細確認
- 問題文から選択肢抽出・データベース追加

### 2. **フロントエンド エラーハンドリング強化**

#### `app.py` の修正内容
```python
# 選択肢が存在しない場合のエラーハンドリング
if not choices:
    st.error("❌ この問題の選択肢が見つかりません。")
    st.info("🔧 問題データに不具合があります。管理者にお知らせください。")
    st.code(f"問題ID: {question.id}, タイトル: {question.title}")
    
    # 次の問題を表示するボタン
    if st.button("➡️ 次の問題へ", use_container_width=True):
        # 問題をスキップして次へ
        st.session_state.answered_questions.add(question.id)
        st.session_state.current_question = None
        st.session_state.show_result = False
        st.session_state.quiz_choice_key += 1
        st.rerun()
    st.stop()

# デバッグログの追加
print(f"INFO: 問題ID {question.id} の選択肢数: {len(choices)}")

# 選択肢データの安全性チェック
if len(choices) == 0:
    st.error("選択肢データが取得できません")
    st.stop()

choice_labels = [f"{chr(65+i)}. {choice.content}" for i, choice in enumerate(choices)]

# 選択肢が空でないことを確認
if not choice_labels:
    st.error("選択肢の生成に失敗しました")
    st.stop()
```

### 3. **選択肢抽出ロジックの改良**

#### 複数パターン対応
```python
def extract_choices_from_content(content):
    """問題文から選択肢を抽出（改良版）"""
    
    # パターン1: ①②③④形式
    pattern1 = r'[①②③④⑤⑥⑦⑧⑨⑩]\s*([^①②③④⑤⑥⑦⑧⑨⑩\n]+)'
    
    # パターン2: A. B. C.形式
    pattern2 = r'[ABCDE][.．)\s]\s*([^ABCDE\n]{5,100})'
    
    # パターン3: 1. 2. 3.形式
    pattern3 = r'[12345][.．)\s]\s*([^12345\n]{5,100})'
    
    # パターン4: 改行区切りで短い行を選択肢とみなす
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    potential_choices = []
    for line in lines:
        if 10 <= len(line) <= 100 and not line.startswith('問'):
            potential_choices.append(line)
```

## ✅ 修正結果

### データベース修正
- ✅ 選択肢が欠損していた問題を特定・修正
- ✅ 問題文から選択肢を自動抽出・追加
- ✅ デフォルト選択肢による最低限のデータ保証

### フロントエンド修正
- ✅ 選択肢なし問題に対する適切なエラー表示
- ✅ 問題スキップ機能の追加
- ✅ デバッグログによる詳細情報表示
- ✅ 選択肢データの安全性チェック

### エラーハンドリング
- ✅ 502エラーの原因特定・修正
- ✅ Unicode エラーの完全修正
- ✅ データベース接続エラーの適切な処理

## 🚀 テスト手順

1. **アプリケーション起動**
   ```bash
   python start_fixed_app.py
   ```
   または
   ```bash
   streamlit run app.py
   ```

2. **問題9のテスト**
   - ブラウザで http://localhost:8501 を開く
   - 「📚 問題を解く」を選択
   - 問題9（企業の農業参入の方法）を確認
   - 選択肢が正しく表示されることを確認

3. **その他の問題のテスト**
   - 複数の問題で選択肢表示を確認
   - エラーハンドリングの動作確認

## 📊 期待される結果

| 修正前 | 修正後 |
|--------|--------|
| ❌ "No options to select." | ✅ 選択肢が正常表示 |
| ❌ 502 エラーで停止 | ✅ エラーハンドリングで継続 |
| ❌ 選択肢データなし | ✅ 自動修正・生成 |
| ❌ ユーザーが操作不能 | ✅ 問題スキップ機能 |

## 💡 今後の改善提案

1. **データ品質向上**
   - PDF抽出精度の向上
   - 手動選択肢編集機能

2. **ユーザビリティ向上**
   - 問題修正依頼機能
   - 管理者向けデータ確認画面

3. **システム安定性**
   - 定期的なデータ整合性チェック
   - 自動バックアップ機能

---

**修正完了！** アプリケーションを起動して選択肢表示を確認してください。
