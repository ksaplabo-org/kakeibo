"""Treeviewの選択・フォーカス状態の保持に対する回帰テスト

`refresh_list()` はRepositoryのデータからTreeviewを全件削除→再構築する。
この再構築によって選択・フォーカスが失われていた回帰を防ぐためのテスト。

このファイルは refresh_list() 単体に対する狭いテストに絞り、
一連のユーザーフロー（追加・更新・削除・ソート）を通したテストは
test_transaction_entry_flow.py 側に置く。
"""

import tkinter.messagebox as messagebox

import pytest

from kakeibo_app.features.transaction_entry import logic
from kakeibo_app.features.transaction_entry.repository import TransactionRepository

# _tk_root フィクスチャは tests/conftest.py で定義（Tkのルートはセッションで1つだけ生成する）


@pytest.fixture
def app(_tk_root, monkeypatch):
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showwarning", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)

    _tk_root.repository = TransactionRepository()
    _tk_root.sort_column = "date"
    _tk_root.sort_reverse = False
    logic.exit_edit_mode(_tk_root)
    logic.on_clear_inputs(_tk_root)
    logic.refresh_list(_tk_root)

    return _tk_root


def test_refresh_list_preserves_selection_when_transaction_still_exists(app):
    """refresh_list() を呼んでも、削除されていない行の選択は維持される"""
    for i in range(1, 4):
        app.repository.add(_transaction(amount=100 * i))
    logic.refresh_list(app)

    target = app.tree.get_children("")[1]
    app.tree.selection_set(target)
    app.tree.focus(target)

    logic.refresh_list(app)  # データは変えず再構築だけ行う

    assert app.tree.selection() == (target,)
    assert app.tree.focus() == target


def test_refresh_list_does_not_force_selection_when_nothing_was_selected(app):
    """何も選択していない状態で refresh_list() を呼んでも選択状態を作らない"""
    app.repository.add(_transaction(amount=100))
    logic.refresh_list(app)

    assert app.tree.selection() == ()
    logic.refresh_list(app)
    assert app.tree.selection() == ()


def test_refresh_list_drops_selection_for_deleted_transaction(app):
    """選択中の取引がRepositoryから削除された後は、その行を選択状態にしない"""
    tid = app.repository.add(_transaction(amount=100))
    logic.refresh_list(app)
    app.tree.selection_set(str(tid))

    app.repository.delete(tid)
    logic.refresh_list(app)

    assert app.tree.selection() == ()
    assert not app.tree.exists(str(tid))


def _transaction(amount: int):
    from datetime import date

    from kakeibo_app.shared.models import Transaction

    return Transaction(amount=amount, date=date(2026, 1, 1), transaction_type="支出", category="食費")
