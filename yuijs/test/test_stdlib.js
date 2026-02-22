// test_stdlib.js — tests for yuistdlib.js
import { describe, test, expect, beforeAll } from 'vitest';
import { YuiValue, YuiType, YuiError } from '../src/yuitypes.js';
import { standardLib } from '../src/yuistdlib.js';

// Build stdlib map: English name → function (mirrors Python fixture)
let stdlib;
beforeAll(() => {
    const modules = [];
    standardLib(modules);
    stdlib = Object.fromEntries(
        modules.map(([name, func]) => [name.split('|').at(-1), func])
    );
});

// Helper: Python value → YuiValue
function v(x) { return new YuiValue(x); }

// Helper: YuiValue → native JS value
function n(result) { return YuiType.toNative(result); }

// ─────────────────────────────────────────────────────────────────────────────
// 絶対値 / abs
// ─────────────────────────────────────────────────────────────────────────────

describe('abs', () => {
    test('positive int',    () => expect(n(stdlib.abs(v(5)))).toBe(5));
    test('negative int',    () => expect(n(stdlib.abs(v(-3)))).toBe(3));
    test('zero',            () => expect(n(stdlib.abs(v(0)))).toBe(0));
    test('positive float',  () => expect(n(stdlib.abs(v(1.5)))).toBeCloseTo(1.5));
    test('negative float',  () => expect(n(stdlib.abs(v(-2.5)))).toBeCloseTo(2.5));

    test('no args throws',      () => expect(() => stdlib.abs()).toThrow(YuiError));
    test('too many args throws', () => expect(() => stdlib.abs(v(1), v(2))).toThrow(YuiError));
    test('wrong type throws',   () => expect(() => stdlib.abs(v('hello'))).toThrow(YuiError));
});

// ─────────────────────────────────────────────────────────────────────────────
// 和 / sum
// ─────────────────────────────────────────────────────────────────────────────

describe('sum', () => {
    test('two ints',    () => expect(n(stdlib.sum(v(3), v(4)))).toBe(7));
    test('three ints',  () => expect(n(stdlib.sum(v(1), v(2), v(3)))).toBe(6));
    test('negative',    () => expect(n(stdlib.sum(v(-1), v(2)))).toBe(1));
    test('floats',      () => expect(n(stdlib.sum(v(1.5), v(2.5)))).toBeCloseTo(4.0));
    test('mixed',       () => expect(n(stdlib.sum(v(1), v(2.5)))).toBeCloseTo(3.5));

    test('no args throws', () => expect(() => stdlib.sum()).toThrow(YuiError));
});

// ─────────────────────────────────────────────────────────────────────────────
// 差 / diff
// ─────────────────────────────────────────────────────────────────────────────

describe('diff', () => {
    test('ints',     () => expect(n(stdlib.diff(v(10), v(3)))).toBe(7));
    test('negative', () => expect(n(stdlib.diff(v(3), v(10)))).toBe(-7));
    test('floats',   () => expect(n(stdlib.diff(v(5.0), v(2.0)))).toBeCloseTo(3.0));
});

// ─────────────────────────────────────────────────────────────────────────────
// 積 / product
// ─────────────────────────────────────────────────────────────────────────────

describe('product', () => {
    test('two ints',   () => expect(n(stdlib.product(v(3), v(4)))).toBe(12));
    test('three ints', () => expect(n(stdlib.product(v(2), v(3), v(4)))).toBe(24));
    test('floats',     () => expect(n(stdlib.product(v(2.0), v(3.0)))).toBeCloseTo(6.0));
    test('zero',       () => expect(n(stdlib.product(v(5), v(0)))).toBe(0));
});

// ─────────────────────────────────────────────────────────────────────────────
// 商 / quotient
// ─────────────────────────────────────────────────────────────────────────────

describe('quotient', () => {
    test('int division', () => expect(n(stdlib.quotient(v(10), v(3)))).toBe(3));
    test('exact',        () => expect(n(stdlib.quotient(v(10), v(2)))).toBe(5));
    // In JS, 10.0 === 10 (integer), so use a genuine float to trigger float branch
    test('float',        () => expect(n(stdlib.quotient(v(2.5), v(1)))).toBeCloseTo(2.5));

    test('zero division int throws',   () => expect(() => stdlib.quotient(v(10), v(0))).toThrow(YuiError));
    test('zero division float throws', () => expect(() => stdlib.quotient(v(10.0), v(0.0))).toThrow(YuiError));
});

