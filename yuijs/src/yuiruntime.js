// yuiruntime.js — runtime visitor (port of yuichan/yuiruntime.py)

import {
    ASTNode,
    ConstNode, NumberNode, StringNode, ArrayNode, ObjectNode,
    NameNode, GetIndexNode, ArrayLenNode, MinusNode, BinaryNode, FuncAppNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PassNode, PrintExpressionNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, ImportNode,
} from './yuiast.js';

import { YuiValue, YuiType, YuiError, formatMessages, IntType, NumberType, FloatType, types } from './yuitypes.js';
import { standardLib } from './yuistdlib.js';
import { YuiParser } from './yuiparser.js';

// ─────────────────────────────────────────────
// Control-flow exceptions
// ─────────────────────────────────────────────

export class YuiBreakException extends Error {
    constructor() { super('break'); this.name = 'YuiBreakException'; }
}

export class YuiReturnException extends Error {
    constructor(value = null) {
        super('return');
        this.name = 'YuiReturnException';
        this.value = value;
    }
}

// ─────────────────────────────────────────────
// Function types
// ─────────────────────────────────────────────

export class YuiFunction {
    constructor(name) { this.name = name; }
    call(arguments_, node, runtime) {
        throw new Error('Abstract method: call');
    }
}

export class LocalFunctionV extends YuiFunction {
    constructor(name, parameters, body) {
        super(name);
        this.parameters = parameters;
        this.body = body;
    }

    call(argValues, node, runtime) {
        runtime.pushenv();
        if (this.parameters.length !== argValues.length) {
            throw new YuiError(
                ['mismatch', 'arguments', `✅${this.parameters.length}`, `❌${argValues.length}`],
                node
            );
        }
        for (let i = 0; i < this.parameters.length; i++) {
            runtime.setenv(this.parameters[i], argValues[i]);
        }
        try {
            runtime.pushCallFrame(this.name, argValues, node);
            runtime.checkRecursionDepth();
            this.body.visit(runtime);
        } catch (e) {
            if (e instanceof YuiReturnException) {
                if (e.value !== null) {
                    runtime.popCallFrame();
                    runtime.popenv();
                    return e.value;
                }
            } else {
                throw e;
            }
        }
        runtime.popCallFrame();
        return new YuiValue(runtime.popenv());
    }
}

export class NativeFunction extends YuiFunction {
    constructor(fn, isFfi = false) {
        super(fn.name || 'anonymous');
        this.fn = fn;
        this.isFfi = isFfi;
    }

    call(argValues, node, runtime) {
        try {
            const result = this.fn(...argValues);
            return result instanceof YuiValue ? result : new YuiValue(result);
        } catch (e) {
            if (e instanceof YuiError) {
                if (!e.errorNode) e.errorNode = node;
                throw e;
            }
            throw new YuiError(['error', 'internal', `🔍${this.name}`, `⚠️ ${e.message}`], node);
        }
    }
}

// ─────────────────────────────────────────────
// YuiRuntime
// ─────────────────────────────────────────────

export class YuiRuntime {
    constructor() {
        this.environments = [{}];
        this.callFrames = [];
        this.filesystems = {};

        this.shouldStop = false;
        this.timeout = 0;
        this._startTime = 0;
        this.interactiveMode = false;
        this.source = '';
        this.allowBinaryOps = false;
        this.functionDefined = false;
        this.resetStats();
    }

    resetStats() {
        this.incrementCount = 0;
        this.decrementCount = 0;
        this.compareCount = 0;
        this.testPassed = [];
        this.testFailed = [];
    }

    hasenv(name) {
        for (let i = this.environments.length - 1; i >= 0; i--) {
            if (name in this.environments[i]) return true;
        }
        return false;
    }

    getenv(name) {
        for (let i = this.environments.length - 1; i >= 0; i--) {
            if (name in this.environments[i]) return this.environments[i][name];
        }
        return null;
    }

    setenv(name, value) {
        this.environments[this.environments.length - 1][name] = value;
    }

    pushenv() {
        this.environments.push({});
    }

    popenv() {
        return this.environments.pop();
    }

