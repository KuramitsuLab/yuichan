import pytest
from .yuitypes import (
    YuiError, YuiValue, YuiType,
    YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType,
    YuiStringType, YuiArrayType, YuiObjectType,
)

class TestValue:
    """式の評価に関するテストクラス"""

    def test_int(self):
        value = YuiValue(0)
        assert value.native == 0

    def test_int(self):
        value = YuiValue(0)
        assert len(value.arrayview) == 32
        assert value.get_item(30).native == 0
        value.set_item(30, YuiValue(1))
        assert value.get_item(30).native == 1
        value.set_item(31, YuiValue(1))
        assert value.native == 3
        assert value.stringfy(arrayview=True, indent_prefix=None) == '[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]'

    def test_float(self):
        value = YuiValue(3.14)
        assert value.native == 3.14
        assert value.arrayview == [1, 3, 1, 4, 0, 0, 0, 0]

        value = YuiValue(-3.14)
        assert value.native == -3.14
        assert value.arrayview == [-1, 3, 1, 4, 0, 0, 0, 0]

    def test_string(self):
        value = YuiValue("ABC")
        assert value.native == "ABC"
        assert value.arrayview == [ord('A'), ord('B'), ord('C')]
        value.set_item(1, YuiValue(ord('X')))
        assert value.native == "AXC"
        assert value.arrayview == [ord('A'), ord('X'), ord('C')]
        value.append(YuiValue(ord('Z')))
        assert value.native == "AXCZ"
        assert value.arrayview == [ord('A'), ord('X'), ord('C'), ord('Z')]
        assert value.stringfy() == '"AXCZ"'
        assert value.stringfy(arrayview=True) == '[65, 88, 67, 90]'

    def test_array(self):
        array = [1, [1, 2, 3], "ABC"]
        value = YuiValue(array)
        assert value.native == array
        assert isinstance(value.arrayview[0], int)
        assert isinstance(value.arrayview[1], YuiValue)
        assert isinstance(value.arrayview[2], str)
        assert value.stringfy() == '[1, [1, 2, 3], "ABC"]'

    def test_object(self):
        obj = {"a": 1, "b": [1, 2], "c": "ABC"}
        value = YuiValue(obj)
        assert value.native == obj
        assert isinstance(value.arrayview[0],YuiValue)
        assert isinstance(value.arrayview[1],YuiValue)
        assert isinstance(value.arrayview[2],YuiValue)
        assert value.stringfy() == '{"a": 1, "b": [1, 2], "c": "ABC"}'
        assert value.stringfy(arrayview=True) == '[["a", 1], ["b", [1, 2]], ["c", "ABC"]]'


