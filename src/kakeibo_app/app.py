"""アプリケーションの起動処理"""

from tkinter import ttk

from .features.transaction_entry.view import MainWindow


def main():
    """アプリケーションを起動する

    DPI認識設定（Windows向け）、MainWindowインスタンス生成、
    スタイル適用、メインループ実行を行う。起動時の未捕捉例外は
    標準出力に記録する（pythonw 起動時は非表示になる点に留意）。
    """
    try:
        # DPI 設定（Windows のみ）
        try:
            from ctypes import windll
            if hasattr(windll.shcore, 'SetProcessDpiAwareness'):
                windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError):
            pass

        app = MainWindow()
        # 利用可能ならWindows標準のテーマを適用
        style = ttk.Style(app)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        # ウィンドウを表示し、ユーザー操作を待ち続ける
        app.mainloop()
    except Exception as e:
        # 起動時の予期しないエラーを画面に出さず、標準出力に記録する
        import traceback
        print("起動時に例外が発生しました：", e)
        traceback.print_exc()
