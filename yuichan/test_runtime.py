"""
YuiRuntime.exec() を通じた実行テスト

すべてのコード実行は Runtime.exec() を通るため、ここでは exec() の
インターフェースを使ったテストを書く。
"""

import pytest
from .yuiruntime import YuiRuntime
from .yuitypes import YuiValue, YuiType, YuiError


# ─────────────────────────────────────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────────────────────────────────────

# 標準ライブラリを使う宣言 (yui 構文の import-standard キーワード)
STDLIB = "標準ライブラリを使う\n"


def run(source: str, syntax: str = 'yui') -> dict:
    """source を exec() で実行し、最終環境 dict を返す"""
    rt = YuiRuntime()
    rt.exec(source, syntax, eval_mode=False)
    return rt.environments[-1]


def run_std(source: str, syntax: str = 'yui') -> dict:
    """標準ライブラリ込みで source を exec() で実行し、最終環境 dict を返す"""
    return run(STDLIB + source, syntax)


def val(env: dict, name: str):
    """環境から変数の Python native 値を取得する"""
    return YuiType.to_native(env[name])


def run_rt(source: str, syntax: str = 'yui') -> YuiRuntime:
    """標準ライブラリ込みで source を exec() で実行し、Runtime ごと返す"""
    rt = YuiRuntime()
    rt.exec(STDLIB + source, syntax, eval_mode=False)
    return rt


# ─────────────────────────────────────────────────────────────────────────────
# NativeFunction の戻り値ラップ (回帰テスト)
# ─────────────────────────────────────────────────────────────────────────────

