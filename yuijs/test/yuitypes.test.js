// yuitypes.js の単体テスト (Python 版 yuichan/test_types.py を移植)
// node --test test/yuitypes.test.js

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  YuiValue,
  YuiError,
  types,
  OPERATORS,
  YuiNullType,
  YuiBooleanType,
  YuiIntType,
  YuiFloatType,
  YuiStringType,
  YuiArrayType,
  YuiObjectType,
  NullType,
  BoolType,
  IntType,
  FloatType,
  StringType,
  ArrayType,
  ObjectType,
} from '../src/yuitypes.js';

// ─────────────────────────────────────────────
// box / unbox ラウンドトリップ
// ─────────────────────────────────────────────
//
// Python 側 BOX_CASES と同じ並び。ただし JS では 1.0 と 1 が区別できないため
// float ケースは「明示的に FloatType を指定する」別パスで扱う。

const BOX_CASES = [
  { native: null, Ty: YuiNullType },
  { native: true, Ty: YuiBooleanType },
  { native: false, Ty: YuiBooleanType },
  { native: 1, Ty: YuiIntType },
  { native: 0, Ty: YuiIntType },
  { native: -1, Ty: YuiIntType },
  { native: 1.5, Ty: YuiFloatType }, // 非整数は自動で float
  { native: -2.25, Ty: YuiFloatType },
  { native: '', Ty: YuiStringType },
  { native: '123', Ty: YuiStringType },
  { native: [], Ty: YuiArrayType },
  { native: [1, 2, 3], Ty: YuiArrayType },
  { native: {}, Ty: YuiObjectType },
  { native: { a: 1, b: 2 }, Ty: YuiObjectType },
];

for (const { native, Ty } of BOX_CASES) {
  test(`box(${JSON.stringify(native)}) returns YuiValue`, () => {
    assert.ok(types.box(native) instanceof YuiValue);
  });
  test(`box(${JSON.stringify(native)}).type is ${Ty.name}`, () => {
    const v = types.box(native);
    assert.ok(v.type instanceof Ty);
  });
  test(`box(${JSON.stringify(native)}).native === input`, () => {
    const v = types.box(native);
    if (native === null) {
      assert.equal(v.native, null);
    } else if (Array.isArray(native) || typeof native === 'object') {
      assert.deepEqual(v.native, native);
    } else {
      assert.equal(v.native, native);
    }
  });
  test(`unbox(box(${JSON.stringify(native)})) === input`, () => {
    const v = types.box(native);
    const result = types.unbox(v);
    if (native === null) {
      assert.equal(result, null);
    } else {
      assert.deepEqual(result, native);
    }
  });
}

// ─────────────────────────────────────────────
// box の冪等性 / シングルトン
// ─────────────────────────────────────────────
test('box(YuiValue) returns the same instance', () => {
  const v = new YuiValue(42);
  assert.equal(types.box(v), v);
});

test('box(null) is YuiValue.NullValue', () => {
  assert.equal(types.box(null), YuiValue.NullValue);
});

test('box(true) is YuiValue.TrueValue', () => {
  assert.equal(types.box(true), YuiValue.TrueValue);
});

test('box(false) is YuiValue.FalseValue', () => {
  assert.equal(types.box(false), YuiValue.FalseValue);
});

// ─────────────────────────────────────────────
// 型判定 (is_*)
// ─────────────────────────────────────────────
const IS_TYPE_CASES = [
  { native: null, expected: [false, false, false, false, false, false] },
  { native: true, expected: [true, false, false, false, false, false] },
  { native: false, expected: [true, false, false, false, false, false] },
  { native: 1, expected: [false, true, false, false, false, false] },
  { native: 0, expected: [false, true, false, false, false, false] },
  { native: -1, expected: [false, true, false, false, false, false] },
  { native: 1.5, expected: [false, false, true, false, false, false] },
  { native: -0.25, expected: [false, false, true, false, false, false] },
  { native: '', expected: [false, false, false, true, false, false] },
  { native: '123', expected: [false, false, false, true, false, false] },
  { native: [], expected: [false, false, false, false, true, false] },
  { native: [1, 2, 3], expected: [false, false, false, false, true, false] },
  { native: {}, expected: [false, false, false, false, false, true] },
  { native: { a: 1 }, expected: [false, false, false, false, false, true] },
];

