# ローカル環境でのStreamlitアプリ実行手順

このドキュメントでは、リファクタリングされたStudy Quiz Appをローカル環境で実行するための手順を説明します。

## 前提条件

- Python 3.9以上がインストールされていること
- pipがインストールされていること
- 必要なパッケージがインストールされていること（requirements.txtに記載）

## 環境設定

1. **依存パッケージのインストール**

```bash
pip install -r requirements.txt
```

2. **環境変数の設定（必要な場合）**

`config/app_config.py`で使用している環境変数がある場合は、`.env`ファイルを作成するか、システムの環境変数として設定してください。

```
# .envファイルの例
DATABASE_URL=sqlite:///quiz_app.db
OPENAI_API_KEY=your_api_key_here
```

## アプリケーションの実行

1. **通常実行**

プロジェクトのルートディレクトリで以下のコマンドを実行します：

```bash
streamlit run app.py
```

2. **診断ツールの実行（オプション）**

アプリケーションの環境設定を確認する場合は、以下のコマンドを実行します：

```bash
python diagnose_app.py
```

## アプリケーションの構造

リファクタリング後のアプリケーションは以下の構造になっています：

- `app.py` - メインアプリケーション（ルーター）
- `config/app_config.py` - 設定とセッション初期化
- `components/question_components.py` - 共通コンポーネント
- `pages/` - 各機能ページ
  - `quiz_page.py` - クイズ機能
  - `statistics_page.py` - 統計表示
  - `question_management_page.py` - 問題管理
  - `settings_page.py` - 設定

## トラブルシューティング

### データベース接続エラー

データベースに接続できない場合は、以下を確認してください：
- SQLiteデータベースの場合、ファイルのパスとアクセス権限
- 外部データベースの場合、接続文字列と認証情報

### モジュールのインポートエラー

モジュールのインポートエラーが発生した場合は、以下を確認してください：
- 必要なパッケージが`pip install -r requirements.txt`でインストールされているか
- Pythonのバージョンが互換性があるか（Python 3.9以上を推奨）

### Streamlitの起動エラー

Streamlitが起動しない場合は、以下を確認してください：
- Streamlitがインストールされているか（`pip install streamlit`）
- 実行中のポート（デフォルト8501）が他のアプリケーションで使用されていないか

### VSCodeでの実行

VSCodeでStreamlitアプリを実行するには、実行構成を使用できます。`.vscode/launch.json`ファイルが既に設定されているため、「実行とデバッグ」パネルから「Streamlit」を選択して実行できます。