    stringfyEnv(stack = -1, indentPrefix = '') {
        const idx = stack < 0 ? this.environments.length + stack : stack;
        const env = this.environments[idx];
        const inner = indentPrefix + '  ';
        const lines = [`${indentPrefix}<${this.stringfyCallFrames(stack)}>\n{`];
        const entries = Object.entries(env);
        for (let i = 0; i < entries.length; i++) {
            const [key, value] = entries[i];
            if (key.startsWith('@')) continue;
            lines.push(`\n${indentPrefix}  "${key}": `);
            lines.push(YuiValue.stringfyValue(value, inner));
            if (i < entries.length - 1) lines.push(', ');
        }
        lines.push(`\n${indentPrefix}}`);
        return lines.join('');
    }

    formatError(error, prefix = ' ', marker = '^', lineoffset = 0) {
        let message = formatMessages(error.messages);
        if (error.errorNode) {
            const [line, col, snippet] = error.errorNode.extract();
            const length = Math.max(
                error.errorNode.endPos != null ? error.errorNode.endPos - error.errorNode.pos : 3,
                3
            );
            const makePointer = marker.repeat(Math.min(length, 16));
            const firstLine = snippet.split('\n')[0];
            const indent = ' '.repeat(col - 1);
            message = `${message} line ${line + lineoffset}, column ${col}:\n${prefix}${firstLine}\n${prefix}${indent}${makePointer}`;
        }
        return `[実行時エラー/RuntimeError] ${message}\n[環境/Environment] ${this.stringfyEnv(-1)}\n`;
    }

    pushCallFrame(funcName, args, node) {
        this.callFrames.push([funcName, args, node]);
    }

    popCallFrame() {
        this.callFrames.pop();
    }

    stringfyCallFrames(stack = -1) {
        if (this.callFrames.length === 0) return 'global';
        const idx = stack < 0 ? this.callFrames.length + stack : stack;
        const frame = this.callFrames[idx];
        const args = frame[1].map(arg => YuiValue.stringfyValue(arg, null)).join(', ');
        return `${frame[0]}(${args})]`;
    }

    checkRecursionDepth() {
        if (this.callFrames.length > 512) {
            const frame = this.callFrames[this.callFrames.length - 1];
            const args = frame[1].map(a => String(a)).join(', ');
            const snippet = `${frame[0]}(${args})`;
            throw new YuiError(['error', 'recursion', `🔍${snippet}`], frame[2]);
        }
    }

    countInc() { this.incrementCount++; }
    countDec() { this.decrementCount++; }
    countCompare() { this.compareCount++; }

    load(fn) {
        return new NativeFunction(fn);
    }

    print(value, node) {
        const [line, , snippet] = node.extract();
        let out;
        if (this.interactiveMode || node instanceof StringNode) {
            out = String(value);
        } else if (node instanceof FuncAppNode) {
            out = `#line: ${line} ${node.snippet.trim()}\n>>> ${node.snippet}\n${value}`;
        } else {
            out = `#line: ${line}\n>>> ${snippet.trim()}\n${value}`;
        }
        // In browser: could use console.log or a custom output handler
        console.log(out);
    }

    start(timeout = 30) {
        this.shouldStop = false;
        this.timeout = timeout;
        this._startTime = Date.now();
    }

    checkExecution(node) {
        if (this.shouldStop) {
            throw new YuiError(['interrupted'], node);
        }
        if (this.timeout > 0 && (Date.now() - this._startTime) / 1000 > this.timeout) {
            throw new YuiError(['error', 'timeout', `❌${this.timeout}[sec]`, `✅${this.timeout}[sec]`], node);
        }
    }

    exec(source, syntax = 'yui', timeout = 30, evalMode = true) {
        this.source = source;
        const parser = new YuiParser(syntax);
        const program = parser.parse(source);
        try {
            this.start(timeout);
            const value = program.evaluate(this);
            return evalMode ? YuiType.toNative(value) : this.environments[this.environments.length - 1];
        } catch (e) {
            if (e instanceof YuiError) {
                e.runtime = this;
                throw e;
            }
            throw e;
        }
    }

