"""UI層 - メイン画面のイベント処理"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import date
from pathlib import Path

from ...constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES
from ...formatters import format_yen
from ...validators import build_transaction_from_form, build_transaction_from_row


def on_sort_column(app, col: str) -> None:
    """列ヘッダーをクリックしてソート"""
    if app.sort_column == col:
        app.sort_reverse = not app.sort_reverse
    else:
        app.sort_column = col
        app.sort_reverse = False

    apply_sort(app)


def apply_sort(app) -> None:
    """現在のソート設定を適用"""
    if not app.sort_column:
        return

    # 列名とキーのマッピング
    key_map = {
        "date": "date",
        "type": "transaction_type",
        "category": "category",
        "price": "price",
        "memo": "memo",
    }

    col = app.sort_column
    items_list = [(iid, app.manager.get_transaction(iid)) for iid in app.tree.get_children("")]

    # マッピングされたキーでソート
    key = key_map[col]
    items_list.sort(key=lambda x: x[1][key], reverse=app.sort_reverse)

    for idx, (iid, _) in enumerate(items_list):
        app.tree.move(iid, "", idx)

    for c in ("date", "type", "category", "price", "memo"):
        app.tree.heading(c, text=app._get_heading_text(c))


def on_type_changed(app) -> None:
    """支出/収入が変更された時にカテゴリを更新"""
    transaction_type = app.type_var.get()
    if transaction_type == "支出":
        categories = EXPENSE_CATEGORIES
        default_category = EXPENSE_CATEGORIES[0]
    else:
        categories = INCOME_CATEGORIES
        default_category = INCOME_CATEGORIES[0]

    app.category_combo.configure(values=categories)
    app.category_var.set(default_category)


def on_add_or_update(app) -> None:
    """取引データを追加または更新

    バリデーション実行 → Transaction オブジェクト生成 →
    TransactionManager に登録 → Treeview 更新 → 合計再計算
    """
    try:
        transaction = build_transaction_from_form(
            app.date_var.get().strip(),
            app.type_var.get(),
            app.category_var.get(),
            app.price_var.get(),
            app.memo_entry.get("1.0", tk.END),
            EXPENSE_CATEGORIES,
            INCOME_CATEGORIES,
            TRANSACTION_TYPES,
        )
    except ValueError as e:
        error_code = str(e).strip("'\"")
        messages = {
            "empty": "日付を入力してください。",
            "format_error": "日付は YYYY/MM/DD 形式で入力してください。\n（例：2026/01/20）",
            "invalid_date": "有効な日付を入力してください。\n（例：2月29日などが存在しない場合）",
            "invalid_type": "種類を選択してください（支出/収入）。",
            "invalid_price": "金額は数値で入力してください。（例：1234 または ¥1,234）",
            "negative_price": "金額は1以上の数値で入力してください。（例：1234 または ¥1,234）",
        }
        messagebox.showwarning("入力エラー", messages.get(error_code, "入力に誤りがあります。"))
        return

    # 追加または更新
    if app.editing_iid is None:
        # 追加モード
        iid = app.tree.insert(
            "",
            "end",
            values=(
                transaction.date,
                transaction.transaction_type,
                transaction.category,
                format_yen(transaction.price),
                transaction.memo,
            ),
        )
        app.manager.add_transaction(iid, transaction)
        added_iid = iid
    else:
        # 更新モード
        iid = app.editing_iid
        app.manager.update_transaction(iid, transaction)
        app.tree.item(
            iid,
            values=(
                transaction.date,
                transaction.transaction_type,
                transaction.category,
                format_yen(transaction.price),
                transaction.memo,
            ),
        )
        exit_edit_mode(app)
        added_iid = None

    update_total(app)
    apply_sort(app)

    # 追加された行にフォーカスを当てる
    if added_iid:
        app.tree.focus(added_iid)
        app.tree.selection_set(added_iid)
        app.tree.see(added_iid)

    on_clear_inputs(app)


def on_clear_inputs(app) -> None:
    """入力フォームをリセット"""
    app.price_var.set("")
    app.type_var.set(TRANSACTION_TYPES[0])
    on_type_changed(app)
    app.date_var.set(date.today().strftime("%Y/%m/%d"))
    app.memo_entry.delete("1.0", tk.END)
    exit_edit_mode(app)


def on_tree_double_click(app, event) -> None:
    """行をダブルクリックして編集モードに遷移"""
    iid = app.tree.focus()
    if not iid:
        return
    data = app.manager.get_transaction(iid)
    if not data:
        return

    app.editing_iid = iid
    app.add_update_btn.configure(text="更新")

    app.price_var.set(str(data["price"]))
    app.type_var.set(data["transaction_type"])
    on_type_changed(app)
    app.category_var.set(data["category"])
    app.date_var.set(data["date"])
    app.memo_entry.delete("1.0", tk.END)
    app.memo_entry.insert("1.0", data.get("memo", ""))


def exit_edit_mode(app) -> None:
    """編集モードを終了"""
    app.editing_iid = None
    app.add_update_btn.configure(text="追加")


def on_delete_selected(app) -> None:
    """選択行を削除"""
    selection = app.tree.selection()
    if not selection:
        messagebox.showinfo("削除", "削除する行を選択してください。")
        return

    if not messagebox.askyesno("確認", f"{len(selection)}件を削除しますか？"):
        return

    for iid in selection:
        app.manager.delete_transaction(iid)
        app.tree.delete(iid)

    if app.editing_iid in selection:
        exit_edit_mode(app)
        on_clear_inputs(app)

    update_total(app)
    apply_sort(app)


def update_total(app) -> None:
    """合計金額を再計算（TransactionManager を使用）"""
    expense, income, net = app.manager.calculate_totals()
    app.total_var.set(format_yen(net))
    app.detail_var.set(f"（支出: {format_yen(expense)} / 収入: {format_yen(income)}）")


def on_show_summary(app) -> None:
    """統計画面（Summary）を開く"""
    if not app.manager.get_all_items():
        messagebox.showinfo("詳細", "表示するデータがありません。")
        return

    try:
        from ..summary.view import Summary
        Summary(app, app.manager.get_all_items())
    except ImportError:
        messagebox.showwarning(
            "詳細",
            "pandas または matplotlib がインストールされていません。\n"
            "詳細表示機能を使用するには以下をインストールしてください:\n"
            "pip install pandas matplotlib",
        )
        return


def on_export_csv(app) -> None:
    """現在のデータを CSV ファイルに保存"""
    if not app.manager.get_all_items():
        messagebox.showinfo("保存", "保存するデータがありません。")
        return

    path = filedialog.asksaveasfilename(
        title="保存",
        defaultextension=".csv",
        filetypes=[("データファイル", "*.csv"), ("すべてのファイル", "*.*")],
    )
    if not path:
        return

    try:
        app.manager.export_csv(path)
        messagebox.showinfo("保存", f"保存しました：\n{Path(path).name}")
    except Exception as e:
        messagebox.showerror("保存エラー", f"保存に失敗しました。\n{e}")


def on_import_csv(app) -> None:
    """CSV ファイルからデータを読み込み"""
    path = filedialog.askopenfilename(
        title="一括取込",
        filetypes=[("データファイル", "*.csv"), ("すべてのファイル", "*.*")],
    )
    if not path:
        return

    try:
        added, invalid, transactions = app.manager.import_csv(
            path,
            lambda row: build_transaction_from_row(
                row,
                EXPENSE_CATEGORIES,
                INCOME_CATEGORIES,
                TRANSACTION_TYPES,
            ),
        )

        for transaction in transactions:
            iid = app.tree.insert(
                "",
                "end",
                values=(
                    transaction.date,
                    transaction.transaction_type,
                    transaction.category,
                    format_yen(transaction.price),
                    transaction.memo,
                ),
            )
            app.manager.add_transaction(iid, transaction)

        update_total(app)
        apply_sort(app)

        message = f"{added}件取り込みました。"
        if invalid > 0:
            message += f"\n無効なデータ: {invalid}件"
        messagebox.showinfo("一括取込", message)
    except Exception as e:
        messagebox.showerror("取込エラー", f"取込に失敗しました。\n{e}")
