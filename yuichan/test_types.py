import pytest
from .yuitypes import (
    YuiValue, YuiType, YuiError, types, OPERATORS,
    YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType,
    YuiStringType, YuiArrayType, YuiObjectType,
    NullType, BoolType, IntType, FloatType, NumberType,
    StringType, ArrayType, ObjectType,
)


# ─────────────────────────────────────────────────────────────────────────────
# box / unbox ラウンドトリップ
# ─────────────────────────────────────────────────────────────────────────────

BOX_CASES = [
    # (native値, 期待する型クラス)
    (None,              YuiNullType),
    (True,              YuiBooleanType),
    (False,             YuiBooleanType),
    (1,                 YuiIntType),
    (0,                 YuiIntType),
    (-1,                YuiIntType),
    (1.0,               YuiFloatType),
    (0.0,               YuiFloatType),
    (-1.0,              YuiFloatType),
    ("",                YuiStringType),
    ("123",             YuiStringType),
    ([],                YuiArrayType),
    ([1, 2, 3],         YuiArrayType),
    ({},                YuiObjectType),
    ({"a": 1, "b": 2},  YuiObjectType),
]

@pytest.mark.parametrize("native, expected_type", BOX_CASES)
def test_box_returns_yuivalue(native, expected_type):
    v = types.box(native)
    assert isinstance(v, YuiValue)

@pytest.mark.parametrize("native, expected_type", BOX_CASES)
def test_box_type(native, expected_type):
    v = types.box(native)
    assert isinstance(v.type, expected_type), f"box({native!r}).type = {v.type}, expected {expected_type}"

@pytest.mark.parametrize("native, expected_type", BOX_CASES)
def test_box_native(native, expected_type):
    v = types.box(native)
    assert v.native == native, f"box({native!r}).native = {v.native!r}, expected {native!r}"

@pytest.mark.parametrize("native, expected_type", BOX_CASES)
def test_unbox_roundtrip(native, expected_type):
    v = types.box(native)
    result = types.unbox(v)
    assert result == native, f"unbox(box({native!r})) = {result!r}, expected {native!r}"

@pytest.mark.parametrize("native, expected_type", BOX_CASES)
def test_unbox_identity(native, expected_type):
    """YuiValue でない値を unbox するとそのまま返る"""
    result = types.unbox(native)
    assert result == native


# ─────────────────────────────────────────────────────────────────────────────
# box の冪等性 (box(YuiValue) → そのまま返る)
# ─────────────────────────────────────────────────────────────────────────────

def test_box_idempotent():
    v = YuiValue(42)
    assert types.box(v) is v


# ─────────────────────────────────────────────────────────────────────────────
# None/True/False はシングルトンを返す
# ─────────────────────────────────────────────────────────────────────────────

def test_box_none_is_nullvalue():
    assert types.box(None) is YuiValue.NullValue

def test_box_true_is_truevalue():
    assert types.box(True) is YuiValue.TrueValue

def test_box_false_is_falsevalue():
    assert types.box(False) is YuiValue.FalseValue


# ─────────────────────────────────────────────────────────────────────────────
# 型判定ヘルパー (is_*)
# ─────────────────────────────────────────────────────────────────────────────

IS_TYPE_CASES = [
    # (native値, is_bool, is_int, is_float, is_string, is_array, is_object)
    (None,             False, False, False, False, False, False),
    (True,             True,  False, False, False, False, False),
    (False,            True,  False, False, False, False, False),
    (1,                False, True,  False, False, False, False),
    (0,                False, True,  False, False, False, False),
    (-1,               False, True,  False, False, False, False),
    (1.0,              False, False, True,  False, False, False),
    (0.0,              False, False, True,  False, False, False),
    (-1.0,             False, False, True,  False, False, False),
    ("",               False, False, False, True,  False, False),
    ("123",            False, False, False, True,  False, False),
    ([],               False, False, False, False, True,  False),
    ([1, 2, 3],        False, False, False, False, True,  False),
    ({},               False, False, False, False, False, True),
    ({"a": 1},         False, False, False, False, False, True),
]

