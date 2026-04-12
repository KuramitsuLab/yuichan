// yuicoding.js — AST → ソースコード生成 (CodingVisitor)
// Python 版 yuichan/yuicoding.py の移植
//
// 依存:
//   - yuiast.js (ノードクラスの instanceof 判定用)
//   - yuisyntax.js (YuiSyntax, loadSyntax)
//   - yuistdlib.js (funcnamemap 構築用, 遅延 import で循環回避)
//
// CodingVisitor は YuiSyntax を継承し、構文 JSON から得た終端記号を使って
// AST を指定言語 (Yui-Classic, pylike, jslike, ...) に書き戻す。

import {
  ASTNode,
  StatementNode,
  BlockNode,
  BinaryNode,
  FuncAppNode,
  FuncDefNode,
  PassNode,
  PrintExpressionNode,
  IfNode,
} from './yuiast.js';
import { YuiSyntax, loadSyntax } from './yuisyntax.js';
import { standardLib } from './yuistdlib.js';

// Python 側の _no_seg セットに相当
const _NO_SEG = new Set(['string-end', 'string-interpolation-end', 'extra-name-end']);

// 直前に空白/区切りがあれば word-segment 不要と判定する終端文字集合
const _NO_SPACE_DEFAULT = ' \n([{';

// terminal() で word-segment を挿入しない先頭文字 (ASCII 記号)
const _NO_WORDSEG_LEADING = ',()[]{}:;"\'.';

export class CodingVisitor extends YuiSyntax {
  /**
   * @param {string|object} syntaxJson — 構文名 (例 "yui") または terminals オブジェクト
   * @param {string|null} functionLanguage — 'emoji'/'ja'/'en' または null
   */
  constructor(syntaxJson, functionLanguage = null) {
    if (typeof syntaxJson === 'string') {
      syntaxJson = loadSyntax(syntaxJson);
    }
    super(syntaxJson);
    this.buffer = [];
    this.indentString = '   ';
    this.indentLevel = 0;
    this.justLinefeeded = false;
    this.funcnamemap = {};
    this.randomSeed = null;
    this.loadFunctionmap(functionLanguage);
  }

  /**
   * 標準ライブラリの関数名辞書をロードする。
   * Python 側は `targets.index(function_language)` で ValueError を投げるので、
   * JS 側も同様に `indexOf === -1` で throw する。
   */
  loadFunctionmap(functionLanguage = null) {
    if (functionLanguage == null) {
      this.funcnamemap = {};
      return false;
    }
    const [targetsStr, modules] = standardLib([]);
    const targets = targetsStr.toLowerCase().split('|');
    const index = targets.indexOf(functionLanguage);
    if (index < 0) {
      throw new Error(
        `Name '${functionLanguage}' not found in standard library targets: ${targets}`,
      );
    }
    this.funcnamemap = {};
    for (const [namesStr, _fn] of modules) {
      const names = namesStr.split('|');
      for (const name of names) {
        this.funcnamemap[name] = names[index];
      }
    }
    return true;
  }

  /**
   * AST ノードからソースコードを生成する。
   * node が StatementNode でなく、かつ print-begin が定義されていれば、
   * 自動的に PrintExpressionNode でラップして出力する (Python 版と同じ)。
   */
  emit(node, indentString = '   ', randomSeed = null) {
    this.buffer = [];
    this.indentLevel = 0;
    this.indentString = indentString;
    this.justLinefeeded = true;
    this.randomSeed = randomSeed;
    if (!(node instanceof StatementNode) && this.isDefined('print-begin')) {
      new PrintExpressionNode(node).visit(this);
    } else {
      node.visit(this);
    }
    return this.buffer.join('');
  }

  lastChar() {
    if (this.buffer.length === 0) return '\n';
    const tail = this.buffer[this.buffer.length - 1];
    return tail[tail.length - 1];
  }

