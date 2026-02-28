// test_coding.js — test CodingVisitor code generation
import { describe, test, expect } from 'vitest';
import { CodingVisitor } from '../src/yuicoding.js';
import { YuiParser } from '../src/yuiparser.js';
import { YuiRuntime } from '../src/yuiruntime.js';
import {
    ConstNode, NumberNode, StringNode, ArrayNode, ObjectNode, NameNode,
    BinaryNode, MinusNode, ArrayLenNode, GetIndexNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode,
} from '../src/yuiast.js';

const STDLIB = '標準ライブラリを使う\n';

// ─────────────────────────────────────────────
// Parametrized testcases: name → [node, expectedYuiCode]
// ─────────────────────────────────────────────
// NOTE: JS yui syntax has word-segmenter:" " so spaces appear between tokens.
// Python yui.json has no word-segmenter so Python generates e.g. "1+2"; JS generates "1 + 2".
const testcases = {
    // ConstNode
    'null':  [new ConstNode(null),  '値なし'],
    'true':  [new ConstNode(true),  '真'],
    'false': [new ConstNode(false), '偽'],
    // NumberNode
    '123': [new NumberNode(123), '123'],
    // StringNode
    '"hello"': [new StringNode('hello'), '"hello"'],
    // ArrayNode — word-segmenter adds space after comma
    '[1,2,3]': [new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)]), '[1, 2, 3]'],
    // ObjectNode — same
    '{"a":1,"b":"two"}': [new ObjectNode([
        new StringNode('a'), new NumberNode(1),
        new StringNode('b'), new StringNode('two'),
    ]), '{"a": 1, "b": "two"}'],
    // MinusNode — unary-minus: "-" is in no-space set
    '-5': [new MinusNode(new NumberNode(5)), '-5'],
    // ArrayLenNode — property-accessor "の" gets space before it
    'arr.length': [new ArrayLenNode(new NameNode('arr')), 'arr の 大きさ'],
    // GetIndexNode — "[" is in no-space set
    'arr[2]': [new GetIndexNode(new NameNode('arr'), new NumberNode(2)), 'arr[2]'],
    // PrintExpressionNode with inspection — "👀" gets space before expression
    'inspect(a)': [new PrintExpressionNode(new NameNode('a'), true), '👀 a'],
    // BinaryNode — binary-infix symbols get spaces from word-segmenter
    '1+2':     [new BinaryNode(new NumberNode(1), '+', new NumberNode(2)), '1 + 2'],
    '3*4':     [new BinaryNode(new NumberNode(3), '*', new NumberNode(4)), '3 * 4'],
    '1+2*3':   [new BinaryNode(new NumberNode(1), '+', new BinaryNode(new NumberNode(2), '*', new NumberNode(3))), '1 + 2 * 3'],
    '(1+2)*3': [new BinaryNode(new BinaryNode(new NumberNode(1), '+', new NumberNode(2)), '*', new NumberNode(3)), '(1 + 2) * 3'],
    '1-2-3':   [new BinaryNode(new BinaryNode(new NumberNode(1), '-', new NumberNode(2)), '-', new NumberNode(3)), '1 - 2 - 3'],
    '1-(2-3)': [new BinaryNode(new NumberNode(1), '-', new BinaryNode(new NumberNode(2), '-', new NumberNode(3))), '1 - (2 - 3)'],
    // AssignmentNode — assignment-infix "=" gets spaces
    'x=10': [new AssignmentNode(new NameNode('x'), new NumberNode(10)), 'x = 10'],
    // IncrementNode
    'x++': [new IncrementNode(new NameNode('x')), 'x を増やす'],
    // DecrementNode
    'x--': [new DecrementNode(new NameNode('x')), 'x を減らす'],
    // AppendNode
    'arr.push(10)': [new AppendNode(new NameNode('arr'), new NumberNode(10)), 'arr に 10 を追加する'],
    // BreakNode
    'break': [new BreakNode(), 'くり返しを抜ける'],
    // ReturnNode
    'return result': [new ReturnNode(new NameNode('result')), 'result が答え'],
    // PrintExpressionNode (print-begin/end both empty in yui)
    'print "Hello, World!"': [new PrintExpressionNode(new StringNode('Hello, World!')), '"Hello, World!"'],
    // BlockNode
    '{ x=1; y=2; }': [new BlockNode([
        new AssignmentNode(new NameNode('x'), new NumberNode(1)),
        new AssignmentNode(new NameNode('y'), new NumberNode(2)),
    ], true), 'x = 1\ny = 2'],
};

