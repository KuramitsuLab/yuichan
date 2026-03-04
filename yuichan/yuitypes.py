from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Union
from abc import ABC, abstractmethod

from .yuierror import YuiError, vprint

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

    def is_immutable(self) -> bool:
        """イミュータブルかどうか"""
        return False

    def is_array_unboxed(self) -> bool:
        """配列内でunboxされるかどうか"""
        return True

    @abstractmethod
    def match(self, box_or_unbox: Any) -> bool:
        pass

    def match_or_raise(self, box_or_unbox, node=None):        
        if not self.match(box_or_unbox):
            raise YuiError(("type-error", f"✅<{self.emoji}{self.name}>", f"❌{box_or_unbox}"), node)    

    @abstractmethod
    def to_arrayview(self, native_value: int) -> Tuple[List[int], int]:
        pass

    def to_sign(self, native_value: Any) -> int:
        return 1

    @abstractmethod
    def to_native(self, elements: List[int], sign: int = 1, node=None) -> Any:
        pass

    @abstractmethod
    def stringfy(self, native_value: Any, indent_prefix: str = "", width=80) -> str:
        pass
    
    def equals(self, left: Any, right: Any) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        return left_value == right_value    

    def less_than(self, left: Any, right: Any, op="<", binary_node = None) -> bool:
        raise YuiError(("imcomparable", f"❌{left} {op} {right}"), binary_node)


class YuiNullType(YuiType):
    def __init__(self):
        super().__init__("null", TY_NULL)

    def is_immutable(self) -> bool:
        """イミュータブルかどうか"""
        return True

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return value is None or (isinstance(value, YuiValue) and isinstance(value.type, YuiNullType))

    def to_arrayview(self, n: None) -> List[int]:
        return []

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> None:
        return None
    
    def stringfy(self, native_value: None, indent_prefix: str = "", width=80) -> str:
        return "null"


class YuiBooleanType(YuiType):
    def __init__(self):
        super().__init__("boolean", TY_BOOLEAN)

    def is_immutable(self) -> bool:
        """イミュータブルかどうか"""
        return True

    def match(self, value: Any) -> bool:
        # Python の bool は int のサブクラスなので先に isinstance(value, bool) でチェックする
        return isinstance(value, bool) or (isinstance(value, YuiValue) and isinstance(value.type, YuiBooleanType))

    def check_element(self, node_or_value: Any) -> None:
        raise YuiError(("immutable", f"❌{self}"), node_or_value)

    def to_arrayview(self, n: bool) -> List[int]:
        return [1] if n else [0]

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> bool:
        return bool(elements[0]) if elements else False

    def stringfy(self, native_value: bool, indent_prefix: str = "", width=80) -> str:
        return "true" if native_value else "false"

    def equals(self, left: Any, right: Any, binary_node=None) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, bool):
            return left_value == right_value
        return False

    def less_than(self, left: Any, right: Any, op="<", binary_node = None) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, bool):
            return left_value < right_value
        return super().less_than(left, right, op, binary_node)


class YuiIntType(YuiType):
    def __init__(self):
        super().__init__("int", TY_INT)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, int) or (isinstance(value, YuiValue) and isinstance(value.type, YuiIntType))

    def to_sign(self, native_value: int) -> int:
        return -1 if native_value < 0 else 1

    def to_arrayview(self, native_value: int) -> List[int]:
        """整数の絶対値を可変長LSBファースト配列に変換（0は空リスト）"""
        n_abs = abs(native_value)
        bits = []
        while n_abs:
            bits.append(int(n_abs & 1))
            n_abs >>= 1
        return bits

    def to_native(self, bits: List[int], sign: int = 1, node=None) -> int:
        """可変長LSBファースト配列を整数に変換"""
        n = 0
        for i, bit in enumerate(bits):
            if bit not in (0, 1) or isinstance(bit, bool):
                array = ArrayType.stringfy(bits, indent_prefix=None, comma=",")
                raise YuiError(("array-value-error", f"❌{types.format_json(bit)}", f"✅0/1", f"🔍{array}"), node)
            n |= bit << i
        return sign * n
    
    def stringfy(self, native_value: int, indent_prefix: str = "", width=80) -> str:
        return f"{native_value}"

    def stringfy_arrayview(self, arrayview: List[int], sign):
        return f"{'-' if sign < 0 else ''}[{','.join(str(b) for b in arrayview)}]"

    def equals(self, left: Any, right: Any) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, bool):
            return False  # bool は IntType と等しくない
        if isinstance(right_value, float):
            return round(float(left_value), 6) == round(right_value, 6)
        return left_value == right_value

    def less_than(self, left: Any, right: Any, op = "<", binary_node = None) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, float):
            return round(float(left_value), 6) < round(right_value, 6)
        if isinstance(right_value, int):
            return left_value < right_value
        super().less_than(left, right, op, binary_node)
    

