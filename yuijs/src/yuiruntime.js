// yuiruntime.js — Yui ランタイム (visitor)
// Python 版 yuichan/yuiruntime.py の移植
//
// 依存: yuiast.js, yuitypes.js, yuierror.js, yuistdlib.js, yuiparser.js
//
// JS ⇔ Python 主な差分:
// - Python の ABC `YuiFunction` は JS の通常 class で代替 (instance check のみ)。
// - YuiBreakException / YuiReturnException は YuiError を継承するが、
//   `instanceof` で判別して通常エラーと区別する (Python と同じ構造)。
// - Python の `time.time()` は JS では `Date.now() / 1000`。
// - Python の `print()` は JS では `console.log`。`runtime.printValue` を override すれば
//   テスト時に出力をキャプチャできる。
// - エラー node の終端は yuiast.js では `end_pos`。Python の None 相当として `-1` をデフォルトに
//   している (yuiast.js 側) ので、長さ計算は `Math.max(end_pos - pos, 3)` で常に 3 以上に。

import {
  ASTNode,
  ConstNode,
  NumberNode,
  StringNode,
  ArrayNode,
  ObjectNode,
  NameNode,
  GetIndexNode,
  ArrayLenNode,
  MinusNode,
  BinaryNode,
  FuncAppNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  PassNode,
  PrintExpressionNode,
  IfNode,
  BreakNode,
  RepeatNode,
  FuncDefNode,
  ReturnNode,
  AssertNode,
  CatchNode,
  ImportNode,
} from './yuiast.js';

import {
  YuiValue,
  types,
  IntType,
  NumberType,
  FloatType,
} from './yuitypes.js';

import { YuiError, formatMessages } from './yuierror.js';
import { standardLib } from './yuistdlib.js';
import { YuiParser } from './yuiparser.js';

// ─────────────────────────────────────────────
// _formatSourceContext — エラー表示用
// ─────────────────────────────────────────────
//
// エラー位置の前後 `context` 行をソースから切り出し、行番号付きで返す。
// Python 版 _format_source_context と同じ出力形式を維持する。

function _formatSourceContext(node, prefix, marker, lineoffset, context = 3) {
  let [line, col] = node.extract();
  line += lineoffset;
  // ASTNode のデフォルト end_pos は -1。Python の None 相当として扱う。
  const length = node.end_pos != null && node.end_pos >= 0
    ? Math.max(node.end_pos - node.pos, 3)
    : 3;
  const pointer = marker.repeat(Math.min(length, 16));

  const allLines = node.source.split('\n');
  const startIdx = Math.max(0, line - 1 - context);
  const lineWidth = String(line).length;
  const sep = ' | ';

  const linesOut = [];
  for (let i = startIdx; i < Math.min(line, allLines.length); i++) {
    const lineno = i + 1;
    const linenoStr = String(lineno).padStart(lineWidth, ' ');
    linesOut.push(`${prefix}${linenoStr}${sep}${allLines[i]}`);
  }

  const pointerIndent = ' '.repeat(prefix.length + lineWidth + sep.length + col - 1);
  linesOut.push(`${pointerIndent}${pointer}`);

  return `line ${line}, column ${col}:\n${linesOut.join('\n')}`;
}

// ─────────────────────────────────────────────
// YuiBreakException / YuiReturnException
// ─────────────────────────────────────────────
//
// Python は YuiError を継承して制御フロー用例外として使う。JS でも同じ構造にして
// `instanceof` で識別する。普通の YuiError 例外と取り違えないよう、専用クラスを定義。

export class YuiBreakException extends YuiError {
  constructor(errorNode = null) {
    super(['unexpected-break'], errorNode);
    this.name = 'YuiBreakException';
  }
}

export class YuiReturnException extends YuiError {
  constructor(value = null, errorNode = null) {
    super(['unexpected-return'], errorNode);
    this.name = 'YuiReturnException';
    this.value = value;
  }
}