@pytest.mark.parametrize("native,is_bool,is_int,is_float,is_string,is_array,is_object", IS_TYPE_CASES)
def test_is_type(native, is_bool, is_int, is_float, is_string, is_array, is_object):
    v = types.box(native)
    assert types.is_bool(v)   == is_bool,   f"is_bool({native!r})"
    assert types.is_int(v)    == is_int,    f"is_int({native!r})"
    assert types.is_float(v)  == is_float,  f"is_float({native!r})"
    assert types.is_string(v) == is_string, f"is_string({native!r})"
    assert types.is_array(v)  == is_array,  f"is_array({native!r})"
    assert types.is_object(v) == is_object, f"is_object({native!r})"

def test_is_number_int():
    assert types.is_number(types.box(42))

def test_is_number_float():
    assert types.is_number(types.box(3.14))

def test_is_number_bool_is_not_number():
    assert not types.is_number(types.box(True))

def test_is_number_string_is_not_number():
    assert not types.is_number(types.box("1"))


# ─────────────────────────────────────────────────────────────────────────────
# get_item / set_item / append
# ─────────────────────────────────────────────────────────────────────────────

class TestArrayGetSetAppend:
    """YuiValue([...]) の get_item / set_item / append"""

    def test_get_item(self):
        v = YuiValue([10, 20, 30])
        assert v.get_item(YuiValue(0)).native == 10
        assert v.get_item(YuiValue(2)).native == 30

    def test_set_item(self):
        v = YuiValue([10, 20, 30])
        v.set_item(YuiValue(1), YuiValue(99))
        assert v.native == [10, 99, 30]

    def test_append(self):
        v = YuiValue([1, 2])
        v.append(YuiValue(3))
        assert v.native == [1, 2, 3]

    def test_append_empty(self):
        v = YuiValue([])
        v.append(YuiValue(42))
        assert v.native == [42]

    def test_get_item_out_of_range_raises(self):
        with pytest.raises(YuiError):
            YuiValue([1, 2]).get_item(YuiValue(5))

    def test_get_item_negative_raises(self):
        with pytest.raises(YuiError):
            YuiValue([1, 2]).get_item(YuiValue(-1))

    def test_set_then_get(self):
        v = YuiValue([0, 0, 0])
        v.set_item(YuiValue(1), YuiValue(7))
        assert v.get_item(YuiValue(1)).native == 7

    def test_append_nested_array(self):
        v = YuiValue([[1, 2], [3, 4]])
        v.append(YuiValue([5, 6]))
        assert v.native == [[1, 2], [3, 4], [5, 6]]


class TestStringGetSetAppend:
    """YuiValue("...") の get_item / set_item / append（文字コード単位）"""

    def test_get_item(self):
        v = YuiValue("ABC")
        assert v.get_item(YuiValue(0)).native == ord('A')
        assert v.get_item(YuiValue(2)).native == ord('C')

    def test_set_item(self):
        v = YuiValue("ABC")
        v.set_item(YuiValue(1), YuiValue(ord('X')))
        assert v.native == "AXC"

    def test_append(self):
        v = YuiValue("AB")
        v.append(YuiValue(ord('C')))
        assert v.native == "ABC"

    def test_append_empty_string(self):
        v = YuiValue("")
        v.append(YuiValue(ord('Z')))
        assert v.native == "Z"

    def test_get_item_out_of_range_raises(self):
        with pytest.raises(YuiError):
            YuiValue("AB").get_item(YuiValue(5))

    def test_get_item_negative_raises(self):
        with pytest.raises(YuiError):
            YuiValue("AB").get_item(YuiValue(-1))

    def test_set_then_get(self):
        v = YuiValue("hello")
        v.set_item(YuiValue(0), YuiValue(ord('H')))
        assert v.get_item(YuiValue(0)).native == ord('H')
        assert v.native == "Hello"


