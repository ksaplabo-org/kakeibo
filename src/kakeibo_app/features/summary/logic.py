"""統計表示ウィンドウの描画処理

責務：Repository から渡されたスナップショット（Transaction のリスト）を
features.summary.aggregation の関数で集計し、その結果を
Treeview へのテーブル表示と matplotlib によるグラフとして描画する。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ...shared.constants import TRANSACTION_TYPES
from ...shared.formatters import (
    format_month_label,
    format_sort_heading,
    format_yen,
    format_year_label,
)
from .aggregation import (
    filter_by_month_range,
    filter_by_type,
    summarize_by_category,
    summarize_by_month,
    summarize_by_year,
    summarize_totals_by_month,
    summarize_totals_by_year,
)

if TYPE_CHECKING:
    from .view import SummaryWindow

# 日本語フォント設定。
# FigureCanvasTkAgg はウィジェットのリサイズ等をきっかけに after_idle で
# 非同期に再描画（draw_idle）することがあり、その再描画は呼び出し元の
# with 文（ローカルコンテキスト）を抜けた後に実行される。そのため
# mpl.rc_context で一時適用する方式だと、非同期再描画時にはフォント設定が
# 既定値（DejaVu Sans）に戻っており日本語が文字化けする。
# 本アプリは matplotlib を Tkinter への埋め込み専用に使うため、
# プロセス全体の設定として import 時に一度だけ適用する。
_FONT_RC = {
    "font.sans-serif": ["MS Gothic", "Hiragino Sans", "IPAexGothic", "sans-serif"],
    "axes.unicode_minus": False,
}
mpl.rcParams.update(_FONT_RC)

# 集計結果のうち、円書式（¥1,234）で表示し右寄せにする列
MONEY_COLUMNS = ("合計", "支出合計", "収入合計", "差額")

# 統計画面の「表示対象」選択肢。「合計」は取引種別ではなく統計画面だけの
# 表示オプションなので、ドメインの取引種別（shared.constants.TRANSACTION_TYPES、
# shared.models.TransactionType と一致必須）とは分けてここで定義する。
SUMMARY_TOTAL_LABEL = "合計"
SUMMARY_DISPLAY_TYPES = [*TRANSACTION_TYPES, SUMMARY_TOTAL_LABEL]


def reset_render_container(body_frame):
    """body_frame の子ウィジェットを全て破棄し、新しい描画用フレームを生成する"""
    for child in body_frame.winfo_children():
        child.destroy()

    container = ttk.Frame(body_frame)
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, minsize=150, weight=0)  # テーブル固定
    container.rowconfigure(1, minsize=350, weight=1)  # グラフは最小350に固定
    return container


def _show_empty_message(container, transaction_type: str) -> None:
    """データが無いことを示すメッセージを表示する"""
    # 「合計」は種別名ではないため、「合計データが〜」とならないよう空にする
    label = "" if transaction_type == SUMMARY_TOTAL_LABEL else transaction_type
    ttk.Label(container, text=f"{label}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)


def _transactions_in_range(window: SummaryWindow) -> list:
    """ウィンドウ共通の月範囲フィルタを適用した取引一覧を返す"""
    return filter_by_month_range(window.transactions, window.month_start, window.month_end)


def render_category_tab(window: SummaryWindow, body_frame: tk.Frame, type_var: tk.StringVar) -> None:
    """カテゴリタブを再描画する"""
    container = reset_render_container(body_frame)

    transaction_type = type_var.get()
    filtered = filter_by_type(_transactions_in_range(window), transaction_type)
    category_sum = summarize_by_category(filtered)
    if category_sum.empty:
        _show_empty_message(container, transaction_type)
        return

    table_frame = ttk.Frame(container)
    table_frame.grid(row=0, column=0, sticky="nsew")
    build_summary_table(table_frame, category_sum, "カテゴリ", initial_sort_column="割合(%)")

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
    plot_pie_chart(chart_frame, category_sum, f"カテゴリ別{transaction_type}")


def _render_period_tab(
    window: SummaryWindow,
    body_frame: tk.Frame,
    type_var: tk.StringVar,
    *,
    period_label: str,
    index_formatter,
    summarize,
    summarize_totals,
) -> None:
    """月別・年別タブを再描画する（期間の粒度だけが異なる共通処理）

    表示対象が「合計」のときは種別で絞らず、支出・収入・差額をまとめて集計し、
    差額の推移を折れ線グラフで表示する。
    """
    container = reset_render_container(body_frame)

    transaction_type = type_var.get()
    in_range = _transactions_in_range(window)
    is_total = transaction_type == SUMMARY_TOTAL_LABEL

    if is_total:
        summary = summarize_totals(in_range)
    else:
        summary = summarize(filter_by_type(in_range, transaction_type))
    if summary.empty:
        _show_empty_message(container, transaction_type)
        return

    table_frame = ttk.Frame(container)
    table_frame.grid(row=0, column=0, sticky="nsew")
    build_summary_table(
        table_frame,
        summary,
        period_label,
        initial_sort_column="index",
        index_formatter=index_formatter,
    )

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
    # グラフのX軸ラベルも「2026年1月」形式にするため、表示用に index を変換する
    chart_data = summary.rename(index=index_formatter)
    if is_total:
        plot_net_line_chart(chart_frame, chart_data, f"{period_label}別収支差額")
    else:
        plot_bar_chart(chart_frame, chart_data, f"{period_label}別{transaction_type}合計")


def render_monthly_tab(window: SummaryWindow, body_frame: tk.Frame, type_var: tk.StringVar) -> None:
    """月別タブを再描画する"""
    _render_period_tab(
        window,
        body_frame,
        type_var,
        period_label="月",
        index_formatter=format_month_label,
        summarize=summarize_by_month,
        summarize_totals=summarize_totals_by_month,
    )


def render_yearly_tab(window: SummaryWindow, body_frame: tk.Frame, type_var: tk.StringVar) -> None:
    """年別タブを再描画する"""
    _render_period_tab(
        window,
        body_frame,
        type_var,
        period_label="年",
        index_formatter=format_year_label,
        summarize=summarize_by_year,
        summarize_totals=summarize_totals_by_year,
    )


def build_summary_table(
    parent, data, category_label="項目", initial_sort_column="index", index_formatter=None
):
    """集計結果（data）を Treeview テーブルとして表示する

    列名 "index" は data.index（カテゴリ名や年月）を指す特別な列として扱う。
    index_formatter を渡すと、index 列の表示文字列のみをその関数で変換する
    （ソートは変換前の元の値で行われるため、並び順は変わらない）。
    """
    format_index = index_formatter or str
    columns = ["index"] + list(data.columns)
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)

    sort_column = initial_sort_column
    sort_reverse = False

    # 列見出しの文字列を組み立てる
    def get_header_text(column):
        if column == "index":
            text = category_label
        elif column == "合計":
            text = "合計金額(¥)"
        elif column in MONEY_COLUMNS:
            text = f"{column}(¥)"
        elif column == "件数":
            text = "件数"
        else:
            text = column
        return format_sort_heading(text, active=(sort_column == column), reverse=sort_reverse)

    # 列ごとに値の表示形式を変える
    def format_value(column, value):
        if column in MONEY_COLUMNS and isinstance(value, (int, float)):
            return format_yen(int(value))
        elif column == "割合(%)" and isinstance(value, (int, float)):
            return f"{value:.1f}"
        elif isinstance(value, (int, float)):
            return f"{int(value):,}"
        else:
            return str(value)

    # 列ヘッダクリック時にテーブルを並べ替える
    def on_sort(column):
        nonlocal sort_column, sort_reverse
        # 同じ列を再度クリックしたら昇順/降順を反転
        if sort_column == column:
            sort_reverse = not sort_reverse
        else:
            sort_column = column
            sort_reverse = False

        # 表示用の行データを組み立て直す
        sorted_rows = []
        for row_index, row in data.iterrows():
            values = [format_index(row_index)] + [
                format_value(data_column, value)
                for data_column, value in zip(data.columns, row)
            ]
            sorted_rows.append((row_index, values, row))

        if sort_column == "index":
            sorted_rows.sort(key=lambda entry: str(entry[0]), reverse=sort_reverse)
        else:
            column_index = columns.index(sort_column) - 1
            sorted_rows.sort(
                key=lambda entry: (
                    float(entry[2].iloc[column_index])
                    if isinstance(entry[2].iloc[column_index], (int, float))
                    else str(entry[2].iloc[column_index])
                ),
                reverse=sort_reverse,
            )

        # 一旦全行を削除してから並べ替え後の内容を挿入し直す
        for item in tree.get_children():
            tree.delete(item)
        for _, values, _ in sorted_rows:
            tree.insert("", "end", values=values)

        for heading_column in columns:
            tree.heading(heading_column, text=get_header_text(heading_column))

    for column in columns:
        tree.heading(column, command=lambda bound_column=column: on_sort(bound_column))

    tree.column("index", width=100, anchor="center")
    for column in data.columns:
        if column in MONEY_COLUMNS or column in ("件数", "割合(%)"):
            tree.column(column, width=140, anchor="e")
        else:
            tree.column(column, width=140, anchor="center")

    on_sort(sort_column)

    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)


def _calculate_figure_size(parent, width_default: int) -> tuple[float, float]:
    """グラフキャンバスサイズ（インチ）を計算する"""
    # 表示中の実際の幅・高さを取得するために画面を確定させる
    parent.update()
    width_pixels = max(parent.winfo_width(), width_default)
    height_pixels = max(parent.winfo_height(), 300)
    return (width_pixels / 100, height_pixels / 100)


def embed_figure(parent, fig: Figure) -> None:
    """matplotlib Figure を Tkinter キャンバスに描画する

    pyplot（plt.subplots 等）を使わず Figure を直接生成しているため、
    グローバルな Figure レジストリに登録されない。キャンバスウィジェットが
    破棄されれば Figure も参照を失い、明示的な close は不要。
    """
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def plot_pie_chart(parent, data, title) -> None:
    """円グラフを描画する"""
    fig = Figure(figsize=_calculate_figure_size(parent, width_default=400), constrained_layout=True)
    ax = fig.add_subplot(111)

    """発展課題01 START

    円グラフを正しく描画させる
    """
    totals = data["合計"]
    # percentages = (totals / totals.sum() * 100).round(1)
    # 凡例に表示する「カテゴリ名 (割合%)」のラベルを作成
    legend_labels = [
    """ここに記載する"""
    ]
    """発展課題01 END

    円グラフを正しく描画させる
    """

    ax.pie(totals, startangle=90)
    ax.set_title(title)
    ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    embed_figure(parent, fig)


def plot_bar_chart(parent, data, title) -> None:
    """棒グラフを描画する"""
    fig = Figure(figsize=_calculate_figure_size(parent, width_default=500), constrained_layout=True)
    ax = fig.add_subplot(111)

    # 金額を千円単位にして棒グラフを描画
    (data["合計"] / 1000).plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_ylabel("金額(千円)")
    ax.set_xlabel("")
    # X軸のラベルを斜めにして見やすくする
    """発展課題02 START

    棒グラフのラベルを正しく描画させよう。
    補足：for文を用いて描画させる。
    """
    
    """ここに記載する"""

    """発展課題02 END

    棒グラフを正しく描画させる
    """


def plot_net_line_chart(parent, data, title) -> None:
    """差額（収入-支出）の推移を折れ線グラフで描画する"""
    fig = Figure(figsize=_calculate_figure_size(parent, width_default=500), constrained_layout=True)
    ax = fig.add_subplot(111)

    # 金額を千円単位にして折れ線グラフを描画
    net = data["差額"] / 1000
    net.plot(kind="line", ax=ax, marker="o", color="tab:blue")
    # プラスとマイナスの境目を示す基準線
    ax.axhline(0, color="gray", linewidth=0.8)
    # 赤字（マイナス）の期間が一目で分かるように基準線との間を赤く塗る
    ax.fill_between(
        range(len(net)), net, 0, where=(net < 0), color="tab:red", alpha=0.3, interpolate=True
    )
    ax.set_title(title)
    ax.set_ylabel("金額(千円)")
    ax.set_xlabel("")
    # X軸のラベルを斜めにして見やすくする
    for label in ax.get_xticklabels():
        label.set_rotation(45)
    embed_figure(parent, fig)