  linefeed() {
    if (!this.justLinefeeded) {
      if (this.indentString) {
        this.buffer.push('\n' + this.indentString.repeat(this.indentLevel));
      } else {
        this.buffer.push(' ');
      }
      this.justLinefeeded = true;
    }
  }

  string(text) {
    if (text.includes('\n')) {
      const lines = text.split('\n');
      for (let i = 0; i < lines.length - 1; i++) {
        this.string(lines[i]);
        this.linefeed();
      }
      this.string(lines[lines.length - 1]);
      return;
    }
    if (text.length === 0) return;
    if (text === ' ' && this.lastChar() === ' ') {
      return; // 連続するスペースを避ける
    }
    this.buffer.push(text);
    this.justLinefeeded = false;
  }

  /**
   * 単語境界を必要に応じて挿入する。
   * - word-segmenter が定義されている言語: 常に空白を挿入
   * - それ以外: randomSeed が設定されていれば 50% の確率で挿入 (Python 版と同じ)
   */
  wordSegment(noSpaceIfLastChars = _NO_SPACE_DEFAULT) {
    if (this.isDefined('word-segmenter')) {
      if (!noSpaceIfLastChars.includes(this.lastChar())) {
        this.string(' ');
      }
    } else if (this.randomSeed != null) {
      if (!noSpaceIfLastChars.includes(this.lastChar())) {
        // Python と同じく Math.random() を使う (seed は実際には使われない)
        if (Math.random() < 0.5) {
          this.string(' ');
        }
      }
    }
  }

  terminal(terminal, _ifUndefined = null, linefeedBefore = false) {
    if (terminal === 'linefeed') {
      this.linefeed();
      return;
    }
    if (!this.isDefined(terminal)) return;
    const token = this.forExample(terminal);
    if (token === '') return;
    if (linefeedBefore) {
      this.linefeed();
    }
    if (!_NO_SEG.has(terminal) && !_NO_WORDSEG_LEADING.includes(token[0])) {
      this.wordSegment();
    }
    this.string(token);
  }

  comment(comment) {
    if (!comment) return;
    if (this.isDefined('comment-begin') && this.isDefined('comment-end')) {
      this.terminal('comment-begin');
      this.string(` ${comment}`);
      this.terminal('comment-end');
    } else if (this.isDefined('line-comment-begin')) {
      for (const line of comment.split(/\r?\n/)) {
        this.terminal('line-comment-begin');
        this.string(` ${line}`);
        this.linefeed();
      }
    }
  }

  expression(node, grouping = null) {
    this.wordSegment();
    if (grouping && this.isDefined('grouping-begin') && this.isDefined('grouping-end')) {
      this.terminal('grouping-begin');
      node.visit(this);
      this.terminal('grouping-end');
    } else {
      node.visit(this);
    }
  }

  statement(node) {
    node.visit(this);
    this.comment(node.comment);
  }

  block(node) {
    if (!(node instanceof BlockNode)) {
      new BlockNode([node]).visit(this);
    } else {
      node.visit(this);
    }
    // Python 側と同様、末尾の word_segment は呼ばない (pylike パーサ互換)
  }

  escape(text) {
    return text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
  }

  // ─────────────────────────────────────────────
  // AST ノード Visitors
  // ─────────────────────────────────────────────

  visitASTNode(node) {
    const name = node.constructor.nodeName ?? node.constructor.name;
    this.string(`FIXME: ${name}`);
  }

  visitConstNode(node) {
    if (node.native_value === null) {
      this.terminal('null');
    } else if (node.native_value === true) {
      this.terminal('boolean-true');
    } else {
      this.terminal('boolean-false');
    }
  }

  visitNumberNode(node) {
    this.terminal('number-begin');
    const v = node.native_value;
    if (typeof v === 'number' && !Number.isInteger(v)) {
      this.string(v.toFixed(6));
    } else {
      this.string(String(v));
    }
    this.terminal('number-end');
  }

