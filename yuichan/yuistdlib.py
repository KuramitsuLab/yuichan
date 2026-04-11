import math
import random
from typing import List, Any

from .yuitypes import (
    YuiValue, YuiError, types,
    TY_INT, TY_FLOAT, TY_STRING, TY_ARRAY, TY_OBJECT, TY_BOOLEAN,
    IntType, NumberType, FloatType
)


def standard_lib(modules: list):
    """
    標準ライブラリを環境に追加する

    以下の関数が使用可能になります：
    - 絶対値(x): 絶対値
    - 平方根(x): 平方根（小数を返す）
    - 乱数(): ランダムな小数
    - 和(x, y, ...): 要素の合計
    - 差(x, y, ...): 要素の差
    - 積(x, y, ...): 要素の積
    - 商(x, y, ...): 要素の商
    - 剰余(x, y): 剰余
    - 最大値(x, y, ...): 最大値
    - 最小値(x, y, ...): 最小値

    - 配列化(x): 配列に変換
    - 文字列化(x): 文字列に変換
    - 小数化(x): 小数に変換
    - 整数化(x): 整数に変換
    - 整数判定(x): 整数かどうか
    - 小数判定(x): 小数かどうか
    - 文字列判定(x): 文字列かどうか
    - オブジェクト化(x): オブジェクトに変換
    - オブジェクト判定(x): オブジェクトかどうか

    Args:
        modules: (名前, 関数) のペアを追加するリスト
    """

    def check_number_of_args(args: List[Any], expected: int) -> None:
        """関数の引数の数をチェックする"""
        if expected == -1: #少なくとも一つの引数が必要
            if len(args) < 1:
                raise YuiError(("mismatch-argument", f"❌{len(args)}", f"✅>0"))
            return
        if len(args) != expected:
            last = args[-1] if args else None
            raise YuiError(("mismatch-argument", f"✅{expected}", f"❌{len(args)}"), last)

    def array_to_varargs(args:list) -> list:
        """引数が配列1つの場合、その要素を展開して返す"""
        if len(args) == 1 and isinstance(args[0], YuiValue):
            return args[0].array
        return args

    def yui_abs(*args: Any) -> Any:
        """絶対値を返す"""
        check_number_of_args(args, 1)
        NumberType.match_or_raise(args[0])
        value = types.unbox(args[0])
        return YuiValue(abs(value))
    modules.append(('📏|絶対値|abs', yui_abs))

    def yui_sqrt(*args: Any) -> Any:
        """平方根を返す（小数）"""
        check_number_of_args(args, 1)
        NumberType.match_or_raise(args[0])
        value = types.unbox(args[0])
        if value < 0:
            raise YuiError(("not-negative-number", f"❌{value}", f"✅>=0"))
        return YuiValue(math.sqrt(value))
    modules.append(('√|平方根|sqrt', yui_sqrt))

    def yui_random(*args: Any) -> Any:
        """ランダムな小数を返す"""
        check_number_of_args(args, 0)
        return YuiValue(random.random())
    modules.append((f'🎲|乱数|random', yui_random))

    def has_float_or_raise(args: List[Any]) -> bool:
        """引数リストに小数が含まれているかどうかを判定する"""
        for nodearg in args:
            NumberType.match_or_raise(nodearg)
            if types.is_float(nodearg):
                return True
        return False

    def yui_sum(*args: Any) -> Any:
        """要素の合計を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_or_raise(args):
            total = float(types.unbox(args[0]))
            for nodearg in args[1:]:
                total += float(types.unbox(nodearg))
            return YuiValue(total)
        else:
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                total += types.unbox(nodearg)
            return YuiValue(total)
    modules.append(('🧮|和|sum', yui_sum))

    def yui_sub(*args: Any) -> Any:
        """要素の差を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_or_raise(args):
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                total -= types.unbox(nodearg)
            return YuiValue(total)
        else:
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                total -= types.unbox(nodearg)
            return YuiValue(total)
    modules.append(('⛓️‍💥|差|diff', yui_sub))

    def yui_product(*args: Any) -> Any:
        """要素の積を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_or_raise(args):
            total = float(types.unbox(args[0]))
            for nodearg in args[1:]:
                total *= types.unbox(nodearg)
            return YuiValue(total)
        else:
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                total *= types.unbox(nodearg)
            return YuiValue(total)
    modules.append(('💰|積|product', yui_product))

    def yui_div(*args: Any) -> Any:
        """要素の商を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_or_raise(args):
            total = float(types.unbox(args[0]))
            for nodearg in args[1:]:
                d = float(types.unbox(nodearg))
                if d == 0.0:
                    raise YuiError((f"division-by-zero", f"❌{d}"), nodearg)
                total /= d
            return YuiValue(total)
        else:
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                d = types.unbox(nodearg)
                if d == 0:
                    raise YuiError((f"division-by-zero", f"❌{d}"), nodearg)
                total //= d
            return YuiValue(total)
    modules.append(('✂️|商|quotient', yui_div))

    def yui_mod(*args: Any) -> Any:
        """剰余を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        if has_float_or_raise(args):
            total = float(types.unbox(args[0]))
            for nodearg in args[1:]:
                d = float(types.unbox(nodearg))
                if d == 0.0:
                    raise YuiError((f"division-by-zero", f"❌{d}"), nodearg)
                total %= d
            return YuiValue(total)
        else:
            total = types.unbox(args[0])
            for nodearg in args[1:]:
                d = types.unbox(nodearg)
                if d == 0:
                    raise YuiError((f"division-by-zero", f"❌{d}"), nodearg)
                total %= d
            return YuiValue(total)
    modules.append(('🍕|剰余|remainder', yui_mod))

    def yui_max(*args: Any) -> Any:
        """最大値を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        result = max(types.unbox(nodearg) for nodearg in args)
        return YuiValue(int(result) if isinstance(result, int) else result)
    modules.append(('👑|最大値|max', yui_max))

    def yui_min(*args: Any) -> Any:
        """最小値を返す"""
        check_number_of_args(args, -1)
        args = array_to_varargs(args)
        result = min(types.unbox(nodearg) for nodearg in args)
        return YuiValue(int(result) if isinstance(result, int) else result)
    modules.append(('🐜|最小値|min', yui_min))

    def yui_isbool(*args: Any) -> YuiValue:
        """ブールか判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_bool(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_BOOLEAN}❓|ブール判定|isbool', yui_isbool))

    def yui_isint(*args: Any) -> YuiValue:
        """整数か判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_int(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_INT}❓|整数判定|isint', yui_isint))

    def yui_isfloat(*args: Any) -> YuiValue:
        """小数か判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_float(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_FLOAT}❓|小数判定|isfloat', yui_isfloat))

    def yui_isstring(*args: Any) -> YuiValue:
        """文字列か判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_string(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_STRING}❓|文字列判定|isstring', yui_isstring))

    def yui_isarray(*args: Any) -> YuiValue:
        """配列か判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_array(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_ARRAY}❓|配列判定|isarray', yui_isarray))

    def yui_isobject(*args: Any) -> YuiValue:
        """オブジェクトか判定する"""
        check_number_of_args(args, 1)
        return YuiValue.TrueValue if types.is_object(args[0]) else YuiValue.FalseValue
    modules.append((f'{TY_OBJECT}❓|オブジェクト判定|isobject', yui_isobject))

    def yui_toint(*args: Any) -> YuiValue:
        """整数化する"""
        check_number_of_args(args, 1)
        if types.is_int(args[0]):
            return args[0]
        unboxed_value = types.unbox(args[0])
        if unboxed_value is None:
            return YuiValue(0)
        try:
            if types.is_array(args[0]):
                elements = args[0].array
                return YuiValue(IntType.to_native(elements))
            return YuiValue(int(float(unboxed_value)))
        except Exception as e   :
            raise YuiError(("int-conversion", f"❌{unboxed_value}", f"🔥{e}")) from e
    modules.append((f'{TY_INT}|整数化|toint', yui_toint))

    def yui_tofloat(*args: Any) -> Any:
        """小数化する"""
        check_number_of_args(args, 1)
        if types.is_float(args[0]):
            return args[0]
        unboxed_value = types.unbox(args[0])
        if unboxed_value is None:
            return YuiValue(0.0)        
        try:
            if types.is_array(args[0]):
                elements = args[0].array
                return YuiValue(FloatType.to_native(elements))
            return YuiValue(float(unboxed_value))
        except Exception as e:
            raise YuiError((f"float-conversion", f"❌{unboxed_value}", f"🔥{e}")) from e
    modules.append((f'{TY_FLOAT}|小数化|tofloat', yui_tofloat))

    def yui_tostring(*args: Any) -> Any:
        """文字列に変換する"""
        check_number_of_args(args, 1)
        if types.is_string(args[0]):
            return args[0]
        if types.is_float(args[0]):
            v = types.unbox(args[0])
            return YuiValue(f"{v:.6f}")
        return YuiValue(str(args[0]))
    modules.append((f'{TY_STRING}|文字列化|tostring', yui_tostring))

    def yui_toarray(*args: Any) -> Any:
        """配列に変換する"""
        check_number_of_args(args, 1)
        value = args[0]
        if types.is_object(value):
            return YuiValue(list(value.native.keys()))
        return YuiValue(value.array)
    modules.append((f'{TY_ARRAY}|配列化|toarray', yui_toarray))

    return 'emoji|ja|en', modules
