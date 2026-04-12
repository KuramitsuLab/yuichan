// yuicoding.js の単体テスト (Python 版 yuichan/test_coding.py を移植)
// node --test test/yuicoding.test.js

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  ConstNode,
  NumberNode,
  StringNode,
  ArrayNode,
  ObjectNode,
  NameNode,
  BinaryNode,
  MinusNode,
  ArrayLenNode,
  GetIndexNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  BreakNode,
  ReturnNode,
  PrintExpressionNode,
} from '../src/yuiast.js';
import { CodingVisitor } from '../src/yuicoding.js';
import { loadSyntax } from '../src/yuisyntax.js';

const yuiSyntax = loadSyntax('yui');

function emit(node) {
  const coder = new CodingVisitor(yuiSyntax);
  return coder.emit(node);
}

// ─────────────────────────────────────────────
// ConstNode
// ─────────────────────────────────────────────

test('null → 値なし', () => assert.equal(emit(new ConstNode(null)), '値なし'));
test('true → 真', () => assert.equal(emit(new ConstNode(true)), '真'));
test('false → 偽', () => assert.equal(emit(new ConstNode(false)), '偽'));

// ─────────────────────────────────────────────
// NumberNode
// ─────────────────────────────────────────────

test('123 → "123"', () => assert.equal(emit(new NumberNode(123)), '123'));
test('0 → "0"', () => assert.equal(emit(new NumberNode(0)), '0'));
test('3.14 → "3.140000"', () => assert.equal(emit(new NumberNode(3.14)), '3.140000'));

// ─────────────────────────────────────────────
// StringNode
// ─────────────────────────────────────────────

test('"hello" → "\\"hello\\""', () =>
  assert.equal(emit(new StringNode('hello')), '"hello"'));

test('"" → "\\"\\""', () => assert.equal(emit(new StringNode('')), '""'));

// ─────────────────────────────────────────────
// ArrayNode / ObjectNode
// ─────────────────────────────────────────────

test('[1,2,3]', () => {
  assert.equal(
    emit(new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)])),
    '[1,2,3]',
  );
});

test('[] → "[]"', () => assert.equal(emit(new ArrayNode([])), '[]'));

test('{"a":1,"b":"two"}', () => {
  const node = new ObjectNode([
    new StringNode('a'),
    new NumberNode(1),
    new StringNode('b'),
    new StringNode('two'),
  ]);
  assert.equal(emit(node), '{"a":1,"b":"two"}');
});

// ─────────────────────────────────────────────
// MinusNode / ArrayLenNode / GetIndexNode
// ─────────────────────────────────────────────

test('-5', () => assert.equal(emit(new MinusNode(new NumberNode(5))), '-5'));

test('|arr| → arrの大きさ', () => {
  assert.equal(emit(new ArrayLenNode(new NameNode('arr'))), 'arrの大きさ');
});

test('arr[2]', () => {
  assert.equal(
    emit(new GetIndexNode(new NameNode('arr'), new NumberNode(2))),
    'arr[2]',
  );
});

// ─────────────────────────────────────────────
// PrintExpressionNode with inspection
// ─────────────────────────────────────────────

test('inspect(a) → 👀a', () => {
  assert.equal(
    emit(new PrintExpressionNode(new NameNode('a'), true)),
    '👀a',
  );
});

// ─────────────────────────────────────────────
// BinaryNode + 括弧制御
// ─────────────────────────────────────────────

test('1+2', () => assert.equal(emit(new BinaryNode('+', 1, 2)), '1+2'));
test('3*4', () => assert.equal(emit(new BinaryNode('*', 3, 4)), '3*4'));

test('1+2*3 (precedence — no grouping)', () => {
  assert.equal(
    emit(new BinaryNode('+', 1, new BinaryNode('*', 2, 3))),
    '1+2*3',
  );
});

test('(1+2)*3 (higher prec child → group)', () => {
  assert.equal(
    emit(new BinaryNode('*', new BinaryNode('+', 1, 2), 3)),
    '(1+2)*3',
  );
});

test('1-2-3 (left associative → no group)', () => {
  assert.equal(
    emit(new BinaryNode('-', new BinaryNode('-', 1, 2), 3)),
    '1-2-3',
  );
});