describe('CodingVisitor', () => {
    test.each(Object.entries(testcases))('%s', (name, [node, expected]) => {
        const visitor = new CodingVisitor('yui');
        expect(visitor.emit(node)).toBe(expected);
    });
});

// ─────────────────────────────────────────────
// Roundtrip and execution tests
// ─────────────────────────────────────────────

function roundtrip(source, syntax = 'yui') {
    const parser = new YuiParser(syntax);
    const ast = parser.parse(source);
    const visitor = new CodingVisitor(syntax);
    return visitor.emit(ast);
}

function execGenerated(source) {
    const rt = new YuiRuntime();
    rt.exec(source, 'yui', 30, false);
    return rt.environments[rt.environments.length - 1];
}

describe('roundtrip (parse → generate → execute)', () => {
    test('simple assignment', () => {
        const source = 'x = 42';
        const generated = roundtrip(source);
        const env = execGenerated(generated);
        expect(env['x']?.native ?? env['x']).toBe(42);
    });

    test('repeat loop', () => {
        const source = 'x = 0\n3回、くり返す {\n  xを増やす\n}';
        const generated = roundtrip(source);
        const env = execGenerated(generated);
        expect(env['x']?.native ?? env['x']).toBe(3);
    });

    test('stdlib usage', () => {
        const source = STDLIB + 'x = 和(3, 4)';
        const generated = roundtrip(source);
        expect(generated).toContain('標準ライブラリを使う');
        expect(generated).toContain('和');
        const env = execGenerated(generated);
        expect(env['x']?.native ?? env['x']).toBe(7);
    });

    test('1-2-3 roundtrip (left-associative)', () => {
        const generated = roundtrip('x = 1-2-3');
        expect(generated).toBe('x = 1 - 2 - 3');
    });

    test('1-(2-3) roundtrip (grouping preserved)', () => {
        const generated = roundtrip('x = 1-(2-3)');
        expect(generated).toBe('x = 1 - (2 - 3)');
    });

    test('(1+2)*3 roundtrip (grouping preserved)', () => {
        const generated = roundtrip('x = (1+2)*3');
        expect(generated).toBe('x = (1 + 2) * 3');
    });
});

describe('pylike syntax', () => {
    test('variable assignment in pylike', () => {
        const rt = new YuiRuntime();
        rt.exec('x = 42', 'pylike', 30, false);
        const env = rt.environments[rt.environments.length - 1];
        const v = env['x'];
        expect(v instanceof Object ? v.native : v).toBe(42);
    });
});

describe('sexpr syntax', () => {
    function execSexpr(src) {
        const rt = new YuiRuntime();
        rt.allowBinaryOps = true;
        rt.exec(src, 'sexpr', 30, false);
        const env = rt.environments[rt.environments.length - 1];
        return (k) => { const v = env[k]; return v instanceof Object ? v.native : v; };
    }

    test('variable assignment', () => {
        const env = execSexpr('(set! x 42)');
        expect(env('x')).toBe(42);
    });

    test('binary expression', () => {
        const env = execSexpr('(set! x (+ 1 2) )');
        expect(env('x')).toBe(3);
    });

    test('if statement with prefix operator', () => {
        const env = execSexpr('(if (== 1 1) (begin (set! x 10)) (begin (set! x 20)))');
        expect(env('x')).toBe(10);
    });

    test('function definition and call', () => {
        const src = '(define (succ n) (begin (return (+ n 1))))\n(set! x (succ 5))';
        const env = execSexpr(src);
        expect(env('x')).toBe(6);
    });

    test('roundtrip: parse and regenerate', () => {
        const src = '(set! x 42)';
        const parser = new YuiParser('sexpr');
        const ast = parser.parse(src);
        const visitor = new CodingVisitor('sexpr');
        const code = visitor.emit(ast);
        const rt = new YuiRuntime();
        rt.exec(code, 'sexpr', 30, false);
        const env = rt.environments[rt.environments.length - 1];
        expect((env['x']?.native ?? env['x'])).toBe(42);
    });
});
