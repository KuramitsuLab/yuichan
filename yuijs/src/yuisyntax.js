// yuisyntax.js — 構文 JSON のロード, 終端記号, 例文生成, BNF 出力
// Python 版 yuichan/yuisyntax.py の移植
//
// 内部依存なし (最下層)。
// findMatchingSyntaxes だけ yuiparser に依存するが、循環を避けるため動的 import で遅延ロードする。
//
// Web 埋め込み対応: 組み込み grammar は yuigrammars.js に辞書としてインライン化してある。
// fs/path/url のような Node 専用 API はこのファイルでは使わない (ブラウザでそのまま動かす)。
// 外部 URL の grammar は loadSyntaxFromUrl(url) で非同期ロードする。

import { GRAMMARS, SYNTAX_NAMES, getGrammar } from './yuigrammars.js';

// ─────────────────────────────────────────────
// _Rng: シード付き乱数ジェネレータ
// ─────────────────────────────────────────────
//
// Python 版は `random.seed(self.seed)` → `randint` → `seed += 1` というクセのある実装。
// JS 側は Mersenne Twister を持たないので、Python とビット完全一致は目指さない。
// 重要なのは「seed が null/undefined のとき常に 0」という性質 — これは tests が依存する。
// seed が数値のときは決定的だが Python とは違う系列になる。
//
class _Rng {
  constructor(seed) {
    this.seed = seed == null ? null : seed >>> 0;
  }

