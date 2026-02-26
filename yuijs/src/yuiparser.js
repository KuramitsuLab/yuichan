// yuiparser.js — PEG parser (port of yuichan/yuiparser.py)

import {
    ASTNode,
    ConstNode, NameNode, StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode, FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, CatchNode, ImportNode,
} from './yuiast.js';

import { YuiValue, YuiType, YuiError } from './yuitypes.js';
import { YuiSyntax, loadSyntax } from './yuisyntax.js';

// ─────────────────────────────────────────────
// Identifier extraction helpers
// ─────────────────────────────────────────────

function extractIdentifiers(text) {
    const identifiers = [];
    const pattern1 = /\n\s*([^\s\]\[\(\)"]+)\s*=(?!=)/g;
    let m;
    while ((m = pattern1.exec(text)) !== null) identifiers.push(m[1]);
    const pattern2 = /([^\s\]\[\(\)"]+)\s*\(/g;
    while ((m = pattern2.exec(text)) !== null) identifiers.push(m[1]);
    const withUnicode = identifiers.filter(id => /[^\x00-\x7F]/.test(id));
    return [...new Set(withUnicode)];
}

// ─────────────────────────────────────────────
// SourceNode (dummy node for error reporting)
// ─────────────────────────────────────────────

class SourceNode extends ASTNode {
    constructor() { super(); }
}

// ─────────────────────────────────────────────
// Source class — wraps source + position + syntax
// ─────────────────────────────────────────────

class Source extends YuiSyntax {
    constructor(source, filename = 'main.yui', pos = 0, syntax = 'yui') {
        const terminals = typeof syntax === 'string' ? loadSyntax(syntax) : syntax;
        super(terminals);
        this.filename = filename;
        this.source = source;
        this.pos = pos;
        this.length = source.length;
        this.specialNames = [];
        this.addSpecialNames(extractIdentifiers(source));
        this.memos = new Map();
    }

    getMemo(nonterminal, pos) {
        return this.memos.get(`${nonterminal}@${pos}`) ?? null;
    }

    setMemo(nonterminal, pos, result, newPos) {
        this.memos.set(`${nonterminal}@${pos}`, [result, newPos]);
    }

    hasNext() { return this.pos < this.length; }
    isEos() { return this.pos >= this.length; }

    consumeString(text) {
        if (this.source.startsWith(text, this.pos)) {
            this.pos += text.length;
            return true;
        }
        return false;
    }

    matchedString(terminal) {
        const pattern = this.getPattern(terminal);
        const remaining = this.source.slice(this.pos);
        const m = pattern.exec(remaining);
        if (m && m.index === 0) return m[0];
        return '';
    }

    isMatch(terminal, { ifUndefined = false, unconsumed = false, lskipWs = true, lskipLf = false } = {}) {
        if (typeof ifUndefined === 'boolean' && !this.isDefined(terminal)) {
            return ifUndefined;
        }
        if (terminal.startsWith('!')) {
            const wrongTerminal = `!${terminal}`;
            if (this.isDefined(wrongTerminal) && this.isMatch(wrongTerminal, { unconsumed: true, lskipWs })) {
                const expected = this.forExample(terminal);
                const matched = this.matchedString(wrongTerminal);
                throw new YuiError(['frequent-mistake', `❌\`${matched}\``, `✅\`${expected}\``], this.p({ length: 1 }));
            }
        }
        const savedPos = this.pos;
        if (lskipWs || lskipLf) {
            this.skipWhitespacesAndComments(lskipLf);
        }
        const patternStr = typeof ifUndefined === 'string' ? ifUndefined : '';
        const pattern = this.getPattern(terminal, patternStr);
        const remaining = this.source.slice(this.pos);
        const m = pattern.exec(remaining);
        if (m && m.index === 0) {
            if (unconsumed) {
                this.pos = savedPos;
                return true;
            }
            this.pos += m[0].length;
            return true;
        }
        this.pos = savedPos;
        return false;
    }

    tryMatch(terminal, { ifUndefined = true, unconsumed = false, BK = false,
                        lskipWs = true, lskipLf = false, openingPos = null } = {}) {
        if (this.isMatch(terminal, { ifUndefined, unconsumed, lskipWs, lskipLf })) return;
        const expectedToken = this.forExample(terminal);
        if (openingPos !== null) {
            throw new YuiError(['expected-closing', `✅\`${expectedToken}\``], this.p({ startPos: openingPos }));
        }
        const snippet = this.captureLine();
        throw new YuiError(
            ['expected-token', `✅\`${expectedToken}\``, `❌\`${snippet}\``, `🔍${terminal}`],
            this.p({ length: 1 }), BK
        );
    }

    findMatch(terminal, suffixes, lskipLf = false) {
        for (const suffix of suffixes) {
            const key = `${terminal}${suffix}`;
            if (this.isMatch(key, { ifUndefined: false, unconsumed: false, lskipWs: true, lskipLf })) {
                return suffix;
            }
        }
        return null;
    }

    canBacktrack(lookahead) {
        if (this.isDefined(lookahead)) {
            const pattern = this.getPattern(lookahead);
            const captured = this.captureLine();
            return !pattern.test(captured);
        }
        return true;
    }

    isEosOrLinefeed({ lskipWs = true, unconsumed = false } = {}) {
        const savedPos = this.pos;
        if (lskipWs) this.skipWhitespacesAndComments(false);
        if (this.isEos()) {
            if (unconsumed) this.pos = savedPos;
            return true;
        }
        return this.isMatch('linefeed', { lskipWs: false, lskipLf: false, unconsumed });
    }

    consumeUntil(terminal, { untilEof = true, disallowString = null } = {}) {
        const pattern = this.getPattern(terminal);
        const remaining = this.source.slice(this.pos);
        const m = pattern.exec(remaining);
        if (m) {
            if (disallowString && remaining.slice(0, m.index).includes(disallowString)) {
                return false;
            }
            this.pos += m.index;
            return true;
        }
        if (untilEof) {
            this.pos = this.length;
            return true;
        }
        return false;
    }

    skipWhitespacesAndComments(includeLinefeed = false) {
        while (this.hasNext()) {
            if (this.isMatch('whitespaces', { lskipWs: false })) continue;
            if (includeLinefeed && this.isMatch('linefeed', { lskipWs: false })) continue;
            if (this.isMatch('line-comment-begin', { ifUndefined: false, lskipWs: false })) {
                this.consumeUntil('linefeed', { untilEof: true });
                continue;
            }
            if (this.isDefined('comment-begin') && this.isDefined('comment-end')) {
                const openingPos = this.pos;
                if (this.isMatch('comment-begin', { lskipWs: false })) {
                    this.consumeUntil('comment-end', { untilEof: true });
                    this.tryMatch('comment-end', { lskipWs: false, openingPos });
                    continue;
                }
            }
            break;
        }
    }

    addSpecialNames(names) {
        const combined = new Set([...this.specialNames, ...names]);
        this.specialNames = [...combined].sort((a, b) => b.length - a.length);
    }

    matchSpecialName({ unconsumed = false } = {}) {
        for (const name of this.specialNames) {
            if (this.source.startsWith(name, this.pos)) {
                if (!unconsumed) this.pos += name.length;
                return name;
            }
        }
        return null;
    }

    captureIndent(indentChars = ' \t\u3000') {
        let startPos = this.pos - 1;
        while (startPos >= 0) {
            const ch = this.source[startPos];
            if (ch === '\n') { startPos++; break; }
            startPos--;
        }
        if (startPos < 0) startPos = 0;
        let endPos = startPos;
        while (endPos < this.length) {
            if (indentChars.includes(this.source[endPos])) endPos++;
            else break;
        }
        return this.source.slice(startPos, endPos);
    }

    captureLine() {
        const startPos = this.pos;
        while (this.pos < this.length) {
            if (this.isMatch('linefeed', { lskipWs: false, unconsumed: true }) ||
                this.isMatch('line-comment-begin', { lskipWs: false, unconsumed: true }) ||
                this.isMatch('comment-begin', { lskipWs: false, unconsumed: true }) ||
                this.isMatch('statement-separator', { lskipWs: false, unconsumed: true })) {
                const captured = this.source.slice(startPos, this.pos);
                this.pos = startPos;
                return captured;
            }
            this.pos++;
        }
        this.pos = startPos;
        return this.source.slice(startPos).split('\n')[0];
    }

    p({ node = null, startPos = null, endPos = null, length = 0 } = {}) {
        node = node ?? new SourceNode();
        node.filename = this.filename;
        node.source = this.source;
        const savePos = this.pos;
        if (startPos !== null) {
            node.pos = startPos;
            if (endPos !== null) node.endPos = endPos;
            else if (length !== 0) node.endPos = Math.min(startPos + length, this.length);
            else node.endPos = savePos;
        } else if (length !== 0) {
            node.pos = this.pos;
            node.endPos = Math.min(this.pos + length, this.length);
        } else {
            node.pos = Math.max(this.pos - 1, 0);
            node.endPos = this.pos;
        }
        return node;
    }
}

// ─────────────────────────────────────────────
// NONTERMINALS registry
// ─────────────────────────────────────────────

const NONTERMINALS = {};

class ParserCombinator {
    quickCheck(source) { return true; }
    match(source, pc) { return true; }
}

function parse(nonterminal, source, pc, { lskipWs = true, lskipLf = false, BK = false } = {}) {
    const combinator = NONTERMINALS[nonterminal];
    const savedPos = source.pos;
    if (lskipWs || lskipLf) {
        source.skipWhitespacesAndComments(lskipLf);
    }
    const memoKey = source.pos;
    const memo = source.getMemo(nonterminal, memoKey);
    if (memo !== null) {
        source.pos = memo[1];
        return memo[0];
    }
    const startPos = source.pos;
    try {
        const result = combinator.match(source, pc);
        source.setMemo(nonterminal, startPos, result, source.pos);
        return result;
    } catch (e) {
        if (e instanceof YuiError) {
            if (e.BK === true && BK === false) {
                source.pos = startPos;
                const snippet = source.captureLine();
                throw new YuiError(
                    [`expected-${nonterminal.slice(1).toLowerCase()}`, `❌${snippet}`, `⚠️${e.message}`],
                    source.p({ length: 1 })
                );
            }
            throw e;
        }
        throw e;
    }
}

function isParsable(nonterminal, source, pc, { lskipWs = true, lskipLf = false } = {}) {
    try {
        parse(nonterminal, source, pc, { lskipWs, lskipLf });
        return true;
    } catch {
        return false;
    }
}

// ─────────────────────────────────────────────
// Literal parsers
// ─────────────────────────────────────────────

class ConstParser extends ParserCombinator {
    quickCheck(source) {
        return source.isMatch('null', { ifUndefined: false }) ||
               source.isMatch('boolean-true', { ifUndefined: false }) ||
               source.isMatch('boolean-false', { ifUndefined: false });
    }

    match(source, pc) {
        const savedPos = source.pos;
        if (source.isMatch('null', { ifUndefined: false })) {
            return source.p({ node: new ConstNode(null), startPos: savedPos });
        }
        if (source.isMatch('boolean-true', { ifUndefined: false })) {
            return source.p({ node: new ConstNode(true), startPos: savedPos });
        }
        if (source.isMatch('boolean-false', { ifUndefined: false })) {
            return source.p({ node: new ConstNode(false), startPos: savedPos });
        }
        throw new YuiError(['expected-null or boolean'], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@Boolean'] = new ConstParser();

class NumberParser extends ParserCombinator {
    quickCheck(source) {
        return source.isMatch('number-first-char', { unconsumed: true });
    }

    match(source, pc) {
        const savedPos = source.pos;
        if (source.isMatch('number-first-char')) {
            source.tryMatch('number-chars', { lskipWs: false });
            if (source.isMatch('number-dot-char', { lskipWs: false })) {
                source.tryMatch('number-first-char', { lskipWs: false });
                source.tryMatch('number-chars', { lskipWs: false });
                const num = source.source.slice(savedPos, source.pos);
                // Mark as float even when value is whole (e.g. 10.0) — JS loses type info
                return source.p({ node: new NumberNode(parseFloat(num), true), startPos: savedPos });
            }
            const num = source.source.slice(savedPos, source.pos);
            return source.p({ node: new NumberNode(parseInt(num, 10)), startPos: savedPos });
        }
        throw new YuiError(['expected-number'], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@Number'] = new NumberParser();

class StringParser extends ParserCombinator {
    quickCheck(source) {
        return source.isMatch('string-begin', { unconsumed: true });
    }

    match(source, pc) {
        const openingQuotePos = source.pos;
        if (source.isMatch('string-begin')) {
            let openingPos = source.pos;
            const stringContent = [];
            let expressionCount = 0;
            while (source.pos < source.length) {
                source.consumeUntil('string-content-end', { untilEof: true });
                stringContent.push(source.source.slice(openingPos, source.pos));
                if (source.isMatch('string-end', { unconsumed: true })) break;
                if (source.isMatch('string-escape')) {
                    if (source.isEos()) {
                        throw new YuiError(['bad-escape-sequence'], source.p({ length: 1 }));
                    }
                    const nextChar = source.source[source.pos];
                    source.pos++;
                    if (nextChar === 'n') stringContent.push('\n');
                    else if (nextChar === 't') stringContent.push('\t');
                    else stringContent.push(nextChar);
                    openingPos = source.pos;
                    continue;
                }
                const startInterPos = source.pos;
                if (source.isMatch('string-interpolation-begin', { lskipWs: false })) {
                    const expression = parse('@Expression', source, pc);
                    source.tryMatch('string-interpolation-end', { openingPos: startInterPos });
                    stringContent.push(expression);
                    expressionCount++;
                    openingPos = source.pos;
                    continue;
                }
                break; // fallthrough - shouldn't happen
            }
            source.tryMatch('string-end', { lskipWs: false, openingPos: openingQuotePos });
            const contents = expressionCount === 0 ? stringContent.join('') : stringContent;
            return source.p({ node: new StringNode(contents), startPos: openingQuotePos });
        }
        throw new YuiError(['expected-string'], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@String'] = new StringParser();

class ArrayParser extends ParserCombinator {
    quickCheck(source) {
        return source.isMatch('array-begin', { unconsumed: true });
    }

    match(source, pc) {
        const openingPos = source.pos;
        if (source.isMatch('array-begin')) {
            const args = [];
            while (!source.isMatch('array-end', { lskipLf: true, unconsumed: true })) {
                args.push(parse('@Expression', source, pc, { lskipLf: true }));
                if (source.isMatch('array-separator', { lskipLf: true })) continue;
            }
            source.tryMatch('array-end', { lskipLf: true, openingPos });
            return source.p({ node: new ArrayNode(args), startPos: openingPos });
        }
        throw new YuiError(['expected-array'], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@Array'] = new ArrayParser();

class ObjectParser extends ParserCombinator {
    quickCheck(source) {
        return source.isMatch('object-begin', { unconsumed: true });
    }

    match(source, pc) {
        const openingPos = source.pos;
        if (source.isMatch('object-begin', { lskipLf: true })) {
            const args = [];
            while (!source.isMatch('object-end', { lskipLf: true, unconsumed: true })) {
                args.push(parse('@String', source, pc, { lskipLf: true }));
                source.tryMatch('key-value-separator', { lskipLf: true });
                args.push(parse('@Expression', source, pc, { lskipLf: true }));
                if (source.isMatch('object-separator', { lskipLf: true })) continue;
            }
            source.tryMatch('object-end', { lskipLf: true, openingPos });
            return source.p({ node: new ObjectNode(args), startPos: openingPos });
        }
        throw new YuiError(['expected-object'], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@Object'] = new ObjectParser();

class NameParser extends ParserCombinator {
    match(source, pc) {
        const specialName = source.matchSpecialName();
        if (specialName !== null) {
            return source.p({
                node: new NameNode(specialName),
                startPos: source.pos - specialName.length,
            });
        }
        if (source.isMatch('extra-name-begin', { ifUndefined: false })) {
            const startPos = source.pos;
            source.consumeUntil('extra-name-end', { disallowString: '\n' });
            const name = source.source.slice(startPos, source.pos);
            const node = source.p({ node: new NameNode(name), startPos });
            source.tryMatch('extra-name-end', { openingPos: startPos - 1 });
            return node;
        }
        const startPos = source.pos;
        if (source.isMatch('name-first-char')) {
            source.tryMatch('name-chars', { lskipWs: false });
            source.tryMatch('name-end', { lskipWs: false });
            const name = source.source.slice(startPos, source.pos);
            return source.p({ node: new NameNode(name), startPos });
        }
        const snippet = source.captureLine().trim();
        throw new YuiError(['wrong-name', `❌${snippet}`], source.p({ length: 1 }), true);
    }
}
NONTERMINALS['@Name'] = new NameParser();

const LITERALS = ['@Number', '@String', '@Array', '@Object', '@Boolean'];

class TermParser extends ParserCombinator {
    match(source, pc) {
        const openingPos = source.pos;
        if (source.isMatch('grouping-begin')) {
            const exprNode = parse('@Expression', source, pc);
            source.tryMatch('grouping-end', { openingPos });
            return exprNode;
        }
        if (source.isMatch('length-begin')) {
            const exprNode = parse('@Expression', source, pc);
            source.tryMatch('length-end', { openingPos });
            return source.p({ node: new ArrayLenNode(exprNode), startPos: openingPos });
        }
        for (const literal of LITERALS) {
            if (NONTERMINALS[literal].quickCheck(source)) {
                source.pos = openingPos;
                return parse(literal, source, pc, { BK: true });
            }
        }
        return parse('@Name', source, pc, { BK: true });
    }
}
NONTERMINALS['@Term'] = new TermParser();

class PrimaryParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        if (source.isMatch('unary-minus', { ifUndefined: false })) {
            const node = parse('@Primary', source, pc);
            return source.p({ node: new MinusNode(node), startPos });
        }
        if (source.isMatch('unary-inspection', { ifUndefined: false })) {
            const node = parse('@Primary', source, pc);
            return source.p({ node: new PrintExpressionNode(node, true), startPos });
        }
        if (source.isMatch('unary-length', { ifUndefined: false })) {
            const node = parse('@Primary', source, pc);
            return source.p({ node: new ArrayLenNode(node), startPos });
        }
        let node = parse('@Term', source, pc, { BK: true });
        while (source.hasNext()) {
            const openingPos = source.pos;
            if (source.isMatch('funcapp-args-begin')) {
                const args = [];
                while (!source.isMatch('funcapp-args-end', { unconsumed: true })) {
                    args.push(parse('@Expression', source, pc, { lskipLf: true }));
                    if (source.isMatch('funcapp-separator')) continue;
                }
                source.tryMatch('funcapp-args-end', { openingPos });
                node = source.p({ node: new FuncAppNode(node, args), startPos });
                continue;
            }
            if (source.isMatch('array-indexer-suffix', { ifUndefined: '\\[' })) {
                const indexNode = parse('@Expression', source, pc);
                source.tryMatch('array-indexer-end', { openingPos });
                node = source.p({ node: new GetIndexNode(node, indexNode), startPos });
                continue;
            }
            const savePos = source.pos;
            if (source.isMatch('property-accessor', { ifUndefined: false })) {
                if (source.isMatch('property-length', { ifUndefined: false })) {
                    node = source.p({ node: new ArrayLenNode(node), startPos });
                    continue;
                }
                if (source.isMatch('property-type', { ifUndefined: false })) {
                    // future: type annotation
                }
                source.pos = savePos;
            }
            break;
        }
        return node;
    }
}
NONTERMINALS['@Primary'] = new PrimaryParser();

class MultiplicativeParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        const leftNode = parse('@Primary', source, pc, { BK: true });
        try {
            if (source.isMatch('binary-infix*', { ifUndefined: false })) {
                const rightNode = parse('@Multiplicative', source, pc);
                return source.p({ node: new BinaryNode(leftNode, '*', rightNode), startPos });
            }
            if (source.isMatch('binary-infix/', { ifUndefined: false })) {
                const rightNode = parse('@Multiplicative', source, pc);
                return source.p({ node: new BinaryNode(leftNode, '/', rightNode), startPos });
            }
            if (source.isMatch('binary-infix%', { ifUndefined: false })) {
                const rightNode = parse('@Multiplicative', source, pc);
                return source.p({ node: new BinaryNode(leftNode, '%', rightNode), startPos });
            }
        } catch {}
        source.pos = leftNode.endPos;
        return leftNode;
    }
}
NONTERMINALS['@Multiplicative'] = new MultiplicativeParser();

class AdditiveParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        const leftNode = parse('@Multiplicative', source, pc, { BK: true });
        try {
            if (source.isMatch('binary-infix+', { ifUndefined: false })) {
                const rightNode = parse('@Additive', source, pc);
                return source.p({ node: new BinaryNode(leftNode, '+', rightNode), startPos });
            }
            if (source.isMatch('binary-infix-', { ifUndefined: false })) {
                const rightNode = parse('@Additive', source, pc);
                return source.p({ node: new BinaryNode(leftNode, '-', rightNode), startPos });
            }
        } catch {}
        source.pos = leftNode.endPos;
        return leftNode;
    }
}
NONTERMINALS['@Additive'] = new AdditiveParser();

class ComparativeParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        const leftNode = parse('@Additive', source, pc, { BK: true });
        try {
            for (const [op, sym] of [
                ['binary==', '=='], ['binary!=', '!='], ['binary<=', '<='],
                ['binary>=', '>='], ['binary<', '<'], ['binary>', '>'],
                ['binaryin', 'in'], ['binarynotin', 'notin'],
            ]) {
                if (source.isMatch(op, { ifUndefined: false })) {
                    const rightNode = parse('@Additive', source, pc);
                    return source.p({
                        node: new BinaryNode(leftNode, sym, rightNode, true),
                        startPos,
                    });
                }
            }
        } catch {}
        source.pos = leftNode.endPos;
        return leftNode;
    }
}
NONTERMINALS['@Comparative'] = new ComparativeParser();

class ExpressionParser extends ParserCombinator {
    match(source, pc) {
        return parse('@Comparative', source, pc, { BK: true });
    }
}
NONTERMINALS['@Expression'] = new ExpressionParser();

// ─────────────────────────────────────────────
// Statement parsers
// ─────────────────────────────────────────────

class AssignmentParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('assignment-lookahead');
        const startPos = source.pos;
        source.tryMatch('assignment-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const leftNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('assignment-infix', { BK });
        const rightNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('assignment-end', { BK });
        return source.p({ node: new AssignmentNode(leftNode, rightNode), startPos });
    }
}
NONTERMINALS['@Assignment'] = new AssignmentParser();

class IncrementParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('increment-lookahead');
        const startPos = source.pos;
        source.tryMatch('increment-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const lvalueNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('increment-infix', { BK });
        source.tryMatch('increment-end', { BK });
        return source.p({ node: new IncrementNode(lvalueNode), startPos });
    }
}
NONTERMINALS['@Increment'] = new IncrementParser();

class DecrementParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('decrement-lookahead');
        const startPos = source.pos;
        source.tryMatch('decrement-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const lvalueNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('decrement-infix', { BK });
        source.tryMatch('decrement-end', { BK });
        return source.p({ node: new DecrementNode(lvalueNode), startPos });
    }
}
NONTERMINALS['@Decrement'] = new DecrementParser();

class AppendParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('append-lookahead');
        const startPos = source.pos;
        source.tryMatch('append-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const lvalueNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('append-infix', { BK });
        const valueNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('append-suffix', { BK });
        source.tryMatch('append-end', { BK });
        return source.p({ node: new AppendNode(lvalueNode, valueNode), startPos });
    }
}
NONTERMINALS['@Append'] = new AppendParser();

class BreakParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        source.tryMatch('break', { BK: true });
        return source.p({ node: new BreakNode(), startPos });
    }
}
NONTERMINALS['@Break'] = new BreakParser();

class ImportParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        source.tryMatch('import-standard', { BK: true });
        return source.p({ node: new ImportNode(), startPos });
    }
}
NONTERMINALS['@Import'] = new ImportParser();

class PassParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        source.tryMatch('pass', { BK: true });
        return source.p({ node: new PassNode(), startPos });
    }
}
NONTERMINALS['@Pass'] = new PassParser();

class ReturnParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('return-lookahead');
        const startPos = source.pos;
        source.tryMatch('return-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const exprNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('return-end', { BK });
        return source.p({ node: new ReturnNode(exprNode), startPos });
    }
}
NONTERMINALS['@Return'] = new ReturnParser();

class PrintExpressionParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('print-lookahead');
        const startPos = source.pos;
        source.tryMatch('print-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const exprNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('print-end', { BK });
        return source.p({ node: new PrintExpressionNode(exprNode), startPos });
    }
}
NONTERMINALS['@PrintExpression'] = new PrintExpressionParser();

class RepeatParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('repeat-lookahead');
        const startPos = source.pos;
        source.tryMatch('repeat-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const timesNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('repeat-times', { BK });
        source.tryMatch('repeat-block', { BK });
        pc = { ...pc, indent: source.captureIndent() };
        const blockNode = parse('@Block', source, pc);
        source.tryMatch('repeat-end', { BK: false });
        return source.p({ node: new RepeatNode(timesNode, blockNode), startPos });
    }
}
NONTERMINALS['@Repeat'] = new RepeatParser();

class IfParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        let BK = source.canBacktrack('if-lookahead');
        source.tryMatch('if-begin', { BK });
        source.tryMatch('if-condition-begin', { BK });
        if (BK) BK = source.pos === startPos;
        let leftNode = parse('@Expression', source, pc, { BK });
        let operator, rightNode;

        if (leftNode instanceof BinaryNode && leftNode.comparative) {
            operator = leftNode.operator;
            rightNode = leftNode.rightNode;
            leftNode = leftNode.leftNode;
        } else {
            operator = source.findMatch('if-infix', ['==', '!=', '<=', '<', '>=', '>', 'notin', 'in']);
            if (!operator) {
                source.tryMatch('if-infix', { BK });
            }
            rightNode = parse('@Expression', source, pc, { BK });
            if (!operator) {
                operator = source.findMatch('if-suffix', ['!=', '<=', '<', '>=', '>', 'notin', 'in', '==']);
                source.skipWhitespacesAndComments();
                if (operator === null) operator = '==';
            }
        }

        source.tryMatch('if-condition-end', { BK });
        pc = { ...pc, indent: source.captureIndent() };
        source.tryMatch('if-then', { BK: false });
        const thenNode = parse('@Block', source, pc, { BK: false });

        const savePos = source.pos;
        source.skipWhitespacesAndComments(true);
        let elseNode = null;
        if (source.isMatch('if-else')) {
            elseNode = parse('@Block', source, pc, { BK: false });
        } else {
            source.pos = savePos;
        }
        source.tryMatch('if-end', { BK: false });

        // Convert operator symbol to OPERATORS entry for IfNode
        const opSymbol = typeof operator === 'string' ? operator : operator.symbol;
        return source.p({ node: new IfNode(leftNode, opSymbol, rightNode, thenNode, elseNode), startPos });
    }
}
NONTERMINALS['@If'] = new IfParser();

