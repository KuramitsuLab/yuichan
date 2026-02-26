import pytest
from .yuiparser import Source
from .yuiast import ConstNode
from .yuitypes import YuiError
from .yuisyntax import load_syntax

yui_syntax = load_syntax('yui')


class TestParseStatementNode_Yui:

    def test_Assignment(self):
        source = Source("x = 1 # コメント")
        assignment_node = source.parse("@Assignment")
        assert str(assignment_node) == "x = 1"

    def test_AssignmentAsStatement(self):
        source = Source("x=1 # コメント")
        assignment_node = source.parse("@Statement")
        assert str(assignment_node) == "x=1"

    def test_Increment(self):
        source = Source("xを増やす")
        increment_node = source.parse("@Increment")
        assert str(increment_node) == "xを増やす"

        source = Source("xを増やす # コメント")
        increment_node = source.parse("@Statement")
        assert str(increment_node) == "xを増やす"

    def test_Increment_lookahead_error(self):
        source = Source("xに3増やす # コメント")
        with pytest.raises(YuiError) as excinfo:
            increment_node = source.parse("@Statement")
        assert "expected" in str(excinfo.value)

    def test_Decrement(self):
        source = Source("xを減らす")
        decrement_node = source.parse("@Decrement")
        assert str(decrement_node) == "xを減らす"

        source = Source("yを減らす # コメント")
        decrement_node = source.parse("@Statement")
        assert str(decrement_node) == "yを減らす"

    def test_Append(self):
        source = Source("xに10を追加する")
        append_node = source.parse("@Append")
        assert str(append_node) == "xに10を追加する"

        source = Source("xに10を追加する # コメント")
        append_node = source.parse("@Statement")
        assert str(append_node) == "xに10を追加する"

    def test_Append_with_tail(self):
        source = Source("xの末尾に10を追加する")
        append_node = source.parse("@Append")
        assert str(append_node) == "xの末尾に10を追加する"

        source = Source("xの末尾に10を追加する # コメント")
        append_node = source.parse("@Statement")
        assert str(append_node) == "xの末尾に10を追加する"


    def test_Break(self):
        source = Source("くり返しを抜ける")
        break_node = source.parse("@Break")
        assert str(break_node) == "くり返しを抜ける"

    def test_Return(self):
        source = Source("1が答え")
        return_node = source.parse("@Return")
        assert str(return_node) == "1が答え"

        source = Source("1が答え # コメント")
        return_node = source.parse("@Return")
        assert str(return_node) == "1が答え"

    def test_FuncDef_with_arg(self):
        source = Source("f = 入力x に対して {\n  xが答え\n}")
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "f = 入力x に対して {\n  xが答え\n}"

    def test_FuncDef_no_arg(self):
        source = Source("f = 入力なし に対して {\n  1が答え\n}")
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "f = 入力なし に対して {\n  1が答え\n}"

    def test_FuncDef_multiple_args(self):
        source = Source("f = 入力x,y に対して {\n  xが答え\n}")
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "f = 入力x,y に対して {\n  xが答え\n}"


class TestParseBlockNode_Yui:

    def test_TopLevel(self):
        source = Source("x = 1\ny=2")
        top_level_node = source.parse("@TopLevel")
        assert str(top_level_node) == "x = 1\ny=2"

    def test_statement_separator(self):
        source = Source("x = 1;y=2")
        source.update_syntax(**{
            "statement-separator": ";",
        })
        top_level_node = source.parse("@TopLevel")
        assert str(top_level_node) == "x = 1;y=2"

    def test_TopLevel_error(self):
        with pytest.raises(YuiError) as excinfo:
            source = Source("x = 1 知らないよ")
            top_level_node = source.parse("@TopLevel")
        assert "wrong" in str(excinfo.value)
        assert "statement" in str(excinfo.value)

    def test_Block(self):
        source = Source("n回 {\n  x = 1\n  y=2\n} くり返す", pos=3)
        block_node = source.parse("@Block")
        assert str(block_node) == "{\n  x = 1\n  y=2\n}"

    def test_Block_emptyline(self):
        source = Source("n回 {\n  x = 1\n #a\n\n  y=2\n} くり返す", pos=3)
        block_node = source.parse("@Block")
        assert str(block_node) == "{\n  x = 1\n #a\n\n  y=2\n}"

    def test_Repeat(self):
        source = Source("3回くり返す {\n  x = 1\n}")
        repeat_node = source.parse("@Repeat")
        assert str(repeat_node) == "3回くり返す {\n  x = 1\n}"

    def test_If(self):
        source = Source("もしxが1ならば {\n  x = 1\n}")
        if_node = source.parse("@If")
        assert str(if_node) == "もしxが1ならば {\n  x = 1\n}"

    def test_IfAsStatement(self):
        source = Source("もしxが1ならば {\n  x = 1\n}")
        if_node = source.parse("@Statement")
        assert str(if_node) == "もしxが1ならば {\n  x = 1\n}"

    def test_If_in(self):
        source = Source("もしxがAのいずれかならば{\n  x = 1\n}")
        if_node = source.parse("@If")
        assert str(if_node) == "もしxがAのいずれかならば{\n  x = 1\n}"

    def test_If_not_in(self):
        source = Source("もしxがAのいずれでもないならば{\n  x = 1\n}")
        if_node = source.parse("@If")
        assert str(if_node) == "もしxがAのいずれでもないならば{\n  x = 1\n}"

    def test_NestedIf(self):
        source = Source("もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1")
        if_node = source.parse("@If")
        assert str(if_node) == "もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}"

    def test_NestedIfAsTopLevel(self):
        source = Source("もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1")
        if_node = source.parse("@TopLevel")
        assert str(if_node) == "もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1"

    def test_Repeat_with_break(self):
        source = Source("10回くり返す{\n   countを増やす\n   もし countが 5ならば{\n      くり返しを抜ける\n   }\n}")
        repeat_node = source.parse("@Repeat")
        assert "くり返しを抜ける" in str(repeat_node)


class TestParseConstNode_Yui:

    def test_null(self):
        source = Source("値なし")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is None
        assert str(node) == "値なし"

    def test_null_english(self):
        source = Source("null")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is None
        assert str(node) == "null"

    def test_true(self):
        source = Source("真")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is True
        assert str(node) == "真"

    def test_true_english(self):
        source = Source("true")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is True
        assert str(node) == "true"

    def test_false(self):
        source = Source("偽")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is False
        assert str(node) == "偽"

    def test_false_english(self):
        source = Source("false")
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is False
        assert str(node) == "false"

    def test_null_as_term(self):
        source = Source("値なし")
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is None

    def test_true_as_term(self):
        source = Source("真")
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is True

    def test_false_as_term(self):
        source = Source("偽")
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is False

    def test_null_in_assignment(self):
        source = Source("x = 値なし")
        node = source.parse("@Assignment")
        assert str(node) == "x = 値なし"

    def test_true_in_assignment(self):
        source = Source("x = 真")
        node = source.parse("@Assignment")
        assert str(node) == "x = 真"
