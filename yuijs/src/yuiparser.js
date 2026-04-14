// yuiparser.js — Packrat パーサ (parser combinator)
// Python 版 yuichan/yuiparser.py の移植
//
// 依存: yuiast.js, yuierror.js, yuisyntax.js
//
// JS ⇔ Python 主な差分:
// - Python `Source(YuiSyntax)` をそのまま `class Source extends YuiSyntax` で移植。
// - Python のメソッド名末尾 '_' は JS では取り除いて camelCase にする
//   (is_ → is / match_ → match / require_ → require)。
//   JS では `is`/`match`/`require` はいずれも予約語ではないので安全。
// - 正規表現は yuisyntax.getPattern() が sticky ('y') フラグ付きで返すので
//   `regex.lastIndex = pos; regex.exec(source)` が Python の pattern.match(s, pos) に対応する。
// - Python の `pattern.search(s, pos)` は JS の sticky では代替できないので、
//   _getSearchPattern() で global ('g') フラグ版を別途キャッシュする。
// - Python `re.findall` は JS `matchAll` で代替 (special-name 抽出)。
// - NONTERMINALS は module-level の plain object として共有する (Python と同じ)。

import {
  ConstNode,
  NameNode,
  StringNode,
  NumberNode,
  ArrayNode,
  ObjectNode,
  MinusNode,
  ArrayLenNode,
  FuncAppNode,
  GetIndexNode,
  BinaryNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  PrintExpressionNode,
  PassNode,
  IfNode,
  BreakNode,
  RepeatNode,
  FuncDefNode,
  ReturnNode,
  AssertNode,
  CatchNode,
  ImportNode,
  ASTNode,
} from './yuiast.js';

import { YuiError, vprint } from './yuierror.js';
import { YuiSyntax, loadSyntax } from './yuisyntax.js';

// ─────────────────────────────────────────────
// SourceNode — `null値` を表すプレースホルダノード
// ─────────────────────────────────────────────
// Python 側は `class SourceNode(ASTNode): pass`。`source.p()` の初期値として使う。
export class SourceNode extends ASTNode {}

// ─────────────────────────────────────────────
// 特殊名 (special-name) 抽出用ユーティリティ
// ─────────────────────────────────────────────

/**
 * ASCII 英数字とアンダースコアのみで構成される名前は
 * 通常の identifier として処理できるため、special-name にはしない。
 * Python: _is_special_name と同じ。
 */
const _ASCII_IDENTIFIER_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;
function _isAsciiIdentifier(s) {
  return _ASCII_IDENTIFIER_RE.test(s);
}

// ─────────────────────────────────────────────
// Source — 構文解析コンテキスト
// ─────────────────────────────────────────────

export class Source extends YuiSyntax {
  /**
   * @param {string} source  ソースコード文字列
   * @param {object} [opts]
   * @param {string} [opts.filename='main.yui']
   * @param {number} [opts.pos=0]
   * @param {string|object} [opts.syntax='yui']  syntax 名または既にロード済みの terminals dict
   */
  constructor(source, opts = {}) {
    const { filename = 'main.yui', pos = 0, syntax = 'yui' } = opts;
    const terminals = typeof syntax === 'string' ? loadSyntax(syntax) : syntax;
    super(terminals);
    this.filename = filename;
    this.source = source;
    this.pos = pos;
    this.length = source.length;
    this.specialNames = [];
    this.currentIndent = '';
    this.memos = new Map();
    // パーサ中の last-match 情報 (Python の self.matched_string / self.matched_suffix 相当)
    this.matchedString = '';
    this.matchedSuffix = null;
    // consume_until 用の global regex キャッシュ
    this._searchRegexes = new Map();
    // 行頭の名前も拾うため、先頭に \n を付けて抽出する (Python と同じ)
    this.extractSpecialNames('\n' + source);
  }

  hasNext() {
    return this.pos < this.length;
  }

  isEos() {
    return this.pos >= this.length;
  }

  consumeString(text) {
    if (this.source.startsWith(text, this.pos)) {
      this.pos += text.length;
      return true;
    }
    return false;
  }

  /**
   * 現在位置で terminal にマッチするなら消費する。
   * Python: match_(terminal, if_undefined, unconsumed, start_pos, check_typo)
   */
  match(terminal, opts = {}) {
    const {
      ifUndefined = false,
      unconsumed = false,
      startPos = null,
      checkTypo = true,
    } = opts;
    if (!this.isDefined(terminal)) {
      if (startPos !== null) {
        this.pos = startPos;
      }
      return ifUndefined;
    }
    const savedPos = startPos === null ? this.pos : startPos;
    if (checkTypo && this.isDefined(`!${terminal}`)) {
      const typoRe = this.getPattern(`!${terminal}`);
      typoRe.lastIndex = this.pos;
      const typoMatch = typoRe.exec(this.source);
      if (typoMatch && typoMatch.index === this.pos) {
        const matched = this.source.slice(this.pos, this.pos + typoMatch[0].length);
        const expected = this.forExample(terminal);
        throw new YuiError(
          ['typo', `❌\`${matched}\``, `✅${expected}`, `🧬${terminal}`],
          this.p(null, null, null, matched.length),
        );
      }
    }
    const pattern = this.getPattern(terminal);
    pattern.lastIndex = this.pos;
    const m = pattern.exec(this.source);
    if (m && m.index === this.pos) {
      this.matchedString = m[0];
      if (unconsumed) {
        this.pos = savedPos;
        return true;
      }
      this.pos = this.pos + m[0].length;
      return true;
    }
    this.matchedString = '';
    this.pos = savedPos;
    return false;
  }

  /** global ('g') フラグ付きの正規表現をキャッシュして返す。consume_until 用。 */
  _getSearchPattern(terminal) {
    let re = this._searchRegexes.get(terminal);
    if (re) return re;
    const src = this.get(terminal);
    if (src === '') return null;
    re = new RegExp(src, 'g');
    this._searchRegexes.set(terminal, re);
    return re;
  }

