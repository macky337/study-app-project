# 🎯 Study Quiz App

**AI搭載の高度な学習支援システム**  
資格試験・学習用の問題生成・管理・クイズ実行を統合したWebアプリケーション

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)

---

## 🚀 主要機能

### 🤖 AI問題生成
- **複数モデル対応:** GPT-4o-mini, GPT-3.5-turbo, GPT-4o, GPT-4
- **カテゴリ指定:** 基本情報技術者、応用情報技術者、TOEIC、英検など
- **難易度調整:** 初級・中級・上級の3段階
- **重複チェック:** 類似問題の自動検出・回避機能

### 📄 PDF問題生成
- **自動抽出:** PDFファイルから問題を自動生成
- **構造化処理:** テキストの自動解析・整理
- **チャンク分割:** 大容量PDF対応

### 📚 過去問抽出
- **既存問題活用:** 過去問データの構造化抽出
- **フォールバック機能:** AI失敗時の代替処理
- **品質保証:** 自動内容検証

### 🎮 インタラクティブクイズ
- **カテゴリ別出題:** 選択したカテゴリからランダム出題
- **リアルタイム記録:** 回答履歴・統計の自動保存
- **詳細解説:** 問題ごとの詳細な解説表示

### 🛡️ 品質保証システム
- **内容検証:** 問題文と選択肢の関連性・適切性チェック
- **AI品質評価:** 自然性・論理性の自動評価
- **構造検証:** 選択肢数・正解設定の妥当性確認

### 🗂️ 高度な問題管理
- **重複検査:** 全問題の類似度分析・重複検出
- **一括操作:** 複数問題の一括削除・編集
- **統計分析:** カテゴリ別・難易度別の詳細統計

### 🎤 音声文字起こし・議事録作成
- **音声認識:** OpenAI Whisperによる高精度文字起こし
- **多形式対応:** MP3, WAV, M4A, MP4など各種音声・動画形式
- **議事録生成:** AI による構造化された議事録の自動作成
- **プライバシー保護:** 学習無効化ヘッダーによるデータ保護

---

## 🏗️ 技術スタック

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **フロントエンド** | Streamlit | Webインターフェース |
| **バックエンド** | Python 3.12+ | アプリケーションロジック |
| **データベース** | PostgreSQL/SQLite | データ永続化 |
| **AI** | OpenAI GPT-4o-mini | 問題生成・内容検証 |
| **音声AI** | OpenAI Whisper | 音声文字起こし |
| **ORM** | SQLModel | データベース操作 |
| **PDF処理** | PyMuPDF | PDF解析・テキスト抽出 |
| **音声処理** | pydub | 音声ファイル変換 |
| **デプロイ** | Railway | 本番環境ホスティング |

---

## 🚦 クイックスタート

### 📋 前提条件
- Python 3.12以上
- OpenAI APIキー
- PostgreSQL (本番) または SQLite (開発)

### 🛠️ インストール

```bash
# 1. リポジトリクローン
git clone https://github.com/<username>/study-app-project.git
cd study-app-project

# 2. 仮想環境作成・有効化
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. 依存関係インストール
pip install -r requirements.txt
```

### ⚙️ 環境設定

`.env`ファイルを作成し、以下を設定：

```env
# OpenAI設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# データベース設定
DATABASE_URL=postgresql://user:password@host:port/database
# または開発環境の場合
# DATABASE_URL=sqlite:///study_app.db

# アプリ設定
APP_NAME=Study Quiz App
DEBUG=false
```

### 🚀 アプリケーション起動

```bash
# Streamlitアプリ起動
streamlit run app.py

# または便利スクリプト使用
# Windows
start_app.bat

# macOS/Linux
./start.sh
```

アプリケーションは `http://localhost:8501` で利用できます。

---

## 📖 使用方法

### 1️⃣ 問題生成

#### AI問題生成
1. 「問題生成」タブを選択
2. カテゴリ・難易度・生成数を設定
3. AIモデルを選択（GPT-4o-mini推奨）
4. 「問題を生成」ボタンをクリック

#### PDF問題生成
1. 「PDF問題生成」タブを選択
2. PDFファイルをアップロード
3. 抽出設定を調整
4. 「PDFから問題生成」を実行

### 2️⃣ クイズ実行
1. 「クイズ」タブを選択
2. カテゴリを選択（または「すべて」）
3. 問題に回答
4. 結果・解説を確認

### 3️⃣ 問題管理
1. 「問題管理」タブを選択
2. 問題一覧を確認
3. 重複検査・削除・編集を実行

---

## 🎛️ 高度な設定

### 🔄 重複チェック設定
- **類似度閾値:** 0.5-1.0 (デフォルト: 0.8)
- **再試行回数:** 1-5回 (デフォルト: 3回)
- **重複処理:** スキップ/警告付き保存