// ─────────────────────────────────────────────
// YuiFunction (abstract) / LocalFunction / NativeFunction
// ─────────────────────────────────────────────

export class YuiFunction {
  constructor(name) {
    this.name = name;
  }
  // eslint-disable-next-line no-unused-vars
  call(_argValues, _node, _runtime) {
    throw new Error('YuiFunction.call must be overridden');
  }
}

/** ユーザ定義関数。body.visit(runtime) で visitor チェーンで評価される。 */
export class LocalFunction extends YuiFunction {
  constructor(name, parameters, body) {
    super(name);
    this.parameters = parameters;
    this.body = body;
  }

  call(argValues, node, runtime) {
    runtime.pushenv();
    if (this.parameters.length !== argValues.length) {
      throw new YuiError(
        ['mismatch-argument', `✅${this.parameters.length}`, `❌${argValues.length}`],
        node,
      );
    }
    this.parameters.forEach((p, i) => runtime.setenv(p, argValues[i]));
    try {
      runtime.pushCallFrame(this.name, argValues, node);
      runtime.checkRecursionDepth();
      this.body.visit(runtime);
    } catch (e) {
      if (e instanceof YuiReturnException) {
        if (e.value != null) {
          runtime.popCallFrame();
          runtime.popenv();
          return e.value;
        }
      } else {
        // 環境/フレームを巻き戻してから再送出
        runtime.popCallFrame();
        runtime.popenv();
        throw e;
      }
    }
    runtime.popCallFrame();
    // 関数が return なしで終わったとき、ローカル環境をオブジェクトとして返す
    return new YuiValue(Object.fromEntries(runtime.popenv()));
  }
}

/** ネイティブ関数 (Python の関数を Yui 関数として呼べるようにする) */
export class NativeFunction extends YuiFunction {
  constructor(fn, isFfi = false) {
    // Python: function.__name__ → JS: fn.name (or fallback)
    super(fn.name || 'anonymous');
    this.function = fn;
    this.isFfi = isFfi;
  }

  call(argValues, node, runtime) {
    try {
      const result = this.function(...argValues);
      return result instanceof YuiValue ? result : new YuiValue(result);
    } catch (e) {
      if (e instanceof YuiError) {
        if (e.errorNode == null) {
          e.errorNode = node;
        }
        throw e;
      }
      const msg = e && e.message ? e.message : String(e);
      throw new YuiError(['internal-error', `🔍${this.name}`, `⚠️ ${msg}`], node);
    }
  }
}

// ─────────────────────────────────────────────
// YuiRuntime — 中心の visitor
// ─────────────────────────────────────────────

export class YuiRuntime {
  constructor() {
    /** @type {Array<Map<string, YuiValue>>} 変数環境のスタック (末尾が最内 scope) */
    this.environments = [new Map()];
    /** @type {Array<[string, Array, ASTNode]>} 関数呼び出しフレーム */
    this.call_frames = [];
    /** 仮想ファイルシステム (将来用) */
    this.filesystems = {};

    this.shouldStop = false;
    this.timeout = 0;
    this.interactive_mode = false;
    this.source = '';
    this.allow_binary_ops = false;
    this.startTime = 0;
    this.resetStats();
  }

  resetStats() {
    this.increment_count = 0;
    this.decrement_count = 0;
    this.compare_count = 0;
    this.test_passed = [];
    this.test_failed = [];
  }

  // ── 環境操作 ───────────────────────────────────────────

  hasenv(name) {
    for (let i = this.environments.length - 1; i >= 0; i--) {
      if (this.environments[i].has(name)) return true;
    }
    return false;
  }

  getenv(name) {
    for (let i = this.environments.length - 1; i >= 0; i--) {
      const env = this.environments[i];
      if (env.has(name)) return env.get(name);
    }
    return null;
  }

