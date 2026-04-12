// yuiparser.js の単体テスト (Python 版 test_parser.py / test_parser_yui.py を移植)
// node --test test/yuiparser.test.js

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  Source,
  YuiParser,
  NONTERMINALS,
} from '../src/yuiparser.js';
import { loadSyntax } from '../src/yuisyntax.js';
import { YuiError } from '../src/yuierror.js';
import {
  ConstNode,
  NumberNode,
  StringNode,
  NameNode,
  ArrayNode,
  ObjectNode,
  BinaryNode,
  AssignmentNode,
  IfNode,
  RepeatNode,
  FuncDefNode,
  BlockNode,
  BreakNode,
  ReturnNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  FuncAppNode,
  GetIndexNode,
  ArrayLenNode,
} from '../src/yuiast.js';

const yuiSyntax = loadSyntax('yui');

// ─────────────────────────────────────────────
// Source のプリミティブ操作
// ─────────────────────────────────────────────

test('Source.isDefined reflects terminals', () => {
  const s = new Source('', { syntax: yuiSyntax });
  s.updateSyntax({
    'line-feed': '\\n',
    whitespace: ' ',
    whitespaces: '[ \\t\\r]+',
  });
  assert.equal(s.isDefined('linefeed'), true);
  assert.equal(s.isDefined('comment-begin'), false);
});

test('Source.is consumes whitespace terminal', () => {
  let s = new Source('X  abc', { pos: 1 });
  assert.equal(s.is('whitespaces', { lskipWs: false }), true);
  assert.equal(s.pos, 3);

  s = new Source('X  abc', { pos: 1 });
  assert.equal(s.is('whitespace', { lskipWs: false }), true);
  assert.equal(s.pos, 2);

  s = new Source('Xabc', { pos: 1 });
  assert.equal(s.is('whitespaces', { lskipWs: false }), false);
  assert.equal(s.pos, 1);

  assert.throws(
    () => {
      const s2 = new Source('Xabc', { pos: 1 });
      s2.require('whitespace', { lskipWs: false });
    },
    (err) => {
      assert.ok(err instanceof YuiError);
      assert.match(err.message, /expected/);
      assert.equal(err.errorNode.pos, 1);
      assert.equal(err.errorNode.end_pos, 2);
      return true;
    },
  );
});

test('Source.consumeUntil stops at linefeed', () => {
  const s = new Source('X    \nabc', { pos: 1 });
  assert.equal(s.consumeUntil('linefeed'), true);
  assert.equal(s.pos, 5);
  assert.equal(s.source[s.pos], '\n');
});

test('Source.captureIndent returns leading whitespace of line', () => {
  const s = new Source('X\n    x=1\nabc', { pos: 3 });
  s.consumeUntil('linefeed');
  assert.equal(s.captureIndent(), '    ');
});

test('Source.skipWhitespacesAndComments handles line comments and block comments', () => {
  let s = new Source('X=1  #hoge   \ny=1', { pos: 3 });
  s.skipWhitespacesAndComments();
  assert.equal(s.source[s.pos], '\n');

  s = new Source('X=1  #hoge   \ny=1', { pos: 3 });
  s.skipWhitespacesAndComments({ includeLinefeed: true });
  assert.equal(s.source[s.pos], 'y');

  s = new Source('X =  (*optional*) 1  #hoge   \ny=1', { pos: 3 });
  s.updateSyntax({
    'comment-begin': '\\(\\*',
    'comment-end': '\\*\\)',
  });
  s.skipWhitespacesAndComments({ includeLinefeed: true });
  assert.equal(s.source[s.pos], '1');
});

// ─────────────────────────────────────────────
// リテラル
// ─────────────────────────────────────────────

test('Number parser handles int and float', () => {
  let s = new Source('01234 #コメント', { pos: 1 });
  let node = s.parse('@Number');
  assert.ok(node instanceof NumberNode);
  assert.equal(String(node), '1234');
  assert.equal(node.native_value, 1234);

  s = new Source('0123.12 #コメント', { pos: 1 });
  node = s.parse('@Number');
  assert.equal(String(node), '123.12');
  assert.equal(node.native_value, 123.12);

  assert.throws(
    () => {
      const s2 = new Source('xxx');
      s2.parse('@Number', { BK: true });
    },
    (err) => {
      assert.ok(err instanceof YuiError);
      assert.match(err.message, /expected/);
      assert.equal(err.errorNode.pos, 0);
      assert.equal(err.errorNode.end_pos, 1);
      return true;
    },
  );
});

