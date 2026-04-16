# Yui 言語 意味論（セミフォーマル版・擬似コード評価器）

本書は Yui 言語の実行時意味を **擬似コード評価器** の形で記述する読み物版。
厳密な推論規則版は [`semantics_ja.md`](semantics_ja.md)、構文は
[`ebnf_ja.md`](ebnf_ja.md) を参照。

読者対象は「実装を読む前に全体像を掴みたい」層。本書は推論規則を使わず、
Python 風の擬似コードと日本語で意味を説明する。

---

## 1. 実行モデルの全体像

Yui プログラムは次の 3 つの状態を持って動く:

| 構成要素 | 型 | 役割 |
|----------|-----|------|
| 環境 `ρ` | `Name → Value` | 変数名から値への写像 |
| ヒープ `H` | `Addr → Array/Object/Closure` | 参照型の実体 |
| 制御 `K` | `Normal | Ret v | Brk` | 関数 return と break の脱出 |

式を評価すると値が返り、文を実行すると環境・ヒープが更新される。
`return` 相当 (`…が答え`) と `break` (`くり返しを抜ける`) は例外風の
制御値で表現する。

---

## 2. 値の世界

```
Value = null
      | Bool   (真 / 偽)
      | Int
      | Float
      | String     -- 内部的には文字コード列
      | Addr       -- 配列/オブジェクト/関数への参照
```

### 値型と参照型

- **値型**: null, Bool, Int, Float, String は「そのもの」が値として渡る
- **参照型**: 配列・オブジェクト・関数は `Addr` として渡る。代入や引数
  渡しでコピーはされず、ヒープ上の同じ実体を共有する

### Int / Float の昇格

二項演算で片方が Float なら結果は Float。両方 Int なら Int を保つ
（`商` は床除算）。

### 文字列の等値と長さ

文字列は内部的には文字コード列 (`[72, 105]` = `"Hi"`) として扱われる。
このため:

- `"Hi"の大きさ` → `2`
- `[72, 105]` と `"Hi"` は等値（配列と文字列の横断比較が成立）

---

## 3. 擬似コード評価器

```python
def eval_expr(e, ρ, H) -> (Value, H):
    match e:
        case 値なし:         return null, H
        case 真:             return True, H
        case 偽:             return False, H
        case Int n:          return n, H
        case Float f:        return f, H
        case Str s:          return s, H

        case Name x:
            if x not in ρ: raise UndefinedVariable(x)
            return ρ[x], H

        case Array [e₁, …, eₖ]:
            vs = []
            for eᵢ in [e₁,…,eₖ]:
                vᵢ, H = eval_expr(eᵢ, ρ, H)
                vs.append(vᵢ)
            a = fresh_addr(); H[a] = vs
            return a, H

        case Object {s₁:e₁, …}:
            d = {}
            for (sᵢ, eᵢ) in pairs:
                vᵢ, H = eval_expr(eᵢ, ρ, H); d[sᵢ] = vᵢ
            o = fresh_addr(); H[o] = d
            return o, H

        case Index e[e']:
            v,  H = eval_expr(e,  ρ, H)
            v', H = eval_expr(e', ρ, H)
            return index_of(H, v, v'), H      # 配列/オブジェクト/文字列

        case Neg -e:
            v, H = eval_expr(e, ρ, H)
            return -v, H

        case Length (e の大きさ):
            v, H = eval_expr(e, ρ, H)
            return length_of(H, v), H         # 配列・文字列・オブジェクト

        case Call e(e₁, …, eₖ):
            f, H = eval_expr(e, ρ, H)
            args = []
            for eᵢ: vᵢ, H = eval_expr(eᵢ, ρ, H); args.append(vᵢ)
            return invoke(f, args, H)         # §4
```

### 文

```python
def eval_stmt(s, ρ, H) -> (Control, ρ', H'):
    match s:
        case Assign (x = e):
            v, H = eval_expr(e, ρ, H)
            return Normal, ρ[x ↦ v], H

        case IndexAssign (x[e₁]…[eₖ] = e):
            ...  # H を書き換え、ρ は不変

        case Inc (x を増やす):
            return Normal, ρ[x ↦ ρ[x] + 1], H
        case Dec (x を減らす):
            return Normal, ρ[x ↦ ρ[x] - 1], H

        case Append (x に e を追加する):
            v, H = eval_expr(e, ρ, H)
            a = ρ[x]; H[a] = H[a] + [v]
            return Normal, ρ, H

        case If (もし c ならば B₁ [そうでなければ B₂]):
            b, H = eval_cond(c, ρ, H)
            if b:     return eval_block(B₁, ρ, H)
            elif B₂:  return eval_block(B₂, ρ, H)
            else:     return Normal, ρ, H

        case Repeat (e 回くり返す B):
            n, H = eval_expr(e, ρ, H)
            for _ in range(n):
                k, ρ, H = eval_block(B, ρ, H)
                if k is Brk:   return Normal, ρ, H
                if k is Ret v: return Ret v, ρ, H
            return Normal, ρ, H

        case FunDef (x = 入力 x₁,…,xₖ に対し B):
            clo = Closure(params=[x₁…xₖ], body=B, env=ρ)
            a = fresh_addr(); H[a] = clo
            return Normal, ρ[x ↦ a], H

        case Return (e が 答え):
            v, H = eval_expr(e, ρ, H)
            return Ret v, ρ, H
        case ReturnNone (関数から抜ける):
            return Ret null, ρ, H
        case Break (くり返しを抜ける):
            return Brk, ρ, H

        case Pass (何もしない):
            return Normal, ρ, H

        case ImportStd (標準ライブラリを使う):
            return Normal, ρ ⊎ ρ_std, H

        case Assert (>>> e ⤶ lit):
            v, H = eval_expr(e, ρ, H)
            if v ≠ ⟦lit⟧: raise AssertionFailed
            return Normal, ρ, H

        case ExprStmt e:
            v, H = eval_expr(e, ρ, H)
            print_if_repl(v)
            return Normal, ρ, H
```

