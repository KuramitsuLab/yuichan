from dataclasses import dataclass
import time
from typing import List, Optional, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod

from .yuitypes import (
    YuiValue, YuiType, YuiError, ASTNode,
    OPERATORS,
)

YuiParser = None  # 循環インポート防止のため、後で設定されます
CodeVisitor = None  # 循環インポート防止のため、後で設定されます

from .message import to_message as _to_message

def set_from_outside(parser, visitor):
    global YuiParser
    global CodeVisitor
    YuiParser = parser
    CodeVisitor = visitor

class YuiRuntime(object):
    """Yui言語のランタイムシステム
    プログラムの実行を制御し、以下の機能を提供します：
    - プログラムのパースと実行
    - タイムアウト制御
    - 実行統計の収集（インクリメント、デクリメント、比較の回数）
    - 再帰呼び出しの追跡
    """

    environments: List[dict]
    filesystems: Dict[str, str]  # 仮想ファイルシステム
    call_frames: List[tuple]  # (func_name, args, pos, end_pos)
    increment_count: int
    decrement_count: int
    compare_count: int
    test_passed: List[str]
    test_failed: List[tuple]
    source: str

    def __init__(self, init_env: Dict[str, Any] = None):
        """YuiRuntimeを初期化する"""
        self.environments = [{} if init_env is None else init_env]
        self.filesystems = {}
        self.call_frames = []
        
        self.shouldStop = False
        self.timeout = 0
        self.interactive_mode = False
        self.source = ""
        self.reset_stats()

    def reset_stats(self):
        """実行統計をリセットする"""
        self.increment_count = 0
        self.decrement_count = 0
        self.compare_count = 0
        self.test_passed = []

    def hasenv(self, name) -> bool:
        """現在の環境に変数が存在するか確認する"""
        for env in reversed(self.environments):
            if name in env:
                return True
        return False

    def getenv(self, name) -> Any:
        """現在の環境から変数を取得する"""
        for env in reversed(self.environments):
            if name in env:
                return env[name]
        return None

    def setenv(self, name, value) -> Any:
        """現在の環境に変数を設定する"""
        self.environments[-1][name] = value  

    def pushenv(self):
        """現在の環境に変数を設定する"""
        self.environments.append({})

    def popenv(self):
        """現在の環境に変数を設定する"""
        return self.environments.pop()
    
    def stringfy_env(self, stack=-1, indent_prefix: str = "") -> str:
        """環境をJSON形式の文字列として出力する"""
        if indent_prefix is None:
            indent_prefix = ""
            inner_indent_prefix = None
            LF = ""
        else:
            inner_indent_prefix = indent_prefix + "  "
            LF = "\n"
        lines = [f"{indent_prefix}<{self.stringfy_call_frames(stack=stack)}>{LF}{{"]
        for i, (key, value) in enumerate(self.environments[stack].items()):
            if key.startswith("@"): continue 
            lines.append(f"{LF}{indent_prefix}  \"{key}\": ")
            lines.append(f"{YuiValue.stringfy_value(value, inner_indent_prefix)}")
            if i < len(self.environments[stack]) - 1:
                lines.append(", ")
        lines.append(f"{LF}{indent_prefix}}}")
        return ''.join(lines)

    def push_call_frame(self, func_name: str, args: List[Any], node):
        """関数呼び出しフレームをスタックに追加"""
        self.call_frames.append((func_name, args, node))

    def pop_call_frame(self):
        """関数呼び出しフレームをスタックから削除"""
        self.call_frames.pop()

    def stringfy_call_frames(self, stack=-1)->str:
        """スタックトレースを文字列として出力する"""
        if len(self.call_frames) == 0:
            return "global"
        call_frame = self.call_frames[stack]
        args = ", ".join(YuiValue.stringfy_value(arg, indent_prefix=None) for arg in call_frame[1])
        return f"{call_frame[0]}({args})]"

    def check_recursion_depth(self):
        """再帰呼び出しの深さをチェック"""
        if len(self.call_frames) > 512:
            args = ", ".join(str(arg) for arg in self.call_frames[-1][1])
            snippet = f"{self.call_frames[-1][0]}({args})"
            raise YuiError(("error", "recursion", f"🔍{snippet}"), self.call_frames[-1][2], self)

    def update_variable(self, name: str, env: Dict[str, Any], pos: int):
        """変数更新時のフック（サブクラスでオーバーライド可能）"""
        pass

    def count_inc(self):
        """インクリメント操作のカウントを増やす"""
        self.increment_count += 1

    def count_dec(self):
        """デクリメント操作のカウントを増やす"""
        self.decrement_count += 1

    def count_compare(self):
        """比較操作のカウントを増やす"""
        self.compare_count += 1

    def exec(self, source: str, syntax: Union[str,dict] = 'yui', timeout: int = 30, eval_mode: bool = True):
        """Yuiプログラムを実行する"""
        self.source = source

        # パースして実行
        parser = YuiParser()
        program = parser.parse(source)
        self.start(timeout)
        value = program.evaluate(self)

        # 結果を返す
        return YuiType.yui_to_native(value) if eval_mode else self.environments[-1]

    def load(self, function: FunctionType):
        """Python関数をYui関数として読み込む"""
        return NativeFunction(function)

    def print(self, value: Any, node: 'ASTNode'):
        """値を出力する"""
        line, _, snippet = node.extract()
        if self.interactive_mode or isinstance(node, StringNode):
            print(f"{value}")
        elif isinstance(node, FuncAppNode):
            print(f"#line: {line} {snippet.strip()}\n>>> {node.snippet}\n{value}")
        else:
            print(f"#line: {line}\n>>> {snippet.strip()}\n{value}")

    def start(self, timeout: int = 30):
        """実行を開始する"""
        self.shouldStop = False
        self.timeout = timeout
        self.startTime = time.time()

    def check_execution(self, node):
        """実行状態をチェックする"""
        # 手動停止フラグのチェック
        if self.shouldStop:
            raise YuiError(('interruptted'), node, self)

        # タイムアウトチェック
        if self.timeout > 0 and (time.time() - self.startTime) > self.timeout:
            raise YuiError(("error", "timeout", f"❌{self.timeout}[sec]", f"✅{self.timeout}[sec]"), node, self)
    
