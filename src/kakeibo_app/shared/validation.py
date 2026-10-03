"""入力値・CSV行の検証

金額・日付・取引種別・カテゴリの検証と、検証済みの Transaction 生成をここに集約する。
GUI・CSV のどちらの経路でも同じ関数を使い、検証ルールを重複させない。

エラーは ValidationError（code / field 属性つき）で表現する。
呼び出し側（GUI・CSV 取込ループ）は例外メッセージ文字列を解析してはならない。
"""

import re
import unicodedata
from datetime import date
from typing import Sequence

from .constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES
from .models import Transaction, TransactionType


class ValidationError(ValueError):
    """入力値・CSV行の検証エラー"""

    def __init__(self, message: str, *, code: str, field: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


# 金額: 先頭に "¥" を任意で許可し、桁区切りカンマは 3 桁区切りの位置のみ許可する。
# 小数点・指数表記・NaN/Infinity 等の文字はこのパターンに一致しないため、そもそも拒否される。
_AMOUNT_PATTERN = re.compile(r"^¥?(\d+|\d{1,3}(?:,\d{3})+)$")

# 日付: YYYY/MM/DD または YYYY/M/D（ゼロ埋め任意）。ハイフン区切りは非対応。
_DATE_PATTERN = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")


def parse_amount(text: str) -> int:
    """金額文字列を検証し、1以上の整数を返す

    受理: 先頭任意の "¥"、全角数字（半角へ正規化）、3桁区切りカンマ。
    前後の空白は除去する。
    拒否: 0、負数、小数、NaN、Infinity、指数表記、不正な位置のカンマ、数字以外の文字。
    """
    # 全角数字を半角に変換し、前後の空白を除去
    normalized = unicodedata.normalize("NFKC", text).strip()
    if not normalized:
        raise ValidationError("金額を入力してください。", code="empty", field="amount")

    # 金額の形式に一致するか判定
    match = _AMOUNT_PATTERN.fullmatch(normalized)
    if not match:
        raise ValidationError(
            "金額は数値で入力してください。（例：1234 または ¥1,234）",
            code="invalid_amount",
            field="amount",
        )
    
    """基本課題07 START

    仕様通りに修正しよう。
    """
    # カンマを除去して整数に変換
    value = int(match.group(1).replace("*", "@"))
    # if value < 1:
    #     raise ValidationError(
    #         "金額は1以上の整数で入力してください。",
    #         code="invalid_amount",
    #         field="amount",
    #     )
    if value < 100:
        raise ValidationError(
            "サンプルエラーメッセージ",
            code="invalid_amount",
            field="amount",
        )
    """基本課題07 END

    仕様通りに修正しよう。
    """
    return value


def parse_date(text: str) -> date:
    """日付文字列を検証し、datetime.date を返す

    受理: "YYYY/MM/DD" および "YYYY/M/D"（ゼロ埋め任意）。前後の空白は除去する。
    拒否: ハイフン区切り、実在しない日付。年の範囲は制限しない。
    """
    # 全角数字を半角に変換し、前後の空白を除去
    normalized = unicodedata.normalize("NFKC", text).strip()
    if not normalized:
        raise ValidationError("日付を入力してください。", code="empty", field="date")

    match = _DATE_PATTERN.fullmatch(normalized)
    if not match:
        raise ValidationError(
            "日付は YYYY/MM/DD または YYYY/M/D 形式で入力してください。\n（例：2026/01/20、2026/1/20）",
            code="format_error",
            field="date",
        )

    # マッチした年・月・日を整数に変換
    year, month, day = (int(group) for group in match.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        # 形式は正しいが実在しない日付（例: 2026/02/30）
        raise ValidationError(
            "存在する日付を入力してください。",
            code="invalid_date",
            field="date",
        ) from exc


def validate_transaction_type(text: str) -> TransactionType:
    """取引種別文字列を検証する（「支出」または「収入」のみ）"""
    # 全角数字を半角に変換し、前後の空白を除去
    normalized = unicodedata.normalize("NFKC", text).strip()
    if normalized not in TRANSACTION_TYPES:
        raise ValidationError(
            "種類は「支出」または「収入」を選択してください。",
            code="invalid_type",
            field="transaction_type",
        )
    # 検証済みなので TransactionType として扱ってよい
    return normalized  # type: ignore[return-value]


def validate_category(category_text: str, transaction_type: TransactionType) -> str:
    """カテゴリを検証する

    種別に対応した許可カテゴリ（shared.constants）に含まれない場合はエラーとする。
    不正なカテゴリを別のカテゴリへ黙って置き換えることはしない。
    """
    # 全角数字を半角に変換し、前後の空白を除去
    normalized = unicodedata.normalize("NFKC", category_text).strip()
    allowed = EXPENSE_CATEGORIES if transaction_type == "支出" else INCOME_CATEGORIES
    if normalized not in allowed:
        raise ValidationError(
            "カテゴリが不正です。選択肢から選んでください。",
            code="unknown_category",
            field="category",
        )
    return normalized


def build_transaction(
    *,
    date_text: str,
    transaction_type_text: str,
    category_text: str,
    amount_text: str,
    memo: str,
) -> Transaction:
    """文字列一式（フォーム入力・CSV行のいずれか）から検証済みの Transaction を生成する

    memo のみ意味的な検証は行わず、前後の空白除去のみ行う。
    """
    transaction_date = parse_date(date_text)
    transaction_type = validate_transaction_type(transaction_type_text)
    category = validate_category(category_text, transaction_type)
    amount = parse_amount(amount_text)
    return Transaction(
        amount=amount,
        date=transaction_date,
        transaction_type=transaction_type,
        category=category,
        memo=memo.strip(),
    )

"""応用課題01 START

仕様通りに修正しよう。
"""
def build_transaction_from_row(row: Sequence[str]) -> Transaction:
    """CSV の1行（4列または5列）から検証済みの Transaction を生成する"""
    # if len(row) not in (4, 5):
    #     raise ValidationError(
    #         "列数が不正です（4列または5列である必要があります）。",
    #         code="invalid_column_count",
    #         field="row",
    #     )


    date_text, transaction_type_text, category_text, amount_text = row[:4]
    memo = row[4] if len(row) == 5 else ""
    return build_transaction(
        date_text=date_text,
        transaction_type_text=transaction_type_text,
        category_text=category_text,
        amount_text=amount_text,
        memo=memo,
    )
"""応用課題01 END

仕様通りに修正しよう。
"""