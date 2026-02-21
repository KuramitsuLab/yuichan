from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

from .yuiast import ASTNode, _eval, set_operators

class YuiError(RuntimeError):
    """Yui言語のエラーを表現するクラス"""
    messages: tuple
    error_node: Optional[ASTNode]
    runtime: Optional['YuiRuntime'] # type: ignore
    BK: bool
    
    def __init__(self, messages: tuple, error_node: Optional[ASTNode] = None,
                 runtime: Optional['YuiRuntime'] = None, #type: ignore
                 BK: bool = False):
        """YuiErrorを初期化する"""
        super().__init__(' '.join(messages))
        self.messages = messages
        self.error_node = error_node if isinstance(error_node, ASTNode) else None
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
        # message = _to_message(self.messages)
        message = ' '.join(self.messages)   
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

TY_NULL = '⛔'
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
        value = _eval(node_or_value)
        if not self.match(value):
            raise YuiError(("error", "type", f"✅<{self.emoji}{self.name}>", f"❌{value}"), node_or_value)

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
        left_value = _eval(left_node)
        right_value = _eval(right_node)
        raise YuiError(("unsupported", "comparison", f"❌{left_value} {op} {right_value}"), left_node)


    # クラス変数として各型のインスタンスを定義
    NullType: 'YuiNullType' = None
    IntType: 'YuiIntType' = None
    FloatType: 'YuiFloatType' = None
    NumberType: 'YuiNumberType' = None
    StringType: 'YuiStringType' = None
    ArrayType: 'YuiArrayType' = None
    ObjectType: 'YuiObjectType' = None

    @staticmethod
    def evaluated(node_or_value: ASTNode) -> Any:
        if isinstance(node_or_value, ASTNode):
            return node_or_value.evaluated_value
        return node_or_value

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
        value = _eval(node_or_value)
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
        value = _eval(node_or_value)
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
        value = _eval(node_or_value)
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
        left_value = _eval(left_node_or_value)
        right_value = _eval(right_node_or_value)        
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
        value = _eval(node_or_value)
        return value is None or (isinstance(value, YuiValue) and isinstance(value.type, YuiNullType))

    def check_element(self, node_or_value: Any) -> None:
        raise YuiError(("immutable", f"❌{self}"), node_or_value)

    def to_arrayview(self, n: None) -> List[int]:
        return []

    def to_native(self, elements: List[int], node=None) -> None:
        return None
    
    def stringfy(self, native_value: None, indent_prefix: str = "", width=80) -> str:
        return "null"
    

class YuiIntType(YuiType):
    def __init__(self):
        super().__init__("int", TY_INT)

    def match(self, node_or_value: Any) -> bool:
        value = _eval(node_or_value)
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
        value = _eval(node_or_value)
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
        value = _eval(node_or_value)
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

class YuiArrayType(YuiType):
    def __init__(self):
        super().__init__("array", TY_ARRAY)

    def match(self, node_or_value: Any) -> bool:
        value = _eval(node_or_value)
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
        print(f"TODO: array equality check for {left_node} and {right_node}")
        return False


class YuiObjectType(YuiType):
    def __init__(self):
        super().__init__("object", TY_OBJECT)

    def match(self, node_or_value: Any) -> bool:
        value = _eval(node_or_value)
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
        print(f"TODO: object equality check for {left_node} and {right_node}")
        return False



YuiType.NullType = YuiNullType()
YuiType.IntType = YuiIntType()
YuiType.FloatType = YuiFloatType()
YuiType.NumberType = YuiNumberType()
YuiType.StringType = YuiStringType()
YuiType.ObjectType = YuiObjectType()
YuiType.ArrayType = YuiArrayType()

TYPES = [YuiType.NullType, YuiType.IntType, YuiType.FloatType, YuiType.NumberType, YuiType.StringType, YuiType.ArrayType, YuiType.ObjectType]

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
        return isinstance(self.type, (YuiNullType, YuiIntType, YuiFloatType, YuiStringType))

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
        left_value = _eval(left_node)
        return left_value.type.equals(left_node, right_node)

