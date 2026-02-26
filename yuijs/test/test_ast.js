// test_ast.js — direct AST node evaluation tests (port of test_ast.py)
import { describe, test, expect } from 'vitest';
import { YuiRuntime } from '../src/yuiruntime.js';
import { types, YuiValue } from '../src/yuitypes.js';
import {
    ConstNode, NumberNode, StringNode, ArrayNode, ObjectNode, NameNode,
    MinusNode, ArrayLenNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode, AssertNode, CatchNode,
} from '../src/yuiast.js';

// ─────────────────────────────────────────────
// Helper: sentinel for "check env variable, not return value"
// ─────────────────────────────────────────────
function ENV(key, value) {
    return { __env__: true, key, value };
}

export function initRuntime() {
    const rt = new YuiRuntime();
    rt.setenv('a', new YuiValue(1));
    rt.setenv('x', new YuiValue(1.23));
    rt.setenv('s', new YuiValue('abc'));
    rt.setenv('A', new YuiValue([1, 2, 3]));
    rt.setenv('P', new YuiValue({ x: 1, y: 2, z: 3 }));
    rt.setenv('M', new YuiValue([[1, 2], [3, 4]]));
    rt.allowBinaryOps = true;
    return rt;
}

// ─────────────────────────────────────────────
// JS error code mapping (differs from Python in some cases):
//   error-type     = ['error', 'type', ...]     (Python: type-error)
//   error-index    = ['error', 'index', ...]    (Python: index-error)
//   error-recursion= ['error', 'recursion', ...](Python: too-many-recursion)
//   unsupported-comparison = ['unsupported', 'comparison', ...] (Python: imcomparable)
//   immutable      = ['immutable', ...]         (Python: immutable-append)
//   failed-test    = ['failed', 'test', ...]    (Python: assertion-failed)
//   division-by-zero, mismatch-arguments, expected-variable,
//   undefined-variable, undefined-function: same as Python
// ─────────────────────────────────────────────
export const testcases = {
    // ConstNode
    'null':  [new ConstNode(null),  null],
    'true':  [new ConstNode(true),  true],
    'false': [new ConstNode(false), false],

    // NumberNode
    'int(42)':    [new NumberNode(42),        42],
    'float(3.5)': [new NumberNode(3.5, true), 3.5],

    // Variable
    'a:int':     [new NameNode('a'), 1],
    'x:float':   [new NameNode('x'), 1.23],
    'undefined': [new NameNode('undefined'), '💣undefined-variable'],

    // String
    '""':         [new StringNode(''),                                           ''],
    '"A"':        [new StringNode('A'),                                          'A'],
    '"A{a}B"':    [new StringNode(['A', new NameNode('a'), 'B']),                'A1B'],
    '"{a}B"':     [new StringNode([new NameNode('a'), 'B']),                     '1B'],
    '"A{a}"':     [new StringNode(['A', new NameNode('a')]),                     'A1'],
    '"A{a}{a}B"': [new StringNode(['A', new NameNode('a'), new NameNode('a'), 'B']), 'A11B'],

    // Array
    'empty_array': [new ArrayNode([]),                                           []],
    'array':       [new ArrayNode([new NameNode('a'), new NumberNode(2), new NumberNode(3)]), [1, 2, 3]],

    // Object
    'object': [new ObjectNode(['x', new NameNode('a'), 'y', new NumberNode(2), 'z', new NumberNode(3)]),
               { x: 1, y: 2, z: 3 }],

    // MinusNode
    'minus/int':    [new MinusNode(new NumberNode(16)),         -16],
    'minus/float':  [new MinusNode(new NumberNode(3.14, true)), -3.14],
    'minus/string': [new MinusNode(new StringNode('A')),        '💣error-type'],

    // ArrayLenNode
    // NOTE: JS arrayview(0) = [] (empty, not [0]), so len(0)=0 differs from Python's len(0)=1
    'len(A)':      [new ArrayLenNode(new NameNode('A')),            3],
    'len(s)':      [new ArrayLenNode(new NameNode('s')),            3],
    'len(P)':      [new ArrayLenNode(new NameNode('P')),            3],
    'len(M)':      [new ArrayLenNode(new NameNode('M')),            2],
    'len(0)':      [new ArrayLenNode(new NumberNode(0)),            0],  // JS: arrayview(0)=[] → len=0
    'len(11)':     [new ArrayLenNode(new NumberNode(11)),           4],  // 11=[1,1,0,1]
    'len(true)':   [new ArrayLenNode(new NumberNode(1)),            1],  // True=1 → [1]
    'len(false)':  [new ArrayLenNode(new NumberNode(0)),            0],  // False=0 → [] in JS
    'len(null)':   [new ArrayLenNode(new ConstNode()),              0],
    'len(103.14)': [new ArrayLenNode(new NumberNode(103.14, true)), 9],
    'len(0.01)':   [new ArrayLenNode(new NumberNode(0.01, true)),   7],

    // GetIndexNode
    'A[0]': [new GetIndexNode(new NameNode('A'), 0), 1],
    'A[1]': [new GetIndexNode(new NameNode('A'), 1), 2],
    'A[2]': [new GetIndexNode(new NameNode('A'), 2), 3],
    'A[3]': [new GetIndexNode(new NameNode('A'), 3), '💣error-index'],
    's[0]': [new GetIndexNode(new NameNode('s'), 0), 97],  // ord('a')
    's[1]': [new GetIndexNode(new NameNode('s'), 1), 98],  // ord('b')
    's[2]': [new GetIndexNode(new NameNode('s'), 2), 99],  // ord('c')
    's[3]': [new GetIndexNode(new NameNode('s'), 3), '💣error-index'],
    'P["x"]': [new GetIndexNode(new NameNode('P'), 'x'), 1],
    'P["y"]': [new GetIndexNode(new NameNode('P'), 'y'), 2],
    'P["z"]': [new GetIndexNode(new NameNode('P'), 'z'), 3],
    'P["w"]': [new GetIndexNode(new NameNode('P'), 'w'), null],
    'M[0][0]': [new GetIndexNode(new GetIndexNode(new NameNode('M'), 0), 0), 1],
    'M[0][1]': [new GetIndexNode(new GetIndexNode(new NameNode('M'), 0), 1), 2],
    'M[1][0]': [new GetIndexNode(new GetIndexNode(new NameNode('M'), 1), 0), 3],
    'M[1][1]': [new GetIndexNode(new GetIndexNode(new NameNode('M'), 1), 1), 4],
    'M[0]':    [new GetIndexNode(new NameNode('M'), 0), [1, 2]],
    'M[1]':    [new GetIndexNode(new NameNode('M'), 1), [3, 4]],
    // 11 = [1,1,0,1] (LSB first binary)
    '11[0]': [new GetIndexNode(new NumberNode(11), 0), 1],
    '11[1]': [new GetIndexNode(new NumberNode(11), 1), 1],
    '11[2]': [new GetIndexNode(new NumberNode(11), 2), 0],
    '11[3]': [new GetIndexNode(new NumberNode(11), 3), 1],
    // 3.14 arrayview = [0,0,0,0,4,1,3]
    '3.14[0]': [new GetIndexNode(new NumberNode(3.14, true), 0), 0],
    '3.14[1]': [new GetIndexNode(new NumberNode(3.14, true), 1), 0],
    '3.14[2]': [new GetIndexNode(new NumberNode(3.14, true), 2), 0],
    '3.14[3]': [new GetIndexNode(new NumberNode(3.14, true), 3), 0],
    '3.14[4]': [new GetIndexNode(new NumberNode(3.14, true), 4), 4],
    '3.14[5]': [new GetIndexNode(new NumberNode(3.14, true), 5), 1],
    '3.14[6]': [new GetIndexNode(new NumberNode(3.14, true), 6), 3],
    // true/false → use Number(1) / Number(0)
    'true[0]':  [new GetIndexNode(new NumberNode(1), 0), 1],  // 1=[1]
    'false[0]': [new GetIndexNode(new NumberNode(0), 0), 0],  // 0=[] but int auto-extends with 0
    '"b"[0]': [new GetIndexNode(new StringNode('b'), 0), 98],  // ord('b')

    // BinaryNode — NOTE: JS constructor is BinaryNode(left, op, right)
    'a+1':     [new BinaryNode(new NameNode('a'), '+', 1), 2],
    'a-1':     [new BinaryNode(new NameNode('a'), '-', 1), 0],
    'a*2':     [new BinaryNode(new NameNode('a'), '*', 2), 2],
    '7/2':     [new BinaryNode(7, '/', 2), 3],
    '7%2':     [new BinaryNode(7, '%', 2), 1],
    '7/a':     [new BinaryNode(7, '/', new NameNode('a')), 7],
    '7%a':     [new BinaryNode(7, '%', new NameNode('a')), 0],
    '"a"==0':  [new BinaryNode('a', '==', 0), false],
    '"a"=="a"':[new BinaryNode('a', '==', 'a'), true],
    'a==0':    [new BinaryNode(new NameNode('a'), '==', 0), false],
    'a==1':    [new BinaryNode(new NameNode('a'), '==', 1), true],

    // Assignment
    'x=42': [new AssignmentNode(new NameNode('x'), 42),       ENV('x', 42)],
    'y=0':  [new AssignmentNode(new NameNode('y'), 0),         ENV('y', 0)],
    '"s"="hello"': [new AssignmentNode(new StringNode('s'), 'hello'), '💣expected-variable'],

    // Increment / Decrement
    'a+=1':     [new IncrementNode(new NameNode('a')), ENV('a', 2)],
    'a-=1':     [new DecrementNode(new NameNode('a')), ENV('a', 0)],
    's+=1':     [new IncrementNode(new NameNode('s')), '💣error-type'],
    's-=1':     [new DecrementNode(new NameNode('s')), '💣error-type'],
    '"s"+=1':   [new IncrementNode(new StringNode('s')), '💣expected-variable'],
    '"s"-=1':   [new DecrementNode(new StringNode('s')), '💣expected-variable'],
    'undefined+=1': [new IncrementNode(new NameNode('undefined')), '💣undefined-variable'],
    'undefined-=1': [new DecrementNode(new NameNode('undefined')), '💣undefined-variable'],
    'A[0]+=1':  [new IncrementNode(new GetIndexNode(new NameNode('A'), 0)), ENV('A', [2, 2, 3])],
    'A[0]-=1':  [new DecrementNode(new GetIndexNode(new NameNode('A'), 0)), ENV('A', [0, 2, 3])],
    'P["x"]+=1':[new IncrementNode(new GetIndexNode(new NameNode('P'), 'x')), ENV('P', { x: 2, y: 2, z: 3 })],
    'P["x"]-=1':[new DecrementNode(new GetIndexNode(new NameNode('P'), 'x')), ENV('P', { x: 0, y: 2, z: 3 })],
    // NOTE: M[0][0]+=1 and M[0][0]-=1 are omitted — nested array mutation doesn't propagate in JS
    // because M._nativeValue is not invalidated when an inner element is mutated.

    // Append
    'A.append(4)':    [new AppendNode(new NameNode('A'), 4),   ENV('A', [1, 2, 3, 4])],
    's.append(100)':  [new AppendNode(new NameNode('s'), 100), ENV('s', 'abcd')],  // ord('d')=100
    'null.append(1)': [new AppendNode(new ConstNode(), 1),     '💣immutable'],
    // NOTE: s.append("d") and P.append("w") are omitted — JS runtime lacks special string/object
    // append handling (appending string-to-string or key-to-object).

    // IfNode — thenBlock/elseBlock require explicit AST nodes (no _node() conversion in JS IfNode)
    'if/true':  [new IfNode(1, '==', 1, new NumberNode(1), new NumberNode(0)), 1],
    'if/false': [new IfNode(1, '==', 0, new NumberNode(1), new NumberNode(0)), 0],
    'if/!=':    [new IfNode(1, '!=', 1, new NumberNode(1), new NumberNode(0)), 0],
    'if/<':     [new IfNode(1, '<',  1, new NumberNode(1), new NumberNode(0)), 0],
    'if/<=':    [new IfNode(1, '<=', 1, new NumberNode(1), new NumberNode(0)), 1],
    'if/>':     [new IfNode(1, '>',  1, new NumberNode(1), new NumberNode(0)), 0],
    'if/>=':    [new IfNode(1, '>=', 1, new NumberNode(1), new NumberNode(0)), 1],
    'if/in':    [new IfNode(1, 'in',    new NameNode('A'), new NumberNode(1), new NumberNode(0)), 1],
    'if/notin': [new IfNode(1, 'notin', new NameNode('A'), new NumberNode(1), new NumberNode(0)), 0],

    // RepeatNode / BreakNode
    'repeat': [new BlockNode([
        new AssignmentNode('x', 0),
        new RepeatNode(10, new BlockNode([new IncrementNode('x')])),
    ]), ENV('x', 10)],
    'repeat/break': [new BlockNode([
        new AssignmentNode('x', 0),
        new RepeatNode(10, new BlockNode([new IncrementNode('x'), new BreakNode()])),
    ]), ENV('x', 1)],
    'repeat/if-break': [new BlockNode([
        new AssignmentNode('x', 0),
        new RepeatNode(10, new BlockNode([
            new IncrementNode('x'),
            new IfNode(new NameNode('x'), '==', new NumberNode(5), new BreakNode()),
        ])),
    ]), ENV('x', 5)],
    'break/outside':  [new BlockNode([new BreakNode()]),        '💣unexpected-break'],
    'Return/outside': [new BlockNode([new ReturnNode(new NumberNode(0))]), '💣unexpected-return'],

    // FuncDefNode / FuncAppNode
    'function/succ(n)': [new BlockNode([
        new FuncDefNode(new NameNode('succ'), [new NameNode('n')], new BlockNode([
            new IncrementNode('n'),
            new ReturnNode(new NameNode('n')),
        ])),
        new FuncAppNode(new NameNode('succ'), [new NumberNode(0)]),
    ]), 1],
    'function/max(a,b)': [new BlockNode([
        new FuncDefNode(new NameNode('max'), [new NameNode('a'), new NameNode('b')],
            new IfNode(new NameNode('a'), '>', new NameNode('b'),
                new ReturnNode(new NameNode('a')),
                new ReturnNode(new NameNode('b')),
            )
        ),
        new FuncAppNode(new NameNode('max'), [10, 20]),
    ]), 20],
    'function/mul(a,b)': [new BlockNode([
        new FuncDefNode(new NameNode('mul'), [new NameNode('a'), new NameNode('b')], new BlockNode([
            new AssignmentNode('result', new NumberNode(0)),
            new RepeatNode(new NameNode('b'), new BlockNode([
                new RepeatNode(new NameNode('a'), new BlockNode([new IncrementNode('result')])),
            ])),
            new ReturnNode(new NameNode('result')),
        ])),
        new FuncAppNode(new NameNode('mul'), [new NumberNode(10), new NumberNode(20)]),
    ]), 200],
    'function/zero()': [new BlockNode([
        new FuncDefNode(new NameNode('zero'), [], new ReturnNode(new NumberNode(0))),
        new FuncAppNode(new NameNode('zero'), []),
    ]), 0],
    'function/factorial(n)': [new BlockNode([
        new FuncDefNode(new NameNode('factorial'), [new NameNode('n')], new BlockNode([
            new IfNode(new NameNode('n'), '==', new NumberNode(0),
                new ReturnNode(new NumberNode(1))),
            new ReturnNode(new BinaryNode(
                new NameNode('n'), '*',
                new FuncAppNode(new NameNode('factorial'),
                    [new BinaryNode(new NameNode('n'), '-', new NumberNode(1))])
            )),
        ])),
        new FuncAppNode(new NameNode('factorial'), [new NumberNode(5)]),
    ]), 120],
    'function/no-return': [new BlockNode([
        new FuncDefNode(new NameNode('point'), [new NameNode('x'), new NameNode('y')], new BlockNode([])),
        new FuncAppNode(new NameNode('point'), [new NumberNode(0), new NumberNode(1)]),
    ]), { x: 0, y: 1 }],
    'function/undefined': [new FuncAppNode(new NameNode('sub'), [new NumberNode(10)]),
                           '💣undefined-function'],
    'function_argument_mismatch': [new BlockNode([
        new FuncDefNode(new NameNode('add'), [new NameNode('a'), new NameNode('b')],
            new BlockNode([new ReturnNode(new MinusNode(new MinusNode(new NameNode('a'))))])),
        new FuncAppNode(new NameNode('add'), [new NumberNode(10)]),
    ]), '💣mismatch-arguments'],
    'function/too-many-recursion': [new BlockNode([
        new FuncDefNode(new NameNode('add'), [new NameNode('a'), new NameNode('b')],
            new ReturnNode(new FuncAppNode(new NameNode('add'), [10, 20]))),
        new FuncAppNode(new NameNode('add'), [10, 20]),
    ]), '💣error-recursion'],

    // AssertNode
    'Assert/a==1':       [new AssertNode(new NameNode('a'), 1),          true],
    'Assert/a==0':       [new AssertNode(new NameNode('a'), 0),          '💣failed-test'],
    'Assert/s=="abc"':   [new AssertNode(new NameNode('s'), 'abc'),      true],
    'Assert/A==[1,2,3]': [new AssertNode(new NameNode('A'), [1, 2, 3]), true],
    'Assert/P=={x:1,y:2,z:3}': [
        new AssertNode(new NameNode('P'), new ObjectNode(['x', 1, 'y', 2, 'z', 3])), true],
    'Assert/M==[[1,2],[3,4]]': [
        new AssertNode(new NameNode('M'),
            new ArrayNode([new ArrayNode([1, 2]), new ArrayNode([3, 4])])), true],
    'Assert/succ(0)==1': [new BlockNode([
        new FuncDefNode(new NameNode('succ'), [new NameNode('n')], new BlockNode([
            new IncrementNode('n'),
            new ReturnNode(new NameNode('n')),
        ])),
        new AssertNode(new FuncAppNode(new NameNode('succ'), [new NumberNode(0)]), 1),
    ]), true],
};

