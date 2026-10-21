"""画面のボタンの代わりをする部品（このファイルは読まなくてOK）

本物の画面（tkinter）のボタンと同じように、
Button(text="追加", command=関数) の形で「押されたときに呼ぶ関数」を登録する。
click() を呼ぶと、ボタンが押されたことになる。
"""


class Button:
    def __init__(self, text, command):
        self.text = text
        self.command = command

    def click(self):
        print(f"[{self.text}] ボタンを押しました")
        try:
            self.command()
        except Exception as error:
            print(f"  エラー {type(error).__name__}: {error}")
