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
                    and (filtered[-1].comment.lower().startswith('test')
                         or filtered[-1].comment.startswith('テスト'))):
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

    def generate(self, syntax: str = 'yui', include_asserts: bool = True,
                 random_seed=None, indent_string=None, function_language=None) -> str:
        node = self.ast_node if include_asserts else _strip_asserts(self.ast_node)
        visitor = CodingVisitor(syntax, function_language=function_language)
        emit_kwargs = dict(random_seed=random_seed)
        if indent_string is not None:
            emit_kwargs['indent_string'] = indent_string
        return visitor.emit(node, **emit_kwargs)

def example_hello_world():
    statements = [
        PassNode(comment='"Hello, world!" と表示する'),
        PrintExpressionNode(StringNode("Hello, world!")),
    ]
    return YuiExample(
        name="hello_world",
        description="'Hello, world!' を表示する",
        ast_node=BlockNode(statements, top_level=True),
        kind='sample',
    )

def example_variables():
    """基本的な算術演算のサンプル"""
    statements = [
        PassNode(comment="変数 x と y を定義する"),
        AssignmentNode(NameNode("x"),NumberNode(1)),
        AssignmentNode(NameNode("y"),MinusNode(NumberNode(2))),
        PassNode(comment="x を1増やす"),
        IncrementNode(NameNode("x")),
        PassNode(comment="y を1減らす"),
        DecrementNode(NameNode("y")),
        PassNode(comment="テスト: x が 2、y が -3"),
        AssertNode(NameNode("x"), NumberNode(2)),
        AssertNode(NameNode("y"), MinusNode(NumberNode(3))),
    ]
    return YuiExample(
        name="variables",
        description="変数の定義とインクリメント/デクリメント",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_loop():
    """ループのサンプル"""
    statements = [
        PassNode(comment="10回ループして5回目でブレイク"),
        AssignmentNode(NameNode("count"),NumberNode(0)),
        RepeatNode(
            NumberNode(10),
            BlockNode([
                IncrementNode(NameNode("count")),
                IfNode(NameNode("count"), "==", NumberNode(5), BlockNode(BreakNode())),
            ]),
        ),
        PassNode(comment="テスト: count が 5"),
        AssertNode(NameNode("count"), NumberNode(5)),
    ]
    return YuiExample(
        name="loop",
        description="10回ループして5回目でブレイク",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_fizzbuzz():
    """1から100までのFizzBuzzをリストに追加する"""
    statements = [
        PassNode(comment="1から100までのFizzBuzzをリストに収集する"),
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
        PassNode(comment="テスト: 長さが100"),
        AssertNode(ArrayLenNode(NameNode("result")), NumberNode(100)),
        PassNode(comment="テスト: Fizz、Buzz、FizzBuzz の位置を確認"),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(2)),  StringNode("Fizz")),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(4)),  StringNode("Buzz")),
        AssertNode(GetIndexNode(NameNode("result"), NumberNode(14)), StringNode("FizzBuzz")),
    ]
    return YuiExample(
        name="fizzbuzz",
        description="1から100までのFizzBuzzをリストに収集する",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_nested_conditional_branches():
    """ネストした条件分岐のサンプル"""
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))
    statements = [
        PassNode(comment="x と y に対するネストした条件をテスト"),
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(2)),
        AssignmentNode(NameNode("z"), NumberNode(3)),
        PassNode(comment="x が 0 なら y を確認して y または z を増やす"),
        IfNode(NameNode("x"),"==", NumberNode(0),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(1),then_block, else_block)),
            BlockNode(IfNode(NameNode("y"),"==", NumberNode(2),then_block, else_block))
        ),
        PassNode(comment="テスト: y が増えて z が増えていない"),
        AssertNode(NameNode("y"), NumberNode(3)),
    ]
    return YuiExample(
        name="nested_conditional_branches",
        description="ネストした条件分岐",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_comparisons():
    then_block = IncrementNode(NameNode("y"))
    else_block = IncrementNode(NameNode("z"))

    statements = [
        PassNode(comment="x に対するさまざまな比較"),
        AssignmentNode(NameNode("x"), NumberNode(1)),
        AssignmentNode(NameNode("y"), NumberNode(0)),
        AssignmentNode(NameNode("z"), NumberNode(0)),
        PassNode(comment="x は 1 と等しいか？"),
        IfNode(NameNode("x"),"==", NumberNode(1),then_block, else_block),
        PassNode(comment="x は 1 と等しくないか？"),
        IfNode(NameNode("x"),"!=", NumberNode(1),then_block, else_block),
        PassNode(comment="x は 1 より小さいか？"),
        IfNode(NameNode("x"),"<", NumberNode(1),then_block, else_block),
        PassNode(comment="x は 1 より大きいか？"),
        IfNode(NameNode("x"),">", NumberNode(1),then_block, else_block),
        PassNode(comment="x は 1 以下か？"),
        IfNode(NameNode("x"),"<=", NumberNode(1),then_block, else_block),
        PassNode(comment="x は 1 以上か？"),
        IfNode(NameNode("x"),">=", NumberNode(1),then_block, else_block),
        PassNode(comment="テスト: すべての条件が正しく評価された"),
        AssertNode(NameNode("y"), NumberNode(3)),
        AssertNode(NameNode("z"), NumberNode(3)),
    ]
    return YuiExample(
        name="comparisons",
        description="比較演算",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_array():
    """配列操作のサンプル"""
    statements = [
        PassNode(comment="要素 1, 2, 3 を持つ配列 A を作成する"),
        AssignmentNode(NameNode("A"),ArrayNode([NumberNode(1),NumberNode(2),NumberNode(3)])),
        PassNode(comment="A の末尾に 0 を追加する"),
        AppendNode(NameNode("A"),NumberNode(0)),
        PassNode(comment="A の最初の要素を1増やす"),
        IncrementNode(GetIndexNode(NameNode("A"), NumberNode(0))),
        PassNode(comment="A に 2 があれば、最初の要素を4番目の要素に設定する"),
        IfNode(NumberNode(2), "in", NameNode("A"),
            AssignmentNode(GetIndexNode(NameNode("A"), NumberNode(0)),GetIndexNode(NameNode("A"), NumberNode(3)))
        ),
        PassNode(comment="テスト: 配列が4要素"),
        AssertNode(ArrayLenNode(NameNode("A")), NumberNode(4)),
    ]
    return YuiExample(
        name="array",
        description="配列の作成と要素操作",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_strings():
    """文字列操作のサンプル"""
    statements = [
        PassNode(comment="'hello' という文字列 s を作成する"),
        AssignmentNode(NameNode("s"), StringNode("hello")),
        PassNode(comment="s の最初の文字を 'H' に設定する"),
        PassNode(comment="注: 文字列は文字コードの配列です。配列と同様に操作できます。"),
        AssignmentNode(GetIndexNode(NameNode("s"), NumberNode(0)), GetIndexNode(StringNode("H"), 0)),
        PassNode(comment='s に " world" を連結する'),
        AssignmentNode(NameNode("t"), StringNode(" world")),
        AssignmentNode(NameNode("i"), NumberNode(0)),
        RepeatNode(ArrayLenNode(NameNode("t")), BlockNode([
            AppendNode(NameNode("s"), GetIndexNode(NameNode("t"), NameNode("i"))),
            IncrementNode(NameNode("i")),
        ])),
        PassNode(comment="テスト: s が 'Hello world' になっている"),
        AssertNode(NameNode("s"), StringNode("Hello world")),
    ]
    return YuiExample(
        name="strings",
        description="文字列の作成と操作",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_objects():
    """オブジェクト操作のサンプル"""
    statements = [
        PassNode(comment="プロパティ x と y を持つオブジェクト O を作成する"),
        AssignmentNode(NameNode("O"), ObjectNode({
            "x": NumberNode(0),
            "y": NumberNode(0)
        })),
        PassNode(comment="O の x プロパティを 1 に設定する"),
        AssignmentNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(1)),
        PassNode(comment="O の y プロパティを 2 に設定する"),
        AssignmentNode(GetIndexNode(NameNode("O"), StringNode("y")), NumberNode(2)),
        PassNode(comment="テスト: O のプロパティが x=1、y=2"),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(1)),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("y")), NumberNode(2)),
    ]
    return YuiExample(
        name="objects",
        description="オブジェクトの作成とプロパティ操作",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_function():
    statements = [
        PassNode(comment="1を加算する関数を定義する"),
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
        description="関数の定義と呼び出し（インクリメント関数）",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )

def example_function_no_argument():
    statements = [
        PassNode(comment="引数なしで 0 を返す関数を定義する"),
        FuncDefNode(
            NameNode("zero"), [], BlockNode(ReturnNode(NumberNode(0)))
        ),
        AssertNode(FuncAppNode(NameNode("zero"), []), NumberNode(0)),
    ]
    return YuiExample(
        name="function_no_argument",
        description="関数の定義と呼び出し（引数なし関数と複数引数関数）",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_function_without_return():
    statements = [
        PassNode(comment="点オブジェクトを作成する関数を定義する"),
        FuncDefNode(
            NameNode("point"), [NameNode("x"), NameNode("y")], BlockNode([
                PassNode(comment="関数が何も返さない場合、ローカル環境をオブジェクトとして返す"),
            ])
        ),
        AssignmentNode(NameNode("O"), FuncAppNode(NameNode("point"), [NumberNode(0), NumberNode(0)])),
        AssertNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(0)),
    ]
    return YuiExample(
        name="function_without_return",
        description="関数の定義と呼び出し（戻り値なし関数）",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )

def example_recursive_function():
    """関数のサンプル"""
    statements = [
        PassNode(comment="階乗を計算する再帰関数を定義する"),
        FuncDefNode(
            NameNode("fact"), [NameNode("n")],
            BlockNode([
                IfNode(NameNode("n"), "==", NumberNode(0),
                    BlockNode([ReturnNode(NumberNode(1))]),
                    BlockNode([
                        PassNode(comment="Yui には算術演算子がありません。"),
                        ReturnNode(FuncAppNode(NameNode("multiplex"), 
                        [NameNode("n"), FuncAppNode(NameNode("fact"), 
                                                    [FuncAppNode(NameNode("decrease"), [NameNode("n")])])]))
                    ])
                )
            ])
        ),
        PassNode(comment="multiplex(a, b): a * b を計算する関数"),
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
        PassNode(comment="decrease(n): n-1 を計算する関数"),
        FuncDefNode(
            NameNode("decrease"), [NameNode("n")], BlockNode([
                DecrementNode(NameNode("n")),
                ReturnNode(NameNode("n"))
            ])
        ),
        PassNode(comment="テスト: fact(0) が 1"),
        AssertNode(FuncAppNode(NameNode("fact"),[NumberNode(0)]), NumberNode(1)),
        PassNode(comment="テスト: fact(5) が 120"),
        AssertNode(FuncAppNode(NameNode("fact"),[NumberNode(5)]), NumberNode(120)),
    ]
    return YuiExample(
        name="recursive_function",
        description="再帰関数の定義と呼び出し（階乗関数）",
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
        PassNode(comment="float形式: [符号, d1..d7]  符号=1または-1、d1..d7 = abs(x)*1e6 の各桁"),
        PassNode(comment="float_add(a, b): 同符号の float 配列を足し合わせる（stdlib なし）"),
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
        PassNode(comment="1.99 + 1.01 = 3.00  (繰り上がり伝播のテスト)"),
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
        description="同符号の float を桁配列として加算する（stdlib なし）",
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
        PassNode(comment="非負整数向けの四則演算関数"),
        PassNode(comment="add(a, b): a + b"),
        add_func,
        PassNode(comment="subtract(a, b): a - b  (a >= b が必要)"),
        subtract_func,
        PassNode(comment="multiply(a, b): a * b"),
        multiply_func,
        PassNode(comment="divide(a, b): 整数商 a // b"),
        divide_func,
        PassNode(comment="modulo(a, b): 余り a % b"),
        modulo_func,
        PassNode(comment="使用例"),
        PrintExpressionNode(FuncAppNode(NameNode("add"),      [NumberNode(3),  NumberNode(4)])),
        PrintExpressionNode(FuncAppNode(NameNode("subtract"), [NumberNode(10), NumberNode(3)])),
        PrintExpressionNode(FuncAppNode(NameNode("multiply"), [NumberNode(3),  NumberNode(4)])),
        PrintExpressionNode(FuncAppNode(NameNode("divide"),   [NumberNode(10), NumberNode(3)])),
        PrintExpressionNode(FuncAppNode(NameNode("modulo"),   [NumberNode(10), NumberNode(3)])),
        PassNode(comment="テスト: add"),
        AssertNode(FuncAppNode(NameNode("add"), [NumberNode(3), NumberNode(4)]), NumberNode(7)),
        AssertNode(FuncAppNode(NameNode("add"), [NumberNode(0), NumberNode(5)]), NumberNode(5)),
        PassNode(comment="テスト: subtract"),
        AssertNode(FuncAppNode(NameNode("subtract"), [NumberNode(10), NumberNode(3)]), NumberNode(7)),
        AssertNode(FuncAppNode(NameNode("subtract"), [NumberNode(5),  NumberNode(5)]), NumberNode(0)),
        PassNode(comment="テスト: multiply"),
        AssertNode(FuncAppNode(NameNode("multiply"), [NumberNode(3), NumberNode(4)]), NumberNode(12)),
        AssertNode(FuncAppNode(NameNode("multiply"), [NumberNode(0), NumberNode(5)]), NumberNode(0)),
        PassNode(comment="テスト: divide"),
        AssertNode(FuncAppNode(NameNode("divide"), [NumberNode(10), NumberNode(3)]), NumberNode(3)),
        AssertNode(FuncAppNode(NameNode("divide"), [NumberNode(9),  NumberNode(3)]), NumberNode(3)),
        PassNode(comment="テスト: modulo"),
        AssertNode(FuncAppNode(NameNode("modulo"), [NumberNode(10), NumberNode(3)]), NumberNode(1)),
        AssertNode(FuncAppNode(NameNode("modulo"), [NumberNode(15), NumberNode(5)]), NumberNode(0)),
    ]
    return YuiExample(
        name="arithmetic",
        description="非負整数向けの算術関数（add, subtract, multiply, divide, modulo）",
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
                        FuncAppNode(NameNode("小数化"), [NameNode("hits")]),
                        NumberNode(4),
                    ]),
                    FuncAppNode(NameNode("小数化"), [NameNode("n")]),
                ])
            ),
        ])
    )
    statements = [
        ImportNode(),
        PassNode(comment="モンテカルロ法: ランダム点のサンプリングで π を推定する"),
        PassNode(comment="単位正方形 [0,1)×[0,1) に n 個のランダム点を投げる。"),
        PassNode(comment="単位円内の点（dist ≤ 1）をカウントする。"),
        PassNode(comment="π ≈ 4 × (hits / n)"),
        monte_carlo_func,
        PassNode(comment="サンプル数が多いほど π ≈ 3.14159... に近づく"),
        PrintExpressionNode(FuncAppNode(NameNode("monte_carlo"), [NumberNode(100)])),
        PrintExpressionNode(FuncAppNode(NameNode("monte_carlo"), [NumberNode(1000)])),
    ]
    return YuiExample(
        name="monte_carlo",
        description="モンテカルロ法で π を推定する（stdlib: 乱数, 平方根）",
        ast_node=BlockNode(statements, top_level=True),
        kind='sample',
    )


