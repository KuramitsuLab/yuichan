// test_runtime.js — port of yuichan/test/test_runtime.py
import { describe, test, expect } from 'vitest';
import { YuiRuntime } from '../src/yuiruntime.js';
import { YuiValue, YuiType, YuiError, types } from '../src/yuitypes.js';

const STDLIB = '標準ライブラリを使う\n';

// Test helpers
function run(source, syntax = 'yui') {
    const rt = new YuiRuntime();
    rt.exec(source, syntax, 30, false);
    return rt.environments[rt.environments.length - 1];
}

function runStd(source) {
    return run(STDLIB + source);
}

function val(env, name) {
    const v = env[name];
    return YuiType.yuiToNative(v);
}

// ─────────────────────────────────────────────
// Basic parsing and execution
// ─────────────────────────────────────────────

describe('basic execution', () => {
    test('integer assignment', () => {
        const env = run('x = 42');
        expect(val(env, 'x')).toBe(42);
    });

    test('float assignment', () => {
        const env = run('x = 3.14');
        expect(val(env, 'x')).toBeCloseTo(3.14);
    });

    test('string assignment', () => {
        const env = run('x = "hello"');
        expect(val(env, 'x')).toBe('hello');
    });

    test('array assignment', () => {
        const env = run('x = [1, 2, 3]');
        expect(val(env, 'x')).toEqual([1, 2, 3]);
    });

    test('null assignment', () => {
        const env = run('x = null');
        expect(val(env, 'x')).toBeNull();
    });

    test('true assignment', () => {
        const env = run('x = true');
        expect(val(env, 'x')).toBe(true);
    });

    test('false assignment', () => {
        const env = run('x = false');
        expect(val(env, 'x')).toBe(false);
    });
});

// ─────────────────────────────────────────────
// Yui syntax
// ─────────────────────────────────────────────

describe('yui syntax', () => {
    test('variable assignment', () => {
        const env = run('x = 10');
        expect(val(env, 'x')).toBe(10);
    });

    test('increment', () => {
        const env = run('x = 0\nxを増やす');
        expect(val(env, 'x')).toBe(1);
    });

    test('decrement', () => {
        const env = run('x = 5\nxを減らす');
        expect(val(env, 'x')).toBe(4);
    });

    test('array append', () => {
        const env = run('a = []\naの末尾に 99 を追加する');
        expect(val(env, 'a')).toEqual([99]);
    });

    test('array length', () => {
        const env = run('a = [1, 2, 3]\nx = |a|');
        expect(val(env, 'x')).toBe(3);
    });

    test('if-then (true branch)', () => {
        // もし A が B より大きいならば → if A > B
        const env = run('x = 0\nもし 2 が 1 より大きいならば、{\n  x = 1\n}');
        expect(val(env, 'x')).toBe(1);
    });

    test('repeat loop', () => {
        const env = run('x = 0\n3回、くり返す {\n  xを増やす\n}');
        expect(val(env, 'x')).toBe(3);
    });
});

// ─────────────────────────────────────────────
// Standard library
// ─────────────────────────────────────────────

describe('standard library', () => {
    test('和 (sum)', () => {
        const env = runStd('x = 和(3, 4)');
        expect(val(env, 'x')).toBe(7);
    });

    test('差 (diff)', () => {
        const env = runStd('x = 差(10, 3)');
        expect(val(env, 'x')).toBe(7);
    });

    test('積 (product)', () => {
        const env = runStd('x = 積(3, 4)');
        expect(val(env, 'x')).toBe(12);
    });

    test('商 (quotient integer)', () => {
        const env = runStd('x = 商(10, 3)');
        expect(val(env, 'x')).toBe(3);
    });

    test('商 (quotient float)', () => {
        const env = runStd('x = 商(10.0, 4.0)');
        expect(val(env, 'x')).toBeCloseTo(2.5);
    });

    test('剰余 (remainder)', () => {
        const env = runStd('x = 剰余(10, 3)');
        expect(val(env, 'x')).toBe(1);
    });

    test('絶対値 (abs)', () => {
        const env = runStd('x = 絶対値(-5)');
        expect(val(env, 'x')).toBe(5);
    });

    test('最大値 (max)', () => {
        const env = runStd('x = 最大値(3, 1, 4, 1, 5)');
        expect(val(env, 'x')).toBe(5);
    });

    test('最小値 (min)', () => {
        const env = runStd('x = 最小値(3, 1, 4, 1, 5)');
        expect(val(env, 'x')).toBe(1);
    });

    test('少数化 (tofloat)', () => {
        const env = runStd('x = 少数化(3)');
        expect(val(env, 'x')).toBeCloseTo(3.0);
    });

    test('整数化 (toint)', () => {
        const env = runStd('x = 整数化(3.9)');
        expect(val(env, 'x')).toBe(3);
    });

    test('平方根 (sqrt) — returns float', () => {
        const env = runStd('x = 平方根(4)');
        expect(types.isFloat(env['x'])).toBe(true);
        expect(val(env, 'x')).toBeCloseTo(2.0);
    });
});

