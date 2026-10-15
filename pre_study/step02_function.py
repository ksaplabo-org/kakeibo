"""STEP02 関数と return、f-string、split

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step02_function.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
本課題では「基本課題05」（shared/formatters.py）で使います。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# def で「関数」を作る。() の中は受け取る値（引数）。
# return の右に書いた値が、関数の結果（戻り値）になる。
def add(a, b):
    """2つの数を足した結果を返す"""
    return a + b


print(add(3, 5))  # 8


# f"..." の中に {変数} と書くと、変数の中身が埋め込まれる
item = "ラーメン"
price = 900
print(f"{item}は{price}円")  # ラーメンは900円

# {変数:,} と書くと、3桁ごとにカンマが入る
print(f"¥{12345:,}")  # ¥12,345

# split は文字列を区切り文字で分けて、リスト（複数の値の並び）にする
print("りんご,みかん,ぶどう".split(","))  # ['りんご', 'みかん', 'ぶどう']

# 分けた結果を、複数の変数にまとめて入れることもできる
first, second = "東京-大阪".split("-")
print(first)   # 東京
print(second)  # 大阪

# int() は数字の文字列を整数にする。先頭の 0 は消える
print(int("07"))  # 7
# ---------------------------------------------------------------------


"""STEP02-1 START

正しいreturn文に修正しよう。
補足：受け取った件数 count を使って「3件」のような文字列を返す。
    今は何を渡しても "0件" が返ってしまう。
"""
def format_count(count):
    """件数を「3件」形式の文字列にする"""
    return "0件"
"""STEP02-1 END

正しいreturn文に修正しよう。
"""


"""STEP02-2 START

関数を修正しよう。
補足：計算はしているのに、答え合わせで「実際の結果: None」と表示される。
    None は「何もない」という意味。関数が何も返していないと None になる。
"""
def calc_nokori(okozukai, shishutsu):
    """おこづかいから支出を引いた残りを返す"""
    nokori = okozukai - shishutsu
"""STEP02-2 END

関数を修正しよう。
"""


"""STEP02-3 START

正しいreturn文に修正しよう。
補足：文字列を変換させる。
    STEP1   date_text は「2026-05-20」形式なので、split メソッドを使用して
            year 、 month 、 day に代入する。
    STEP2   int() を使って「05」を「5」にする。
    STEP3   month 、 day を使用して正しいreturn文に修正する。
"""
def format_date_label(date_text):
    """「2026-05-20」形式の日付を「5月20日」形式に変換する"""
    return "1月1日"
"""STEP02-3 END

正しいreturn文に修正しよう。
"""

# ヒント（詰まったら読もう）
# STEP02-1：例の f"{item}は{price}円" を参考にしよう。
# STEP02-3：year, month, day = date_text.split("-") で3つに分けられる。


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
print("===== STEP02 答え合わせ =====")
results = [
    check("format_count(3)", lambda: format_count(3), "3件"),
    check("format_count(12)", lambda: format_count(12), "12件"),
    check("calc_nokori(3000, 1200)", lambda: calc_nokori(3000, 1200), 1800),
    check('format_date_label("2026-05-20")', lambda: format_date_label("2026-05-20"), "5月20日"),
    check('format_date_label("2026-11-03")', lambda: format_date_label("2026-11-03"), "11月3日"),
]
if all(results):
    print("STEP02 クリア！ 次は step03_if.py に進もう。")
else:
    print("× のところを見直そう。")
