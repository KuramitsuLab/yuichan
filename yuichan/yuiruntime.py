import time
from typing import List, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod

from .yuiast import (
    ASTNode,
    ConstNode, NumberNode, StringNode, ArrayNode, ObjectNode,
    NameNode, GetIndexNode, ArrayLenNode, MinusNode, BinaryNode, FuncAppNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PassNode, PrintExpressionNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, CatchNode, ImportNode,
)
from .yuitypes import YuiValue, YuiError, types, IntType, NumberType, FloatType
from .yuierror import _format_messages
from .yuistdlib import standard_lib
from .yuiparser import YuiParser


def _format_source_context(node, prefix: str, marker: str, lineoffset: int, context: int = 3) -> str:
    """エラー箇所を行番号付き・前後コンテキスト付きで返す"""
    line, col, _ = node.extract()
    line += lineoffset
    length = max(node.end_pos - node.pos, 3) if node.end_pos is not None else 3
    make_pointer = marker * min(length, 16)

    all_lines = node.source.split('\n')
    start_idx = max(0, line - 1 - context)   # 直前 context 行 (0-based)
    line_width = len(str(line))
    sep = " | "

    lines_out = []
    for i in range(start_idx, min(line, len(all_lines))):
        lineno = i + 1
        lines_out.append(f"{prefix}{lineno:>{line_width}}{sep}{all_lines[i]}")

    pointer_indent = " " * (len(prefix) + line_width + len(sep) + col - 1)
    lines_out.append(f"{pointer_indent}{make_pointer}")

    return f"line {line}, column {col}:\n" + "\n".join(lines_out)


