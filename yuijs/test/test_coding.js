// test_coding.js — test CodingVisitor code generation
import { describe, test, expect } from 'vitest';
import { CodingVisitor } from '../src/yuicoding.js';
import { YuiParser } from '../src/yuiparser.js';
import { YuiRuntime } from '../src/yuiruntime.js';
import {
    ConstNode, NumberNode, StringNode, ArrayNode, NameNode,
    AssignmentNode, BlockNode, FuncDefNode, FuncAppNode, ReturnNode,
    RepeatNode, IncrementNode, AppendNode,
} from '../src/yuiast.js';

const STDLIB = '標準ライブラリを使う\n';

// Helper: parse and regenerate
function roundtrip(source, syntax = 'yui') {
    const parser = new YuiParser(syntax);
    const ast = parser.parse(source);
    const visitor = new CodingVisitor(syntax);
    return visitor.emit(ast);
}

// Helper: regenerate from AST and then execute
function execGenerated(source) {
    const rt = new YuiRuntime();
    rt.exec(source, 'yui', 30, false);
    return rt.environments[rt.environments.length - 1];
}

describe('CodingVisitor', () => {
    test('null literal', () => {
        const node = new ConstNode(null);
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('値なし');
    });

    test('true literal', () => {
        const node = new ConstNode(true);
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('真');
    });

    test('false literal', () => {
        const node = new ConstNode(false);
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('偽');
    });

    test('integer literal', () => {
        const node = new NumberNode(42);
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('42');
    });

    test('string literal', () => {
        const node = new StringNode('hello');
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('"hello"');
    });

    test('array literal', () => {
        const node = new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)]);
        const visitor = new CodingVisitor('yui');
        const result = visitor.emit(new BlockNode([new AssignmentNode('x', node)], true));
        expect(result).toContain('[1, 2, 3]');
    });

    test('function definition', () => {
        const body = new BlockNode([new ReturnNode(new NameNode('n'))]);
        const func = new FuncDefNode('identity', ['n'], body);
        const visitor = new CodingVisitor('yui');
        const code = visitor.emit(new BlockNode([func], true));
        expect(code).toContain('入力');
        expect(code).toContain('に対し');
        expect(code).toContain('identity');
    });
});

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
        // Roundtrip generates `x = 和(3, 4)` (spaces around =), which re-parses correctly.
        const source = STDLIB + 'x = 和(3, 4)';
        const generated = roundtrip(source);
        expect(generated).toContain('標準ライブラリを使う');
        expect(generated).toContain('和');
        const env = execGenerated(generated);
        expect(env['x']?.native ?? env['x']).toBe(7);
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
        // sexpr binary: (set! x + 1 2)) — the ( comes from assignment-begin, ) closes binary then assignment
        const env = execSexpr('(set! x + 1 2))');
        expect(env('x')).toBe(3);
    });

    test('if statement with prefix operator', () => {
        const env = execSexpr('(if (== 1 1) (begin (set! x 10)) (begin (set! x 20)))');
        expect(env('x')).toBe(10);
    });

    test('function definition and call', () => {
        const src = '(define (succ n) (begin (return + n 1))))\n(set! x (succ 5))';
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