for (const { native, expected } of IS_TYPE_CASES) {
  const [isBool, isInt, isFloat, isStr, isArr, isObj] = expected;
  test(`is_* for ${JSON.stringify(native)}`, () => {
    const v = types.box(native);
    assert.equal(types.is_bool(v), isBool, 'is_bool');
    assert.equal(types.is_int(v), isInt, 'is_int');
    assert.equal(types.is_float(v), isFloat, 'is_float');
    assert.equal(types.is_string(v), isStr, 'is_string');
    assert.equal(types.is_array(v), isArr, 'is_array');
    assert.equal(types.is_object(v), isObj, 'is_object');
  });
}

test('is_number: int', () => {
  assert.ok(types.is_number(types.box(42)));
});
test('is_number: float', () => {
  assert.ok(types.is_number(types.box(3.14)));
});
test('is_number: bool is NOT a number', () => {
  assert.ok(!types.is_number(types.box(true)));
});
test('is_number: string is NOT a number', () => {
  assert.ok(!types.is_number(types.box('1')));
});

// ─────────────────────────────────────────────
// 明示的 FloatType: int と float の区別
// ─────────────────────────────────────────────
test('explicit FloatType: 1.0 as float is not int', () => {
  const f = new YuiValue(1, FloatType);
  assert.ok(types.is_float(f));
  assert.ok(!types.is_int(f));
});

test('explicit FloatType: equals int with same value', () => {
  const f = new YuiValue(1, FloatType);
  const i = types.box(1);
  // int/float cross-type 等値
  assert.ok(f.equals(i));
  assert.ok(i.equals(f));
});

test('explicit FloatType: stringify shows 6 decimals', () => {
  const f = new YuiValue(1, FloatType);
  assert.equal(FloatType.stringify(1), '1.000000');
  assert.equal(f.stringify(null), '1.000000');
});

// ─────────────────────────────────────────────
// get_item / set_item / append (Array)
// ─────────────────────────────────────────────
test('Array: get_item', () => {
  const v = new YuiValue([10, 20, 30]);
  assert.equal(v.get_item(new YuiValue(0)).native, 10);
  assert.equal(v.get_item(new YuiValue(2)).native, 30);
});

test('Array: set_item', () => {
  const v = new YuiValue([10, 20, 30]);
  v.set_item(new YuiValue(1), new YuiValue(99));
  assert.deepEqual(v.native, [10, 99, 30]);
});

test('Array: append', () => {
  const v = new YuiValue([1, 2]);
  v.append(new YuiValue(3));
  assert.deepEqual(v.native, [1, 2, 3]);
});

test('Array: append to empty', () => {
  const v = new YuiValue([]);
  v.append(new YuiValue(42));
  assert.deepEqual(v.native, [42]);
});

test('Array: get_item out of range throws', () => {
  assert.throws(
    () => new YuiValue([1, 2]).get_item(new YuiValue(5)),
    YuiError,
  );
});

test('Array: get_item negative throws', () => {
  assert.throws(
    () => new YuiValue([1, 2]).get_item(new YuiValue(-1)),
    YuiError,
  );
});

test('Array: set then get', () => {
  const v = new YuiValue([0, 0, 0]);
  v.set_item(new YuiValue(1), new YuiValue(7));
  assert.equal(v.get_item(new YuiValue(1)).native, 7);
});

// ─────────────────────────────────────────────
// String (文字コード単位)
// ─────────────────────────────────────────────
test('String: get_item returns char code', () => {
  const v = new YuiValue('ABC');
  assert.equal(v.get_item(new YuiValue(0)).native, 'A'.codePointAt(0));
  assert.equal(v.get_item(new YuiValue(2)).native, 'C'.codePointAt(0));
});

test('String: set_item', () => {
  const v = new YuiValue('ABC');
  v.set_item(new YuiValue(1), new YuiValue('X'.codePointAt(0)));
  assert.equal(v.native, 'AXC');
});

test('String: append', () => {
  const v = new YuiValue('AB');
  v.append(new YuiValue('C'.codePointAt(0)));
  assert.equal(v.native, 'ABC');
});

test('String: append to empty', () => {
  const v = new YuiValue('');
  v.append(new YuiValue('Z'.codePointAt(0)));
  assert.equal(v.native, 'Z');
});

test('String: get_item out of range throws', () => {
  assert.throws(
    () => new YuiValue('AB').get_item(new YuiValue(5)),
    YuiError,
  );
});

// ─────────────────────────────────────────────
// Object (文字列キー)
// ─────────────────────────────────────────────
test('Object: get_item by key', () => {
  const v = new YuiValue({ x: 10, y: 20 });
  assert.equal(v.get_item(new YuiValue('x')).native, 10);
  assert.equal(v.get_item(new YuiValue('y')).native, 20);
});

