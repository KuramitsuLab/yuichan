// yuistdlib.js — 標準ライブラリ関数
// Python 版 yuichan/yuistdlib.py の移植
//
// 依存: yuitypes.js のみ。AST ノードには依存しない (runtime から呼ばれる想定)。
//
// standardLib(modules) は modules 配列に [名前パターン, 関数] のペアを push し、
// [targets, modules] を返す。targets は '|' 区切りの言語名 ('emoji|ja|en')。
//
// JS ⇔ Python の差分:
// - Python は `*args` (tuple), JS は `...args` (array) — 呼び出し側は spread で渡す。
// - Python の `int(float(x))` は JS では `Math.trunc(Number(x))`。
// - Python の `f"{v:.6f}"` は JS では `v.toFixed(6)`。
// - Python の `//` (floor division) は JS では `Math.floor(a/b)` に置き換える。
// - NaN チェック: Python の `float("hello")` は ValueError を投げるが、JS の
//   `Number("hello")` は NaN を返すだけなので、明示的に `Number.isFinite` で検査する。

import {
  YuiValue,
  YuiError,
  types,
  NumberType,
  IntType,
  FloatType,
  TY_INT,
  TY_FLOAT,
  TY_STRING,
  TY_ARRAY,
  TY_OBJECT,
  TY_BOOLEAN,
} from './yuitypes.js';

/**
 * 標準ライブラリを登録する。
 * modules 配列に [名前パターン, 関数] のペアを追加し、[targets, modules] を返す。
 *
 * 関数は Python 側の `*args` と同じく可変長引数で呼び出される想定。
 * 呼び出し側 (runtime) は `fn(...argValues)` のように spread して渡すこと。
 */
