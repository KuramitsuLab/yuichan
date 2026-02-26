// yuicoding.js — code generation visitor (port of yuichan/yuicoding.py)

import {
    ASTNode, ConstNode, NameNode,
    StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode, FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode, StatementNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, CatchNode, ImportNode,
} from './yuiast.js';

import { YuiType } from './yuitypes.js';
import { loadSyntax, YuiSyntax } from './yuisyntax.js';

export class CodingVisitor extends YuiSyntax {
    constructor(syntaxJson) {
        if (typeof syntaxJson === 'string') {
            syntaxJson = loadSyntax(syntaxJson);
        }
        super(syntaxJson);
        this.buffer = [];
        this.indent = 0;
        this.justLinefeeded = false;
    }

    emit(node, randomSeed = null) {
        this.buffer = [];
        this.indent = 0;
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
        const last = this.buffer[this.buffer.length - 1];
        return last[last.length - 1];
    }

    linefeed() {
        if (!this.justLinefeeded) {
            this.buffer.push('\n' + '  '.repeat(this.indent));
            this.justLinefeeded = true;
        }
    }

    string(text) {
        if (text.includes('\n')) {
            const lines = text.split('\n');
            for (const line of lines.slice(0, -1)) {
                this.string(line);
                this.linefeed();
            }
            this.string(lines[lines.length - 1]);
            return;
        }
        if (text.length === 0) return;
        if (text === ' ' && this.lastChar() === ' ') return; // avoid consecutive spaces
        this.buffer.push(text);
        this.justLinefeeded = false;
    }

    wordSegment(noSpaceIfLastChars = ' \n([{') {
        if (this.isDefined('word-segmenter')) {
            if (!noSpaceIfLastChars.includes(this.lastChar())) {
                this.string(' ');
            }
        }
    }

    terminal(terminal, { ifUndefined = null, linefeedBefore = false } = {}) {
        if (terminal === 'linefeed') {
            this.linefeed();
            return;
        }
        if (!this.isDefined(terminal)) return;
        const token = this.forExample(terminal);
        if (token === '') {
            console.warn(`Warning: terminal '${terminal}' is empty string`);
            return;
        }
        if (linefeedBefore) this.linefeed();
        if (!',()[]{}:"\'.' .includes(token[0])) {
            this.wordSegment();
        }
        this.string(token);
    }

    comment(comment) {
        if (!comment) return;
        if (this.isDefined('comment-begin') && this.isDefined('comment-end')) {
            this.terminal('comment-begin');
            this.string(comment);
            this.terminal('comment-end');
        } else if (this.isDefined('line-comment-begin')) {
            for (const line of comment.split('\n')) {
                this.terminal('line-comment-begin');
                this.string(` ${line}`);
                this.linefeed();
            }
        }
    }

    expression(node) {
        this.wordSegment();
        node.visit(this);
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
        // this.wordSegment();  // pylike で末尾スペースが付きパースエラーになるため無効化
    }

    escape(text) {
        return text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    }

    // ─────────────────────────────────────────────
    // Visitor methods
    // ─────────────────────────────────────────────

    visitASTNode(node) {
        this.string(`FIXME: ${node.constructor.name}`);
    }

    visitConstNode(node) {
        if (node.nativeValue === null) {
            this.terminal('null');
        } else if (node.nativeValue === true) {
            this.terminal('boolean-true');
        } else {
            this.terminal('boolean-false');
        }
    }

    visitNumberNode(node) {
        this.terminal('number-begin');
        this.string(YuiType.arrayviewS(node.nativeValue));
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
        const savedBuffer = this.buffer;
        this.buffer = [];
        this.terminal('array-begin');
        node.elements.forEach((element, i) => {
            if (i > 0) this.terminal('array-separator');
            this.expression(element);
        });
        this.terminal('array-end');
        const content = this.buffer.join('');
        this.buffer = savedBuffer;
        if (content.length <= 80 && !content.includes('\n')) {
            this.string(content);
            return;
        }
        this.terminal('array-begin');
        this.indent++;
        this.linefeed();
        node.elements.forEach((element, i) => {
            if (i > 0) {
                this.terminal('array-separator');
                this.linefeed();
            }
            this.expression(element);
        });
        this.indent--;
        this.linefeed();
        this.terminal('array-end');
    }

