// yuitypes.js — type system (port of yuichan/yuitypes.py)

import { ASTNode, setOperators } from './yuiast.js';
export { YuiError, ERROR_MESSAGES, formatMessages } from './yuierror.js';
import { YuiError } from './yuierror.js';

// ─────────────────────────────────────────────
// Type emoji constants
// ─────────────────────────────────────────────
export const TY_NULL    = '🚫';
export const TY_BOOLEAN = '🎭';
export const TY_INT     = '🔢';
export const TY_FLOAT   = '📊';
export const TY_NUMBER  = '🔢';
export const TY_ARRAY   = '🍡';
export const TY_OBJECT  = '🗂️';
export const TY_STRING  = '🔤';

// ─────────────────────────────────────────────
// YuiType base class and subclasses
// ─────────────────────────────────────────────

export class YuiType {
    constructor(name, emoji) {
        this.name = name;
        this.emoji = emoji;
    }

    toString() {
        return this.emoji;
    }

    // 配列内で unbox されるかどうか（scalar 型は true、array/object は false）
    isArrayUnboxed() {
        return true;
    }

    isImmutable() {
        return false;
    }

    // Abstract: must be overridden
    match(value) {
        throw new Error('Abstract method: match');
    }

    matchOrRaise(nodeOrValue = null) {
        if (!this.match(nodeOrValue)) {
            throw new YuiError(
                ['error', 'type', `✅<${this.emoji}${this.name}>`, `❌${nodeOrValue}`],
                nodeOrValue instanceof ASTNode ? nodeOrValue : null
            );
        }
    }

    toSign(nativeValue) {
        return 1;
    }

    toArrayview(n) {
        throw new Error('Abstract method: toArrayview');
    }

    toNative(elements, sign = 1, node = null) {
        throw new Error('Abstract method: toNative');
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        throw new Error('Abstract method: stringfy');
    }

    equals(leftNode, rightNode) {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        return leftValue === rightValue;
    }

    lessThan(leftNode, rightNode, op = '<') {
        throw new YuiError(
            ['unsupported', 'comparison', `❌${leftNode} ${op} ${rightNode}`],
            leftNode instanceof ASTNode ? leftNode : null
        );
    }

    // ─── static utility methods ───

    static evaluated(value) {
        return value;
    }

    static isBool(nodeOrValue) {
        return BoolType.match(nodeOrValue);
    }

    static isInt(nodeOrValue) {
        return IntType.match(nodeOrValue);
    }

    static isFloat(nodeOrValue) {
        return FloatType.match(nodeOrValue);
    }

    static isNumber(nodeOrValue) {
        return NumberType.match(nodeOrValue);
    }

    static isString(nodeOrValue) {
        return StringType.match(nodeOrValue);
    }

    static isArray(nodeOrValue) {
        return ArrayType.match(nodeOrValue);
    }

    static isObject(nodeOrValue) {
        return ObjectType.match(nodeOrValue);
    }

    static matchedNative(nodeOrValue) {
        if (nodeOrValue instanceof YuiValue) {
            return nodeOrValue.native;
        }
        return nodeOrValue;
    }

    static fromArrayview(value) {
        if (value instanceof YuiValue) return value;
        return new YuiValue(value);
    }

    static intoArrayview(nodeOrValue) {
        const value = nodeOrValue;
        if (value instanceof YuiValue && value.isPrimitive()) {
            return value.native;
        }
        if (typeof value === 'number' || typeof value === 'string' || value === null) {
            return value;
        }
        if (value instanceof YuiValue) return value;
        return new YuiValue(value);
    }

