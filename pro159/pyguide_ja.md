# Yui プログラミングガイド（Python ユーザ向け）

Yui は日本語で書ける教育用プログラミング言語です。
本ガイドでは、各機能を **まず Python で示し、同じ処理を Yui でどう書くか** を対比しながら紹介します。
Python にある概念・ない概念の両方を明確にすることで、Python 経験者がすばやく Yui を習得できるようにします。

---

## 1. はじめてのプログラム

Python の `print` に相当する「式を単独で書くとその値が表示される」動作が Yui にもあります。

**Python**

```python
print("Hello, world!")
```

**Yui**

```yui
# "Hello, world!" と表示する
"Hello, world!"
```

- Yui では、代入・制御文以外の**単独の式**は自動的に印字されます（REPL 的挙動）。
- 行頭から `#`（または `＃`）以降はコメントです。

---

## 2. 変数と増減

**Python**

```python
x = 1
y = -2
x += 1
y -= 1
assert x == 2
assert y == -3
```

**Yui**

```yui
x = 1
y = -2
xを増やす
yを減らす

>>> x
2
>>> y
-3
```

- Yui の `>>> 式` + 期待値は Python の **doctest と同じ記法**で、プログラム内にテストを埋め込めます。
- `xを増やす` は `x += 1` に、`yを減らす` は `y -= 1` に相当します。

---

## 3. 型とリテラル

Python と Yui の型の対応は以下のとおりです。

| Python | Yui | Yui リテラル |
|--------|-----|----------|
| `None` | ヌル | `値なし` |
| `bool` | 論理値 | `真` / `偽` |
| `int` | 整数 | `42` |
| `float` | 小数 | `3.14`（表示は小数点以下 6 桁固定） |
| `str` | 文字列 | `"あ"` |
| `list` | 配列 | `[1, 2, 3]` |
| `dict` | オブジェクト | `{"x": 1, "y": 2}` |

注意点:

- Yui の **文字列は内部的に文字コード（int）の配列**です。`list` と同じ操作（要素追加・長さ取得）が使えます。
- Yui の小数は表示上、常に 6 桁の小数点以下が付きます（`3.000000`）。

---

## 4. 文字列補間

**Python**（f-string）

```python
name = "ゆい"
age = 12
msg = f"こんにちは、{name}さん！あなたは{age}歳です。"
assert msg == "こんにちは、ゆいさん！あなたは12歳です。"
```

**Yui**

```yui
name = "ゆい"
age  = 12
msg  = "こんにちは、{name}さん！あなたは{age}歳です。"

>>> msg
"こんにちは、ゆいさん！あなたは12歳です。"
```

- Python の f-string の `f` プレフィックスは不要です。**通常の文字列に `{式}` を書けば展開されます**。
- `{` や `"` を文字として書きたいときは `\{` `\"`。`\\`, `\n`, `\t` も使えます。

---

## 5. 配列（リスト）

**Python**

```python
A = [1, 2, 3]
A.append(0)
A[0] += 1
if 2 in A:
    A[0] = A[3]
assert len(A) == 4
```

**Yui**

```yui
A = [1, 2, 3]
Aに0を追加する
A[0]を増やす
もし2がAのいずれかならば{
   A[0] = A[3]
}

>>> Aの大きさ
4
```

対応表:

| Python | Yui |
|--------|-----|
| `A.append(x)` | `Aにxを追加する` |
| `len(A)` | `Aの大きさ` |
| `A[i]` | `A[i]`（同じ） |
| `x in A` | `もしxがAのいずれかならば` |
| `x not in A` | `もしxがAのいずれでもないならば` |

### 5.1 インデックスと長さ

**Python**

```python
A = [10, 20, 30]
n = len(A)
first = A[0]
last = A[n - 1]
A[1] = 200
```

**Yui**

