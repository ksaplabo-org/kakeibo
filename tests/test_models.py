"""shared.models.Transaction のテスト"""

from datetime import date
from typing import get_args

import pytest

from kakeibo_app.shared.constants import TRANSACTION_TYPES
from kakeibo_app.shared.models import Transaction, TransactionType


def test_construct_and_fields():
    t = Transaction(amount=1500, date=date(2026, 1, 20), transaction_type="支出", category="食費", memo="昼食")
    assert t.amount == 1500
    assert t.date == date(2026, 1, 20)
    assert t.transaction_type == "支出"
    assert t.category == "食費"
    assert t.memo == "昼食"


def test_memo_defaults_to_empty_string():
    t = Transaction(amount=100, date=date(2026, 1, 1), transaction_type="収入", category="給与")
    assert t.memo == ""


def test_equality_is_structural():
    a = Transaction(amount=100, date=date(2026, 1, 1), transaction_type="支出", category="食費", memo="")
    b = Transaction(amount=100, date=date(2026, 1, 1), transaction_type="支出", category="食費", memo="")
    assert a == b


def test_immutable():
    t = Transaction(amount=100, date=date(2026, 1, 1), transaction_type="支出", category="食費", memo="")
    with pytest.raises(AttributeError):
        t.amount = 200


def test_asdict_available():
    t = Transaction(amount=100, date=date(2026, 1, 1), transaction_type="支出", category="食費", memo="m")
    d = t._asdict()
    assert d["amount"] == 100
    assert d["category"] == "食費"


def test_transaction_type_matches_constants_transaction_types():
    """型チェック用の TransactionType（Literal）と、実行時に選択肢
    として使う constants.TRANSACTION_TYPES は別々の場所で定義されているため、
    片方だけ変更されると静的検査と実行時の値がズレてしまう。
    このテストはその不整合を検出する安全網であり、値そのものは変更しない。
    """
    assert get_args(TransactionType) == tuple(TRANSACTION_TYPES)