test('Object: missing key returns NullValue', () => {
  const v = new YuiValue({ x: 10 });
  assert.equal(v.get_item(new YuiValue('z')).native, null);
});

test('Object: set_item existing key', () => {
  const v = new YuiValue({ x: 10 });
  v.set_item(new YuiValue('x'), new YuiValue(99));
  assert.equal(v.native.x, 99);
});

test('Object: set_item new key', () => {
  const v = new YuiValue({ x: 10 });
  v.set_item(new YuiValue('y'), new YuiValue(20));
  assert.equal(v.native.y, 20);
});

test('Object: set then get', () => {
  const v = new YuiValue({});
  v.set_item(new YuiValue('k'), new YuiValue(42));
  assert.equal(v.get_item(new YuiValue('k')).native, 42);
});

// ─────────────────────────────────────────────
// Int (ビット単位 get_item / set_item)
// ─────────────────────────────────────────────
test('Int: get_item returns bits LSB-first', () => {
  const v = new YuiValue(5); // 0b101
  assert.equal(v.get_item(new YuiValue(0)).native, 1);
  assert.equal(v.get_item(new YuiValue(1)).native, 0);
  assert.equal(v.get_item(new YuiValue(2)).native, 1);
});

test('Int: get_item implicit leading zero', () => {
  const v = new YuiValue(5);
  assert.equal(v.get_item(new YuiValue(31)).native, 0);
});

test('Int: set_item flip bit', () => {
  const v = new YuiValue(2); // [0, 1]
  v.set_item(new YuiValue(0), new YuiValue(1));
  assert.equal(v.native, 3);
});

test('Int: set_item clear bit', () => {
  const v = new YuiValue(3); // [1, 1]
  v.set_item(new YuiValue(1), new YuiValue(0));
  assert.equal(v.native, 1);
});

test('Int: set_item out of range throws', () => {
  const v = new YuiValue(0);
  assert.throws(() => v.set_item(new YuiValue(1), new YuiValue(1)), YuiError);
});

test('Int: get_item negative throws', () => {
  assert.throws(() => new YuiValue(0).get_item(new YuiValue(-1)), YuiError);
});

// ─────────────────────────────────────────────
// arrayview ラウンドトリップ
// ─────────────────────────────────────────────
test('IntType: arrayview roundtrip 0', () => {
  assert.deepEqual(IntType.to_arrayview(0), []);
  assert.equal(IntType.to_native([], 1), 0);
});

test('IntType: arrayview roundtrip 5', () => {
  const bits = IntType.to_arrayview(5);
  assert.deepEqual(bits, [1, 0, 1]);
  assert.equal(IntType.to_native(bits, 1), 5);
});

test('IntType: arrayview roundtrip -42', () => {
  const bits = IntType.to_arrayview(-42);
  const sign = IntType.to_sign(-42);
  assert.equal(IntType.to_native(bits, sign), -42);
});

test('IntType: arrayview large number', () => {
  const n = 1234567;
  const bits = IntType.to_arrayview(n);
  assert.equal(IntType.to_native(bits, 1), n);
});

test('FloatType: arrayview roundtrip 3.14', () => {
  const digits = FloatType.to_arrayview(3.14);
  assert.deepEqual(digits, [0, 0, 0, 0, 4, 1, 3]);
  assert.equal(FloatType.to_native(digits, 1), 3.14);
});

test('FloatType: arrayview roundtrip -3.14', () => {
  const digits = FloatType.to_arrayview(-3.14);
  const sign = FloatType.to_sign(-3.14);
  assert.equal(FloatType.to_native(digits, sign), -3.14);
});

test('FloatType: arrayview roundtrip 0.5', () => {
  const digits = FloatType.to_arrayview(0.5);
  assert.equal(FloatType.to_native(digits, 1), 0.5);
});

test('StringType: arrayview roundtrip', () => {
  const codes = StringType.to_arrayview('Hello');
  assert.deepEqual(codes, [72, 101, 108, 108, 111]);
  assert.equal(StringType.to_native(codes), 'Hello');
});

// ─────────────────────────────────────────────
// equals: 同値 / 異型 / 同型異値
// ─────────────────────────────────────────────
for (const { native } of BOX_CASES) {
  test(`equals self: ${JSON.stringify(native)}`, () => {
    const v = types.box(native);
    assert.ok(v.equals(v));
  });
  test(`equals copy: ${JSON.stringify(native)}`, () => {
    const a = types.box(native);
    const b = types.box(native);
    assert.ok(a.equals(b));
  });
}