  consumeUntil(terminal, opts = {}) {
    const { untilEof = true, disallowString = null } = opts;
    const re = this._getSearchPattern(terminal);
    if (re) {
      re.lastIndex = this.pos;
      const m = re.exec(this.source);
      if (m) {
        const matchStart = m.index;
        if (disallowString) {
          if (this.source.slice(this.pos, matchStart).includes(disallowString)) {
            return false;
          }
        }
        this.pos = matchStart;
        return true;
      }
    }
    if (untilEof) {
      this.pos = this.length;
      return true;
    }
    return false;
  }

  skipWhitespacesAndComments({ includeLinefeed = false } = {}) {
    while (this.hasNext()) {
      if (this.match('whitespace', { checkTypo: false })) continue;
      if (includeLinefeed && this.match('linefeed', { checkTypo: false })) continue;
      if (this.match('line-comment-begin')) {
        this.consumeUntil('linefeed', { untilEof: true });
        continue;
      }
      if (this.match('comment-begin')) {
        const openingPos = this.pos - this.matchedString.length;
        this.consumeUntil('comment-end', { untilEof: true });
        this.require('comment-end', { lskipWs: false, openingPos });
        continue;
      }
      break;
    }
  }

  isEosOrLinefeed({ lskipWs = true, unconsumed = false } = {}) {
    const savedPos = this.pos;
    if (lskipWs) {
      this.skipWhitespacesAndComments({ includeLinefeed: false });
    }
    if (this.isEos()) {
      if (unconsumed) {
        this.pos = savedPos;
      }
      return true;
    }
    return this.is('linefeed', {
      lskipWs: false,
      lskipLf: false,
      unconsumed,
    });
  }

  /**
   * 現在位置で terminal にマッチするかをチェック (ws スキップを含む)。
   * Python: is_(terminal, suffixes, if_undefined, unconsumed, lskip_ws, lskip_lf)
   */
  is(terminal, opts = {}) {
    const {
      suffixes = null,
      ifUndefined = false,
      unconsumed = false,
      lskipWs = true,
      lskipLf = false,
    } = opts;
    const startPos = this.pos;
    if (lskipWs || lskipLf) {
      this.skipWhitespacesAndComments({ includeLinefeed: lskipLf });
    }
    if (suffixes !== null) {
      this.matchedSuffix = null;
      const savedPos = this.pos;
      for (const suffix of suffixes) {
        const key = `${terminal}${suffix}`;
        if (this.match(key, { unconsumed, startPos })) {
          this.matchedSuffix = suffix;
          return true;
        }
        this.pos = savedPos;
      }
      this.pos = startPos;
      return false;
    }
    if (terminal.includes('|')) {
      for (const option of terminal.split('|')) {
        if (this.match(option, { ifUndefined, unconsumed, startPos })) {
          return true;
        }
      }
      this.pos = startPos;
      return false;
    }
    return this.match(terminal, { ifUndefined, unconsumed, startPos });
  }

  /**
   * 現在位置で terminal にマッチすることを要求する。失敗したら YuiError を投げる。
   * Python: require_(terminal, suffixes, if_undefined=True, unconsumed, lskip_ws, lskip_lf, opening_pos, BK)
   */
  require(terminal, opts = {}) {
    const {
      suffixes = null,
      ifUndefined = true,
      unconsumed = false,
      lskipWs = true,
      lskipLf = false,
      openingPos = null,
      BK = false,
    } = opts;
    if (!this.isDefined(terminal)) {
      return;
    }
    if (this.is(terminal, { suffixes, ifUndefined, unconsumed, lskipWs, lskipLf })) {
      return;
    }
    const expectedToken = this.forExample(terminal);
    if (openingPos !== null) {
      throw new YuiError(
        ['expected-closing', `✅\`${expectedToken}\``, `🧬${terminal}`],
        this.p(null, openingPos),
      );
    }
    const snippet = this.captureLine();
    throw new YuiError(
      ['expected-token', `❌\`${snippet}\``, `✅\`${expectedToken}\``, `🧬${terminal}`],
      this.p(null, null, null, 1),
      BK,
    );
  }

  save() {
    return [this.pos, this.currentIndent];
  }

  backtrack(saved) {
    this.pos = saved[0];
    this.currentIndent = saved[1];
  }

  getMemo(nonterminal, pos) {
    const key = `${nonterminal}\u0000${pos}`;
    return this.memos.get(key) ?? null;
  }

  setMemo(nonterminal, pos, result, newPos) {
    const key = `${nonterminal}\u0000${pos}`;
    this.memos.set(key, [result, newPos]);
  }

  /**
   * nonterminal をパースする。Packrat parsing のメモ化あり。
   * Python: parse(nonterminal, lskip_ws, lskip_lf, BK)
   */
  parse(nonterminal, opts = {}) {
    const { lskipWs = true, lskipLf = false, BK = false } = opts;
    const patterns = NONTERMINALS[nonterminal];
    if (patterns === undefined) {
      throw new Error(`Unknown nonterminal: ${nonterminal}`);
    }
    if (lskipWs || lskipLf) {
      this.skipWhitespacesAndComments({ includeLinefeed: lskipLf });
    }

    const memo = this.getMemo(nonterminal, this.pos);
    if (memo !== null) {
      this.pos = memo[1];
      return memo[0];
    }

    const saved = this.save();
    const savedPos = this.pos;
    try {
      const result = patterns.match(this);
      this.setMemo(nonterminal, savedPos, result, this.pos);
      return result;
    } catch (e) {
      if (e instanceof YuiError) {
        if (e.BK === true && BK === false) {
          this.backtrack(saved);
          const snippet = this.captureLine();
          throw new YuiError(
            [`expected-${nonterminal.slice(1).toLowerCase()}`, `❌${snippet}`, `⚠️${e.message}`],
            this.p(null, null, null, 1),
          );
        }
      }
      throw e;
    }
  }