### 🤖 AI設定
- **モデル選択:** コスト vs 品質のバランス
- **温度設定:** 創造性レベル (0.1-1.0)
- **最大トークン:** 出力長制限

### 📊 内容検証
- **基本検証:** 文字数・選択肢数・正解設定
- **AI検証:** 関連性・適切性・自然性
- **品質フィルタ:** 不適切問題の自動除外

---

## 🌐 デプロイメント

### Railway デプロイ（推奨）
1. [Railway](https://railway.app) アカウント作成
2. PostgreSQL データベース作成
3. 環境変数設定（必須）：
   ```
   OPENAI_API_KEY=your_api_key
   DATABASE_URL=your_postgres_url
   ```
4. リポジトリ接続・自動デプロイ

**⚠️ 重要な注意事項:**
- Railway環境では音声ファイルサイズが20MBに制限されます
- ffmpegは自動インストールされるため、大容量ファイル分割が利用可能です
- メモリ制限により、同時処理数に制限があります

詳細手順: [`RAILWAY_HOBBY_GUIDE.md`](RAILWAY_HOBBY_GUIDE.md)

### その他のプラットフォーム
- **Heroku:** `Procfile` 対応済み
- **Docker:** コンテナ化可能（ffmpeg含む）
- **VPS:** 手動デプロイ対応

---

## 📁 プロジェクト構造

```
study-app-project/
├── app.py                          # メインアプリケーション
├── requirements.txt                # 依存関係
├── .env.example                    # 環境変数テンプレート
├── Procfile                        # デプロイ設定
│
├── database/                       # データベース層
│   ├── connection.py              # DB接続管理
│   └── operations.py              # CRUD・検証機能
│
├── models/                         # データモデル
│   ├── question.py                # 問題モデル
│   ├── choice.py                  # 選択肢モデル
│   └── user_answer.py             # 回答モデル
│
├── services/                       # ビジネスロジック
│   ├── enhanced_openai_service.py  # OpenAI統合
│   ├── question_generator.py       # AI問題生成
│   ├── pdf_question_generator.py   # PDF問題生成
│   ├── past_question_extractor.py  # 過去問抽出
│   └── pdf_processor.py            # PDF処理
│
├── utils/                          # ユーティリティ
│   ├── helpers.py                 # 共通関数
│   └── sample_data.py             # サンプルデータ
│
└── docs/                           # ドキュメント
    ├── STARTUP_GUIDE.md           # 起動ガイド
    ├── RAILWAY_HOBBY_GUIDE.md     # Railwayデプロイ
    ├── PRIVACY_PROTECTION.md     # プライバシー保護
    └── COMPLETION_REPORT.md       # 実装完了レポート
```

---

## 🛡️ セキュリティ・プライバシー

### 🔐 データ保護
- ✅ OpenAI学習データ使用無効化
- ✅ 環境変数による機密情報管理  
- ✅ SQLインジェクション対策
- ✅ 入力値検証・サニタイゼーション

### 🌍 プライバシー
- アップロードされたPDFは学習に使用されません
- ユーザーデータは暗号化して保存
- GDPR準拠のデータ処理

詳細: [`PRIVACY_PROTECTION.md`](PRIVACY_PROTECTION.md)

---

## 🤝 コントリビューション

### バグレポート・機能要望
[GitHub Issues](https://github.com/<username>/study-app-project/issues) でお知らせください。

### 開発参加
1. フォーク作成
2. フィーチャーブランチ作成 (`git checkout -b feature/新機能`)
3. コミット (`git commit -m 'feat: 新機能追加'`)
4. プッシュ (`git push origin feature/新機能`)
5. プルリクエスト作成

---

## 📞 サポート

### 📚 ドキュメント
- [起動ガイド](STARTUP_GUIDE.md) - 詳細なセットアップ手順
- [Railway デプロイ](RAILWAY_HOBBY_GUIDE.md) - 本番環境構築
- [機能完了レポート](COMPLETION_REPORT.md) - 実装済み機能一覧

### 🐛 トラブルシューティング
- OpenAI API接続エラー → APIキー・クレジット残高確認
- データベース接続エラー → 接続URL・認証情報確認
- PDF処理エラー → ファイル形式・サイズ確認

### 📧 お問い合わせ
技術的な質問や提案は [GitHub Discussions](https://github.com/<username>/study-app-project/discussions) をご利用ください。

---

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

---

## 🙏 謝辞

- [OpenAI](https://openai.com) - GPT APIの提供
- [Streamlit](https://streamlit.io) - Webアプリフレームワーク
- [Railway](https://railway.app) - ホスティングプラットフォーム
- Python コミュニティ - 優秀なライブラリ群

---

**🎯 Study Quiz App で効率的な学習を始めましょう！**
