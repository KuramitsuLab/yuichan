// yuitypes.js — Yui の型システム, YuiValue, オペレータ
// Python 版 yuichan/yuitypes.py の移植
//
// 依存: yuierror.js のみ。
//
// JS ⇔ Python の主な差分:
// - Python の bool は int のサブクラスだが JS は typeof で区別できるので
//   TYPES の順序問題は無くなる (とはいえ Python 側と一致させて順序は保つ)
// - Python の int と float は別型だが JS は number しかないので
//   `Number.isInteger(x)` で区別する → 1.0 リテラルは int 扱い。
//   float として扱いたい場合は `new YuiValue(x, FloatType)` を明示する。
// - 任意精度整数のビット演算は 32bit に丸められるため、LSB 配列との
//   変換には `Math.floor(n/2)` と `bit * 2**i` を使う (2^53 まで安全)。
// - `this._nativeValue = undefined` を「未計算」の番兵にして、
//   native === null が正当な NullValue と区別できるようにしている。

import { YuiError } from './yuierror.js';

// ─────────────────────────────────────────────
// 型記号 (絵文字) 定数
// ─────────────────────────────────────────────
export const TY_NULL = '🚫';
export const TY_BOOLEAN = '🎭';
export const TY_INT = '🔢';
export const TY_FLOAT = '📊';
export const TY_NUMBER = '🔢';
export const TY_ARRAY = '🍡';
export const TY_OBJECT = '🗂️';
export const TY_STRING = '🔤';

// ─────────────────────────────────────────────
// YuiType 基底クラス (抽象クラス相当)
// ─────────────────────────────────────────────
export class YuiType {
  constructor(name, emoji) {
    this.name = name;
    this.emoji = emoji;
  }

  toString() {
    return this.emoji;
  }

  is_immutable() {
    return false;
  }

  is_array_unboxed() {
    return true;
  }

  match(_value) {
    throw new Error('abstract YuiType.match');
  }

  match_or_raise(value, node = null) {
    if (!this.match(value)) {
      throw new YuiError(
        ['type-error', `✅<${this.emoji}${this.name}>`, `❌${value}`],
        node,
      );
    }
  }

  to_arrayview(_nativeValue) {
    throw new Error('abstract YuiType.to_arrayview');
  }

  to_sign(_nativeValue) {
    return 1;
  }

  to_native(_elements, _sign = 1, _node = null) {
    throw new Error('abstract YuiType.to_native');
  }

  stringify(_nativeValue, _indentPrefix = '', _width = 80) {
    throw new Error('abstract YuiType.stringify');
  }

  equals(left, right) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    return l === r;
  }

  less_than(left, right, op = '<', binaryNode = null) {
    throw new YuiError(['imcomparable', `❌${left} ${op} ${right}`], binaryNode);
  }
}

// ─────────────────────────────────────────────
// YuiNullType
// ─────────────────────────────────────────────
export class YuiNullType extends YuiType {
  constructor() {
    super('null', TY_NULL);
  }

  is_immutable() {
    return true;
  }

  match(value) {
    return (
      value === null ||
      value === undefined ||
      (value instanceof YuiValue && value.type instanceof YuiNullType)
    );
  }

  to_arrayview(_n) {
    return [];
  }

  to_native(_elements, _sign = 1, _node = null) {
    return null;
  }

  stringify(_nativeValue, _indentPrefix = '', _width = 80) {
    return 'null';
  }
}

// ─────────────────────────────────────────────
// YuiBooleanType
// ─────────────────────────────────────────────
export class YuiBooleanType extends YuiType {
  constructor() {
    super('boolean', TY_BOOLEAN);
  }

  is_immutable() {
    return true;
  }

  match(value) {
    return (
      typeof value === 'boolean' ||
      (value instanceof YuiValue && value.type instanceof YuiBooleanType)
    );
  }

  to_arrayview(n) {
    return n ? [1] : [0];
  }

  to_native(elements, _sign = 1, _node = null) {
    return elements && elements.length > 0 ? Boolean(elements[0]) : false;
  }

