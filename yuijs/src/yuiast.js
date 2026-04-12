// yuiast.js — AST ノード定義
// Python 版 yuichan/yuiast.py の移植
//
// 依存: yuitypes.js (OPERATORS のみ)
//
// JS ⇔ Python の主な差分:
// - Python の ABC はそのままの JS class で代替 (インスタンス化を禁じる runtime check は付けない)。
// - `visit(visitor)` は Python の `getattr(visitor, 'visit' + class.__name__)` と等価。
//   ただし JS のクラス名はミニファイヤに書き換えられるため、モジュール末尾の
//   オブジェクトリテラル `{BlockNode, ...}` でキー名 (= 論理名) を明示的に登録して
//   各 class に static `nodeName` を付与する。dispatch はこの値を優先して参照する。
//   これにより esbuild/terser/webpack での minify (--keep-names なし) でも動く。
// - `_node()` の dict 分岐: JS では plain object を `Object.prototype` チェックで判定し、
//   ASTNode インスタンスとは厳密に区別する。
// - Python は `int/float` 区別があるので `isinstance(node, (int, float))` で NumberNode にしていたが、
//   JS は `typeof === 'number'` でまとめて NumberNode 化する。NaN/Infinity はそのまま渡る。

import { OPERATORS } from './yuitypes.js';

// ─────────────────────────────────────────────
// ASTNode 基底クラス
// ─────────────────────────────────────────────
export class ASTNode {
  constructor() {
    this.filename = 'main.yui';
    this.source = '';
    this.pos = 0;
    this.end_pos = -1;
    this.comment = null;
  }

  setpos(source, pos, end_pos = -1, filename = 'main.yui') {
    this.source = source;
    this.pos = pos;
    this.end_pos = end_pos;
    this.filename = filename;
    this.comment = null;
    return this;
  }

  /** ノードに対応するソースコードのスニペットを返す */
  toString() {
    // Python: self.source[self.pos:self.end_pos]
    // end_pos === -1 のときは Python 側も "source[pos:-1]" となり末尾 1 文字を除外する。
    // 挙動を一致させるため JS でもそのまま slice する。
    return this.source.slice(this.pos, this.end_pos);
  }

  evaluate(runtime) {
    return this.visit(runtime);
  }

  /** ノードを訪問する。visitor は visit{ClassName} メソッドを実装すること。
   *  minify 耐性のため、モジュール末尾で登録される static `nodeName` を優先して
   *  参照する。未登録のサブクラスでは constructor.name にフォールバックする。 */
  visit(visitor) {
    const name = this.constructor.nodeName ?? this.constructor.name;
    const methodName = 'visit' + name;
    const method = visitor[methodName];
    if (typeof method !== 'function') {
      throw new TypeError(
        `visitor is missing method ${methodName} for ${name}`
      );
    }
    return method.call(visitor, this);
  }

  // パース後フック (サブクラスでオーバーライド可)
  parsed(_orderPolicy = '') {
    // no-op
  }

  /**
   * ソースコード内の位置をエラー表示用の情報に変換する。
   * Returns: [line, col, snippet]
   *   - line: 行番号 (1始まり)
   *   - col:  列番号 (1始まり)
   *   - snippet: エラー行のコードスニペット
   */
  extract() {
    let linenum = 1;
    let col = 1;
    let start = 0;

    // Python: for i, char in enumerate(self.source): if i == self.pos: break
    const src = this.source;
    const len = src.length;
    for (let i = 0; i < len; i++) {
      if (i === this.pos) break;
      if (src.charCodeAt(i) === 10 /* '\n' */) {
        linenum += 1;
        col = 1;
        start = i + 1;
      } else {
        col += 1;
      }
    }

    let endPos = src.indexOf('\n', start);
    if (endPos === -1) endPos = src.length;
    return [linenum, col, src.slice(start, endPos)];
  }
}

// ─────────────────────────────────────────────
// ExpressionNode / StatementNode (抽象中間クラス)
// ─────────────────────────────────────────────
export class ExpressionNode extends ASTNode {}
export class StatementNode extends ASTNode {}

// ─────────────────────────────────────────────
// _node 変換ヘルパ
// ─────────────────────────────────────────────
//
// Python 版:
//   - None/bool → ConstNode
//   - int/float → NumberNode
//   - str       → "📦" 接頭辞なら NameNode, それ以外は StringNode
//   - list      → ArrayNode (要素は再帰変換)
//   - dict      → ObjectNode ([key, value, key, value, ...] の並び)
//   - ASTNode   → そのまま
//
// JS 版もこれに準拠する。plain object 判定は Object.prototype / null prototype のみ許可する
// (Map や class インスタンスは弾く) ことで ASTNode と厳格に区別する。