class TestBoolean:
    """YuiBooleanType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_boolean(self):
        assert isinstance(YuiValue(True).type, YuiBooleanType)
        assert isinstance(YuiValue(False).type, YuiBooleanType)

    def test_is_bool(self):
        assert YuiType.is_bool(YuiValue(True))
        assert YuiType.is_bool(YuiValue(False))

    def test_bool_is_not_int(self):
        """bool は YuiIntType ではなく YuiBooleanType に分類される"""
        assert not YuiType.is_int(YuiValue(True))
        assert not YuiType.is_int(YuiValue(False))

    def test_int_is_not_bool(self):
        assert not YuiType.is_bool(YuiValue(0))
        assert not YuiType.is_bool(YuiValue(1))

    def test_is_primitive(self):
        assert YuiValue(True).is_primitive()
        assert YuiValue(False).is_primitive()

    # ── native / arrayview ──────────────────────────────────────────────────

    def test_native_true(self):
        assert YuiValue(True).native is True

    def test_native_false(self):
        assert YuiValue(False).native is False

    def test_arrayview_true(self):
        assert YuiValue(True).arrayview == [1]

    def test_arrayview_false(self):
        assert YuiValue(False).arrayview == []

    def test_roundtrip_true(self):
        """arrayview → to_native のラウンドトリップ"""
        v = YuiValue(True)
        restored = YuiType.BooleanType.to_native(v.arrayview)
        assert restored is True

    def test_roundtrip_false(self):
        v = YuiValue(False)
        restored = YuiType.BooleanType.to_native(v.arrayview)
        assert restored is False

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy_true(self):
        assert YuiValue(True).stringfy() == "true"

    def test_stringfy_false(self):
        assert YuiValue(False).stringfy() == "false"

    # ── equals ──────────────────────────────────────────────────────────────

    def test_equals_true_true(self):
        assert YuiValue(True).equals(YuiValue(True))

    def test_equals_false_false(self):
        assert YuiValue(False).equals(YuiValue(False))

    def test_equals_true_false(self):
        assert not YuiValue(True).equals(YuiValue(False))

    def test_equals_false_true(self):
        assert not YuiValue(False).equals(YuiValue(True))

    def test_equals_bool_vs_int(self):
        """bool と int は型が異なるため等しくない"""
        assert not YuiValue(True).equals(YuiValue(1))
        assert not YuiValue(False).equals(YuiValue(0))

    # ── less_than ───────────────────────────────────────────────────────────

    def test_less_than_false_lt_true(self):
        assert YuiValue(False).less_than(YuiValue(True))

    def test_less_than_true_not_lt_false(self):
        assert not YuiValue(True).less_than(YuiValue(False))

    def test_less_than_equal_is_false(self):
        assert not YuiValue(True).less_than(YuiValue(True))

    # ── check_element (immutable) ────────────────────────────────────────────

    def test_check_element_raises(self):
        """boolean は配列要素に使えない"""
        with pytest.raises(YuiError):
            YuiType.BooleanType.check_element(YuiValue(True))


class TestNull:
    """YuiNullType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_null(self):
        assert isinstance(YuiValue(None).type, YuiNullType)

    def test_nullvalue_singleton(self):
        assert YuiValue.NullValue.type is YuiType.NullType

    def test_not_other_types(self):
        null = YuiValue(None)
        assert not YuiType.is_bool(null)
        assert not YuiType.is_int(null)
        assert not YuiType.is_float(null)
        assert not YuiType.is_string(null)
        assert not YuiType.is_array(null)
        assert not YuiType.is_object(null)

    # ── native / arrayview ──────────────────────────────────────────────────

    def test_native_is_none(self):
        assert YuiValue(None).native is None

    def test_arrayview_is_empty(self):
        assert YuiValue(None).arrayview == []

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue(None).stringfy() == "null"

    # ── equals ──────────────────────────────────────────────────────────────

    def test_equals_null_null(self):
        assert YuiValue(None).equals(YuiValue(None))

    def test_equals_null_vs_zero(self):
        assert not YuiValue(None).equals(YuiValue(0))

    # ── check_element (immutable) ────────────────────────────────────────────

    def test_check_element_raises(self):
        with pytest.raises(YuiError):
            YuiType.NullType.check_element(YuiValue(None))