@dataclass
class ExpressionNode(ASTNode):
    """式（Expression）の基底クラス"""
    def __init__(self):
        super().__init__()

def node(node: Any) -> ASTNode:
    if node is None: return None
    if isinstance(node, (int, float)):
        return NumberNode(node)
    if isinstance(node, str):
        return StringNode(node)
    if isinstance(node, list):
        return ArrayNode([node(e) for e in node])
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

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiValue]:
        if self.native_value is True:
            self.evaluated_value = YuiValue.TrueValue
        elif self.native_value is False:
            self.evaluated_value = YuiValue.FalseValue
        else:
            self.evaluated_value = YuiValue.NullValue
        return self.evaluated_value

@dataclass
class NumberNode(ExpressionNode):
    """数値リテラルを表すノード"""
    native_value: Union[int, float]

    def __init__(self, value: Union[int, float]):
        super().__init__()
        self.native_value = value

    def visit(self, visitor):
        return visitor.visitNumberNode(self)

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiValue]:
        """数値を返す"""
        self.evaluated_value = YuiValue(self.native_value)
        return self.evaluated_value

@dataclass
class ArrayLenNode(ExpressionNode):
    """配列の長さ（|配列|）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def visit(self, visitor):
        return visitor.visitArrayLenNode(self)

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiValue]:
        """配列の長さを返す"""
        value = self.element.evaluate(runtime)
        self.evaluated_value = YuiValue(len(value.arrayview))
        return self.evaluated_value

@dataclass
class MinusNode(ExpressionNode):
    """負の数（-式）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def visit(self, visitor):
        return visitor.visitMinusNode(self)

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiValue]:
        """式を評価して符号を反転する"""
        self.element.evaluate(runtime)
        YuiType.NumberType.match_or_raise(self.element, runtime)
        value = YuiType.matched_native(self.element)
        self.evaluated_value = YuiValue(-value)
        return self.evaluated_value

