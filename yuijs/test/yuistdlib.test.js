// yuistdlib.js の単体テスト (Python 版 yuichan/test_stdlib.py を部分移植)
// node --test test/yuistdlib.test.js
//
// Python 側は runtime 経由で FuncAppNode を評価するが、JS 側はまだ runtime が
// ないので、stdlib 関数を直接 `fn(...args)` で呼び出してテストする。
// 引数は runtime が渡すのと同じく YuiValue でラップする。

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  YuiValue,
  YuiError,
  types,
  FloatType,
} from '../src/yuitypes.js';
import { standardLib } from '../src/yuistdlib.js';

// ─────────────────────────────────────────────
// stdlib を読み込み、名前 → 関数のルックアップを作る
// ─────────────────────────────────────────────
function loadStdlib() {
  const modules = [];
  const [targets] = standardLib(modules);
  const fnByName = {};
  for (const [namesStr, fn] of modules) {
    for (const name of namesStr.split('|')) {
      fnByName[name] = fn;
    }
  }
  return { targets, modules, fnByName };
}

const { targets, modules, fnByName } = loadStdlib();

// 引数を YuiValue でラップするヘルパ。float を明示したいときは [x, 'float']。
function box(v) {
  if (v instanceof YuiValue) return v;
  if (Array.isArray(v) && v.length === 2 && v[1] === 'float') {
    return new YuiValue(v[0], FloatType);
  }
  return new YuiValue(v);
}

/** fnByName[name](args...) を呼び、unbox した結果を返す */
function call(name, ...rawArgs) {
  const fn = fnByName[name];
  if (!fn) throw new Error(`stdlib function not found: ${name}`);
  const result = fn(...rawArgs.map(box));
  return types.unbox(result);
}

/** 呼び出しがメッセージ配列の先頭に expectedKey を含む YuiError を投げることを検証 */
function callThrows(name, rawArgs, expectedKey) {
  const fn = fnByName[name];
  assert.ok(fn, `stdlib function not found: ${name}`);
  assert.throws(
    () => fn(...rawArgs.map(box)),
    (e) => {
      if (!(e instanceof YuiError)) return false;
      return e.messages[0] === expectedKey;
    },
    `${name}(${rawArgs.map((a) => JSON.stringify(a)).join(',')}) should throw ${expectedKey}`,
  );
}

// ─────────────────────────────────────────────
// registration: targets / 関数の登録確認
// ─────────────────────────────────────────────

test('standardLib: targets は "emoji|ja|en"', () => {
  assert.equal(targets, 'emoji|ja|en');
});

test('standardLib: 全ての module 名は 3 つの variant を持つ', () => {
  for (const [namesStr] of modules) {
    const parts = namesStr.split('|');
    assert.equal(parts.length, 3, `${namesStr} has ${parts.length} variants`);
  }
});

test('standardLib: 期待される関数がすべて登録されている', () => {
  const expected = [
    // emoji variant
    '📏', '√', '🎲', '🧮', '⛓️‍💥', '💰', '✂️', '🍕', '👑', '🐜',
    // ja variant
    '絶対値', '平方根', '乱数', '和', '差', '積', '商', '剰余', '最大値', '最小値',
    'ブール判定', '整数判定', '小数判定', '文字列判定', '配列判定', 'オブジェクト判定',
    '整数化', '小数化', '文字列化', '配列化',
    // en variant
    'abs', 'sqrt', 'random', 'sum', 'diff', 'product', 'quotient', 'remainder',
    'max', 'min',
    'isbool', 'isint', 'isfloat', 'isstring', 'isarray', 'isobject',
    'toint', 'tofloat', 'tostring', 'toarray',
  ];
  for (const name of expected) {
    assert.ok(fnByName[name], `missing: ${name}`);
  }
});

// ─────────────────────────────────────────────
// abs / sqrt / random
// ─────────────────────────────────────────────

