"""shared.balance.calculate_totals のテスト（pandas 非依存）"""

from datetime import date

from kakeibo_app.shared.balance import calculate_totals
from kakeibo_app.shared.models import Transaction


def _t(amount: int, transaction_type: str) -> Transaction:
    return Transaction(amount=amount, date=date(2026, 1, 1), transaction_type=transaction_type, category="食費")


def test_calculate_totals_empty():
    assert calculate_totals([]) == (0, 0, 0)


def test_calculate_totals_expense_only():
    transactions = [_t(1000, "支出"), _t(2000, "支出")]
    assert calculate_totals(transactions) == (3000, 0, -3000)


def test_calculate_totals_income_only():
    transactions = [_t(5000, "収入")]
    assert calculate_totals(transactions) == (0, 5000, 5000)


def test_calculate_totals_mixed():
    transactions = [_t(1000, "支出"), _t(500, "支出"), _t(3000, "収入")]
    expense, income, net = calculate_totals(transactions)
    assert expense == 1500
    assert income == 3000
    assert net == 1500


def test_calculate_totals_does_not_import_pandas():
    # balance モジュール自体は pandas を import しないことを確認する。
    # (他のテストが先に pandas を読み込んでいる可能性があるため、モジュールの
    #  ソース内に import 文が無いことも合わせて確認する)
    import inspect

    import kakeibo_app.shared.balance as balance_module

    source = inspect.getsource(balance_module)
    assert "import pandas" not in source
