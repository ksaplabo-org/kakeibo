"""合計計算（pandas に依存しない純粋関数）

支出合計・収入合計・ネット残高（収入-支出）を計算する。
統計表示（features/summary）の集計処理とは異なり、この計算は
通常の取引登録画面（features/transaction_entry）が常時必要とするため、
pandas を import しないモジュールに置く。
"""

from typing import NamedTuple

from .models import Transaction


class Totals(NamedTuple):
    """calculate_totals の戻り値。net は income - expense"""

    expense: int
    income: int
    net: int


def calculate_totals(transactions: list[Transaction]) -> Totals:
    """取引一覧から支出合計・収入合計・ネット残高を計算する"""
    # 支出のみの金額を合計
    expense = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "支出"
    )
    # 収入のみの金額を合計
    income = sum(
        transaction.amount
        for transaction in transactions
        if transaction.transaction_type == "収入"
    )
    return Totals(expense, income, income - expense)
