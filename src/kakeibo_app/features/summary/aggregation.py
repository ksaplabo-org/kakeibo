"""統計表示専用の集計処理（pandas 依存）

pandas は本モジュールでのみ import する。通常の取引登録・CSV入出力の経路
（features/transaction_entry、shared/balance）は本モジュールに依存しない。
"""

import pandas as pd

from ...shared.models import Transaction

# 年月・年を表す期間キーの文字列形式。月範囲フィルタの値と月別集計の
# インデックスで同じ形式を使うため、本モジュールで一元管理する。
_MONTH_KEY_FORMAT = "%Y-%m"
_YEAR_KEY_FORMAT = "%Y"


def filter_by_type(transactions: list[Transaction], transaction_type: str) -> list[Transaction]:
    """種別でデータをフィルタする"""
    return [
        transaction
        for transaction in transactions
        if transaction.transaction_type == transaction_type
    ]


def available_months(transactions: list[Transaction]) -> list[str]:
    """データに存在する年月（"2026-01" 形式）を昇順の重複なしで返す

    月範囲フィルタの選択肢を組み立てるために使う。期間キーの文字列形式を
    本モジュールに閉じ込め、filter_by_month_range に渡す値と必ず同じ形式に
    そろえる目的で、画面側ではなくここで生成する。
    """
    return sorted({transaction.date.strftime(_MONTH_KEY_FORMAT) for transaction in transactions})


def filter_by_month_range(
    transactions: list[Transaction],
    start: str | None = None,
    end: str | None = None,
) -> list[Transaction]:
    """年月の範囲でデータを絞り込む

    Args:
        transactions: 絞り込み対象
        start: 開始年月（"2026-01" 形式）。None なら下限なし
        end: 終了年月（"2026-03" 形式）。None なら上限なし

    Returns:
        start・end を含む範囲内の取引のみのリスト。
        両方 None の場合は全件を返す。
    """
    # "%Y-%m" はゼロ埋めされるため、辞書順の比較がそのまま年月の前後関係になる
    return [
        transaction
        for transaction in transactions
        if (start is None or transaction.date.strftime(_MONTH_KEY_FORMAT) >= start)
        and (end is None or transaction.date.strftime(_MONTH_KEY_FORMAT) <= end)
    ]


def summarize_by_category(transactions: list[Transaction]) -> pd.DataFrame:
    """カテゴリ別の合計・件数・割合を計算する

    Returns:
        割合の降順の DataFrame。transactions が空の場合は列を持たない
        空 DataFrame（df.empty が True）を返すため、呼び出し側は必ず
        empty で分岐すること。
    """
    # 取引データを表形式に変換
    data = pd.DataFrame(
        [
            {"category": transaction.category, "amount": transaction.amount}
            for transaction in transactions
        ]
    )
    if data.empty:
        return data

    # カテゴリ別に合計と件数を集計
    result = data.groupby("category")["amount"].agg(["sum", "count"])
    result.columns = ["合計", "件数"]
    # 割合(%)の列を追加
    result["割合(%)"] = (result["合計"] / result["合計"].sum() * 100).round(1)
    # 割合の大きい順に並べ替え
    return result.sort_values("割合(%)", ascending=False)


def summarize_by_month(transactions: list[Transaction]) -> pd.DataFrame:
    """月別の合計・件数を計算する

    Returns:
        年月の昇順の DataFrame。空入力時の戻り値は summarize_by_category を参照。
    """
    # 日付を「年-月」の文字列に変換
    data = pd.DataFrame(
        [
            {"month": transaction.date.strftime(_MONTH_KEY_FORMAT), "amount": transaction.amount}
            for transaction in transactions
        ]
    )
    if data.empty:
        return data

    # 月別に合計と件数を集計
    result = data.groupby("month")["amount"].agg(["sum", "count"])
    result.columns = ["合計", "件数"]
    # 年月の昇順に並べ替え
    return result.sort_index()


def summarize_by_year(transactions: list[Transaction]) -> pd.DataFrame:
    """年別の合計・件数を計算する

    Returns:
        年の昇順の DataFrame。空入力時の戻り値は summarize_by_category を参照。
    """
    # 日付を「年」の文字列に変換
    data = pd.DataFrame(
        [
            {"year": str(transaction.date.year), "amount": transaction.amount}
            for transaction in transactions
        ]
    )
    if data.empty:
        return data

    # 年別に合計と件数を集計
    result = data.groupby("year")["amount"].agg(["sum", "count"])
    result.columns = ["合計", "件数"]
    # 年の昇順に並べ替え
    return result.sort_index()


def _summarize_totals(transactions: list[Transaction], period_format: str) -> pd.DataFrame:
    """期間ごとに支出合計・収入合計・差額を計算する（月別・年別の共通処理）

    filter_by_type で種別を絞らず、支出と収入を同時に集計する点が
    summarize_by_month / summarize_by_year との違い。

    Args:
        transactions: 集計対象
        period_format: 期間キーの strftime 書式（"%Y-%m" または "%Y"）
    """
    data = pd.DataFrame(
        [
            {
                "period": transaction.date.strftime(period_format),
                "type": transaction.transaction_type,
                "amount": transaction.amount,
            }
            for transaction in transactions
        ]
    )
    if data.empty:
        return data

    # 種別を列方向に展開する（期間 × 支出/収入 の表にする）
    result = data.pivot_table(
        index="period", columns="type", values="amount", aggfunc="sum", fill_value=0
    )
    # 片方の種別しか存在しない場合に列が欠けるため、必ず両方の列を用意する
    result = result.reindex(columns=["支出", "収入"], fill_value=0)
    result.columns = ["支出合計", "収入合計"]
    # 金額は支出・収入とも正の値で保持されているため、差額は引き算で求める
    result["差額"] = result["収入合計"] - result["支出合計"]
    # 期間の昇順に並べ替え
    return result.sort_index()


def summarize_totals_by_month(transactions: list[Transaction]) -> pd.DataFrame:
    """月別の支出合計・収入合計・差額を計算する

    Returns:
        年月の昇順の DataFrame。空入力時の戻り値は summarize_by_category を参照。
    """
    return _summarize_totals(transactions, _MONTH_KEY_FORMAT)


def summarize_totals_by_year(transactions: list[Transaction]) -> pd.DataFrame:
    """年別の支出合計・収入合計・差額を計算する

    Returns:
        年の昇順の DataFrame。空入力時の戻り値は summarize_by_category を参照。
    """
    return _summarize_totals(transactions, _YEAR_KEY_FORMAT)
