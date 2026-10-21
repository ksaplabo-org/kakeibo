"""STEP03 二重 if 文（ネスト／入れ子）

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study_answers/step03_nested_if.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# if の中に、さらに if を書くことができる（ネスト／入れ子）。
# 字下げ（行頭のスペース）の深さで「どの if の中か」が決まる。
def judge_lunch(okozukai, is_holiday):
    """お昼ごはんをどうするか決める"""
    if is_holiday:                 # 休日のとき
        if okozukai >= 1000:       #   └ さらに、お金が1000円以上あるとき
            return "ランチに行こう"
        else:                      #   └ お金が足りないとき
            return "家で食べよう"
    else:                          # 平日のとき（お金は関係ない）
        return "お弁当"


print(judge_lunch(3000, True))   # ランチに行こう
print(judge_lunch(500, True))    # 家で食べよう
print(judge_lunch(3000, False))  # お弁当

# True / False は「正しい / 正しくない」を表す値。
# not をつけると逆になる（not True → False）。
# ---------------------------------------------------------------------


"""STEP03-1 START

if文を修正しよう。
補足：二重if文（ネスト/入れ子）を使う。
    やることリストの1行に、状態を表す印をつける。

    done（完了したか） | urgent（急ぎか） | 返す文字列
    -------------------+-----------------+--------------
    False              | True            | "急 買い物"
    False              | False           | "□ 買い物"
    True               | （関係ない）     | "済 買い物"

    ※ 引数の * について：* より後ろの引数は、呼び出すときに
      format_task("買い物", done=False, urgent=True) のように名前をつけて渡す。
"""
def format_task(label, *, done, urgent):
    """やることに状態の印（急/□/済）をつける

    Args:
        label: やることの名前（例：「買い物」）
        done: 完了したかどうか
        urgent: 急ぎかどうか（done が True の場合は無視される）

    Returns:
        「急 買い物」のような文字列
    """
    if not done:
        if urgent:
            mark = "急"
        else:
            mark = "□"
    else:
        mark = "済"
    return f"{mark} {label}"
"""STEP03-1 END

if文を修正しよう。
"""

# ヒント（詰まったら読もう）
# 例の judge_lunch と同じ形。
# 「まだ完了していない（not done）」ときの中で、さらに urgent で分ける。


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
print("===== STEP03 答え合わせ =====")
results = [
    check("未完了・急ぎ", lambda: format_task("買い物", done=False, urgent=True), "急 買い物"),
    check("未完了・急ぎでない", lambda: format_task("買い物", done=False, urgent=False), "□ 買い物"),
    check("完了・急ぎ", lambda: format_task("掃除", done=True, urgent=True), "済 掃除"),
    check("完了・急ぎでない", lambda: format_task("掃除", done=True, urgent=False), "済 掃除"),
]
if all(results):
    print("STEP03 クリア！")
else:
    print("× のところを見直そう。")
