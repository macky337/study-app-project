from sqlmodel import Session
from database.connection import engine
from database.operations import QuestionService, ChoiceService


def create_sample_data():
    """サンプルデータを作成"""
    with Session(engine) as session:
        question_service = QuestionService(session)
        choice_service = ChoiceService(session)
        
        # サンプル問題1: 基本情報技術者試験
        question1 = question_service.create_question(
            title="プログラミング言語の分類",
            content="次のうち、オブジェクト指向プログラミング言語はどれか。",
            category="基本情報技術者",
            explanation="Javaはオブジェクト指向プログラミング言語の代表例です。",
            difficulty="easy"
        )
        
        # 選択肢を追加
        choice_service.create_choice(question1.id, "A. C言語", False, 1)
        choice_service.create_choice(question1.id, "B. Java", True, 2)
        choice_service.create_choice(question1.id, "C. アセンブリ言語", False, 3)
        choice_service.create_choice(question1.id, "D. HTML", False, 4)
        
        # サンプル問題2: データベース
        question2 = question_service.create_question(
            title="データベースの正規化",
            content="第1正規形の条件として正しいものはどれか。",
            category="データベース",
            explanation="第1正規形では、各属性の値が原子値（分割できない値）である必要があります。",
            difficulty="medium"
        )
        
        choice_service.create_choice(question2.id, "A. 部分関数従属がない", False, 1)
        choice_service.create_choice(question2.id, "B. 推移関数従属がない", False, 2)
        choice_service.create_choice(question2.id, "C. 各属性の値が原子値である", True, 3)
        choice_service.create_choice(question2.id, "D. 候補キーが複数ある", False, 4)
        
        # サンプル問題3: ネットワーク
        question3 = question_service.create_question(
            title="TCP/IPプロトコル",
            content="HTTPプロトコルが動作するOSI参照モデルの層はどれか。",
            category="ネットワーク",
            explanation="HTTPはアプリケーション層（第7層）で動作するプロトコルです。",
            difficulty="medium"
        )
        
        choice_service.create_choice(question3.id, "A. 物理層", False, 1)
        choice_service.create_choice(question3.id, "B. ネットワーク層", False, 2)
        choice_service.create_choice(question3.id, "C. トランスポート層", False, 3)
        choice_service.create_choice(question3.id, "D. アプリケーション層", True, 4)
        
        print("✅ Sample data created successfully!")
        print(f"   - Question 1: {question1.title}")
        print(f"   - Question 2: {question2.title}")
        print(f"   - Question 3: {question3.title}")


if __name__ == "__main__":
    from database.connection import create_tables
    
    # テーブル作成
    create_tables()
    
    # サンプルデータ作成
    create_sample_data()
