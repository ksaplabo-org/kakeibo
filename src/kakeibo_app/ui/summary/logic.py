"""UI層 - 統計表示ウィンドウの集計・描画処理"""

from decimal import Decimal
from tkinter import ttk

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...formatters import format_yen

# matplotlib 設定（日本語フォント + 負の符号表示修正）
plt.rcParams["font.sans-serif"] = ["MS Gothic", "Hiragino Sans", "IPAexGothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def filtered_items(app, target):
    """種別でデータをフィルタ"""
    return [item for item in app.items.values() if item.get("transaction_type") == target]


def prepare_render_frame(app, body_frame):
    """レンダリング用フレームを準備（前置き処理）"""
    for child in body_frame.winfo_children():
        child.destroy()

    container = ttk.Frame(body_frame)
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, minsize=150, weight=0)  # テーブル固定
    container.rowconfigure(1, minsize=350, weight=1)  # グラフは最小350に固定
    return container


def render_category_tab(app, body_frame, type_var):
    """カテゴリタブを再描画"""
    container = prepare_render_frame(app, body_frame)

    target = type_var.get()
    filtered = filtered_items(app, target)

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
    category_sum = category_sum.sort_values("割合(%)", ascending=False)

    table_frame = ttk.Frame(container)
    table_frame.grid(row=0, column=0, sticky="nsew")
    create_table(app, table_frame, category_sum, "カテゴリ", initial_sort_column="割合(%)")

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
    title = f"カテゴリ別{target}"
    plot_pie_chart(app, chart_frame, category_sum, title)


def render_monthly_tab(app, body_frame, type_var):
    """月別タブを再描画"""
    container = prepare_render_frame(app, body_frame)

    target = type_var.get()
    filtered = filtered_items(app, target)

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
    create_table(app, table_frame, monthly_sum, "月", initial_sort_column="index")

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
    title = f"月別{target}合計"
    plot_bar_chart(app, chart_frame, monthly_sum, title)


def render_yearly_tab(app, body_frame, type_var):
    """年別タブを再描画"""
    container = prepare_render_frame(app, body_frame)

    target = type_var.get()
    filtered = filtered_items(app, target)

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
    create_table(app, table_frame, yearly_sum, "年", initial_sort_column="index")

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
    title = f"年別{target}合計"
    plot_bar_chart(app, chart_frame, yearly_sum, title)


def render_sample_tab(app, body_frame, type_var):
    """サンプルタブを再描画"""
    for child in body_frame.winfo_children():
        child.destroy()

    container = ttk.Frame(body_frame)
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=0, minsize=300)  # テーブル左、幅固定
    container.columnconfigure(1, weight=1)  # グラフ右、残り全体
    container.rowconfigure(0, weight=1)  # 行全体を縦いっぱいに使用

    target = type_var.get()
    filtered = filtered_items(app, target)

    df = pd.DataFrame([
        {"category": item["category"], "price": float(item["price"])}
        for item in filtered
    ])
    if df.empty:
        ttk.Label(container, text=f"{target}データがありません").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=20,
        )
        return

    category_sum = df.groupby("category")["price"].agg(["sum", "count"])
    category_sum.columns = ["合計", "件数"]
    category_sum["割合(%)"] = (category_sum["合計"] / category_sum["合計"].sum() * 100).round(1)
    category_sum = category_sum.sort_values("割合(%)", ascending=False)

    table_frame = ttk.Frame(container)
    table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    create_table(app, table_frame, category_sum, "カテゴリ", initial_sort_column="割合(%)")

    chart_frame = ttk.Frame(container)
    chart_frame.grid(row=0, column=1, sticky="nsew")
    title = f"カテゴリ別{target}"
    plot_pie_chart(app, chart_frame, category_sum, title)

    body_frame.columnconfigure(0, weight=1)
    body_frame.rowconfigure(0, weight=1)


