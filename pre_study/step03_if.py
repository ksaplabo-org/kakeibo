"""STEP03 if 文（条件分岐）

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step03_if.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
本課題では「基本課題03」「基本課題04」（features/transaction_entry/logic.py）で使います。
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


# if / else は1行でも書ける（三項演算子）
#   値1 if 条件 else 値2   → 条件が正しければ 値1、そうでなければ 値2
price = 1500
label = "高い" if price >= 1000 else "安い"
print(label)  # 高い
# ---------------------------------------------------------------------


"""STEP03-1 START

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
"""STEP03-1 END

if文を修正しよう。
"""


"""STEP03-2 START

条件式を修正しよう。
補足：差額 net がマイナスなら "red"（赤字を赤く表示）、それ以外は "black" を返す。
    1行で書く if / else（三項演算子）になっている。
"""
def balance_color(net):
    """差額に応じて文字の色を返す"""
    return "red" if True else "black"
"""STEP03-2 END

条件式を修正しよう。
"""


"""STEP03-3 START

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
"""STEP03-3 END

収入カテゴリを修正しよう。
"""

# ヒント（詰まったら読もう）
# STEP03-1：「0円以上」は nokori >= 0 と書く。
# STEP03-2：「マイナス」は「0より小さい」ということ。


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
        return True
    print(f"  × {label}")
    print(f"      期待する結果: {expected!r}")
    print(f"      実際の結果  : {actual!r}")
    return False


print()
print("===== STEP03 答え合わせ =====")
results = [
    check("judge_balance(500)", lambda: judge_balance(500), "黒字"),
    check("judge_balance(0)", lambda: judge_balance(0), "黒字"),
    check("judge_balance(-100)", lambda: judge_balance(-100), "赤字"),
    check("balance_color(-500)", lambda: balance_color(-500), "red"),
    check("balance_color(0)", lambda: balance_color(0), "black"),
    check("balance_color(300)", lambda: balance_color(300), "black"),
    check('get_categories("支出")', lambda: get_categories("支出"), ["食費", "日用品", "交通費"]),
    check('get_categories("収入")', lambda: get_categories("収入"), ["給料", "おこづかい"]),
]
if all(results):
    print("STEP03 クリア！ 次は step04_nested_if.py に進もう。")
else:
    print("× のところを見直そう。")
