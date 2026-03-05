// yuiexample.js — port of yuichan/yuiexample.py (CLI-independent parts only)

import {
    ConstNode, NumberNode, StringNode, NameNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode, PassNode,
    FuncDefNode, FuncAppNode, ReturnNode, ImportNode,
    PrintExpressionNode,
    GetIndexNode, AssertNode,
} from './yuiast.js';

import { CodingVisitor } from './yuicoding.js';

/** BlockNode から AssertNode を取り除いた新しい BlockNode を返す。
 *  直前の "Test ..." PassNode もあわせて除去する。
 */
function _stripAsserts(block) {
    const filtered = [];
    for (const stmt of block.statements) {
        if (stmt instanceof AssertNode) {
            if (filtered.length > 0) {
                const prev = filtered[filtered.length - 1];
                if (prev instanceof PassNode
                        && prev.comment
                        && prev.comment.toLowerCase().startsWith('test')) {
                    filtered.pop();
                }
            }
        } else {
            filtered.push(stmt);
        }
    }
    return new BlockNode(filtered, block.topLevel);
}

export class YuiExample {
    /** kind: 'sample' | 'test' | 'both' */
    constructor(name, description, astNode, kind = 'both') {
        this.name = name;
        this.description = description;
        this.astNode = astNode;
        this.kind = kind;
    }

    generate(syntax = 'yui', includeAsserts = true) {
        const node = includeAsserts ? this.astNode : _stripAsserts(this.astNode);
        const visitor = new CodingVisitor(syntax);
        return visitor.emit(node);
    }
}

export function exampleHelloWorld() {
    const statements = [
        new PassNode('Print "Hello, world!"'),
        new PrintExpressionNode(new StringNode('Hello, world!')),
    ];
    return new YuiExample(
        'hello_world',
        "Print 'Hello, world!'",
        new BlockNode(statements, true),
        'sample',
    );
}