@dataclass
class StringNode(ExpressionNode):
    """文字列リテラル（"..."）を表すノード"""
    contents: Union[str, List[Union[str, ExpressionNode]]]

    def __init__(self, contents: Union[str, List[Union[str, ExpressionNode]]]):
        super().__init__()
        self.contents = contents

    def visit(self, visitor):
        return visitor.visitStringNode(self)

    def evaluate(self, runtime: YuiRuntime) -> YuiValue:
        if isinstance(self.contents, str):
            self.evaluated_value = YuiValue(self.contents)
            return self.evaluated_value
        string_values = []
        for content in self.contents:
            if isinstance(content, str):
                string_values.append(content)
            else: # string埋め込み式
                value = content.evaluate(runtime)
                value = YuiType.yui_to_native(value)
                string_values.append(f'{value}')
        self.evaluated_value = YuiValue(''.join(string_values))
        return self.evaluated_value

@dataclass
class ArrayNode(ExpressionNode):
    """配列リテラル（[要素, ...]）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [node(e) for e in elements]

    def visit(self, visitor):
        return visitor.visitArrayNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """各要素を評価してYuiValueを作成する"""
        array_value = YuiValue([])
        for element in self.elements:
            element.evaluate(runtime)
            array_value.append(element, runtime)
        self.evaluated_value = array_value
        return self.evaluated_value

@dataclass
class ObjectNode(ExpressionNode):
    """辞書リテラル（{要素, ...}）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [node(e) for e in elements]

    def visit(self, visitor):
        return visitor.visitObjectNode(self)

    def evaluate(self, runtime: YuiRuntime) -> YuiValue:
        """各要素を評価してYuiValueを作成する"""
        object_value = YuiValue({})
        for i in range(0, len(self.elements), 2):
            self.elements[i].evaluate(runtime)
            self.elements[i+1].evaluate(runtime)
            object_value.set_item(self.elements[i], self.elements[i+1], runtime)
        self.evaluated_value = object_value
        return self.evaluated_value

@dataclass
class NameNode(ExpressionNode):
    """変数参照を表すノード"""
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def visit(self, visitor):
        return visitor.visitNameNode(self)

    def evaluate(self, runtime: YuiRuntime)-> YuiValue:
        """変数の値を返す（インデックスがあれば配列要素を返す）"""
        if not runtime.hasenv(self.name):
            raise YuiError(("undefined", "variable", f"❌{self.name}"), self, runtime)
        self.evaluated_value = runtime.getenv(self.name)
        return self.evaluated_value
    
    def update(self, value_node: ASTNode, runtime: YuiRuntime):
        """変数の値を更新する"""
        runtime.setenv(self.name, YuiType.evaluated(value_node))

@dataclass
class GetIndexNode(ASTNode):
    """配列またはオブジェクトのインデックス取得を表すノード"""
    collection: ExpressionNode
    index_node: ExpressionNode

    def __init__(self, collection: ExpressionNode, index: ExpressionNode):
        super().__init__()
        self.collection = node(collection)
        self.index_node = node(index)

    def visit(self, visitor):
        return visitor.visitGetIndexNode(self)

    def evaluate(self, runtime: YuiRuntime)-> YuiValue:
        """配列またはオブジェクトから値を取得する"""
        collection_value = self.collection.evaluate(runtime)
        self.index_node.evaluate(runtime)
        self.evaluated_value = collection_value.get_item(self.index_node, runtime)
        return self.evaluated_value
    
    def update(self, value_node: ASTNode, runtime: YuiRuntime):
        """変数の値を更新する"""
        collection_value = self.collection.evaluate(runtime)
        self.index_node.evaluate(runtime)
        collection_value.set_item(self.index_node, value_node, runtime)

