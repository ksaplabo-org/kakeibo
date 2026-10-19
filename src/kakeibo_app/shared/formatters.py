"""値の表示形式変換"""


def format_yen(value: int) -> str:
    """金額を「¥1,234」形式で文字列化する"""
    # ":," は3桁ごとにカンマ区切りを入れる書式指定
    return f"¥{value:,}"

"""基本課題05 START 日付フォーマット関数の修正 

仕様：
・「YYYY-MM」形式の年月文字列を受け取り、「YYYY年M月」形式で返す
   例：「2026-05」→「2026年5月」

ヒント
・split メソッドを使って「年」と「月」に分割できる
・文字列の「05」は整数に型変換にすると「5」になる

"""
def format_month_label(month: str) -> str:
    """「2026-05」形式の年月文字列を「2026年5月」形式に変換する"""

    return "2026年11月"
"""基本課題05 END 日付フォーマット関数の修正 """

def format_year_label(year: str) -> str:
    """「2026」形式の年文字列を「2026年」形式に変換する"""
    return f"{year}年"

"""基本課題06 START ソートの表示制御関数の修正 

仕様：
・対象の列が現在のソート対象ではない場合、“▽”を設定する
・対象の列が現在のソート対象の場合、
   現在のソート順が降順であれば“▼”、昇順であれば“▲”を設定する

ヒント：
・二重 if 文（ネスト）の活用しよう

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
"""基本課題06 END ソートの表示制御関数の修正 """