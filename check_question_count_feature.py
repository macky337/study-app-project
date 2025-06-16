#!/usr/bin/env python3
"""
問題数指定機能の実装状況チェック
"""

print("=== 問題数指定機能の実装状況 ===")
print("1. AI問題生成タブ: count スライダー (1-10問)")
print("2. PDF問題生成モード: pdf_num_questions スライダー (1-30問)")
print("3. 過去問抽出モード: max_extract_questions スライダー (1-50問)")
print("")

print("=== 確認すべき点 ===")
print("- UIでスライダーが表示されているか")
print("- スライダーの値が正しく関数に渡されているか")
print("- 指定した数の問題が実際に生成されているか")
print("")

# app.pyから該当するコードを抽出して確認
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== AI問題生成での問題数指定 ===")
    # countスライダーを検索
    if 'count = st.slider("生成数"' in content:
        print("✅ AI問題生成にcountスライダーが実装されています")
    else:
        print("❌ AI問題生成のcountスライダーが見つかりません")
    
    # count変数の使用を確認
    if 'count=count,' in content:
        print("✅ count変数が問題生成関数に渡されています")
    else:
        print("❌ count変数が問題生成関数に渡されていません")
    
    print("")
    print("=== PDF問題生成での問題数指定 ===")
    # pdf_num_questionsスライダーを検索
    if 'pdf_num_questions = st.slider("生成問題数"' in content:
        print("✅ PDF問題生成にpdf_num_questionsスライダーが実装されています")
    else:
        print("❌ PDF問題生成のpdf_num_questionsスライダーが見つかりません")
    
    # pdf_num_questions変数の使用を確認
    if 'num_questions=pdf_num_questions,' in content:
        print("✅ pdf_num_questions変数がPDF問題生成関数に渡されています")
    else:
        print("❌ pdf_num_questions変数がPDF問題生成関数に渡されていません")
    
    print("")
    print("=== 過去問抽出での問題数指定 ===")
    # max_extract_questionsスライダーを検索
    if 'max_extract_questions = st.slider("抽出問題数上限"' in content:
        print("✅ 過去問抽出にmax_extract_questionsスライダーが実装されています")
    else:
        print("❌ 過去問抽出のmax_extract_questionsスライダーが見つかりません")
    
    # max_extract_questions変数の使用を確認
    if 'max_questions=max_extract_questions,' in content:
        print("✅ max_extract_questions変数が過去問抽出関数に渡されています")
    else:
        print("❌ max_extract_questions変数が過去問抽出関数に渡されていません")

except FileNotFoundError:
    print("❌ app.pyファイルが見つかりません")
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")

print("")
print("=== 総合判定 ===")
print("問題数指定機能は実装されていますが、UIで見つけにくい可能性があります。")
print("以下を確認してください:")
print("1. AI問題生成タブで「生成数」スライダーが表示されているか")
print("2. PDF問題生成モードで「生成問題数」スライダーが表示されているか")
print("3. 過去問抽出モードで「抽出問題数上限」スライダーが表示されているか")
