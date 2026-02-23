#!/usr/bin/env python
"""
Yui言語のサンプルコード生成ツール

ASTノードを使ってサンプルコードを構築し、
CodeVisitorで異なる構文（Yui、Python風など）に変換して出力します。
"""

from typing import List
from .yuiast import (
    ConstNode, NumberNode, StringNode, NameNode, ArrayNode, ObjectNode, MinusNode, ArrayLenNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode, PassNode,
    FuncDefNode, FuncAppNode, ReturnNode, ImportNode,
    PrintExpressionNode,
    BinaryNode, GetIndexNode, AssertNode
)
from .yuicoding import CodingVisitor


def _strip_asserts(block) -> 'BlockNode':
    """BlockNode から AssertNode を取り除いた新しい BlockNode を返す。
    直前の "Test ..." PassNode もあわせて除去する。
    """
    filtered = []
    for stmt in block.statements:
        if isinstance(stmt, AssertNode):
            if (filtered
                    and isinstance(filtered[-1], PassNode)
                    and filtered[-1].comment
                    and filtered[-1].comment.lower().startswith('test')):
                filtered.pop()
        else:
            filtered.append(stmt)
    return BlockNode(filtered, block.top_level)


class YuiExample:
    """Yui言語のサンプルコード生成クラス

    kind:
      'sample' — yui_editor など学習環境向けサンプル
      'test'   — 実装テスト専用（学習環境には表示しない）
      'both'   — 両方に使用
    """

    def __init__(self, name: str, description: str, ast_node, kind: str = 'both'):
        self.name = name
        self.description = description
        self.ast_node = ast_node
        self.kind = kind

    def generate(self, syntax: str = 'yui', include_asserts: bool = True) -> str:
        node = self.ast_node if include_asserts else _strip_asserts(self.ast_node)
        visitor = CodingVisitor(syntax)
        return visitor.emit(node)

def example_hello_world():
    statements = [
        PassNode(comment='Print "Hello, world!"'),
        PrintExpressionNode(StringNode("Hello, world!")),
    ]
    return YuiExample(
        name="hello_world",
        description="Print 'Hello, world!'",
        ast_node=BlockNode(statements, top_level=True),
        kind='sample',
    )

