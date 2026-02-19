# Yui (ゆい) 言語

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Yui（ゆい）** は、構文をカスタマイズ可能なプログラミング言語です。日本語風の自然な構文から、Python風の構文、絵文字構文まで、JSONファイルで自由に定義できます。

## 特徴

✨ **構文のカスタマイズ性**
- JSON形式の構文定義ファイルで自由に文法を変更可能
- 日本語、英語、絵文字など多様な構文を定義可能

🔄 **構文変換機能**
- あるYuiコードを別の構文に自動変換（`--convert-to`）
- 変換結果は `<構文名>/` ディレクトリに保存
- Markdownファイル内の `yui` コードブロックも一括変換

📊 **テスト支援**
- `--pass@1`: 複数スクリプトを実行して成功率（pass@1）を計算
- `--test-examples`: 組み込みサンプルをすべてテスト
- `_doctest.yui` 規約: `a.yui` + `a_doctest.yui` を自動連結して実行

🎯 **シンプルな言語仕様**
- 変数、配列、オブジェクト
- 条件分岐（もし〜ならば）
- ループ（N回くり返す）
- 関数定義

💻 **インタラクティブモード**
- REPL環境で即座にコードを実行・検証

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/KuramitsuLab/yuichan.git
cd yuichan

# インストール（開発モード）
pip install -e .
```

## クイックスタート

### 1. 基本的な使い方

```bash
# ファイルを実行（--syntax は必須）
yui --syntax yui examples/hello.yui

# 対話モード
yui --syntax yui -i

# ヘルプを表示
yui --help
```

### 2. サンプルコード（Yui構文）

```yui
# 変数の定義
x = 10

# くり返し
3回くり返す {
  xを増やす
}

# 条件分岐
もし x が 13 ならば {
  x = 100
}
```

### 3. サンプルコード（Python風構文）

```python
# 変数の定義
x = 10

# くり返し
for _ in range(3):
    x += 1

# 条件分岐
if x == 13:
    x = 100
```

## コマンドリファレンス

### 基本コマンド

```bash
# ファイルを実行
yui --syntax yui file.yui

# 対話モード（インタラクティブREPL）
yui --syntax yui -i

# バージョン表示
yui --version
```

### 環境の入出力

```bash
# 環境変数をJSONファイルから読み込んで実行
yui --syntax yui --input input.json file.yui

# 実行後の環境変数をJSONファイルに保存
yui --syntax yui file.yui --output output.json

# 組み合わせ例（環境をチェーン）
yui --syntax yui --input env1.json step1.yui --output env2.json
yui --syntax yui --input env2.json step2.yui --output result.json
```

**input.json の例:**
```json
{
  "x": 10,
  "y": 20,
  "data": [1, 2, 3, 4, 5]
}
```

### カスタム構文の使用

```bash
# Python風の構文で実行
yui --syntax pylike file.yui

# 絵文字構文で実行
yui --syntax emoji file.yui

# 独自の構文ファイルで実行
yui --syntax path/to/my-syntax.json file.yui
```

### 構文変換（--convert-to）

```bash
# Yui構文 → Python風構文に変換（pylike/ ディレクトリに保存）
yui --syntax yui --convert-to pylike file.yui

# 複数ファイルを一括変換
yui --syntax yui --convert-to pylike *.yui

# Markdownファイル内の ```yui ブロックを変換
yui --syntax yui --convert-to pylike README.md
```

変換結果は `<target_syntax>/` ディレクトリに元のファイル名で保存されます。

**変換前（Yui構文）:**
```yui
x = 10
xを増やす
3回くり返す {
  xを増やす
}
```

**変換後（Python風構文）→ `pylike/file.yui` に保存:**
```python
x = 10
x += 1
for _ in range(3):
    x += 1
