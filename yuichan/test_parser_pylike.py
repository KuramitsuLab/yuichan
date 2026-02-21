import pytest
from .yuiparser import Source, parse
from .yuiast import ConstNode
from .yuitypes import YuiError
from .yuisyntax import load_syntax

py_syntax = load_syntax('pylike')


class TestParseStatementNode_Pylike:

    def test_Assignment(self):
        source = Source("x = 1 # コメント", syntax=py_syntax)
        assignment_node = parse("@Assignment", source, pc={})
        assert str(assignment_node) == "x = 1"

    def test_AssignmentAsStatement(self):
        source = Source("x=1 # コメント", syntax=py_syntax)
        assignment_node = parse("@Statement", source, pc={})
        assert str(assignment_node) == "x=1"

    def test_Increment(self):
        source = Source("x += 1", syntax=py_syntax)
        increment_node = parse("@Increment", source, pc={})
        assert str(increment_node) == "x += 1"

        source = Source("y += 1", syntax=py_syntax)
        increment_node = parse("@Statement", source, pc={})
        assert str(increment_node) == "y += 1"

    def test_Decrement(self):
        source = Source("x -= 1", syntax=py_syntax)
        decrement_node = parse("@Decrement", source, pc={})
        assert str(decrement_node) == "x -= 1"

        source = Source("y -= 1 # コメント", syntax=py_syntax)
        decrement_node = parse("@Statement", source, pc={})
        assert str(decrement_node) == "y -= 1"

    def test_Append(self):
        source = Source("x.append(10)", syntax=py_syntax)
        append_node = parse("@Append", source, pc={})
        assert str(append_node) == "x.append(10)"

        source = Source("x.append(10) # コメント", syntax=py_syntax)
        append_node = parse("@Statement", source, pc={})
        assert str(append_node) == "x.append(10)"

    def test_Break(self):
        source = Source("break", syntax=py_syntax)
        break_node = parse("@Break", source, pc={})
        assert str(break_node) == "break"

    def test_Return(self):
        source = Source("return 1 # コメント", syntax=py_syntax)
        return_node = parse("@Return", source, pc={})
        assert str(return_node) == "return 1"

        source = Source("return 1", syntax=py_syntax)
        return_node = parse("@Statement", source, pc={})
        assert str(return_node) == "return 1"

    def test_FuncDef(self):
        source = Source("def f(x):\n  return x\n\n", syntax=py_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "def f(x):\n  return x\n\n"

    def test_FuncDef_no_args(self):
        source = Source("def f():\n  return 1\n\n", syntax=py_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "def f():\n  return 1\n\n"

    def test_FuncDef_multiple_args(self):
        source = Source("def f(x, y):\n  return x\n\n", syntax=py_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "def f(x, y):\n  return x\n\n"


class TestParseBlockNode_Pylike:

    def test_TopLevel(self):
        source = Source("x = 1\ny=2", syntax=py_syntax)
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x = 1\ny=2"

    def test_If(self):
        source = Source("if x==1:\n  x=1\n\n", syntax=py_syntax)
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "if x==1:\n  x=1\n\n"

    def test_IfAsStatement(self):
        source = Source("if x==1:\n  x=1\n\ny=2", syntax=py_syntax)
        if_node = parse("@Statement", source, pc={})
        assert str(if_node) == "if x==1:\n  x=1\n\n"

    def test_NestedIf(self):
        source = Source("if x==1:\n  x=0\n  if x==0:\n    x=1\n\n", syntax=py_syntax)
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "if x==1:\n  x=0\n  if x==0:\n    x=1\n\n"

    def test_NestedIfAsTopLevel(self):
        source = Source("if x==1:\n  x=0\n  if x==0:\n    x=1\n\ny=2", syntax=py_syntax)
        if_node = parse("@TopLevel", source, pc={})
        assert str(if_node) == "if x==1:\n  x=0\n  if x==0:\n    x=1\n\ny=2"

    def test_Repeat(self):
        source = Source("for _ in range(3):\n  x=1\n\n", syntax=py_syntax)
        repeat_node = parse("@Repeat", source, pc={})
        assert str(repeat_node) == "for _ in range(3):\n  x=1\n\n"

    def test_Repeat_with_break(self):
        source = Source("for _ in range(10):\n  count += 1\n  if count==5:\n    break\n\n", syntax=py_syntax)
        repeat_node = parse("@Repeat", source, pc={})
        assert "break" in str(repeat_node)


class TestParseConstNode_Pylike:

    def test_null(self):
        source = Source("None", syntax=py_syntax)
        node = parse("@Boolean", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is None
        assert str(node) == "None"

    def test_true(self):
        source = Source("True", syntax=py_syntax)
        node = parse("@Boolean", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is True
        assert str(node) == "True"

    def test_false(self):
        source = Source("False", syntax=py_syntax)
        node = parse("@Boolean", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is False
        assert str(node) == "False"

    def test_null_as_term(self):
        source = Source("None", syntax=py_syntax)
        node = parse("@Term", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is None

    def test_true_as_term(self):
        source = Source("True", syntax=py_syntax)
        node = parse("@Term", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is True

    def test_false_as_term(self):
        source = Source("False", syntax=py_syntax)
        node = parse("@Term", source, pc={})
        assert isinstance(node, ConstNode)
        assert node.native_value is False

    def test_null_in_assignment(self):
        source = Source("x = None", syntax=py_syntax)
        node = parse("@Assignment", source, pc={})
        assert str(node) == "x = None"

    def test_true_in_assignment(self):
        source = Source("x = True", syntax=py_syntax)
        node = parse("@Assignment", source, pc={})
        assert str(node) == "x = True"
