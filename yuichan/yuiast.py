from dataclasses import dataclass
import time
from typing import List, Optional, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod

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

    enviroments: List[dict]
    filesystems: Dict[str, str]  # 仮想ファイルシステム
    call_frames: List[tuple]  # (func_name, args, pos, end_pos)
    increment_count: int
    decrement_count: int
    compare_count: int
    test_passed: List[str]
    source: str

    def __init__(self, init_env: Dict[str, Any] = None):
        """YuiRuntimeを初期化する"""
        self.enviroments = [{} if init_env is None else init_env]
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
        for env in reversed(self.enviroments):
            if name in env:
                return True
        return False

    def getenv(self, name) -> Any:
        """現在の環境から変数を取得する"""
        for env in reversed(self.enviroments):
            if name in env:
                return env[name]
        return None

    def setenv(self, name, value) -> Any:
        """現在の環境に変数を設定する"""
        self.enviroments[-1][name] = value  

    def pushenv(self):
        """現在の環境に変数を設定する"""
        self.enviroments.append({})

    def popenv(self):
        """現在の環境に変数を設定する"""
        return self.enviroments.pop()
    
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
        for i, (key, value) in enumerate(self.enviroments[stack].items()):
            if key.startswith("@"): continue 
            lines.append(f"{LF}{indent_prefix}  \"{key}\": ")
            lines.append(f"{YuiData.stringfy_value(value, inner_indent_prefix)}")
            if i < len(self.enviroments[stack]) - 1:
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
        args = ", ".join(YuiData.stringfy_value(arg, indent_prefix=None) for arg in call_frame[1])
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
        return YuiData.yui_to_native(value) if eval_mode else self.enviroments[-1]

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
class Operator(ABC):
    symbol: str
    comparative: bool

    def __init__(self, symbol: str, comparative: bool):
        self.symbol = symbol
        self.comparative = comparative

    def __str__(self):
        return self.symbol

    @abstractmethod
    def evaluate(self, left: Any, right: Any, node = None, env = None) -> Any:
        pass

@dataclass
class Equals(Operator):
    def __init__(self, symbol: str = "=="):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) == 0

@dataclass
class NotEquals(Operator):
    def __init__(self, symbol: str = "!="):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) != 0

@dataclass
class LessThan(Operator):
    def __init__(self, symbol: str = "<"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) < 0

@dataclass
class GreaterThan(Operator):
    def __init__(self, symbol: str = ">"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) > 0

@dataclass
class LessThanEquals(Operator):
    def __init__(self, symbol: str = "<="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) <= 0