class YuiRuntime(object):
    """Yui言語のランタイムシステム(Visitor版)
    プログラムの実行を制御し、以下の機能を提供します：
    - プログラムのパースと実行
    - タイムアウト制御
    - 実行統計の収集（インクリメント、デクリメント、比較の回数）
    - 再帰呼び出しの追跡
    """

    environments: List[dict]
    filesystems: Dict[str, str]  # 仮想ファイルシステム
    call_frames: List[tuple]  # (func_name, args, pos, end_pos)
    shouldStop: bool
    timeout: int
    interactive_mode: bool
    source: str
    allow_binary_ops: bool
    function_defined: bool
    increment_count: int
    decrement_count: int
    compare_count: int
    test_passed: List[str]
    test_failed: List[tuple]

    def __init__(self):
        """YuiRuntimeを初期化する"""
        self.environments = [{}]
        self.call_frames = []
        self.filesystems = {}

        self.shouldStop = False
        self.timeout = 0
        self.interactive_mode = False
        self.source = ""
        self.allow_binary_ops = False
        self.function_defined = False
        self.reset_stats()

    def reset_stats(self):
        """実行統計をリセットする"""
        self.increment_count = 0
        self.decrement_count = 0
        self.compare_count = 0
        self.test_passed = []
        self.test_failed = []

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

    def format_error(self, error: 'YuiError', prefix: str = " ", marker: str = '^', lineoffset: int = 0) -> str: # type: ignore
        """YuiError を整形したメッセージを返す。パースエラーは構文エラー、実行中エラーは実行時エラーとして表示する"""
        is_runtime = hasattr(error, 'runtime')
        message = _format_messages(error.messages)
        if error.error_node:
            context = _format_source_context(error.error_node, prefix, marker, lineoffset)
            message = f"{message} {context}"
        if is_runtime:
            return f"[実行時エラー/RuntimeError] {message}\n[環境/Environment] {self.stringfy_env(stack=-1)}\n"
        return f"[構文エラー/SyntaxError] {message}"

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
        if len(self.call_frames) > 128:
            args = ", ".join(str(arg) for arg in self.call_frames[-1][1])
            snippet = f"{self.call_frames[-1][0]}({args})"
            raise YuiError(("too-many-recursion", f"🔍{snippet}"), self.call_frames[-1][2])

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

    def load(self, function: FunctionType):
        """Python関数をYui関数として読み込む"""
        return NativeFunction(function)

    def print(self, value: Any, node: ASTNode):
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
            raise YuiError(('interruptted'), node)

        # タイムアウトチェック
        if self.timeout > 0 and (time.time() - self.startTime) > self.timeout:
            raise YuiError(("runtime-timeout", f"❌{self.timeout}[sec]", f"✅{self.timeout}[sec]"), node)

    def exec(self, source: str, syntax: Union[str,dict] = 'yui', timeout: int = 30, eval_mode: bool = True):
        """Yuiプログラムを実行する"""
        self.source = source

        # パースして実行
        parser = YuiParser(syntax)
        program = parser.parse(source)
        try:
            self.start(timeout)
            value = program.evaluate(self)
        except YuiError as e:
            e.runtime = self
            raise e

        # 結果を返す
        return types.unbox(value) if eval_mode else self.environments[-1]


    ## visitor

    def evaluate(self, node: ASTNode):
        """メインエントリーポイント。node.visit(self) に委譲する"""
        return node.visit(self)

    # ──────────────────────────────────────────────────────────
    # リテラル・値ノード
    # ──────────────────────────────────────────────────────────

    def visitConstNode(self, node: ConstNode):
        if node.native_value is True:
            return YuiValue.TrueValue
        if node.native_value is False:
            return YuiValue.FalseValue
        return YuiValue.NullValue

    def visitNumberNode(self, node: NumberNode):
        return YuiValue(node.native_value)

    def visitStringNode(self, node: StringNode):
        if isinstance(node.contents, str):
            return YuiValue(node.contents)
        parts = []
        for content in node.contents:
            if isinstance(content, str):
                parts.append(content)
            else:
                value = content.visit(self)
                parts.append(f'{types.unbox(value)}')
        return YuiValue(''.join(parts))

    def visitArrayNode(self, node: ArrayNode):
        array_value = YuiValue([])
        for element in node.elements:
            v = element.visit(self)
            array_value.append(v)
        return array_value

    def visitObjectNode(self, node: ObjectNode):
        object_value = YuiValue({})
        for i in range(0, len(node.elements), 2):
            key = node.elements[i].visit(self)
            val = node.elements[i + 1].visit(self)
            object_value.set_item(key, val)
        return object_value

    # ──────────────────────────────────────────────────────────
    # 変数参照・演算ノード
    # ──────────────────────────────────────────────────────────

    def visitNameNode(self, node: NameNode):
        if not self.hasenv(node.name):
            raise YuiError(("undefined-variable", f"❌{node.name}"), node)
        return self.getenv(node.name)

    def visitGetIndexNode(self, node: GetIndexNode):
        collection = node.collection.visit(self)
        index = node.index_node.visit(self)
        return collection.get_item(index)

    def visitArrayLenNode(self, node: ArrayLenNode):
        value = node.element.visit(self)
        return YuiValue(len(value.array))

    def visitMinusNode(self, node: MinusNode):
        value = node.element.visit(self)
        NumberType.match_or_raise(value)
        return YuiValue(-types.unbox(value))

    def visitBinaryNode(self, node: BinaryNode):
        if not (self.allow_binary_ops):
            raise YuiError(("unsupported-operator", f"🔍{node.operator.symbol}"), node)
        left = node.left_node.visit(self)
        right = node.right_node.visit(self)
        return types.box(node.operator.evaluate(left, right))

    def visitFuncAppNode(self, node: FuncAppNode):
        name = f'@{node.name_node.name}'
        if not self.hasenv(name):
            raise YuiError(("undefined-function", f"❌{node.name_node.name}"), node.name_node)
        function = self.getenv(name)
        if not isinstance(function, YuiFunction):
            raise YuiError(("type-error", "✅<function>", f"❌{function}"), node.name_node)

        # 引数を訪問した直後に値を確定させる（再帰で同一ノードが上書きされる問題を防ぐ）
        arg_values = [arg_node.visit(self) for arg_node in node.arguments]

        if node.snippet == '':
            args = ', '.join(str(v) for v in arg_values)
            node.snippet = f'{node.name_node}({args})'

        return function.call(arg_values, node, self)

    # ──────────────────────────────────────────────────────────
    # 代入・変更ノード
    # ──────────────────────────────────────────────────────────

    def visitAssignmentNode(self, node: AssignmentNode):
        if not hasattr(node.variable, 'update'):
            raise YuiError(("expected-variable", f"❌{node.variable}"), node.variable)
        value = node.expression.visit(self)
        node.variable.update(value, self)
        return value

    def visitIncrementNode(self, node: IncrementNode):
        if not hasattr(node.variable, 'update'):
            raise YuiError(("expected-variable", f"❌{node.variable}"), node.variable)
        value = node.variable.visit(self)
        IntType.match_or_raise(value)
        result = YuiValue(types.unbox(value) + 1)
        node.variable.update(result, self)
        self.count_inc()
        return result

    def visitDecrementNode(self, node: DecrementNode):
        if not hasattr(node.variable, 'update'):
            raise YuiError(("expected-variable", f"❌{node.variable}"), node.variable)
        value = node.variable.visit(self)
        IntType.match_or_raise(value)
        result = YuiValue(types.unbox(value) - 1)
        node.variable.update(result, self)
        self.count_dec()
        return result

    def visitAppendNode(self, node: AppendNode):
        array = node.variable.visit(self)
        value = node.expression.visit(self)
        if types.is_string(array) and types.is_string(value):
            # 文字列への文字列追加: 各文字コードを順に追加
            for char_code in value.array:
                array.append(YuiValue(char_code))
        elif types.is_object(array) and types.is_string(value):
            # オブジェクトへのキー追加: 値は現在の要素数+1
            key = types.unbox(value)
            new_index = len(array.array) + 1
            array.append(YuiValue([key, new_index]))
        else:
            array.append(value)
        return array

    # ──────────────────────────────────────────────────────────
    # 制御構造ノード
    # ──────────────────────────────────────────────────────────

    def visitBlockNode(self, node: BlockNode):
        value = YuiValue.NullValue
        for statement in node.statements:
            value =statement.visit(self)
        return value

    def visitIfNode(self, node: IfNode):
        left = node.left.visit(self)
        right = node.right.visit(self)
        result = node.operator.evaluate(left, right)
        self.count_compare()
        if result:
            return node.then_block.visit(self)
        elif node.else_block:
            return node.else_block.visit(self)
        else:
            return YuiValue.NullValue

    def visitBreakNode(self, node: BreakNode):
        raise YuiBreakException(node)

    def visitPassNode(self, node: PassNode):
        pass

    def visitRepeatNode(self, node: RepeatNode):
        count_value = node.count_node.visit(self)
        IntType.match_or_raise(count_value)
        count = types.unbox(count_value)
        result = YuiValue.NullValue
        try:
            for _ in range(abs(count)):
                self.check_execution(node)
                node.block_node.visit(self)
        except YuiBreakException:
            pass
        return result

    def visitReturnNode(self, node: ReturnNode):
        if isinstance(node.expression, ASTNode):
            value = node.expression.visit(self)
        else:
            value = None #何も返さない
        raise YuiReturnException(value, node)

    def visitFuncDefNode(self, node: FuncDefNode):
        """LocalFunctionV を登録することで、関数本体も visitor チェーンで評価される"""
        params = [p.name for p in node.parameters]
        function = LocalFunctionV(node.name_node.name, params, node.body)
        self.setenv(f'@{node.name_node.name}', function)
        self.function_defined = True
        return function

    # ──────────────────────────────────────────────────────────
    # 出力・テストノード
    # ──────────────────────────────────────────────────────────

    def is_in_the_top_level(self):
        """現在の呼び出しスタックがトップレベルかどうかを判定する"""
        return len(self.call_frames) == 0

    def visitPrintExpressionNode(self, node: PrintExpressionNode):
        if not node.grouping and (self.is_in_the_top_level() or node.inspection):
            if isinstance(node.expression, FuncAppNode):
                node.expression.snippet = ''
            value = node.expression.visit(self)
            self.print(value, node.expression)
        else:
            value = node.expression.visit(self)
        return value

    def visitAssertNode(self, node: AssertNode):
        tested = reference_value = None
        try:
            tested = node.test.visit(self)
            reference_value = node.reference.visit(self)
            if tested.type.equals(tested, reference_value):
                self.test_passed.append(str(node.test))
                return YuiValue.TrueValue
        except YuiError:
            raise
        except Exception:
            pass
        raise YuiError(
            ("assertion-failed", f"🔍{node.test}", f"❌{tested}", f"✅{reference_value}"),
            node,
        )
        return YuiValue.FalseValue

    def visitImportNode(self, node: ImportNode):
        """ライブラリを環境に追加する"""
        modules = []
        is_null = node.module_name is None or (isinstance(node.module_name, ConstNode) and node.module_name.native_value is None)
        if is_null:
            standard_lib(modules)
        for names, func in modules:
            for name in names.split('|'): # 多言語関数名
                self.setenv(f'@{name}', NativeFunction(func))
        return YuiValue.NullValue

    def load_stdlib(self):
        self.visitImportNode(ImportNode(None))

    def visitCatchNode(self, node: CatchNode):
        try:
            return node.expression.visit(self)
        except YuiError as e:
            return f"💣{e.messages[0]}"


    # # ──────────────────────────────────────────────────────────
    # # フォールバック
    # # ──────────────────────────────────────────────────────────

    # def visitASTNode(self, node: ASTNode):
    #     """visitXxxNode が未定義のノードは evaluate にフォールバック"""
    #     return node.evaluate(self)


