from tkinter import ttk

from .ui.main.view import KakeiboApp


def main():
    """
    アプリケーション起動
    
    DPI認識設定（表示崩れを防ぐため）
    KakeiboAppインスタンス生成
    スタイル適用、メインループ実行。
    """
    try:
        # DPI 設定（Windows のみ）
        try:
            from ctypes import windll
            if hasattr(windll.shcore, 'SetProcessDpiAwareness'):
                windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError):
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