    static arrayviewS(value) {
        if (value === null || value === undefined) return 'null';
        if (typeof value === 'string') {
            const escaped = value.replace(/"/g, '\\"').replace(/\n/g, '\\n');
            return `"${escaped}"`;
        }
        if (typeof value === 'number' && !Number.isInteger(value)) {
            return value.toFixed(6);
        }
        return String(value);
    }

    // Convert YuiValue (or nested) to native JS value (recursive)
    static toNative(nodeOrValue) {
        if (nodeOrValue instanceof YuiValue) {
            return YuiType.toNative(nodeOrValue.native);
        }
        if (Array.isArray(nodeOrValue)) {
            return nodeOrValue.map(v => YuiType.toNative(v));
        }
        if (nodeOrValue !== null && typeof nodeOrValue === 'object' && !(nodeOrValue instanceof YuiValue)) {
            const result = {};
            for (const [k, v] of Object.entries(nodeOrValue)) {
                result[String(k)] = YuiType.toNative(v);
            }
            return result;
        }
        return nodeOrValue;
    }

    static nativeToYui(nativeValue) {
        if (nativeValue === null || nativeValue === undefined) return YuiValue.NullValue;
        if (typeof nativeValue === 'boolean') {
            return nativeValue ? YuiValue.TrueValue : YuiValue.FalseValue;
        }
        if (typeof nativeValue === 'number' || Array.isArray(nativeValue) ||
            typeof nativeValue === 'string' || (typeof nativeValue === 'object' && nativeValue !== null)) {
            return new YuiValue(nativeValue);
        }
        if (nativeValue instanceof YuiValue) return nativeValue;
        return new YuiValue(nativeValue);
    }

    static yuiToNative(value) {
        if (value instanceof YuiValue) {
            return YuiType.yuiToNative(value.native);
        }
        if (Array.isArray(value)) {
            return value.map(e => YuiType.yuiToNative(e));
        }
        if (value !== null && typeof value === 'object') {
            const result = {};
            for (const [key, item] of Object.entries(value)) {
                result[key] = YuiType.yuiToNative(item);
            }
            return result;
        }
        return value;
    }

    static compare(leftNodeOrValue, rightNodeOrValue) {
        if (types.isNumber(leftNodeOrValue) && types.isNumber(rightNodeOrValue)) {
            const lv = _round(YuiType.matchedNative(leftNodeOrValue), 6);
            const rv = _round(YuiType.matchedNative(rightNodeOrValue), 6);
            return _compare(lv, rv);
        }
        if (types.isString(leftNodeOrValue) && types.isString(rightNodeOrValue)) {
            const lv = YuiType.matchedNative(leftNodeOrValue);
            const rv = YuiType.matchedNative(rightNodeOrValue);
            return _compare(lv, rv);
        }
        let lv = leftNodeOrValue;
        let rv = rightNodeOrValue;
        if (!(rv instanceof YuiValue)) {
            rv = new YuiValue(rv.native);
        }
        return _compare(lv.arrayview, rv.arrayview);
    }
}

// Static type instances (set after class definitions)
export let NullType = null;
export let BoolType = null;
export let IntType = null;
export let FloatType = null;
export let NumberType = null;
export let StringType = null;
export let ArrayType = null;
export let ObjectType = null;

function _round(n, decimals) {
    const factor = 10 ** decimals;
    return Math.round(n * factor) / factor;
}

function _compare(left, right) {
    if (left === right) return 0;
    if (left < right) return -1;
    return 1;
}

// ─────────────────────────────────────────────
// Concrete type classes
// ─────────────────────────────────────────────

// NullType and BoolType are immutable
// ArrayType and ObjectType are not array-unboxed (placeholder; overridden below)

export class YuiNullType extends YuiType {
    constructor() {
        super('null', TY_NULL);
    }

    isImmutable() {
        return true;
    }

    match(nodeOrValue) {
        if (nodeOrValue === null || nodeOrValue === undefined) return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiNullType;
    }

    checkElement(nodeOrValue) {
        throw new YuiError(['immutable', `❌${this}`], null);
    }

    toArrayview(n) {
        return [];
    }

    toNative(elements, sign = 1, node = null) {
        return null;
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        return 'null';
    }
}

export class YuiBooleanType extends YuiType {
    constructor() {
        super('boolean', TY_BOOLEAN);
    }

    isImmutable() {
        return true;
    }

    match(nodeOrValue) {
        // In JS, booleans are a distinct type (no subclass issue like Python)
        if (typeof nodeOrValue === 'boolean') return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiBooleanType;
    }

    checkElement(nodeOrValue) {
        throw new YuiError(['immutable', `❌${this}`], null);
    }

    toArrayview(n) {
        return n ? [1] : [0];
    }

    toNative(elements, sign = 1, node = null) {
        return elements.length > 0 ? Boolean(elements[0]) : false;
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        return nativeValue ? 'true' : 'false';
    }

