# 📋 プロジェクトファイル整理状況

## 🎯 整理の目的
- 不要なテスト・デバッグファイルの削除
- プロジェクトの可読性向上
- 重要なファイルの明確化

## ✅ 保持すべき重要ファイル

### 🚀 アプリケーション本体
- `app.py` - **メインアプリケーション**（最も重要）
- `requirements.txt` - 依存関係定義
- `Procfile` - Railway デプロイ設定

### 🗃️ データベース・モデル
- `database/` - データベース操作クラス
- `models/` - データモデル定義
- `services/` - ビジネスロジック
- `utils/` - ユーティリティ関数
- `study_app.db` - ローカルデータベース

### 🔧 設定・起動スクリプト
- `start_railway.py` - Railway起動スクリプト
- `railway_debug.py` - Railway診断ツール
- `start_with_check.py` - 安全起動スクリプト
- `start.sh` - Linux/Mac用起動スクリプト

### 📖 ドキュメント（重要）
- `README.md` - プロジェクト説明
- `LICENSE` - ライセンス
- `STARTUP_GUIDE.md` - 起動ガイド
- `RAILWAY_HOBBY_GUIDE.md` - Railway使用ガイド
- `RAILWAY_LIMITED_ACCESS_GUIDE.md` - トラブルシューティング
- `PRIVACY_PROTECTION.md` - プライバシー保護

### 🧪 有用なテストファイル
- `test_enhanced_service.py` - サービス層テスト
- `test_pdf_services.py` - PDF機能テスト
- `test_category_selection.py` - カテゴリ機能テスト
- `test_duplicate_detection.py` - 重複検出テスト
- `test_final_features.py` - 最終機能テスト
- `test_delete_question.py` - 削除機能テスト
- `test_question_management.py` - 問題管理テスト

### ⚙️ 設定ファイル
- `.env.example` - 環境変数サンプル
- `.gitignore` - Git除外設定
- `.vscode/` - VSCode設定
- `.streamlit/` - Streamlit設定

## 🗑️ 削除対象ファイル（不要）

### 🐛 デバッグ・診断ファイル
```
debug_*.py, diagnose_*.py, fix_*.py
quick_*.py, emergency_*.py, immediate_*.py
```

### 🧪 古い・重複テストファイル
```
test_db.py, test_direct.py, test_local.py, test_minimal.py
test_extraction_*.py, test_improved_*.py, test_integration_*.py
```

### 📄 古いレポート・ログファイル
```
*_REPORT.md, *_LOG.md, *.txt (出力ファイル)
```

### 🚀 古い起動・設定ファイル
```
app_minimal.py, app_new.py
start_app*.*, launch_app.py
setup_*.py, init_*.py, create_*.py
```

### 🧹 クリーンアップ・削除スクリプト
```
cleanup_*.py, delete_*.py, remove_*.py
auto_git_*.py
```

## 📊 整理後の理想的なプロジェクト構造

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
├── .env.example                    # 環境変数サンプル
├── .gitignore                      # Git設定
├── .vscode/                        # VSCode設定
├── .streamlit/                     # Streamlit設定
├── STARTUP_GUIDE.md                # 起動ガイド
├── RAILWAY_HOBBY_GUIDE.md          # Railway使用ガイド
├── RAILWAY_LIMITED_ACCESS_GUIDE.md # トラブルシューティング
├── PRIVACY_PROTECTION.md           # プライバシー保護
└── test_*.py                       # 有用なテストファイル
```

## 🎉 期待される効果

1. **可読性向上**: 重要なファイルが明確になる
2. **保守性向上**: 不要ファイルによる混乱がなくなる
3. **起動速度向上**: ファイル数削減による高速化
4. **Git効率化**: 追跡ファイル数の削減

## 🔄 今後のファイル管理方針

1. **一時ファイル**: 作業完了後は即座に削除
2. **テストファイル**: 機能完成後は統合・削除
3. **デバッグファイル**: 問題解決後は削除
4. **レポートファイル**: 最新版のみ保持

---
**注意**: 削除前に重要なファイルのバックアップを確認してください。