def create_table(app, parent, df, category_label="項目", initial_sort_column=None):
    """Treeviewテーブルを表示"""
    columns = ["index"] + list(df.columns)
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)

    # ソート状態を追跡
    sort_state = {"column": initial_sort_column, "reverse": False}

    # ヘッダーテキスト生成関数
    def get_header_text(col):
        if col == "index":
            text = category_label
        elif col == "合計":
            text = "合計金額(¥)"
        elif col == "件数":
            text = "件数"
        else:
            text = col

        # 全列に▲を常時表示
        if sort_state["column"] == col:
            indicator = "▼" if sort_state["reverse"] else "▲"
            text = f"{text} {indicator}"
        else:
            text = f"{text} ▲"
        return text

    # フォーマット関数（金額を¥フォーマットに）
    def format_value(col, val):
        if col == "合計" and isinstance(val, (int, float)):
            return format_yen(Decimal(str(val)))
        elif col == "割合(%)" and isinstance(val, (int, float)):
            return f"{val:.1f}"  # 小数点第1位で表示
        elif isinstance(val, (int, float)):
            return f"{int(val):,}"
        else:
            return str(val)

    # ソート関数
    def on_sort(col):
        if sort_state["column"] == col:
            sort_state["reverse"] = not sort_state["reverse"]
        else:
            sort_state["column"] = col
            sort_state["reverse"] = False

        # データを再ソート
        sorted_items = []
        for idx, row in df.iterrows():
            values = [str(idx)] + [format_value(c, val) for c, val in zip(df.columns, row)]
            sorted_items.append((idx, values, row))

        # ソート実行
        if col == "index":
            sorted_items.sort(key=lambda x: str(x[0]), reverse=sort_state["reverse"])
        else:
            col_idx = columns.index(col) - 1
            sorted_items.sort(
                key=lambda x: float(x[2].iloc[col_idx]) if isinstance(x[2].iloc[col_idx], (int, float)) else str(x[2].iloc[col_idx]),
                reverse=sort_state["reverse"],
            )

        # Treeviewを再構築
        for item in tree.get_children():
            tree.delete(item)
        for _, values, _ in sorted_items:
            tree.insert("", "end", values=values)

        # ヘッダーを更新
        for c in columns:
            tree.heading(c, text=get_header_text(c))

    # 列ヘッダーを設定
    for col in columns:
        tree.heading(col, text=get_header_text(col), command=lambda c=col: on_sort(c))

    # アンカー設定（メイン画面と統一）
    tree.column("index", width=100, anchor="center")
    for col in df.columns:
        if col in ["合計", "件数", "割合(%)"]:
            tree.column(col, width=140, anchor="e")  # 右寄せ
        else:
            tree.column(col, width=140, anchor="center")  # 中央寄せ

    # 初期ソートを実行（データ挿入も含まれる）
    on_sort(initial_sort_column)

    # スクロールバー
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)


def setup_plot_canvas(app, parent, width_default=400):
    """グラフキャンバスサイズを計算・返却"""
    parent.update()  # 完全なレイアウト更新
    width_pixels = max(parent.winfo_width(), width_default)
    height_pixels = max(parent.winfo_height(), 300)
    figsize = (width_pixels / 100, height_pixels / 100)
    return figsize


def draw_plot(app, parent, fig):
    """matplotlibキャンバスをTkinterに描画"""
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def plot_pie_chart(app, parent, data, title):
    """円グラフを描画"""
    figsize = setup_plot_canvas(app, parent, width_default=400)
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)

    # パーセンテージを計算
    totals = data["合計"]
    percentages = (totals / totals.sum() * 100).round(1)

    # 凡例ラベルを作成（カテゴリ名 + パーセンテージ）
    legend_labels = [f"{cat} ({pct:.1f}%)" for cat, pct in zip(data.index, percentages)]

    ax.pie(totals, startangle=90)
    ax.set_title(title)
    ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    draw_plot(app, parent, fig)


def plot_bar_chart(app, parent, data, title):
    """棒グラフを描画"""
    figsize = setup_plot_canvas(app, parent, width_default=500)
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    (data["合計"] / 1000).plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_ylabel("金額(千円)")
    ax.set_xlabel("")
    plt.xticks(rotation=45)
    draw_plot(app, parent, fig)
