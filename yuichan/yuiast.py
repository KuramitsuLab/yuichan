from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

OPERATORS = None

def set_operators(operators: dict):
    global OPERATORS
    OPERATORS = operators

@dataclass
class ASTNode(ABC):
    """抽象構文木（AST）の基底クラス"""
    filename: str
    source: str
    pos: int
    end_pos: int
    comment: Optional[str]

    def __init__(self):
        """ASTNodeを初期化する"""
        self.filename = "main.yui"
        self.source = ""
        self.pos = 0
        self.end_pos = -1
        self.comment = None

    def setpos(self, source: str, pos: int, end_pos: int = -1, filename: str = "main.yui"):
        self.source = source
        self.pos = pos
        self.end_pos = end_pos
        self.filename = filename
        self.comment = None
        return self
    
    def __str__(self) -> str:
        """ノードに対応するソースコードのスニペットを返す"""
        return self.source[self.pos:self.end_pos]

    def evaluate(self, runtime: 'YuiRuntime') -> 'YuiValue': # type: ignore
        return self.visit(runtime)

    def visit(self, visitor):
        """ノードを訪問する"""
        method_name = 'visit' + self.__class__.__name__
        visit = getattr(visitor, method_name, visitor.visitASTNode)
        return visit(self)
    
    def extract(self) -> tuple:
        """ソースコード内の位置をエラー表示用の情報に変換する

        Returns:
            tuple: (line, col, snippet)
                - line: 行番号（1始まり）
                - col: 列番号（1始まり）
                - snippet: エラー行のコードスニペット
        """
        linenum = 1
        col = 1
        start = 0

        # エラー位置まで文字を辿り、行番号と列番号を計算
        for i, char in enumerate(self.source):
            if i == self.pos:
                break
            if char == '\n':
                linenum += 1
                col = 1
                start = i + 1
            else:
                col += 1

        # エラー行の終端を見つける
        end_pos = self.source.find('\n', start)
        if end_pos == -1:
            end_pos = len(self.source)
        return linenum, col, self.source[start:end_pos]


@dataclass
class ExpressionNode(ASTNode):
    """式（Expression）の基底クラス"""
    def __init__(self):
        super().__init__()

def _node(node: Any) -> ASTNode:
    if node is None: return None
    if isinstance(node, (int, float)):
        return NumberNode(node)
    if isinstance(node, str):
        return StringNode(node)
    if isinstance(node, list):
        return ArrayNode([_node(e) for e in node])
    assert isinstance(node, ASTNode)
    return node

@dataclass
class ConstNode(ExpressionNode):
    """null/boolean値を表すノード (native_value: None, True, or False)"""
    native_value: Any  # None, True, or False

    def __init__(self, value=None):
        super().__init__()
        self.native_value = value

    def visit(self, visitor):
        return visitor.visitConstNode(self)


@dataclass
class NumberNode(ExpressionNode):
    """数値リテラルを表すノード"""
    native_value: Union[int, float]

    def __init__(self, value: Union[int, float]):
        super().__init__()
        self.native_value = value

    def visit(self, visitor):
        return visitor.visitNumberNode(self)

@dataclass
class ArrayLenNode(ExpressionNode):
    """配列の長さ（|配列|）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def visit(self, visitor):
        return visitor.visitArrayLenNode(self)

@dataclass
class MinusNode(ExpressionNode):
    """負の数（-式）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def visit(self, visitor):
        return visitor.visitMinusNode(self)

@dataclass
class StringNode(ExpressionNode):
    """文字列リテラル（"..."）を表すノード"""
    contents: Union[str, List[Union[str, ExpressionNode]]]

    def __init__(self, contents: Union[str, List[Union[str, ExpressionNode]]]):
        super().__init__()
        self.contents = contents

    def visit(self, visitor):
        return visitor.visitStringNode(self)

