from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

from .yuiast import ASTNode, set_operators


ERROR_MESSAGES = {
    # パーサーエラー
    "expected-token":           "トークンが不正です",
    "expected-number":          "数値が必要です",
    "expected-string":          "文字列が必要です",
    "expected-array":           "配列が必要です",
    "expected-object":          "オブジェクトが必要です",
    "expected-boolean":         "真偽値が必要です",
    "expected-closing":         "閉じ括弧が必要です",
    "expected-variable":        "変数が必要です",
    "frequent-mistake":         "よくある間違いです",
    "wrong-name":               "名前が不正です",
    "wrong-statement":          "不正な文です",
    "wrong-escape-sequence":    "不正なエスケープシーケンスです",
    "wrong-indent-level":       "インデントが不正です",
    # ランタイムエラー
    "undefined-variable":       "変数が未定義です",
    "undefined-function":       "関数が未定義です",
    "type-error":               "型エラーです",
    "division-by-zero":         "ゼロ除算です",
    "error-index":              "インデックスエラーです",
    "error-value":              "値エラーです",
    "too-many-recursions":      "再帰が深すぎます",
    "runtime-timeout":          "タイムアウトです",
    "unsupported-operator":     "サポートされていない演算子です",
    "unsupported-comparison":   "サポートされていない比較です",
    "mismatch-argument-number": "引数の数が合いません",
    "not-negative-number":      "負の数は使えません",
    "float-conversion":         "少数への変換エラーです",
    "internal-error":           "内部エラーです",
    "immutable":                "変更できません",
    "array-format":             "配列フォーマットエラーです",
}


def _format_messages(messages: tuple) -> str:
    """先頭キーを ERROR_MESSAGES で置き換えて表示用文字列を返す"""
    if not messages:
        return ""
    key = messages[0]
    display = ERROR_MESSAGES.get(key, key)
    rest = ' '.join(messages[1:])
    return f"{display} {rest}".strip() if rest else display


def _normalize_messages(messages) -> tuple:
    """非絵文字の連続する文字列を '-' で結合する。絵文字（ord > 127）で始まる文字列は独立要素として残す。"""
    if isinstance(messages, str):
        messages = (messages,)
    result = []
    parts: list = []
    for msg in messages:
        if msg and ord(msg[0]) > 127:
            if parts:
                result.append('-'.join(parts))
                parts = []
            result.append(msg)
        else:
            parts.append(msg)
    if parts:
        result.append('-'.join(parts))
    return tuple(result)


class YuiError(RuntimeError):
    """Yui言語のエラーを表現するクラス"""
    messages: tuple
    error_node: Optional[ASTNode]
    BK: bool

    def __init__(self, messages: tuple, error_node: Optional[ASTNode] = None,
                 BK: bool = False):
        """YuiErrorを初期化する"""
        self.messages = _normalize_messages(messages)
        super().__init__(' '.join(self.messages))
        self.error_node = error_node if isinstance(error_node, ASTNode) else None
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

    def formatted_message(self, prefix: str = " ", marker: str = '^', lineoffset: int = 0) -> str:
        """構文エラーとして整形したメッセージを返す。ランタイムエラーは YuiRuntime.format_error() を使うこと。"""
        message = _format_messages(self.messages)
        if self.error_node:
            line, col, snippet = self.error_node.extract()
            length = max(self.error_node.end_pos - self.error_node.pos, 3) if self.error_node.end_pos is not None else 3
            make_pointer = marker * min(length, 16)
            snippet = snippet.split('\n')[0]
            indent = " " * (col - 1)
            message = f"{message} line {line + lineoffset}, column {col}:\n{prefix}{snippet}\n{prefix}{indent}{make_pointer}"
        return f"[構文エラー/SyntaxError] {message}"

TY_NULL = '⛔'
TY_BOOLEAN = '🔘'
TY_INT = '💯'
TY_FLOAT = '📊'
TY_NUMBER = '🔢'
TY_ARRAY = '🍡'
TY_OBJECT = '🗂️'
TY_STRING = '💬'

