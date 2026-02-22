// yuistdlib.js — standard library (port of yuichan/yuistdlib.py)

import { YuiValue, YuiType, YuiError } from './yuitypes.js';

export function standardLib(modules) {
    function checkNumberOfArgs(nodeargs, expected) {
        if (expected === -1) {
            if (nodeargs.length < 1) {
                throw new YuiError(['required', 'arguments', `❌${nodeargs.length}`, '✅>0']);
            }
            return;
        }
        if (nodeargs.length !== expected) {
            const last = nodeargs.length > 0 ? nodeargs[nodeargs.length - 1] : null;
            throw new YuiError(
                ['expected', 'arguments', `✅${expected}`, `❌${nodeargs.length}`],
                null
            );
        }
    }

    function arrayToVarargs(nodeargs) {
        if (nodeargs.length === 1 && nodeargs[0] instanceof YuiValue) {
            return nodeargs[0].array;
        }
        return nodeargs;
    }

    function hasFloatOrRaise(nodeargs) {
        for (const nodearg of nodeargs) {
            YuiType.NumberType.matchOrRaise(nodearg);
            if (YuiType.isFloat(nodearg)) return true;
        }
        return false;
    }

    // ── 絶対値 / abs ──────────────────────────────────────────

    function yuiAbs(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        YuiType.NumberType.matchOrRaise(nodeargs[0]);
        const value = YuiType.matchedNative(nodeargs[0]);
        return new YuiValue(Math.abs(value));
    }
    modules.push(['📏|絶対値|abs', yuiAbs]);

    // ── 乱数 / random ─────────────────────────────────────────

    function yuiRandom(...nodeargs) {
        checkNumberOfArgs(nodeargs, 0);
        return new YuiValue(Math.random());
    }
    modules.push(['🎲📊|乱数|random', yuiRandom]);

    function yuiRandint(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        YuiType.IntType.matchOrRaise(nodeargs[0]);
        const x = YuiType.matchedNative(nodeargs[0]);
        if (x <= 0) throw new YuiError(['error', 'invalid argument', `❌${x}`, '✅>0']);
        return new YuiValue(Math.floor(Math.random() * x));
    }
    modules.push(['🎲📊|乱整数|randint', yuiRandint]);

    // ── 和 / sum ──────────────────────────────────────────────

    function yuiSum(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        if (hasFloatOrRaise(nodeargs)) {
            let total = parseFloat(YuiType.matchedNative(nodeargs[0]));
            for (const nodearg of nodeargs.slice(1)) {
                total += parseFloat(YuiType.matchedNative(nodearg));
            }
            return new YuiValue(total);
        } else {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                total += YuiType.matchedNative(nodearg);
            }
            return new YuiValue(total);
        }
    }
    modules.push(['🧮|和|sum', yuiSum]);

    // ── 差 / diff ─────────────────────────────────────────────

    function yuiSub(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        if (hasFloatOrRaise(nodeargs)) {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                total -= YuiType.matchedNative(nodearg);
            }
            return new YuiValue(total);
        } else {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                total -= YuiType.matchedNative(nodearg);
            }
            return new YuiValue(total);
        }
    }
    modules.push(['➖|差|diff', yuiSub]);

    // ── 積 / product ──────────────────────────────────────────

    function yuiProduct(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        if (hasFloatOrRaise(nodeargs)) {
            let total = parseFloat(YuiType.matchedNative(nodeargs[0]));
            for (const nodearg of nodeargs.slice(1)) {
                total *= YuiType.matchedNative(nodearg);
            }
            return new YuiValue(total);
        } else {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                total *= YuiType.matchedNative(nodearg);
            }
            return new YuiValue(total);
        }
    }
    modules.push(['✖️|積|product', yuiProduct]);

    // ── 商 / quotient ─────────────────────────────────────────

    function yuiDiv(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        if (hasFloatOrRaise(nodeargs)) {
            let total = parseFloat(YuiType.matchedNative(nodeargs[0]));
            for (const nodearg of nodeargs.slice(1)) {
                const d = parseFloat(YuiType.matchedNative(nodearg));
                if (d === 0.0) throw new YuiError(['error', 'division by zero', `❌${d}`], null);
                total /= d;
            }
            return new YuiValue(total);
        } else {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                const d = YuiType.matchedNative(nodearg);
                if (d === 0) throw new YuiError(['error', 'division by zero', `❌${d}`], null);
                total = Math.floor(total / d);
            }
            return new YuiValue(total);
        }
    }
    modules.push(['✂️|商|quotient', yuiDiv]);

    // ── 剰余 / remainder ──────────────────────────────────────

    function yuiMod(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        if (hasFloatOrRaise(nodeargs)) {
            let total = parseFloat(YuiType.matchedNative(nodeargs[0]));
            for (const nodearg of nodeargs.slice(1)) {
                const d = parseFloat(YuiType.matchedNative(nodearg));
                if (d === 0.0) throw new YuiError(['error', 'division by zero', `❌${d}`], null);
                total %= d;
            }
            return new YuiValue(total);
        } else {
            let total = YuiType.matchedNative(nodeargs[0]);
            for (const nodearg of nodeargs.slice(1)) {
                const d = YuiType.matchedNative(nodearg);
                if (d === 0) throw new YuiError(['error', 'division by zero', `❌${d}`], null);
                // Python-compatible modulo (always non-negative for positive divisor)
                total = ((total % d) + d) % d;
            }
            return new YuiValue(total);
        }
    }
    modules.push(['🍕|剰余|remainder', yuiMod]);

    // ── Bitwise ───────────────────────────────────────────────

    function yuiAnd(...nodeargs) {
        let total = YuiType.matchedNative(nodeargs[0]);
        for (const nodearg of nodeargs.slice(1)) total &= YuiType.matchedNative(nodearg);
        return new YuiValue(total);
    }
    modules.push(['💡✖️|論理積|and', yuiAnd]);

    function yuiOr(...nodeargs) {
        let total = YuiType.matchedNative(nodeargs[0]);
        for (const nodearg of nodeargs.slice(1)) total |= YuiType.matchedNative(nodearg);
        return new YuiValue(total);
    }
    modules.push(['💡➕|論理和|or', yuiOr]);

    function yuiXor(...nodeargs) {
        let total = YuiType.matchedNative(nodeargs[0]);
        for (const nodearg of nodeargs.slice(1)) total ^= YuiType.matchedNative(nodearg);
        return new YuiValue(total);
    }
    modules.push(['💡🔀|排他的論理和|xor', yuiXor]);

    function yuiNot(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return new YuiValue(~YuiType.matchedNative(nodeargs[0]));
    }
    modules.push(['💡🔄|ビット反転|not', yuiNot]);

    function yuiLeftShift(...nodeargs) {
        checkNumberOfArgs(nodeargs, 2);
        return new YuiValue(YuiType.matchedNative(nodeargs[0]) << YuiType.matchedNative(nodeargs[1]));
    }
    modules.push(['💡⬅️|左シフト|shl', yuiLeftShift]);

    function yuiRightShift(...nodeargs) {
        checkNumberOfArgs(nodeargs, 2);
        return new YuiValue(YuiType.matchedNative(nodeargs[0]) >> YuiType.matchedNative(nodeargs[1]));
    }
    modules.push(['💡➡️|右シフト|shr', yuiRightShift]);

    // ── 最大値 / max ──────────────────────────────────────────

    function yuiMax(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        const result = Math.max(...nodeargs.map(a => YuiType.matchedNative(a)));
        return new YuiValue(Number.isInteger(result) ? result : result);
    }
    modules.push(['👑|最大値|max', yuiMax]);

    // ── 最小値 / min ──────────────────────────────────────────

    function yuiMin(...nodeargs) {
        checkNumberOfArgs(nodeargs, -1);
        nodeargs = arrayToVarargs(nodeargs);
        const result = Math.min(...nodeargs.map(a => YuiType.matchedNative(a)));
        return new YuiValue(Number.isInteger(result) ? result : result);
    }
    modules.push(['🐜|最小値|min', yuiMin]);

    // ── Type checks / conversions ─────────────────────────────

    function yuiIsint(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return YuiType.isInt(nodeargs[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push(['💯❓|整数判定|isint', yuiIsint]);

    function yuiToint(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return new YuiValue(Math.trunc(YuiType.matchedNative(nodeargs[0])));
    }
    modules.push(['💯|整数化|toint', yuiToint]);

    function yuiIsfloat(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return YuiType.isFloat(nodeargs[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push(['📊❓|少数判定|isfloat', yuiIsfloat]);

    function yuiTofloat(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        const value = nodeargs[0];
        if (YuiType.isString(value)) {
            const str = YuiType.matchedNative(value);
            const f = parseFloat(str);
            if (isNaN(f)) throw new YuiError(['error', 'conversion', `❌${str}`]);
            return new YuiValue(f, YuiType.FloatType);
        }
        // Explicitly set FloatType: in JS, parseFloat(3) === 3 (integer),
        // so we must force the type to distinguish float from int.
        return new YuiValue(parseFloat(YuiType.matchedNative(nodeargs[0])), YuiType.FloatType);
    }
    modules.push(['📊|少数化|tofloat', yuiTofloat]);

    function yuiIsstring(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return YuiType.isString(nodeargs[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push(['💬❓|文字列判定|isstring', yuiIsstring]);

    function yuiTostring(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        if (YuiType.isFloat(nodeargs[0])) {
            const v = YuiType.matchedNative(nodeargs[0]);
            return new YuiValue(v.toFixed(6));
        }
        return new YuiValue(String(nodeargs[0]));
    }
    modules.push(['💬|文字列化|tostring', yuiTostring]);

    function yuiIsobject(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return YuiType.isObject(nodeargs[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push(['🗂️❓|オブジェクト判定|isobject', yuiIsobject]);

    function yuiToobject(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        if (YuiType.isObject(nodeargs[0])) return nodeargs[0];
        if (YuiType.isString(nodeargs[0])) {
            const s = YuiType.matchedNative(nodeargs[0]);
            if (s.startsWith('{')) {
                try {
                    return new YuiValue(JSON.parse(s));
                } catch {}
            }
        }
        return new YuiValue({});
    }
    modules.push(['🗂️|オブジェクト化|toobject', yuiToobject]);

    function yuiIsarray(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        return YuiType.isArray(nodeargs[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push(['🍡❓|配列判定|isarray', yuiIsarray]);

    function yuiToarray(...nodeargs) {
        checkNumberOfArgs(nodeargs, 1);
        const value = nodeargs[0];
        if (value instanceof YuiValue) {
            // Force compute arrayview and discard native value
            const _ = value.arrayview;
            value._nativeValue = null;
            return value;
        }
        return new YuiValue(YuiType.matchedNative(value));
    }
    modules.push(['🍡|配列化|toarray', yuiToarray]);
}