    equals(leftNode, rightNode) {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'boolean') {
            return leftValue === rightValue;
        }
        return false;
    }

    lessThan(leftNode, rightNode, op = '<') {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'boolean') {
            return leftValue < rightValue;
        }
        return super.lessThan(leftNode, rightNode, op);
    }
}

export class YuiIntType extends YuiType {
    constructor() {
        super('int', TY_INT);
    }

    match(nodeOrValue) {
        // In JS, integers and floats are both 'number', so check Number.isInteger
        if (typeof nodeOrValue === 'number' && Number.isInteger(nodeOrValue)) return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiIntType;
    }

    checkElement(nodeOrValue) {
        IntType.matchOrRaise(nodeOrValue);
        const value = YuiType.matchedNative(nodeOrValue);
        if (value !== 0 && value !== 1) {
            throw new YuiError(['error', 'value', '✅0/1', `❌${value}`], null);
        }
    }

    toSign(n) {
        return n < 0 ? -1 : 1;
    }

    toArrayview(n) {
        // 可変長符号なし絶対値 LSBファースト（0は空配列）
        let nAbs = Math.abs(n);
        const bits = [];
        while (nAbs) {
            bits.push(nAbs & 1);
            nAbs = Math.floor(nAbs / 2);
        }
        return bits;
    }

    toNative(bits, sign = 1, node = null) {
        // 可変長LSBファースト配列を整数に変換
        let n = 0;
        for (let i = 0; i < bits.length; i++) {
            const bit = bits[i];
            if ((bit !== 0 && bit !== 1) || typeof bit === 'boolean') {
                const array = ArrayType.stringfy(bits, null, ",");
                throw new YuiError(
                    ['array-value-error', `❌${types.format_json(bit)}`, '✅0/1', `🔍${array}`],
                    node
                );
            }
            if (bit) n += Math.pow(2, i);
        }
        return sign * n;
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        return String(nativeValue);
    }

    equals(leftNode, rightNode) {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'boolean') return false; // bool != int
        if (typeof rightValue === 'number' && !Number.isInteger(rightValue)) {
            return _round(leftValue, 6) === _round(rightValue, 6);
        }
        return leftValue === rightValue;
    }

    lessThan(leftNode, rightNode, op = '<') {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'number') {
            if (!Number.isInteger(rightValue)) {
                return _round(leftValue, 6) < _round(rightValue, 6);
            }
            return leftValue < rightValue;
        }
        return super.lessThan(leftNode, rightNode, op);
    }
}

export class YuiFloatType extends YuiType {
    constructor() {
        super('float', TY_FLOAT);
    }

    match(nodeOrValue) {
        if (typeof nodeOrValue === 'number' && !Number.isInteger(nodeOrValue)) return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiFloatType;
    }

    checkElement(nodeOrValue) {
        IntType.matchOrRaise(nodeOrValue);
        const value = YuiType.matchedNative(nodeOrValue);
        if (value < 0 || value > 9) {
            throw new YuiError(['error', 'value', '✅0-9', `❌${value}`], null);
        }
    }

    toSign(x) {
        return x < 0 ? -1 : 1;
    }

    toArrayview(x) {
        // 絶対値をLSB（小さい桁）ファーストの一桁整数配列に変換
        const s = Math.abs(x).toFixed(6).replace('.', '');
        const digits = s.split('').map(Number);
        return digits.reverse();
    }

    toNative(digits, sign = 1, node = null) {
        // LSBファーストをMSBファーストに戻して数値に変換
        for (const d of digits) {
            if (!Number.isInteger(d) || typeof d === 'boolean' || d < 0 || d > 9) {
                const array = ArrayType.stringfy(digits, null, ',');
                throw new YuiError(
                    ['array-value-error', `❌${types.format_json(d)}`, '✅0-9', `🔍${array}`],
                    node
                );
            }
        }
        const numDigits = [...digits].reverse();
        const s = numDigits.join('');
        let value;
        if (s.length <= 6) {
            // 整数部なし（小数点以下のみ）
            value = parseFloat('0.' + s.padStart(6, '0'));
        } else {
            // 小数点を6桁前に挿入
            value = parseFloat(s.slice(0, -6) + '.' + s.slice(-6));
        }
        return sign * value;
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        return nativeValue.toFixed(6);
    }