    evaluate(node) {
        return node.visit(this);
    }

    // ─────────────────────────────────────────────
    // Visitor methods — Literals
    // ─────────────────────────────────────────────

    visitConstNode(node) {
        if (node.nativeValue === true) return YuiValue.TrueValue;
        if (node.nativeValue === false) return YuiValue.FalseValue;
        return YuiValue.NullValue;
    }

    visitNumberNode(node) {
        // If the source had a decimal point, force FloatType even if value is whole (e.g. 10.0)
        if (node.isFloat) {
            return new YuiValue(node.nativeValue, FloatType);
        }
        return new YuiValue(node.nativeValue);
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
                parts.push(String(YuiType.yuiToNative(value)));
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
            objectValue.setItem(key, val);
        }
        return objectValue;
    }

    // ─────────────────────────────────────────────
    // Variable / expression visitors
    // ─────────────────────────────────────────────

    visitNameNode(node) {
        if (!this.hasenv(node.name)) {
            throw new YuiError(['undefined', 'variable', `❌${node.name}`], node);
        }
        return this.getenv(node.name);
    }

    visitGetIndexNode(node) {
        const collection = node.collection.visit(this);
        const index = node.indexNode.visit(this);
        return collection.getItem(index);
    }

    visitArrayLenNode(node) {
        const value = node.element.visit(this);
        return new YuiValue(value.arrayview.length);
    }

    visitMinusNode(node) {
        const value = node.element.visit(this);
        NumberType.matchOrRaise(value);
        return new YuiValue(-YuiType.matchedNative(value));
    }

    visitBinaryNode(node) {
        if (!(this.allowBinaryOps || (this.functionDefined && this.testPassed.length > 0))) {
            throw new YuiError(
                ['error', 'binary operator not enabled', `🔍${node.operator}`],
                node
            );
        }
        const left  = node.leftNode.visit(this);
        const right = node.rightNode.visit(this);
        const op = node.operator;

        // 文字列連結: + のみ
        if (op === '+' && types.isString(left) && types.isString(right)) {
            return new YuiValue(YuiType.matchedNative(left) + YuiType.matchedNative(right));
        }

        // 配列連結: + のみ
        if (op === '+' && types.isArray(left) && types.isArray(right)) {
            return new YuiValue([...left.array, ...right.array]);
        }

        // 数値演算
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left);
        const r = YuiType.matchedNative(right);
        const isFloat = types.isFloat(left) || types.isFloat(right);

        let result;
        if (op === '+') {
            result = l + r;
        } else if (op === '-') {
            result = l - r;
        } else if (op === '*') {
            result = l * r;
        } else if (op === '/') {
            if (r === 0) throw new YuiError(['error', 'division by zero', `❌${r}`], node);
            result = isFloat ? l / r : Math.floor(l / r);
        } else if (op === '%') {
            if (r === 0) throw new YuiError(['error', 'division by zero', `❌${r}`], node);
            // int: Python互換（正の除数に対して常に非負）
            // float: JSのmodulo（小数のため符号は稀なケース）
            result = isFloat ? l % r : ((l % r) + r) % r;
        } else {
            throw new YuiError(['error', 'unsupported operator', `🔍${op}`], node);
        }

        return isFloat ? new YuiValue(result, FloatType) : new YuiValue(result);
    }

    visitFuncAppNode(node) {
        const name = `@${node.nameNode.name}`;
        if (!this.hasenv(name)) {
            throw new YuiError(['undefined', 'function', `❌${node.nameNode.name}`], node.nameNode);
        }
        const func = this.getenv(name);
        if (!(func instanceof YuiFunction)) {
            throw new YuiError(['error', 'type', '✅<function>', `❌${func}`], node.nameNode);
        }
        const argValues = node.arguments.map(arg => arg.visit(this));
        if (node.snippet === '') {
            const args = argValues.map(v => String(v)).join(', ');
            node.snippet = `${node.nameNode.name}(${args})`;
        }
        return func.call(argValues, node, this);
    }

    // ─────────────────────────────────────────────
    // Assignment / mutation visitors
    // ─────────────────────────────────────────────

    visitAssignmentNode(node) {
        if (typeof node.variable.update !== 'function') {
            throw new YuiError(['expected', 'variable', `❌${node.variable}`], node.variable);
        }
        const value = node.expression.visit(this);
        node.variable.update(value, this);
        return value;
    }

    visitIncrementNode(node) {
        if (typeof node.variable.update !== 'function') {
            throw new YuiError(['expected-variable', `❌${node.variable}`], node.variable);
        }
        const value = node.variable.visit(this);
        IntType.matchOrRaise(value);
        const result = new YuiValue(YuiType.matchedNative(value) + 1);
        node.variable.update(result, this);
        this.countInc();
        return result;
    }

    visitDecrementNode(node) {
        if (typeof node.variable.update !== 'function') {
            throw new YuiError(['expected-variable', `❌${node.variable}`], node.variable);
        }
        const value = node.variable.visit(this);
        IntType.matchOrRaise(value);
        const result = new YuiValue(YuiType.matchedNative(value) - 1);
        node.variable.update(result, this);
        this.countDec();
        return result;
    }

    visitAppendNode(node) {
        const array = node.variable.visit(this);
        const value = node.expression.visit(this);
        array.append(value);
        return array;
    }

    // ─────────────────────────────────────────────
    // Control-flow visitors
    // ─────────────────────────────────────────────

    visitBlockNode(node) {
        let value = YuiValue.NullValue;
        for (const statement of node.statements) {
            value = statement.visit(this);
        }
        return value;
    }

    visitIfNode(node) {
        const left = node.left.visit(this);
        const right = node.right.visit(this);
        const result = node.operator.evaluate(left, right);
        this.countCompare();
        if (result) {
            return node.thenBlock.visit(this);
        } else if (node.elseBlock) {
            node.elseBlock.visit(this);
        }
    }

    visitBreakNode(node) {
        throw new YuiBreakException();
    }

    visitPassNode(node) {
        // do nothing
    }

    visitRepeatNode(node) {
        const countValue = node.countNode.visit(this);
        IntType.matchOrRaise(countValue);
        const count = YuiType.matchedNative(countValue);
        try {
            for (let i = 0; i < Math.abs(count); i++) {
                this.checkExecution(node);
                node.blockNode.visit(this);
            }
        } catch (e) {
            if (e instanceof YuiBreakException) return YuiValue.NullValue;
            throw e;
        }
        return YuiValue.NullValue;
    }

    visitReturnNode(node) {
        const value = node.expression.visit(this);
        throw new YuiReturnException(value);
    }

    visitFuncDefNode(node) {
        const params = node.parameters.map(p => p.name);
        const func = new LocalFunctionV(node.nameNode.name, params, node.body);
        this.setenv(`@${node.nameNode.name}`, func);
        this.functionDefined = true;
        return func;
    }

    // ─────────────────────────────────────────────
    // Print / assert visitors
    // ─────────────────────────────────────────────

    visitPrintExpressionNode(node) {
        if (node.expression instanceof FuncAppNode) {
            node.expression.snippet = '';
        }
        const value = node.expression.visit(this);
        this.print(value, node.expression);
        return value;
    }

    visitAssertNode(node) {
        let tested = null;
        let referenceValue = null;
        try {
            tested = node.test.visit(this);
            referenceValue = node.reference.visit(this);
            if (tested.type.equals(tested, referenceValue)) {
                this.testPassed.push(String(node.test));
                return YuiValue.TrueValue;
            }
        } catch (e) {
            if (e instanceof YuiError) throw e;
            // other errors → fall through to test failure
        }
        throw new YuiError(
            ['failed', 'test', `🔍${node.test}`, `❌${tested}`, `✅${referenceValue}`],
            node
        );
        return YuiValue.FalseValue;
    }

    visitImportNode(node) {
        const modules = [];
        if (node.moduleName === null) {
            standardLib(modules);
        }
        for (const [names, fn] of modules) {
            for (const name of names.split('|')) {
                this.setenv(`@${name}`, new NativeFunction(fn));
            }
        }
        return YuiValue.NullValue;
    }
}
