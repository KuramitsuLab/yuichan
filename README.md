# Yui (ゆい) 言語

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Yui（ゆい）** は、構文をカスタマイズ可能なプログラミング言語です。日本語風の自然な構文から、Python風の構文まで、JSONファイルで自由に定義できます。

## 特徴

✨ **構文のカスタマイズ性**
- JSON形式の構文定義ファイルで自由に文法を変更可能
- 日本語、英語、その他の言語で独自の構文を定義

🔄 **構文変換機能**
- あるYuiコードを別の構文に自動変換（CodeVisitor使用）
- Markdownファイル内のコードブロックも一括変換

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
# ファイルを実行
yui examples/hello.yui

# 対話モード
yui -i

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
yui file.yui

# 対話モード（インタラクティブREPL）
yui -i

# バージョン表示
yui --version
```

### 環境の入出力

```bash
# 環境変数をJSONファイルから読み込んで実行
yui --input input.json file.yui

# 実行後の環境変数をJSONファイルに保存
yui file.yui --output output.json

# 組み合わせ例（環境をチェーン）
yui --input env1.json step1.yui --output env2.json
yui --input env2.json step2.yui --output result.json
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
# Python風の構文ファイルで実行
yui --syntax syntax-py.json file.yui

# 独自の構文ファイルで実行
yui --syntax my-syntax.json file.yui
```

### 構文変換（CodeVisitor）

```bash
# Yui構文 → Python風構文に変換
yui --syntax syntax-yui.json file.yui --syntax-to syntax-py.json

# Markdownファイル内の ```yui ブロックを変換
yui --syntax syntax-yui.json README.md --syntax-to syntax-py.json > README_py.md
```

**変換前（Yui構文）:**
```yui
x = 10
xを増やす
3回くり返す {
  xを増やす
}
```

**変換後（Python風構文）:**
```python
x = 10
x += 1
for _ in range(3):
    x += 1
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
# 算術演算（Python風構文の場合）
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

構文は `syntax-*.json` ファイルで定義されます。以下は主要な終端記号の例です：

```json
{
  "number-begin": "[0-9]",
  "identifier-begin": "[A-Za-z_]",
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

### デフォルト構文ファイル

- `syntax-yui.json`: 日本語風の自然な構文（デフォルト）
- `syntax-py.json`: Python風の構文

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

# カバレッジ付き
pytest --cov=yuichan
```

### テストファイル構成

- `test_yuiparser.py`: パーサーのテスト
- `test_yuiast.py`: ASTノード・ランタイムのテスト
- `test_pattern.py`: 正規表現パターン処理のテスト

### プロジェクト構成

```
yuichan/
├── yuichan/
│   ├── __init__.py          # パッケージ初期化
│   ├── main.py              # CLIエントリーポイント
│   ├── yuiparser.py         # パーサー（構文解析）
│   ├── yuiast.py            # AST定義・ランタイム
│   ├── syntax-yui.json      # Yui構文定義
│   ├── syntax-py.json       # Python風構文定義
│   ├── test_yuiparser.py    # パーサーテスト
│   ├── test_yuiast.py       # ASTテスト
│   └── test_pattern.py      # パターンテスト
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