test('1-(2-3) (right child same prec → group)', () => {
  assert.equal(
    emit(new BinaryNode('-', 1, new BinaryNode('-', 2, 3))),
    '1-(2-3)',
  );
});

// ─────────────────────────────────────────────
// 代入 / 増減 / append / break / return
// ─────────────────────────────────────────────

test('x=10', () => {
  assert.equal(
    emit(new AssignmentNode(new NameNode('x'), new NumberNode(10))),
    'x=10',
  );
});

test('xを増やす', () => {
  assert.equal(emit(new IncrementNode(new NameNode('x'))), 'xを増やす');
});

test('xを減らす', () => {
  assert.equal(emit(new DecrementNode(new NameNode('x'))), 'xを減らす');
});

test('arrに10を追加する', () => {
  assert.equal(
    emit(new AppendNode(new NameNode('arr'), new NumberNode(10))),
    'arrに10を追加する',
  );
});

test('break → くり返しを抜ける', () => {
  assert.equal(emit(new BreakNode()), 'くり返しを抜ける');
});

test('return result → resultが答え', () => {
  assert.equal(
    emit(new ReturnNode(new NameNode('result'))),
    'resultが答え',
  );
});

// ─────────────────────────────────────────────
// PrintExpressionNode (expression statement)
// ─────────────────────────────────────────────

test('print "Hello, World!"', () => {
  assert.equal(
    emit(new PrintExpressionNode(new StringNode('Hello, World!'))),
    '"Hello, World!"',
  );
});

// ─────────────────────────────────────────────
// BlockNode (top_level)
// ─────────────────────────────────────────────

test('top-level block: x=1\\ny=2', () => {
  const node = new BlockNode(
    [
      new AssignmentNode(new NameNode('x'), new NumberNode(1)),
      new AssignmentNode(new NameNode('y'), new NumberNode(2)),
    ],
    true,
  );
  assert.equal(emit(node), 'x=1\ny=2');
});

// ─────────────────────────────────────────────
// CodingVisitor 自体の挙動
// ─────────────────────────────────────────────

test('CodingVisitor: 文字列引数で syntax をロードできる', () => {
  const coder = new CodingVisitor('yui');
  assert.equal(coder.emit(new ConstNode(null)), '値なし');
});

test('CodingVisitor: functionLanguage なしでは funcnamemap は空', () => {
  const coder = new CodingVisitor(yuiSyntax);
  assert.deepEqual(coder.funcnamemap, {});
});

test('CodingVisitor: functionLanguage="ja" で funcnamemap がロードされる', () => {
  const coder = new CodingVisitor(yuiSyntax, 'ja');
  // 絵文字/英語名のどちらからでも日本語にマップされるはず
  assert.equal(coder.funcnamemap['abs'], '絶対値');
  assert.equal(coder.funcnamemap['📏'], '絶対値');
  assert.equal(coder.funcnamemap['絶対値'], '絶対値');
  assert.equal(coder.funcnamemap['sum'], '和');
  assert.equal(coder.funcnamemap['max'], '最大値');
});

test('CodingVisitor: functionLanguage="emoji" で絵文字にマップ', () => {
  const coder = new CodingVisitor(yuiSyntax, 'emoji');
  assert.equal(coder.funcnamemap['abs'], '📏');
  assert.equal(coder.funcnamemap['絶対値'], '📏');
  assert.equal(coder.funcnamemap['sum'], '🧮');
});

test('CodingVisitor: functionLanguage="en" で英語にマップ', () => {
  const coder = new CodingVisitor(yuiSyntax, 'en');
  assert.equal(coder.funcnamemap['絶対値'], 'abs');
  assert.equal(coder.funcnamemap['📏'], 'abs');
});

test('CodingVisitor: 未知の functionLanguage はエラー', () => {
  assert.throws(
    () => new CodingVisitor(yuiSyntax, 'fr'),
    /not found in standard library targets/,
  );
});

test('CodingVisitor: lastChar は初期状態で改行', () => {
  const coder = new CodingVisitor(yuiSyntax);
  assert.equal(coder.lastChar(), '\n');
});

test('CodingVisitor: escape は \\, ", \\n をエスケープ', () => {
  const coder = new CodingVisitor(yuiSyntax);
  assert.equal(coder.escape('a\\b"c\nd'), 'a\\\\b\\"c\\nd');
});