```yui
標準ライブラリを使う
A = [10, 20, 30]
n = Aの大きさ
first = A[0]
last  = A[差(n,1)]
A[1] = 200
```

- Yui には `-` の中置演算がないため、`n - 1` は `差(n, 1)` と書きます。

---

## 6. オブジェクト（辞書）

**Python**

```python
O = {"x": 0, "y": 0}
O["x"] = 1
O["y"] = 2
assert O["x"] == 1
```

**Yui**

```yui
O = {"x": 0, "y": 0}
O["x"] = 1
O["y"] = 2

>>> O["x"]
1
```

構文は Python の `dict` とほぼ同じです。キーは文字列を使います。

---

## 7. 文字列は配列

Python では `str` と `list` は別物ですが、Yui では文字列 = 文字コード配列です。

**Python**

```python
s = list("hello")
s[0] = "H"
for c in " world":
    s.append(c)
assert "".join(s) == "Hello world"
```

**Yui**

```yui
s = "hello"
s[0] = "H"[0]

t = " world"
i = 0
tの大きさ回くり返す{
   sにt[i]を追加する
   iを増やす
}

>>> s
"Hello world"
```

- `"H"[0]` は文字コードで、配列の要素と同じ型です。

---

## 8. 条件分岐

**Python**

```python
flag = True
if flag:
    result = 1
else:
    result = 2
```

**Yui**

```yui
flag   = 真
result = 0
もしflagが真ならば{
   result = 1
}
そうでなければ{
   result = 2
}
```

### 8.1 比較演算子 → 接尾辞

Yui は `==` `!=` `<` `>` などの**記号を使いません**。`もし A が B <接尾辞> ならば` と書きます。

| Python | Yui |
|--------|-----|
| `a == b` | `もしaがbならば` |
| `a != b` | `もしaがb以外ならば` |
| `a < b`  | `もしaがbより小さいならば` |
| `a > b`  | `もしaがbより大きいならば` |
| `a <= b` | `もしaがb以下ならば` |
| `a >= b` | `もしaがb以上ならば` |
| `a in xs` | `もしaがxsのいずれかならば` |
| `a not in xs` | `もしaがxsのいずれでもないならば` |

**Python**

```python
fruits = ["apple", "banana", "cherry"]
found = 1 if "banana" in fruits else 0
missing = 1 if "grape" not in fruits else 0
```

**Yui**

```yui
fruits = ["apple", "banana", "cherry"]
found   = 0
missing = 0
もし"banana"がfruitsのいずれかならば{ foundを増やす }
もし"grape"がfruitsのいずれでもないならば{ missingを増やす }
```

### 8.2 多段分岐

Yui には `elif` がありません。`そうでなければ { もし ... }` をネストします。

---

## 9. 繰り返し

Yui のループは **回数指定の `N回くり返す`** のみです。`while` や `for x in xs` はありません。

**Python**

```python
count = 0
for _ in range(10):
    count += 1
    if count == 5:
        break
assert count == 5
```

**Yui**

```yui
count = 0
10回くり返す{
   countを増やす
   もしcountが5ならば{
      くり返しを抜ける
   }
}

>>> count
5
```

| Python | Yui |
|--------|-----|
| `for _ in range(N):` | `N回くり返す{ ... }` |
| `break` | `くり返しを抜ける` |

配列を舐めたいときは、インデックス変数を自分で増やします（`7. 文字列は配列` の例を参照）。

---

## 10. 関数

### 10.1 定義と戻り値

**Python**

```python
def succ(n):
    n += 1
    return n

assert succ(0) == 1
```

**Yui**

```yui
succ = 入力nに対し{
   nを増やす
   nが答え
}

>>> succ(0)
1
```

| Python | Yui |
|--------|-----|
| `def f(a, b):` | `f = 入力 a, b に対し { ... }` |
| `def f():` | `f = 入力なしに対し { ... }` |
| `return x` | `xが答え` |
| `return`（値なし） | `関数から抜ける` |

