"""メイン画面（入力フォーム、一覧表示）"""

import tkinter as tk
from datetime import date
from tkinter import font as tkfont
from tkinter import ttk

from ...shared.constants import EXPENSE_CATEGORIES, TRANSACTION_TYPES
from .logic import (
    on_add_or_update,
    on_clear_inputs,
    on_delete_selected,
    on_export_csv,
    on_import_csv,
    on_show_summary,
    on_sort_column,
    on_tree_double_click,
    on_type_changed,
    refresh_list,
)
from .repository import TransactionRepository


class MainWindow(tk.Tk):
    """家計簿アプリケーションのメイン画面

    責務：
    - GUI 構築と表示（入力フォーム、一覧、ボタン）
    - Tkinter イベントの受け口（実処理は logic モジュールへ委譲）

    業務データの保持・CRUD は TransactionRepository（Tkinter 非依存）に委譲する。
    Treeview は表示専用であり、業務データの正本は repository が持つ。
    """

    # UI パディング定数
    FORM_PADX = 12
    FORM_PADY_TOP = (12, 6)
    FORM_PADY_ROW = 8
    INNER_PADX = 6
    LABEL_PADX = (20, 6)
    BUTTON_PADX = 3
    BUTTON_PADY = 3

    def __init__(self):
        super().__init__()
        self.title("家計簿")
        self.geometry("820x560")

        self.repository = TransactionRepository()

        # UI 状態管理
        self.editing_id: int | None = None  # 編集対象の内部ID（None なら追加モード）
        self.sort_column = "date"  # ソート中の列
        self.sort_reverse = False  # ソート方向（False=昇順、True=降順）

        self._build_ui()
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _build_ui(self):
        """UI 全体を構築

        フォーム（種別、日付、カテゴリ、金額、メモ）、
        一覧表示（Treeview）、操作ボタン、合計表示を生成。
        """
        form = ttk.LabelFrame(self, text="収支入力")
        form.pack(fill="x", padx=self.FORM_PADX, pady=self.FORM_PADY_TOP)

        # グリッド列の設定
        form.columnconfigure(1, weight=0)
        form.columnconfigure(3, weight=0)
        form.columnconfigure(4, weight=1)

        # Row 0: 支出/収入
        self.type_var = tk.StringVar(value=TRANSACTION_TYPES[0])
        radio_frame = ttk.Frame(form)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)
        for transaction_type in TRANSACTION_TYPES:
            tk.Radiobutton(
                radio_frame,
                text=transaction_type,
                variable=self.type_var,
                value=transaction_type,
                command=lambda: on_type_changed(self),
            ).pack(side="left", padx=3)

        # Row 0: 日付
        ttk.Label(form, text="日付").grid(row=0, column=2, sticky="e", padx=self.LABEL_PADX, pady=self.FORM_PADY_ROW)
        self.date_var = tk.StringVar(value=date.today().strftime("%Y/%m/%d"))
        ttk.Entry(form, textvariable=self.date_var, width=15).grid(row=0, column=3, sticky="w", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)

        # Row 1: カテゴリ
        ttk.Label(form, text="カテゴリ").grid(row=1, column=0, sticky="e", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)
        self.category_var = tk.StringVar(value=EXPENSE_CATEGORIES[0])
        self.category_combo = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=EXPENSE_CATEGORIES,
            width=18,
            state="readonly",
        )
        self.category_combo.grid(row=1, column=1, sticky="w", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)

        # Row 1: 金額
        ttk.Label(form, text="金額").grid(row=1, column=2, sticky="e", padx=self.LABEL_PADX, pady=self.FORM_PADY_ROW)
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var, width=15).grid(row=1, column=3, sticky="w", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)

        # Row 2: メモ
        ttk.Label(form, text="メモ").grid(row=2, column=0, sticky="ne", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)
        memo_entry = tk.Text(form, width=60, height=3)
        memo_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)
        self.memo_entry = memo_entry

        # 追加・クリアボタン
        button_frame = ttk.Frame(form)
        button_frame.grid(row=2, column=4, sticky="sw", padx=self.INNER_PADX, pady=self.FORM_PADY_ROW)

        self.add_update_button = ttk.Button(button_frame, text="追加", command=lambda: on_add_or_update(self))
        self.add_update_button.pack(side="left", padx=self.BUTTON_PADX, pady=self.BUTTON_PADY)
        ttk.Button(button_frame, text="クリア", command=lambda: on_clear_inputs(self)).pack(side="left", padx=self.BUTTON_PADX, pady=self.BUTTON_PADY)

        # 取引一覧（Treeview）
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=self.FORM_PADX, pady=(0, 6))

        columns = ("date", "type", "category", "amount", "memo")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12, selectmode="extended")

        # 列見出しクリックでソート
        for column in columns:
            self.tree.heading(column, command=lambda bound_column=column: on_sort_column(self, bound_column))

        self.tree.column("date", width=100, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("category", width=120, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("memo", width=300)

        # 縦スクロールバー
        yscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # ダブルクリックで編集モードへ
        self.tree.bind("<Double-1>", lambda event: on_tree_double_click(self, event))

        # 保存・取込・統計・削除ボタン
        ops = ttk.Frame(self)
        ops.pack(fill="x", padx=self.FORM_PADX, pady=(0, 6))

        left_ops = ttk.Frame(ops)
        left_ops.pack(side="left")
        ttk.Button(left_ops, text="保存", command=lambda: on_export_csv(self)).pack(side="left", padx=(0, 6))
        ttk.Button(left_ops, text="一括取込", command=lambda: on_import_csv(self)).pack(side="left", padx=(0, 6))
        ttk.Button(left_ops, text="統計", command=lambda: on_show_summary(self)).pack(side="left", padx=(0, 6))

        right_ops = ttk.Frame(ops)
        right_ops.pack(side="right")
        ttk.Button(right_ops, text="選択削除", command=lambda: on_delete_selected(self)).pack(side="right", padx=(6, 16))

        # 合計金額の表示
        total_frame = ttk.Frame(self)
        total_frame.pack(fill="x", padx=self.FORM_PADX, pady=(0, 12))

        # 合計表示は標準フォントより少し大きくする
        base_font = tkfont.nametofont("TkDefaultFont")
        total_font = base_font.copy()
        total_font.configure(size=base_font.cget("size") + 2, weight="bold")
        detail_font = base_font.copy()
        detail_font.configure(size=base_font.cget("size") + 1)

        ttk.Label(total_frame, text="合計：", font=total_font).pack(side="left")
        self.total_var = tk.StringVar(value="¥0")
        self.total_label = ttk.Label(total_frame, textvariable=self.total_var, font=total_font)
        self.total_label.pack(side="left")
        self.detail_var = tk.StringVar(value="")
        ttk.Label(total_frame, textvariable=self.detail_var, font=detail_font).pack(side="left", padx=(12, 0))

        on_type_changed(self)
        refresh_list(self)
