// yuiruntime.js の単体テスト (Python 版 yuichan/test_runtime.py の移植)
// node --test test/yuiruntime.test.js

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  YuiRuntime,
  LocalFunction,
  NativeFunction,
  YuiFunction,
  YuiBreakException,
  YuiReturnException,
} from '../src/yuiruntime.js';
import {
  YuiValue,
  types,
  YuiError,
} from '../src/yuitypes.js';

const STDLIB = '標準ライブラリを使う\n';

function run(source, syntax = 'yui') {
  const rt = new YuiRuntime();
  rt.exec(source, syntax, { evalMode: false });
  return rt.getTopEnv();
}

function runStd(source, syntax = 'yui') {
  return run(STDLIB + source, syntax);
}

function val(env, name) {
  return types.unbox(env.get(name));
}

function runRt(source, syntax = 'yui') {
  const rt = new YuiRuntime();
  rt.exec(STDLIB + source, syntax, { evalMode: false });
  return rt;
}

function runBin(source) {
  const rt = new YuiRuntime();
  rt.allow_binary_ops = true;
  rt.exec(source, 'yui', { evalMode: false });
  return rt.getTopEnv();
}

// ─────────────────────────────────────────────
// NativeFunction の戻り値ラップ
// ─────────────────────────────────────────────

test('和() の結果が YuiValue として格納される', () => {
  const env = runStd('x = 和(3, 4)');
  assert.ok(env.get('x') instanceof YuiValue);
  assert.equal(val(env, 'x'), 7);
});

test('積() の結果', () => {
  const env = runStd('x = 積(3, 4)');
  assert.equal(val(env, 'x'), 12);
});

test('差() の結果', () => {
  const env = runStd('x = 差(10, 3)');
  assert.equal(val(env, 'x'), 7);
});

test('商() の結果 (floor division)', () => {
  const env = runStd('x = 商(10, 3)');
  assert.equal(val(env, 'x'), 3);
});

test('剰余() の結果', () => {
  const env = runStd('x = 剰余(10, 3)');
  assert.equal(val(env, 'x'), 1);
});

test('最大値() の結果', () => {
  const env = runStd('x = 最大値(3, 7, 2)');
  assert.equal(val(env, 'x'), 7);
});

test('最小値() の結果', () => {
  const env = runStd('x = 最小値(3, 7, 2)');
  assert.equal(val(env, 'x'), 2);
});

test('整数判定() の結果 (JS は bool を返す)', () => {
  // Python 版は bool が int のサブクラスなので `== 1` が成立するが、
  // JS 版では真偽値 true を返すだけ。意味的には等価。
  const env = runStd('x = 整数判定(42)');
  assert.equal(val(env, 'x'), true);
});

test('整数化() の結果', () => {
  const env = runStd('x = 整数化(3.9)');
  assert.equal(val(env, 'x'), 3);
});

test('平方根() の結果は float', () => {
  const env = runStd('x = 平方根(4)');
  assert.ok(types.is_float(env.get('x')));
  assert.ok(Math.abs(val(env, 'x') - 2.0) < 1e-6);
});

test('乱数() の結果は [0, 1] の float', () => {
  const env = runStd('x = 乱数()');
  assert.ok(types.is_float(env.get('x')));
  const v = val(env, 'x');
  assert.ok(v >= 0.0 && v <= 1.0);
});

// ─────────────────────────────────────────────
// Assert (>>>) と NativeFunction の統合
// ─────────────────────────────────────────────

test('和() を直接アサートできる', () => {
  const rt = runRt('>>> 和(3, 4)\n7');
  assert.ok(rt.test_passed.length > 0);
});

test('積() を直接アサートできる', () => {
  const rt = runRt('>>> 積(3, 4)\n12');
  assert.ok(rt.test_passed.length > 0);
});

test('Native 関数の結果を変数経由でアサートできる', () => {
  const rt = runRt('x = 和(3, 4)\n>>> x\n7');
  assert.ok(rt.test_passed.length > 0);
});

test('ネストしたネイティブ呼び出しをアサートできる', () => {
  const rt = runRt('x = 和(積(2, 5), 3)\n>>> x\n13');
  assert.ok(rt.test_passed.length > 0);
});

