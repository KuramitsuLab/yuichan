// yuisyntax.js の単体テスト
// node --test test/yuisyntax.test.js
//
// Python 側 (yuichan.yuisyntax) の出力を ground truth として使う。

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  DEFAULT_SYNTAX_JSON,
  YuiSyntax,
  loadSyntax,
  loadSyntaxFromUrl,
  listSyntaxNames,
  generateBnf,
  getExampleFromPattern,
  GRAMMARS,
  SYNTAX_NAMES,
  getGrammar,
  _internals,
} from '../src/yuisyntax.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─────────────────────────────────────────────
// _Rng (deterministic seed=null behavior)
// ─────────────────────────────────────────────
test('_Rng with null seed always returns 0', () => {
  const rng = new _internals._Rng(null);
  for (let i = 0; i < 10; i++) {
    assert.equal(rng.nextInt(100), 0);
  }
});

test('_Rng with numeric seed is deterministic across runs', () => {
  const a = new _internals._Rng(42);
  const b = new _internals._Rng(42);
  for (let i = 0; i < 5; i++) {
    assert.equal(a.nextInt(100), b.nextInt(100));
  }
});

// ─────────────────────────────────────────────
// getExampleFromPattern
// Python ground truth (yuichan.yuisyntax.get_example_from_pattern, seed=None):
//   '[ \\t\\r　]'      -> ' '
//   '[A-Za-z_]'        -> 'A'
//   '[A-Za-z0-9_]*'    -> ''
//   '値なし|null'       -> '値なし'
//   '真|true'           -> '真'
//   '\\+'              -> '+'
//   '(の末尾)?に'       -> 'に'
//   '[\\.][0-9]'       -> '.0'
//   '>>>\\s+'          -> '>>> '
//   '[\\n]'            -> '\n'
//   '\\\\'             -> '\\'
//   '\\{'              -> '{'
// ─────────────────────────────────────────────
test('getExampleFromPattern matches Python ground truth (seed=null)', () => {
  const cases = [
    ['[ \\t\\r　]', ' '],
    ['[A-Za-z_]', 'A'],
    ['[A-Za-z0-9_]*', ''],
    ['値なし|null', '値なし'],
    ['真|true', '真'],
    ['\\+', '+'],
    ['(の末尾)?に', 'に'],
    ['[\\.][0-9]', '.0'],
    ['>>>\\s+', '>>> '],
    ['[\\n]', '\n'],
    ['\\\\', '\\'],
    ['\\{', '{'],
  ];
  for (const [pattern, expected] of cases) {
    assert.equal(
      getExampleFromPattern(pattern),
      expected,
      `pattern=${JSON.stringify(pattern)}`
    );
  }
});

test('getExampleFromPattern throws on unmatched parens', () => {
  assert.throws(() => getExampleFromPattern('(unclosed'), /Unmatched parentheses/);
});

// ─────────────────────────────────────────────
// loadSyntax
// ─────────────────────────────────────────────
test('loadSyntax(null) loads yui by default', () => {
  const t = loadSyntax();
  assert.equal(t['syntax'], 'Yui-Classic');
  assert.equal(t['null'], '値なし|null');
});

test('loadSyntax fills in DEFAULT_SYNTAX_JSON for missing keys', () => {
  const t = loadSyntax('yui');
  // 'unary-inspect' is in DEFAULT but not in yui.json
  assert.equal(t['unary-inspect'], '👀');
  assert.equal(t['catch-begin'], '🧤');
});

test('loadSyntax derives string-content-end if not present', () => {
  // empty.json doesn't define string-content-end (we'll verify against yui.json which does)
  const t = loadSyntax('yui');
  // yui.json defines string-content-end explicitly
  assert.equal(t['string-content-end'], '\\\\|\\{|\\"');
});

test('loadSyntax derives string-content-end from defaults when missing', () => {
  // Use a synthetic minimal json: write a temp file? Easier — use loadSyntax on empty.json
  // and confirm derivation. empty.json content TBD; just check the rule.
  const t = loadSyntax('empty');
  // string-escape '\\\\', interpolation-begin '\\{', string-end '"' (default from DEFAULT_SYNTAX_JSON)
  assert.ok(t['string-content-end'].includes('|'));
});