  stringify(nativeValue, _indentPrefix = '', _width = 80) {
    return nativeValue ? 'true' : 'false';
  }

  equals(left, right, _binaryNode = null) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'boolean') {
      return l === r;
    }
    return false;
  }

  less_than(left, right, op = '<', binaryNode = null) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'boolean') {
      return Number(l) < Number(r);
    }
    return super.less_than(left, right, op, binaryNode);
  }
}

// ─────────────────────────────────────────────
// YuiIntType
// ─────────────────────────────────────────────
export class YuiIntType extends YuiType {
  constructor() {
    super('int', TY_INT);
  }

  match(value) {
    return (
      (typeof value === 'number' && Number.isInteger(value)) ||
      (value instanceof YuiValue && value.type instanceof YuiIntType)
    );
  }

  to_sign(nativeValue) {
    return nativeValue < 0 ? -1 : 1;
  }

  /** 整数の絶対値を可変長 LSB ファースト配列に変換 (0 は空配列) */
  to_arrayview(nativeValue) {
    let n = Math.abs(nativeValue);
    const bits = [];
    while (n > 0) {
      bits.push(n % 2);
      n = Math.floor(n / 2);
    }
    return bits;
  }

  /** 可変長 LSB ファースト配列を整数に変換 */
  to_native(bits, sign = 1, node = null) {
    let n = 0;
    for (let i = 0; i < bits.length; i++) {
      const bit = bits[i];
      if (typeof bit === 'boolean' || (bit !== 0 && bit !== 1)) {
        const array = ArrayType.stringify(bits, null, 80, ',');
        throw new YuiError(
          ['array-value-error', `❌${types.format_json(bit)}`, '✅0/1', `🔍${array}`],
          node,
        );
      }
      n += bit * Math.pow(2, i);
    }
    return sign * n;
  }

  stringify(nativeValue, _indentPrefix = '', _width = 80) {
    return `${nativeValue}`;
  }

  stringify_arrayview(arrayview, sign) {
    return `${sign < 0 ? '-' : ''}[${arrayview.join(',')}]`;
  }

  equals(left, right) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'boolean') return false; // bool は int と等しくない
    if (typeof r === 'number') {
      // int vs float は小数点以下 6 桁で比較
      return _round6(l) === _round6(r);
    }
    return l === r;
  }

  less_than(left, right, op = '<', binaryNode = null) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'number') {
      return _round6(l) < _round6(r);
    }
    return super.less_than(left, right, op, binaryNode);
  }
}

// ─────────────────────────────────────────────
// YuiFloatType
// ─────────────────────────────────────────────
export class YuiFloatType extends YuiType {
  constructor() {
    super('float', TY_FLOAT);
  }

  match(value) {
    // 非整数の number は float 扱い (1.5 は float, 1 は int)。
    // 明示的に FloatType でラップされた YuiValue も許容。
    return (
      (typeof value === 'number' && !Number.isInteger(value)) ||
      (value instanceof YuiValue && value.type instanceof YuiFloatType)
    );
  }

  to_sign(x) {
    return x < 0 ? -1 : 1;
  }

  /**
   * 浮動小数点数の絶対値を LSB ファーストの一桁整数配列に変換。
   *   3.14  → [0, 0, 0, 0, 4, 1, 3]  (sign=1)
   *   -3.14 → [0, 0, 0, 0, 4, 1, 3]  (sign=-1)
   */
  to_arrayview(x) {
    const s = Math.abs(x).toFixed(6).replace('.', '');
    const digits = [];
    for (const ch of s) {
      digits.push(parseInt(ch, 10));
    }
    return digits.reverse();
  }

