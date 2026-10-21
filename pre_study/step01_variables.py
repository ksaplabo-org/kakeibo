"""STEP01 変数と print

このファイルの動かし方：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step01_variables.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# 「=」は「右の値を、左の名前（変数）に入れる」という意味
okozukai = 3000
print("おこづかい：", okozukai, "円")

# 計算もできる（+ 足し算、- 引き算、* 掛け算、/ 割り算）
print("2倍にすると：", okozukai * 2, "円")
# ---------------------------------------------------------------------


"""STEP01-1 START

エラーを直そう。
補足：まずは何も変えずに実行してみよう。ターミナルに赤い文字（エラー）が出る。
    エラーメッセージの「一番下の行」に原因が、
    その少し上の「line ○○」に何行目でエラーが起きたかが書いてある。
"""
print("確認：", okozukaii, "円")
"""STEP01-1 END

エラーを直そう。
"""


"""STEP01-2 START

計算を修正しよう。
補足：おこづかいでラーメンとジュースを買った。
    残りのおこづかい（おこづかい − ラーメン − ジュース）を nokori に入れる。
    数字を直接書くのではなく、変数 okozukai・ramen・juice を使って計算しよう。
"""
ramen = 900
juice = 150
nokori = 0
"""STEP01-2 END

計算を修正しよう。
"""

print("残り：", nokori, "円")


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
print("===== STEP01 答え合わせ =====")
results = [
    check("nokori の値", lambda: nokori, 1950),
]
if all(results):
    print("STEP01 クリア！")
else:
    print("× のところを見直そう。")