class YuiFunction(ABC):
    name: str
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def call(self, arguments: List[Any], node: ASTNode, runtime: 'YuiRuntime') -> YuiValue:
        pass

class LocalFunction(YuiFunction):
    """ユーザが関数の型"""
    
    def __init__(self, name: str, parameters: List[str], body: ASTNode):
        super().__init__(name)
        self.parameters = parameters
        self.body = body

    def call(self, arg_values: List[Any], node: ASTNode, runtime: 'YuiRuntime') -> YuiValue:
        runtime.pushenv()
        if len(self.parameters) != len(arg_values):
            raise YuiError(("mismatch-argument", f"✅{len(self.parameters)}", f"❌{len(arg_values)}"), node)
        for param_name, value in zip(self.parameters, arg_values):
            runtime.setenv(param_name, value)
        try:
            runtime.push_call_frame(self.name, arg_values, node)
            runtime.check_recursion_depth()
            self.body.evaluate(runtime)
        except YuiBreakException as e:
             raise YuiError(("unexpected-break", f"🔍{node}"), e.error_node)
        except YuiReturnException as e:
            if e.value is not None:
                runtime.pop_call_frame()
                runtime.popenv()
                return e.value
        runtime.pop_call_frame()
        return YuiValue(runtime.popenv())


class LocalFunctionV(LocalFunction):
    """visitor パターン版 LocalFunction。body.visit(runtime) で実行する。"""

    def call(self, arg_values: List[Any], node: ASTNode, runtime: 'YuiRuntime') -> YuiValue:
        runtime.pushenv()
        if len(self.parameters) != len(arg_values):
            raise YuiError(
                ("mismatch", "arguments", f"✅{len(self.parameters)}", f"❌{len(arg_values)}"), node)
        for param_name, value in zip(self.parameters, arg_values):
            runtime.setenv(param_name, value)
        try:
            runtime.push_call_frame(self.name, arg_values, node)
            runtime.check_recursion_depth()
            self.body.visit(runtime)
        except YuiReturnException as e:
            if e.value is not None:
                runtime.pop_call_frame()
                runtime.popenv()
                return e.value
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

    def call(self, arg_values: List[Any], node: ASTNode, runtime: 'YuiRuntime') -> YuiValue:
        try:
            result = self.function(*arg_values)
            return result if isinstance(result, YuiValue) else YuiValue(result)
        except YuiError as e:
            if e.error_node is None:
                e.error_node = node
            raise e
        except Exception as e:
            raise YuiError(("internal-error", f"🔍{self.name}", f"⚠️ {e}"), node)

class YuiBreakException(YuiError):
    """ループを抜けるための例外"""
    def __init__(self, error_node):
        super().__init__(("unexpected-break",), error_node)

class YuiReturnException(YuiError):
    """関数から値を返すための例外"""
    def __init__(self, value=None, error_node=None):
        super().__init__(("unexpected-return",), error_node)
        self.value = value