  /** LSB ファーストの一桁整数配列を浮動小数点数に変換 */
  to_native(digits, sign = 1, node = null) {
    for (const d of digits) {
      if (!(typeof d === 'number' && Number.isInteger(d) && d >= 0 && d <= 9)) {
        const array = ArrayType.stringify(digits, null, 80, ',');
        throw new YuiError(
          ['array-value-error', `❌${types.format_json(d)}`, '✅0-9', `🔍${array}`],
          node,
        );
      }
    }
    // MSB ファーストに戻す
    const msb = [...digits].reverse();
    const s = msb.join('');
    let value;
    if (s.length <= 6) {
      value = parseFloat('0.' + s.padStart(6, '0'));
    } else {
      value = parseFloat(s.slice(0, -6) + '.' + s.slice(-6));
    }
    return sign * value;
  }

  stringify(nativeValue, _indentPrefix = '', _width = 80) {
    return nativeValue.toFixed(6);
  }

  equals(left, right) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'boolean') return false;
    if (typeof r === 'number') {
      return _round6(l) === _round6(r);
    }
    return false;
  }

  less_than(left, right, op = '<', binaryNode = null) {
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (typeof r === 'number') {
      return l < r;
    }
    return super.less_than(left, right, op, binaryNode);
  }
}

// ─────────────────────────────────────────────
// YuiNumberType (union: int | float)
// ─────────────────────────────────────────────
export class YuiNumberType extends YuiType {
  constructor() {
    super('number', TY_NUMBER);
  }

  match(value) {
    return IntType.match(value) || FloatType.match(value);
  }

  to_arrayview(_v) {
    throw new Error('NumberType is a union type; use IntType or FloatType');
  }

  to_native(_elements, _sign = 1, _node = null) {
    throw new Error('NumberType is a union type; use IntType or FloatType');
  }

  stringify(_v, _indentPrefix = '', _width = 80) {
    throw new Error('NumberType is a union type; use IntType or FloatType');
  }
}

// ─────────────────────────────────────────────
// YuiStringType
// ─────────────────────────────────────────────
export class YuiStringType extends YuiType {
  constructor() {
    super('string', TY_STRING);
  }

  match(value) {
    return (
      typeof value === 'string' ||
      (value instanceof YuiValue && value.type instanceof YuiStringType)
    );
  }

  /** 文字コード (Unicode code point) 配列に変換 */
  to_arrayview(x) {
    const codes = [];
    for (const ch of x) {
      codes.push(ch.codePointAt(0));
    }
    return codes;
  }

  to_native(elements, _sign = 1, node = null) {
    const parts = [];
    for (const d of elements) {
      if (!(typeof d === 'number' && Number.isInteger(d) && d >= 0 && d <= 0x10ffff)) {
        const array = ArrayType.stringify(elements, null, 80, ',');
        throw new YuiError(
          ['array-value-error', `❌${types.format_json(d)}`, '✅<文字コード>', `🔍${array}`],
          node,
        );
      }
      parts.push(String.fromCodePoint(d));
    }
    return parts.join('');
  }

  stringify(nativeValue, _indentPrefix = '', _width = 80) {
    return types.format_json(nativeValue);
  }

  equals(left, right) {
    const l = types.unbox(left);
    if (types.is_string(right)) {
      return l === types.unbox(right);
    }
    return false;
  }

  less_than(left, right, _op = '<', _binaryNode = null) {
    const l = types.unbox(left);
    if (types.is_string(right)) {
      const r = types.unbox(right);
      return l < r;
    }
    return false;
  }
}

// ─────────────────────────────────────────────
// YuiArrayType
// ─────────────────────────────────────────────
export class YuiArrayType extends YuiType {
  constructor() {
    super('array', TY_ARRAY);
  }

  is_array_unboxed() {
    return false;
  }

  match(value) {
    return (
      Array.isArray(value) ||
      (value instanceof YuiValue && value.type instanceof YuiArrayType)
    );
  }

  to_arrayview(arrayValue) {
    return arrayValue.map((v) => types.array_unbox(v));
  }

  to_native(elements, _sign = 1, _node = null) {
    const result = [];
    for (const el of elements) {
      if (el instanceof YuiValue) {
        result.push(el.native);
      } else {
        result.push(el);
      }
    }
    return result;
  }

