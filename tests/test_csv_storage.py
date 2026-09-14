"""shared.csv_storage（CSV入出力）の仕様に対する contract test"""

from datetime import date
from pathlib import Path

import pytest

from kakeibo_app.shared.csv_storage import export_csv, import_csv, to_csv_row
from kakeibo_app.shared.models import Transaction


def _t(amount=1000, d=date(2026, 1, 20), transaction_type="支出", category="食費", memo="") -> Transaction:
    return Transaction(amount=amount, date=d, transaction_type=transaction_type, category=category, memo=memo)


def _write(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.write_text(content, encoding=encoding, newline="")


# ---- import: 列数・ヘッダ ----

def test_import_5_columns_with_header(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,支出,食費,1500,昼食\n")
    result = import_csv(str(p))
    assert result.skipped_count == 0
    assert len(result.transactions) == 1
    assert result.transactions[0].memo == "昼食"


def test_import_4_columns_with_header(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額\n2026/01/20,支出,食費,1500\n")
    result = import_csv(str(p))
    assert result.skipped_count == 0
    assert result.transactions[0].memo == ""


def test_import_without_header_treats_first_row_as_data(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "2026/01/20,支出,食費,1500,昼食\n")
    result = import_csv(str(p))
    assert len(result.transactions) == 1


def test_import_with_bom(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,支出,食費,1500,昼食\n", encoding="utf-8-sig")
    result = import_csv(str(p))
    assert result.skipped_count == 0
    assert len(result.transactions) == 1


def test_import_blank_lines_are_ignored_not_counted_as_invalid(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n\n2026/01/20,支出,食費,1500,昼食\n\n")
    result = import_csv(str(p))
    assert result.skipped_count == 0
    assert len(result.transactions) == 1


# ---- import: 行単位のエラー ----

def test_import_rejects_wrong_column_count(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,支出,食費\n")
    result = import_csv(str(p))
    assert result.skipped_count == 1
    assert result.transactions == []


def test_import_rejects_invalid_date(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/02/XX,支出,食費,1500,x\n")
    result = import_csv(str(p))
    assert result.skipped_count == 1


def test_import_rejects_invalid_amount(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,支出,食費,abc,x\n")
    result = import_csv(str(p))
    assert result.skipped_count == 1


def test_import_rejects_unknown_category_without_fallback(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,支出,存在しないカテゴリ,1500,x\n")
    result = import_csv(str(p))
    # 不正カテゴリは reject する（先頭カテゴリへの黙った置換はしない）
    assert result.skipped_count == 1
    assert result.transactions == []


def test_import_rejects_invalid_type(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,不正な種類,食費,1500,x\n")
    result = import_csv(str(p))
    assert result.skipped_count == 1


def test_import_partial_success(tmp_path):
    p = tmp_path / "a.csv"
    _write(
        p,
        "日付,種類,カテゴリ,金額,メモ\n"
        "2026/01/20,支出,食費,1500,ok1\n"
        "2026/01/21,不正な種類,食費,1500,ng\n"
        "2026/01/22,支出,食費,2000,ok2\n",
    )
    result = import_csv(str(p))
    assert result.skipped_count == 1
    assert len(result.transactions) == 2
    assert {t.memo for t in result.transactions} == {"ok1", "ok2"}


def test_import_errors_carry_line_number_and_reason(tmp_path):
    p = tmp_path / "a.csv"
    _write(p, "日付,種類,カテゴリ,金額,メモ\n2026/01/20,不正な種類,食費,1500,x\n")
    result = import_csv(str(p))
    line_number, error = result.errors[0]
    assert line_number == 2
    assert error.field == "transaction_type"


# ---- import: ファイルI/Oエラー ----

def test_import_missing_file_raises_oserror():
    with pytest.raises(OSError):
        import_csv("this_file_does_not_exist.csv")


def test_import_non_utf8_file_raises_unicode_decode_error(tmp_path):
    p = tmp_path / "sjis.csv"
    p.write_bytes("日付,種類,カテゴリ,金額,メモ\n2026/01/01,支出,食費,100,テスト\n".encode("cp932"))
    with pytest.raises(UnicodeDecodeError):
        import_csv(str(p))


# ---- export ----

def test_export_writes_utf8_without_bom(tmp_path):
    p = tmp_path / "out.csv"
    export_csv([(1, _t())], str(p))
    raw = p.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")


def test_export_order_is_date_ascending(tmp_path):
    p = tmp_path / "out.csv"
    items = [
        (1, _t(d=date(2026, 3, 1))),
        (2, _t(d=date(2026, 1, 1))),
        (3, _t(d=date(2026, 2, 1))),
    ]
    export_csv(items, str(p))
    lines = p.read_text(encoding="utf-8").splitlines()[1:]
    dates = [line.split(",")[0] for line in lines]
    assert dates == ["2026/01/01", "2026/02/01", "2026/03/01"]


def test_export_tie_break_is_repository_id_ascending(tmp_path):
    p = tmp_path / "out.csv"
    same_day = date(2026, 1, 1)
    items = [
        (5, _t(d=same_day, memo="second")),
        (2, _t(d=same_day, memo="first")),
    ]
    export_csv(items, str(p))
    lines = p.read_text(encoding="utf-8").splitlines()[1:]
    memos = [line.split(",")[-1] for line in lines]
    assert memos == ["first", "second"]


def test_export_import_round_trip(tmp_path):
    p = tmp_path / "roundtrip.csv"
    original = _t(amount=1234, d=date(2026, 5, 6), transaction_type="収入", category="給与", memo="往復")
    export_csv([(1, original)], str(p))
    result = import_csv(str(p))
    assert len(result.transactions) == 1
    restored = result.transactions[0]
    assert restored.amount == original.amount
    assert restored.date == original.date
    assert restored.transaction_type == original.transaction_type
    assert restored.category == original.category
    assert restored.memo == original.memo


def test_to_csv_row_formats_date_as_yyyy_mm_dd():
    row = to_csv_row(_t(d=date(2026, 1, 2)))
    assert row[0] == "2026/01/02"
