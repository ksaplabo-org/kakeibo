"""バリデータ層 - 入力検証・型変換"""

import re
from decimal import Decimal, InvalidOperation
from datetime import date

from .models import Transaction


def parse_decimal(text: str) -> Decimal:
    """文字列をDecimalに変換（空白や¥、カンマ許容）
    
    Args:
        text (str): 変換対象文字列（「¥1,234」や「1234」形式対応）
    
    Returns:
        Decimal: 数値
    
    Raises:
        InvalidOperation: 入力が空の場合
    """
    normalized = text.replace("¥", "").replace(",", "").strip()
    if normalized == "":
        raise InvalidOperation("empty")
    return Decimal(normalized)


def parse_price(text: str) -> Decimal:
    """金額文字列を検証して Decimal に変換

    Args:
        text (str): 金額文字列（「¥1,234」や「1234」形式対応）

    Returns:
        Decimal: 検証済みの金額
    
    Raises:
        ValueError("invalid_price"): 数値として解釈できない
        ValueError("negative_price"): 1未満の金額
    """
    try:
        value = parse_decimal(text)
    except InvalidOperation as e:
        raise ValueError("invalid_price") from e
    if value < 1:
        raise ValueError("negative_price")
    return value


def parse_date(text: str) -> date:
    """文字列をYYYY/MM/DD形式の日付に変換
    
    Args:
        text (str): 日付文字列
    
    Returns:
        date: datetime.date オブジェクト
    
    Raises:
        ValueError("empty"): 入力が空の場合
        ValueError("format_error"): 形式が不正な場合
        ValueError("invalid_date"): 存在しない日付の場合
    """
    # 入力チェック
    text = text.strip()
    if not text:
        raise ValueError("empty")
    
    # フォーマットチェック
    if not re.fullmatch(r"^\d{4}/\d{2}/\d{2}$", text):
        raise ValueError("format_error")
    
    # 有効日付チェック
    parts = text.split("/")
    year_s, month_s, day_s = parts
    try:
        return date(int(year_s), int(month_s), int(day_s))
    except ValueError as e:
        raise ValueError("invalid_date") from e


def validate_transaction_type(text: str, transaction_types) -> str:
    """取引種別の検証

    Args:
        text (str): 入力された取引種別
        transaction_types: 許可する取引種別一覧

    Returns:
        str: 検証済みの取引種別
    
    Raises:
        ValueError("invalid_type"): 想定外の種別
    """
    value = text.strip()
    if value not in transaction_types:
        raise ValueError("invalid_type")
    return value


def normalize_category(
    category: str,
    transaction_type: str,
    expense_categories,
    income_categories,
) -> str:
    """カテゴリを正規化（空・不正は既定値に寄せる）

    Args:
        category (str): 入力カテゴリ
        transaction_type (str): 取引種別（支出/収入）
        expense_categories: 支出カテゴリ一覧
        income_categories: 収入カテゴリ一覧

    Returns:
        str: 正規化後カテゴリ
    """
    categories = expense_categories if transaction_type == "支出" else income_categories
    normalized = category.strip() if category else ""
    if not normalized or normalized not in categories:
        return categories[0]
    return normalized


def build_transaction_from_form(
    date_str: str,
    transaction_type: str,
    category: str,
    price_str: str,
    memo: str,
    expense_categories,
    income_categories,
    transaction_types,
) -> Transaction:
    """フォーム入力から Transaction を生成

    Args:
        date_str (str): 日付文字列（YYYY/MM/DD）
        transaction_type (str): 取引種別（支出/収入）
        category (str): 入力カテゴリ
        price_str (str): 金額文字列
        memo (str): メモ文字列
        expense_categories: 支出カテゴリ一覧
        income_categories: 収入カテゴリ一覧
        transaction_types: 許可する取引種別一覧

    Returns:
        Transaction: 検証済み取引オブジェクト

    Raises:
        ValueError: 各検証で不正入力の場合
    """
    # 日付の検証と変換
    parse_date(date_str)
    # 取引種別の検証
    validated_type = validate_transaction_type(transaction_type, transaction_types)
    # 金額の検証と変換
    price = parse_price(price_str)
    # 種別に応じてカテゴリを正規化
    normalized_category = normalize_category(
        category,
        validated_type,
        expense_categories,
        income_categories,
    )
    # メモは前後空白を除去して保持
    return Transaction(date_str, validated_type, normalized_category, price, memo.strip())


def build_transaction_from_row(
    row,
    expense_categories,
    income_categories,
    transaction_types,
) -> Transaction:
    """CSV 行から Transaction を生成

    Args:
        row: CSV の1行データ
        expense_categories: 支出カテゴリ一覧
        income_categories: 収入カテゴリ一覧
        transaction_types: 許可する取引種別一覧

    Returns:
        Transaction: 検証済み取引オブジェクト

    Raises:
        ValueError("insufficient_columns"): 必須列が不足している
        ValueError: フォーム変換時の検証エラー
    """
    if len(row) < 4:
        raise ValueError("insufficient_columns")

    # 行データをフォーム入力と同様に処理
    date_str, transaction_type, category, price_s = row[:4]
    memo = row[4] if len(row) > 4 else ""

    return build_transaction_from_form(
        date_str.strip(),
        transaction_type.strip(),
        category.strip(),
        price_s.strip(),
        memo.strip(),
        expense_categories,
        income_categories,
        transaction_types,
    )
