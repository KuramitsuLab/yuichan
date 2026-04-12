// index.js — yuijs の公開 API エントリポイント
//
// 用途: Web アプリ / Node スクリプトへの埋め込み。
//
// 最小構成で Yui コードを実行したい場合:
//
//   import { run } from 'yuijs';
//   const result = run('x は 1\ny は 2\n', { syntax: 'yui' });
//   // result.value       — eval mode の結果 (最後の式の値)
//   // result.env         — 実行後の変数環境 (最終スコープのスナップショット)
//   // result.runtime     — 使い終わった YuiRuntime (統計参照等に使える)
//
// より低レベルな制御が必要な場合は YuiRuntime / YuiParser / CodingVisitor を
// 直接 import する:
//
//   import { YuiRuntime, YuiParser, CodingVisitor } from 'yuijs';
//   const rt = new YuiRuntime();
//   rt.exec(source, 'yui');
//
// 構文変換 (yui → pylike など):
//
//   import { convert } from 'yuijs';
//   const pylike = convert(source, { from: 'yui', to: 'pylike' });

// ─────────────────────────────────────────────
// 型システム / 値
// ─────────────────────────────────────────────
export {
  YuiValue,
  YuiType,
  YuiNullType,
  YuiBooleanType,
  YuiIntType,
  YuiFloatType,
  YuiNumberType,
  YuiStringType,
  YuiArrayType,
  YuiObjectType,
  NullType,
  BoolType,
  IntType,
  FloatType,
  NumberType,
  StringType,
  ArrayType,
  ObjectType,
  types,
  OPERATORS,
} from './yuitypes.js';

// ─────────────────────────────────────────────
// エラー
// ─────────────────────────────────────────────
export {
  YuiError,
  ERROR_MESSAGES,
  formatMessages,
  normalizeMessages,
  setVerbose,
  isVerbose,
} from './yuierror.js';

// ─────────────────────────────────────────────
// AST ノード (埋め込み先でプログラム構築に使う)
// ─────────────────────────────────────────────
export {
  ASTNode,
  ExpressionNode,
  StatementNode,
  ConstNode,
  NumberNode,
  StringNode,
  NameNode,
  ArrayNode,
  ObjectNode,
  MinusNode,
  ArrayLenNode,
  GetIndexNode,
  BinaryNode,
  FuncAppNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  IfNode,
  RepeatNode,
  BreakNode,
  PassNode,
  ImportNode,
  ReturnNode,
  FuncDefNode,
  PrintExpressionNode,
  AssertNode,
  CatchNode,
  _node,
} from './yuiast.js';

// ─────────────────────────────────────────────
// 構文定義 / パーサ / コード生成
// ─────────────────────────────────────────────
export {
  YuiSyntax,
  loadSyntax,
  loadSyntaxFromUrl,
  listSyntaxNames,
  findMatchingSyntaxes,
  generateBnf,
  DEFAULT_SYNTAX_JSON,
  GRAMMARS,
  SYNTAX_NAMES,
  getGrammar,
} from './yuisyntax.js';

export { Source, SourceNode, YuiParser } from './yuiparser.js';

export { CodingVisitor } from './yuicoding.js';

// ─────────────────────────────────────────────
// ランタイム / 標準ライブラリ
// ─────────────────────────────────────────────
export {
  YuiRuntime,
  YuiFunction,
  LocalFunction,
  NativeFunction,
  YuiBreakException,
  YuiReturnException,
} from './yuiruntime.js';

export { standardLib } from './yuistdlib.js';

// ─────────────────────────────────────────────
// サンプルコード
// ─────────────────────────────────────────────
export {
  YuiExample,
  getAllExamples,
  getSamples,
  getTestExamples,
} from './yuiexample.js';

// ─────────────────────────────────────────────
// 高レベル便利関数
// ─────────────────────────────────────────────

import { YuiRuntime as _YuiRuntime } from './yuiruntime.js';
import { CodingVisitor as _CodingVisitor } from './yuicoding.js';
import { YuiParser as _YuiParser } from './yuiparser.js';
import { types as _types } from './yuitypes.js';

/**
 * Yui ソースコードを実行し、結果・環境・ランタイムを返す。
 * Web アプリからの単発呼び出し向け。例外はそのまま投げる
 * (呼び出し側で `catch (e) { if (e instanceof YuiError) { ... } }` で処理)。
 *
 * @param {string} source — Yui ソースコード
 * @param {object} [opts]
 * @param {string|object} [opts.syntax='yui'] — 構文名または terminals dict
 * @param {number} [opts.timeout=30] — 実行タイムアウト (秒)
 * @param {boolean} [opts.allowBinaryOps=false] — `+ - * / %` を許可するか
 * @param {object} [opts.env={}] — 実行開始時の初期変数環境
 * @returns {{value: any, env: object, runtime: YuiRuntime}}
 */
export function run(source, opts = {}) {
  const {
    syntax = 'yui',
    timeout = 30,
    allowBinaryOps = false,
    env = {},
  } = opts;
  const runtime = new _YuiRuntime();
  runtime.allow_binary_ops = allowBinaryOps;
  // 初期環境を流し込む (YuiValue でラップ)
  for (const [key, value] of Object.entries(env)) {
    runtime.setenv(key, _types.box(value));
  }
  const value = runtime.exec(source, syntax, { timeout, evalMode: true });
  const envSnapshot = {};
  for (const [key, v] of runtime.getTopEnv()) {
    if (key.startsWith('@')) continue; // 関数などの内部エントリはスキップ
    envSnapshot[key] = _types.unbox(v);
  }
  return { value, env: envSnapshot, runtime };
}

/**
 * 構文 A → 構文 B のコード変換。parser + CodingVisitor を組み合わせる。
 *
 * @param {string} source
 * @param {object} opts
 * @param {string|object} opts.from — 元の構文名
 * @param {string|object} opts.to — 変換先の構文名
 * @param {string} [opts.indentString='   ']
 * @param {string|null} [opts.functionLanguage=null] — 'ja'/'en'/'emoji' など
 * @returns {string}
 */
export function convert(source, opts) {
  const { from, to, indentString = '   ', functionLanguage = null } = opts;
  if (from == null || to == null) {
    throw new Error('convert: both `from` and `to` must be specified');
  }
  const parser = new _YuiParser(from);
  const ast = parser.parse(source);
  const visitor = new _CodingVisitor(to, functionLanguage);
  return visitor.emit(ast, indentString);
}

// バージョン (Python 側 yuichan/__init__.py の __version__ に相当)
export const VERSION = '0.0.1';
