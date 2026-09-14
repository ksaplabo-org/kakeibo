# アーキテクチャ設計書

- 対象システム: 家計簿アプリケーション（kakeibo-app）
- 本書の位置づけ: 現行実装（2026年時点のソースコード）をリバースエンジニアリングして作成したアーキテクチャ設計書。将来の仕様ではなく **実装済みの構造** を記述する。

## 目次

1. [システム概要](#1-システム概要)
2. [技術スタック](#2-技術スタック)
3. [全体アーキテクチャ](#3-全体アーキテクチャ)
4. [ディレクトリ構成と責務](#4-ディレクトリ構成と責務)
5. [モジュール依存関係](#5-モジュール依存関係)
6. [レイヤ設計と設計原則](#6-レイヤ設計と設計原則)
7. [起動シーケンス](#7-起動シーケンス)
8. [永続化方式](#8-永続化方式)
9. [テスト戦略](#9-テスト戦略)
10. [アーキテクチャ上の既知の制約](#10-アーキテクチャ上の既知の制約)

---

## 1. システム概要

Python + Tkinter で実装された、Windows上で動作するシングルプロセス・シングルウィンドウのデスクトップGUIアプリケーション。

- 起動〜終了までの1プロセス内で完結する（サーバー・DBなし）
- 業務データはプロセスのメモリ上（`TransactionRepository`）にのみ保持
- 永続化はユーザー操作によるCSVファイルの明示的な入出力のみ
- GUIスレッドはTkinterのメインループ1本のみ（非同期処理・マルチスレッドなし）

## 2. 技術スタック

| 分類 | 技術 | バージョン制約 | 用途 |
|---|---|---|---|
| 言語 | Python | >= 3.10 | 実行環境 |
| GUI | tkinter / ttk（標準ライブラリ） | - | ウィンドウ・フォーム・一覧表示 |
| データ処理 | pandas | >= 2.0 | 統計集計（`features/summary`限定） |
| 描画 | matplotlib | >= 3.7 | 統計グラフ（円グラフ・棒グラフ・折れ線グラフ） |
| テスト | pytest | >= 7.0 | 自動テスト |
| パッケージング | setuptools（`pyproject.toml`） | - | `pip install -e .` によるインストール |
| 永続化 | CSV（`csv`標準モジュール） | UTF-8 | エクスポート/インポート |

依存ライブラリは `pandas` と `matplotlib` の2つのみで、いずれも「統計表示」機能に限定して使用される。通常の入力・一覧・保存機能はこの2つに依存しない（後述のレイヤ分離を参照）。

## 3. 全体アーキテクチャ

レイヤードアーキテクチャ（MVC類似の3層構成）を、機能（画面）単位のパッケージ内で反復する構造。

```
┌─────────────────────────────────────────────────────────┐
│  app.py / __main__.py            起動エントリーポイント     │
└───────────────────────┬───────────────────────────────────┘
                         │ 生成
┌───────────────────────▼───────────────────────────────────┐
│ features/transaction_entry （メイン画面機能）                │
│                                                             │
│  view.py  ── MainWindow（tk.Tk） 画面構築・イベント登録のみ   │
│      │ command=lambda: on_xxx(self)                       │
│      ▼                                                     │
│  logic.py ── イベントハンドラ（Controller）                  │
│      │ validation呼出       │ repository操作                │
│      ▼                     ▼                               │
│  shared/validation.py   repository.py（TransactionRepository）│
│                             │  = 業務データの正本（SSoT）      │
└─────────────────────────────┼───────────────────────────────┘
                              │ get_all() でスナップショットを渡す
┌─────────────────────────────▼───────────────────────────────┐
│ features/summary （統計画面機能・遅延import）                 │
│                                                              │
│  view.py  ── SummaryWindow（tk.Toplevel） タブ構成・月範囲     │
│      │        フィルタの配置のみ                              │
│      ▼                                                       │
│  logic.py ── 集計結果のTreeview表示・matplotlib描画（Renderer）│
│      │        表示対象（支出/収入/合計）の選択肢定義もここ      │
│      ▼                                                       │
│  aggregation.py ── pandasによる集計（カテゴリ別/月別/年別/     │
│                    収支合計）・期間キー形式と月範囲フィルタ     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ shared/ （両機能から共有される純粋ロジック・境界処理）            │
│  models.py      : Transaction（不変データ型）= ドメインモデル   │
│  constants.py   : カテゴリ・取引種別の定義                      │
│  validation.py  : 入力値・CSV行の検証（GUI/CSV共通）            │
│  balance.py     : 合計計算（pandas非依存の純粋関数）             │
│  formatters.py  : 表示用文字列整形                              │
│  csv_storage.py : CSV読み書き（I/O境界）                        │
└──────────────────────────────────────────────────────────────┘
```

## 4. ディレクトリ構成と責務

```text
kakeibo/
├── pyproject.toml                        パッケージ定義・依存関係・pytest設定
├── README.md                             利用者向けドキュメント
├── samples/                              サンプルCSV（正常系・異常系）
├── src/kakeibo_app/
│   ├── __main__.py                       `python -m kakeibo_app` エントリーポイント
│   ├── app.py                            起動処理（DPI設定・テーマ適用・mainloop）
│   ├── shared/                           機能横断の共有モジュール
│   │   ├── models.py                     Transaction（不変レコード）
│   │   ├── constants.py                  カテゴリ・取引種別の定義
│   │   ├── validation.py                 入力検証（GUI・CSV共通）
│   │   ├── balance.py                    合計計算（純粋関数）
│   │   ├── formatters.py                 表示用文字列整形
│   │   └── csv_storage.py                CSV入出力
│   └── features/                         画面（機能）単位のパッケージ
│       ├── transaction_entry/            収支入力・一覧画面
│       │   ├── repository.py             取引データの保持・CRUD（SSoT）
│       │   ├── logic.py                  GUIイベントハンドラ（Controller）
│       │   └── view.py                   画面構築（MainWindow）
│       └── summary/                      統計表示画面
│           ├── aggregation.py            pandasによる集計処理
│           ├── logic.py                  集計結果の表示・グラフ描画（Renderer）
│           └── view.py                   画面構築（SummaryWindow）
└── tests/                                自動テスト（レイヤ単位・統合）
```

| モジュール | 責務 | Tkinter依存 | pandas/matplotlib依存 |
|---|---|:---:|:---:|
| `shared/models.py` | ドメインモデル定義 | なし | なし |
| `shared/constants.py` | マスタデータ定義 | なし | なし |
| `shared/validation.py` | 入力・CSV行の検証 | なし | なし |
| `shared/balance.py` | 合計計算 | なし | なし |
| `shared/formatters.py` | 表示用整形 | なし | なし |
| `shared/csv_storage.py` | CSV I/O | なし | なし |
| `transaction_entry/repository.py` | データ保持・CRUD | なし | なし |
| `transaction_entry/logic.py` | イベント制御 | あり（messagebox/filedialog等） | なし |
| `transaction_entry/view.py` | 画面構築 | あり | なし |
| `summary/aggregation.py` | 統計集計 | なし | pandasのみ |
| `summary/logic.py` | 集計結果描画 | あり | matplotlib |
| `summary/view.py` | 画面構築 | あり | なし |
| `app.py` | 起動処理 | あり | なし |

## 5. モジュール依存関係

```
__main__.py → app.py → transaction_entry.view
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
      transaction_entry.logic  transaction_entry.repository
              │                          │
              ├──────────────┬───────────┘
              ▼              ▼
        shared.validation  shared.balance（repository経由）
              │
              ▼
      shared.models / shared.constants

transaction_entry.logic ──(遅延import: on_show_summary内)──→ summary.view
summary.view → summary.logic → summary.aggregation → shared.models
```

重要な特徴:

- **依存は一方向**（`shared` ← `features/*`。`shared`は`features`を参照しない）
- **`summary`パッケージは`transaction_entry`から関数レベルでは参照されず**、`on_show_summary()`内でのみ`import`される（後述6.5）
- `transaction_entry`パッケージは`summary`パッケージに依存しない逆方向の参照はない（`summary.view`が`transaction_entry`から受け取るのは`Transaction`のリストのみで、`MainWindow`や`Repository`型そのものには依存しない）

## 6. レイヤ設計と設計原則

現行コードのdocstring・コメントから読み取れる、意図的な設計判断を以下に整理する。

### 6.1 Transaction は不変な正準データ型

`shared/models.py` の `Transaction` は `NamedTuple`（イミュータブル）。文字列との相互変換（入力欄の文字列・表示用文字列・CSVの1行）は境界モジュール（`validation.py` / `formatters.py` / `csv_storage.py`）でのみ行い、`Transaction`自体は「検証済みの値」だけを保持する。更新は既存インスタンスの書き換えではなく新規生成で行う。

### 6.2 Repository が業務データの唯一の正本（SSoT）

`TransactionRepository`（`transaction_entry/repository.py`）がプロセス内で唯一の業務データ保持者。Treeview（`MainWindow.tree`）は表示専用のキャッシュであり、Treeviewの表示内容を読み取って業務データを復元することはしない。統計画面（`SummaryWindow`）にはRepositoryそのものではなく、開いた時点のスナップショット（`get_all()`の戻り値のリスト）を渡すため、開いた後にメイン画面のデータが変わっても統計画面には反映されない（自動更新なし）。

### 6.3 検証ロジックの一元化

金額・日付・取引種別・カテゴリの検証はすべて `shared/validation.py` に集約されている。GUIからの入力（`build_transaction`）もCSV取込（`build_transaction_from_row`）も同じ検証関数を経由するため、検証ルールが二重管理にならない。検証エラーは文字列ではなく `ValidationError`（`code`/`field`属性つき）で表現し、呼び出し側がメッセージ文字列を解析する必要がない設計になっている。

### 6.4 依存ライブラリのフットプリント限定

- `pandas` は `features/summary/aggregation.py` からのみimportされる。通常の取引登録・CSV入出力・合計計算（`shared/balance.py`）の経路はpandasに依存しない。
- `mpl.rcParams` の日本語フォント設定（`features/summary/logic.py`）はプロセス全体に一度だけ適用され、統計画面を開かない限りmatplotlibの初期化コストは発生しない。

### 6.5 統計画面の遅延import

`transaction_entry/logic.py` の `on_show_summary()` は、関数内で `from ..summary.view import SummaryWindow` を実行する（モジュールの先頭ではない）。これにより、統計画面を一度も開かないセッションではpandas/matplotlibの読み込みコストを回避できる。

### 6.6 集計キーの形式は集計層が所有する

統計画面の月範囲フィルタは、選択肢の生成（`aggregation.available_months()`）も絞り込み（`aggregation.filter_by_month_range()`）も`aggregation.py`側にある。年月キーの文字列形式（`"%Y-%m"`）は同モジュールの定数で一元管理され、`view.py`は取引データから期間キーを導出しない。これにより「コンボボックスが返す値」と「フィルタが期待する値」の形式が構造的にズレないことを保証し、pandas非依存の純粋関数としてテストできる範囲を広げている。

同様に、統計画面の表示対象の選択肢（`SUMMARY_DISPLAY_TYPES`＝支出/収入/合計）は`summary/logic.py`で定義する。「合計」は取引種別ではなく画面上の表示オプションであり、ドメインの取引種別（`shared/constants.py`の`TRANSACTION_TYPES`）に混ぜると`shared/models.py`の`TransactionType`との整合性（`tests/test_models.py`で検証）が崩れるため、意図的に別レイヤに置いている。

### 6.7 表示専用ウィジェットと業務データの分離

一覧表示（Treeview）はイベント（追加・更新・削除・ソート）のたびに全件削除→再構築される（`refresh_list()`）。この再構築で選択・フォーカス状態が失われないよう、再構築前後で「なお存在する行」の選択・フォーカスを明示的に復元するロジックが組み込まれている（`tests/test_treeview_selection_regression.py`で回帰テスト化）。

## 7. 起動シーケンス

```
python -m kakeibo_app
  └─ __main__.py: __name__ == "__main__" 判定
       └─ app.main()
            ├─ Windows DPI Awareness 設定（失敗しても無視）
            ├─ MainWindow() 生成
            │    ├─ TransactionRepository() 生成
            │    └─ _build_ui() でフォーム・一覧・ボタンを構築
            ├─ ttk.Style に "vista" テーマがあれば適用
            └─ app.mainloop() でイベントループ開始（ブロッキング）
```

起動時の未捕捉例外は `app.main()`内の `try/except` で捕捉し、標準出力にトレースバックを出力する（`pythonw`実行時は非表示になる点に注意、10章参照）。

## 8. 永続化方式

- **実行中**: すべて `TransactionRepository` 上のメモリ内 `dict[int, Transaction]`。アプリ終了で消失する。
- **永続化**: ユーザーが明示的に「保存」（CSVエクスポート）を行った場合のみファイルに書き出される。
- **読込**: 「一括取込」（CSVインポート）は既存データへの **追記** であり、置き換えではない。重複検知は行わない。

データベースやアプリ内蔵の自動保存機構は存在しない（9章「アーキテクチャ上の既知の制約」参照）。

## 9. テスト戦略

`tests/` はレイヤに対応する形で分割されている。

| テストファイル | 対象レイヤ／モジュール |
|---|---|
| `test_models.py` | `shared/models.py`（`TransactionType`と`TRANSACTION_TYPES`の整合性含む） |
| `test_validation.py` | `shared/validation.py` |
| `test_balance.py` | `shared/balance.py` |
| `test_csv_storage.py` | `shared/csv_storage.py` |
| `test_repository.py` | `transaction_entry/repository.py` |
| `test_aggregation.py` | `summary/aggregation.py` |
| `test_transaction_entry_flow.py` | `transaction_entry` の統合（GUIイベント→logic→repository→view反映） |
| `test_treeview_selection_regression.py` | `refresh_list()` の選択・フォーカス保持に対する狭い回帰テスト |

`tests/conftest.py` にはGUIテスト特有の制約に対する対応が明記されている。Tkinterはプロセス内で複数の `tk.Tk()` を生成・破棄すると不安定になることが確認されているため、`_tk_root` フィクスチャは **セッションスコープで1つだけ** `MainWindow` を生成し、各テストは業務データ（`repository`を差し替え）とUI状態（`sort_column`等）をリセットすることでテスト間の独立性を確保している。

## 10. アーキテクチャ上の既知の制約

- **単一ウィンドウ・単一スレッド**: 大量データ時のI/Oやグラフ描画がUIスレッドをブロックする可能性がある（非同期化なし）。
- **内部ID（`TransactionRepository._next_id`）はプロセス内限定の連番**であり、永続的なレコードIDではない。CSV保存後・再取込後にIDが再割当てされるため、外部システムとのID連携はできない。
- **統計画面はスナップショット固定**で、メイン画面のデータ変更を後から反映しない（意図的な設計だが、利用者からは「統計が更新されない」ように見える可能性がある）。
- **CSV取込に重複検知がない**ため、誤操作で同一データが重複登録されるリスクは実装上ケアされていない（運用でカバーする前提）。

詳細は「詳細設計書」および本タスク末尾の「課題・懸念点」を参照。
