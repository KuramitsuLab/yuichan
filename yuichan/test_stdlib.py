import pytest
from .yuitypes import YuiValue, YuiType, YuiError
from .yuistdlib import standard_lib


@pytest.fixture(scope="module")
def stdlib():
    """標準ライブラリ関数を英語名 → 関数の dict として返す"""
    modules = []
    standard_lib(modules)
    return {name.split('|')[-1]: func for name, func in modules}


def v(x):
    """Python値 → YuiValue"""
    return YuiValue(x)


def n(result):
    """YuiValue/native → Python値"""
    return YuiType.to_native(result)


# ─────────────────────────────────────────────────────────────────────────────
# 算術
# ─────────────────────────────────────────────────────────────────────────────

class TestAbs:
    def test_positive_int(self, stdlib):    assert n(stdlib['abs'](v(5))) == 5
    def test_negative_int(self, stdlib):    assert n(stdlib['abs'](v(-3))) == 3
    def test_zero(self, stdlib):            assert n(stdlib['abs'](v(0))) == 0
    def test_positive_float(self, stdlib):  assert abs(n(stdlib['abs'](v(1.5))) - 1.5) < 1e-6
    def test_negative_float(self, stdlib):  assert abs(n(stdlib['abs'](v(-2.5))) - 2.5) < 1e-6

    def test_no_args(self, stdlib):
        with pytest.raises(YuiError): stdlib['abs']()
    def test_too_many_args(self, stdlib):
        with pytest.raises(YuiError): stdlib['abs'](v(1), v(2))
    def test_wrong_type(self, stdlib):
        with pytest.raises(YuiError): stdlib['abs'](v("hello"))


class TestSum:
    def test_two_ints(self, stdlib):    assert n(stdlib['sum'](v(3), v(4))) == 7
    def test_three_ints(self, stdlib):  assert n(stdlib['sum'](v(1), v(2), v(3))) == 6
    def test_negative(self, stdlib):    assert n(stdlib['sum'](v(-1), v(2))) == 1
    def test_floats(self, stdlib):      assert abs(n(stdlib['sum'](v(1.5), v(2.5))) - 4.0) < 1e-6
    def test_mixed(self, stdlib):       assert abs(n(stdlib['sum'](v(1), v(2.5))) - 3.5) < 1e-6

    def test_no_args(self, stdlib):
        with pytest.raises(YuiError): stdlib['sum']()


class TestDiff:
    def test_ints(self, stdlib):    assert n(stdlib['diff'](v(10), v(3))) == 7
    def test_negative(self, stdlib): assert n(stdlib['diff'](v(3), v(10))) == -7
    def test_floats(self, stdlib):  assert abs(n(stdlib['diff'](v(5.0), v(2.0))) - 3.0) < 1e-6


class TestProduct:
    def test_two_ints(self, stdlib):   assert n(stdlib['product'](v(3), v(4))) == 12
    def test_three_ints(self, stdlib): assert n(stdlib['product'](v(2), v(3), v(4))) == 24
    def test_floats(self, stdlib):     assert abs(n(stdlib['product'](v(2.0), v(3.0))) - 6.0) < 1e-6
    def test_zero(self, stdlib):       assert n(stdlib['product'](v(5), v(0))) == 0


class TestQuotient:
    def test_int_division(self, stdlib): assert n(stdlib['quotient'](v(10), v(3))) == 3
    def test_exact(self, stdlib):        assert n(stdlib['quotient'](v(10), v(2))) == 5
    def test_float(self, stdlib):        assert abs(n(stdlib['quotient'](v(10.0), v(4.0))) - 2.5) < 1e-6

    def test_zero_division_int(self, stdlib):
        with pytest.raises(YuiError): stdlib['quotient'](v(10), v(0))
    def test_zero_division_float(self, stdlib):
        with pytest.raises(YuiError): stdlib['quotient'](v(10.0), v(0.0))


class TestRemainder:
    def test_ints(self, stdlib):      assert n(stdlib['remainder'](v(10), v(3))) == 1
    def test_no_remainder(self, stdlib): assert n(stdlib['remainder'](v(9), v(3))) == 0
    def test_floats(self, stdlib):    assert abs(n(stdlib['remainder'](v(5.5), v(2.0))) - 1.5) < 1e-6

    def test_zero_division(self, stdlib):
        with pytest.raises(YuiError): stdlib['remainder'](v(10), v(0))


class TestMaxMin:
    def test_max_ints(self, stdlib):    assert n(stdlib['max'](v(3), v(1), v(4), v(1), v(5))) == 5
    def test_max_floats(self, stdlib):  assert abs(n(stdlib['max'](v(1.5), v(2.5))) - 2.5) < 1e-6
    def test_max_negative(self, stdlib): assert n(stdlib['max'](v(-3), v(-1))) == -1
    def test_min_ints(self, stdlib):    assert n(stdlib['min'](v(3), v(1), v(4))) == 1
    def test_min_floats(self, stdlib):  assert abs(n(stdlib['min'](v(1.5), v(0.5))) - 0.5) < 1e-6
    def test_min_negative(self, stdlib): assert n(stdlib['min'](v(-3), v(-1))) == -3

    def test_max_no_args(self, stdlib):
        with pytest.raises((YuiError, Exception)): stdlib['max']()
    def test_min_no_args(self, stdlib):
        with pytest.raises((YuiError, Exception)): stdlib['min']()


# ─────────────────────────────────────────────────────────────────────────────
# 乱数
# ─────────────────────────────────────────────────────────────────────────────