@dataclass
class NotEquals(Operator):
    def __init__(self, symbol: str = "!="):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        return not left_value.type.equals(left_node, right_node)

@dataclass
class LessThan(Operator):
    def __init__(self, symbol: str = "<"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        return not left_value.type.equals(left_node, right_node) and \
            left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class GreaterThan(Operator):
    def __init__(self, symbol: str = ">"):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        return not left_value.type.equals(left_node, right_node) and \
            not left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class LessThanEquals(Operator):
    def __init__(self, symbol: str = "<="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        return left_value.type.equals(left_node, right_node) or \
            left_value.type.less_than(left_node, right_node, op=self.symbol)

@dataclass
class GreaterThanEquals(Operator):
    def __init__(self, symbol: str = ">="):
        super().__init__(symbol, comparative=True)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        return left_value.type.equals(left_node, right_node) or \
            not left_value.type.less_than(left_node, right_node, op=self.symbol)
    
@dataclass
class In(Operator):
    def __init__(self, symbol: str = "in"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        right_array = _eval(right_node).arrayview
        for element in right_array:
            if left_value.type.equals(left_node, element):
                return True
        return False

@dataclass
class NotIn(Operator):
    def __init__(self, symbol: str = "notin"):
        super().__init__(symbol, comparative=False)

    def evaluate(self, left_node: Any, right_node: Any) -> bool:
        left_value = _eval(left_node)
        right_array = _eval(right_node).arrayview
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

    def check_number_of_args(nodeargs: List[Any], expected: int) -> None:
        """関数の引数の数をチェックする"""
        if expected == -1: #少なくとも一つの引数が必要
            if len(nodeargs) < 1:
                raise YuiError(("required", "arguments", f"❌{len(nodeargs)}", f"✅>0"))
            return
        if len(nodeargs) != expected:
            raise YuiError(("expected", "arguments", f"✅{expected}", f"❌{len(nodeargs)}"), nodeargs[-1])

    def array_to_varargs(nodeargs:list) -> list:
        """引数が配列1つの場合、その要素を展開して返す"""
        if len(nodeargs) == 1 and isinstance(nodeargs[0], YuiValue):
            return nodeargs[0].array
        return nodeargs

    def yui_abs(*nodeargs: Any) -> Any:
        """絶対値を返す"""
        check_number_of_args(nodeargs, 1)
        YuiType.NumberType.match_or_raise(nodeargs[0])
        value = YuiType.matched_native(nodeargs[0])
        if YuiType.is_float(value):
            value = YuiType.ensure_float(value)
            return YuiValue(abs(value))
        return abs(YuiType.ensure_int(value))
    modules.append(('📏|絶対値|abs', yui_abs))

    def yui_random(*nodeargs: Any) -> Any:
        """ランダムな整数を返す"""
        check_number_of_args(nodeargs, 0)
        return YuiValue(random.random())
    modules.append((f'🎲{TY_FLOAT}|乱数|random', yui_random))
    
    def yui_randint(*nodeargs: Any) -> Any:
        """0以上x未満のランダムな整数を返す"""
        check_number_of_args(nodeargs, 1)
        YuiType.IntType.match_or_raise(nodeargs[0])
        x = YuiType.matched_native(nodeargs[0])
        if x <= 0:
            raise YuiError(("error", "invalid argument", f"❌{x}", f"✅>0"))
        return YuiValue(random.randint(0, x - 1))
    modules.append((f'🎲{TY_FLOAT}|乱整数|randint', yui_randint))

    def has_float_or_raise(nodeargs: List[Any]) -> bool:
        """引数リストに少数が含まれているかどうかを判定する"""
        for nodearg in nodeargs:
            YuiType.NumberType.match_or_raise(nodearg)
            if YuiType.is_float(nodearg):
                return True
        return False
    
    def yui_sum(*nodeargs: Any) -> Any:
        """要素の合計を返す"""
        check_number_of_args(nodeargs, -1)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                total += float(YuiType.matched_native(nodearg))
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total += YuiType.matched_native(nodearg)
            return total
    modules.append(('🧮|和|sum', yui_sum))

    def yui_sub(*nodeargs: Any) -> Any:
        """要素の差を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        if has_float_or_raise(nodeargs):
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total -= YuiType.matched_native(nodearg)
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total -= YuiType.matched_native(nodearg)
            return total
    modules.append(('➖|差|diff', yui_sub))

    def yui_product(*nodeargs: Any) -> Any:
        """要素の積を返す"""
        check_number_of_args(nodeargs, -1)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                total *= YuiType.matched_native(nodearg)
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total *= YuiType.matched_native(nodearg)
            return total
    modules.append(('✖️|積|product', yui_product))

    def yui_div(*nodeargs: Any) -> Any:
        """要素の商を返す"""
        check_number_of_args(nodeargs, -1)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                d = float(YuiType.matched_native(nodearg))
                if d == 0.0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total /= d
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                d = YuiType.matched_native(nodearg)
                if d == 0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total //= d
            return total
    modules.append(('✂️|商|quotient', yui_div))

    def yui_mod(*nodeargs: Any) -> Any:
        """剰余を返す"""
        check_number_of_args(nodeargs, -1)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                d = float(YuiType.matched_native(nodearg))
                if d == 0.0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total %= d
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                d = YuiType.matched_native(nodearg)
                if d == 0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total %= d
            return total
    modules.append(('🍕|剰余|remainder', yui_mod))


    def yui_and(*nodeargs: Any) -> int:
        """論理積を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total &= YuiType.matched_native(nodearg)
        return total
    modules.append(('💡✖️|論理積|and', yui_and))

    def yui_or(*nodeargs: Any) -> int:
        """論理和を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total |= YuiType.matched_native(nodearg)
        return total
    modules.append(('💡➕|論理和|or', yui_or))

    def yui_xor(*nodeargs: Any) -> Any:
        """排他的論理和を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total ^= YuiType.matched_native(nodearg)
        return total
    modules.append(('💡🔀|排他的論理和|xor', yui_xor))

    def yui_not(*nodeargs: Any) -> Any:
        """ビット反転を返す"""
        check_number_of_args(nodeargs, 1)
        return ~(YuiType.matched_native(nodeargs[0]))
    modules.append(('💡🔄|ビット反転|not', yui_not))

    def yui_left_shift(*nodeargs: Any) -> Any:
        """左シフトを返す"""
        check_number_of_args(nodeargs, 2)
        return YuiType.matched_native(nodeargs[0]) << YuiType.matched_native(nodeargs[1])
    modules.append(('💡⬅️|左シフト|shl', yui_left_shift))
    
    def yui_right_shift(*nodeargs: Any) -> Any:
        """右シフトを返す"""
        check_number_of_args(nodeargs, 2)
        return YuiType.matched_native(nodeargs[0]) >> YuiType.matched_native(nodeargs[1])
    modules.append(('💡➡️|右シフト|shr', yui_right_shift))

    def yui_max(*nodeargs: Any) -> Any:
        """最大値を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        result = max(YuiType.matched_native(nodearg) for nodearg in nodeargs)
        if isinstance(result, float):
            return YuiValue(result)
        return int(result)
    modules.append(('👑|最大値|max', yui_max))

    def yui_min(*nodeargs: Any) -> Any:
        """最小値を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        result = min(YuiType.matched_native(nodearg) for nodearg in nodeargs)
        if isinstance(result, float):
            return YuiValue(result)
        return int(result)
    modules.append(('🐜|最小値|min', yui_min))

    def yui_isint(*nodeargs: Any) -> Any:
        """整数か判定する"""
        check_number_of_args(nodeargs, 1)
        return 1 if isinstance(nodeargs[0], int) else 0
    modules.append((f'{TY_INT}❓|整数判定|isint', yui_isint))

    def yui_toint(*nodeargs: Any) -> Any:
        """整数化する"""
        check_number_of_args(nodeargs, 1)
        value = nodeargs[0]
        value = int(YuiType.matched_native(nodeargs[0]))
        return value
    modules.append((f'{TY_INT}|整数化|toint', yui_toint))

    def yui_isfloat(*nodeargs: Any) -> Any:
        """小数か判定する"""
        check_number_of_args(nodeargs, 1)
        return 1 if YuiType.is_float(nodeargs[0]) else 0
    modules.append((f'{TY_FLOAT}❓|少数判定|isfloat', yui_isfloat))

    def yui_tofloat(*nodeargs: Any) -> Any:
        """小数化する"""
        check_number_of_args(nodeargs, 1)
        value = nodeargs[0]
        if YuiType.is_string(value):
            string_value = value.to_string()
            try:
                return YuiValue(float(string_value))
            except ValueError:
                raise YuiError((f"error", "conversion", f"❌{string_value}"))
        value = float(YuiType.matched_native(nodeargs[0]))
        return YuiValue(value)
    modules.append((f'{TY_FLOAT}|少数化|tofloat', yui_tofloat))

    def yui_isstring(*nodeargs: Any) -> Any:
        """文字列か判定する"""
        check_number_of_args(nodeargs, 1)
        return 1 if YuiType.is_string(nodeargs[0]) else 0
    modules.append((f'{TY_STRING}❓|文字列判定|isstring', yui_isstring))

    def yui_tostring(*nodeargs: Any) -> Any:
        """文字列に変換する"""
        check_number_of_args(nodeargs, 1)
        if YuiType.is_float(nodeargs[0]):
            v = YuiType.StringType.matched_native(nodeargs[0])
            return YuiValue(f"{v:.6f}")
        return YuiValue(str(nodeargs[0]))
    modules.append((f'{TY_STRING}|文字列化|tostring', yui_tostring))

    def yui_isobject(*nodeargs: Any) -> Any:
        """オブジェクトか判定する"""
        check_number_of_args(nodeargs, 1)
        return 1 if YuiType.is_object(nodeargs[0]) else 0
    modules.append((f'{TY_OBJECT}❓|オブジェクト判定|isobject', yui_isobject))

    def yui_toobject(*nodeargs: Any) -> Any:
        """オブジェクトに変換する"""
        check_number_of_args(nodeargs, 1)
        if YuiType.is_string(nodeargs[0]):
            s = yui.ensure_string(nodeargs[0])
            if s.startswith('{'):
                try:
                    v = json.loads(s) # JSONとしてパースできるか確認
                    return YuiValue(v)
                except json.JSONDecodeError:
                    pass
            return YuiValue({})
        return YuiValue(str(nodeargs[0]))
    modules.append((f'{TY_OBJECT}|オブジェクト化|toobject', yui_toobject))

    def yui_isarray(*nodeargs: Any) -> bool:
        """オブジェクトか判定する"""
        check_number_of_args(nodeargs, 1)
        return 1 if isinstance(nodeargs[0], YuiValue) else 0
    modules.append((f'{TY_ARRAY}❓|配列判定|isarray', yui_isarray))

    def yui_toarray(*nodeargs: Any) -> Any:
        """配列に変換する"""
        check_number_of_args(nodeargs, 1)
        if isinstance(nodeargs[0], YuiValue):
            nodeargs[0].view = "array"
            nodeargs[0].native_value = None
            return nodeargs[0]
        return YuiValue(YuiType.matched_native(nodeargs[0]))
    modules.append((f'{TY_ARRAY}|配列化|toarray', yui_toarray))

