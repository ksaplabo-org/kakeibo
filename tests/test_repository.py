"""features.transaction_entry.repository.TransactionRepository のテスト

Tkinter に依存せず GUI なしでテストできることを確認する。
"""

import inspect
from datetime import date

import pytest

from kakeibo_app.features.transaction_entry import repository as repository_module
from kakeibo_app.features.transaction_entry.repository import TransactionRepository
from kakeibo_app.shared.models import Transaction


def _t(amount: int = 1000, transaction_type: str = "支出", category: str = "食費") -> Transaction:
    return Transaction(amount=amount, date=date(2026, 1, 1), transaction_type=transaction_type, category=category)


def test_repository_module_does_not_import_tkinter():
    source = inspect.getsource(repository_module)
    assert "tkinter" not in source


def test_add_returns_sequential_ids():
    m = TransactionRepository()
    first_id = m.add(_t())
    second_id = m.add(_t())
    assert first_id == 1
    assert second_id == 2


def test_get_returns_added_transaction():
    m = TransactionRepository()
    tid = m.add(_t(amount=1500))
    assert m.get(tid).amount == 1500


def test_get_all_returns_all_transactions():
    m = TransactionRepository()
    m.add(_t(amount=100))
    m.add(_t(amount=200))
    assert {t.amount for t in m.get_all()} == {100, 200}


def test_update_replaces_transaction_by_id():
    m = TransactionRepository()
    tid = m.add(_t(amount=100))
    m.update(tid, _t(amount=999))
    assert m.get(tid).amount == 999


def test_update_unknown_id_raises():
    m = TransactionRepository()
    with pytest.raises(KeyError):
        m.update(999, _t())


def test_delete_removes_transaction():
    m = TransactionRepository()
    tid = m.add(_t())
    m.delete(tid)
    assert m.get(tid) is None
    assert m.get_all() == []


def test_delete_unknown_id_is_noop():
    m = TransactionRepository()
    m.delete(999)  # 例外にならない


def test_ids_are_not_reused_after_delete():
    m = TransactionRepository()
    tid1 = m.add(_t())
    m.delete(tid1)
    tid2 = m.add(_t())
    assert tid2 != tid1


def test_get_all_with_id_pairs_ids_with_transactions():
    m = TransactionRepository()
    tid = m.add(_t(amount=100))
    pairs = m.get_all_with_id()
    assert pairs == [(tid, m.get(tid))]


def test_calculate_totals_delegates_to_shared_balance():
    m = TransactionRepository()
    m.add(_t(amount=1000, transaction_type="支出"))
    m.add(_t(amount=3000, transaction_type="収入"))
    assert m.calculate_totals() == (1000, 3000, 2000)
