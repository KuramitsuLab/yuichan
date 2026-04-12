// yuierror.js — Yui のエラー型と表示用ユーティリティ
// Python 版 yuichan/yuierror.py の移植
//
// 内部依存なし (最下層)。

// ─────────────────────────────────────────────
// Verbose logging
// ─────────────────────────────────────────────
let _verbose = false;

export function setVerbose(flag) {
  _verbose = !!flag;
}

export function isVerbose() {
  return _verbose;
}

/** Verbose モード時のみ stderr に出力 */
export function vprint(...args) {
  if (_verbose) {
    // Node の console.error は stderr に書く
    console.error(...args);
  }
}

// ─────────────────────────────────────────────
// エラーメッセージ辞書 (Python 側と完全に同期させること)
// ─────────────────────────────────────────────
export const ERROR_MESSAGES = {
  // パーサーエラー
  'expected-token':         '書き方が間違っています',
  'expected-number':        '数値が必要です',
  'expected-string':        '文字列が必要です',
  'expected-array':         '配列が必要です',
  'expected-object':        'オブジェクトが必要です',
  'expected-boolean':       '真偽値が必要です',
  'expected-closing':       '閉じ括弧が必要です',
  'expected-variable':      'ここは変数が必要です',
  'expected-expression':    '変数や値が必要です',

  'typo':                   'うっかり間違えてませんか？',
  'wrong-name':             '名前が不正です',
  'wrong-statement':        '何とも解釈できない書き方です',
  'wrong-escape-sequence':  '不正なエスケープシーケンスです',
  'wrong-indent-level':     'インデントが不正です',
  'unexpected-return':      '関数内でのみ使えます',
  'unexpected-break':       'くり返しの中でのみ使えます',

  // ランタイムエラー
  'undefined-variable':     '変数が定義されていません',
  'undefined-function':     '関数が定義されていません',
  'type-error':             'データの種類（型）が違っています',
  'value-error':            'データの値がおかしいです',
  'array-value-error':      '値がおかしくて配列データが壊れます',
  'division-by-zero':       'ゼロで割ってしまいました',
  'error-index':            '配列のインデックスが範囲外です',
  'error-value':            '値エラーです',
  'too-many-recursion':     '再帰が深すぎます',
  'runtime-timeout':        'タイムアウトしました',
  'unsupported-operator':   'サポートされていない演算子です',
  'imcomparable':           '両者は直接比較できません',
  'mismatch-argument':      '引数の数が合いません',
  'not-negative-number':    '負の数は使えません',
  'float-conversion':       '小数への変換エラーです',
  'internal-error':         '内部エラーです',
  'append-immutable':       '変更できません',
  'array-format':           '配列フォーマットエラーです',
  'assertion-failed':       'テストを失敗',
};

/**
 * 先頭キーを ERROR_MESSAGES で置き換えて表示用文字列を返す。
 * messages は配列・タプル相当 (空配列なら空文字列)。
 */
export function formatMessages(messages) {
  if (!messages || messages.length === 0) {
    return '';
  }
  const key = messages[0];
  const display = Object.prototype.hasOwnProperty.call(ERROR_MESSAGES, key)
    ? ERROR_MESSAGES[key]
    : key;
  const rest = messages.slice(1).join(' ');
  if (rest) {
    return `${display} ${rest}`.trim();
  }
  return display;
}

/**
 * 非絵文字の連続する文字列を '-' で結合する。
 * 絵文字 (codepoint > 127) で始まる文字列は独立要素として残す。
 *
 * Python 側は `ord(msg[0]) > 127` で判定。JS では codePointAt(0) を使う。
 * これによりサロゲートペアの絵文字 (U+1F4A3 など) も正しく検出できる。
 */
export function normalizeMessages(messages) {
  if (typeof messages === 'string') {
    messages = [messages];
  }
  if (!Array.isArray(messages)) {
    // Python の tuple 相当としてイテラブルを許容
    messages = Array.from(messages);
  }
  const result = [];
  let parts = [];
  for (const msg of messages) {
    if (msg && msg.length > 0 && msg.codePointAt(0) > 127) {
      if (parts.length > 0) {
        result.push(parts.join('-'));
        parts = [];
      }
      result.push(msg);
    } else {
      parts.push(msg);
    }
  }
  if (parts.length > 0) {
    result.push(parts.join('-'));
  }
  return Object.freeze(result);
}

/**
 * Yui 言語のエラーを表現するクラス。
 * Python 版は RuntimeError を継承。JS では Error を継承する。
 *
 * - messages: 凍結された配列。先頭はエラーキー、以降は補足情報。
 * - errorNode: AST ノード (pos プロパティを持つもの) または null。
 *              循環 import を避けるため duck-type 判定する。
 * - BK: バックトラック用フラグ (パーサが内部で使う)。
 */
export class YuiError extends Error {
  constructor(messages, errorNode = null, BK = false) {
    const normalized = normalizeMessages(messages);
    super(normalized.join(' '));
    this.name = 'YuiError';
    this.messages = normalized;
    // pos プロパティを持つときだけ AST node とみなす
    this.errorNode =
      errorNode != null && typeof errorNode === 'object' && 'pos' in errorNode
        ? errorNode
        : null;
    this.BK = BK;
  }

  /** メッセージを末尾に追加する。配列を再凍結。 */
  addMessage(message) {
    this.messages = Object.freeze([...this.messages, message]);
  }

  /** エラー箇所の行番号 (1始まり)。AST node がない場合は 0。 */
  get lineno() {
    if (this.errorNode) {
      const [line] = this.errorNode.extract();
      return line;
    }
    return 0;
  }

  /** エラー箇所の列番号 (1始まり)。AST node がない場合は 0。 */
  get offset() {
    if (this.errorNode) {
      const [, offset] = this.errorNode.extract();
      return offset;
    }
    return 0;
  }

  /** エラー箇所のコードスニペット。 */
  get text() {
    if (this.errorNode) {
      const [, , snippet] = this.errorNode.extract();
      return snippet;
    }
    return '';
  }

  /**
   * 構文エラーとして整形したメッセージを返す。
   * ランタイムエラーは YuiRuntime.formatError() を使うこと。
   */
  formattedMessage(prefix = ' ', marker = '^', lineoffset = 0) {
    let message = formatMessages(this.messages);
    if (this.errorNode) {
      const [line, col, rawSnippet] = this.errorNode.extract();
      const span =
        this.errorNode.endPos != null
          ? Math.max(this.errorNode.endPos - this.errorNode.pos, 3)
          : 3;
      const pointerLen = Math.min(span, 16);
      const pointer = marker.repeat(pointerLen);
      const snippet = rawSnippet.split('\n')[0];
      const indent = ' '.repeat(col - 1);
      message =
        `${message} line ${line + lineoffset}, column ${col}:\n` +
        `${prefix}${snippet}\n` +
        `${prefix}${indent}${pointer}`;
    }
    return `[構文エラー/SyntaxError] ${message}`;
  }
}
