import pytest

from .yuiast import (
    ConstNode, NumberNode, StringNode,
    ArrayNode, ObjectNode,
    NameNode,BinaryNode,
    MinusNode, ArrayLenNode, GetIndexNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode,
)
from .yuicoding import CodingVisitor
from .yuisyntax import load_syntax

yui_syntax = load_syntax('yui')

testcases = {
    # ConstNode
    "null":  (ConstNode(None),'値なし'),
    "true":  (ConstNode(True),'真'),
    "false": (ConstNode(False),'偽'),
    # NumberNode
    "123": (NumberNode(123), '123'),
    # StringNode
    '"hello"': (StringNode("hello"), '"hello"'),
    # ArrayNode
    "[1,2,3]": (ArrayNode([NumberNode(1), NumberNode(2), NumberNode(3)]), '[1,2,3]'),
    # ObjectNode
    '{"a":1,"b":"two"}': (ObjectNode([
        StringNode("a"), NumberNode(1),
        StringNode("b"), StringNode("two"),
    ]), '{"a":1,"b":"two"}'),
    # MinusNode
    "-5": (MinusNode(NumberNode(5)), '-5'),
    # ArrayLenNode
    "arr.length": (ArrayLenNode(NameNode("arr")), 'arrの大きさ'),
    # GetIndexNode
    "arr[2]": (GetIndexNode(NameNode("arr"), NumberNode(2)), 'arr[2]'),
    # PrintExpressionNode with inspection
    "inspect(a)": (PrintExpressionNode(NameNode("a"), inspection=True), '👀a'),
    # BinaryNode
    "1+2": (BinaryNode("+", 1, 2), '1+2'),
    "3*4": (BinaryNode("*", 3, 4), '3*4'),
    "1+2*3": (BinaryNode("+", 1, BinaryNode("*", 2, 3)), '1+2*3'),
    "(1+2)*3": (BinaryNode("*", BinaryNode("+", 1, 2), 3), '(1+2)*3'),
    "1-2-3": (BinaryNode("-", BinaryNode("-", 1, 2), 3), '1-2-3'),
    "1-(2-3)": (BinaryNode("-", 1, BinaryNode("-", 2, 3)), '1-(2-3)'),
    # AssignmentNode
    "x=10": (AssignmentNode(NameNode("x"), NumberNode(10)), 'x=10'),
    # IncrementNode
    "x++": (IncrementNode(NameNode("x")), 'xを増やす'),
    # DecrementNode
    "x--": (DecrementNode(NameNode("x")), 'xを減らす'),
    # AppendNode
    "arr.push(10)": (AppendNode(NameNode("arr"), NumberNode(10)), 'arrに10を追加する'),
    # BreakNode
    "break": (BreakNode(), 'くり返しを抜ける'),
    # ReturnNode
    "return result": (ReturnNode(NameNode("result")), 'resultが答え'),
    # PrintExpressionNode
    'print "Hello, World!"': (PrintExpressionNode(StringNode("Hello, World!")), '"Hello, World!"'),   
    # BlockNode
    "{ x=1; y=2; }": (BlockNode([
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(2)),
    ], top_level=True), 'x=1\ny=2'),
}

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_coding(name):
    node, expected = testcases[name]
    coder = CodingVisitor(syntax_json=yui_syntax)
    assert coder.emit(node) == expected