test('ネイティブ関数を使うユーザ定義関数をアサートできる', () => {
  const code =
    'ten_times = 入力 n に対して {\n' +
    '  積(n, 10) が答え\n' +
    '}\n' +
    '>>> ten_times(5)\n' +
    '50\n';
  const rt = runRt(code);
  assert.ok(rt.test_passed.length > 0);
});

test('ループ内でネイティブ関数を使うユーザ定義関数をアサートできる', () => {
  const code =
    'accumulate = 入力 n に対して {\n' +
    '  result = 0\n' +
    '  n回くり返す {\n' +
    '    result = 和(result, 1)\n' +
    '  }\n' +
    '  result が答え\n' +
    '}\n' +
    '>>> accumulate(5)\n' +
    '5\n';
  const rt = runRt(code);
  assert.ok(rt.test_passed.length > 0);
});

test('アサート失敗は YuiError を投げる', () => {
  assert.throws(
    () => runRt('>>> 和(3, 4)\n99'),
    (err) => err instanceof YuiError && err.messages[0] === 'assertion-failed',
  );
});

// ─────────────────────────────────────────────
// 基本実行
// ─────────────────────────────────────────────

test('assignment (int)', () => {
  assert.equal(val(run('x = 42'), 'x'), 42);
});

test('assignment (string)', () => {
  assert.equal(val(run('s = "hello"'), 's'), 'hello');
});

test('increment', () => {
  assert.equal(val(run('x = 0\nxを増やす'), 'x'), 1);
});

test('decrement', () => {
  assert.equal(val(run('x = 5\nxを減らす'), 'x'), 4);
});

test('arithmetic add via stdlib', () => {
  assert.equal(val(runStd('x = 和(3, 4)'), 'x'), 7);
});

test('arithmetic mul via stdlib', () => {
  assert.equal(val(runStd('x = 積(3, 4)'), 'x'), 12);
});

test('repeat loop', () => {
  assert.equal(val(run('x = 0\n3回くり返す {\n  xを増やす\n}'), 'x'), 3);
});

test('if true branch', () => {
  const env = run('x = 10\nもし x が 10 ならば {\n  x = 99\n}');
  assert.equal(val(env, 'x'), 99);
});

test('if false branch (no change)', () => {
  const env = run('x = 5\nもし x が 10 ならば {\n  x = 99\n}');
  assert.equal(val(env, 'x'), 5);
});

test('user-defined function', () => {
  const code =
    STDLIB +
    'add = 入力 a, b に対して {\n' +
    '  和(a, b) が答え\n' +
    '}\n' +
    'result = add(3, 4)';
  assert.equal(val(run(code), 'result'), 7);
});

test('array literal', () => {
  const env = run('a = [1, 2, 3]');
  assert.deepEqual(val(env, 'a'), [1, 2, 3]);
});

test('array append', () => {
  const env = run('a = [1, 2]\naに3を追加する');
  assert.deepEqual(val(env, 'a'), [1, 2, 3]);
});

test('multiple exec calls share env', () => {
  const rt = new YuiRuntime();
  rt.exec('x = 10', 'yui', { evalMode: false });
  rt.exec('y = x\nyを増やす\nyを増やす\nyを増やす\nyを増やす\nyを増やす', 'yui', { evalMode: false });
  assert.equal(
    types.unbox(rt.getTopEnv().get('y')),
    15,
  );
});

test('syntax error raises YuiError', () => {
  assert.throws(
    () => run('もし もし もし'),
    (err) => err instanceof YuiError,
  );
});

// ─────────────────────────────────────────────
// 二項演算子 (allow_binary_ops=true)
// ─────────────────────────────────────────────

test('binary ops disabled by default', () => {
  assert.throws(
    () => run('x = 1 + 2'),
    (err) => err instanceof YuiError && err.messages[0] === 'unsupported-operator',
  );
});

test('int + int', () => {
  assert.equal(val(runBin('x = 1 + 2'), 'x'), 3);
});

test('int - int', () => {
  assert.equal(val(runBin('x = 10 - 3'), 'x'), 7);
});

test('int * int', () => {
  assert.equal(val(runBin('x = 3 * 4'), 'x'), 12);
});

test('int / int (floor)', () => {
  assert.equal(val(runBin('x = 10 / 3'), 'x'), 3);
});

test('int % int', () => {
  assert.equal(val(runBin('x = 10 % 3'), 'x'), 1);
});