  canBacktrack(lookahead) {
    if (this.isDefined(lookahead)) {
      const captured = this.captureLine();
      // lookahead を current line から検索する (sticky ではなく普通の検索)
      const src = this.get(lookahead);
      try {
        const re = new RegExp(src);
        return !re.test(captured);
      } catch {
        return true;
      }
    }
    return true;
  }

  /**
   * 変数定義形 `name =` や 関数呼び出し形 `name(` から special-name を抽出する。
   * Python: extract_special_names
   */
  extractSpecialNames(text) {
    let names;
    if (this.isDefined('special-names')) {
      names = (this.terminals['special-names'] || '').split('|');
    } else {
      names = [];
    }

    const namePattern =
      this.terminals['special-name-pattern'] ||
      '[^\\s\\[\\]\\(\\)",\\.+*/%=!<>-]+';

    // コメントを除去してから抽出する (コメント内の `name(` / `name =` に惑わされないため)
    const textForExtraction = this._stripCommentsForExtraction(text);

    // 1. 変数定義のパターン (例: `name =`, ただし `==` は除外)
    const varPatternRaw =
      this.terminals['special-name-variable'] ||
      '(?:^|\\n)\\s*({name_pattern})\\s*=(?!=)';
    const varPattern = varPatternRaw.replace('{name_pattern}', namePattern);

    const varRe = new RegExp(varPattern, 'g');
    for (const m of textForExtraction.matchAll(varRe)) {
      if (m[1] !== undefined) names.push(m[1]);
    }

    // 2. 関数名のパターン (例: `name(`)
    const funcPatternRaw =
      this.terminals['special-name-funcname'] ||
      '({name_pattern})\\s*[\\(]';
    const funcPattern = funcPatternRaw.replace('{name_pattern}', namePattern);

    const funcRe = new RegExp(funcPattern, 'g');
    for (const m of textForExtraction.matchAll(funcRe)) {
      if (m[1] !== undefined) names.push(m[1]);
    }

    // 3. キーワードが接頭辞として貼り付いた名前 (例: `もし剰余(` → `剰余` も登録) を救済
    const excludePrefix = this.terminals['special-name-exclude-prefix'] || '';
    if (excludePrefix) {
      const prefixRe = new RegExp(`^(?:${excludePrefix})`);
      const expanded = [];
      for (const name of names) {
        let stripped = name;
        while (true) {
          const m = prefixRe.exec(stripped);
          if (!m || m[0].length === 0 || m[0].length === stripped.length) break;
          stripped = stripped.slice(m[0].length);
        }
        if (stripped !== name && stripped) expanded.push(stripped);
      }
      names.push(...expanded);
    }

    // ASCII 識別子は普通に name-first-char でパースできるので除外。
    // 重複も除去する。
    const uniq = new Set();
    for (const n of names) {
      const trimmed = n.trim();
      if (trimmed === '') continue;
      if (_isAsciiIdentifier(trimmed)) continue;
      uniq.add(trimmed);
    }
    // 長い名前優先 (prefix マッチでの衝突回避)
    this.specialNames = [...uniq].sort((a, b) => b.length - a.length);
    vprint(`@extracted special names: ${JSON.stringify(this.specialNames)}`);
  }

  _stripCommentsForExtraction(text) {
    let result = text;
    const lineComment = this.terminals['line-comment-begin'] || '';
    if (lineComment) {
      const lineRe = new RegExp(`(?:${lineComment}).*?(?=\\n|$)`, 'g');
      result = result.replace(lineRe, (m) => ' '.repeat(m.length));
    }
    const commentBegin = this.terminals['comment-begin'] || '';
    const commentEnd = this.terminals['comment-end'] || '';
    if (commentBegin && commentEnd) {
      const blockRe = new RegExp(`(?:${commentBegin})[\\s\\S]*?(?:${commentEnd})`, 'g');
      result = result.replace(blockRe, (m) => ' '.repeat(m.length));
    }
    return result;
  }

  matchSpecialName({ unconsumed = false } = {}) {
    for (const name of this.specialNames) {
      if (this.source.startsWith(name, this.pos)) {
        if (!unconsumed) {
          this.pos += name.length;
        }
        return name;
      }
    }
    return null;
  }

  captureIndent(indentChars = ' \t\u3000') {
    let startPos = this.pos - 1;
    while (startPos >= 0) {
      const char = this.source[startPos];
      if (char === '\n') {
        startPos += 1;
        break;
      }
      startPos -= 1;
    }
    if (startPos < 0) startPos = 0;
    let endPos = startPos;
    while (endPos < this.length) {
      const char = this.source[endPos];
      if (indentChars.includes(char)) {
        endPos += 1;
      } else {
        break;
      }
    }
    return this.source.slice(startPos, endPos);
  }

  captureLine() {
    const startPos = this.pos;
    while (this.pos < this.length) {
      if (
        this.is('linefeed|line-comment-begin|comment-begin|statement-separator|block-begin', {
          lskipWs: false,
          unconsumed: true,
        })
      ) {
        const captured = this.source.slice(startPos, this.pos);
        this.pos = startPos;
        return captured;
      }
      this.pos += 1;
    }
    this.pos = startPos;
    // EOF に到達 — 最初の改行までを返す
    return this.source.slice(startPos).split('\n')[0];
  }

  captureComment() {
    const savePos = this.pos;
    let comment = null;
    if (this.is('line-comment-begin')) {
      const startPos = this.pos;
      this.consumeUntil('linefeed', { untilEof: true });
      comment = this.source.slice(startPos, this.pos);
    }
    if (this.is('comment-begin')) {
      const startPos = this.pos;
      this.consumeUntil('comment-end', { untilEof: true });
      comment = this.source.slice(startPos, this.pos);
    }
    this.pos = savePos;
    return comment;
  }