    equals(leftNode, rightNode) {
        const leftValue = _round(YuiType.toNative(leftNode), 6);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'number') {
            return leftValue === _round(rightValue, 6);
        }
        return false;
    }

    lessThan(leftNode, rightNode, op = '<') {
        const leftValue = YuiType.toNative(leftNode);
        const rightValue = YuiType.toNative(rightNode);
        if (typeof rightValue === 'number') {
            return leftValue < rightValue;
        }
        return super.lessThan(leftNode, rightNode, op);
    }
}

export class YuiNumberType extends YuiType {
    constructor() {
        super('number', TY_NUMBER);
    }

    match(nodeOrValue) {
        return IntType.match(nodeOrValue) || FloatType.match(nodeOrValue);
    }

    checkElement(nodeOrValue) {}

    toArrayview(n) {
        if (!Number.isInteger(n)) {
            return FloatType.toArrayview(n);
        }
        return IntType.toArrayview(n);
    }

    toSign(n) {
        if (!Number.isInteger(n)) return FloatType.toSign(n);
        return IntType.toSign(n);
    }

    toNative(bits, sign = 1, node = null) {
        if (bits.length === 32) {
            return IntType.toNative(bits, sign, node);
        }
        return FloatType.toNative(bits, sign, node);
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        if (!Number.isInteger(nativeValue)) {
            return FloatType.stringfy(nativeValue, indentPrefix, width);
        }
        return IntType.stringfy(nativeValue, indentPrefix, width);
    }
}

export class YuiStringType extends YuiType {
    constructor() {
        super('string', TY_STRING);
    }

    match(nodeOrValue) {
        if (typeof nodeOrValue === 'string') return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiStringType;
    }

    checkElement(nodeOrValue) {
        IntType.matchOrRaise(nodeOrValue);
    }

    toArrayview(x) {
        const codes = [];
        for (const ch of x) {
            codes.push(ch.codePointAt(0));
        }
        return codes;
    }

    toNative(elements, sign = 1, node = null) {
        const contents = [];
        for (const d of elements) {
            if (!Number.isInteger(d) || typeof d === 'boolean' || d < 0 || d > 0x10FFFF) {
                const array = ArrayType.stringfy(elements, null, ',');
                throw new YuiError(
                    ['array-value-error', `❌${types.format_json(d)}`, '✅<文字コード>', `🔍${array}`],
                    node
                );
            }
            contents.push(String.fromCodePoint(d));
        }
        return contents.join('');
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        return types.format_json(nativeValue);
    }

    equals(leftNode, rightNode) {
        const leftValue = YuiType.toNative(leftNode);
        if (types.isString(rightNode)) {
            const rightValue = YuiType.matchedNative(rightNode);
            return leftValue === rightValue;
        }
        return false;
    }

    lessThan(leftNode, rightNode, op = '<') {
        const leftValue = YuiType.toNative(leftNode);
        if (types.isString(rightNode)) {
            const rightValue = YuiType.matchedNative(rightNode);
            return leftValue < rightValue;
        }
        return false;
    }
}

function _arrayEqual(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        return a.every((x, i) => _arrayEqual(x, b[i]));
    }
    if (Array.isArray(a) && typeof b === 'string') {
        try {
            return a.map(c => String.fromCodePoint(c)).join('') === b;
        } catch {
            return false;
        }
    }
    if (typeof a === 'string' && Array.isArray(b)) {
        return _arrayEqual(b, a);
    }
    return a === b;
}

export class YuiArrayType extends YuiType {
    constructor() {
        super('array', TY_ARRAY);
    }

    isArrayUnboxed() {
        return false;
    }

    match(nodeOrValue) {
        if (Array.isArray(nodeOrValue)) return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiArrayType;
    }

    checkElement(nodeOrValue) {}

    toArrayview(arrayValue) {
        return arrayValue.map(value => YuiType.intoArrayview(value));
    }

    toNative(elements, sign = 1, node = null) {
        return elements.map(element => {
            if (element instanceof YuiValue) return element.native;
            return element;
        });
    }

