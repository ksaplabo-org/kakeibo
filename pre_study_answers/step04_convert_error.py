"""STEP04 文字列から数値への変換、エラーを出す（raise）

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study_answers/step04_convert_error.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# 画面で入力された値は、数字に見えても「文字列」として受け取る。
# 計算に使うには int() で整数に変換する。
text = "120"
print(int(text) + 30)  # 150

# replace(A, B) は、文字列の中の A を B に置き換える。
# B を "" （空の文字列）にすると、A を取り除ける。
print("1,500".replace(",", ""))  # 1500

# raise を使うと、自分でエラーを起こせる。
# 「この値はおかしい」と処理を止めて、呼び出し元に知らせるために使う。
def check_age(age):
    """年齢が0未満ならエラーにする"""
    if age < 0:
        raise ValueError("年齢は0以上で入力してください。")
    return age


# try / except で、エラーが起きたときの処理を書ける。
try:
    check_age(-5)
except ValueError as error:
    print("エラーが起きました：", error)  # エラーが起きました： 年齢は0以上で入力してください。
# ---------------------------------------------------------------------


"""STEP04-1 START

仕様通りに修正しよう。
補足：修正部分は3か所
    1. カンマを除去して整数に変換する。
    2. value が1未満の場合、if文の処理を行う。
    3. if文内のエラーメッセージを "ポイントは1以上の整数で入力してください。" にする。
"""
def parse_points(text):
    """「1,500」のような文字列を整数 1500 に変換する。1未満ならエラーにする"""
    # カンマを除去して整数に変換
    value = int(text.replace(",", ""))
    if value < 1:
        raise ValueError("ポイントは1以上の整数で入力してください。")
    return value
"""STEP04-1 END

仕様通りに修正しよう。
"""


"""STEP04-2 START

仕様通りに修正しよう。
補足：if文を使用して、条件が正しい場合の処理を行う。
    STEP1   name が空の文字列 "" の場合、処理を行う。
    STEP2   エラーメッセージ "品名を入力してください。" で ValueError を発生させる。
"""
def check_item_name(name):
    """品名が空でないか確認し、問題なければそのまま返す"""

    if name == "":
        raise ValueError("品名を入力してください。")

    return name
"""STEP04-2 END

仕様通りに修正しよう。
"""

# ヒント（詰まったら読もう）
# STEP04-1：例の "1,500".replace(",", "") を参考にしよう。
# STEP04-2：例の check_age と同じ形。「空の文字列」は name == "" と書く。


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
print("===== STEP04 答え合わせ =====")
results = [
    check('parse_points("1,500")', lambda: parse_points("1,500"), 1500),
    check('parse_points("50")', lambda: parse_points("50"), 50),
    check('parse_points("1")', lambda: parse_points("1"), 1),
    check(
        'parse_points("0")',
        lambda: parse_points("0"),
        "エラー ValueError: ポイントは1以上の整数で入力してください。",
    ),
    check('check_item_name("牛乳")', lambda: check_item_name("牛乳"), "牛乳"),
    check('check_item_name("")', lambda: check_item_name(""), "エラー ValueError: 品名を入力してください。"),
]
if all(results):
    print("STEP04 クリア！")
else:
    print("× のところを見直そう。")