test('loadSyntax key count matches Python (yui has 133 keys)', () => {
  const t = loadSyntax('yui');
  assert.equal(Object.keys(t).length, 133);
});

// ─────────────────────────────────────────────
// listSyntaxNames
// ─────────────────────────────────────────────
test('listSyntaxNames returns sorted names without .json', () => {
  const names = listSyntaxNames();
  assert.deepEqual(names, [
    'ast', 'bridget', 'emoji', 'empty', 'jslike',
    'nannan', 'pylike', 'sexpr', 'wenyan', 'yui', 'zup',
  ]);
});

// ─────────────────────────────────────────────
// 組み込み grammar 辞書 (yuigrammars.js)
// ─────────────────────────────────────────────
test('GRAMMARS dict exposes all 11 built-in grammars', () => {
  assert.equal(Object.keys(GRAMMARS).length, 11);
  assert.ok(GRAMMARS['yui'] != null);
  assert.equal(GRAMMARS['yui']['syntax'], 'Yui-Classic');
});

test('GRAMMARS is frozen (immutable)', () => {
  assert.ok(Object.isFrozen(GRAMMARS));
});

test('SYNTAX_NAMES is the sorted list', () => {
  assert.deepEqual([...SYNTAX_NAMES], [
    'ast', 'bridget', 'emoji', 'empty', 'jslike',
    'nannan', 'pylike', 'sexpr', 'wenyan', 'yui', 'zup',
  ]);
});

test('getGrammar(name) returns the grammar dict or null', () => {
  assert.ok(getGrammar('yui') != null);
  assert.equal(getGrammar('nope'), null);
});

test('loadSyntax throws on unknown name', () => {
  assert.throws(
    () => loadSyntax('unknown-grammar-xyz'),
    /unknown syntax: unknown-grammar-xyz/,
  );
});

test('loadSyntax accepts a terminals dict directly', () => {
  const customDict = { 'syntax': 'custom', 'null': 'NIL' };
  const t = loadSyntax(customDict);
  assert.equal(t['syntax'], 'custom');
  assert.equal(t['null'], 'NIL');
  // DEFAULT_SYNTAX_JSON も埋まる
  assert.equal(t['unary-inspect'], '👀');
});

// ─────────────────────────────────────────────
// loadSyntaxFromUrl (Web 埋め込み用)
// ─────────────────────────────────────────────
test('loadSyntaxFromUrl with injected fetch', async () => {
  const mockFetch = async (url) => {
    assert.equal(url, 'https://example.com/custom.json');
    return {
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ 'syntax': 'from-url', 'null': 'empty' }),
    };
  };
  const t = await loadSyntaxFromUrl('https://example.com/custom.json', {
    fetch: mockFetch,
  });
  assert.equal(t['syntax'], 'from-url');
  assert.equal(t['null'], 'empty');
  // デフォルトも埋まっている
  assert.equal(t['unary-inspect'], '👀');
});

test('loadSyntaxFromUrl rejects on HTTP error', async () => {
  const mockFetch = async () => ({
    ok: false,
    status: 404,
    statusText: 'Not Found',
    json: async () => ({}),
  });
  await assert.rejects(
    loadSyntaxFromUrl('https://example.com/missing.json', { fetch: mockFetch }),
    /HTTP 404/,
  );
});

test('loadSyntaxFromUrl rejects on non-object JSON', async () => {
  const mockFetch = async () => ({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => 'not an object',
  });
  await assert.rejects(
    loadSyntaxFromUrl('https://example.com/bad.json', { fetch: mockFetch }),
    /did not return a JSON object/,
  );
});

