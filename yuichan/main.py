#!/usr/bin/env python
"""
Yui言語のCLIインターフェース
"""

import sys
import json
import os
import argparse
from typing import Dict, Any

try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

from yuichan import __version__
from .yuiparser import YuiParser, CodingVisitor
from .yuiast import YuiRuntime, YuiError
from . import yuiexample


def main(argv=None):
    """メインエントリーポイント"""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='yui',
        description=f'Yui Language Interpreter v{__version__}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  yui file.yui                              # ファイルを実行
  yui -i                                    # 対話モード
  yui --input input.json file.yui           # 環境を読み込んで実行
  yui file.yui --output output.json         # 実行後の環境を保存
  yui --syntax syntax-py.json file.yui     # カスタム構文で実行
  yui --syntax syntax-yui.json file.yui --syntax-to syntax-py.json  # 構文変換
  yui --syntax syntax-yui.json file.md --syntax-to syntax-py.json   # Markdown変換
  yui --list-examples                       # サンプル一覧を表示
  yui --make-examples                       # 全サンプルを生成（Yui + Python風）
  yui --make-examples --example loop        # 特定のサンプルのみ生成
  yui --make-examples --syntax syntax-yui.json  # Yui構文のみで生成
"""
    )

    parser.add_argument('-V', '--version', action='version',
                        version=f'Yui {__version__}')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='対話モードで起動')
    parser.add_argument('--syntax', type=str, metavar='FILE',
                        help='構文ファイル（JSON）を指定（実行時は必須）')
    parser.add_argument('--syntax-to', type=str, metavar='FILE',
                        help='変換先の構文ファイル（--syntaxと併用）')
    parser.add_argument('--input', type=str, metavar='FILE',
                        help='環境変数をJSONファイルから読み込む')
    parser.add_argument('--output', type=str, metavar='FILE',
                        help='実行後の環境変数をJSONファイルに保存')
    parser.add_argument('--make-examples', action='store_true',
                        help='サンプルコードを生成')
    parser.add_argument('--example', type=str, metavar='NAME',
                        help='特定のサンプルのみ生成（--make-examplesと併用）')
    parser.add_argument('--list-examples', action='store_true',
                        help='利用可能なサンプル一覧を表示')
    parser.add_argument('file', nargs='?', help='実行するYuiファイル')

    args = parser.parse_args(argv)

    try:
        # サンプル一覧表示
        if args.list_examples:
            list_examples()
            return

        # サンプル生成モード
        if args.make_examples:
            if not args.syntax:
                print("エラー: --syntax オプションが必要です", file=sys.stderr)
                print("例: yui --syntax syntax-yui.json --make-examples", file=sys.stderr)
                print("\n利用可能な構文ファイル:", file=sys.stderr)
                print("  - syntax-yui.json  (日本語風)", file=sys.stderr)
                print("  - syntax-py.json   (Python風)", file=sys.stderr)
                sys.exit(1)
            syntaxes = [args.syntax]
            make_examples(args.example, syntaxes)
            return

        # 構文ファイルの必須チェック（実行・対話・変換モード）
        if not args.syntax:
            print("エラー: --syntax オプションが必要です", file=sys.stderr)
            print("\n使用方法:", file=sys.stderr)
            print("  yui --syntax <構文ファイル> [オプション] [ファイル]", file=sys.stderr)
            print("\n例:", file=sys.stderr)
            print("  yui --syntax syntax-yui.json file.yui", file=sys.stderr)
            print("  yui --syntax syntax-py.json -i", file=sys.stderr)
            print("\n利用可能な構文ファイル:", file=sys.stderr)
            print("  - syntax-yui.json  (日本語風)", file=sys.stderr)
            print("  - syntax-py.json   (Python風)", file=sys.stderr)
            sys.exit(1)

        syntax = args.syntax

        # 環境の初期化
        env = {}
        if args.input:
            env = load_env_from_json(args.input)
            print(f"環境を読み込みました: {args.input}")

        # 構文変換モード
        if args.syntax_to:
            if not args.file:
                print("エラー: --syntax-to には入力ファイルが必要です", file=sys.stderr)
                sys.exit(1)
            convert_syntax(args.file, syntax, args.syntax_to)
            return

        # ファイル実行
        if args.file:
            env = run_file(args.file, env, syntax)

            # 環境の保存
            if args.output:
                save_env_to_json(env, args.output)
                print(f"環境を保存しました: {args.output}")

            return

        # 対話モード
        if args.interactive or not args.file:
            interactive_mode(env, syntax)
            return

    except YuiError as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n終了します")
        sys.exit(0)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_file(filename: str, env: Dict[str, Any], syntax: str = 'syntax-yui.json') -> Dict[str, Any]:
    """ファイルを実行"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    # パーサーで構文木を生成
    parser = YuiParser(syntax)
    ast = parser.parse(code)

    # ランタイムで実行
    runtime = YuiRuntime()
    for key, value in env.items():
        runtime.setenv(key, value)

    ast.evaluate(runtime)

    # 環境を返す（最後のスコープから取得）
    result_env = {}
    if runtime.enviroments:
        result_env = runtime.enviroments[-1].copy()

    return result_env