  visitStringNode(node) {
    this.terminal('string-begin');
    if (typeof node.contents === 'string') {
      this.string(this.escape(node.contents));
    } else {
      for (const content of node.contents) {
        if (typeof content === 'string') {
          this.string(this.escape(content));
        } else {
          this.terminal('string-interpolation-begin');
          content.visit(this);
          this.terminal('string-interpolation-end');
        }
      }
    }
    this.terminal('string-end');
  }

  visitNameNode(node) {
    this.terminal('name-begin');
    this.string(node.name);
    this.terminal('name-end');
  }

  visitArrayNode(node) {
    // いったん別バッファに書き出して 1 行版を試す
    const savedBuffer = this.buffer;
    this.buffer = [];
    this.terminal('array-begin');
    node.elements.forEach((el, i) => {
      if (i > 0) this.terminal('array-separator');
      this.expression(el);
    });
    this.terminal('array-end');
    const content = this.buffer.join('');
    this.buffer = savedBuffer;
    if (content.length <= 80 && !content.includes('\n')) {
      this.string(content);
      return;
    }
    // 折り返し版
    this.terminal('array-begin');
    this.indentLevel += 1;
    this.linefeed();
    node.elements.forEach((el, i) => {
      if (i > 0) {
        this.terminal('array-separator');
        this.linefeed();
      }
      this.expression(el);
    });
    this.indentLevel -= 1;
    this.linefeed();
    this.terminal('array-end');
  }

  visitObjectNode(node) {
    const savedBuffer = this.buffer;
    this.buffer = [];
    this.terminal('object-begin');
    for (let i = 0; i < node.elements.length; i += 2) {
      if (i > 0) this.terminal('object-separator');
      const keyNode = node.elements[i];
      const valueNode = node.elements[i + 1];
      this.expression(keyNode);
      this.terminal('key-value-separator');
      this.expression(valueNode);
    }
    this.terminal('object-end');
    const content = this.buffer.join('');
    this.buffer = savedBuffer;
    if (content.length <= 80 && !content.includes('\n')) {
      this.string(content);
      return;
    }
    // 折り返し版
    this.terminal('object-begin');
    this.indentLevel += 1;
    this.linefeed();
    for (let i = 0; i < node.elements.length; i += 2) {
      if (i > 0) {
        this.terminal('object-separator');
        this.linefeed();
      }
      const keyNode = node.elements[i];
      const valueNode = node.elements[i + 1];
      this.expression(keyNode);
      this.terminal('key-value-separator');
      this.expression(valueNode);
    }
    this.indentLevel -= 1;
    this.linefeed();
    this.terminal('object-end');
  }

  visitMinusNode(node) {
    if (this.isDefined('minus-begin')) {
      this.terminal('minus-begin');
      this.expression(node.element);
      this.terminal('minus-end');
    } else if (this.isDefined('unary-minus')) {
      this.terminal('unary-minus');
      node.element.visit(this); // 負の数で不要な word_segment を避ける
    } else {
      this.visitASTNode(node);
    }
  }

  visitBinaryNode(node) {
    const symbol = node.operator.symbol;
    if (this.isDefined('binary-infix-prefix-begin')) {
      this.terminal(`binary-infix-prefix${symbol}`);
      this.wordSegment();
      this.expression(node.left_node);
      this.wordSegment();
      this.expression(node.right_node);
      this.terminal('binary-infix-prefix-end');
    } else {
      this.expression(node.left_node, this.checkLeftGrouping(node, node.left_node));
      this.wordSegment();
      this.terminal(`binary-infix${symbol}`);
      this.wordSegment();
      this.expression(node.right_node, this.checkRightGrouping(node, node.right_node));
    }
  }

  checkLeftGrouping(parent, child) {
    if (!(child instanceof BinaryNode)) return false;
    const parentPrec = parent.operator.precedence;
    const childPrec = child.operator.precedence;
    return childPrec > parentPrec;
  }