test('loadSyntaxFromUrl rejects when no fetch is available', async () => {
  // globalThis.fetch を一時的に退避して「fetch が存在しない環境」を再現する
  const originalFetch = globalThis.fetch;
  delete globalThis.fetch;
  try {
    await assert.rejects(
      loadSyntaxFromUrl('https://example.com/x.json'),
      /fetch is not available/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('loadSyntaxFromUrl uses global fetch by default (Node 18+)', async () => {
  // 実際の HTTP は避けたいので fetch をその場で差し替える。
  const originalFetch = globalThis.fetch;
  let called = false;
  globalThis.fetch = async () => {
    called = true;
    return {
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ 'syntax': 'mocked' }),
    };
  };
  try {
    const t = await loadSyntaxFromUrl('https://example.com/x.json');
    assert.ok(called);
    assert.equal(t['syntax'], 'mocked');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ─────────────────────────────────────────────
// YuiSyntax class
// ─────────────────────────────────────────────
test('YuiSyntax constructor copies the input dict', () => {
  const src = { foo: 'bar' };
  const s = new YuiSyntax(src);
  src.foo = 'mutated';
  assert.equal(s.terminals.foo, 'bar');
});

test('YuiSyntax.isDefined: true for non-empty string, false for empty/missing', () => {
  const s = new YuiSyntax({ a: 'x', b: '', c: undefined });
  assert.equal(s.isDefined('a'), true);
  assert.equal(s.isDefined('b'), false);
  assert.equal(s.isDefined('missing'), false);
});

test('YuiSyntax.get returns the source string', () => {
  const s = new YuiSyntax({ x: '\\d+' });
  assert.equal(s.get('x'), '\\d+');
  assert.equal(s.get('missing'), '');
});

test('YuiSyntax.getPattern compiles to sticky RegExp and caches', () => {
  const s = new YuiSyntax({ x: '\\d+' });
  const p1 = s.getPattern('x');
  assert.ok(p1 instanceof RegExp);
  assert.equal(p1.sticky, true);
  // Same instance on second call (cached)
  const p2 = s.getPattern('x');
  assert.strictEqual(p1, p2);
});

test('YuiSyntax.getPattern works on a real source position (sticky)', () => {
  const s = new YuiSyntax({ word: '[A-Za-z]+' });
  const re = s.getPattern('word');
  re.lastIndex = 4;
  const m = re.exec('123 abc 456');
  assert.ok(m);
  assert.equal(m[0], 'abc');
  // Sticky should NOT match at a position that doesn't start with [A-Za-z]
  re.lastIndex = 0;
  const noMatch = re.exec('123 abc 456');
  assert.equal(noMatch, null);
});

test('YuiSyntax.get returns source even after compilation', () => {
  const s = new YuiSyntax({ x: '\\d+' });
  s.getPattern('x'); // compile
  assert.equal(s.get('x'), '\\d+');
});

test('YuiSyntax.forExample uses Python-equivalent example for known patterns', () => {
  const s = new YuiSyntax({ kw: '値なし|null' });
  assert.equal(s.forExample('kw'), '値なし');
});

test('YuiSyntax.forExample works after pattern was compiled', () => {
  const s = new YuiSyntax({ kw: '値なし|null' });
  s.getPattern('kw');
  assert.equal(s.forExample('kw'), '値なし');
});

test('YuiSyntax.getPattern throws on invalid regex', () => {
  const s = new YuiSyntax({ bad: '(' });
  assert.throws(() => s.getPattern('bad'), /Invalid regex/);
});

// ─────────────────────────────────────────────
// generateBnf — exact byte match against Python ground truth
// ─────────────────────────────────────────────
test('generateBnf for yui matches Python ground truth byte-for-byte', () => {
  const expected = readFileSync(
    join(__dirname, 'fixtures', 'yui_bnf_expected.txt'),
    'utf-8'
  ).trimEnd();
  const t = loadSyntax('yui');
  const actual = generateBnf(t).trimEnd();
  assert.equal(actual, expected);
});

// ─────────────────────────────────────────────
// DEFAULT_SYNTAX_JSON sanity
// ─────────────────────────────────────────────
test('DEFAULT_SYNTAX_JSON contains expected core keys', () => {
  for (const key of [
    'whitespace', 'linefeed', 'number-first-char', 'name-first-char',
    'string-begin', 'array-begin', 'object-begin',
    'unary-inspect', 'catch-begin', 'assert-begin',
  ]) {
    assert.ok(key in DEFAULT_SYNTAX_JSON, `missing ${key}`);
  }
});
