#!/usr/bin/env python3
"""
過去問抽出の改善版テスト
"""

def test_improved_extraction():
    """改善された過去問抽出のテスト"""
    
    print("🧪 改善版過去問抽出機能のテスト")
    print("=" * 60)
    
    # サンプルテキスト（実際のPDFに近い形式）
    sample_text = """
【問1】
名刺の交換マナーについて、適切なものをすべて選べ。
① いすに座っている時に名刺交換が始まったら、すぐに立ち上がりテーブル越しに名刺を差し出し、交換する
② 名刺は文字に指がかからないように持ち、名刺の文字が相手に向くようにして差し出す
③ 相手の名刺を受け取る際は片手で受け取り、すぐに名刺入れにしまう
④ 名刺交換の際には、役職が高い方から渡していく
(正解）②,④
(解説）①名刺交換はテーブル越しには行わない。テーブルを回り込み相手の正面に立って交換する。
③受け取る際は原則両手で受け取り、すぐにはしまわずにしばらく手元に置いて確認する。

【問2】
お通夜の香典として1万円を封筒に入れる場合、適切なものをすべて選べ。
①新札を1枚用意し、肖像画が封筒の開口部から見えるようにして入れる
②新札を1枚用意し、肖像画が封筒の底部に向かうようにして入れる
③古札を1枚用意し、肖像画が封筒の開口部から見えるようにして入れる
④古札を1枚用意し、肖像画が封筒の底部に向かうようにして入れる
正解：④
解説：お通夜や葬儀では、新札は失礼とされます。古札を使用し、肖像画は底部に向けて入れます。
"""
    
    print(f"📝 サンプルテキスト長: {len(sample_text)} 文字")
    print(f"📄 内容プレビュー:\n{sample_text[:300]}...")
    
    try:
        # 過去問抽出サービスをテスト
        from services.past_question_extractor import PastQuestionExtractor
        
        # ダミーセッション（テスト用）
        class DummySession:
            pass
        
        extractor = PastQuestionExtractor(DummySession())
        
        # 問題分割のテスト
        print(f"\n🔍 問題分割テスト")
        questions = extractor._split_into_questions(sample_text)
        print(f"✅ 分割結果: {len(questions)}問を検出")
        
        for i, q in enumerate(questions):
            print(f"\n📋 問題{i+1} (長さ: {len(q)}文字):")
            print(f"   プレビュー: {q[:150]}...")
        
        # 構造化抽出のテスト（最初の問題のみ）
        if questions:
            print(f"\n🚀 構造化抽出テスト（問題1）")
            first_question = questions[0]
            
            # フォールバック抽出をテスト
            print(f"\n🔄 フォールバック抽出テスト")
            fallback_result = extractor._fallback_extraction(first_question)
            
            if fallback_result:
                print(f"✅ フォールバック抽出成功")
                print(f"   タイトル: {fallback_result['title']}")
                print(f"   問題文: {fallback_result['question'][:100]}...")
                print(f"   選択肢数: {len(fallback_result['choices'])}")
                for i, choice in enumerate(fallback_result['choices']):
                    status = "⭐正解" if choice['is_correct'] else "  "
                    print(f"   {status} 選択肢{i+1}: {choice['text'][:50]}...")
                print(f"   解説: {fallback_result['explanation'][:100]}...")
            else:
                print(f"❌ フォールバック抽出失敗")
        
        print(f"\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ テスト中にエラー発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_improved_extraction()
