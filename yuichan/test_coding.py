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
from .yuicoding import CodingVisitor
from .yuisyntax import load_syntax

yui_syntax = load_syntax('yui')

class TestCodeGeneration:
    """Yuiコード生成に関するテストクラス"""

    def init_coder(self):
        return CodingVisitor(syntax_json=yui_syntax)

    def test_ConstNode_null(self):
        emitter = self.init_coder()
        assert emitter.emit(ConstNode(None)) == '値なし'

    def test_ConstNode_true(self):
        emitter = self.init_coder()
        assert emitter.emit(ConstNode(True)) == '真'

    def test_ConstNode_false(self):
        emitter = self.init_coder()
        assert emitter.emit(ConstNode(False)) == '偽'

    def test_NumberNode(self):
        node = NumberNode(123)
        emitter = self.init_coder()
        assert emitter.emit(node) == '123'

    def test_StringNode(self):
        node = StringNode("hello")
        emitter = self.init_coder()
        assert emitter.emit(node) == '"hello"'

    def test_ArrayNode(self):
        node = ArrayNode([NumberNode(1), NumberNode(2), NumberNode(3)])
        emitter = self.init_coder()
        assert emitter.emit(node) == '[1,2,3]'

    def test_ObjectNode(self):
        node = ObjectNode([
            StringNode("a"), NumberNode(1),
            StringNode("b"), StringNode("two"),
        ])
        emitter = self.init_coder()
        assert emitter.emit(node) == '{"a":1,"b":"two"}'

    def test_MinusNode(self):
        node = MinusNode(NumberNode(5))
        emitter = self.init_coder()
        assert emitter.emit(node) == '-5'
    
    def test_ArrayLenNode(self):
        node = ArrayLenNode(NameNode("arr"))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'arrの大きさ'
    
    def test_GetIndexNode(self):
        node = GetIndexNode(NameNode("arr"), NumberNode(2))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'arr[2]'
    
    def test_AssignmentNode(self):
        node = AssignmentNode(NameNode("x"), NumberNode(10))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'x = 10'

    def test_IncrementNode(self):
        node = IncrementNode(NameNode("x"))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'xを増やす'

    def test_DecrementNode(self):
        node = DecrementNode(NameNode("x"))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'xを減らす'

    def test_AppendNode(self):
        node = AppendNode(NameNode("arr"), NumberNode(10))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'arrに10を追加する'

    def test_BreakNode(self):
        node = BreakNode()
        emitter = self.init_coder()
        assert emitter.emit(node) == 'くり返しを抜ける'

    def test_ReturnNode(self):
        node = ReturnNode(NameNode("result"))
        emitter = self.init_coder()
        assert emitter.emit(node) == 'resultが答え'

    def test_PrintExpressionNode(self):
        node = PrintExpressionNode(StringNode("Hello, World!"))
        emitter = self.init_coder()
        assert emitter.emit(node) == '"Hello, World!"'

    def test_BlockNode(self):
        node = BlockNode([
            AssignmentNode(NameNode("x"), NumberNode(1)),
            AssignmentNode(NameNode("y"), NumberNode(2)),
        ], top_level=True)
        emitter = self.init_coder()
        assert emitter.emit(node) == 'x = 1\ny = 2'