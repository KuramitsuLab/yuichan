// yuiexample.test.js — 生成されたコードがパースできることを検証する
// Python 版 yuichan/test_example.py の移植。
//
// 各 (syntax, example) の組について:
//   1. example.generate(syntax) でコードを生成
//   2. Source(code, {syntax}).parse('@TopLevel') が例外を投げないこと

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { getAllExamples, YuiExample } from '../src/yuiexample.js';
import { Source } from '../src/yuiparser.js';

const SYNTAXES = ['yui', 'pylike', 'emoji'];
const ALL_EXAMPLES = getAllExamples();

// 期待される例の数 (Python 版と揃える)
test('getAllExamples returns 20 examples', () => {
  assert.equal(ALL_EXAMPLES.length, 20);
});

test('each example has required fields', () => {
  for (const ex of ALL_EXAMPLES) {
    assert.ok(ex instanceof YuiExample, `${ex.name} is not a YuiExample`);
    assert.equal(typeof ex.name, 'string');
    assert.equal(typeof ex.description, 'string');
    assert.ok(
      ['sample', 'test', 'both'].includes(ex.kind),
      `${ex.name}.kind = ${ex.kind}`,
    );
    assert.ok(ex.ast_node != null);
  }
});

// 生成 → パース ラウンドトリップ (Python test_example.py と同じロジック)
for (const syntaxName of SYNTAXES) {
  for (const example of ALL_EXAMPLES) {
    test(`generate-then-parse: ${syntaxName}/${example.name}`, () => {
      const code = example.generate(syntaxName);
      assert.equal(typeof code, 'string');
      assert.ok(code.length > 0);
      const source = new Source(code, { syntax: syntaxName });
      // 例外を投げなければ合格
      source.parse('@TopLevel');
    });
  }
}

// includeAsserts=false で AssertNode と "テスト..." コメントが除去されること
test('generate(includeAsserts=false) strips AssertNodes', () => {
  const ex = ALL_EXAMPLES.find((e) => e.name === 'variables');
  const withAsserts = ex.generate('yui', { includeAsserts: true });
  const withoutAsserts = ex.generate('yui', { includeAsserts: false });
  assert.ok(withAsserts.length > withoutAsserts.length);
  // "テスト" コメントが stripped 版では消えている
  assert.ok(!withoutAsserts.includes('テスト: x が 2'));
});
