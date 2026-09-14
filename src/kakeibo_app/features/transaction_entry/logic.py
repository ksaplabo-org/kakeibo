"""メイン画面のイベント処理

責務：GUIイベントから純粋ロジック（validation・repository・balance）への橋渡し。
Treeview はここでは表示専用として扱い、業務データは常に Repository から取得する
（Treeview の表示内容を読み取ってデータを復元することはしない）。
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Callable

from ...shared import csv_storage
from ...shared.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES
from ...shared.formatters import format_yen, format_sort_heading
from ...shared.models import Transaction
from ...shared.validation import ValidationError, build_transaction

# 型ヒントのためだけの import（循環インポートを避けるため実行時は読み込まない）
if TYPE_CHECKING:
    from .view import MainWindow

# Treeview の列とその見出しラベル
_COLUMN_LABELS: dict[str, str] = {
    "date": "日付",
    "type": "種類",
    "category": "カテゴリ",
    "amount": "金額",
    "memo": "メモ",
}

# 列名 -> Transaction からソートキーを取り出す関数
_SORT_KEYS: dict[str, Callable[[Transaction], object]] = {
    "date": lambda transaction: transaction.date,
    "type": lambda transaction: transaction.transaction_type,
    "category": lambda transaction: transaction.category,
    "amount": lambda transaction: transaction.amount,
    "memo": lambda transaction: transaction.memo,
}


def _to_display_row(transaction: Transaction) -> tuple[str, str, str, str, str]:
    """Transaction を Treeview の表示行（文字列のタプル）に変換する"""
    return (
        transaction.date.strftime("%Y/%m/%d"),
        transaction.transaction_type,
        transaction.category,
        format_yen(transaction.amount),
        transaction.memo,
    )


def _heading_text(app: MainWindow, column: str) -> str:
    """列ヘッダのテキストを取得する（ソート状態を含む）"""
    label = _COLUMN_LABELS[column]
    return format_sort_heading(label, active=(app.sort_column == column), reverse=app.sort_reverse)


def refresh_list(app: MainWindow) -> None:
    """Repository の現在のデータから Treeview を再構築する

    Treeview はここで組み立てられる表示専用の一覧であり、業務データの正本ではない。
    全件を一旦削除して再構築するため、再構築の前後で「なお存在する行」の選択状態と
    フォーカスは維持する（削除された等、既に存在しない行を無理に選択状態にはしない）。
    """
    # 再構築後も残る行だけ、選択状態を復元する対象として控えておく
    previous_selection = [
        iid for iid in app.tree.selection() if app.repository.get(int(iid)) is not None
    ]
    previous_focus = app.tree.focus()

    for iid in app.tree.get_children(""):
        app.tree.delete(iid)

    # 選択中の列に対応するソート基準を取得して並べ替え
    transactions_with_id = app.repository.get_all_with_id()
    key = _SORT_KEYS[app.sort_column]
    transactions_with_id.sort(key=lambda pair: key(pair[1]), reverse=app.sort_reverse)

    for transaction_id, transaction in transactions_with_id:
        app.tree.insert("", "end", iid=str(transaction_id), values=_to_display_row(transaction))

    for column in _COLUMN_LABELS:
        app.tree.heading(column, text=_heading_text(app, column))

    if previous_selection:
        app.tree.selection_set(previous_selection)
        app.tree.focus(previous_focus if previous_focus in previous_selection else previous_selection[0])


def _select_row(app: MainWindow, transaction_id: int) -> None:
    """指定した取引の行を選択・フォーカスし、見える位置までスクロールする

    対象の行が Treeview 上に存在しない場合は何もしない。
    """
    iid = str(transaction_id)
    if not app.tree.exists(iid):
        return
    app.tree.selection_set(iid)
    app.tree.focus(iid)
    app.tree.see(iid)


def refresh_totals(app: MainWindow) -> None:
    """合計表示を Repository の現在のデータから再計算する"""
    expense, income, net = app.repository.calculate_totals()
    app.total_var.set(format_yen(net))
    app.total_label.configure(foreground="red" if net < 0 else "black")
    app.detail_var.set(f"（支出: {format_yen(expense)} / 収入: {format_yen(income)}）")


def refresh_derived_display(app: MainWindow) -> None:
    """一覧・合計など、Repository から導かれる表示をまとめて再構築する

    データを変更する処理（追加・更新・削除・取込）は、最後に必ずこの1関数を呼ぶ。
    """
    refresh_list(app)
    refresh_totals(app)


def on_sort_column(app: MainWindow, column: str) -> None:
    """列ヘッダをクリックしてソートする"""
    if app.sort_column == column:
        app.sort_reverse = not app.sort_reverse
    else:
        app.sort_column = column
        app.sort_reverse = False
    refresh_list(app)


def on_type_changed(app: MainWindow) -> None:
    """支出/収入が変更された時にカテゴリを更新する"""
    transaction_type = app.type_var.get()
    if transaction_type == "支出":
        categories = EXPENSE_CATEGORIES
    else:
        categories = INCOME_CATEGORIES
    app.category_combo.configure(values=categories)
    app.category_var.set(categories[0])


def _enter_edit_mode(app: MainWindow, transaction_id: int, transaction: Transaction) -> None:
    """編集モードに入る（フォームは Repository から取得した Transaction で埋める）"""
    app.editing_id = transaction_id
    app.add_update_button.configure(text="更新")

    app.amount_var.set(str(transaction.amount))
    app.type_var.set(transaction.transaction_type)
    on_type_changed(app)
    app.category_var.set(transaction.category)
    app.date_var.set(transaction.date.strftime("%Y/%m/%d"))
    app.memo_entry.delete("1.0", tk.END)
    app.memo_entry.insert("1.0", transaction.memo)


def exit_edit_mode(app: MainWindow) -> None:
    """編集モードを終了する"""
    app.editing_id = None
    app.add_update_button.configure(text="追加")


def on_add_or_update(app: MainWindow) -> None:
    """取引データを追加または更新する"""
    try:
        transaction = build_transaction(
            date_text=app.date_var.get(),
            transaction_type_text=app.type_var.get(),
            category_text=app.category_var.get(),
            amount_text=app.amount_var.get(),
            memo=app.memo_entry.get("1.0", tk.END),
        )
    except ValidationError as error:
        messagebox.showwarning("入力エラー", str(error))
        return

    if app.editing_id is None:
        affected_id = app.repository.add(transaction)
    else:
        affected_id = app.editing_id
        app.repository.update(affected_id, transaction)
        exit_edit_mode(app)

    refresh_derived_display(app)
    _select_row(app, affected_id)
    on_clear_inputs(app)


def on_clear_inputs(app: MainWindow) -> None:
    """入力フォームをリセットする"""
    app.amount_var.set("")
    app.type_var.set(TRANSACTION_TYPES[0])
    on_type_changed(app)
    app.date_var.set(date.today().strftime("%Y/%m/%d"))
    app.memo_entry.delete("1.0", tk.END)
    exit_edit_mode(app)


def on_tree_double_click(app: MainWindow, event: tk.Event) -> None:
    """行をダブルクリックして編集モードに遷移

    表示行ではなく Repository が保持する Transaction からフォームを組み立てる。
    列見出し（ソート操作）でのダブルクリックは対象外とする。
    """
    region = app.tree.identify_region(event.x, event.y)
    if region != "cell":
        return

    iid = app.tree.focus()
    if not iid:
        return
    transaction_id = int(iid)
    transaction = app.repository.get(transaction_id)
    if transaction is None:
        return
    _enter_edit_mode(app, transaction_id, transaction)


def on_delete_selected(app: MainWindow) -> None:
    """選択行を削除する"""
    selection = app.tree.selection()
    if not selection:
        messagebox.showinfo("削除", "削除する行を選択してください。")
        return

    if not messagebox.askyesno("確認", f"{len(selection)}件を削除しますか？"):
        return

    # 選択されている行のIDを取り出して削除
    selected_ids = {int(iid) for iid in selection}
    for transaction_id in selected_ids:
        app.repository.delete(transaction_id)

    if app.editing_id in selected_ids:
        exit_edit_mode(app)
        on_clear_inputs(app)

    refresh_derived_display(app)


def on_show_summary(app: MainWindow) -> None:
    """統計画面（SummaryWindow）を開く

    Repository 自身ではなく、その時点の独立したデータ（スナップショット）を渡す。
    """
    transactions = app.repository.get_all()
    if not transactions:
        messagebox.showinfo("詳細", "表示するデータがありません。")
        return

    # 統計画面を開くときだけ読み込む（pandas/matplotlib への依存を限定するため）
    from ..summary.view import SummaryWindow

    SummaryWindow(app, transactions)


def on_export_csv(app: MainWindow) -> None:
    """現在のデータを CSV ファイルに保存する"""
    transactions_with_id = app.repository.get_all_with_id()
    if not transactions_with_id:
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
        csv_storage.export_csv(transactions_with_id, path)
    except OSError as error:
        messagebox.showerror("保存エラー", f"保存に失敗しました。\n{error}")
        return

    messagebox.showinfo("保存", f"保存しました：\n{Path(path).name}")


def on_import_csv(app: MainWindow) -> None:
    """CSV ファイルからデータを読み込み

    ファイル全体の読み込み・検証が終わってから、成功した取引だけを Repository に反映する。
    ファイルI/Oの失敗（OSError）、文字コードの不一致（UnicodeDecodeError）、
    行単位の検証エラーは区別して扱う。
    """
    path = filedialog.askopenfilename(
        title="一括取込",
        filetypes=[("データファイル", "*.csv"), ("すべてのファイル", "*.*")],
    )
    if not path:
        return

    try:
        result = csv_storage.import_csv(path)
    except UnicodeDecodeError:
        messagebox.showerror(
            "取込エラー",
            "ファイルの文字コードを読み取れませんでした。\nUTF-8 で保存し直してから再度お試しください。",
        )
        return
    except OSError as error:
        messagebox.showerror("取込エラー", f"取込に失敗しました。\n{error}")
        return

    for transaction in result.transactions:
        app.repository.add(transaction)

    refresh_derived_display(app)

    message = f"{len(result.transactions)}件取り込みました。"
    if result.skipped_count:
        message += f"\n無効なデータ: {result.skipped_count}件"
    messagebox.showinfo("一括取込", message)