class FuncDefParser extends ParserCombinator {
    match(source, pc) {
        let BK = source.canBacktrack('funcdef-lookahead');
        const startPos = source.pos;
        source.tryMatch('funcdef-begin', { BK });
        source.tryMatch('funcdef-name-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const nameNode = parse('@Name', source, pc, { BK });
        source.tryMatch('funcdef-name-end', { BK });

        const args = [];
        if (!source.isMatch('funcdef-noarg')) {
            source.tryMatch('funcdef-args-begin', { BK });
            while (!source.isMatch('funcdef-args-end', { unconsumed: true })) {
                const argNode = parse('@Name', source, pc);
                args.push(argNode);
                if (source.isMatch('funcdef-arg-separator')) continue;
                break;
            }
            source.tryMatch('funcdef-args-end', { BK: false });
        }

        pc = { ...pc, indent: source.captureIndent() };
        source.tryMatch('funcdef-block', { BK });
        const bodyNode = parse('@Block', source, pc, { BK: false });
        source.tryMatch('funcdef-end', { BK: false });
        return source.p({ node: new FuncDefNode(nameNode, args, bodyNode), startPos });
    }
}
NONTERMINALS['@FuncDef'] = new FuncDefParser();

class AssertParser extends ParserCombinator {
    match(source, pc) {
        const startPos = source.pos;
        let BK = source.canBacktrack('assert-lookahead');
        source.tryMatch('assert-begin', { BK });
        if (BK) BK = source.pos === startPos;
        const testNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('assert-infix', { BK });
        const referenceNode = parse('@Expression', source, pc, { BK });
        source.tryMatch('assert-end', { BK });
        return source.p({ node: new AssertNode(testNode, referenceNode), startPos });
    }
}
NONTERMINALS['@Assert'] = new AssertParser();

// ─────────────────────────────────────────────
// Block and top-level parsers
// ─────────────────────────────────────────────

class BlockParser extends ParserCombinator {
    match(source, pc) {
        const savedPos = source.pos;
        source.tryMatch('block-begin');
        if (source.isMatch('block-end')) {
            return source.p({ node: new BlockNode([]), startPos: savedPos });
        }

        let statements = parse('@Statement[]', source, pc);
        if (source.isMatch('block-end')) {
            return source.p({ node: new BlockNode(statements), startPos: savedPos });
        }

        const endLevelIndent = pc.indent ?? '';
        while (source.hasNext()) {
            source.isEosOrLinefeed();
            const lineStartPos = source.pos;
            if (source.consumeString(endLevelIndent)) {
                if (source.isMatch('whitespace', { lskipWs: false })) {
                    if (source.isMatch('block-end', { unconsumed: true })) {
                        throw new YuiError(
                            ['wrong-indent-level', `✅\`${endLevelIndent}\``],
                            source.p({ startPos: lineStartPos, length: endLevelIndent.length })
                        );
                    }
                    statements = statements.concat(parse('@Statement[]', source, pc));
                    continue;
                }
            }
            if (source.isMatch('linefeed', { unconsumed: true })) continue;
            break;
        }
        source.tryMatch('block-end', { openingPos: savedPos });
        return source.p({ node: new BlockNode(statements), startPos: savedPos });
    }
}
NONTERMINALS['@Block'] = new BlockParser();

const STATEMENTS = [
    '@FuncDef', '@Assignment', '@Assert', '@If', '@Repeat',
    '@Break', '@Increment', '@Decrement', '@Append', '@Return',
    '@Import', '@Pass', '@PrintExpression',
];

class StatementParser extends ParserCombinator {
    match(source, pc) {
        const savedPos = source.pos;
        for (const parserName of STATEMENTS) {
            source.pos = savedPos;
            try {
                return parse(parserName, source, pc, { BK: true });
            } catch (e) {
                if (e instanceof YuiError && e.BK) continue;
                throw e;
            }
        }
        source.pos = savedPos;
        const line = source.captureLine();
        throw new YuiError(['wrong-statement', `❌${line}`], source.p({ length: 1 }));
    }
}
NONTERMINALS['@Statement'] = new StatementParser();

class StatementsParser extends ParserCombinator {
    match(source, pc) {
        let statements;
        if (source.isEosOrLinefeed({ lskipWs: true, unconsumed: true })) {
            statements = [];
        } else {
            statements = [parse('@Statement', source, pc)];
        }
        while (source.isMatch('statement-separator', { ifUndefined: false })) {
            statements.push(parse('@Statement', source, pc));
        }
        return statements;
    }
}
NONTERMINALS['@Statement[]'] = new StatementsParser();

class TopLevelParser extends ParserCombinator {
    match(source, pc) {
        source.skipWhitespacesAndComments(true);
        const savedPos = source.pos;
        const statements = [];
        while (source.hasNext()) {
            const curPos = source.pos;
            statements.push(...parse('@Statement[]', source, pc));
            if (curPos === source.pos) break;
            source.skipWhitespacesAndComments(true);
        }
        return source.p({ node: new BlockNode(statements, true), startPos: savedPos });
    }
}
NONTERMINALS['@TopLevel'] = new TopLevelParser();

// ─────────────────────────────────────────────
// YuiParser — public API
// ─────────────────────────────────────────────

export class YuiParser {
    constructor(syntax = 'yui') {
        this.syntax = syntax;
        this.terminals = typeof syntax === 'object' ? { ...syntax } : loadSyntax(syntax);
    }

    parse(sourceCode) {
        const source = new Source(sourceCode, 'main.yui', 0, this.terminals);
        return parse('@TopLevel', source, {});
    }
}
