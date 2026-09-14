"""features.transaction_entry の GUIイベント層に対する統合テスト

「ユーザー操作 → logic → Repository → Viewへの反映」という流れをカバーする。
Repository / Validation / CsvStorage 単体の仕様は既存テストで担保済みのため、
ここでは重複させず、GUI経由での配線と、ユーザーから見える振る舞い
（Treeviewの内容・選択状態・フォーカス）だけを検証する。

refresh_list() の選択・フォーカス維持そのものに対する狭いテストは
test_treeview_selection_regression.py 側に置く。
"""

import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import pytest

from kakeibo_app.features.transaction_entry import logic
from kakeibo_app.features.transaction_entry.repository import TransactionRepository

# _tk_root フィクスチャは tests/conftest.py で定義（Tkのルートはセッションで1つだけ生成する）


class _FakeEvent:
    """Treeview のダブルクリックイベントを模したスタブ（x, y座標は使用しない）"""

    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y


def _double_click_event_on_row(app, monkeypatch) -> _FakeEvent:
    """行（セル領域）でのダブルクリックを模す

    テスト用ウィンドウは withdraw() されており実ピクセル座標を持たないため、
    identify_region を "cell" 固定に差し替える。
    """
    monkeypatch.setattr(app.tree, "identify_region", lambda x, y: "cell")
    return _FakeEvent()


@pytest.fixture
def app(_tk_root, monkeypatch):
    # messagebox はモーダルダイアログを開くため、テストでは常に無害な応答に固定する。
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showwarning", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)

    # 各テストがまっさらな状態から始まるよう、業務データとUI状態をリセットする
    # （ウィンドウ自体は使い回すが、Repositoryとフォーム状態はテストごとに独立させる）
    _tk_root.repository = TransactionRepository()
    _tk_root.sort_column = "date"
    _tk_root.sort_reverse = False
    logic.exit_edit_mode(_tk_root)
    logic.on_clear_inputs(_tk_root)
    logic.refresh_list(_tk_root)

    return _tk_root


def _fill_and_submit(app, *, date_text, amount, memo="", transaction_type="支出", category="食費"):
    """フォームに値を入れて追加/更新ボタン相当のイベントを発火する"""
    app.type_var.set(transaction_type)
    logic.on_type_changed(app)
    app.category_var.set(category)
    app.date_var.set(date_text)
    app.amount_var.set(str(amount))
    app.memo_entry.delete("1.0", tk.END)
    app.memo_entry.insert("1.0", memo)
    logic.on_add_or_update(app)


def _latest_transaction_id(app) -> int:
    """直近に追加された取引のID（連番の最大値）を取得する"""
    return max(tid for tid, _ in app.repository.get_all_with_id())


# ---- 新規登録 ----

def test_register_new_transaction_reflects_in_repository_and_tree(app):
    _fill_and_submit(app, date_text="2026/01/20", amount=1500, memo="昼食")

    transactions = app.repository.get_all()
    assert len(transactions) == 1
    assert transactions[0].amount == 1500
    assert transactions[0].memo == "昼食"
    assert len(app.tree.get_children("")) == 1


def test_register_selects_and_reveals_the_new_row(app):
    """新規登録後、追加した行が選択される"""
    for i in range(1, 4):
        _fill_and_submit(app, date_text=f"2026/01/{i:02d}", amount=100 * i)

    # 新しい行が一覧の途中に挿入される並びにしておく（見落としやすい状況を再現）
    app.sort_column = "date"
    app.sort_reverse = True
    logic.refresh_list(app)

    _fill_and_submit(app, date_text="2026/02/15", amount=9999, memo="new")
    new_id = _latest_transaction_id(app)

    assert app.tree.selection() == (str(new_id),)
    assert app.tree.focus() == str(new_id)


# ---- 更新 ----

def test_update_existing_transaction_changes_value_and_keeps_row_selected(app, monkeypatch):
    """更新後、更新した行が選択されたままになる"""
    _fill_and_submit(app, date_text="2026/01/01", amount=100, memo="before")
    _fill_and_submit(app, date_text="2026/01/02", amount=200, memo="other")

    target_id = min(tid for tid, t in app.repository.get_all_with_id() if t.memo == "before")

    app.tree.selection_set(str(target_id))
    app.tree.focus(str(target_id))
    logic.on_tree_double_click(app, _double_click_event_on_row(app, monkeypatch))

    app.amount_var.set("500")
    app.memo_entry.delete("1.0", tk.END)
    app.memo_entry.insert("1.0", "updated")
    logic.on_add_or_update(app)

    updated = app.repository.get(target_id)
    assert updated.amount == 500
    assert updated.memo == "updated"
    assert app.tree.selection() == (str(target_id),)