test('abs(5)', () => assert.equal(call('abs', 5), 5));
test('abs(-3)', () => assert.equal(call('abs', -3), 3));
test('abs(0)', () => assert.equal(call('abs', 0), 0));
test('abs(1.5)', () => assert.equal(call('abs', 1.5), 1.5));
test('abs(-2.5)', () => assert.equal(call('abs', -2.5), 2.5));
test('abs() → mismatch-argument', () => callThrows('abs', [], 'mismatch-argument'));
test('abs(1,2) → mismatch-argument', () => callThrows('abs', [1, 2], 'mismatch-argument'));
test('abs("hello") → type-error', () => callThrows('abs', ['hello'], 'type-error'));

test('sqrt(4)', () => assert.equal(call('sqrt', 4), 2));
test('sqrt(9)', () => assert.equal(call('sqrt', 9), 3));
test('sqrt(0)', () => assert.equal(call('sqrt', 0), 0));
test('sqrt(2)', () => assert.ok(Math.abs(call('sqrt', 2) - Math.sqrt(2)) < 1e-12));
test('sqrt(-1) → not-negative-number', () =>
  callThrows('sqrt', [-1], 'not-negative-number'));
test('sqrt() → mismatch-argument', () => callThrows('sqrt', [], 'mismatch-argument'));
test('sqrt("hello") → type-error', () => callThrows('sqrt', ['hello'], 'type-error'));

test('random() returns a number in [0,1)', () => {
  const v = call('random');
  assert.equal(typeof v, 'number');
  assert.ok(v >= 0 && v < 1);
});
test('random(1) → mismatch-argument', () => callThrows('random', [1], 'mismatch-argument'));

// ─────────────────────────────────────────────
// sum / diff / product / quotient / remainder
// ─────────────────────────────────────────────

test('sum(1,2)', () => assert.equal(call('sum', 1, 2), 3));
test('sum(1,2,3)', () => assert.equal(call('sum', 1, 2, 3), 6));
test('sum(1,2,3,4)', () => assert.equal(call('sum', 1, 2, 3, 4), 10));
test('sum(-1,2)', () => assert.equal(call('sum', -1, 2), 1));
test('sum(1.5,2.5)', () => assert.equal(call('sum', 1.5, 2.5), 4));
test('sum(1,2.5)', () => assert.equal(call('sum', 1, 2.5), 3.5));
test('sum(2.5,1)', () => assert.equal(call('sum', 2.5, 1), 3.5));
test('sum(3,-1)', () => assert.equal(call('sum', 3, -1), 2));
test('sum([1,2,3])', () => assert.equal(call('sum', [1, 2, 3]), 6));
test('sum() → mismatch-argument', () => callThrows('sum', [], 'mismatch-argument'));

test('diff(10,3)', () => assert.equal(call('diff', 10, 3), 7));
test('diff(10,3,2)', () => assert.equal(call('diff', 10, 3, 2), 5));
test('diff(3,10)', () => assert.equal(call('diff', 3, 10), -7));
test('diff(5.0,2.0)', () => assert.equal(call('diff', [5.0, 'float'], [2.0, 'float']), 3));
test('diff(5,2.5)', () => assert.equal(call('diff', 5, 2.5), 2.5));

test('product(3,4)', () => assert.equal(call('product', 3, 4), 12));
test('product(2,3,4)', () => assert.equal(call('product', 2, 3, 4), 24));
test('product(2,3,4,5)', () => assert.equal(call('product', 2, 3, 4, 5), 120));
test('product(5,0)', () => assert.equal(call('product', 5, 0), 0));
test('product(2,3.0) float', () =>
  assert.equal(call('product', 2, [3.0, 'float']), 6));
test('product([1,2,3])', () => assert.equal(call('product', [1, 2, 3]), 6));

