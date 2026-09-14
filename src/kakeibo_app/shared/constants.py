"""カテゴリと取引種別の定義"""

# 支出カテゴリ
EXPENSE_CATEGORIES = [
    "食費", "日用品", "交通", "交際費", "娯楽",
    "住居", "光熱費", "医療", "教育", "貯金", "その他"
]

# 収入カテゴリ
INCOME_CATEGORIES = [
    "給与", "ボーナス", "副業", "投資", "その他収入"
]

# 取引種別。値の集合は shared.models.TransactionType（Literal）と一致させること。
TRANSACTION_TYPES = ["支出", "収入"]
