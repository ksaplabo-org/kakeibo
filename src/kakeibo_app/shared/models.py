"""正準データ型（Transaction）

アプリケーション内で取引データを表す唯一の正準表現。
文字列との変換（入力・表示・CSV）は境界（validation / formatters / csv_storage）でのみ行い、
Transaction 自体は検証済みの値だけを保持する不変レコードとする。
"""

from datetime import date
from typing import Literal, NamedTuple

# 取引種別。値の集合は shared.constants.TRANSACTION_TYPES と一致させること
# （tests/test_models.py で自動的に整合性を検証している）。
TransactionType = Literal["支出", "収入"]


# NamedTupleを継承した、書き換え不可（イミュータブル）なデータ型
class Transaction(NamedTuple):
    """1件の取引を表す不変レコード

    更新する場合は、既存インスタンスの一部を書き換えるのではなく、
    新しい Transaction を生成して置き換える。
    """

    amount: int
    date: date
    transaction_type: TransactionType
    category: str
    memo: str = ""