  /**
   * ASTNode に filename / source / pos / end_pos を書き込んで返す。
   * node 省略時は SourceNode を作る。
   *
   * Python: p(node=None, start_pos=None, end_pos=None, length=0)
   * JS 側は option オブジェクトだとパーサ本体の呼び出しが冗長になりすぎるので
   * 位置引数を Python と同じ順で受ける (後方 3 つが任意)。
   */
  p(node = null, startPos = null, endPos = null, length = 0) {
    const n = node || new SourceNode();
    n.filename = this.filename;
    n.source = this.source;

    const savePos = this.pos;
    if (startPos !== null) {
      n.pos = startPos;
      if (endPos !== null && endPos !== undefined) {
        n.end_pos = endPos;
      } else if (length !== 0) {
        n.end_pos = Math.min(startPos + length, this.length);
      } else {
        n.end_pos = savePos;
      }
    } else if (length !== 0) {
      n.pos = this.pos;
      n.end_pos = Math.min(this.pos + length, this.length);
    } else {
      n.pos = Math.max(this.pos - 1, 0);
      n.end_pos = this.pos;
    }
    return n;
  }

  printDebug(message) {
    const node = this.p(null, this.pos);
    const [linenum, col, line] = node.extract();
    console.log(`@debug ${message} at pos=${this.pos} line=${linenum} col=${col}`);
    console.log(`${line}\n${' '.repeat(col - 1)}^`);
  }
}

// ─────────────────────────────────────────────
// NONTERMINALS — パーサーコンビネータ登録テーブル
// ─────────────────────────────────────────────

export const NONTERMINALS = {};

class ParserCombinator {
  // eslint-disable-next-line no-unused-vars
  quickCheck(_source) {
    return true;
  }
  // eslint-disable-next-line no-unused-vars
  match(_source) {
    return true;
  }
}

// ─────────────────────────────────────────────
// リテラル: Const / Number / String / Array / Object / Name
// ─────────────────────────────────────────────

class ConstParser extends ParserCombinator {
  quickCheck(source) {
    return source.is('null|boolean-true|boolean-false');
  }
  match(source) {
    const savedPos = source.pos;
    if (source.is('null')) {
      return source.p(new ConstNode(null), savedPos);
    }
    if (source.is('boolean-true')) {
      return source.p(new ConstNode(true), savedPos);
    }
    if (source.is('boolean-false')) {
      return source.p(new ConstNode(false), savedPos);
    }
    throw new YuiError(['expected-boolean'], source.p(null, null, null, 1), true);
  }
}
NONTERMINALS['@Boolean'] = new ConstParser();

class NumberParser extends ParserCombinator {
  quickCheck(source) {
    if (source.matchSpecialName({ unconsumed: true }) !== null) {
      return false;
    }
    return source.is('number-first-char', { unconsumed: true });
  }
  match(source) {
    const startPos = source.pos;
    if (source.is('number-first-char')) {
      source.require('number-chars', { lskipWs: false });
      if (source.is('number-dot-char', { lskipWs: false })) {
        source.is('number-chars', { lskipWs: false });
        const number = source.source.slice(startPos, source.pos);
        return source.p(new NumberNode(parseFloat(number)), startPos);
      }
      const number = source.source.slice(startPos, source.pos);
      return source.p(new NumberNode(parseInt(number, 10)), startPos);
    }
    throw new YuiError(['expected-number'], source.p(null, null, null, 1), true);
  }
}
NONTERMINALS['@Number'] = new NumberParser();

const _ESCAPED_STRING = {
  n: '\n',
  t: '\t',
};

class StringParser extends ParserCombinator {
  quickCheck(source) {
    return source.is('string-begin', { unconsumed: true });
  }
  match(source) {
    const openingQuotePos = source.pos;
    if (source.is('string-begin')) {
      let openingPos = source.pos;
      const stringContent = [];
      let expressionCount = 0;
      while (source.pos < source.length) {
        source.consumeUntil('string-content-end', { untilEof: true });
        stringContent.push(source.source.slice(openingPos, source.pos));
        if (source.is('string-end', { unconsumed: true })) {
          break;
        }
        if (source.is('string-escape')) {
          if (source.isEos()) {
            throw new YuiError(['wrong-escape-sequence'], source.p(null, null, null, 1));
          }
          const nextChar = source.source[source.pos];
          source.pos += 1;
          stringContent.push(_ESCAPED_STRING[nextChar] ?? nextChar);
          openingPos = source.pos;
          continue;
        }
        const startInterPos = source.pos;
        if (source.is('string-interpolation-begin', { lskipWs: false })) {
          const expression = source.parse('@Expression');
          source.require('string-interpolation-end', { openingPos: startInterPos });
          stringContent.push(expression);
          expressionCount += 1;
          openingPos = source.pos;
          continue;
        }
      }
      source.require('string-end', { lskipWs: false, openingPos: openingQuotePos });
      const contents = expressionCount === 0 ? stringContent.join('') : stringContent;
      return source.p(new StringNode(contents), openingQuotePos);
    }
    throw new YuiError(['expected-string'], source.p(null, null, null, 1), true);
  }
}
NONTERMINALS['@String'] = new StringParser();

class ArrayParser extends ParserCombinator {
  quickCheck(source) {
    return source.is('array-begin', { unconsumed: true });
  }
  match(source) {
    const openingPos = source.pos;
    if (source.is('array-begin')) {
      const args = [];
      while (!source.is('array-end', { lskipLf: true, unconsumed: true })) {
        args.push(source.parse('@Expression', { lskipLf: true }));
        if (source.is('array-separator', { lskipLf: true })) {
          continue;
        }
      }
      source.require('array-end', { lskipLf: true, openingPos });
      return source.p(new ArrayNode(args), openingPos);
    }
    throw new YuiError(['expected-array'], source.p(null, null, null, 1), true);
  }
}
NONTERMINALS['@Array'] = new ArrayParser();