  stringify(elements, indentPrefix = '', width = 80, comma = ', ') {
    // まずワンライン版を組み立てる
    const content = `[${elements.map((el) => types.format_json(el)).join(comma)}]`;
    if (indentPrefix === null || indentPrefix.length + content.length <= width) {
      return content;
    }
    // 折り返し版
    const innerIndent = indentPrefix + '  ';
    const LF = '\n';
    const formatted = elements.map((el) =>
      el instanceof YuiValue
        ? el.stringify(innerIndent, false, width)
        : types.format_json(el),
    );
    return `[${LF}${innerIndent}${formatted.join(`,${LF}${innerIndent}`)}${LF}${indentPrefix}]`;
  }

  equals(left, right, _binaryNode = null) {
    if (!types.is_array(right) && !types.is_string(right)) {
      return false;
    }
    const ln = types.unbox(left);
    const rn = types.unbox(right);
    return _array_equal(ln, rn);
  }
}

/** 配列の再帰的等価比較 (文字コード配列 ⇔ 文字列 の相互比較を含む) */
function _array_equal(a, b) {
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((el, i) => _array_equal(el, b[i]));
  }
  if (Array.isArray(a) && typeof b === 'string') {
    try {
      const s = a.map((c) => String.fromCodePoint(c)).join('');
      return s === b;
    } catch (_e) {
      return false;
    }
  }
  if (typeof a === 'string' && Array.isArray(b)) {
    return _array_equal(b, a);
  }
  // 深いオブジェクト比較 (YuiObjectType.equals から来る可能性)
  if (a && typeof a === 'object' && b && typeof b === 'object') {
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    for (const k of ka) {
      if (!Object.prototype.hasOwnProperty.call(b, k)) return false;
      if (!_array_equal(a[k], b[k])) return false;
    }
    return true;
  }
  return a === b;
}

// ─────────────────────────────────────────────
// YuiObjectType
// ─────────────────────────────────────────────
export class YuiObjectType extends YuiType {
  constructor() {
    super('object', TY_OBJECT);
  }

  is_array_unboxed() {
    return false;
  }

  match(value) {
    return (
      (value !== null &&
        typeof value === 'object' &&
        !Array.isArray(value) &&
        !(value instanceof YuiValue)) ||
      (value instanceof YuiValue && value.type instanceof YuiObjectType)
    );
  }

  /** key/value の配列をエンコード (各要素は YuiValue([key, value])) */
  to_arrayview(objectValue) {
    const elements = [];
    for (const [key, value] of Object.entries(objectValue)) {
      elements.push(new YuiValue([String(key), types.array_unbox(value)]));
    }
    return elements;
  }

  to_native(elements, _sign = 1, node = null) {
    const obj = {};
    for (let kv of elements) {
      if (!(kv instanceof YuiValue)) {
        throw new YuiError(
          ['array-value-error', `❌${kv}`, '✅[key, value]', `🔍${elements}`],
          node,
        );
      }
      const pair = kv.native;
      if (!Array.isArray(pair) || pair.length !== 2) {
        throw new YuiError(
          ['array-value-error', `❌${pair}`, '✅[key, value]', `🔍${elements}`],
          node,
        );
      }
      const key = pair[0];
      if (typeof key !== 'string') {
        throw new YuiError(
          ['array-value-error', `❌${key}`, '✅<string>', `🔍${pair}`],
          node,
        );
      }
      obj[key] = pair[1];
    }
    return obj;
  }

  stringify(nativeValue, indentPrefix = '', width = 80) {
    const entries = Object.entries(nativeValue);
    const content = `{${entries.map(([k, v]) => `"${k}": ${types.format_json(v)}`).join(', ')}}`;
    if (indentPrefix === null || indentPrefix.length + content.length <= width) {
      return content;
    }
    const innerIndent = indentPrefix + '  ';
    const LF = '\n';
    const formatted = entries.map(([key, value]) => {
      const valStr = value instanceof YuiValue
        ? value.stringify(innerIndent, false, width)
        : types.format_json(value);
      return `"${key}": ${valStr}`;
    });
    return `{${LF}${innerIndent}${formatted.join(`,${LF}${innerIndent}`)}${LF}${indentPrefix}}`;
  }