@dataclass
class GreaterThanEquals(Operator):
    def __init__(self, symbol: str = ">="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        return YuiData.compare(left, right, node, env) >= 0

@dataclass
class In(Operator):
    def __init__(self, symbol: str = "in"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        if YuiData.is_string(left) and YuiData.is_string(right):
            left = YuiData.ensure_string(left)
            right = YuiData.ensure_string(right)
            return left in right
        YuiData.type_check(right, 'data', node, env)
        for element in right.array:
            if YuiData.compare(left, element, node, env) == 0:
                return True
        return False

@dataclass
class NotIn(Operator):
    def __init__(self, symbol: str = "notin"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left: Any, right: Any, node = None, env = None) -> bool:
        if YuiData.is_string(left) and YuiData.is_string(right):
            left = YuiData.ensure_string(left)
            right = YuiData.ensure_string(right)
            return left not in right
        YuiData.type_check(right, 'data', node, env)
        for element in right.array:
            if YuiData.compare(left, element, node, env) == 0:
                return False
        return True

OPERATORS = {
    '==': Equals(),
    '!=': NotEquals(),
    '<': LessThan(),
    '>': GreaterThan(),
    '<=': LessThanEquals(),
    '>=': GreaterThanEquals(),
    'in': In(),
    'notin': NotIn(),
}

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

    @abstractmethod
    def evaluate(self, runtime: YuiRuntime) -> Union[int, 'YuiData']:
        pass

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


class YuiError(RuntimeError):
    """
    Yui言語のエラーを表現するクラス
    """
    messages: tuple
    error_node: Optional[ASTNode]
    runtime: Optional[YuiRuntime]
    BK: bool
    
    def __init__(self, messages: tuple, 
                 error_node: Optional[ASTNode] = None,
                 runtime: Optional[YuiRuntime] = None,
                 BK: bool = False):
        """YuiErrorを初期化する"""
        super().__init__(' '.join(messages))
        self.messages = messages
        self.error_node = error_node
        self.runtime = runtime
        self.BK = BK

    @property
    def lineno(self) -> int:
        """エラー箇所の行番号を返す（1始まり）"""
        if self.error_node:
            line, _, _ = self.error_node.extract()
            return line
        return 0

    @property
    def offset(self) -> int:
        """エラー箇所の列番号を返す（1始まり）"""
        if self.error_node:
            _, offset, _ = self.error_node.extract()
            return offset
        return 0

    @property
    def text(self) -> str:
        """エラー箇所のコードスニペットを返す"""
        if self.error_node:
            _, _, snippet = self.error_node.extract()
            return snippet
        return ""

    def formatted_message(self, prefix=" ", marker: str = '^', lineoffset: int = 0) -> str:
        """エラーメッセージを整形して返す"""
        message = _to_message(self.messages)
        if self.error_node:
            line, col, snippet = self.error_node.extract()
            # エラー範囲の長さを計算（最小3文字）
            length = max(self.error_node.end_pos - self.error_node.pos, 3) if self.error_node.end_pos is not None else 3
            # エラー位置を指すポインタを作成
            make_pointer = marker * min(length, 16)
            snippet = snippet.split('\n')[0]  # エラー行の最初の行だけを表示
            indent = " " * (col - 1)
            message = f"{message} line {line + lineoffset}, column {col}:\n{prefix}{snippet}\n{prefix}{indent}{make_pointer}"
        if self.runtime is None:
            message = f"[構文エラー] {message}"
        else:
            message = f"[実行時エラー] {message}\n[環境] {self.runtime.stringfy_env(stack=-1)}\n"
        return message

class YuiData(object):
    """Yui言語のデータ型"""
    view: str
    elements: List[Any]
    native_value: Optional[Union[str, float, dict, int]]

    def __init__(self, native_value: Any):
        """YuiDataを初期化する"""
        if isinstance(native_value, str):
            self.view = "string"
        elif isinstance(native_value, float):
            self.view = "float"
        elif isinstance(native_value, dict):
            self.view = "object"
        elif isinstance(native_value, int):
            self.view = "binary"
        else:
            self.view = "array"
        self.native_value = native_value
        self.elements = None

    def sync(self) -> Optional[Union[str, float, dict, int]]:
        if self.elements is None:
            if self.view == "string":
                self.elements = [ord(ch) for ch in self.native_value]
            elif self.view == "float":
                # 浮動小数点数は桁の配列として格納
                self.elements = YuiData.float_to_array(self.native_value)
            elif self.view == "array":
                # 配列の要素を再帰的にエンコード
                self.elements = [YuiData.native_to_yui(v) for v in self.native_value]
            elif self.view == "object":
                self.elements = []
                for k, v in self.native_value.items():
                    self.elements.append(YuiData.native_to_yui(str(k)))
                    self.elements.append(YuiData.native_to_yui(v))
        if self.native_value is None:
            if self.view == "string":
                chars = [chr(code) for code in self.elements]
                self.native_value = ''.join(chars)
            if self.view == "float":
                self.native_value = YuiData.array_to_float(self.elements)
            if self.view == "object":
                obj = {}
                for i in range(0, len(self.elements), 2):
                    key = YuiData.yui_to_native(self.elements[i])
                    value = YuiData.yui_to_native(self.elements[i+1])
                    obj[key] = value
                self.native_value = obj
            if self.view == "array":
                self.native_value = [YuiData.yui_to_native(element) for element in self.elements]
        return self.elements
    
    @property
    def native(self) -> Any:
        if self.native_value is None:
            self.sync()
        return self.native_value

    @property
    def array(self) -> List[Any]:
        if self.elements is None:
            self.sync()
        return self.elements

    @staticmethod
    def native_to_yui(native_value) -> Any:
        """ネイティブ値をYui形式に変換して返す"""
        if isinstance(native_value, (list, str, float, tuple)):
            return YuiData(native_value)
        if isinstance(native_value, dict):
            # 辞書の値を再帰的にエンコード
            for key, value in native_value.items():
                native_value[key] = YuiData.native_to_yui(value)
            return native_value
        return native_value

    @staticmethod
    def yui_to_native(value: Any) -> Any:
        """Yui形式の値をネイティブ値に変換して返す"""
        if isinstance(value, YuiData):
            if value.native_value is None:
                value.sync()
            return value.native_value
        if isinstance(value, list):
            return [YuiData.yui_to_native(e) for e in value]
        if isinstance(value, dict):
            new_value = {}
            for key, item in value.items():
                new_value[key] = YuiData.yui_to_native(item)
            return new_value
        return value

    @staticmethod
    def float_to_array(x: float) -> List[int]:
        """浮動小数点数を符号付き一桁整数配列に変換
        Example:
            [1, 3, 1, 4, 0, 0]  # 3.1400
            [-1, 2, 5, 0, 0, 0]  # -2.5000
        """
        sign = -1 if x < 0 else 1
        s = f"{abs(x):.6f}"  # 小数点以下6桁に丸める
        s = s.replace('.', '')  # 小数点を削除
        digits = [sign] + [int(ch) for ch in s]
        return digits

    @staticmethod
    def array_to_float(digits: List[int]) -> float:
        """符号付き一桁整数配列を浮動小数点数に変換
        Example:
            >>> array_to_float([1, 3, 1, 4, 0, 0])
            3.14
            >>> array_to_float([-1, 2, 5, 0, 0, 0])
            -2.5
        """
        sign = digits[0]
        if not(isinstance(sign, int) and sign in (1, -1)):
            raise YuiError(f"少数に変換できません: ❌{digits}")
        num_digits = digits[1:]
        for d in num_digits:
            if not (isinstance(d, int) and 0 <= d <= 9):
                raise YuiError(f"少数に変換できません: ❌{digits}")
        s = ''.join(str(d) for d in num_digits)

        if len(s) <= 6:
            # 小数部のみの場合（整数部なし）
            value = int(s)
        else:
            # 小数点を6桁前に挿入
            value = float(s[:-6] + '.' + s[-6:])
        return sign * value
    
    @staticmethod
    def is_string(value) -> bool:
        if isinstance(value, YuiData) and value.view == "string":
            return True
        return isinstance(value, str)
    
    @staticmethod
    def ensure_string(value) -> str:
        if isinstance(value, YuiData) and value.view == "string":
            if value.native_value is None:
                value.sync()
            return value.native_value
        YuiData.type_check(value, 'string')
        return value

    @staticmethod
    def is_float(value) -> bool:
        if isinstance(value, YuiData) and value.view == "float":
            return True
        return isinstance(value, float)
    
    @staticmethod
    def ensure_float(value) -> float:
        if isinstance(value, YuiData) and value.view == "float":
            if value.native_value is None:
                value.sync()
            return value.native_value
        YuiData.type_check(value, 'float')
        return value

    @staticmethod
    def is_number(value) -> bool:
        if isinstance(value, YuiData) and value.view == "float":
            return True
        return isinstance(value, (float, int))
    
    @staticmethod
    def ensure_number(value) -> Union[float, int]:
        if isinstance(value, YuiData) and value.view == "float":
            if value.native_value is None:
                value.sync()
            return value.native_value
        YuiData.type_check(value, 'number')
        return value

    @staticmethod
    def ensure_int(value) -> int:
        if isinstance(value, YuiData) and value.view == "float":
            if value.native_value is None:
                value.sync()
            return int(value.native_value)
        YuiData.type_check(value, 'int')
        return int(value)


    @staticmethod
    def is_object(value) -> bool:
        if isinstance(value, YuiData) and value.view == "object":
            return True
        return isinstance(value, dict)
    
    @staticmethod
    def ensure_object(value) -> dict:
        if isinstance(value, YuiData) and value.view == "object":
            if value.native_value is None:
                value.sync()
            return value.native_value
        YuiData.type_check(value, 'object')
        return value

    @staticmethod
    def type_check(value, expected_type: str, node = None, env = None):
        if expected_type == 'data':
            if not isinstance(value, YuiData):
                raise YuiError(("error", "type", f"✅<not-int>", f"❌{value}"), node, env)
            return
        if expected_type == 'array':
            if not isinstance(value, YuiData) and value.view == "array":
                raise YuiError(("error", "type", f"✅<array>", f"❌{value}"), node, env)
            return
        if expected_type == 'string':
            if not YuiData.is_string(value):
                raise YuiError(("error", "type", f"✅<string>", f"❌{value}"), node, env)
            return
        if expected_type == 'float':
            if not YuiData.is_float(value):
                raise YuiError(("error", "type", f"✅<float>", f"❌{value}"), node, env)
            return
        if expected_type == 'number':
            if not YuiData.is_number(value):
                raise YuiError(("error", "type", f"✅<number>", f"❌{value}"), node, env)
            return
        if expected_type == 'object':
            if not YuiData.is_object(value):
                raise YuiError(("error", "type", f"✅<object>", f"❌{value}"), node, env)
            return
        if expected_type == 'int':
            if not isinstance(value, int):
                raise YuiError(("error", "type", f"✅<int>", f"❌{value}"), node, env)
            return
        assert expected_type is None, f"unknown type: {expected_type}"

    def stringfy(self, indent_prefix: str = "", inner_view: bool = False, width=80) -> str:
        self.sync()
        if self.view == "string":
            if inner_view:
                return f"{self.array}"
            content = self.native_value.replace('"', '\\"').replace('\n', '\\n')
            return f'"{content}"'
        if self.view == "float":
            if inner_view:
                return f"{self.array}"
            return f"{self.native_value:.6f}"
        if indent_prefix is None:
            indent_prefix = ""
            inner_indent_prefix = None
            LF = ""
        else:
            inner_indent_prefix = indent_prefix + "  "
            LF = "\n"
        if self.view == "array":
            flat_view = False
            if len(self.elements) > 0 and isinstance(self.elements[0], int):
                flat_view = True
            if flat_view:
                buffer = ["["]
                for i, element in enumerate(self.elements):
                    if i > 0:
                        buffer.append(", ")
                    if isinstance(element, YuiData):
                        buffer.append(element.stringfy(inner_indent_prefix, inner_view=False, width=width))
                    else: 
                        buffer.append(f"{element}")
                buffer.append("]")  
                content = ''.join(buffer)
                if len(indent_prefix) + len(content) <= width:
                    return content
        if self.view == "object":
            if not inner_view:
                buffer = ["{"]
                for i, (key, value) in enumerate(self.native_value.items()):
                    if i > 0:
                        buffer.append(", ")
                    buffer.append(f'{LF}{inner_indent_prefix}"{key}" :')
                    if isinstance(value, YuiData):
                        buffer.append(value.stringfy(inner_indent_prefix, inner_view=False, width=width))
                    else: 
                        buffer.append(f"{value}")
                buffer.append(f"{LF}{indent_prefix}}}")
                return ''.join(buffer)
        buffer = ["["]
        for i, element in enumerate(self.elements):
            buffer.append(f"{LF}{inner_indent_prefix}")
            if isinstance(element, YuiData):
                buffer.append(element.stringfy(inner_indent_prefix, inner_view=False, width=width))
            else:
                buffer.append(f"{element}")
        if i < len(self.elements) - 1:
            buffer.append(", ")
        buffer.append(f"{LF}{indent_prefix}]")
        return ''.join(buffer)

    @staticmethod
    def stringfy_value(value: Any, indent_prefix: str = "") -> str:
        """値をJSON形式の文字列として出力する"""
        if isinstance(value, YuiData):
            return value.stringfy(indent_prefix, inner_view=False)
        return f"{value}"

    @staticmethod
    def compare(v: Any, v2: Any, node = None, env = None) -> int:
        if YuiData.is_number(v) and YuiData.is_number(v2):
            v = round(YuiData.ensure_number(v), 6)
            v2 = round(YuiData.ensure_number(v2), 6)
            if v < v2:
                return -1
            elif v > v2:
                return 1
            else:
                return 0
        if isinstance(v, YuiData) and isinstance(v2, YuiData):
            array = [YuiData.yui_to_native(e) for e in v.array]
            array2 = [YuiData.yui_to_native(e) for e in v2.array]
            if array < array2:
                return -1
            elif array > array2:
                return 1
            else:
                return 0
        raise YuiError(("error", "incomparable", f"❌{v}", f"❌{v2}"), node, env)

    def get(self, index: int, node = None, env = None) -> Any:
        if YuiData.is_string(index):
            key = YuiData.ensure_string(index)
            YuiData.type_check(self, 'object', node, env)
            obj = YuiData.ensure_object(self)
            return obj.get(key) #, None)
        YuiData.type_check(index, 'number', node, env)
        index = int(YuiData.ensure_number(index))
        if self.elements is None:
            self.sync()
        if index < 0 or index >= len(self.elements):
            raise YuiError(("error", "index", f"✅<{(len(self.elements))}", f"❌{index}", f"🔍{self.elements}"), node, env)
        return self.elements[index]

    def set(self, index: int, value: Any, node = None, env = None) -> Any:
        if YuiData.is_string(index):
            key = YuiData.ensure_string(index)
            YuiData.type_check(self, 'object', node, env)
            self.native[key] = value
            self.elements = None
        else:
            YuiData.type_check(index, 'number', node, env)
            index = int(YuiData.ensure_number(index))
            array = self.array
            if index < 0 or index >= len(array):
                raise YuiError(("error", "index", f"✅<{(len(self.elements))}", f"❌{index}", f"🔍{array}"), node, env)
            array[index] = value
            self.native_value = None

    def append(self, value: Any, node = None, env = None) -> Any:
        self.array.append(value)

    def __str__(self):
        """文字列表現を返す"""
        return self.stringfy(indent_prefix=None)

    def __repr__(self):
        """デバッグ用文字列表現を返す"""
        return str(self.native)

def standard_lib(modules: list):
    """
    標準ライブラリを環境に追加する

    以下の関数が使用可能になります：
    - 絶対値(x): 絶対値
    - 乱数(): ランダムな少数
    - 乱整数(x): 0以上x未満のランダムな整数
    - 和(x, y, ...): 要素の合計
    - 差(x, y, ...): 要素の差
    - 積(x, y, ...): 要素の積
    - 商(x, y, ...): 要素の商
    - 剰余(x, y): 剰余
    - 最大値(x, y, ...): 最大値
    - 最小値(x, y, ...): 最小値

    - 論理積(x, y, ...): ビット単位の論理積
    - 論理和(x, y, ...): ビット単位の論理和
    - 排他的論理和(x, y, ...): ビット単位の排他的論理和
    - ビット反転(x): ビット単位の反転
    - 左シフト(x, n): xをnビット左シフト
    - 右シフト(x, n): xをnビット右シフト   

    - 配列化(x): 配列に変換
    - 文字列化(x): 文字列に変換
    - 少数化(x): 少数に変換
    - 整数化(x): 整数に変換
    - 整数判定(x): 整数かどうか
    - 少数判定(x): 少数かどうか
    - 文字列判定(x): 文字列かどうか
    - オブジェクト化(x): オブジェクトに変換
    - オブジェクト判定(x): オブジェクトかどうか

    Args:
        env: 関数を追加する環境
    """
    import random
    import json

    def check_number_of_args(args: List[Any], expected: int) -> None:
        """関数の引数の数をチェックする"""
        if expected == -1: #少なくとも一つの引数が必要
            if len(args) < 1:
                raise YuiError(("required", "arguments", f"❌{len(args)}", f"✅>0"))
            return
        if len(args) != expected:
            raise YuiError(("expected", "arguments", f"✅{expected}", f"❌{len(args)}"))

    def array_to_varargs(args:list) -> list:
        """引数が配列1つの場合、その要素を展開して返す"""
        if len(args) == 1 and isinstance(args[0], YuiData):
            return args[0].array
        return args

    def yui_abs(*args: Any) -> Any:
        """絶対値を返す"""
        check_number_of_args(args, 1)
        if YuiData.is_float(args[0]):
            value = YuiData.ensure_float(args[0])
            return YuiData(abs(value))
        return abs(YuiData.ensure_int(args[0]))
    modules.append(('📏|絶対値|abs', yui_abs))

    def yui_random(*args: Any) -> Any:
        """ランダムな整数を返す"""
        check_number_of_args(args, 0)
        return YuiData(random.random())
    modules.append(('🎲📊|乱数|random', yui_random))
    
    def yui_randint(*args: Any) -> Any:
        """0以上x未満のランダムな整数を返す"""
        check_number_of_args(args, 1)
        x = YuiData.ensure_int(args[0])
        if x <= 0:
            raise YuiError(("error", "invalid argument", f"❌{x}", f"✅>0"))
        return YuiData(random.randint(0, x - 1))
    modules.append(('🎲|乱整数|randint', yui_randint))

    def yui_and(*args: Any) -> int:
        """論理積を返す"""
        args = array_to_varargs(args)
        total = YuiData.ensure_int(args[0])
        for arg in args[1:]:
            total &= YuiData.ensure_int(arg)
        return total
    modules.append(('💡✖️|論理積|and', yui_and))

    def yui_or(*args: Any) -> int:
        """論理和を返す"""
        args = array_to_varargs(args)
        total = YuiData.ensure_int(args[0])
        for arg in args[1:]:
            total |= YuiData.ensure_int(arg)
        return total
    modules.append(('💡✖️|論理和|or', yui_or))

    def yui_xor(*args: Any) -> Any:
        """排他的論理和を返す"""
        args = array_to_varargs(args)
        total = YuiData.ensure_int(args[0])
        for arg in args[1:]:
            total ^= YuiData.ensure_int(arg)
        return total
    modules.append(('💡✖️|排他的論理和|xor', yui_xor))

    def yui_not(*args: Any) -> Any:
        """ビット反転を返す"""
        check_number_of_args(args, 1)
        return ~(YuiData.ensure_int(args[0]))
    modules.append(('💡🔄|ビット反転|not', yui_not))

    def yui_left_shift(*args: Any) -> Any:
        """左シフトを返す"""
        check_number_of_args(args, 2)
        return YuiData.ensure_int(args[0]) << YuiData.ensure_int(args[1])
    modules.append(('💡⬅️|左シフト|left_shift', yui_left_shift))
    
    def yui_right_shift(*args: Any) -> Any:
        """右シフトを返す"""
        check_number_of_args(args, 2)
        return YuiData.ensure_int(args[0]) >> YuiData.ensure_int(args[1])
    modules.append(('💡➡️|右シフト|right_shift', yui_right_shift))

    def has_float_in_args(args: List[Any]) -> bool:
        """引数リストに少数が含まれているかどうかを判定する"""
        for arg in args:
            if YuiData.is_float(arg):
                return True
        return False
    
    def yui_sum(*args: Any) -> Any:
        """要素の合計を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_in_args(args):
            total = float(YuiData.ensure_number(args[0]))
            for arg in args[1:]:
                total += YuiData.ensure_number(arg)
            return YuiData(total)
        else:
            total = YuiData.ensure_int(args[0])
            for arg in args[1:]:
                total += YuiData.ensure_int(arg)
            return total
    modules.append(('➕|和|sum', yui_sum))

    def yui_sub(*args: Any) -> Any:
        """要素の差を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_in_args(args):
            total = YuiData.ensure_number(args[0])
            for arg in args[1:]:
                total -= YuiData.ensure_number(arg)
            return YuiData(total)
        else:
            total = YuiData.ensure_int(args[0])
            for arg in args[1:]:
                total -= YuiData.ensure_int(arg)
            return total
    modules.append(('➖|差|sub', yui_sub))

    def yui_accum(*args: Any) -> Any:
        """要素の積を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_in_args(args):
            total = float(YuiData.ensure_number(args[0]))
            for arg in args[1:]:
                total *= YuiData.ensure_number(arg)
            return YuiData(total)
        else:
            total = YuiData.ensure_int(args[0])
            for arg in args[1:]:
                total *= YuiData.ensure_int(arg)
            return total
    modules.append(('✖️|積|accum', yui_accum))

    def yui_div(*args: Any) -> Any:
        """要素の商を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_in_args(args):
            total = float(YuiData.ensure_number(args[0]))
            for arg in args[1:]:
                d = float(YuiData.ensure_number(arg))
                if d == 0.0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"))
            return YuiData(total)
        else:
            total = YuiData.ensure_int(args[0])
            for arg in args[1:]:
                d = YuiData.ensure_int(arg)
                if d == 0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"))
                total //= d
            return total
    modules.append(('➗|商|div', yui_div))

    def yui_mod(*args: Any) -> Any:
        """剰余を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_in_args(args):
            total = float(YuiData.ensure_number(args[0]))
            for arg in args[1:]:
                d = float(YuiData.ensure_number(arg))
                if d == 0.0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"))
                total %= d
            return YuiData(total)
        else:
            total = YuiData.ensure_int(args[0])
            for arg in args[1:]:
                d = YuiData.ensure_int(arg)
                if d == 0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"))
                total %= d
            return total
    modules.append(('🧮|剰余|mod', yui_mod))

    def yui_max(*args: Any) -> Any:
        """最大値を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        result = max(YuiData.ensure_number(arg) for arg in args)
        if isinstance(result, float):
            return YuiData(result)
        return int(result)
    modules.append(('📏|最大値|max', yui_max))

    def yui_min(*args: Any) -> Any:
        """最小値を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        result = min(YuiData.ensure_number(arg) for arg in args)
        if isinstance(result, float):
            return YuiData(result)
        return int(result)
    modules.append(('📏|最小値|min', yui_min))

    def yui_isint(*args: Any) -> Any:
        """整数判定に変換する"""
        check_number_of_args(args, 1)
        return 1 if isinstance(args[0], int) else 0
    modules.append(('🔢❓|整数判定|isint', yui_isint))

    def yui_toint(*args: Any) -> Any:
        """整数化する"""
        check_number_of_args(args, 1)
        value = args[0]
        if YuiData.is_string(value):
            string_value = value.to_string()
            try:
                return int(string_value)
            except ValueError:
                raise YuiError((f"error", "conversion", f"❌{string_value}"))
        value = int(YuiData.ensure_number(args[0]))
        return value
    modules.append(('🔢|整数化|toint', yui_toint))

    def yui_todecimal(*args: Any) -> Any:
        """小数化する"""
        check_number_of_args(args, 1)
        value = args[0]
        if YuiData.is_string(value):
            string_value = value.to_string()
            try:
                return YuiData(float(string_value))
            except ValueError:
                raise YuiError((f"error", "conversion", f"❌{string_value}"))
        value = float(YuiData.ensure_number(args[0]))
        return YuiData(value)
    modules.append(('📊|少数化|todecimal', yui_todecimal))

    def yui_isdecimal(*args: Any) -> Any:
        """小数判定に変換する"""
        check_number_of_args(args, 1)
        return 1 if YuiData.is_float(args[0]) else 0
    modules.append(('📊❓|少数判定|isdecimal', yui_isdecimal))

    def yui_isstring(*args: Any) -> Any:
        """文字列判定に変換する"""
        check_number_of_args(args, 1)
        return 1 if YuiData.is_string(args[0]) else 0
    modules.append(('🔤❓|文字列判定|isstring', yui_isstring))

    def yui_tostring(*args: Any) -> Any:
        """文字列に変換する"""
        check_number_of_args(args, 1)
        if YuiData.is_float(args[0]):
            v = YuiData.ensure_float(args[0])
            return YuiData(f"{v:.6f}")
        return YuiData(str(args[0]))
    modules.append(('🔤|文字列化|tostring', yui_tostring))

    def yui_isobject(*args: Any) -> Any:
        """オブジェクト判定に変換する"""
        check_number_of_args(args, 1)
        return 1 if YuiData.is_object(args[0]) else 0
    modules.append(('🗂️❓|オブジェクト判定|isobject', yui_isobject))

    def yui_toobject(*args: Any) -> Any:
        """オブジェクトに変換する"""
        check_number_of_args(args, 1)
        if YuiData.is_string(args[0]):
            s = YuiData.ensure_string(args[0])
            if s.startswith('{'):
                try:
                    v = json.loads(s) # JSONとしてパースできるか確認
                    return YuiData(v)
                except json.JSONDecodeError:
                    pass
            return YuiData({})
        return YuiData(str(args[0]))
    modules.append(('🗂️|オブジェクト化|toobject', yui_toobject))

    def yui_toarray(*args: Any) -> Any:
        """配列に変換する"""
        check_number_of_args(args, 1)
        if isinstance(args[0], YuiData):
            args[0].view = "array"
            args[0].native_value = None
            return args[0]
        return YuiData(YuiData.ensure_int(args[0]))
    modules.append(('🚃|配列化|toarray', yui_toarray))


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
class NullNode(ExpressionNode):
    """null値（?）を表すノード"""
    def __init__(self):
        super().__init__()

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiData]:
        """None を返す"""
        return YuiData([])

@dataclass
class NumberNode(ExpressionNode):
    """数値リテラルを表すノード"""
    value: Union[int, float]

    def __init__(self, value: Union[int, float]):
        super().__init__()
        self.value = value

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiData]:
        """数値を返す（浮動小数点数はYuiDataに変換）"""
        if isinstance(self.value, float):
            return YuiData(self.value)
        return self.value

@dataclass
class ArrayLenNode(ExpressionNode):
    """配列の長さ（|配列|）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiData]:
        """配列の長さを返す"""
        value = self.element.evaluate(runtime)
        YuiData.type_check(value, 'data', self.element, runtime)
        return len(value.array)

@dataclass
class MinusNode(ExpressionNode):
    """負の数（-式）を表すノード"""
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def evaluate(self, runtime: YuiRuntime) -> Union[int, YuiData]:
        """式を評価して符号を反転する"""
        value = self.element.evaluate(runtime)
        YuiData.type_check(value, 'number', self.element, runtime)
        value = YuiData.ensure_number(value)
        if isinstance(value, float):
            return YuiData(-value)
        return -value

@dataclass
class StringNode(ExpressionNode):
    """文字列リテラル（"..."）を表すノード"""
    contents: Union[str, List[Union[str, ExpressionNode]]]

    def __init__(self, contents: Union[str, List[Union[str, ExpressionNode]]]):
        super().__init__()
        self.contents = contents

    def evaluate(self, runtime: YuiRuntime) -> Union[YuiData, int]:
        if isinstance(self.contents, str):
            return YuiData(self.contents)
        string_values = []
        for content in self.contents:
            if isinstance(content, str):
                string_values.append(content)
            else: # string埋め込み式
                value = content.evaluate(runtime)
                value = YuiData.yui_to_native(value)
                string_values.append(f'{value}')
        return YuiData(''.join(string_values))

@dataclass
class ArrayNode(ExpressionNode):
    """配列リテラル（[要素, ...]）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [node(e) for e in elements]

    def evaluate(self, runtime: YuiRuntime):
        """各要素を評価してYuiDataを作成する"""
        array_content = [element.evaluate(runtime) for element in self.elements]
        return YuiData(array_content)

@dataclass
class ObjectNode(ExpressionNode):
    """辞書リテラル（{要素, ...}）を表すノード"""
    elements: List[Any]

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = [node(e) for e in elements]

    def evaluate(self, runtime: YuiRuntime)-> Union[YuiData, int]:
        """各要素を評価してYuiDataを作成する"""
        object_content = {}
        for i in range(0, len(self.elements), 2):
            key = self.elements[i].evaluate(runtime)
            value = self.elements[i+1].evaluate(runtime)
            YuiData.type_check(key, 'string', self.elements[i], runtime)
            key = YuiData.ensure_string(key)
            object_content[key] = value
        return YuiData(object_content)

@dataclass
class NameNode(ExpressionNode):
    """変数参照を表すノード"""
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def evaluate(self, runtime: YuiRuntime)-> Union[YuiData, int]:
        """変数の値を返す（インデックスがあれば配列要素を返す）"""
        if not runtime.hasenv(self.name):
            raise YuiError(("undefined", "variable", f"❌{self.name}"), self, runtime)
        return runtime.getenv(self.name)
    
    def update(self, value: Any, runtime: YuiRuntime):
        """変数の値を更新する"""
        runtime.setenv(self.name, value)

@dataclass
class GetIndexNode(ASTNode):
    """配列またはオブジェクトのインデックス取得を表すノード"""
    collection: ExpressionNode
    index_node: ExpressionNode

    def __init__(self, collection: ExpressionNode, index: ExpressionNode):
        super().__init__()
        self.collection = node(collection)
        self.index_node = node(index)

    def evaluate(self, runtime: YuiRuntime)-> Union[YuiData, int]:
        """配列またはオブジェクトから値を取得する"""
        collection_value = self.collection.evaluate(runtime)
        index_value = self.index_node.evaluate(runtime)
        YuiData.type_check(collection_value, 'data', self.collection, runtime)
        return collection_value.get(index_value, self.index_node, runtime)
    
    def update(self, value: Any, runtime: YuiRuntime):
        """変数の値を更新する"""
        collection_value = self.collection.evaluate(runtime)
        index_value = self.index_node.evaluate(runtime)
        YuiData.type_check(collection_value, 'data', self.collection, runtime)
        return collection_value.set(index_value, value,self.index_node, runtime)

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

    def evaluate(self, runtime):
        pass


class YuiFunction(ABC):
    name: str
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def call(self, arguments: List[Any], node: ASTNode, runtime: YuiRuntime) -> Union[YuiData, int]:
        pass

class LocalFunction(YuiFunction):
    """ユーザが関数の型"""
    
    def __init__(self, name: str, parameters: List[str], body: ASTNode):
        super().__init__(name)
        self.parameters = parameters
        self.body = body

    def call(self, arguments: List[Any], node: ASTNode, runtime: YuiRuntime) -> Union[YuiData, int]:
        # 新しい環境を作成
        runtime.pushenv()
        if len(self.parameters) != len(arguments):
            raise YuiError(("mismatch", "arguments", f"✅{len(self.parameters)}", f"❌{len(arguments)}"), node, runtime)

        for parameter, parameter_value in zip(self.parameters, arguments):
            runtime.setenv(parameter, parameter_value)

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
        return YuiData(runtime.popenv())
        
class NativeFunction(YuiFunction):
    """ネイティブ関数の型"""
    is_ffi: bool = True
    name: str
    function: callable

    def __init__(self, function: callable, is_ffi=False):
        super().__init__(function.__name__)
        self.function = function
        self.is_ffi = is_ffi

    def call(self, arguments: List[Any], node: ASTNode, runtime: YuiRuntime) -> Union[YuiData, int]:
        try:
            return self.function(*arguments)
        except YuiError as e:
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

    def evaluate(self, runtime: YuiRuntime):
        """関数を呼び出して結果を返す"""
        if isinstance(self.name_node, NameNode):
            name = f'@{self.name_node.name}'
            if not runtime.hasenv(name):
                raise YuiError(("undefined", "function", f"❌{self.name_node.name}"), self.name_node, runtime)
            function = runtime.getenv(name)
        if not isinstance(function, YuiFunction):
            raise YuiError(("error", "type", "✅<function>", f"❌{function}"), self.name_node, runtime)
        arguments = [argument.evaluate(runtime) for argument in self.arguments]
        if self.snippet == '':
            args = ', '.join(f'{arg}' for arg in arguments)
            self.snippet = f'{self.name_node}({args})'
        return function.call(arguments, self, runtime)


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

    def evaluate(self, runtime: YuiRuntime):
        """式を評価して変数に代入する"""
        value = self.expression.evaluate(runtime)
        if not hasattr(self.variable, 'update'):
            raise YuiError(("expected", "variable", f"❌{self.variable}"), self.variable, runtime)
        self.variable.update(value, runtime)

@dataclass
class IncrementNode(StatementNode):
    """インクリメント（変数 を 増やす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)

    def evaluate(self, runtime: YuiRuntime):
        """変数を1増やす"""
        value = self.variable.evaluate(runtime)
        YuiData.type_check(value, 'int', self.variable, runtime)
        self.variable.update(value + 1, runtime)
        runtime.count_inc()