  setenv(name, value) {
    this.environments.at(-1).set(name, value);
  }

  pushenv() {
    this.environments.push(new Map());
  }

  popenv() {
    return this.environments.pop();
  }

  /** 最内 (末尾) スコープを返す。 */
  getTopEnv() {
    return this.environments.at(-1);
  }

  stringifyEnv(stack = -1, indentPrefix = '') {
    let inner;
    let LF;
    if (indentPrefix == null) {
      indentPrefix = '';
      inner = null;
      LF = '';
    } else {
      inner = indentPrefix + '  ';
      LF = '\n';
    }
    const idx = stack < 0 ? this.environments.length + stack : stack;
    const env = this.environments[idx];
    const lines = [`${indentPrefix}<${this.stringifyCallFrames(stack)}>${LF}{`];
    const entries = [...env].filter(([k]) => !k.startsWith('@'));
    entries.forEach(([key, value], i) => {
      lines.push(`${LF}${indentPrefix}  "${key}": `);
      lines.push(value && typeof value.stringify === 'function'
        ? value.stringify(inner)
        : String(value));
      if (i < entries.length - 1) {
        lines.push(', ');
      }
    });
    lines.push(`${LF}${indentPrefix}}`);
    return lines.join('');
  }

  // ── エラー整形 ─────────────────────────────────────────

  formatError(error, prefix = ' ', marker = '^', lineoffset = 0) {
    const isRuntime = error.runtime != null;
    let message = formatMessages(error.messages);
    if (error.errorNode) {
      const context = _formatSourceContext(error.errorNode, prefix, marker, lineoffset);
      message = `${message} ${context}`;
    }
    if (isRuntime) {
      return `[実行時エラー/RuntimeError] ${message}\n[環境/Environment] ${this.stringifyEnv(-1)}\n`;
    }
    return `[構文エラー/SyntaxError] ${message}`;
  }

  // ── 呼び出しフレーム ───────────────────────────────────

  pushCallFrame(funcName, args, node) {
    this.call_frames.push([funcName, args, node]);
  }

  popCallFrame() {
    return this.call_frames.pop();
  }

  stringifyCallFrames(stack = -1) {
    if (this.call_frames.length === 0) {
      return 'global';
    }
    const idx = stack < 0 ? this.call_frames.length + stack : stack;
    const frame = this.call_frames[idx];
    const args = frame[1].map((arg) => String(arg)).join(', ');
    return `${frame[0]}(${args})]`;
  }

  checkRecursionDepth() {
    if (this.call_frames.length > 128) {
      const last = this.call_frames[this.call_frames.length - 1];
      const args = last[1].map((arg) => String(arg)).join(', ');
      const snippet = `${last[0]}(${args})`;
      throw new YuiError(['too-many-recursion', `🔍${snippet}`], last[2]);
    }
  }

  // ── 変数更新フック (sub-class でオーバーライド可能) ────

  // eslint-disable-next-line no-unused-vars
  updateVariable(_name, _env, _pos) {
    // no-op
  }

  // ── カウンタ ───────────────────────────────────────────

  countInc() {
    this.increment_count += 1;
  }
  countDec() {
    this.decrement_count += 1;
  }
  countCompare() {
    this.compare_count += 1;
  }

  // ── 関数の読み込み ─────────────────────────────────────

  load(fn) {
    return new NativeFunction(fn);
  }

  // ── プリント ───────────────────────────────────────────
  //
  // テスト用にオーバーライドできるよう、`print` という名前は避け
  // `printValue` メソッドで提供する。実装内部は console.log を使う。

  printValue(value, node = null) {
    if (node == null) {
      console.log(`${value && value.native !== undefined ? value.native : value}`);
      return;
    }
    const [lineno, , snippet] = node.extract();
    if (this.interactive_mode && this.isInTheTopLevel()) {
      console.log(`${value.stringify('', true)}`);
    } else if (this.isInTheTopLevel()) {
      console.log(`>>> ${node} #📍${lineno}\n${value.stringify('', true)}`);
    } else {
      const padded = String(node).padEnd(36, ' ');
      console.log(`${String(lineno).padStart(4, ' ')}: 👀${padded} → ${value.stringify('', true)}`);
    }
    void snippet; // unused but mirrors Python signature
  }