@dataclass
class BinaryNode(ASTNode):
    """二項演算子を表すノード"""
    left_node: ExpressionNode
    right_node: ExpressionNode
    operator: str
    comparative: bool

    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode, comparative: bool = False):
        super().__init__()
        self.left_node = node(left)
        self.operator = operator
        self.right_node = node(right)
        self.comparative = comparative

    def visit(self, visitor):
        return visitor.visitBinaryNode(self)

    def evaluate(self, runtime):
        raise YuiError(("error", "internal", f"🔍{self.operator} operator is not implemented"), self, runtime)


class YuiFunction(ABC):
    name: str
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def call(self, arguments: List[Any], node: ASTNode, runtime: YuiRuntime) -> YuiValue:
        pass

class LocalFunction(YuiFunction):
    """ユーザが関数の型"""
    
    def __init__(self, name: str, parameters: List[str], body: ASTNode):
        super().__init__(name)
        self.parameters = parameters
        self.body = body

    def call(self, arguments: List[Any], node: ASTNode, runtime: YuiRuntime) -> YuiValue:
        # 新しい環境を作成
        runtime.pushenv()
        if len(self.parameters) != len(arguments):
            raise YuiError(("mismatch", "arguments", f"✅{len(self.parameters)}", f"❌{len(arguments)}"), node, runtime)

        for parameter_name, parameter_value in zip(self.parameters, arguments):
            runtime.setenv(parameter_name, parameter_value.evaluated_value)

        try:
            # 関数本体を評価
            runtime.push_call_frame(self.name, arguments, node)
            runtime.check_recursion_depth()
            self.body.evaluate(runtime)
        except YuiReturnException as e:
            # return 文で値が返された
            if e.value is not None:
                runtime.pop_call_frame()
                runtime.popenv()
                return e.value
        # return 文がない場合は変更された変数のみ返す
        runtime.pop_call_frame()
        return YuiValue(runtime.popenv())
        
class NativeFunction(YuiFunction):
    """ネイティブ関数の型"""
    is_ffi: bool = True
    name: str
    function: callable

    def __init__(self, function: callable, is_ffi=False):
        super().__init__(function.__name__)
        self.function = function
        self.is_ffi = is_ffi

    def call(self, arguments: List[ASTNode], node: ASTNode, runtime: YuiRuntime) -> YuiValue:
        try:
            return self.function(*arguments)
        except YuiError as e:
            if e.error_node is None:
                e.error_node = node
            e.runtime = runtime
            raise e
        except Exception as e:
            raise YuiError(("error", "internal", f"🔍{self.name}", f"⚠️ {e}"), node, runtime)


@dataclass
class FuncAppNode(ExpressionNode):
    """関数呼び出し（関数名(引数, ...)）を表すノード"""
    name: ExpressionNode
    arguments: List[ExpressionNode]
    snippet: str

    def __init__(self, name: ExpressionNode, arguments: List[ExpressionNode]):
        super().__init__()
        self.name_node = NameNode(name) if isinstance(name, str) else node(name)
        self.arguments = [node(arg) for arg in arguments]
        self.snippet = str(self)

    def visit(self, visitor):
        return visitor.visitFuncAppNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """関数を呼び出して結果を返す"""
        if isinstance(self.name_node, NameNode):
            name = f'@{self.name_node.name}'
            if not runtime.hasenv(name):
                raise YuiError(("undefined", "function", f"❌{self.name_node.name}"), self.name_node, runtime)
            function = runtime.getenv(name)
        if not isinstance(function, YuiFunction):
            raise YuiError(("error", "type", "✅<function>", f"❌{function}"), self.name_node, runtime)
        
        arguments = []
        for argnone in self.arguments:
            argnone.evaluate(runtime)
            arguments.append(argnone)
        
        if self.snippet == '':
            args = ', '.join(f'{YuiType.evaluated(argnode)}' for argnode in arguments)
            self.snippet = f'{self.name_node}({args})'
        self.evaluated_value = function.call(arguments, self, runtime)
        return self.evaluated_value


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
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)
        self.expression = node(expression)

    def visit(self, visitor):
        return visitor.visitAssignmentNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """式を評価して変数に代入する"""
        if not hasattr(self.variable, 'update'):
            raise YuiError(("expected", "variable", f"❌{self.variable}"), self.variable, runtime)
        self.expression.evaluate(runtime)
        self.variable.update(self.expression, runtime)

