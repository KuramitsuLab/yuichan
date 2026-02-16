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

    def generate(self, syntax: str = 'syntax-yui.json') -> str:
        visitor = CodingVisitor(syntax)
        return visitor.emit(self.ast_node)


# サンプル1: 基本的な変数と演算
def example_basic_arithmetic():
    """基本的な算術演算のサンプル"""
    statements = [
        AssignmentNode(NameNode("x"),NumberNode(1)),
        AssignmentNode(NameNode("y"),MinusNode(NumberNode(2))),
        IncrementNode(NameNode("x")),
        DecrementNode(NameNode("y")),
        AssertNode(NameNode("x"), NumberNode(2)),
        AssertNode(NameNode("y"), MinusNode(NumberNode(3))),
    ]
    return YuiExample(
        name="basic_arithmetic",
        description="Basic variable definition and increment/decrement",
        ast_node=BlockNode(statements, top_level=True)
    )


# サンプル2: ループとカウンター
def example_loop():
    """ループのサンプル"""
    statements = [
        AssignmentNode(NameNode("count"),NumberNode(0)),
        RepeatNode(
            NumberNode(10),
            BlockNode([
                IncrementNode(NameNode("count")),
                IfNode(NameNode("count"), "==", NumberNode(5), BlockNode(BreakNode())),
            ]),
        ),
        AssertNode(NameNode("count"), NumberNode(5)),
    ]

    return YuiExample(
        name="loop",
        description="Loop 10 times and break at 5",
        ast_node=BlockNode(statements, top_level=True)
    )


# サンプル3: 条件分岐
def example_conditional():
    """条件分岐のサンプル"""
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))
    statements = [
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(0)),
        AssignmentNode(NameNode("z"), NumberNode(0)),
        IfNode(NameNode("x"),"==", NumberNode(1),then_block, else_block),
        IfNode(NameNode("x"),"!=", NumberNode(1),then_block, else_block),
        IfNode(NameNode("x"),"<=", NumberNode(1),then_block, else_block),
        IfNode(NameNode("x"),">=", NumberNode(1),then_block, else_block),
        IfNode(NameNode("x"),"<", NumberNode(1),then_block, else_block),
        IfNode(NameNode("x"),">", NumberNode(1),then_block, else_block),
        AssertNode(NameNode("y"), NumberNode(3)),
        AssertNode(NameNode("z"), NumberNode(3)),
    ]
    return YuiExample(
        name="conditional",
        description="Conditional branching (if-else)",
        ast_node=BlockNode(statements, top_level=True)
    )

# サンプル3: 条件分岐
def example_nested_conditional():
    """ネストした条件分岐のサンプル"""
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))
    statements = [
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(2)),
        AssignmentNode(NameNode("z"), NumberNode(3)),
        IfNode(NameNode("x"),"==", NumberNode(0),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(1),then_block, else_block)),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(2),then_block, else_block))
        ),
        AssertNode(NameNode("y"), NumberNode(3)),
    ]
    return YuiExample(
        name="nested_conditional",
        description="Nested conditional branching",
        ast_node=BlockNode(statements, top_level=True)
    )

# サンプル4: 配列操作
def example_array():
    """配列操作のサンプル"""
    statements = [
        AssignmentNode(NameNode("A"),ArrayNode([NumberNode(1),NumberNode(2),NumberNode(3)])),
        AppendNode(NameNode("A"),NumberNode(0)),
        IncrementNode(GetIndexNode(NameNode("A"), NumberNode(0))),
        IfNode(NumberNode(2), "in", NameNode("A"),
            AssignmentNode(GetIndexNode(NameNode("A"), NumberNode(0)),GetIndexNode(NameNode("A"), NumberNode(3)))
        ),
        AssertNode(ArrayLenNode(NameNode("A")), NumberNode(4)),
    ]
    return YuiExample(
        name="array",
        description="Array creation and element manipulation",
        ast_node=BlockNode(statements, top_level=True)
    )


# サンプル5: 関数定義と呼び出し
def example_function():
    """関数のサンプル"""
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
        FuncDefNode(
            NameNode("zero"), [], BlockNode(ReturnNode(NumberNode(0)))
        ),
        AssertNode(FuncAppNode(NameNode("zero"), []), NumberNode(0)),
        FuncDefNode(
            NameNode("point"), [NameNode("x"), NameNode("y")], BlockNode([])
        ),
        AssignmentNode(NameNode("O"), FuncAppNode(NameNode("point"), [NumberNode(0), NumberNode(0)])),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(0)),
    ]
    return YuiExample(
        name="function",
        description="Function definition and call (increment function)",
        ast_node=BlockNode(statements, top_level=True)
    )


# すべてのサンプルを取得
def get_all_examples() -> List[YuiExample]:
    """すべてのサンプルを返す"""
    return [
        example_basic_arithmetic(),
        example_loop(),
        example_conditional(),
        example_nested_conditional(),
        example_array(),
        example_function(),
    ]


def print_example(example: YuiExample, syntaxes: List[str] = None):
    """
    サンプルを複数の構文で出力

    Args:
        example: YuiExampleオブジェクト
        syntaxes: 構文ファイルのリスト（Noneの場合はデフォルト構文のみ）
    """
    if syntaxes is None:
        syntaxes = ['syntax-yui.json']

    print(f"\n{'='*60}")
    print(f"サンプル名: {example.name}")
    print(f"説明: {example.description}")
    print(f"{'='*60}")

    for syntax in syntaxes:
        try:
            import os
            syntax_basename = os.path.basename(syntax)
            syntax_name = syntax_basename.replace('syntax-', '').replace('.json', '')
            code = example.generate(syntax)
            print(f"\n--- {syntax_name} 構文 ---")
            print(code)
        except Exception as e:
            print(f"\n--- {syntax_name} 構文 (エラー) ---")
            print(f"エラー: {e}")


def main():
    """メイン関数 - すべてのサンプルを出力"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Yui言語のサンプルコード生成ツール'
    )
    parser.add_argument(
        '--syntax',
        nargs='+',
        default=['syntax-yui.json', 'syntax-py.json'],
        help='使用する構文ファイル（複数指定可）'
    )
    parser.add_argument(
        '--example',
        type=str,
        help='特定のサンプルのみ生成（サンプル名を指定）'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='利用可能なサンプルの一覧を表示'
    )

    args = parser.parse_args()

    examples = get_all_examples()

    # サンプル一覧を表示
    if args.list:
        print("\n利用可能なサンプル:")
        for ex in examples:
            print(f"  {ex.name:20s} - {ex.description}")
        return

    # 特定のサンプルのみ生成
    if args.example:
        example = next((ex for ex in examples if ex.name == args.example), None)
        if example:
            print_example(example, args.syntax)
        else:
            print(f"エラー: サンプル '{args.example}' が見つかりません")
            print("\n利用可能なサンプル:")
            for ex in examples:
                print(f"  - {ex.name}")
        return

    # すべてのサンプルを生成
    for example in examples:
        print_example(example, args.syntax)


if __name__ == '__main__':
    main()
