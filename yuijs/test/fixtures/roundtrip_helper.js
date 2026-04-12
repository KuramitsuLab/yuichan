// test/fixtures/roundtrip_helper.js
// 各 syntax の roundtrip テストの共通ヘルパ。
// Python 版 yuichan/syntax/test_yui.py の gen_roundtrip_test() に相当。

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { BlockNode } from '../../src/yuiast.js';
import { loadSyntax } from '../../src/yuisyntax.js';
import { CodingVisitor } from '../../src/yuicoding.js';
import { types, YuiError } from '../../src/yuitypes.js';

import {
  astTestcases,
  initRuntime,
  isEnvExpected,
} from './ast_testcases.js';

function assertExpected(name, runtime, result, err, expected) {
  if (typeof expected === 'string' && expected.startsWith('💣')) {
    assert.ok(err instanceof YuiError,
      `${name}: expected YuiError ${expected}, got result=${JSON.stringify(result)}`);
    assert.equal(`💣${err.messages[0]}`, expected, `${name}: error key mismatch`);
    return;
  }
  if (err) {
    throw err;
  }
  if (isEnvExpected(expected)) {
    const actual = types.unbox(runtime.getenv(expected.name));
    assert.deepEqual(actual, expected.value,
      `${name}: env[${expected.name}] mismatch`);
    return;
  }
  assert.deepEqual(types.unbox(result), expected, `${name}: result mismatch`);
}

/**
 * 指定した syntax 名で roundtrip テスト群を登録する。
 * Python 版の gen_roundtrip_test(syntax_name) + pytest parametrize に相当。
 */
export function registerRoundtripTests(syntaxName) {
  const syntax = loadSyntax(syntaxName);

  for (const [name, node, expected] of astTestcases) {
    test(`roundtrip/${syntaxName}: ${name}`, () => {
      if (node instanceof BlockNode) {
        node.top_level = true;
      }
      const visitor = new CodingVisitor(syntax);
      const code = visitor.emit(node);

      const runtime = initRuntime();
      let result;
      let err = null;
      try {
        result = runtime.exec(code, syntaxName, { evalMode: true });
      } catch (e) {
        if (e instanceof YuiError) {
          err = e;
        } else {
          throw new Error(
            `${name}: unexpected error during exec\n--- code ---\n${code}\n--- error ---\n${e.stack ?? e}`,
          );
        }
      }
      try {
        assertExpected(name, runtime, result, err, expected);
      } catch (e) {
        const detail = `\n--- generated code ---\n${code}\n----------------------`;
        e.message += detail;
        throw e;
      }
    });
  }
}
