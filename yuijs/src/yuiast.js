// yuiast.js — AST node definitions (port of yuichan/yuiast.py)

let OPERATORS = null;

export function setOperators(operators) {
    OPERATORS = operators;
}

// ─────────────────────────────────────────────
// Base classes
// ─────────────────────────────────────────────

export class ASTNode {
    constructor() {
        this.filename = 'main.yui';
        this.source = '';
        this.pos = 0;
        this.endPos = -1;
        this.comment = null;
    }

    setpos(source, pos, endPos = -1, filename = 'main.yui') {
        this.source = source;
        this.pos = pos;
        this.endPos = endPos;
        this.filename = filename;
        this.comment = null;
        return this;
    }

    toString() {
        return this.source.slice(this.pos, this.endPos);
    }

    evaluate(runtime) {
        return this.visit(runtime);
    }

    visit(visitor) {
        const method = 'visit' + this.constructor.name;
        if (typeof visitor[method] === 'function') {
            return visitor[method](this);
        }
        if (typeof visitor.visitASTNode === 'function') {
            return visitor.visitASTNode(this);
        }
        throw new Error(`No visitor method: ${method}`);
    }

    extract() {
        // Returns [linenum, col, snippet]
        let linenum = 1;
        let col = 1;
        let start = 0;
        for (let i = 0; i < this.source.length; i++) {
            if (i === this.pos) break;
            if (this.source[i] === '\n') {
                linenum++;
                col = 1;
                start = i + 1;
            } else {
                col++;
            }
        }
        let endPos = this.source.indexOf('\n', start);
        if (endPos === -1) endPos = this.source.length;
        return [linenum, col, this.source.slice(start, endPos)];
    }
}

export class ExpressionNode extends ASTNode {
    constructor() {
        super();
    }
}

// Helper: wrap raw values into AST nodes
function _node(node) {
    if (node === null || node === undefined) return null;
    if (typeof node === 'number') return new NumberNode(node);
    if (typeof node === 'string') return new StringNode(node);
    if (Array.isArray(node)) return new ArrayNode(node.map(_node));
    if (node instanceof ASTNode) return node;
    throw new Error(`Cannot convert to ASTNode: ${node}`);
}

// ─────────────────────────────────────────────
// Literal / value nodes
// ─────────────────────────────────────────────

export class ConstNode extends ExpressionNode {
    // null/boolean: nativeValue is null, true, or false
    constructor(value = null) {
        super();
        this.nativeValue = value;
    }

    visit(visitor) {
        return visitor.visitConstNode(this);
    }
}

export class NumberNode extends ExpressionNode {
    constructor(value, isFloat = false) {
        super();
        this.nativeValue = value;
        this.isFloat = isFloat;  // true when source had decimal point (e.g. 10.0)
    }

    visit(visitor) {
        return visitor.visitNumberNode(this);
    }
}

export class ArrayLenNode extends ExpressionNode {
    constructor(element) {
        super();
        this.element = element;
    }

    visit(visitor) {
        return visitor.visitArrayLenNode(this);
    }
}

export class MinusNode extends ExpressionNode {
    constructor(element) {
        super();
        this.element = element;
    }

    visit(visitor) {
        return visitor.visitMinusNode(this);
    }
}

export class StringNode extends ExpressionNode {
    constructor(contents) {
        super();
        this.contents = contents;
    }

    visit(visitor) {
        return visitor.visitStringNode(this);
    }
}

export class ArrayNode extends ExpressionNode {
    constructor(elements) {
        super();
        this.elements = elements.map(_node);
    }

    visit(visitor) {
        return visitor.visitArrayNode(this);
    }
}

export class ObjectNode extends ExpressionNode {
    constructor(elements) {
        super();
        this.elements = elements.map(_node);
    }

    visit(visitor) {
        return visitor.visitObjectNode(this);
    }
}

// ─────────────────────────────────────────────
// Variable / expression nodes
// ─────────────────────────────────────────────

export class NameNode extends ExpressionNode {
    constructor(name) {
        super();
        this.name = name;
    }

    visit(visitor) {
        return visitor.visitNameNode(this);
    }

    update(value, visitor) {
        visitor.setenv(this.name, value);
    }
}

export class GetIndexNode extends ASTNode {
    constructor(collection, index) {
        super();
        this.collection = _node(collection);
        this.indexNode = _node(index);
    }

    visit(visitor) {
        return visitor.visitGetIndexNode(this);
    }

    update(value, visitor) {
        const collection = this.collection.visit(visitor);
        const index = this.indexNode.visit(visitor);
        collection.setItem(index, value);
    }
}