```

### テスト・成功率計測（--pass@1）

複数のスクリプトファイルを実行し、成功率（pass@1）を計算します。

```bash
yui --syntax yui --pass@1 test/*.yui
```

**動作ルール:**
- `_doctest.yui` で終わるファイルは単独実行の対象から除外
- `a.yui` を実行する際、`a_doctest.yui` が存在すれば両方を連結して実行

**出力例:**
```
✓ test/01_hello.yui
✓ test/02_fib.yui + 02_fib_doctest.yui
✗ test/03_sort.yui
  | Error: ...

==================================================
Total: 3
Passed: 2
Failed: 1
pass@1: 66.67% (2/3)
==================================================
```

### サンプル管理

```bash
# 利用可能なサンプルを一覧表示
yui --list-examples

# サンプルを .yui ファイルとして生成（examples/ ディレクトリ）
yui --syntax yui --make-examples

# 特定のサンプルのみ生成
yui --syntax yui --make-examples --example hello

# すべてのサンプルをテスト実行
yui --syntax yui --test-examples
```

## 言語仕様

### データ型

```yui
# 整数
x = 42

# 浮動小数点数
pi = 3.14

# 文字列
name = "Yui"

# 配列
numbers = [1, 2, 3, 4, 5]

# オブジェクト（辞書）
person = {"name": "Yui", "age": 20}
```

### 演算

```yui
# 算術演算
x = 10 + 5
y = 20 - 3
z = 6 * 7
w = 15 / 3

# インクリメント・デクリメント（Yui構文）
xを増やす
yを減らす

# 配列への追加（Yui構文）
numbersに10を追加する
```

### 制御構造

#### 条件分岐（Yui構文）

```yui
もし x が 10 ならば {
  xを増やす
}

もし x が 5 より大きい ならば {
  x = 0
} そうでなければ {
  xを増やす
}
```

#### ループ（Yui構文）

```yui
# N回繰り返し
5回くり返す {
  xを増やす
}

# Break
10回くり返す {
  xを増やす
  もし x が 5 ならば {
    くり返しを抜ける
  }
}
```

### 関数

```yui
# 関数定義（Yui構文）
add = 入力 a, b に対して {
  a + b が答え
}

# 関数呼び出し
result = add(10, 20)
```

## 構文定義ファイル

構文は `yuichan/syntax/` ディレクトリの JSON ファイルで定義されます。

### 組み込み構文

| 名前 | ファイル | 説明 |
|------|----------|------|
| `yui` | `syntax/yui.json` | 日本語風の自然な構文（デフォルト） |
| `pylike` | `syntax/pylike.json` | Python風の構文 |
| `emoji` | `syntax/emoji.json` | 絵文字ベースの構文 |

### 構文定義の主要キー

```json
{
  "number-first-char": "[0-9]",
  "name-first-char": "[A-Za-z_\\u4E00-\\u9FFF]",
  "string-begin": "\"",
  "string-end": "\"",

  "assignment-infix": "=",
  "increment-end": "増やす",
  "decrement-end": "減らす",

  "if-begin": "もし",
  "if-infix": "が",
  "if-then": "ならば",
  "if-else": "そうでなければ",

  "repeat-times": "回[、]?",
  "repeat-block": "くり返す",

  "block-begin": "\\{",
  "block-end": "\\}"
}
```

## サンプルプログラム

### フィボナッチ数列

**Yui構文:**
```yui
fib = 入力 n に対して {
  もし n が 1 以下 ならば {
    n が答え
  } そうでなければ {
    a = fib(n - 1)
    b = fib(n - 2)
    a + b が答え
  }
}

result = fib(10)
```

**Python風構文:**
```python
def fib(n):
    if n <= 1:
        return n
    else:
        a = fib(n - 1)
        b = fib(n - 2)
        return a + b

result = fib(10)
```

### 配列操作

```yui
# 配列の初期化
data = [1, 2, 3]

# 要素の追加
dataに4を追加する
dataに5を追加する

# ループで処理
|data|回くり返す {
  data[0]を増やす
}
```

## 開発

### テスト実行

```bash
# すべてのテストを実行
pytest

# 特定のテストファイル
pytest yuichan/test_yuiparser.py
pytest yuichan/test_yuiast.py
pytest yuichan/test_yuiemit.py

# カバレッジ付き
pytest --cov=yuichan
```

### テストファイル構成

- `test_yuiparser.py`: パーサーのテスト
- `test_yuiast.py`: ASTノード・ランタイムのテスト
- `test_yuiemit.py`: コード生成（構文変換）のテスト
- `test_pattern.py`: 正規表現パターン処理のテスト

### プロジェクト構成

```
yuichan/
├── yuichan/
│   ├── __init__.py          # パッケージ初期化
│   ├── main.py              # CLIエントリーポイント
│   ├── yuiparser.py         # パーサー（構文解析）・CodingVisitor
│   ├── yuiast.py            # AST定義・ランタイム
│   ├── yuiexample.py        # 組み込みサンプル定義
│   ├── syntax/
│   │   ├── yui.json         # 日本語風構文定義
│   │   ├── pylike.json      # Python風構文定義
│   │   └── emoji.json       # 絵文字構文定義
│   ├── test_yuiparser.py    # パーサーテスト
│   ├── test_yuiast.py       # ASTテスト
│   ├── test_yuiemit.py      # コード生成テスト
│   └── test_pattern.py      # パターンテスト
├── test/                    # .yui テストスクリプト
├── examples/                # 生成されたサンプルファイル
├── pyproject.toml           # プロジェクト設定
├── LICENSE                  # MITライセンス
└── README.md               # このファイル
```

## パッケージング

```bash
# ビルド
python -m build

# TestPyPIにアップロード
python -m twine upload --repository testpypi dist/*

# PyPIにアップロード
python -m twine upload dist/*
```

## ライセンス

MIT License - Copyright (c) 2026 Kimio Kuramitsu's Laboratory

詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 貢献

プルリクエストや Issue の投稿を歓迎します！

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## リンク

- [GitHub リポジトリ](https://github.com/KuramitsuLab/yuichan)
- [Issue トラッカー](https://github.com/KuramitsuLab/yuichan/issues)

## 謝辞

Yui言語の開発は、プログラミング教育と多言語対応プログラミング環境の研究の一環として行われています。
