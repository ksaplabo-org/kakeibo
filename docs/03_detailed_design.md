# 詳細設計書

- 対象システム: 家計簿アプリケーション（kakeibo-app）
- 本書の位置づけ: 現行実装をリバースエンジニアリングして作成した詳細設計書。モジュール／関数単位の仕様、処理シーケンス、バリデーション・CSV・集計・描画の詳細ロジックを記述する。

## 目次

1. [モジュール構成一覧](#1-モジュール構成一覧)
2. [ドメインモデル](#2-ドメインモデル)
3. [バリデーション詳細仕様](#3-バリデーション詳細仕様)
4. [Repository詳細仕様](#4-repository詳細仕様)
5. [メイン画面（transaction_entry）詳細仕様](#5-メイン画面transaction_entry詳細仕様)
6. [CSV入出力詳細仕様](#6-csv入出力詳細仕様)
7. [統計画面（summary）詳細仕様](#7-統計画面summary詳細仕様)
8. [グラフ描画・日本語フォント仕様](#8-グラフ描画日本語フォント仕様)
9. [共通ユーティリティ](#9-共通ユーティリティ)
10. [起動処理詳細](#10-起動処理詳細)
11. [エラーハンドリング方針一覧](#11-エラーハンドリング方針一覧)
12. [テスト対応表](#12-テスト対応表)

---

## 1. モジュール構成一覧

| ファイル | 主なクラス／関数 |
|---|---|
| `app.py` | `main()` |
| `shared/models.py` | `Transaction`, `TransactionType` |
| `shared/constants.py` | `EXPENSE_CATEGORIES`, `INCOME_CATEGORIES`, `TRANSACTION_TYPES` |
| `shared/validation.py` | `ValidationError`, `parse_amount`, `parse_date`, `validate_transaction_type`, `validate_category`, `build_transaction`, `build_transaction_from_row` |
| `shared/balance.py` | `Totals`, `calculate_totals` |
| `shared/formatters.py` | `format_yen`, `format_month_label`, `format_year_label`, `format_sort_heading` |
| `shared/csv_storage.py` | `CsvImportResult`, `to_csv_row`, `export_csv`, `import_csv` |
| `transaction_entry/repository.py` | `TransactionRepository` |
| `transaction_entry/logic.py` | `refresh_list`, `refresh_totals`, `refresh_derived_display`, `on_sort_column`, `on_type_changed`, `exit_edit_mode`, `on_add_or_update`, `on_clear_inputs`, `on_tree_double_click`, `on_delete_selected`, `on_show_summary`, `on_export_csv`, `on_import_csv` |
| `transaction_entry/view.py` | `MainWindow` |
| `summary/aggregation.py` | `filter_by_type`, `available_months`, `filter_by_month_range`, `summarize_by_category`, `summarize_by_month`, `summarize_by_year`, `summarize_totals_by_month`, `summarize_totals_by_year` |
| `summary/logic.py` | `SUMMARY_TOTAL_LABEL`, `SUMMARY_DISPLAY_TYPES`, `MONEY_COLUMNS`, `reset_render_container`, `render_category_tab`, `render_monthly_tab`, `render_yearly_tab`, `build_summary_table`, `embed_figure`, `plot_pie_chart`, `plot_bar_chart`, `plot_net_line_chart` |
| `summary/view.py` | `SummaryWindow` |

## 2. ドメインモデル

### 2.1 `Transaction`（`shared/models.py`）

```python
TransactionType = Literal["支出", "収入"]

class Transaction(NamedTuple):
    amount: int
    date: date
    transaction_type: TransactionType
    category: str
    memo: str = ""
```

- `NamedTuple`によるイミュータブルな値オブジェクト。等価性はフィールド値による構造的等価（`==`）。
- `TransactionType`の値集合は`shared.constants.TRANSACTION_TYPES`と一致する必要があり、`tests/test_models.py`で整合性を自動検証している。
- 更新操作は「新しい`Transaction`を生成して`Repository`側で置き換える」形で行われ、`Transaction`自体にミューテータは存在しない。

### 2.2 マスタデータ（`shared/constants.py`）

```python
EXPENSE_CATEGORIES = ["食費","日用品","交通","交際費","娯楽","住居","光熱費","医療","教育","貯金","その他"]
INCOME_CATEGORIES  = ["給与","ボーナス","副業","投資","その他収入"]
TRANSACTION_TYPES  = ["支出","収入"]
```

コンボボックスの選択肢・バリデーションの許可リストの両方でこの定数がそのまま使われる（別経路での重複定義なし）。

## 3. バリデーション詳細仕様

すべて `shared/validation.py` に実装。GUI入力（`build_transaction`）とCSV行（`build_transaction_from_row`）は最終的に同じ検証関数群を通る。

### 3.1 `ValidationError`

```python
class ValidationError(ValueError):
    def __init__(self, message: str, *, code: str, field: str): ...
```

| 属性 | 内容 |
|---|---|
| `message`（例外の`str()`） | 画面表示用の日本語メッセージ |
| `code` | 機械判定用のエラー種別コード（下表参照） |
| `field` | エラー対象フィールド名（`"amount"` / `"date"` / `"transaction_type"` / `"category"` / `"row"`） |

呼び出し側はメッセージ文字列をパースしてはならず、`code`/`field`で判定する設計。

### 3.2 金額（`parse_amount`）

- 正規表現: `^¥?(\d+|\d{1,3}(?:,\d{3})+)$`
- 前処理: `unicodedata.normalize("NFKC", text).strip()`（全角数字→半角、前後空白除去）
- 空文字 → `code="empty"`
- パターン不一致（小数・指数表記・不正な桁区切り等） → `code="invalid_amount"`
- 値が1未満（0または負数はそもそも正規表現の`\d+`に一致しないが、マッチ後の整数変換で`< 1`を再チェック） → `code="invalid_amount"`

| 入力 | 結果 |
|---|---|
| `1000` | 有効: 1000 |
| `1,000` | 有効: 1000 |
| `¥1,000` | 有効: 1000 |
| `１０００`（全角） | 有効: 1000 |
| `0` | 無効（1以上ではない） |
| `-1000` | 無効（正規表現不一致） |
| `1000.5` | 無効（正規表現不一致） |
| `1,00` | 無効（3桁区切り不正） |

### 3.3 日付（`parse_date`）

- 正規表現: `^(\d{4})/(\d{1,2})/(\d{1,2})$`
- 前処理は金額と同様（NFKC正規化＋strip）
- 空文字 → `code="empty"`
- パターン不一致（`-`区切り等） → `code="format_error"`
- パターンは一致するが`datetime.date(y, m, d)`が`ValueError`（実在しない日付） → `code="invalid_date"`
- 年の範囲チェックはなし（`date`コンストラクタが許容する範囲＝西暦1〜9999年まで有効）

### 3.4 取引種別（`validate_transaction_type`）

- NFKC正規化＋strip後、`TRANSACTION_TYPES`（`["支出","収入"]`）に含まれるかを判定
- 不一致 → `code="invalid_type"`, `field="transaction_type"`

### 3.5 カテゴリ（`validate_category`）

- 取引種別に応じて`EXPENSE_CATEGORIES`または`INCOME_CATEGORIES`を許可リストとして使用
- 許可リスト外 → `code="unknown_category"`, `field="category"`
- **不正カテゴリを先頭カテゴリ等へ自動フォールバックすることはしない**（`test_import_rejects_unknown_category_without_fallback`で明示的に検証されている仕様）

### 3.6 `build_transaction` / `build_transaction_from_row`

```python
def build_transaction(*, date_text, transaction_type_text, category_text, amount_text, memo) -> Transaction
def build_transaction_from_row(row: Sequence[str]) -> Transaction
```

- 検証順序: 日付 → 種別 → カテゴリ（種別に依存するため種別より後） → 金額
- `memo`は意味的検証なし（`strip()`のみ）
- `build_transaction_from_row`は行の列数が4または5以外の場合に`code="invalid_column_count"`, `field="row"`を送出してから各フィールドの検証に進む。5列目（メモ）が無い場合は`memo=""`扱い。

## 4. Repository詳細仕様

### `TransactionRepository`（`transaction_entry/repository.py`）

Tkinterに一切依存しない（`test_repository_module_does_not_import_tkinter`で保証）。合計計算は自前実装せず`shared.balance.calculate_totals`に委譲する。

| メンバ | シグネチャ | 仕様 |
|---|---|---|
| `_items` | `dict[int, Transaction]` | 内部データストア |
| `_next_id` | `int`（初期値1） | 次回発番するID |
| `add` | `(transaction: Transaction) -> int` | 現在の`_next_id`を発番して保存、`_next_id`を+1して返す |
| `update` | `(transaction_id: int, transaction: Transaction) -> None` | 既存IDでなければ`KeyError`を送出（`delete`とは非対称の挙動） |
| `delete` | `(transaction_id: int) -> None` | 存在しないIDは無視（例外を出さない） |
| `get` | `(transaction_id: int) -> Transaction \| None` | 存在しない場合`None` |
| `get_all` | `() -> list[Transaction]` | 独立した新しいリストを返す（内部状態への参照を漏らさない） |
| `get_all_with_id` | `() -> list[tuple[int, Transaction]]` | CSVエクスポートの並び替え等に使用 |
| `calculate_totals` | `() -> Totals` | `shared.balance.calculate_totals(self.get_all())`を呼ぶだけ |

**IDの性質**: 1始まりの連番。削除してもIDは再利用されない（`test_ids_are_not_reused_after_delete`）。アプリ実行中のみ有効で、永続的なレコードIDではない。Treeviewの`iid`はこのID文字列がそのまま使われるが、UI側の識別子がこのIDの発生源になることはない（一方向の依存）。

## 5. メイン画面（transaction_entry）詳細仕様

### 5.1 `MainWindow`（`view.py`）の責務

- GUI構築（`_build_ui`）とTkinterイベントの受け口のみ。実処理はすべて`logic`モジュールへ委譲（`command=lambda: on_xxx(self)`の形でハンドラを束縛）。
- 保持する主要な状態: `repository`（`TransactionRepository`）、`editing_id`（編集中の内部ID、`None`なら新規モード）、`sort_column`／`sort_reverse`（一覧のソート状態）。

### 5.2 一覧再構築（`refresh_list`）

```
1. 現在選択中のiidのうち、repository.get(int(iid))がNoneでないものだけを previous_selection として保持
2. 現在のfocusを previous_focus として保持
3. Treeviewの全行を削除
4. repository.get_all_with_id() を取得し、sort_column に対応するキー関数（_SORT_KEYS）で
   sort_reverse に従って並べ替え
5. 並べ替え後の順で全行を再挿入（iid=str(transaction_id)）
6. 各列見出しのテキストをソート状態（▲/▼）付きで更新
7. previous_selection が空でなければ選択・フォーカスを復元
   （previous_focus がまだ有効ならそれを、無効なら先頭を focus）
```

この「削除されていない行だけ選択復元」というロジックが、Treeviewの全件再構築による選択消失を防ぐための核心部分（`tests/test_treeview_selection_regression.py`で3パターン検証）。

### 5.3 追加・更新（`on_add_or_update`）

```
1. フォームの各値から build_transaction() で検証済み Transaction を生成
   → ValidationError なら messagebox.showwarning でエラー表示して処理中断
2. editing_id が None の場合:
     repository.add(transaction) で新規追加、affected_id = 発番されたID
   editing_id が None でない場合:
     affected_id = editing_id
     repository.update(affected_id, transaction)
     exit_edit_mode() で編集モード解除（ボタン表示を「追加」に戻す）
3. refresh_derived_display()（一覧・合計の再描画）
4. _select_row() で対象行を選択・フォーカス・スクロール表示
5. on_clear_inputs() でフォームをリセット
```

### 5.4 編集モード（`on_tree_double_click` / `_enter_edit_mode` / `exit_edit_mode`）

- ダブルクリックされた行の`iid`から`int`変換したIDで`repository.get()`し、`None`でなければ編集モードに入る。
- 編集モードに入るとフォームの各値がTransactionの内容で埋められ、追加/更新ボタンのテキストが「更新」になり、`app.editing_id`がそのIDに設定される。
- **フォームへの復元はTreeviewの表示行からではなく、Repositoryから取得した`Transaction`から行う**（表示専用データを業務データの代わりに使わない、という設計原則の実例）。

### 5.5 削除（`on_delete_selected`）

```
1. Treeview選択が空なら「削除する行を選択してください」と案内して終了
2. 確認ダイアログ（askyesno）で「いいえ」ならキャンセル
3. 選択中のiidをintのsetに変換し、それぞれ repository.delete() を呼ぶ
4. 削除対象に編集中のIDが含まれていた場合、編集モードを解除しフォームをクリア
5. refresh_derived_display()
```

### 5.6 ソート（`on_sort_column`）

- 同じ列を再クリック: `sort_reverse`を反転
- 別の列をクリック: `sort_column`を切替、`sort_reverse=False`にリセット
- `refresh_list()`を呼んで再描画

ソートキー関数（`_SORT_KEYS`）:

| 列 | ソートキー |
|---|---|
| `date` | `transaction.date` |
| `type` | `transaction.transaction_type` |
| `category` | `transaction.category` |
| `amount` | `transaction.amount` |
| `memo` | `transaction.memo` |

### 5.7 種別変更時のカテゴリ切替（`on_type_changed`）

`type_var`の値に応じて`category_combo`の選択肢を`EXPENSE_CATEGORIES`／`INCOME_CATEGORIES`に切り替え、先頭の値を選択状態にする（種別変更のたびにカテゴリ選択がリセットされる）。

### 5.8 合計表示（`refresh_totals`）

`repository.calculate_totals()`の`(expense, income, net)`を取得し、`total_var`に`net`（ネット残高）、`detail_var`に`（支出: ¥xxx / 収入: ¥xxx）`をセットする。

### 5.9 統計画面の起動（`on_show_summary`）

```
1. repository.get_all() が空なら「表示するデータがありません」と案内して終了
2. 関数内で from ..summary.view import SummaryWindow（遅延import）
3. SummaryWindow(app, transactions) を生成（スナップショットを渡す。Repository自体は渡さない）
```

## 6. CSV入出力詳細仕様

### 6.1 定数

```python
_CSV_HEADER = ["日付", "種類", "カテゴリ", "金額", "メモ"]
_KNOWN_HEADERS = (_CSV_HEADER, _CSV_HEADER[:4])  # 5列/4列のヘッダをそれぞれ許容
```

### 6.2 `export_csv(items, path) -> int`

```
1. items（(内部ID, Transaction)のリスト）を (date, 内部ID) の昇順でソート
2. UTF-8（BOMなし）・newline=""でファイルを開く
3. ヘッダ行を書き出す
4. 各Transactionを to_csv_row() で ["YYYY/MM/DD", 種別, カテゴリ, 金額(str), メモ] に変換して書き出す
5. 書き出した件数を返す
```

- ソートキーが`(date, 内部ID)`であるため、同一日付内のタイブレークは「登録・取込順（内部ID昇順）」で安定する。
- ファイルI/O失敗時は`OSError`がそのまま呼び出し元に伝播する。

### 6.3 `import_csv(path) -> CsvImportResult`

```python
class CsvImportResult(NamedTuple):
    transactions: list[Transaction]
    skipped_count: int
    errors: list[tuple[int, ValidationError]]
```

```
1. utf-8-sig でファイル全体を読み込み csv.reader で行リスト化
   → OSError（ファイルが開けない）/ UnicodeDecodeError（UTF-8として不正）はここで送出、
     一部でも読み込んでいた内容は破棄される（全件失敗）
2. 先頭行が _KNOWN_HEADERS のいずれかと一致すればヘッダとして読み飛ばす
   （一致しなければ1行目からデータ行として扱う）
3. 各行について：
   - 空行（全セルが空白のみ、または行自体が空）は無視（エラーにもスキップ数にも計上しない）
   - build_transaction_from_row(row) で検証 → 成功なら transactions に追加、
     ValidationError なら errors に (行番号, error) を追加
4. skipped_count = len(errors) として結果を返す
```

- **行番号**は1始まりで、ヘッダ行をスキップした場合はデータの実際のファイル上の行番号（`enumerate(..., start=start_index+1)`）。
- **部分成功方式**: ファイルが最後まで読める限り、1行のエラーが他の行の取込を妨げない。ファイル自体が読めない場合はどの行も反映されない。
- 呼び出し元（`transaction_entry.logic.on_import_csv`）は`result.transactions`をループしてそれぞれ`repository.add()`する。つまり**Repositoryへの反映はファイル全体の読込・検証が完了した後にまとめて行われ**、途中の行のエラーでRepositoryが部分的に汚染されることはない。

### 6.4 CSV仕様まとめ表

| 項目 | 仕様 |
|---|---|
| 読込エンコーディング | `utf-8-sig`（BOMなし/ありどちらも透過的に読める） |
| 書出エンコーディング | `utf-8`（BOMなし） |
| ヘッダ判定 | 5列ヘッダまたは4列ヘッダと完全一致した場合のみスキップ。それ以外は1行目からデータ扱い |
| 許容列数 | 4列（メモなし）または5列。それ以外は`invalid_column_count`でスキップ |
| 空行 | 無視（エラーカウントに含めない） |
| 重複チェック | なし（同一ファイルを2回取り込むと2重登録される） |
| 取込の反映単位 | ファイル全体読了後に、検証成功分のみ一括でRepositoryに追加 |

## 7. 統計画面（summary）詳細仕様

### 7.1 `SummaryWindow`（`view.py`）

- `tk.Toplevel`のモーダルウィンドウ（`transient(parent)` + `grab_set()`）。
- コンストラクタ引数`transactions: list[Transaction]`はスナップショットであり、以後メイン画面の変更を反映しない。
- `_create_tab(tab_name, renderer, display_types)`で「カテゴリ別」「年別」「月別」の3タブを生成。各タブは独立した`type_var`（表示対象切替用の`StringVar`）を持つ。ラジオボタンの`command`で`renderer(self, body_frame, type_var)`を再実行し、タブ内だけを再描画する。表示対象の選択肢は、カテゴリ別が`TRANSACTION_TYPES`、年別・月別が`SUMMARY_DISPLAY_TYPES`（支出/収入/合計）。
- `_create_month_filter()`でNotebookの上に全タブ共通の月範囲フィルタを配置する。選択肢は`aggregation.available_months()`が返す年月のみで、表示ラベルは`format_month_label`による「2026年1月」形式。先頭の`NO_MONTH_SELECTED`（`"(指定なし)"`）が絞り込みなしを表す。
- `month_start` / `month_end`プロパティが、選択中の表示ラベルを内部形式（`"2026-01"`）に引き直して返す。未選択時は`None`。
- フィルタ変更時は`_render_all_tabs()`が`_tab_renderers`に登録済みの全タブ再描画関数を呼ぶ（タブごとの表示対象の選択状態は保持される）。

### 7.2 集計処理（`aggregation.py`）

pandasに依存するのはこのモジュールのみ。年月キーの文字列形式（`_MONTH_KEY_FORMAT = "%Y-%m"`）は本モジュールで一元管理し、画面側は`available_months()`経由で取得した値をそのまま`filter_by_month_range()`に渡す。

```python
def filter_by_type(transactions, transaction_type) -> list[Transaction]
def available_months(transactions) -> list[str]                    # 例: ["2025-12", "2026-01"]
def filter_by_month_range(transactions, start=None, end=None) -> list[Transaction]
def summarize_by_category(transactions) -> pd.DataFrame   # index=category, columns=[合計,件数,割合(%)]
def summarize_by_month(transactions) -> pd.DataFrame       # index=YYYY-MM, columns=[合計,件数]
def summarize_by_year(transactions) -> pd.DataFrame        # index=YYYY,    columns=[合計,件数]
def summarize_totals_by_month(transactions) -> pd.DataFrame # index=YYYY-MM, columns=[支出合計,収入合計,差額]
def summarize_totals_by_year(transactions) -> pd.DataFrame  # index=YYYY,    columns=[支出合計,収入合計,差額]
```

| 関数 | 集計キー | 追加列 | 並び順 | 空入力時 |
|---|---|---|---|---|
| `summarize_by_category` | `category` | `割合(%)` = 合計に対する割合を小数第1位で丸め | `割合(%)`の降順 | 列を持たない空`DataFrame`（`.empty is True`） |
| `summarize_by_month` | `date.strftime("%Y-%m")` | なし | インデックス（年月）昇順 | 同上 |
| `summarize_by_year` | `str(date.year)` | なし | インデックス（年）昇順 | 同上 |
| `summarize_totals_by_month` / `summarize_totals_by_year` | 同上（`_summarize_totals`で共通化） | `差額` = `収入合計 - 支出合計` | インデックス昇順 | 同上 |

`filter_by_month_range`は`start`・`end`の指定月自身を範囲に含む（両端閉区間）。`"%Y-%m"`はゼロ埋めされるため、辞書順比較がそのまま年月の前後関係になる。いずれかが`None`ならその側の制限は無い。

`summarize_totals_*`は種別でフィルタせず`pivot_table`で支出・収入を列方向に展開する。片方の種別しか存在しない期間でも列が欠けないよう`reindex`で0埋めする。金額は支出・収入とも正の値で保持されるため、差額は減算で求める。

呼び出し側（`render_*_tab`）は必ず`.empty`で分岐し、空の場合はテーブル・グラフを描画せず「〇〇データがありません」を表示する。

### 7.3 描画処理（`logic.py`）

`logic.py`という名称だが、実体はTreeview構築とmatplotlib描画（レンダラー）である（アーキテクチャ設計書 6章参照）。

表示対象の選択肢（`SUMMARY_TOTAL_LABEL` / `SUMMARY_DISPLAY_TYPES`）は本モジュールで定義する。「合計」は取引種別ではなく統計画面だけの表示オプションのため、ドメインの取引種別（`shared/constants.py`の`TRANSACTION_TYPES`、`shared/models.py`の`TransactionType`と一致必須）とは意図的に分けている。

| 関数 | 役割 |
|---|---|
| `reset_render_container(body_frame)` | 既存の子ウィジェットを全破棄し、テーブル行（高さ150固定）・グラフ行（高さ350以上）の2段グリッドを持つ新しいコンテナを生成 |
| `_transactions_in_range(window)` | ウィンドウ共通の月範囲フィルタ（`window.month_start` / `month_end`）を適用した取引一覧を返す。全`render_*_tab`が集計前に経由する |
| `render_category_tab` | 月範囲フィルタ→種別フィルタ→カテゴリ別集計→テーブル＋円グラフを描画 |
| `render_monthly_tab` / `render_yearly_tab` | `_render_period_tab`に期間の粒度（`period_label`・`index_formatter`・集計関数）を渡す薄いラッパー |
| `_render_period_tab(...)` | 月別・年別の共通描画。表示対象が「合計」なら種別で絞らず`summarize_totals_*`＋差額グラフ、それ以外は従来の種別別集計＋合計グラフ |
| `build_summary_table(parent, data, category_label, initial_sort_column, index_formatter)` | 集計結果`DataFrame`をTreeviewテーブルとして表示。列見出しクリックで独自ソート（`on_sort`のクロージャで列ごとの型に応じた比較を行う）。`index_formatter`はindex列の**表示文字列のみ**を変換し、ソートは変換前の値で行うため並び順は変わらない |
| `_calculate_figure_size(parent, width_default)` | `parent.update()`で実際のウィジェットサイズを確定させ、ピクセル÷100でFigureのインチサイズを算出 |
| `embed_figure(parent, fig)` | `FigureCanvasTkAgg`でFigureをTkウィジェットに埋め込み、`canvas.draw()`後に`pack`する |
| `plot_pie_chart` | カテゴリ別円グラフ。凡例ラベルは「カテゴリ名 (割合%)」形式 |
| `plot_bar_chart` | 年別/月別棒グラフ。金額を1000で割って「千円」単位表示、X軸ラベルを45度回転 |
| `plot_net_line_chart` | 「合計」選択時の差額折れ線グラフ（マーカー付き）。ゼロ位置に基準線を引き、マイナスの区間のみ基準線との間を赤く塗る。単位・ラベル回転は`plot_bar_chart`と同じ |

`build_summary_table`の値表示ルール（`format_value`）:

| 列 | 表示形式 |
|---|---|
| `MONEY_COLUMNS`（`合計`, `支出合計`, `収入合計`, `差額`） | `format_yen(int(value))`（¥区切り） |
| `割合(%)` | 小数第1位までの文字列（`f"{value:.1f}"`） |
| その他の数値列（`件数`等） | 3桁区切りの整数文字列 |
| それ以外 | `str(value)`そのまま |

index列の表示は`index_formatter`に従う（月別=`format_month_label`で「2026年1月」、年別=`format_year_label`で「2026年」、カテゴリ別=変換なし）。グラフのX軸ラベルも同じ形式にそろえるため、描画前に`DataFrame.rename(index=index_formatter)`した表示用のコピーを渡す。

## 8. グラフ描画・日本語フォント仕様

```python
_FONT_RC = {
    "font.sans-serif": ["MS Gothic", "Hiragino Sans", "IPAexGothic", "sans-serif"],
    "axes.unicode_minus": False,
}
mpl.rcParams.update(_FONT_RC)   # summary/logic.py のimport時に一度だけ適用
```

- 適用範囲は**プロセス全体**（本アプリケーションはmatplotlibをTkinter埋め込み専用にのみ使用するため、恒久適用で問題ない）。
- **設計上の注意点（過去の不具合と修正の記録）**: 当初は`mpl.rc_context(_FONT_RC)`で各描画関数呼び出しのたびに一時適用する実装だった。しかし`FigureCanvasTkAgg`はウィジェットのリサイズ等をきっかけに`after_idle`で**非同期に**再描画（`draw_idle` → `draw()`）することがあり、この非同期再描画は`with`ブロックを抜けた後（rcParamsが既定値のDejaVu Sansに戻った後）に発生するため、初回表示やウィンドウリサイズ時に日本語グリフが見つからず文字化け（□）する不具合があった。`mpl.rcParams.update()`によるモジュールimport時の恒久適用に変更することで解消済み。
- `axes.unicode_minus = False`は、日本語フォント使用時にマイナス記号が文字化けするのを防ぐための設定（本アプリの棒グラフ・軸目盛りに影響）。

## 9. 共通ユーティリティ

### 9.1 `shared/balance.py`

```python
class Totals(NamedTuple):
    expense: int
    income: int
    net: int

def calculate_totals(transactions: list[Transaction]) -> Totals
```

- pandasに依存しない純粋関数。`transaction_type == "支出"`の合計、`== "収入"`の合計、`net = income - expense`を算出。
- 通常の取引登録画面が常時必要とするため、あえてpandas非依存モジュール（`summary/aggregation.py`とは別）に配置されている。

### 9.2 `shared/formatters.py`

```python
def format_yen(value: int) -> str          # 例: 1234 -> "¥1,234"
def format_month_label(month: str) -> str  # 例: "2026-05" -> "2026年5月"（月のゼロ埋めなし）
def format_year_label(year: str) -> str    # 例: "2026" -> "2026年"
def format_sort_heading(label, *, active, reverse) -> str
    # 非アクティブ列は "▽"、アクティブ列は昇順 "▲" / 降順 "▼" を付与
    # 例: format_sort_heading("日付", active=True, reverse=False) -> "日付 ▲"
```

`format_sort_heading`は`transaction_entry`（一覧の列見出し）と`summary`（統計テーブルの列見出し）の両方で共通利用される。どの列でソート中かを区別できるよう、ソート対象でない列は白い三角（▽）で表示する。

`format_month_label` / `format_year_label`は統計画面の表示専用。集計キー（`"2026-05"`）は並び替えのためゼロ埋めされた比較可能な形式を保ち、画面表示の直前にのみ日本語表記へ変換する。

## 10. 起動処理詳細

`app.py: main()`

```
1. Windows DPI Awareness 設定を試みる（ctypes.windll.shcore.SetProcessDpiAwareness(1)）
   → ImportError/AttributeError（非Windows環境等）は無視して続行
2. MainWindow() を生成（この中で TransactionRepository と UI 全体が構築される）
3. ttk.Style(app) で利用可能なテーマ一覧に "vista" があれば適用
4. app.mainloop() でイベントループ開始
5. 上記のいずれかで未捕捉の例外が発生した場合：
   - messagebox 等で画面表示はしない
   - print() と traceback.print_exc() で標準出力にのみ記録
   （pythonw.exe 実行時は標準出力が破棄されるため、この場合ログは残らない点に留意）
```

## 11. エラーハンドリング方針一覧

| 例外種別 | 発生箇所 | ハンドリング |
|---|---|---|
| `ValidationError`（`code`/`field`付き） | `shared/validation.py` | GUI: `messagebox.showwarning`で表示して処理中断。CSV取込: 行単位でキャッチし`errors`に集約、他行の処理は継続 |
| `OSError` | `csv_storage.export_csv` / `import_csv`（ファイルI/O） | GUI: `messagebox.showerror`で表示、処理中断（データ変更なし） |
| `UnicodeDecodeError` | `csv_storage.import_csv`（UTF-8以外のファイル読込） | GUI: 専用メッセージ（「ファイルの文字コードを読み取れませんでした」）を表示、取込は行われない |
| `KeyError` | `TransactionRepository.update`（存在しないID） | 呼び出し元（`on_add_or_update`）は`editing_id`がRepositoryに存在する前提で呼ぶため、通常フローでは発生しない設計。GUI側での明示的なcatchはなし |
| その他未捕捉例外（起動時） | `app.main()` | `try/except Exception`で標準出力に記録するのみ（画面表示なし） |

## 12. テスト対応表

| モジュール／機能 | テストファイル | 主な観点 |
|---|---|---|
| `shared/models.py` | `test_models.py` | `TransactionType`と`TRANSACTION_TYPES`の整合性 等 |
| `shared/validation.py` | `test_validation.py` | 金額・日付・種別・カテゴリの正常系／異常系 |
| `shared/balance.py` | `test_balance.py` | 支出/収入合計・ネット残高の計算 |
| `shared/csv_storage.py` | `test_csv_storage.py` | 列数・ヘッダ判定・BOM対応・部分成功・エクスポート順序・往復変換 |
| `transaction_entry/repository.py` | `test_repository.py` | CRUD、ID採番・非再利用、Tkinter非依存の確認 |
| `summary/aggregation.py` | `test_aggregation.py` | カテゴリ別/月別/年別集計の正しさ、月範囲フィルタの境界値、収支合計（支出・収入・差額）の集計 |
| `transaction_entry`全体（GUI統合） | `test_transaction_entry_flow.py` | 登録・更新・ソート・削除・CSV往復のユーザー操作フロー |
| `refresh_list`の選択保持 | `test_treeview_selection_regression.py` | 再構築後の選択・フォーカス維持／非維持の3パターン |

`tests/conftest.py`の`_tk_root`フィクスチャ（セッションスコープ、`MainWindow`を1つだけ生成）により、Tkinterの複数ルート生成に伴う不安定さを回避しつつ、各テストでは`repository`差し替えとUI状態リセットによってテスト間の独立性を確保している。