@dataclass
class YuiType(ABC):
    """Yui言語の型を表現するクラス"""
    name: str
    emoji: str

    def __init__(self, name: str, emoji: str):
        self.name = name
        self.emoji = emoji

    def __str__(self):
        return self.emoji

    @abstractmethod
    def match(self, value: Any) -> bool:
        pass

    def match_or_raise(self, node_or_value = None):
        value = node_or_value
        if not self.match(value):
            raise YuiError(("type-error", f"✅<{self.emoji}{self.name}>", f"❌{value}"), node_or_value)

    @abstractmethod
    def to_arrayview(self, n: int) -> List[int]:
        pass

    @abstractmethod
    def to_native(self, elements: List[int], node=None) -> Any:
        pass

    @abstractmethod
    def stringfy(self, native_value: Any, indent_prefix: str = "", width=80) -> str:
        pass
    
    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_value = YuiType.to_native((left_node))
        right_value = YuiType.to_native((right_node))
        return left_value == right_value    

    def less_than(self, left_node: Any, right_node: Any, op = "<") -> bool:
        left_value = left_node
        right_value = right_node
        raise YuiError(("unsupported", "comparison", f"❌{left_value} {op} {right_value}"), left_node)


    # クラス変数として各型のインスタンスを定義
    NullType: 'YuiNullType' = None
    BooleanType: 'YuiBooleanType' = None
    IntType: 'YuiIntType' = None
    FloatType: 'YuiFloatType' = None
    NumberType: 'YuiNumberType' = None
    StringType: 'YuiStringType' = None
    ArrayType: 'YuiArrayType' = None
    ObjectType: 'YuiObjectType' = None

    @staticmethod
    def evaluated(value: Any) -> Any:
        return value

    @staticmethod
    def is_bool(node_or_value: Any) -> bool:
        return YuiType.BooleanType.match(node_or_value)

    @staticmethod
    def is_int(node_or_value: Any) -> bool:
        return YuiType.IntType.match(node_or_value)

    @staticmethod
    def is_float(node_or_value: Any) -> bool:
        return YuiType.FloatType.match(node_or_value)

    @staticmethod
    def is_number(node_or_value: Any) -> bool:
        return YuiType.NumberType.match(node_or_value)      
    
    @staticmethod
    def is_string(node_or_value: Any) -> bool:
        return YuiType.StringType.match(node_or_value)

    @staticmethod
    def is_array(node_or_value: Any) -> bool:
        return YuiType.ArrayType.match(node_or_value)

    @staticmethod
    def is_object(node_or_value: Any) -> bool:
        return YuiType.ObjectType.match(node_or_value)

    @staticmethod
    def matched_native(node_or_value) -> None:
        value = node_or_value
        if isinstance(value, YuiValue):
            return value.native
        return value # 型チェック済みを想定

    @staticmethod
    def from_arrayview(value: Any) -> 'YuiValue':
        if isinstance(value, YuiValue):
            return value
        return YuiValue(value)

    @staticmethod
    def into_arrayview(node_or_value) -> Any:
        value = node_or_value
        if isinstance(value, YuiValue) and value.is_primitive():
            return value.native
        if isinstance(value, (int, float, str)) or value is None:
            return value
        return YuiValue(value)

    @staticmethod
    def arrayview_s(value):
        if value is None:
            return "null"
        elif isinstance(value, str):
            value = value.replace('"', '\\"').replace('\n', '\\n')
            return f'"{value}"'
        elif isinstance(value, float):
            return f"{value:.6f}"
        else:
            return str(value)
    
    @staticmethod
    def to_native(node_or_value) -> Any:
        value = node_or_value
        if isinstance(value, YuiValue):
            return value.native
        if isinstance(value, list):
            return [YuiType.to_native(v) for v in value]
        if isinstance(value, dict):
            return {str(k): YuiType.to_native(v) for k, v in value.items()}
        return value

    @staticmethod
    def native_to_yui(native_value) -> Any:
        """ネイティブ値をYui形式に変換して返す"""
        if native_value is None:
            return YuiValue.NullValue
        if isinstance(native_value, bool):
            return YuiValue.TrueValue if native_value else YuiValue.FalseValue
        if isinstance(native_value, (int, float, list, str, dict, tuple)):
            return YuiValue(native_value)
        assert isinstance(native_value, YuiValue)
        return native_value

    @staticmethod
    def yui_to_native(value: Any) -> Any:
        """Yui形式の値をネイティブ値に変換して返す"""
        if isinstance(value, YuiValue):
            return value.native
        if isinstance(value, list):
            return [YuiType.yui_to_native(e) for e in value]
        if isinstance(value, dict):
            new_value = {}
            for key, item in value.items():
                new_value[key] = YuiType.yui_to_native(item)
            return new_value
        return value

    @staticmethod
    def compare(left_node_or_value, right_node_or_value: Any) -> int:
        print(f"Comparing {left_node_or_value} and {right_node_or_value}")
        if YuiType.is_number(left_node_or_value) and YuiType.is_number(right_node_or_value):
            left_value = round(YuiType.matched_native(left_node_or_value), 6)
            right_value = round(YuiType.matched_native(right_node_or_value), 6)
            return _compare(left_value, right_value)
        if YuiType.is_string(left_node_or_value) and YuiType.is_string(right_node_or_value):
            left_value = YuiType.matched_native(left_node_or_value)
            right_value = YuiType.matched_native(right_node_or_value)
            return _compare(left_value, right_value)
        left_value = left_node_or_value
        right_value = right_node_or_value        
        if not isinstance(right_value, YuiValue):
            right_value = YuiValue(right_value.native)
        return _compare(left_value.arrayview, right_value.arrayview)