export function exampleVariables() {
    const statements = [
        new PassNode('Define variables x and y'),
        new AssignmentNode(new NameNode('x'), new NumberNode(1)),
        new AssignmentNode(new NameNode('y'), new MinusNode(new NumberNode(2))),
        new PassNode('Increment x'),
        new IncrementNode(new NameNode('x')),
        new PassNode('Decrement y'),
        new DecrementNode(new NameNode('y')),
        new PassNode('Test that x is 2 and y is -3'),
        new AssertNode(new NameNode('x'), new NumberNode(2)),
        new AssertNode(new NameNode('y'), new MinusNode(new NumberNode(3))),
    ];
    return new YuiExample(
        'variables',
        'Basic variable definition and increment/decrement',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleLoop() {
    const statements = [
        new PassNode('Loop 10 times and break at 5'),
        new AssignmentNode(new NameNode('count'), new NumberNode(0)),
        new RepeatNode(
            new NumberNode(10),
            new BlockNode([
                new IncrementNode(new NameNode('count')),
                new IfNode(new NameNode('count'), '==', new NumberNode(5),
                    new BlockNode(new BreakNode())
                ),
            ])
        ),
        new PassNode('Test that count is 5'),
        new AssertNode(new NameNode('count'), new NumberNode(5)),
    ];
    return new YuiExample(
        'loop',
        'Loop 10 times and break at 5',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleFizzBuzz() {
    const statements = [
        new PassNode('FizzBuzz from 1 to 100, collected into a list'),
        new AssignmentNode(new NameNode('result'), new ArrayNode([])),
        new AssignmentNode(new NameNode('i'),    new NumberNode(0)),
        new AssignmentNode(new NameNode('fizz'), new NumberNode(0)),
        new AssignmentNode(new NameNode('buzz'), new NumberNode(0)),
        new RepeatNode(new NumberNode(100), new BlockNode([
            new IncrementNode(new NameNode('i')),
            new IncrementNode(new NameNode('fizz')),
            new IncrementNode(new NameNode('buzz')),
            new IfNode(new NameNode('fizz'), '==', new NumberNode(3),
                new BlockNode(new AssignmentNode(new NameNode('fizz'), new NumberNode(0)))),
            new IfNode(new NameNode('buzz'), '==', new NumberNode(5),
                new BlockNode(new AssignmentNode(new NameNode('buzz'), new NumberNode(0)))),
            new IfNode(new NameNode('fizz'), '==', new NumberNode(0),
                new BlockNode(
                    new IfNode(new NameNode('buzz'), '==', new NumberNode(0),
                        new BlockNode(new AppendNode(new NameNode('result'), new StringNode('FizzBuzz'))),
                        new BlockNode(new AppendNode(new NameNode('result'), new StringNode('Fizz'))),
                    )
                ),
                new BlockNode(
                    new IfNode(new NameNode('buzz'), '==', new NumberNode(0),
                        new BlockNode(new AppendNode(new NameNode('result'), new StringNode('Buzz'))),
                        new BlockNode(new AppendNode(new NameNode('result'), new NameNode('i'))),
                    )
                ),
            ),
        ])),
        new PrintExpressionNode(new NameNode('result')),
        new PassNode('Test: length is 100'),
        new AssertNode(new ArrayLenNode(new NameNode('result')), new NumberNode(100)),
        new PassNode('Test: spot-check Fizz, Buzz, FizzBuzz positions'),
        new AssertNode(new GetIndexNode(new NameNode('result'), new NumberNode(2)),  new StringNode('Fizz')),
        new AssertNode(new GetIndexNode(new NameNode('result'), new NumberNode(4)),  new StringNode('Buzz')),
        new AssertNode(new GetIndexNode(new NameNode('result'), new NumberNode(14)), new StringNode('FizzBuzz')),
    ];
    return new YuiExample(
        'fizzbuzz',
        'FizzBuzz from 1 to 100, collected into a list',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleNestedConditionalBranches() {
    const thenBlock = new IncrementNode(new NameNode('y'));
    const elseBlock = new IncrementNode(new NameNode('z'));
    const statements = [
        new PassNode('Test nested conditions on x and y'),
        new AssignmentNode(new NameNode('x'), new NumberNode(1)),
        new AssignmentNode(new NameNode('y'), new NumberNode(2)),
        new AssignmentNode(new NameNode('z'), new NumberNode(3)),
        new PassNode('If x is 0, check y and increment y or z accordingly'),
        new IfNode(new NameNode('x'), '==', new NumberNode(0),
            new BlockNode(new IfNode(new NameNode('y'), '==', new NumberNode(1), thenBlock, elseBlock)),
            new BlockNode(new IfNode(new NameNode('y'), '==', new NumberNode(2), thenBlock, elseBlock))
        ),
        new PassNode('Test that y was incremented and z was not'),
        new AssertNode(new NameNode('y'), new NumberNode(3)),
    ];
    return new YuiExample(
        'nested_conditional_branches',
        'Nested conditional branching',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleComparisons() {
    const thenBlock = new IncrementNode(new NameNode('y'));
    const elseBlock = new IncrementNode(new NameNode('z'));
    const statements = [
        new PassNode('Various comparisons on x'),
        new AssignmentNode(new NameNode('x'), new NumberNode(1)),
        new AssignmentNode(new NameNode('y'), new NumberNode(0)),
        new AssignmentNode(new NameNode('z'), new NumberNode(0)),
        new PassNode('Is x equal to 1?'),
        new IfNode(new NameNode('x'), '==', new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Is x not equal to 1?'),
        new IfNode(new NameNode('x'), '!=', new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Is x less than 1?'),
        new IfNode(new NameNode('x'), '<',  new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Is x greater than 1?'),
        new IfNode(new NameNode('x'), '>',  new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Is x less than or equal to 1?'),
        new IfNode(new NameNode('x'), '<=', new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Is x greater than or equal to 1?'),
        new IfNode(new NameNode('x'), '>=', new NumberNode(1), thenBlock, elseBlock),
        new PassNode('Test that all conditions were evaluated correctly'),
        new AssertNode(new NameNode('y'), new NumberNode(3)),
        new AssertNode(new NameNode('z'), new NumberNode(3)),
    ];
    return new YuiExample(
        'comparisons',
        'Comparison operations',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleArray() {
    const statements = [
        new PassNode('Create an array A with elements 1, 2, 3'),
        new AssignmentNode(new NameNode('A'),
            new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)])
        ),
        new PassNode('Append 0 to the end of A'),
        new AppendNode(new NameNode('A'), new NumberNode(0)),
        new PassNode('Increment the first element of A'),
        new IncrementNode(new GetIndexNode(new NameNode('A'), new NumberNode(0))),
        new PassNode('If 2 is in A, set the first element to the fourth element'),
        new IfNode(new NumberNode(2), 'in', new NameNode('A'),
            new AssignmentNode(
                new GetIndexNode(new NameNode('A'), new NumberNode(0)),
                new GetIndexNode(new NameNode('A'), new NumberNode(3))
            )
        ),
        new PassNode('Test that the array has 4 elements'),
        new AssertNode(new ArrayLenNode(new NameNode('A')), new NumberNode(4)),
    ];
    return new YuiExample(
        'array',
        'Array creation and element manipulation',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleStrings() {
    const statements = [
        new PassNode("Create a string s with value 'hello'"),
        new AssignmentNode(new NameNode('s'), new StringNode('hello')),
        new PassNode("Set the first character of s to 'H'"),
        new PassNode('Note: strings are just the array of character codes. So we can manipulate them like arrays.'),
        new AssignmentNode(
            new GetIndexNode(new NameNode('s'), new NumberNode(0)),
            new GetIndexNode(new StringNode('H'), new NumberNode(0))
        ),
        new PassNode('Append " world" to s'),
        new AssignmentNode(new NameNode('t'), new StringNode(' world')),
        new AssignmentNode(new NameNode('i'), new NumberNode(0)),
        new RepeatNode(new ArrayLenNode(new NameNode('t')), new BlockNode([
            new AppendNode(new NameNode('s'), new GetIndexNode(new NameNode('t'), new NameNode('i'))),
            new IncrementNode(new NameNode('i')),
        ])),
        new PassNode("Test that s is now 'Hello world'"),
        new AssertNode(new NameNode('s'), new StringNode('Hello world')),
    ];
    return new YuiExample(
        'strings',
        'String creation and manipulation',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleObjects() {
    const statements = [
        new PassNode('Create an object O with properties x and y'),
        new AssignmentNode(new NameNode('O'), new ObjectNode([
            new StringNode('x'), new NumberNode(0),
            new StringNode('y'), new NumberNode(0),
        ])),
        new PassNode('Set the x property of O to 1'),
        new AssignmentNode(
            new GetIndexNode(new NameNode('O'), new StringNode('x')),
            new NumberNode(1)
        ),
        new PassNode('Set the y property of O to 2'),
        new AssignmentNode(
            new GetIndexNode(new NameNode('O'), new StringNode('y')),
            new NumberNode(2)
        ),
        new PassNode('Test that O has properties x=1 and y=2'),
        new AssertNode(new GetIndexNode(new NameNode('O'), new StringNode('x')), new NumberNode(1)),
        new AssertNode(new GetIndexNode(new NameNode('O'), new StringNode('y')), new NumberNode(2)),
    ];
    return new YuiExample(
        'objects',
        'Object creation and property manipulation',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleFunction() {
    const statements = [
        new PassNode('Define function that adds 1'),
        new FuncDefNode(
            new NameNode('succ'), [new NameNode('n')],
            new BlockNode([
                new IncrementNode(new NameNode('n')),
                new ReturnNode(new NameNode('n')),
            ])
        ),
        new AssignmentNode(new NameNode('result'),
            new FuncAppNode(new NameNode('succ'), [new NumberNode(0)])
        ),
        new AssertNode(new NameNode('result'), new NumberNode(1)),
    ];
    return new YuiExample(
        'function',
        'Function definition and call (increment function)',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleFunctionNoArgument() {
    const statements = [
        new PassNode('Define function that returns 0'),
        new FuncDefNode(
            new NameNode('zero'), [],
            new BlockNode(new ReturnNode(new NumberNode(0)))
        ),
        new AssertNode(new FuncAppNode(new NameNode('zero'), []), new NumberNode(0)),
    ];
    return new YuiExample(
        'function_no_argument',
        'Function definition and call (zero-argument function)',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleFunctionWithoutReturn() {
    const statements = [
        new PassNode('Define function that creates a point object'),
        new FuncDefNode(
            new NameNode('point'), [new NameNode('x'), new NameNode('y')],
            new BlockNode([
                new PassNode('If function does not return anything, return the local environment as an object'),
            ])
        ),
        new AssignmentNode(new NameNode('O'),
            new FuncAppNode(new NameNode('point'), [new NumberNode(0), new NumberNode(0)])
        ),
        new AssertNode(new GetIndexNode(new NameNode('O'), new StringNode('x')), new NumberNode(0)),
    ];
    return new YuiExample(
        'function_without_return',
        'Function definition and call (function without return value)',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleRecursiveFunction() {
    const statements = [
        new PassNode('Define recursive function that computes factorial'),
        new FuncDefNode(
            new NameNode('fact'), [new NameNode('n')],
            new BlockNode([
                new IfNode(new NameNode('n'), '==', new NumberNode(0),
                    new BlockNode([new ReturnNode(new NumberNode(1))]),
                    new BlockNode([
                        new PassNode('Yui does not have arithmetic operators.'),
                        new ReturnNode(new FuncAppNode(new NameNode('multiplex'), [
                            new NameNode('n'),
                            new FuncAppNode(new NameNode('fact'), [
                                new FuncAppNode(new NameNode('decrease'), [new NameNode('n')])
                            ])
                        ]))
                    ])
                )
            ])
        ),
        new PassNode('multiplex(a, b) function for a * b.'),
        new FuncDefNode(
            new NameNode('multiplex'), [new NameNode('a'), new NameNode('b')],
            new BlockNode([
                new AssignmentNode(new NameNode('result'), new NumberNode(0)),
                new RepeatNode(new NameNode('b'), new BlockNode([
                    new RepeatNode(new NameNode('a'), new BlockNode([
                        new IncrementNode(new NameNode('result'))
                    ]))
                ])),
                new ReturnNode(new NameNode('result'))
            ])
        ),
        new PassNode('decrease(n) function for n-1.'),
        new FuncDefNode(
            new NameNode('decrease'), [new NameNode('n')],
            new BlockNode([
                new DecrementNode(new NameNode('n')),
                new ReturnNode(new NameNode('n'))
            ])
        ),
        new PassNode('Test fact(0) is 1'),
        new AssertNode(new FuncAppNode(new NameNode('fact'), [new NumberNode(0)]), new NumberNode(1)),
        new PassNode('Test that fact(5) is 120'),
        new AssertNode(new FuncAppNode(new NameNode('fact'), [new NumberNode(5)]), new NumberNode(120)),
    ];
    return new YuiExample(
        'recursive_function',
        'Recursive function definition and call (factorial function)',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleFloatAdd() {
    const statements = [
        new PassNode('float format: [sign, d1..d7]  sign=1 or -1, d1..d7 = abs(x)*1e6 digits'),
        new PassNode('float_add(a, b): add two same-sign float arrays (no stdlib)'),
        new FuncDefNode(
            new NameNode('float_add'), [new NameNode('a'), new NameNode('b')],
            new BlockNode([
                new AssignmentNode(new NameNode('result'), new ArrayNode([
                    new GetIndexNode(new NameNode('a'), new NumberNode(0)),
                    new NumberNode(0), new NumberNode(0), new NumberNode(0),
                    new NumberNode(0), new NumberNode(0), new NumberNode(0), new NumberNode(0),
                ])),
                new AssignmentNode(new NameNode('carry'), new NumberNode(0)),
                new AssignmentNode(new NameNode('i'), new NumberNode(7)),
                new RepeatNode(new NumberNode(7), new BlockNode([
                    new AssignmentNode(new NameNode('sum'), new NameNode('carry')),
                    new RepeatNode(
                        new GetIndexNode(new NameNode('a'), new NameNode('i')),
                        new BlockNode([new IncrementNode(new NameNode('sum'))])
                    ),
                    new RepeatNode(
                        new GetIndexNode(new NameNode('b'), new NameNode('i')),
                        new BlockNode([new IncrementNode(new NameNode('sum'))])
                    ),
                    new AssignmentNode(new NameNode('carry'), new NumberNode(0)),
                    new IfNode(new NameNode('sum'), '>=', new NumberNode(10), new BlockNode([
                        new IncrementNode(new NameNode('carry')),
                        new RepeatNode(new NumberNode(10), new BlockNode([
                            new DecrementNode(new NameNode('sum')),
                        ])),
                    ])),
                    new AssignmentNode(
                        new GetIndexNode(new NameNode('result'), new NameNode('i')),
                        new NameNode('sum')
                    ),
                    new DecrementNode(new NameNode('i')),
                ])),
                new ReturnNode(new NameNode('result')),
            ])
        ),
        new PassNode('3.14 + 2.50 = 5.64'),
        new AssignmentNode(new NameNode('a'), new ArrayNode([
            new NumberNode(1), new NumberNode(3), new NumberNode(1), new NumberNode(4),
            new NumberNode(0), new NumberNode(0), new NumberNode(0), new NumberNode(0),
        ])),
        new AssignmentNode(new NameNode('b'), new ArrayNode([
            new NumberNode(1), new NumberNode(2), new NumberNode(5), new NumberNode(0),
            new NumberNode(0), new NumberNode(0), new NumberNode(0), new NumberNode(0),
        ])),
        new AssignmentNode(new NameNode('c'),
            new FuncAppNode(new NameNode('float_add'), [new NameNode('a'), new NameNode('b')])
        ),
        new PassNode('c == [1, 5, 6, 4, 0, 0, 0, 0]  (5.640000)'),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(0)), new NumberNode(1)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(1)), new NumberNode(5)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(2)), new NumberNode(6)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(3)), new NumberNode(4)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(4)), new NumberNode(0)),
        new PassNode('1.99 + 1.01 = 3.00  (tests carry propagation)'),
        new AssignmentNode(new NameNode('a'), new ArrayNode([
            new NumberNode(1), new NumberNode(1), new NumberNode(9), new NumberNode(9),
            new NumberNode(0), new NumberNode(0), new NumberNode(0), new NumberNode(0),
        ])),
        new AssignmentNode(new NameNode('b'), new ArrayNode([
            new NumberNode(1), new NumberNode(1), new NumberNode(0), new NumberNode(1),
            new NumberNode(0), new NumberNode(0), new NumberNode(0), new NumberNode(0),
        ])),
        new AssignmentNode(new NameNode('c'),
            new FuncAppNode(new NameNode('float_add'), [new NameNode('a'), new NameNode('b')])
        ),
        new PassNode('c == [1, 3, 0, 0, 0, 0, 0, 0]  (3.000000)'),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(1)), new NumberNode(3)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(2)), new NumberNode(0)),
        new AssertNode(new GetIndexNode(new NameNode('c'), new NumberNode(3)), new NumberNode(0)),
    ];
    return new YuiExample(
        'float_add',
        'Add two same-sign floats as digit arrays (no stdlib)',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleArithmetic() {
    const addFunc = new FuncDefNode(
        new NameNode('add'), [new NameNode('a'), new NameNode('b')],
        new BlockNode([
            new AssignmentNode(new NameNode('result'), new NameNode('a')),
            new RepeatNode(new NameNode('b'), new BlockNode([
                new IncrementNode(new NameNode('result')),
            ])),
            new ReturnNode(new NameNode('result')),
        ])
    );
    const subtractFunc = new FuncDefNode(
        new NameNode('subtract'), [new NameNode('a'), new NameNode('b')],
        new BlockNode([
            new AssignmentNode(new NameNode('result'), new NameNode('a')),
            new RepeatNode(new NameNode('b'), new BlockNode([
                new DecrementNode(new NameNode('result')),
            ])),
            new ReturnNode(new NameNode('result')),
        ])
    );
    const multiplyFunc = new FuncDefNode(
        new NameNode('multiply'), [new NameNode('a'), new NameNode('b')],
        new BlockNode([
            new AssignmentNode(new NameNode('result'), new NumberNode(0)),
            new RepeatNode(new NameNode('b'), new BlockNode([
                new AssignmentNode(new NameNode('result'),
                    new FuncAppNode(new NameNode('add'), [new NameNode('result'), new NameNode('a')])),
            ])),
            new ReturnNode(new NameNode('result')),
        ])
    );
    const divideFunc = new FuncDefNode(
        new NameNode('divide'), [new NameNode('a'), new NameNode('b')],
        new BlockNode([
            new AssignmentNode(new NameNode('q'), new NumberNode(0)),
            new AssignmentNode(new NameNode('r'), new NameNode('a')),
            new RepeatNode(new NameNode('a'), new BlockNode([
                new IfNode(new NameNode('r'), '<', new NameNode('b'),
                    new BlockNode(new BreakNode())),
                new IncrementNode(new NameNode('q')),
                new AssignmentNode(new NameNode('r'),
                    new FuncAppNode(new NameNode('subtract'), [new NameNode('r'), new NameNode('b')])),
            ])),
            new ReturnNode(new NameNode('q')),
        ])
    );
    const moduloFunc = new FuncDefNode(
        new NameNode('modulo'), [new NameNode('a'), new NameNode('b')],
        new BlockNode([
            new AssignmentNode(new NameNode('r'), new NameNode('a')),
            new RepeatNode(new NameNode('a'), new BlockNode([
                new IfNode(new NameNode('r'), '<', new NameNode('b'),
                    new BlockNode(new BreakNode())),
                new AssignmentNode(new NameNode('r'),
                    new FuncAppNode(new NameNode('subtract'), [new NameNode('r'), new NameNode('b')])),
            ])),
            new ReturnNode(new NameNode('r')),
        ])
    );
    const statements = [
        new PassNode('Arithmetic functions for non-negative integers'),
        new PassNode('add(a, b): a + b'),
        addFunc,
        new PassNode('subtract(a, b): a - b  (requires a >= b)'),
        subtractFunc,
        new PassNode('multiply(a, b): a * b'),
        multiplyFunc,
        new PassNode('divide(a, b): integer quotient a // b'),
        divideFunc,
        new PassNode('modulo(a, b): remainder a % b'),
        moduloFunc,
        new PassNode('Usage examples'),
        new PrintExpressionNode(new FuncAppNode(new NameNode('add'),      [new NumberNode(3),  new NumberNode(4)])),
        new PrintExpressionNode(new FuncAppNode(new NameNode('subtract'), [new NumberNode(10), new NumberNode(3)])),
        new PrintExpressionNode(new FuncAppNode(new NameNode('multiply'), [new NumberNode(3),  new NumberNode(4)])),
        new PrintExpressionNode(new FuncAppNode(new NameNode('divide'),   [new NumberNode(10), new NumberNode(3)])),
        new PrintExpressionNode(new FuncAppNode(new NameNode('modulo'),   [new NumberNode(10), new NumberNode(3)])),
        new PassNode('Test add'),
        new AssertNode(new FuncAppNode(new NameNode('add'), [new NumberNode(3), new NumberNode(4)]), new NumberNode(7)),
        new AssertNode(new FuncAppNode(new NameNode('add'), [new NumberNode(0), new NumberNode(5)]), new NumberNode(5)),
        new PassNode('Test subtract'),
        new AssertNode(new FuncAppNode(new NameNode('subtract'), [new NumberNode(10), new NumberNode(3)]), new NumberNode(7)),
        new AssertNode(new FuncAppNode(new NameNode('subtract'), [new NumberNode(5),  new NumberNode(5)]), new NumberNode(0)),
        new PassNode('Test multiply'),
        new AssertNode(new FuncAppNode(new NameNode('multiply'), [new NumberNode(3), new NumberNode(4)]), new NumberNode(12)),
        new AssertNode(new FuncAppNode(new NameNode('multiply'), [new NumberNode(0), new NumberNode(5)]), new NumberNode(0)),
        new PassNode('Test divide'),
        new AssertNode(new FuncAppNode(new NameNode('divide'), [new NumberNode(10), new NumberNode(3)]), new NumberNode(3)),
        new AssertNode(new FuncAppNode(new NameNode('divide'), [new NumberNode(9),  new NumberNode(3)]), new NumberNode(3)),
        new PassNode('Test modulo'),
        new AssertNode(new FuncAppNode(new NameNode('modulo'), [new NumberNode(10), new NumberNode(3)]), new NumberNode(1)),
        new AssertNode(new FuncAppNode(new NameNode('modulo'), [new NumberNode(15), new NumberNode(5)]), new NumberNode(0)),
    ];
    return new YuiExample(
        'arithmetic',
        'Arithmetic functions (add, subtract, multiply, divide, modulo) for non-negative integers',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleNullAssignment() {
    const statements = [
        new PassNode('Assign null to a variable'),
        new AssignmentNode(new NameNode('x'), new ConstNode(null)),
        new PassNode('Test that x is null'),
        new AssertNode(new NameNode('x'), new ConstNode(null)),
    ];
    return new YuiExample(
        'null_assignment',
        'Assign null to a variable and compare',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleBooleanAssignment() {
    const statements = [
        new PassNode('Assign true and false to variables'),
        new AssignmentNode(new NameNode('t'), new ConstNode(true)),
        new AssignmentNode(new NameNode('f'), new ConstNode(false)),
        new PassNode('Test that t is true and f is false'),
        new AssertNode(new NameNode('t'), new ConstNode(true)),
        new AssertNode(new NameNode('f'), new ConstNode(false)),
    ];
    return new YuiExample(
        'boolean_assignment',
        'Assign true/false to variables and compare',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleBooleanBranch() {
    const statements = [
        new PassNode('Branch on a boolean value'),
        new AssignmentNode(new NameNode('flag'), new ConstNode(true)),
        new AssignmentNode(new NameNode('result'), new NumberNode(0)),
        new IfNode(new NameNode('flag'), '==', new ConstNode(true),
            new BlockNode(new AssignmentNode(new NameNode('result'), new NumberNode(1))),
            new BlockNode(new AssignmentNode(new NameNode('result'), new NumberNode(2)))
        ),
        new PassNode('Test that result is 1 because flag was true'),
        new AssertNode(new NameNode('result'), new NumberNode(1)),
    ];
    return new YuiExample(
        'boolean_branch',
        'Conditional branch based on a boolean value',
        new BlockNode(statements, true),
        'both',
    );
}

export function exampleNullCheck() {
    const statements = [
        new PassNode('Define is_null function'),
        new FuncDefNode(
            new NameNode('is_null'), [new NameNode('v')],
            new BlockNode([
                new IfNode(new NameNode('v'), '==', new ConstNode(null),
                    new BlockNode(new ReturnNode(new ConstNode(true))),
                    new BlockNode(new ReturnNode(new ConstNode(false)))
                )
            ])
        ),
        new PassNode('Test is_null with null and non-null values'),
        new AssertNode(new FuncAppNode(new NameNode('is_null'), [new ConstNode(null)]),  new ConstNode(true)),
        new AssertNode(new FuncAppNode(new NameNode('is_null'), [new NumberNode(0)]),    new ConstNode(false)),
        new AssertNode(new FuncAppNode(new NameNode('is_null'), [new StringNode('')]),   new ConstNode(false)),
    ];
    return new YuiExample(
        'null_check',
        'Function that checks if a value is null',
        new BlockNode(statements, true),
        'test',
    );
}

export function exampleMonteCarlo() {
    const monteCarloFunc = new FuncDefNode(
        new NameNode('monte_carlo'), [new NameNode('n')],
        new BlockNode([
            new AssignmentNode(new NameNode('hits'), new NumberNode(0)),
            new RepeatNode(new NameNode('n'), new BlockNode([
                new AssignmentNode(new NameNode('x'), new FuncAppNode(new NameNode('乱数'), [])),
                new AssignmentNode(new NameNode('y'), new FuncAppNode(new NameNode('乱数'), [])),
                new AssignmentNode(new NameNode('dist'),
                    new FuncAppNode(new NameNode('平方根'), [
                        new FuncAppNode(new NameNode('和'), [
                            new FuncAppNode(new NameNode('積'), [new NameNode('x'), new NameNode('x')]),
                            new FuncAppNode(new NameNode('積'), [new NameNode('y'), new NameNode('y')]),
                        ]),
                    ])
                ),
                new IfNode(new NameNode('dist'), '<=', new NumberNode(1),
                    new BlockNode(new IncrementNode(new NameNode('hits')))
                ),
            ])),
            new ReturnNode(
                new FuncAppNode(new NameNode('商'), [
                    new FuncAppNode(new NameNode('積'), [
                        new FuncAppNode(new NameNode('小数化'), [new NameNode('hits')]),
                        new NumberNode(4),
                    ]),
                    new FuncAppNode(new NameNode('小数化'), [new NameNode('n')]),
                ])
            ),
        ])
    );
    const statements = [
        new ImportNode(),
        new PassNode('Monte Carlo method: estimate π by random point sampling'),
        new PassNode('Throw n random points at a unit square [0,1)×[0,1).'),
        new PassNode('Points inside the unit circle (dist ≤ 1) are counted.'),
        new PassNode('π ≈ 4 × (hits / n)'),
        monteCarloFunc,
        new PassNode('More samples → closer to π ≈ 3.14159...'),
        new PrintExpressionNode(new FuncAppNode(new NameNode('monte_carlo'), [new NumberNode(100)])),
        new PrintExpressionNode(new FuncAppNode(new NameNode('monte_carlo'), [new NumberNode(1000)])),
    ];
    return new YuiExample(
        'monte_carlo',
        'Estimate π using the Monte Carlo method (stdlib: 乱数, 平方根)',
        new BlockNode(statements, true),
        'sample',
    );
}

export function getAllExamples() {
    return [
        exampleHelloWorld(),
        exampleVariables(),
        exampleLoop(),
        exampleFizzBuzz(),
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
        exampleNullCheck(),
    ];
}

/** 学習環境向けサンプルのみ返す（kind='sample' または 'both'） */
export function getAllSamples() {
    return getAllExamples().filter(e => e.kind === 'sample' || e.kind === 'both');
}

/** 実装テスト用の例のみ返す（kind='test' または 'both'） */
export function getAllTestExamples() {
    return getAllExamples().filter(e => e.kind === 'test' || e.kind === 'both');
}
