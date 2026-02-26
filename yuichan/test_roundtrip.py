"""
Round-trip tests: generate code from yuiexample ASTs, then parse the
generated code back.  A test fails if parsing raises an exception.
"""
import pytest
from .yuiast import (
    ConstNode, NumberNode, StringNode,
    ArrayNode, ObjectNode,
    NameNode,
    MinusNode, ArrayLenNode, GetIndexNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode,
)

from .yuiparser import Source
from .yuisyntax import load_syntax
from .yuicoding import CodingVisitor
from .yuiruntime import YuiRuntime
from .yuitypes import types

SYNTAXES = ['yui', 'pylike', 'emoji']

_examples_by_name = {
    # ConstNode
    "null":  ConstNode(None),
    "true":  ConstNode(True),
    "false": ConstNode(False),
    # NumberNode
    "int":   NumberNode(42),
    "float": NumberNode(3.5),
    # MinusNode (negative literals) — regression for unary-minus not wrapping in MinusNode
    "minus_int":   MinusNode(NumberNode(16)),
    "minus_float": MinusNode(NumberNode(3.14)),
    # StringNode
    "empty_string": StringNode(""),
    "string": StringNode("hello"),
    # ArrayNode
    "empty_array": ArrayNode([]),
    "array": ArrayNode([NumberNode(1), NumberNode(2), NumberNode(3)]),
    # Assignment + read
    "assign": BlockNode([
        AssignmentNode(NameNode("x"), NumberNode(42)),
        PrintExpressionNode(NameNode("x")),
    ], top_level=True),
    # Assignment with negative value — regression for unary-minus in assignment RHS
    "assign_minus": BlockNode([
        AssignmentNode(NameNode("x"), MinusNode(NumberNode(5))),
        PrintExpressionNode(NameNode("x")),
    ], top_level=True),
    # Increment — regression for statement ordering (Increment must be tried before Assignment)
    "increment": BlockNode([
        AssignmentNode(NameNode("n"), NumberNode(0)),
        IncrementNode(NameNode("n")),
        PrintExpressionNode(NameNode("n")),
    ], top_level=True),
    # Decrement — same regression check
    "decrement": BlockNode([
        AssignmentNode(NameNode("n"), NumberNode(5)),
        DecrementNode(NameNode("n")),
        PrintExpressionNode(NameNode("n")),
    ], top_level=True),
    # Append
    "append": BlockNode([
        AssignmentNode(NameNode("A"), ArrayNode([NumberNode(1), NumberNode(2)])),
        AppendNode(NameNode("A"), NumberNode(3)),
        PrintExpressionNode(NameNode("A")),
    ], top_level=True),
    # Assert with negative reference value — regression for closest_integer("-15.5") bug:
    # the doctest reference "-16" was parsed as positive 16 when MinusNode was missing.
    "assert_minus_ref": BlockNode([
        AssignmentNode(NameNode("x"), MinusNode(NumberNode(16))),
        AssertNode(NameNode("x"), MinusNode(NumberNode(16))),
    ], top_level=True),
    # If (true branch)
    "if_true": BlockNode([
        AssignmentNode(NameNode("x"), NumberNode(5)),
        AssignmentNode(NameNode("y"), NumberNode(0)),
        IfNode(NameNode("x"), ">", NumberNode(3), IncrementNode(NameNode("y")), None),
        PrintExpressionNode(NameNode("y")),
    ], top_level=True),
    # Repeat
    "repeat": BlockNode([
        AssignmentNode(NameNode("s"), NumberNode(0)),
        RepeatNode(NumberNode(3), BlockNode([IncrementNode(NameNode("s"))])),
        PrintExpressionNode(NameNode("s")),
    ], top_level=True),
    # Variables: mix of assignment + increment, the exact case that exposed the ordering bug
    "variables": BlockNode([
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), MinusNode(NumberNode(2))),
        IncrementNode(NameNode("x")),
        DecrementNode(NameNode("y")),
        AssertNode(NameNode("x"), NumberNode(2)),
        AssertNode(NameNode("y"), MinusNode(NumberNode(3))),
    ], top_level=True),
}

_params = [
    pytest.param(syntax_name, name, id=f"{syntax_name}/{name}")
    for syntax_name in SYNTAXES
    for name in _examples_by_name
]

@pytest.mark.parametrize("syntax_name,example_name", _params)
def test_generate_then_parse(syntax_name, example_name):
    """Generate code from an example AST and verify it can be parsed back."""
    syntax = load_syntax(syntax_name)
    
    node = _examples_by_name[example_name]
    rumtime = YuiRuntime()
    value = types.unbox(node.evaluate(rumtime))

    visitor = CodingVisitor(syntax)
    code = visitor.emit(node)

    source = Source(code, syntax=syntax)
    node2 = source.parse("@TopLevel")
    value2 = types.unbox(node2.evaluate(rumtime))
    assert value == value2