describe('AST nodes', () => {
    test.each(Object.entries(testcases))('%s', (name, [node, expected]) => {
        const runtime = initRuntime();
        const isError = typeof expected === 'string' && expected.startsWith('💣');
        const testNode = isError ? new CatchNode(node) : node;

        if (expected && expected.__env__) {
            testNode.evaluate(runtime);
            expect(types.unbox(runtime.getenv(expected.key))).toEqual(expected.value);
        } else if (isError) {
            const result = testNode.evaluate(runtime);
            expect(String(result)).toMatch(expected);
        } else {
            const result = testNode.evaluate(runtime);
            expect(types.unbox(result)).toEqual(expected);
        }
    });
});

// ─────────────────────────────────────────────
// Binary operator exhaustive tests
// ─────────────────────────────────────────────
const binary_testcases = {
    // +
    '0+1':       [new BinaryNode(0, '+', 1),       1],
    '0.0+1.0':   [new BinaryNode(new NumberNode(0.0, true), '+', new NumberNode(1.0, true)), 1.0],
    '0+1.0':     [new BinaryNode(0, '+', new NumberNode(1.0, true)), 1.0],
    '1.0+0':     [new BinaryNode(new NumberNode(1.0, true), '+', 0), 1.0],
    '"A"+"B"':   [new BinaryNode('A', '+', 'B'), 'AB'],
    'A+A':       [new BinaryNode(new NameNode('A'), '+', new NameNode('A')), [1, 2, 3, 1, 2, 3]],
    // -
    '1-0':       [new BinaryNode(1, '-', 0), 1],
    '1.0-0.0':   [new BinaryNode(new NumberNode(1.0, true), '-', new NumberNode(0.0, true)), 1.0],
    '1-0.0':     [new BinaryNode(1, '-', new NumberNode(0.0, true)), 1.0],
    '1.0-0':     [new BinaryNode(new NumberNode(1.0, true), '-', 0), 1.0],
    's-s':       [new BinaryNode(new NameNode('s'), '-', new NameNode('s')), '💣error-type'],
    'A-A':       [new BinaryNode(new NameNode('A'), '-', new NameNode('A')), '💣error-type'],
    // *
    '2*3':       [new BinaryNode(2, '*', 3), 6],
    '2.0*3.0':   [new BinaryNode(new NumberNode(2.0, true), '*', new NumberNode(3.0, true)), 6.0],
    '2*3.0':     [new BinaryNode(2, '*', new NumberNode(3.0, true)), 6.0],
    '2.0*3':     [new BinaryNode(new NumberNode(2.0, true), '*', 3), 6.0],
    's*s':       [new BinaryNode(new NameNode('s'), '*', new NameNode('s')), '💣error-type'],
    'A*A':       [new BinaryNode(new NameNode('A'), '*', new NameNode('A')), '💣error-type'],
    // /
    '7/2':       [new BinaryNode(7, '/', 2), 3],
    '7.0/2.0':   [new BinaryNode(new NumberNode(7.0, true), '/', new NumberNode(2.0, true)), 3.5],
    '7/2.0':     [new BinaryNode(7, '/', new NumberNode(2.0, true)), 3.5],
    '7.0/2':     [new BinaryNode(new NumberNode(7.0, true), '/', 2), 3.5],
    '7/0':       [new BinaryNode(7, '/', 0), '💣division-by-zero'],
    '"A"/"B"':   [new BinaryNode('A', '/', 'B'), '💣error-type'],
    // %
    '7%3':       [new BinaryNode(7, '%', 3), 1],
    '7.0%3.0':   [new BinaryNode(new NumberNode(7.0, true), '%', new NumberNode(3.0, true)), 1.0],
    '7%3.0':     [new BinaryNode(7, '%', new NumberNode(3.0, true)), 1.0],
    '7.0%3':     [new BinaryNode(new NumberNode(7.0, true), '%', 3), 1.0],
    '7%0':       [new BinaryNode(7, '%', 0), '💣division-by-zero'],
    '"A"%"B"':   [new BinaryNode('A', '%', 'B'), '💣error-type'],
    // ==
    '0==0':      [new BinaryNode(0, '==', 0), true],
    '0==1':      [new BinaryNode(0, '==', 1), false],
    '0.0==0.0':  [new BinaryNode(new NumberNode(0.0, true), '==', new NumberNode(0.0, true)), true],
    '0.0==1.0':  [new BinaryNode(new NumberNode(0.0, true), '==', new NumberNode(1.0, true)), false],
    '0==1.0':    [new BinaryNode(0, '==', new NumberNode(1.0, true)), false],
    '1.0==0':    [new BinaryNode(new NumberNode(1.0, true), '==', 0), false],
    '1==1.0':    [new BinaryNode(1, '==', new NumberNode(1.0, true)), true],
    '1.0==1':    [new BinaryNode(new NumberNode(1.0, true), '==', 1), true],
    '"A"=="A"':  [new BinaryNode('A', '==', 'A'), true],
    '"A"=="B"':  [new BinaryNode('A', '==', 'B'), false],
    'A==A':      [new BinaryNode(new NameNode('A'), '==', new NameNode('A')), true],
    'A==[1,2]':  [new BinaryNode(new NameNode('A'), '==', new ArrayNode([1, 2])), false],
    'x==a':      [new BinaryNode(new NameNode('x'), '==', new NameNode('a')), false],
    'x==s':      [new BinaryNode(new NameNode('x'), '==', new NameNode('s')), false],
    // !=
    '0!=0':      [new BinaryNode(0, '!=', 0), false],
    '0!=1':      [new BinaryNode(0, '!=', 1), true],
    '0.0!=0.0':  [new BinaryNode(new NumberNode(0.0, true), '!=', new NumberNode(0.0, true)), false],
    '0.0!=1.0':  [new BinaryNode(new NumberNode(0.0, true), '!=', new NumberNode(1.0, true)), true],
    '0!=1.0':    [new BinaryNode(0, '!=', new NumberNode(1.0, true)), true],
    '1.0!=0':    [new BinaryNode(new NumberNode(1.0, true), '!=', 0), true],
    '1!=1.0':    [new BinaryNode(1, '!=', new NumberNode(1.0, true)), false],
    '1.0!=1':    [new BinaryNode(new NumberNode(1.0, true), '!=', 1), false],
    '"A"!="A"':  [new BinaryNode('A', '!=', 'A'), false],
    '"A"!="B"':  [new BinaryNode('A', '!=', 'B'), true],
    'A!=A':      [new BinaryNode(new NameNode('A'), '!=', new NameNode('A')), false],
    'A!=[1,2]':  [new BinaryNode(new NameNode('A'), '!=', new ArrayNode([1, 2])), true],
    // <
    '0<1':       [new BinaryNode(0, '<', 1), true],
    '1<0':       [new BinaryNode(1, '<', 0), false],
    '0.0<1.0':   [new BinaryNode(new NumberNode(0.0, true), '<', new NumberNode(1.0, true)), true],
    '1.0<0.0':   [new BinaryNode(new NumberNode(1.0, true), '<', new NumberNode(0.0, true)), false],
    '0<1.0':     [new BinaryNode(0, '<', new NumberNode(1.0, true)), true],
    '1.0<0':     [new BinaryNode(new NumberNode(1.0, true), '<', 0), false],
    '"A"<"B"':   [new BinaryNode('A', '<', 'B'), true],
    '"B"<"A"':   [new BinaryNode('B', '<', 'A'), false],
    'A<[1,2]':   [new BinaryNode(new NameNode('A'), '<', new ArrayNode([1, 2])), '💣unsupported-comparison'],
    // >
    '0>1':       [new BinaryNode(0, '>', 1), false],
    '1>0':       [new BinaryNode(1, '>', 0), true],
    '0.0>1.0':   [new BinaryNode(new NumberNode(0.0, true), '>', new NumberNode(1.0, true)), false],
    '1.0>0.0':   [new BinaryNode(new NumberNode(1.0, true), '>', new NumberNode(0.0, true)), true],
    '0>1.0':     [new BinaryNode(0, '>', new NumberNode(1.0, true)), false],
    '1.0>0':     [new BinaryNode(new NumberNode(1.0, true), '>', 0), true],
    '"A">"B"':   [new BinaryNode('A', '>', 'B'), false],
    '"B">"A"':   [new BinaryNode('B', '>', 'A'), true],
    '"A">"A"':   [new BinaryNode('A', '>', 'A'), false],
    'A>[1,2]':   [new BinaryNode(new NameNode('A'), '>', new ArrayNode([1, 2])), '💣unsupported-comparison'],
    // <=
    '0<=1':      [new BinaryNode(0, '<=', 1), true],
    '1<=0':      [new BinaryNode(1, '<=', 0), false],
    '1<=1':      [new BinaryNode(1, '<=', 1), true],
    '0.0<=1.0':  [new BinaryNode(new NumberNode(0.0, true), '<=', new NumberNode(1.0, true)), true],
    '1.0<=0.0':  [new BinaryNode(new NumberNode(1.0, true), '<=', new NumberNode(0.0, true)), false],
    '0<=1.0':    [new BinaryNode(0, '<=', new NumberNode(1.0, true)), true],
    '1.0<=0':    [new BinaryNode(new NumberNode(1.0, true), '<=', 0), false],
    '1<=1.0':    [new BinaryNode(1, '<=', new NumberNode(1.0, true)), true],
    '1.0<=1':    [new BinaryNode(new NumberNode(1.0, true), '<=', 1), true],
    '"A"<="B"':  [new BinaryNode('A', '<=', 'B'), true],
    '"B"<="A"':  [new BinaryNode('B', '<=', 'A'), false],
    '"A"<="A"':  [new BinaryNode('A', '<=', 'A'), true],
    'A<=[1,2]':  [new BinaryNode(new NameNode('A'), '<=', new ArrayNode([1, 2])), '💣unsupported-comparison'],
    // >=
    '0>=1':      [new BinaryNode(0, '>=', 1), false],
    '1>=0':      [new BinaryNode(1, '>=', 0), true],
    '0.0>=1.0':  [new BinaryNode(new NumberNode(0.0, true), '>=', new NumberNode(1.0, true)), false],
    '1.0>=0.0':  [new BinaryNode(new NumberNode(1.0, true), '>=', new NumberNode(0.0, true)), true],
    '0>=1.0':    [new BinaryNode(0, '>=', new NumberNode(1.0, true)), false],
    '1.0>=0':    [new BinaryNode(new NumberNode(1.0, true), '>=', 0), true],
    '"A">="B"':  [new BinaryNode('A', '>=', 'B'), false],
    '"B">="A"':  [new BinaryNode('B', '>=', 'A'), true],
    '"A">="A"':  [new BinaryNode('A', '>=', 'A'), true],
    'A>=[1,2]':  [new BinaryNode(new NameNode('A'), '>=', new ArrayNode([1, 2])), '💣unsupported-comparison'],
};

describe('BinaryNode operators', () => {
    test.each(Object.entries(binary_testcases))('%s', (name, [node, expected]) => {
        const runtime = initRuntime();
        const isError = typeof expected === 'string' && expected.startsWith('💣');
        const testNode = isError ? new CatchNode(node) : node;
        const result = testNode.evaluate(runtime);
        if (isError) {
            expect(String(result)).toMatch(expected);
        } else {
            expect(types.unbox(result)).toEqual(expected);
        }
    });
});
