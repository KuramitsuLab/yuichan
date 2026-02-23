import math
import random
import json
from typing import List, Any

from .yuitypes import (
    YuiValue, YuiType, YuiError,
    TY_INT, TY_FLOAT, TY_STRING, TY_ARRAY, TY_OBJECT,
)


def standard_lib(modules: list):
    """
    標準ライブラリを環境に追加する

    以下の関数が使用可能になります：
    - 絶対値(x): 絶対値
    - 平方根(x): 平方根（少数を返す）
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
        modules: (名前, 関数) のペアを追加するリスト
    """

    def check_number_of_args(nodeargs: List[Any], expected: int) -> None:
        """関数の引数の数をチェックする"""
        if expected == -1: #少なくとも一つの引数が必要
            if len(nodeargs) < 1:
                raise YuiError(("required", "arguments", f"❌{len(nodeargs)}", f"✅>0"))
            return
        if len(nodeargs) != expected:
            last = nodeargs[-1] if nodeargs else None
            raise YuiError(("expected", "arguments", f"✅{expected}", f"❌{len(nodeargs)}"), last)

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
        return YuiValue(abs(value))
    modules.append(('📏|絶対値|abs', yui_abs))

    def yui_sqrt(*nodeargs: Any) -> Any:
        """平方根を返す（少数）"""
        check_number_of_args(nodeargs, 1)
        YuiType.NumberType.match_or_raise(nodeargs[0])
        value = YuiType.matched_native(nodeargs[0])
        if value < 0:
            raise YuiError(("error", "negative sqrt", f"❌{value}", f"✅>=0"))
        return YuiValue(math.sqrt(value))
    modules.append(('√|平方根|sqrt', yui_sqrt))

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
        nodeargs = array_to_varargs(nodeargs)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                total += float(YuiType.matched_native(nodearg))
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total += YuiType.matched_native(nodearg)
            return YuiValue(total)
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
            return YuiValue(total)
    modules.append(('➖|差|diff', yui_sub))

    def yui_product(*nodeargs: Any) -> Any:
        """要素の積を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                total *= YuiType.matched_native(nodearg)
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                total *= YuiType.matched_native(nodearg)
            return YuiValue(total)
    modules.append(('✖️|積|product', yui_product))

    def yui_div(*nodeargs: Any) -> Any:
        """要素の商を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        if has_float_or_raise(nodeargs):
            total = float(YuiType.matched_native(nodeargs[0]))
            for nodearg in nodeargs[1:]:
                d = float(YuiType.matched_native(nodearg))
                if d == 0.0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total /= d
            return YuiValue(total)
        else:
            total = YuiType.matched_native(nodeargs[0])
            for nodearg in nodeargs[1:]:
                d = YuiType.matched_native(nodearg)
                if d == 0:
                    raise YuiError((f"error", "division by zero", f"❌{d}"), nodearg)
                total //= d
            return YuiValue(total)
    modules.append(('✂️|商|quotient', yui_div))

    def yui_mod(*nodeargs: Any) -> Any:
        """剰余を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
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
            return YuiValue(total)
    modules.append(('🍕|剰余|remainder', yui_mod))

    def yui_and(*nodeargs: Any) -> YuiValue:
        """論理積を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total &= YuiType.matched_native(nodearg)
        return YuiValue(total)
    modules.append(('💡✖️|論理積|and', yui_and))

    def yui_or(*nodeargs: Any) -> YuiValue:
        """論理和を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total |= YuiType.matched_native(nodearg)
        return YuiValue(total)
    modules.append(('💡➕|論理和|or', yui_or))

    def yui_xor(*nodeargs: Any) -> YuiValue:
        """排他的論理和を返す"""
        total = YuiType.matched_native(nodeargs[0])
        for nodearg in nodeargs[1:]:
            total ^= YuiType.matched_native(nodearg)
        return YuiValue(total)
    modules.append(('💡🔀|排他的論理和|xor', yui_xor))

    def yui_not(*nodeargs: Any) -> YuiValue:
        """ビット反転を返す"""
        check_number_of_args(nodeargs, 1)
        return YuiValue(~(YuiType.matched_native(nodeargs[0])))
    modules.append(('💡🔄|ビット反転|not', yui_not))

    def yui_left_shift(*nodeargs: Any) -> YuiValue:
        """左シフトを返す"""
        check_number_of_args(nodeargs, 2)
        return YuiValue(YuiType.matched_native(nodeargs[0]) << YuiType.matched_native(nodeargs[1]))
    modules.append(('💡⬅️|左シフト|shl', yui_left_shift))

    def yui_right_shift(*nodeargs: Any) -> YuiValue:
        """右シフトを返す"""
        check_number_of_args(nodeargs, 2)
        return YuiValue(YuiType.matched_native(nodeargs[0]) >> YuiType.matched_native(nodeargs[1]))
    modules.append(('💡➡️|右シフト|shr', yui_right_shift))

    def yui_max(*nodeargs: Any) -> Any:
        """最大値を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        result = max(YuiType.matched_native(nodearg) for nodearg in nodeargs)
        return YuiValue(int(result) if isinstance(result, int) else result)
    modules.append(('👑|最大値|max', yui_max))

    def yui_min(*nodeargs: Any) -> Any:
        """最小値を返す"""
        check_number_of_args(nodeargs, -1)
        nodeargs = array_to_varargs(nodeargs)
        result = min(YuiType.matched_native(nodearg) for nodearg in nodeargs)
        return YuiValue(int(result) if isinstance(result, int) else result)
    modules.append(('🐜|最小値|min', yui_min))

    def yui_isint(*nodeargs: Any) -> YuiValue:
        """整数か判定する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue.TrueValue if YuiType.is_int(nodeargs[0]) else YuiValue.FalseValue
    modules.append((f'{TY_INT}❓|整数判定|isint', yui_isint))

    def yui_toint(*nodeargs: Any) -> YuiValue:
        """整数化する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue(int(YuiType.matched_native(nodeargs[0])))
    modules.append((f'{TY_INT}|整数化|toint', yui_toint))

    def yui_isfloat(*nodeargs: Any) -> YuiValue:
        """小数か判定する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue.TrueValue if YuiType.is_float(nodeargs[0]) else YuiValue.FalseValue
    modules.append((f'{TY_FLOAT}❓|少数判定|isfloat', yui_isfloat))

    def yui_tofloat(*nodeargs: Any) -> Any:
        """小数化する"""
        check_number_of_args(nodeargs, 1)
        value = nodeargs[0]
        if YuiType.is_string(value):
            string_value = YuiType.matched_native(value)
            try:
                return YuiValue(float(string_value))
            except ValueError:
                raise YuiError((f"error", "conversion", f"❌{string_value}"))
        value = float(YuiType.matched_native(nodeargs[0]))
        return YuiValue(value)
    modules.append((f'{TY_FLOAT}|少数化|tofloat', yui_tofloat))

    def yui_isstring(*nodeargs: Any) -> YuiValue:
        """文字列か判定する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue.TrueValue if YuiType.is_string(nodeargs[0]) else YuiValue.FalseValue
    modules.append((f'{TY_STRING}❓|文字列判定|isstring', yui_isstring))

    def yui_tostring(*nodeargs: Any) -> Any:
        """文字列に変換する"""
        check_number_of_args(nodeargs, 1)
        if YuiType.is_float(nodeargs[0]):
            v = YuiType.matched_native(nodeargs[0])
            return YuiValue(f"{v:.6f}")
        return YuiValue(str(nodeargs[0]))
    modules.append((f'{TY_STRING}|文字列化|tostring', yui_tostring))

    def yui_isobject(*nodeargs: Any) -> YuiValue:
        """オブジェクトか判定する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue.TrueValue if YuiType.is_object(nodeargs[0]) else YuiValue.FalseValue
    modules.append((f'{TY_OBJECT}❓|オブジェクト判定|isobject', yui_isobject))

    def yui_toobject(*nodeargs: Any) -> Any:
        """オブジェクトに変換する"""
        check_number_of_args(nodeargs, 1)
        if YuiType.is_object(nodeargs[0]):
            return nodeargs[0]
        if YuiType.is_string(nodeargs[0]):
            s = YuiType.matched_native(nodeargs[0])
            if s.startswith('{'):
                try:
                    obj = json.loads(s)
                    return YuiValue(obj)
                except json.JSONDecodeError:
                    pass
        return YuiValue({})
    modules.append((f'{TY_OBJECT}|オブジェクト化|toobject', yui_toobject))

    def yui_isarray(*nodeargs: Any) -> YuiValue:
        """配列か判定する"""
        check_number_of_args(nodeargs, 1)
        return YuiValue.TrueValue if YuiType.is_array(nodeargs[0]) else YuiValue.FalseValue
    modules.append((f'{TY_ARRAY}❓|配列判定|isarray', yui_isarray))

    def yui_toarray(*nodeargs: Any) -> Any:
        """配列に変換する"""
        check_number_of_args(nodeargs, 1)
        value = nodeargs[0]
        if isinstance(value, YuiValue):
            _ = value.arrayview  # elements を先に確定させてから native_value を破棄
            value.native_value = None
            return value
        return YuiValue(YuiType.matched_native(value))
    modules.append((f'{TY_ARRAY}|配列化|toarray', yui_toarray))