test('Number is also reachable via @Expression', () => {
  const s = new Source('01234 #コメント', { pos: 1 });
  const node = s.parse('@Expression');
  assert.equal(String(node), '1234');
});

test('String parser handles plain and interpolated strings', () => {
  let s = new Source('"ABC"');
  let node = s.parse('@String');
  assert.ok(node instanceof StringNode);
  assert.equal(String(node), '"ABC"');

  s = new Source('"AB{1}C"');
  node = s.parse('@String');
  assert.equal(String(node), '"AB{1}C"');
});

test('String as @Expression', () => {
  const s = new Source('"ABC"');
  const node = s.parse('@Expression');
  assert.equal(String(node), '"ABC"');
});

test('String with wrong quote raises YuiError', () => {
  assert.throws(
    () => new Source("'A'").parse('@Expression'),
    (err) => {
      assert.ok(err instanceof YuiError);
      assert.match(err.message, /wrong|typo/);
      return true;
    },
  );
});

test('Array parser handles inline and multiline arrays', () => {
  let s = new Source('[1,2]');
  let node = s.parse('@Array');
  assert.ok(node instanceof ArrayNode);
  assert.equal(String(node), '[1,2]');

  s = new Source('[\n1,\n2\n]');
  node = s.parse('@Array');
  assert.equal(String(node), '[\n1,\n2\n]');
});

test('Object parser', () => {
  const s = new Source('{"A": 1}');
  const node = s.parse('@Object');
  assert.ok(node instanceof ObjectNode);
  assert.equal(String(node), '{"A": 1}');
});

test('Name parser accepts underscored identifiers', () => {
  const s = new Source('x_1 = 1');
  const node = s.parse('@Name');
  assert.ok(node instanceof NameNode);
  assert.equal(String(node), 'x_1');
});

test('GetIndex parser', () => {
  const s = new Source('x[0]');
  const node = s.parse('@Expression');
  assert.ok(node instanceof GetIndexNode);
  assert.equal(String(node), 'x[0]');
});

test('ArrayLen parser via pipes', () => {
  const s = new Source('|a|');
  const node = s.parse('@Expression');
  assert.ok(node instanceof ArrayLenNode);
  assert.equal(String(node), '|a|');
});

test('FuncApp as @Primary / @Expression', () => {
  for (const nt of ['@Primary', '@Expression']) {
    let s = new Source('x(0)');
    let node = s.parse(nt);
    assert.ok(node instanceof FuncAppNode);
    assert.equal(String(node), 'x(0)');

    s = new Source('x()');
    node = s.parse(nt);
    assert.equal(String(node), 'x()');

    s = new Source('x(1, 2)');
    node = s.parse(nt);
    assert.equal(String(node), 'x(1, 2)');
  }
});

// ─────────────────────────────────────────────
// 二項演算子
// ─────────────────────────────────────────────

test('Binary operators', () => {
  for (const [src, op] of [
    ['1 + 2', '+'],
    ['1 - 2', '-'],
    ['3 * 4', '*'],
    ['3 / 4', '/'],
    ['5 % 2', '%'],
  ]) {
    const s = new Source(src);
    const node = s.parse('@Expression');
    assert.ok(node instanceof BinaryNode);
    assert.equal(String(node), src);
    assert.equal(String(node.operator), op);
  }
});

test('Operator precedence: 1 + 2 * 3 groups multiplication first', () => {
  const s = new Source('1 + 2 * 3');
  const node = s.parse('@Expression');
  assert.ok(node instanceof BinaryNode);
  assert.equal(String(node.operator), '+');
  // left = 1, right = 2*3
  assert.ok(node.right_node instanceof BinaryNode);
  assert.equal(String(node.right_node.operator), '*');
});

// ─────────────────────────────────────────────
// Const (null / true / false) — 日本語と英語両方
// ─────────────────────────────────────────────

test('ConstNode literals (Japanese + English)', () => {
  for (const [src, val] of [
    ['値なし', null],
    ['null', null],
    ['真', true],
    ['true', true],
    ['偽', false],
    ['false', false],
  ]) {
    const s = new Source(src);
    const node = s.parse('@Boolean');
    assert.ok(node instanceof ConstNode);
    assert.equal(node.native_value, val);
    assert.equal(String(node), src);
  }
});

test('ConstNode is reachable via @Term', () => {
  for (const [src, val] of [
    ['値なし', null],
    ['真', true],
    ['偽', false],
  ]) {
    const s = new Source(src);
    const node = s.parse('@Term');
    assert.ok(node instanceof ConstNode);
    assert.equal(node.native_value, val);
  }
});