class YuiFloatType(YuiType):
    def __init__(self):
        super().__init__("float", TY_FLOAT)

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, float) or (isinstance(value, YuiValue) and isinstance(value.type, YuiFloatType))

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
        for d in digits:
            if not (isinstance(d, int) and 0 <= d <= 9):
                array = ArrayType.stringfy(digits, indent_prefix=None, comma=",")
                raise YuiError(("array-value-error", f"❌{types.format_json(d)}", f"✅0-9", f"🔍{array}"), node)
        num_digits = list(reversed(digits))  # MSBファーストに戻す
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

    def equals(self, left: Any, right: Any) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, bool):
            return False  # bool は float と等しくない
        if isinstance(right_value, (float, int)):
            return round(left_value, 6) == round(right_value, 6)
        return False

    def less_than(self, left: Any, right: Any, op = "<", binary_node = None) -> bool:
        left_value = types.unbox(left)
        right_value = types.unbox(right)
        if isinstance(right_value, (int, float)):
            return left_value < right_value
        super().less_than(left, right, op=op, binary_node=binary_node)

class YuiNumberType(YuiType):
    def __init__(self):
        super().__init__("number", TY_NUMBER)

    def match(self, node_or_value: Any) -> bool:
        return IntType.match(node_or_value) or FloatType.match(node_or_value)

    def to_arrayview(self, native_value):
        raise NotImplementedError("NumberType is a union type; use IntType or FloatType")

    def to_native(self, elements, sign=1, node=None):
        raise NotImplementedError("NumberType is a union type; use IntType or FloatType")

    def stringfy(self, native_value, indent_prefix="", width=80):
        raise NotImplementedError("NumberType is a union type; use IntType or FloatType")


class YuiStringType(YuiType):
    def __init__(self):
        super().__init__("string", TY_STRING)

    def match(self, value: Any) -> bool:
        return isinstance(value, str) or (isinstance(value, YuiValue) and isinstance(value.type, YuiStringType))

    def to_arrayview(self, x: str) -> List[int]:
        """文字コード"""
        return [ord(ch) for ch in x]

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
        contents = []
        for d in elements:
            if not (isinstance(d, int) and 0 <= d <= 0x10FFFF):
                array = ArrayType.stringfy(elements, indent_prefix=None, comma=",")
                raise YuiError(("array-value-error", f"❌{types.format_json(d)}", f"✅<文字コード>", f"🔍{array}"), node)
            contents.append(chr(d))
        return ''.join(contents)

    def stringfy(self, native_value: str, indent_prefix: str = "", width=80) -> str:
        return types.format_json(native_value)
    
    def equals(self, left: Any, right: Any) -> bool:
        left_value = types.unbox(left)
        if types.is_string(right):
            right_value = types.unbox(right)
            return left_value == right_value
        return False   

    def less_than(self, left: Any, right: Any, op = "<", binary_node = None) -> bool:
        left_value = types.unbox(left)
        if types.is_string(right):
            right_value = types.unbox(right)
            return left_value < right_value
        return False

