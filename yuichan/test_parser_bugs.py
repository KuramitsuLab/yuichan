"""
パーサ／実行時の既知バグの回帰テスト

pro159/hamari_ja.md で記録された 4 件のうち、再調査で実態が判明した 3 件:

  Bug 1: もし <関数呼び出し> が ... ならば   が "expected-expression" でパース失敗
  Bug 6: doctest (>>> 式 / 期待値) の直後のコメントに <数字><空白>(...) があると、
         次の式の `数字(...)` を関数呼び出しとして解釈してしまう
  Bug 9: 1 行形式 もし...ならば{ xを増やす } がパース失敗 (xを減らす は通る — 非対称!)

(hamari_ja.md の Bug 8 は再調査の結果、独立したバグではなく、Bug 9 が
 もし aがbならば{ eqを増やす } の場面で先に出ていただけと判明した)

すべて xfail でマークしてある。バグが修正されたら xfail を外す。
"""

from .yuiruntime import YuiRuntime
from .yuitypes import YuiError, types

STDLIB = "標準ライブラリを使う\n"


def run(source: str, with_stdlib: bool = True) -> dict:
    """source を exec() で実行し、最終環境 dict を返す"""
    rt = YuiRuntime()
    code = (STDLIB if with_stdlib else "") + source
    rt.exec(code, syntax='yui', eval_mode=False)
    return rt.environments[-1]


def val(env: dict, name: str):
    """環境から変数の Python native 値を取得する"""
    return types.unbox(env[name])


# ─────────────────────────────────────────────────────────────────────────────
# Bug 1: もし <関数呼び出し> が ... ならば がパース失敗する
# ─────────────────────────────────────────────────────────────────────────────

class TestBug1_FuncCallInIfLeft:
    """
    もし の左辺に関数呼び出しを直接書くとパースに失敗する。
    関数呼び出しの結果を一旦変数に束ねれば動く。
    """

    def test_workaround_via_temp_variable(self):
        """回避策: 関数呼び出しの結果を変数に束ねてから比較すれば動く"""
        src = """
j=4
parity=剰余(j,2)
result=0
もしparityが0ならば{
   result=1
}
"""
        env = run(src)
        assert val(env, 'result') == 1

    def test_func_call_directly_in_if_condition(self):
        """もし <関数呼び出し> が <値> ならば も動くべき"""
        src = """
j=4
result=0
もし剰余(j,2)が0ならば{
   result=1
}
"""
        env = run(src)
        assert val(env, 'result') == 1

    def test_func_call_on_right_side_of_if(self):
        """もし <変数> が <関数呼び出し> ならば も動くべき (右辺に関数呼び出し)"""
        src = """
pos=5
result=0
もしposが差(0,1)ならば{
   result=1
}
"""
        env = run(src)
        # 5 != -1 → result は 0 のまま (パース・実行できることが本質)
        assert val(env, 'result') == 0


# ─────────────────────────────────────────────────────────────────────────────
# Bug 6: doctest 直後のコメント中の `<数字> (...)` が関数呼び出しに化ける
# ─────────────────────────────────────────────────────────────────────────────

class TestBug6_DoctestCommentNumberParen:
    """
    >>> 式 / 期待値 の直後のコメントに `<1 桁数字> <空白> (...)` パターンがあると、
    `数字(...)` が関数呼び出しとして解釈され、`undefined-variable` で失敗する。

    観測:
      # X (端数切り捨て)        → OK
      # X 3 (端数切り捨て)      → FAIL    ← `3 (...)` が引っかかる
      # 3 (foo)                 → FAIL
      # 13 を 2 (端数切り捨て)  → OK      ← 多桁数字直後の (...) は OK
      # 13 を 2 X (端数切り捨て) → OK     ← `2 X` で間に文字が入れば OK

    つまり、コメント終端付近の **1 桁数字 + 空白 + ( ...** が
    関数呼び出しのパース対象になってしまっている。
    """

    def test_workaround_no_number_paren(self):
        """回避策: コメント末尾に <数字>(...) を書かなければ通る"""
        src = """
f=入力xに対し{
   xが答え
}
>>> f(3)
3
# 端数は切り捨てられる
>>> f(3)
3
"""
        run(src)  # 例外なく完走すれば OK

    def test_workaround_multidigit_ok(self):
        """対照: 多桁数字 + (...) は通る"""
        src = """
f=入力xに対し{
   xが答え
}
>>> f(3)
3
# 13 (端数切り捨て)
>>> f(3)
3
"""
        run(src)

    def test_single_digit_paren_in_comment(self):
        """コメント `# 3 (foo)` だけでも引っかかる"""
        src = """
f=入力xに対し{
   xが答え
}
>>> f(3)
3
# 3 (foo)
>>> f(3)
3
"""
        run(src)

    def test_original_bitshift_comment(self):
        """ハマりどころ #6 を最初に踏んだ実例"""
        src = """
f=入力xに対し{
   xが答え
}
>>> f(3)
3
# テスト: 13 を 2 ビット右シフトすると 3 (端数切り捨て)
>>> f(3)
3
"""
        run(src)


# ─────────────────────────────────────────────────────────────────────────────
# Bug 9: 1 行 もし...ならば{ xを増やす } がパース失敗 (減らす は通る、非対称)
# ─────────────────────────────────────────────────────────────────────────────

class TestBug9_IncrementInOneLineIf:
    """
    1 行形式 もし...ならば{ ... } の本体に xを増やす を書くとパース失敗する。
    対称的なはずの xを減らす は同じ位置で動く ─ 増やす だけが壊れている。
    複数行に展開すれば 増やす も動く。
    """

    def test_workaround_multiline_increment(self):
        """回避策: xを増やす を複数行に展開すれば動く"""
        src = """
x=0
もし1が1ならば{
   xを増やす
}
"""
        env = run(src)
        assert val(env, 'x') == 1

    def test_one_line_assignment_works(self):
        """対照: 1 行形式に代入文を入れるのは通る"""
        src = """
x=0
もし1が1ならば{ x=5 }
"""
        env = run(src)
        assert val(env, 'x') == 5

    def test_one_line_decrement_works(self):
        """対照: 1 行形式に xを減らす は (なぜか) 通る — 増やす との非対称"""
        src = """
x=5
もし1が1ならば{ xを減らす }
"""
        env = run(src)
        assert val(env, 'x') == 4

    def test_one_line_increment_fails(self):
        """1 行形式に xを増やす を入れると `expected-expression` で失敗する"""
        src = """
x=0
もし1が1ならば{ xを増やす }
"""
        env = run(src)
        assert val(env, 'x') == 1

    def test_one_line_increment_with_var_compare(self):
        """もし aがbならば{ eqを増やす } も同じ理由で失敗 (triangle.yui で踏んだ実例)"""
        src = """
a=5
b=5
eq=0
もしaがbならば{ eqを増やす }
"""
        env = run(src)
        assert val(env, 'eq') == 1