class TestInt:
    """YuiIntType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_int(self):
        assert isinstance(YuiValue(42).type, YuiIntType)

    def test_is_int(self):
        assert YuiType.is_int(YuiValue(42))
        assert YuiType.is_int(YuiValue(-1))
        assert YuiType.is_int(YuiValue(0))

    def test_is_number(self):
        assert YuiType.is_number(YuiValue(42))

    def test_not_bool(self):
        """bool は IntType ではなく BooleanType"""
        assert not YuiType.is_bool(YuiValue(42))

    def test_is_primitive(self):
        assert YuiValue(42).is_primitive()

    # ── native ──────────────────────────────────────────────────────────────

    def test_native(self):
        assert YuiValue(42).native == 42
        assert YuiValue(-1).native == -1
        assert YuiValue(0).native == 0

    # ── arrayview (32ビット2の補数) ─────────────────────────────────────────

    def test_arrayview_length(self):
        assert len(YuiValue(0).arrayview) == 32

    def test_arrayview_zero(self):
        assert YuiValue(0).arrayview == [0] * 32

    def test_arrayview_one(self):
        bits = YuiValue(1).arrayview
        assert bits[-1] == 1
        assert all(b == 0 for b in bits[:-1])

    def test_arrayview_negative_one(self):
        """-1 はすべてのビットが 1（2の補数）"""
        assert YuiValue(-1).arrayview == [1] * 32

    def test_roundtrip(self):
        for n in [0, 1, -1, 42, -42, 2**31 - 1, -(2**31)]:
            v = YuiValue(n)
            assert YuiType.IntType.to_native(v.arrayview) == n

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue(42).stringfy() == "42"
        assert YuiValue(-1).stringfy() == "-1"
        assert YuiValue(0).stringfy() == "0"

    # ── get_item / set_item ──────────────────────────────────────────────────

    def test_get_item(self):
        v = YuiValue(0)
        assert v.get_item(YuiValue(31)).native == 0

    def test_set_get_item(self):
        v = YuiValue(0)
        v.set_item(YuiValue(30), YuiValue(1))
        v.set_item(YuiValue(31), YuiValue(1))
        assert v.native == 3

    def test_set_item_invalid_raises(self):
        """ビット値は 0/1 のみ"""
        with pytest.raises(YuiError):
            YuiValue(0).set_item(YuiValue(0), YuiValue(5))

    def test_get_item_out_of_range_raises(self):
        with pytest.raises(YuiError):
            YuiValue(0).get_item(YuiValue(32))

    # ── equals ──────────────────────────────────────────────────────────────

    def test_equals_same(self):
        assert YuiValue(42).equals(YuiValue(42))

    def test_equals_different(self):
        assert not YuiValue(42).equals(YuiValue(43))

    def test_equals_int_and_float(self):
        assert YuiValue(3).equals(YuiValue(3.0))

    def test_equals_int_vs_bool(self):
        """int と bool は等しくない"""
        assert not YuiValue(1).equals(YuiValue(True))
        assert not YuiValue(0).equals(YuiValue(False))

    # ── less_than ───────────────────────────────────────────────────────────

    def test_less_than(self):
        assert YuiValue(1).less_than(YuiValue(2))

    def test_not_less_than_equal(self):
        assert not YuiValue(2).less_than(YuiValue(2))

    def test_not_less_than_greater(self):
        assert not YuiValue(3).less_than(YuiValue(2))

    def test_less_than_vs_float(self):
        assert YuiValue(1).less_than(YuiValue(1.5))


class TestFloat:
    """YuiFloatType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_float(self):
        assert isinstance(YuiValue(3.14).type, YuiFloatType)

    def test_is_float(self):
        assert YuiType.is_float(YuiValue(3.14))

    def test_is_number(self):
        assert YuiType.is_number(YuiValue(3.14))

    def test_not_int(self):
        assert not YuiType.is_int(YuiValue(3.14))

    def test_is_primitive(self):
        assert YuiValue(3.14).is_primitive()

    # ── native ──────────────────────────────────────────────────────────────

    def test_native(self):
        assert YuiValue(3.14).native == 3.14

    def test_native_negative(self):
        assert YuiValue(-2.5).native == -2.5

    # ── arrayview ───────────────────────────────────────────────────────────

    def test_arrayview_positive(self):
        assert YuiValue(3.14).arrayview == [1, 3, 1, 4, 0, 0, 0, 0]

    def test_arrayview_negative(self):
        assert YuiValue(-3.14).arrayview == [-1, 3, 1, 4, 0, 0, 0, 0]

    def test_arrayview_zero(self):
        assert YuiValue(0.0).arrayview == [1, 0, 0, 0, 0, 0, 0, 0]

    def test_roundtrip(self):
        for x in [3.14, -2.5, 1.0, 0.0]:
            v = YuiValue(x)
            assert abs(YuiType.FloatType.to_native(v.arrayview) - x) < 1e-6

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue(3.14).stringfy() == "3.140000"
        assert YuiValue(-2.5).stringfy() == "-2.500000"

    # ── equals ──────────────────────────────────────────────────────────────

    def test_equals_same(self):
        assert YuiValue(3.14).equals(YuiValue(3.14))

    def test_equals_different(self):
        assert not YuiValue(3.14).equals(YuiValue(2.71))

    def test_equals_float_and_int(self):
        assert YuiValue(3.0).equals(YuiValue(3))

    # ── less_than ───────────────────────────────────────────────────────────

    def test_less_than(self):
        assert YuiValue(1.0).less_than(YuiValue(2.0))

    def test_not_less_than_equal(self):
        assert not YuiValue(2.0).less_than(YuiValue(2.0))

    def test_less_than_vs_int(self):
        assert YuiValue(1.5).less_than(YuiValue(2))