関数内で作った変数は**ローカルスコープ**（Python と同じ）。

### 10.2 暗黙の戻り値（コンストラクタ風）

Python では `return` がないと `None` が返りますが、Yui では**ローカル変数をまとめたオブジェクトが返ります**。
Python の `dataclass` や簡易コンストラクタのように使えます。

**Python 擬似コード**

```python
def point(x, y):
    return {"x": x, "y": y}

O = point(3, 5)
assert O["x"] == 3
```

**Yui**

```yui
point = 入力x,yに対し{
   # 何も返さない → {"x": ..., "y": ...} が返る
}
O = point(3, 5)

>>> O["x"]
3
```

### 10.3 再帰

**Python**

```python
def fact(n):
    if n == 0:
        return 1
    return n * fact(n - 1)

assert fact(5) == 120
```

**Yui**

```yui
標準ライブラリを使う

fact = 入力nに対し{
   もしnが0ならば{
      1が答え
   }
   そうでなければ{
      積(n, fact(差(n,1)))が答え
   }
}

>>> fact(5)
120
```

Yui には `*` `-` の中置演算がないので、`積` `差` を使います。

---

## 11. 標準ライブラリ

Python は演算子や組み込み関数が豊富ですが、Yui は**記号を使わず、関数で演算する**のが特徴です。
ソース先頭で `標準ライブラリを使う` と宣言してから関数を呼びます。

### 11.1 四則演算

| Python | Yui |
|--------|-----|
| `a + b + c` | `和(a, b, c)`（配列も可: `和([a,b,c])`） |
| `a - b` | `差(a, b)` |
| `a * b` | `積(a, b)` |
| `a // b` | `商(a, b)`（int/int は床除算） |
| `a % b` | `剰余(a, b)` |

**Python**

```python
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

assert gcd(12, 18) == 6
```

**Yui**

```yui
標準ライブラリを使う

gcd = 入力a,bに対し{
   a回くり返す{
      もしbが0ならば{
         くり返しを抜ける
      }
      r = 剰余(a, b)
      a = b
      b = r
   }
   aが答え
}

>>> gcd(12, 18)
6
```

Yui には `while` がないので、**十分大きい回数のループ + break** で `while` を模倣します。

### 11.2 数学関数

| Python | Yui |
|--------|-----|
| `abs(x)` | `絶対値(x)` |
| `math.sqrt(x)` | `平方根(x)` |
| `max(a, b, ...)` / `max(xs)` | `最大値(a, b, ...)` / `最大値(xs)` |
| `min(a, b, ...)` / `min(xs)` | `最小値(a, b, ...)` / `最小値(xs)` |
| `random.random()` | `乱数()` |

**Python**

```python
assert abs(-7) == 7
assert max(3, 1, 4, 1, 5) == 5
```

**Yui**

```yui
標準ライブラリを使う

>>> 絶対値(-7)
7
>>> 平方根(9)
3.000000
>>> 最大値(3, 1, 4, 1, 5)
5
>>> 最小値([10, 20, 30])
10
```

### 11.3 型変換

| Python | Yui |
|--------|-----|
| `int(x)` | `整数化(x)` |
| `float(x)` | `小数化(x)` |
| `str(x)` | `文字列化(x)` |
| `list(s)`（文字列→文字コード列） | `配列化(x)` |

**Python**

```python
assert int("42") == 42
assert int(3.7) == 3
assert str(42) == "42"
assert list("Hi".encode()) == [72, 105]
```

**Yui**

```yui
標準ライブラリを使う

>>> 整数化("42")
42
>>> 整数化(3.700000)
3
>>> 文字列化(42)
"42"
>>> 配列化("Hi")
[72,105]
```

### 11.4 型判定

