"""アプリケーション起動エントリーポイント"""

from .app import main

# python -m kakeibo_app で実行されたときだけ起動する
if __name__ == "__main__":
    main()
