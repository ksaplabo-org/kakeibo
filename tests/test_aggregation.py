"""features.summary.aggregation のテスト（pandas 集計、date型 Transaction 前提）"""

from datetime import date

from kakeibo_app.features.summary.aggregation import (
    available_months,
    summarize_by_category,
    filter_by_month_range,
    filter_by_type,
    summarize_by_month,
    summarize_by_year,
    summarize_totals_by_month,
    summarize_totals_by_year,
)
from kakeibo_app.shared.models import Transaction


def _t(amount, d, transaction_type="支出", category="食費") -> Transaction:
    return Transaction(amount=amount, date=d, transaction_type=transaction_type, category=category)


def test_filter_by_type_returns_only_matching_transactions():
    transactions = [
        _t(100, date(2026, 1, 1), "支出"),
        _t(200, date(2026, 1, 2), "収入"),
    ]
    assert filter_by_type(transactions, "支出") == [transactions[0]]


def test_summarize_by_category_empty():
    assert summarize_by_category([]).empty


def test_summarize_by_category_aggregates_by_category():
    transactions = [
        _t(1000, date(2026, 1, 1), category="食費"),
        _t(500, date(2026, 1, 2), category="食費"),
        _t(2000, date(2026, 1, 3), category="住居"),
    ]
    result = summarize_by_category(transactions)
    assert result.loc["食費", "合計"] == 1500
    assert result.loc["食費", "件数"] == 2
    assert result.loc["住居", "合計"] == 2000


def test_summarize_by_month_empty():
    assert summarize_by_month([]).empty


def test_summarize_by_month_groups_by_year_month():
    transactions = [
        _t(1000, date(2026, 1, 15)),
        _t(500, date(2026, 1, 20)),
        _t(2000, date(2026, 2, 1)),
    ]
    result = summarize_by_month(transactions)
    assert result.loc["2026-01", "合計"] == 1500
    assert result.loc["2026-02", "合計"] == 2000


def test_summarize_by_year_empty():
    assert summarize_by_year([]).empty


def test_summarize_by_year_groups_by_year():
    transactions = [
        _t(1000, date(2025, 12, 31)),
        _t(2000, date(2026, 1, 1)),
    ]
    result = summarize_by_year(transactions)
    assert result.loc["2025", "合計"] == 1000
    assert result.loc["2026", "合計"] == 2000


def _range_sample() -> list[Transaction]:
    return [
        _t(100, date(2025, 12, 31)),
        _t(200, date(2026, 1, 15)),
        _t(300, date(2026, 2, 1)),
        _t(400, date(2026, 3, 20)),
    ]


def test_available_months_empty():
    assert available_months([]) == []


def test_available_months_returns_sorted_unique_months():
    transactions = [
        _t(100, date(2026, 2, 1)),
        _t(100, date(2025, 12, 31)),
        _t(100, date(2026, 2, 20)),
        _t(100, date(2026, 1, 15)),
    ]
    assert available_months(transactions) == ["2025-12", "2026-01", "2026-02"]


def test_available_months_values_are_accepted_by_filter_by_month_range():
    # 月範囲フィルタの選択肢と絞り込み条件で年月の形式がズレないことの確認
    transactions = _range_sample()
    months = available_months(transactions)
    assert filter_by_month_range(transactions, start=months[0], end=months[-1]) == transactions


def test_filter_by_month_range_without_bounds_returns_all():
    transactions = _range_sample()
    assert filter_by_month_range(transactions) == transactions


def test_filter_by_month_range_start_only():
    transactions = _range_sample()
    assert filter_by_month_range(transactions, start="2026-02") == transactions[2:]


def test_filter_by_month_range_end_only():
    transactions = _range_sample()
    assert filter_by_month_range(transactions, end="2026-01") == transactions[:2]


def test_filter_by_month_range_includes_boundary_months():
    transactions = _range_sample()
    result = filter_by_month_range(transactions, start="2026-01", end="2026-02")
    assert result == transactions[1:3]


def test_filter_by_month_range_returns_empty_when_start_after_end():
    assert filter_by_month_range(_range_sample(), start="2026-03", end="2026-01") == []


def test_summarize_totals_by_month_empty():
    assert summarize_totals_by_month([]).empty


def test_summarize_totals_by_month_splits_expense_and_income():
    transactions = [
        _t(1000, date(2026, 1, 10), "支出"),
        _t(500, date(2026, 1, 20), "支出"),
        _t(3000, date(2026, 1, 25), "収入"),
        _t(4000, date(2026, 2, 5), "支出"),
        _t(3000, date(2026, 2, 25), "収入"),
    ]
    result = summarize_totals_by_month(transactions)
    assert result.loc["2026-01", "支出合計"] == 1500
    assert result.loc["2026-01", "収入合計"] == 3000
    # 収入が支出を上回る月は差額がプラスになる
    assert result.loc["2026-01", "差額"] == 1500
    # 支出が収入を上回る月は差額がマイナスになる
    assert result.loc["2026-02", "差額"] == -1000


def test_summarize_totals_by_month_fills_missing_type_with_zero():
    # 支出しか無い月でも収入合計の列が 0 で埋まること
    result = summarize_totals_by_month([_t(1000, date(2026, 1, 10), "支出")])
    assert result.loc["2026-01", "収入合計"] == 0
    assert result.loc["2026-01", "差額"] == -1000


def test_summarize_totals_by_year_empty():
    assert summarize_totals_by_year([]).empty


def test_summarize_totals_by_year_groups_by_year():
    transactions = [
        _t(1000, date(2025, 6, 1), "支出"),
        _t(5000, date(2025, 7, 1), "収入"),
        _t(2000, date(2026, 1, 1), "支出"),
    ]
    result = summarize_totals_by_year(transactions)
    assert result.loc["2025", "差額"] == 4000
    assert result.loc["2026", "支出合計"] == 2000
    assert result.loc["2026", "差額"] == -2000


def test_summary_accepts_date_typed_transactions_without_to_datetime():
    # Transaction.date が既に datetime.date であるため、pd.to_datetime を使わずに
    # strftime だけでグルーピングできることの確認。
    t = _t(100, date(2026, 3, 5))
    assert isinstance(t.date, date)
    result = summarize_by_month([t])
    assert "2026-03" in result.index
