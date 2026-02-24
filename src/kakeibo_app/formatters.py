"""フォーマッタ層 - 値の表示形式変換"""

from decimal import Decimal


def format_yen(value: Decimal) -> str:
    """金額を「¥1,234」形式で文字列化
    
    Args:
        value (Decimal): 金額
    
    Returns:
        str: 「¥1,234」形式の文字列
    """
    return f"¥{int(value):,}"