  checkRightGrouping(parent, child) {
    if (!(child instanceof BinaryNode)) return false;
    const parentPrec = parent.operator.precedence;
    const childPrec = child.operator.precedence;
    return childPrec >= parentPrec;
  }

  visitArrayLenNode(node) {
    if (this.isDefined('property-length')) {
      this.expression(node.element);
      this.terminal('property-length');
    } else if (this.isDefined('unary-length')) {
      this.terminal('unary-length');
      this.expression(node.element);
    } else if (this.isDefined('length-begin')) {
      this.terminal('length-begin');
      this.expression(node.element);
      this.terminal('length-end');
    }
  }

  visitGetIndexNode(node) {
    let collection = node.collection;
    let index = node.index_node;
    if (this.get('array-indexer-order') === 'reversed') {
      [collection, index] = [index, collection];
    }
    this.terminal('array-indexer-begin');
    this.expression(collection);
    this.terminal('array-indexer-infix');
    this.terminal('array-indexer-suffix');
    this.expression(index);
    this.terminal('array-indexer-end');
  }

  visitFuncAppNode(node) {
    this.terminal('funcapp-begin');
    const originalName = node.name_node.name;
    const name = Object.prototype.hasOwnProperty.call(this.funcnamemap, originalName)
      ? this.funcnamemap[originalName]
      : originalName;
    this.string(name);

    if (this.isDefined('funcapp-noarg') && node.arguments.length === 0) {
      this.terminal('funcapp-noarg');
    } else {
      this.terminal('funcapp-args-begin');
      node.arguments.forEach((arg, i) => {
        if (i > 0) this.terminal('funcapp-separator');
        const grouping = arg instanceof FuncAppNode && !this.isDefined('funcapp-args-end');
        this.expression(arg, grouping);
      });
      this.terminal('funcapp-args-end');
      this.terminal('funcapp-end');
    }
  }

  visitAssignmentNode(node) {
    let variable = node.variable;
    let expression = node.expression;
    if (this.get('assignment-order') === 'reversed') {
      [variable, expression] = [expression, variable];
    }
    this.terminal('assignment-begin');
    this.expression(variable);
    this.terminal('assignment-infix');
    this.expression(expression);
    this.terminal('assignment-end');
  }

  visitIncrementNode(node) {
    this.terminal('increment-begin');
    this.expression(node.variable);
    this.terminal('increment-end');
  }

  visitDecrementNode(node) {
    this.terminal('decrement-begin');
    this.expression(node.variable);
    this.terminal('decrement-end');
  }

  visitAppendNode(node) {
    let variable = node.variable;
    let expression = node.expression;
    if (this.get('assignment-order') === 'reversed') {
      [variable, expression] = [expression, variable];
    }
    this.terminal('append-begin');
    this.expression(variable);
    this.terminal('append-infix');
    this.expression(expression);
    this.terminal('append-end');
  }

  visitBreakNode(_node) {
    this.terminal('break');
  }

  visitPassNode(_node) {
    // block 内で処理される
  }

  visitReturnNode(node) {
    if (node.expression instanceof ASTNode) {
      this.terminal('return-begin');
      this.expression(node.expression);
      this.terminal('return-end');
    } else {
      this.terminal('return-none');
    }
  }

  visitPrintExpressionNode(node) {
    if (node.grouping) {
      this.terminal('grouping-begin');
      this.expression(node.expression);
      this.terminal('grouping-end');
      return;
    }
    if (node.inspection) {
      this.terminal('unary-inspect');
      this.expression(node.expression);
    } else {
      this.terminal('print-begin');
      this.expression(node.expression);
      this.terminal('print-end');
    }
  }