| Python | Yui |
|--------|-----|
| `isinstance(x, bool)` | `ブール判定(x)` |
| `isinstance(x, int)` | `整数判定(x)` |
| `isinstance(x, float)` | `小数判定(x)` |
| `isinstance(x, str)` | `文字列判定(x)` |
| `isinstance(x, list)` | `配列判定(x)` |
| `isinstance(x, dict)` | `オブジェクト判定(x)` |

```yui
標準ライブラリを使う

>>> 整数判定(42)
真
>>> 文字列判定("hello")
真
>>> 整数判定("42")
偽
```

---

## 12. 総合例: FizzBuzz

**Python**

```python
result = []
for i in range(1, 101):
    if i % 15 == 0:
        result.append("FizzBuzz")
    elif i % 3 == 0:
        result.append("Fizz")
    elif i % 5 == 0:
        result.append("Buzz")
    else:
        result.append(i)
assert len(result) == 100
```

**Yui**

剰余を使わずにカウンタで Fizz/Buzz を判定できます。

```yui
result = []
i    = 0
fizz = 0
buzz = 0

100回くり返す{
   iを増やす
   fizzを増やす
   buzzを増やす
   もしfizzが3ならば{ fizz = 0 }
   もしbuzzが5ならば{ buzz = 0 }

   もしfizzが0ならば{
      もしbuzzが0ならば{
         resultに"FizzBuzz"を追加する
      }そうでなければ{
         resultに"Fizz"を追加する
      }
   }そうでなければ{
      もしbuzzが0ならば{
         resultに"Buzz"を追加する
      }そうでなければ{
         resultにiを追加する
      }
   }
}

>>> resultの大きさ
100
>>> result[2]
"Fizz"
>>> result[4]
"Buzz"
>>> result[14]
"FizzBuzz"
```

---

## 13. 総合例: モンテカルロ法で π を推定

**Python**

```python
import random, math

def monte_carlo(n):
    hits = 0
    for _ in range(n):
        x, y = random.random(), random.random()
        if math.sqrt(x*x + y*y) <= 1:
            hits += 1
    return 4 * hits / n

monte_carlo(1000)
```

**Yui**

```yui
標準ライブラリを使う

monte_carlo = 入力nに対し{
   hits = 0
   n回くり返す{
      x = 乱数()
      y = 乱数()
      dist = 平方根(和(積(x,x), 積(y,y)))
      もしdistが1以下ならば{
         hitsを増やす
      }
   }
   商(積(小数化(hits), 4), 小数化(n))が答え
}

monte_carlo(1000)
```

---

## 14. Python にあって Yui にないもの（要注意）

Python 経験者がつまずきやすいポイントです。

- **中置演算子が無い**: `+ - * / % == != < <= > >=` すべて使えません。算術は `和/差/積/商/剰余`、比較は `が〜ならば` 構文で書きます。
- **`while` / `for x in xs` が無い**: `N回くり返す { ... くり返しを抜ける }` のみ。
- **`elif` が無い**: `そうでなければ { もし ... }` をネストして書く。
- **`return` で値なしは別構文**: `関数から抜ける` を使います。
- **ローカルだけの関数本体**: `return` を書かないと `None` でなく**ローカル変数のオブジェクト**が返る（Python にない挙動）。
- **演算子モジュール・クラス・例外は無い**: Yui は教育用の最小構文のみ。

---

## 15. まとめ

Python と比較した Yui の特徴は次のとおりです。

- **記号を減らし、日本語の語順で書く**。
- 比較は `が〜ならば`、四則演算は `和/差/積/商/剰余`。
- 文字列は文字コード配列で、`list` と統一的に扱える。
- 関数は `入力...に対し{ ...が答え }`、戻り値なしはローカル変数を辞書化して返す。
- `>>> 式` と期待値を書くと doctest 互換のテストをプログラム内に残せる。

より詳しい仕様は `pro159/spec_ja.md`、構文の形式定義は `pro159/ebnf_ja.md`、実例は `yui_examples/` を参照してください。