def test_double_click_on_column_heading_does_not_clear_inputs_in_progress(app, monkeypatch):
    """列見出し（ソート操作）でのダブルクリックでは、入力中のフォームが上書きされない

    列ヘッダのソートはシングルクリックの command で完結する一方、
    Treeview 全体に張られた <Double-1> バインドはヘッダー領域でも発火しうる。
    その場合に編集モードへ入って入力中の内容を上書きしてしまわないことを確認する。
    """
    _fill_and_submit(app, date_text="2026/01/01", amount=100, memo="existing")

    app.amount_var.set("12345")
    app.memo_entry.delete("1.0", tk.END)
    app.memo_entry.insert("1.0", "入力中のメモ")

    monkeypatch.setattr(app.tree, "identify_region", lambda x, y: "heading")
    logic.on_tree_double_click(app, _FakeEvent())

    assert app.amount_var.get() == "12345"
    assert app.memo_entry.get("1.0", "end-1c") == "入力中のメモ"
    assert app.editing_id is None
    # 更新完了後は編集モードを抜けていること（既存仕様）
    assert app.editing_id is None
    assert app.add_update_button.cget("text") == "追加"


# ---- ソート ----

def test_sort_column_reorders_tree(app):
    _fill_and_submit(app, date_text="2026/01/03", amount=300)
    _fill_and_submit(app, date_text="2026/01/01", amount=100)
    _fill_and_submit(app, date_text="2026/01/02", amount=200)

    app.sort_column = "date"
    app.sort_reverse = False
    logic.refresh_list(app)

    dates = [app.tree.item(iid, "values")[0] for iid in app.tree.get_children("")]
    assert dates == ["2026/01/01", "2026/01/02", "2026/01/03"]


def test_sort_column_preserves_selection(app):
    """ソート後も選択していた取引が選択されたままになる"""
    _fill_and_submit(app, date_text="2026/01/03", amount=300)
    _fill_and_submit(app, date_text="2026/01/01", amount=100)
    _fill_and_submit(app, date_text="2026/01/02", amount=200)

    some_row = app.tree.get_children("")[1]
    selected_transaction_id = int(some_row)
    app.tree.selection_set(some_row)
    app.tree.focus(some_row)

    logic.on_sort_column(app, "amount")  # 列ヘッダクリック相当（ソート列を変更）

    assert app.tree.selection() == (str(selected_transaction_id),)
    assert app.tree.focus() == str(selected_transaction_id)

    # ソート自体も実際に列順を変えていることを確認する
    amounts = [app.tree.item(iid, "values")[3] for iid in app.tree.get_children("")]
    assert amounts == sorted(amounts)


# ---- 削除 ----

def test_delete_selected_removes_row_and_selects_nothing(app):
    """削除後、存在しなくなった行を選択状態にしない"""
    _fill_and_submit(app, date_text="2026/01/01", amount=100)
    _fill_and_submit(app, date_text="2026/01/02", amount=200)

    all_ids = [tid for tid, _ in app.repository.get_all_with_id()]
    to_delete = str(all_ids[0])
    app.tree.selection_set(to_delete)

    logic.on_delete_selected(app)

    assert app.repository.get(int(to_delete)) is None
    assert len(app.repository.get_all()) == 1
    assert app.tree.selection() == ()
    assert not app.tree.exists(to_delete)


# ---- CSV（GUI配線のみ。CSV仕様自体の網羅は test_csv_storage.py が担当） ----

def test_csv_export_then_import_round_trip_via_gui(app, tmp_path, monkeypatch):
    _fill_and_submit(
        app,
        date_text="2026/05/06",
        amount=1234,
        memo="roundtrip",
        transaction_type="収入",
        category="給与",
    )

    csv_path = tmp_path / "export.csv"
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **kwargs: str(csv_path))
    logic.on_export_csv(app)
    assert csv_path.exists()

    monkeypatch.setattr(filedialog, "askopenfilename", lambda **kwargs: str(csv_path))
    before = len(app.repository.get_all())
    logic.on_import_csv(app)

    # CSV取込は既存データへの追記（既存仕様）
    assert len(app.repository.get_all()) == before + 1
    imported = [t for t in app.repository.get_all() if t.memo == "roundtrip"]
    assert len(imported) == 2