  // ── 実行制御 ───────────────────────────────────────────

  start(timeout = 30) {
    this.shouldStop = false;
    this.timeout = timeout;
    this.startTime = Date.now() / 1000;
  }

  checkExecution(node) {
    if (this.shouldStop) {
      throw new YuiError(['interruptted'], node);
    }
    if (this.timeout > 0 && Date.now() / 1000 - this.startTime > this.timeout) {
      throw new YuiError(
        ['runtime-timeout', `❌${this.timeout}[sec]`, `✅${this.timeout}[sec]`],
        node,
      );
    }
  }

  /**
   * Yui プログラムを実行する。
   * @param {string} source
   * @param {string|object} [syntax='yui']
   * @param {object} [opts]
   * @param {number} [opts.timeout=30]
   * @param {boolean} [opts.evalMode=true]
   */
  exec(source, syntax = 'yui', opts = {}) {
    const { timeout = 30, evalMode = true } = opts;
    this.source = source;

    const parser = new YuiParser(syntax);
    const program = parser.parse(source);
    let value;
    try {
      this.start(timeout);
      value = program.evaluate(this);
    } catch (e) {
      if (e instanceof YuiError) {
        e.runtime = this;
      }
      throw e;
    }
    return evalMode ? types.unbox(value) : this.environments.at(-1);
  }

  // ──────────────────────────────────────────────────────────
  // visitor entrypoint
  // ──────────────────────────────────────────────────────────

  evaluate(node) {
    return node.visit(this);
  }

  // ──────────────────────────────────────────────────────────
  // リテラル・値ノード
  // ──────────────────────────────────────────────────────────

  visitConstNode(node) {
    if (node.native_value === true) return YuiValue.TrueValue;
    if (node.native_value === false) return YuiValue.FalseValue;
    return YuiValue.NullValue;
  }

  visitNumberNode(node) {
    const v = node.native_value;
    // JS には int/float の native 区別がない。`Number.isInteger(2.0)` が true に
    // なるため、ソース snippet に '.' がある場合は float リテラルとして扱う
    // (Python 側で `1.0` が float となるのと同じセマンティクスを保つ)。
    const snippet = String(node);
    if (snippet.includes('.') || (typeof v === 'number' && !Number.isInteger(v))) {
      return new YuiValue(v, FloatType);
    }
    return new YuiValue(v);
  }

  visitStringNode(node) {
    if (typeof node.contents === 'string') {
      return new YuiValue(node.contents);
    }
    const parts = [];
    for (const content of node.contents) {
      if (typeof content === 'string') {
        parts.push(content);
      } else {
        const value = content.visit(this);
        parts.push(`${types.unbox(value)}`);
      }
    }
    return new YuiValue(parts.join(''));
  }

  visitArrayNode(node) {
    const arrayValue = new YuiValue([]);
    for (const element of node.elements) {
      const v = element.visit(this);
      arrayValue.append(v);
    }
    return arrayValue;
  }

  visitObjectNode(node) {
    const objectValue = new YuiValue({});
    for (let i = 0; i < node.elements.length; i += 2) {
      const key = node.elements[i].visit(this);
      const val = node.elements[i + 1].visit(this);
      objectValue.set_item(key, val);
    }
    return objectValue;
  }

  // ──────────────────────────────────────────────────────────
  // 変数参照・演算ノード
  // ──────────────────────────────────────────────────────────

  visitNameNode(node) {
    if (!this.hasenv(node.name)) {
      throw new YuiError(['undefined-variable', `❌${node.name}`], node);
    }
    return this.getenv(node.name);
  }