class YuiArrayType(YuiType):
    def __init__(self):
        super().__init__("array", TY_ARRAY)

    def is_array_unboxed(self) -> bool:
        """配列内でunboxされるかどうか"""
        return False

    def match(self, node_or_value: Any) -> bool:
        value = node_or_value
        return isinstance(value, list) or (isinstance(value, YuiValue) and isinstance(value.type, YuiArrayType))
    
    def to_arrayview(self, array_value: list) -> List[int]:
        """配列の要素をエンコード"""
        return [types.array_unbox(value) for value in array_value]

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
        array = []
        for element in elements:
            if isinstance(element, YuiValue):
                array.append(element.native)
            else:
                array.append(element)
        return array
    
    def stringfy(self, elements: List[int], indent_prefix: str = "", comma=", ", width=80) -> str:
        buffer = ["["]
        for i, element in enumerate(elements):
            if i > 0:
                buffer.append(comma)
            buffer.append(f"{types.format_json(element)}")
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
                buffer.append(f"{types.format_json(element)}")
            if i < len(elements) - 1:
                buffer.append(",")
        buffer.append(f"{LF}{indent_prefix}]")
        return ''.join(buffer)

    def equals(self, left: Any, right: Any, binary_node=None) -> bool:
        if not types.is_array(right) and not types.is_string(right):
            return False
        left_native = types.unbox(left)
        right_native = types.unbox(right)
        return _array_equal(left_native, right_native)

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

class YuiObjectType(YuiType):
    def __init__(self):
        super().__init__("object", TY_OBJECT)

    def is_array_unboxed(self) -> bool:
        """配列内でunboxされるかどうか"""
        return False

    def match(self, value: Any) -> bool:
        return isinstance(value, dict) or (isinstance(value, YuiValue) and isinstance(value.type, YuiObjectType))

    def to_arrayview(self, object_value: dict) -> List[int]:
        """オブジェクトのキーと値をエンコード"""
        elements = []
        for key, value in object_value.items():
            elements.append(YuiValue([str(key), types.array_unbox(value)]))
        return elements

    def to_native(self, elements: List[int], sign: int = 1, node=None) -> str:
        obj = {}
        for key_value in elements:
            if not isinstance(key_value, YuiValue):
                raise YuiError((f"array-value-error", f"❌{key_value}", f"✅[key, value]", f"🔍{elements}"), node)
            key_value = key_value.native
            if not isinstance(key_value, list) or len(key_value) != 2:
                raise YuiError((f"array-value-error", f"❌{key_value}", f"✅[key, value]", f"🔍{elements}"), node)
            key = key_value[0]
            if not isinstance(key, str):
                raise YuiError((f"array-value-error", f"❌{key}", f"✅<string>", f"🔍{key_value}"), node)
            value = key_value[1]
            obj[key] = value
        return obj

    def stringfy(self, native_value: dict, indent_prefix: str = "", width=80) -> str:
        buffer = ["{"]
        for i, (key, value) in enumerate(native_value.items()):
            if i > 0:
                buffer.append(", ")
            buffer.append(f'"{key}": {types.format_json(value)}')
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
                buffer.append(f'{types.format_json(value)}')
            if i < len(native_value) - 1:
                buffer.append(",")
        buffer.append(f"{LF}{indent_prefix}}}")
        return ''.join(buffer)

    def equals(self, left: Any, right: Any, binary_node=None) -> bool:
        left_native = types.unbox(left)
        right_native = types.unbox(right)
        if not isinstance(right_native, dict):
            return False
        if set(left_native.keys()) != set(right_native.keys()):
            return False
        return all(_array_equal(left_native[k], right_native[k]) for k in left_native)

NullType = YuiNullType()
BoolType = YuiBooleanType()
IntType = YuiIntType()
FloatType = YuiFloatType()
NumberType = YuiNumberType()
StringType = YuiStringType()
ObjectType = YuiObjectType()
ArrayType = YuiArrayType()

