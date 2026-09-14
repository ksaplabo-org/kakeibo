"""統計表示ウィンドウ（タブ構成とフィルタ）"""

import tkinter as tk
from tkinter import ttk

from ...shared.constants import TRANSACTION_TYPES
from ...shared.formatters import format_month_label
from ...shared.models import Transaction
from .aggregation import available_months
from .logic import (
    SUMMARY_DISPLAY_TYPES,
    render_category_tab,
    render_monthly_tab,
    render_yearly_tab,
)

# 月範囲フィルタのコンボボックスで「絞り込まない」を表す選択肢
NO_MONTH_SELECTED = "(指定なし)"


class SummaryWindow(tk.Toplevel):
    """統計表示ウィンドウ

    parent から渡されるのは Repository 自身ではなく、その時点の独立した取引一覧
    （スナップショット）。開いたあとメイン画面のデータが変化しても、この
    ウィンドウの表示内容は自動更新しない。
    """

    def __init__(self, parent, transactions: list[Transaction]):
        """統計画面初期化

        モーダルウィンドウを設定、カテゴリ別・年別・月別タブを生成。
        月範囲フィルタは全タブ共通、支出/収入の表示対象はタブごとに保持する。
        """
        super().__init__(parent)
        self.title("統計")
        self.geometry("900x600")
        self.transactions: list[Transaction] = transactions

        # モーダルウィンドウに設定
        self.transient(parent)
        self.grab_set()

        # フィルタ変更時に全タブを描画し直すための再描画関数を貯めるリスト
        self._tab_renderers: list = []

        self._create_month_filter()

        # タブ作成（表示対象フィルタはタブごとに独立して持つ）
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._create_tab("カテゴリ別", render_category_tab, TRANSACTION_TYPES)
        self._create_tab("年別", render_yearly_tab, SUMMARY_DISPLAY_TYPES)
        self._create_tab("月別", render_monthly_tab, SUMMARY_DISPLAY_TYPES)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _create_month_filter(self) -> None:
        """全タブ共通の月範囲フィルタ（開始・終了のコンボボックス）を配置する

        選択肢は実データに存在する年月のみとし、存在しない月は選べないようにする。
        """
        # 表示ラベル（2026年1月）から内部の値（2026-01）を引くための対応表。
        # 年月の文字列形式は aggregation 側が決めるため、ここでは生成しない。
        self._month_options = {
            format_month_label(month): month for month in available_months(self.transactions)
        }
        choices = [NO_MONTH_SELECTED, *self._month_options]

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text="期間:").pack(side="left", padx=(0, 6))
        self.start_var = tk.StringVar(value=NO_MONTH_SELECTED)
        self.end_var = tk.StringVar(value=NO_MONTH_SELECTED)
        for label, variable in (("開始", self.start_var), ("終了", self.end_var)):
            ttk.Label(filter_frame, text=label).pack(side="left", padx=(6, 3))
            combobox = ttk.Combobox(
                filter_frame, textvariable=variable, values=choices, state="readonly", width=12
            )
            combobox.pack(side="left")
            combobox.bind("<<ComboboxSelected>>", lambda _event: self._render_all_tabs())

        ttk.Button(filter_frame, text="クリア", command=self._clear_month_filter).pack(
            side="left", padx=(12, 0)
        )

    @property
    def month_start(self) -> str | None:
        """絞り込みの開始年月（"2026-01" 形式）。指定なしの場合は None"""
        # 「(指定なし)」は対応表に無いため get が None を返す
        return self._month_options.get(self.start_var.get())

    @property
    def month_end(self) -> str | None:
        """絞り込みの終了年月（"2026-01" 形式）。指定なしの場合は None"""
        return self._month_options.get(self.end_var.get())

    def _clear_month_filter(self) -> None:
        """月範囲フィルタを指定なしに戻す"""
        self.start_var.set(NO_MONTH_SELECTED)
        self.end_var.set(NO_MONTH_SELECTED)
        self._render_all_tabs()

    def _render_all_tabs(self) -> None:
        """全タブを現在のフィルタ条件で描画し直す"""
        for render in self._tab_renderers:
            render()

    def _create_tab(self, tab_name, renderer, display_types):
        """タブを作成し、表示対象フィルタと本体を配置する

        Args:
            tab_name: タブ名（「カテゴリ別」など）
            renderer: (window, body_frame, type_var) を受け取り描画する関数
            display_types: 表示対象ラジオボタンの選択肢
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)

        # 表示対象（支出/収入/合計）の切り替えラジオボタン
        type_var = tk.StringVar(value=display_types[0])
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Label(filter_frame, text="表示対象:").pack(side="left", padx=(0, 6))

        # 表・グラフを描画する領域
        body_frame = ttk.Frame(tab)

        def render():
            renderer(self, body_frame, type_var)

        for display_type in display_types:
            ttk.Radiobutton(
                filter_frame,
                text=display_type,
                value=display_type,
                variable=type_var,
                command=render,
            ).pack(side="left", padx=6)

        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        body_frame.columnconfigure(0, weight=1)

        # フィルタ変更時にこのタブも描画し直せるよう登録しておく
        self._tab_renderers.append(render)

        # 初期表示として一度描画しておく
        render()