export function standardLib(modules) {
  // ─────────────────────────────────────────────
  // ヘルパ
  // ─────────────────────────────────────────────

  function checkNumberOfArgs(args, expected) {
    if (expected === -1) {
      // 少なくとも 1 引数
      if (args.length < 1) {
        throw new YuiError(['mismatch-argument', `❌${args.length}`, '✅>0']);
      }
      return;
    }
    if (args.length !== expected) {
      const last = args.length > 0 ? args[args.length - 1] : null;
      throw new YuiError(
        ['mismatch-argument', `✅${expected}`, `❌${args.length}`],
        last,
      );
    }
  }

  /** 引数が配列 YuiValue 1 つだけの場合、その要素を展開して返す */
  function arrayToVarargs(args) {
    if (args.length === 1 && args[0] instanceof YuiValue && types.is_array(args[0])) {
      return args[0].array;
    }
    return args;
  }

  /** 引数リストに float が含まれるかを判定しつつ、全要素の型を検査する */
  function hasFloatOrRaise(args) {
    for (const arg of args) {
      NumberType.match_or_raise(arg);
      if (types.is_float(arg)) return true;
    }
    return false;
  }

  // ─────────────────────────────────────────────
  // 数値関数
  // ─────────────────────────────────────────────

  function yuiAbs(...args) {
    checkNumberOfArgs(args, 1);
    NumberType.match_or_raise(args[0]);
    const value = types.unbox(args[0]);
    return new YuiValue(Math.abs(value));
  }
  modules.push(['📏|絶対値|abs', yuiAbs]);

  function yuiSqrt(...args) {
    checkNumberOfArgs(args, 1);
    NumberType.match_or_raise(args[0]);
    const value = types.unbox(args[0]);
    if (value < 0) {
      throw new YuiError(['not-negative-number', `❌${value}`, '✅>=0']);
    }
    // Python の math.sqrt は常に float を返す。JS 側は Math.sqrt(4) が
    // 整数 2 を返すため、Number.isInteger(2) が true となり IntType に
    // 推論されてしまう。Python のセマンティクスを保つため FloatType を明示する。
    return new YuiValue(Math.sqrt(value), FloatType);
  }
  modules.push(['√|平方根|sqrt', yuiSqrt]);

  function yuiRandom(...args) {
    checkNumberOfArgs(args, 0);
    return new YuiValue(Math.random());
  }
  modules.push(['🎲|乱数|random', yuiRandom]);

  function yuiSum(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const isFloat = hasFloatOrRaise(args);
    let total = types.unbox(args[0]);
    if (isFloat) total = Number(total);
    for (let i = 1; i < args.length; i++) {
      total += types.unbox(args[i]);
    }
    return new YuiValue(total);
  }
  modules.push(['🧮|和|sum', yuiSum]);

  function yuiSub(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    hasFloatOrRaise(args); // 型検査のみ
    let total = types.unbox(args[0]);
    for (let i = 1; i < args.length; i++) {
      total -= types.unbox(args[i]);
    }
    return new YuiValue(total);
  }
  modules.push(['⛓️‍💥|差|diff', yuiSub]);

  function yuiProduct(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const isFloat = hasFloatOrRaise(args);
    let total = types.unbox(args[0]);
    if (isFloat) total = Number(total);
    for (let i = 1; i < args.length; i++) {
      total *= types.unbox(args[i]);
    }
    return new YuiValue(total);
  }
  modules.push(['💰|積|product', yuiProduct]);

  function yuiDiv(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const isFloat = hasFloatOrRaise(args);
    let total = types.unbox(args[0]);
    if (isFloat) {
      total = Number(total);
      for (let i = 1; i < args.length; i++) {
        const d = Number(types.unbox(args[i]));
        if (d === 0) {
          throw new YuiError(['division-by-zero', `❌${d}`], args[i]);
        }
        total /= d;
      }
    } else {
      for (let i = 1; i < args.length; i++) {
        const d = types.unbox(args[i]);
        if (d === 0) {
          throw new YuiError(['division-by-zero', `❌${d}`], args[i]);
        }
        // Python の floor division: 負数に対しても床 (Math.floor を使用)
        total = Math.floor(total / d);
      }
    }
    return new YuiValue(total);
  }
  modules.push(['✂️|商|quotient', yuiDiv]);

  function yuiMod(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const isFloat = hasFloatOrRaise(args);
    let total = types.unbox(args[0]);
    if (isFloat) total = Number(total);
    for (let i = 1; i < args.length; i++) {
      const d = types.unbox(args[i]);
      if (d === 0) {
        throw new YuiError(['division-by-zero', `❌${d}`], args[i]);
      }
      // Python の % は正の除数に対して常に非負を返す
      total = ((total % d) + d) % d;
    }
    return new YuiValue(total);
  }
  modules.push(['🍕|剰余|remainder', yuiMod]);

  function yuiMax(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const values = args.map((a) => types.unbox(a));
    // Math.max は number 同士の比較。Python の max と挙動一致。
    return new YuiValue(Math.max(...values));
  }
  modules.push(['👑|最大値|max', yuiMax]);

  function yuiMin(...args) {
    checkNumberOfArgs(args, -1);
    args = arrayToVarargs(args);
    const values = args.map((a) => types.unbox(a));
    return new YuiValue(Math.min(...values));
  }
  modules.push(['🐜|最小値|min', yuiMin]);

  // ─────────────────────────────────────────────
  // 型判定関数
  // ─────────────────────────────────────────────

  function yuiIsBool(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_bool(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_BOOLEAN}❓|ブール判定|isbool`, yuiIsBool]);

  function yuiIsInt(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_int(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_INT}❓|整数判定|isint`, yuiIsInt]);

  function yuiIsFloat(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_float(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_FLOAT}❓|小数判定|isfloat`, yuiIsFloat]);

  function yuiIsString(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_string(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_STRING}❓|文字列判定|isstring`, yuiIsString]);

  function yuiIsArray(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_array(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_ARRAY}❓|配列判定|isarray`, yuiIsArray]);

  function yuiIsObject(...args) {
    checkNumberOfArgs(args, 1);
    return types.is_object(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
  }
  modules.push([`${TY_OBJECT}❓|オブジェクト判定|isobject`, yuiIsObject]);

  // ─────────────────────────────────────────────
  // 型変換関数
  // ─────────────────────────────────────────────

  function yuiToint(...args) {
    checkNumberOfArgs(args, 1);
    if (types.is_int(args[0])) return args[0];
    const unboxed = types.unbox(args[0]);
    if (unboxed === null || unboxed === undefined) return new YuiValue(0);
    try {
      if (types.is_array(args[0])) {
        const elements = args[0].array;
        return new YuiValue(IntType.to_native(elements));
      }
      // Python の int(float(x)) 相当。NaN / ±Infinity は除外する。
      const f = Number(unboxed);
      if (!Number.isFinite(f)) {
        throw new Error(`cannot convert ${types.format_json(unboxed)} to number`);
      }
      return new YuiValue(Math.trunc(f));
    } catch (e) {
      const msg = e && e.message ? e.message : String(e);
      throw new YuiError(['int-conversion', `❌${unboxed}`, `🔥${msg}`]);
    }
  }
  modules.push([`${TY_INT}|整数化|toint`, yuiToint]);

  function yuiTofloat(...args) {
    checkNumberOfArgs(args, 1);
    if (types.is_float(args[0])) return args[0];
    const unboxed = types.unbox(args[0]);
    if (unboxed === null || unboxed === undefined) return new YuiValue(0.0);
    try {
      if (types.is_array(args[0])) {
        const elements = args[0].array;
        return new YuiValue(FloatType.to_native(elements));
      }
      const f = Number(unboxed);
      if (!Number.isFinite(f)) {
        throw new Error(`cannot convert ${types.format_json(unboxed)} to float`);
      }
      return new YuiValue(f);
    } catch (e) {
      const msg = e && e.message ? e.message : String(e);
      throw new YuiError(['float-conversion', `❌${unboxed}`, `🔥${msg}`]);
    }
  }
  modules.push([`${TY_FLOAT}|小数化|tofloat`, yuiTofloat]);

  function yuiTostring(...args) {
    checkNumberOfArgs(args, 1);
    if (types.is_string(args[0])) return args[0];
    if (types.is_float(args[0])) {
      const v = types.unbox(args[0]);
      return new YuiValue(v.toFixed(6));
    }
    // Python の str(YuiValue) は __str__ → stringify(None) を呼ぶ。JS 版も同じ。
    return new YuiValue(args[0].toString());
  }
  modules.push([`${TY_STRING}|文字列化|tostring`, yuiTostring]);

  function yuiToarray(...args) {
    checkNumberOfArgs(args, 1);
    const value = args[0];
    if (types.is_object(value)) {
      // Python: list(value.native.keys())
      return new YuiValue(Object.keys(value.native));
    }
    return new YuiValue(value.array);
  }
  modules.push([`${TY_ARRAY}|配列化|toarray`, yuiToarray]);

  return ['emoji|ja|en', modules];
}
