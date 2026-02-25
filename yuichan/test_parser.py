import pytest
from .yuiparser import Source
from .yuitypes import YuiError
from .yuisyntax import load_syntax

yui_syntax = load_syntax('yui')

class TestSource:
    """式の評価に関するテストクラス"""

    def test_is_defined(self):
        source = Source('', syntax=yui_syntax)
        source.update_syntax(**{
            "line-feed": r"\n",
            "whitespace": " ",
            "whitespaces": r"[ \t\r]+",
        })
        assert source.is_defined("linefeed")
        assert source.is_defined("comment-begin") == False

    def test_consume(self):
        source = Source("X  abc", pos=1)
        assert source.is_("whitespaces", lskip_ws=False) == True
        assert source.pos == 3

        source = Source("X  abc", pos=1)
        assert source.is_("whitespace", lskip_ws=False) == True
        assert source.pos == 2

        source = Source("Xabc", pos=1)
        assert source.is_("whitespaces", lskip_ws=False) == False
        assert source.pos == 1
        with pytest.raises(YuiError) as excinfo:
            source = Source("Xabc", pos=1)
            source.require_("whitespace", lskip_ws=False)
            assert source.pos == 1
        assert "expected" in str(excinfo.value)
        assert excinfo.value.error_node.pos == 1
        assert excinfo.value.error_node.end_pos == 2

    def test_consume_until(self):
        source = Source("X    \nabc", pos=1)
        assert source.consume_until("linefeed") == True
        assert source.pos == 5
        assert source.source[source.pos] == '\n'

    def test_capture_indent(self):
        source = Source("X\n    x=1\nabc", pos=3)
        source.consume_until("linefeed")
        assert source.capture_indent() == "    "

    def test_skip_whitespaces_comments(self):
        source = Source("X=1  #hoge   \ny=1", pos=3)
        source.skip_whitespaces_and_comments()
        assert source.source[source.pos] == '\n'

        source = Source("X=1  #hoge   \ny=1", pos=3)
        source.skip_whitespaces_and_comments(include_linefeed=True)
        assert source.source[source.pos] == 'y'

        source = Source("X =  (*optional*) 1  #hoge   \ny=1", pos=3)
        source.update_syntax(**{
            "comment-begin": r"\(\*",
            "comment-end": r"\*\)",
        })
        source.skip_whitespaces_and_comments(include_linefeed=True)
        assert source.source[source.pos] == '1'


class TestParseExpressionNode:

    def test_Number(self):
        source = Source("01234 #コメント", pos=1)

        number_node = source.parse("@Number")
        assert str(number_node) == '1234'

        source = Source("0123.12 #コメント", pos=1)
        number_node = source.parse("@Number")
        assert str(number_node) == '123.12'

        with pytest.raises(YuiError) as excinfo:
            source = Source("xxx")
            number_node = source.parse("@Number", BK=True)
        assert "expected" in str(excinfo.value)
        assert excinfo.value.error_node.pos == 0
        assert excinfo.value.error_node.end_pos == 1

    def test_NumberAsExpression(self):
        source = Source("01234 #コメント", pos=1)

        number_node = source.parse("@Expression")
        assert str(number_node) == '1234'

        source = Source("0123.12 #コメント", pos=1)
        number_node = source.parse("@Expression")
        assert str(number_node) == '123.12'

    def test_String(self):
        source = Source('"ABC"', pos=0)
        string_node = source.parse("@String")
        assert str(string_node) == '"ABC"'

        source = Source('"AB{1}C"', pos=0)
        string_node = source.parse("@String")
        assert str(string_node) == '"AB{1}C"'

    def test_StringAsExpression(self):
        source = Source('"ABC"', pos=0)
        string_node = source.parse("@Expression")
        assert str(string_node) == '"ABC"'

        source = Source('"AB{1}C"', pos=0)
        string_node = source.parse("@Expression")
        assert str(string_node) == '"AB{1}C"'

    def test_String_wrong_token(self):
        with pytest.raises(YuiError) as excinfo:
            source = Source("'A'", pos=0)
            string_node = source.parse("@Expression")
        assert "wrong" in str(excinfo.value) or "typo" in str(excinfo.value)

    def test_Array(self):
        source = Source('[1,2]', pos=0)
        array_node = source.parse("@Array")
        assert str(array_node) == '[1,2]'

        source = Source('[\n1,\n2\n]', pos=0)
        array_node = source.parse("@Array")
        assert str(array_node) == '[\n1,\n2\n]'

    def test_Object(self):
        source = Source('{"A": 1}', pos=0)
        object_node = source.parse("@Object")
        assert str(object_node) == '{"A": 1}'

    def test_Name(self):
        source = Source("x_1 = 1")
        name_node = source.parse("@Name")
        assert str(name_node) == "x_1"

    def test_GetArrayIndex(self):
        source = Source("x[0]")
        name_node = source.parse("@Expression")
        assert str(name_node) == "x[0]"

    def test_FuncAppAsPrimary(self):
        source = Source("x(0)")
        name_node = source.parse("@Primary")
        assert str(name_node) == "x(0)"

        source = Source("x()")
        name_node = source.parse("@Primary")
        assert str(name_node) == "x()"

        source = Source("x(1, 2)")
        name_node = source.parse("@Primary")
        assert str(name_node) == "x(1, 2)"

    def test_FuncAppAsExpression(self):
        source = Source("x(0)")
        name_node = source.parse("@Expression")
        assert str(name_node) == "x(0)"

        source = Source("x()")
        name_node = source.parse("@Expression")
        assert str(name_node) == "x()"

        source = Source("x(1, 2)")
        name_node = source.parse("@Expression")
        assert str(name_node) == "x(1, 2)"

class TestParseBinaryNode:
    
    def test_Add(self):
        source = Source("1 + 2")
        add_node = source.parse("@Expression")
        assert str(add_node) == "1 + 2"

    def test_Subtract(self):
        source = Source("1 - 2")
        subtract_node = source.parse("@Expression")
        assert str(subtract_node) == "1 - 2"

    def test_Multiply(self):
        source = Source("3 * 4")
        multiply_node = source.parse("@Expression")
        assert str(multiply_node) == "3 * 4"

    def test_Divide(self):
        source = Source("3 / 4")
        divide_node = source.parse("@Expression")
        assert str(divide_node) == "3 / 4"

    def test_Modulo(self):
        source = Source("5 % 2")
        modulo_node = source.parse("@Expression")
        assert str(modulo_node) == "5 % 2"


