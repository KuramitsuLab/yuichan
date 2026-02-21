"""
claude.py — ラウンドトリップ・バグ分析用ツール

目的:
  - yuiexample の AST からコードを生成し、再パースできるかを検証する
  - パース失敗時のエラー位置と周辺コンテキストを可視化する
  - CodingVisitor / BlockParser のバグを局所的に再現・確認する

このファイルは削除しない。デバッグ・回帰確認に再利用する。
"""
from yuichan.yuiexample import get_all_examples
from yuichan.yuiparser import Source, parse
from yuichan.yuisyntax import load_syntax
from yuichan.yuitypes import YuiError


def check_roundtrip(syntax_name: str, example_name: str, verbose=True) -> bool:
    """
    指定した syntax と example でコード生成→再パースを試みる。
    成功なら True、失敗なら False を返す。verbose=True でエラー詳細を表示。
    """
    examples = {ex.name: ex for ex in get_all_examples()}
    syntax = load_syntax(syntax_name)
    example = examples[example_name]
    code = example.generate(syntax)
    if verbose:
        print(f"=== {syntax_name}/{example_name} ===")
        for i, line in enumerate(code.split('\n')):
            print(f"  {i:2d}: {repr(line)}")
        print()
    source = Source(code, syntax=syntax)
    try:
        parse('@TopLevel', source, pc={})
        if verbose:
            print("  → OK")
        return True
    except YuiError as e:
        if verbose:
            pos = e.error_node.pos
            before = code[max(0, pos - 60):pos]
            after  = code[pos:pos + 60]
            print(f"  → FAIL at pos={pos}")
            print(f"     before: {repr(before)}")
            print(f"     >>>HERE: {repr(after)}")
            print(f"     error: {e}")
        return False


def show_funcapp_tokens(syntax_name: str):
    """
    指定 syntax の funcapp 関連トークンを一覧表示する。
    Bug 2 (visitFuncAppNode のトークン名不一致) の確認に使う。
    load_syntax は dict を返す。
    """
    syntax = load_syntax(syntax_name)
    print(f"=== funcapp tokens in {syntax_name} ===")
    for key in sorted(syntax):
        if 'funcapp' in key:
            print(f"  {key}: {repr(syntax[key])}")


def emit_funcapp_example(syntax_name: str):
    """
    FuncAppNode(f, [x, 1]) を指定 syntax で emit した結果を表示する。
    Bug 2: funcapp-suffix vs funcapp-args-suffix の差異確認に使う。
    """
    from yuichan.yuicoding import CodingVisitor
    from yuichan.yuiast import FuncAppNode, NameNode, NumberNode
    syntax = load_syntax(syntax_name)
    visitor = CodingVisitor(syntax)
    node = FuncAppNode(NameNode('f'), [NameNode('x'), NumberNode(1)])
    result = visitor.emit(node)
    print(f"{syntax_name}: {repr(result)}")


def emit_block_with_comment_only(syntax_name: str):
    """
    PassNode(comment=...) 1つだけを含む FuncDefNode を emit する。
    Bug 1: block-end のインデントずれの確認に使う。
    """
    from yuichan.yuicoding import CodingVisitor
    from yuichan.yuiast import FuncDefNode, NameNode, BlockNode, PassNode
    syntax = load_syntax(syntax_name)
    visitor = CodingVisitor(syntax)
    node = FuncDefNode(
        NameNode("f"), [NameNode("x")],
        BlockNode([PassNode(comment="comment only body")])
    )
    result = visitor.emit(node)
    print(f"=== {syntax_name}: FuncDef with comment-only body ===")
    for i, line in enumerate(result.split('\n')):
        print(f"  {i}: {repr(line)}")


if __name__ == '__main__':
    # Bug 1: block-end インデントずれ (yui/emoji の function_without_return)
    print("■ Bug 1: block-end indent mismatch")
    emit_block_with_comment_only('yui')
    emit_block_with_comment_only('emoji')

    print()
    check_roundtrip('yui',   'function_without_return')
    check_roundtrip('emoji', 'function_without_return')

    # Bug 2: visitFuncAppNode のトークン名不一致
    print("\n■ Bug 2: funcapp token name mismatch")
    for sn in ['yui', 'pylike', 'emoji']:
        show_funcapp_tokens(sn)
    print()
    for sn in ['yui', 'pylike', 'emoji']:
        emit_funcapp_example(sn)

    print()
    check_roundtrip('emoji', 'recursive_function')