def _compare(left, right) -> int:
    if left == right:
        return 0
    if left < right:
        return -1
    else:
        return 1

class YuiNullType(YuiType):
    def __init__(self):
        super().__init__("null", TY_NULL)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return value is None or (isinstance(value, YuiValue) and isinstance(value.type, YuiNullType))

    def check_element(self, node_or_value: Any) -> None:
        raise YuiError(("immutable", f"❌{self}"), node_or_value)

    def to_arrayview(self, n: None) -> List[int]:
        return []

    def to_native(self, elements: List[int], node=None) -> None:
        return None
    
    def stringfy(self, native_value: None, indent_prefix: str = "", width=80) -> str:
        return "null"

class YuiBooleanType(YuiType):
    def __init__(self):
        super().__init__("boolean", TY_BOOLEAN)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        # Python の bool は int のサブクラスなので先に isinstance(value, bool) でチェックする
        return isinstance(value, bool) or (isinstance(value, YuiValue) and isinstance(value.type, YuiBooleanType))

    def check_element(self, node_or_value: Any) -> None:
        raise YuiError(("immutable", f"❌{self}"), node_or_value)

    def to_arrayview(self, n: bool) -> List[int]:
        return [1] if n else []

    def to_native(self, elements: List[int], node=None) -> bool:
        return len(elements) > 0

    def stringfy(self, native_value: bool, indent_prefix: str = "", width=80) -> str:
        return "true" if native_value else "false"

    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_value = YuiType.to_native(left_node)
        right_value = YuiType.to_native(right_node)
        if isinstance(right_value, bool):
            return left_value == right_value
        return False

    def less_than(self, left_node: Any, right_node: Any, op: str = "<") -> bool:
        left_value = YuiType.to_native(left_node)
        right_value = YuiType.to_native(right_node)
        if isinstance(right_value, bool):
            return left_value < right_value
        return super().less_than(left_node, right_node, op=op)


class YuiIntType(YuiType):
    def __init__(self):
        super().__init__("int", TY_INT)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, int) or (isinstance(value, YuiValue) and isinstance(value.type, YuiIntType))

    def check_element(self, node_or_value: Any) -> None:
        YuiType.IntType.match_or_raise(node_or_value)
        value = self.matched_native(node_or_value)
        if value != 0 and value != 1:
            raise YuiError(("error", "value", f"✅0/1", f"❌{value}"), node_or_value)

    def to_arrayview(self, n: int) -> List[int]:
        """整数を32ビットの2の補数表現の整数配列に変換"""
        # 32ビットにマスク（符号なし整数として扱う）
        n_unsigned = n & 0xFFFFFFFF    
        # 各ビットを抽出（MSBからLSBへ）
        bits = []
        for i in range(31, -1, -1):
            value = (n_unsigned >> i) & 1
            bits.append(value) # int はそのまま
        return bits

    def to_native(self, bits: List[int], node=None) -> int:
        """32ビットの2の補数表現の整数配列を整数に変換"""
        if len(bits) != 32:
            raise YuiError(("array", "format", f"❌{len(bits)}", "✅32"), node)
        
        # ビット列を符号なし整数に変換
        n_unsigned = 0
        for bit in bits:
            n_unsigned = (n_unsigned << 1) | bit
        
        # 32ビット符号付き整数に変換（2の補数）
        if n_unsigned >= 0x80000000:  # MSBが1（負数）
            n = n_unsigned - 0x100000000
        else:
            n = n_unsigned        
        return n
    
    def stringfy(self, native_value: int, indent_prefix: str = "", width=80) -> str:
        return f"{native_value}"
    
    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_value = YuiType.to_native(left_node)
        right_value = YuiType.to_native(right_node)
        if isinstance(right_value, bool):
            return False  # bool は IntType と等しくない
        if isinstance(right_value, float):
            return round(float(left_value), 6) == round(right_value, 6)
        return left_value == right_value

    def less_than(self, left_node: Any, right_node: Any, op = "<") -> bool:
        left_value = YuiType.to_native(left_node)
        right_value = YuiType.to_native(right_node)
        if isinstance(right_value, float):
            return round(float(left_value), 6) < round(right_value, 6)
        if isinstance(right_value, int):
            return left_value < right_value
        super().less_than(left_node, right_node, op=op)
    