  equals(left, right, _binaryNode = null) {
    const ln = types.unbox(left);
    const rn = types.unbox(right);
    if (rn === null || typeof rn !== 'object' || Array.isArray(rn)) {
      return false;
    }
    const lk = Object.keys(ln);
    const rk = Object.keys(rn);
    if (lk.length !== rk.length) return false;
    const lkSet = new Set(lk);
    for (const k of rk) {
      if (!lkSet.has(k)) return false;
    }
    for (const k of lk) {
      if (!_array_equal(ln[k], rn[k])) return false;
    }
    return true;
  }
}

// ─────────────────────────────────────────────
// 型インスタンス (シングルトン)
// ─────────────────────────────────────────────
export const NullType = new YuiNullType();
export const BoolType = new YuiBooleanType();
export const IntType = new YuiIntType();
export const FloatType = new YuiFloatType();
export const NumberType = new YuiNumberType();
export const StringType = new YuiStringType();
export const ArrayType = new YuiArrayType();
export const ObjectType = new YuiObjectType();

// Python 側と同じ順序。bool を IntType より前に置く (JS では不要だが一致させる)。
const TYPES = [
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
    // YuiValue を渡されたら native を取り出す
    this._nativeValue =
      nativeValue instanceof YuiValue ? nativeValue.native : nativeValue;
    // undefined は null と同じ扱い
    if (this._nativeValue === undefined) this._nativeValue = null;
    this.type = type == null ? _typing(nativeValue) : type;
    this._elements = undefined;
    this._sign = undefined;
    this.inner_view = false;
  }

  get native() {
    if (this._nativeValue === undefined) {
      this._nativeValue = this.type.to_native(this._elements, this._sign);
    }
    return this._nativeValue;
  }

  /** arrayview (LSB ファースト配列) を遅延生成 */
  get array() {
    if (this._elements === undefined) {
      this._elements = this.type.to_arrayview(this._nativeValue);
      this._sign = this.type.to_sign(this._nativeValue);
      this._nativeValue = undefined; // 配列を使うので native キャッシュは無効化
      this.inner_view = true;
    }
    return this._elements;
  }

  get_item(index, getindexNode = null) {
    // object[string] ルックアップ
    if (types.is_string(index) && types.is_object(this)) {
      const key = types.unbox(index);
      const obj = types.unbox(this);
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        return types.box(obj[key]);
      }
      return YuiValue.NullValue;
    }

    IntType.match_or_raise(index, getindexNode);
    const idx = types.unbox(index);
    const elements = this.array;
    this.inner_view = true;

    if (idx < 0) {
      throw new YuiError(['index-error', '✅>=0', `❌${idx}`], getindexNode);
    }
    // int 型は範囲外を暗黙の 0 として返す
    if (this.type instanceof YuiIntType && idx >= elements.length) {
      return types.box(0);
    }
    if (idx >= elements.length) {
      throw new YuiError(
        ['index-error', `✅<${elements.length}`, `❌${idx}`, `🔍${elements}`],
        getindexNode,
      );
    }
    return types.box(elements[idx]);
  }

  set_item(index, value, getindexNode = null) {
    value = types.array_unbox(value);
    if (this.type.is_immutable()) {
      throw new YuiError(['immutable-set', `❌${this.type}`], null);
    }
    if (types.is_string(index) && types.is_object(this)) {
      const key = types.unbox(index);
      // native を直接取得して in-place で更新
      const obj = this.native;
      obj[key] = value;
      this._elements = undefined;
      return;
    }
    IntType.match_or_raise(index, getindexNode);
    const idx = types.unbox(index);
    if (idx < 0) {
      throw new YuiError(['index-error', '✅>=0', `❌${idx}`], getindexNode);
    }
    const elements = this.array;
    if (idx >= elements.length) {
      throw new YuiError(
        ['index-error', `✅<${elements.length}`, `❌${idx}`, `🔍${elements}`],
        getindexNode,
      );
    }
    this.inner_view = true;
    elements[idx] = value;
    try {
      this.type.to_native(elements, this._sign, getindexNode);
    } catch (e) {
      if (e instanceof YuiError) {
        this.type = ArrayType;
      }
      throw e;
    }
    this._nativeValue = undefined;
  }

  append(value, appendNode = null) {
    value = types.array_unbox(value);
    if (this.type.is_immutable()) {
      throw new YuiError(['immutable-append', `❌${this.type}`], appendNode);
    }
    this.array.push(value);
    this.inner_view = true;
    try {
      this.type.to_native(this._elements, this._sign, appendNode);
    } catch (e) {
      if (e instanceof YuiError) {
        this.type = ArrayType;
      }
      throw e;
    }
    this._nativeValue = undefined;
  }

  toString() {
    return this.stringify(null);
  }

  stringify(indentPrefix = '', innerView = false, width = 80) {
    const nativeView = this.type.stringify(this.native, indentPrefix, width);
    if (innerView === true && this.inner_view && this.type.is_array_unboxed()) {
      const elements = this.array;
      const arrayView = ArrayType.stringify(elements, null, width, ',');
      return `${nativeView.padEnd(12)}   🔬${arrayView}`;
    }
    return nativeView;
  }

  equals(other) {
    return this.type.equals(this, other);
  }

  less_than(other, op = '<', binaryNode = null) {
    return this.type.less_than(this, other, op, binaryNode);
  }
}

