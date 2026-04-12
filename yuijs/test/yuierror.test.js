// yuierror.js の単体テスト
// node --test test/yuierror.test.js

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  ERROR_MESSAGES,
  YuiError,
  formatMessages,
  normalizeMessages,
  setVerbose,
  isVerbose,
  vprint,
} from '../src/yuierror.js';

// ─────────────────────────────────────────────
// ERROR_MESSAGES dictionary
// ─────────────────────────────────────────────
test('ERROR_MESSAGES has known keys', () => {
  assert.equal(ERROR_MESSAGES['expected-token'], '書き方が間違っています');
  assert.equal(ERROR_MESSAGES['type-error'], 'データの種類（型）が違っています');
  assert.equal(ERROR_MESSAGES['mismatch-argument'], '引数の数が合いません');
});

// ─────────────────────────────────────────────
// formatMessages
// ─────────────────────────────────────────────
test('formatMessages substitutes the first key', () => {
  assert.equal(formatMessages(['expected-token']), '書き方が間違っています');
});

test('formatMessages appends the rest joined by space', () => {
  assert.equal(
    formatMessages(['type-error', '❌foo', '✅bar']),
    'データの種類（型）が違っています ❌foo ✅bar'
  );
});

test('formatMessages with unknown key returns the key itself', () => {
  assert.equal(formatMessages(['no-such-key']), 'no-such-key');
});

test('formatMessages with empty input returns empty string', () => {
  assert.equal(formatMessages([]), '');
  assert.equal(formatMessages(null), '');
  assert.equal(formatMessages(undefined), '');
});

// ─────────────────────────────────────────────
// normalizeMessages
// ─────────────────────────────────────────────
test('normalizeMessages joins ASCII parts with -', () => {
  // 全部 ASCII なら一つに連結される
  assert.deepEqual(normalizeMessages(['type', 'error']), ['type-error']);
});

test('normalizeMessages keeps non-ASCII (>127) elements standalone', () => {
  // ❌ は U+274C, ✅ は U+2705 — どちらも > 127
  const result = normalizeMessages(['type', 'error', '❌foo', '✅bar']);
  assert.deepEqual(result, ['type-error', '❌foo', '✅bar']);
});

test('normalizeMessages handles a leading non-ASCII element', () => {
  const result = normalizeMessages(['❌foo', 'a', 'b']);
  assert.deepEqual(result, ['❌foo', 'a-b']);
});

test('normalizeMessages accepts a plain string and wraps it', () => {
  assert.deepEqual(normalizeMessages('hello'), ['hello']);
});

test('normalizeMessages handles surrogate pair emoji (codepoint > 0xFFFF)', () => {
  // 💣 = U+1F4A3 (サロゲートペア)。codePointAt は正しく > 127 を返す
  const result = normalizeMessages(['💣mismatch', 'foo']);
  assert.deepEqual(result, ['💣mismatch', 'foo']);
});

test('normalizeMessages returns a frozen array', () => {
  const result = normalizeMessages(['a', 'b']);
  assert.ok(Object.isFrozen(result));
});

// ─────────────────────────────────────────────
// YuiError
// ─────────────────────────────────────────────
test('YuiError extends Error and exposes messages/BK', () => {
  const err = new YuiError(['type-error', '❌x']);
  assert.ok(err instanceof Error);
  assert.ok(err instanceof YuiError);
  assert.equal(err.name, 'YuiError');
  assert.deepEqual(err.messages, ['type-error', '❌x']);
  assert.equal(err.BK, false);
  assert.equal(err.errorNode, null);
});

test('YuiError accepts a string and normalizes it', () => {
  const err = new YuiError('boom');
  assert.deepEqual(err.messages, ['boom']);
});

test('YuiError ignores errorNode without pos property', () => {
  const fakeNode = { foo: 1 };
  const err = new YuiError(['type-error'], fakeNode);
  assert.equal(err.errorNode, null);
});

test('YuiError accepts errorNode that has pos property', () => {
  const node = {
    pos: 0,
    endPos: 3,
    extract() {
      return [1, 2, 'foo'];
    },
  };
  const err = new YuiError(['type-error'], node);
  assert.strictEqual(err.errorNode, node);
  assert.equal(err.lineno, 1);
  assert.equal(err.offset, 2);
  assert.equal(err.text, 'foo');
});

test('YuiError.addMessage appends and re-freezes', () => {
  const err = new YuiError(['type-error']);
  err.addMessage('extra');
  assert.deepEqual(err.messages, ['type-error', 'extra']);
  assert.ok(Object.isFrozen(err.messages));
});

test('YuiError.formattedMessage without errorNode', () => {
  const err = new YuiError(['expected-token']);
  assert.equal(
    err.formattedMessage(),
    '[構文エラー/SyntaxError] 書き方が間違っています'
  );
});

test('YuiError.formattedMessage with errorNode renders snippet + pointer', () => {
  const node = {
    pos: 4,
    endPos: 7,
    extract() {
      return [2, 5, 'abc def'];
    },
  };
  const err = new YuiError(['expected-token'], node);
  const formatted = err.formattedMessage();
  assert.match(formatted, /\[構文エラー\/SyntaxError\] 書き方が間違っています line 2, column 5:/);
  assert.match(formatted, /abc def/);
  assert.match(formatted, /\^\^\^/); // 3-char pointer
});

test('YuiError.formattedMessage respects lineoffset', () => {
  const node = {
    pos: 0,
    endPos: 1,
    extract() {
      return [0, 1, 'x'];
    },
  };
  const err = new YuiError(['expected-token'], node);
  const formatted = err.formattedMessage(' ', '^', 10);
  assert.match(formatted, /line 10,/);
});

// ─────────────────────────────────────────────
// verbose toggling
// ─────────────────────────────────────────────
test('setVerbose / isVerbose toggle', () => {
  setVerbose(false);
  assert.equal(isVerbose(), false);
  setVerbose(true);
  assert.equal(isVerbose(), true);
  setVerbose(false); // 後始末
});

test('vprint does not throw when verbose is off or on', () => {
  setVerbose(false);
  assert.doesNotThrow(() => vprint('hidden'));
  setVerbose(true);
  // verbose 時は stderr に出力するが、一時的に console.error を黙らせる
  const orig = console.error;
  console.error = () => {};
  try {
    assert.doesNotThrow(() => vprint('shown'));
  } finally {
    console.error = orig;
    setVerbose(false);
  }
});