  visitGetIndexNode(node) {
    const collection = node.collection.visit(this);
    const index = node.index_node.visit(this);
    return collection.get_item(index, node);
  }

  visitArrayLenNode(node) {
    const value = node.element.visit(this);
    return new YuiValue(value.array.length);
  }

  visitMinusNode(node) {
    const value = node.element.visit(this);
    NumberType.match_or_raise(value);
    return new YuiValue(-types.unbox(value));
  }

  visitBinaryNode(node) {
    if (!this.allow_binary_ops) {
      throw new YuiError(['unsupported-operator', `🔍${node.operator.symbol}`], node);
    }
    const left = node.left_node.visit(this);
    const right = node.right_node.visit(this);
    const result = node.operator.evaluate(left, right, node);
    // JS 固有: int OP float → float の保全。
    // Python では `isinstance(3.0, float) == True` で float と判別できるが、JS では
    // `Number.isInteger(3) === true` なので、`1.5 + 1.5 = 3` のような結果が int 扱いに
    // なる。オペランドに float が含まれていたら明示的に FloatType で box する。
    if (typeof result === 'number' && (types.is_float(left) || types.is_float(right))) {
      return new YuiValue(result, FloatType);
    }
    return types.box(result);
  }

  visitFuncAppNode(node) {
    const name = `@${node.name_node.name}`;
    if (!this.hasenv(name)) {
      throw new YuiError(
        ['undefined-function', `❌${node.name_node.name}`],
        node.name_node,
      );
    }
    const fn = this.getenv(name);
    if (!(fn instanceof YuiFunction)) {
      throw new YuiError(
        ['type-error', '✅<function>', `❌${fn}`],
        node.name_node,
      );
    }

    // 引数を訪問した直後に値を確定 (再帰呼び出しで上書きされる問題を防ぐ)
    const argValues = node.arguments.map((argNode) => argNode.visit(this));

    if (node.snippet === '') {
      const argsStr = argValues.map((v) => String(v)).join(', ');
      node.snippet = `${node.name_node}(${argsStr})`;
    }

    return fn.call(argValues, node, this);
  }

  // ──────────────────────────────────────────────────────────
  // 代入・変更ノード
  // ──────────────────────────────────────────────────────────

  visitAssignmentNode(node) {
    if (typeof node.variable.update !== 'function') {
      throw new YuiError(
        ['expected-variable', `❌${node.variable}`],
        node.variable,
      );
    }
    const value = node.expression.visit(this);
    node.variable.update(value, this);
    return value;
  }

  visitIncrementNode(node) {
    if (typeof node.variable.update !== 'function') {
      throw new YuiError(
        ['expected-variable', `❌${node.variable}`],
        node.variable,
      );
    }
    const value = node.variable.visit(this);
    IntType.match_or_raise(value);
    const result = new YuiValue(types.unbox(value) + 1);
    node.variable.update(result, this);
    this.countInc();
    return result;
  }

  visitDecrementNode(node) {
    if (typeof node.variable.update !== 'function') {
      throw new YuiError(
        ['expected-variable', `❌${node.variable}`],
        node.variable,
      );
    }
    const value = node.variable.visit(this);
    IntType.match_or_raise(value);
    const result = new YuiValue(types.unbox(value) - 1);
    node.variable.update(result, this);
    this.countDec();
    return result;
  }

  visitAppendNode(node) {
    const array = node.variable.visit(this);
    const value = node.expression.visit(this);
    if (types.is_string(array) && types.is_string(value)) {
      // 文字列への文字列追加: 各文字コードを順に追加
      for (const charCode of value.array) {
        array.append(new YuiValue(charCode), node);
      }
    } else if (types.is_object(array) && types.is_string(value)) {
      // オブジェクトへのキー追加: 値は現在の要素数+1
      const key = types.unbox(value);
      const newIndex = array.array.length + 1;
      array.append(new YuiValue([key, newIndex]), node);
    } else {
      array.append(value, node);
    }
    return array;
  }

