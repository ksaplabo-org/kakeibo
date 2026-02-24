"""データモデル層 - トランザクション管理"""

import csv
from decimal import Decimal
from typing import Dict, Optional


class Transaction:
    """個別の取引データを表すモデル
    
    Attributes:
        date (str): 日付（YYYY/MM/DD形式）
        transaction_type (str): 「支出」または「収入」
        category (str): カテゴリ
        price (Decimal): 金額
        memo (str): メモ
    """
    
    def __init__(self, date: str, transaction_type: str, category: str, 
                 price: Decimal, memo: str = ""):
        """トランザクションの初期化
        
        Args:
            date: 日付（YYYY/MM/DD形式）
            transaction_type: 「支出」または「収入」
            category: カテゴリ
            price: 金額
            memo: メモ（デフォルト空文字）
        """
        self.date = date
        self.transaction_type = transaction_type
        self.category = category
        self.price = price
        self.memo = memo
    
    def to_dict(self) -> dict:
        """辞書形式に変換
        
        Returns:
            dict: トランザクションデータ
        """
        return {
            "date": self.date,
            "transaction_type": self.transaction_type,
            "category": self.category,
            "price": self.price,
            "memo": self.memo
        }


class TransactionManager:
    """トランザクションの管理・永続化を担当
    
    Attributes:
        items (Dict[str, dict]): Treeview の iid をキー、トランザクションデータを値とする辞書
    """
    
    def __init__(self):
        """マネージャの初期化"""
        self.items: Dict[str, dict] = {}
    
    def add_transaction(self, iid: str, transaction: Transaction) -> None:
        """トランザクションを追加
        
        Args:
            iid: Treeview の id（ユニーク識別子）
            transaction: 追加するトランザクション
        """
        self.items[iid] = transaction.to_dict()
    
    def update_transaction(self, iid: str, transaction: Transaction) -> None:
        """トランザクションを更新
        
        Args:
            iid: Treeview の id
            transaction: 更新するトランザクション
        """
        self.items[iid] = transaction.to_dict()
    
    def delete_transaction(self, iid: str) -> None:
        """トランザクションを削除
        
        Args:
            iid: Treeview の id
        """
        if iid in self.items:
            del self.items[iid]
    
    def get_transaction(self, iid: str) -> Optional[dict]:
        """トランザクションを取得
        
        Args:
            iid: Treeview の id
        
        Returns:
            dict: トランザクションデータ、存在しない場合は None
        """
        return self.items.get(iid)
    
    def get_all_items(self) -> Dict[str, dict]:
        """すべてのトランザクションを取得
        
        Returns:
            Dict: すべてのトランザクションデータ
        """
        return self.items.copy()
    
    def calculate_totals(self) -> tuple:
        """支出・収入・ネット残高を計算
        
        Returns:
            tuple: (支出合計, 収入合計, ネット残高)
        """
        expense = Decimal(0)
        income = Decimal(0)
        for item in self.items.values():
            if item["transaction_type"] == "支出":
                expense += item["price"]
            else:  # 収入
                income += item["price"]
        net = income - expense
        return expense, income, net
    
    def export_csv(self, path: str) -> int:
        """データを CSV ファイルに保存
        
        Args:
            path: 保存先ファイルパス
        
        Returns:
            int: 保存されたデータ件数
        
        Raises:
            IOError: ファイル書き込みエラー
        """
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["日付", "種類", "カテゴリ", "金額", "メモ"])
                for item in self.items.values():
                    writer.writerow([
                        item["date"], 
                        item["transaction_type"], 
                        item["category"],
                        str(item["price"]), 
                        item.get("memo", "")
                    ])
            return len(self.items)
        except Exception as e:
            raise IOError(f"CSV 保存エラー: {e}")
    
    def import_csv(self, path: str, validators: callable) -> tuple:
        """CSV ファイルからデータを読み込み
        
        Args:
            path: 読み込むファイルパス
            validators: バリデーション関数（行データを検証して Transaction を返す）
        
        Returns:
            tuple: (追加件数, 無効件数, 追加されたトランザクションリスト)
        
        Raises:
            IOError: ファイル読み込みエラー
        """
        added = 0
        invalid = 0
        transactions = []
        
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # ヘッダー判定
            start_idx = 0
            if rows and rows[0][:4] == ["日付", "種類", "カテゴリ", "金額"]:
                start_idx = 1
            
            for row in rows[start_idx:]:
                try:
                    transaction = validators(row)
                    transactions.append(transaction)
                    added += 1
                except ValueError:
                    invalid += 1
            
            return added, invalid, transactions
        except Exception as e:
            raise IOError(f"CSV 読み込みエラー: {e}")