// ─────────────────────────────────────────────────────────────────────────────
// 剰余 / remainder
// ─────────────────────────────────────────────────────────────────────────────

describe('remainder', () => {
    test('ints',        () => expect(n(stdlib.remainder(v(10), v(3)))).toBe(1));
    test('no remainder',() => expect(n(stdlib.remainder(v(9), v(3)))).toBe(0));
    test('floats',      () => expect(n(stdlib.remainder(v(5.5), v(2.0)))).toBeCloseTo(1.5));

    test('zero division throws', () => expect(() => stdlib.remainder(v(10), v(0))).toThrow(YuiError));
});

// ─────────────────────────────────────────────────────────────────────────────
// 最大値・最小値 / max, min
// ─────────────────────────────────────────────────────────────────────────────

describe('max and min', () => {
    test('max ints',     () => expect(n(stdlib.max(v(3), v(1), v(4), v(1), v(5)))).toBe(5));
    test('max floats',   () => expect(n(stdlib.max(v(1.5), v(2.5)))).toBeCloseTo(2.5));
    test('max negative', () => expect(n(stdlib.max(v(-3), v(-1)))).toBe(-1));
    test('min ints',     () => expect(n(stdlib.min(v(3), v(1), v(4)))).toBe(1));
    test('min floats',   () => expect(n(stdlib.min(v(1.5), v(0.5)))).toBeCloseTo(0.5));
    test('min negative', () => expect(n(stdlib.min(v(-3), v(-1)))).toBe(-3));

    test('max no args throws', () => expect(() => stdlib.max()).toThrow());
    test('min no args throws', () => expect(() => stdlib.min()).toThrow());
});

// ─────────────────────────────────────────────────────────────────────────────
// 乱数 / random, randint
// ─────────────────────────────────────────────────────────────────────────────

describe('random', () => {
    test('random returns float', () => expect(YuiType.isFloat(stdlib.random())).toBe(true));

    test('random is in [0, 1)', () => {
        for (let i = 0; i < 20; i++) {
            const val = n(stdlib.random());
            expect(val).toBeGreaterThanOrEqual(0.0);
            expect(val).toBeLessThan(1.0);
        }
    });

    test('randint returns int', () => expect(YuiType.isInt(stdlib.randint(v(10)))).toBe(true));

    test('randint is in [0, n)', () => {
        for (let i = 0; i < 20; i++) {
            const val = n(stdlib.randint(v(10)));
            expect(val).toBeGreaterThanOrEqual(0);
            expect(val).toBeLessThan(10);
        }
    });

    test('randint(1) always returns 0', () => {
        expect(n(stdlib.randint(v(1)))).toBe(0);
    });

    test('randint(0) throws', ()  => expect(() => stdlib.randint(v(0))).toThrow(YuiError));
    test('randint(-5) throws', () => expect(() => stdlib.randint(v(-5))).toThrow(YuiError));
});

// ─────────────────────────────────────────────────────────────────────────────
// ビット演算 / bitwise
// ─────────────────────────────────────────────────────────────────────────────

describe('bitwise', () => {
    test('and',          () => expect(n(stdlib.and(v(0b1010), v(0b1100)))).toBe(0b1000));
    test('and zero',     () => expect(n(stdlib.and(v(0b1111), v(0b0000)))).toBe(0));

    test('or',           () => expect(n(stdlib.or(v(0b1010), v(0b1100)))).toBe(0b1110));
    test('or identity',  () => expect(n(stdlib.or(v(0b1010), v(0)))).toBe(0b1010));

    test('xor',          () => expect(n(stdlib.xor(v(0b1010), v(0b1100)))).toBe(0b0110));
    test('xor self',     () => expect(n(stdlib.xor(v(0b1010), v(0b1010)))).toBe(0));

    test('not zero',     () => expect(n(stdlib.not(v(0)))).toBe(-1));
    test('not -1',       () => expect(n(stdlib.not(v(-1)))).toBe(0));
    test('not positive', () => expect(n(stdlib.not(v(1)))).toBe(-2));

    test('shl',          () => expect(n(stdlib.shl(v(1), v(3)))).toBe(8));
    test('shl zero',     () => expect(n(stdlib.shl(v(5), v(0)))).toBe(5));

    test('shr',          () => expect(n(stdlib.shr(v(8), v(3)))).toBe(1));
    test('shr zero',     () => expect(n(stdlib.shr(v(5), v(0)))).toBe(5));
});

