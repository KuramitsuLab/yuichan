#!/usr/bin/env python
"""
Yui言語のサンプルコード生成ツール

ASTノードを使ってサンプルコードを構築し、
CodeVisitorで異なる構文（Yui、Python風など）に変換して出力します。
"""

from typing import List, Dict
from .yuiast import (
    NumberNode, StringNode, NameNode, ArrayNode, ObjectNode, MinusNode, ArrayLenNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode, PassNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode,
    BinaryNode, GetIndexNode, AssertNode
)
from .yuiparser import CodingVisitor, load_syntax


class YuiExample:
    """Yui言語のサンプルコード生成クラス"""

    def __init__(self, name: str, description: str, ast_node):
        self.name = name
        self.description = description
        self.ast_node = ast_node

    def generate(self, syntax: str = 'yui') -> str:
        visitor = CodingVisitor(syntax)
        return visitor.emit(self.ast_node)

def example_hello_world():
    statements = [
        PassNode(comment='Print "Hello, world!"'),
        PrintExpressionNode(StringNode("Hello, world!")),
    ]
    return YuiExample(
        name="hello_world",
        description="Print 'Hello, world!'",
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
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
        ast_node=BlockNode(statements, top_level=True)
    )


# すべてのサンプルを取得
def get_all_examples() -> List[YuiExample]:
    """すべてのサンプルを返す"""
    return [
        example_hello_world(),
        example_variables(),
        example_loop(),
        example_nested_conditional_branches(),
        example_comparisons(),
        example_array(),
        example_strings(),
        example_function(),
        example_function_no_argument(),
        example_function_without_return(),
        example_recursive_function(),
    ]


# def print_example(example: YuiExample, syntaxes: List[str] = None):
#     """サンプルを複数の構文で出力"""
#     if syntaxes is None:
#         syntaxes = ['yui']

#     print(f"\n{'='*60}")
#     print(f"サンプル名: {example.name}")
#     print(f"説明: {example.description}")
#     print(f"{'='*60}")

#     for syntax in syntaxes:
#         try:
#             import os
#             syntax_basename = os.path.basename(syntax)
#             syntax_name = syntax_basename.replace('syntax-', '').replace('.json', '')
#             code = example.generate(syntax)
#             print(f"\n--- {syntax_name} 構文 ---")
#             print(code)
#         except Exception as e:
#             print(f"\n--- {syntax_name} 構文 (エラー) ---")
#             print(f"エラー: {e}")


# def main():
#     """メイン関数 - すべてのサンプルを出力"""
#     import argparse

#     parser = argparse.ArgumentParser(
#         description='Yui言語のサンプルコード生成ツール'
#     )
#     parser.add_argument(
#         '--syntax',
#         nargs='+',
#         default=['yui', 'pylike'],
#         help='使用する構文ファイル（複数指定可）'
#     )
#     parser.add_argument(
#         '--example',
#         type=str,
#         help='特定のサンプルのみ生成（サンプル名を指定）'
#     )
#     parser.add_argument(
#         '--list',
#         action='store_true',
#         help='利用可能なサンプルの一覧を表示'
#     )

#     args = parser.parse_args()

#     examples = get_all_examples()

#     # サンプル一覧を表示
#     if args.list:
#         print("\n利用可能なサンプル:")
#         for ex in examples:
#             print(f"  {ex.name:20s} - {ex.description}")
#         return

#     # 特定のサンプルのみ生成
#     if args.example:
#         example = next((ex for ex in examples if ex.name == args.example), None)
#         if example:
#             print_example(example, args.syntax)
#         else:
#             print(f"エラー: サンプル '{args.example}' が見つかりません")
#             print("\n利用可能なサンプル:")
#             for ex in examples:
#                 print(f"  - {ex.name}")
#         return

#     # すべてのサンプルを生成
#     for example in examples:
#         print_example(example, args.syntax)


# if __name__ == '__main__':
#     main()