// bool は int/float と等しくない
for (const [b, n] of [
  [true, 1],
  [false, 0],
]) {
  test(`bool ${b} !== number ${n}`, () => {
    assert.ok(!types.box(b).equals(types.box(n)));
    assert.ok(!types.box(n).equals(types.box(b)));
  });
}

// 異なる型は等しくない
const CROSS_TYPE_PAIRS = [
  [null, 0],
  [null, false],
  [null, ''],
  [null, []],
  [null, {}],
  [true, 1],
  [false, 0],
  [1, '1'],
  [1, [1]],
  [[], {}],
  [[1, 2, 3], { a: 1 }],
];

for (const [a, b] of CROSS_TYPE_PAIRS) {
  test(`not equals: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`, () => {
    assert.ok(!types.box(a).equals(types.box(b)));
    assert.ok(!types.box(b).equals(types.box(a)));
  });
}

// 同型・異値
const SAME_TYPE_PAIRS = [
  [true, false],
  [1, 0],
  [1, -1],
  [0, -1],
  [1.5, 0.5],
  [1.5, -1.5],
  ['', '123'],
  [[], [1, 2, 3]],
  [{}, { a: 1, b: 2 }],
];

for (const [a, b] of SAME_TYPE_PAIRS) {
  test(`same type not equal: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`, () => {
    assert.ok(!types.box(a).equals(types.box(b)));
    assert.ok(!types.box(b).equals(types.box(a)));
  });
}

// charcode array ⇔ string cross-equal
test('array equals: charcode array vs string', () => {
  const arr = types.box([72, 105]);
  const str = types.box('Hi');
  assert.ok(arr.equals(str));
});

// ─────────────────────────────────────────────
// OPERATORS
// ─────────────────────────────────────────────
function op(symbol, a, b) {
  return OPERATORS[symbol].evaluate(types.box(a), types.box(b));
}

// == ───────────────────────────────────────────
const EQ_CASES = [
  [null, null, true],
  [true, true, true],
  [false, false, true],
  [1, 1, true],
  [0, 0, true],
  [-1, -1, true],
  [1.5, 1.5, true],
  ['hi', 'hi', true],
  [[1, 2], [1, 2], true],
  [1, 2, false],
  [true, false, false],
  [true, 1, false],
  [false, 0, false],
];

for (const [a, b, expected] of EQ_CASES) {
  test(`== ${JSON.stringify(a)} vs ${JSON.stringify(b)}`, () => {
    assert.equal(op('==', a, b), expected);
  });
}

// != ───────────────────────────────────────────
const NE_CASES = [
  [1, 2, true],
  [1, 1, false],
  [true, 1, true],
  [true, true, false],
];

for (const [a, b, expected] of NE_CASES) {
  test(`!= ${JSON.stringify(a)} vs ${JSON.stringify(b)}`, () => {
    assert.equal(op('!=', a, b), expected);
  });
}

// < ───────────────────────────────────────────
const LT_CASES = [
  [1, 2, true],
  [2, 1, false],
  [1, 1, false],
  [1.5, 2.5, true],
  [1, 1.5, true],
  [1.5, 2, true],
  ['abc', 'abd', true],
  [false, true, true],
];

for (const [a, b, expected] of LT_CASES) {
  test(`< ${JSON.stringify(a)} vs ${JSON.stringify(b)}`, () => {
    assert.equal(op('<', a, b), expected);
  });
}

// > ───────────────────────────────────────────
test('> 2 1 is true', () => assert.equal(op('>', 2, 1), true));
test('> 1 2 is false', () => assert.equal(op('>', 1, 2), false));
test('> 1 1 is false', () => assert.equal(op('>', 1, 1), false));
test('> 2.5 1.5 is true', () => assert.equal(op('>', 2.5, 1.5), true));

// <= / >= ─────────────────────────────────────
test('<= 1 2 is true', () => assert.equal(op('<=', 1, 2), true));
test('<= 1 1 is true', () => assert.equal(op('<=', 1, 1), true));
test('<= 2 1 is false', () => assert.equal(op('<=', 2, 1), false));
test('>= 2 1 is true', () => assert.equal(op('>=', 2, 1), true));
test('>= 1 1 is true', () => assert.equal(op('>=', 1, 1), true));
test('>= 1 2 is false', () => assert.equal(op('>=', 1, 2), false));

// in / notin ─────────────────────────────────
test('in: 2 in [1,2,3]', () => assert.equal(op('in', 2, [1, 2, 3]), true));
test('in: 9 in [1,2,3]', () => assert.equal(op('in', 9, [1, 2, 3]), false));
test('in: 0 in []', () => assert.equal(op('in', 0, []), false));
test('notin: 2 notin [1,2,3]', () =>
  assert.equal(op('notin', 2, [1, 2, 3]), false));