    stringfy(elements, indentPrefix = '', comma = ', ', width = 80) {
        const parts = elements.map(e => YuiType.arrayviewS(e));
        const oneLine = '[' + parts.join(comma) + ']';
        if (indentPrefix === null || indentPrefix.length + oneLine.length <= width) {
            return oneLine;
        }
        const inner = indentPrefix + '  ';
        const lines = elements.map((e, i) => {
            const s = e instanceof YuiValue ? e.stringfy(inner, false, width) : YuiType.arrayviewS(e);
            return `\n${inner}${s}${i < elements.length - 1 ? ',' : ''}`;
        });
        return '[' + lines.join('') + `\n${indentPrefix}]`;
    }

    equals(leftNode, rightNode) {
        const leftNative = YuiType.toNative(leftNode);
        const rightNative = YuiType.toNative(rightNode);
        return _arrayEqual(leftNative, rightNative);
    }
}

export class YuiObjectType extends YuiType {
    constructor() {
        super('object', TY_OBJECT);
    }

    isArrayUnboxed() {
        return false;
    }

    match(nodeOrValue) {
        if (nodeOrValue !== null && typeof nodeOrValue === 'object' &&
            !Array.isArray(nodeOrValue) && !(nodeOrValue instanceof YuiValue)) return true;
        return nodeOrValue instanceof YuiValue && nodeOrValue.type instanceof YuiObjectType;
    }

    checkElement(nodeOrValue) {
        ArrayType.matchOrRaise(nodeOrValue);
        const array = YuiType.matchedNative(nodeOrValue);
        if (!Array.isArray(array) || array.length !== 2 || !StringType.match(array[0])) {
            throw new YuiError(['error', 'value', '✅[key, value]', `❌${array}`], null);
        }
    }

    toArrayview(objectValue) {
        return Object.entries(objectValue).map(([key, value]) => {
            return new YuiValue([String(key), YuiType.intoArrayview(value)]);
        });
    }

    toNative(elements, sign = 1, node = null) {
        const obj = {};
        for (const keyValue of elements) {
            if (!(keyValue instanceof YuiValue)) {
                throw new YuiError(['array-value-error', `❌${keyValue}`, '✅[key, value]', `🔍${elements}`], node);
            }
            const kv = keyValue.native;
            if (!Array.isArray(kv) || kv.length !== 2) {
                throw new YuiError(['array-value-error', `❌${kv}`, '✅[key, value]', `🔍${elements}`], node);
            }
            const key = kv[0];
            if (typeof key !== 'string') {
                throw new YuiError(['array-value-error', `❌${key}`, '✅<string>', `🔍${kv}`], node);
            }
            obj[key] = kv[1];
        }
        return obj;
    }

    stringfy(nativeValue, indentPrefix = '', width = 80) {
        const entries = Object.entries(nativeValue);
        const parts = entries.map(([k, v]) => `"${k}": ${YuiType.arrayviewS(v)}`);
        const oneLine = '{' + parts.join(', ') + '}';
        if (indentPrefix === null || indentPrefix.length + oneLine.length <= width) {
            return oneLine;
        }
        const inner = indentPrefix + '  ';
        const lines = entries.map(([k, v], i) => {
            const s = v instanceof YuiValue ? v.stringfy(inner, false, width) : YuiType.arrayviewS(v);
            return `\n${inner}"${k}": ${s}${i < entries.length - 1 ? ',' : ''}`;
        });
        return '{' + lines.join('') + `\n${indentPrefix}}`;
    }

    equals(leftNode, rightNode) {
        const leftNative = YuiType.toNative(leftNode);
        const rightNative = YuiType.toNative(rightNode);
        if (typeof rightNative !== 'object' || rightNative === null || Array.isArray(rightNative)) {
            return false;
        }
        const lKeys = Object.keys(leftNative);
        const rKeys = Object.keys(rightNative);
        if (lKeys.length !== rKeys.length) return false;
        if (!lKeys.every(k => rKeys.includes(k))) return false;
        return lKeys.every(k => _arrayEqual(leftNative[k], rightNative[k]));
    }
}

// ─────────────────────────────────────────────
// Instantiate type singletons
// ─────────────────────────────────────────────

