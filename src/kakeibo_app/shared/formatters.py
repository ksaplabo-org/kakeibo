"""値の表示形式変換"""


def format_yen(value: int) -> str:
    """金額を「¥1,234」形式で文字列化する"""
    # ":," は3桁ごとにカンマ区切りを入れる書式指定
    return f"¥{value:,}"

"""基本課題05 START

正しいreturn文に修正しよう。
補足：文字列を変換させる。
    STEP1   month には「2026-05」形式なので、split メソッドを使用して year 、 month_number に代入する。
    STEP2   year 、 month_number を使用して正しいretrun文に修正する。
"""
def format_month_label(month: str) -> str:
    """「2026-05」形式の年月文字列を「2026年5月」形式に変換する"""
    return "2026年11月"
"""基本課題05 END

正しいreturn文に修正しよう。
"""

def format_year_label(year: str) -> str:
    """「2026」形式の年文字列を「2026年」形式に変換する"""
    return f"{year}年"

"""基本課題06 START

if文を修正しよう。
補足：二重if文（ネスト/入れ子）について
    分岐の中にさらに分岐がある構造のこと。
    
    例）別途資料参照（1dayインターン_ネストについて.pptx）
"""
def format_sort_heading(label: str, *, active: bool, reverse: bool) -> str:
    """列見出しにソート状態（▲/▼）を付与する

    Treeview の列見出し表示（transaction_entry・summary の両方）で共通に使う。

    Args:
        label: 列の表示名（例：「日付」）
        active: この列が現在のソート対象かどうか
        reverse: 降順かどうか（active が False の場合は無視される）

    Returns:
        「日付 ▲」のような見出し文字列
    """
    if not active:
        arrow = "▽"
    else:
        arrow = "▼"
    return f"{label} {arrow}"
"""基本課題06 END

if文を修正しよう。
"""