function _isPlainObject(x) {
  if (x === null || typeof x !== 'object') return false;
  if (Array.isArray(x)) return false;
  const proto = Object.getPrototypeOf(x);
  return proto === Object.prototype || proto === null;
}

export function _node(node) {
  if (node === null || node === undefined) {
    return new ConstNode(null);
  }
  if (typeof node === 'boolean') {
    return new ConstNode(node);
  }
  if (typeof node === 'number') {
    return new NumberNode(node);
  }
  if (typeof node === 'string') {
    if (node.startsWith('📦')) {
      // "📦 name" → NameNode("name")
      return new NameNode(node.slice('📦'.length).trim());
    }
    return new StringNode(node);
  }
  if (Array.isArray(node)) {
    return new ArrayNode(node.map((e) => _node(e)));
  }
  if (node instanceof ASTNode) {
    return node;
  }
  if (_isPlainObject(node)) {
    const entries = [];
    for (const [k, v] of Object.entries(node)) {
      entries.push(_node(String(k)));
      entries.push(_node(v));
    }
    return new ObjectNode(entries);
  }
  throw new TypeError(`_node: unsupported value ${node}`);
}

// ─────────────────────────────────────────────
// 式ノード
// ─────────────────────────────────────────────

/** null/boolean 値 (native_value: null | true | false) */
export class ConstNode extends ExpressionNode {
  constructor(value = null) {
    super();
    this.native_value = value;
  }
}

/** 数値リテラル */
export class NumberNode extends ExpressionNode {
  constructor(value) {
    super();
    this.native_value = value;
  }
}

/** 配列の長さ (|配列|) */
export class ArrayLenNode extends ExpressionNode {
  constructor(element) {
    super();
    this.element = _node(element);
  }
}

/** 負の数 (-式) */
export class MinusNode extends ExpressionNode {
  constructor(element) {
    super();
    this.element = _node(element);
  }
}

/** 文字列リテラル ("...") — 補間あり/なし */
export class StringNode extends ExpressionNode {
  constructor(contents) {
    super();
    // Python 版は str も List[str | ExpressionNode] もそのまま保持する。
    // JS 版も同じく保持する (runtime 側で分岐)。
    this.contents = contents;
  }
}

/** 配列リテラル [要素, ...] */
export class ArrayNode extends ExpressionNode {
  constructor(elements) {
    super();
    this.elements = elements.map((e) => _node(e));
  }
}

/** オブジェクトリテラル {要素, ...} — [key, value, key, value, ...] の並びで格納 */
export class ObjectNode extends ExpressionNode {
  constructor(elements) {
    super();
    this.elements = elements.map((e) => _node(e));
  }
}

/** 変数参照 */
export class NameNode extends ExpressionNode {
  constructor(name) {
    super();
    this.name = name;
  }

  /** 変数の値を更新する (代入先としての動作) */
  update(value, visitor) {
    visitor.setenv(this.name, value);
  }
}

/** 配列/オブジェクトのインデックス取得 */
export class GetIndexNode extends ASTNode {
  constructor(collection, index, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [collection, index] = [index, collection];
    }
    this.collection = _node(collection);
    this.index_node = _node(index);
  }

  /** インデックス先への代入 */
  update(value, visitor) {
    const collection = this.collection.visit(visitor);
    const index = this.index_node.visit(visitor);
    collection.set_item(index, value, this);
  }
}

/** 二項演算子 */
export class BinaryNode extends ASTNode {
  constructor(operator, left, right) {
    super();
    const op = OPERATORS[operator];
    if (op === undefined) {
      throw new Error(`BinaryNode: unknown operator ${operator}`);
    }
    this.operator = op;
    this.left_node = _node(left);
    this.right_node = _node(right);
    this.comparative = op.comparative;
  }
}

/** 関数呼び出し 名前(引数, ...) */
export class FuncAppNode extends ExpressionNode {
  constructor(name, args, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [name, args] = [args, name];
    }
    // Python: NameNode(name) if isinstance(name, str) else _node(name)
    // — 文字列が直接渡ってきた場合は StringNode ではなく NameNode 扱い
    this.name_node = typeof name === 'string' ? new NameNode(name) : _node(name);
    this.arguments = args.map((arg) => _node(arg));
    this.snippet = this.toString();
  }
}

// ─────────────────────────────────────────────
// 文ノード
// ─────────────────────────────────────────────

/** 代入 (変数 = 式) */
export class AssignmentNode extends StatementNode {
  constructor(variable, expression, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [variable, expression] = [expression, variable];
    }
    this.variable = _node(variable);
    this.expression = _node(expression);
  }
}

/** インクリメント (変数 を 増やす) */
export class IncrementNode extends StatementNode {
  constructor(variable) {
    super();
    this.variable = _node(variable);
  }
}

/** デクリメント (変数 を 減らす) */
export class DecrementNode extends StatementNode {
  constructor(variable) {
    super();
    this.variable = _node(variable);
  }
}

