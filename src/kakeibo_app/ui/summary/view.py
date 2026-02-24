"""UI層 - 統計表示ウィンドウ（グラフ・集計表示）"""

import tkinter as tk
from tkinter import ttk

from ...constants import TRANSACTION_TYPES
from .logic import (
    filtered_items,
    prepare_render_frame,
    render_category_tab,
    render_monthly_tab,
    render_yearly_tab,
    render_sample_tab,
    create_table,
    setup_plot_canvas,
    draw_plot,
    plot_pie_chart,
    plot_bar_chart,
)


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

    def _filtered_items(self, target):
        """種別でデータをフィルタ

        Args:
            target (文字列): 「支出」または「収入」

        Returns:
            list: 指定種別のみを抜き出したリスト
        """
        return filtered_items(self, target)

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

        renderer_method(body_frame, type_var)

    def _prepare_render_frame(self, body_frame):
        """レンダリング用フレームを準備（前置き処理）

        既存の子ウィジェットを削除し、コンテナフレームを返却。
        テーブル行を150ピクセルに固定、グラフは残り全体を占有。

        Returns:
            ttk.Frame: 描画用コンテナフレーム
        """
        return prepare_render_frame(self, body_frame)

    def _render_category_tab(self, body_frame, type_var):
        """カテゴリタブを再描画

        削除・再構成、種別フィルタ反映、テーブル・円グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        return render_category_tab(self, body_frame, type_var)

    def _render_monthly_tab(self, body_frame, type_var):
        """月別タブを再描画

        削除・再構成、種別フィルタ反映、月別集計を計算、テーブル・棒グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        return render_monthly_tab(self, body_frame, type_var)

    def _render_yearly_tab(self, body_frame, type_var):
        """年別タブを再描画

        削除・再構成、種別フィルタ反映、年別集計を計算、テーブル・棒グラフを描画。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        return render_yearly_tab(self, body_frame, type_var)

    def _render_sample_tab(self, body_frame, type_var):
        """サンプルタブを再描画

        カテゴリ別と同じデータを使用、テーブルとグラフを左右に配置。

        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        return render_sample_tab(self, body_frame, type_var)

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
        return create_table(self, parent, df, category_label, initial_sort_column)

    def _setup_plot_canvas(self, parent, width_default=400):
        """グラフキャンバスサイズを計算・返却

        Args:
            parent: 描画領域フレーム
            width_default: デフォルト幅（ピクセル）

        Returns:
            tuple: (figsize, canvas関数に渡す parent)
        """
        return setup_plot_canvas(self, parent, width_default)

    def _draw_plot(self, parent, fig):
        """matplotlibキャンバスをTkinterに描画

        Args:
            parent: 描画領域フレーム
            fig: matplotlib figure
        """
        return draw_plot(self, parent, fig)

    def _plot_pie_chart(self, parent, data, title):
        """円グラフを描画

        カテゴリ別の支出/収入割合を円グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。

        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        return plot_pie_chart(self, parent, data, title)

    def _plot_bar_chart(self, parent, data, title):
        """棒グラフを描画

        月別/年別集計を棒グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。

        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        return plot_bar_chart(self, parent, data, title)