class TestString:
    """YuiStringType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_string(self):
        assert isinstance(YuiValue("hello").type, YuiStringType)

    def test_is_string(self):
        assert YuiType.is_string(YuiValue("hello"))

    def test_not_other_types(self):
        s = YuiValue("hello")
        assert not YuiType.is_int(s)
        assert not YuiType.is_float(s)
        assert not YuiType.is_array(s)

    def test_is_primitive(self):
        assert YuiValue("hello").is_primitive()

    # ── native / arrayview ──────────────────────────────────────────────────

    def test_native(self):
        assert YuiValue("ABC").native == "ABC"

    def test_arrayview(self):
        assert YuiValue("ABC").arrayview == [ord('A'), ord('B'), ord('C')]

    def test_empty_string(self):
        assert YuiValue("").native == ""
        assert YuiValue("").arrayview == []

    def test_roundtrip(self):
        for s in ["ABC", "hello", "日本語", ""]:
            v = YuiValue(s)
            assert YuiType.StringType.to_native(v.arrayview) == s

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue("hello").stringfy() == '"hello"'

    def test_stringfy_with_quote(self):
        assert YuiValue('say "hi"').stringfy() == '"say \\"hi\\""'

    def test_stringfy_with_newline(self):
        assert YuiValue("a\nb").stringfy() == '"a\\nb"'

    # ── get_item / set_item / append ─────────────────────────────────────────

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

    def test_append_non_int_raises(self):
        """文字コード以外は追加できない"""
        with pytest.raises(YuiError):
            YuiValue("AB").append(YuiValue("C"))

    def test_get_item_out_of_range_raises(self):
        with pytest.raises(YuiError):
            YuiValue("AB").get_item(YuiValue(5))

    # ── equals ──────────────────────────────────────────────────────────────

    def test_equals_same(self):
        assert YuiValue("hello").equals(YuiValue("hello"))

    def test_equals_different(self):
        assert not YuiValue("hello").equals(YuiValue("world"))

    def test_equals_vs_int(self):
        assert not YuiValue("1").equals(YuiValue(1))

    # ── less_than ───────────────────────────────────────────────────────────

    def test_less_than(self):
        assert YuiValue("abc").less_than(YuiValue("abd"))

    def test_not_less_than_equal(self):
        assert not YuiValue("abc").less_than(YuiValue("abc"))

    def test_not_less_than_greater(self):
        assert not YuiValue("abd").less_than(YuiValue("abc"))


class TestArray:
    """YuiArrayType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_array(self):
        assert isinstance(YuiValue([1, 2, 3]).type, YuiArrayType)

    def test_is_array(self):
        assert YuiType.is_array(YuiValue([1, 2, 3]))

    def test_not_other_types(self):
        a = YuiValue([1, 2, 3])
        assert not YuiType.is_int(a)
        assert not YuiType.is_string(a)
        assert not YuiType.is_object(a)

    # ── native / arrayview ──────────────────────────────────────────────────

    def test_native(self):
        assert YuiValue([1, 2, 3]).native == [1, 2, 3]

    def test_empty_array(self):
        assert YuiValue([]).native == []
        assert YuiValue([]).arrayview == []

    def test_arrayview_int_elements(self):
        """プリミティブな int 要素はそのまま int"""
        assert YuiValue([1, 2, 3]).arrayview == [1, 2, 3]

    def test_arrayview_nested_array(self):
        """ネストした配列は YuiValue に包まれる"""
        v = YuiValue([1, [2, 3], "A"])
        assert isinstance(v.arrayview[0], int)
        assert isinstance(v.arrayview[1], YuiValue)
        assert isinstance(v.arrayview[2], str)

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue([1, 2, 3]).stringfy() == "[1, 2, 3]"

    def test_stringfy_empty(self):
        assert YuiValue([]).stringfy() == "[]"

    def test_stringfy_with_string(self):
        assert YuiValue([1, "AB"]).stringfy() == '[1, "AB"]'

    # ── get_item / set_item / append ─────────────────────────────────────────

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

    def test_get_item_out_of_range_raises(self):
        with pytest.raises(YuiError):
            YuiValue([1, 2]).get_item(YuiValue(5))


class TestObject:
    """YuiObjectType のテスト"""

    # ── 型判定 ──────────────────────────────────────────────────────────────

    def test_type_is_object(self):
        assert isinstance(YuiValue({"a": 1}).type, YuiObjectType)

    def test_is_object(self):
        assert YuiType.is_object(YuiValue({"a": 1}))

    def test_not_other_types(self):
        o = YuiValue({"a": 1})
        assert not YuiType.is_int(o)
        assert not YuiType.is_array(o)
        assert not YuiType.is_string(o)

    # ── native / arrayview ──────────────────────────────────────────────────

    def test_native(self):
        obj = {"a": 1, "b": "hello"}
        assert YuiValue(obj).native == obj

    def test_empty_object(self):
        assert YuiValue({}).native == {}

    def test_arrayview_structure(self):
        """各キーと値のペアが YuiValue として格納される"""
        v = YuiValue({"x": 1, "y": 2})
        assert len(v.arrayview) == 2
        assert all(isinstance(e, YuiValue) for e in v.arrayview)

    # ── stringfy ────────────────────────────────────────────────────────────

    def test_stringfy(self):
        assert YuiValue({"a": 1}).stringfy() == '{"a": 1}'

    def test_stringfy_empty(self):
        assert YuiValue({}).stringfy() == '{}'

    def test_stringfy_mixed(self):
        assert YuiValue({"a": 1, "b": "hi"}).stringfy() == '{"a": 1, "b": "hi"}'

    # ── get_item / set_item ──────────────────────────────────────────────────

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