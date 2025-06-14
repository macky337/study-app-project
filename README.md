# Study App Project

資格試験用の問題生成＆クイズ学習 Web アプリ  
- **Stack**: Python, Streamlit, PostgreSQL (Railway), OpenAI GPT-4o  
- **Features (MVP)**  
  1. 問題・選択肢・解説を登録してクイズ出題  
  2. 正誤判定と学習履歴の保存  
  3. 間違えた問題の復習  

## セットアップ

```bash
git clone https://github.com/<you>/study-app-project.git
cd study-app-project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 開発環境

- Python 3.8+
- Streamlit
- PostgreSQL (Railway)
- OpenAI GPT-4o

## デプロイ

このプロジェクトはRailwayでホストされることを想定しています。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