@dataclass
class ArrayNode(ExpressionNode):
    """配列リテラル（[要素, ...]）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [_node(e) for e in elements]

    def visit(self, visitor):
        return visitor.visitArrayNode(self)

@dataclass
class ObjectNode(ExpressionNode):
    """辞書リテラル（{要素, ...}）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [_node(e) for e in elements]

    def visit(self, visitor):
        return visitor.visitObjectNode(self)

@dataclass
class NameNode(ExpressionNode):
    """変数参照を表すノード"""
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def visit(self, visitor):
        return visitor.visitNameNode(self)
    
    def update(self, value, visitor):
        """変数の値を更新する"""
        visitor.setenv(self.name, value)

@dataclass
class GetIndexNode(ASTNode):
    """配列またはオブジェクトのインデックス取得を表すノード"""
    collection: ExpressionNode
    index_node: ExpressionNode

    def __init__(self, collection: ExpressionNode, index: ExpressionNode):
        super().__init__()
        self.collection = _node(collection)
        self.index_node = _node(index)

    def visit(self, visitor):
        return visitor.visitGetIndexNode(self)
    
    def update(self, value, visitor):
        """変数の値を更新する"""
        collection = self.collection.visit(visitor)
        index = self.index_node.visit(visitor)
        collection.set_item(index, value)

@dataclass
class BinaryNode(ASTNode):
    """二項演算子を表すノード"""
    left_node: ExpressionNode
    right_node: ExpressionNode
    operator: str
    comparative: bool

    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode, comparative: bool = False):
        super().__init__()
        self.left_node = _node(left)
        self.operator = operator
        self.right_node = _node(right)
        self.comparative = comparative

    # def evaluate(self, runtime):
    #     raise YuiError(("internal-error", f"🔍{self.operator} operator is not implemented"), self, runtime)

    def visit(self, visitor):
        return visitor.visitBinaryNode(self)

@dataclass
class FuncAppNode(ExpressionNode):
    """関数呼び出し（関数名(引数, ...)）を表すノード"""
    name: ExpressionNode
    arguments: List[ExpressionNode]
    snippet: str

    def __init__(self, name: ExpressionNode, arguments: List[ExpressionNode]):
        super().__init__()
        self.name_node = NameNode(name) if isinstance(name, str) else _node(name)
        self.arguments = [_node(arg) for arg in arguments]
        self.snippet = str(self)

    def visit(self, visitor):
        return visitor.visitFuncAppNode(self)


@dataclass
class StatementNode(ASTNode):
    """文（Statement）の基底クラス"""
    def __init__(self):
        super().__init__()