# bool は Python で int のサブクラスなので BooleanType を IntType より先に置く
TYPES = [NullType, BoolType, IntType, FloatType, NumberType, StringType, ArrayType, ObjectType]

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
    sign: int
    inner_view: bool

    def __init__(self, native_value: Any, type: Optional[YuiType] = None):
        """YuiValueを初期化する"""
        self.native_value = native_value.native if isinstance(native_value, YuiValue) else native_value
        self.type = _typing(native_value) if type is None else type
        self.elements = None
        self.sign = None
        self.inner_view = False
    
    @property
    def native(self) -> Any:
        if self.native_value is None:
            self.native_value = self.type.to_native(self.elements, self.sign)
        return self.native_value

    @property
    def array(self):
        if self.elements is None:
            self.elements = self.type.to_arrayview(self.native_value)
            self.sign = self.type.to_sign(self.native_value)
            self.native_value = None  # elements を使うので native キャッシュを無効化
            self.inner_view = True
        return self.elements

    def get_item(self, index: Any, getindex_node=None) -> Any:
        if types.is_string(index) and types.is_object(self):
            key = types.unbox(index)
            obj = types.unbox(self)
            return types.box(obj.get(key, YuiValue.NullValue))
        
        IntType.match_or_raise(index, getindex_node)
        index = types.unbox(index)
        elements = self.array
        self.inner_view = True
        # int type: implicit leading zeros for out-of-range
        if index < 0:
            raise YuiError(("index-error", f"✅>=0", f"❌{index}"), getindex_node)
        if isinstance(self.type, YuiIntType) and index >= len(elements):
            return types.box(0)
        if index >= len(elements):
            raise YuiError(("index-error", f"✅<{len(elements)}", f"❌{index}", f"🔍{elements}"), getindex_node)
        return types.box(elements[index])

    def set_item(self, index: Any, value: Any, getindex_node=None) -> Any:
        value = types.array_unbox(value)
        if self.type.is_immutable():
            raise YuiError(("immutable-set", f"❌{self.type}"), None)
        if types.is_string(index) and types.is_object(self):
            key = types.unbox(index)
            obj = self.native  # use native directly to mutate in place
            obj[key] = value
            self.elements = None
            return
        IntType.match_or_raise(index, getindex_node)
        index = types.unbox(index)
        if index < 0:
            raise YuiError(("index-error", f"✅>=0", f"❌{index}"), getindex_node)
        elements = self.array
        if index >= len(elements):
            raise YuiError(("index-error", f"✅<{len(elements)}", f"❌{index}", f"🔍{elements}"), getindex_node)
        self.inner_view = True
        elements[index] = value
        try:
            self.type.to_native(elements, self.sign, getindex_node)
        except YuiError as e:
            self.type = ArrayType
            raise e
        self.native_value = None

    def append(self, value: Any, append_node=None) -> Any:
        value = types.array_unbox(value)
        if self.type.is_immutable():
            raise YuiError(("immutable-append", f"❌{self.type}"), append_node)
        self.array.append(value)
        self.inner_view = True
        try:
            self.type.to_native(self.array, self.sign, append_node)
        except YuiError as e:
            self.type = ArrayType
            raise e
        self.native_value = None

    def __str__(self):
        """文字列表現を返す"""
        return self.stringfy(indent_prefix=None)

    def __repr__(self):
        """デバッグ用文字列表現を返す"""
        return str(self.native)

    def stringfy(self, indent_prefix: str = "", inner_view=False, width=80) -> str:
        native_view = self.type.stringfy(self.native, indent_prefix=indent_prefix, width=width)
        if inner_view == True and self.inner_view and self.type.is_array_unboxed():
            elements =self.array
            array_view = ArrayType.stringfy(elements, indent_prefix=None, comma= ",", width=width)
            return f"{native_view:12}   🔬{array_view}"
        return native_view

    def equals(self, other: Any) -> bool:
        return self.type.equals(self, other)

    def less_than(self, other: Any, op = "<", binary_node=None) -> bool:
        return self.type.less_than(self, other, op, binary_node)