@dataclass
class DecrementNode(StatementNode):
    """デクリメント（変数 を 減らす）を表すノード"""
    variable: NameNode

    def __init__(self, variable: NameNode):
        super().__init__()
        self.variable = NameNode(variable) if isinstance(variable, str) else node(variable)

    def evaluate(self, runtime: YuiRuntime):
        """変数を1減らす"""
        value = self.variable.evaluate(runtime)
        YuiData.type_check(value, 'int', self.variable, runtime)
        self.variable.update(value - 1, runtime)
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

    def evaluate(self, runtime: YuiRuntime):
        """値を評価して配列に追加する"""
        array = self.variable.evaluate(runtime)
        YuiData.type_check(array, 'array', self.variable, runtime)
        array.append(self.expression.evaluate(runtime))


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

    def evaluate(self, runtime: YuiRuntime):
        """条件を評価して適切なブロックを実行する"""
        left_value = self.left.evaluate(runtime)
        right_value = self.right.evaluate(runtime)
        result = self.operator.evaluate(left_value, right_value, self, runtime)
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

    def evaluate(self, runtime: YuiRuntime):
        raise YuiBreakException()


@dataclass
class PassNode(StatementNode):
    def __init__(self, comment: Optional[str] = None):
        super().__init__()
        self.comment = comment

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

    def evaluate(self, runtime: YuiRuntime):
        """ループを実行する"""
        count = self.count_node.evaluate(runtime)
        YuiData.type_check(count, 'int', self.count_node, runtime)
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

    def evaluate(self, runtime: YuiRuntime):
        """式を評価して期待値と比較する"""
        test_value = self.test.evaluate(runtime)
        reference_value = self.reference.evaluate(runtime)
        try:
            if YuiData.compare(test_value, reference_value, self.test, runtime) == 0:
                runtime.test_passed.append(str(self.test))
                return
        except Exception as e:
            pass
        raise YuiError(("failed", "test", f"🔍{self.test}", f"❌{test_value}", f"✅{reference_value}"), self, runtime)

