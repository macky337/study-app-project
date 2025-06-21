# 📋 手動ファイル削除ガイド

## 🎯 削除が必要な不要ファイル

### 🗑️ 最優先削除対象（完全に不要）

#### **古いアプリファイル**
```
app_minimal.py
app_new.py
```

#### **デバッグ・診断スクリプト**
```
debug_*.py (全て)
diagnose_*.py (全て)
check_*.py (全て)
```

#### **修正・修復スクリプト**
```
fix_*.py (全て)
auto_git_*.py (全て)
```

#### **削除・クリーンアップスクリプト**
```
delete_*.py (全て)
cleanup_*.py (全て)
remove_*.py (全て)
force_*.py (全て)
direct_delete.py
immediate_delete.py
emergency_test.py
```

#### **セットアップ・初期化スクリプト**
```
init_db.py
setup_*.py (全て)
create_tables_direct.py
insert_sample_data.py
```

#### **古い起動スクリプト**
```
launch_app.py
start_app.py
start_fixed_app.py
start_app*.bat (全て)
start_local.bat
```

#### **クイック系・一時スクリプト**
```
quick_*.py (全て)
temp_*.py (全て)
```

#### **古いRailway関連**
```
railway_minimal.py
railway_safe_start.py
```

#### **古いテストファイル**
```
test_db.py
test_direct.py
test_local.py
test_minimal.py
test_status.py
test_extraction_*.py (全て)
test_improved_*.py (全て)
test_integration_*.py (全て)
test_past_question_extraction.py
```

#### **レポート・ログファイル**
```
*_REPORT.md (全て)
*_LOG.md (全て)
complete_solution_report.py
completion_report.py
final_fix_report.py
final_status_check.py
improvement_summary.py
```

#### **出力・一時ファイル**
```
debug_output.txt
debug_result.txt
test_result.txt
f.read()
= (空ファイル)
```

#### **その他**
```
import_test.py
verify_privacy.py
```

---

## ✅ 保持すべきファイル

### **🚀 アプリケーション本体**
- `app.py` - **メインアプリケーション**
- `requirements.txt` - 依存関係
- `Procfile` - Railway設定

### **🗃️ アーキテクチャ**
- `database/` - データベース層
- `models/` - データモデル
- `services/` - ビジネスロジック
- `utils/` - ユーティリティ

### **🔧 起動・設定**
- `start_railway.py` - Railway起動
- `railway_debug.py` - Railway診断
- `start_with_check.py` - 安全起動
- `start.sh` - Linux/Mac起動

### **📖 ドキュメント**
- `README.md` - プロジェクト説明
- `LICENSE` - ライセンス
- `STARTUP_GUIDE.md` - 起動ガイド
- `RAILWAY_HOBBY_GUIDE.md` - Railway使用ガイド
- `RAILWAY_LIMITED_ACCESS_GUIDE.md` - トラブルシューティング
- `PRIVACY_PROTECTION.md` - プライバシー保護
- `PROJECT_CLEANUP_STATUS.md` - このファイル

### **🧪 有用なテストファイル**
- `test_enhanced_service.py` - サービステスト
- `test_pdf_services.py` - PDFサービステスト
- `test_category_selection.py` - カテゴリ機能テスト
- `test_duplicate_detection.py` - 重複検出テスト
- `test_final_features.py` - 最終機能テスト
- `test_delete_question.py` - 削除機能テスト
- `test_question_management.py` - 問題管理テスト

### **⚙️ 設定ファイル**
- `.env.example` - 環境変数サンプル
- `.gitignore` - Git設定
- `.vscode/` - VSCode設定
- `.streamlit/` - Streamlit設定

### **🗄️ データ**
- `study_app.db` - ローカルデータベース

---

## 🛠️ 手動削除手順

### **方法1: VSCodeファイルエクスプローラー**
1. VSCodeの左サイドバーでファイルエクスプローラーを開く
2. 削除対象ファイルを**Ctrl+クリック**で複数選択
3. **右クリック** → **削除**
4. **ゴミ箱に移動**を確認

### **方法2: Windowsエクスプローラー**
1. プロジェクトフォルダをエクスプローラーで開く
2. 削除対象ファイルを**Ctrl+クリック**で複数選択
3. **Delete**キーを押す
4. **ゴミ箱に移動**を確認

### **方法3: コマンドライン**
```cmd
cd "c:\Users\user\Documents\GitHub\study-app-project"

rem 一括削除（注意：慎重に実行）
del app_minimal.py app_new.py debug_*.py diagnose_*.py fix_*.py
del check_*.py delete_*.py cleanup_*.py remove_*.py force_*.py
del quick_*.py temp_*.py init_db.py setup_*.py
del test_db.py test_direct.py test_local.py test_minimal.py
del *_REPORT.md *_LOG.md *.txt
```

---

## 📊 期待される最終構造

```
study-app-project/
├── app.py                          # メインアプリケーション
├── requirements.txt                # 依存関係
├── Procfile                        # Railway設定
├── README.md                       # プロジェクト説明
├── LICENSE                         # ライセンス
├── study_app.db                    # ローカルDB
├── start_railway.py                # Railway起動
├── railway_debug.py                # Railway診断
├── start_with_check.py             # 安全起動
├── start.sh                        # Linux/Mac起動
├── database/                       # データベース層
├── models/                         # データモデル
├── services/                       # ビジネスロジック
├── utils/                          # ユーティリティ
├── STARTUP_GUIDE.md                # 起動ガイド
├── RAILWAY_HOBBY_GUIDE.md          # Railway使用ガイド
├── RAILWAY_LIMITED_ACCESS_GUIDE.md # トラブルシューティング
├── PRIVACY_PROTECTION.md           # プライバシー保護
├── PROJECT_CLEANUP_STATUS.md       # 整理ガイド
├── test_enhanced_service.py        # 有用なテスト
├── test_pdf_services.py            # ファイル...
├── test_category_selection.py      
├── test_duplicate_detection.py     
├── test_final_features.py          
├── test_delete_question.py         
├── test_question_management.py     
├── .env.example                    # 環境変数サンプル
├── .gitignore                      # Git設定
├── .vscode/                        # VSCode設定
└── .streamlit/                     # Streamlit設定
```

---

## 🎯 削除完了後の確認

削除完了後、以下を確認してください：

1. **アプリケーション動作確認**
   ```bash
   streamlit run app.py
   ```

2. **Git状態確認**
   ```bash
   git status
   git add .
   git commit -m "cleanup: Remove unnecessary files"
   ```

3. **ファイル数確認**
   - **目標**: 30個程度のファイル・ディレクトリ
   - **現在**: 100個以上 → 大幅削減が必要

**手動削除を推奨します。VSCodeまたはエクスプローラーで一括選択して削除してください。** 🗑️