YuiValue.NullValue = YuiValue(None, type=NullType)
YuiValue.TrueValue = YuiValue(True, type=BoolType)
YuiValue.FalseValue = YuiValue(False, type=BoolType)

class types:

    @staticmethod
    def box(value: Any) -> YuiValue:
        if isinstance(value, YuiValue):
            return value
        if value is None:
            return YuiValue.NullValue
        elif isinstance(value, bool):
            return YuiValue.TrueValue if value else YuiValue.FalseValue
        return YuiValue(value)

    @staticmethod
    def array_unbox(value: Any) -> Any:
        if isinstance(value, YuiValue):
            if value.type.is_array_unboxed():
                return value.native
        if isinstance(value, (list, dict)):
            return YuiValue(value)
        return value

    @staticmethod
    def unbox(value) -> Any:
        if isinstance(value, YuiValue):
            return types.unbox(value.native)
        if isinstance(value, list):
            return [types.unbox(v) for v in value]
        if isinstance(value, dict):
            return {str(k): types.unbox(v) for k, v in value.items()}
        return value

    @staticmethod
    def is_bool(box_or_unbox: Any) -> bool:
        global BoolType
        return BoolType.match(box_or_unbox)

    @staticmethod
    def is_int(box_or_unbox: Any) -> bool:
        global IntType
        return IntType.match(box_or_unbox)

    @staticmethod
    def is_float(box_or_unbox: Any) -> bool:
        global FloatType
        return FloatType.match(box_or_unbox)

    @staticmethod
    def is_number(box_or_unbox: Any) -> bool:
        global NumberType
        return NumberType.match(box_or_unbox)      
    
    @staticmethod
    def is_string(box_or_unbox: Any) -> bool:
        global StringType
        return StringType.match(box_or_unbox)

    @staticmethod
    def is_array(box_or_unbox: Any) -> bool:
        global ArrayType
        return ArrayType.match(box_or_unbox)

    @staticmethod
    def is_object(box_or_unbox: Any) -> bool:
        global ObjectType
        return ObjectType.match(box_or_unbox)

    @staticmethod
    def format_json(value):
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{value}"'
        elif isinstance(value, float):
            return f"{value:.6f}"
        else:
            return str(value)
    
    @staticmethod
    def arrayview_s(native_value: Any) -> str:
        """ネイティブ値の配列ビュー文字列表現を返す（コード生成用）"""
        if isinstance(native_value, bool):
            elements = BoolType.to_arrayview(native_value)
            sign = 1
        elif isinstance(native_value, int):
            elements = IntType.to_arrayview(native_value)
            sign = IntType.to_sign(native_value)
        elif isinstance(native_value, float):
            elements = FloatType.to_arrayview(native_value)
            sign = FloatType.to_sign(native_value)
        else:
            return str(native_value)
        return f"{'-' if sign < 0 else ''}[{','.join(str(b) for b in elements)}]"

    @staticmethod
    def compare(left_node_or_value, right_node_or_value: Any) -> int:
        print(f"Comparing {left_node_or_value} and {right_node_or_value}")
        if types.is_number(left_node_or_value) and types.is_number(right_node_or_value):
            left_value = round(types.unbox(left_node_or_value), 6)
            right_value = round(types.unbox(right_node_or_value), 6)
            return _compare(left_value, right_value)
        if types.is_string(left_node_or_value) and types.is_string(right_node_or_value):
            left_value = types.unbox(left_node_or_value)
            right_value = types.unbox(right_node_or_value)
            return _compare(left_value, right_value)
        left_value = left_node_or_value
        right_value = right_node_or_value        
        if not isinstance(right_value, YuiValue):
            right_value = YuiValue(right_value.native)
        return _compare(left_value.array, right_value.array)

def _compare(left, right) -> int:
    if left == right:
        return 0
    if left < right:
        return -1
    else:
        return 1


## オペレーター

@dataclass
class Operator(ABC):
    symbol: str
    precedence: int
    
    def __init__(self, symbol: str, precedence: int = 0):
        self.symbol = symbol
        self.precedence = precedence

    def __str__(self):
        return self.symbol

    @property
    def comparative(self) -> bool:
        return self.precedence == 3

    @abstractmethod
    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        pass