// シングルトン (Python 側の YuiValue.NullValue 等と揃える)
YuiValue.NullValue = new YuiValue(null, NullType);
YuiValue.TrueValue = new YuiValue(true, BoolType);
YuiValue.FalseValue = new YuiValue(false, BoolType);

// ─────────────────────────────────────────────
// types ヘルパー (Python の class types: に相当)
// ─────────────────────────────────────────────
export const types = {
  box(value) {
    if (value instanceof YuiValue) return value;
    if (value === null || value === undefined) return YuiValue.NullValue;
    if (typeof value === 'boolean') {
      return value ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    return new YuiValue(value);
  },

  /**
   * 配列/オブジェクトの中身に入れる用の unbox。
   * array_unboxed な型 (null/bool/int/float/string) はそのまま native を返す。
   * 配列/オブジェクトは YuiValue でくるんで返す。
   */
  array_unbox(value) {
    if (value instanceof YuiValue) {
      if (value.type.is_array_unboxed()) {
        return value.native;
      }
      return value;
    }
    if (Array.isArray(value) || (value !== null && typeof value === 'object')) {
      return new YuiValue(value);
    }
    return value;
  },

  /** 再帰的な unbox: YuiValue / 配列 / オブジェクトの中身も展開する */
  unbox(value) {
    if (value instanceof YuiValue) {
      return types.unbox(value.native);
    }
    if (Array.isArray(value)) {
      return value.map((v) => types.unbox(v));
    }
    if (value !== null && typeof value === 'object') {
      const out = {};
      for (const [k, v] of Object.entries(value)) {
        out[String(k)] = types.unbox(v);
      }
      return out;
    }
    return value;
  },

  is_null(v) {
    return NullType.match(v);
  },
  is_bool(v) {
    return BoolType.match(v);
  },
  is_int(v) {
    return IntType.match(v);
  },
  is_float(v) {
    return FloatType.match(v);
  },
  is_number(v) {
    return NumberType.match(v);
  },
  is_string(v) {
    return StringType.match(v);
  },
  is_array(v) {
    return ArrayType.match(v);
  },
  is_object(v) {
    return ObjectType.match(v);
  },

  /**
   * Python の yuichan.types.format_json に相当。
   * JS 側は int/float が number に統合されているため、Number.isInteger で分岐する。
   */
  format_json(value) {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'string') {
      const v = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
      return `"${v}"`;
    }
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return String(value);
      return value.toFixed(6);
    }
    if (value instanceof YuiValue) {
      return value.stringify(null);
    }
    if (Array.isArray(value)) {
      return '[' + value.map((v) => types.format_json(v)).join(', ') + ']';
    }
    if (typeof value === 'object') {
      const parts = Object.entries(value).map(
        ([k, v]) => `"${k}": ${types.format_json(v)}`,
      );
      return '{' + parts.join(', ') + '}';
    }
    return String(value);
  },

  /** ネイティブ値の配列ビュー文字列表現 (コード生成用) */
  arrayview_s(nativeValue) {
    let elements, sign;
    if (typeof nativeValue === 'boolean') {
      elements = BoolType.to_arrayview(nativeValue);
      sign = 1;
    } else if (typeof nativeValue === 'number' && Number.isInteger(nativeValue)) {
      elements = IntType.to_arrayview(nativeValue);
      sign = IntType.to_sign(nativeValue);
    } else if (typeof nativeValue === 'number') {
      elements = FloatType.to_arrayview(nativeValue);
      sign = FloatType.to_sign(nativeValue);
    } else {
      return String(nativeValue);
    }
    return `${sign < 0 ? '-' : ''}[${elements.join(',')}]`;
  },

  compare(left, right) {
    if (types.is_number(left) && types.is_number(right)) {
      const l = _round6(types.unbox(left));
      const r = _round6(types.unbox(right));
      return _compare(l, r);
    }
    if (types.is_string(left) && types.is_string(right)) {
      const l = types.unbox(left);
      const r = types.unbox(right);
      return _compare(l, r);
    }
    let l = left;
    let r = right;
    if (!(r instanceof YuiValue)) {
      r = new YuiValue(r);
    }
    if (!(l instanceof YuiValue)) {
      l = new YuiValue(l);
    }
    return _compare(l.array, r.array);
  },
};

