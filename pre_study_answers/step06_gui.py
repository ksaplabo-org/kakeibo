"""STEP06 はじめての画面（tkinter）

実行方法：
    VSCode 右上の ▷（Run Python File）を押す。
    または、ターミナルで kakeibo フォルダに移動して次のコマンドを実行する。
        python pre_study_answers/step06_gui.py

実行するとウィンドウが開く。このステップは「答え合わせ」の代わりに、
画面が下の完成イメージと同じになり、ボタンが正しく動けばクリア。

完成イメージ：
    ┌──────────────────────────────────┐
    │  品名 [                    ]     │
    │  金額 [                    ]     │
    │               [追加] [クリア]     │
    │  （ここにメッセージが出る）        │
    └──────────────────────────────────┘

    ・品名と金額を入れて「追加」を押すと「○○を○○円で追加しました。」と表示される
    ・「クリア」を押すと品名と金額の入力欄が空になる
"""

import tkinter as tk
from tkinter import ttk


# --- ボタンが押されたときの処理 --------------------------------------
def on_add():
    """入力された品名と金額をメッセージに表示する"""
    name = name_var.get()
    amount = amount_var.get()
    message_var.set(f"{name}を{amount}円で追加しました。")


def on_clear():
    """品名と金額の入力欄を空にする"""
    name_var.set("")
    amount_var.set("")
    message_var.set("入力欄をクリアしました。")


# --- 画面を作る ------------------------------------------------------
root = tk.Tk()
root.title("STEP06 はじめての画面")

form = ttk.Frame(root, padding=12)
form.pack()

# grid(row=行, column=列) で、表のマス目のように部品を並べる。
#   row=0 が1行目、column=0 が1列目。
#   sticky="e" は右寄せ（east）、"w" は左寄せ（west）。
#   padx / pady は部品のまわりのすき間。

# 1行目：品名
ttk.Label(form, text="品名").grid(row=0, column=0, sticky="e", padx=6, pady=6)
name_var = tk.StringVar()
ttk.Entry(form, textvariable=name_var, width=20).grid(row=0, column=1, sticky="w", padx=6, pady=6)

"""STEP06-1 START

レイアウトを修正しよう。
補足：「金額」の行が、品名の右側にずれて表示されている。
    完成イメージのように、品名の下（2行目）に表示されるようにする。
    ラベルの文字も「金額」に直す。上の「品名」の行と見比べよう。
"""
# 2行目：金額
ttk.Label(form, text="金額").grid(row=1, column=0, sticky="e", padx=6, pady=6)
amount_var = tk.StringVar()
ttk.Entry(form, textvariable=amount_var, width=20).grid(row=1, column=1, sticky="w", padx=6, pady=6)
"""STEP06-1 END

レイアウトを修正しよう。
"""

# 3行目：ボタン
button_frame = ttk.Frame(form)
button_frame.grid(row=2, column=1, sticky="w", padx=6, pady=6)

"""STEP06-2 START

このファイルの中からメソッドを探そう。
補足：ボタンを押したときに呼ぶ関数を command= に登録する。
    text="追加" の処理：入力された品名と金額をメッセージに表示する。
    text="クリア" の処理：品名と金額の入力欄を空にする。
"""
ttk.Button(button_frame, text="追加", command=lambda: on_add()).pack(side="left", padx=3)
ttk.Button(button_frame, text="クリア", command=lambda: on_clear()).pack(side="left", padx=3)
"""STEP06-2 END

このファイルの中からメソッドを探そう。
"""

# 4行目：メッセージ
message_var = tk.StringVar(value="品名と金額を入力してください。")
ttk.Label(form, textvariable=message_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=6)

# ヒント（詰まったら読もう）
# STEP06-1：row が「何行目か」、column が「何列目か」。品名の行は row=0。
# STEP06-2：STEP05 と同じ形。このファイルの上のほうにある関数を探そう。

# ウィンドウを表示し続ける（閉じるまでここで待つ）
root.mainloop()
