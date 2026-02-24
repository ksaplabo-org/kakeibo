"""UI層 - メイン画面（入力フォーム、一覧表示、データ管理）"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from datetime import date

from ...constants import EXPENSE_CATEGORIES, TRANSACTION_TYPES
from ...models import TransactionManager
from .logic import (
    on_sort_column,
    apply_sort,
    on_type_changed,
    on_add_or_update,
    on_clear_inputs,
    on_tree_double_click,
    exit_edit_mode,
    on_delete_selected,
    update_total,
    on_show_summary,
    on_export_csv,
    on_import_csv,
)


class KakeiboApp(tk.Tk):
    """家計簿アプリケーションのメイン画面

    責務：
    - GUI 構築と表示（入力フォーム、一覧、ボタン）
    - ユーザーイベント処理（追加、編集、削除）
    - 画面更新

    ロジックは TransactionManager に委譲
    """

    # UI パディング定数
    FORM_PADX = 12
    FORM_PADY_TOP = (12, 6)
    FORM_PADY_NEXT = 8
    LABEL_PADX = (0, 6)
    BUTTON_PADX = 6

    def __init__(self):
        """アプリケーション初期化

        ウィンドウサイズ・タイトル設定、TransactionManager 初期化、UI 構築を実行。
        """
        super().__init__()
        self.title("家計簿")
        self.geometry("820x560")
        self.minsize(760, 520)

        # データ管理（UI と分離）
        self.manager = TransactionManager()

        # UI 状態管理
        self.editing_iid = None  # 編集対象の行（None なら追加モード）
        self.sort_column = "date"  # ソート中の列
        self.sort_reverse = False  # ソート方向（False=昇順、True=降順）

        self._build_ui()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    # ==== UI 構築 ====
    def _build_ui(self):
        """UI 全体を構築

        フォーム（種別、日付、カテゴリ、金額、メモ）、
        一覧表示（Treeview）、操作ボタン、合計表示を生成。
        """
        # 入力フォーム枠
        form = ttk.LabelFrame(self, text="収支入力")
        form.pack(fill="x", padx=self.FORM_PADX, pady=self.FORM_PADY_TOP)

        # グリッド列の設定
        form.columnconfigure(1, weight=0)
        form.columnconfigure(3, weight=0)
        form.columnconfigure(4, weight=1)

        # Row 0: 支出/収入
        self.type_var = tk.StringVar(value=TRANSACTION_TYPES[0])
        radio_frame = ttk.Frame(form)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=self.FORM_PADY_NEXT)
        for t_type in TRANSACTION_TYPES:
            tk.Radiobutton(
                radio_frame,
                text=t_type,
                variable=self.type_var,
                value=t_type,
                command=self._on_type_changed,
            ).pack(side="left", padx=3)

        # Row 0: 日付
        ttk.Label(form, text="日付").grid(row=0, column=2, sticky="e", padx=(20, 6), pady=self.FORM_PADY_NEXT)
        self.date_var = tk.StringVar(value=date.today().strftime("%Y/%m/%d"))
        ttk.Entry(form, textvariable=self.date_var, width=15).grid(row=0, column=3, sticky="w", padx=6, pady=self.FORM_PADY_NEXT)

        # Row 1: カテゴリ
        ttk.Label(form, text="カテゴリ").grid(row=1, column=0, sticky="e", padx=6, pady=self.FORM_PADY_NEXT)
        self.category_var = tk.StringVar(value=EXPENSE_CATEGORIES[0])
        self.category_combo = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=EXPENSE_CATEGORIES,
            width=18,
            state="readonly",
        )
        self.category_combo.grid(row=1, column=1, sticky="w", padx=6, pady=self.FORM_PADY_NEXT)

        # Row 1: 金額
        ttk.Label(form, text="金額").grid(row=1, column=2, sticky="e", padx=(20, 6), pady=self.FORM_PADY_NEXT)
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var, width=15).grid(row=1, column=3, sticky="w", padx=6, pady=self.FORM_PADY_NEXT)

        # Row 2: メモ
        ttk.Label(form, text="メモ").grid(row=2, column=0, sticky="ne", padx=6, pady=(8, 8))
        memo_entry = tk.Text(form, width=60, height=3)
        memo_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=6, pady=8)
        self.memo_entry = memo_entry

        # ボタン群（追加／更新、クリア）
        button_frame = ttk.Frame(form)
        button_frame.grid(row=2, column=4, sticky="sw", padx=6, pady=8)

        self.add_update_btn = ttk.Button(button_frame, text="追加", command=self.on_add_or_update)
        self.add_update_btn.pack(side="left", padx=3, pady=3)
        ttk.Button(button_frame, text="クリア", command=self.on_clear_inputs).pack(side="left", padx=3, pady=3)

        # 一覧（Treeview）
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=self.FORM_PADX, pady=(0, 6))

        columns = ("date", "type", "category", "price", "memo")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12, selectmode="extended")

        for col in columns:
            self.tree.heading(col, text=self._get_heading_text(col), command=lambda c=col: self.on_sort_column(c))

        self.tree.column("date", width=100, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("category", width=120, anchor="center")
        self.tree.column("price", width=100, anchor="e")
        self.tree.column("memo", width=300)

        # スクロールバー
        yscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # 操作ボタン行
        ops = ttk.Frame(self)
        ops.pack(fill="x", padx=self.FORM_PADX, pady=(0, 6))

        # 左側ボタン
        left_ops = ttk.Frame(ops)
        left_ops.pack(side="left")
        ttk.Button(left_ops, text="保存", command=self.on_export_csv).pack(side="left", padx=(0, 6))
        ttk.Button(left_ops, text="一括取込", command=self.on_import_csv).pack(side="left", padx=(0, 6))
        ttk.Button(left_ops, text="統計", command=self.on_show_summary).pack(side="left", padx=(0, 6))

        # 右側ボタン
        right_ops = ttk.Frame(ops)
        right_ops.pack(side="right")
        ttk.Button(right_ops, text="選択削除", command=self.on_delete_selected).pack(side="right", padx=(6, 16))

        # 合計表示
        total_frame = ttk.Frame(self)
        total_frame.pack(fill="x", padx=self.FORM_PADX, pady=(0, 12))

        base_font = tkfont.nametofont("TkDefaultFont")
        total_font = base_font.copy()
        total_font.configure(size=base_font.cget("size") + 2, weight="bold")
        detail_font = base_font.copy()
        detail_font.configure(size=base_font.cget("size") + 1)

        ttk.Label(total_frame, text="合計：", font=total_font).pack(side="left")
        self.total_var = tk.StringVar(value="¥0")
        ttk.Label(total_frame, textvariable=self.total_var, font=total_font).pack(side="left")
        self.detail_var = tk.StringVar(value="")
        ttk.Label(total_frame, textvariable=self.detail_var, font=detail_font).pack(side="left", padx=(12, 0))

        self._on_type_changed()

    # ==== ヘルパー関数 ====
    def _get_heading_text(self, col: str) -> str:
        """列ヘッダーのテキストを取得（ソート状態を含む）"""
        text_map = {
            "date": "日付", "type": "種類", "category": "カテゴリ", "price": "金額", "memo": "メモ"
        }
        text = text_map.get(col, col)
        if self.sort_column == col:
            indicator = "▼" if self.sort_reverse else "▲"
            text = f"{text} {indicator}"
        else:
            text = f"{text} ▲"
        return text

    # ==== イベントハンドラ ====
    def on_sort_column(self, col: str):
        """列ヘッダーをクリックしてソート"""
        on_sort_column(self, col)

    def _apply_sort(self):
        """現在のソート設定を適用"""
        apply_sort(self)

    def _on_type_changed(self):
        """支出/収入が変更された時にカテゴリを更新"""
        on_type_changed(self)

    def on_add_or_update(self):
        """取引データを追加または更新"""
        on_add_or_update(self)

    def on_clear_inputs(self):
        """入力フォームをリセット"""
        on_clear_inputs(self)

    def on_tree_double_click(self, event):
        """行をダブルクリックして編集モードに遷移"""
        on_tree_double_click(self, event)

    def _exit_edit_mode(self):
        """編集モードを終了"""
        exit_edit_mode(self)

    def on_delete_selected(self):
        """選択行を削除"""
        on_delete_selected(self)

    def _update_total(self):
        """合計金額を再計算（TransactionManager を使用）"""
        update_total(self)

    def on_show_summary(self):
        """統計画面（Summary）を開く"""
        on_show_summary(self)

    # ==== CSV 入出力 ====
    def on_export_csv(self):
        """現在のデータを CSV ファイルに保存"""
        on_export_csv(self)

    def on_import_csv(self):
        """CSV ファイルからデータを読み込み"""
        on_import_csv(self)