class TestRandom:
    def test_is_float(self, stdlib):
        assert YuiType.is_float(stdlib['random']())

    def test_range(self, stdlib):
        for _ in range(20):
            val = n(stdlib['random']())
            assert 0.0 <= val < 1.0

    def test_randint_is_int(self, stdlib):
        assert YuiType.is_int(stdlib['randint'](v(10)))

    def test_randint_range(self, stdlib):
        for _ in range(20):
            val = n(stdlib['randint'](v(10)))
            assert 0 <= val < 10

    def test_randint_one(self, stdlib):
        # 上限1 → 必ず0
        assert n(stdlib['randint'](v(1))) == 0

    def test_randint_zero_raises(self, stdlib):
        with pytest.raises(YuiError): stdlib['randint'](v(0))
    def test_randint_negative_raises(self, stdlib):
        with pytest.raises(YuiError): stdlib['randint'](v(-5))


# ─────────────────────────────────────────────────────────────────────────────
# ビット演算
# ─────────────────────────────────────────────────────────────────────────────

class TestBitwise:
    def test_and(self, stdlib):   assert n(stdlib['and'](v(0b1010), v(0b1100))) == 0b1000
    def test_and_zero(self, stdlib): assert n(stdlib['and'](v(0b1111), v(0b0000))) == 0

    def test_or(self, stdlib):    assert n(stdlib['or'](v(0b1010), v(0b1100))) == 0b1110
    def test_or_identity(self, stdlib): assert n(stdlib['or'](v(0b1010), v(0))) == 0b1010

    def test_xor(self, stdlib):   assert n(stdlib['xor'](v(0b1010), v(0b1100))) == 0b0110
    def test_xor_self(self, stdlib): assert n(stdlib['xor'](v(0b1010), v(0b1010))) == 0

    def test_not_zero(self, stdlib):      assert n(stdlib['not'](v(0))) == -1
    def test_not_minus_one(self, stdlib): assert n(stdlib['not'](v(-1))) == 0
    def test_not_positive(self, stdlib):  assert n(stdlib['not'](v(1))) == -2

    def test_shl(self, stdlib):     assert n(stdlib['shl'](v(1), v(3))) == 8
    def test_shl_zero(self, stdlib): assert n(stdlib['shl'](v(5), v(0))) == 5

    def test_shr(self, stdlib):     assert n(stdlib['shr'](v(8), v(3))) == 1
    def test_shr_zero(self, stdlib): assert n(stdlib['shr'](v(5), v(0))) == 5


# ─────────────────────────────────────────────────────────────────────────────
# 型判定
# ─────────────────────────────────────────────────────────────────────────────

class TestTypePredicates:
    # isint
    def test_isint_int(self, stdlib):    assert n(stdlib['isint'](v(42))) == 1
    def test_isint_float(self, stdlib):  assert n(stdlib['isint'](v(42.0))) == 0
    def test_isint_string(self, stdlib): assert n(stdlib['isint'](v("hello"))) == 0

    # isfloat
    def test_isfloat_float(self, stdlib):  assert n(stdlib['isfloat'](v(3.14))) == 1
    def test_isfloat_int(self, stdlib):    assert n(stdlib['isfloat'](v(3))) == 0
    def test_isfloat_string(self, stdlib): assert n(stdlib['isfloat'](v("3.14"))) == 0

    # isstring
    def test_isstring_string(self, stdlib):  assert n(stdlib['isstring'](v("hello"))) == 1
    def test_isstring_int(self, stdlib):     assert n(stdlib['isstring'](v(42))) == 0
    def test_isstring_float(self, stdlib):   assert n(stdlib['isstring'](v(3.14))) == 0

    # isarray
    def test_isarray_array(self, stdlib): assert n(stdlib['isarray'](v([1, 2, 3]))) == 1
    def test_isarray_int(self, stdlib):   assert n(stdlib['isarray'](v(42))) == 0

    # isobject
    def test_isobject_object(self, stdlib): assert n(stdlib['isobject'](v({"a": 1}))) == 1
    def test_isobject_int(self, stdlib):    assert n(stdlib['isobject'](v(42))) == 0
    def test_isobject_array(self, stdlib):  assert n(stdlib['isobject'](v([1, 2]))) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 型変換
# ─────────────────────────────────────────────────────────────────────────────

class TestTypeConversions:
    # toint
    def test_toint_from_float_truncates(self, stdlib): assert n(stdlib['toint'](v(3.9))) == 3
    def test_toint_from_negative_float(self, stdlib):  assert n(stdlib['toint'](v(-3.9))) == -3
    def test_toint_from_int(self, stdlib):             assert n(stdlib['toint'](v(5))) == 5

    # tofloat
    def test_tofloat_from_int(self, stdlib):
        result = stdlib['tofloat'](v(3))
        assert YuiType.is_float(result)
        assert abs(n(result) - 3.0) < 1e-6
    def test_tofloat_from_float(self, stdlib):
        assert abs(n(stdlib['tofloat'](v(3.14))) - 3.14) < 1e-6
    def test_tofloat_from_string(self, stdlib):
        result = stdlib['tofloat'](v("2.5"))
        assert abs(n(result) - 2.5) < 1e-6

    # tostring
    def test_tostring_from_int(self, stdlib):   assert n(stdlib['tostring'](v(42))) == "42"
    def test_tostring_from_float(self, stdlib):
        assert n(stdlib['tostring'](v(3.14))) == "3.140000"
    def test_tostring_from_negative_int(self, stdlib): assert n(stdlib['tostring'](v(-5))) == "-5"

    # toarray
    def test_toarray_from_array(self, stdlib):
        result = stdlib['toarray'](v([1, 2, 3]))
        assert YuiType.is_array(result)
        assert n(result) == [1, 2, 3]

    # toobject
    def test_toobject_from_object(self, stdlib):
        result = stdlib['toobject'](v({"x": 1}))
        assert YuiType.is_object(result)
