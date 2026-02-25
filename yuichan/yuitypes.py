from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

from .yuiast import ASTNode, set_operators
from .yuierror import YuiError, ERROR_MESSAGES, _format_messages, _normalize_messages

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

    def to_sign(self, native_value: Any) -> int:
        """符号を返す（デフォルトは常に 1）"""
        return 1

    @abstractmethod
    def to_native(self, elements: List[int], sign: int = 1, node=None) -> Any:
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

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> None:
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

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> bool:
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

    def to_sign(self, n: int) -> int:
        return -1 if n < 0 else 1

    def to_arrayview(self, n: int) -> List[int]:
        """整数の絶対値を可変長LSBファースト配列に変換（0は空リスト）"""
        n_abs = abs(n)
        bits = []
        while n_abs:
            bits.append(n_abs & 1)
            n_abs >>= 1
        return bits

    def to_native(self, bits: List[int], sign: int = 1, node=None) -> int:
        """可変長LSBファースト配列を整数に変換"""
        n = 0
        for i, bit in enumerate(bits):
            n |= bit << i
        return sign * n
    
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
        if value < 0 or value > 9:
            raise YuiError(("error", "value", f"✅0-9", f"❌{value}"), node_or_value)

    def to_sign(self, x: float) -> int:
        return -1 if x < 0 else 1

    def to_arrayview(self, x: float) -> List[int]:
        """浮動小数点数の絶対値をLSB（小さい桁）ファーストの一桁整数配列に変換
        Example:
            3.14  → [0, 0, 0, 0, 4, 1, 3]  (sign=1)
            -3.14 → [0, 0, 0, 0, 4, 1, 3]  (sign=-1)
        """
        s = f"{abs(x):.6f}"  # 小数点以下6桁に丸める
        s = s.replace('.', '')  # 小数点を削除
        digits = [int(ch) for ch in s]
        return list(reversed(digits))

    def to_native(self, digits: List[int], sign: int = 1, node=None) -> float:
        """LSBファーストの一桁整数配列を浮動小数点数に変換
        Example:
            to_native([0, 0, 0, 0, 4, 1, 3], sign=1)  → 3.14
            to_native([0, 0, 0, 0, 4, 1, 3], sign=-1) → -3.14
        """
        num_digits = list(reversed(digits))  # MSBファーストに戻す
        for i, d in enumerate(num_digits):
            if not (isinstance(d, int) and 0 <= d <= 9):
                raise YuiError(("conversion", "tofloat", f"❌[{i}]{d}", f"✅0-9", f"🔍{digits}"), node)
        s = ''.join(str(d) for d in num_digits)
        if len(s) <= 6:
            # 整数部なし（小数点以下のみ）
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
    
    def to_sign(self, n: Union[int, float]) -> int:
        if isinstance(n, float):
            return YuiType.FloatType.to_sign(n)
        else:
            return YuiType.IntType.to_sign(n)

    def to_native(self, bits: List[int], sign: int = 1, node=None) -> int:
        if len(bits) == 32:
            return YuiType.IntType.to_native(bits, sign=sign, node=node)
        else:
            return YuiType.FloatType.to_native(bits, sign=sign, node=node)
    
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

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
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

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
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

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
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
        self.sign = 1
        self.type = _typing(native_value) if type is None else type
    
    @property
    def native(self) -> Any:
        if self.native_value is None:
            self.native_value = self.type.to_native(self.elements, sign=self.sign)
        return self.native_value

    @property
    def arrayview(self):
        if self.elements is None:
            self.sign = self.type.to_sign(self.native_value)
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
        if index < 0:
            raise YuiError(("error", "index", f"✅>=0", f"❌{index}"), node_or_index)
        if isinstance(self.type, YuiIntType) and index >= len(elements):
            return YuiType.from_arrayview(0)  # int は上位ビットが暗黙的に 0
        if index >= len(elements):
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
        if index < 0:
            raise YuiError(("error", "index", f"✅>=0", f"❌{index}"), node_or_index)
        if isinstance(self.type, YuiIntType) and index >= len(elements):
            elements.extend([0] * (index - len(elements) + 1))  # int は上位ビットを0で自動拡張
        elif index >= len(elements):
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