def example_variables():
    """基本的な算術演算のサンプル"""
    statements = [
        PassNode(comment="Define variables x and y"),
        AssignmentNode(NameNode("x"),NumberNode(1)),
        AssignmentNode(NameNode("y"),MinusNode(NumberNode(2))),
        PassNode(comment="Increment x"),
        IncrementNode(NameNode("x")),
        PassNode(comment="Decrement y"),
        DecrementNode(NameNode("y")),
        PassNode(comment="Test that x is 2 and y is -3"),
        AssertNode(NameNode("x"), NumberNode(2)),
        AssertNode(NameNode("y"), MinusNode(NumberNode(3))),
    ]
    return YuiExample(
        name="variables",
        description="Basic variable definition and increment/decrement",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_loop():
    """ループのサンプル"""
    statements = [
        PassNode(comment="Loop 10 times and break at 5"),
        AssignmentNode(NameNode("count"),NumberNode(0)),
        RepeatNode(
            NumberNode(10),
            BlockNode([
                IncrementNode(NameNode("count")),
                IfNode(NameNode("count"), "==", NumberNode(5), BlockNode(BreakNode())),
            ]),
        ),
        PassNode(comment="Test that count is 5"),
        AssertNode(NameNode("count"), NumberNode(5)),
    ]
    return YuiExample(
        name="loop",
        description="Loop 10 times and break at 5",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_fizzbuzz():
    """1から100までのFizzBuzzをリストに追加する"""
    statements = [
        PassNode(comment="FizzBuzz from 1 to 100, collected into a list"),
        AssignmentNode(NameNode("result"), ArrayNode([])),
        AssignmentNode(NameNode("i"),    NumberNode(0)),
        AssignmentNode(NameNode("fizz"), NumberNode(0)),
        AssignmentNode(NameNode("buzz"), NumberNode(0)),
        RepeatNode(NumberNode(100), BlockNode([
            IncrementNode(NameNode("i")),
            IncrementNode(NameNode("fizz")),
            IncrementNode(NameNode("buzz")),
            IfNode(NameNode("fizz"), "==", NumberNode(3),
                BlockNode(AssignmentNode(NameNode("fizz"), NumberNode(0)))),
            IfNode(NameNode("buzz"), "==", NumberNode(5),
                BlockNode(AssignmentNode(NameNode("buzz"), NumberNode(0)))),
            IfNode(NameNode("fizz"), "==", NumberNode(0),
                BlockNode(
                    IfNode(NameNode("buzz"), "==", NumberNode(0),
                        BlockNode(AppendNode(NameNode("result"), StringNode("FizzBuzz"))),
                        BlockNode(AppendNode(NameNode("result"), StringNode("Fizz"))),
                    )
                ),
                BlockNode(
                    IfNode(NameNode("buzz"), "==", NumberNode(0),
                        BlockNode(AppendNode(NameNode("result"), StringNode("Buzz"))),
                        BlockNode(AppendNode(NameNode("result"), NameNode("i"))),
                    )
                ),
            ),
        ])),
        PrintExpressionNode(NameNode("result")),
        PassNode(comment="Test: length is 100"),
        AssertNode(ArrayLenNode(NameNode("result")), NumberNode(100)),
        PassNode(comment="Test: spot-check Fizz, Buzz, FizzBuzz positions"),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(2)),  StringNode("Fizz")),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(4)),  StringNode("Buzz")),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(14)), StringNode("FizzBuzz")),
    ]
    return YuiExample(
        name="fizzbuzz",
        description="FizzBuzz from 1 to 100, collected into a list",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_nested_conditional_branches():
    """ネストした条件分岐のサンプル"""
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))
    statements = [
        PassNode(comment="Test nested conditions on x and y"),
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(2)),
        AssignmentNode(NameNode("z"), NumberNode(3)),
        PassNode(comment="If x is 0, check y and increment y or z accordingly"),
        IfNode(NameNode("x"),"==", NumberNode(0),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(1),then_block, else_block)),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(2),then_block, else_block))
        ),
        PassNode(comment="Test that y was incremented and z was not"),
        AssertNode(NameNode("y"), NumberNode(3)),
    ]
    return YuiExample(
        name="nested_conditional_branches",
        description="Nested conditional branching",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_comparisons():
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))

    statements = [
        PassNode(comment="Various comparisons on x"),
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(0)),
        AssignmentNode(NameNode("z"), NumberNode(0)),
        PassNode(comment="Is x equal to 1?"),
        IfNode(NameNode("x"),"==", NumberNode(1),then_block, else_block),
        PassNode(comment="Is x not equal to 1?"),
        IfNode(NameNode("x"),"!=", NumberNode(1),then_block, else_block),
        PassNode(comment="Is x less than 1?"),
        IfNode(NameNode("x"),"<", NumberNode(1),then_block, else_block),
        PassNode(comment="Is x greater than 1?"),
        IfNode(NameNode("x"),">", NumberNode(1),then_block, else_block),
        PassNode(comment="Is x less than or equal to 1?"),
        IfNode(NameNode("x"),"<=", NumberNode(1),then_block, else_block),
        PassNode(comment="Is x greater than or equal to 1?"),
        IfNode(NameNode("x"),">=", NumberNode(1),then_block, else_block),
        PassNode(comment="Test that all conditions were evaluated correctly"),
        AssertNode(NameNode("y"), NumberNode(3)),
        AssertNode(NameNode("z"), NumberNode(3)),
    ]
    return YuiExample(
        name="comparisons",
        description="Comparison operations",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_array():
    """配列操作のサンプル"""
    statements = [
        PassNode(comment="Create an array A with elements 1, 2, 3"),
        AssignmentNode(NameNode("A"),ArrayNode([NumberNode(1),NumberNode(2),NumberNode(3)])),
        PassNode(comment="Append 0 to the end of A"),
        AppendNode(NameNode("A"),NumberNode(0)),
        PassNode(comment="Increment the first element of A"),
        IncrementNode(GetIndexNode(NameNode("A"), NumberNode(0))),
        PassNode(comment="If 2 is in A, set the first element to the fourth element"),
        IfNode(NumberNode(2), "in", NameNode("A"),
            AssignmentNode(GetIndexNode(NameNode("A"), NumberNode(0)),GetIndexNode(NameNode("A"), NumberNode(3)))
        ),
        PassNode(comment="Test that the array has 4 elements"),
        AssertNode(ArrayLenNode(NameNode("A")), NumberNode(4)),
    ]
    return YuiExample(
        name="array",
        description="Array creation and element manipulation",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_strings():
    """文字列操作のサンプル"""
    statements = [
        PassNode(comment="Create a string s with value 'hello'"),
        AssignmentNode(NameNode("s"), StringNode("hello")),
        PassNode(comment="Set the first character of s to 'H'"),
        PassNode(comment="Note: strings are just the array of character codes. So we can manipulate them like arrays."),
        AssignmentNode(GetIndexNode(NameNode("s"), NumberNode(0)), GetIndexNode(StringNode("H"), 0)),
        PassNode(comment='Append " world" to s'),
        AssignmentNode(NameNode("t"), StringNode(" world")),
        AssignmentNode(NameNode("i"), NumberNode(0)),
        RepeatNode(ArrayLenNode(NameNode("t")), BlockNode([
            AppendNode(NameNode("s"), GetIndexNode(NameNode("t"), NameNode("i"))),
            IncrementNode(NameNode("i")),
        ])),
        PassNode(comment="Test that s is now 'Hello world'"),
        AssertNode(NameNode("s"), StringNode("Hello world")),
    ]
    return YuiExample(
        name="strings",
        description="String creation and manipulation",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_objects():
    """オブジェクト操作のサンプル"""
    statements = [
        PassNode(comment="Create an object O with properties x and y"),
        AssignmentNode(NameNode("O"), ObjectNode({
            "x": NumberNode(0),
            "y": NumberNode(0)
        })),
        PassNode(comment="Set the x property of O to 1"),
        AssignmentNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(1)),
        PassNode(comment="Set the y property of O to 2"),
        AssignmentNode(GetIndexNode(NameNode("O"), StringNode("y")), NumberNode(2)),
        PassNode(comment="Test that O has properties x=1 and y=2"),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(1)),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("y")), NumberNode(2)),
    ]
    return YuiExample(
        name="objects",
        description="Object creation and property manipulation",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_function():
    statements = [
        PassNode(comment="Define function that adds 1"),
        FuncDefNode(
            NameNode("succ"), [NameNode("n")],
            BlockNode([
                IncrementNode(NameNode("n")),
                ReturnNode(NameNode("n"))
            ])
        ),
        AssignmentNode(NameNode("result"),
            FuncAppNode(NameNode("succ"),[NumberNode(0)])
        ),
        AssertNode(NameNode("result"), NumberNode(1)),
    ]
    return YuiExample(
        name="function",
        description="Function definition and call (increment function)",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_function_no_argument():
    statements = [
        PassNode(comment="Define function that adds 1"),
        FuncDefNode(
            NameNode("zero"), [], BlockNode(ReturnNode(NumberNode(0)))
        ),
        AssertNode(FuncAppNode(NameNode("zero"), []), NumberNode(0)),
    ]
    return YuiExample(
        name="function_no_argument",
        description="Function definition and call (zero-argument function and multi-argument function)",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_function_without_return():
    statements = [
        PassNode(comment="Define function that creates a point object"),
        FuncDefNode(
            NameNode("point"), [NameNode("x"), NameNode("y")], BlockNode([
                PassNode(comment="If function does not return anything, return the local environment as an object"),
            ])
        ),
        AssignmentNode(NameNode("O"), FuncAppNode(NameNode("point"), [NumberNode(0), NumberNode(0)])),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(0)),
    ]
    return YuiExample(
        name="function_without_return",
        description="Function definition and call (function without return value)",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_recursive_function():
    """関数のサンプル"""
    statements = [
        PassNode(comment="Define recursive function that computes factorial"),
        FuncDefNode(
            NameNode("fact"), [NameNode("n")],
            BlockNode([
                IfNode(NameNode("n"), "==", NumberNode(0),
                    BlockNode([ReturnNode(NumberNode(1))]),
                    BlockNode([
                        PassNode(comment="Yui does not have arithmetic operators."),
                        ReturnNode(FuncAppNode(NameNode("multiplex"), 
                        [NameNode("n"), FuncAppNode(NameNode("fact"), 
                                                    [FuncAppNode(NameNode("decrease"), [NameNode("n")])])]))
                    ])
                )
            ])
        ),
        PassNode(comment="multiplex(a, b) function for a * b."),
        FuncDefNode(
            NameNode("multiplex"), [NameNode("a"), NameNode("b")], BlockNode([
                AssignmentNode(NameNode("result"), NumberNode(0)),
                RepeatNode(NameNode("b"), BlockNode([
                    RepeatNode(NameNode("a"), BlockNode([
                        IncrementNode(NameNode("result"))
                    ]))
                ])),
                ReturnNode(NameNode("result"))
            ])
        ),
        PassNode(comment="decrease(n) function for n-1."),
        FuncDefNode(
            NameNode("decrease"), [NameNode("n")], BlockNode([
                DecrementNode(NameNode("n")),
                ReturnNode(NameNode("n"))
            ])
        ),
        PassNode(comment="Test fact(0) is 1"),
        AssertNode(FuncAppNode(NameNode("fact"),[NumberNode(0)]), NumberNode(1)),
        PassNode(comment="Test that fact(5) is 120"),
        AssertNode(FuncAppNode(NameNode("fact"),[NumberNode(5)]), NumberNode(120)),
    ]
    return YuiExample(
        name="recursive_function",
        description="Recursive function definition and call (factorial function)",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_float_add():
    """float 配列の加算（stdlib なし）

    float の内部表現: [sign, d1, d2, d3, d4, d5, d6, d7]
      sign: 1 (正) または -1 (負)
      d1..d7: abs(value) * 1e6 の各桁 (合計7桁)
      例) 3.14 → [1, 3, 1, 4, 0, 0, 0, 0]
         -2.5 → [-1, 2, 5, 0, 0, 0, 0, 0]

    float_add(a, b): 同符号の float 配列を足し合わせる
    アルゴリズム: i=7 から i=1 まで逆順に桁ごとに加算し繰り上がりを伝播する
    """
    statements = [
        PassNode(comment="float format: [sign, d1..d7]  sign=1 or -1, d1..d7 = abs(x)*1e6 digits"),
        PassNode(comment="float_add(a, b): add two same-sign float arrays (no stdlib)"),
        FuncDefNode(
            NameNode("float_add"), [NameNode("a"), NameNode("b")],
            BlockNode([
                # result = [1, 0, 0, 0, 0, 0, 0, 0]  (sign は後で a[0] を設定)
                AssignmentNode(NameNode("result"), ArrayNode([
                    GetIndexNode(NameNode("a"), NumberNode(0)),
                    NumberNode(0), NumberNode(0), NumberNode(0),
                    NumberNode(0), NumberNode(0), NumberNode(0), NumberNode(0),
                ])),
                AssignmentNode(NameNode("carry"), NumberNode(0)),
                AssignmentNode(NameNode("i"), NumberNode(7)),
                # i=7 から i=1 まで 7 回くり返す
                RepeatNode(NumberNode(7), BlockNode([
                    # sum = carry
                    AssignmentNode(NameNode("sum"), NameNode("carry")),
                    # sum を a[i] 回増やす
                    RepeatNode(GetIndexNode(NameNode("a"), NameNode("i")), BlockNode([
                        IncrementNode(NameNode("sum")),
                    ])),
                    # sum を b[i] 回増やす
                    RepeatNode(GetIndexNode(NameNode("b"), NameNode("i")), BlockNode([
                        IncrementNode(NameNode("sum")),
                    ])),
                    # carry = 0
                    AssignmentNode(NameNode("carry"), NumberNode(0)),
                    # もし sum >= 10 ならば: carry=1, sum -= 10
                    IfNode(NameNode("sum"), ">=", NumberNode(10), BlockNode([
                        IncrementNode(NameNode("carry")),
                        RepeatNode(NumberNode(10), BlockNode([
                            DecrementNode(NameNode("sum")),
                        ])),
                    ])),
                    # result[i] = sum
                    AssignmentNode(
                        GetIndexNode(NameNode("result"), NameNode("i")),
                        NameNode("sum"),
                    ),
                    # i -= 1
                    DecrementNode(NameNode("i")),
                ])),
                ReturnNode(NameNode("result")),
            ])
        ),
        PassNode(comment="3.14 + 2.50 = 5.64"),
        AssignmentNode(NameNode("a"), ArrayNode([
            NumberNode(1), NumberNode(3), NumberNode(1), NumberNode(4),
            NumberNode(0), NumberNode(0), NumberNode(0), NumberNode(0),
        ])),
        AssignmentNode(NameNode("b"), ArrayNode([
            NumberNode(1), NumberNode(2), NumberNode(5), NumberNode(0),
            NumberNode(0), NumberNode(0), NumberNode(0), NumberNode(0),
        ])),
        AssignmentNode(NameNode("c"),
            FuncAppNode(NameNode("float_add"), [NameNode("a"), NameNode("b")])),
        PassNode(comment="c == [1, 5, 6, 4, 0, 0, 0, 0]  (5.640000)"),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(0)), NumberNode(1)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(1)), NumberNode(5)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(2)), NumberNode(6)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(3)), NumberNode(4)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(4)), NumberNode(0)),
        PassNode(comment="1.99 + 1.01 = 3.00  (tests carry propagation)"),
        AssignmentNode(NameNode("a"), ArrayNode([
            NumberNode(1), NumberNode(1), NumberNode(9), NumberNode(9),
            NumberNode(0), NumberNode(0), NumberNode(0), NumberNode(0),
        ])),
        AssignmentNode(NameNode("b"), ArrayNode([
            NumberNode(1), NumberNode(1), NumberNode(0), NumberNode(1),
            NumberNode(0), NumberNode(0), NumberNode(0), NumberNode(0),
        ])),
        AssignmentNode(NameNode("c"),
            FuncAppNode(NameNode("float_add"), [NameNode("a"), NameNode("b")])),
        PassNode(comment="c == [1, 3, 0, 0, 0, 0, 0, 0]  (3.000000)"),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(1)), NumberNode(3)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(2)), NumberNode(0)),
        AssertNode(GetIndexNode(NameNode("c"), NumberNode(3)), NumberNode(0)),
    ]
    return YuiExample(
        name="float_add",
        description="Add two same-sign floats as digit arrays (no stdlib)",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def example_arithmetic():
    """四則演算と余りを関数で定義するサンプル（0以上の整数を前提）"""
    add_func = FuncDefNode(
        NameNode("add"), [NameNode("a"), NameNode("b")],
        BlockNode([
            AssignmentNode(NameNode("result"), NameNode("a")),
            RepeatNode(NameNode("b"), BlockNode([
                IncrementNode(NameNode("result")),
            ])),
            ReturnNode(NameNode("result")),
        ])
    )
    subtract_func = FuncDefNode(
        NameNode("subtract"), [NameNode("a"), NameNode("b")],
        BlockNode([
            AssignmentNode(NameNode("result"), NameNode("a")),
            RepeatNode(NameNode("b"), BlockNode([
                DecrementNode(NameNode("result")),
            ])),
            ReturnNode(NameNode("result")),
        ])
    )
    multiply_func = FuncDefNode(
        NameNode("multiply"), [NameNode("a"), NameNode("b")],
        BlockNode([
            AssignmentNode(NameNode("result"), NumberNode(0)),
            RepeatNode(NameNode("b"), BlockNode([
                AssignmentNode(NameNode("result"),
                    FuncAppNode(NameNode("add"), [NameNode("result"), NameNode("a")])),
            ])),
            ReturnNode(NameNode("result")),
        ])
    )
    divide_func = FuncDefNode(
        NameNode("divide"), [NameNode("a"), NameNode("b")],
        BlockNode([
            AssignmentNode(NameNode("q"), NumberNode(0)),
            AssignmentNode(NameNode("r"), NameNode("a")),
            RepeatNode(NameNode("a"), BlockNode([
                IfNode(NameNode("r"), "<", NameNode("b"),
                    BlockNode(BreakNode())),
                IncrementNode(NameNode("q")),
                AssignmentNode(NameNode("r"),
                    FuncAppNode(NameNode("subtract"), [NameNode("r"), NameNode("b")])),
            ])),
            ReturnNode(NameNode("q")),
        ])
    )
    modulo_func = FuncDefNode(
        NameNode("modulo"), [NameNode("a"), NameNode("b")],
        BlockNode([
            AssignmentNode(NameNode("r"), NameNode("a")),
            RepeatNode(NameNode("a"), BlockNode([
                IfNode(NameNode("r"), "<", NameNode("b"),
                    BlockNode(BreakNode())),
                AssignmentNode(NameNode("r"),
                    FuncAppNode(NameNode("subtract"), [NameNode("r"), NameNode("b")])),
            ])),
            ReturnNode(NameNode("r")),
        ])
    )
    statements = [
        PassNode(comment="Arithmetic functions for non-negative integers"),
        PassNode(comment="add(a, b): a + b"),
        add_func,
        PassNode(comment="subtract(a, b): a - b  (requires a >= b)"),
        subtract_func,
        PassNode(comment="multiply(a, b): a * b"),
        multiply_func,
        PassNode(comment="divide(a, b): integer quotient a // b"),
        divide_func,
        PassNode(comment="modulo(a, b): remainder a % b"),
        modulo_func,
        PassNode(comment="Usage examples"),
        PrintExpressionNode(FuncAppNode(NameNode("add"),      [NumberNode(3),  NumberNode(4)])),
        PrintExpressionNode(FuncAppNode(NameNode("subtract"), [NumberNode(10), NumberNode(3)])),
        PrintExpressionNode(FuncAppNode(NameNode("multiply"), [NumberNode(3),  NumberNode(4)])),
        PrintExpressionNode(FuncAppNode(NameNode("divide"),   [NumberNode(10), NumberNode(3)])),
        PrintExpressionNode(FuncAppNode(NameNode("modulo"),   [NumberNode(10), NumberNode(3)])),
        PassNode(comment="Test add"),
        AssertNode(FuncAppNode(NameNode("add"), [NumberNode(3), NumberNode(4)]), NumberNode(7)),
        AssertNode(FuncAppNode(NameNode("add"), [NumberNode(0), NumberNode(5)]), NumberNode(5)),
        PassNode(comment="Test subtract"),
        AssertNode(FuncAppNode(NameNode("subtract"), [NumberNode(10), NumberNode(3)]), NumberNode(7)),
        AssertNode(FuncAppNode(NameNode("subtract"), [NumberNode(5),  NumberNode(5)]), NumberNode(0)),
        PassNode(comment="Test multiply"),
        AssertNode(FuncAppNode(NameNode("multiply"), [NumberNode(3), NumberNode(4)]), NumberNode(12)),
        AssertNode(FuncAppNode(NameNode("multiply"), [NumberNode(0), NumberNode(5)]), NumberNode(0)),
        PassNode(comment="Test divide"),
        AssertNode(FuncAppNode(NameNode("divide"), [NumberNode(10), NumberNode(3)]), NumberNode(3)),
        AssertNode(FuncAppNode(NameNode("divide"), [NumberNode(9),  NumberNode(3)]), NumberNode(3)),
        PassNode(comment="Test modulo"),
        AssertNode(FuncAppNode(NameNode("modulo"), [NumberNode(10), NumberNode(3)]), NumberNode(1)),
        AssertNode(FuncAppNode(NameNode("modulo"), [NumberNode(15), NumberNode(5)]), NumberNode(0)),
    ]
    return YuiExample(
        name="arithmetic",
        description="Arithmetic functions (add, subtract, multiply, divide, modulo) for non-negative integers",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_monte_carlo():
    """モンテカルロ法で π を推定するサンプル（乱数・平方根を使用）"""
    monte_carlo_func = FuncDefNode(
        NameNode("monte_carlo"), [NameNode("n")],
        BlockNode([
            AssignmentNode(NameNode("hits"), NumberNode(0)),
            RepeatNode(NameNode("n"), BlockNode([
                AssignmentNode(NameNode("x"), FuncAppNode(NameNode("乱数"), [])),
                AssignmentNode(NameNode("y"), FuncAppNode(NameNode("乱数"), [])),
                AssignmentNode(NameNode("dist"),
                    FuncAppNode(NameNode("平方根"), [
                        FuncAppNode(NameNode("和"), [
                            FuncAppNode(NameNode("積"), [NameNode("x"), NameNode("x")]),
                            FuncAppNode(NameNode("積"), [NameNode("y"), NameNode("y")]),
                        ])
                    ])
                ),
                IfNode(NameNode("dist"), "<=", NumberNode(1),
                    BlockNode(IncrementNode(NameNode("hits")))
                ),
            ])),
            ReturnNode(
                FuncAppNode(NameNode("商"), [
                    FuncAppNode(NameNode("積"), [
                        FuncAppNode(NameNode("少数化"), [NameNode("hits")]),
                        NumberNode(4),
                    ]),
                    FuncAppNode(NameNode("少数化"), [NameNode("n")]),
                ])
            ),
        ])
    )
    statements = [
        ImportNode(),
        PassNode(comment="Monte Carlo method: estimate π by random point sampling"),
        PassNode(comment="Throw n random points at a unit square [0,1)×[0,1)."),
        PassNode(comment="Points inside the unit circle (dist ≤ 1) are counted."),
        PassNode(comment="π ≈ 4 × (hits / n)"),
        monte_carlo_func,
        PassNode(comment="More samples → closer to π ≈ 3.14159..."),
        PrintExpressionNode(FuncAppNode(NameNode("monte_carlo"), [NumberNode(100)])),
        PrintExpressionNode(FuncAppNode(NameNode("monte_carlo"), [NumberNode(1000)])),
    ]
    return YuiExample(
        name="monte_carlo",
        description="Estimate π using the Monte Carlo method (stdlib: 乱数, 平方根)",
        ast_node=BlockNode(statements, top_level=True),
        kind='sample',
    )


def example_null_assignment():
    """null の代入と比較"""
    statements = [
        PassNode(comment="Assign null to a variable"),
        AssignmentNode(NameNode("x"), ConstNode(None)),
        PassNode(comment="Test that x is null"),
        AssertNode(NameNode("x"), ConstNode(None)),
    ]
    return YuiExample(
        name="null_assignment",
        description="Assign null to a variable and compare",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def example_boolean_assignment():
    """true / false の代入とアサート"""
    statements = [
        PassNode(comment="Assign true and false to variables"),
        AssignmentNode(NameNode("t"), ConstNode(True)),
        AssignmentNode(NameNode("f"), ConstNode(False)),
        PassNode(comment="Test that t is true and f is false"),
        AssertNode(NameNode("t"), ConstNode(True)),
        AssertNode(NameNode("f"), ConstNode(False)),
    ]
    return YuiExample(
        name="boolean_assignment",
        description="Assign true/false to variables and compare",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def example_boolean_branch():
    """boolean で条件分岐"""
    statements = [
        PassNode(comment="Branch on a boolean value"),
        AssignmentNode(NameNode("flag"), ConstNode(True)),
        AssignmentNode(NameNode("result"), NumberNode(0)),
        IfNode(NameNode("flag"), "==", ConstNode(True),
            BlockNode(AssignmentNode(NameNode("result"), NumberNode(1))),
            BlockNode(AssignmentNode(NameNode("result"), NumberNode(2))),
        ),
        PassNode(comment="Test that result is 1 because flag was true"),
        AssertNode(NameNode("result"), NumberNode(1)),
    ]
    return YuiExample(
        name="boolean_branch",
        description="Conditional branch based on a boolean value",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_null_check():
    """null チェック関数"""
    statements = [
        PassNode(comment="Define is_null function"),
        FuncDefNode(
            NameNode("is_null"), [NameNode("v")],
            BlockNode([
                IfNode(NameNode("v"), "==", ConstNode(None),
                    BlockNode(ReturnNode(ConstNode(True))),
                    BlockNode(ReturnNode(ConstNode(False))),
                )
            ])
        ),
        PassNode(comment="Test is_null with null and non-null values"),
        AssertNode(FuncAppNode(NameNode("is_null"), [ConstNode(None)]),  ConstNode(True)),
        AssertNode(FuncAppNode(NameNode("is_null"), [NumberNode(0)]),    ConstNode(False)),
        AssertNode(FuncAppNode(NameNode("is_null"), [StringNode("")]),   ConstNode(False)),
    ]
    return YuiExample(
        name="null_check",
        description="Function that checks if a value is null",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def get_all_examples() -> List[YuiExample]:
    """すべての例を返す（kind に関わらず）"""
    return [
        example_hello_world(),
        example_variables(),
        example_loop(),
        example_fizzbuzz(),
        example_nested_conditional_branches(),
        example_comparisons(),
        example_array(),
        example_strings(),
        example_objects(),
        example_function(),
        example_function_no_argument(),
        example_function_without_return(),
        example_recursive_function(),
        example_arithmetic(),
        example_float_add(),
        example_monte_carlo(),
        example_null_assignment(),
        example_boolean_assignment(),
        example_boolean_branch(),
        example_null_check(),
    ]


def get_samples() -> List[YuiExample]:
    """学習環境向けサンプルを返す（kind='sample' または 'both'）"""
    return [e for e in get_all_examples() if e.kind in ('sample', 'both')]


def get_test_examples() -> List[YuiExample]:
    """実装テスト用の例を返す（kind='test' または 'both'）"""
    return [e for e in get_all_examples() if e.kind in ('test', 'both')]
