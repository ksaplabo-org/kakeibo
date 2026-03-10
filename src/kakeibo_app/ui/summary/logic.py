"""統計表示の集計・テーブル連携ロジック"""

import pandas as pd


def filtered_items(items, target):
    """種別でデータをフィルタ"""
    # 指定された取引種別だけを抽出
    return [item for item in items.values() if item.get("transaction_type") == target]


def summarize_by_category(items, target):
    """カテゴリ別集計を返却"""
    filtered = filtered_items(items, target)
    df = pd.DataFrame(
        [{"category": item["category"], "price": float(item["price"])} for item in filtered]
    )
    if df.empty:
        # 表示側が扱いやすいよう列定義つきの空DataFrameを返す
        return pd.DataFrame(columns=["合計", "件数", "割合(%)"])

    # カテゴリ単位で合計金額と件数を算出
    category_sum = df.groupby("category")["price"].agg(["sum", "count"])
    category_sum.columns = ["合計", "件数"]
    # 全体に占める金額割合を追加
    category_sum["割合(%)"] = (category_sum["合計"] / category_sum["合計"].sum() * 100).round(1)
    return category_sum.sort_values("割合(%)", ascending=False)


def summarize_by_year(items, target):
    """年別集計を返却"""
    filtered = filtered_items(items, target)
    df = pd.DataFrame([{"date": item["date"], "price": float(item["price"])} for item in filtered])
    if df.empty:
        # 年別表示用の列を維持したまま空を返す
        return pd.DataFrame(columns=["合計", "件数"])

    # 日付を年キー（YYYY）へ変換
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year.astype(str)
    yearly_sum = df.groupby("year")["price"].agg(["sum", "count"])
    yearly_sum.columns = ["合計", "件数"]
    return yearly_sum.sort_index()


def summarize_by_month(items, target):
    """月別集計を返却"""
    filtered = filtered_items(items, target)
    df = pd.DataFrame([{"date": item["date"], "price": float(item["price"])} for item in filtered])
    if df.empty:
        # 月別表示用の列を維持したまま空を返す
        return pd.DataFrame(columns=["合計", "件数"])

    # 日付を月キー（YYYY-MM）へ変換
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    monthly_sum = df.groupby("month")["price"].agg(["sum", "count"])
    monthly_sum.columns = ["合計", "件数"]
    return monthly_sum.sort_index()


def update_table_headers(app, tree, columns, category_label, sort_state, df):
    """現在のソート状態で列ヘッダーを更新

    Args:
        app: Summaryビューインスタンス
        tree: 対象のTreeview
        columns (list[str]): 列名一覧
        category_label (str): index列の表示名
        sort_state (dict): ソート状態（column, reverse）
        df: 表示元のデータフレーム
    """
    for col in columns:
        tree.heading(
            col,
            text=app._get_table_header_text(col, category_label, sort_state),
            command=lambda c=col: app._on_table_sort(c, tree, columns, category_label, sort_state, df),
        )


def on_table_sort(app, col, tree, columns, category_label, sort_state, df):
    """テーブル列クリック時のソート処理

    Args:
        app: Summaryビューインスタンス
        col (str): クリックされた列名
        tree: 対象のTreeview
        columns (list[str]): 列名一覧
        category_label (str): index列の表示名
        sort_state (dict): ソート状態（column, reverse）
        df: 表示元のデータフレーム
    """
    if sort_state["column"] == col:
        sort_state["reverse"] = not sort_state["reverse"]
    else:
        sort_state["column"] = col
        sort_state["reverse"] = False

    sorted_items = app._build_sorted_items(df, columns, sort_state["column"], sort_state["reverse"])
    app._render_table_rows(tree, sorted_items)
    update_table_headers(app, tree, columns, category_label, sort_state, df)