def example_null_assignment():
    """null の代入と比較"""
    statements = [
        PassNode(comment="変数に null を代入する"),
        AssignmentNode(NameNode("x"), ConstNode(None)),
        PassNode(comment="テスト: x が null"),
        AssertNode(NameNode("x"), ConstNode(None)),
    ]
    return YuiExample(
        name="null_assignment",
        description="変数に null を代入して比較する",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def example_boolean_assignment():
    """true / false の代入とアサート"""
    statements = [
        PassNode(comment="true と false を変数に代入する"),
        AssignmentNode(NameNode("t"), ConstNode(True)),
        AssignmentNode(NameNode("f"), ConstNode(False)),
        PassNode(comment="テスト: t が true で f が false"),
        AssertNode(NameNode("t"), ConstNode(True)),
        AssertNode(NameNode("f"), ConstNode(False)),
    ]
    return YuiExample(
        name="boolean_assignment",
        description="変数に true/false を代入して比較する",
        ast_node=BlockNode(statements, top_level=True),
        kind='test',
    )


def example_boolean_branch():
    """boolean で条件分岐"""
    statements = [
        PassNode(comment="boolean 値で条件分岐する"),
        AssignmentNode(NameNode("flag"), ConstNode(True)),
        AssignmentNode(NameNode("result"), NumberNode(0)),
        IfNode(NameNode("flag"), "==", ConstNode(True),
            BlockNode(AssignmentNode(NameNode("result"), NumberNode(1))),
            BlockNode(AssignmentNode(NameNode("result"), NumberNode(2))),
        ),
        PassNode(comment="テスト: flag が true だったので result が 1"),
        AssertNode(NameNode("result"), NumberNode(1)),
    ]
    return YuiExample(
        name="boolean_branch",
        description="boolean 値に基づく条件分岐",
        ast_node=BlockNode(statements, top_level=True),
        kind='both',
    )


def example_null_check():
    """null チェック関数"""
    statements = [
        PassNode(comment="is_null 関数を定義する"),
        FuncDefNode(
            NameNode("is_null"), [NameNode("v")],
            BlockNode([
                IfNode(NameNode("v"), "==", ConstNode(None),
                    BlockNode(ReturnNode(ConstNode(True))),
                    BlockNode(ReturnNode(ConstNode(False))),
                )
            ])
        ),
        PassNode(comment="テスト: null と非 null の値で is_null を確認"),
        AssertNode(FuncAppNode(NameNode("is_null"), [ConstNode(None)]),  ConstNode(True)),
        AssertNode(FuncAppNode(NameNode("is_null"), [NumberNode(0)]),    ConstNode(False)),
        AssertNode(FuncAppNode(NameNode("is_null"), [StringNode("")]),   ConstNode(False)),
    ]
    return YuiExample(
        name="null_check",
        description="値が null かどうかを確認する関数",
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