NullType    = new YuiNullType();
BoolType = new YuiBooleanType();
IntType     = new YuiIntType();
FloatType   = new YuiFloatType();
NumberType  = new YuiNumberType();
StringType  = new YuiStringType();
ObjectType  = new YuiObjectType();
ArrayType   = new YuiArrayType();

// bool must come before int (in Python, bool is subclass of int; in JS they're distinct)
export const TYPES = [
    NullType,
    BoolType,
    IntType,
    FloatType,
    NumberType,
    StringType,
    ArrayType,
    ObjectType,
];

function _typing(value) {
    for (const ty of TYPES) {
        if (ty.match(value)) return ty;
    }
    throw new Error(`unknown type for value: ${value}`);
}

// ─────────────────────────────────────────────
// YuiValue
// ─────────────────────────────────────────────

export class YuiValue {
    constructor(nativeValue, type = null) {
        this._nativeValue = nativeValue instanceof YuiValue ? nativeValue.native : YuiType.toNative(nativeValue);
        this.type = type !== null ? type : _typing(nativeValue);
        this._elements = null;
        this._sign = null;
        this.innerView = false;
    }

    get sign() {
        return this._sign !== null ? this._sign : 1;
    }

    get native() {
        if (this._nativeValue === null && this._elements !== null) {
            this._nativeValue = this.type.toNative(this._elements, this._sign);
        }
        return this._nativeValue;
    }

    get arrayview() {
        if (this._elements === null) {
            this._sign = this.type.toSign(this._nativeValue);
            this._elements = this.type.toArrayview(this._nativeValue);
            this._nativeValue = null;  // elements を使うので native キャッシュを無効化
            this.innerView = true;
        }
        return this._elements;
    }

    // Alias
    get array() {
        return this.arrayview;
    }

    getItem(nodeOrIndex, getindexNode = null) {
        if (types.isString(nodeOrIndex) && types.isObject(this)) {
            const key = YuiType.matchedNative(nodeOrIndex);
            const obj = YuiType.matchedNative(this);
            const val = obj[key];
            return types.box(val !== undefined ? val : YuiValue.NullValue);
        }
        IntType.matchOrRaise(nodeOrIndex, getindexNode);
        const index = YuiType.matchedNative(nodeOrIndex);
        const elements = this.arrayview;
        this.innerView = true;
        if (index < 0) {
            throw new YuiError(['index-error', '✅>=0', `❌${index}`], getindexNode);
        }
        // int type: implicit leading zeros for out-of-range
        if (this.type instanceof YuiIntType && index >= elements.length) {
            return types.box(0);
        }
        if (index >= elements.length) {
            throw new YuiError(
                ['index-error', `✅<${elements.length}`, `❌${index}`, `🔍${elements}`],
                getindexNode
            );
        }
        return types.box(elements[index]);
    }

    setItem(nodeOrIndex, nodeOrValue, getindexNode = null) {
        const value = types.array_unbox(nodeOrValue);
        if (this.type.isImmutable()) {
            throw new YuiError(['immutable-set', `❌${this.type}`], null);
        }
        if (types.isString(nodeOrIndex) && types.isObject(this)) {
            const key = YuiType.matchedNative(nodeOrIndex);
            const obj = this._nativeValue;
            obj[key] = value;
            this._elements = null;
            return;
        }
        IntType.matchOrRaise(nodeOrIndex, getindexNode);
        const index = YuiType.matchedNative(nodeOrIndex);
        if (index < 0) {
            throw new YuiError(['index-error', '✅>=0', `❌${index}`], getindexNode);
        }
        const elements = this.arrayview;
        if (index >= elements.length) {
            throw new YuiError(
                ['index-error', `✅<${elements.length}`, `❌${index}`, `🔍${elements}`],
                getindexNode
            );
        }
        this.innerView = true;
        elements[index] = value;
        try {
            this.type.toNative(elements, this._sign, getindexNode);
        } catch (e) {
            this.type = ArrayType;
            throw e;
        }
        this._nativeValue = null;
    }

