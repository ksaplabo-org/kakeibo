import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans']
plt.rcParams['axes.unicode_minus'] = False

# 支出/収入の種別定義
TRANSACTION_TYPES = ["支出", "収入"]

# 統計表示ウィンドウクラス
class Summary(tk.Toplevel):
    """統計表示ウィンドウ"""
    def __init__(self, parent, items):
        """統計画面初期化
        
        モーダルウィンドウを設定、カテゴリ別・年別・月別タブを生成。
        各タブで独立した支出/収入フィルタを保持。
        """
        super().__init__(parent)
        self.title("統計表示")
        self.geometry("900x600")
        self.items = items

        # モーダルウィンドウに設定
        self.transient(parent)
        self.grab_set()

        # タブ作成（タブごとに独立したフィルタを持つ）
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self._create_category_tab()
        self._create_yearly_tab()
        self._create_monthly_tab()

    def _filtered_items(self, target):
        """種別でデータをフィルタ
        
        Args:
            target (文字列): 「支出」または「収入」
        
        Returns:
            list: 指定種別のみを抜き出したリスト
        """
        return [item for item in self.items.values() if item.get("transaction_type") == target]

    def _create_category_tab(self):
        """カテゴリ別タブを作成
        
        支出/収入フィルタラジオボタンを配置、初回表示を実行。
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="カテゴリ別")

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
                command=lambda: self._render_category_tab(body_frame, type_var)
            ).pack(side="left", padx=6)

        body_frame = ttk.Frame(tab)
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        body_frame.columnconfigure(0, weight=1)
        body_frame.rowconfigure(0, weight=1)
        body_frame.rowconfigure(1, weight=1)

        self._render_category_tab(body_frame, type_var)

    def _render_category_tab(self, body_frame, type_var):
        """カテゴリタブを再描画
        
        削除・再構成、種別フィルタ反映、テーブル・円グラフを描画。
        
        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        for child in body_frame.winfo_children():
            child.destroy()

        target = type_var.get()
        filtered = self._filtered_items(target)

        container = ttk.Frame(body_frame)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        df = pd.DataFrame([
            {"category": item["category"], "price": float(item["price"])}
            for item in filtered
        ])
        if df.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        category_sum = df.groupby("category")["price"].agg(["sum", "count"])
        category_sum.columns = ["合計", "件数"]
        category_sum["割合(%)"] = (category_sum["合計"] / category_sum["合計"].sum() * 100).round(1)
        category_sum = category_sum.sort_values("合計", ascending=False)

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        self._create_table(table_frame, category_sum, "カテゴリ")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew")
        title = f"カテゴリ別{target}"
        self._plot_pie_chart(chart_frame, category_sum, title)

    def _create_monthly_tab(self):
        """月別タブを作成
        
        支出/収入フィルタラジオボタンを配置、初回表示を実行。
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="月別")

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
                command=lambda: self._render_monthly_tab(body_frame, type_var)
            ).pack(side="left", padx=6)

        body_frame = ttk.Frame(tab)
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        body_frame.columnconfigure(0, weight=1)
        body_frame.rowconfigure(0, weight=1)
        body_frame.rowconfigure(1, weight=1)

        self._render_monthly_tab(body_frame, type_var)

    def _render_monthly_tab(self, body_frame, type_var):
        """月別タブを再描画
        
        削除・再構成、種別フィルタ反映、月別集計を計算、テーブル・棒グラフを描画。
        
        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        for child in body_frame.winfo_children():
            child.destroy()

        target = type_var.get()
        filtered = self._filtered_items(target)

        container = ttk.Frame(body_frame)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        df = pd.DataFrame([
            {"date": item["date"], "price": float(item["price"])}
            for item in filtered
        ])
        if df.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")
        monthly_sum = df.groupby("month")["price"].agg(["sum", "count"])
        monthly_sum.columns = ["合計", "件数"]
        monthly_sum = monthly_sum.sort_index()

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        self._create_table(table_frame, monthly_sum, "月")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew")
        title = f"月別{target}合計"
        self._plot_bar_chart(chart_frame, monthly_sum, title)

    def _create_yearly_tab(self):
        """年別タブを作成
        
        支出/収入フィルタラジオボタンを配置、初回表示を実行。
        """
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="年別")

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
                command=lambda: self._render_yearly_tab(body_frame, type_var)
            ).pack(side="left", padx=6)

        body_frame = ttk.Frame(tab)
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        body_frame.columnconfigure(0, weight=1)
        body_frame.rowconfigure(0, weight=1)
        body_frame.rowconfigure(1, weight=1)

        self._render_yearly_tab(body_frame, type_var)

    def _render_yearly_tab(self, body_frame, type_var):
        """年別タブを再描画
        
        削除・再構成、種別フィルタ反映、年別集計を計算、テーブル・棒グラフを描画。
        
        Args:
            body_frame: コンテンツを配置する親フレーム
            type_var (StringVar): 支出/収入ラジオボタンの値
        """
        for child in body_frame.winfo_children():
            child.destroy()

        target = type_var.get()
        filtered = self._filtered_items(target)

        container = ttk.Frame(body_frame)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        df = pd.DataFrame([
            {"date": item["date"], "price": float(item["price"])}
            for item in filtered
        ])
        if df.empty:
            ttk.Label(container, text=f"{target}データがありません").grid(row=0, column=0, sticky="nsew", pady=20)
            return

        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year.astype(str)
        yearly_sum = df.groupby("year")["price"].agg(["sum", "count"])
        yearly_sum.columns = ["合計", "件数"]
        yearly_sum = yearly_sum.sort_index()

        table_frame = ttk.Frame(container)
        table_frame.grid(row=0, column=0, sticky="nsew")
        self._create_table(table_frame, yearly_sum, "年")

        chart_frame = ttk.Frame(container)
        chart_frame.grid(row=1, column=0, sticky="nsew")
        title = f"年別{target}合計"
        self._plot_bar_chart(chart_frame, yearly_sum, title)

    def _create_table(self, parent, df, category_label="項目"):
        """Treeviewテーブルを表示
        
        パンダスDataFrameをテーブル形式で描画、詳細情報を読みやすく表示。
        
        Args:
            parent: テーブル配置親フレーム
            df: 集計結果パンダスデータフレーム
            category_label (文字列): 一番左の列名（「カテゴリ」「月」「年」）
        """
        columns = ["index"] + list(df.columns)
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        tree.heading("index", text=category_label)
        tree.column("index", width=100)

        for col in df.columns:
            if col == "合計":
                header = "合計金額(¥)"
            elif col == "件数":
                header = "件数"
            else:
                header = col
            tree.heading(col, text=header)
            tree.column(col, width=140)

        for idx, row in df.iterrows():
            values = [str(idx)] + [f"{val:,.0f}" if isinstance(val, (int, float)) else str(val) for val in row]
            tree.insert("", "end", values=values)

        # スクロールバー
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

    def _plot_pie_chart(self, parent, data, title):
        """円グラフを描画
        
        カテゴリ別の支出/収入割合を円グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。
        
        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        # 親フレームのサイズを更新
        parent.update_idletasks()
        width_pixels = max(parent.winfo_width(), 400)
        height_pixels = max(parent.winfo_height(), 300)

        # インチ単位に変換（DPI=100）
        figsize = (width_pixels / 100, height_pixels / 100)

        fig, ax = plt.subplots(figsize=figsize)
        ax.pie(data["合計"], labels=data.index, autopct="%1.1f%%", startangle=90)
        ax.set_title(title)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _plot_bar_chart(self, parent, data, title):
        """棒グラフを描画
        
        月別/年別集計を棒グラフで可視化、
        matplotlibを使用しTkinterキャンバスに描画。
        
        Args:
            parent: 描画領域フレーム
            data: 集計結果パンダスデータフレーム
            title (文字列): グラフタイトル
        """
        # 親フレームのサイズを更新
        parent.update_idletasks()
        width_pixels = max(parent.winfo_width(), 500)
        height_pixels = max(parent.winfo_height(), 300)

        # インチ単位に変換（DPI=100）
        figsize = (width_pixels / 100, height_pixels / 100)

        fig, ax = plt.subplots(figsize=figsize)
        data["合計"].plot(kind="bar", ax=ax)
        ax.set_title(title)
        ax.set_ylabel("金額")
        ax.set_xlabel("")
        plt.tight_layout()
        plt.xticks(rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