### ブロック

```python
def eval_block(B, ρ, H):
    for s in B:
        k, ρ, H = eval_stmt(s, ρ, H)
        if k is not Normal:   # Ret v / Brk をそのまま伝播
            return k, ρ, H
    return Normal, ρ, H
```

---

## 4. 関数呼び出しの意味

```python
def invoke(f, args, H):
    if f is NativeFunction:       # 和, 積, 剰余, …
        return f.impl(args), H

    clo = H[f]                     # Closure
    ρ' = clo.env[xᵢ ↦ argsᵢ for each param xᵢ]
    k, ρ'', H = eval_block(clo.body, ρ', H)

    if k is Ret v:                 # 明示的 return
        return v, H
    if k is Normal:                # 暗黙: ローカル変数をまとめたオブジェクト
        return locals_as_object(clo.env, ρ''), H
    if k is Brk:
        raise BreakOutsideLoop
```

暗黙の戻り値 `locals_as_object` は、関数本体で **新規に束縛された
ローカル変数のみ** をオブジェクトにまとめて返す（呼び出し前から
見えていたクロージャ捕捉変数は含めない）。

---

## 5. 条件式の意味

`もし <e₁> が <e₂> <接尾辞> ならば` は、`e₁`, `e₂` を評価した値 `v₁`, `v₂`
について次のように真偽を決める:

| 接尾辞           | 真となる条件 |
|------------------|--------------|
| (なし)           | `v₁ = v₂`              （等値） |
| `以外`           | `v₁ ≠ v₂`              |
| `より小さい`     | `v₁ < v₂`              |
| `より大きい`     | `v₁ > v₂`              |
| `以下`           | `v₁ ≤ v₂`              |
| `以上`           | `v₁ ≥ v₂`              |
| `のいずれか`     | `v₁ ∈ v₂`              （v₂ は配列/文字列） |
| `のいずれでもない` | `v₁ ∉ v₂`            |

等値の細則:

- 数値: 数学的等値（Int と Float は値で比較）
- 文字列: 文字コード列の要素ごと一致
- 配列: 要素ごと再帰比較
- 配列 vs 文字列: 文字コード列として一致すれば等値
- オブジェクト: 現状は参照等値（TODO）

---

## 6. 組み込み関数（抜粋）

標準ライブラリ関数は `標準ライブラリを使う` で `ρ` に追加される。
主要な算術関数:

| 名前 | 意味 |
|------|------|
| `和(x,y)` | `x + y`。Int×Int → Int、Float が絡めば Float |
| `差(x,y)` | `x - y` |
| `積(x,y)` | `x * y` |
| `商(x,y)` | Int×Int は床除算、Float が絡めば通常除算 |
| `剰余(n,m)` | `n - m * ⌊n/m⌋`（Int 専用） |
| `小数化(n)` | Int → Float 明示昇格 |
| `絶対値(x)` | `|x|` |

ゼロ除算はエラー。

---

## 7. ハマりどころとの対応

[`hamari_ja.md`](hamari_ja.md) の既知事項は意味論では次のように捉えられる:

- **`商(int, int)` が床除算**: §6 のとおり Int×Int の `商` は定義上 `⌊x/y⌋`。
  小数の答えが欲しいときは `小数化` で Float に昇格させる
- **`+ - * / %` が使えない**: これは構文の制約（`ebnf_ja.md` §4）。
  意味論レベルでは組み込み関数 `和`/`差`/… 経由でのみ算術が起こる
- **配列から pop できない**: §3 の Append は末尾伸張のみ。配列は参照型
  なので論理長を別管理する際の一貫性維持は呼び出し側の責任
- **文字列と配列の等値**: §5 の細則にあるとおり、文字コード列としての
  一致で等値が成立する

---

## 8. まだ書けていないこと

本書は読み物レベルの近似であり、以下は擬似コードでは省略している:

- 式評価中の副作用（関数呼び出し・インデックス代入）で `H` が変化する
  際の厳密な順序
- 文字列補間 `"…{e}…"` の脱糖
- doctest の浮動小数点許容誤差
- オブジェクト等値を構造等値に広げる可能性
- エラー意味論（どの未定義動作をどんなエラーに対応させるか）

厳密版は `semantics_ja.md` を参照。実装対応は `yuichan/yuiruntime.py`。