class YuiFloatType(YuiType):
    def __init__(self):
        super().__init__("float", TY_FLOAT)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, float) or (isinstance(value, YuiValue) and isinstance(value.type, YuiFloatType))

    def check_element(self, node_or_value: Any) -> None:
        YuiType.IntType.match_or_raise(node_or_value)
        value = self.matched_native(node_or_value)
        if value < -1 or value > 9:
            raise YuiError(("error", "value", f"✅-1,0-9", f"❌{value}"), node_or_value)

    def to_arrayview(self, x: float) -> List[int]:
        """浮動小数点数を符号付き一桁整数配列に変換
        Example:
            [1, 3, 1, 4, 0, 0, 0, 0]  # 3.140000
            [-1, 2, 5, 0, 0, 0, 0, 0]  # -2.500000
        """
        sign = -1 if x < 0 else 1
        s = f"{abs(x):.6f}"  # 小数点以下6桁に丸める
        s = s.replace('.', '')  # 小数点を削除
        digits = [sign] + [int(ch) for ch in s]
        return digits

    def to_native(self, digits: List[int], node=None) -> float:
        """符号付き一桁整数配列を浮動小数点数に変換
        Example:
            >>> array_to_float([1, 3, 1, 4, 0, 0, 0, 0])
            3.140000
            >>> array_to_float([-1, 2, 5, 0, 0, 0, 0, 0])
            -2.500000
        """
        sign = digits[0]
        if not(isinstance(sign, int) and sign in (1, -1)):
            raise YuiError(f"conversion", "tofloat", f"❌[0]{digits[0]}", f"✅1/-1", f"🔍{digits}", node)
        num_digits = digits[1:]
        for i, d in enumerate(num_digits, start=1):
            if not (isinstance(d, int) and 0 <= d <= 9):
                raise YuiError(f"conversion", "tofloat", f"❌[{i}]{d}", f"✅0-9", f"🔍{digits}", node)
        s = ''.join(str(d) for d in num_digits)
        if len(s) <= 6:
            # 小数部のみの場合（整数部なし）
            value = int(s)
        else:
            # 小数点を6桁前に挿入
            value = float(s[:-6] + '.' + s[-6:])
        return sign * value
    
    def stringfy(self, native_value: float, indent_prefix: str = "", width=80) -> str:
        return f"{native_value:.6f}"

    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_value = round(YuiType.to_native(left_node), 6)
        right_value = YuiType.to_native((right_node))
        if isinstance(right_value, (float, int)):
            return left_value == round(right_value, 6)
        return False   

    def less_than(self, left_node: Any, right_node: Any, op = "<") -> bool:
        left_value = YuiType.to_native(left_node)
        right_value = YuiType.to_native(right_node)
        if isinstance(right_value, (int, float)):
            return left_value < right_value
        super().less_than(left_node, right_node, op=op)

class YuiNumberType(YuiType):
    def __init__(self):
        super().__init__("number", TY_NUMBER)

    def match(self, node_or_value: Any) -> bool:
        return YuiType.IntType.match(node_or_value) or YuiType.FloatType.match(node_or_value)

    def check_element(self, node_or_value: Any) -> None:
        pass

    def to_arrayview(self, n: Union[int, float]) -> List[int]:
        if isinstance(n, float):
            return YuiType.FloatType.to_arrayview(n)
        else:
            return YuiType.IntType.to_arrayview(n)
    
    def to_native(self, bits: List[int], node=None) -> int:
        if len(bits) == 32:
            return YuiType.IntType.to_native(bits, node=node)
        else:
            return YuiType.FloatType.to_native(bits, node=node)
    
    def stringfy(self, native_value: int, indent_prefix: str = "", width=80) -> str:
        if isinstance(native_value, float):
            return YuiType.FloatType.stringfy(native_value, indent_prefix=indent_prefix, width=width)
        else:
            return YuiType.IntType.stringfy(native_value, indent_prefix=indent_prefix, width=width)

