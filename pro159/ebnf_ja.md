# Yui 言語 構文定義（拡張 BNF）

本書は Yui 言語（`yui` 構文方言）の文法を拡張 BNF で定義する。

## 記法

- `A = B` — 生成規則
- `A | B` — 選択
- `[ A ]` — 0 回または 1 回（省略可）
- `{ A }` — 0 回以上の繰り返し
- `"..."` — 終端記号（リテラル文字列）
- `/.../` — 正規表現による終端
- 字句要素間には空白（半角/全角スペース、タブ）を挟める。文は改行 `LF` で区切る。

---

## 1. プログラム

```
program         = { statement } ;
statement       = ( import_stmt
                  | assert_stmt
                  | assignment
                  | increment
                  | decrement
                  | append
                  | if_stmt
                  | repeat_stmt
                  | funcdef
                  | return_stmt
                  | break_stmt
                  | pass_stmt
                  | expr_stmt ) , LF ;
LF              = /\n/ ;
```

---

## 2. 字句

```
whitespace      = /[ \t\r　]/ ;
line_comment    = ( "#" | "＃" ) , { /[^\n]/ } ;

identifier      = simple_name | extra_name ;
simple_name     = /[A-Za-z_][A-Za-z0-9_]*/ ;
extra_name      = "「" , { /[^」]/ } , "」" ;

integer         = /[0-9]+/ ;
float           = /[0-9]+/ , "." , /[0-9]+/ ;
number          = float | integer ;

string          = '"' , { string_part } , '"' ;
string_part     = string_char | string_escape | string_interp ;
string_char     = /[^"\\{]/ ;
string_escape   = "\\" , /./ ;
string_interp   = "{" , expression , "}" ;
```

---

## 3. 型リテラル

```
literal         = null_lit
                | bool_lit
                | number
                | string
                | array_lit
                | object_lit ;

null_lit        = "値なし" ;
bool_lit        = "真" | "偽" ;

array_lit       = "[" , [ expression , { array_sep , expression } ] , "]" ;
array_sep       = "," | "、" | "，" ;

object_lit      = "{" , [ key_value , { obj_sep , key_value } ] , "}" ;
obj_sep         = "," | "、" | "，" ;
key_value       = string , ":" , expression ;
```

---

## 4. 式

演算子の優先順位は高い順に: 一次式 → インデックス/プロパティ/関数呼び出し（後置）→ 単項 `-` → 長さ演算 → 基底。

```
expression      = length_expr | unary_expr ;

length_expr     = postfix_expr , "の大きさ" ;

unary_expr      = [ "-" ] , postfix_expr ;

postfix_expr    = primary_expr , { postfix_op } ;
postfix_op      = index_suffix
                | call_suffix ;

index_suffix    = "[" , expression , "]" ;
call_suffix     = "(" , [ expression , { "," , expression } ] , ")" ;

primary_expr    = literal
                | identifier ;
```

注:
- `yui` 方言では `+ - * / % == != < <= > >=` の**中置演算子は無効**。算術・比較は標準ライブラリ関数（`和/差/積/商/剰余` 等）および `もし ... ならば` の接尾辞で表現する。
- 関数呼び出し・インデックスは任意に連結できる（例: `f(x)[0]`, `O["a"][1]`）。

---

## 5. 代入・増減・追加

```
assignment      = assign_target , "=" , expression ;
assign_target   = identifier , { index_suffix } ;

increment       = assign_target , "を増やす" ;
decrement       = assign_target , "を減らす" ;

append          = append_form1 | append_form2 ;
append_form1    = assign_target , [ "の末尾" ] , "に" , expression , "を追加する" ;
append_form2    = assign_target , "を" , assign_target , "に追加する" ;
```

---

## 6. 条件分岐

```
if_stmt         = "もし" , condition , "ならば" , block ,
                  [ "そうでなければ" , block ] ;

condition       = expression , "が" , expression , [ cmp_suffix ] ;

cmp_suffix      = "以外"
                | "より小さい"
                | "より大きい"
                | "以下"
                | "以上"
                | "のいずれか"
                | "のいずれでもない" ;
```

`cmp_suffix` なしは等値比較（`==`）を意味する。

---

## 7. 繰り返し

```
repeat_stmt     = expression , "回" , "くり返す" , block ;
break_stmt      = "くり返しを抜ける" ;
```

---

## 8. 関数定義と戻り値

```
funcdef         = identifier , "=" , func_literal ;
func_literal    = funcdef_args , "に対し" , block ;

funcdef_args    = "入力" , param_list
                | "入力なし" ;
param_list      = identifier , { "," , identifier } ;

return_stmt     = return_value | return_none ;
return_value    = expression , "が" , "答え" ;
return_none     = "関数から抜ける" ;
```

本体が戻り値文なしに終わった場合、関数内ローカル変数をまとめたオブジェクトが暗黙に返る。

---

## 9. インポート

```
import_stmt     = import_standard | import_named ;
import_standard = "標準ライブラリを使う" ;
import_named    = identifier , "を使う" ;
```

---

## 10. アサート（doctest）

```
assert_stmt     = ">>>" , expression , LF , expected_value ;
expected_value  = literal ;
```

`>>>` に続く式の評価結果が、次行のリテラルと等しくなることを検証する。

---

## 11. 式文・その他

```
expr_stmt       = expression ;
pass_stmt       = "何もしない" ;
```

単独の式文は評価結果が自動的に印字される。

---

## 12. ブロック

```
block           = "{" , { statement } , "}" ;
```

`{ ... }` 内は複数の文を含み、条件分岐・繰り返し・関数定義の本体となる。