test('float + float', () => {
  assert.ok(Math.abs(val(runBin('x = 1.5 + 2.5'), 'x') - 4.0) < 1e-6);
});

test('float / int', () => {
  assert.ok(Math.abs(val(runBin('x = 10.0 / 4'), 'x') - 2.5) < 1e-6);
});

test('float % float', () => {
  assert.ok(Math.abs(val(runBin('x = 5.5 % 2.0'), 'x') - 1.5) < 1e-6);
});

test('int + float promotes to float', () => {
  const env = runBin('x = 1 + 2.0');
  assert.ok(types.is_float(env.get('x')));
  assert.ok(Math.abs(val(env, 'x') - 3.0) < 1e-6);
});

test('int - float promotes to float', () => {
  const env = runBin('x = 5 - 1.5');
  assert.ok(types.is_float(env.get('x')));
  assert.ok(Math.abs(val(env, 'x') - 3.5) < 1e-6);
});

test('int * float promotes to float', () => {
  const env = runBin('x = 3 * 2.0');
  assert.ok(types.is_float(env.get('x')));
  assert.ok(Math.abs(val(env, 'x') - 6.0) < 1e-6);
});

test('int / float promotes to float', () => {
  const env = runBin('x = 7 / 2.0');
  assert.ok(types.is_float(env.get('x')));
  assert.ok(Math.abs(val(env, 'x') - 3.5) < 1e-6);
});

test('string concat', () => {
  assert.equal(val(runBin('x = "hello" + " world"'), 'x'), 'hello world');
});

test('string concat with empty', () => {
  assert.equal(val(runBin('x = "" + "abc"'), 'x'), 'abc');
});

test('array concat', () => {
  assert.deepEqual(val(runBin('x = [1, 2] + [3, 4]'), 'x'), [1, 2, 3, 4]);
});

test('array concat with empty', () => {
  assert.deepEqual(val(runBin('x = [] + [1, 2]'), 'x'), [1, 2]);
});

test('divide by zero raises YuiError', () => {
  assert.throws(
    () => runBin('x = 5 / 0'),
    (err) => err instanceof YuiError && err.messages[0] === 'division-by-zero',
  );
});

test('modulo by zero raises YuiError', () => {
  assert.throws(
    () => runBin('x = 5 % 0'),
    (err) => err instanceof YuiError && err.messages[0] === 'division-by-zero',
  );
});

// ─────────────────────────────────────────────
// 制御フロー: return, break, recursion
// ─────────────────────────────────────────────

test('recursive factorial', () => {
  const rt = new YuiRuntime();
  rt.exec(
    STDLIB +
      'fact = 入力 n に対して {\n' +
      '  もし n が 0 ならば { 1 が答え }\n' +
      '  積(n, fact(差(n, 1))) が答え\n' +
      '}\n' +
      'result = fact(5)',
    'yui',
    { evalMode: false },
  );
  const env = rt.getTopEnv();
  assert.equal(val(env, 'result'), 120);
});

test('infinite recursion raises too-many-recursion', () => {
  assert.throws(
    () => {
      const rt = new YuiRuntime();
      rt.exec(
        'f = 入力 n に対して {\n  f(n) が答え\n}\nf(0)',
        'yui',
        { evalMode: false },
      );
    },
    (err) => err instanceof YuiError && err.messages[0] === 'too-many-recursion',
  );
});

test('break exits repeat loop', () => {
  const env = run(
    'x = 0\n' +
      '10回くり返す {\n' +
      '  xを増やす\n' +
      '  もし x が 3 ならば { くり返しを抜ける }\n' +
      '}',
  );
  assert.equal(val(env, 'x'), 3);
});

test('undefined variable raises YuiError', () => {
  assert.throws(
    () => run('x = y'),
    (err) => err instanceof YuiError && err.messages[0] === 'undefined-variable',
  );
});

test('undefined function raises YuiError', () => {
  assert.throws(
    () => run('x = unknown_fn(1)'),
    (err) => err instanceof YuiError && err.messages[0] === 'undefined-function',
  );
});

// ─────────────────────────────────────────────
// Runtime API
// ─────────────────────────────────────────────

