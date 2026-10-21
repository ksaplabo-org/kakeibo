"""STEP02 if 文（条件分岐）

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step02_if.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# 比較の書き方
#   a == b   a と b が等しい
#   a != b   a と b が等しくない
#   a <  b   a は b より小さい（a <= b は「以下」）
#   a >  b   a は b より大きい（a >= b は「以上」）
def judge_price(price):
    """値段が1000円以上なら「高い」、そうでなければ「安い」を返す"""
    if price >= 1000:
        return "高い"
    else:
        return "安い"


print(judge_price(1500))  # 高い
print(judge_price(300))   # 安い

# ---------------------------------------------------------------------


"""STEP02-1 START

if文を修正しよう。
補足：残りが0円以上なら「黒字」、マイナスなら「赤字」を返す。
    if True: だと、いつも上の処理しか実行されない。
"""
def judge_balance(nokori):
    """残りのお金から「黒字」か「赤字」かを判定する"""
    if True:
        return "黒字"
    else:
        return "赤字"
"""STEP02-1 END

if文を修正しよう。
"""


"""STEP02-2 START

収入カテゴリを修正しよう。
補足：kind が「支出」なら支出のカテゴリ、「収入」なら収入のカテゴリを返す。
    収入のカテゴリは「給料」「おこづかい」の2つ。
    今は収入を選んでも、支出のカテゴリが返ってしまう。
"""
def get_categories(kind):
    """種類（支出/収入）に合ったカテゴリの一覧を返す"""
    if kind == "支出":
        return ["食費", "日用品", "交通費"]
    else:
        return ["食費", "日用品", "交通費"]
"""STEP02-2 END

収入カテゴリを修正しよう。
"""

# ヒント（詰まったら読もう）
# STEP02-1：「0円以上」は nokori >= 0 と書く。
# STEP02-2：「マイナス」は「0より小さい」ということ。


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
print("===== STEP02 答え合わせ =====")
results = [
    check("judge_balance(500)", lambda: judge_balance(500), "黒字"),
    check("judge_balance(0)", lambda: judge_balance(0), "黒字"),
    check("judge_balance(-100)", lambda: judge_balance(-100), "赤字"),
    check('get_categories("支出")', lambda: get_categories("支出"), ["食費", "日用品", "交通費"]),
    check('get_categories("収入")', lambda: get_categories("収入"), ["給料", "おこづかい"]),
]
if all(results):
    print("STEP02 クリア！")
else:
    print("× のところを見直そう。")
