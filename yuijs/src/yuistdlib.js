// yuistdlib.js — standard library (port of yuichan/yuistdlib.py)

import {
    YuiValue, YuiType, YuiError, types,
    TY_INT, TY_FLOAT, TY_STRING, TY_ARRAY, TY_OBJECT, TY_BOOLEAN,
    IntType, NumberType, FloatType
} from './yuitypes.js';

/**
 * 標準ライブラリ関数を modules に登録する。
 * Python の standard_lib と同じく modules を破壊的に更新し、
 * 戻り値として ('emoji|ja|en', modules) 相当を返す。
 */
export function standardLib(modules) {
    function checkNumberOfArgs(args, expected) {
        if (expected === -1) {
            if (args.length < 1) {
                throw new YuiError(['mismatch-argument', `❌${args.length}`, '✅>0']);
            }
            return;
        }
        if (args.length !== expected) {
            const last = args.length > 0 ? args[args.length - 1] : null;
            throw new YuiError(
                ['mismatch-argument', `✅${expected}`, `❌${args.length}`],
                null
            );
        }
    }

    function arrayToVarargs(args) {
        if (args.length === 1 && args[0] instanceof YuiValue) {
            return args[0].array;
        }
        return args;
    }

    function hasFloatOrRaise(args) {
        for (const arg of args) {
            NumberType.matchOrRaise(arg);
            if (types.isFloat(arg)) return true;
        }
        return false;
    }

    // ── 絶対値 / abs ──────────────────────────────────────────
    function yuiAbs(...args) {
        checkNumberOfArgs(args, 1);
        NumberType.matchOrRaise(args[0]);
        const value = types.unbox(args[0]);
        return new YuiValue(Math.abs(value));
    }
    modules.push(['📏|絶対値|abs', yuiAbs]);

    // ── 平方根 / sqrt ─────────────────────────────────────────
    function yuiSqrt(...args) {
        checkNumberOfArgs(args, 1);
        NumberType.matchOrRaise(args[0]);
        const value = types.unbox(args[0]);
        if (value < 0) {
            throw new YuiError(['not-negative-number', `❌${value}`, '✅>=0']);
        }
        return new YuiValue(Math.sqrt(value), FloatType);
    }
    modules.push(['√|平方根|sqrt', yuiSqrt]);

    // ── 乱数 / random ─────────────────────────────────────────
    function yuiRandom(...args) {
        checkNumberOfArgs(args, 0);
        return new YuiValue(Math.random(), FloatType);
    }
    modules.push(['🎲|乱数|random', yuiRandom]);

    // ── 和 / sum ──────────────────────────────────────────────
    function yuiSum(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        if (hasFloatOrRaise(args)) {
            let total = parseFloat(types.unbox(args[0]));
            for (const arg of args.slice(1)) total += parseFloat(types.unbox(arg));
            return new YuiValue(total, FloatType);
        }
        let total = types.unbox(args[0]);
        for (const arg of args.slice(1)) total += types.unbox(arg);
        return new YuiValue(total);
    }
    modules.push(['🧮|和|sum', yuiSum]);

    // ── 差 / diff ─────────────────────────────────────────────
    function yuiSub(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        if (hasFloatOrRaise(args)) {
            let total = types.unbox(args[0]);
            for (const arg of args.slice(1)) total -= types.unbox(arg);
            return new YuiValue(total, FloatType);
        }
        let total = types.unbox(args[0]);
        for (const arg of args.slice(1)) total -= types.unbox(arg);
        return new YuiValue(total);
    }
    modules.push(['⛓️‍💥|差|diff', yuiSub]);

    // ── 積 / product ──────────────────────────────────────────
    function yuiProduct(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        if (hasFloatOrRaise(args)) {
            let total = parseFloat(types.unbox(args[0]));
            for (const arg of args.slice(1)) total *= types.unbox(arg);
            return new YuiValue(total, FloatType);
        }
        let total = types.unbox(args[0]);
        for (const arg of args.slice(1)) total *= types.unbox(arg);
        return new YuiValue(total);
    }
    modules.push(['💰|積|product', yuiProduct]);

    // ── 商 / quotient ─────────────────────────────────────────
    function yuiDiv(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        if (hasFloatOrRaise(args)) {
            let total = parseFloat(types.unbox(args[0]));
            for (const arg of args.slice(1)) {
                const d = parseFloat(types.unbox(arg));
                if (d === 0.0) throw new YuiError(['division-by-zero', `❌${d}`], arg);
                total /= d;
            }
            return new YuiValue(total, FloatType);
        }
        let total = types.unbox(args[0]);
        for (const arg of args.slice(1)) {
            const d = types.unbox(arg);
            if (d === 0) throw new YuiError(['division-by-zero', `❌${d}`], arg);
            total = Math.floor(total / d);
        }
        return new YuiValue(total);
    }
    modules.push(['✂️|商|quotient', yuiDiv]);

    // ── 剰余 / remainder ──────────────────────────────────────
    function yuiMod(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        if (hasFloatOrRaise(args)) {
            let total = parseFloat(types.unbox(args[0]));
            for (const arg of args.slice(1)) {
                const d = parseFloat(types.unbox(arg));
                if (d === 0.0) throw new YuiError(['division-by-zero', `❌${d}`], arg);
                total %= d;
            }
            return new YuiValue(total, FloatType);
        }
        let total = types.unbox(args[0]);
        for (const arg of args.slice(1)) {
            const d = types.unbox(arg);
            if (d === 0) throw new YuiError(['division-by-zero', `❌${d}`], arg);
            // Python-compatible modulo (always non-negative for positive divisor)
            total = ((total % d) + d) % d;
        }
        return new YuiValue(total);
    }
    modules.push(['🍕|剰余|remainder', yuiMod]);

    // ── 最大値 / max ──────────────────────────────────────────
    function yuiMax(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        const vals = args.map(a => types.unbox(a));
        const result = Math.max(...vals);
        return new YuiValue(Number.isInteger(result) ? result : result);
    }
    modules.push(['👑|最大値|max', yuiMax]);

    // ── 最小値 / min ──────────────────────────────────────────
    function yuiMin(...args) {
        checkNumberOfArgs(args, -1);
        args = arrayToVarargs(args);
        const vals = args.map(a => types.unbox(a));
        const result = Math.min(...vals);
        return new YuiValue(Number.isInteger(result) ? result : result);
    }
    modules.push(['🐜|最小値|min', yuiMin]);

    // ── 型判定・変換 ─────────────────────────────────────────

    function yuiIsbool(...args) {
        checkNumberOfArgs(args, 1);
        return types.isBool(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_BOOLEAN}❓|ブール判定|isbool`, yuiIsbool]);

    function yuiIsint(...args) {
        checkNumberOfArgs(args, 1);
        return types.isInt(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_INT}❓|整数判定|isint`, yuiIsint]);

    function yuiIsfloat(...args) {
        checkNumberOfArgs(args, 1);
        return types.isFloat(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_FLOAT}❓|小数判定|isfloat`, yuiIsfloat]);

    function yuiIsstring(...args) {
        checkNumberOfArgs(args, 1);
        return types.isString(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_STRING}❓|文字列判定|isstring`, yuiIsstring]);

    function yuiIsarray(...args) {
        checkNumberOfArgs(args, 1);
        return types.isArray(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_ARRAY}❓|配列判定|isarray`, yuiIsarray]);

    function yuiIsobject(...args) {
        checkNumberOfArgs(args, 1);
        return types.isObject(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_OBJECT}❓|オブジェクト判定|isobject`, yuiIsobject]);

    function yuiToint(...args) {
        checkNumberOfArgs(args, 1);
        if (types.isInt(args[0])) return args[0];
        const unboxed = types.unbox(args[0]);
        if (unboxed === null || unboxed === undefined) return new YuiValue(0);
        try {
            if (types.isArray(args[0])) {
                const elements = args[0].array;
                return new YuiValue(IntType.toNative(elements));
            }
            return new YuiValue(Math.trunc(parseFloat(unboxed)));
        } catch (e) {
            throw new YuiError(['int-conversion', `❌${unboxed}`, `🔥${e.message || e}`]);
        }
    }
    modules.push([`${TY_INT}|整数化|toint`, yuiToint]);

    function yuiTofloat(...args) {
        checkNumberOfArgs(args, 1);
        if (types.isFloat(args[0])) return args[0];
        const unboxed = types.unbox(args[0]);
        if (unboxed === null || unboxed === undefined) return new YuiValue(0.0, FloatType);
        try {
            if (types.isArray(args[0])) {
                const elements = args[0].array;
                return new YuiValue(FloatType.toNative(elements), FloatType);
            }
            const f = parseFloat(unboxed);
            if (Number.isNaN(f)) {
                throw new Error(`cannot convert ${unboxed}`);
            }
            return new YuiValue(f, FloatType);
        } catch (e) {
            throw new YuiError(['float-conversion', `❌${unboxed}`, `🔥${e.message || e}`]);
        }
    }
    modules.push([`${TY_FLOAT}|小数化|tofloat`, yuiTofloat]);

    function yuiTostring(...args) {
        checkNumberOfArgs(args, 1);
        if (types.isString(args[0])) return args[0];
        if (types.isFloat(args[0])) {
            const v = types.unbox(args[0]);
            return new YuiValue(v.toFixed(6));
        }
        return new YuiValue(String(args[0]));
    }
    modules.push([`${TY_STRING}|文字列化|tostring`, yuiTostring]);

    function yuiToarray(...args) {
        checkNumberOfArgs(args, 1);
        const value = args[0];
        if (types.isObject(value)) {
            return new YuiValue(Object.keys(value.native));
        }
        return new YuiValue(value.array);
    }
    modules.push([`${TY_ARRAY}|配列化|toarray`, yuiToarray]);

    return ['emoji|ja|en', modules];
}
