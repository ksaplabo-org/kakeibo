"""STEP06 リストと for 文

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study/step06_list_for.py
    画面下の「ターミナル」に結果が表示される。

一番下に「答え合わせ」があるので、全部 ○ になればクリア。
本課題では「応用課題01」（shared/validation.py）、
「応用課題02」（shared/csv_storage.py）で使います。
"""

# --- 例：まずはこのまま読んでみよう ---------------------------------
# リストは、複数の値を順番に並べたもの。[ ] で囲み、カンマで区切る。
foods = ["パン", "牛乳", "たまご"]

print(len(foods))  # 3（len で要素の数がわかる）
print(foods[0])    # パン（番号は 0 から始まる）
print(foods[1:])   # ['牛乳', 'たまご']（[1:] で「1番目から最後まで」を取り出す。スライス）

foods.append("バナナ")  # append で最後に追加
print(foods)            # ['パン', '牛乳', 'たまご', 'バナナ']

# for 文で、リストの要素を1つずつ取り出して処理できる
for food in foods:
    print("買うもの：", food)

# enumerate を使うと、番号も一緒に取り出せる（start= で始まりの番号を決める）
for number, food in enumerate(foods, start=1):
    print(number, food)  # 1 パン / 2 牛乳 / ...

# in を使うと「リストの中にあるか」を調べられる
print(3 in [3, 4])  # True
print(5 in [3, 4])  # False

# リストの中にリストを入れることもできる（表のようなデータ）
rows = [
    ["日付", "品名", "金額"],
    ["2026/05/01", "パン", "200"],
]
print(rows[1][1])  # パン（1行目の、1列目）
# ---------------------------------------------------------------------


"""STEP06-1 START

for文を使って合計を計算しよう。
補足：amounts の中の金額を1つずつ取り出して、result に足していく。
"""
def total(amounts):
    """金額のリストの合計を返す"""
    result = 0

    """ここに記載する"""

    return result
"""STEP06-1 END

for文を使って合計を計算しよう。
"""


"""STEP06-2 START

番号を修正しよう。
補足：番号は 1 から始めたいのに、今は 0 から始まってしまう。
"""
def number_items(items):
    """品名のリストに番号をつけたリストを返す（例：["1: パン", "2: 牛乳"]）"""
    lines = []
    for number, item in enumerate(items, start=0):
        lines.append(f"{number}: {item}")
    return lines
"""STEP06-2 END

番号を修正しよう。
"""


"""STEP06-3 START

仕様通りに修正しよう。
補足：if文を使用して、条件が正しくない場合の処理を行う。
    STEP1   row（1行分のデータ）の列数が 3列 でも 4列 でもない場合、処理を行う。
    STEP2   エラーメッセージ "列数が不正です（3列または4列である必要があります）。"
            で ValueError を発生させる。
"""
def check_columns(row):
    """1行分のデータ（3列または4列）の列数を確認する。正しければ True を返す"""

    """ここに記載する"""

    return True
"""STEP06-3 END

仕様通りに修正しよう。
"""


"""STEP06-4 START

仕様通りに修正しよう。
補足：条件式を追加する。（三項演算子）
    先頭の行の1列目が "日付" なら、それは見出し（ヘッダ）の行。
    見出しがあれば start_index を 1、なければ 0 にする。
"""
def remove_header(rows):
    """先頭行が見出しなら、それを取り除いた行のリストを返す"""
    # 見出しの行があれば読み飛ばす

    """ここに記載する"""

    return rows[start_index:]
"""STEP06-4 END

仕様通りに修正しよう。
"""

# ヒント（詰まったら読もう）
# STEP06-1：for amount in amounts: の中で result = result + amount
# STEP06-3：「3でも4でもない」は len(row) not in [3, 4] と書ける。
# STEP06-4：STEP03 の三項演算子（値1 if 条件 else 値2）と、例の rows[1][1] を参考にしよう。


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


COLUMN_ERROR = "エラー ValueError: 列数が不正です（3列または4列である必要があります）。"
HEADER = ["日付", "品名", "金額"]
ROW1 = ["2026/05/01", "パン", "200"]
ROW2 = ["2026/05/02", "牛乳", "180"]

print()
print("===== STEP06 答え合わせ =====")
results = [
    check("total([100, 200, 300])", lambda: total([100, 200, 300]), 600),
    check("total([])", lambda: total([]), 0),
    check('number_items(["パン", "牛乳"])', lambda: number_items(["パン", "牛乳"]), ["1: パン", "2: 牛乳"]),
    check("check_columns（3列）", lambda: check_columns(["a", "b", "c"]), True),
    check("check_columns（4列）", lambda: check_columns(["a", "b", "c", "d"]), True),
    check("check_columns（2列）", lambda: check_columns(["a", "b"]), COLUMN_ERROR),
    check("check_columns（5列）", lambda: check_columns(["a", "b", "c", "d", "e"]), COLUMN_ERROR),
    check("remove_header（見出しあり）", lambda: remove_header([HEADER, ROW1, ROW2]), [ROW1, ROW2]),
    check("remove_header（見出しなし）", lambda: remove_header([ROW1, ROW2]), [ROW1, ROW2]),
]
if all(results):
    print("STEP06 クリア！ 次は step07_import フォルダの main.py に進もう。")
else:
    print("× のところを見直そう。")