test('ConstNode in assignment', () => {
  for (const src of ['x = 値なし', 'x = 真']) {
    const s = new Source(src);
    const node = s.parse('@Assignment');
    assert.ok(node instanceof AssignmentNode);
    assert.equal(String(node), src);
  }
});

// ─────────────────────────────────────────────
// Statement — yui syntax
// ─────────────────────────────────────────────

test('Assignment statement', () => {
  let s = new Source('x = 1 # コメント');
  let node = s.parse('@Assignment');
  assert.equal(String(node), 'x = 1');

  s = new Source('x=1 # コメント');
  node = s.parse('@Statement');
  assert.equal(String(node), 'x=1');
});

test('Increment statement', () => {
  let s = new Source('xを増やす');
  let node = s.parse('@Increment');
  assert.ok(node instanceof IncrementNode);
  assert.equal(String(node), 'xを増やす');

  s = new Source('xを増やす # コメント');
  node = s.parse('@Statement');
  assert.equal(String(node), 'xを増やす');
});

test('Increment lookahead rejects non-matching prefix', () => {
  assert.throws(
    () => new Source('xに3増やす # コメント').parse('@Statement'),
    (err) => {
      assert.ok(err instanceof YuiError);
      assert.match(err.message, /expected/);
      return true;
    },
  );
});

test('Decrement statement', () => {
  let s = new Source('xを減らす');
  let node = s.parse('@Decrement');
  assert.ok(node instanceof DecrementNode);
  assert.equal(String(node), 'xを減らす');

  s = new Source('yを減らす # コメント');
  node = s.parse('@Statement');
  assert.equal(String(node), 'yを減らす');
});

test('Append statement', () => {
  let s = new Source('xに10を追加する');
  let node = s.parse('@Append');
  assert.ok(node instanceof AppendNode);
  assert.equal(String(node), 'xに10を追加する');

  s = new Source('xに10を追加する # コメント');
  node = s.parse('@Statement');
  assert.equal(String(node), 'xに10を追加する');
});

test('Append statement with tail', () => {
  let s = new Source('xの末尾に10を追加する');
  let node = s.parse('@Append');
  assert.equal(String(node), 'xの末尾に10を追加する');

  s = new Source('xの末尾に10を追加する # コメント');
  node = s.parse('@Statement');
  assert.equal(String(node), 'xの末尾に10を追加する');
});

test('Break statement', () => {
  const s = new Source('くり返しを抜ける');
  const node = s.parse('@Break');
  assert.ok(node instanceof BreakNode);
  assert.equal(String(node), 'くり返しを抜ける');
});

test('Return statement', () => {
  let s = new Source('1が答え');
  let node = s.parse('@Return');
  assert.ok(node instanceof ReturnNode);
  assert.equal(String(node), '1が答え');

  s = new Source('1が答え # コメント');
  node = s.parse('@Return');
  assert.equal(String(node), '1が答え');
});

test('FuncDef with single argument', () => {
  const s = new Source('f = 入力x に対して {\n  xが答え\n}');
  const node = s.parse('@FuncDef');
  assert.ok(node instanceof FuncDefNode);
  assert.equal(String(node), 'f = 入力x に対して {\n  xが答え\n}');
});

test('FuncDef with no argument', () => {
  const s = new Source('f = 入力なし に対して {\n  1が答え\n}');
  const node = s.parse('@FuncDef');
  assert.equal(String(node), 'f = 入力なし に対して {\n  1が答え\n}');
});

test('FuncDef with multiple arguments', () => {
  const s = new Source('f = 入力x,y に対して {\n  xが答え\n}');
  const node = s.parse('@FuncDef');
  assert.equal(String(node), 'f = 入力x,y に対して {\n  xが答え\n}');
  assert.equal(node.parameters.length, 2);
});

// ─────────────────────────────────────────────
// Block / If / Repeat / TopLevel
// ─────────────────────────────────────────────

test('TopLevel parses two assignments', () => {
  const s = new Source('x = 1\ny=2');
  const node = s.parse('@TopLevel');
  assert.ok(node instanceof BlockNode);
  assert.equal(String(node), 'x = 1\ny=2');
  assert.equal(node.statements.length, 2);
});

test('TopLevel respects custom statement-separator', () => {
  const s = new Source('x = 1;y=2');
  s.updateSyntax({ 'statement-separator': ';' });
  const node = s.parse('@TopLevel');
  assert.equal(String(node), 'x = 1;y=2');
});