@dataclass
class Equals(Operator):
    def __init__(self, symbol: str = "=="):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return left.equals(right)

@dataclass
class NotEquals(Operator):
    def __init__(self, symbol: str = "!="):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return not left.equals(right)

@dataclass
class LessThan(Operator):
    def __init__(self, symbol: str = "<"):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return not left.equals(right) and \
            left.less_than(right, self.symbol, binary_node)

@dataclass
class GreaterThan(Operator):
    def __init__(self, symbol: str = ">"):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return not left.equals(right) and \
            not left.less_than(right, self.symbol, binary_node)

@dataclass
class LessThanEquals(Operator):
    def __init__(self, symbol: str = "<="):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return left.equals(right) or \
            left.less_than(right, self.symbol, binary_node)

@dataclass
class GreaterThanEquals(Operator):
    def __init__(self, symbol: str = ">="):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        return left.equals(right) or \
            not left.less_than(right, self.symbol, binary_node)

@dataclass
class In(Operator):
    def __init__(self, symbol: str = "in"):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        right_array = right.array
        for element in right_array:
            if left.equals(element):
                return True
        return False

@dataclass
class NotIn(Operator):
    def __init__(self, symbol: str = "notin"):
        super().__init__(symbol, precedence=3)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> bool:
        right_array = right.array
        for element in right_array:
            if left.equals(element):
                return False
        return True

@dataclass
class Add(Operator):
    def __init__(self, symbol: str = "+"):
        super().__init__(symbol, precedence=2)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        if types.is_string(left) and types.is_string(right):
            return types.unbox(left) + types.unbox(right)
        if types.is_array(left) and types.is_array(right):
            return left.native + right.native
        NumberType.match_or_raise(left, binary_node)
        NumberType.match_or_raise(right, binary_node)
        return types.unbox(left) + types.unbox(right)

@dataclass
class Sub(Operator):
    def __init__(self, symbol: str = "-"):
        super().__init__(symbol, precedence=2)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        NumberType.match_or_raise(left, binary_node)
        NumberType.match_or_raise(right, binary_node)
        return types.unbox(left) - types.unbox(right)

@dataclass
class Mul(Operator):
    def __init__(self, symbol: str = "*"):
        super().__init__(symbol, precedence=1)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        NumberType.match_or_raise(left, binary_node)
        NumberType.match_or_raise(right, binary_node)
        return types.unbox(left) * types.unbox(right)

@dataclass
class Div(Operator):
    def __init__(self, symbol: str = "/"):
        super().__init__(symbol, precedence=1)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        NumberType.match_or_raise(left, binary_node)
        NumberType.match_or_raise(right, binary_node)
        l, r = types.unbox(left), types.unbox(right)
        if r == 0:
            raise YuiError(("division-by-zero", f"❌{r}"), binary_node)
        if types.is_float(left) or types.is_float(right):
            return l / r
        return l // r

@dataclass
class Mod(Operator):
    def __init__(self, symbol: str = "%"):
        super().__init__(symbol, precedence=1)

    def evaluate(self, left: YuiValue, right: YuiValue, binary_node=None) -> Any:
        NumberType.match_or_raise(left, binary_node)
        NumberType.match_or_raise(right, binary_node)
        l, r = types.unbox(left), types.unbox(right)
        if r == 0:
            raise YuiError(("division-by-zero", f"❌{r}"), binary_node)
        return l % r  # Python: 正の除数に対して常に非負

OPERATORS = {
    '==': Equals(),
    '!=': NotEquals(),
    '<': LessThan(),
    '>': GreaterThan(),
    '<=': LessThanEquals(),
    '>=': GreaterThanEquals(),
    'in': In(),
    'notin': NotIn(),
    '+': Add(),
    '-': Sub(),
    '*': Mul(),
    '/': Div(),
    '%': Mod(),
}