    visitObjectNode(node) {
        const savedBuffer = this.buffer;
        this.buffer = [];
        this.terminal('object-begin');
        for (let i = 0; i < node.elements.length; i += 2) {
            if (i > 0) this.terminal('object-separator');
            this.expression(node.elements[i]);
            this.terminal('key-value-separator');
            this.expression(node.elements[i + 1]);
        }
        this.terminal('object-end');
        const content = this.buffer.join('');
        this.buffer = savedBuffer;
        if (content.length <= 80 && !content.includes('\n')) {
            this.string(content);
            return;
        }
        this.terminal('object-begin');
        this.indent++;
        this.linefeed();
        for (let i = 0; i < node.elements.length; i += 2) {
            if (i > 0) {
                this.terminal('object-separator');
                this.linefeed();
            }
            this.expression(node.elements[i]);
            this.terminal('key-value-separator');
            this.expression(node.elements[i + 1]);
        }
        this.indent--;
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
            node.element.visit(this);
        } else {
            this.visitASTNode(node);
        }
    }

    visitBinaryNode(node) {
        const symbol = node.operator.symbol ?? String(node.operator);
        if (this.isDefined('binary-infix-prefix-begin')) {
            this.terminal(`binary-infix-prefix${symbol}`);
            this.wordSegment();
            this.expression(node.leftNode);
            this.wordSegment();
            this.expression(node.rightNode);
            this.terminal('binary-infix-prefix-end');
        } else {
            this.expression(node.leftNode);
            this.wordSegment();
            this.terminal(`binary-infix${symbol}`);
            this.wordSegment();
            this.expression(node.rightNode);
        }
    }

    visitArrayLenNode(node) {
        if (this.isDefined('property-length')) {
            this.expression(node.element);
            this.terminal('property-accessor');
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
        this.terminal('array-indexer-begin');
        this.expression(node.collection);
        this.terminal('array-indexer-suffix');
        this.expression(node.indexNode);
        this.terminal('array-indexer-end');
    }

    visitFuncAppNode(node) {
        this.terminal('funcapp-begin');
        this.expression(node.nameNode);
        this.terminal('funcapp-args-begin');
        node.arguments.forEach((arg, i) => {
            if (i > 0) this.terminal('funcapp-separator');
            this.expression(arg);
        });
        this.terminal('funcapp-args-end');
        this.terminal('funcapp-end');
    }

    visitAssignmentNode(node) {
        this.terminal('assignment-begin');
        this.expression(node.variable);
        this.terminal('assignment-infix');
        this.expression(node.expression);
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
        this.terminal('append-begin');
        this.expression(node.variable);
        this.terminal('append-infix');
        this.expression(node.expression);
        this.terminal('append-end');
    }

    visitBreakNode(node) {
        this.terminal('break');
    }

    visitPassNode(node) {
        // handled inside block
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
        } else if (node.inspection && this.isDefined('unary-inspection')) {
            this.terminal('unary-inspection');
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
            const opSymbol = node.operator.symbol ?? String(node.operator);
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
        this.block(node.thenBlock);
        if (node.elseBlock && !(node.elseBlock instanceof PassNode)) {
            if (this.isDefined('if-else-if') && node.elseBlock instanceof IfNode) {
                this.terminal('if-else-if', { linefeedBefore: true });
                this.block(node.elseBlock);
            } else {
                this.terminal('if-else', { linefeedBefore: true });
                this.block(node.elseBlock);
            }
        }
        this.terminal('if-end', { linefeedBefore: true });
    }

    visitRepeatNode(node) {
        this.terminal('repeat-begin');
        this.expression(node.countNode);
        this.terminal('repeat-times');
        this.terminal('repeat-block');
        this.block(node.blockNode);
        this.terminal('repeat-end', { linefeedBefore: true });
    }

    visitFuncDefNode(node) {
        this.terminal('funcdef-begin');
        this.terminal('funcdef-name-begin');
        this.expression(node.nameNode);
        this.terminal('funcdef-name-end');
        if (this.isDefined('funcdef-noarg') && node.parameters.length === 0) {
            this.terminal('funcdef-noarg');
        } else {
            this.terminal('funcdef-args-begin');
            node.parameters.forEach((arg, i) => {
                if (i > 0) this.terminal('funcdef-arg-separator');
                this.expression(arg);
            });
            this.terminal('funcdef-args-end');
        }
        this.terminal('funcdef-block');
        this.block(node.body);
        this.terminal('funcdef-end', { linefeedBefore: true });
    }

    visitAssertNode(node) {
        this.terminal('assert-begin');
        this.expression(node.test);
        this.terminal('assert-infix');
        this.expression(node.reference);
        this.terminal('assert-end');
    }

    visitBlockNode(node) {
        if (!node.topLevel) {
            this.terminal('block-begin-prefix');
            this.terminal('block-begin');
            this.indent++;
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
                if (statement instanceof FuncDefNode) this.linefeed();
                this.terminal('block-separator');
                if (statement instanceof PassNode) this.linefeed();
                this.comment(statement.comment);
            });
        }

        if (!node.topLevel) {
            this.indent--;
            this.justLinefeeded = false;
            this.terminal('block-end', { linefeedBefore: true });
        }
    }

    visitImportNode(node) {
        this.terminal('import-standard');
    }
}