class YuiStringType(YuiType):
    def __init__(self):
        super().__init__("string", TY_STRING)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, str) or (isinstance(value, YuiValue) and isinstance(value.type, YuiStringType))

    def check_element(self, node_or_value: Any) -> None:
        YuiType.IntType.match_or_raise(node_or_value)

    def to_arrayview(self, x: str) -> List[int]:
        """文字コード"""
        return [ord(ch) for ch in x]

    def to_native(self, elements: List[int], node=None) -> str:
        return ''.join(chr(d) for d in elements)

    def stringfy(self, native_value: str, indent_prefix: str = "", width=80) -> str:
        content = native_value.replace('"', '\\"').replace('\n', '\\n')
        return f'"{content}"'
    
    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_value = YuiType.to_native(left_node)
        if YuiType.is_string(right_node):
            right_value = YuiType.matched_native(right_node)
            return left_value == right_value
        return False   

    def less_than(self, left_node: Any, right_node: Any, op = "<") -> bool:
        left_value = YuiType.to_native(left_node)
        if YuiType.is_string(right_node):
            right_value = YuiType.matched_native(right_node)
            return left_value < right_value
        return False

def _array_equal(a, b) -> bool:
    """配列の再帰的等価比較（文字コード配列と文字列の相互比較を含む）"""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_array_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, list) and isinstance(b, str):
        try:
            return ''.join(chr(c) for c in a) == b
        except (TypeError, ValueError):
            return False
    if isinstance(a, str) and isinstance(b, list):
        return _array_equal(b, a)
    return a == b


class YuiArrayType(YuiType):
    def __init__(self):
        super().__init__("array", TY_ARRAY)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, list) or (isinstance(value, YuiValue) and isinstance(value.type, YuiArrayType))
    
    def check_element(self, node_or_value: Any) -> None:
        pass

    def to_arrayview(self, array_value: list) -> List[int]:
        """配列の要素をエンコード"""
        return [YuiType.into_arrayview(value) for value in array_value]

    def to_native(self, elements: List[int], node=None) -> str:
        array = []
        for element in elements:
            if isinstance(element, YuiValue):
                array.append(element.native)
            else:
                array.append(element)
        return array
    
    def stringfy(self, elements: List[int], indent_prefix: str = "", width=80) -> str:
        buffer = ["["]
        for i, element in enumerate(elements):
            if i > 0:
                buffer.append(", ")
            buffer.append(f"{YuiType.arrayview_s(element)}")
        buffer.append("]")
        string_content = ''.join(buffer)
        if indent_prefix is None or len(indent_prefix) + len(string_content) <= width:
            return string_content
        inner_indent_prefix = indent_prefix + "  "
        LF = "\n"
        buffer = ["["]
        for i, element in enumerate(elements):
            buffer.append(f"{LF}{inner_indent_prefix}")
            if isinstance(element, YuiValue):
                buffer.append(element.stringfy(inner_indent_prefix, width=width))
            else:
                buffer.append(f"{YuiType.arrayview_s(element)}")
            if i < len(elements) - 1:
                buffer.append(",")
        buffer.append(f"{LF}{indent_prefix}]")
        return ''.join(buffer)

    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_native = YuiType.to_native(left_node)
        right_native = YuiType.to_native(right_node)
        return _array_equal(left_native, right_native)