// ─────────────────────────────────────────────────────────────────────────────
// 型判定 / type predicates
// ─────────────────────────────────────────────────────────────────────────────

describe('type predicates', () => {
    // isint
    // Note: In JS, 42.0 === 42 (integer), so use 3.14 to represent float
    test('isint — int returns true',    () => expect(n(stdlib.isint(v(42)))).toBe(true));
    test('isint — float returns false', () => expect(n(stdlib.isint(v(3.14)))).toBe(false));
    test('isint — string returns false',() => expect(n(stdlib.isint(v('hello')))).toBe(false));

    // isfloat
    test('isfloat — float returns true', () => expect(n(stdlib.isfloat(v(3.14)))).toBe(true));
    test('isfloat — int returns false',  () => expect(n(stdlib.isfloat(v(3)))).toBe(false));
    test('isfloat — string returns false',() => expect(n(stdlib.isfloat(v('3.14')))).toBe(false));

    // isstring
    test('isstring — string returns true', () => expect(n(stdlib.isstring(v('hello')))).toBe(true));
    test('isstring — int returns false',   () => expect(n(stdlib.isstring(v(42)))).toBe(false));
    test('isstring — float returns false', () => expect(n(stdlib.isstring(v(3.14)))).toBe(false));

    // isarray
    test('isarray — array returns true', () => expect(n(stdlib.isarray(v([1, 2, 3])))).toBe(true));
    test('isarray — int returns false',  () => expect(n(stdlib.isarray(v(42)))).toBe(false));

    // isobject
    test('isobject — object returns true', () => expect(n(stdlib.isobject(v({ a: 1 })))).toBe(true));
    test('isobject — int returns false',   () => expect(n(stdlib.isobject(v(42)))).toBe(false));
    test('isobject — array returns false', () => expect(n(stdlib.isobject(v([1, 2])))).toBe(false));
});

// ─────────────────────────────────────────────────────────────────────────────
// 型変換 / type conversions
// ─────────────────────────────────────────────────────────────────────────────

describe('type conversions', () => {
    // toint
    test('toint from float truncates toward zero', () => expect(n(stdlib.toint(v(3.9)))).toBe(3));
    test('toint from negative float',              () => expect(n(stdlib.toint(v(-3.9)))).toBe(-3));
    test('toint from int',                         () => expect(n(stdlib.toint(v(5)))).toBe(5));

    // tofloat
    test('tofloat from int returns float', () => {
        const result = stdlib.tofloat(v(3));
        expect(YuiType.isFloat(result)).toBe(true);
        expect(n(result)).toBeCloseTo(3.0);
    });
    test('tofloat from float', () => expect(n(stdlib.tofloat(v(3.14)))).toBeCloseTo(3.14));
    test('tofloat from string', () => expect(n(stdlib.tofloat(v('2.5')))).toBeCloseTo(2.5));

    // tostring
    test('tostring from int',          () => expect(n(stdlib.tostring(v(42)))).toBe('42'));
    test('tostring from float',        () => expect(n(stdlib.tostring(v(3.14)))).toBe('3.140000'));
    test('tostring from negative int', () => expect(n(stdlib.tostring(v(-5)))).toBe('-5'));

    // toarray
    test('toarray from array returns array', () => {
        const result = stdlib.toarray(v([1, 2, 3]));
        expect(YuiType.isArray(result)).toBe(true);
        expect(n(result)).toEqual([1, 2, 3]);
    });

    // toobject
    test('toobject from object returns object', () => {
        const result = stdlib.toobject(v({ x: 1 }));
        expect(YuiType.isObject(result)).toBe(true);
    });
});