class TestObjectGetSetAppend:
    """YuiValue({...}) の get_item / set_item（文字列キー）"""

    def test_get_item_by_key(self):
        v = YuiValue({"x": 10, "y": 20})
        assert v.get_item(YuiValue("x")).native == 10
        assert v.get_item(YuiValue("y")).native == 20

    def test_get_item_missing_key_returns_null(self):
        v = YuiValue({"x": 10})
        assert v.get_item(YuiValue("z")).native is None

    def test_set_item_existing_key(self):
        v = YuiValue({"x": 10})
        v.set_item(YuiValue("x"), YuiValue(99))
        assert v.native["x"] == 99

    def test_set_item_new_key(self):
        v = YuiValue({"x": 10})
        v.set_item(YuiValue("y"), YuiValue(20))
        assert v.native["y"] == 20

    def test_set_then_get(self):
        v = YuiValue({})
        v.set_item(YuiValue("k"), YuiValue(42))
        assert v.get_item(YuiValue("k")).native == 42


class TestIntGetSetItem:
    """YuiValue(int) の get_item / set_item（ビット単位）"""

    def test_get_item_in_range(self):
        v = YuiValue(5)  # 5 = 0b101 → bits=[1,0,1]
        assert v.get_item(YuiValue(0)).native == 1
        assert v.get_item(YuiValue(1)).native == 0
        assert v.get_item(YuiValue(2)).native == 1

    def test_get_item_implicit_zero(self):
        """arrayview より上のビットは暗黙的に 0"""
        v = YuiValue(5)  # array=[1,0,1], length=3
        assert v.get_item(YuiValue(31)).native == 0

    def test_set_item_flip_bit(self):
        v = YuiValue(2)  # 0b10 → [0, 1]
        v.set_item(YuiValue(0), YuiValue(1))  # bit0: 0→1
        assert v.native == 3                   # 0b11 = 3

    def test_set_item_clear_bit(self):
        v = YuiValue(3)  # 0b11 → [1, 1]
        v.set_item(YuiValue(1), YuiValue(0))  # bit1: 1→0
        assert v.native == 1                   # 0b01 = 1

    def test_set_item_out_of_range_raises(self):
        """範囲外は自動拡張せずエラー"""
        v = YuiValue(0)  # array=[0], length=1
        with pytest.raises(YuiError):
            v.set_item(YuiValue(1), YuiValue(1))

    def test_get_item_negative_raises(self):
        with pytest.raises(YuiError):
            YuiValue(0).get_item(YuiValue(-1))


# ─────────────────────────────────────────────────────────────────────────────
# equals: BOX_CASES 間の比較
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("native, _", BOX_CASES)
def test_equals_self(native, _):
    """どの値も自分自身と等しい"""
    v = types.box(native)
    assert v.equals(v)

@pytest.mark.parametrize("native, _", BOX_CASES)
def test_equals_copy(native, _):
    """同じ native から作った別インスタンスも等しい"""
    a = types.box(native)
    b = types.box(native)
    assert a.equals(b)


# ── int / float クロスタイプ ─────────────────────────────────────────────────

INT_FLOAT_EQUAL_PAIRS = [
    (1,   1.0),
    (0,   0.0),
    (-1, -1.0),
]

@pytest.mark.parametrize("i, f", INT_FLOAT_EQUAL_PAIRS)
def test_int_equals_float(i, f):
    assert types.box(i).equals(types.box(f))

@pytest.mark.parametrize("i, f", INT_FLOAT_EQUAL_PAIRS)
def test_float_equals_int(i, f):
    assert types.box(f).equals(types.box(i))


# ── bool は int / float と等しくない ─────────────────────────────────────────

@pytest.mark.parametrize("b, n", [
    (True,  1),
    (False, 0),
    (True,  1.0),
    (False, 0.0),
])
def test_bool_not_equals_number(b, n):
    assert not types.box(b).equals(types.box(n))
    assert not types.box(n).equals(types.box(b))


# ── 異なる型は等しくない（代表例） ────────────────────────────────────────────

