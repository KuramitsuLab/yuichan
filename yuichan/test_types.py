import pytest
from .yuitypes import (
    YuiError, YuiValue, YuiValue,
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