class ObjectParser extends ParserCombinator {
  quickCheck(source) {
    return source.is('object-begin', { unconsumed: true });
  }
  match(source) {
    const openingPos = source.pos;
    if (source.is('object-begin', { lskipLf: true })) {
      const args = [];
      while (!source.is('object-end', { lskipLf: true, unconsumed: true })) {
        args.push(source.parse('@String', { lskipLf: true }));
        source.require('key-value-separator', { lskipLf: true });
        args.push(source.parse('@Expression', { lskipLf: true }));
        if (source.is('object-separator', { lskipLf: true })) {
          continue;
        }
      }
      source.require('object-end', { lskipLf: true, openingPos });
      return source.p(new ObjectNode(args), openingPos);
    }
    throw new YuiError(['expected-object'], source.p(null, null, null, 1), true);
  }
}
NONTERMINALS['@Object'] = new ObjectParser();

class NameParser extends ParserCombinator {
  match(source) {
    let startPos = source.pos;
    if (source.is('keywords')) {
      const matchedKeyword = source.matchedString;
      const savedPos = source.pos;
      source.is('name-chars', { lskipWs: false });
      if (source.pos === savedPos) {
        // continuation なし → キーワード確定
        throw new YuiError(
          ['keyword-name', `❌\`${matchedKeyword}\``],
          source.p(null, startPos),
          true,
        );
      }
      source.pos = startPos;
    }
    const specialName = source.matchSpecialName();
    if (specialName !== null) {
      return source.p(new NameNode(specialName), source.pos - specialName.length);
    }
    if (source.is('extra-name-begin')) {
      startPos = source.pos;
      source.consumeUntil('extra-name-end', { disallowString: '\n' });
      const name = source.source.slice(startPos, source.pos);
      const node = source.p(new NameNode(name), startPos);
      source.require('extra-name-end', { openingPos: startPos - 1 });
      return node;
    }
    startPos = source.pos;
    if (source.is('name-first-char')) {
      source.require('name-chars', { lskipWs: false });
      source.require('name-last-char', { lskipWs: false });
      const name = source.source.slice(startPos, source.pos);
      return source.p(new NameNode(name), startPos);
    }
    const snippet = source.captureLine().trim();
    throw new YuiError(
      ['wrong-name', `❌${snippet}`],
      source.p(null, null, null, 1),
      true,
    );
  }
}
NONTERMINALS['@Name'] = new NameParser();

const LITERALS = ['@Number', '@String', '@Array', '@Object', '@Boolean'];

// ─────────────────────────────────────────────
// Term / Primary / 二項演算
// ─────────────────────────────────────────────

class TermParser extends ParserCombinator {
  match(source) {
    const openingPos = source.pos;
    if (source.is('array-indexer-begin')) {
      const expression = source.parse('@Expression');
      source.require('array-indexer-infix');
      const index = source.parse('@Expression');
      source.require('array-indexer-end', { openingPos });
      const orderPolicy = source.get('array-indexer-order');
      return source.p(new GetIndexNode(expression, index, orderPolicy), openingPos);
    }
    if (source.is('minus-begin')) {
      const expression = source.parse('@Expression', { BK: false });
      if (source.is('minus-end')) {
        return source.p(new MinusNode(expression), openingPos);
      }
      source.pos = openingPos;
    }
    if (source.is('length-begin')) {
      const expressionNode = source.parse('@Expression');
      source.require('length-end', { openingPos });
      return source.p(new ArrayLenNode(expressionNode), openingPos);
    }
    if (source.is('catch-begin')) {
      const catchOpening = source.pos - source.matchedString.length;
      const expression = source.parse('@Expression', { BK: false });
      source.require('catch-end', { openingPos: catchOpening });
      return source.p(new CatchNode(expression), catchOpening);
    }
    if (source.is('grouping-begin')) {
      const expressionNode = source.parse('@Expression');
      source.require('grouping-end', { openingPos });
      return source.p(new PrintExpressionNode(expressionNode, false, true), openingPos);
    }
    if (source.isDefined('binary-infix-prefix-begin')) {
      if (
        source.is('binary-infix-prefix', {
          suffixes: ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>', 'in', 'notin'],
        })
      ) {
        const operator = source.matchedSuffix;
        const leftNode = source.parse('@Expression', { BK: false });
        const rightNode = source.parse('@Expression', { BK: false });
        source.require('binary-infix-prefix-end');
        return source.p(new BinaryNode(operator, leftNode, rightNode), openingPos);
      }
    }
    // funcapp-begin (prefix-style function application, e.g. wenyan)
    {
      const saved = source.save();
      try {
        if (source.is('funcapp-begin')) {
          const name = source.parse('@Name', { BK: true });
          const args = [];
          if (source.is('funcapp-args-begin')) {
            while (!source.is('funcapp-args-end', { unconsumed: true })) {
              args.push(source.parse('@Expression', { lskipLf: true }));
              if (source.is('funcapp-separator')) {
                continue;
              }
              break;
            }
            source.require('funcapp-args-end', { openingPos });
          } else if (source.is('funcapp-noarg')) {
            // 引数なし (例: 以虛)
          } else {
            while (!source.is('funcapp-end', { unconsumed: true })) {
              source.require('funcapp-separator');
              const expression = source.parse('@Expression', { BK: false });
              args.push(expression);
            }
            source.require('funcapp-end');
          }
          return source.p(new FuncAppNode(name, args), openingPos);
        }
      } catch (e) {
        if (!(e instanceof YuiError)) throw e;
        source.backtrack(saved);
      }
    }

    for (const literal of LITERALS) {
      if (NONTERMINALS[literal].quickCheck(source)) {
        source.pos = openingPos;
        return source.parse(literal, { BK: true });
      }
    }
    return source.parse('@Name', { BK: true });
  }
}
NONTERMINALS['@Term'] = new TermParser();

class PrimaryParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    if (source.is('unary-minus')) {
      return source.p(new MinusNode(source.parse('@Primary')), startPos);
    }
    if (source.is('unary-length')) {
      return source.p(new ArrayLenNode(source.parse('@Primary')), startPos);
    }
    if (source.is('unary-inspect')) {
      const node = source.parse('@Primary');
      return source.p(new PrintExpressionNode(node, true), startPos);
    }
    let node = source.parse('@Term', { BK: true });
    while (source.hasNext()) {
      const openingPos = source.pos;
      if (source.is('funcapp-noarg')) {
        node = source.p(new FuncAppNode(node, []), startPos);
        continue;
      }
      if (source.is('funcapp-args-begin')) {
        const args = [];
        while (!source.is('funcapp-args-end', { unconsumed: true })) {
          args.push(source.parse('@Expression', { lskipLf: true }));
          if (source.is('funcapp-separator')) {
            continue;
          }
          break;
        }
        source.require('funcapp-args-end', { openingPos });
        node = source.p(new FuncAppNode(node, args), startPos);
        continue;
      }
      if (source.is('array-indexer-suffix')) {
        const indexNode = source.parse('@Expression');
        source.require('array-indexer-end', { openingPos });
        node = source.p(new GetIndexNode(node, indexNode), startPos);
        continue;
      }
      if (source.is('property-length')) {
        node = source.p(new ArrayLenNode(node), startPos);
        continue;
      }
      break;
    }
    return node;
  }
}
NONTERMINALS['@Primary'] = new PrimaryParser();

class MultiplicativeParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    let leftNode = source.parse('@Primary', { BK: true });
    let saved = source.save();
    try {
      while (source.is('binary-infix', { suffixes: ['*', '/', '%'] })) {
        const operator = source.matchedSuffix;
        const rightNode = source.parse('@Primary');
        leftNode = source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
        saved = source.save();
      }
    } catch (e) {
      if (!(e instanceof YuiError)) throw e;
    }
    source.backtrack(saved);
    return leftNode;
  }
}
NONTERMINALS['@Multiplicative'] = new MultiplicativeParser();

class AdditiveParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    let leftNode = source.parse('@Multiplicative', { BK: true });
    let saved = source.save();
    try {
      while (source.is('binary-infix', { suffixes: ['+', '-'] })) {
        const operator = source.matchedSuffix;
        const rightNode = source.parse('@Multiplicative');
        leftNode = source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
        saved = source.save();
      }
    } catch (e) {
      if (!(e instanceof YuiError)) throw e;
    }
    source.backtrack(saved);
    return leftNode;
  }
}
NONTERMINALS['@Additive'] = new AdditiveParser();

class ComparativeParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    const leftNode = source.parse('@Additive', { BK: true });
    const saved = source.save();
    try {
      if (
        source.is('binary-infix', {
          suffixes: ['==', '!=', '<=', '>=', '<', '>', 'in', 'notin'],
        })
      ) {
        const operator = source.matchedSuffix;
        const rightNode = source.parse('@Additive');
        return source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
      }
    } catch (e) {
      if (!(e instanceof YuiError)) throw e;
    }
    source.backtrack(saved);
    return leftNode;
  }
}
NONTERMINALS['@Expression'] = new ComparativeParser();

// ─────────────────────────────────────────────
// Statement
// ─────────────────────────────────────────────

class AssignmentParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('assignment-lookahead');
    const startPos = source.pos;
    source.require('assignment-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const leftNode = source.parse('@Expression', { BK });
    source.require('assignment-infix', { BK });
    const rightNode = source.parse('@Expression', { BK });
    source.require('assignment-end', { BK });
    const orderPolicy = source.get('assignment-order');
    return source.p(new AssignmentNode(leftNode, rightNode, orderPolicy), startPos);
  }
}
NONTERMINALS['@Assignment'] = new AssignmentParser();

class IncrementParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('increment-lookahead');
    const startPos = source.pos;
    source.require('increment-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const lvalueNode = source.parse('@Expression', { BK });
    source.require('increment-end', { BK });
    return source.p(new IncrementNode(lvalueNode), startPos);
  }
}
NONTERMINALS['@Increment'] = new IncrementParser();

class DecrementParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('decrement-lookahead');
    const startPos = source.pos;
    source.require('decrement-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const lvalueNode = source.parse('@Expression', { BK });
    source.require('decrement-end', { BK });
    return source.p(new DecrementNode(lvalueNode), startPos);
  }
}
NONTERMINALS['@Decrement'] = new DecrementParser();

class AppendParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('append-lookahead');
    const startPos = source.pos;
    source.require('append-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const lvalueNode = source.parse('@Expression', { BK });
    source.require('append-infix', { BK });
    const value = source.parse('@Expression', { BK });
    source.require('append-end', { BK });
    const orderPolicy = source.get('append-order');
    return source.p(new AppendNode(lvalueNode, value, orderPolicy), startPos);
  }
}
NONTERMINALS['@Append'] = new AppendParser();

class BreakParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    source.require('break', { BK: true });
    return source.p(new BreakNode(), startPos);
  }
}
NONTERMINALS['@Break'] = new BreakParser();

class ImportParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    source.require('import-standard', { BK: true });
    return source.p(new ImportNode(), startPos);
  }
}
NONTERMINALS['@Import'] = new ImportParser();

class PassParser extends ParserCombinator {
  match(source) {
    if (!source.isDefined('pass')) {
      throw new YuiError(['pass-not-defined'], source.p(null, null, null, 1), true);
    }
    const startPos = source.pos;
    source.require('pass', { BK: true });
    return source.p(new PassNode(), startPos);
  }
}
NONTERMINALS['@Pass'] = new PassParser();

class ReturnParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('return-lookahead');
    const startPos = source.pos;
    source.require('return-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const exprNode = source.parse('@Expression', { BK });
    source.require('return-end', { BK });
    return source.p(new ReturnNode(exprNode), startPos);
  }
}
NONTERMINALS['@Return'] = new ReturnParser();

class PrintExpressionParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('print-lookahead');
    const startPos = source.pos;
    source.require('print-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const exprNode = source.parse('@Expression', { BK });
    source.require('print-end', { BK });
    return source.p(new PrintExpressionNode(exprNode), startPos);
  }
}
NONTERMINALS['@PrintExpression'] = new PrintExpressionParser();

class RepeatParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('repeat-lookahead');
    const startPos = source.pos;
    source.require('repeat-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const timesNode = source.parse('@Expression', { BK });
    source.require('repeat-times', { BK });
    source.require('repeat-block', { BK });
    const blockNode = source.parse('@Block');
    source.require('repeat-end', { lskipLf: true, BK: false });
    const orderPolicy = source.get('repeat-order');
    return source.p(
      new RepeatNode(timesNode, blockNode, orderPolicy),
      startPos,
      blockNode.end_pos,
    );
  }
}
NONTERMINALS['@Repeat'] = new RepeatParser();

class IfParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    let BK = source.canBacktrack('if-lookahead');
    source.require('if-begin', { BK });
    source.require('if-condition-begin', { BK });
    if (BK) BK = source.pos === startPos;

    let operator;
    let leftNode;
    let rightNode;
    if (source.is('if-prefix', { suffixes: ['==', '!=', '<=', '<', '>=', '>', 'notin', 'in'] })) {
      operator = source.matchedSuffix;
      BK = false;
      leftNode = source.parse('@Expression', { BK });
      rightNode = source.parse('@Expression', { BK });
    } else {
      leftNode = source.parse('@Expression', { BK });
      if (leftNode instanceof BinaryNode && leftNode.comparative) {
        operator = String(leftNode.operator);
        rightNode = leftNode.right_node;
        leftNode = leftNode.left_node;
      } else if (
        source.is('if-infix', { suffixes: ['notin', 'in', '!=', '<=', '<', '>=', '>', '=='] })
      ) {
        operator = source.matchedSuffix;
        BK = false;
        rightNode = source.parse('@Expression', { BK });
      } else {
        source.require('if-infix', { BK });
        rightNode = source.parse('@Expression', { BK });
        if (
          source.is('if-suffix', { suffixes: ['!=', '<=', '<', '>=', '>', 'notin', 'in', '=='] })
        ) {
          operator = source.matchedSuffix;
        } else {
          operator = '==';
        }
      }
    }
    source.require('if-condition-end', { BK });

    source.require('if-then', { BK });
    const thenNode = source.parse('@Block', { BK: false });
    const elseEndPos = source.pos;
    let nodeEndPos = thenNode.end_pos;
    let elseNode = null;

    source.skipWhitespacesAndComments({ includeLinefeed: true });
    if (source.is('if-else')) {
      elseNode = source.parse('@Block', { BK: false });
      nodeEndPos = elseNode.end_pos;
    } else if (source.isDefined('if-end') && !source.is('if-end', { unconsumed: true })) {
      try {
        elseNode = source.parse('@Block', { BK: false });
        nodeEndPos = elseNode.end_pos;
      } catch (e) {
        if (!(e instanceof YuiError)) throw e;
        source.pos = elseEndPos;
        elseNode = null;
      }
    } else {
      source.pos = elseEndPos;
      elseNode = null;
    }
    source.require('if-end', { lskipLf: true, BK: false });
    return source.p(
      new IfNode(leftNode, operator, rightNode, thenNode, elseNode),
      startPos,
      nodeEndPos,
    );
  }
}
NONTERMINALS['@If'] = new IfParser();

