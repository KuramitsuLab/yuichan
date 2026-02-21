import pytest
from .yuiparser import Source, parse
from .yuitypes import YuiError
from .yuisyntax import load_syntax

yui_syntax = load_syntax('yui')


class TestParseStatementNode_Yui:

    def test_Assignment(self):
        source = Source("x = 1 # コメント")
        assignment_node = parse("@Assignment", source, pc={})
        assert str(assignment_node) == "x = 1"

    def test_AssignmentAsStatement(self):
        source = Source("x=1 # コメント")
        assignment_node = parse("@Statement", source, pc={})
        assert str(assignment_node) == "x=1"

    def test_Increment(self):
        source = Source("xを増やす")
        increment_node = parse("@Increment", source, pc={})
        assert str(increment_node) == "xを増やす"

        source = Source("xを増やす # コメント")
        increment_node = parse("@Statement", source, pc={})
        assert str(increment_node) == "xを増やす"

    def test_Increment_lookahead_error(self):
        source = Source("xに3増やす # コメント")
        with pytest.raises(YuiError) as excinfo:
            increment_node = parse("@Statement", source, pc={})
        assert "expected" in str(excinfo.value)

    def test_Decrement(self):
        source = Source("xを減らす")
        decrement_node = parse("@Decrement", source, pc={})
        assert str(decrement_node) == "xを減らす"

        source = Source("yを減らす # コメント")
        decrement_node = parse("@Statement", source, pc={})
        assert str(decrement_node) == "yを減らす"

    def test_Append(self):
        source = Source("xに10を追加する")
        append_node = parse("@Append", source, pc={})
        assert str(append_node) == "xに10を追加する"

        source = Source("xに10を追加する # コメント")
        append_node = parse("@Statement", source, pc={})
        assert str(append_node) == "xに10を追加する"

    def test_Break(self):
        source = Source("くり返しを抜ける")
        break_node = parse("@Break", source, pc={})
        assert str(break_node) == "くり返しを抜ける"

    def test_Return(self):
        source = Source("1が答え")
        return_node = parse("@Return", source, pc={})
        assert str(return_node) == "1が答え"

        source = Source("1が答え # コメント")
        return_node = parse("@Return", source, pc={})
        assert str(return_node) == "1が答え"

    def test_FuncDef_with_arg(self):
        source = Source("f = 入力x に対して {\n  xが答え\n}")
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "f = 入力x に対して {\n  xが答え\n}"

    def test_FuncDef_no_arg(self):
        source = Source("f = 入力なし に対して {\n  1が答え\n}")
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "f = 入力なし に対して {\n  1が答え\n}"

    def test_FuncDef_multiple_args(self):
        source = Source("f = 入力x,y に対して {\n  xが答え\n}")
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "f = 入力x,y に対して {\n  xが答え\n}"


class TestParseBlockNode_Yui:

    def test_TopLevel(self):
        source = Source("x = 1\ny=2")
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x = 1\ny=2"

    def test_statement_separator(self):
        source = Source("x = 1;y=2")
        source.update_syntax(**{
            "statement-separator": ";",
        })
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x = 1;y=2"

    def test_TopLevel_error(self):
        with pytest.raises(YuiError) as excinfo:
            source = Source("x = 1 知らないよ")
            top_level_node = parse("@TopLevel", source, pc={})
        assert "wrong" in str(excinfo.value)
        assert "statement" in str(excinfo.value)

    def test_Block(self):
        source = Source("n回 {\n  x = 1\n  y=2\n} くり返す", pos=3)
        block_node = parse("@Block", source, pc={})
        assert str(block_node) == "{\n  x = 1\n  y=2\n}"

    def test_Block_emptyline(self):
        source = Source("n回 {\n  x = 1\n #a\n\n  y=2\n} くり返す", pos=3)
        block_node = parse("@Block", source, pc={})
        assert str(block_node) == "{\n  x = 1\n #a\n\n  y=2\n}"

    def test_Repeat(self):
        source = Source("3回くり返す {\n  x = 1\n}")
        repeat_node = parse("@Repeat", source, pc={})
        assert str(repeat_node) == "3回くり返す {\n  x = 1\n}"

    def test_If(self):
        source = Source("もしxが1ならば {\n  x = 1\n}")
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "もしxが1ならば {\n  x = 1\n}"

    def test_IfAsStatement(self):
        source = Source("もしxが1ならば {\n  x = 1\n}")
        if_node = parse("@Statement", source, pc={})
        assert str(if_node) == "もしxが1ならば {\n  x = 1\n}"

    def test_If_in(self):
        source = Source("もしxがAのいずれかならば{\n  x = 1\n}")
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "もしxがAのいずれかならば{\n  x = 1\n}"

    def test_If_not_in(self):
        source = Source("もしxがAのいずれでもないならば{\n  x = 1\n}")
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "もしxがAのいずれでもないならば{\n  x = 1\n}"

    def test_NestedIf(self):
        source = Source("もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1")
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}"

    def test_NestedIfAsTopLevel(self):
        source = Source("もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1")
        if_node = parse("@TopLevel", source, pc={})
        assert str(if_node) == "もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1"

    def test_Repeat_with_break(self):
        source = Source("10回くり返す{\n   countを増やす\n   もし countが 5ならば{\n      くり返しを抜ける\n   }\n}")
        repeat_node = parse("@Repeat", source, pc={})
        assert "くり返しを抜ける" in str(repeat_node)
