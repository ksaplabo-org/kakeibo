"""バリデータ層 - 入力検証・型変換"""

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
    parts = text.split("/")
    if len(parts) != 3:
        raise ValueError("format_error")
    for part in parts:
        if not part.isdigit():
            raise ValueError("format_error")
    
    # 有効日付チェック
    try:
        return date.fromisoformat(text.replace("/", "-"))
    except ValueError as e:
        if "month must be in" in str(e) or "day is out of range" in str(e):
            raise ValueError("invalid_date")
        else:
            raise ValueError("format_error")


def validate_transaction_type(text: str, transaction_types) -> str:
    """取引種別の検証
    
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
    """カテゴリを正規化（空・不正は既定値に寄せる）"""
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
    """フォーム入力から Transaction を生成"""
    parse_date(date_str)
    validated_type = validate_transaction_type(transaction_type, transaction_types)
    price = parse_price(price_str)
    normalized_category = normalize_category(
        category,
        validated_type,
        expense_categories,
        income_categories,
    )
    return Transaction(date_str, validated_type, normalized_category, price, memo.strip())


def build_transaction_from_row(
    row,
    expense_categories,
    income_categories,
    transaction_types,
) -> Transaction:
    """CSV 行から Transaction を生成"""
    if len(row) < 4:
        raise ValueError("insufficient_columns")

    date_str, transaction_type, category, price_s = row[:4]
    memo = row[4] if len(row) > 4 else ""

    return build_transaction_from_form(
        date_str.strip(),
        transaction_type,
        category,
        price_s,
        memo,
        expense_categories,
        income_categories,
        transaction_types,
    )