class FuncDefParser extends ParserCombinator {
  match(source) {
    let BK = source.canBacktrack('funcdef-lookahead');
    const startPos = source.pos;
    source.require('funcdef-begin', { BK });
    source.require('funcdef-name-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const nameNode = source.parse('@Name', { BK });
    source.require('funcdef-name-end', { BK });

    const args = [];
    if (!source.is('funcdef-noarg')) {
      source.require('funcdef-args-begin', { BK });
      while (!source.is('funcdef-args-end', { unconsumed: true })) {
        args.push(source.parse('@Name', { BK }));
        if (source.is('funcdef-arg-separator', { ifUndefined: true })) {
          continue;
        }
        break;
      }
      source.require('funcdef-args-end', { BK });
    }

    source.require('funcdef-block', { BK });
    const bodyNode = source.parse('@Block', { BK: false });
    source.require('funcdef-end', { lskipLf: true, BK: false });
    return source.p(
      new FuncDefNode(nameNode, args, bodyNode),
      startPos,
      bodyNode.end_pos,
    );
  }
}
NONTERMINALS['@FuncDef'] = new FuncDefParser();

// Assert 内の式は Yui 標準構文でも解釈できるようフォールバック用に保持する
const _YUI_FALLBACK_SYNTAX = loadSyntax('yui');

class AssertParser extends ParserCombinator {
  match(source) {
    const startPos = source.pos;
    let BK = source.canBacktrack('assert-lookahead');
    source.require('assert-begin', { BK });
    if (BK) BK = source.pos === startPos;
    const saved = source.save();
    let firstError = null;
    try {
      let testNode = source.parse('@Expression', { BK });
      let referenceNode;
      if (testNode instanceof BinaryNode && testNode.comparative) {
        referenceNode = testNode.right_node;
        testNode = testNode.left_node;
      } else {
        source.require('assert-infix', { BK });
        referenceNode = source.parse('@Expression', { BK });
      }
      source.require('assert-end', { BK });
      const orderPolicy = source.get('assert-order');
      return source.p(new AssertNode(testNode, referenceNode, orderPolicy), startPos);
    } catch (e) {
      if (!(e instanceof YuiError)) throw e;
      firstError = e;
      source.backtrack(saved);
    }
    const savedTerminals = source.terminals;
    try {
      // Yui 構文で再度試す
      source.terminals = { ..._YUI_FALLBACK_SYNTAX };
      // sticky/global regex キャッシュは terminals に紐付いているので破棄
      source._searchRegexes = new Map();
      const testNode = source.parse('@Expression', { BK });
      source.require('assert-infix', { BK });
      const referenceNode = source.parse('@Expression', { BK });
      source.require('assert-end', { BK });
      const orderPolicy = source.get('assert-order');
      return source.p(new AssertNode(testNode, referenceNode, orderPolicy), startPos);
    } catch (_) {
      throw firstError;
    } finally {
      source.terminals = savedTerminals;
      source._searchRegexes = new Map();
    }
  }
}
NONTERMINALS['@Assert'] = new AssertParser();

class BlockParser extends ParserCombinator {
  match(source) {
    const saved = source.save();
    if (source.is('line-block-begin')) {
      const openingPos = source.pos - source.matchedString.length;
      if (source.is('line-block-end')) {
        return source.p(new BlockNode([]), openingPos);
      }
      try {
        const statements = source.parse('@Statement[]');
        source.require('line-block-end', { BK: false });
        return source.p(new BlockNode(statements), openingPos);
      } catch (e) {
        if (!(e instanceof YuiError)) throw e;
        source.backtrack(saved);
      }
    }

    source.require('block-begin', { lskipLf: true });
    const openingPos = source.pos - source.matchedString.length;
    const statements = [];
    if (source.isDefined('indent') && !source.isDefined('block-end')) {
      const indent = source.captureIndent();
      let blockEndPos = null;
      while (source.hasNext()) {
        const savedBeforeLf = source.save();
        source.require('linefeed', { lskipWs: true });
        if (source.is('linefeed', { unconsumed: true })) {
          continue;
        }
        if (source.consumeString(indent)) {
          if (source.is('block-end', { lskipWs: false, unconsumed: true })) {
            break;
          }
          if (source.is('whitespace', { lskipWs: false })) {
            statements.push(...source.parse('@Statement[]'));
            continue;
          }
        }
        blockEndPos = source.pos;
        source.backtrack(savedBeforeLf);
        break;
      }
      source.require('block-end', { openingPos });
      return source.p(new BlockNode(statements), openingPos, blockEndPos);
    }

    while (!source.is('block-end', { lskipLf: true, unconsumed: true })) {
      const curPos = source.pos;
      statements.push(...source.parse('@Statement[]', { lskipLf: true }));
      if (curPos === source.pos) {
        break;
      }
    }
    source.require('block-end', { lskipLf: true, openingPos });
    return source.p(new BlockNode(statements), openingPos);
  }
}
NONTERMINALS['@Block'] = new BlockParser();

const STATEMENTS = [
  '@FuncDef',
  '@Increment',
  '@Decrement',
  '@Append',
  '@Import',
  '@Break',
  '@Assignment',
  '@Assert',
  '@If',
  '@Repeat',
  '@Return',
  '@Pass',
  '@PrintExpression',
];

class StatementParser extends ParserCombinator {
  match(source) {
    const saved = source.save();
    for (const parserName of STATEMENTS) {
      try {
        return source.parse(parserName, { BK: true });
      } catch (e) {
        if (!(e instanceof YuiError)) throw e;
        if (!e.BK) throw e;
      }
      source.backtrack(saved);
    }
    const line = source.captureLine();
    if (line.trim() === '' && !source.isDefined('pass')) {
      return source.p(new PassNode(), source.pos);
    }
    throw new YuiError(
      ['wrong-statement', `❌${line}`],
      source.p(null, null, null, 1),
    );
  }
}
NONTERMINALS['@Statement'] = new StatementParser();

class StatementsParser extends ParserCombinator {
  match(source) {
    let statements;
    if (source.isEosOrLinefeed({ lskipWs: true, unconsumed: true })) {
      statements = [];
    } else {
      statements = [source.parse('@Statement')];
    }
    while (source.is('statement-separator')) {
      statements.push(source.parse('@Statement'));
    }
    return statements;
  }
}
NONTERMINALS['@Statement[]'] = new StatementsParser();

class TopLevelParser extends ParserCombinator {
  match(source) {
    source.skipWhitespacesAndComments({ includeLinefeed: true });
    const savedPos = source.pos;
    const statements = [];
    while (source.hasNext()) {
      const curPos = source.pos;
      statements.push(...source.parse('@Statement[]'));
      if (curPos === source.pos) {
        break;
      }
      source.skipWhitespacesAndComments({ includeLinefeed: true });
    }
    if (source.hasNext()) {
      const line = source.captureLine();
      throw new YuiError(
        ['wrong-statement', `❌${line}`],
        source.p(null, null, null, 1),
      );
    }
    return source.p(new BlockNode(statements, true), savedPos);
  }
}
NONTERMINALS['@TopLevel'] = new TopLevelParser();

// ─────────────────────────────────────────────
// YuiParser — CLI / runtime から使う薄いラッパ
// ─────────────────────────────────────────────

export class YuiParser {
  /**
   * @param {string|object} syntax syntax 名, ファイルパス, または terminals dict
   */
  constructor(syntax) {
    this.syntax = syntax;
    if (syntax != null && typeof syntax === 'object') {
      this.terminals = { ...syntax };
    } else {
      this.terminals = loadSyntax(syntax);
    }
  }

  parse(sourceCode) {
    const source = new Source(sourceCode, { syntax: this.terminals });
    return source.parse('@TopLevel');
  }
}
