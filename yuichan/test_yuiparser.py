import pytest
from .yuiparser import (
    Source, parse, YuiError, 
)

class TestSource:
    """式の評価に関するテストクラス"""

    def test_syntax(self):
        source = Source('')
        source.update_syntax(**{
            "line-feed": r"\n",
            "whitespace": " ",
            "whitespaces": r"[ \t\r]+",
        })
        assert source.is_defined("linefeed")
        assert source.is_defined("comment-begin") == False

    def test_consume(self):
        source = Source("X  abc", pos=1)
        assert source.is_match("whitespaces") == True
        assert source.pos == 3

        source = Source("X  abc", pos=1)
        assert source.is_match("whitespace") == True
        assert source.pos == 2

        source = Source("Xabc", pos=1)
        assert source.is_match("whitespaces") == False
        assert source.pos == 1
        with pytest.raises(YuiError) as excinfo:
            source = Source("Xabc", pos=1)
            source.try_match("whitespace")
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
        assert source.source[source .pos] == '1'

class TestParseExpressionNode:
    def test_Number(self):
        source = Source("0123", pos=1)
        assert source.is_defined("number-begin")
        assert source.is_defined("number-chars")

        number_node = parse("@Number", source, pc={})
        assert str(number_node) == '123'

        source = Source("0123.12", pos=1)
        number_node = parse("@Number", source, pc={})
        assert str(number_node) == '123.12'

        with pytest.raises(YuiError) as excinfo:
            source = Source("xxx")
            number_node = parse("@Number", source, pc={})
        assert "expected" in str(excinfo.value)
        assert excinfo.value.error_node.pos == 0
        assert excinfo.value.error_node.end_pos == 1

    def test_String(self):
        source = Source('"ABC"', pos=0)
        string_node = parse("@String", source, pc={})
        assert str(string_node) == '"ABC"'

        source = Source('"AB{1}C"', pos=0)
        string_node = parse("@String", source, pc={})
        assert str(string_node) == '"AB{1}C"'

    def test_Name(self):
        source = Source("x_1 = 1")
        name_node = parse("@Name", source, pc={})
        assert str(name_node) == "x_1"

class TestParseStatementNode:

    def test_Assignment(self):
        source = Source("x = 1")
        assignment_node = parse("@Assignment", source, pc={})
        assert str(assignment_node) == "x = 1"

    def test_Increment(self):
        source = Source("xを増やす")
        increment_node = parse("@Increment", source, pc={})
        assert str(increment_node) == "xを増やす"

    def test_Decrement(self):
        source = Source("xを減らす")
        decrement_node = parse("@Decrement", source, pc={})
        assert str(decrement_node) == "xを減らす"

    def test_Append(self):
        source = Source("xに10を追加する")
        append_node = parse("@Append", source, pc={})
        assert str(append_node) == "xに10を追加する"

        source = Source("xに10を追加する")
        append_node = parse("@Statement", source, pc={})
        assert str(append_node) == "xに10を追加する"



class TestParseBlockNode:

    def test_TopLevel(self):
        source = Source("x = 1\ny=2")
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x = 1\ny=2"

        # with pytest.raises(YuiError) as excinfo:
        #     source = Source("10")
        #     name_node = parse("@Name", source, pc={})
        # assert "expected" in str(excinfo.value)
        # assert excinfo.value.error_node.pos == 0
        # assert excinfo.value.error_node.end_pos == 1

    def test_statement_separator(self):
        source = Source("x = 1;y=2")
        source.update_syntax(**{
            "statement-separator": ";",
        })
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x = 1;y=2"

    def test_Block(self):
        source = Source("n回 {\n  x = 1\n  y=2\n} くり返す", pos=3)
        block_node = parse("@Block", source, pc={})
        assert str(block_node) == "{\n  x = 1\n  y=2\n}"

    def test_Repeat(self):
        source = Source("3回くり返す {\n  x = 1\n}")
        repeat_node = parse("@Repeat", source, pc={})
        assert str(repeat_node) == "3回くり返す {\n  x = 1\n}"


class aNode:


    def test_Block(self):
        source = Source("{\n  x = 1\n  y = 2\n}")
        block_node = parse("@Block", source, pc={})
        assert str(block_node) == "{\n  x = 1\n  y = 2\n}"

        with pytest.raises(YuiError) as excinfo:
            source = Source("  {\n    x = 1\n  y = 2\n  }", pos=2)
            block_node = parse("@Block", source, pc={})
        assert "indentation" in str(excinfo.value)
