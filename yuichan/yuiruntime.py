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
    AssertNode, ImportNode,
)
from .yuitypes import YuiValue, YuiType, YuiError, _format_messages
from .yuistdlib import standard_lib
from .yuiparser import YuiParser


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
        """YuiError を実行時エラーとして整形したメッセージを返す（環境情報付き）"""
        message = _format_messages(error.messages)
        if error.error_node:
            line, col, snippet = error.error_node.extract()
            length = max(error.error_node.end_pos - error.error_node.pos, 3) if error.error_node.end_pos is not None else 3
            make_pointer = marker * min(length, 16)
            snippet = snippet.split('\n')[0]
            indent = " " * (col - 1)
            message = f"{message} line {line + lineoffset}, column {col}:\n{prefix}{snippet}\n{prefix}{indent}{make_pointer}"
        return f"[実行時エラー/RuntimeError] {message}\n[環境/Environment] {self.stringfy_env(stack=-1)}\n"

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
            raise YuiError(("too-many-recursions", f"🔍{snippet}"), self.call_frames[-1][2])

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
        return YuiType.yui_to_native(value) if eval_mode else self.environments[-1]


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
                parts.append(f'{YuiType.yui_to_native(value)}')
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
        return YuiValue(len(value.arrayview))

    def visitMinusNode(self, node: MinusNode):
        value = node.element.visit(self)
        YuiType.NumberType.match_or_raise(value)
        return YuiValue(-YuiType.matched_native(value))

    def visitBinaryNode(self, node: BinaryNode):
        if not (self.allow_binary_ops or (self.function_defined and self.test_passed)):
            raise YuiError(("unsupported-operator", f"🔍{node.operator}"), node)
        left = node.left_node.visit(self)
        right = node.right_node.visit(self)
        op = node.operator

        # 文字列連結: + のみ
        if op == '+' and YuiType.is_string(left) and YuiType.is_string(right):
            return YuiValue(YuiType.matched_native(left) + YuiType.matched_native(right))

        # 配列連結: + のみ
        if op == '+' and YuiType.is_array(left) and YuiType.is_array(right):
            return YuiValue(left.native + right.native)

        # 数値演算
        YuiType.NumberType.match_or_raise(left)
        YuiType.NumberType.match_or_raise(right)
        l = YuiType.matched_native(left)
        r = YuiType.matched_native(right)
        is_float = YuiType.is_float(left) or YuiType.is_float(right)

        if op == '+':
            result = l + r
        elif op == '-':
            result = l - r
        elif op == '*':
            result = l * r
        elif op == '/':
            if r == 0:
                raise YuiError(("division-by-zero", f"❌{r}"), node)
            result = l / r if is_float else l // r
        elif op == '%':
            if r == 0:
                raise YuiError(("division-by-zero", f"❌{r}"), node)
            result = l % r  # Python: 正の除数に対して常に非負
        else:
            raise YuiError(("unsupported-operator", f"🔍{op}"), node)

        return YuiValue(float(result) if is_float else result)

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

    def visitIncrementNode(self, node: IncrementNode):
        value = node.variable.visit(self)
        YuiType.IntType.match_or_raise(value)
        node.variable.update(YuiValue(YuiType.matched_native(value) + 1), self)
        self.count_inc()

    def visitDecrementNode(self, node: DecrementNode):
        value = node.variable.visit(self)
        YuiType.IntType.match_or_raise(value)
        node.variable.update(YuiValue(YuiType.matched_native(value) - 1), self)
        self.count_dec()

    def visitAppendNode(self, node: AppendNode):
        array = node.variable.visit(self)
        value = node.expression.visit(self)
        array.append(value)

    # ──────────────────────────────────────────────────────────
    # 制御構造ノード
    # ──────────────────────────────────────────────────────────

    def visitBlockNode(self, node: BlockNode):
        for statement in node.statements:
            statement.visit(self)

    def visitIfNode(self, node: IfNode):
        left = node.left.visit(self)
        right = node.right.visit(self)
        result = node.operator.evaluate(left, right)
        self.count_compare()
        if result:
            node.then_block.visit(self)
        elif node.else_block:
            node.else_block.visit(self)

    def visitBreakNode(self, node: BreakNode):
        raise YuiBreakException()

    def visitPassNode(self, node: PassNode):
        pass

    def visitRepeatNode(self, node: RepeatNode):
        count_value = node.count_node.visit(self)
        YuiType.IntType.match_or_raise(count_value)
        count = YuiType.matched_native(count_value)
        try:
            for _ in range(abs(count)):
                self.check_execution(node)
                node.block_node.visit(self)
        except YuiBreakException:
            pass

    def visitReturnNode(self, node: ReturnNode):
        value = node.expression.visit(self)
        raise YuiReturnException(value)

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

    def visitPrintExpressionNode(self, node: PrintExpressionNode):
        if isinstance(node.expression, MinusNode):
            return node.expression.element.visit(self)
        if isinstance(node.expression, FuncAppNode):
            node.expression.snippet = ''
        value = node.expression.visit(self)
        self.print(value, node.expression)
        return value

    def visitAssertNode(self, node: AssertNode):
        tested = reference_value = None
        try:
            tested = node.test.visit(self)
            reference_value = node.reference.visit(self)
            if tested.type.equals(tested, reference_value):
                self.test_passed.append(str(node.test))
                return
        except YuiError:
            raise
        except Exception:
            pass
        raise YuiError(
            ("failed", f"🔍{node.test}", f"❌{tested}", f"✅{reference_value}"),
            node,
        )

    def visitImportNode(self, node: ImportNode):
        """ライブラリを環境に追加する"""
        modules = []
        if node.module_name is None:
            standard_lib(modules)
        for names, func in modules:
            for name in names.split('|'): # 多言語関数名
                self.setenv(f'@{name}', NativeFunction(func))

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
            raise YuiError(
                ("mismatch", "arguments", f"✅{len(self.parameters)}", f"❌{len(arg_values)}"), node)
        for param_name, value in zip(self.parameters, arg_values):
            runtime.setenv(param_name, value)
        try:
            runtime.push_call_frame(self.name, arg_values, node)
            runtime.check_recursion_depth()
            self.body.evaluate(runtime)
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

class YuiBreakException(RuntimeError):
    """ループを抜けるための例外"""
    def __init__(self):
        pass

class YuiReturnException(RuntimeError):
    """関数から値を返すための例外"""
    def __init__(self, value=None):
        self.value = value