function _round6(n) {
  // Python の round(x, 6) 相当 (banker's rounding の微差は無視)
  return Math.round(n * 1_000_000) / 1_000_000;
}

function _compare(l, r) {
  if (Array.isArray(l) && Array.isArray(r)) {
    for (let i = 0; i < Math.min(l.length, r.length); i++) {
      const c = _compare(l[i], r[i]);
      if (c !== 0) return c;
    }
    return _compare(l.length, r.length);
  }
  if (l === r) return 0;
  if (l < r) return -1;
  return 1;
}

// ─────────────────────────────────────────────
// オペレータ
// ─────────────────────────────────────────────
export class Operator {
  constructor(symbol, precedence = 0) {
    this.symbol = symbol;
    this.precedence = precedence;
  }

  toString() {
    return this.symbol;
  }

  get comparative() {
    return this.precedence === 3;
  }

  evaluate(_left, _right, _binaryNode = null) {
    throw new Error('abstract Operator.evaluate');
  }
}

export class Equals extends Operator {
  constructor(symbol = '==') {
    super(symbol, 3);
  }
  evaluate(left, right, _binaryNode = null) {
    return left.equals(right);
  }
}

export class NotEquals extends Operator {
  constructor(symbol = '!=') {
    super(symbol, 3);
  }
  evaluate(left, right, _binaryNode = null) {
    return !left.equals(right);
  }
}

export class LessThan extends Operator {
  constructor(symbol = '<') {
    super(symbol, 3);
  }
  evaluate(left, right, binaryNode = null) {
    return !left.equals(right) && left.less_than(right, this.symbol, binaryNode);
  }
}

export class GreaterThan extends Operator {
  constructor(symbol = '>') {
    super(symbol, 3);
  }
  evaluate(left, right, binaryNode = null) {
    return !left.equals(right) && !left.less_than(right, this.symbol, binaryNode);
  }
}

export class LessThanEquals extends Operator {
  constructor(symbol = '<=') {
    super(symbol, 3);
  }
  evaluate(left, right, binaryNode = null) {
    return left.equals(right) || left.less_than(right, this.symbol, binaryNode);
  }
}