class YuiObjectType(YuiType):
    def __init__(self):
        super().__init__("object", TY_OBJECT)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, dict) or (isinstance(value, YuiValue) and isinstance(value.type, YuiObjectType))

    def check_element(self, node_or_value: Any) -> None:
        global ArrayType, StringType
        ArrayType.match_or_raise(node_or_value)
        array = self.matched_native(node_or_value)
        if len(array) != 2 or not StringType.match(array[0]):
            raise YuiError(("error", "value", f"✅[key, value]", f"❌{array}"), node_or_value)

    def to_arrayview(self, object_value: dict) -> List[int]:
        """オブジェクトのキーと値をエンコード"""
        elements = []
        for key, value in object_value.items():
            elements.append(YuiValue([str(key), YuiType.into_arrayview(value)]))
        return elements

    def to_native(self, elements: List[int], node=None) -> str:
        obj = {}
        for key_value in elements:
            if not isinstance(key_value, YuiValue):
                raise YuiError(f"conversion", "toobject", f"❌{key_value}", f"✅[key, value]", f"🔍{elements}", node)
            key_value = key_value.native
            if not isinstance(key_value, list) or len(key_value) != 2:
                raise YuiError(f"conversion", "toobject", f"❌{key_value}", f"✅[key, value]", f"🔍{elements}", node)
            key = key_value[0]
            if not isinstance(key, str):
                raise YuiError(f"conversion", "toobject", f"❌{key}", f"✅<string>", f"🔍{key_value}", node)
            value = key_value[1]
            obj[key] = value
        return obj

    def stringfy(self, native_value: dict, indent_prefix: str = "", width=80) -> str:
        buffer = ["{"]
        for i, (key, value) in enumerate(native_value.items()):
            if i > 0:
                buffer.append(", ")
            buffer.append(f'"{key}": {YuiType.arrayview_s(value)}')
        buffer.append("}")
        string_content = ''.join(buffer)
        if indent_prefix is None or len(indent_prefix) + len(string_content) <= width:
            return string_content
        inner_indent_prefix = indent_prefix + "  "
        LF = "\n"
        buffer = ["{"]
        for i, (key, value) in enumerate(native_value.items()):
            buffer.append(f"{LF}{inner_indent_prefix}")
            buffer.append(f'"{key}": ')
            if isinstance(value, YuiValue):
                buffer.append(value.stringfy(inner_indent_prefix, width=width))
            else:
                buffer.append(f'{YuiType.arrayview_s(value)}')
            if i < len(native_value) - 1:
                buffer.append(",")
        buffer.append(f"{LF}{indent_prefix}}}")
        return ''.join(buffer)

    def equals(self, left_node: Any, right_node: Any) -> bool:
        left_native = YuiType.to_native(left_node)
        right_native = YuiType.to_native(right_node)
        if not isinstance(right_native, dict):
            return False
        if set(left_native.keys()) != set(right_native.keys()):
            return False
        return all(_array_equal(left_native[k], right_native[k]) for k in left_native)



YuiType.NullType = YuiNullType()
YuiType.BooleanType = YuiBooleanType()
YuiType.IntType = YuiIntType()
YuiType.FloatType = YuiFloatType()
YuiType.NumberType = YuiNumberType()
YuiType.StringType = YuiStringType()
YuiType.ObjectType = YuiObjectType()
YuiType.ArrayType = YuiArrayType()

# bool は Python で int のサブクラスなので BooleanType を IntType より先に置く
TYPES = [YuiType.NullType, YuiType.BooleanType, YuiType.IntType, YuiType.FloatType, YuiType.NumberType, YuiType.StringType, YuiType.ArrayType, YuiType.ObjectType]

def _typing(value: Any) -> YuiType:
    """値に対応するYuiTypeを返す"""
    for ty in TYPES:
        if ty.match(value):
            return ty
    raise ValueError(f"unknown type for value: {value}")

