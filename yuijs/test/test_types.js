// test_types.js — port of yuichan/test/test_types.py
import { describe, test, expect } from 'vitest';
import {
    YuiValue, YuiType, YuiError,
    YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType,
    YuiStringType, YuiArrayType, YuiObjectType,
    OPERATORS,
} from '../src/yuitypes.js';

// ─────────────────────────────────────────────
// YuiValue construction
// ─────────────────────────────────────────────

describe('YuiValue construction', () => {
    test('null', () => {
        const v = new YuiValue(null);
        expect(v.type).toBeInstanceOf(YuiNullType);
        expect(v.native).toBeNull();
    });

    test('boolean true', () => {
        const v = new YuiValue(true);
        expect(v.type).toBeInstanceOf(YuiBooleanType);
        expect(v.native).toBe(true);
    });

    test('boolean false', () => {
        const v = new YuiValue(false);
        expect(v.type).toBeInstanceOf(YuiBooleanType);
        expect(v.native).toBe(false);
    });

    test('integer', () => {
        const v = new YuiValue(42);
        expect(v.type).toBeInstanceOf(YuiIntType);
        expect(v.native).toBe(42);
    });

    test('float', () => {
        const v = new YuiValue(3.14);
        expect(v.type).toBeInstanceOf(YuiFloatType);
        expect(v.native).toBeCloseTo(3.14);
    });

    test('string', () => {
        const v = new YuiValue('hello');
        expect(v.type).toBeInstanceOf(YuiStringType);
        expect(v.native).toBe('hello');
    });

    test('array', () => {
        const v = new YuiValue([1, 2, 3]);
        expect(v.type).toBeInstanceOf(YuiArrayType);
        expect(v.native).toEqual([1, 2, 3]);
    });

    test('object', () => {
        const v = new YuiValue({ a: 1 });
        expect(v.type).toBeInstanceOf(YuiObjectType);
        expect(v.native).toEqual({ a: 1 });
    });

    test('NullValue constant', () => {
        expect(YuiValue.NullValue.native).toBeNull();
        expect(YuiValue.NullValue.type).toBeInstanceOf(YuiNullType);
    });

    test('TrueValue constant', () => {
        expect(YuiValue.TrueValue.native).toBe(true);
        expect(YuiValue.TrueValue.type).toBeInstanceOf(YuiBooleanType);
    });

    test('FalseValue constant', () => {
        expect(YuiValue.FalseValue.native).toBe(false);
        expect(YuiValue.FalseValue.type).toBeInstanceOf(YuiBooleanType);
    });
});

// ─────────────────────────────────────────────
// YuiType.match
// ─────────────────────────────────────────────

describe('YuiType.match', () => {
    test('NullType matches null', () => {
        expect(YuiType.NullType.match(null)).toBe(true);
        expect(YuiType.NullType.match(YuiValue.NullValue)).toBe(true);
        expect(YuiType.NullType.match(0)).toBe(false);
    });

    test('BooleanType matches booleans', () => {
        expect(YuiType.BooleanType.match(true)).toBe(true);
        expect(YuiType.BooleanType.match(false)).toBe(true);
        expect(YuiType.BooleanType.match(YuiValue.TrueValue)).toBe(true);
        // integer 1 should NOT match BooleanType (JS has distinct types)
        expect(YuiType.BooleanType.match(1)).toBe(false);
    });

    test('IntType matches integers but not floats or booleans', () => {
        expect(YuiType.IntType.match(42)).toBe(true);
        expect(YuiType.IntType.match(0)).toBe(true);
        expect(YuiType.IntType.match(3.14)).toBe(false);
        expect(YuiType.IntType.match(true)).toBe(false);
        expect(YuiType.IntType.match(false)).toBe(false);
    });

    test('FloatType matches floats', () => {
        expect(YuiType.FloatType.match(3.14)).toBe(true);
        expect(YuiType.FloatType.match(42)).toBe(false);
        expect(YuiType.FloatType.match(new YuiValue(1.5))).toBe(true);
    });

    test('StringType matches strings', () => {
        expect(YuiType.StringType.match('hello')).toBe(true);
        expect(YuiType.StringType.match(42)).toBe(false);
    });

    test('ArrayType matches arrays', () => {
        expect(YuiType.ArrayType.match([1, 2])).toBe(true);
        expect(YuiType.ArrayType.match(new YuiValue([]))).toBe(true);
        expect(YuiType.ArrayType.match('hello')).toBe(false);
    });

    test('ObjectType matches objects', () => {
        expect(YuiType.ObjectType.match({ a: 1 })).toBe(true);
        expect(YuiType.ObjectType.match(new YuiValue({ a: 1 }))).toBe(true);
        expect(YuiType.ObjectType.match([1, 2])).toBe(false);
    });
});

// ─────────────────────────────────────────────
// arrayview / native round-trip
// ─────────────────────────────────────────────

