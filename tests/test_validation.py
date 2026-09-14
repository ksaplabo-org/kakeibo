"""shared.validation のテスト

金額は整数のみを受理し、小数・NaN・Infinity・指数表記は拒否する。
カテゴリは許可リストに厳密一致するもののみを受理し、
不正な値を別の値へ黙って置き換えることはしない。
これらの仕様を contract として検証する。
"""

from datetime import date

import pytest

from kakeibo_app.shared.validation import (
    ValidationError,
    build_transaction,
    build_transaction_from_row,
    parse_amount,
    parse_date,
    validate_category,
    validate_transaction_type,
)


# ---- 金額 ----

@pytest.mark.parametrize(
    "text, expected",
    [
        ("1234", 1234),
        ("1,234", 1234),
        ("¥1234", 1234),
        ("¥1,234", 1234),
        ("12,345", 12345),
        ("１２３４", 1234),  # 全角数字
        ("  1234  ", 1234),  # 前後空白
        ("1", 1),
    ],
)
def test_parse_amount_accepts_valid_values(text, expected):
    assert parse_amount(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "0",
        "-1",
        "1.5",
        "1e3",
        "Infinity",
        "NaN",
        "1,0,0",
        "abc",
        "",
        "   ",
        "12,34",  # 不正な桁区切り
        "1,2345",  # 不正な桁区切り
    ],
)
def test_parse_amount_rejects_invalid_values(text):
    with pytest.raises(ValidationError):
        parse_amount(text)


def test_parse_amount_error_has_code_and_field():
    with pytest.raises(ValidationError) as excinfo:
        parse_amount("abc")
    assert excinfo.value.field == "amount"
    assert excinfo.value.code == "invalid_amount"


# ---- 日付 ----

@pytest.mark.parametrize(
    "text, expected",
    [
        ("2026/01/20", date(2026, 1, 20)),
        ("2026/1/2", date(2026, 1, 2)),
        (" 2026/01/20 ", date(2026, 1, 20)),
        ("2024/02/29", date(2024, 2, 29)),  # 閏年
    ],
)
def test_parse_date_accepts_valid_values(text, expected):
    assert parse_date(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "2026-01-20",  # ハイフン非対応
        "2026/02/29",  # 閏年でない年の2/29
        "2026/13/01",
        "2026/00/10",
        "",
        "   ",
        "20260120",
    ],
)
def test_parse_date_rejects_invalid_values(text):
    with pytest.raises(ValidationError):
        parse_date(text)


def test_parse_date_has_no_year_range_restriction():
    # 年範囲の制限を設けない。datetime.date として構築可能なら受理する。
    assert parse_date("0001/01/01") == date(1, 1, 1)


# ---- transaction type ----

def test_validate_transaction_type_accepts_known_values():
    assert validate_transaction_type("支出") == "支出"
    assert validate_transaction_type("収入") == "収入"


def test_validate_transaction_type_rejects_unknown_value():
    with pytest.raises(ValidationError):
        validate_transaction_type("不明")


# ---- category ----

def test_validate_category_accepts_known_category():
    assert validate_category("食費", "支出") == "食費"


def test_validate_category_rejects_unknown_category_without_fallback():
    # 不正カテゴリは reject する。先頭カテゴリへの黙った置換はしない。
    with pytest.raises(ValidationError) as excinfo:
        validate_category("存在しないカテゴリ", "支出")
    assert excinfo.value.code == "unknown_category"


def test_validate_category_rejects_category_of_wrong_type():
    with pytest.raises(ValidationError):
        validate_category("給与", "支出")  # 「給与」は収入カテゴリ


def test_validate_category_rejects_empty():
    with pytest.raises(ValidationError):
        validate_category("", "支出")


# ---- build_transaction ----

def test_build_transaction_success():
    t = build_transaction(
        date_text="2026/1/20",
        transaction_type_text="支出",
        category_text="食費",
        amount_text="¥1,500",
        memo=" 昼食 ",
    )
    assert t.amount == 1500
    assert t.date == date(2026, 1, 20)
    assert t.transaction_type == "支出"
    assert t.category == "食費"
    assert t.memo == "昼食"


def test_build_transaction_from_row_5_columns():
    t = build_transaction_from_row(["2026/01/20", "支出", "食費", "1500", "メモ"])
    assert t.memo == "メモ"


def test_build_transaction_from_row_4_columns_memo_empty():
    t = build_transaction_from_row(["2026/01/20", "支出", "食費", "1500"])
    assert t.memo == ""


@pytest.mark.parametrize(
    "row",
    [
        [],
        ["2026/01/20", "支出", "食費"],  # 3列
        ["2026/01/20", "支出", "食費", "1500", "メモ", "余分"],  # 6列
    ],
)
def test_build_transaction_from_row_rejects_wrong_column_count(row):
    with pytest.raises(ValidationError) as excinfo:
        build_transaction_from_row(row)
    assert excinfo.value.code == "invalid_column_count"
