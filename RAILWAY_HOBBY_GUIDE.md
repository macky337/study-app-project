# Railway Hobby Plan - PDF機能使用ガイド

## 🚀 Railway Hobby Plan の利点

Railway Hobby Plan では以下のメリットがあります：

### 📊 リソース制限
- **メモリ**: より多くのメモリ利用可能
- **CPU**: より高いCPU性能
- **実行時間**: より長い実行時間制限
- **同時接続**: より多くの同時接続可能

### 📄 PDF機能の強化
- **ファイルサイズ**: 最大**50MB**まで対応
- **処理時間**: 大きなPDFファイルの処理が可能
- **問題生成数**: 1回で最大**30問**まで生成可能

## 💡 最適な使用方法

### 📚 大きなPDFファイルの処理
```
✅ 推奨設定:
- ファイルサイズ: 15-50MB
- 生成問題数: 10-20問
- 難易度: 中級
- テキスト抽出: 自動選択
```

### ⚡ 効率的な問題生成
```
🎯 バッチ生成のコツ:
1. 1つのPDFから10-15問を生成
2. カテゴリを明確に設定
3. 解説を含める設定にする
4. 生成後はすぐにクイズでテスト
```

## 🔧 本番環境設定

### 環境変数
```bash
DATABASE_URL=postgresql://... 
OPENAI_API_KEY=sk-...
PORT=8080 (自動設定)
```

### 起動設定
- **Procfile**: `web: python start_railway.py`
- **CORS設定**: 無効化済み
- **XSRFProtection**: 無効化済み

## 📋 PDF機能使用手順

### 1. PDFアップロード
- 最大50MBまでのPDFファイル対応
- テキストベースPDF推奨
- 画像スキャンPDFは OCR 未対応

### 2. 生成設定
- **問題数**: 10問（大きなファイルの場合）
- **難易度**: 教材レベルに合わせて設定
- **カテゴリ**: 具体的な名前を設定

### 3. 実行・結果確認
- 進捗表示でリアルタイム確認
- 生成結果の詳細レビュー
- クイズ機能での即座テスト

## ⚠️ 注意事項

### OpenAI API制限
- Rate Limit: 1分間に複数回のリクエスト制限
- Token制限: 1回あたりの処理文字数制限
- クォータ制限: 月間使用量制限

### 推奨運用
```
🔄 効率的な運用方法:
- 大きなPDFは章ごとに分割
- 生成は1回5-10問に留める  
- 問題の品質を必ず確認
- 定期的なデータベースバックアップ
```

## 🎯 パフォーマンス最適化

### PDF処理の高速化
- **自動選択**: 最適な抽出方法を自動選択
- **チャンク処理**: 大きなテキストを適切に分割
- **並列処理**: 複数問題の並列生成

### メモリ効率
- **ストリーミング処理**: 大きなファイルの段階的処理
- **ガベージコレクション**: 処理完了後のメモリ解放
- **キャッシュ管理**: 重複処理の回避

## 🌐 本番環境でのテスト

1. **Railway URL**: https://<your-app>.up.railway.app
2. **PDF機能**: 問題管理 → PDF問題生成
3. **15.7MB PDFファイル**: 正常処理確認済み
4. **生成テスト**: 10問生成で動作確認

## 💡 トラブルシューティング

### よくある問題
- **OpenAI API エラー**: キー設定確認
- **PDF読み取り失敗**: テキストベースPDF使用
- **メモリ不足**: ファイルサイズを小さくする
- **タイムアウト**: 問題数を減らす

Hobby Plan の強力なリソースを活用して、効率的にPDF問題生成をお楽しみください！