    append(nodeOrValue, appendNode = null) {
        const value = types.array_unbox(nodeOrValue);
        if (this.type.isImmutable()) {
            throw new YuiError(['immutable-append', `❌${this.type}`], appendNode);
        }
        this.arrayview.push(value);
        this.innerView = true;
        try {
            this.type.toNative(this.arrayview, this._sign, appendNode);
        } catch (e) {
            this.type = ArrayType;
            throw e;
        }
        this._nativeValue = null;
    }

    isPrimitive() {
        return this.type instanceof YuiNullType ||
               this.type instanceof YuiBooleanType ||
               this.type instanceof YuiIntType ||
               this.type instanceof YuiFloatType ||
               this.type instanceof YuiStringType;
    }

    static stringfyValue(value, indentPrefix = '', width = 80) {
        if (value instanceof YuiValue) {
            return value.stringfy(indentPrefix, false, width);
        }
        return String(value);
    }

    stringfy(indentPrefix = '', innerView = false, width = 80) {
        const nativeView = this.type.stringfy(this.native, indentPrefix, width);
        if (innerView === true && this.innerView && this.type.isArrayUnboxed()) {
            const elements = this._elements;
            const arrayView = ArrayType.stringfy(elements, null, ',', width);
            // Python: f"{native_view:12}   🔬{array_view}"
            const padded = nativeView.length >= 12 ? nativeView : nativeView + ' '.repeat(12 - nativeView.length);
            return `${padded}   🔬${arrayView}`;
        }
        return nativeView;
    }

    equals(otherNode) {
        return this.type.equals(this, otherNode);
    }

    lessThan(otherNode, op = '<') {
        return this.type.lessThan(this, otherNode, op);
    }

    toString() {
        return this.stringfy(null);
    }
}

// Special constant values
YuiValue.NullValue  = new YuiValue(null,  NullType);
YuiValue.TrueValue  = new YuiValue(true,  BoolType);
YuiValue.FalseValue = new YuiValue(false, BoolType);

// ─────────────────────────────────────────────
// Operators
// ─────────────────────────────────────────────

export class Operator {
    constructor(symbol, precedence = 0) {
        this.symbol = symbol;
        this.precedence = precedence;
    }

    get comparative() {
        return this.precedence === 3;
    }

    toString() {
        return this.symbol;
    }

    evaluate(leftNode, rightNode) {
        throw new Error('Abstract method: evaluate');
    }
}

export class Equals extends Operator {
    constructor(symbol = '==') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return leftNode.type.equals(leftNode, rightNode);
    }
}

export class NotEquals extends Operator {
    constructor(symbol = '!=') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return !leftNode.type.equals(leftNode, rightNode);
    }
}

export class LessThan extends Operator {
    constructor(symbol = '<') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return !leftNode.type.equals(leftNode, rightNode) &&
               leftNode.type.lessThan(leftNode, rightNode, this.symbol);
    }
}

export class GreaterThan extends Operator {
    constructor(symbol = '>') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return !leftNode.type.equals(leftNode, rightNode) &&
               !leftNode.type.lessThan(leftNode, rightNode, this.symbol);
    }
}

export class LessThanEquals extends Operator {
    constructor(symbol = '<=') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return leftNode.type.equals(leftNode, rightNode) ||
               leftNode.type.lessThan(leftNode, rightNode, this.symbol);
    }
}

export class GreaterThanEquals extends Operator {
    constructor(symbol = '>=') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        return leftNode.type.equals(leftNode, rightNode) ||
               !leftNode.type.lessThan(leftNode, rightNode, this.symbol);
    }
}

export class In extends Operator {
    constructor(symbol = 'in') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        const rightArray = rightNode.arrayview;
        for (const element of rightArray) {
            if (leftNode.type.equals(leftNode, element)) return true;
        }
        return false;
    }
}

export class NotIn extends Operator {
    constructor(symbol = 'notin') {
        super(symbol, 3);
    }

    evaluate(leftNode, rightNode) {
        const rightArray = rightNode.arrayview;
        for (const element of rightArray) {
            if (leftNode.type.equals(leftNode, element)) return false;
        }
        return true;
    }
}