  // ──────────────────────────────────────────────────────────
  // 制御構造ノード
  // ──────────────────────────────────────────────────────────

  visitBlockNode(node) {
    let value = YuiValue.NullValue;
    for (const statement of node.statements) {
      if (statement instanceof PassNode) continue;
      value = statement.visit(this);
    }
    return value;
  }

  visitIfNode(node) {
    const left = node.left.visit(this);
    const right = node.right.visit(this);
    const result = node.operator.evaluate(left, right, node);
    this.countCompare();
    if (result) {
      return node.then_block.visit(this);
    }
    if (node.else_block) {
      return node.else_block.visit(this);
    }
    return YuiValue.NullValue;
  }

  visitBreakNode(node) {
    throw new YuiBreakException(node);
  }

  // eslint-disable-next-line no-unused-vars
  visitPassNode(_node) {
    // no-op
  }

  visitRepeatNode(node) {
    const countValue = node.count_node.visit(this);
    IntType.match_or_raise(countValue);
    const count = types.unbox(countValue);
    const result = YuiValue.NullValue;
    try {
      for (let i = 0; i < Math.abs(count); i++) {
        this.checkExecution(node);
        node.block_node.visit(this);
      }
    } catch (e) {
      if (e instanceof YuiBreakException) {
        // 正常終了
      } else {
        throw e;
      }
    }
    return result;
  }

  visitReturnNode(node) {
    let value = null;
    if (node.expression instanceof ASTNode) {
      value = node.expression.visit(this);
    }
    throw new YuiReturnException(value, node);
  }

  visitFuncDefNode(node) {
    const params = node.parameters.map((p) => p.name);
    const fn = new LocalFunction(node.name_node.name, params, node.body);
    this.setenv(`@${node.name_node.name}`, fn);
    return fn;
  }

  // ──────────────────────────────────────────────────────────
  // 出力・テストノード
  // ──────────────────────────────────────────────────────────

  isInTheTopLevel() {
    return this.call_frames.length === 0;
  }

  visitPrintExpressionNode(node) {
    const value = node.expression.visit(this);
    if (node.expression instanceof StringNode) {
      this.printValue(value); // 常にプリント
    } else if (node.inspection || (this.isInTheTopLevel() && !node.grouping)) {
      this.printValue(value, node.expression);
    }
    return value;
  }

  visitAssertNode(node) {
    let tested = null;
    let referenceValue = null;
    try {
      tested = node.test.visit(this);
      referenceValue = node.reference.visit(this);
      if (tested.type.equals(tested, referenceValue)) {
        this.test_passed.push(String(node.test));
        return YuiValue.TrueValue;
      }
    } catch (e) {
      if (e instanceof YuiError) {
        throw e;
      }
      // それ以外の例外は assertion-failed に変換 (Python 側 except Exception: pass と同じ)
    }
    throw new YuiError(
      ['assertion-failed', `🔍${node.test}`, `❌${tested}`, `✅${referenceValue}`],
      node,
    );
  }

  visitImportNode(node) {
    const modules = [];
    const isNull =
      node.module_name == null ||
      (node.module_name instanceof ConstNode && node.module_name.native_value === null);
    if (isNull) {
      standardLib(modules);
    }
    for (const [names, fn] of modules) {
      for (const name of names.split('|')) {
        this.setenv(`@${name}`, new NativeFunction(fn));
      }
    }
    return YuiValue.NullValue;
  }

  loadStdlib() {
    this.visitImportNode(new ImportNode(null));
  }

  visitCatchNode(node) {
    try {
      return node.expression.visit(this);
    } catch (e) {
      if (e instanceof YuiError) {
        return new YuiValue(`💣${e.messages[0]}`);
      }
      throw e;
    }
  }
}