def interactive_mode(env: Dict[str, Any], syntax: str = 'syntax-yui.json'):
    """対話モード"""
    print(f"Yui v{__version__} - 対話モード")
    print(f"構文: {syntax}")
    print("終了するには 'quit' または 'exit' を入力してください\n")

    # readline の履歴ファイルを設定
    history_file = os.path.expanduser("~/.yui_history")
    if READLINE_AVAILABLE:
        try:
            if os.path.exists(history_file):
                readline.read_history_file(history_file)
            readline.set_history_length(1000)
        except Exception:
            pass

    runtime = YuiRuntime()
    for key, value in env.items():
        runtime.setenv(key, value)

    try:
        while True:
            try:
                code = input(">>> ")
                if code.lower() in ['quit', 'exit']:
                    break

                code = code.strip()
                if code == "":
                    # 環境を表示
                    if runtime.enviroments and len(runtime.enviroments[-1]) > 0:
                        print(json.dumps(runtime.enviroments[-1], indent=2, ensure_ascii=False))
                    continue

                # パースして実行
                parser = YuiParser(syntax)
                ast = parser.parse(code)
                ast.evaluate(runtime)

            except YuiError as e:
                print(f"エラー: {e}")
            except KeyboardInterrupt:
                print("\n終了します")
                break
            except EOFError:
                print("\n終了します")
                break
    finally:
        if READLINE_AVAILABLE:
            try:
                readline.write_history_file(history_file)
            except Exception:
                pass


def convert_syntax(input_file: str, source_syntax: str, target_syntax: str):
    """構文変換"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Markdownファイルの場合
    if input_file.endswith('.md'):
        convert_markdown(content, source_syntax, target_syntax)
    else:
        # 通常のファイル変換
        parser = YuiParser(source_syntax)
        ast = parser.parse(content)

        visitor = CodingVisitor(target_syntax)
        converted = visitor.emit(ast)

        print(converted)


def convert_markdown(content: str, source_syntax: str, target_syntax: str):
    """Markdownファイル内のコードブロックを変換"""
    lines = content.split('\n')
    in_code_block = False
    current_block = []

    for line in lines:
        stripped = line.strip()

        # ```yui で始まるブロックを検出
        if stripped.startswith("```yui") and not in_code_block:
            in_code_block = True
            current_block = []
            print(line)  # コードブロック開始をそのまま出力
            continue

        # コードブロック終了
        if stripped.startswith("```") and in_code_block:
            # コードブロックを変換
            code = '\n'.join(current_block)
            if code.strip():
                try:
                    parser = YuiParser(source_syntax)
                    ast = parser.parse(code)

                    visitor = CodingVisitor(target_syntax)
                    converted = visitor.emit(ast)

                    print(converted)
                except Exception as e:
                    print(f"# 変換エラー: {e}")
                    print(code)

            print(line)  # コードブロック終了をそのまま出力
            in_code_block = False
            current_block = []
            continue

        # コードブロック内
        if in_code_block:
            current_block.append(line)
        else:
            # コードブロック外はそのまま出力
            print(line)


def load_env_from_json(filename: str) -> Dict[str, Any]:
    """JSONファイルから環境を読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_env_to_json(env: Dict[str, Any], filename: str):
    """環境をJSONファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(env, f, indent=2, ensure_ascii=False)


def list_examples():
    """利用可能なサンプル一覧を表示"""
    examples = yuiexample.get_all_examples()
    print("\n利用可能なサンプル:")
    print(f"{'名前':<20} 説明")
    print("-" * 60)
    for ex in examples:
        print(f"{ex.name:<20} {ex.description}")


def make_examples(example_name: str = None, syntaxes: list = None):
    """
    サンプルコードを生成

    Args:
        example_name: 特定のサンプル名（Noneの場合は全サンプル）
        syntaxes: 構文ファイルのリスト
    """
    if syntaxes is None:
        syntaxes = ['syntax-yui.json', 'syntax-py.json']

    examples = yuiexample.get_all_examples()

    # 特定のサンプルのみ生成
    if example_name:
        example = next((ex for ex in examples if ex.name == example_name), None)
        if example:
            yuiexample.print_example(example, syntaxes)
        else:
            print(f"エラー: サンプル '{example_name}' が見つかりません", file=sys.stderr)
            print("\n利用可能なサンプル:")
            for ex in examples:
                print(f"  - {ex.name}")
            sys.exit(1)
        return

    # すべてのサンプルを生成
    for example in examples:
        yuiexample.print_example(example, syntaxes)


if __name__ == "__main__":
    main()