  visitIfNode(node) {
    this.terminal('if-begin');
    this.terminal('if-condition-begin');
    if (node.left instanceof BinaryNode && node.left.comparative) {
      this.expression(node.left);
    } else {
      const opSymbol = String(node.operator);
      if (this.isDefined(`if-prefix${opSymbol}`)) {
        this.terminal(`if-prefix${opSymbol}`);
        this.expression(node.left);
        this.expression(node.right);
      } else {
        this.expression(node.left);
        if (this.isDefined(`if-infix${opSymbol}`)) {
          this.terminal(`if-infix${opSymbol}`);
        } else {
          this.terminal('if-infix');
        }
        this.expression(node.right);
        if (this.isDefined(`if-suffix${opSymbol}`)) {
          this.terminal(`if-suffix${opSymbol}`);
        } else {
          this.terminal('if-suffix');
        }
      }
    }
    this.terminal('if-condition-end');
    this.terminal('if-then');
    this.block(node.then_block);
    if (node.else_block && !(node.else_block instanceof PassNode)) {
      if (this.isDefined('if-else-if') && node.else_block instanceof IfNode) {
        this.terminal('if-else-if', null, true);
        this.block(node.else_block);
      } else {
        this.terminal('if-else', null, true);
        this.block(node.else_block);
      }
    }
    this.terminal('if-end', null, true);
  }

  visitRepeatNode(node) {
    let countNode = node.count_node;
    let blockNode = node.block_node;
    if (this.get('repeat-order') === 'reversed') {
      [countNode, blockNode] = [blockNode, countNode];
    }
    this.terminal('repeat-begin');
    this.expression(countNode);
    this.terminal('repeat-times');
    this.terminal('repeat-block');
    this.block(blockNode);
    this.terminal('repeat-end', null, true);
  }

  visitFuncDefNode(node) {
    this.terminal('funcdef-begin');
    this.terminal('funcdef-name-begin');
    this.expression(node.name_node);
    this.terminal('funcdef-name-end');
    if (this.isDefined('funcdef-noarg') && node.parameters.length === 0) {
      this.terminal('funcdef-noarg');
    } else {
      this.terminal('funcdef-args-begin');
      node.parameters.forEach((param, i) => {
        if (i > 0) this.terminal('funcdef-arg-separator');
        this.expression(param);
      });
      this.terminal('funcdef-args-end');
    }
    this.terminal('funcdef-block');
    this.block(node.body);
    this.terminal('funcdef-end', null, true);
  }

  visitImportNode(_node) {
    this.terminal('import-standard');
  }

  visitAssertNode(node) {
    let testNode = node.test;
    let referenceNode = node.reference;
    if (this.get('assert-order') === 'reversed') {
      [testNode, referenceNode] = [referenceNode, testNode];
    }
    this.terminal('assert-begin');
    this.expression(testNode);
    this.terminal('assert-infix');
    this.expression(referenceNode);
    this.terminal('assert-end');
  }

  visitCatchNode(node) {
    this.terminal('catch-begin');
    this.expression(node.expression);
    this.terminal('catch-end');
  }

  visitBlockNode(node) {
    if (!node.top_level) {
      this.terminal('block-begin-prefix');
      this.terminal('block-begin');
      this.indentLevel += 1;
      this.linefeed();
    }

    if (node.statements.length === 0) {
      this.terminal('pass');
    } else {
      node.statements.forEach((statement, i) => {
        if (i > 0) this.linefeed();
        if (!(statement instanceof StatementNode) && this.isDefined('print-begin')) {
          new PrintExpressionNode(statement).visit(this);
        } else {
          statement.visit(this);
        }
        if (statement instanceof FuncDefNode) {
          this.linefeed();
        }
        if (!this.justLinefeeded) {
          this.terminal('statement-separator');
        }
        if (statement instanceof PassNode) {
          this.linefeed();
        }
        this.comment(statement.comment);
      });
    }

    if (!node.top_level) {
      this.indentLevel -= 1;
      this.justLinefeeded = false; // インデント変化後に正しい linefeed をさせる
      this.terminal('block-end', null, true);
    }
  }
}