export class GreaterThanEquals extends Operator {
  constructor(symbol = '>=') {
    super(symbol, 3);
  }
  evaluate(left, right, binaryNode = null) {
    return left.equals(right) || !left.less_than(right, this.symbol, binaryNode);
  }
}

export class In extends Operator {
  constructor(symbol = 'in') {
    super(symbol, 3);
  }
  evaluate(left, right, _binaryNode = null) {
    const arr = right.array;
    for (const el of arr) {
      if (left.equals(el)) return true;
    }
    return false;
  }
}

export class NotIn extends Operator {
  constructor(symbol = 'notin') {
    super(symbol, 3);
  }
  evaluate(left, right, _binaryNode = null) {
    const arr = right.array;
    for (const el of arr) {
      if (left.equals(el)) return false;
    }
    return true;
  }
}

// Python SSoT に合わせて各 evaluate() は生のネイティブ値を返す。
// 「int OP float → float」の保全は、オペランド情報が残っている visitBinaryNode
// 側 (yuiruntime.js) で行う。JS では `Number.isInteger(3) === true` なので
// `1.5 + 1.5 = 3` の結果を int 扱いしないよう、呼び出し側で明示的に FloatType で
// box する必要がある (Python では `isinstance(3.0, float) == True` で判別できる)。

export class Add extends Operator {
  constructor(symbol = '+') {
    super(symbol, 2);
  }
  evaluate(left, right, binaryNode = null) {
    if (types.is_string(left) && types.is_string(right)) {
      return types.unbox(left) + types.unbox(right);
    }
    if (types.is_array(left) && types.is_array(right)) {
      return [...left.native, ...right.native];
    }
    NumberType.match_or_raise(left, binaryNode);
    NumberType.match_or_raise(right, binaryNode);
    return types.unbox(left) + types.unbox(right);
  }
}

export class Sub extends Operator {
  constructor(symbol = '-') {
    super(symbol, 2);
  }
  evaluate(left, right, binaryNode = null) {
    NumberType.match_or_raise(left, binaryNode);
    NumberType.match_or_raise(right, binaryNode);
    return types.unbox(left) - types.unbox(right);
  }
}

export class Mul extends Operator {
  constructor(symbol = '*') {
    super(symbol, 1);
  }
  evaluate(left, right, binaryNode = null) {
    NumberType.match_or_raise(left, binaryNode);
    NumberType.match_or_raise(right, binaryNode);
    return types.unbox(left) * types.unbox(right);
  }
}

export class Div extends Operator {
  constructor(symbol = '/') {
    super(symbol, 1);
  }
  evaluate(left, right, binaryNode = null) {
    NumberType.match_or_raise(left, binaryNode);
    NumberType.match_or_raise(right, binaryNode);
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (r === 0) {
      throw new YuiError(['division-by-zero', `❌${r}`], binaryNode);
    }
    if (types.is_float(left) || types.is_float(right)) {
      // 真の除算: 生のネイティブ float を返す (FloatType の保全は呼び出し側)
      return l / r;
    }
    // Python の floor division (負数に対しても床) 相当
    return Math.floor(l / r);
  }
}

export class Mod extends Operator {
  constructor(symbol = '%') {
    super(symbol, 1);
  }
  evaluate(left, right, binaryNode = null) {
    NumberType.match_or_raise(left, binaryNode);
    NumberType.match_or_raise(right, binaryNode);
    const l = types.unbox(left);
    const r = types.unbox(right);
    if (r === 0) {
      throw new YuiError(['division-by-zero', `❌${r}`], binaryNode);
    }
    // Python の % は正の除数に対して常に非負を返す
    return ((l % r) + r) % r;
  }
}

export const OPERATORS = {
  '==': new Equals(),
  '!=': new NotEquals(),
  '<': new LessThan(),
  '>': new GreaterThan(),
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

// YuiError も再 export しておく (Python の from .yuitypes import YuiError に相当)
export { YuiError };