  /** [0, n) の整数を返す。seed が null なら常に 0 (決定的フォールバック)。 */
  nextInt(n) {
    if (this.seed == null) {
      return 0;
    }
    // mulberry32: シンプルで決定的な PRNG
    let t = (this.seed = (this.seed + 0x6d2b79f5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    const r = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    return Math.floor(r * n);
  }
}

// ─────────────────────────────────────────────
// 例文生成: 正規表現パターンから代表文字列を作る
// ─────────────────────────────────────────────
//
// Python 版と同様、`▁` プレースホルダで `\(`, `\)`, `\|` などのエスケープを退避する。
// この記号 (U+2581 LOWER ONE EIGHTH BLOCK) は通常の Yui ソースには現れない前提。

const ESC_REPLACEMENTS = [
  [/\\\|/g, '▁｜'],
  [/\\\[/g, '▁［'],
  [/\\\]/g, '▁］'],
  [/\\\(/g, '▁（'],
  [/\\\)/g, '▁）'],
  [/\\\*/g, '▁＊'],
  [/\\\?/g, '▁？'],
  [/\\\+/g, '▁＋'],
  // Python 側では `+` を消し `*` を `?` に変える (ループは 0 or 1 回扱い)
  [/\+/g, ''],
  [/\*/g, '?'],
];

const ESC_RESTORE = [
  ['▁｜', '|'],
  ['▁［', '['],
  ['▁］', ']'],
  ['▁（', '('],
  ['▁）', ')'],
  ['▁？', '?'],
  ['▁＋', '+'],
  ['▁＊', '*'],
];

export function getExampleFromPattern(pattern, randomSeed = null) {
  const rng = new _Rng(randomSeed);
  const originalPattern = pattern;
  for (const [re, repl] of ESC_REPLACEMENTS) {
    pattern = pattern.replace(re, repl);
  }
  let processed = '';
  while (pattern.length > 0) {
    const sPos = pattern.indexOf('('); // シングルループだけ対応
    if (sPos === -1) {
      processed += getExampleFromPatternInner(pattern, rng);
      break;
    }
    const ePos = pattern.indexOf(')', sPos + 1);
    if (ePos === -1) {
      throw new Error(`Unmatched parentheses in pattern: \`${originalPattern}\``);
    }
    processed += getExampleFromPatternInner(pattern.slice(0, sPos), rng);
    const inner = pattern.slice(sPos + 1, ePos);
    pattern = pattern.slice(ePos + 1);
    if (pattern.startsWith('?')) {
      pattern = pattern.slice(1);
      if (rng.nextInt(2) !== 0) {
        processed += getExampleFromPatternInner(inner, rng);
      }
    } else {
      processed += getExampleFromPatternInner(inner, rng);
    }
  }
  for (const [a, b] of ESC_RESTORE) {
    processed = processed.split(a).join(b);
  }
  if (processed.includes('▁')) {
    throw new Error(
      `Unprocessed escape sequences remain in \`${originalPattern}\`: \`${processed}\``
    );
  }
  return processed;
}

/**
 * 先頭文字を取り出して [先頭, 残り] を返す。
 * バックスラッシュエスケープ・▁プレースホルダ・絵文字バリエーションセレクタを考慮。
 * 末尾が `?` なら 50% で空文字列を返す (rng が決定的なら常に空 or 常に有り)。
 */
function splitHeadingChar(s, rng) {
  let headingChar;
  let remaining;

  if (s.startsWith('\\')) {
    // エスケープシーケンス (\\, \s, \t, \n, \r, \d, \w, ...)
    const next = s[1];
    remaining = s.slice(2);
    switch (next) {
      case '\\': headingChar = '\\'; break;
      case 's':  headingChar = ' '; break;
      case 't':  headingChar = '\t'; break;
      case 'n':  headingChar = '\n'; break;
      case 'r':  headingChar = '\r'; break;
      case 'd':  headingChar = '1'; break;
      case 'w':  headingChar = 'a'; break;
      default:   headingChar = next; break;
    }
  } else if (s.startsWith('▁')) {
    // ▁ プレースホルダは 2 文字単位 (▁＋ など)
    headingChar = s.slice(0, 2);
    remaining = s.slice(2);
  } else if (
    s.length >= 2 &&
    (s[1] === '\uFE0F' || s[1] === '\u200D')
  ) {
    // 合字や絵文字のバリエーションセレクタ
    headingChar = s.slice(0, 2);
    remaining = s.slice(2);
  } else {
    headingChar = s[0];
    remaining = s.slice(1);
  }

  if (remaining.startsWith('?')) {
    if (rng.nextInt(2) === 0) {
      return ['', remaining.slice(1)];
    }
    return [headingChar, remaining.slice(1)];
  }
  return [headingChar, remaining];
}

function getExampleFromPatternInner(pattern, rng) {
  if (pattern === '') {
    return '';
  }
  // 選択肢 | の処理: いずれかを選ぶ
  if (pattern.includes('|')) {
    const choices = pattern.split('|');
    pattern = choices[rng.nextInt(choices.length)];
    if (pattern === '') {
      return '';
    }
  }
  // 文字クラス [abc] の処理
  if (pattern.startsWith('[')) {
    const endPos = pattern.indexOf(']');
    if (pattern[endPos + 1] === '?') {
      return getExampleFromPatternInner(pattern.slice(endPos + 2), rng);
    }
    const [headingChar] = splitHeadingChar(pattern.slice(1, endPos), rng);
    return headingChar + getExampleFromPatternInner(pattern.slice(endPos + 1), rng);
  }
  const [headingChar, remaining] = splitHeadingChar(pattern, rng);
  return headingChar + getExampleFromPatternInner(remaining, rng);
}

// ─────────────────────────────────────────────
// デフォルト終端記号 (Python 側と完全に同期)
// ─────────────────────────────────────────────
export const DEFAULT_SYNTAX_JSON = {
  'whitespace':  '[ \\t\\r　]',
  'whitespaces': '[ \\t\\r　]+',
  'linefeed':    '[\\n]',
  'line-comment-begin': '[#＃]',

  'number-first-char': '[0-9]',
  'number-chars':      '[0-9]*',
  'number-dot-char':   '[\\.][0-9]',

  'name-first-char': '[A-Za-z_]',
  'name-chars':      '[A-Za-z0-9_]*',

  'string-begin':              '"',
  'string-end':                '"',
  'string-escape':             '\\\\',
  'string-interpolation-begin': '\\{',
  'string-interpolation-end':   '\\}',

  'grouping-begin': '\\(',
  'grouping-end':   '\\)',

  'array-begin':     '\\[',
  'array-end':       '\\]',
  'array-separator': ',',

  'object-begin':         '\\{',
  'object-end':           '\\}',
  'object-separator':     ',',
  'key-value-separator':  ':',

  'array-indexer-suffix': '\\[',
  'array-indexer-end':    '\\]',
  'unary-minus':          '-',

  'funcapp-args-begin': '\\(',
  'funcapp-args-end':   '\\)',
  'funcapp-separator':  ',',

  'unary-inspect': '👀',
  'catch-begin':   '🧤',
  'catch-end':     '🧤',

  'print-begin': '',
  'print-end':   '',

  'assert-begin': '>>>\\s+',
  'assert-infix': '[\\n]',
  'assert-end':   '',
};

// ─────────────────────────────────────────────
// loadSyntax / listSyntaxNames / findMatchingSyntaxes
// ─────────────────────────────────────────────

/**
 * 組み込み grammar の終端記号辞書にデフォルトを埋めて返す。
 * 直接 terminals オブジェクトを渡した場合もそのまま補完する (shallow copy)。
 *
 * @param {string|object|null} name — grammar 名 (例 'yui') または terminals オブジェクト
 *   - null/undefined → 'yui'
 *   - string → yuigrammars.js の辞書から引く (存在しなければ例外)
 *   - object → そのまま使う (shallow copy)
 * @returns {object} 終端記号 dict (デフォルト値で補完済み)
 */
export function loadSyntax(name = null) {
  let terminals;
  if (name == null) {
    name = 'yui';
  }
  if (typeof name === 'string') {
    const found = getGrammar(name);
    if (found == null) {
      throw new Error(
        `unknown syntax: ${name} (available: ${SYNTAX_NAMES.join(', ')})`,
      );
    }
    terminals = { ...found };
  } else if (typeof name === 'object') {
    terminals = { ...name };
  } else {
    throw new TypeError(`loadSyntax: expected string or object, got ${typeof name}`);
  }

  return _fillDefaults(terminals);
}

/**
 * 終端記号辞書に DEFAULT_SYNTAX_JSON を埋めて string-content-end も導出する。
 * loadSyntax および loadSyntaxFromUrl の共通ヘルパ。
 */
function _fillDefaults(terminals) {
  for (const [key, pattern] of Object.entries(DEFAULT_SYNTAX_JSON)) {
    if (!(key in terminals)) {
      terminals[key] = pattern;
    }
  }
  if (!('string-content-end' in terminals)) {
    const escape = terminals['string-escape'] ?? '\\\\';
    const interpolation = terminals['string-interpolation-begin'] ?? '\\{';
    const stringEnd = terminals['string-end'] ?? '\\"';
    terminals['string-content-end'] = `${escape}|${interpolation}|${stringEnd}`;
  }
  return terminals;
}

/**
 * 外部 URL から JSON で terminals をロードする (非同期)。
 * ブラウザ / Node 18+ の fetch を利用する。
 *
 * @param {string} url — grammar JSON の URL
 * @param {object} [opts]
 * @param {typeof fetch} [opts.fetch] — 差し替え用 fetch 実装 (テスト等)
 * @returns {Promise<object>} デフォルト値で補完された terminals dict
 */
export async function loadSyntaxFromUrl(url, opts = {}) {
  const fetchImpl = opts.fetch ?? globalThis.fetch;
  if (typeof fetchImpl !== 'function') {
    throw new Error(
      'loadSyntaxFromUrl: global fetch is not available. ' +
        'Pass opts.fetch to provide one, or run on Node 18+.',
    );
  }
  const response = await fetchImpl(url);
  if (!response.ok) {
    throw new Error(
      `loadSyntaxFromUrl: HTTP ${response.status} ${response.statusText} for ${url}`,
    );
  }
  const terminals = await response.json();
  if (terminals == null || typeof terminals !== 'object') {
    throw new Error(`loadSyntaxFromUrl: ${url} did not return a JSON object`);
  }
  return _fillDefaults(terminals);
}

/**
 * 組み込み grammar の名前一覧 (ソート済み)。
 * 引数 `syntaxDir` は Python との API 互換のため受け取るが、Web 埋め込み対応で
 * 組み込み辞書からのみ読むようになったため無視する。
 */
// eslint-disable-next-line no-unused-vars
export function listSyntaxNames(_syntaxDir = null) {
  return [...SYNTAX_NAMES];
}

/**
 * 利用可能な全 syntax に対して sources のソースコードを解析し、成否を返す。
 *
 * 戻り値: [{ name, matched, status }, ...]
 *
 * yuiparser に依存するため動的 import する。
 */
// eslint-disable-next-line no-unused-vars
export async function findMatchingSyntaxes(sources, _syntaxDir = null) {
  // 循環インポートを避けるため遅延 import
  const { YuiParser } = await import('./yuiparser.js');

  const results = [];
  for (const name of SYNTAX_NAMES) {
    let errorInfo = null;
    for (const [filename, code] of Object.entries(sources)) {
      try {
        new YuiParser(name).parse(code);
      } catch (e) {
        errorInfo = { filename, error: e };
        break;
      }
    }
    if (errorInfo == null) {
      results.push({ name, matched: true, status: 'OK' });
    } else {
      const { filename, error } = errorInfo;
      results.push({
        name,
        matched: false,
        status: `FAIL (${filename}: ${error.message ?? error})`,
      });
    }
  }
  return results;
}

/**
 * 組み込み grammar 辞書の re-export (yuigrammars.js 経由)。
 * 他モジュールから直接 grammar を参照したいときに使う。
 */
export { GRAMMARS, SYNTAX_NAMES, getGrammar };

// ─────────────────────────────────────────────
// YuiSyntax クラス
// ─────────────────────────────────────────────
//
// 終端記号テーブルのラッパ。get_pattern で初回に正規表現をコンパイルしてキャッシュする。
// パーサ層が `regex.exec(source)` を pos 指定で呼べるよう、コンパイル時に sticky フラグ (`y`) を付ける。
//

export class YuiSyntax {
  constructor(syntaxJson) {
    if (syntaxJson == null || typeof syntaxJson !== 'object') {
      throw new TypeError('Terminals must be an object');
    }
    // shallow copy (Python の dict.copy() 相当)
    this.terminals = { ...syntaxJson };
    this.randomSeed = null;
  }

  isDefined(terminal) {
    const v = this.terminals[terminal];
    if (v == null) return false;
    if (typeof v === 'string') return v !== '';
    // 既にコンパイル済み RegExp ならソースを見る
    if (v instanceof RegExp) return v.source !== '';
    return true;
  }

  updateSyntax(updates) {
    Object.assign(this.terminals, updates);
  }

  /** 終端記号の元パターン文字列を返す (コンパイル済み RegExp なら .source)。未定義は ''。 */
  get(terminal) {
    const pattern = this.terminals[terminal];
    if (pattern == null) return '';
    if (typeof pattern === 'string') return pattern;
    if (pattern instanceof RegExp) return pattern.source;
    return '';
  }

  /**
   * sticky フラグ付き RegExp を返し、内部にキャッシュする。
   * 未定義時は ifUndefined (文字列) をコンパイルして返す。
   */
  getPattern(terminal, ifUndefined = '') {
    let pattern = this.terminals[terminal];
    if (pattern == null) {
      pattern = ifUndefined;
    }
    if (typeof pattern === 'string') {
      let compiled;
      try {
        // sticky (y) フラグで「pos 位置からのみマッチ」させる。
        // パーサ層は regex.lastIndex = pos; regex.exec(source) で使う。
        compiled = new RegExp(pattern, 'y');
      } catch (e) {
        throw new Error(`Invalid regex '${terminal}': ${pattern}`);
      }
      this.terminals[terminal] = compiled;
      return compiled;
    }
    if (pattern instanceof RegExp) {
      return pattern;
    }
    throw new Error(`Invalid pattern type for '${terminal}'`);
  }

  /** 終端記号にマッチする代表文字列を返す (BNF 表示用)。 */
  forExample(terminal) {
    if (!this.isDefined(terminal)) {
      return '';
    }
    let pattern = this.terminals[terminal];
    if (pattern instanceof RegExp) {
      pattern = pattern.source;
    }
    return getExampleFromPattern(pattern, this.randomSeed);
  }
}

// ─────────────────────────────────────────────
// generate_bnf: syntax dict から BNF 風の文法表記を生成
// ─────────────────────────────────────────────
export function generateBnf(terminals) {
  const s = new YuiSyntax(terminals);
  const syntaxName = terminals['syntax'] ?? '?';

  /** トークンの代表文字列。未定義なら ''。改行は ↵ に置換。 */
  function ex(name) {
    if (!s.isDefined(name)) return '';
    const val = s.forExample(name);
    if (val === '\n') return '↵';
    return val;
  }

  const E = '<expr>';
  const N = '<name>';
  const B = '<block>';

  const out = [];

  function section(title) {
    out.push('');
    out.push(`${title}:`);
  }

  /** BNF 規則を 1 行追加。空文字列の部品は無視する。 */
  function r(lhs, ...parts) {
    const tokens = parts
      .filter((p) => p != null && String(p) !== '')
      .map(String);
    if (tokens.length > 0) {
      const padded = lhs.padEnd(18);
      out.push(`  ${padded} ::= ${tokens.join(' ')}`);
    }
  }

  // ── ヘッダ ────────────────────────────────────────────────
  out.push(`Grammar for '${syntaxName}'`);
  out.push('─'.repeat(40));

  // ── Literals ─────────────────────────────────────────────
  section('Literals');

  r('Number', '0  |  3.14');

  const sb = ex('string-begin');
  const se = ex('string-end');
  const ib = ex('string-interpolation-begin');
  const ie = ex('string-interpolation-end');
  const interp = ib ? `  (interp: ${ib}${E}${ie})` : '';
  r('String', `${sb}...${se}${interp}`);

  const ab = ex('array-begin') || '[';
  const ae = ex('array-end') || ']';
  const asep = ex('array-separator') || ',';
  r('Array', `${ab} ${E} {${asep} ${E}} ${ae}`);

  const ob = ex('object-begin') || '{';
  const oe = ex('object-end') || '}';
  const kvsep = ex('key-value-separator') || ':';
  const osep = ex('object-separator') || ',';
  r('Object', `${ob} "key"${kvsep}${E} {${osep} "key"${kvsep}${E}} ${oe}`);

  const nl = ex('null');
  if (nl) r('Null', nl);

  const bt = ex('boolean-true');
  const bf = ex('boolean-false');
  if (bt || bf) {
    r('Boolean', bt || '?', '|', bf || '?');
  }

  const nb = ex('extra-name-begin');
  const ne = ex('extra-name-end');
  if (nb) {
    r('Name', `${nb}...${ne}  |  letter...`);
  } else {
    r('Name', 'letter...');
  }

  // ── Expressions ──────────────────────────────────────────
  section('Expressions');

  const gb = ex('grouping-begin');
  const ge = ex('grouping-end');
  if (gb) r('Grouping', `${gb} ${E} ${ge}`);

  if (ex('length-begin')) {
    r('Length', ex('length-begin') + E + ex('length-end'));
  } else if (ex('unary-length')) {
    r('Length', ex('unary-length') + ' ' + E);
  } else if (ex('property-accessor') && ex('property-length')) {
    r('Length', `${E}${ex('property-accessor')}${ex('property-length')}`);
  }

  if (ex('unary-minus')) {
    r('Minus', ex('unary-minus') + E);
  }

  const faB = ex('funcapp-args-begin');
  const faE = ex('funcapp-args-end');
  const faSep = ex('funcapp-separator') || ',';
  if (faB) {
    r('FuncApp', `${E}${faB}${E} {${faSep} ${E}}${faE}`);
  }

  const aiB = ex('array-indexer-suffix') || '[';
  const aiE = ex('array-indexer-end') || ']';
  r('Index', `${E}${aiB}${E}${aiE}`);

  const pa = ex('property-accessor');
  if (pa) {
    const props = ['property-length', 'property-type']
      .map((k) => ex(k))
      .filter((v) => v);
    if (props.length > 0) {
      r('Property', `${E}${pa}(${props.join(' | ')})`);
    }
  }

  const arith = ['+', '-', '*', '/', '%']
    .map((op) => [op, ex(`binary${op}`)])
    .filter(([, t]) => t);
  if (arith.length > 0) {
    r('Arithmetic', arith.map(([, t]) => `${E} ${t} ${E}`).join(' | '));
  }

  const compOps = ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin']
    .map((op) => [op, ex(`binary${op}`)])
    .filter(([, t]) => t);
  if (compOps.length > 0) {
    r('Comparison', compOps.map(([, t]) => `${E} ${t} ${E}`).join(' | '));
  }

  // ── Statements ───────────────────────────────────────────
  section('Statements');

  r('Assignment',
    ex('assignment-begin'), E, ex('assignment-infix'), E, ex('assignment-end'));
  r('Increment',
    ex('increment-begin'), E, ex('increment-infix'), ex('increment-end'));
  r('Decrement',
    ex('decrement-begin'), E, ex('decrement-infix'), ex('decrement-end'));
  r('Append',
    ex('append-begin'), E, ex('append-infix'), E, ex('append-end'));

  if (ex('break'))    r('Break',    ex('break'));
  if (ex('continue')) r('Continue', ex('continue'));
  if (ex('pass'))     r('Pass',     ex('pass'));

  r('Return', ex('return-begin'), E, ex('return-end'));
  if (ex('return-none')) {
    r('Return (void)', ex('return-none'));
  }

  r('Print', ex('print-begin'), E, ex('print-end'));

  r('Repeat',
    ex('repeat-begin'), E, ex('repeat-times'), ex('repeat-block'), B, ex('repeat-end'));

  // If — infix-op 形式 (pylike/emoji) か suffix 形式 (yui) かで分岐
  const ifB  = ex('if-begin');
  const ifCb = ex('if-condition-begin');
  const ifCe = ex('if-condition-end');
  const ifThen = ex('if-then');
  const ifElse = ex('if-else');
  const ifEnd  = ex('if-end');

  const ifInfixOps = ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin']
    .map((op) => [op, ex(`if-infix${op}`)])
    .filter(([, t]) => t);
  const ifSuffixOps = ['!=', '<', '<=', '>', '>=', 'in', 'notin', '==']
    .map((op) => ex(`if-suffix${op}`))
    .filter((t) => t);

  if (ifInfixOps.length > 0) {
    const opAlts = ifInfixOps.map(([, t]) => `${E} ${t} ${E}`).join(' | ');
    r('If', ifB, ifCb, `(${opAlts})`, ifCe, ifThen, B,
      ifElse ? `[ ${ifElse} ${B} ]` : '', ifEnd);
  } else {
    const infixWord = ex('if-infix');
    const suffixStr =
      ifSuffixOps.length > 0
        ? `[ ${ifSuffixOps.slice(0, 3).join(' | ')}... ]`
        : '';
    r('If', ifB, ifCb, E, infixWord, E, suffixStr, ifCe, ifThen, B,
      ifElse ? `[ ${ifElse} ${B} ]` : '', ifEnd);
  }

  // FuncDef
  const fdB    = ex('funcdef-begin');
  const fdNb   = ex('funcdef-name-begin');
  const fdNe   = ex('funcdef-name-end');
  const fdNoarg = ex('funcdef-noarg');
  const fdAb   = ex('funcdef-args-begin');
  const fdAe   = ex('funcdef-args-end');
  const fdAsep = ex('funcdef-arg-separator');
  const fdBlk  = ex('funcdef-block');
  const fdEnd  = ex('funcdef-end');

  const argsPart = fdNoarg
    ? `( ${fdNoarg}  |  ${fdAb} ${N} {${fdAsep} ${N}} ${fdAe} )`
    : `${fdAb} ${N} {${fdAsep} ${N}} ${fdAe}`;

  r('FuncDef', fdB, fdNb, N, fdNe, argsPart, fdBlk, B, fdEnd);

  // Assert
  if (s.isDefined('assert-begin')) {
    r('Assert', ex('assert-begin'), E, ex('assert-infix'), E, ex('assert-end'));
  }

  if (s.isDefined('import-standard')) {
    r('Import', ex('import-standard'));
  }

  // ── Blocks ───────────────────────────────────────────────
  section('Blocks');

  const blkB = ex('block-begin');
  const blkE = ex('block-end');
  if (blkB && blkE) {
    r('Block', blkB, '<stmt>...', blkE);
  } else if (blkB) {
    r('Block', blkB, '<stmt>...', '(indent-delimited)');
  } else {
    r('Block', '<stmt>...', '(indent-delimited)');
  }
  r('TopLevel', '<stmt>...');

  // ── Comments ─────────────────────────────────────────────
  section('Comments');
  if (s.isDefined('line-comment-begin')) {
    r('LineComment', ex('line-comment-begin') + ' ...');
  }
  if (s.isDefined('comment-begin') && s.isDefined('comment-end')) {
    r('BlockComment', ex('comment-begin') + ' ... ' + ex('comment-end'));
  }

  return out.join('\n');
}

// 内部利用ユーティリティを export (テスト用)
export const _internals = { _Rng, splitHeadingChar, getExampleFromPatternInner };