class TestNativeFunctionWrapping:
    """
    NativeFunction.call() が plain Python 値を YuiValue でラップすることの確認。

    修正前: 和() / 積() などの整数パスが plain int を返すため、
            変数に代入後に .type 参照で AttributeError が発生し、
            アサートが ❌10 ✅10 のように偽陰性になっていた。
    修正後: NativeFunction.call() で isinstance チェックして YuiValue に統一。
    """

    def test_sum_stores_yuivalue(self):
        """和() の結果が環境に YuiValue として格納される"""
        env = run_std("x = 和(3, 4)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 7

    def test_product_stores_yuivalue(self):
        """積() の結果が環境に YuiValue として格納される"""
        env = run_std("x = 積(3, 4)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 12

    def test_diff_stores_yuivalue(self):
        env = run_std("x = 差(10, 3)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 7

    def test_quotient_stores_yuivalue(self):
        env = run_std("x = 商(10, 3)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 3

    def test_remainder_stores_yuivalue(self):
        env = run_std("x = 剰余(10, 3)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 1

    def test_max_stores_yuivalue(self):
        env = run_std("x = 最大値(3, 7, 2)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 7

    def test_min_stores_yuivalue(self):
        env = run_std("x = 最小値(3, 7, 2)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 2

    def test_and_stores_yuivalue(self):
        env = run_std("x = 論理積(12, 10)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == (12 & 10)

    def test_or_stores_yuivalue(self):
        env = run_std("x = 論理和(12, 10)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == (12 | 10)

    def test_isint_stores_yuivalue(self):
        env = run_std("x = 整数判定(42)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 1

    def test_toint_stores_yuivalue(self):
        env = run_std("x = 整数化(3.9)")
        assert isinstance(env['x'], YuiValue)
        assert val(env, 'x') == 3

    def test_sqrt_stores_yuivalue(self):
        env = run_std("x = 平方根(4)")
        assert isinstance(env['x'], YuiValue)
        assert YuiType.is_float(env['x'])
        assert abs(val(env, 'x') - 2.0) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# アサート (>>>) が NativeFunction の戻り値で正しく動作すること (回帰テスト)
# ─────────────────────────────────────────────────────────────────────────────

class TestAssertWithNativeFunctions:
    """
    NativeFunction の結果をアサートできること。

    修正前: tested が plain int のため tested.type で AttributeError →
            except Exception で握りつぶし → ❌10 ✅10 という偽陰性エラー。
    """

    def test_sum_assert_passes(self):
        """和() の結果を直接アサートできること"""
        rt = run_rt(">>> 和(3, 4)\n7")
        assert rt.test_passed  # 失敗なら exec() が YuiError を送出する

    def test_product_assert_passes(self):
        rt = run_rt(">>> 積(3, 4)\n12")
        assert rt.test_passed

    def test_sum_via_variable_assert_passes(self):
        """Native 関数の結果を変数に代入してからアサートできること (バグの主な再現ケース)"""
        code = "x = 和(3, 4)\n>>> x\n7"
        rt = run_rt(code)
        assert rt.test_passed

    def test_chained_native_assert_passes(self):
        """Native 関数をネストした呼び出し結果をアサートできること"""
        # 積(result, 10) のような内部でネイティブ関数を使うケース
        code = "x = 和(積(2, 5), 3)\n>>> x\n13"
        rt = run_rt(code)
        assert rt.test_passed

    def test_user_function_using_native_assert(self):
        """
        Native 関数を内部で使うユーザ定義関数のアサート。
        closest_integer の失敗パターンの再現。
        """
        code = (
            "ten_times = 入力 n に対して {\n"
            "  積(n, 10) が答え\n"
            "}\n"
            ">>> ten_times(5)\n"
            "50\n"
        )
        rt = run_rt(code)
        assert rt.test_passed

    def test_user_function_chained_native_assert(self):
        """ループ内でネイティブ関数を重ねて使うユーザ定義関数のアサート"""
        code = (
            "accumulate = 入力 n に対して {\n"
            "  result = 0\n"
            "  n回くり返す {\n"
            "    result = 和(result, 1)\n"
            "  }\n"
            "  result が答え\n"
            "}\n"
            ">>> accumulate(5)\n"
            "5\n"
        )
        rt = run_rt(code)
        assert rt.test_passed

    def test_assert_failure_raises_yuierror(self):
        """アサート失敗時に YuiError が送出されること"""
        with pytest.raises(YuiError):
            run_rt(">>> 和(3, 4)\n99")


# ─────────────────────────────────────────────────────────────────────────────
# 基本実行
# ─────────────────────────────────────────────────────────────────────────────

class TestBasicExec:
    def test_assignment(self):
        assert val(run("x = 42"), 'x') == 42

    def test_string_assignment(self):
        assert val(run('s = "hello"'), 's') == "hello"

    def test_increment(self):
        assert val(run("x = 0\nxを増やす"), 'x') == 1

    def test_decrement(self):
        assert val(run("x = 5\nxを減らす"), 'x') == 4

    def test_arithmetic_add(self):
        # BinaryNode (+) は未実装のため、標準ライブラリの 和() を使う
        assert val(run_std("x = 和(3, 4)"), 'x') == 7

    def test_arithmetic_mul(self):
        # BinaryNode (*) は未実装のため、標準ライブラリの 積() を使う
        assert val(run_std("x = 積(3, 4)"), 'x') == 12

    def test_repeat(self):
        assert val(run("x = 0\n3回くり返す {\n  xを増やす\n}"), 'x') == 3

    def test_if_true(self):
        env = run("x = 10\nもし x が 10 ならば {\n  x = 99\n}")
        assert val(env, 'x') == 99

    def test_if_false(self):
        env = run("x = 5\nもし x が 10 ならば {\n  x = 99\n}")
        assert val(env, 'x') == 5

    def test_user_function(self):
        # BinaryNode (+) は未実装のため、標準ライブラリの 和() を使う
        code = (
            STDLIB +
            "add = 入力 a, b に対して {\n"
            "  和(a, b) が答え\n"
            "}\n"
            "result = add(3, 4)"
        )
        assert val(run(code), 'result') == 7

    def test_array_literal(self):
        env = run("a = [1, 2, 3]")
        assert val(env, 'a') == [1, 2, 3]

    def test_array_append(self):
        env = run("a = [1, 2]\naに3を追加する")
        assert val(env, 'a') == [1, 2, 3]

    def test_multiple_exec_shares_env(self):
        """同じ runtime で exec() を2回呼んでも環境が引き継がれること"""
        rt = YuiRuntime()
        rt.exec("x = 10", 'yui', eval_mode=False)
        # BinaryNode (+) は未実装のため、インクリメントで +5 を表現
        rt.exec("y = x\nyを増やす\nyを増やす\nyを増やす\nyを増やす\nyを増やす", 'yui', eval_mode=False)
        assert YuiType.to_native(rt.environments[-1]['y']) == 15

    def test_syntax_error_raises_yuierror(self):
        with pytest.raises(YuiError):
            run("もし もし もし")


# ─────────────────────────────────────────────────────────────────────────────
# 二項演算子 (allow_binary_ops=True)
# ─────────────────────────────────────────────────────────────────────────────

class TestBinaryOps:
    """BinaryNode の評価テスト"""

    def run_bin(self, source: str) -> dict:
        rt = YuiRuntime()
        rt.allow_binary_ops = True
        rt.exec(source, 'yui', eval_mode=False)
        return rt.environments[-1]

    # ── 無効時のエラー ────────────────────────────────────────
    def test_disabled_by_default(self):
        with pytest.raises(YuiError):
            run("x = 1 + 2")

    # ── 整数算術 ──────────────────────────────────────────────
    def test_add_ints(self):
        assert val(self.run_bin("x = 1 + 2"), 'x') == 3

    def test_subtract_ints(self):
        assert val(self.run_bin("x = 10 - 3"), 'x') == 7

    def test_multiply_ints(self):
        assert val(self.run_bin("x = 3 * 4"), 'x') == 12

    def test_divide_int_floor(self):
        assert val(self.run_bin("x = 10 / 3"), 'x') == 3

    def test_modulo_ints(self):
        assert val(self.run_bin("x = 10 % 3"), 'x') == 1

    # ── 少数算術 ──────────────────────────────────────────────
    def test_add_floats(self):
        assert abs(val(self.run_bin("x = 1.5 + 2.5"), 'x') - 4.0) < 1e-6

    def test_divide_float(self):
        assert abs(val(self.run_bin("x = 10.0 / 4"), 'x') - 2.5) < 1e-6

    def test_modulo_float(self):
        assert abs(val(self.run_bin("x = 5.5 % 2.0"), 'x') - 1.5) < 1e-6

    # ── 型昇格: 整数 OP 少数 → 少数 ──────────────────────────
    def test_int_plus_float_is_float(self):
        env = self.run_bin("x = 1 + 2.0")
        assert YuiType.is_float(env['x'])
        assert abs(val(env, 'x') - 3.0) < 1e-6

    def test_int_minus_float_is_float(self):
        env = self.run_bin("x = 5 - 1.5")
        assert YuiType.is_float(env['x'])
        assert abs(val(env, 'x') - 3.5) < 1e-6

    def test_int_multiply_float_is_float(self):
        env = self.run_bin("x = 3 * 2.0")
        assert YuiType.is_float(env['x'])
        assert abs(val(env, 'x') - 6.0) < 1e-6

    def test_int_divide_float_is_float(self):
        env = self.run_bin("x = 7 / 2.0")
        assert YuiType.is_float(env['x'])
        assert abs(val(env, 'x') - 3.5) < 1e-6

    # ── 文字列連結 ────────────────────────────────────────────
    def test_string_concat(self):
        assert val(self.run_bin('x = "hello" + " world"'), 'x') == "hello world"

    def test_string_concat_empty(self):
        assert val(self.run_bin('x = "" + "abc"'), 'x') == "abc"

    # ── 配列連結 ──────────────────────────────────────────────
    def test_array_concat(self):
        assert val(self.run_bin("x = [1, 2] + [3, 4]"), 'x') == [1, 2, 3, 4]

    def test_array_concat_empty(self):
        assert val(self.run_bin("x = [] + [1, 2]"), 'x') == [1, 2]

    # ── ゼロ除算 ──────────────────────────────────────────────
    def test_divide_by_zero(self):
        with pytest.raises(YuiError):
            self.run_bin("x = 5 / 0")

    def test_modulo_by_zero(self):
        with pytest.raises(YuiError):
            self.run_bin("x = 5 % 0")


class TestBinaryOpsUnlock:
    """関数定義 + アサート通過でアンロックされることのテスト"""

    FUNC_AND_ASSERT = (
        STDLIB +
        "double = 入力 n に対して {\n"
        "  積(n, 2) が答え\n"
        "}\n"
        ">>> double(3)\n"
        "6\n"
    )

    def run_unlocked(self, extra: str) -> dict:
        rt = YuiRuntime()
        rt.exec(self.FUNC_AND_ASSERT, 'yui', eval_mode=False)
        rt.exec(extra, 'yui', eval_mode=False)
        return rt.environments[-1]

    # ── アンロック条件 ────────────────────────────────────────
    def test_function_defined_flag(self):
        """visitFuncDefNode が function_defined を True にする"""
        rt = YuiRuntime()
        rt.exec("f = 入力 n に対して { nが答え }", 'yui', eval_mode=False)
        assert rt.function_defined is True

    def test_function_defined_false_initially(self):
        """初期状態は False"""
        rt = YuiRuntime()
        assert rt.function_defined is False

    def test_locked_without_assert(self):
        """関数定義のみ（アサートなし）ではロックのまま"""
        rt = YuiRuntime()
        rt.exec("f = 入力 n に対して { nが答え }", 'yui', eval_mode=False)
        with pytest.raises(YuiError):
            rt.exec("x = 1 + 2", 'yui', eval_mode=False)

    def test_locked_without_function(self):
        """アサート通過のみ（関数定義なし）ではロックのまま"""
        rt = YuiRuntime()
        rt.exec(STDLIB + ">>> 和(1, 2)\n3", 'yui', eval_mode=False)
        with pytest.raises(YuiError):
            rt.exec("x = 1 + 2", 'yui', eval_mode=False)

    def test_unlocked_after_func_and_assert(self):
        """関数定義 + アサート通過後は二項演算子が使える"""
        env = self.run_unlocked("x = 1 + 2")
        assert val(env, 'x') == 3

    def test_unlocked_add(self):
        assert val(self.run_unlocked("x = 10 + 5"), 'x') == 15

    def test_unlocked_subtract(self):
        assert val(self.run_unlocked("x = 10 - 3"), 'x') == 7

    def test_unlocked_multiply(self):
        assert val(self.run_unlocked("x = 3 * 4"), 'x') == 12

    def test_unlocked_divide(self):
        assert val(self.run_unlocked("x = 10 / 4"), 'x') == 2

    def test_unlocked_modulo(self):
        assert val(self.run_unlocked("x = 10 % 3"), 'x') == 1