test('notin: 9 notin [1,2,3]', () =>
  assert.equal(op('notin', 9, [1, 2, 3]), true));
test('notin: 0 notin []', () => assert.equal(op('notin', 0, []), true));

// + ──────────────────────────────────────────
test('+ int int', () => assert.equal(op('+', 1, 2), 3));
test('+ float float', () => assert.equal(op('+', 1.5, 2.5), 4));
test('+ string string', () => assert.equal(op('+', 'ab', 'cd'), 'abcd'));
test('+ array array', () =>
  assert.deepEqual(op('+', [1, 2], [3, 4]), [1, 2, 3, 4]));

// - ──────────────────────────────────────────
test('- int int', () => assert.equal(op('-', 5, 2), 3));

// * ──────────────────────────────────────────
test('* int int', () => assert.equal(op('*', 3, 4), 12));

// / ──────────────────────────────────────────
test('/ int int floor', () => assert.equal(op('/', 7, 2), 3));
test('/ float float', () => assert.equal(op('/', 7.5, 2.5), 3));
test('/ div by zero throws', () => {
  assert.throws(() => op('/', 1, 0), YuiError);
});

test('/ int float', () => {
  // 明示的 FloatType で割り算
  const l = types.box(7);
  const r = new YuiValue(2, FloatType);
  assert.equal(OPERATORS['/'].evaluate(l, r), 3.5);
});

// % ──────────────────────────────────────────
test('% int int', () => assert.equal(op('%', 7, 3), 1));
test('% negative', () => assert.equal(op('%', -1, 3), 2)); // Python の挙動に合わせて常に非負
test('% div by zero throws', () => {
  assert.throws(() => op('%', 1, 0), YuiError);
});

// ─────────────────────────────────────────────
// format_json
// ─────────────────────────────────────────────
test('format_json: null', () => assert.equal(types.format_json(null), 'null'));
test('format_json: true', () => assert.equal(types.format_json(true), 'true'));
test('format_json: false', () =>
  assert.equal(types.format_json(false), 'false'));
test('format_json: int', () => assert.equal(types.format_json(42), '42'));
test('format_json: float', () =>
  assert.equal(types.format_json(3.14), '3.140000'));
test('format_json: string escapes', () =>
  assert.equal(types.format_json('a"b\\c\nd'), '"a\\"b\\\\c\\nd"'));

// ─────────────────────────────────────────────
// stringify
// ─────────────────────────────────────────────
test('stringify: null', () =>
  assert.equal(types.box(null).stringify(null), 'null'));
test('stringify: bool', () => {
  assert.equal(types.box(true).stringify(null), 'true');
  assert.equal(types.box(false).stringify(null), 'false');
});
test('stringify: int', () => assert.equal(types.box(42).stringify(null), '42'));
test('stringify: float', () =>
  assert.equal(types.box(3.14).stringify(null), '3.140000'));
test('stringify: string', () =>
  assert.equal(types.box('hi').stringify(null), '"hi"'));
test('stringify: array inline', () =>
  assert.equal(types.box([1, 2, 3]).stringify(null), '[1, 2, 3]'));
test('stringify: object inline', () =>
  assert.equal(
    types.box({ a: 1, b: 2 }).stringify(null),
    '{"a": 1, "b": 2}',
  ));

// ─────────────────────────────────────────────
// compare
// ─────────────────────────────────────────────
test('compare: numbers', () => {
  assert.equal(types.compare(types.box(1), types.box(2)), -1);
  assert.equal(types.compare(types.box(2), types.box(1)), 1);
  assert.equal(types.compare(types.box(1), types.box(1)), 0);
});

test('compare: strings', () => {
  assert.equal(types.compare(types.box('a'), types.box('b')), -1);
  assert.equal(types.compare(types.box('b'), types.box('a')), 1);
});

// ─────────────────────────────────────────────
// arrayview_s (コード生成用)
// ─────────────────────────────────────────────
test('arrayview_s: int', () => {
  assert.equal(types.arrayview_s(5), '[1,0,1]');
  assert.equal(types.arrayview_s(-5), '-[1,0,1]');
  assert.equal(types.arrayview_s(0), '[]');
});

test('arrayview_s: bool', () => {
  assert.equal(types.arrayview_s(true), '[1]');
  assert.equal(types.arrayview_s(false), '[0]');
});

test('arrayview_s: float', () => {
  assert.equal(types.arrayview_s(3.14), '[0,0,0,0,4,1,3]');
});