export class BinaryNode extends ASTNode {
    constructor(left, operator, right, comparative = false) {
        super();
        this.leftNode = _node(left);
        this.operator = OPERATORS && typeof operator === 'string' ? OPERATORS[operator] : operator;
        this.rightNode = _node(right);
        this.comparative = comparative;
    }
}

export class FuncAppNode extends ExpressionNode {
    constructor(name, argumentsList) {
        super();
        this.nameNode = typeof name === 'string' ? new NameNode(name) : _node(name);
        this.arguments = argumentsList.map(_node);
        this.snippet = '';
    }

    visit(visitor) {
        return visitor.visitFuncAppNode(this);
    }
}

// ─────────────────────────────────────────────
// Statement nodes
// ─────────────────────────────────────────────

export class StatementNode extends ASTNode {
    constructor() {
        super();
    }
}

export class AssignmentNode extends StatementNode {
    constructor(variable, expression) {
        super();
        this.variable = typeof variable === 'string' ? new NameNode(variable) : _node(variable);
        this.expression = _node(expression);
    }

    visit(visitor) {
        return visitor.visitAssignmentNode(this);
    }
}

export class IncrementNode extends StatementNode {
    constructor(variable) {
        super();
        this.variable = typeof variable === 'string' ? new NameNode(variable) : _node(variable);
    }

    visit(visitor) {
        return visitor.visitIncrementNode(this);
    }
}

export class DecrementNode extends StatementNode {
    constructor(variable) {
        super();
        this.variable = typeof variable === 'string' ? new NameNode(variable) : _node(variable);
    }

    visit(visitor) {
        return visitor.visitDecrementNode(this);
    }
}

export class AppendNode extends StatementNode {
    constructor(variable, expression) {
        super();
        this.variable = typeof variable === 'string' ? new NameNode(variable) : _node(variable);
        this.expression = _node(expression);
    }

    visit(visitor) {
        return visitor.visitAppendNode(this);
    }
}

export class BlockNode extends StatementNode {
    constructor(statements, topLevel = false) {
        super();
        if (statements instanceof StatementNode) {
            this.statements = [statements];
        } else {
            this.statements = statements;
        }
        this.topLevel = topLevel;
    }

    visit(visitor) {
        return visitor.visitBlockNode(this);
    }
}

export class IfNode extends StatementNode {
    constructor(left, operator, right, thenBlock, elseBlock = null) {
        super();
        this.left = _node(left);
        this.operator = OPERATORS[operator];
        this.right = _node(right);
        this.thenBlock = thenBlock;
        this.elseBlock = elseBlock;
    }

    visit(visitor) {
        return visitor.visitIfNode(this);
    }
}

export class BreakNode extends StatementNode {
    constructor() {
        super();
    }

    visit(visitor) {
        return visitor.visitBreakNode(this);
    }
}

export class PassNode extends StatementNode {
    constructor(comment = null) {
        super();
        this.comment = comment;
    }

    visit(visitor) {
        return visitor.visitPassNode(this);
    }
}

export class RepeatNode extends StatementNode {
    constructor(countNode, blockNode) {
        super();
        this.countNode = _node(countNode);
        this.blockNode = blockNode;
    }

    visit(visitor) {
        return visitor.visitRepeatNode(this);
    }
}

export class ImportNode extends StatementNode {
    constructor(moduleName = null) {
        super();
        this.moduleName = typeof moduleName === 'string' ? new NameNode(moduleName) : _node(moduleName);
    }

    visit(visitor) {
        return visitor.visitImportNode(this);
    }
}

export class ReturnNode extends StatementNode {
    constructor(expression) {
        super();
        this.expression = _node(expression);
    }

    visit(visitor) {
        return visitor.visitReturnNode(this);
    }
}

export class FuncDefNode extends StatementNode {
    constructor(nameNode, parameters, body) {
        super();
        this.nameNode = typeof nameNode === 'string' ? new NameNode(nameNode) : _node(nameNode);
        this.parameters = parameters.map(p => typeof p === 'string' ? new NameNode(p) : _node(p));
        this.body = body;
    }

    visit(visitor) {
        return visitor.visitFuncDefNode(this);
    }
}

export class PrintExpressionNode extends StatementNode {
    constructor(expression, inspection = false, grouping = false) {
        super();
        this.expression = _node(expression);
        this.inspection = inspection;
        this.grouping = grouping;
    }

    visit(visitor) {
        return visitor.visitPrintExpressionNode(this);
    }
}

export class AssertNode extends StatementNode {
    constructor(test, reference) {
        super();
        this.test = _node(test);
        this.reference = _node(reference);
    }

    visit(visitor) {
        return visitor.visitAssertNode(this);
    }
}
