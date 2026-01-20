import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal, InvalidOperation
from datetime import date
import csv
from pathlib import Path

# Summary モジュールのインポートを試みる
try:
    from summary import Summary
except ImportError:
    Summary = None

#==== 定数定義 ====
# 支出カテゴリ
EXPENSE_CATEGORIES = [
    "食費", "日用品", "交通", "交際費", "娯楽",
    "住居", "光熱費", "医療", "教育", "貯金", "その他"
]

# 収入カテゴリ
INCOME_CATEGORIES = [
    "給与", "ボーナス", "副業", "投資", "その他収入"
]

# 取引種別
TRANSACTION_TYPES = ["支出", "収入"]

#==== ヘルパー関数 ====
# 金額表示フォーマット
def format_yen(value: Decimal) -> str:
    """金額を「¥1,234」形式で文字列化"""
    # 小数点なしで丸め（必要なら .quantize(Decimal("1"))）
    return f"¥{int(value):,}"

# 文字列をDecimalに変換
def parse_decimal(text: str) -> Decimal:
    """文字列をDecimalに変換（空白や¥、カンマ許容）"""
    normalized = text.replace("¥", "").replace(",", "").strip()
    if normalized == "":
        raise InvalidOperation("empty")
    return Decimal(normalized)

#==== メインアプリケーションクラス ====
class KakeiboApp(tk.Tk):
    def __init__(self):
        """アプリケーション初期化
        
        ウィンドウサイズ・タイトル設定、データ構造（items辞書）初期化、
        UI構築を実行。
        """
        super().__init__()
        self.title("家計簿（支出管理・一覧・合計）")
        self.geometry("820x560")
        self.minsize(760, 520)

        # データ保持（Treeviewのiidをキー、値は辞書）
        self.items = {}
        self.editing_iid = None  # 編集対象の行（Noneなら追加モード）

        self._build_ui()

    # ==== UI 構築 ====
    def _build_ui(self):
        """UI全体を構築
        
        収支入力フォーム（支出/収入選択、日付、カテゴリ、金額、メモ）、
        一覧表示（Treeview）、操作ボタン（CSV保存/読込、統計、削除）、
        合計表示を生成。
        """
        # 入力フォーム枠
        form = ttk.LabelFrame(self, text="収支入力")
        form.pack(fill="x", padx=12, pady=(12, 6))

        # グリッド列の設定
        form.columnconfigure(1, weight=0)  # 入力欄1
        form.columnconfigure(3, weight=0)  # 入力欄2
        form.columnconfigure(4, weight=1)  # メモ欄（伸縮）

        # Row 0: 支出/収入
        self.type_var = tk.StringVar(value=TRANSACTION_TYPES[0])
        radio_frame = ttk.Frame(form)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=8)
        for t_type in TRANSACTION_TYPES:
            tk.Radiobutton(radio_frame, text=t_type, variable=self.type_var, value=t_type, 
                          command=self._on_type_changed).pack(side="left", padx=3)

        # Row 0: 日付
        ttk.Label(form, text="日付").grid(row=0, column=2, sticky="e", padx=(20, 6), pady=8)
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(form, textvariable=self.date_var, width=15).grid(row=0, column=3, sticky="w", padx=6, pady=8)

        # Row 1: カテゴリ
        ttk.Label(form, text="カテゴリ").grid(row=1, column=0, sticky="e", padx=6, pady=8)
        self.category_var = tk.StringVar(value=EXPENSE_CATEGORIES[0])
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var, values=EXPENSE_CATEGORIES, width=18, state="readonly")
        self.category_combo.grid(row=1, column=1, sticky="w", padx=6, pady=8)

        # Row 1: 金額
        ttk.Label(form, text="金額").grid(row=1, column=2, sticky="e", padx=(20, 6), pady=8)
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var, width=15).grid(row=1, column=3, sticky="w", padx=6, pady=8)

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
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        columns = ("date", "type", "category", "price", "memo")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12,
            selectmode="extended"
        )
        self.tree.heading("date", text="日付")
        self.tree.heading("type", text="種類")
        self.tree.heading("category", text="カテゴリ")
        self.tree.heading("price", text="金額")
        self.tree.heading("memo", text="メモ")

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

        # ダブルクリックで編集モードへ
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # 操作ボタン行
        ops = ttk.Frame(self)
        ops.pack(fill="x", padx=12, pady=(0, 6))

        # 左側ボタン
        left_ops = ttk.Frame(ops)
        left_ops.pack(side="left")

        # CSV保存
        ttk.Button(left_ops, text="CSV保存", command=self.on_export_csv)\
            .pack(side="left", padx=(0, 6))
        # CSV読込
        ttk.Button(left_ops, text="CSV読込", command=self.on_import_csv)\
            .pack(side="left", padx=(0, 6))
        # 統計表示
        ttk.Button(left_ops, text="統計", command=self.on_show_summary)\
            .pack(side="left", padx=(0, 6))

        # 右側ボタン（危険操作）
        right_ops = ttk.Frame(ops)
        right_ops.pack(side="right")

        # 選択削除
        ttk.Button(right_ops, text="選択削除", command=self.on_delete_selected)\
            .pack(side="right", padx=(6, 16))

        # 合計表示
        total_frame = ttk.Frame(self)
        total_frame.pack(fill="x", padx=12, pady=(0, 12))

        # 合計ラベル
        ttk.Label(total_frame, text="合計：", font=("Segoe UI", 12, "bold"))\
            .pack(side="left")
        self.total_var = tk.StringVar(value="¥0")
        # 合計金額表示
        ttk.Label(total_frame, textvariable=self.total_var, font=("Segoe UI", 12, "bold"))\
            .pack(side="left")
        self.detail_var = tk.StringVar(value="")
        # 支出/収入内訳表示
        ttk.Label(total_frame, textvariable=self.detail_var, font=("Segoe UI", 11))\
            .pack(side="left", padx=(12, 0))

    # ==== イベントハンドラ ====
    def _on_type_changed(self):
        """支出/収入が変更された時にカテゴリを更新"""
        transaction_type = self.type_var.get()
        if transaction_type == "支出":
            categories = EXPENSE_CATEGORIES
            default_category = EXPENSE_CATEGORIES[0]
        else:  # 収入
            categories = INCOME_CATEGORIES
            default_category = INCOME_CATEGORIES[0]
        
        # Comboboxの値を更新
        self.category_combo.configure(values=categories)
        self.category_var.set(default_category)
    
    def on_add_or_update(self):
        """取引データを追加または更新
        
        フォーム入力をバリデーション（日付形式、金額数値、種別確認）、
        ペイロード作成、Treeviewに新規行追加または既存行更新、
        合計を再計算、フォームをクリア。
        """
        # 種別バリデーション
        transaction_type = self.type_var.get().strip()
        if transaction_type not in TRANSACTION_TYPES:
            messagebox.showwarning("入力エラー", "種類を選択してください（支出/収入）。")
            return

        # 日付バリデーション
        date_str = self.date_var.get().strip()
        try:
            date.fromisoformat(date_str)
        except Exception:
            messagebox.showwarning("入力エラー", "日付は YYYY-MM-DD 形式で入力してください。")
            return

        # カテゴリバリデーション
        categories = EXPENSE_CATEGORIES if transaction_type == "支出" else INCOME_CATEGORIES
        category = self.category_var.get().strip() or categories[0]
        if category not in categories:
            category = categories[0]

        # 金額バリデーション
        try:
            price = parse_decimal(self.price_var.get())
            if price < 0:
                raise InvalidOperation("negative")
        except Exception:
            messagebox.showwarning("入力エラー", "金額は0以上の数値で入力してください。（例：1234 または ¥1,234）")
            return

        # メモ取得
        memo = self.memo_entry.get("1.0", tk.END).strip()

        # ペイロード作成
        payload = {
            "date": date_str,
            "transaction_type": transaction_type,
            "category": category or "その他",
            "price": price,
            "memo": memo
        }

        # 追加または更新処理
        if self.editing_iid is None:
            # 追加モード
            iid = self.tree.insert(
                "", "end",
                values=(
                    payload["date"],
                    payload["transaction_type"],
                    payload["category"],
                    format_yen(payload["price"]),
                    payload["memo"]
                )
            )
            self.items[iid] = payload
        else:
            # 更新モード
            iid = self.editing_iid
            self.items[iid] = payload
            self.tree.item(
                iid,
                values=(
                    payload["date"],
                    payload["transaction_type"],
                    payload["category"],
                    format_yen(payload["price"]),
                    payload["memo"]
                )
            )
            self._exit_edit_mode() # 編集モード終了

        self._update_total() # 合計再計算
        self.on_clear_inputs() # フォームクリア

    def on_clear_inputs(self):
        """入力フォームをリセット
        
        金額・日付・カテゴリ・メモをクリア、支出を選択状態に戻す、
        編集モードを終了。
        """
        self.price_var.set("") # 金額クリア
        self.type_var.set(TRANSACTION_TYPES[0]) # 支出に戻す
        self._on_type_changed()  # 種別を支出に戻した際にコンボボックスの選択肢も初期化
        self.date_var.set(date.today().isoformat()) # 日付を今日に戻す
        self.memo_entry.delete("1.0", tk.END) # メモクリア

        # 追加モードに戻す（編集中ならキャンセル）
        self._exit_edit_mode()

    def on_tree_double_click(self, event):
        """行をダブルクリックして編集モードに遷移
        
        クリック行のデータをitems辞書から取得、フォームに反映、
        ボタンラベルを「追加」から「更新」に変更。
        """
        iid = self.tree.focus()
        if not iid:
            return
        data = self.items.get(iid)
        if not data:
            return

        self.editing_iid = iid 
        self.add_update_btn.configure(text="更新") # ボタンラベル変更

        # 入力に反映
        self.price_var.set(str(data["price"]))
        self.type_var.set(data["transaction_type"])
        self._on_type_changed()  # カテゴリリストを種別に合わせて更新
        self.category_var.set(data["category"])
        self.date_var.set(data["date"])
        self.memo_entry.delete("1.0", tk.END)
        self.memo_entry.insert("1.0", data.get("memo", ""))

    def _exit_edit_mode(self):
        """編集モードを終了
        
        編集対象IDをクリア、追加ボタンのラベルを「追加」に戻す。
        """
        self.editing_iid = None
        self.add_update_btn.configure(text="追加")

    def on_delete_selected(self):
        """選択行を削除
        
        選択確認ダイアログを表示、確認後にTreeviewとitems辞書から削除、
        編集中なら編集モードを終了、合計を再計算。
        """
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("削除", "削除する行を選択してください。")
            return

        if not messagebox.askyesno("確認", f"{len(selection)}件を削除しますか？"):
            return

        for iid in selection:
            if iid in self.items:
                del self.items[iid]
            self.tree.delete(iid)

        # 編集中の行が削除された場合は追加モードへ
        if self.editing_iid in selection:
            self._exit_edit_mode()
            self.on_clear_inputs()

        self._update_total()

    def _update_total(self):
        """合計金額を再計算（支出と収入を別々に計算し、ネット値を表示）"""
        expense = Decimal(0)
        income = Decimal(0)
        for item in self.items.values():
            if item["transaction_type"] == "支出":
                expense += item["price"]
            else:  # 収入
                income += item["price"]
        net = income - expense
        self.total_var.set(format_yen(net))
        self.detail_var.set(f"（支出: {format_yen(expense)} / 収入: {format_yen(income)}）")

    def on_show_summary(self):
        """統計画面（Summary）を開く
        
        pandas/matplotlib確認、データ存在確認、Summaryをモーダルで起動。
        """
        if not self.items:
            messagebox.showinfo("詳細", "表示するデータがありません。")
            return

        if Summary is None:
            messagebox.showwarning("詳細", "pandas または matplotlib がインストールされていません。\n" +
                                   "詳細表示機能を使用するには以下をインストールしてください:\n" +
                                   "pip install pandas matplotlib")
            return

        Summary(self, self.items)

    # ==== CSV 入出力 ====
    def on_export_csv(self):
        """現在のデータをCSVファイルに保存
        
        ファイル保存ダイアログを表示、ヘッダー行作成、
        Treeview全行をCSV形式で書き込み、完了メッセージ表示。
        """
        if not self.items:
            messagebox.showinfo("CSV保存", "保存するデータがありません。")
            return

        path = filedialog.asksaveasfilename(
            title="CSV保存",
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["日付", "種類", "カテゴリ", "金額", "メモ"])
                for iid in self.tree.get_children(""):
                    d = self.items[iid]
                    writer.writerow([
                        d["date"], d["transaction_type"], d["category"],
                        str(d["price"]), d.get("memo", "")
                    ])
            messagebox.showinfo("CSV保存", f"保存しました：\n{Path(path).name}")
        except Exception as e:
            messagebox.showerror("CSV保存エラー", f"保存に失敗しました。\n{e}")

    def on_import_csv(self):
        """CSVファイルからデータを読み込み
        
        ファイル選択ダイアログを表示、ヘッダー判定、各行をバリデーション
        （日付形式・種別・金額の検証）、Treeviewに追加、合計を再計算。
        """
        path = filedialog.askopenfilename(
            title="CSV読込",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        if not path:
            return

        try:
            added = 0
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            # ヘッダー判定
            start_idx = 0
            if rows and rows[0][:4] == ["日付", "種類", "カテゴリ", "金額"]:
                start_idx = 1

            for row in rows[start_idx:]:
                if len(row) < 4:
                    continue
                date_str, transaction_type, category, price_s = row[:4]
                memo = row[4] if len(row) > 4 else ""
                
                # バリデーション
                date_str = date_str.strip()
                try:
                    date.fromisoformat(date_str)
                except Exception:
                    continue
                
                transaction_type = transaction_type.strip()
                if transaction_type not in TRANSACTION_TYPES:
                    continue
                
                try:
                    price = parse_decimal(price_s)
                    if price < 0:
                        raise InvalidOperation("negative")
                except Exception:
                    continue
                
                categories = EXPENSE_CATEGORIES if transaction_type == "支出" else INCOME_CATEGORIES
                category = category.strip() or categories[0]
                if category not in categories:
                    category = categories[0]

                payload = {
                    "date": date_str,
                    "transaction_type": transaction_type,
                    "category": category,
                    "price": price,
                    "memo": memo.strip()
                }
                iid = self.tree.insert(
                    "", "end",
                    values=(
                        payload["date"],
                        payload["transaction_type"],
                        payload["category"],
                        format_yen(payload["price"]),
                        payload["memo"]
                    )
                )
                self.items[iid] = payload
                added += 1

            self._update_total()
            messagebox.showinfo("CSV読込", f"{added}件読み込みました。")
        except Exception as e:
            messagebox.showerror("CSV読込エラー", f"読込に失敗しました。\n{e}")


def main():
    """アプリケーション起動
    
    DPI認識設定（Windows向け）、KakeiboAppインスタンス生成、
    スタイル適用、メインループ実行。
    """
    try:
        # DPI 設定（失敗しても無視）
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        app = KakeiboApp()
        style = ttk.Style(app)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        app.mainloop()
    except Exception as e:
        import traceback
        print("起動時に例外が発生しました：", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()