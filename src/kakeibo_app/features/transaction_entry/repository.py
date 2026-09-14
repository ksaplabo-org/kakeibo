"""取引データの保持・CRUD・内部ID管理

TransactionRepository はアプリ内の取引データの唯一の正本（Single Source of Truth）。
Tkinter には一切依存しない。合計計算のロジックは持たず shared.balance に委譲する。
"""

from ...shared.balance import Totals, calculate_totals
from ...shared.models import Transaction


class TransactionRepository:
    """取引データを保持する

    内部IDは 1 から始まる連番で、アプリ実行中だけ有効な識別子（永続IDではない）。
    Treeview の iid 等、UI 側の識別子はこの内部IDを文字列化して利用してよいが、
    UI 側の識別子をこの内部IDの発生源にしてはならない。
    """

    def __init__(self) -> None:
        self._items: dict[int, Transaction] = {}
        self._next_id: int = 1

    def add(self, transaction: Transaction) -> int:
        """取引を追加し、発番した内部IDを返す"""
        transaction_id = self._next_id
        self._items[transaction_id] = transaction
        self._next_id += 1
        return transaction_id

    def update(self, transaction_id: int, transaction: Transaction) -> None:
        """既存の取引を新しい Transaction で置き換える

        Raises:
            KeyError: transaction_id が存在しない場合（delete と異なり無視しない）
        """
        if transaction_id not in self._items:
            raise KeyError(transaction_id)
        self._items[transaction_id] = transaction

    def delete(self, transaction_id: int) -> None:
        """取引を削除する（存在しないIDは無視する）"""
        self._items.pop(transaction_id, None)

    def get(self, transaction_id: int) -> Transaction | None:
        """内部IDから1件取得する（存在しなければ None）"""
        return self._items.get(transaction_id)

    def get_all(self) -> list[Transaction]:
        """全取引を取得する

        Returns:
            独立した新しいリスト。Transaction 自体は不変のため、
            SummaryWindow 等へそのまま渡してもこの Repository の状態に影響しない。
        """
        return list(self._items.values())

    def get_all_with_id(self) -> list[tuple[int, Transaction]]:
        """内部IDと取引の組を取得する（CSVエクスポートの並び替え等で使用）"""
        return list(self._items.items())

    def calculate_totals(self) -> Totals:
        """支出合計・収入合計・ネット残高を計算する（実体は shared.balance）"""
        return calculate_totals(self.get_all())