@dataclass
class IncrementNode(StatementNode):
    """インクリメント（変数 を 増やす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)

    def visit(self, visitor):
        return visitor.visitIncrementNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """変数を1増やす"""
        self.variable.evaluate(runtime)
        YuiType.IntType.match_or_raise(self.variable, runtime)
        self.variable.evaluated_value = YuiValue(YuiType.matched_native(self.variable) + 1)
        self.variable.update(self.variable, runtime)
        runtime.count_inc()

@dataclass
class DecrementNode(StatementNode):
    """デクリメント（変数 を 減らす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)

    def visit(self, visitor):
        return visitor.visitDecrementNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """変数を1減らす"""
        self.variable.evaluate(runtime)
        YuiType.IntType.match_or_raise(self.variable, runtime)
        self.variable.evaluated_value = YuiValue(YuiType.matched_native(self.variable) - 1)
        self.variable.update(self.variable, runtime)
        runtime.count_dec()

@dataclass
class AppendNode(StatementNode):
    """配列への追加（変数の末尾に 値 を 追加する）を表すノード"""
    variable: NameNode
    expression: ExpressionNode

    def __init__(self, variable: NameNode, expression: ExpressionNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)
        self.expression = node(expression)

    def visit(self, visitor):
        return visitor.visitAppendNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """値を評価して配列に追加する"""
        array = self.variable.evaluate(runtime)
        self.expression.evaluate(runtime)
        array.append(self.expression, runtime)

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

    def evaluate(self, runtime: YuiRuntime):
        for statement in self.statements:
            statement.evaluate(runtime)

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
        self.left = node(left)
        self.operator = OPERATORS[operator]
        self.right = node(right)
        self.then_block = then_block
        self.else_block = else_block

    def visit(self, visitor):
        return visitor.visitIfNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """条件を評価して適切なブロックを実行する"""
        self.left.evaluate(runtime)
        self.right.evaluate(runtime)
        result = self.operator.evaluate(self.left, self.right, runtime)
        runtime.count_compare()

        # 結果に応じてブロックを実行
        if result:
            self.then_block.evaluate(runtime)
        elif self.else_block:
            self.else_block.evaluate(runtime)


class YuiBreakException(RuntimeError):
    """ループを抜けるための例外"""
    def __init__(self):
        pass


@dataclass
class BreakNode(StatementNode):
    def __init__(self):
        super().__init__()

    def visit(self, visitor):
        return visitor.visitBreakNode(self)

    def evaluate(self, runtime: YuiRuntime):
        raise YuiBreakException()


@dataclass
class PassNode(StatementNode):
    def __init__(self, comment: Optional[str] = None):
        super().__init__()
        self.comment = comment

    def visit(self, visitor):
        return visitor.visitPassNode(self)

    def evaluate(self, runtime: YuiRuntime):
        pass

@dataclass
class RepeatNode(StatementNode):
    """ループ（N回 くり返す）を表すノード"""
    count: ExpressionNode
    body: BlockNode

    def __init__(self, count_node: ExpressionNode, block_node: BlockNode):
        super().__init__()
        self.count_node = node(count_node)    
        self.block_node = block_node

    def visit(self, visitor):
        return visitor.visitRepeatNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """ループを実行する"""
        count = self.count_node.evaluate(runtime)
        YuiType.IntType.match_or_raise(self.count_node, runtime)
        count = YuiType.matched_native(self.count_node)
        try:
            for _ in range(abs(count)):
                runtime.check_execution(self)
                self.block_node.evaluate(runtime)
        except YuiBreakException:
            pass

