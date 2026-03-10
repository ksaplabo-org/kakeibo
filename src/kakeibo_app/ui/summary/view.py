"""UI層 - 統計表示ウィンドウ（グラフ・集計表示）"""

from decimal import Decimal
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...constants import TRANSACTION_TYPES
from ...formatters import format_yen
from .logic import (
    on_table_sort,
    summarize_by_category,
    summarize_by_month,
    summarize_by_year,
    update_table_headers,
)


# matplotlib 設定（日本語フォント + 負の符号表示修正）
plt.rcParams["font.sans-serif"] = ["MS Gothic", "Hiragino Sans", "IPAexGothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


# 統計表示ウィンドウクラス
class Summary(tk.Toplevel):
    """統計表示ウィンドウ"""
    def __init__(self, parent, items):
        """統計画面初期化

        モーダルウィンドウを設定、カテゴリ別・年別・月別タブを生成。
        各タブで独立した支出/収入フィルタを保持。
        """
        super().__init__(parent)
        self.title("統計")
        self.geometry("900x600")
        self.items = items

        # モーダルウィンドウに設定
        self.transient(parent)
        self.grab_set()

        # タブ作成（タブごとに独立したフィルタを持つ）
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self._create_tab("カテゴリ別", self._render_category_tab)
        self._create_tab("年別", self._render_yearly_tab)
        self._create_tab("月別", self._render_monthly_tab)
        # self._create_tab("サンプル", self._render_sample_tab)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _create_tab(self, tab_name, renderer_method):
        """タブを作成し、支出/収入フィルタと本体を配置

        Args:
            tab_name (str): タブ名（「カテゴリ別」など）
            renderer_method: パラメータ (body_frame, type_var) を受け集計・描画するメソッド
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)

        type_var = tk.StringVar(value=TRANSACTION_TYPES[0])
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))
        # フィルタ選択UI（支出/収入ラジオボタン）
        ttk.Label(filter_frame, text="表示対象:").pack(side="left", padx=(0, 6))
        for t_type in TRANSACTION_TYPES:
            ttk.Radiobutton(
                filter_frame,
                text=t_type,
                value=t_type,
                variable=type_var,
                command=lambda: renderer_method(body_frame, type_var),
            ).pack(side="left", padx=6)

        body_frame = ttk.Frame(tab)
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        body_frame.columnconfigure(0, weight=1)
        # 選択された取引種別で集計・描画
        renderer_method(body_frame, type_var)

    def _prepare_render_frame(self, body_frame):
        """レンダリング用フレームを準備（前置き処理）

        既存の子ウィジェットを削除し、コンテナフレームを返却。
        テーブル行を150ピクセルに固定、グラフは残り全体を占有。

        Returns:
            ttk.Frame: 描画用コンテナフレーム
        """
        for child in body_frame.winfo_children():
            child.destroy()

        container = ttk.Frame(body_frame)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, minsize=150, weight=0)  # テーブル固定
        container.rowconfigure(1, minsize=350, weight=1)  # グラフは最小350に固定
        return container

    def _render_category_tab(self, body_frame, type_var):
        """カテゴリタブを再描画

        削除・再構成、種別フィルタ反映、テーブル・円グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        container = self._prepare_render_frame(body_frame)

        # 現在選択中の取引種別で再集計
        target = type_var.get()
        category_sum = summarize_by_category(self.items, target)
        # データがない場合はテーブル・グラフを描画せずメッセージ表示のみ
        if category_sum.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        # テーブルは割合(%)で初期ソート、クリックでソート切替可能
        self._create_table(table_frame, category_sum, "カテゴリ", initial_sort_column="割合(%)")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        # グラフタイトルに取引種別を含める
        title = f"カテゴリ別{target}"
        # 円グラフを描画
        self._plot_pie_chart(chart_frame, category_sum, title)


    def _render_yearly_tab(self, body_frame, type_var):
        """年別タブを再描画

        削除・再構成、種別フィルタ反映、年別集計を計算、テーブル・棒グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        container = self._prepare_render_frame(body_frame)

        # 現在選択中の取引種別で再集計
        target = type_var.get()
        yearly_sum = summarize_by_year(self.items, target)
        # データがない場合はテーブル・グラフを描画せずメッセージ表示のみ
        if yearly_sum.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        # テーブルは年（index）で初期ソート、クリックでソート切替可能
        self._create_table(table_frame, yearly_sum, "年", initial_sort_column="index")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        # グラフタイトルに取引種別を含める
        title = f"年別{target}合計"
        # 棒グラフを描画
        self._plot_bar_chart(chart_frame, yearly_sum, title)


    def _render_monthly_tab(self, body_frame, type_var):
        """月別タブを再描画

        削除・再構成、種別フィルタ反映、月別集計を計算、テーブル・棒グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        container = self._prepare_render_frame(body_frame)

        # 現在選択中の取引種別で再集計
        target = type_var.get()
        monthly_sum = summarize_by_month(self.items, target)
        # データがない場合はテーブル・グラフを描画せずメッセージ表示のみ
        if monthly_sum.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        # テーブルは月（index）で初期ソート、クリックでソート切替可能
        self._create_table(table_frame, monthly_sum, "月", initial_sort_column="index")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        # グラフタイトルに取引種別を含める
        title = f"月別{target}合計"
        # 棒グラフを描画
        self._plot_bar_chart(chart_frame, monthly_sum, title)


    # def _render_sample_tab(self, body_frame, type_var):
    #     """サンプルタブを再描画

    #     カテゴリ別と同じデータを使用、テーブルとグラフを左右に配置。

    #     Args:
    #         body_frame: コンテンツを配置する親フレーム
    #         type_var (StringVar): 支出/収入ラジオボタンの値
    #     """
    #     for child in body_frame.winfo_children():
    #         child.destroy()

    #     container = ttk.Frame(body_frame)
    #     container.grid(row=0, column=0, sticky="nsew")
    #     container.columnconfigure(0, weight=0, minsize=300)  # テーブル左、幅固定
    #     container.columnconfigure(1, weight=1)  # グラフ右、残り全体
    #     container.rowconfigure(0, weight=1)  # 行全体を縦いっぱいに使用

    #     target = type_var.get()
    #     category_sum = summarize_by_category(self.items, target)
    #     if category_sum.empty:
    #         ttk.Label(container, text=f"{target}データがありません").grid(
    #             row=0,
    #             column=0,
    #             columnspan=2,
    #             sticky="nsew",
    #             pady=20,
    #         )
    #         return

    #     table_frame = ttk.Frame(container)
    #     table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    #     self._create_table(table_frame, category_sum, "カテゴリ", initial_sort_column="割合(%)")

    #     chart_frame = ttk.Frame(container)
    #     chart_frame.grid(row=0, column=1, sticky="nsew")
    #     title = f"カテゴリ別{target}"
    #     self._plot_pie_chart(chart_frame, category_sum, title)

    #     body_frame.columnconfigure(0, weight=1)
    #     body_frame.rowconfigure(0, weight=1)


    def _create_table(self, parent, df, category_label="項目", initial_sort_column=None):
        """Treeviewテーブルを表示

        パンダスDataFrameをテーブル形式で描画、詳細情報を読みやすく表示。
        ソート機能付き。

        Args:
            parent: テーブル配置親フレーム
            df: 集計結果パンダスデータフレーム
            category_label (文字列): 一番左の列名（「カテゴリ」「月」「年」）
            initial_sort_column (文字列): 初期ソート列（"index", "割合(%)", なども）
        """
        columns = ["index"] + list(df.columns)
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        # 列ヘッダーの設定と初期ソート状態の適用
        default_column = initial_sort_column if initial_sort_column in columns else "index"
        sort_state = {"column": default_column, "reverse": False}
        # 現在のソート状態を反映した列ヘッダーテキストを更新
        self._update_table_headers(tree, columns, category_label, sort_state, df)

        tree.column("index", width=100, anchor="center")
        # データ列の幅と配置を設定
        for col in df.columns:
            if col in ["合計", "件数", "割合(%)"]:
                tree.column(col, width=140, anchor="e")
            else:
                tree.column(col, width=140, anchor="center")

        self._on_table_sort(default_column, tree, columns, category_label, sort_state, df)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

    def _setup_plot_canvas(self, parent, width_default=400):
        """グラフキャンバスサイズを計算・返却

        Args:
            parent: 描画領域フレーム
            width_default: デフォルト幅（ピクセル）

        Returns:
            tuple: (figsize, canvas関数に渡す parent)
        """
        parent.update()
        width_pixels = max(parent.winfo_width(), width_default)
        height_pixels = max(parent.winfo_height(), 300)
        return (width_pixels / 100, height_pixels / 100)

    def _draw_plot(self, parent, fig):
        """matplotlibキャンバスをTkinterに描画

        Args:
            parent: 描画領域フレーム
            fig: matplotlib figure
        """
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _plot_pie_chart(self, parent, data, title):
        """円グラフを描画

        カテゴリ別の支出/収入割合を円グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。

        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        figsize = self._setup_plot_canvas(parent, width_default=400)
        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)

        totals = data["合計"]
        percentages = (totals / totals.sum() * 100).round(1)
        legend_labels = [f"{cat} ({pct:.1f}%)" for cat, pct in zip(data.index, percentages)]

        ax.pie(totals, startangle=90)
        ax.set_title(title)
        ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
        self._draw_plot(parent, fig)

    def _plot_bar_chart(self, parent, data, title):
        """棒グラフを描画

        月別/年別集計を棒グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。

        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        figsize = self._setup_plot_canvas(parent, width_default=500)
        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        (data["合計"] / 1000).plot(kind="bar", ax=ax)
        ax.set_title(title)
        ax.set_ylabel("金額(千円)")
        ax.set_xlabel("")
        plt.xticks(rotation=45)
        self._draw_plot(parent, fig)

    # ==== ヘルパー関数 ====

    def _get_table_header_text(self, col, category_label, sort_state):
        """テーブル列ヘッダーテキストを生成

        Args:
            col (str): 列名
            category_label (str): index列の表示名
            sort_state (dict): ソート状態（column, reverse）
        """
        if col == "index":
            text = category_label
        elif col == "合計":
            text = "合計金額(¥)"
        elif col == "件数":
            text = "件数"
        else:
            text = col

        if sort_state["column"] == col:
            indicator = "▼" if sort_state["reverse"] else "▲"
            return f"{text} {indicator}"
        return f"{text} ▲"

    def _format_table_value(self, col, val):
        """テーブル表示用に値を整形

        Args:
            col (str): 列名
            val: 整形対象の値
        """
        if col == "合計" and isinstance(val, (int, float)):
            return format_yen(Decimal(str(val)))
        if col == "割合(%)" and isinstance(val, (int, float)):
            return f"{val:.1f}"
        if isinstance(val, (int, float)):
            return f"{int(val):,}"
        return str(val)

    def _build_sorted_items(self, df, columns, sort_column, reverse):
        """ソート済み行データを生成

        Args:
            df: ソート対象のデータフレーム
            columns (list[str]): 表示列一覧
            sort_column (str): ソート対象列
            reverse (bool): 降順フラグ
        """
        sorted_items = []
        for idx, row in df.iterrows():
            values = [str(idx)] + [self._format_table_value(c, val) for c, val in zip(df.columns, row)]
            sorted_items.append((idx, values, row))

        if sort_column == "index":
            sorted_items.sort(key=lambda x: str(x[0]), reverse=reverse)
        else:
            col_idx = columns.index(sort_column) - 1
            sorted_items.sort(
                key=lambda x: float(x[2].iloc[col_idx]) if isinstance(x[2].iloc[col_idx], (int, float)) else str(x[2].iloc[col_idx]),
                reverse=reverse,
            )
        return sorted_items

    def _render_table_rows(self, tree, sorted_items):
        """Treeviewの行を再描画

        Args:
            tree: 描画先のTreeview
            sorted_items (list): 表示順に並んだ行データ
        """
        for item in tree.get_children():
            tree.delete(item)
        for _, values, _ in sorted_items:
            tree.insert("", "end", values=values)

    def _update_table_headers(self, tree, columns, category_label, sort_state, df):
        """現在のソート状態で列ヘッダーを更新

        Args:
            tree: 対象のTreeview
            columns (list[str]): 列名一覧
            category_label (str): index列の表示名
            sort_state (dict): ソート状態（column, reverse）
            df: 表示元のデータフレーム
        """
        return update_table_headers(self, tree, columns, category_label, sort_state, df)

    # ==== イベントハンドラ ====

    def _on_table_sort(self, col, tree, columns, category_label, sort_state, df):
        """テーブル列クリック時のソート処理

        Args:
            col (str): クリックされた列名
            tree: 対象のTreeview
            columns (list[str]): 列名一覧
            category_label (str): index列の表示名
            sort_state (dict): ソート状態（column, reverse）
            df: 表示元のデータフレーム
        """
        return on_table_sort(self, col, tree, columns, category_label, sort_state, df)