test('quotient(10,3)', () => assert.equal(call('quotient', 10, 3), 3));
test('quotient(10,2)', () => assert.equal(call('quotient', 10, 2), 5));
test('quotient(100,5,2)', () => assert.equal(call('quotient', 100, 5, 2), 10));
test('quotient(10,4.0)', () => assert.equal(call('quotient', 10, [4.0, 'float']), 2.5));
test('quotient(10,0) → division-by-zero', () =>
  callThrows('quotient', [10, 0], 'division-by-zero'));

test('remainder(10,3)', () => assert.equal(call('remainder', 10, 3), 1));
test('remainder(9,3)', () => assert.equal(call('remainder', 9, 3), 0));
test('remainder(100,7,3)', () => assert.equal(call('remainder', 100, 7, 3), 2));
test('remainder(5.5,2.0)', () =>
  assert.equal(call('remainder', [5.5, 'float'], [2.0, 'float']), 1.5));
test('remainder(10,3.0)', () => assert.equal(call('remainder', 10, [3.0, 'float']), 1));
test('remainder(10,0) → division-by-zero', () =>
  callThrows('remainder', [10, 0], 'division-by-zero'));

// ─────────────────────────────────────────────
// max / min
// ─────────────────────────────────────────────

test('max(3,1,4,1,5)', () => assert.equal(call('max', 3, 1, 4, 1, 5), 5));
test('max(-3,-1)', () => assert.equal(call('max', -3, -1), -1));
test('max(1.5,2.5)', () => assert.equal(call('max', 1.5, 2.5), 2.5));
test('max(1,3.0,2)', () => assert.equal(call('max', 1, [3.0, 'float'], 2), 3));
test('max([1,2,3])', () => assert.equal(call('max', [1, 2, 3]), 3));
test('max() → mismatch-argument', () => callThrows('max', [], 'mismatch-argument'));

test('min(3,1,4)', () => assert.equal(call('min', 3, 1, 4), 1));
test('min(-3,-1)', () => assert.equal(call('min', -3, -1), -3));
test('min(1.5,0.5)', () => assert.equal(call('min', 1.5, 0.5), 0.5));
test('min(1.5,2,0.5)', () => assert.equal(call('min', 1.5, 2, 0.5), 0.5));
test('min([1,2,3])', () => assert.equal(call('min', [1, 2, 3]), 1));
test('min() → mismatch-argument', () => callThrows('min', [], 'mismatch-argument'));

// ─────────────────────────────────────────────
// 型判定関数
// ─────────────────────────────────────────────

test('isbool', () => {
  assert.equal(call('isbool', null), false);
  assert.equal(call('isbool', true), true);
  assert.equal(call('isbool', false), true);
  assert.equal(call('isbool', 0), false);
  assert.equal(call('isbool', 'hello'), false);
  assert.equal(call('isbool', [1, 2, 3]), false);
  assert.equal(call('isbool', { x: 1 }), false);
});

test('isint', () => {
  assert.equal(call('isint', null), false);
  assert.equal(call('isint', true), false);
  assert.equal(call('isint', 42), true);
  assert.equal(call('isint', [1.0, 'float']), false);
  assert.equal(call('isint', 'hello'), false);
  assert.equal(call('isint', [1, 2, 3]), false);
});

test('isfloat', () => {
  assert.equal(call('isfloat', null), false);
  assert.equal(call('isfloat', 3.14), true);
  assert.equal(call('isfloat', 3), false);
  assert.equal(call('isfloat', '3.14'), false);
  assert.equal(call('isfloat', { x: 1 }), false);
});

test('isstring', () => {
  assert.equal(call('isstring', null), false);
  assert.equal(call('isstring', true), false);
  assert.equal(call('isstring', 'hello'), true);
  assert.equal(call('isstring', 42), false);
  assert.equal(call('isstring', [1, 2, 3]), false);
});

test('isarray', () => {
  assert.equal(call('isarray', null), false);
  assert.equal(call('isarray', true), false);
  assert.equal(call('isarray', 42), false);
  assert.equal(call('isarray', 'hello'), false);
  assert.equal(call('isarray', [1, 2, 3]), true);
  assert.equal(call('isarray', { x: 1 }), false);
});

