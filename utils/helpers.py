import uuid
from datetime import datetime


def generate_session_id() -> str:
    """セッションIDを生成"""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def format_accuracy(correct: int, total: int) -> str:
    """正答率をフォーマット"""
    if total == 0:
        return "0.0%"
    accuracy = (correct / total) * 100
    return f"{accuracy:.1f}%"


def get_difficulty_emoji(difficulty: str) -> str:
    """難易度に対応する絵文字を取得"""
    emoji_map = {
        "easy": "🟢",
        "medium": "🟡", 
        "hard": "🔴"
    }
    return emoji_map.get(difficulty, "⚪")