// ─────────────────────────────────────────────
// Functions
// ─────────────────────────────────────────────

describe('function definition and call', () => {
    test('simple identity function', () => {
        // A function that returns its argument (no stdlib needed)
        const env = run('identity = 入力 n に対し {\n  nが答え\n}\nx = identity(42)');
        expect(val(env, 'x')).toBe(42);
    });

    test('function with stdlib', () => {
        const env = runStd(
            'double = 入力 n に対し {\n  積(n, 2)が答え\n}\nx = double(5)'
        );
        expect(val(env, 'x')).toBe(10);
    });

    test('recursive function (factorial)', () => {
        const env = runStd(`
factorial = 入力 n に対し {
    result = 1
    もし n が 1 より大きいならば、{
        prev = factorial(差(n, 1))
        result = 積(n, prev)
    }
    resultが答え
}
x = factorial(5)`);
        expect(val(env, 'x')).toBe(120);
    });
});

// ─────────────────────────────────────────────
// Assert / doctest
// ─────────────────────────────────────────────

describe('assert (doctest)', () => {
    test('passing assert', () => {
        const rt = new YuiRuntime();
        // Use array literal (no stdlib needed, no binary ops)
        rt.exec('>>> [1, 2]\n[1, 2]', 'yui', 30, false);
        // No exception = pass
    });

    test('assert with stdlib', () => {
        const rt = new YuiRuntime();
        rt.exec(STDLIB + '>>> 和(1, 2)\n3', 'yui', 30, false);
    });

    test('test_passed tracking', () => {
        const rt = new YuiRuntime();
        rt.exec(STDLIB + '>>> 和(1, 2)\n3', 'yui', 30, false);
        expect(rt.testPassed.length).toBe(1);
    });
});

// ─────────────────────────────────────────────
// Binary operators (allowBinaryOps = true)
// ─────────────────────────────────────────────

describe('binary operators', () => {
    function runBin(source) {
        const rt = new YuiRuntime();
        rt.allowBinaryOps = true;
        rt.exec(source, 'yui', 30, false);
        return rt.environments[rt.environments.length - 1];
    }

    // 無効時のエラー
    test('disabled by default', () => {
        const rt = new YuiRuntime();
        expect(() => rt.exec('x = 1 + 2', 'yui', 30, false)).toThrow(YuiError);
    });

    // 整数算術
    test('add ints',        () => expect(val(runBin('x = 1 + 2'),   'x')).toBe(3));
    test('subtract ints',   () => expect(val(runBin('x = 10 - 3'),  'x')).toBe(7));
    test('multiply ints',   () => expect(val(runBin('x = 3 * 4'),   'x')).toBe(12));
    test('divide int floor',() => expect(val(runBin('x = 10 / 3'),  'x')).toBe(3));
    test('modulo ints',     () => expect(val(runBin('x = 10 % 3'),  'x')).toBe(1));

    // 少数算術
    test('add floats',      () => expect(val(runBin('x = 1.5 + 2.5'), 'x')).toBeCloseTo(4.0));
    test('divide float',    () => expect(val(runBin('x = 10.0 / 4'),  'x')).toBeCloseTo(2.5));
    test('modulo float',    () => expect(val(runBin('x = 5.5 % 2.0'), 'x')).toBeCloseTo(1.5));

    // 型昇格: int OP float → float
    test('int + float is float', () => {
        const env = runBin('x = 1 + 2.0');
        expect(types.isFloat(env['x'])).toBe(true);
        expect(val(env, 'x')).toBeCloseTo(3.0);
    });
    test('int - float is float', () => {
        const env = runBin('x = 5 - 1.5');
        expect(types.isFloat(env['x'])).toBe(true);
        expect(val(env, 'x')).toBeCloseTo(3.5);
    });
    test('int * float is float', () => {
        const env = runBin('x = 3 * 2.0');
        expect(types.isFloat(env['x'])).toBe(true);
        expect(val(env, 'x')).toBeCloseTo(6.0);
    });
    test('int / float is float', () => {
        const env = runBin('x = 7 / 2.0');
        expect(types.isFloat(env['x'])).toBe(true);
        expect(val(env, 'x')).toBeCloseTo(3.5);
    });

    // 文字列連結
    test('string concat',       () => expect(val(runBin('x = "hello" + " world"'), 'x')).toBe('hello world'));
    test('string concat empty', () => expect(val(runBin('x = "" + "abc"'),          'x')).toBe('abc'));

    // 配列連結
    test('array concat',       () => expect(val(runBin('x = [1, 2] + [3, 4]'), 'x')).toEqual([1, 2, 3, 4]));
    test('array concat empty', () => expect(val(runBin('x = [] + [1, 2]'),     'x')).toEqual([1, 2]));

    // ゼロ除算
    test('divide by zero throws',  () => expect(() => runBin('x = 5 / 0')).toThrow(YuiError));
    test('modulo by zero throws',  () => expect(() => runBin('x = 5 % 0')).toThrow(YuiError));
});