@dataclass
class AssignmentNode(StatementNode):
    """代入文（変数 = 式）を表すノード"""
    variable: NameNode
    expression: ExpressionNode

    def __init__(self, variable: NameNode, expression: ExpressionNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else _node(variable)
        self.expression = _node(expression)

    def visit(self, visitor):
        return visitor.visitAssignmentNode(self)

@dataclass
class IncrementNode(StatementNode):
    """インクリメント（変数 を 増やす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else _node(variable)

    def visit(self, visitor):
        return visitor.visitIncrementNode(self)

@dataclass
class DecrementNode(StatementNode):
    """デクリメント（変数 を 減らす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else _node(variable)

    def visit(self, visitor):
        return visitor.visitDecrementNode(self)

@dataclass
class AppendNode(StatementNode):
    """配列への追加（変数の末尾に 値 を 追加する）を表すノード"""
    variable: NameNode
    expression: ExpressionNode

    def __init__(self, variable: NameNode, expression: ExpressionNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else _node(variable)
        self.expression = _node(expression)

    def visit(self, visitor):
        return visitor.visitAppendNode(self)

@dataclass
class BlockNode(StatementNode):
    statements: List[StatementNode]
    top_level: bool

    def __init__(self, statements: List[StatementNode], top_level: bool = False):
        super().__init__()
        if isinstance(statements, StatementNode):
            self.statements = [statements]
        else:
            assert isinstance(statements, list)
            self.statements = statements
        self.top_level = top_level

    def visit(self, visitor):
        return visitor.visitBlockNode(self)

@dataclass
class IfNode(StatementNode):
    """条件分岐（もし〜ならば）を表すノード"""
    left: ExpressionNode
    operator: str  # "==", "!=", ">", "<", "!=", "in", "not in"
    right: ExpressionNode
    then_block: BlockNode
    else_block: Optional[BlockNode] = None

    def __init__(self, 
                 left: ExpressionNode, operator: str, right: ExpressionNode,
                 then_block: BlockNode, else_block: Optional[BlockNode] = None):
        super().__init__()
        self.left = _node(left)
        self.operator = OPERATORS[operator]
        self.right = _node(right)
        self.then_block = then_block
        self.else_block = else_block

    def visit(self, visitor):
        return visitor.visitIfNode(self)

@dataclass
class BreakNode(StatementNode):
    def __init__(self):
        super().__init__()

    def visit(self, visitor):
        return visitor.visitBreakNode(self)

@dataclass
class PassNode(StatementNode):
    def __init__(self, comment: Optional[str] = None):
        super().__init__()
        self.comment = comment

    def visit(self, visitor):
        return visitor.visitPassNode(self)

@dataclass
class RepeatNode(StatementNode):
    """ループ（N回 くり返す）を表すノード"""
    count: ExpressionNode
    body: BlockNode

    def __init__(self, count_node: ExpressionNode, block_node: BlockNode):
        super().__init__()
        self.count_node = _node(count_node)    
        self.block_node = block_node

    def visit(self, visitor):
        return visitor.visitRepeatNode(self)

@dataclass
class ImportNode(StatementNode):
    """ライブラリのインポート（標準ライブラリを使う）を表すノード"""
    module_name: str

    def __init__(self, module_name: str = None):
        super().__init__()
        self.module_name = NameNode(module_name) if isinstance(module_name, str) else _node(module_name)

    def visit(self, visitor):
        return visitor.visitImportNode(self)

@dataclass
class ReturnNode(StatementNode):
    """関数からの返値（式 が 答え）を表すノード"""
    expression: ExpressionNode

    def __init__(self, expression: ExpressionNode):
        super().__init__()
        self.expression = _node(expression)

    def visit(self, visitor):
        return visitor.visitReturnNode(self)

@dataclass
class FuncDefNode(StatementNode):
    """関数定義を表すノード"""
    name_node: NameNode
    parameters: List[NameNode]
    body: BlockNode

    def __init__(self, name_node: NameNode, parameters: List[NameNode], body: BlockNode):
        super().__init__()
        self.name_node = NameNode(name_node) if isinstance(name_node, str) else _node(name_node)
        self.parameters = [NameNode(param) if isinstance(param, str) else _node(param) for param in parameters]
        self.body = body

    def visit(self, visitor):
        return visitor.visitFuncDefNode(self)


@dataclass
class PrintExpressionNode(StatementNode):
    """式の出力（単独で書かれた式）を表すノード"""
    expression: ExpressionNode
    inspection: bool
    groping: bool = False

    def __init__(self, expression: ExpressionNode, inspection: bool = False, groping: bool = False):
        super().__init__()
        self.expression = _node(expression)
        self.inspection = inspection
        self.groping = groping

    def visit(self, visitor):
        return visitor.visitPrintExpressionNode(self)

@dataclass
class AssertNode(StatementNode):
    """テストケース（>>> 式 → 期待値）を表すノード"""
    test: ExpressionNode
    reference: ExpressionNode

    def __init__(self, test: ExpressionNode, reference: ExpressionNode):
        super().__init__()
        self.test = _node(test)
        self.reference = _node(reference)

    def visit(self, visitor):
        return visitor.visitAssertNode(self)


