var YuiEditor = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __esm = (fn, res) => function __init() {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  };
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/yuierror.js
  function setVerbose(flag) {
    _verbose = !!flag;
  }
  function isVerbose() {
    return _verbose;
  }
  function vprint(...args) {
    if (_verbose) {
      console.error(...args);
    }
  }
  function formatMessages(messages) {
    if (!messages || messages.length === 0) {
      return "";
    }
    const key = messages[0];
    const display = Object.prototype.hasOwnProperty.call(ERROR_MESSAGES, key) ? ERROR_MESSAGES[key] : key;
    const rest = messages.slice(1).join(" ");
    if (rest) {
      return `${display} ${rest}`.trim();
    }
    return display;
  }
  function normalizeMessages(messages) {
    if (typeof messages === "string") {
      messages = [messages];
    }
    if (!Array.isArray(messages)) {
      messages = Array.from(messages);
    }
    const result = [];
    let parts = [];
    for (const msg of messages) {
      if (msg && msg.length > 0 && msg.codePointAt(0) > 127) {
        if (parts.length > 0) {
          result.push(parts.join("-"));
          parts = [];
        }
        result.push(msg);
      } else {
        parts.push(msg);
      }
    }
    if (parts.length > 0) {
      result.push(parts.join("-"));
    }
    return Object.freeze(result);
  }
  var _verbose, ERROR_MESSAGES, YuiError;
  var init_yuierror = __esm({
    "src/yuierror.js"() {
      _verbose = false;
      ERROR_MESSAGES = {
        // パーサーエラー
        "expected-token": "書き方が間違っています",
        "expected-number": "数値が必要です",
        "expected-string": "文字列が必要です",
        "expected-array": "配列が必要です",
        "expected-object": "オブジェクトが必要です",
        "expected-boolean": "真偽値が必要です",
        "expected-closing": "閉じ括弧が必要です",
        "expected-variable": "ここは変数が必要です",
        "expected-expression": "変数や値が必要です",
        "typo": "うっかり間違えてませんか？",
        "wrong-name": "名前が不正です",
        "wrong-statement": "何とも解釈できない書き方です",
        "wrong-escape-sequence": "不正なエスケープシーケンスです",
        "wrong-indent-level": "インデントが不正です",
        "unexpected-return": "関数内でのみ使えます",
        "unexpected-break": "くり返しの中でのみ使えます",
        // ランタイムエラー
        "undefined-variable": "変数が定義されていません",
        "undefined-function": "関数が定義されていません",
        "type-error": "データの種類（型）が違っています",
        "value-error": "データの値がおかしいです",
        "array-value-error": "値がおかしくて配列データが壊れます",
        "division-by-zero": "ゼロで割ってしまいました",
        "error-index": "配列のインデックスが範囲外です",
        "error-value": "値エラーです",
        "too-many-recursion": "再帰が深すぎます",
        "runtime-timeout": "タイムアウトしました",
        "unsupported-operator": "サポートされていない演算子です",
        "imcomparable": "両者は直接比較できません",
        "mismatch-argument": "引数の数が合いません",
        "not-negative-number": "負の数は使えません",
        "float-conversion": "小数への変換エラーです",
        "internal-error": "内部エラーです",
        "append-immutable": "変更できません",
        "array-format": "配列フォーマットエラーです",
        "assertion-failed": "テストを失敗"
      };
      YuiError = class extends Error {
        constructor(messages, errorNode = null, BK = false) {
          const normalized = normalizeMessages(messages);
          super(normalized.join(" "));
          this.name = "YuiError";
          this.messages = normalized;
          this.errorNode = errorNode != null && typeof errorNode === "object" && "pos" in errorNode ? errorNode : null;
          this.BK = BK;
        }
        /** メッセージを末尾に追加する。配列を再凍結。 */
        addMessage(message) {
          this.messages = Object.freeze([...this.messages, message]);
        }
        /** エラー箇所の行番号 (1始まり)。AST node がない場合は 0。 */
        get lineno() {
          if (this.errorNode) {
            const [line] = this.errorNode.extract();
            return line;
          }
          return 0;
        }
        /** エラー箇所の列番号 (1始まり)。AST node がない場合は 0。 */
        get offset() {
          if (this.errorNode) {
            const [, offset] = this.errorNode.extract();
            return offset;
          }
          return 0;
        }
        /** エラー箇所のコードスニペット。 */
        get text() {
          if (this.errorNode) {
            const [, , snippet] = this.errorNode.extract();
            return snippet;
          }
          return "";
        }
        /**
         * 構文エラーとして整形したメッセージを返す。
         * ランタイムエラーは YuiRuntime.formatError() を使うこと。
         */
        formattedMessage(prefix = " ", marker = "^", lineoffset = 0) {
          let message = formatMessages(this.messages);
          if (this.errorNode) {
            const [line, col, rawSnippet] = this.errorNode.extract();
            const span = this.errorNode.endPos != null ? Math.max(this.errorNode.endPos - this.errorNode.pos, 3) : 3;
            const pointerLen = Math.min(span, 16);
            const pointer = marker.repeat(pointerLen);
            const snippet = rawSnippet.split("\n")[0];
            const indent = " ".repeat(col - 1);
            message = `${message} line ${line + lineoffset}, column ${col}:
${prefix}${snippet}
${prefix}${indent}${pointer}`;
          }
          return `[構文エラー/SyntaxError] ${message}`;
        }
      };
    }
  });

  // src/yuitypes.js
  function _array_equal(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length !== b.length) return false;
      return a.every((el, i) => _array_equal(el, b[i]));
    }
    if (Array.isArray(a) && typeof b === "string") {
      try {
        const s = a.map((c) => String.fromCodePoint(c)).join("");
        return s === b;
      } catch (_e) {
        return false;
      }
    }
    if (typeof a === "string" && Array.isArray(b)) {
      return _array_equal(b, a);
    }
    if (a && typeof a === "object" && b && typeof b === "object") {
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
  function _typing(value) {
    for (const ty of TYPES) {
      if (ty.match(value)) return ty;
    }
    throw new Error(`unknown type for value: ${value}`);
  }
  function _round6(n) {
    return Math.round(n * 1e6) / 1e6;
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
  var TY_NULL, TY_BOOLEAN, TY_INT, TY_FLOAT, TY_NUMBER, TY_ARRAY, TY_OBJECT, TY_STRING, YuiType, YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType, YuiNumberType, YuiStringType, YuiArrayType, YuiObjectType, NullType, BoolType, IntType, FloatType, NumberType, StringType, ArrayType, ObjectType, TYPES, YuiValue, types, Operator, Equals, NotEquals, LessThan, GreaterThan, LessThanEquals, GreaterThanEquals, In, NotIn, Add, Sub, Mul, Div, Mod, OPERATORS;
  var init_yuitypes = __esm({
    "src/yuitypes.js"() {
      init_yuierror();
      TY_NULL = "🚫";
      TY_BOOLEAN = "🎭";
      TY_INT = "🔢";
      TY_FLOAT = "📊";
      TY_NUMBER = "🔢";
      TY_ARRAY = "🍡";
      TY_OBJECT = "🗂️";
      TY_STRING = "🔤";
      YuiType = class {
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
          throw new Error("abstract YuiType.match");
        }
        match_or_raise(value, node = null) {
          if (!this.match(value)) {
            throw new YuiError(
              ["type-error", `✅<${this.emoji}${this.name}>`, `❌${value}`],
              node
            );
          }
        }
        to_arrayview(_nativeValue) {
          throw new Error("abstract YuiType.to_arrayview");
        }
        to_sign(_nativeValue) {
          return 1;
        }
        to_native(_elements, _sign = 1, _node2 = null) {
          throw new Error("abstract YuiType.to_native");
        }
        stringify(_nativeValue, _indentPrefix = "", _width = 80) {
          throw new Error("abstract YuiType.stringify");
        }
        equals(left, right) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          return l === r;
        }
        less_than(left, right, op = "<", binaryNode = null) {
          throw new YuiError(["imcomparable", `❌${left} ${op} ${right}`], binaryNode);
        }
      };
      YuiNullType = class _YuiNullType extends YuiType {
        constructor() {
          super("null", TY_NULL);
        }
        is_immutable() {
          return true;
        }
        match(value) {
          return value === null || value === void 0 || value instanceof YuiValue && value.type instanceof _YuiNullType;
        }
        to_arrayview(_n) {
          return [];
        }
        to_native(_elements, _sign = 1, _node2 = null) {
          return null;
        }
        stringify(_nativeValue, _indentPrefix = "", _width = 80) {
          return "null";
        }
      };
      YuiBooleanType = class _YuiBooleanType extends YuiType {
        constructor() {
          super("boolean", TY_BOOLEAN);
        }
        is_immutable() {
          return true;
        }
        match(value) {
          return typeof value === "boolean" || value instanceof YuiValue && value.type instanceof _YuiBooleanType;
        }
        to_arrayview(n) {
          return n ? [1] : [0];
        }
        to_native(elements, _sign = 1, _node2 = null) {
          return elements && elements.length > 0 ? Boolean(elements[0]) : false;
        }
        stringify(nativeValue, _indentPrefix = "", _width = 80) {
          return nativeValue ? "true" : "false";
        }
        equals(left, right, _binaryNode = null) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "boolean") {
            return l === r;
          }
          return false;
        }
        less_than(left, right, op = "<", binaryNode = null) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "boolean") {
            return Number(l) < Number(r);
          }
          return super.less_than(left, right, op, binaryNode);
        }
      };
      YuiIntType = class _YuiIntType extends YuiType {
        constructor() {
          super("int", TY_INT);
        }
        match(value) {
          return typeof value === "number" && Number.isInteger(value) || value instanceof YuiValue && value.type instanceof _YuiIntType;
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
            if (typeof bit === "boolean" || bit !== 0 && bit !== 1) {
              const array = ArrayType.stringify(bits, null, 80, ",");
              throw new YuiError(
                ["array-value-error", `❌${types.format_json(bit)}`, "✅0/1", `🔍${array}`],
                node
              );
            }
            n += bit * Math.pow(2, i);
          }
          return sign * n;
        }
        stringify(nativeValue, _indentPrefix = "", _width = 80) {
          return `${nativeValue}`;
        }
        stringify_arrayview(arrayview, sign) {
          return `${sign < 0 ? "-" : ""}[${arrayview.join(",")}]`;
        }
        equals(left, right) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "boolean") return false;
          if (typeof r === "number") {
            return _round6(l) === _round6(r);
          }
          return l === r;
        }
        less_than(left, right, op = "<", binaryNode = null) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "number") {
            return _round6(l) < _round6(r);
          }
          return super.less_than(left, right, op, binaryNode);
        }
      };
      YuiFloatType = class _YuiFloatType extends YuiType {
        constructor() {
          super("float", TY_FLOAT);
        }
        match(value) {
          return typeof value === "number" && !Number.isInteger(value) || value instanceof YuiValue && value.type instanceof _YuiFloatType;
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
          const s = Math.abs(x).toFixed(6).replace(".", "");
          const digits = [];
          for (const ch of s) {
            digits.push(parseInt(ch, 10));
          }
          return digits.reverse();
        }
        /** LSB ファーストの一桁整数配列を浮動小数点数に変換 */
        to_native(digits, sign = 1, node = null) {
          for (const d of digits) {
            if (!(typeof d === "number" && Number.isInteger(d) && d >= 0 && d <= 9)) {
              const array = ArrayType.stringify(digits, null, 80, ",");
              throw new YuiError(
                ["array-value-error", `❌${types.format_json(d)}`, "✅0-9", `🔍${array}`],
                node
              );
            }
          }
          const msb = [...digits].reverse();
          const s = msb.join("");
          let value;
          if (s.length <= 6) {
            value = parseFloat("0." + s.padStart(6, "0"));
          } else {
            value = parseFloat(s.slice(0, -6) + "." + s.slice(-6));
          }
          return sign * value;
        }
        stringify(nativeValue, _indentPrefix = "", _width = 80) {
          return nativeValue.toFixed(6);
        }
        equals(left, right) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "boolean") return false;
          if (typeof r === "number") {
            return _round6(l) === _round6(r);
          }
          return false;
        }
        less_than(left, right, op = "<", binaryNode = null) {
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (typeof r === "number") {
            return l < r;
          }
          return super.less_than(left, right, op, binaryNode);
        }
      };
      YuiNumberType = class extends YuiType {
        constructor() {
          super("number", TY_NUMBER);
        }
        match(value) {
          return IntType.match(value) || FloatType.match(value);
        }
        to_arrayview(_v) {
          throw new Error("NumberType is a union type; use IntType or FloatType");
        }
        to_native(_elements, _sign = 1, _node2 = null) {
          throw new Error("NumberType is a union type; use IntType or FloatType");
        }
        stringify(_v, _indentPrefix = "", _width = 80) {
          throw new Error("NumberType is a union type; use IntType or FloatType");
        }
      };
      YuiStringType = class _YuiStringType extends YuiType {
        constructor() {
          super("string", TY_STRING);
        }
        match(value) {
          return typeof value === "string" || value instanceof YuiValue && value.type instanceof _YuiStringType;
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
            if (!(typeof d === "number" && Number.isInteger(d) && d >= 0 && d <= 1114111)) {
              const array = ArrayType.stringify(elements, null, 80, ",");
              throw new YuiError(
                ["array-value-error", `❌${types.format_json(d)}`, "✅<文字コード>", `🔍${array}`],
                node
              );
            }
            parts.push(String.fromCodePoint(d));
          }
          return parts.join("");
        }
        stringify(nativeValue, _indentPrefix = "", _width = 80) {
          return types.format_json(nativeValue);
        }
        equals(left, right) {
          const l = types.unbox(left);
          if (types.is_string(right)) {
            return l === types.unbox(right);
          }
          return false;
        }
        less_than(left, right, _op = "<", _binaryNode = null) {
          const l = types.unbox(left);
          if (types.is_string(right)) {
            const r = types.unbox(right);
            return l < r;
          }
          return false;
        }
      };
      YuiArrayType = class _YuiArrayType extends YuiType {
        constructor() {
          super("array", TY_ARRAY);
        }
        is_array_unboxed() {
          return false;
        }
        match(value) {
          return Array.isArray(value) || value instanceof YuiValue && value.type instanceof _YuiArrayType;
        }
        to_arrayview(arrayValue) {
          return arrayValue.map((v) => types.array_unbox(v));
        }
        to_native(elements, _sign = 1, _node2 = null) {
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
        stringify(elements, indentPrefix = "", width = 80, comma = ", ") {
          const content = `[${elements.map((el) => types.format_json(el)).join(comma)}]`;
          if (indentPrefix === null || indentPrefix.length + content.length <= width) {
            return content;
          }
          const innerIndent = indentPrefix + "  ";
          const LF = "\n";
          const formatted = elements.map(
            (el) => el instanceof YuiValue ? el.stringify(innerIndent, false, width) : types.format_json(el)
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
      };
      YuiObjectType = class _YuiObjectType extends YuiType {
        constructor() {
          super("object", TY_OBJECT);
        }
        is_array_unboxed() {
          return false;
        }
        match(value) {
          return value !== null && typeof value === "object" && !Array.isArray(value) && !(value instanceof YuiValue) || value instanceof YuiValue && value.type instanceof _YuiObjectType;
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
                ["array-value-error", `❌${kv}`, "✅[key, value]", `🔍${elements}`],
                node
              );
            }
            const pair = kv.native;
            if (!Array.isArray(pair) || pair.length !== 2) {
              throw new YuiError(
                ["array-value-error", `❌${pair}`, "✅[key, value]", `🔍${elements}`],
                node
              );
            }
            const key = pair[0];
            if (typeof key !== "string") {
              throw new YuiError(
                ["array-value-error", `❌${key}`, "✅<string>", `🔍${pair}`],
                node
              );
            }
            obj[key] = pair[1];
          }
          return obj;
        }
        stringify(nativeValue, indentPrefix = "", width = 80) {
          const entries = Object.entries(nativeValue);
          const content = `{${entries.map(([k, v]) => `"${k}": ${types.format_json(v)}`).join(", ")}}`;
          if (indentPrefix === null || indentPrefix.length + content.length <= width) {
            return content;
          }
          const innerIndent = indentPrefix + "  ";
          const LF = "\n";
          const formatted = entries.map(([key, value]) => {
            const valStr = value instanceof YuiValue ? value.stringify(innerIndent, false, width) : types.format_json(value);
            return `"${key}": ${valStr}`;
          });
          return `{${LF}${innerIndent}${formatted.join(`,${LF}${innerIndent}`)}${LF}${indentPrefix}}`;
        }
        equals(left, right, _binaryNode = null) {
          const ln = types.unbox(left);
          const rn = types.unbox(right);
          if (rn === null || typeof rn !== "object" || Array.isArray(rn)) {
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
      };
      NullType = new YuiNullType();
      BoolType = new YuiBooleanType();
      IntType = new YuiIntType();
      FloatType = new YuiFloatType();
      NumberType = new YuiNumberType();
      StringType = new YuiStringType();
      ArrayType = new YuiArrayType();
      ObjectType = new YuiObjectType();
      TYPES = [
        NullType,
        BoolType,
        IntType,
        FloatType,
        NumberType,
        StringType,
        ArrayType,
        ObjectType
      ];
      YuiValue = class _YuiValue {
        constructor(nativeValue, type = null) {
          this._nativeValue = nativeValue instanceof _YuiValue ? nativeValue.native : nativeValue;
          if (this._nativeValue === void 0) this._nativeValue = null;
          this.type = type == null ? _typing(nativeValue) : type;
          this._elements = void 0;
          this._sign = void 0;
          this.inner_view = false;
        }
        get native() {
          if (this._nativeValue === void 0) {
            this._nativeValue = this.type.to_native(this._elements, this._sign);
          }
          return this._nativeValue;
        }
        /** arrayview (LSB ファースト配列) を遅延生成 */
        get array() {
          if (this._elements === void 0) {
            this._elements = this.type.to_arrayview(this._nativeValue);
            this._sign = this.type.to_sign(this._nativeValue);
            this._nativeValue = void 0;
            this.inner_view = true;
          }
          return this._elements;
        }
        get_item(index, getindexNode = null) {
          if (types.is_string(index) && types.is_object(this)) {
            const key = types.unbox(index);
            const obj = types.unbox(this);
            if (Object.prototype.hasOwnProperty.call(obj, key)) {
              return types.box(obj[key]);
            }
            return _YuiValue.NullValue;
          }
          IntType.match_or_raise(index, getindexNode);
          const idx = types.unbox(index);
          const elements = this.array;
          this.inner_view = true;
          if (idx < 0) {
            throw new YuiError(["index-error", "✅>=0", `❌${idx}`], getindexNode);
          }
          if (this.type instanceof YuiIntType && idx >= elements.length) {
            return types.box(0);
          }
          if (idx >= elements.length) {
            throw new YuiError(
              ["index-error", `✅<${elements.length}`, `❌${idx}`, `🔍${elements}`],
              getindexNode
            );
          }
          return types.box(elements[idx]);
        }
        set_item(index, value, getindexNode = null) {
          value = types.array_unbox(value);
          if (this.type.is_immutable()) {
            throw new YuiError(["immutable-set", `❌${this.type}`], null);
          }
          if (types.is_string(index) && types.is_object(this)) {
            const key = types.unbox(index);
            const obj = this.native;
            obj[key] = value;
            this._elements = void 0;
            return;
          }
          IntType.match_or_raise(index, getindexNode);
          const idx = types.unbox(index);
          if (idx < 0) {
            throw new YuiError(["index-error", "✅>=0", `❌${idx}`], getindexNode);
          }
          const elements = this.array;
          if (idx >= elements.length) {
            throw new YuiError(
              ["index-error", `✅<${elements.length}`, `❌${idx}`, `🔍${elements}`],
              getindexNode
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
          this._nativeValue = void 0;
        }
        append(value, appendNode = null) {
          value = types.array_unbox(value);
          if (this.type.is_immutable()) {
            throw new YuiError(["immutable-append", `❌${this.type}`], appendNode);
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
          this._nativeValue = void 0;
        }
        toString() {
          return this.stringify(null);
        }
        stringify(indentPrefix = "", innerView = false, width = 80) {
          const nativeView = this.type.stringify(this.native, indentPrefix, width);
          if (innerView === true && this.inner_view && this.type.is_array_unboxed()) {
            const elements = this.array;
            const arrayView = ArrayType.stringify(elements, null, width, ",");
            return `${nativeView.padEnd(12)}   🔬${arrayView}`;
          }
          return nativeView;
        }
        equals(other) {
          return this.type.equals(this, other);
        }
        less_than(other, op = "<", binaryNode = null) {
          return this.type.less_than(this, other, op, binaryNode);
        }
      };
      YuiValue.NullValue = new YuiValue(null, NullType);
      YuiValue.TrueValue = new YuiValue(true, BoolType);
      YuiValue.FalseValue = new YuiValue(false, BoolType);
      types = {
        box(value) {
          if (value instanceof YuiValue) return value;
          if (value === null || value === void 0) return YuiValue.NullValue;
          if (typeof value === "boolean") {
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
          if (Array.isArray(value) || value !== null && typeof value === "object") {
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
          if (value !== null && typeof value === "object") {
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
          if (value === null || value === void 0) return "null";
          if (typeof value === "boolean") return value ? "true" : "false";
          if (typeof value === "string") {
            const v = value.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
            return `"${v}"`;
          }
          if (typeof value === "number") {
            if (Number.isInteger(value)) return String(value);
            return value.toFixed(6);
          }
          if (value instanceof YuiValue) {
            return value.stringify(null);
          }
          if (Array.isArray(value)) {
            return "[" + value.map((v) => types.format_json(v)).join(", ") + "]";
          }
          if (typeof value === "object") {
            const parts = Object.entries(value).map(
              ([k, v]) => `"${k}": ${types.format_json(v)}`
            );
            return "{" + parts.join(", ") + "}";
          }
          return String(value);
        },
        /** ネイティブ値の配列ビュー文字列表現 (コード生成用) */
        arrayview_s(nativeValue) {
          let elements, sign;
          if (typeof nativeValue === "boolean") {
            elements = BoolType.to_arrayview(nativeValue);
            sign = 1;
          } else if (typeof nativeValue === "number" && Number.isInteger(nativeValue)) {
            elements = IntType.to_arrayview(nativeValue);
            sign = IntType.to_sign(nativeValue);
          } else if (typeof nativeValue === "number") {
            elements = FloatType.to_arrayview(nativeValue);
            sign = FloatType.to_sign(nativeValue);
          } else {
            return String(nativeValue);
          }
          return `${sign < 0 ? "-" : ""}[${elements.join(",")}]`;
        },
        compare(left, right) {
          if (types.is_number(left) && types.is_number(right)) {
            const l2 = _round6(types.unbox(left));
            const r2 = _round6(types.unbox(right));
            return _compare(l2, r2);
          }
          if (types.is_string(left) && types.is_string(right)) {
            const l2 = types.unbox(left);
            const r2 = types.unbox(right);
            return _compare(l2, r2);
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
        }
      };
      Operator = class {
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
          throw new Error("abstract Operator.evaluate");
        }
      };
      Equals = class extends Operator {
        constructor(symbol = "==") {
          super(symbol, 3);
        }
        evaluate(left, right, _binaryNode = null) {
          return left.equals(right);
        }
      };
      NotEquals = class extends Operator {
        constructor(symbol = "!=") {
          super(symbol, 3);
        }
        evaluate(left, right, _binaryNode = null) {
          return !left.equals(right);
        }
      };
      LessThan = class extends Operator {
        constructor(symbol = "<") {
          super(symbol, 3);
        }
        evaluate(left, right, binaryNode = null) {
          return !left.equals(right) && left.less_than(right, this.symbol, binaryNode);
        }
      };
      GreaterThan = class extends Operator {
        constructor(symbol = ">") {
          super(symbol, 3);
        }
        evaluate(left, right, binaryNode = null) {
          return !left.equals(right) && !left.less_than(right, this.symbol, binaryNode);
        }
      };
      LessThanEquals = class extends Operator {
        constructor(symbol = "<=") {
          super(symbol, 3);
        }
        evaluate(left, right, binaryNode = null) {
          return left.equals(right) || left.less_than(right, this.symbol, binaryNode);
        }
      };
      GreaterThanEquals = class extends Operator {
        constructor(symbol = ">=") {
          super(symbol, 3);
        }
        evaluate(left, right, binaryNode = null) {
          return left.equals(right) || !left.less_than(right, this.symbol, binaryNode);
        }
      };
      In = class extends Operator {
        constructor(symbol = "in") {
          super(symbol, 3);
        }
        evaluate(left, right, _binaryNode = null) {
          const arr = right.array;
          for (const el of arr) {
            if (left.equals(el)) return true;
          }
          return false;
        }
      };
      NotIn = class extends Operator {
        constructor(symbol = "notin") {
          super(symbol, 3);
        }
        evaluate(left, right, _binaryNode = null) {
          const arr = right.array;
          for (const el of arr) {
            if (left.equals(el)) return false;
          }
          return true;
        }
      };
      Add = class extends Operator {
        constructor(symbol = "+") {
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
      };
      Sub = class extends Operator {
        constructor(symbol = "-") {
          super(symbol, 2);
        }
        evaluate(left, right, binaryNode = null) {
          NumberType.match_or_raise(left, binaryNode);
          NumberType.match_or_raise(right, binaryNode);
          return types.unbox(left) - types.unbox(right);
        }
      };
      Mul = class extends Operator {
        constructor(symbol = "*") {
          super(symbol, 1);
        }
        evaluate(left, right, binaryNode = null) {
          NumberType.match_or_raise(left, binaryNode);
          NumberType.match_or_raise(right, binaryNode);
          return types.unbox(left) * types.unbox(right);
        }
      };
      Div = class extends Operator {
        constructor(symbol = "/") {
          super(symbol, 1);
        }
        evaluate(left, right, binaryNode = null) {
          NumberType.match_or_raise(left, binaryNode);
          NumberType.match_or_raise(right, binaryNode);
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (r === 0) {
            throw new YuiError(["division-by-zero", `❌${r}`], binaryNode);
          }
          if (types.is_float(left) || types.is_float(right)) {
            return l / r;
          }
          return Math.floor(l / r);
        }
      };
      Mod = class extends Operator {
        constructor(symbol = "%") {
          super(symbol, 1);
        }
        evaluate(left, right, binaryNode = null) {
          NumberType.match_or_raise(left, binaryNode);
          NumberType.match_or_raise(right, binaryNode);
          const l = types.unbox(left);
          const r = types.unbox(right);
          if (r === 0) {
            throw new YuiError(["division-by-zero", `❌${r}`], binaryNode);
          }
          return (l % r + r) % r;
        }
      };
      OPERATORS = {
        "==": new Equals(),
        "!=": new NotEquals(),
        "<": new LessThan(),
        ">": new GreaterThan(),
        "<=": new LessThanEquals(),
        ">=": new GreaterThanEquals(),
        "in": new In(),
        "notin": new NotIn(),
        "+": new Add(),
        "-": new Sub(),
        "*": new Mul(),
        "/": new Div(),
        "%": new Mod()
      };
    }
  });

  // src/yuiast.js
  function _isPlainObject(x) {
    if (x === null || typeof x !== "object") return false;
    if (Array.isArray(x)) return false;
    const proto = Object.getPrototypeOf(x);
    return proto === Object.prototype || proto === null;
  }
  function _node(node) {
    if (node === null || node === void 0) {
      return new ConstNode(null);
    }
    if (typeof node === "boolean") {
      return new ConstNode(node);
    }
    if (typeof node === "number") {
      return new NumberNode(node);
    }
    if (typeof node === "string") {
      if (node.startsWith("📦")) {
        return new NameNode(node.slice("📦".length).trim());
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
  var ASTNode, ExpressionNode, StatementNode, ConstNode, NumberNode, ArrayLenNode, MinusNode, StringNode, ArrayNode, ObjectNode, NameNode, GetIndexNode, BinaryNode, FuncAppNode, AssignmentNode, IncrementNode, DecrementNode, AppendNode, BlockNode, IfNode, BreakNode, PassNode, RepeatNode, ImportNode, ReturnNode, FuncDefNode, PrintExpressionNode, AssertNode, CatchNode, _AST_CLASSES;
  var init_yuiast = __esm({
    "src/yuiast.js"() {
      init_yuitypes();
      ASTNode = class {
        constructor() {
          this.filename = "main.yui";
          this.source = "";
          this.pos = 0;
          this.end_pos = -1;
          this.comment = null;
        }
        setpos(source, pos, end_pos = -1, filename = "main.yui") {
          this.source = source;
          this.pos = pos;
          this.end_pos = end_pos;
          this.filename = filename;
          this.comment = null;
          return this;
        }
        /** ノードに対応するソースコードのスニペットを返す */
        toString() {
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
          const methodName = "visit" + name;
          const method = visitor[methodName];
          if (typeof method !== "function") {
            throw new TypeError(
              `visitor is missing method ${methodName} for ${name}`
            );
          }
          return method.call(visitor, this);
        }
        // パース後フック (サブクラスでオーバーライド可)
        parsed(_orderPolicy = "") {
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
          const src = this.source;
          const len = src.length;
          for (let i = 0; i < len; i++) {
            if (i === this.pos) break;
            if (src.charCodeAt(i) === 10) {
              linenum += 1;
              col = 1;
              start = i + 1;
            } else {
              col += 1;
            }
          }
          let endPos = src.indexOf("\n", start);
          if (endPos === -1) endPos = src.length;
          return [linenum, col, src.slice(start, endPos)];
        }
      };
      ExpressionNode = class extends ASTNode {
      };
      StatementNode = class extends ASTNode {
      };
      ConstNode = class extends ExpressionNode {
        constructor(value = null) {
          super();
          this.native_value = value;
        }
      };
      NumberNode = class extends ExpressionNode {
        constructor(value) {
          super();
          this.native_value = value;
        }
      };
      ArrayLenNode = class extends ExpressionNode {
        constructor(element) {
          super();
          this.element = _node(element);
        }
      };
      MinusNode = class extends ExpressionNode {
        constructor(element) {
          super();
          this.element = _node(element);
        }
      };
      StringNode = class extends ExpressionNode {
        constructor(contents) {
          super();
          this.contents = contents;
        }
      };
      ArrayNode = class extends ExpressionNode {
        constructor(elements) {
          super();
          this.elements = elements.map((e) => _node(e));
        }
      };
      ObjectNode = class extends ExpressionNode {
        constructor(elements) {
          super();
          this.elements = elements.map((e) => _node(e));
        }
      };
      NameNode = class extends ExpressionNode {
        constructor(name) {
          super();
          this.name = name;
        }
        /** 変数の値を更新する (代入先としての動作) */
        update(value, visitor) {
          visitor.setenv(this.name, value);
        }
      };
      GetIndexNode = class extends ASTNode {
        constructor(collection, index, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
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
      };
      BinaryNode = class extends ASTNode {
        constructor(operator, left, right) {
          super();
          const op = OPERATORS[operator];
          if (op === void 0) {
            throw new Error(`BinaryNode: unknown operator ${operator}`);
          }
          this.operator = op;
          this.left_node = _node(left);
          this.right_node = _node(right);
          this.comparative = op.comparative;
        }
      };
      FuncAppNode = class extends ExpressionNode {
        constructor(name, args, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
            [name, args] = [args, name];
          }
          this.name_node = typeof name === "string" ? new NameNode(name) : _node(name);
          this.arguments = args.map((arg) => _node(arg));
          this.snippet = this.toString();
        }
      };
      AssignmentNode = class extends StatementNode {
        constructor(variable, expression, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
            [variable, expression] = [expression, variable];
          }
          this.variable = _node(variable);
          this.expression = _node(expression);
        }
      };
      IncrementNode = class extends StatementNode {
        constructor(variable) {
          super();
          this.variable = _node(variable);
        }
      };
      DecrementNode = class extends StatementNode {
        constructor(variable) {
          super();
          this.variable = _node(variable);
        }
      };
      AppendNode = class extends StatementNode {
        constructor(variable, expression, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
            [variable, expression] = [expression, variable];
          }
          this.variable = _node(variable);
          this.expression = _node(expression);
        }
      };
      BlockNode = class extends StatementNode {
        constructor(statements, topLevel = false) {
          super();
          if (statements instanceof StatementNode) {
            this.statements = [statements];
          } else {
            if (!Array.isArray(statements)) {
              throw new TypeError("BlockNode: statements must be a list or a StatementNode");
            }
            this.statements = statements;
          }
          this.top_level = topLevel;
        }
      };
      IfNode = class extends StatementNode {
        constructor(left, operator, right, thenBlock, elseBlock = null) {
          super();
          const op = OPERATORS[operator];
          if (op === void 0) {
            throw new Error(`IfNode: unknown operator ${operator}`);
          }
          this.left = _node(left);
          this.operator = op;
          this.right = _node(right);
          this.then_block = _node(thenBlock);
          this.else_block = elseBlock !== null && elseBlock !== void 0 ? _node(elseBlock) : new PassNode();
        }
      };
      BreakNode = class extends StatementNode {
      };
      PassNode = class extends StatementNode {
        constructor(comment = null) {
          super();
          this.comment = comment;
        }
      };
      RepeatNode = class extends StatementNode {
        constructor(countNode, blockNode, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
            [countNode, blockNode] = [blockNode, countNode];
          }
          this.count_node = _node(countNode);
          this.block_node = _node(blockNode);
        }
      };
      ImportNode = class extends StatementNode {
        constructor(moduleName = null) {
          super();
          this.module_name = typeof moduleName === "string" ? new NameNode(moduleName) : _node(moduleName);
        }
      };
      ReturnNode = class extends StatementNode {
        constructor(expression) {
          super();
          this.expression = _node(expression);
        }
      };
      FuncDefNode = class extends StatementNode {
        constructor(nameNode, parameters, body) {
          super();
          this.name_node = _node(nameNode);
          this.parameters = parameters.map((p) => _node(p));
          this.body = _node(body);
        }
      };
      PrintExpressionNode = class extends StatementNode {
        constructor(expression, inspection = false, grouping = false) {
          super();
          this.expression = _node(expression);
          this.inspection = inspection;
          this.grouping = grouping;
        }
      };
      AssertNode = class extends StatementNode {
        constructor(test, reference, orderPolicy = "") {
          super();
          if (orderPolicy === "reversed") {
            [test, reference] = [reference, test];
          }
          this.test = _node(test);
          this.reference = _node(reference);
        }
      };
      CatchNode = class extends ExpressionNode {
        constructor(expression) {
          super();
          this.expression = _node(expression);
        }
      };
      _AST_CLASSES = {
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
        CatchNode
      };
      for (const [name, cls] of Object.entries(_AST_CLASSES)) {
        Object.defineProperty(cls, "nodeName", {
          value: name,
          writable: false,
          enumerable: false,
          configurable: false
        });
      }
    }
  });

  // src/yuigrammars.js
  function getGrammar(name) {
    return GRAMMARS[name] ?? null;
  }
  var GRAMMARS, SYNTAX_NAMES;
  var init_yuigrammars = __esm({
    "src/yuigrammars.js"() {
      GRAMMARS = Object.freeze({
        "ast": {
          "syntax": "ASTNode",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "word-segmenter": " ",
          "line-comment-begin": "\\#",
          "comment-begin": "",
          "comment-end": "",
          "statement-separator": ",",
          "number-begin": "NumberNode\\(",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "number-end": "\\)",
          "name-begin": 'NameNode\\("',
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "name-end": '"\\)',
          "string-begin": 'StringNode\\("',
          "string-end": '"\\)',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "array-begin": "ArrayNode\\(\\[",
          "array-end": "\\]\\)",
          "array-separator": ",",
          "object-begin": "ObjectNode\\(\\[",
          "object-end": "\\]\\)",
          "object-separator": ",",
          "key-value-separator": ",",
          "grouping-begin!": "\\(",
          "grouping-end!": "\\)",
          "length-begin": "ArrayLenNode\\(",
          "length-end": "\\)",
          "minus-begin": "MinusNode\\(",
          "minus-end": "\\)",
          "array-indexer-begin": "GetIndexNode\\(",
          "array-indexer-suffix": ",",
          "array-indexer-end": "\\)",
          "funcapp-begin": "FuncApp\\(",
          "funcapp-args-begin": "",
          "funcapp-args-end": "\\)",
          "funcapp-separator": ",",
          "block-begin": "BlockNode\\(\\[",
          "block-end": "\\]\\)",
          "block-separator": ",",
          "assignment-begin": "AssignmentNode\\(",
          "assignment-infix": ",",
          "assignment-end": "\\)",
          "increment-begin": "IncrementNode\\(",
          "increment-end": "\\)",
          "decrement-begin": "DecrementNode\\(",
          "decrement-end": "\\)",
          "append-begin": "AppendNode\\(",
          "append-infix": ",",
          "append-end": "\\)",
          "print-begin": "PrintExpression\\(",
          "print-end": "\\)",
          "break": "BreakNode\\(\\)",
          "pass": "PassNode\\(\\)",
          "return-begin": "ReturnNode\\(",
          "return-end": "\\)",
          "repeat-begin": "RepeatNode\\(",
          "repeat-times": ",",
          "repeat-block": "",
          "repeat-end": "\\)",
          "if-begin": "IfNode\\(",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": ', "==",',
          "if-infix!=": ', "!=",',
          "if-infix<": ', "<",',
          "if-infix<=": ', "<=",',
          "if-infix>": ', ">",',
          "if-infix>=": ', ">=",',
          "if-infixin": ', "in",',
          "if-infixnotin": ', "notin",',
          "if-then": ",",
          "if-else": ",",
          "if-end": "\\)",
          "funcdef-begin": "FuncNode\\(",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": ", \\[",
          "funcdef-noarg": "\\[\\]",
          "funcdef-arg-separator": "\\,",
          "funcdef-args-end": "\\]",
          "funcdef-block": ",",
          "funcdef-end": "\\)",
          "assert-begin": "AssertNode\\(",
          "assert-infix": ",",
          "assert-end": "\\)",
          "import-begin": "ImportNode\\(",
          "import-end": "\\)"
        },
        "bridget": {
          "syntax": "Plain English",
          "function-language": "en",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "line-comment-begin": "#",
          "word-segmenter": " ",
          "comment-begin": "",
          "comment-end": "",
          "indent": "  ",
          "special-name-pattern": '[^\\s\\[\\]\\(\\)",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+',
          "special-name-funcname": "\\s(?:is|to)\\s+({name_pattern})\\s+of",
          "special-name-variable": "Remember\\s+that\\s+({name_pattern})\\s+is",
          "null": "[nN]othing|null",
          "boolean-true": "[yY]es|true",
          "boolean-false": "[nN]o|false",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "extra-name-begin": "`",
          "extra-name-end": "`",
          "string-begin": '"',
          "string-end": '"',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "binary-infix+": "\\+",
          "binary-infix-": "-",
          "binary-infix*": "\\*",
          "binary-infix/": "/",
          "binary-infix%": "%",
          "binary-infix==": "==",
          "binary-infix!=": "!=",
          "binary-infix<=": "<=",
          "binary-infix>=": ">=",
          "binary-infix<": "<",
          "binary-infix>": ">",
          "unary-minus": "-",
          "array-indexer-begin": "item",
          "array-indexer-infix": "in",
          "array-indexer-suffix": "",
          "array-indexer-end": "",
          "array-indexer-order": "reversed",
          "property-length": "'s\\s+length",
          "funcapp-args-begin": "of",
          "funcapp-args-end": "",
          "funcapp-separator": "and",
          "funcapp-noarg": ", do it",
          "import-standard": "Use the standard library",
          "import-begin": "Use",
          "import-end": "",
          "block-begin": ":",
          "block-end": "",
          "assignment-begin": "Remember\\s+that",
          "assignment-infix": "is",
          "assignment-end": "",
          "increment-begin": "Increase",
          "increment-end": "(by\\s+1)?",
          "decrement-begin": "Decrease",
          "decrement-end": "(by\\s+1)?",
          "append-begin": "Add",
          "append-infix": "to",
          "append-end": "",
          "append-order": "reverse",
          "!break": "break",
          "break": "Leave the loop",
          "pass": "Do nothing",
          "print-begin": "Now,",
          "print-end": "",
          "!return-begin": "return",
          "return-begin": "The answer is",
          "return-end": "",
          "return-none": "Stop here",
          "repeat-begin": "Do this",
          "repeat-times": "times",
          "repeat-block": "",
          "repeat-end": "End do",
          "!if-begin": "if",
          "if-begin": "When",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": "is\\s",
          "if-infix!=": "is not\\s",
          "if-infix<": "is less than",
          "if-infix<=": "is at least",
          "if-infix>": "is more than",
          "if-infix>=": "is at most",
          "if-infixin": "is in\\s",
          "if-infixnotin": "is not in",
          "if-then": ",\\s+then",
          "if-else": "But,\\s+if not",
          "if-end": "End when",
          "funcdef-begin": "This is how to",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "of",
          "funcdef-arg-separator": "and",
          "funcdef-args-end": "",
          "funcdef-noarg": "[^o][^f]",
          "funcdef-block": "",
          "funcdef-end": "Now you know"
        },
        "emoji": {
          "syntax": "🪢",
          "function-language": "emoji",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "word-segmenter": " ",
          "linefeed": "[\\n]",
          "line-comment-begin": "💭|🗨️|📌|⚠️",
          "indent": "  ",
          "comment-begin": "",
          "comment-end": "",
          "special-name-pattern": '[^\\s\\[\\]\\(\\)",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+',
          "special-name-variable": "({name_pattern})\\s+⬅️",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "null": "🫥|null",
          "boolean-true": "👍|true",
          "boolean-false": "👎|false",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "extra-name-begin": "",
          "extra-name-end": "",
          "string-begin": '"',
          "string-end": '"',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "array-begin": "\\[",
          "array-end": "\\]",
          "array-separator": ",",
          "object-begin": "\\{",
          "object-end": "\\}",
          "object-separator": ",",
          "key-value-separator": ":",
          "grouping-begin": "\\(",
          "grouping-end": "\\)",
          "unary-minus": "-",
          "unary-length": "📐",
          "binary-infix+": "➕|\\+|＋",
          "binary-infix-": "➖|\\-|－",
          "binary-infix*": "✖️|\\*|×",
          "binary-infix/": "➗|/|÷",
          "binary-infix%": "💔|%|％",
          "binary-infix==": "⚖️|==",
          "binary-infix!=": "🚫⚖️|!=",
          "binary-infix<=": "📈⚖️|<=",
          "binary-infix>=": "📉⚖️|>=",
          "binary-infix<": "📈|<",
          "binary-infix>": "📉|>",
          "binary-infixin": "📥|∈",
          "binary-infixnotin": "🚫📥|∉",
          "array-indexer-suffix": "\\[",
          "array-indexer-end": "\\]",
          "property-accessor": "",
          "property-type": "",
          "not-property-name": "",
          "funcapp-args-begin": "\\(",
          "funcapp-args-end": "\\)",
          "funcapp-separator": ",",
          "block-begin": "👉",
          "block-end": "🔚",
          "assignment-begin": "",
          "assignment-infix": "⬅️",
          "assignment-end": "",
          "increment-begin": "",
          "increment-end": "⬆️",
          "decrement-begin": "",
          "decrement-end": "⬇️",
          "append-begin": "",
          "append-infix": "🧲",
          "append-end": "",
          "print-begin": "",
          "print-end": "",
          "break": "🚀",
          "pass": "💤",
          "return-begin": "✅|💡",
          "return-end": "",
          "repeat-begin": "🌀",
          "repeat-times": "",
          "repeat-block": "",
          "repeat-end": "",
          "if-begin": "❓|🤔",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": "⚖️|==|＝",
          "if-infix!=": "🚫⚖️|!=|≠",
          "if-infix<": "📈|<",
          "if-infix<=": "📈⚖️|<=|≦",
          "if-infix>": "📉|>",
          "if-infix>=": "📉⚖️|>=|≧",
          "if-infixin": "📥|∈",
          "if-infixnotin": "🚫📥|∉",
          "if-then": "",
          "else-if": "❗❓",
          "if-else": "❗|🙅",
          "if-end": "",
          "funcdef-begin": "🧩",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "\\(",
          "funcdef-arg-separator": "\\,",
          "funcdef-args-end": "\\)",
          "funcdef-noarg": "",
          "funcdef-block": "",
          "funcdef-end": "",
          "import-standard": "🗝️\\s+📚",
          "import-begin": "🗝️",
          "import-end": ""
        },
        "empty": {
          "syntax": "empty"
        },
        "jslike": {
          "syntax": "javascript-like",
          "function-language": "en",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "word-segmenter": " ",
          "line-comment-begin": "//",
          "comment-begin": "/\\*",
          "comment-end": "\\*/",
          "keywords": "function|return|if|else|for|in|not|and|or|break|assert",
          "statement-separator": ";",
          "null": "null",
          "boolean-true": "true",
          "boolean-false": "false",
          "!string-begin": "'|`",
          "grouping-begin": "\\(",
          "grouping-end": "\\)",
          "binary-infix+": "\\+",
          "binary-infix-": "\\-",
          "binary-infix*": "\\*",
          "binary-infix/": "\\/",
          "binary-infix%": "\\%",
          "binary-infix==": "==",
          "binary-infix!=": "!=",
          "binary-infix<=": "<=",
          "binary-infix>=": ">=",
          "binary-infix<": "<",
          "binary-infix>": ">",
          "unary-minus": "\\-",
          "array-indexer-suffix": "\\[",
          "array-indexer-end": "\\]",
          "property-length": "\\.length",
          "not-property-name": "push",
          "funcapp-args-begin": "\\(",
          "funcapp-args-end": "\\)",
          "funcapp-separator": ",",
          "block-begin-prefix": " ",
          "block-begin": "\\{",
          "block-end": "\\}",
          "assignment-begin": "",
          "assignment-infix": "\\=",
          "assignment-end": "",
          "increment-begin": "",
          "increment-end": "\\+\\+|\\+\\=\\s*1",
          "decrement-begin": "",
          "decrement-end": "\\-\\-|\\-\\=\\s*1",
          "append-begin": "",
          "append-infix": ".push\\s*\\(",
          "append-end": "\\)",
          "import-begin": "require\\s*\\(",
          "import-end": "\\)",
          "import-standard": 'require\\s*\\("stdlib"\\)',
          "print-begin": "",
          "print-end": "",
          "break": "break",
          "pass": "",
          "return-begin": "return\\s",
          "return-end": "",
          "return-noarg": "return",
          "repeat-begin": "while\\s*\\(\\s+times\\s*\\(",
          "repeat-times": "\\)\\s*\\)",
          "repeat-block": "",
          "repeat-end": "",
          "if-begin": "if\\s",
          "if-condition-begin": "\\(",
          "if-condition-end": "\\)",
          "if-prefix": "",
          "if-infix==": "==",
          "if-infix!=": "!=",
          "if-infix<": "<",
          "if-infix<=": "<=",
          "if-infix>": ">",
          "if-infix>=": ">=",
          "if-infixin": "in",
          "if-then": "",
          "if-else": "else\\s*",
          "if-end": "",
          "funcdef-begin": "function\\s",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "\\(",
          "funcdef-noarg": "",
          "funcdef-arg-separator": ",",
          "funcdef-args-end": "\\)",
          "funcdef-block": "",
          "funcdef-end": ""
        },
        "nannan": {
          "syntax": "なんなん？",
          "function-language": "ja",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "line-comment-begin": "⚠️",
          "comment-begin": "",
          "comment-end": "",
          "indent": "  ",
          "keywords": "def|return|if|else|elif|for|in|not|and|or|break|pass|assert|import|True|False|None",
          "null": "「しらんがな」|null",
          "boolean-true": "「そやな」|true",
          "boolean-false": "「ちゃうな」|false",
          "grouping-begin!": "\\(",
          "grouping-end!": "\\)",
          "length-begin": "\\|",
          "length-end": "\\|",
          "binary-infix+": "\\+|＋",
          "binary-infix-": "-|ー",
          "binary-infix*": "\\*|×",
          "binary-infix/": "/|÷",
          "binary-infix%": "%|％",
          "binary-infix==": "==|＝＝",
          "binary-infix!=": "!=|≠",
          "binary-infix<=": "<=|≦",
          "binary-infix>=": ">=|≧",
          "binary-infix<": "<|＜",
          "binary-infix>": ">|＞",
          "binary-infixin": "∈",
          "binary-infixnotin": "∉",
          "unary-minus": "-",
          "array-indexer-suffix": "\\[",
          "array-indexer-end": "\\]",
          "property-length": "の大きさ",
          "funcapp-args-begin": "\\(",
          "funcapp-args-end": "\\)",
          "funcapp-separator": ",",
          "import-standard": "標準のやつ使う",
          "import-begin": "",
          "import-end": "を使う",
          "block-begin": "？|❓",
          "block-end": "",
          "block-line": "",
          "assignment-begin": "",
          "assignment-infix": "=",
          "assignment-end": "",
          "increment-begin": "",
          "increment-infix": "",
          "increment-end": "上げとく",
          "increment-lookahead": "上げとく",
          "decrement-begin": "",
          "decrement-infix": "",
          "decrement-end": "下げとく",
          "decrement-lookahead": "下げとく",
          "append-begin": "",
          "append-infix": "に",
          "append-end": "を?入れとく",
          "print-begin": "",
          "print-end": "",
          "break": "もうええって",
          "pass": "ほっとく",
          "return-begin": "この",
          "return-end": "だよ",
          "return-none": "わからん",
          "repeat-begin": "",
          "repeat-times": "回[、]?",
          "repeat-block": "まわそうか",
          "repeat-end": "",
          "if-lookahead": "ほんま",
          "if-begin": "",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix": "が",
          "if-suffix==": "と同じ",
          "if-suffix!=": "やない",
          "if-suffix<": "より小さい",
          "if-suffix<=": "以下",
          "if-suffix>": "より大きい",
          "if-suffix>=": "以上",
          "if-suffixin": "のいずれか",
          "if-suffixnotin": "のいずれでもない",
          "if-then": "ってほんま",
          "if-else": "違うん",
          "if-end": "",
          "funcdef-lookahead": "なんなん",
          "funcdef-begin": "",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "\\(",
          "funcdef-arg-separator": "[,、]",
          "funcdef-args-end": "\\)",
          "funcdef-block": "ってなんなん",
          "funcdef-end": "",
          "assert-begin": ">>>\\s+",
          "assert-infix": "[\\n]",
          "assert-end": ""
        },
        "pylike": {
          "syntax": "python-like",
          "function-language": "en",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "word-segmenter": " ",
          "line-comment-begin": "[#＃]",
          "comment-begin": "",
          "comment-end": "",
          "indent": "  ",
          "keywords": "def|return|if|else|elif|for|in|not|and|or|break|pass|assert|import|True|False|None",
          "null": "None",
          "boolean-true": "True",
          "boolean-false": "False",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "extra-name-begin": "",
          "extra-name-end": "",
          "string-begin": '"',
          "string-end": '"',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "array-begin": "\\[",
          "array-end": "\\]",
          "array-separator": ",",
          "object-begin": "\\{",
          "object-end": "\\}",
          "object-separator": ",",
          "key-value-separator": ":",
          "grouping-begin": "\\(",
          "grouping-end": "\\)",
          "length-begin": "len\\s*\\(",
          "length-end": "\\)",
          "binary-infix+": "\\+",
          "binary-infix-": "\\-",
          "binary-infix*": "\\*",
          "binary-infix/": "\\/",
          "binary-infix%": "\\%",
          "binary-infix==": "==",
          "binary-infix!=": "!=",
          "binary-infix<=": "<=",
          "binary-infix>=": ">=",
          "binary-infix<": "<",
          "binary-infix>": ">",
          "unary-minus": "\\-",
          "array-indexer-suffix": "\\[",
          "array-indexer-end": "\\]",
          "property-accessor": "\\.",
          "not-property-name": "append",
          "funcapp-args-begin": "\\(",
          "funcapp-args-end": "\\)",
          "funcapp-separator": ",",
          "block-begin": "\\:",
          "block-end": "",
          "block-else": "else|elif|except|finally",
          "block-line": "",
          "assignment-begin": "",
          "assignment-infix": "\\=",
          "assignment-end": "",
          "increment-begin": "",
          "increment-end": "\\+\\=\\s*1",
          "decrement-begin": "",
          "decrement-end": "\\-\\=\\s*1",
          "append-begin": "",
          "append-infix": ".append\\s*\\(",
          "append-end": "\\)",
          "print-begin": "",
          "print-end": "",
          "break": "break",
          "pass": "pass",
          "return-begin": "return\\s",
          "return-end": "",
          "repeat-begin": "while\\s+times\\s*\\(",
          "repeat-times": "\\)",
          "repeat-block": "",
          "repeat-end": "",
          "if-begin": "if\\s",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": "==",
          "if-infix!=": "!=",
          "if-infix<": "<",
          "if-infix<=": "<=",
          "if-infix>": ">",
          "if-infix>=": ">=",
          "if-infixin": "in\\s",
          "if-infixnotin": "not\\s+in\\s",
          "if-then": "",
          "if-else": "else\\s*",
          "if-end": "",
          "funcdef-begin": "def\\s",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "\\(",
          "funcdef-noarg": "",
          "funcdef-arg-separator": ",",
          "funcdef-args-end": "\\)",
          "funcdef-block": "",
          "funcdef-end": "",
          "import-standard": "import\\s+stdlib",
          "import-begin": "import\\s",
          "import-end": ""
        },
        "sexpr": {
          "syntax": "s-expression",
          "function-language": "en",
          "whitespace": "[ \\t\\r\\n　]",
          "whitespaces": "[ \\t\\r\\n　]+",
          "linefeed": "[\\n]",
          "line-comment-begin": ";",
          "comment-begin": "",
          "comment-end": "",
          "word-segmenter": " ",
          "indent": "",
          "keywords": "begin\\b|require\\b|inc\\b|dec\\b|append\\b|set\\b|aref\\b|if\\b|repeat\\b|break\\b|print\\b|assert\\b|define\\b|return\\b",
          "special-name-pattern": '[^\\s\\[\\]\\(\\)",]+',
          "special-name-funcname": "\\(({name_pattern})\\s",
          "special-name-variable": "\\(set\\!\\s+({name_pattern})\\s",
          "null": "nil|null",
          "boolean-true": "true",
          "boolean-false": "false",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_\\!\\?]*",
          "string-begin": '"',
          "string-end": '"',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "!string-begin": `'|f"`,
          "array-begin": "\\[",
          "array-end": "\\]",
          "array-separator": ",",
          "object-begin": "\\{",
          "object-end": "\\}",
          "object-separator": ",",
          "key-value-separator": ":",
          "grouping-begin": "",
          "grouping-end": "",
          "unary-minus": "",
          "minus-begin": "\\(-\\s+",
          "minus-end": "\\)",
          "length-begin": "\\(len\\s+",
          "length-end": "\\)",
          "binary-infix-prefix-begin": "\\(",
          "binary-infix-prefix+": "\\+",
          "binary-infix-prefix-": "-",
          "binary-infix-prefix*": "\\*",
          "binary-infix-prefix/": "/",
          "binary-infix-prefix%": "%",
          "binary-infix-prefix==": "==",
          "binary-infix-prefix!=": "!=",
          "binary-infix-prefix<=": "<=",
          "binary-infix-prefix>=": ">=",
          "binary-infix-prefix<": "<",
          "binary-infix-prefix>": ">",
          "binary-infix-prefix-end": "\\)",
          "array-indexer-begin": "\\(aref\\s+",
          "array-indexer-suffix": "",
          "array-indexer-end": "\\)",
          "funcapp-begin": "\\(",
          "funcapp-args-begin": "",
          "funcapp-args-end": "",
          "funcapp-separator": "",
          "funcapp-end": "\\)",
          "import-standard": "\\(require-standard\\)",
          "import-begin": "\\(require\\s+",
          "import-end": "\\)",
          "block-begin-prefix": " ",
          "block-begin": "\\(begin\\s+",
          "block-end": "\\)",
          "assignment-begin": "\\(set\\!\\s+",
          "assignment-infix": "",
          "assignment-end": "\\)",
          "increment-begin": "\\(inc\\!\\s+",
          "increment-end": "\\)",
          "decrement-begin": "\\(dec\\!\\s+",
          "decrement-end": "\\)",
          "append-begin": "\\(append\\s+",
          "append-infix": "",
          "append-end": "\\)",
          "#print-begin": "\\(print\\s+",
          "#print-end": "\\)",
          "break": "\\(break\\)",
          "pass": "",
          "return-begin": "\\(return\\s+",
          "return-end": "\\)",
          "return-none": "\\(return\\)",
          "repeat-begin": "\\(repeat\\s+",
          "repeat-times": "",
          "repeat-end": "\\)",
          "if-begin": "\\(if\\s+",
          "if-condition-begin": "\\(",
          "if-condition-end": "\\)",
          "if-prefix==": "==",
          "if-prefix!=": "!=",
          "if-prefix<": "<",
          "if-prefix<=": "<=",
          "if-prefix>": ">",
          "if-prefix>=": ">=",
          "if-prefixin": "in",
          "if-prefixnotin": "not-in",
          "if-then": "",
          "if-else": "",
          "if-end": "\\)",
          "funcdef-begin": "\\(define\\s+",
          "funcdef-name-begin": "\\(",
          "funcdef-name-end": "",
          "funcdef-args-begin": "",
          "funcdef-arg-separator": "",
          "funcdef-args-end": "\\)",
          "funcdef-noarg": "",
          "funcdef-block": "",
          "funcdef-end": "\\)",
          "assert-begin": "\\(assert\\s+",
          "assert-infix": "",
          "assert-end": "\\)"
        },
        "wenyan": {
          "syntax": "Wenyan Like",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "line-comment-begin": "注(、|。)?",
          "word-segmenter": "",
          "comment-begin": "注始(。|)",
          "comment-end": "注終(。|)",
          "indent": "  ",
          "special-name-pattern": '[^\\s\\[\\]\\(\\)",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+',
          "special-name-funcname": "施\\s*({name_pattern})\\s*於",
          "special-name-variable": "名之曰\\s*({name_pattern})\\s*[。]",
          "null": "無|null",
          "boolean-true": "然|true",
          "boolean-false": "否|false",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "extra-name-begin": "`",
          "extra-name-end": "`",
          "string-begin": "「",
          "string-end": "」",
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "binary-infix+": "\\+",
          "binary-infix-": "-",
          "binary-infix*": "\\*",
          "binary-infix/": "/",
          "binary-infix%": "%",
          "binary-infix==": "==",
          "binary-infix!=": "!=",
          "binary-infix<=": "<=",
          "binary-infix>=": ">=",
          "binary-infix<": "<",
          "binary-infix>": ">",
          "unary-minus": "-",
          "array-indexer-begin": "取",
          "array-indexer-infix": "之第",
          "array-indexer-suffix": "",
          "array-indexer-end": "",
          "property-length": "之量",
          "funcapp-begin": "施",
          "funcapp-args-begin": "於",
          "funcapp-args-end": "",
          "funcapp-separator": "與",
          "funcapp-noarg": "以虛",
          "import-standard": "引標準庫",
          "import-begin": "引",
          "import-end": "",
          "block-begin": "",
          "block-end": "",
          "assignment-begin": "吾有一數(、|)曰",
          "assignment-infix": "(、|)名之曰",
          "assignment-end": "。",
          "assignment-order": "reversed",
          "increment-begin": "(增|増)",
          "increment-end": "以一(。|)",
          "decrement-begin": "減",
          "decrement-end": "以一(。|)",
          "append-begin": "納",
          "append-infix": "入",
          "append-end": "(。|)",
          "append-order": "reversed",
          "!break": "break",
          "break": "止(。|)",
          "pass": "無為(。|)",
          "print-begin": "吿曰",
          "print-end": "(。|)",
          "!return-begin": "return",
          "return-begin": "以",
          "return-end": "答(。|)",
          "return-none": "還無(。|)",
          "repeat-begin": "",
          "repeat-times": "度、",
          "repeat-block": "",
          "repeat-end": "度畢(。|)",
          "!if-begin": "if",
          "if-begin": "若",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": "等於",
          "if-infix!=": "異於",
          "if-infix<": "小於",
          "if-infix>": "大於",
          "if-infix<=": "不大於",
          "if-infix>=": "不小於",
          "if-infixin": "含",
          "if-infixnotin": "不含",
          "if-then": "乎(、|)則",
          "if-else": "否則",
          "if-end": "條畢(。|)",
          "funcdef-begin": "術曰",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "以",
          "funcdef-arg-separator": "與",
          "funcdef-args-end": "",
          "funcdef-noarg": "。",
          "funcdef-block": "",
          "funcdef-end": "術畢(。|)"
        },
        "yui": {
          "syntax": "Yui-Classic",
          "function-language": "ja",
          "whitespace": "[ \\t\\r　]",
          "whitespaces": "[ \\t\\r　]+",
          "linefeed": "[\\n]",
          "line-comment-begin": "[#＃]",
          "comment-begin": "",
          "comment-end": "",
          "indent": "  ",
          "null": "値なし|null",
          "boolean-true": "真|true",
          "boolean-false": "偽|false",
          "number-first-char": "[0-9]",
          "number-chars": "[0-9]*",
          "number-dot-char": "[\\.]",
          "name-first-char": "[A-Za-z_]",
          "name-chars": "[A-Za-z0-9_]*",
          "extra-name-begin": "「",
          "extra-name-end": "」",
          "string-begin": '"',
          "string-end": '"',
          "string-escape": "\\\\",
          "string-interpolation-begin": "\\{",
          "string-interpolation-end": "\\}",
          "string-content-end": '\\\\|\\{|\\"',
          "!string-begin": `'|f"`,
          "array-begin": "\\[",
          "array-end": "\\]",
          "array-separator": "[,、，]",
          "object-begin": "\\{",
          "object-end": "\\}",
          "object-separator": "[,、，]",
          "key-value-separator": ":",
          "grouping-begin!": "\\(",
          "grouping-end!": "\\)",
          "length-begin": "\\|",
          "length-end": "\\|",
          "binary-infix+": "\\+",
          "binary-infix-": "-",
          "binary-infix*": "\\*",
          "binary-infix/": "/",
          "binary-infix%": "%",
          "binary-infix==": "==",
          "binary-infix!=": "!=",
          "binary-infix<=": "<=",
          "binary-infix>=": ">=",
          "binary-infix<": "<",
          "binary-infix>": ">",
          "unary-minus": "-",
          "array-indexer-suffix": "\\[",
          "array-indexer-end": "\\]",
          "property-length": "の大きさ",
          "funcapp-args-begin": "\\(",
          "funcapp-args-end": "\\)",
          "funcapp-separator": "[,、，]",
          "import-standard": "標準ライブラリを使う",
          "import-operator": "四則演算子を使う",
          "import-begin": "",
          "import-end": "を使う",
          "!block-begin": ":|：",
          "block-begin": "[\\{｛]",
          "block-end": "[\\}｝]",
          "block-line": "",
          "assignment-begin": "",
          "assignment-infix": "[=＝]",
          "assignment-end": "",
          "increment-begin": "",
          "increment-infix": "",
          "increment-end": "を増やす",
          "!increment-end": "\\+\\=|\\+\\+",
          "increment-lookahead": "増やす",
          "decrement-begin": "",
          "decrement-infix": "",
          "!decrement-end": "\\-\\=|\\-\\-",
          "decrement-end": "を減らす",
          "append-lookahead": "を追加する",
          "append-begin": "",
          "append-infix": "(の末尾)?に",
          "append-end": "を追加する",
          "append2-lookahead": "に追加する",
          "append2-begin": "",
          "append2-infix": "を",
          "append2-end": "に追加する",
          "print-begin": "",
          "print-end": "",
          "!break": "break",
          "break": "くり返しを抜ける",
          "pass": "何もしない",
          "!return-begin": "return",
          "return-begin": "",
          "return-end": "が[、]?答え",
          "return-none": "関数から抜ける",
          "repeat-begin": "",
          "repeat-times": "回[、]?",
          "!repeat-block": "繰り返す|くりかえす",
          "repeat-block": "くり返す",
          "repeat-end": "",
          "!if-begin": "if",
          "if-begin": "もし",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix": "が",
          "!if-infix": "は|==|!=|<|<=|>|>=|＝|≦|≧|≠",
          "if-suffix!=": "以外",
          "!if-suffix!=": "でない",
          "if-suffix<": "より小さい",
          "if-suffix<=": "以下",
          "if-suffix>": "より大きい",
          "if-suffix>=": "以上",
          "if-suffixin": "のいずれか",
          "if-suffixnotin": "のいずれでもない",
          "if-then": "ならば[、]?",
          "if-else": "そうでなければ[、]?",
          "if-end": "",
          "funcdef-begin": "",
          "funcdef-name-begin": "",
          "funcdef-name-end": "[=＝]",
          "funcdef-args-begin": "入力",
          "funcdef-arg-separator": "[,、]",
          "funcdef-args-end": "",
          "funcdef-noarg": "入力なし",
          "funcdef-block": "に対し[て]?[、]?",
          "funcdef-end": ""
        },
        "zup": {
          "syntax": "cryptic zup",
          "description": "Zup is a programming language designed to be deliberately opaque to anyone unfamiliar with its specification. All keywords follow a strict CVC (Consonant-Vowel-Consonant) syllable structure, drawn from a constrained phoneme set that avoids common patterns found in natural languages — making the vocabulary impossible to guess by intuition alone.",
          "function-language": "emoji",
          "word-segmenter": " ",
          "comment-begin": "",
          "comment-end": "",
          "indent": "  ",
          "special-name-variable": "Kem\\s+({name_pattern})\\s+par",
          "null": "zup",
          "boolean-true": "vak",
          "boolean-false": "mep",
          "binary-infix+": "rug",
          "binary-infix-": "dap",
          "binary-infix*": "gev",
          "binary-infix/": "kum",
          "binary-infix%": "zen",
          "binary-infix==": "paz",
          "binary-infix!=": "nup",
          "binary-infix<=": "dur",
          "binary-infix>=": "pev",
          "binary-infix<": "dup",
          "binary-infix>": "pep",
          "binary-infixin": "kag",
          "property-length": "\\@kez",
          "import-standard": "Nav rem vaz",
          "import-begin": "Nav",
          "import-end": "",
          "block-begin": ":",
          "block-end": "",
          "assignment-begin": "Kem",
          "assignment-infix": "par",
          "assignment-end": "",
          "increment-begin": "Rav",
          "increment-end": "",
          "decrement-begin": "Zar",
          "decrement-end": "",
          "append-begin": "Mev",
          "append-infix": "naz",
          "append-end": "",
          "break": "Dez kup",
          "pass": "Mup nek",
          "print-begin": "",
          "print-end": "",
          "return-begin": "Dup vem",
          "return-end": "",
          "return-none": "Nag pag",
          "repeat-begin": "Mup dum",
          "repeat-times": "pag",
          "repeat-block": "",
          "repeat-end": "Dam mup",
          "if-begin": "Nev",
          "if-condition-begin": "",
          "if-condition-end": "",
          "if-prefix": "",
          "if-infix==": "paz",
          "if-infix!=": "nup",
          "if-infix<": "dup",
          "if-infix<=": "dur",
          "if-infix>": "pep",
          "if-infix>=": "pev",
          "if-infixin": "kag",
          "if-infixnotin": "nag",
          "if-then": "ger",
          "if-else": "Zum",
          "if-end": "Dam nev",
          "funcdef-begin": "Dum",
          "funcdef-name-begin": "",
          "funcdef-name-end": "",
          "funcdef-args-begin": "\\(",
          "funcdef-arg-separator": ",",
          "funcdef-args-end": "\\)",
          "funcdef-noarg": "",
          "funcdef-block": "",
          "funcdef-end": "Pam dum"
        }
      });
      SYNTAX_NAMES = Object.freeze(["ast", "bridget", "emoji", "empty", "jslike", "nannan", "pylike", "sexpr", "wenyan", "yui", "zup"]);
    }
  });

  // src/yuiparser.js
  var yuiparser_exports = {};
  __export(yuiparser_exports, {
    NONTERMINALS: () => NONTERMINALS,
    Source: () => Source,
    SourceNode: () => SourceNode,
    YuiParser: () => YuiParser
  });
  function _isAsciiIdentifier(s) {
    return _ASCII_IDENTIFIER_RE.test(s);
  }
  var SourceNode, _ASCII_IDENTIFIER_RE, Source, NONTERMINALS, ParserCombinator, ConstParser, NumberParser, _ESCAPED_STRING, StringParser, ArrayParser, ObjectParser, NameParser, LITERALS, TermParser, PrimaryParser, MultiplicativeParser, AdditiveParser, ComparativeParser, AssignmentParser, IncrementParser, DecrementParser, AppendParser, BreakParser, ImportParser, PassParser, ReturnParser, PrintExpressionParser, RepeatParser, IfParser, FuncDefParser, _YUI_FALLBACK_SYNTAX, AssertParser, BlockParser, STATEMENTS, StatementParser, StatementsParser, TopLevelParser, YuiParser;
  var init_yuiparser = __esm({
    "src/yuiparser.js"() {
      init_yuiast();
      init_yuierror();
      init_yuisyntax();
      SourceNode = class extends ASTNode {
      };
      _ASCII_IDENTIFIER_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;
      Source = class extends YuiSyntax {
        /**
         * @param {string} source  ソースコード文字列
         * @param {object} [opts]
         * @param {string} [opts.filename='main.yui']
         * @param {number} [opts.pos=0]
         * @param {string|object} [opts.syntax='yui']  syntax 名または既にロード済みの terminals dict
         */
        constructor(source, opts = {}) {
          const { filename = "main.yui", pos = 0, syntax = "yui" } = opts;
          const terminals = typeof syntax === "string" ? loadSyntax(syntax) : syntax;
          super(terminals);
          this.filename = filename;
          this.source = source;
          this.pos = pos;
          this.length = source.length;
          this.specialNames = [];
          this.currentIndent = "";
          this.memos = /* @__PURE__ */ new Map();
          this.matchedString = "";
          this.matchedSuffix = null;
          this._searchRegexes = /* @__PURE__ */ new Map();
          this.extractSpecialNames("\n" + source);
        }
        hasNext() {
          return this.pos < this.length;
        }
        isEos() {
          return this.pos >= this.length;
        }
        consumeString(text) {
          if (this.source.startsWith(text, this.pos)) {
            this.pos += text.length;
            return true;
          }
          return false;
        }
        /**
         * 現在位置で terminal にマッチするなら消費する。
         * Python: match_(terminal, if_undefined, unconsumed, start_pos, check_typo)
         */
        match(terminal, opts = {}) {
          const {
            ifUndefined = false,
            unconsumed = false,
            startPos = null,
            checkTypo = true
          } = opts;
          if (!this.isDefined(terminal)) {
            if (startPos !== null) {
              this.pos = startPos;
            }
            return ifUndefined;
          }
          const savedPos = startPos === null ? this.pos : startPos;
          if (checkTypo && this.isDefined(`!${terminal}`)) {
            const typoRe = this.getPattern(`!${terminal}`);
            typoRe.lastIndex = this.pos;
            const typoMatch = typoRe.exec(this.source);
            if (typoMatch && typoMatch.index === this.pos) {
              const matched = this.source.slice(this.pos, this.pos + typoMatch[0].length);
              const expected = this.forExample(terminal);
              throw new YuiError(
                ["typo", `❌\`${matched}\``, `✅${expected}`, `🧬${terminal}`],
                this.p(null, null, null, matched.length)
              );
            }
          }
          const pattern = this.getPattern(terminal);
          pattern.lastIndex = this.pos;
          const m = pattern.exec(this.source);
          if (m && m.index === this.pos) {
            this.matchedString = m[0];
            if (unconsumed) {
              this.pos = savedPos;
              return true;
            }
            this.pos = this.pos + m[0].length;
            return true;
          }
          this.matchedString = "";
          this.pos = savedPos;
          return false;
        }
        /** global ('g') フラグ付きの正規表現をキャッシュして返す。consume_until 用。 */
        _getSearchPattern(terminal) {
          let re = this._searchRegexes.get(terminal);
          if (re) return re;
          const src = this.get(terminal);
          if (src === "") return null;
          re = new RegExp(src, "g");
          this._searchRegexes.set(terminal, re);
          return re;
        }
        consumeUntil(terminal, opts = {}) {
          const { untilEof = true, disallowString = null } = opts;
          const re = this._getSearchPattern(terminal);
          if (re) {
            re.lastIndex = this.pos;
            const m = re.exec(this.source);
            if (m) {
              const matchStart = m.index;
              if (disallowString) {
                if (this.source.slice(this.pos, matchStart).includes(disallowString)) {
                  return false;
                }
              }
              this.pos = matchStart;
              return true;
            }
          }
          if (untilEof) {
            this.pos = this.length;
            return true;
          }
          return false;
        }
        skipWhitespacesAndComments({ includeLinefeed = false } = {}) {
          while (this.hasNext()) {
            if (this.match("whitespace", { checkTypo: false })) continue;
            if (includeLinefeed && this.match("linefeed", { checkTypo: false })) continue;
            if (this.match("line-comment-begin")) {
              this.consumeUntil("linefeed", { untilEof: true });
              continue;
            }
            if (this.match("comment-begin")) {
              const openingPos = this.pos - this.matchedString.length;
              this.consumeUntil("comment-end", { untilEof: true });
              this.require("comment-end", { lskipWs: false, openingPos });
              continue;
            }
            break;
          }
        }
        isEosOrLinefeed({ lskipWs = true, unconsumed = false } = {}) {
          const savedPos = this.pos;
          if (lskipWs) {
            this.skipWhitespacesAndComments({ includeLinefeed: false });
          }
          if (this.isEos()) {
            if (unconsumed) {
              this.pos = savedPos;
            }
            return true;
          }
          return this.is("linefeed", {
            lskipWs: false,
            lskipLf: false,
            unconsumed
          });
        }
        /**
         * 現在位置で terminal にマッチするかをチェック (ws スキップを含む)。
         * Python: is_(terminal, suffixes, if_undefined, unconsumed, lskip_ws, lskip_lf)
         */
        is(terminal, opts = {}) {
          const {
            suffixes = null,
            ifUndefined = false,
            unconsumed = false,
            lskipWs = true,
            lskipLf = false
          } = opts;
          const startPos = this.pos;
          if (lskipWs || lskipLf) {
            this.skipWhitespacesAndComments({ includeLinefeed: lskipLf });
          }
          if (suffixes !== null) {
            this.matchedSuffix = null;
            const savedPos = this.pos;
            for (const suffix of suffixes) {
              const key = `${terminal}${suffix}`;
              if (this.match(key, { unconsumed, startPos })) {
                this.matchedSuffix = suffix;
                return true;
              }
              this.pos = savedPos;
            }
            this.pos = startPos;
            return false;
          }
          if (terminal.includes("|")) {
            for (const option of terminal.split("|")) {
              if (this.match(option, { ifUndefined, unconsumed, startPos })) {
                return true;
              }
            }
            this.pos = startPos;
            return false;
          }
          return this.match(terminal, { ifUndefined, unconsumed, startPos });
        }
        /**
         * 現在位置で terminal にマッチすることを要求する。失敗したら YuiError を投げる。
         * Python: require_(terminal, suffixes, if_undefined=True, unconsumed, lskip_ws, lskip_lf, opening_pos, BK)
         */
        require(terminal, opts = {}) {
          const {
            suffixes = null,
            ifUndefined = true,
            unconsumed = false,
            lskipWs = true,
            lskipLf = false,
            openingPos = null,
            BK = false
          } = opts;
          if (!this.isDefined(terminal)) {
            return;
          }
          if (this.is(terminal, { suffixes, ifUndefined, unconsumed, lskipWs, lskipLf })) {
            return;
          }
          const expectedToken = this.forExample(terminal);
          if (openingPos !== null) {
            throw new YuiError(
              ["expected-closing", `✅\`${expectedToken}\``, `🧬${terminal}`],
              this.p(null, openingPos)
            );
          }
          const snippet = this.captureLine();
          throw new YuiError(
            ["expected-token", `❌\`${snippet}\``, `✅\`${expectedToken}\``, `🧬${terminal}`],
            this.p(null, null, null, 1),
            BK
          );
        }
        save() {
          return [this.pos, this.currentIndent];
        }
        backtrack(saved) {
          this.pos = saved[0];
          this.currentIndent = saved[1];
        }
        getMemo(nonterminal, pos) {
          const key = `${nonterminal}\0${pos}`;
          return this.memos.get(key) ?? null;
        }
        setMemo(nonterminal, pos, result, newPos) {
          const key = `${nonterminal}\0${pos}`;
          this.memos.set(key, [result, newPos]);
        }
        /**
         * nonterminal をパースする。Packrat parsing のメモ化あり。
         * Python: parse(nonterminal, lskip_ws, lskip_lf, BK)
         */
        parse(nonterminal, opts = {}) {
          const { lskipWs = true, lskipLf = false, BK = false } = opts;
          const patterns = NONTERMINALS[nonterminal];
          if (patterns === void 0) {
            throw new Error(`Unknown nonterminal: ${nonterminal}`);
          }
          if (lskipWs || lskipLf) {
            this.skipWhitespacesAndComments({ includeLinefeed: lskipLf });
          }
          const memo = this.getMemo(nonterminal, this.pos);
          if (memo !== null) {
            this.pos = memo[1];
            return memo[0];
          }
          const saved = this.save();
          const savedPos = this.pos;
          try {
            const result = patterns.match(this);
            this.setMemo(nonterminal, savedPos, result, this.pos);
            return result;
          } catch (e) {
            if (e instanceof YuiError) {
              if (e.BK === true && BK === false) {
                this.backtrack(saved);
                const snippet = this.captureLine();
                throw new YuiError(
                  [`expected-${nonterminal.slice(1).toLowerCase()}`, `❌${snippet}`, `⚠️${e.message}`],
                  this.p(null, null, null, 1)
                );
              }
            }
            throw e;
          }
        }
        canBacktrack(lookahead) {
          if (this.isDefined(lookahead)) {
            const captured = this.captureLine();
            const src = this.get(lookahead);
            try {
              const re = new RegExp(src);
              return !re.test(captured);
            } catch {
              return true;
            }
          }
          return true;
        }
        /**
         * 変数定義形 `name =` や 関数呼び出し形 `name(` から special-name を抽出する。
         * Python: extract_special_names
         */
        extractSpecialNames(text) {
          let names;
          if (this.isDefined("special-names")) {
            names = (this.terminals["special-names"] || "").split("|");
          } else {
            names = [];
          }
          const namePattern = this.terminals["special-name-pattern"] || '[^\\s\\[\\]\\(\\)",\\.+*/%=!<>-]+';
          const varPatternRaw = this.terminals["special-name-variable"] || "(?:^|\\n)\\s*({name_pattern})\\s*=(?!=)";
          const varPattern = varPatternRaw.replace("{name_pattern}", namePattern);
          const varRe = new RegExp(varPattern, "g");
          for (const m of text.matchAll(varRe)) {
            if (m[1] !== void 0) names.push(m[1]);
          }
          const funcPatternRaw = this.terminals["special-name-funcname"] || "({name_pattern})\\s*[\\(]";
          const funcPattern = funcPatternRaw.replace("{name_pattern}", namePattern);
          const funcRe = new RegExp(funcPattern, "g");
          for (const m of text.matchAll(funcRe)) {
            if (m[1] !== void 0) names.push(m[1]);
          }
          const uniq = /* @__PURE__ */ new Set();
          for (const n of names) {
            const trimmed = n.trim();
            if (trimmed === "") continue;
            if (_isAsciiIdentifier(trimmed)) continue;
            uniq.add(trimmed);
          }
          this.specialNames = [...uniq].sort((a, b) => b.length - a.length);
          vprint(`@extracted special names: ${JSON.stringify(this.specialNames)}`);
        }
        matchSpecialName({ unconsumed = false } = {}) {
          for (const name of this.specialNames) {
            if (this.source.startsWith(name, this.pos)) {
              if (!unconsumed) {
                this.pos += name.length;
              }
              return name;
            }
          }
          return null;
        }
        captureIndent(indentChars = " 	　") {
          let startPos = this.pos - 1;
          while (startPos >= 0) {
            const char = this.source[startPos];
            if (char === "\n") {
              startPos += 1;
              break;
            }
            startPos -= 1;
          }
          if (startPos < 0) startPos = 0;
          let endPos = startPos;
          while (endPos < this.length) {
            const char = this.source[endPos];
            if (indentChars.includes(char)) {
              endPos += 1;
            } else {
              break;
            }
          }
          return this.source.slice(startPos, endPos);
        }
        captureLine() {
          const startPos = this.pos;
          while (this.pos < this.length) {
            if (this.is("linefeed|line-comment-begin|comment-begin|statement-separator", {
              lskipWs: false,
              unconsumed: true
            })) {
              const captured = this.source.slice(startPos, this.pos);
              this.pos = startPos;
              return captured;
            }
            this.pos += 1;
          }
          this.pos = startPos;
          return this.source.slice(startPos).split("\n")[0];
        }
        captureComment() {
          const savePos = this.pos;
          let comment = null;
          if (this.is("line-comment-begin")) {
            const startPos = this.pos;
            this.consumeUntil("linefeed", { untilEof: true });
            comment = this.source.slice(startPos, this.pos);
          }
          if (this.is("comment-begin")) {
            const startPos = this.pos;
            this.consumeUntil("comment-end", { untilEof: true });
            comment = this.source.slice(startPos, this.pos);
          }
          this.pos = savePos;
          return comment;
        }
        /**
         * ASTNode に filename / source / pos / end_pos を書き込んで返す。
         * node 省略時は SourceNode を作る。
         *
         * Python: p(node=None, start_pos=None, end_pos=None, length=0)
         * JS 側は option オブジェクトだとパーサ本体の呼び出しが冗長になりすぎるので
         * 位置引数を Python と同じ順で受ける (後方 3 つが任意)。
         */
        p(node = null, startPos = null, endPos = null, length = 0) {
          const n = node || new SourceNode();
          n.filename = this.filename;
          n.source = this.source;
          const savePos = this.pos;
          if (startPos !== null) {
            n.pos = startPos;
            if (endPos !== null && endPos !== void 0) {
              n.end_pos = endPos;
            } else if (length !== 0) {
              n.end_pos = Math.min(startPos + length, this.length);
            } else {
              n.end_pos = savePos;
            }
          } else if (length !== 0) {
            n.pos = this.pos;
            n.end_pos = Math.min(this.pos + length, this.length);
          } else {
            n.pos = Math.max(this.pos - 1, 0);
            n.end_pos = this.pos;
          }
          return n;
        }
        printDebug(message) {
          const node = this.p(null, this.pos);
          const [linenum, col, line] = node.extract();
          console.log(`@debug ${message} at pos=${this.pos} line=${linenum} col=${col}`);
          console.log(`${line}
${" ".repeat(col - 1)}^`);
        }
      };
      NONTERMINALS = {};
      ParserCombinator = class {
        // eslint-disable-next-line no-unused-vars
        quickCheck(_source) {
          return true;
        }
        // eslint-disable-next-line no-unused-vars
        match(_source) {
          return true;
        }
      };
      ConstParser = class extends ParserCombinator {
        quickCheck(source) {
          return source.is("null|boolean-true|boolean-false");
        }
        match(source) {
          const savedPos = source.pos;
          if (source.is("null")) {
            return source.p(new ConstNode(null), savedPos);
          }
          if (source.is("boolean-true")) {
            return source.p(new ConstNode(true), savedPos);
          }
          if (source.is("boolean-false")) {
            return source.p(new ConstNode(false), savedPos);
          }
          throw new YuiError(["expected-boolean"], source.p(null, null, null, 1), true);
        }
      };
      NONTERMINALS["@Boolean"] = new ConstParser();
      NumberParser = class extends ParserCombinator {
        quickCheck(source) {
          if (source.matchSpecialName({ unconsumed: true }) !== null) {
            return false;
          }
          return source.is("number-first-char", { unconsumed: true });
        }
        match(source) {
          const startPos = source.pos;
          if (source.is("number-first-char")) {
            source.require("number-chars", { lskipWs: false });
            if (source.is("number-dot-char", { lskipWs: false })) {
              source.is("number-chars", { lskipWs: false });
              const number2 = source.source.slice(startPos, source.pos);
              return source.p(new NumberNode(parseFloat(number2)), startPos);
            }
            const number = source.source.slice(startPos, source.pos);
            return source.p(new NumberNode(parseInt(number, 10)), startPos);
          }
          throw new YuiError(["expected-number"], source.p(null, null, null, 1), true);
        }
      };
      NONTERMINALS["@Number"] = new NumberParser();
      _ESCAPED_STRING = {
        n: "\n",
        t: "	"
      };
      StringParser = class extends ParserCombinator {
        quickCheck(source) {
          return source.is("string-begin", { unconsumed: true });
        }
        match(source) {
          const openingQuotePos = source.pos;
          if (source.is("string-begin")) {
            let openingPos = source.pos;
            const stringContent = [];
            let expressionCount = 0;
            while (source.pos < source.length) {
              source.consumeUntil("string-content-end", { untilEof: true });
              stringContent.push(source.source.slice(openingPos, source.pos));
              if (source.is("string-end", { unconsumed: true })) {
                break;
              }
              if (source.is("string-escape")) {
                if (source.isEos()) {
                  throw new YuiError(["wrong-escape-sequence"], source.p(null, null, null, 1));
                }
                const nextChar = source.source[source.pos];
                source.pos += 1;
                stringContent.push(_ESCAPED_STRING[nextChar] ?? nextChar);
                openingPos = source.pos;
                continue;
              }
              const startInterPos = source.pos;
              if (source.is("string-interpolation-begin", { lskipWs: false })) {
                const expression = source.parse("@Expression");
                source.require("string-interpolation-end", { openingPos: startInterPos });
                stringContent.push(expression);
                expressionCount += 1;
                openingPos = source.pos;
                continue;
              }
            }
            source.require("string-end", { lskipWs: false, openingPos: openingQuotePos });
            const contents = expressionCount === 0 ? stringContent.join("") : stringContent;
            return source.p(new StringNode(contents), openingQuotePos);
          }
          throw new YuiError(["expected-string"], source.p(null, null, null, 1), true);
        }
      };
      NONTERMINALS["@String"] = new StringParser();
      ArrayParser = class extends ParserCombinator {
        quickCheck(source) {
          return source.is("array-begin", { unconsumed: true });
        }
        match(source) {
          const openingPos = source.pos;
          if (source.is("array-begin")) {
            const args = [];
            while (!source.is("array-end", { lskipLf: true, unconsumed: true })) {
              args.push(source.parse("@Expression", { lskipLf: true }));
              if (source.is("array-separator", { lskipLf: true })) {
                continue;
              }
            }
            source.require("array-end", { lskipLf: true, openingPos });
            return source.p(new ArrayNode(args), openingPos);
          }
          throw new YuiError(["expected-array"], source.p(null, null, null, 1), true);
        }
      };
      NONTERMINALS["@Array"] = new ArrayParser();
      ObjectParser = class extends ParserCombinator {
        quickCheck(source) {
          return source.is("object-begin", { unconsumed: true });
        }
        match(source) {
          const openingPos = source.pos;
          if (source.is("object-begin", { lskipLf: true })) {
            const args = [];
            while (!source.is("object-end", { lskipLf: true, unconsumed: true })) {
              args.push(source.parse("@String", { lskipLf: true }));
              source.require("key-value-separator", { lskipLf: true });
              args.push(source.parse("@Expression", { lskipLf: true }));
              if (source.is("object-separator", { lskipLf: true })) {
                continue;
              }
            }
            source.require("object-end", { lskipLf: true, openingPos });
            return source.p(new ObjectNode(args), openingPos);
          }
          throw new YuiError(["expected-object"], source.p(null, null, null, 1), true);
        }
      };
      NONTERMINALS["@Object"] = new ObjectParser();
      NameParser = class extends ParserCombinator {
        match(source) {
          let startPos = source.pos;
          if (source.is("keywords")) {
            const matchedKeyword = source.matchedString;
            const savedPos = source.pos;
            source.is("name-chars", { lskipWs: false });
            if (source.pos === savedPos) {
              throw new YuiError(
                ["keyword-name", `❌\`${matchedKeyword}\``],
                source.p(null, startPos),
                true
              );
            }
            source.pos = startPos;
          }
          const specialName = source.matchSpecialName();
          if (specialName !== null) {
            return source.p(new NameNode(specialName), source.pos - specialName.length);
          }
          if (source.is("extra-name-begin")) {
            startPos = source.pos;
            source.consumeUntil("extra-name-end", { disallowString: "\n" });
            const name = source.source.slice(startPos, source.pos);
            const node = source.p(new NameNode(name), startPos);
            source.require("extra-name-end", { openingPos: startPos - 1 });
            return node;
          }
          startPos = source.pos;
          if (source.is("name-first-char")) {
            source.require("name-chars", { lskipWs: false });
            source.require("name-last-char", { lskipWs: false });
            const name = source.source.slice(startPos, source.pos);
            return source.p(new NameNode(name), startPos);
          }
          const snippet = source.captureLine().trim();
          throw new YuiError(
            ["wrong-name", `❌${snippet}`],
            source.p(null, null, null, 1),
            true
          );
        }
      };
      NONTERMINALS["@Name"] = new NameParser();
      LITERALS = ["@Number", "@String", "@Array", "@Object", "@Boolean"];
      TermParser = class extends ParserCombinator {
        match(source) {
          const openingPos = source.pos;
          if (source.is("array-indexer-begin")) {
            const expression = source.parse("@Expression");
            source.require("array-indexer-infix");
            const index = source.parse("@Expression");
            source.require("array-indexer-end", { openingPos });
            const orderPolicy = source.get("array-indexer-order");
            return source.p(new GetIndexNode(expression, index, orderPolicy), openingPos);
          }
          if (source.is("minus-begin")) {
            const expression = source.parse("@Expression", { BK: false });
            if (source.is("minus-end")) {
              return source.p(new MinusNode(expression), openingPos);
            }
            source.pos = openingPos;
          }
          if (source.is("length-begin")) {
            const expressionNode = source.parse("@Expression");
            source.require("length-end", { openingPos });
            return source.p(new ArrayLenNode(expressionNode), openingPos);
          }
          if (source.is("catch-begin")) {
            const catchOpening = source.pos - source.matchedString.length;
            const expression = source.parse("@Expression", { BK: false });
            source.require("catch-end", { openingPos: catchOpening });
            return source.p(new CatchNode(expression), catchOpening);
          }
          if (source.is("grouping-begin")) {
            const expressionNode = source.parse("@Expression");
            source.require("grouping-end", { openingPos });
            return source.p(new PrintExpressionNode(expressionNode, false, true), openingPos);
          }
          if (source.isDefined("binary-infix-prefix-begin")) {
            if (source.is("binary-infix-prefix", {
              suffixes: ["+", "-", "*", "/", "%", "==", "!=", "<=", ">=", "<", ">", "in", "notin"]
            })) {
              const operator = source.matchedSuffix;
              const leftNode = source.parse("@Expression", { BK: false });
              const rightNode = source.parse("@Expression", { BK: false });
              source.require("binary-infix-prefix-end");
              return source.p(new BinaryNode(operator, leftNode, rightNode), openingPos);
            }
          }
          {
            const saved = source.save();
            try {
              if (source.is("funcapp-begin")) {
                const name = source.parse("@Name", { BK: true });
                const args = [];
                if (source.is("funcapp-args-begin")) {
                  while (!source.is("funcapp-args-end", { unconsumed: true })) {
                    args.push(source.parse("@Expression", { lskipLf: true }));
                    if (source.is("funcapp-separator")) {
                      continue;
                    }
                    break;
                  }
                  source.require("funcapp-args-end", { openingPos });
                } else if (source.is("funcapp-noarg")) {
                } else {
                  while (!source.is("funcapp-end", { unconsumed: true })) {
                    source.require("funcapp-separator");
                    const expression = source.parse("@Expression", { BK: false });
                    args.push(expression);
                  }
                  source.require("funcapp-end");
                }
                return source.p(new FuncAppNode(name, args), openingPos);
              }
            } catch (e) {
              if (!(e instanceof YuiError)) throw e;
              source.backtrack(saved);
            }
          }
          for (const literal of LITERALS) {
            if (NONTERMINALS[literal].quickCheck(source)) {
              source.pos = openingPos;
              return source.parse(literal, { BK: true });
            }
          }
          return source.parse("@Name", { BK: true });
        }
      };
      NONTERMINALS["@Term"] = new TermParser();
      PrimaryParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          if (source.is("unary-minus")) {
            return source.p(new MinusNode(source.parse("@Primary")), startPos);
          }
          if (source.is("unary-length")) {
            return source.p(new ArrayLenNode(source.parse("@Primary")), startPos);
          }
          if (source.is("unary-inspect")) {
            const node2 = source.parse("@Primary");
            return source.p(new PrintExpressionNode(node2, true), startPos);
          }
          let node = source.parse("@Term", { BK: true });
          while (source.hasNext()) {
            const openingPos = source.pos;
            if (source.is("funcapp-noarg")) {
              node = source.p(new FuncAppNode(node, []), startPos);
              continue;
            }
            if (source.is("funcapp-args-begin")) {
              const args = [];
              while (!source.is("funcapp-args-end", { unconsumed: true })) {
                args.push(source.parse("@Expression", { lskipLf: true }));
                if (source.is("funcapp-separator")) {
                  continue;
                }
                break;
              }
              source.require("funcapp-args-end", { openingPos });
              node = source.p(new FuncAppNode(node, args), startPos);
              continue;
            }
            if (source.is("array-indexer-suffix")) {
              const indexNode = source.parse("@Expression");
              source.require("array-indexer-end", { openingPos });
              node = source.p(new GetIndexNode(node, indexNode), startPos);
              continue;
            }
            if (source.is("property-length")) {
              node = source.p(new ArrayLenNode(node), startPos);
              continue;
            }
            break;
          }
          return node;
        }
      };
      NONTERMINALS["@Primary"] = new PrimaryParser();
      MultiplicativeParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          let leftNode = source.parse("@Primary", { BK: true });
          let saved = source.save();
          try {
            while (source.is("binary-infix", { suffixes: ["*", "/", "%"] })) {
              const operator = source.matchedSuffix;
              const rightNode = source.parse("@Primary");
              leftNode = source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
              saved = source.save();
            }
          } catch (e) {
            if (!(e instanceof YuiError)) throw e;
          }
          source.backtrack(saved);
          return leftNode;
        }
      };
      NONTERMINALS["@Multiplicative"] = new MultiplicativeParser();
      AdditiveParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          let leftNode = source.parse("@Multiplicative", { BK: true });
          let saved = source.save();
          try {
            while (source.is("binary-infix", { suffixes: ["+", "-"] })) {
              const operator = source.matchedSuffix;
              const rightNode = source.parse("@Multiplicative");
              leftNode = source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
              saved = source.save();
            }
          } catch (e) {
            if (!(e instanceof YuiError)) throw e;
          }
          source.backtrack(saved);
          return leftNode;
        }
      };
      NONTERMINALS["@Additive"] = new AdditiveParser();
      ComparativeParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          const leftNode = source.parse("@Additive", { BK: true });
          const saved = source.save();
          try {
            if (source.is("binary-infix", {
              suffixes: ["==", "!=", "<=", ">=", "<", ">", "in", "notin"]
            })) {
              const operator = source.matchedSuffix;
              const rightNode = source.parse("@Additive");
              return source.p(new BinaryNode(operator, leftNode, rightNode), startPos);
            }
          } catch (e) {
            if (!(e instanceof YuiError)) throw e;
          }
          source.backtrack(saved);
          return leftNode;
        }
      };
      NONTERMINALS["@Expression"] = new ComparativeParser();
      AssignmentParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("assignment-lookahead");
          const startPos = source.pos;
          source.require("assignment-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const leftNode = source.parse("@Expression", { BK });
          source.require("assignment-infix", { BK });
          const rightNode = source.parse("@Expression", { BK });
          source.require("assignment-end", { BK });
          const orderPolicy = source.get("assignment-order");
          return source.p(new AssignmentNode(leftNode, rightNode, orderPolicy), startPos);
        }
      };
      NONTERMINALS["@Assignment"] = new AssignmentParser();
      IncrementParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("increment-lookahead");
          const startPos = source.pos;
          source.require("increment-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const lvalueNode = source.parse("@Expression", { BK });
          source.require("increment-end", { BK });
          return source.p(new IncrementNode(lvalueNode), startPos);
        }
      };
      NONTERMINALS["@Increment"] = new IncrementParser();
      DecrementParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("decrement-lookahead");
          const startPos = source.pos;
          source.require("decrement-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const lvalueNode = source.parse("@Expression", { BK });
          source.require("decrement-end", { BK });
          return source.p(new DecrementNode(lvalueNode), startPos);
        }
      };
      NONTERMINALS["@Decrement"] = new DecrementParser();
      AppendParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("append-lookahead");
          const startPos = source.pos;
          source.require("append-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const lvalueNode = source.parse("@Expression", { BK });
          source.require("append-infix", { BK });
          const value = source.parse("@Expression", { BK });
          source.require("append-end", { BK });
          const orderPolicy = source.get("append-order");
          return source.p(new AppendNode(lvalueNode, value, orderPolicy), startPos);
        }
      };
      NONTERMINALS["@Append"] = new AppendParser();
      BreakParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          source.require("break", { BK: true });
          return source.p(new BreakNode(), startPos);
        }
      };
      NONTERMINALS["@Break"] = new BreakParser();
      ImportParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          source.require("import-standard", { BK: true });
          return source.p(new ImportNode(), startPos);
        }
      };
      NONTERMINALS["@Import"] = new ImportParser();
      PassParser = class extends ParserCombinator {
        match(source) {
          if (!source.isDefined("pass")) {
            throw new YuiError(["pass-not-defined"], source.p(null, null, null, 1), true);
          }
          const startPos = source.pos;
          source.require("pass", { BK: true });
          return source.p(new PassNode(), startPos);
        }
      };
      NONTERMINALS["@Pass"] = new PassParser();
      ReturnParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("return-lookahead");
          const startPos = source.pos;
          source.require("return-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const exprNode = source.parse("@Expression", { BK });
          source.require("return-end", { BK });
          return source.p(new ReturnNode(exprNode), startPos);
        }
      };
      NONTERMINALS["@Return"] = new ReturnParser();
      PrintExpressionParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("print-lookahead");
          const startPos = source.pos;
          source.require("print-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const exprNode = source.parse("@Expression", { BK });
          source.require("print-end", { BK });
          return source.p(new PrintExpressionNode(exprNode), startPos);
        }
      };
      NONTERMINALS["@PrintExpression"] = new PrintExpressionParser();
      RepeatParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("repeat-lookahead");
          const startPos = source.pos;
          source.require("repeat-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const timesNode = source.parse("@Expression", { BK });
          source.require("repeat-times", { BK });
          source.require("repeat-block", { BK });
          const blockNode = source.parse("@Block");
          source.require("repeat-end", { lskipLf: true, BK: false });
          const orderPolicy = source.get("repeat-order");
          return source.p(
            new RepeatNode(timesNode, blockNode, orderPolicy),
            startPos,
            blockNode.end_pos
          );
        }
      };
      NONTERMINALS["@Repeat"] = new RepeatParser();
      IfParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          let BK = source.canBacktrack("if-lookahead");
          source.require("if-begin", { BK });
          source.require("if-condition-begin", { BK });
          if (BK) BK = source.pos === startPos;
          let operator;
          let leftNode;
          let rightNode;
          if (source.is("if-prefix", { suffixes: ["==", "!=", "<=", "<", ">=", ">", "notin", "in"] })) {
            operator = source.matchedSuffix;
            BK = false;
            leftNode = source.parse("@Expression", { BK });
            rightNode = source.parse("@Expression", { BK });
          } else {
            leftNode = source.parse("@Expression", { BK });
            if (leftNode instanceof BinaryNode && leftNode.comparative) {
              operator = String(leftNode.operator);
              rightNode = leftNode.right_node;
              leftNode = leftNode.left_node;
            } else if (source.is("if-infix", { suffixes: ["notin", "in", "!=", "<=", "<", ">=", ">", "=="] })) {
              operator = source.matchedSuffix;
              BK = false;
              rightNode = source.parse("@Expression", { BK });
            } else {
              source.require("if-infix", { BK });
              rightNode = source.parse("@Expression", { BK });
              if (source.is("if-suffix", { suffixes: ["!=", "<=", "<", ">=", ">", "notin", "in", "=="] })) {
                operator = source.matchedSuffix;
              } else {
                operator = "==";
              }
            }
          }
          source.require("if-condition-end", { BK });
          source.require("if-then", { BK });
          const thenNode = source.parse("@Block", { BK: false });
          const elseEndPos = source.pos;
          let nodeEndPos = thenNode.end_pos;
          let elseNode = null;
          source.skipWhitespacesAndComments({ includeLinefeed: true });
          if (source.is("if-else")) {
            elseNode = source.parse("@Block", { BK: false });
            nodeEndPos = elseNode.end_pos;
          } else if (source.isDefined("if-end") && !source.is("if-end", { unconsumed: true })) {
            try {
              elseNode = source.parse("@Block", { BK: false });
              nodeEndPos = elseNode.end_pos;
            } catch (e) {
              if (!(e instanceof YuiError)) throw e;
              source.pos = elseEndPos;
              elseNode = null;
            }
          } else {
            source.pos = elseEndPos;
            elseNode = null;
          }
          source.require("if-end", { lskipLf: true, BK: false });
          return source.p(
            new IfNode(leftNode, operator, rightNode, thenNode, elseNode),
            startPos,
            nodeEndPos
          );
        }
      };
      NONTERMINALS["@If"] = new IfParser();
      FuncDefParser = class extends ParserCombinator {
        match(source) {
          let BK = source.canBacktrack("funcdef-lookahead");
          const startPos = source.pos;
          source.require("funcdef-begin", { BK });
          source.require("funcdef-name-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const nameNode = source.parse("@Name", { BK });
          source.require("funcdef-name-end", { BK });
          const args = [];
          if (!source.is("funcdef-noarg")) {
            source.require("funcdef-args-begin", { BK });
            while (!source.is("funcdef-args-end", { unconsumed: true })) {
              args.push(source.parse("@Name", { BK }));
              if (source.is("funcdef-arg-separator", { ifUndefined: true })) {
                continue;
              }
              break;
            }
            source.require("funcdef-args-end", { BK });
          }
          source.require("funcdef-block", { BK });
          const bodyNode = source.parse("@Block", { BK: false });
          source.require("funcdef-end", { lskipLf: true, BK: false });
          return source.p(
            new FuncDefNode(nameNode, args, bodyNode),
            startPos,
            bodyNode.end_pos
          );
        }
      };
      NONTERMINALS["@FuncDef"] = new FuncDefParser();
      _YUI_FALLBACK_SYNTAX = loadSyntax("yui");
      AssertParser = class extends ParserCombinator {
        match(source) {
          const startPos = source.pos;
          let BK = source.canBacktrack("assert-lookahead");
          source.require("assert-begin", { BK });
          if (BK) BK = source.pos === startPos;
          const saved = source.save();
          let firstError = null;
          try {
            let testNode = source.parse("@Expression", { BK });
            let referenceNode;
            if (testNode instanceof BinaryNode && testNode.comparative) {
              referenceNode = testNode.right_node;
              testNode = testNode.left_node;
            } else {
              source.require("assert-infix", { BK });
              referenceNode = source.parse("@Expression", { BK });
            }
            source.require("assert-end", { BK });
            const orderPolicy = source.get("assert-order");
            return source.p(new AssertNode(testNode, referenceNode, orderPolicy), startPos);
          } catch (e) {
            if (!(e instanceof YuiError)) throw e;
            firstError = e;
            source.backtrack(saved);
          }
          const savedTerminals = source.terminals;
          try {
            source.terminals = { ..._YUI_FALLBACK_SYNTAX };
            source._searchRegexes = /* @__PURE__ */ new Map();
            const testNode = source.parse("@Expression", { BK });
            source.require("assert-infix", { BK });
            const referenceNode = source.parse("@Expression", { BK });
            source.require("assert-end", { BK });
            const orderPolicy = source.get("assert-order");
            return source.p(new AssertNode(testNode, referenceNode, orderPolicy), startPos);
          } catch (_) {
            throw firstError;
          } finally {
            source.terminals = savedTerminals;
            source._searchRegexes = /* @__PURE__ */ new Map();
          }
        }
      };
      NONTERMINALS["@Assert"] = new AssertParser();
      BlockParser = class extends ParserCombinator {
        match(source) {
          const saved = source.save();
          if (source.is("line-block-begin")) {
            const openingPos2 = source.pos - source.matchedString.length;
            if (source.is("line-block-end")) {
              return source.p(new BlockNode([]), openingPos2);
            }
            try {
              const statements2 = source.parse("@Statement[]");
              source.require("line-block-end", { BK: false });
              return source.p(new BlockNode(statements2), openingPos2);
            } catch (e) {
              if (!(e instanceof YuiError)) throw e;
              source.backtrack(saved);
            }
          }
          source.require("block-begin", { lskipLf: true });
          const openingPos = source.pos - source.matchedString.length;
          const statements = [];
          if (source.isDefined("indent") && !source.isDefined("block-end")) {
            const indent = source.captureIndent();
            let blockEndPos = null;
            while (source.hasNext()) {
              const savedBeforeLf = source.save();
              source.require("linefeed", { lskipWs: true });
              if (source.is("linefeed", { unconsumed: true })) {
                continue;
              }
              if (source.consumeString(indent)) {
                if (source.is("block-end", { lskipWs: false, unconsumed: true })) {
                  break;
                }
                if (source.is("whitespace", { lskipWs: false })) {
                  statements.push(...source.parse("@Statement[]"));
                  continue;
                }
              }
              blockEndPos = source.pos;
              source.backtrack(savedBeforeLf);
              break;
            }
            source.require("block-end", { openingPos });
            return source.p(new BlockNode(statements), openingPos, blockEndPos);
          }
          while (!source.is("block-end", { lskipLf: true, unconsumed: true })) {
            const curPos = source.pos;
            statements.push(...source.parse("@Statement[]", { lskipLf: true }));
            if (curPos === source.pos) {
              break;
            }
          }
          source.require("block-end", { lskipLf: true, openingPos });
          return source.p(new BlockNode(statements), openingPos);
        }
      };
      NONTERMINALS["@Block"] = new BlockParser();
      STATEMENTS = [
        "@FuncDef",
        "@Increment",
        "@Decrement",
        "@Append",
        "@Import",
        "@Break",
        "@Assignment",
        "@Assert",
        "@If",
        "@Repeat",
        "@Return",
        "@Pass",
        "@PrintExpression"
      ];
      StatementParser = class extends ParserCombinator {
        match(source) {
          const saved = source.save();
          for (const parserName of STATEMENTS) {
            try {
              return source.parse(parserName, { BK: true });
            } catch (e) {
              if (!(e instanceof YuiError)) throw e;
              if (!e.BK) throw e;
            }
            source.backtrack(saved);
          }
          const line = source.captureLine();
          if (line.trim() === "" && !source.isDefined("pass")) {
            return source.p(new PassNode(), source.pos);
          }
          throw new YuiError(
            ["wrong-statement", `❌${line}`],
            source.p(null, null, null, 1)
          );
        }
      };
      NONTERMINALS["@Statement"] = new StatementParser();
      StatementsParser = class extends ParserCombinator {
        match(source) {
          let statements;
          if (source.isEosOrLinefeed({ lskipWs: true, unconsumed: true })) {
            statements = [];
          } else {
            statements = [source.parse("@Statement")];
          }
          while (source.is("statement-separator")) {
            statements.push(source.parse("@Statement"));
          }
          return statements;
        }
      };
      NONTERMINALS["@Statement[]"] = new StatementsParser();
      TopLevelParser = class extends ParserCombinator {
        match(source) {
          source.skipWhitespacesAndComments({ includeLinefeed: true });
          const savedPos = source.pos;
          const statements = [];
          while (source.hasNext()) {
            const curPos = source.pos;
            statements.push(...source.parse("@Statement[]"));
            if (curPos === source.pos) {
              break;
            }
            source.skipWhitespacesAndComments({ includeLinefeed: true });
          }
          if (source.hasNext()) {
            const line = source.captureLine();
            throw new YuiError(
              ["wrong-statement", `❌${line}`],
              source.p(null, null, null, 1)
            );
          }
          return source.p(new BlockNode(statements, true), savedPos);
        }
      };
      NONTERMINALS["@TopLevel"] = new TopLevelParser();
      YuiParser = class {
        /**
         * @param {string|object} syntax syntax 名, ファイルパス, または terminals dict
         */
        constructor(syntax) {
          this.syntax = syntax;
          if (syntax != null && typeof syntax === "object") {
            this.terminals = { ...syntax };
          } else {
            this.terminals = loadSyntax(syntax);
          }
        }
        parse(sourceCode) {
          const source = new Source(sourceCode, { syntax: this.terminals });
          return source.parse("@TopLevel");
        }
      };
    }
  });

  // src/yuisyntax.js
  function getExampleFromPattern(pattern, randomSeed = null) {
    const rng = new _Rng(randomSeed);
    const originalPattern = pattern;
    for (const [re, repl] of ESC_REPLACEMENTS) {
      pattern = pattern.replace(re, repl);
    }
    let processed = "";
    while (pattern.length > 0) {
      const sPos = pattern.indexOf("(");
      if (sPos === -1) {
        processed += getExampleFromPatternInner(pattern, rng);
        break;
      }
      const ePos = pattern.indexOf(")", sPos + 1);
      if (ePos === -1) {
        throw new Error(`Unmatched parentheses in pattern: \`${originalPattern}\``);
      }
      processed += getExampleFromPatternInner(pattern.slice(0, sPos), rng);
      const inner = pattern.slice(sPos + 1, ePos);
      pattern = pattern.slice(ePos + 1);
      if (pattern.startsWith("?")) {
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
    if (processed.includes("▁")) {
      throw new Error(
        `Unprocessed escape sequences remain in \`${originalPattern}\`: \`${processed}\``
      );
    }
    return processed;
  }
  function splitHeadingChar(s, rng) {
    let headingChar;
    let remaining;
    if (s.startsWith("\\")) {
      const next = s[1];
      remaining = s.slice(2);
      switch (next) {
        case "\\":
          headingChar = "\\";
          break;
        case "s":
          headingChar = " ";
          break;
        case "t":
          headingChar = "	";
          break;
        case "n":
          headingChar = "\n";
          break;
        case "r":
          headingChar = "\r";
          break;
        case "d":
          headingChar = "1";
          break;
        case "w":
          headingChar = "a";
          break;
        default:
          headingChar = next;
          break;
      }
    } else if (s.startsWith("▁")) {
      headingChar = s.slice(0, 2);
      remaining = s.slice(2);
    } else if (s.length >= 2 && (s[1] === "️" || s[1] === "‍")) {
      headingChar = s.slice(0, 2);
      remaining = s.slice(2);
    } else {
      headingChar = s[0];
      remaining = s.slice(1);
    }
    if (remaining.startsWith("?")) {
      if (rng.nextInt(2) === 0) {
        return ["", remaining.slice(1)];
      }
      return [headingChar, remaining.slice(1)];
    }
    return [headingChar, remaining];
  }
  function getExampleFromPatternInner(pattern, rng) {
    if (pattern === "") {
      return "";
    }
    if (pattern.includes("|")) {
      const choices = pattern.split("|");
      pattern = choices[rng.nextInt(choices.length)];
      if (pattern === "") {
        return "";
      }
    }
    if (pattern.startsWith("[")) {
      const endPos = pattern.indexOf("]");
      if (pattern[endPos + 1] === "?") {
        return getExampleFromPatternInner(pattern.slice(endPos + 2), rng);
      }
      const [headingChar2] = splitHeadingChar(pattern.slice(1, endPos), rng);
      return headingChar2 + getExampleFromPatternInner(pattern.slice(endPos + 1), rng);
    }
    const [headingChar, remaining] = splitHeadingChar(pattern, rng);
    return headingChar + getExampleFromPatternInner(remaining, rng);
  }
  function loadSyntax(name = null) {
    let terminals;
    if (name == null) {
      name = "yui";
    }
    if (typeof name === "string") {
      const found = getGrammar(name);
      if (found == null) {
        throw new Error(
          `unknown syntax: ${name} (available: ${SYNTAX_NAMES.join(", ")})`
        );
      }
      terminals = { ...found };
    } else if (typeof name === "object") {
      terminals = { ...name };
    } else {
      throw new TypeError(`loadSyntax: expected string or object, got ${typeof name}`);
    }
    return _fillDefaults(terminals);
  }
  function _fillDefaults(terminals) {
    for (const [key, pattern] of Object.entries(DEFAULT_SYNTAX_JSON)) {
      if (!(key in terminals)) {
        terminals[key] = pattern;
      }
    }
    if (!("string-content-end" in terminals)) {
      const escape = terminals["string-escape"] ?? "\\\\";
      const interpolation = terminals["string-interpolation-begin"] ?? "\\{";
      const stringEnd = terminals["string-end"] ?? '\\"';
      terminals["string-content-end"] = `${escape}|${interpolation}|${stringEnd}`;
    }
    return terminals;
  }
  async function loadSyntaxFromUrl(url, opts = {}) {
    const fetchImpl = opts.fetch ?? globalThis.fetch;
    if (typeof fetchImpl !== "function") {
      throw new Error(
        "loadSyntaxFromUrl: global fetch is not available. Pass opts.fetch to provide one, or run on Node 18+."
      );
    }
    const response = await fetchImpl(url);
    if (!response.ok) {
      throw new Error(
        `loadSyntaxFromUrl: HTTP ${response.status} ${response.statusText} for ${url}`
      );
    }
    const terminals = await response.json();
    if (terminals == null || typeof terminals !== "object") {
      throw new Error(`loadSyntaxFromUrl: ${url} did not return a JSON object`);
    }
    return _fillDefaults(terminals);
  }
  function listSyntaxNames(_syntaxDir = null) {
    return [...SYNTAX_NAMES];
  }
  async function findMatchingSyntaxes(sources, _syntaxDir = null) {
    const { YuiParser: YuiParser2 } = await Promise.resolve().then(() => (init_yuiparser(), yuiparser_exports));
    const results = [];
    for (const name of SYNTAX_NAMES) {
      let errorInfo = null;
      for (const [filename, code] of Object.entries(sources)) {
        try {
          new YuiParser2(name).parse(code);
        } catch (e) {
          errorInfo = { filename, error: e };
          break;
        }
      }
      if (errorInfo == null) {
        results.push({ name, matched: true, status: "OK" });
      } else {
        const { filename, error } = errorInfo;
        results.push({
          name,
          matched: false,
          status: `FAIL (${filename}: ${error.message ?? error})`
        });
      }
    }
    return results;
  }
  function generateBnf(terminals) {
    const s = new YuiSyntax(terminals);
    const syntaxName = terminals["syntax"] ?? "?";
    function ex(name) {
      if (!s.isDefined(name)) return "";
      const val = s.forExample(name);
      if (val === "\n") return "↵";
      return val;
    }
    const E = "<expr>";
    const N = "<name>";
    const B = "<block>";
    const out = [];
    function section(title) {
      out.push("");
      out.push(`${title}:`);
    }
    function r(lhs, ...parts) {
      const tokens = parts.filter((p) => p != null && String(p) !== "").map(String);
      if (tokens.length > 0) {
        const padded = lhs.padEnd(18);
        out.push(`  ${padded} ::= ${tokens.join(" ")}`);
      }
    }
    out.push(`Grammar for '${syntaxName}'`);
    out.push("─".repeat(40));
    section("Literals");
    r("Number", "0  |  3.14");
    const sb = ex("string-begin");
    const se = ex("string-end");
    const ib = ex("string-interpolation-begin");
    const ie = ex("string-interpolation-end");
    const interp = ib ? `  (interp: ${ib}${E}${ie})` : "";
    r("String", `${sb}...${se}${interp}`);
    const ab = ex("array-begin") || "[";
    const ae = ex("array-end") || "]";
    const asep = ex("array-separator") || ",";
    r("Array", `${ab} ${E} {${asep} ${E}} ${ae}`);
    const ob = ex("object-begin") || "{";
    const oe = ex("object-end") || "}";
    const kvsep = ex("key-value-separator") || ":";
    const osep = ex("object-separator") || ",";
    r("Object", `${ob} "key"${kvsep}${E} {${osep} "key"${kvsep}${E}} ${oe}`);
    const nl = ex("null");
    if (nl) r("Null", nl);
    const bt = ex("boolean-true");
    const bf = ex("boolean-false");
    if (bt || bf) {
      r("Boolean", bt || "?", "|", bf || "?");
    }
    const nb = ex("extra-name-begin");
    const ne = ex("extra-name-end");
    if (nb) {
      r("Name", `${nb}...${ne}  |  letter...`);
    } else {
      r("Name", "letter...");
    }
    section("Expressions");
    const gb = ex("grouping-begin");
    const ge = ex("grouping-end");
    if (gb) r("Grouping", `${gb} ${E} ${ge}`);
    if (ex("length-begin")) {
      r("Length", ex("length-begin") + E + ex("length-end"));
    } else if (ex("unary-length")) {
      r("Length", ex("unary-length") + " " + E);
    } else if (ex("property-accessor") && ex("property-length")) {
      r("Length", `${E}${ex("property-accessor")}${ex("property-length")}`);
    }
    if (ex("unary-minus")) {
      r("Minus", ex("unary-minus") + E);
    }
    const faB = ex("funcapp-args-begin");
    const faE = ex("funcapp-args-end");
    const faSep = ex("funcapp-separator") || ",";
    if (faB) {
      r("FuncApp", `${E}${faB}${E} {${faSep} ${E}}${faE}`);
    }
    const aiB = ex("array-indexer-suffix") || "[";
    const aiE = ex("array-indexer-end") || "]";
    r("Index", `${E}${aiB}${E}${aiE}`);
    const pa = ex("property-accessor");
    if (pa) {
      const props = ["property-length", "property-type"].map((k) => ex(k)).filter((v) => v);
      if (props.length > 0) {
        r("Property", `${E}${pa}(${props.join(" | ")})`);
      }
    }
    const arith = ["+", "-", "*", "/", "%"].map((op) => [op, ex(`binary${op}`)]).filter(([, t]) => t);
    if (arith.length > 0) {
      r("Arithmetic", arith.map(([, t]) => `${E} ${t} ${E}`).join(" | "));
    }
    const compOps = ["==", "!=", "<", "<=", ">", ">=", "in", "notin"].map((op) => [op, ex(`binary${op}`)]).filter(([, t]) => t);
    if (compOps.length > 0) {
      r("Comparison", compOps.map(([, t]) => `${E} ${t} ${E}`).join(" | "));
    }
    section("Statements");
    r(
      "Assignment",
      ex("assignment-begin"),
      E,
      ex("assignment-infix"),
      E,
      ex("assignment-end")
    );
    r(
      "Increment",
      ex("increment-begin"),
      E,
      ex("increment-infix"),
      ex("increment-end")
    );
    r(
      "Decrement",
      ex("decrement-begin"),
      E,
      ex("decrement-infix"),
      ex("decrement-end")
    );
    r(
      "Append",
      ex("append-begin"),
      E,
      ex("append-infix"),
      E,
      ex("append-end")
    );
    if (ex("break")) r("Break", ex("break"));
    if (ex("continue")) r("Continue", ex("continue"));
    if (ex("pass")) r("Pass", ex("pass"));
    r("Return", ex("return-begin"), E, ex("return-end"));
    if (ex("return-none")) {
      r("Return (void)", ex("return-none"));
    }
    r("Print", ex("print-begin"), E, ex("print-end"));
    r(
      "Repeat",
      ex("repeat-begin"),
      E,
      ex("repeat-times"),
      ex("repeat-block"),
      B,
      ex("repeat-end")
    );
    const ifB = ex("if-begin");
    const ifCb = ex("if-condition-begin");
    const ifCe = ex("if-condition-end");
    const ifThen = ex("if-then");
    const ifElse = ex("if-else");
    const ifEnd = ex("if-end");
    const ifInfixOps = ["==", "!=", "<", "<=", ">", ">=", "in", "notin"].map((op) => [op, ex(`if-infix${op}`)]).filter(([, t]) => t);
    const ifSuffixOps = ["!=", "<", "<=", ">", ">=", "in", "notin", "=="].map((op) => ex(`if-suffix${op}`)).filter((t) => t);
    if (ifInfixOps.length > 0) {
      const opAlts = ifInfixOps.map(([, t]) => `${E} ${t} ${E}`).join(" | ");
      r(
        "If",
        ifB,
        ifCb,
        `(${opAlts})`,
        ifCe,
        ifThen,
        B,
        ifElse ? `[ ${ifElse} ${B} ]` : "",
        ifEnd
      );
    } else {
      const infixWord = ex("if-infix");
      const suffixStr = ifSuffixOps.length > 0 ? `[ ${ifSuffixOps.slice(0, 3).join(" | ")}... ]` : "";
      r(
        "If",
        ifB,
        ifCb,
        E,
        infixWord,
        E,
        suffixStr,
        ifCe,
        ifThen,
        B,
        ifElse ? `[ ${ifElse} ${B} ]` : "",
        ifEnd
      );
    }
    const fdB = ex("funcdef-begin");
    const fdNb = ex("funcdef-name-begin");
    const fdNe = ex("funcdef-name-end");
    const fdNoarg = ex("funcdef-noarg");
    const fdAb = ex("funcdef-args-begin");
    const fdAe = ex("funcdef-args-end");
    const fdAsep = ex("funcdef-arg-separator");
    const fdBlk = ex("funcdef-block");
    const fdEnd = ex("funcdef-end");
    const argsPart = fdNoarg ? `( ${fdNoarg}  |  ${fdAb} ${N} {${fdAsep} ${N}} ${fdAe} )` : `${fdAb} ${N} {${fdAsep} ${N}} ${fdAe}`;
    r("FuncDef", fdB, fdNb, N, fdNe, argsPart, fdBlk, B, fdEnd);
    if (s.isDefined("assert-begin")) {
      r("Assert", ex("assert-begin"), E, ex("assert-infix"), E, ex("assert-end"));
    }
    if (s.isDefined("import-standard")) {
      r("Import", ex("import-standard"));
    }
    section("Blocks");
    const blkB = ex("block-begin");
    const blkE = ex("block-end");
    if (blkB && blkE) {
      r("Block", blkB, "<stmt>...", blkE);
    } else if (blkB) {
      r("Block", blkB, "<stmt>...", "(indent-delimited)");
    } else {
      r("Block", "<stmt>...", "(indent-delimited)");
    }
    r("TopLevel", "<stmt>...");
    section("Comments");
    if (s.isDefined("line-comment-begin")) {
      r("LineComment", ex("line-comment-begin") + " ...");
    }
    if (s.isDefined("comment-begin") && s.isDefined("comment-end")) {
      r("BlockComment", ex("comment-begin") + " ... " + ex("comment-end"));
    }
    return out.join("\n");
  }
  var _Rng, ESC_REPLACEMENTS, ESC_RESTORE, DEFAULT_SYNTAX_JSON, YuiSyntax;
  var init_yuisyntax = __esm({
    "src/yuisyntax.js"() {
      init_yuigrammars();
      _Rng = class {
        constructor(seed) {
          this.seed = seed == null ? null : seed >>> 0;
        }
        /** [0, n) の整数を返す。seed が null なら常に 0 (決定的フォールバック)。 */
        nextInt(n) {
          if (this.seed == null) {
            return 0;
          }
          let t = this.seed = this.seed + 1831565813 >>> 0;
          t = Math.imul(t ^ t >>> 15, t | 1);
          t ^= t + Math.imul(t ^ t >>> 7, t | 61);
          const r = ((t ^ t >>> 14) >>> 0) / 4294967296;
          return Math.floor(r * n);
        }
      };
      ESC_REPLACEMENTS = [
        [/\\\|/g, "▁｜"],
        [/\\\[/g, "▁［"],
        [/\\\]/g, "▁］"],
        [/\\\(/g, "▁（"],
        [/\\\)/g, "▁）"],
        [/\\\*/g, "▁＊"],
        [/\\\?/g, "▁？"],
        [/\\\+/g, "▁＋"],
        // Python 側では `+` を消し `*` を `?` に変える (ループは 0 or 1 回扱い)
        [/\+/g, ""],
        [/\*/g, "?"]
      ];
      ESC_RESTORE = [
        ["▁｜", "|"],
        ["▁［", "["],
        ["▁］", "]"],
        ["▁（", "("],
        ["▁）", ")"],
        ["▁？", "?"],
        ["▁＋", "+"],
        ["▁＊", "*"]
      ];
      DEFAULT_SYNTAX_JSON = {
        "whitespace": "[ \\t\\r　]",
        "whitespaces": "[ \\t\\r　]+",
        "linefeed": "[\\n]",
        "line-comment-begin": "[#＃]",
        "number-first-char": "[0-9]",
        "number-chars": "[0-9]*",
        "number-dot-char": "[\\.][0-9]",
        "name-first-char": "[A-Za-z_]",
        "name-chars": "[A-Za-z0-9_]*",
        "string-begin": '"',
        "string-end": '"',
        "string-escape": "\\\\",
        "string-interpolation-begin": "\\{",
        "string-interpolation-end": "\\}",
        "grouping-begin": "\\(",
        "grouping-end": "\\)",
        "array-begin": "\\[",
        "array-end": "\\]",
        "array-separator": ",",
        "object-begin": "\\{",
        "object-end": "\\}",
        "object-separator": ",",
        "key-value-separator": ":",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "unary-minus": "-",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": ",",
        "unary-inspect": "👀",
        "catch-begin": "🧤",
        "catch-end": "🧤",
        "print-begin": "",
        "print-end": "",
        "assert-begin": ">>>\\s+",
        "assert-infix": "[\\n]",
        "assert-end": ""
      };
      YuiSyntax = class {
        constructor(syntaxJson) {
          if (syntaxJson == null || typeof syntaxJson !== "object") {
            throw new TypeError("Terminals must be an object");
          }
          this.terminals = { ...syntaxJson };
          this.randomSeed = null;
        }
        isDefined(terminal) {
          const v = this.terminals[terminal];
          if (v == null) return false;
          if (typeof v === "string") return v !== "";
          if (v instanceof RegExp) return v.source !== "";
          return true;
        }
        updateSyntax(updates) {
          Object.assign(this.terminals, updates);
        }
        /** 終端記号の元パターン文字列を返す (コンパイル済み RegExp なら .source)。未定義は ''。 */
        get(terminal) {
          const pattern = this.terminals[terminal];
          if (pattern == null) return "";
          if (typeof pattern === "string") return pattern;
          if (pattern instanceof RegExp) return pattern.source;
          return "";
        }
        /**
         * sticky フラグ付き RegExp を返し、内部にキャッシュする。
         * 未定義時は ifUndefined (文字列) をコンパイルして返す。
         */
        getPattern(terminal, ifUndefined = "") {
          let pattern = this.terminals[terminal];
          if (pattern == null) {
            pattern = ifUndefined;
          }
          if (typeof pattern === "string") {
            let compiled;
            try {
              compiled = new RegExp(pattern, "y");
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
            return "";
          }
          let pattern = this.terminals[terminal];
          if (pattern instanceof RegExp) {
            pattern = pattern.source;
          }
          return getExampleFromPattern(pattern, this.randomSeed);
        }
      };
    }
  });

  // src/index.js
  var index_exports = {};
  __export(index_exports, {
    ASTNode: () => ASTNode,
    AppendNode: () => AppendNode,
    ArrayLenNode: () => ArrayLenNode,
    ArrayNode: () => ArrayNode,
    ArrayType: () => ArrayType,
    AssertNode: () => AssertNode,
    AssignmentNode: () => AssignmentNode,
    BinaryNode: () => BinaryNode,
    BlockNode: () => BlockNode,
    BoolType: () => BoolType,
    BreakNode: () => BreakNode,
    CatchNode: () => CatchNode,
    CodingVisitor: () => CodingVisitor,
    ConstNode: () => ConstNode,
    DEFAULT_SYNTAX_JSON: () => DEFAULT_SYNTAX_JSON,
    DecrementNode: () => DecrementNode,
    ERROR_MESSAGES: () => ERROR_MESSAGES,
    ExpressionNode: () => ExpressionNode,
    FloatType: () => FloatType,
    FuncAppNode: () => FuncAppNode,
    FuncDefNode: () => FuncDefNode,
    GRAMMARS: () => GRAMMARS,
    GetIndexNode: () => GetIndexNode,
    IfNode: () => IfNode,
    ImportNode: () => ImportNode,
    IncrementNode: () => IncrementNode,
    IntType: () => IntType,
    LocalFunction: () => LocalFunction,
    MinusNode: () => MinusNode,
    NameNode: () => NameNode,
    NativeFunction: () => NativeFunction,
    NullType: () => NullType,
    NumberNode: () => NumberNode,
    NumberType: () => NumberType,
    OPERATORS: () => OPERATORS,
    ObjectNode: () => ObjectNode,
    ObjectType: () => ObjectType,
    PassNode: () => PassNode,
    PrintExpressionNode: () => PrintExpressionNode,
    RepeatNode: () => RepeatNode,
    ReturnNode: () => ReturnNode,
    SYNTAX_NAMES: () => SYNTAX_NAMES,
    Source: () => Source,
    SourceNode: () => SourceNode,
    StatementNode: () => StatementNode,
    StringNode: () => StringNode,
    StringType: () => StringType,
    VERSION: () => VERSION,
    YuiArrayType: () => YuiArrayType,
    YuiBooleanType: () => YuiBooleanType,
    YuiBreakException: () => YuiBreakException,
    YuiError: () => YuiError,
    YuiExample: () => YuiExample,
    YuiFloatType: () => YuiFloatType,
    YuiFunction: () => YuiFunction,
    YuiIntType: () => YuiIntType,
    YuiNullType: () => YuiNullType,
    YuiNumberType: () => YuiNumberType,
    YuiObjectType: () => YuiObjectType,
    YuiParser: () => YuiParser,
    YuiReturnException: () => YuiReturnException,
    YuiRuntime: () => YuiRuntime,
    YuiStringType: () => YuiStringType,
    YuiSyntax: () => YuiSyntax,
    YuiType: () => YuiType,
    YuiValue: () => YuiValue,
    _node: () => _node,
    convert: () => convert,
    findMatchingSyntaxes: () => findMatchingSyntaxes,
    formatMessages: () => formatMessages,
    generateBnf: () => generateBnf,
    getAllExamples: () => getAllExamples,
    getGrammar: () => getGrammar,
    getSamples: () => getSamples,
    getTestExamples: () => getTestExamples,
    isVerbose: () => isVerbose,
    listSyntaxNames: () => listSyntaxNames,
    loadSyntax: () => loadSyntax,
    loadSyntaxFromUrl: () => loadSyntaxFromUrl,
    normalizeMessages: () => normalizeMessages,
    run: () => run,
    setVerbose: () => setVerbose,
    standardLib: () => standardLib,
    types: () => types
  });
  init_yuitypes();
  init_yuierror();
  init_yuiast();
  init_yuisyntax();
  init_yuiparser();

  // src/yuicoding.js
  init_yuiast();
  init_yuisyntax();

  // src/yuistdlib.js
  init_yuitypes();
  function standardLib(modules) {
    function checkNumberOfArgs(args, expected) {
      if (expected === -1) {
        if (args.length < 1) {
          throw new YuiError(["mismatch-argument", `❌${args.length}`, "✅>0"]);
        }
        return;
      }
      if (args.length !== expected) {
        const last = args.length > 0 ? args[args.length - 1] : null;
        throw new YuiError(
          ["mismatch-argument", `✅${expected}`, `❌${args.length}`],
          last
        );
      }
    }
    function arrayToVarargs(args) {
      if (args.length === 1 && args[0] instanceof YuiValue && types.is_array(args[0])) {
        return args[0].array;
      }
      return args;
    }
    function hasFloatOrRaise(args) {
      for (const arg of args) {
        NumberType.match_or_raise(arg);
        if (types.is_float(arg)) return true;
      }
      return false;
    }
    function yuiAbs(...args) {
      checkNumberOfArgs(args, 1);
      NumberType.match_or_raise(args[0]);
      const value = types.unbox(args[0]);
      return new YuiValue(Math.abs(value));
    }
    modules.push(["📏|絶対値|abs", yuiAbs]);
    function yuiSqrt(...args) {
      checkNumberOfArgs(args, 1);
      NumberType.match_or_raise(args[0]);
      const value = types.unbox(args[0]);
      if (value < 0) {
        throw new YuiError(["not-negative-number", `❌${value}`, "✅>=0"]);
      }
      return new YuiValue(Math.sqrt(value), FloatType);
    }
    modules.push(["√|平方根|sqrt", yuiSqrt]);
    function yuiRandom(...args) {
      checkNumberOfArgs(args, 0);
      return new YuiValue(Math.random());
    }
    modules.push(["🎲|乱数|random", yuiRandom]);
    function yuiSum(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const isFloat = hasFloatOrRaise(args);
      let total = types.unbox(args[0]);
      if (isFloat) total = Number(total);
      for (let i = 1; i < args.length; i++) {
        total += types.unbox(args[i]);
      }
      return new YuiValue(total);
    }
    modules.push(["🧮|和|sum", yuiSum]);
    function yuiSub(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      hasFloatOrRaise(args);
      let total = types.unbox(args[0]);
      for (let i = 1; i < args.length; i++) {
        total -= types.unbox(args[i]);
      }
      return new YuiValue(total);
    }
    modules.push(["⛓️‍💥|差|diff", yuiSub]);
    function yuiProduct(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const isFloat = hasFloatOrRaise(args);
      let total = types.unbox(args[0]);
      if (isFloat) total = Number(total);
      for (let i = 1; i < args.length; i++) {
        total *= types.unbox(args[i]);
      }
      return new YuiValue(total);
    }
    modules.push(["💰|積|product", yuiProduct]);
    function yuiDiv(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const isFloat = hasFloatOrRaise(args);
      let total = types.unbox(args[0]);
      if (isFloat) {
        total = Number(total);
        for (let i = 1; i < args.length; i++) {
          const d = Number(types.unbox(args[i]));
          if (d === 0) {
            throw new YuiError(["division-by-zero", `❌${d}`], args[i]);
          }
          total /= d;
        }
      } else {
        for (let i = 1; i < args.length; i++) {
          const d = types.unbox(args[i]);
          if (d === 0) {
            throw new YuiError(["division-by-zero", `❌${d}`], args[i]);
          }
          total = Math.floor(total / d);
        }
      }
      return new YuiValue(total);
    }
    modules.push(["✂️|商|quotient", yuiDiv]);
    function yuiMod(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const isFloat = hasFloatOrRaise(args);
      let total = types.unbox(args[0]);
      if (isFloat) total = Number(total);
      for (let i = 1; i < args.length; i++) {
        const d = types.unbox(args[i]);
        if (d === 0) {
          throw new YuiError(["division-by-zero", `❌${d}`], args[i]);
        }
        total = (total % d + d) % d;
      }
      return new YuiValue(total);
    }
    modules.push(["🍕|剰余|remainder", yuiMod]);
    function yuiMax(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const values = args.map((a) => types.unbox(a));
      return new YuiValue(Math.max(...values));
    }
    modules.push(["👑|最大値|max", yuiMax]);
    function yuiMin(...args) {
      checkNumberOfArgs(args, -1);
      args = arrayToVarargs(args);
      const values = args.map((a) => types.unbox(a));
      return new YuiValue(Math.min(...values));
    }
    modules.push(["🐜|最小値|min", yuiMin]);
    function yuiIsBool(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_bool(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_BOOLEAN}❓|ブール判定|isbool`, yuiIsBool]);
    function yuiIsInt(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_int(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_INT}❓|整数判定|isint`, yuiIsInt]);
    function yuiIsFloat(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_float(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_FLOAT}❓|小数判定|isfloat`, yuiIsFloat]);
    function yuiIsString(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_string(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_STRING}❓|文字列判定|isstring`, yuiIsString]);
    function yuiIsArray(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_array(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_ARRAY}❓|配列判定|isarray`, yuiIsArray]);
    function yuiIsObject(...args) {
      checkNumberOfArgs(args, 1);
      return types.is_object(args[0]) ? YuiValue.TrueValue : YuiValue.FalseValue;
    }
    modules.push([`${TY_OBJECT}❓|オブジェクト判定|isobject`, yuiIsObject]);
    function yuiToint(...args) {
      checkNumberOfArgs(args, 1);
      if (types.is_int(args[0])) return args[0];
      const unboxed = types.unbox(args[0]);
      if (unboxed === null || unboxed === void 0) return new YuiValue(0);
      try {
        if (types.is_array(args[0])) {
          const elements = args[0].array;
          return new YuiValue(IntType.to_native(elements));
        }
        const f = Number(unboxed);
        if (!Number.isFinite(f)) {
          throw new Error(`cannot convert ${types.format_json(unboxed)} to number`);
        }
        return new YuiValue(Math.trunc(f));
      } catch (e) {
        const msg = e && e.message ? e.message : String(e);
        throw new YuiError(["int-conversion", `❌${unboxed}`, `🔥${msg}`]);
      }
    }
    modules.push([`${TY_INT}|整数化|toint`, yuiToint]);
    function yuiTofloat(...args) {
      checkNumberOfArgs(args, 1);
      if (types.is_float(args[0])) return args[0];
      const unboxed = types.unbox(args[0]);
      if (unboxed === null || unboxed === void 0) return new YuiValue(0);
      try {
        if (types.is_array(args[0])) {
          const elements = args[0].array;
          return new YuiValue(FloatType.to_native(elements));
        }
        const f = Number(unboxed);
        if (!Number.isFinite(f)) {
          throw new Error(`cannot convert ${types.format_json(unboxed)} to float`);
        }
        return new YuiValue(f);
      } catch (e) {
        const msg = e && e.message ? e.message : String(e);
        throw new YuiError(["float-conversion", `❌${unboxed}`, `🔥${msg}`]);
      }
    }
    modules.push([`${TY_FLOAT}|小数化|tofloat`, yuiTofloat]);
    function yuiTostring(...args) {
      checkNumberOfArgs(args, 1);
      if (types.is_string(args[0])) return args[0];
      if (types.is_float(args[0])) {
        const v = types.unbox(args[0]);
        return new YuiValue(v.toFixed(6));
      }
      return new YuiValue(args[0].toString());
    }
    modules.push([`${TY_STRING}|文字列化|tostring`, yuiTostring]);
    function yuiToarray(...args) {
      checkNumberOfArgs(args, 1);
      const value = args[0];
      if (types.is_object(value)) {
        return new YuiValue(Object.keys(value.native));
      }
      return new YuiValue(value.array);
    }
    modules.push([`${TY_ARRAY}|配列化|toarray`, yuiToarray]);
    return ["emoji|ja|en", modules];
  }

  // src/yuicoding.js
  var _NO_SEG = /* @__PURE__ */ new Set(["string-end", "string-interpolation-end", "extra-name-end"]);
  var _NO_SPACE_DEFAULT = " \n([{";
  var _NO_WORDSEG_LEADING = `,()[]{}:;"'.`;
  var CodingVisitor = class extends YuiSyntax {
    /**
     * @param {string|object} syntaxJson — 構文名 (例 "yui") または terminals オブジェクト
     * @param {string|null} functionLanguage — 'emoji'/'ja'/'en' または null
     */
    constructor(syntaxJson, functionLanguage = null) {
      if (typeof syntaxJson === "string") {
        syntaxJson = loadSyntax(syntaxJson);
      }
      super(syntaxJson);
      this.buffer = [];
      this.indentString = "   ";
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
      const targets = targetsStr.toLowerCase().split("|");
      const index = targets.indexOf(functionLanguage);
      if (index < 0) {
        throw new Error(
          `Name '${functionLanguage}' not found in standard library targets: ${targets}`
        );
      }
      this.funcnamemap = {};
      for (const [namesStr, _fn] of modules) {
        const names = namesStr.split("|");
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
    emit(node, indentString = "   ", randomSeed = null) {
      this.buffer = [];
      this.indentLevel = 0;
      this.indentString = indentString;
      this.justLinefeeded = true;
      this.randomSeed = randomSeed;
      if (!(node instanceof StatementNode) && this.isDefined("print-begin")) {
        new PrintExpressionNode(node).visit(this);
      } else {
        node.visit(this);
      }
      return this.buffer.join("");
    }
    lastChar() {
      if (this.buffer.length === 0) return "\n";
      const tail = this.buffer[this.buffer.length - 1];
      return tail[tail.length - 1];
    }
    linefeed() {
      if (!this.justLinefeeded) {
        if (this.indentString) {
          this.buffer.push("\n" + this.indentString.repeat(this.indentLevel));
        } else {
          this.buffer.push(" ");
        }
        this.justLinefeeded = true;
      }
    }
    string(text) {
      if (text.includes("\n")) {
        const lines = text.split("\n");
        for (let i = 0; i < lines.length - 1; i++) {
          this.string(lines[i]);
          this.linefeed();
        }
        this.string(lines[lines.length - 1]);
        return;
      }
      if (text.length === 0) return;
      if (text === " " && this.lastChar() === " ") {
        return;
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
      if (this.isDefined("word-segmenter")) {
        if (!noSpaceIfLastChars.includes(this.lastChar())) {
          this.string(" ");
        }
      } else if (this.randomSeed != null) {
        if (!noSpaceIfLastChars.includes(this.lastChar())) {
          if (Math.random() < 0.5) {
            this.string(" ");
          }
        }
      }
    }
    terminal(terminal, _ifUndefined = null, linefeedBefore = false) {
      if (terminal === "linefeed") {
        this.linefeed();
        return;
      }
      if (!this.isDefined(terminal)) return;
      const token = this.forExample(terminal);
      if (token === "") return;
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
      if (this.isDefined("comment-begin") && this.isDefined("comment-end")) {
        this.terminal("comment-begin");
        this.string(` ${comment}`);
        this.terminal("comment-end");
      } else if (this.isDefined("line-comment-begin")) {
        for (const line of comment.split(/\r?\n/)) {
          this.terminal("line-comment-begin");
          this.string(` ${line}`);
          this.linefeed();
        }
      }
    }
    expression(node, grouping = null) {
      this.wordSegment();
      if (grouping && this.isDefined("grouping-begin") && this.isDefined("grouping-end")) {
        this.terminal("grouping-begin");
        node.visit(this);
        this.terminal("grouping-end");
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
    }
    escape(text) {
      return text.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
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
        this.terminal("null");
      } else if (node.native_value === true) {
        this.terminal("boolean-true");
      } else {
        this.terminal("boolean-false");
      }
    }
    visitNumberNode(node) {
      this.terminal("number-begin");
      const v = node.native_value;
      if (typeof v === "number" && !Number.isInteger(v)) {
        this.string(v.toFixed(6));
      } else {
        this.string(String(v));
      }
      this.terminal("number-end");
    }
    visitStringNode(node) {
      this.terminal("string-begin");
      if (typeof node.contents === "string") {
        this.string(this.escape(node.contents));
      } else {
        for (const content of node.contents) {
          if (typeof content === "string") {
            this.string(this.escape(content));
          } else {
            this.terminal("string-interpolation-begin");
            content.visit(this);
            this.terminal("string-interpolation-end");
          }
        }
      }
      this.terminal("string-end");
    }
    visitNameNode(node) {
      this.terminal("name-begin");
      this.string(node.name);
      this.terminal("name-end");
    }
    visitArrayNode(node) {
      const savedBuffer = this.buffer;
      this.buffer = [];
      this.terminal("array-begin");
      node.elements.forEach((el, i) => {
        if (i > 0) this.terminal("array-separator");
        this.expression(el);
      });
      this.terminal("array-end");
      const content = this.buffer.join("");
      this.buffer = savedBuffer;
      if (content.length <= 80 && !content.includes("\n")) {
        this.string(content);
        return;
      }
      this.terminal("array-begin");
      this.indentLevel += 1;
      this.linefeed();
      node.elements.forEach((el, i) => {
        if (i > 0) {
          this.terminal("array-separator");
          this.linefeed();
        }
        this.expression(el);
      });
      this.indentLevel -= 1;
      this.linefeed();
      this.terminal("array-end");
    }
    visitObjectNode(node) {
      const savedBuffer = this.buffer;
      this.buffer = [];
      this.terminal("object-begin");
      for (let i = 0; i < node.elements.length; i += 2) {
        if (i > 0) this.terminal("object-separator");
        const keyNode = node.elements[i];
        const valueNode = node.elements[i + 1];
        this.expression(keyNode);
        this.terminal("key-value-separator");
        this.expression(valueNode);
      }
      this.terminal("object-end");
      const content = this.buffer.join("");
      this.buffer = savedBuffer;
      if (content.length <= 80 && !content.includes("\n")) {
        this.string(content);
        return;
      }
      this.terminal("object-begin");
      this.indentLevel += 1;
      this.linefeed();
      for (let i = 0; i < node.elements.length; i += 2) {
        if (i > 0) {
          this.terminal("object-separator");
          this.linefeed();
        }
        const keyNode = node.elements[i];
        const valueNode = node.elements[i + 1];
        this.expression(keyNode);
        this.terminal("key-value-separator");
        this.expression(valueNode);
      }
      this.indentLevel -= 1;
      this.linefeed();
      this.terminal("object-end");
    }
    visitMinusNode(node) {
      if (this.isDefined("minus-begin")) {
        this.terminal("minus-begin");
        this.expression(node.element);
        this.terminal("minus-end");
      } else if (this.isDefined("unary-minus")) {
        this.terminal("unary-minus");
        node.element.visit(this);
      } else {
        this.visitASTNode(node);
      }
    }
    visitBinaryNode(node) {
      const symbol = node.operator.symbol;
      if (this.isDefined("binary-infix-prefix-begin")) {
        this.terminal(`binary-infix-prefix${symbol}`);
        this.wordSegment();
        this.expression(node.left_node);
        this.wordSegment();
        this.expression(node.right_node);
        this.terminal("binary-infix-prefix-end");
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
      if (this.isDefined("property-length")) {
        this.expression(node.element);
        this.terminal("property-length");
      } else if (this.isDefined("unary-length")) {
        this.terminal("unary-length");
        this.expression(node.element);
      } else if (this.isDefined("length-begin")) {
        this.terminal("length-begin");
        this.expression(node.element);
        this.terminal("length-end");
      }
    }
    visitGetIndexNode(node) {
      let collection = node.collection;
      let index = node.index_node;
      if (this.get("array-indexer-order") === "reversed") {
        [collection, index] = [index, collection];
      }
      this.terminal("array-indexer-begin");
      this.expression(collection);
      this.terminal("array-indexer-infix");
      this.terminal("array-indexer-suffix");
      this.expression(index);
      this.terminal("array-indexer-end");
    }
    visitFuncAppNode(node) {
      this.terminal("funcapp-begin");
      const originalName = node.name_node.name;
      const name = Object.prototype.hasOwnProperty.call(this.funcnamemap, originalName) ? this.funcnamemap[originalName] : originalName;
      this.string(name);
      if (this.isDefined("funcapp-noarg") && node.arguments.length === 0) {
        this.terminal("funcapp-noarg");
      } else {
        this.terminal("funcapp-args-begin");
        node.arguments.forEach((arg, i) => {
          if (i > 0) this.terminal("funcapp-separator");
          const grouping = arg instanceof FuncAppNode && !this.isDefined("funcapp-args-end");
          this.expression(arg, grouping);
        });
        this.terminal("funcapp-args-end");
        this.terminal("funcapp-end");
      }
    }
    visitAssignmentNode(node) {
      let variable = node.variable;
      let expression = node.expression;
      if (this.get("assignment-order") === "reversed") {
        [variable, expression] = [expression, variable];
      }
      this.terminal("assignment-begin");
      this.expression(variable);
      this.terminal("assignment-infix");
      this.expression(expression);
      this.terminal("assignment-end");
    }
    visitIncrementNode(node) {
      this.terminal("increment-begin");
      this.expression(node.variable);
      this.terminal("increment-end");
    }
    visitDecrementNode(node) {
      this.terminal("decrement-begin");
      this.expression(node.variable);
      this.terminal("decrement-end");
    }
    visitAppendNode(node) {
      let variable = node.variable;
      let expression = node.expression;
      if (this.get("assignment-order") === "reversed") {
        [variable, expression] = [expression, variable];
      }
      this.terminal("append-begin");
      this.expression(variable);
      this.terminal("append-infix");
      this.expression(expression);
      this.terminal("append-end");
    }
    visitBreakNode(_node2) {
      this.terminal("break");
    }
    visitPassNode(_node2) {
    }
    visitReturnNode(node) {
      if (node.expression instanceof ASTNode) {
        this.terminal("return-begin");
        this.expression(node.expression);
        this.terminal("return-end");
      } else {
        this.terminal("return-none");
      }
    }
    visitPrintExpressionNode(node) {
      if (node.grouping) {
        this.terminal("grouping-begin");
        this.expression(node.expression);
        this.terminal("grouping-end");
        return;
      }
      if (node.inspection) {
        this.terminal("unary-inspect");
        this.expression(node.expression);
      } else {
        this.terminal("print-begin");
        this.expression(node.expression);
        this.terminal("print-end");
      }
    }
    visitIfNode(node) {
      this.terminal("if-begin");
      this.terminal("if-condition-begin");
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
            this.terminal("if-infix");
          }
          this.expression(node.right);
          if (this.isDefined(`if-suffix${opSymbol}`)) {
            this.terminal(`if-suffix${opSymbol}`);
          } else {
            this.terminal("if-suffix");
          }
        }
      }
      this.terminal("if-condition-end");
      this.terminal("if-then");
      this.block(node.then_block);
      if (node.else_block && !(node.else_block instanceof PassNode)) {
        if (this.isDefined("if-else-if") && node.else_block instanceof IfNode) {
          this.terminal("if-else-if", null, true);
          this.block(node.else_block);
        } else {
          this.terminal("if-else", null, true);
          this.block(node.else_block);
        }
      }
      this.terminal("if-end", null, true);
    }
    visitRepeatNode(node) {
      let countNode = node.count_node;
      let blockNode = node.block_node;
      if (this.get("repeat-order") === "reversed") {
        [countNode, blockNode] = [blockNode, countNode];
      }
      this.terminal("repeat-begin");
      this.expression(countNode);
      this.terminal("repeat-times");
      this.terminal("repeat-block");
      this.block(blockNode);
      this.terminal("repeat-end", null, true);
    }
    visitFuncDefNode(node) {
      this.terminal("funcdef-begin");
      this.terminal("funcdef-name-begin");
      this.expression(node.name_node);
      this.terminal("funcdef-name-end");
      if (this.isDefined("funcdef-noarg") && node.parameters.length === 0) {
        this.terminal("funcdef-noarg");
      } else {
        this.terminal("funcdef-args-begin");
        node.parameters.forEach((param, i) => {
          if (i > 0) this.terminal("funcdef-arg-separator");
          this.expression(param);
        });
        this.terminal("funcdef-args-end");
      }
      this.terminal("funcdef-block");
      this.block(node.body);
      this.terminal("funcdef-end", null, true);
    }
    visitImportNode(_node2) {
      this.terminal("import-standard");
    }
    visitAssertNode(node) {
      let testNode = node.test;
      let referenceNode = node.reference;
      if (this.get("assert-order") === "reversed") {
        [testNode, referenceNode] = [referenceNode, testNode];
      }
      this.terminal("assert-begin");
      this.expression(testNode);
      this.terminal("assert-infix");
      this.expression(referenceNode);
      this.terminal("assert-end");
    }
    visitCatchNode(node) {
      this.terminal("catch-begin");
      this.expression(node.expression);
      this.terminal("catch-end");
    }
    visitBlockNode(node) {
      if (!node.top_level) {
        this.terminal("block-begin-prefix");
        this.terminal("block-begin");
        this.indentLevel += 1;
        this.linefeed();
      }
      if (node.statements.length === 0) {
        this.terminal("pass");
      } else {
        node.statements.forEach((statement, i) => {
          if (i > 0) this.linefeed();
          if (!(statement instanceof StatementNode) && this.isDefined("print-begin")) {
            new PrintExpressionNode(statement).visit(this);
          } else {
            statement.visit(this);
          }
          if (statement instanceof FuncDefNode) {
            this.linefeed();
          }
          if (!this.justLinefeeded) {
            this.terminal("statement-separator");
          }
          if (statement instanceof PassNode) {
            this.linefeed();
          }
          this.comment(statement.comment);
        });
      }
      if (!node.top_level) {
        this.indentLevel -= 1;
        this.justLinefeeded = false;
        this.terminal("block-end", null, true);
      }
    }
  };

  // src/yuiruntime.js
  init_yuiast();
  init_yuitypes();
  init_yuierror();
  init_yuiparser();
  function _formatSourceContext(node, prefix, marker, lineoffset, context = 3) {
    let [line, col] = node.extract();
    line += lineoffset;
    const length = node.end_pos != null && node.end_pos >= 0 ? Math.max(node.end_pos - node.pos, 3) : 3;
    const pointer = marker.repeat(Math.min(length, 16));
    const allLines = node.source.split("\n");
    const startIdx = Math.max(0, line - 1 - context);
    const lineWidth = String(line).length;
    const sep = " | ";
    const linesOut = [];
    for (let i = startIdx; i < Math.min(line, allLines.length); i++) {
      const lineno = i + 1;
      const linenoStr = String(lineno).padStart(lineWidth, " ");
      linesOut.push(`${prefix}${linenoStr}${sep}${allLines[i]}`);
    }
    const pointerIndent = " ".repeat(prefix.length + lineWidth + sep.length + col - 1);
    linesOut.push(`${pointerIndent}${pointer}`);
    return `line ${line}, column ${col}:
${linesOut.join("\n")}`;
  }
  var YuiBreakException = class extends YuiError {
    constructor(errorNode = null) {
      super(["unexpected-break"], errorNode);
      this.name = "YuiBreakException";
    }
  };
  var YuiReturnException = class extends YuiError {
    constructor(value = null, errorNode = null) {
      super(["unexpected-return"], errorNode);
      this.name = "YuiReturnException";
      this.value = value;
    }
  };
  var YuiFunction = class {
    constructor(name) {
      this.name = name;
    }
    // eslint-disable-next-line no-unused-vars
    call(_argValues, _node2, _runtime) {
      throw new Error("YuiFunction.call must be overridden");
    }
  };
  var LocalFunction = class extends YuiFunction {
    constructor(name, parameters, body) {
      super(name);
      this.parameters = parameters;
      this.body = body;
    }
    call(argValues, node, runtime) {
      runtime.pushenv();
      if (this.parameters.length !== argValues.length) {
        throw new YuiError(
          ["mismatch-argument", `✅${this.parameters.length}`, `❌${argValues.length}`],
          node
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
          runtime.popCallFrame();
          runtime.popenv();
          throw e;
        }
      }
      runtime.popCallFrame();
      return new YuiValue(Object.fromEntries(runtime.popenv()));
    }
  };
  var NativeFunction = class extends YuiFunction {
    constructor(fn, isFfi = false) {
      super(fn.name || "anonymous");
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
        throw new YuiError(["internal-error", `🔍${this.name}`, `⚠️ ${msg}`], node);
      }
    }
  };
  var YuiRuntime = class {
    constructor() {
      this.environments = [/* @__PURE__ */ new Map()];
      this.call_frames = [];
      this.filesystems = {};
      this.shouldStop = false;
      this.timeout = 0;
      this.interactive_mode = false;
      this.source = "";
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
      this.environments.push(/* @__PURE__ */ new Map());
    }
    popenv() {
      return this.environments.pop();
    }
    /** 最内 (末尾) スコープを返す。 */
    getTopEnv() {
      return this.environments.at(-1);
    }
    stringifyEnv(stack = -1, indentPrefix = "") {
      let inner;
      let LF;
      if (indentPrefix == null) {
        indentPrefix = "";
        inner = null;
        LF = "";
      } else {
        inner = indentPrefix + "  ";
        LF = "\n";
      }
      const idx = stack < 0 ? this.environments.length + stack : stack;
      const env = this.environments[idx];
      const lines = [`${indentPrefix}<${this.stringifyCallFrames(stack)}>${LF}{`];
      const entries = [...env].filter(([k]) => !k.startsWith("@"));
      entries.forEach(([key, value], i) => {
        lines.push(`${LF}${indentPrefix}  "${key}": `);
        lines.push(value && typeof value.stringify === "function" ? value.stringify(inner) : String(value));
        if (i < entries.length - 1) {
          lines.push(", ");
        }
      });
      lines.push(`${LF}${indentPrefix}}`);
      return lines.join("");
    }
    // ── エラー整形 ─────────────────────────────────────────
    formatError(error, prefix = " ", marker = "^", lineoffset = 0) {
      const isRuntime = error.runtime != null;
      let message = formatMessages(error.messages);
      if (error.errorNode) {
        const context = _formatSourceContext(error.errorNode, prefix, marker, lineoffset);
        message = `${message} ${context}`;
      }
      if (isRuntime) {
        return `[実行時エラー/RuntimeError] ${message}
[環境/Environment] ${this.stringifyEnv(-1)}
`;
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
        return "global";
      }
      const idx = stack < 0 ? this.call_frames.length + stack : stack;
      const frame = this.call_frames[idx];
      const args = frame[1].map((arg) => String(arg)).join(", ");
      return `${frame[0]}(${args})]`;
    }
    checkRecursionDepth() {
      if (this.call_frames.length > 128) {
        const last = this.call_frames[this.call_frames.length - 1];
        const args = last[1].map((arg) => String(arg)).join(", ");
        const snippet = `${last[0]}(${args})`;
        throw new YuiError(["too-many-recursion", `🔍${snippet}`], last[2]);
      }
    }
    // ── 変数更新フック (sub-class でオーバーライド可能) ────
    // eslint-disable-next-line no-unused-vars
    updateVariable(_name, _env, _pos) {
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
        console.log(`${value && value.native !== void 0 ? value.native : value}`);
        return;
      }
      const [lineno, , snippet] = node.extract();
      if (this.interactive_mode && this.isInTheTopLevel()) {
        console.log(`${value.stringify("", true)}`);
      } else if (this.isInTheTopLevel()) {
        console.log(`>>> ${node} #📍${lineno}
${value.stringify("", true)}`);
      } else {
        const padded = String(node).padEnd(36, " ");
        console.log(`${String(lineno).padStart(4, " ")}: 👀${padded} → ${value.stringify("", true)}`);
      }
      void snippet;
    }
    // ── 実行制御 ───────────────────────────────────────────
    start(timeout = 30) {
      this.shouldStop = false;
      this.timeout = timeout;
      this.startTime = Date.now() / 1e3;
    }
    checkExecution(node) {
      if (this.shouldStop) {
        throw new YuiError(["interruptted"], node);
      }
      if (this.timeout > 0 && Date.now() / 1e3 - this.startTime > this.timeout) {
        throw new YuiError(
          ["runtime-timeout", `❌${this.timeout}[sec]`, `✅${this.timeout}[sec]`],
          node
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
    exec(source, syntax = "yui", opts = {}) {
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
      const snippet = String(node);
      if (snippet.includes(".") || typeof v === "number" && !Number.isInteger(v)) {
        return new YuiValue(v, FloatType);
      }
      return new YuiValue(v);
    }
    visitStringNode(node) {
      if (typeof node.contents === "string") {
        return new YuiValue(node.contents);
      }
      const parts = [];
      for (const content of node.contents) {
        if (typeof content === "string") {
          parts.push(content);
        } else {
          const value = content.visit(this);
          parts.push(`${types.unbox(value)}`);
        }
      }
      return new YuiValue(parts.join(""));
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
        throw new YuiError(["undefined-variable", `❌${node.name}`], node);
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
        throw new YuiError(["unsupported-operator", `🔍${node.operator.symbol}`], node);
      }
      const left = node.left_node.visit(this);
      const right = node.right_node.visit(this);
      const result = node.operator.evaluate(left, right, node);
      if (typeof result === "number" && (types.is_float(left) || types.is_float(right))) {
        return new YuiValue(result, FloatType);
      }
      return types.box(result);
    }
    visitFuncAppNode(node) {
      const name = `@${node.name_node.name}`;
      if (!this.hasenv(name)) {
        throw new YuiError(
          ["undefined-function", `❌${node.name_node.name}`],
          node.name_node
        );
      }
      const fn = this.getenv(name);
      if (!(fn instanceof YuiFunction)) {
        throw new YuiError(
          ["type-error", "✅<function>", `❌${fn}`],
          node.name_node
        );
      }
      const argValues = node.arguments.map((argNode) => argNode.visit(this));
      if (node.snippet === "") {
        const argsStr = argValues.map((v) => String(v)).join(", ");
        node.snippet = `${node.name_node}(${argsStr})`;
      }
      return fn.call(argValues, node, this);
    }
    // ──────────────────────────────────────────────────────────
    // 代入・変更ノード
    // ──────────────────────────────────────────────────────────
    visitAssignmentNode(node) {
      if (typeof node.variable.update !== "function") {
        throw new YuiError(
          ["expected-variable", `❌${node.variable}`],
          node.variable
        );
      }
      const value = node.expression.visit(this);
      node.variable.update(value, this);
      return value;
    }
    visitIncrementNode(node) {
      if (typeof node.variable.update !== "function") {
        throw new YuiError(
          ["expected-variable", `❌${node.variable}`],
          node.variable
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
      if (typeof node.variable.update !== "function") {
        throw new YuiError(
          ["expected-variable", `❌${node.variable}`],
          node.variable
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
        for (const charCode of value.array) {
          array.append(new YuiValue(charCode), node);
        }
      } else if (types.is_object(array) && types.is_string(value)) {
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
    visitPassNode(_node2) {
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
        this.printValue(value);
      } else if (node.inspection || this.isInTheTopLevel() && !node.grouping) {
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
      }
      throw new YuiError(
        ["assertion-failed", `🔍${node.test}`, `❌${tested}`, `✅${referenceValue}`],
        node
      );
    }
    visitImportNode(node) {
      const modules = [];
      const isNull = node.module_name == null || node.module_name instanceof ConstNode && node.module_name.native_value === null;
      if (isNull) {
        standardLib(modules);
      }
      for (const [names, fn] of modules) {
        for (const name of names.split("|")) {
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
  };

  // src/yuiexample.js
  init_yuiast();
  function _stripAsserts(block) {
    const filtered = [];
    for (const stmt of block.statements) {
      if (stmt instanceof AssertNode) {
        const prev = filtered[filtered.length - 1];
        if (prev instanceof PassNode && prev.comment && (prev.comment.toLowerCase().startsWith("test") || prev.comment.startsWith("テスト"))) {
          filtered.pop();
        }
      } else {
        filtered.push(stmt);
      }
    }
    return new BlockNode(filtered, block.top_level);
  }
  var YuiExample = class {
    constructor(name, description, astNode, kind = "both") {
      this.name = name;
      this.description = description;
      this.ast_node = astNode;
      this.kind = kind;
    }
    /**
     * AST を指定された構文のソースコードとして出力する。
     * @param {string} syntax — 'yui' / 'pylike' / 'emoji' など
     * @param {object} options
     * @param {boolean} [options.includeAsserts=true] — false なら AssertNode を落とす
     * @param {number|null} [options.randomSeed=null]
     * @param {string|null} [options.indentString=null] — null なら CodingVisitor のデフォルト
     * @param {string|null} [options.functionLanguage=null]
     */
    generate(syntax = "yui", options = {}) {
      const {
        includeAsserts = true,
        randomSeed = null,
        indentString = null,
        functionLanguage = null
      } = options;
      const node = includeAsserts ? this.ast_node : _stripAsserts(this.ast_node);
      const visitor = new CodingVisitor(syntax, functionLanguage);
      if (indentString != null) {
        return visitor.emit(node, indentString, randomSeed);
      }
      return visitor.emit(node, void 0, randomSeed);
    }
  };
  function exampleHelloWorld() {
    const statements = [
      new PassNode('"Hello, world!" と表示する'),
      new PrintExpressionNode(new StringNode("Hello, world!"))
    ];
    return new YuiExample(
      "hello_world",
      "'Hello, world!' を表示する",
      new BlockNode(statements, true),
      "sample"
    );
  }
  function exampleVariables() {
    const statements = [
      new PassNode("変数 x と y を定義する"),
      new AssignmentNode(new NameNode("x"), new NumberNode(1)),
      new AssignmentNode(new NameNode("y"), new MinusNode(new NumberNode(2))),
      new PassNode("x を1増やす"),
      new IncrementNode(new NameNode("x")),
      new PassNode("y を1減らす"),
      new DecrementNode(new NameNode("y")),
      new PassNode("テスト: x が 2、y が -3"),
      new AssertNode(new NameNode("x"), new NumberNode(2)),
      new AssertNode(new NameNode("y"), new MinusNode(new NumberNode(3)))
    ];
    return new YuiExample(
      "variables",
      "変数の定義とインクリメント/デクリメント",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleLoop() {
    const statements = [
      new PassNode("10回ループして5回目でブレイク"),
      new AssignmentNode(new NameNode("count"), new NumberNode(0)),
      new RepeatNode(
        new NumberNode(10),
        new BlockNode([
          new IncrementNode(new NameNode("count")),
          new IfNode(
            new NameNode("count"),
            "==",
            new NumberNode(5),
            new BlockNode(new BreakNode())
          )
        ])
      ),
      new PassNode("テスト: count が 5"),
      new AssertNode(new NameNode("count"), new NumberNode(5))
    ];
    return new YuiExample(
      "loop",
      "10回ループして5回目でブレイク",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleFizzbuzz() {
    const statements = [
      new PassNode("1から100までのFizzBuzzをリストに収集する"),
      new AssignmentNode(new NameNode("result"), new ArrayNode([])),
      new AssignmentNode(new NameNode("i"), new NumberNode(0)),
      new AssignmentNode(new NameNode("fizz"), new NumberNode(0)),
      new AssignmentNode(new NameNode("buzz"), new NumberNode(0)),
      new RepeatNode(
        new NumberNode(100),
        new BlockNode([
          new IncrementNode(new NameNode("i")),
          new IncrementNode(new NameNode("fizz")),
          new IncrementNode(new NameNode("buzz")),
          new IfNode(
            new NameNode("fizz"),
            "==",
            new NumberNode(3),
            new BlockNode(
              new AssignmentNode(new NameNode("fizz"), new NumberNode(0))
            )
          ),
          new IfNode(
            new NameNode("buzz"),
            "==",
            new NumberNode(5),
            new BlockNode(
              new AssignmentNode(new NameNode("buzz"), new NumberNode(0))
            )
          ),
          new IfNode(
            new NameNode("fizz"),
            "==",
            new NumberNode(0),
            new BlockNode(
              new IfNode(
                new NameNode("buzz"),
                "==",
                new NumberNode(0),
                new BlockNode(
                  new AppendNode(
                    new NameNode("result"),
                    new StringNode("FizzBuzz")
                  )
                ),
                new BlockNode(
                  new AppendNode(new NameNode("result"), new StringNode("Fizz"))
                )
              )
            ),
            new BlockNode(
              new IfNode(
                new NameNode("buzz"),
                "==",
                new NumberNode(0),
                new BlockNode(
                  new AppendNode(new NameNode("result"), new StringNode("Buzz"))
                ),
                new BlockNode(
                  new AppendNode(new NameNode("result"), new NameNode("i"))
                )
              )
            )
          )
        ])
      ),
      new PrintExpressionNode(new NameNode("result")),
      new PassNode("テスト: 長さが100"),
      new AssertNode(
        new ArrayLenNode(new NameNode("result")),
        new NumberNode(100)
      ),
      new PassNode("テスト: Fizz、Buzz、FizzBuzz の位置を確認"),
      new AssertNode(
        new GetIndexNode(new NameNode("result"), new NumberNode(2)),
        new StringNode("Fizz")
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("result"), new NumberNode(4)),
        new StringNode("Buzz")
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("result"), new NumberNode(14)),
        new StringNode("FizzBuzz")
      )
    ];
    return new YuiExample(
      "fizzbuzz",
      "1から100までのFizzBuzzをリストに収集する",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleNestedConditionalBranches() {
    const thenBlock = new IncrementNode(new NameNode("y"));
    const elseBlock = new IncrementNode(new NameNode("z"));
    const statements = [
      new PassNode("x と y に対するネストした条件をテスト"),
      new AssignmentNode(new NameNode("x"), new NumberNode(1)),
      new AssignmentNode(new NameNode("y"), new NumberNode(2)),
      new AssignmentNode(new NameNode("z"), new NumberNode(3)),
      new PassNode("x が 0 なら y を確認して y または z を増やす"),
      new IfNode(
        new NameNode("x"),
        "==",
        new NumberNode(0),
        new BlockNode(
          new IfNode(
            new NameNode("y"),
            "==",
            new NumberNode(1),
            thenBlock,
            elseBlock
          )
        ),
        new BlockNode(
          new IfNode(
            new NameNode("y"),
            "==",
            new NumberNode(2),
            thenBlock,
            elseBlock
          )
        )
      ),
      new PassNode("テスト: y が増えて z が増えていない"),
      new AssertNode(new NameNode("y"), new NumberNode(3))
    ];
    return new YuiExample(
      "nested_conditional_branches",
      "ネストした条件分岐",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleComparisons() {
    const thenBlock = new IncrementNode(new NameNode("y"));
    const elseBlock = new IncrementNode(new NameNode("z"));
    const statements = [
      new PassNode("x に対するさまざまな比較"),
      new AssignmentNode(new NameNode("x"), new NumberNode(1)),
      new AssignmentNode(new NameNode("y"), new NumberNode(0)),
      new AssignmentNode(new NameNode("z"), new NumberNode(0)),
      new PassNode("x は 1 と等しいか？"),
      new IfNode(
        new NameNode("x"),
        "==",
        new NumberNode(1),
        thenBlock,
        elseBlock
      ),
      new PassNode("x は 1 と等しくないか？"),
      new IfNode(
        new NameNode("x"),
        "!=",
        new NumberNode(1),
        thenBlock,
        elseBlock
      ),
      new PassNode("x は 1 より小さいか？"),
      new IfNode(new NameNode("x"), "<", new NumberNode(1), thenBlock, elseBlock),
      new PassNode("x は 1 より大きいか？"),
      new IfNode(new NameNode("x"), ">", new NumberNode(1), thenBlock, elseBlock),
      new PassNode("x は 1 以下か？"),
      new IfNode(
        new NameNode("x"),
        "<=",
        new NumberNode(1),
        thenBlock,
        elseBlock
      ),
      new PassNode("x は 1 以上か？"),
      new IfNode(
        new NameNode("x"),
        ">=",
        new NumberNode(1),
        thenBlock,
        elseBlock
      ),
      new PassNode("テスト: すべての条件が正しく評価された"),
      new AssertNode(new NameNode("y"), new NumberNode(3)),
      new AssertNode(new NameNode("z"), new NumberNode(3))
    ];
    return new YuiExample(
      "comparisons",
      "比較演算",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleArray() {
    const statements = [
      new PassNode("要素 1, 2, 3 を持つ配列 A を作成する"),
      new AssignmentNode(
        new NameNode("A"),
        new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)])
      ),
      new PassNode("A の末尾に 0 を追加する"),
      new AppendNode(new NameNode("A"), new NumberNode(0)),
      new PassNode("A の最初の要素を1増やす"),
      new IncrementNode(
        new GetIndexNode(new NameNode("A"), new NumberNode(0))
      ),
      new PassNode("A に 2 があれば、最初の要素を4番目の要素に設定する"),
      new IfNode(
        new NumberNode(2),
        "in",
        new NameNode("A"),
        new AssignmentNode(
          new GetIndexNode(new NameNode("A"), new NumberNode(0)),
          new GetIndexNode(new NameNode("A"), new NumberNode(3))
        )
      ),
      new PassNode("テスト: 配列が4要素"),
      new AssertNode(
        new ArrayLenNode(new NameNode("A")),
        new NumberNode(4)
      )
    ];
    return new YuiExample(
      "array",
      "配列の作成と要素操作",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleStrings() {
    const statements = [
      new PassNode("'hello' という文字列 s を作成する"),
      new AssignmentNode(new NameNode("s"), new StringNode("hello")),
      new PassNode("s の最初の文字を 'H' に設定する"),
      new PassNode("注: 文字列は文字コードの配列です。配列と同様に操作できます。"),
      new AssignmentNode(
        new GetIndexNode(new NameNode("s"), new NumberNode(0)),
        new GetIndexNode(new StringNode("H"), 0)
      ),
      new PassNode('s に " world" を連結する'),
      new AssignmentNode(new NameNode("t"), new StringNode(" world")),
      new AssignmentNode(new NameNode("i"), new NumberNode(0)),
      new RepeatNode(
        new ArrayLenNode(new NameNode("t")),
        new BlockNode([
          new AppendNode(
            new NameNode("s"),
            new GetIndexNode(new NameNode("t"), new NameNode("i"))
          ),
          new IncrementNode(new NameNode("i"))
        ])
      ),
      new PassNode("テスト: s が 'Hello world' になっている"),
      new AssertNode(new NameNode("s"), new StringNode("Hello world"))
    ];
    return new YuiExample(
      "strings",
      "文字列の作成と操作",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleObjects() {
    const statements = [
      new PassNode("プロパティ x と y を持つオブジェクト O を作成する"),
      new AssignmentNode(
        new NameNode("O"),
        _node({ x: new NumberNode(0), y: new NumberNode(0) })
      ),
      new PassNode("O の x プロパティを 1 に設定する"),
      new AssignmentNode(
        new GetIndexNode(new NameNode("O"), new StringNode("x")),
        new NumberNode(1)
      ),
      new PassNode("O の y プロパティを 2 に設定する"),
      new AssignmentNode(
        new GetIndexNode(new NameNode("O"), new StringNode("y")),
        new NumberNode(2)
      ),
      new PassNode("テスト: O のプロパティが x=1、y=2"),
      new AssertNode(
        new GetIndexNode(new NameNode("O"), new StringNode("x")),
        new NumberNode(1)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("O"), new StringNode("y")),
        new NumberNode(2)
      )
    ];
    return new YuiExample(
      "objects",
      "オブジェクトの作成とプロパティ操作",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleFunction() {
    const statements = [
      new PassNode("1を加算する関数を定義する"),
      new FuncDefNode(
        new NameNode("succ"),
        [new NameNode("n")],
        new BlockNode([
          new IncrementNode(new NameNode("n")),
          new ReturnNode(new NameNode("n"))
        ])
      ),
      new AssignmentNode(
        new NameNode("result"),
        new FuncAppNode(new NameNode("succ"), [new NumberNode(0)])
      ),
      new AssertNode(new NameNode("result"), new NumberNode(1))
    ];
    return new YuiExample(
      "function",
      "関数の定義と呼び出し（インクリメント関数）",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleFunctionNoArgument() {
    const statements = [
      new PassNode("引数なしで 0 を返す関数を定義する"),
      new FuncDefNode(
        new NameNode("zero"),
        [],
        new BlockNode(new ReturnNode(new NumberNode(0)))
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("zero"), []),
        new NumberNode(0)
      )
    ];
    return new YuiExample(
      "function_no_argument",
      "関数の定義と呼び出し（引数なし関数と複数引数関数）",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleFunctionWithoutReturn() {
    const statements = [
      new PassNode("点オブジェクトを作成する関数を定義する"),
      new FuncDefNode(
        new NameNode("point"),
        [new NameNode("x"), new NameNode("y")],
        new BlockNode([
          new PassNode(
            "関数が何も返さない場合、ローカル環境をオブジェクトとして返す"
          )
        ])
      ),
      new AssignmentNode(
        new NameNode("O"),
        new FuncAppNode(new NameNode("point"), [
          new NumberNode(0),
          new NumberNode(0)
        ])
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("O"), new StringNode("x")),
        new NumberNode(0)
      )
    ];
    return new YuiExample(
      "function_without_return",
      "関数の定義と呼び出し（戻り値なし関数）",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleRecursiveFunction() {
    const statements = [
      new PassNode("階乗を計算する再帰関数を定義する"),
      new FuncDefNode(
        new NameNode("fact"),
        [new NameNode("n")],
        new BlockNode([
          new IfNode(
            new NameNode("n"),
            "==",
            new NumberNode(0),
            new BlockNode([new ReturnNode(new NumberNode(1))]),
            new BlockNode([
              new PassNode("Yui には算術演算子がありません。"),
              new ReturnNode(
                new FuncAppNode(new NameNode("multiplex"), [
                  new NameNode("n"),
                  new FuncAppNode(new NameNode("fact"), [
                    new FuncAppNode(new NameNode("decrease"), [new NameNode("n")])
                  ])
                ])
              )
            ])
          )
        ])
      ),
      new PassNode("multiplex(a, b): a * b を計算する関数"),
      new FuncDefNode(
        new NameNode("multiplex"),
        [new NameNode("a"), new NameNode("b")],
        new BlockNode([
          new AssignmentNode(new NameNode("result"), new NumberNode(0)),
          new RepeatNode(
            new NameNode("b"),
            new BlockNode([
              new RepeatNode(
                new NameNode("a"),
                new BlockNode([new IncrementNode(new NameNode("result"))])
              )
            ])
          ),
          new ReturnNode(new NameNode("result"))
        ])
      ),
      new PassNode("decrease(n): n-1 を計算する関数"),
      new FuncDefNode(
        new NameNode("decrease"),
        [new NameNode("n")],
        new BlockNode([
          new DecrementNode(new NameNode("n")),
          new ReturnNode(new NameNode("n"))
        ])
      ),
      new PassNode("テスト: fact(0) が 1"),
      new AssertNode(
        new FuncAppNode(new NameNode("fact"), [new NumberNode(0)]),
        new NumberNode(1)
      ),
      new PassNode("テスト: fact(5) が 120"),
      new AssertNode(
        new FuncAppNode(new NameNode("fact"), [new NumberNode(5)]),
        new NumberNode(120)
      )
    ];
    return new YuiExample(
      "recursive_function",
      "再帰関数の定義と呼び出し（階乗関数）",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleArithmetic() {
    const addFunc = new FuncDefNode(
      new NameNode("add"),
      [new NameNode("a"), new NameNode("b")],
      new BlockNode([
        new AssignmentNode(new NameNode("result"), new NameNode("a")),
        new RepeatNode(
          new NameNode("b"),
          new BlockNode([new IncrementNode(new NameNode("result"))])
        ),
        new ReturnNode(new NameNode("result"))
      ])
    );
    const subtractFunc = new FuncDefNode(
      new NameNode("subtract"),
      [new NameNode("a"), new NameNode("b")],
      new BlockNode([
        new AssignmentNode(new NameNode("result"), new NameNode("a")),
        new RepeatNode(
          new NameNode("b"),
          new BlockNode([new DecrementNode(new NameNode("result"))])
        ),
        new ReturnNode(new NameNode("result"))
      ])
    );
    const multiplyFunc = new FuncDefNode(
      new NameNode("multiply"),
      [new NameNode("a"), new NameNode("b")],
      new BlockNode([
        new AssignmentNode(new NameNode("result"), new NumberNode(0)),
        new RepeatNode(
          new NameNode("b"),
          new BlockNode([
            new AssignmentNode(
              new NameNode("result"),
              new FuncAppNode(new NameNode("add"), [
                new NameNode("result"),
                new NameNode("a")
              ])
            )
          ])
        ),
        new ReturnNode(new NameNode("result"))
      ])
    );
    const divideFunc = new FuncDefNode(
      new NameNode("divide"),
      [new NameNode("a"), new NameNode("b")],
      new BlockNode([
        new AssignmentNode(new NameNode("q"), new NumberNode(0)),
        new AssignmentNode(new NameNode("r"), new NameNode("a")),
        new RepeatNode(
          new NameNode("a"),
          new BlockNode([
            new IfNode(
              new NameNode("r"),
              "<",
              new NameNode("b"),
              new BlockNode(new BreakNode())
            ),
            new IncrementNode(new NameNode("q")),
            new AssignmentNode(
              new NameNode("r"),
              new FuncAppNode(new NameNode("subtract"), [
                new NameNode("r"),
                new NameNode("b")
              ])
            )
          ])
        ),
        new ReturnNode(new NameNode("q"))
      ])
    );
    const moduloFunc = new FuncDefNode(
      new NameNode("modulo"),
      [new NameNode("a"), new NameNode("b")],
      new BlockNode([
        new AssignmentNode(new NameNode("r"), new NameNode("a")),
        new RepeatNode(
          new NameNode("a"),
          new BlockNode([
            new IfNode(
              new NameNode("r"),
              "<",
              new NameNode("b"),
              new BlockNode(new BreakNode())
            ),
            new AssignmentNode(
              new NameNode("r"),
              new FuncAppNode(new NameNode("subtract"), [
                new NameNode("r"),
                new NameNode("b")
              ])
            )
          ])
        ),
        new ReturnNode(new NameNode("r"))
      ])
    );
    const statements = [
      new PassNode("非負整数向けの四則演算関数"),
      new PassNode("add(a, b): a + b"),
      addFunc,
      new PassNode("subtract(a, b): a - b  (a >= b が必要)"),
      subtractFunc,
      new PassNode("multiply(a, b): a * b"),
      multiplyFunc,
      new PassNode("divide(a, b): 整数商 a // b"),
      divideFunc,
      new PassNode("modulo(a, b): 余り a % b"),
      moduloFunc,
      new PassNode("使用例"),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("add"), [
          new NumberNode(3),
          new NumberNode(4)
        ])
      ),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("subtract"), [
          new NumberNode(10),
          new NumberNode(3)
        ])
      ),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("multiply"), [
          new NumberNode(3),
          new NumberNode(4)
        ])
      ),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("divide"), [
          new NumberNode(10),
          new NumberNode(3)
        ])
      ),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("modulo"), [
          new NumberNode(10),
          new NumberNode(3)
        ])
      ),
      new PassNode("テスト: add"),
      new AssertNode(
        new FuncAppNode(new NameNode("add"), [
          new NumberNode(3),
          new NumberNode(4)
        ]),
        new NumberNode(7)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("add"), [
          new NumberNode(0),
          new NumberNode(5)
        ]),
        new NumberNode(5)
      ),
      new PassNode("テスト: subtract"),
      new AssertNode(
        new FuncAppNode(new NameNode("subtract"), [
          new NumberNode(10),
          new NumberNode(3)
        ]),
        new NumberNode(7)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("subtract"), [
          new NumberNode(5),
          new NumberNode(5)
        ]),
        new NumberNode(0)
      ),
      new PassNode("テスト: multiply"),
      new AssertNode(
        new FuncAppNode(new NameNode("multiply"), [
          new NumberNode(3),
          new NumberNode(4)
        ]),
        new NumberNode(12)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("multiply"), [
          new NumberNode(0),
          new NumberNode(5)
        ]),
        new NumberNode(0)
      ),
      new PassNode("テスト: divide"),
      new AssertNode(
        new FuncAppNode(new NameNode("divide"), [
          new NumberNode(10),
          new NumberNode(3)
        ]),
        new NumberNode(3)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("divide"), [
          new NumberNode(9),
          new NumberNode(3)
        ]),
        new NumberNode(3)
      ),
      new PassNode("テスト: modulo"),
      new AssertNode(
        new FuncAppNode(new NameNode("modulo"), [
          new NumberNode(10),
          new NumberNode(3)
        ]),
        new NumberNode(1)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("modulo"), [
          new NumberNode(15),
          new NumberNode(5)
        ]),
        new NumberNode(0)
      )
    ];
    return new YuiExample(
      "arithmetic",
      "非負整数向けの算術関数（add, subtract, multiply, divide, modulo）",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleFloatAdd() {
    const statements = [
      new PassNode(
        "float形式: [符号, d1..d7]  符号=1または-1、d1..d7 = abs(x)*1e6 の各桁"
      ),
      new PassNode("float_add(a, b): 同符号の float 配列を足し合わせる（stdlib なし）"),
      new FuncDefNode(
        new NameNode("float_add"),
        [new NameNode("a"), new NameNode("b")],
        new BlockNode([
          new AssignmentNode(
            new NameNode("result"),
            new ArrayNode([
              new GetIndexNode(new NameNode("a"), new NumberNode(0)),
              new NumberNode(0),
              new NumberNode(0),
              new NumberNode(0),
              new NumberNode(0),
              new NumberNode(0),
              new NumberNode(0),
              new NumberNode(0)
            ])
          ),
          new AssignmentNode(new NameNode("carry"), new NumberNode(0)),
          new AssignmentNode(new NameNode("i"), new NumberNode(7)),
          new RepeatNode(
            new NumberNode(7),
            new BlockNode([
              new AssignmentNode(new NameNode("sum"), new NameNode("carry")),
              new RepeatNode(
                new GetIndexNode(new NameNode("a"), new NameNode("i")),
                new BlockNode([new IncrementNode(new NameNode("sum"))])
              ),
              new RepeatNode(
                new GetIndexNode(new NameNode("b"), new NameNode("i")),
                new BlockNode([new IncrementNode(new NameNode("sum"))])
              ),
              new AssignmentNode(new NameNode("carry"), new NumberNode(0)),
              new IfNode(
                new NameNode("sum"),
                ">=",
                new NumberNode(10),
                new BlockNode([
                  new IncrementNode(new NameNode("carry")),
                  new RepeatNode(
                    new NumberNode(10),
                    new BlockNode([new DecrementNode(new NameNode("sum"))])
                  )
                ])
              ),
              new AssignmentNode(
                new GetIndexNode(new NameNode("result"), new NameNode("i")),
                new NameNode("sum")
              ),
              new DecrementNode(new NameNode("i"))
            ])
          ),
          new ReturnNode(new NameNode("result"))
        ])
      ),
      new PassNode("3.14 + 2.50 = 5.64"),
      new AssignmentNode(
        new NameNode("a"),
        new ArrayNode([
          new NumberNode(1),
          new NumberNode(3),
          new NumberNode(1),
          new NumberNode(4),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0)
        ])
      ),
      new AssignmentNode(
        new NameNode("b"),
        new ArrayNode([
          new NumberNode(1),
          new NumberNode(2),
          new NumberNode(5),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0)
        ])
      ),
      new AssignmentNode(
        new NameNode("c"),
        new FuncAppNode(new NameNode("float_add"), [
          new NameNode("a"),
          new NameNode("b")
        ])
      ),
      new PassNode("c == [1, 5, 6, 4, 0, 0, 0, 0]  (5.640000)"),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(0)),
        new NumberNode(1)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(1)),
        new NumberNode(5)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(2)),
        new NumberNode(6)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(3)),
        new NumberNode(4)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(4)),
        new NumberNode(0)
      ),
      new PassNode("1.99 + 1.01 = 3.00  (繰り上がり伝播のテスト)"),
      new AssignmentNode(
        new NameNode("a"),
        new ArrayNode([
          new NumberNode(1),
          new NumberNode(1),
          new NumberNode(9),
          new NumberNode(9),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0)
        ])
      ),
      new AssignmentNode(
        new NameNode("b"),
        new ArrayNode([
          new NumberNode(1),
          new NumberNode(1),
          new NumberNode(0),
          new NumberNode(1),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0),
          new NumberNode(0)
        ])
      ),
      new AssignmentNode(
        new NameNode("c"),
        new FuncAppNode(new NameNode("float_add"), [
          new NameNode("a"),
          new NameNode("b")
        ])
      ),
      new PassNode("c == [1, 3, 0, 0, 0, 0, 0, 0]  (3.000000)"),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(1)),
        new NumberNode(3)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(2)),
        new NumberNode(0)
      ),
      new AssertNode(
        new GetIndexNode(new NameNode("c"), new NumberNode(3)),
        new NumberNode(0)
      )
    ];
    return new YuiExample(
      "float_add",
      "同符号の float を桁配列として加算する（stdlib なし）",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleMonteCarlo() {
    const monteCarloFunc = new FuncDefNode(
      new NameNode("monte_carlo"),
      [new NameNode("n")],
      new BlockNode([
        new AssignmentNode(new NameNode("hits"), new NumberNode(0)),
        new RepeatNode(
          new NameNode("n"),
          new BlockNode([
            new AssignmentNode(
              new NameNode("x"),
              new FuncAppNode(new NameNode("乱数"), [])
            ),
            new AssignmentNode(
              new NameNode("y"),
              new FuncAppNode(new NameNode("乱数"), [])
            ),
            new AssignmentNode(
              new NameNode("dist"),
              new FuncAppNode(new NameNode("平方根"), [
                new FuncAppNode(new NameNode("和"), [
                  new FuncAppNode(new NameNode("積"), [
                    new NameNode("x"),
                    new NameNode("x")
                  ]),
                  new FuncAppNode(new NameNode("積"), [
                    new NameNode("y"),
                    new NameNode("y")
                  ])
                ])
              ])
            ),
            new IfNode(
              new NameNode("dist"),
              "<=",
              new NumberNode(1),
              new BlockNode(new IncrementNode(new NameNode("hits")))
            )
          ])
        ),
        new ReturnNode(
          new FuncAppNode(new NameNode("商"), [
            new FuncAppNode(new NameNode("積"), [
              new FuncAppNode(new NameNode("小数化"), [new NameNode("hits")]),
              new NumberNode(4)
            ]),
            new FuncAppNode(new NameNode("小数化"), [new NameNode("n")])
          ])
        )
      ])
    );
    const statements = [
      new ImportNode(),
      new PassNode("モンテカルロ法: ランダム点のサンプリングで π を推定する"),
      new PassNode("単位正方形 [0,1)×[0,1) に n 個のランダム点を投げる。"),
      new PassNode("単位円内の点（dist ≤ 1）をカウントする。"),
      new PassNode("π ≈ 4 × (hits / n)"),
      monteCarloFunc,
      new PassNode("サンプル数が多いほど π ≈ 3.14159... に近づく"),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("monte_carlo"), [new NumberNode(100)])
      ),
      new PrintExpressionNode(
        new FuncAppNode(new NameNode("monte_carlo"), [new NumberNode(1e3)])
      )
    ];
    return new YuiExample(
      "monte_carlo",
      "モンテカルロ法で π を推定する（stdlib: 乱数, 平方根）",
      new BlockNode(statements, true),
      "sample"
    );
  }
  function exampleNullAssignment() {
    const statements = [
      new PassNode("変数に null を代入する"),
      new AssignmentNode(new NameNode("x"), new ConstNode(null)),
      new PassNode("テスト: x が null"),
      new AssertNode(new NameNode("x"), new ConstNode(null))
    ];
    return new YuiExample(
      "null_assignment",
      "変数に null を代入して比較する",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleBooleanAssignment() {
    const statements = [
      new PassNode("true と false を変数に代入する"),
      new AssignmentNode(new NameNode("t"), new ConstNode(true)),
      new AssignmentNode(new NameNode("f"), new ConstNode(false)),
      new PassNode("テスト: t が true で f が false"),
      new AssertNode(new NameNode("t"), new ConstNode(true)),
      new AssertNode(new NameNode("f"), new ConstNode(false))
    ];
    return new YuiExample(
      "boolean_assignment",
      "変数に true/false を代入して比較する",
      new BlockNode(statements, true),
      "test"
    );
  }
  function exampleBooleanBranch() {
    const statements = [
      new PassNode("boolean 値で条件分岐する"),
      new AssignmentNode(new NameNode("flag"), new ConstNode(true)),
      new AssignmentNode(new NameNode("result"), new NumberNode(0)),
      new IfNode(
        new NameNode("flag"),
        "==",
        new ConstNode(true),
        new BlockNode(
          new AssignmentNode(new NameNode("result"), new NumberNode(1))
        ),
        new BlockNode(
          new AssignmentNode(new NameNode("result"), new NumberNode(2))
        )
      ),
      new PassNode("テスト: flag が true だったので result が 1"),
      new AssertNode(new NameNode("result"), new NumberNode(1))
    ];
    return new YuiExample(
      "boolean_branch",
      "boolean 値に基づく条件分岐",
      new BlockNode(statements, true),
      "both"
    );
  }
  function exampleNullCheck() {
    const statements = [
      new PassNode("is_null 関数を定義する"),
      new FuncDefNode(
        new NameNode("is_null"),
        [new NameNode("v")],
        new BlockNode([
          new IfNode(
            new NameNode("v"),
            "==",
            new ConstNode(null),
            new BlockNode(new ReturnNode(new ConstNode(true))),
            new BlockNode(new ReturnNode(new ConstNode(false)))
          )
        ])
      ),
      new PassNode("テスト: null と非 null の値で is_null を確認"),
      new AssertNode(
        new FuncAppNode(new NameNode("is_null"), [new ConstNode(null)]),
        new ConstNode(true)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("is_null"), [new NumberNode(0)]),
        new ConstNode(false)
      ),
      new AssertNode(
        new FuncAppNode(new NameNode("is_null"), [new StringNode("")]),
        new ConstNode(false)
      )
    ];
    return new YuiExample(
      "null_check",
      "値が null かどうかを確認する関数",
      new BlockNode(statements, true),
      "test"
    );
  }
  function getAllExamples() {
    return [
      exampleHelloWorld(),
      exampleVariables(),
      exampleLoop(),
      exampleFizzbuzz(),
      exampleNestedConditionalBranches(),
      exampleComparisons(),
      exampleArray(),
      exampleStrings(),
      exampleObjects(),
      exampleFunction(),
      exampleFunctionNoArgument(),
      exampleFunctionWithoutReturn(),
      exampleRecursiveFunction(),
      exampleArithmetic(),
      exampleFloatAdd(),
      exampleMonteCarlo(),
      exampleNullAssignment(),
      exampleBooleanAssignment(),
      exampleBooleanBranch(),
      exampleNullCheck()
    ];
  }
  function getSamples() {
    return getAllExamples().filter(
      (e) => e.kind === "sample" || e.kind === "both"
    );
  }
  function getTestExamples() {
    return getAllExamples().filter(
      (e) => e.kind === "test" || e.kind === "both"
    );
  }

  // src/index.js
  init_yuiparser();
  init_yuitypes();
  function run(source, opts = {}) {
    const {
      syntax = "yui",
      timeout = 30,
      allowBinaryOps = false,
      env = {}
    } = opts;
    const runtime = new YuiRuntime();
    runtime.allow_binary_ops = allowBinaryOps;
    for (const [key, value2] of Object.entries(env)) {
      runtime.setenv(key, types.box(value2));
    }
    const value = runtime.exec(source, syntax, { timeout, evalMode: true });
    const envSnapshot = {};
    for (const [key, v] of runtime.getTopEnv()) {
      if (key.startsWith("@")) continue;
      envSnapshot[key] = types.unbox(v);
    }
    return { value, env: envSnapshot, runtime };
  }
  function convert(source, opts) {
    const { from, to, indentString = "   ", functionLanguage = null } = opts;
    if (from == null || to == null) {
      throw new Error("convert: both `from` and `to` must be specified");
    }
    const parser = new YuiParser(from);
    const ast = parser.parse(source);
    const visitor = new CodingVisitor(to, functionLanguage);
    return visitor.emit(ast, indentString);
  }
  var VERSION = "0.0.1";
  return __toCommonJS(index_exports);
})();