@dataclass
class ImportNode(StatementNode):
    """ライブラリのインポート（標準ライブラリを使う）を表すノード"""
    module_name: str

    def __init__(self, module_name: str = None):
        super().__init__()
        self.module_name = NameNode(module_name) if isinstance(module_name, str) else node(module_name)

    def visit(self, visitor):
        return visitor.visitImportNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """ライブラリを環境に追加する"""
        modules = []
        if self.module_name is None:
            standard_lib(modules)
        for name, func in modules:
            runtime.setenv(f'@{name}', NativeFunction(func))

class YuiReturnException(RuntimeError):
    """関数から値を返すための例外"""
    def __init__(self, value=None):
        self.value = value

@dataclass
class ReturnNode(StatementNode):
    """関数からの返値（式 が 答え）を表すノード"""
    expression: ExpressionNode

    def __init__(self, expression: ExpressionNode):
        super().__init__()
        self.expression = node(expression)

    def visit(self, visitor):
        return visitor.visitReturnNode(self)

    def evaluate(self, runtime: YuiRuntime):
        value = self.expression.evaluate(runtime)
        raise YuiReturnException(value)

@dataclass
class FuncDefNode(StatementNode):
    """関数定義を表すノード"""
    name_node: NameNode
    parameters: List[NameNode]
    body: BlockNode

    def __init__(self, name_node: NameNode, parameters: List[NameNode], body: BlockNode):
        super().__init__()
        self.name_node = NameNode(name_node) if isinstance(name_node, str) else node(name_node)
        self.parameters = [NameNode(param) if isinstance(param, str) else node(param) for param in parameters]
        self.body = body

    def visit(self, visitor):
        return visitor.visitFuncDefNode(self)

    def evaluate(self, runtime: YuiRuntime):
        params = [param.name for param in self.parameters]
        function = LocalFunction(self.name_node.name, params, self.body)
        runtime.setenv(f'@{self.name_node.name}', function)
        return function

@dataclass
class PrintExpressionNode(StatementNode):
    """式の出力（単独で書かれた式）を表すノード"""
    expression: ExpressionNode
    inspection: bool
    groping: bool = False

    def __init__(self, expression: ExpressionNode, inspection: bool = False, groping: bool = False):
        super().__init__()
        self.expression = node(expression)
        self.inspection = inspection
        self.groping = groping

    def visit(self, visitor):
        return visitor.visitPrintExpressionNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """式を評価して結果を出力する"""
        if isinstance(self.expression, MinusNode):  
            value = self.expression.element.evaluate(runtime)  # マイナス記号は出力しない
            return value
        if isinstance(self.expression, FuncAppNode):
            self.expression.snippet = '' # 表示の用のスニペットをクリア
        value = self.expression.evaluate(runtime)
        runtime.print(value, self.expression)
        return value

@dataclass
class AssertNode(StatementNode):
    """テストケース（>>> 式 → 期待値）を表すノード"""
    test: ExpressionNode
    reference: ExpressionNode

    def __init__(self, test: ExpressionNode, reference: ExpressionNode):
        super().__init__()
        self.test = node(test)
        self.reference = node(reference)

    def visit(self, visitor):
        return visitor.visitAssertNode(self)

    def evaluate(self, runtime: YuiRuntime):
        """式を評価して期待値と比較する"""
        try:
            tested = self.test.evaluate(runtime)
            reference_value = self.reference.evaluate(runtime)
            if tested.type.equals(self.test, self.reference):
                runtime.test_passed.append(str(self.test))
                return
        except Exception as e:
            print(f"Error during test evaluation: {e}")
            pass
        raise YuiError(("failed", "test", f"🔍{self.test}", f"❌{tested}", f"✅{reference_value}"), self, runtime)