// ─────────────────────────────────────────────
// Binary ops auto-unlock (関数定義 + アサート通過)
// ─────────────────────────────────────────────

describe('binary ops auto-unlock', () => {
    const FUNC_AND_ASSERT =
        STDLIB +
        'double = 入力 n に対し {\n' +
        '  積(n, 2)が答え\n' +
        '}\n' +
        '>>> double(3)\n' +
        '6\n';

    function runUnlocked(extra) {
        const rt = new YuiRuntime();
        rt.exec(FUNC_AND_ASSERT, 'yui', 30, false);
        rt.exec(extra, 'yui', 30, false);
        return rt.environments[rt.environments.length - 1];
    }

    // アンロック条件
    test('functionDefined starts false', () => {
        const rt = new YuiRuntime();
        expect(rt.functionDefined).toBe(false);
    });

    test('visitFuncDefNode sets functionDefined', () => {
        const rt = new YuiRuntime();
        rt.exec('f = 入力 n に対し { nが答え }', 'yui', 30, false);
        expect(rt.functionDefined).toBe(true);
    });

    test('locked without assert (func only)', () => {
        const rt = new YuiRuntime();
        rt.exec('f = 入力 n に対し { nが答え }', 'yui', 30, false);
        expect(() => rt.exec('x = 1 + 2', 'yui', 30, false)).toThrow(YuiError);
    });

    test('locked without function (assert only)', () => {
        const rt = new YuiRuntime();
        rt.exec(STDLIB + '>>> 和(1, 2)\n3', 'yui', 30, false);
        expect(() => rt.exec('x = 1 + 2', 'yui', 30, false)).toThrow(YuiError);
    });

    test('unlocked after func + assert', () => expect(val(runUnlocked('x = 1 + 2'),   'x')).toBe(3));
    test('unlocked add',                 () => expect(val(runUnlocked('x = 10 + 5'),  'x')).toBe(15));
    test('unlocked subtract',            () => expect(val(runUnlocked('x = 10 - 3'),  'x')).toBe(7));
    test('unlocked multiply',            () => expect(val(runUnlocked('x = 3 * 4'),   'x')).toBe(12));
    test('unlocked divide',              () => expect(val(runUnlocked('x = 10 / 4'),  'x')).toBe(2));
    test('unlocked modulo',              () => expect(val(runUnlocked('x = 10 % 3'),  'x')).toBe(1));
});

// ─────────────────────────────────────────────
// YuiRuntime.exec eval mode
// ─────────────────────────────────────────────

describe('exec() evalMode', () => {
    test('evalMode=true returns last value', () => {
        const rt = new YuiRuntime();
        const result = rt.exec('x = 42', 'yui', 30, true);
        // exec in eval_mode returns last value (undefined for assignment)
    });

    test('evalMode=false returns environment', () => {
        const rt = new YuiRuntime();
        const env = rt.exec('x = 42', 'yui', 30, false);
        expect(env['x']).toBeDefined();
    });
});