test('TopLevel rejects garbage trailing tokens', () => {
  assert.throws(
    () => new Source('x = 1 知らないよ').parse('@TopLevel'),
    (err) => {
      assert.ok(err instanceof YuiError);
      assert.match(err.message, /wrong/);
      assert.match(err.message, /statement/);
      return true;
    },
  );
});

test('Block parses two statements inside braces', () => {
  const s = new Source('n回 {\n  x = 1\n  y=2\n} くり返す', { pos: 3 });
  const node = s.parse('@Block');
  assert.equal(String(node), '{\n  x = 1\n  y=2\n}');
});

test('Block allows blank lines and comments', () => {
  const s = new Source('n回 {\n  x = 1\n #a\n\n  y=2\n} くり返す', { pos: 3 });
  const node = s.parse('@Block');
  assert.equal(String(node), '{\n  x = 1\n #a\n\n  y=2\n}');
});

test('Repeat statement', () => {
  const s = new Source('3回くり返す {\n  x = 1\n}');
  const node = s.parse('@Repeat');
  assert.ok(node instanceof RepeatNode);
  assert.equal(String(node), '3回くり返す {\n  x = 1\n}');
});

test('If statement', () => {
  const s = new Source('もしxが1ならば {\n  x = 1\n}');
  const node = s.parse('@If');
  assert.ok(node instanceof IfNode);
  assert.equal(String(node), 'もしxが1ならば {\n  x = 1\n}');
});

test('If statement via @Statement dispatch', () => {
  const s = new Source('もしxが1ならば {\n  x = 1\n}');
  const node = s.parse('@Statement');
  assert.equal(String(node), 'もしxが1ならば {\n  x = 1\n}');
});

test('If with `のいずれか` (in)', () => {
  const s = new Source('もしxがAのいずれかならば{\n  x = 1\n}');
  const node = s.parse('@If');
  assert.equal(String(node), 'もしxがAのいずれかならば{\n  x = 1\n}');
});

test('If with `のいずれでもない` (not in)', () => {
  const s = new Source('もしxがAのいずれでもないならば{\n  x = 1\n}');
  const node = s.parse('@If');
  assert.equal(String(node), 'もしxがAのいずれでもないならば{\n  x = 1\n}');
});

test('Nested If as @If slices off outer block', () => {
  const s = new Source('もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1');
  const node = s.parse('@If');
  assert.equal(
    String(node),
    'もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}',
  );
});

test('Nested If as @TopLevel includes trailing assignment', () => {
  const s = new Source('もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1');
  const node = s.parse('@TopLevel');
  assert.equal(
    String(node),
    'もしxが1ならば {\n  x=0\n  もしxが0ならば {\n    x=1\n  }\n}\ny=1',
  );
});

test('Repeat with inner break', () => {
  const s = new Source('10回くり返す{\n   countを増やす\n   もし countが 5ならば{\n      くり返しを抜ける\n   }\n}');
  const node = s.parse('@Repeat');
  assert.match(String(node), /くり返しを抜ける/);
});

// ─────────────────────────────────────────────
// YuiParser (エンドツーエンド)
// ─────────────────────────────────────────────

test('YuiParser parses a small yui program end-to-end', () => {
  const p = new YuiParser('yui');
  const ast = p.parse('標準ライブラリを使う\nx = 1\ny = 2');
  assert.ok(ast instanceof BlockNode);
  assert.equal(ast.statements.length, 3);
  assert.equal(ast.top_level, true);
});

test('YuiParser works across all bundled syntaxes (empty program)', () => {
  const syntaxes = ['ast', 'bridget', 'emoji', 'empty', 'jslike', 'nannan', 'pylike', 'sexpr', 'wenyan', 'yui', 'zup'];
  for (const name of syntaxes) {
    const p = new YuiParser(name);
    const ast = p.parse('');
    assert.ok(ast instanceof BlockNode, `${name} empty program`);
    assert.equal(ast.statements.length, 0, `${name} empty program has no statements`);
  }
});

test('NONTERMINALS table exposes all expected keys', () => {
  const expected = [
    '@Boolean', '@Number', '@String', '@Array', '@Object', '@Name',
    '@Term', '@Primary', '@Multiplicative', '@Additive', '@Expression',
    '@Assignment', '@Increment', '@Decrement', '@Append',
    '@Break', '@Import', '@Pass', '@Return', '@PrintExpression',
    '@Repeat', '@If', '@FuncDef', '@Assert',
    '@Block', '@Statement', '@Statement[]', '@TopLevel',
  ];
  for (const key of expected) {
    assert.ok(key in NONTERMINALS, `NONTERMINALS missing ${key}`);
  }
});
