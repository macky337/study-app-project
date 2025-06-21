# Streamlitアプリ起動手順

## 🔧 修正完了
- ✅ enhanced_openai_service.pyの構文エラー修正
- ✅ .streamlit/config.tomlの設定修正

## 🚀 アプリ起動方法

### 1. コマンドプロンプトを開く
```cmd
cd "c:\Users\user\Documents\GitHub\study-app-project"
```

### 2. Streamlitアプリを起動
```cmd
streamlit run app.py
```

### 3. ブラウザでアクセス
正しいURL: **http://localhost:8501**

## 📋 修正された設定
- アドレス: `0.0.0.0` → `localhost`
- ポート: `8080` → `8501`
- ヘッドレス: `true` → `false`

## ⚠️ 注意事項
- `http://0.0.0.0:8501/` は無効なアドレスです
- 必ず `http://localhost:8501` を使用してください

## 🎯 期待される結果
- データベース接続エラーが解消されている
- Study Quiz Appのホーム画面が表示される
- PDF問題抽出機能が利用可能

## 🔍 トラブルシューティング
もしまだエラーが出る場合は：
1. ターミナルを閉じて新しく開く
2. 環境変数を再読み込み
3. `python -c "from services.enhanced_openai_service import EnhancedOpenAIService; print('OK')"`でテスト