test('resetStats zeros all counters', () => {
  const rt = new YuiRuntime();
  rt.exec('x = 0\nxを増やす\nxを増やす\nxを減らす', 'yui', { evalMode: false });
  assert.equal(rt.increment_count, 2);
  assert.equal(rt.decrement_count, 1);
  rt.resetStats();
  assert.equal(rt.increment_count, 0);
  assert.equal(rt.decrement_count, 0);
  assert.equal(rt.compare_count, 0);
});

test('exec with evalMode=true returns unboxed value', () => {
  const rt = new YuiRuntime();
  const result = rt.exec('42', 'yui'); // default evalMode=true
  // Top-level expression value is null for no-print statements; but with
  // '42' alone the parser will wrap as PrintExpressionNode at top level.
  // Runtime returns top-level block value. '42' prints but result is returned.
  assert.ok(result === 42 || result === null);
});

test('exec with evalMode=false returns env snapshot', () => {
  const rt = new YuiRuntime();
  const env = rt.exec('x = 42', 'yui', { evalMode: false });
  assert.equal(types.unbox(env.get('x')), 42);
});

test('loadStdlib populates stdlib functions', () => {
  const rt = new YuiRuntime();
  rt.loadStdlib();
  // stdlib 関数はキー '@名前' で環境に登録される
  assert.ok(rt.hasenv('@和'));
  assert.ok(rt.hasenv('@積'));
});

test('LocalFunction is a YuiFunction', () => {
  const fn = new LocalFunction('foo', ['a', 'b'], null);
  assert.ok(fn instanceof YuiFunction);
  assert.equal(fn.name, 'foo');
  assert.deepEqual(fn.parameters, ['a', 'b']);
});

test('NativeFunction wraps a plain JS function and returns YuiValue', () => {
  const fn = new NativeFunction(function add(a, b) {
    return new YuiValue(types.unbox(a) + types.unbox(b));
  });
  assert.ok(fn instanceof YuiFunction);
  assert.equal(fn.name, 'add');
  const rt = new YuiRuntime();
  const result = fn.call([new YuiValue(3), new YuiValue(4)], null, rt);
  assert.ok(result instanceof YuiValue);
  assert.equal(types.unbox(result), 7);
});

test('NativeFunction wraps non-YuiValue results', () => {
  const fn = new NativeFunction(function raw() {
    return 42;
  });
  const rt = new YuiRuntime();
  const result = fn.call([], null, rt);
  assert.ok(result instanceof YuiValue);
  assert.equal(types.unbox(result), 42);
});

test('NativeFunction converts JS exceptions to internal-error', () => {
  const fn = new NativeFunction(function bad() {
    throw new Error('boom');
  });
  const rt = new YuiRuntime();
  assert.throws(
    () => fn.call([], null, rt),
    (err) => err instanceof YuiError && err.messages[0] === 'internal-error',
  );
});

test('YuiBreakException is a YuiError', () => {
  const e = new YuiBreakException(null);
  assert.ok(e instanceof YuiError);
  assert.equal(e.messages[0], 'unexpected-break');
});

test('YuiReturnException carries value and is a YuiError', () => {
  const v = new YuiValue(42);
  const e = new YuiReturnException(v, null);
  assert.ok(e instanceof YuiError);
  assert.equal(e.messages[0], 'unexpected-return');
  assert.equal(e.value, v);
});

// ─────────────────────────────────────────────
// 環境操作
// ─────────────────────────────────────────────

test('hasenv / getenv / setenv walk scopes', () => {
  const rt = new YuiRuntime();
  rt.setenv('x', new YuiValue(1));
  rt.pushenv();
  rt.setenv('y', new YuiValue(2));
  assert.ok(rt.hasenv('x'));
  assert.ok(rt.hasenv('y'));
  assert.equal(types.unbox(rt.getenv('x')), 1);
  assert.equal(types.unbox(rt.getenv('y')), 2);
  rt.popenv();
  assert.ok(rt.hasenv('x'));
  assert.ok(!rt.hasenv('y'));
});

test('isInTheTopLevel reflects call frame depth', () => {
  const rt = new YuiRuntime();
  assert.equal(rt.isInTheTopLevel(), true);
  rt.pushCallFrame('foo', [], null);
  assert.equal(rt.isInTheTopLevel(), false);
  rt.popCallFrame();
  assert.equal(rt.isInTheTopLevel(), true);
});
