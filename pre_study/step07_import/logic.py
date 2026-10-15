"""買い物リストの処理

ボタンが押されたときに呼ばれる関数をまとめたファイル。
どの関数も、引数 app（画面の状態をまとめた辞書）を受け取る。

    app["input"]  入力欄に入っている文字
    app["items"]  買い物リスト（品名のリスト）
"""


def on_add_item(app):
    """入力欄の品名を買い物リストに追加し、入力欄を空にする"""
    item = app["input"]
    if item == "":
        print("  品名を入力してください。")
        return
    app["items"].append(item)
    app["input"] = ""
    print(f"  「{item}」を買い物リストに追加しました。")


def on_clear_input(app):
    """入力欄を空にする（買い物リストはそのまま）"""
    app["input"] = ""
    print("  入力欄をクリアしました。")


def on_remove_last(app):
    """買い物リストの最後の品名を削除する"""
    if len(app["items"]) == 0:
        print("  買い物リストは空です。")
        return
    item = app["items"].pop()
    print(f"  「{item}」を買い物リストから削除しました。")


def show_items(app):
    """買い物リストを表示する"""
    print(f"  買い物リスト：{app['items']}　入力欄：「{app['input']}」")