@pytest.mark.parametrize("a, b", [
    (None,        0),
    (None,        False),
    (None,        ""),
    (None,        []),
    (None,        {}),
    (True,        1),
    (False,       0),
    (1,           "1"),
    (1,           [1]),
    ([],          {}),
    ([1, 2, 3],   {"a": 1}),
])
def test_not_equals_cross_type(a, b):
    assert not types.box(a).equals(types.box(b))
    assert not types.box(b).equals(types.box(a))


# ── 同じ型・異なる値は等しくない ─────────────────────────────────────────────

@pytest.mark.parametrize("a, b", [
    (True,          False),
    (1,             0),
    (1,             -1),
    (0,             -1),
    (1.0,           0.0),
    (1.0,          -1.0),
    (0.0,          -1.0),
    ("",            "123"),
    ([],            [1, 2, 3]),
    ({},            {"a": 1, "b": 2}),
])
def test_not_equals_same_type(a, b):
    assert not types.box(a).equals(types.box(b))
    assert not types.box(b).equals(types.box(a))


# ─────────────────────────────────────────────────────────────────────────────
# OPERATORS
# ─────────────────────────────────────────────────────────────────────────────

def op(symbol, a, b):
    return OPERATORS[symbol].evaluate(types.box(a), types.box(b))


# ── == ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    # 同値
    (None,  None,   True),
    (True,  True,   True),
    (False, False,  True),
    (1,     1,      True),
    (0,     0,      True),
    (-1,    -1,     True),
    (1.0,   1.0,    True),
    ("hi",  "hi",   True),
    ([1,2], [1,2],  True),
    # int / float クロスタイプ
    (1,     1.0,    True),
    (0,     0.0,    True),
    (-1,   -1.0,    True),
    # 異値
    (1,     2,      False),
    (True,  False,  False),
    # bool は int/float と等しくない
    (True,  1,      False),
    (False, 0,      False),
    (True,  1.0,    False),
    (False, 0.0,    False),
])
def test_op_eq(a, b, expected):
    assert op('==', a, b) == expected


# ── != ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    (1,    2,    True),
    (1,    1,    False),
    (1,    1.0,  False),   # クロスタイプ等値 → != は False
    (True, 1,    True),    # bool != int
    (True, True, False),
])
def test_op_ne(a, b, expected):
    assert op('!=', a, b) == expected


# ── < ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    (1,     2,     True),
    (2,     1,     False),
    (1,     1,     False),   # 等値は < でない
    (1.0,   2.0,   True),
    (1,     1.5,   True),    # int vs float
    (1.5,   2,     True),    # float vs int
    ("abc", "abd", True),
    (False, True,  True),
])
def test_op_lt(a, b, expected):
    assert op('<', a, b) == expected


# ── > ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    (2,   1,   True),
    (1,   2,   False),
    (1,   1,   False),
    (2.0, 1.0, True),
    (2,   1.5, True),
])
def test_op_gt(a, b, expected):
    assert op('>', a, b) == expected


# ── <= ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    (1,   2,   True),
    (1,   1,   True),    # 等値は <= で True
    (2,   1,   False),
    (1,   1.0, True),    # int vs float 等値
])
def test_op_le(a, b, expected):
    assert op('<=', a, b) == expected


# ── >= ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a, b, expected", [
    (2,   1,   True),
    (1,   1,   True),    # 等値は >= で True
    (1,   2,   False),
    (1.0, 1,   True),    # float vs int 等値
])
def test_op_ge(a, b, expected):
    assert op('>=', a, b) == expected


# ── in / notin ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("elem, arr, expected", [
    (2,   [1, 2, 3], True),
    (9,   [1, 2, 3], False),
    (1.0, [1, 2, 3], True),    # int/float クロスタイプ
    (0,   [],        False),
])
def test_op_in(elem, arr, expected):
    assert op('in', elem, arr) == expected

@pytest.mark.parametrize("elem, arr, expected", [
    (2,   [1, 2, 3], False),
    (9,   [1, 2, 3], True),
    (0,   [],        True),
])
def test_op_notin(elem, arr, expected):
    assert op('notin', elem, arr) == expected
