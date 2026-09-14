"""GUIテスト共通のfixture

tkinter は、プロセス内で複数の tk.Tk() ルートを生成・破棄すると、
2つ目以降の生成が Tcl の初期化エラーで不安定になることがある
（この環境で実際に確認済み。テストの内容とは無関係な tkinter 自体の制約）。

そのため Tk のルートウィンドウはテストセッション全体で1つだけ生成し、
各テストは _tk_root フィクスチャ経由でこれを使い回す。テストごとの独立性は
（ウィンドウを再生成する代わりに）業務データ・UI状態のリセットで確保する。
"""

import pytest

from kakeibo_app.features.transaction_entry.view import MainWindow


@pytest.fixture(scope="session")
def _tk_root():
    instance = MainWindow()
    instance.withdraw()
    yield instance
    instance.destroy()
