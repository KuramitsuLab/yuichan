#!/usr/bin/env python
"""
Yui言語のサンプルコード生成ツール

ASTノードを使ってサンプルコードを構築し、
CodeVisitorで異なる構文（Yui、Python風など）に変換して出力します。
"""

from typing import List, Dict
from .yuiast import (
    NumberNode, StringNode, NameNode, ArrayNode, ObjectNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode,
    BinaryNode, GetIndexNode,
)
from .yuiparser import CodingVisitor, load_syntax


class YuiExample:
    """Yui言語のサンプルコード生成クラス"""

    def __init__(self, name: str, description: str, ast_node):
        """
        Args:
            name: サンプルの名前
            description: サンプルの説明
            ast_node: ASTノード（BlockNode推奨）
        """
        self.name = name
        self.description = description
        self.ast_node = ast_node

    def generate(self, syntax: str = 'syntax-yui.json') -> str:
        """
        指定された構文でコードを生成

        Args:
            syntax: 構文ファイルのパス

        Returns:
            生成されたコード文字列
        """
        visitor = CodingVisitor(syntax)
        return visitor.emit(self.ast_node)


# サンプル1: 基本的な変数と演算
def example_basic_arithmetic():
    """基本的な算術演算のサンプル"""
    statements = [
        AssignmentNode(
            NameNode("x"),
            NumberNode(10)
        ),
        AssignmentNode(
            NameNode("y"),
            NumberNode(20)
        ),
        IncrementNode(NameNode("x")),
        DecrementNode(NameNode("y")),
    ]

    return YuiExample(
        name="basic_arithmetic",
        description="基本的な変数の定義とインクリメント・デクリメント",
        ast_node=BlockNode(*statements)
    )


# サンプル2: ループとカウンター
def example_loop():
    """ループのサンプル"""
    statements = [
        AssignmentNode(
            NameNode("count"),
            NumberNode(0)
        ),
        RepeatNode(
            NumberNode(5),
            BlockNode(
                IncrementNode(NameNode("count"))
            )
        ),
    ]

    return YuiExample(
        name="loop",
        description="5回ループしてカウンターを増やす",
        ast_node=BlockNode(*statements)
    )


# サンプル3: 条件分岐
def example_conditional():
    """条件分岐のサンプル"""
    statements = [
        AssignmentNode(
            NameNode("x"),
            NumberNode(10)
        ),
        IfNode(
            left=NameNode("x"),
            operator="eq",
            right=NumberNode(10),
            then_block=BlockNode(
                AssignmentNode(
                    NameNode("result"),
                    StringNode("equal")
                )
            ),
            else_block=BlockNode(
                AssignmentNode(
                    NameNode("result"),
                    StringNode("not equal")
                )
            )
        ),
    ]

    return YuiExample(
        name="conditional",
        description="条件分岐（if-else）のサンプル",
        ast_node=BlockNode(*statements)
    )


# サンプル4: 配列操作
def example_array():
    """配列操作のサンプル"""
    statements = [
        AssignmentNode(
            NameNode("numbers"),
            ArrayNode([
                NumberNode(1),
                NumberNode(2),
                NumberNode(3)
            ])
        ),
        AppendNode(
            NameNode("numbers"),
            NumberNode(4)
        ),
        AppendNode(
            NameNode("numbers"),
            NumberNode(5)
        ),
    ]

    return YuiExample(
        name="array",
        description="配列の作成と要素の追加",
        ast_node=BlockNode(*statements)
    )


# サンプル5: 関数定義と呼び出し
def example_function():
    """関数のサンプル"""
    statements = [
        FuncDefNode(
            name_node=NameNode("double"),
            parameters=[NameNode("n")],
            body=BlockNode(
                ReturnNode(
                    BinaryNode(
                        NameNode("n"),
                        "*",
                        NumberNode(2)
                    )
                )
            )
        ),
        AssignmentNode(
            NameNode("result"),
            FuncAppNode(
                NameNode("double"),
                [NumberNode(21)]
            )
        ),
    ]

    return YuiExample(
        name="function",
        description="関数の定義と呼び出し（2倍にする関数）",
        ast_node=BlockNode(*statements)
    )


# サンプル6: ネストしたループとbreak
def example_nested_loop_with_break():
    """ネストループとbreakのサンプル"""
    statements = [
        AssignmentNode(
            NameNode("x"),
            NumberNode(0)
        ),
        RepeatNode(
            NumberNode(10),
            BlockNode(
                IncrementNode(NameNode("x")),
                IfNode(
                    left=NameNode("x"),
                    operator="eq",
                    right=NumberNode(5),
                    then_block=BlockNode(
                        BreakNode()
                    )
                )
            )
        ),
    ]

    return YuiExample(
        name="loop_with_break",
        description="ループとbreak文（5回でループを抜ける）",
        ast_node=BlockNode(*statements)
    )


# すべてのサンプルを取得
def get_all_examples() -> List[YuiExample]:
    """すべてのサンプルを返す"""
    return [
        example_basic_arithmetic(),
        example_loop(),
        example_conditional(),
        example_array(),
        example_function(),
        example_nested_loop_with_break(),
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
