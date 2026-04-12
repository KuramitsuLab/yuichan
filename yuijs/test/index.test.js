// index.test.js — 公開 API エントリのスモークテスト
// すべての re-export が解決し、run / convert が動作することを確認する。

import { test } from 'node:test';
import assert from 'node:assert/strict';

import * as yuijs from '../src/index.js';
import {
  run,
  convert,
  YuiRuntime,
  YuiValue,
  YuiParser,
  CodingVisitor,
  YuiError,
  YuiExample,
  getAllExamples,
  types,
  NumberNode,
  BlockNode,
  AssignmentNode,
  NameNode,
  VERSION,
} from '../src/index.js';

// ─────────────────────────────────────────────
// re-export surface
// ─────────────────────────────────────────────

test('index exports core classes', () => {
  const expected = [
    // types
    'YuiValue', 'types', 'OPERATORS',
    'IntType', 'FloatType', 'StringType', 'ArrayType', 'ObjectType',
    'NullType', 'BoolType', 'NumberType',
    // errors
    'YuiError', 'ERROR_MESSAGES', 'formatMessages',
    // ast
    'ASTNode', 'NumberNode', 'StringNode', 'NameNode', 'BlockNode',
    'AssignmentNode', 'IfNode', 'RepeatNode', 'FuncDefNode', 'FuncAppNode',
    'ReturnNode', 'ConstNode', '_node',
    // syntax / parser / coding
    'YuiSyntax', 'loadSyntax', 'listSyntaxNames', 'generateBnf',
    'Source', 'YuiParser', 'CodingVisitor',
    // runtime / stdlib
    'YuiRuntime', 'YuiFunction', 'LocalFunction', 'NativeFunction',
    'YuiBreakException', 'YuiReturnException',
    'standardLib',
    // examples
    'YuiExample', 'getAllExamples', 'getSamples', 'getTestExamples',
    // helpers
    'run', 'convert', 'VERSION',
  ];
  for (const name of expected) {
    assert.ok(yuijs[name] != null, `missing export: ${name}`);
  }
});

test('VERSION is a string', () => {
  assert.equal(typeof VERSION, 'string');
  assert.match(VERSION, /^\d+\.\d+\.\d+$/);
});

// ─────────────────────────────────────────────
// run() — 最小シナリオ
// ─────────────────────────────────────────────

test('run() executes a simple yui program and returns env snapshot', () => {
  // hello_world は PrintExpressionNode があるので stdout が汚れる。
  // assignment のみのプログラムで env だけ検証する。
  const ex = getAllExamples().find((e) => e.name === 'variables');
  const src = ex.generate('yui', { includeAsserts: false });
  const { env, runtime } = run(src, { syntax: 'yui' });
  assert.equal(env.x, 2);
  assert.equal(env.y, -3);
  assert.ok(runtime instanceof YuiRuntime);
});

test('run() surfaces YuiError for undefined variables', () => {
  // 単独で変数参照すると PrintExpressionNode として評価されるが、
  // 未定義変数なので YuiError を投げる
  assert.throws(
    () => run('undefined_var\n', { syntax: 'yui' }),
    (err) => err instanceof YuiError,
  );
});

test('run() loads initial env values', () => {
  // initial env に x=10 を入れて increment する
  const src = 'xを増やす\n';
  const { env } = run(src, { syntax: 'yui', env: { x: 10 } });
  assert.equal(env.x, 11);
});

// ─────────────────────────────────────────────
// convert() — syntax roundtrip
// ─────────────────────────────────────────────

test('convert() transforms yui source to pylike', () => {
  const ex = getAllExamples().find((e) => e.name === 'hello_world');
  const yuiSrc = ex.generate('yui');
  const pylikeSrc = convert(yuiSrc, { from: 'yui', to: 'pylike' });
  assert.equal(typeof pylikeSrc, 'string');
  assert.ok(pylikeSrc.length > 0);
  // 変換後も Hello, world! リテラルは残っている
  assert.ok(pylikeSrc.includes('Hello, world!'));
  // pylike としてパースできる
  const parser = new YuiParser('pylike');
  const ast = parser.parse(pylikeSrc);
  assert.ok(ast != null);
});

test('convert() requires both from and to', () => {
  assert.throws(() => convert('x = 1', { from: 'yui' }), /from.*to/);
  assert.throws(() => convert('x = 1', { to: 'pylike' }), /from.*to/);
});

// ─────────────────────────────────────────────
// 低レベル API も併用できる
// ─────────────────────────────────────────────

test('low-level YuiParser + YuiRuntime still works via index imports', () => {
  const src = 'x=1\ny=2\n';
  const parser = new YuiParser('yui');
  const ast = parser.parse(src);
  assert.ok(ast != null);
  const rt = new YuiRuntime();
  const env = rt.exec(src, 'yui', { evalMode: false });
  assert.equal(types.unbox(env.get('x')), 1);
  assert.equal(types.unbox(env.get('y')), 2);
});

test('AST node construction via index exports', () => {
  const block = new BlockNode(
    [new AssignmentNode(new NameNode('a'), new NumberNode(42))],
    true,
  );
  assert.equal(block.statements.length, 1);
  assert.equal(block.statements[0].expression.native_value, 42);
});