test('isobject', () => {
  assert.equal(call('isobject', null), false);
  assert.equal(call('isobject', true), false);
  assert.equal(call('isobject', 42), false);
  assert.equal(call('isobject', 'hello'), false);
  assert.equal(call('isobject', [1, 2, 3]), false);
  assert.equal(call('isobject', { x: 1, y: 2 }), true);
});

// ─────────────────────────────────────────────
// 型変換関数
// ─────────────────────────────────────────────

test('toint', () => {
  assert.equal(call('toint', null), 0);
  assert.equal(call('toint', true), 1);
  assert.equal(call('toint', false), 0);
  assert.equal(call('toint', 5), 5);
  assert.equal(call('toint', 3.9), 3);
  assert.equal(call('toint', -3.9), -3);
  assert.equal(call('toint', '42'), 42);
  assert.equal(call('toint', '-3.9'), -3);
});

test('toint([1,0,1])', () => assert.equal(call('toint', [1, 0, 1]), 5));
test('toint("hello") → int-conversion', () =>
  callThrows('toint', ['hello'], 'int-conversion'));
test('toint([1,2,3]) → int-conversion', () =>
  callThrows('toint', [[1, 2, 3]], 'int-conversion'));
test('toint(object) → int-conversion', () =>
  callThrows('toint', [{ x: 1 }], 'int-conversion'));

test('tofloat', () => {
  assert.equal(call('tofloat', null), 0);
  assert.equal(call('tofloat', true), 1);
  assert.equal(call('tofloat', false), 0);
  assert.equal(call('tofloat', 3), 3);
  assert.equal(call('tofloat', 3.14), 3.14);
  assert.equal(call('tofloat', '2.5'), 2.5);
  assert.equal(call('tofloat', '-3.9'), -3.9);
});

test('tofloat([1,2,3]) — floatfloat digit decoding', () => {
  // FloatType.to_native([1,2,3]) = 0.000321
  const v = call('tofloat', [1, 2, 3]);
  assert.ok(Math.abs(v - 0.000321) < 1e-12);
});
test('tofloat([0,0,0,0,4,1,3])', () => {
  const v = call('tofloat', [0, 0, 0, 0, 4, 1, 3]);
  assert.ok(Math.abs(v - 3.14) < 1e-12);
});
test('tofloat("hello") → float-conversion', () =>
  callThrows('tofloat', ['hello'], 'float-conversion'));
test('tofloat(object) → float-conversion', () =>
  callThrows('tofloat', [{ x: 1 }], 'float-conversion'));

test('tostring', () => {
  assert.equal(call('tostring', null), 'null');
  assert.equal(call('tostring', true), 'true');
  assert.equal(call('tostring', false), 'false');
  assert.equal(call('tostring', 42), '42');
  assert.equal(call('tostring', 3.14), '3.140000');
  assert.equal(call('tostring', 0.0000011), '0.000001');
  assert.equal(call('tostring', -5), '-5');
  assert.equal(call('tostring', 'hello'), 'hello');
  assert.equal(call('tostring', [1, 2, 3]), '[1, 2, 3]');
});

test('toarray', () => {
  assert.deepEqual(call('toarray', null), []);
  assert.deepEqual(call('toarray', true), [1]);
  assert.deepEqual(call('toarray', false), [0]);
  assert.deepEqual(call('toarray', 5), [1, 0, 1]);
  assert.deepEqual(call('toarray', 3.14), [0, 0, 0, 0, 4, 1, 3]);
  assert.deepEqual(call('toarray', 'ABC'), [65, 66, 67]);
  assert.deepEqual(call('toarray', [1, 2, 3]), [1, 2, 3]);
  assert.deepEqual(call('toarray', { x: 1, y: 2, z: 3 }), ['x', 'y', 'z']);
});