export class Add extends Operator {
    constructor(symbol = '+') { super(symbol, 2); }
    evaluate(left, right) {
        if (types.isString(left) && types.isString(right)) {
            return new YuiValue(YuiType.matchedNative(left) + YuiType.matchedNative(right));
        }
        if (types.isArray(left) && types.isArray(right)) {
            return new YuiValue([...left.array, ...right.array]);
        }
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left), r = YuiType.matchedNative(right);
        const isFloat = types.isFloat(left) || types.isFloat(right);
        return isFloat ? new YuiValue(l + r, FloatType) : new YuiValue(l + r);
    }
}

export class Sub extends Operator {
    constructor(symbol = '-') { super(symbol, 2); }
    evaluate(left, right) {
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left), r = YuiType.matchedNative(right);
        const isFloat = types.isFloat(left) || types.isFloat(right);
        return isFloat ? new YuiValue(l - r, FloatType) : new YuiValue(l - r);
    }
}

export class Mul extends Operator {
    constructor(symbol = '*') { super(symbol, 1); }
    evaluate(left, right) {
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left), r = YuiType.matchedNative(right);
        const isFloat = types.isFloat(left) || types.isFloat(right);
        return isFloat ? new YuiValue(l * r, FloatType) : new YuiValue(l * r);
    }
}

export class Div extends Operator {
    constructor(symbol = '/') { super(symbol, 1); }
    evaluate(left, right) {
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left), r = YuiType.matchedNative(right);
        if (r === 0) throw new YuiError(['division-by-zero', `❌${r}`], null);
        const isFloat = types.isFloat(left) || types.isFloat(right);
        return isFloat ? new YuiValue(l / r, FloatType) : new YuiValue(Math.floor(l / r));
    }
}

export class Mod extends Operator {
    constructor(symbol = '%') { super(symbol, 1); }
    evaluate(left, right) {
        NumberType.matchOrRaise(left);
        NumberType.matchOrRaise(right);
        const l = YuiType.matchedNative(left), r = YuiType.matchedNative(right);
        if (r === 0) throw new YuiError(['division-by-zero', `❌${r}`], null);
        const isFloat = types.isFloat(left) || types.isFloat(right);
        const result = isFloat ? l % r : ((l % r) + r) % r;
        return isFloat ? new YuiValue(result, FloatType) : new YuiValue(result);
    }
}

export const OPERATORS = {
    '==': new Equals(),
    '!=': new NotEquals(),
    '<':  new LessThan(),
    '>':  new GreaterThan(),
    '<=': new LessThanEquals(),
    '>=': new GreaterThanEquals(),
    'in': new In(),
    'notin': new NotIn(),
    '+': new Add(),
    '-': new Sub(),
    '*': new Mul(),
    '/': new Div(),
    '%': new Mod(),
};

// ─────────────────────────────────────────────
// types utility object (mirrors Python's `types` class in yuitypes.py)
// ─────────────────────────────────────────────

export const types = {
    box(value) {
        if (value instanceof YuiValue) return value;
        if (value === null || value === undefined) return YuiValue.NullValue;
        if (typeof value === 'boolean') return value ? YuiValue.TrueValue : YuiValue.FalseValue;
        return new YuiValue(value);
    },
    unbox(value) { return YuiType.toNative(value); },
    arrayUnbox(value) { return YuiType.intoArrayview(value); },
    array_unbox(value) { return YuiType.intoArrayview(value); },
    isBool(v)   { return BoolType.match(v); },
    isInt(v)    { return IntType.match(v); },
    isFloat(v)  { return FloatType.match(v); },
    isNumber(v) { return NumberType.match(v); },
    isString(v) { return StringType.match(v); },
    isArray(v)  { return ArrayType.match(v); },
    isObject(v) { return ObjectType.match(v); },
    is_bool(v)   { return BoolType.match(v); },
    is_int(v)    { return IntType.match(v); },
    is_float(v)  { return FloatType.match(v); },
    is_number(v) { return NumberType.match(v); },
    is_string(v) { return StringType.match(v); },
    is_array(v)  { return ArrayType.match(v); },
    is_object(v) { return ObjectType.match(v); },
    formatJson(v) { return YuiType.arrayviewS(v); },
    format_json(v) { return YuiType.arrayviewS(v); },
    arrayviewS(v) { return YuiType.arrayviewS(v); },
    compare(l, r) { return YuiType.compare(l, r); },
};

// Wire operators into yuiast
setOperators(OPERATORS);
