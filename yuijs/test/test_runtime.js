// test_runtime.js — port of yuichan/test/test_runtime.py
import { describe, test, expect } from 'vitest';
import { YuiRuntime } from '../src/yuiruntime.js';
import { YuiValue, YuiType } from '../src/yuitypes.js';

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
        const env = run('a = []\naの末尾に 99 を 追加する');
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