describe('arrayview round-trip', () => {
    test('int 0', () => {
        const bits = YuiType.IntType.toArrayview(0);
        expect(bits).toHaveLength(32);
        expect(YuiType.IntType.toNative(bits)).toBe(0);
    });

    test('int positive', () => {
        const bits = YuiType.IntType.toArrayview(42);
        expect(YuiType.IntType.toNative(bits)).toBe(42);
    });

    test('int negative', () => {
        const v = new YuiValue(-1);
        expect(YuiType.IntType.toNative(v.arrayview, v.sign)).toBe(-1);
    });

    test('float round-trip', () => {
        const v = new YuiValue(3.14);
        const result = YuiType.FloatType.toNative(v.arrayview, v.sign);
        expect(result).toBeCloseTo(3.14, 5);
    });

    test('float negative', () => {
        const v = new YuiValue(-2.5);
        const result = YuiType.FloatType.toNative(v.arrayview, v.sign);
        expect(result).toBeCloseTo(-2.5, 5);
    });

    test('string char codes', () => {
        const codes = YuiType.StringType.toArrayview('abc');
        expect(codes).toEqual([97, 98, 99]);
        expect(YuiType.StringType.toNative(codes)).toBe('abc');
    });
});

// ─────────────────────────────────────────────
// YuiValue.equals
// ─────────────────────────────────────────────

describe('YuiValue.equals', () => {
    test('int equals int', () => {
        expect(new YuiValue(1).equals(new YuiValue(1))).toBe(true);
        expect(new YuiValue(1).equals(new YuiValue(2))).toBe(false);
    });

    test('float equals float (6 decimal places)', () => {
        expect(new YuiValue(1.0).equals(new YuiValue(1.0))).toBe(true);
        expect(new YuiValue(3.14).equals(new YuiValue(3.14))).toBe(true);
    });

    test('int equals float', () => {
        expect(new YuiValue(1).equals(new YuiValue(1.0))).toBe(true);
    });

    test('bool equals bool', () => {
        expect(YuiValue.TrueValue.equals(YuiValue.TrueValue)).toBe(true);
        expect(YuiValue.FalseValue.equals(YuiValue.TrueValue)).toBe(false);
    });

    test('bool does not equal int', () => {
        // true !== 1 in Yui
        expect(YuiValue.TrueValue.equals(new YuiValue(1))).toBe(false);
    });

    test('null equals null', () => {
        expect(YuiValue.NullValue.equals(YuiValue.NullValue)).toBe(true);
    });

    test('string equals string', () => {
        expect(new YuiValue('hello').equals(new YuiValue('hello'))).toBe(true);
        expect(new YuiValue('hello').equals(new YuiValue('world'))).toBe(false);
    });

    test('array equals array', () => {
        expect(new YuiValue([1, 2]).equals(new YuiValue([1, 2]))).toBe(true);
        expect(new YuiValue([1, 2]).equals(new YuiValue([1, 3]))).toBe(false);
    });

    test('char-code array equals string', () => {
        // [97, 98, 99] equals "abc" (cross-type comparison)
        expect(new YuiValue([97, 98, 99]).equals(new YuiValue('abc'))).toBe(true);
    });
});

// ─────────────────────────────────────────────
// YuiValue.getItem / setItem / append
// ─────────────────────────────────────────────

describe('YuiValue.getItem / setItem / append', () => {
    test('getItem from array', () => {
        const arr = new YuiValue([10, 20, 30]);
        const idx = new YuiValue(1);
        const item = arr.getItem(idx);
        expect(item.native).toBe(20);
    });

    test('setItem in array', () => {
        const arr = new YuiValue([10, 20, 30]);
        const idx = new YuiValue(0);
        arr.setItem(idx, new YuiValue(99));
        expect(arr.native[0]).toBe(99);
    });

    test('append to array', () => {
        const arr = new YuiValue([]);
        arr.append(new YuiValue(42));
        expect(arr.native).toEqual([42]);
    });
});

// ─────────────────────────────────────────────
// OPERATORS
// ─────────────────────────────────────────────

describe('OPERATORS', () => {
    test('== returns true for equal values', () => {
        const a = new YuiValue(5);
        const b = new YuiValue(5);
        expect(OPERATORS['=='].evaluate(a, b)).toBe(true);
    });

    test('!= returns true for unequal values', () => {
        const a = new YuiValue(5);
        const b = new YuiValue(6);
        expect(OPERATORS['!='].evaluate(a, b)).toBe(true);
    });

    test('< compares integers', () => {
        const a = new YuiValue(3);
        const b = new YuiValue(5);
        expect(OPERATORS['<'].evaluate(a, b)).toBe(true);
        expect(OPERATORS['<'].evaluate(b, a)).toBe(false);
    });

    test('> compares integers', () => {
        const a = new YuiValue(7);
        const b = new YuiValue(3);
        expect(OPERATORS['>'].evaluate(a, b)).toBe(true);
    });

    test('in checks membership', () => {
        const elem = new YuiValue(2);
        const arr = new YuiValue([1, 2, 3]);
        expect(OPERATORS['in'].evaluate(elem, arr)).toBe(true);
        const notElem = new YuiValue(9);
        expect(OPERATORS['in'].evaluate(notElem, arr)).toBe(false);
    });
});

// ─────────────────────────────────────────────
// YuiValue.stringfy
// ─────────────────────────────────────────────

describe('YuiValue.stringfy', () => {
    test('null', () => {
        expect(YuiValue.NullValue.stringfy()).toBe('null');
    });

    test('true / false', () => {
        expect(YuiValue.TrueValue.stringfy()).toBe('true');
        expect(YuiValue.FalseValue.stringfy()).toBe('false');
    });

    test('int', () => {
        expect(new YuiValue(42).stringfy()).toBe('42');
    });

    test('float', () => {
        expect(new YuiValue(3.14).stringfy()).toBe('3.140000');
    });

    test('string', () => {
        expect(new YuiValue('hello').stringfy()).toBe('"hello"');
    });
});