class YuiValue(object):
    """Yui言語のデータ型"""
    native_value: Optional[Union[str, float, dict, int]]
    type: YuiType
    elements: Optional[List[Any]]

    def __init__(self, native_value: Any, type: Optional[YuiType] = None):
        """YuiValueを初期化する"""
        self.native_value = YuiType.to_native(native_value)
        self.elements = None
        self.type = _typing(native_value) if type is None else type
    
    @property
    def native(self) -> Any:
        if self.native_value is None:
            self.native_value = self.type.to_native(self.elements)
        return self.native_value

    @property
    def arrayview(self):
        if self.elements is None:
            self.elements = self.type.to_arrayview(self.native_value)
        return self.elements

    def get_item(self, node_or_index: int) -> Any:
        if YuiType.is_string(node_or_index):
            key = YuiType.matched_native(node_or_index)
            if YuiType.is_object(self):
                obj = YuiType.matched_native(self)
                return YuiType.from_arrayview(obj.get(key, YuiValue.NullValue))
        
        YuiType.IntType.match_or_raise(node_or_index)
        index = YuiType.matched_native(node_or_index)
        elements = self.arrayview
        if index < 0 or index >= len(elements):
            raise YuiError(("error", "index", f"✅<{(len(elements))}", f"❌{index}", f"🔍{elements}"), node_or_index)
        return YuiType.from_arrayview(elements[index])
    
    def set_item(self, node_or_index: int, node_or_value: Any) -> Any:
        value = YuiType.into_arrayview(node_or_value)
        if YuiType.is_string(node_or_index):
            key = YuiType.matched_native(node_or_index)
            if YuiType.is_object(self):
                obj = YuiType.matched_native(self)
                obj[key] = value
                self.elements = None
                return
        YuiType.IntType.match_or_raise(node_or_index)
        index = YuiType.matched_native(node_or_index)
        elements = self.arrayview
        if index < 0 or index >= len(elements):
            raise YuiError(("error", "index", f"✅<{(len(elements))}", f"❌{index}", f"🔍{elements}"), node_or_index)
        self.type.check_element(node_or_value)
        elements[index] = value
        self.native_value = None

    def append(self, node_or_value: Any) -> Any:
        self.type.check_element(node_or_value)
        value = YuiType.into_arrayview(node_or_value)
        self.arrayview.append(value)
        self.native_value = None

    def is_primitive(self) -> bool:
        return isinstance(self.type, (YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType, YuiStringType))

    @staticmethod
    def stringfy_value(value: Any, indent_prefix: str = "", width=80) -> str:
        """YuiValue または任意の値を文字列に変換する（クラスメソッドとして呼び出し可能）"""
        if isinstance(value, YuiValue):
            return value.stringfy(indent_prefix=indent_prefix, width=width)
        return str(value)

    @property
    def array(self):
        """arrayview の別名（後方互換）"""
        return self.arrayview

    def stringfy(self, indent_prefix: str = "", arrayview: bool = False, width=80) -> str:
        if arrayview:
            elements =self.arrayview
            return YuiType.ArrayType.stringfy(elements, indent_prefix=indent_prefix, width=width)
        else:
            return self.type.stringfy(self.native, indent_prefix=indent_prefix, width=width)

    def equals(self, other_node: Any) -> bool:
        return self.type.equals(self, other_node)

    def less_than(self, other_node: Any, op = "<") -> bool:
        return self.type.less_than(self, other_node, op=op)

    def __str__(self):
        """文字列表現を返す"""
        return self.stringfy(indent_prefix=None)

    def __repr__(self):
        """デバッグ用文字列表現を返す"""
        return str(self.native)

YuiValue.NullValue = YuiValue(None, type=YuiType.NullType)
YuiValue.TrueValue = YuiValue(True, type=YuiType.BooleanType)
YuiValue.FalseValue = YuiValue(False, type=YuiType.BooleanType)

## オペレーター

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
    def evaluate(self, left_node: Any, right_node: Any) -> Any:
        pass

@dataclass
class Equals(Operator):
    def __init__(self, symbol: str = "=="):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return left_value.type.equals(left_node, right_node)

@dataclass
class NotEquals(Operator):
    def __init__(self, symbol: str = "!="):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return not left_value.type.equals(left_node, right_node)

@dataclass
class LessThan(Operator):
    def __init__(self, symbol: str = "<"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return not left_value.type.equals(left_node, right_node) and \
            left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class GreaterThan(Operator):
    def __init__(self, symbol: str = ">"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return not left_value.type.equals(left_node, right_node) and \
            not left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class LessThanEquals(Operator):
    def __init__(self, symbol: str = "<="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return left_value.type.equals(left_node, right_node) or \
            left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class GreaterThanEquals(Operator):
    def __init__(self, symbol: str = ">="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        return left_value.type.equals(left_node, right_node) or \
            not left_value.type.less_than(left_node, right_node, op=self.symbol)
    
@dataclass
class In(Operator):
    def __init__(self, symbol: str = "in"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        right_array = right_node.arrayview
        for element in right_array:
            if left_value.type.equals(left_node, element):
                return True
        return False

@dataclass
class NotIn(Operator):
    def __init__(self, symbol: str = "notin"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = left_node
        right_array = right_node.arrayview
        for element in right_array:
            if left_value.type.equals(left_node, element):
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

set_operators(OPERATORS)

