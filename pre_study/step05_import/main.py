"""STEP05 別のファイルの関数を使う（import）、ボタンに関数を登録する

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step05_import/main.py
    画面下の「ターミナル」に結果が表示される。

このフォルダには3つのファイルがある。
    main.py    … このファイル。ボタンを作って押してみる（これを実行する）
    logic.py   … ボタンが押されたときの処理（関数）が書いてある
    button.py  … 画面のボタンの代わりをする部品（読まなくてOK）

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# from ファイル名 import 関数名 と書くと、別のファイルの関数が使えるようになる。
# （ファイル名の .py は書かない）
from button import Button
from logic import on_add_item, on_clear_input, on_remove_last, show_items

# 画面の状態をまとめたもの（辞書）。app["input"] のように取り出す。
app = {"input": "", "items": []}

# ボタンには「押されたときに呼ぶ関数」を command= で登録する。
#   lambda: 関数名(app) は「あとで 関数名(app) を呼んでね」という予約のようなもの。
#   ボタンを作った時点では呼ばれず、押されたときに初めて呼ばれる。
show_button = Button(text="表示", command=lambda: show_items(app))
# ---------------------------------------------------------------------


"""STEP05-1 START

logic.pyからメソッドを探そう。
補足：logic.py を開いて、それぞれのボタンに合う関数を探す。
    text="追加" の処理：入力欄の品名を買い物リストに追加する。
    text="クリア" の処理：入力欄を空にする。
"""
add_button = Button(text="追加", command=lambda: test(app))
clear_button = Button(text="クリア", command=lambda: test(app))
"""STEP05-1 END

logic.pyからメソッドを探そう。
"""

# ヒント（詰まったら読もう）
# 例の show_button と同じ形。test の部分を logic.py の関数名に置き換える。
# logic.py の関数は、上の from logic import ... ですでに使えるようになっている。


# --- ボタンを押してみる ----------------------------------------------
print("【入力欄に「牛乳」と入れて「追加」を押す】")
app["input"] = "牛乳"
add_button.click()
show_button.click()

print("【入力欄に「パン」と入れて「クリア」を押す】")
app["input"] = "パン"
clear_button.click()
show_button.click()
after_clear = {"input": app["input"], "items": list(app["items"])}

print("【入力欄に「たまご」と入れて「追加」を押す】")
app["input"] = "たまご"
add_button.click()
show_button.click()
after_second_add = {"input": app["input"], "items": list(app["items"])}


# =====================================================================
# ここから下は答え合わせ用です（変更しないでください）
# =====================================================================
def check(label, func, expected):
    try:
        actual = func()
    except Exception as error:
        actual = f"エラー {type(error).__name__}: {error}"
    if actual == expected:
        print(f"  ○ {label}")
        print(f"      期待する結果: {expected!r}")
        print(f"      実際の結果  : {actual!r}")
        return True
    print(f"  × {label}")
    print(f"      期待する結果: {expected!r}")
    print(f"      実際の結果  : {actual!r}")
    return False


print()
print("===== STEP05 答え合わせ =====")
results = [
    check("「クリア」の後", lambda: after_clear, {"input": "", "items": ["牛乳"]}),
    check("2回目の「追加」の後", lambda: after_second_add, {"input": "", "items": ["牛乳", "たまご"]}),
]
if all(results):
    print("STEP05 クリア！")
else:
    print("× のところを見直そう。")