/** 配列への追加 (変数の末尾に 値 を追加する) */
export class AppendNode extends StatementNode {
  constructor(variable, expression, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [variable, expression] = [expression, variable];
    }
    this.variable = _node(variable);
    this.expression = _node(expression);
  }
}

/** 文の並び */
export class BlockNode extends StatementNode {
  constructor(statements, topLevel = false) {
    super();
    if (statements instanceof StatementNode) {
      this.statements = [statements];
    } else {
      if (!Array.isArray(statements)) {
        throw new TypeError('BlockNode: statements must be a list or a StatementNode');
      }
      this.statements = statements;
    }
    this.top_level = topLevel;
  }
}

/** 条件分岐 (もし〜ならば) */
export class IfNode extends StatementNode {
  constructor(left, operator, right, thenBlock, elseBlock = null) {
    super();
    const op = OPERATORS[operator];
    if (op === undefined) {
      throw new Error(`IfNode: unknown operator ${operator}`);
    }
    this.left = _node(left);
    this.operator = op;
    this.right = _node(right);
    this.then_block = _node(thenBlock);
    this.else_block = elseBlock !== null && elseBlock !== undefined
      ? _node(elseBlock)
      : new PassNode();
  }
}

/** break */
export class BreakNode extends StatementNode {}

/** pass / コメントのみの行 */
export class PassNode extends StatementNode {
  constructor(comment = null) {
    super();
    this.comment = comment;
  }
}

/** ループ (N回 くり返す) */
export class RepeatNode extends StatementNode {
  constructor(countNode, blockNode, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [countNode, blockNode] = [blockNode, countNode];
    }
    this.count_node = _node(countNode);
    this.block_node = _node(blockNode);
  }
}

/** ライブラリのインポート (標準ライブラリを使う) */
export class ImportNode extends StatementNode {
  constructor(moduleName = null) {
    super();
    // Python: NameNode(module_name) if isinstance(module_name, str) else _node(module_name)
    this.module_name = typeof moduleName === 'string'
      ? new NameNode(moduleName)
      : _node(moduleName);
  }
}

/** 関数からの返値 (式 が 答え) */
export class ReturnNode extends StatementNode {
  constructor(expression) {
    super();
    this.expression = _node(expression);
  }
}

/** 関数定義 */
export class FuncDefNode extends StatementNode {
  constructor(nameNode, parameters, body) {
    super();
    this.name_node = _node(nameNode);
    this.parameters = parameters.map((p) => _node(p));
    this.body = _node(body);
  }
}

/** 式の出力 (単独で書かれた式) */
export class PrintExpressionNode extends StatementNode {
  constructor(expression, inspection = false, grouping = false) {
    super();
    this.expression = _node(expression);
    this.inspection = inspection;
    this.grouping = grouping;
  }
}

/** テストケース (>>> 式 → 期待値) */
export class AssertNode extends StatementNode {
  constructor(test, reference, orderPolicy = '') {
    super();
    if (orderPolicy === 'reversed') {
      [test, reference] = [reference, test];
    }
    this.test = _node(test);
    this.reference = _node(reference);
  }
}

/** エラーをキャッチするノード (デバッグ用) */
export class CatchNode extends ExpressionNode {
  constructor(expression) {
    super();
    this.expression = _node(expression);
  }
}

// ─────────────────────────────────────────────
// visitor dispatch 名の登録
// ─────────────────────────────────────────────
//
// minify 耐性のため、各 AST class に論理名 (static `nodeName`) を明示的に付与する。
// 下のオブジェクトリテラルのキー (`ConstNode:`, `NumberNode:` …) は文字列として
// ソース上に現れるため、esbuild / terser / webpack 等のミニファイヤはクラス変数
// 名 (値側) を書き換えても、このキー (= 論理名) はそのまま保持する。
//
// 登録されていないクラス (利用者側のサブクラス等) は `constructor.name` に
// フォールバックするため、開発時 (非 minify) では従来通り動作する。
const _AST_CLASSES = {
  ASTNode,
  ExpressionNode,
  StatementNode,
  ConstNode,
  NumberNode,
  StringNode,
  ArrayLenNode,
  MinusNode,
  ArrayNode,
  ObjectNode,
  NameNode,
  GetIndexNode,
  BinaryNode,
  FuncAppNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  IfNode,
  BreakNode,
  PassNode,
  RepeatNode,
  ImportNode,
  ReturnNode,
  FuncDefNode,
  PrintExpressionNode,
  AssertNode,
  CatchNode,
};

for (const [name, cls] of Object.entries(_AST_CLASSES)) {
  Object.defineProperty(cls, 'nodeName', {
    value: name,
    writable: false,
    enumerable: false,
    configurable: false,
  });
}
