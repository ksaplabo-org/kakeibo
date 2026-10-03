"""CSV の読み書き

責務は「ファイルを開く・読む・書く」ことと「CSV行と Transaction の境界」の処理に限る。
金額・日付・カテゴリ等の意味的な検証は shared.validation に委譲し、ここでは行わない。

ファイルI/Oエラー（OSError）と行単位の検証エラー（ValidationError）は明確に区別する。
import_csv はファイル全体を読み終えるまで Repository には一切反映しない
（呼び出し側が transactions を Repository に追加するのは、この関数が正常に戻ったあと）。
"""

import csv
from typing import NamedTuple

from .models import Transaction
from .validation import ValidationError, build_transaction_from_row

# 書き出し時のヘッダ、および読み込み時に「ヘッダ行」として認識する既知の形（4列/5列）
_CSV_HEADER = ["日付", "種類", "カテゴリ", "金額", "メモ"]
_KNOWN_HEADERS = (
    _CSV_HEADER,
    _CSV_HEADER[:4],
)


class CsvImportResult(NamedTuple):
    """CSV取込の結果

    transactions: 検証に成功した取引（この時点ではまだ Repository に反映されていない）
    skipped_count: 検証に失敗して除外した行数（空行は含まない）
    errors: (行番号, ValidationError) の一覧（理由の詳細表示が必要な場合に使う）
    """

    transactions: list[Transaction]
    skipped_count: int
    errors: list[tuple[int, ValidationError]]


def to_csv_row(transaction: Transaction) -> list[str]:
    """Transaction を CSV の1行（文字列のリスト）に変換する"""
    return [
        transaction.date.strftime("%Y/%m/%d"),
        transaction.transaction_type,
        transaction.category,
        str(transaction.amount),
        transaction.memo,
    ]


def export_csv(items: list[tuple[int, Transaction]], path: str) -> int:
    """取引データを CSV ファイルに保存する

    出力順は日付昇順、同一日付内は内部ID昇順（Transaction 自体はID を持たないため、
    (内部ID, Transaction) の組で受け取る）。

    Returns:
        書き出した件数

    Raises:
        OSError: ファイルの書き込みに失敗した場合
    """
    # 日付順、同一日付内はID順に並べ替え
    ordered = sorted(items, key=lambda pair: (pair[1].date, pair[0]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_HEADER)
        for _, transaction in ordered:
            writer.writerow(to_csv_row(transaction))
    return len(ordered)


def import_csv(path: str) -> CsvImportResult:
    """CSV ファイルを読み込み、検証済みの取引一覧を返す

    手順：ファイルを最後まで読む → 行ごとに検証する → 結果をまとめて返す。
    ファイル自体が開けない・読めない場合、または UTF-8 として不正な
    バイト列を含む場合は例外がそのまま送出され、本関数は何も返さない
    （呼び出し側で一部だけ反映されることはない）。

    Raises:
        OSError: ファイルを開く・読むことに失敗した場合
        UnicodeDecodeError: ファイルが UTF-8（BOM有無いずれか）以外の
            エンコーディングで保存されている場合
    """
    # BOM付きUTF-8にも対応した読み込み
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    """応用課題02 START

        ヘッダ行があった場合の開始行 if 0行目がヘッダ行であるか in ヘッダ行判定（この文字列があればヘッダとみなす） else ヘッダ行がない場合の開始位置
    """
    # ヘッダ行があれば読み飛ばす
    # start_index = 1 if rows and list(rows[0]) in _KNOWN_HEADERS else 0

    transactions: list[Transaction] = []
    errors: list[tuple[int, ValidationError]] = []

    for line_number, row in enumerate(rows[start_index:], start=start_index + 1):
        if not row or all(cell.strip() == "" for cell in row):
            continue  # 空行は無視（不正行としては計上しない）
        try:
            transactions.append(build_transaction_from_row(row))
        except ValidationError as error:
            errors.append((line_number, error))

    """応用課題02 END

    仕様通りに修正しよう。
    """
    return CsvImportResult(transactions=transactions, skipped_count=len(errors), errors=errors)
