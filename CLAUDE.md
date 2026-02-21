# CLAUDE.md — yuichan プロジェクト概要

## プロジェクト概要

**yuichan** は日本語プログラミング言語 Yui の実装。
パッケージは `yuichan/` に入っており、`python3 -m yuichan.main` で実行する。

---

## 主要ファイル構成

| ファイル | 役割 |
|----------|------|
| `yuichan/yuitypes.py` | `YuiValue`, `YuiType` とすべての型クラス、定数 |
| `yuichan/yuiast.py` | AST ノード定義（`ConstNode`, `NumberNode`, `StringNode` など）|
| `yuichan/yuiruntime.py` | `RuntimeVisitor`（`visit*` メソッド群）|
| `yuichan/yuiparser.py` | パーサー |
| `yuichan/yuicoding.py` | コード生成 visitor |
| `yuichan/yuistdlib.py` | 標準ライブラリ関数（`和`, `積`, `最大値` など）|
| `yuichan/main.py` | CLI エントリーポイント |
| `yuiast.py` (ルート) | 旧版 AST（`YuiRuntime` クラスも含む）。`yuichan/yuiast.py` と二重管理中 |

---

## 型システム（yuitypes.py）

### 型クラス一覧（TYPES リストの順序が重要）

```
YuiNullType    → null (None)
YuiBooleanType → true/false (bool) ← IntType より前に置くこと（bool は int のサブクラス）
YuiIntType     → 整数 (int)
YuiFloatType   → 少数 (float)
YuiStringType  → 文字列 (str) ← 内部は文字コードの配列
YuiArrayType   → 配列 (list)
YuiObjectType  → オブジェクト (dict)
```

### YuiValue の定数

```python
YuiValue.NullValue  = YuiValue(None,  type=YuiType.NullType)
YuiValue.TrueValue  = YuiValue(True,  type=YuiType.BooleanType)
YuiValue.FalseValue = YuiValue(False, type=YuiType.BooleanType)
```

### 重要メソッド

- `YuiType.to_native(node_or_value)` — YuiValue → Python native 値
- `YuiType.yui_to_native(value)` — 再帰的に native 変換（`exec()` の戻り値に使用）
- `YuiType.native_to_yui(native)` — Python native → YuiValue
- `YuiValue.stringfy_value(value, indent_prefix)` — 値を文字列表示（staticmethod）
- `YuiValue.arrayview` — 内部配列表現（`.array` は `arrayview` の別名）

---

## AST ノード

### ConstNode（旧 NullNode）

`None` / `True` / `False` を表すノード。`native_value` フィールドを持つ。

```python
ConstNode()        # null
ConstNode(True)    # true
ConstNode(False)   # false
```

### visitor メソッド名

ノードクラス名に対応: `visitConstNode`, `visitNumberNode`, `visitStringNode`, ...

---

## ランタイム

### exec() による統一実行

すべてのコード実行は `YuiRuntime.exec()` を通す。

```python
rt = YuiRuntime()
rt.exec(source, syntax='yui', eval_mode=False)
env = rt.enviroments[-1]  # ← typo: "enviroments"（e が1つ）
```

### 標準ライブラリの読み込み

Yui ソース先頭に `標準ライブラリを使う` が必要。

```python
STDLIB = "標準ライブラリを使う\n"
rt.exec(STDLIB + source)
```

---

## 既知の制限・注意事項

- **`BinaryNode` は未実装**：`+`, `*` などの演算子は実行時エラーになる。標準ライブラリの `和()`, `積()` などを使う。
- **文字列の内部表現**：`YuiStringType` の値は文字コード（int）の配列として格納される。
- **配列の等値比較**：`_array_equal(a, b)` で再帰比較。文字コード配列と文字列の相互比較も対応。
- **`NativeFunction.call()`** の戻り値は自動で `YuiValue` にラップされるが、stdlib 側でも明示的に返すこと。
- **`environments`**：`rt.environments[-1]` で最終スコープの変数環境を取得する。

---

## テスト

```bash
# ユニットテスト
python -m pytest yuichan/

# HumanEval ベンチマーク
python3 -m yuichan.main --pass@1 --syntax yui humaneval/*.yui
```

### テストファイル

| ファイル | 内容 |
|----------|------|
| `test_types.py` | `YuiValue` / 型クラスの単体テスト |
| `test_runtime.py` | `Runtime.exec()` を通じた実行テスト |
| `test_parser_yui.py` | yui 構文のパーステスト |

---

## CLI オプション

```bash
python3 -m yuichan.main <file.yui>           # ファイル実行
python3 -m yuichan.main --interactive        # REPL
python3 -m yuichan.main --pass@1 --syntax yui humaneval/*.yui  # ベンチマーク
python3 -m yuichan.main --syntax yui         # 構文指定
```

---

## バージョン履歴メモ

- v0.5.0: リリース済み（PyPI）
- 直近の変更: `ConstNode`（旧 `NullNode`）, `YuiBooleanType`, `YuiValue.TrueValue/FalseValue`, stdlib の YuiValue 返却修正, 配列等値比較実装
