#!/usr/bin/env python
"""
Yui Language CLI Interface
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
from .yuiparser import YuiParser
from .yuicoding import CodingVisitor
from .yuisyntax import load_syntax, generate_bnf, list_syntax_names, find_matching_syntaxes
from .yuiruntime import YuiRuntime
from .yuitypes import YuiError
from .yuiast import IncrementNode, NameNode
from . import yuiexample
from . import message as _message


def main(argv=None):
    """Main entry point"""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='yui',
        description=f'Yui Language Interpreter v{__version__}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  yui --syntax yui file.yui                          # Execute a file
  yui --syntax yui -i                                # Interactive mode
  yui --syntax yui --input env.json file.yui         # Load environment and execute
  yui --syntax yui file.yui --output result.json     # Save environment after execution
  yui --syntax yui --convert-to pylike file.yui      # Convert a file (saved to pylike/)
  yui --syntax yui --convert-to pylike *.yui         # Convert multiple files
  yui --syntax yui --convert-to pylike file.md       # Convert Markdown code blocks
  yui --syntax yui --bnf                             # Show BNF grammar for a syntax
  yui --syntax yui --pass@1 test/*.yui               # Run tests and show pass rate
  yui --syntax yui --test-examples                   # Test built-in examples
  yui --syntax yui --make-examples                   # Generate example .yui files
  yui --list-examples                                # List available examples
  yui --list-syntax                                  # List syntax files with examples
  yui --find-syntax file.yui                        # Find syntax that can parse given files
  yui --find-syntax test/*.yui                      # Find syntax matching multiple files

Syntax files (yuichan/syntax/):
  yui      - Japanese-style natural syntax (default)
  pylike   - Python-style syntax
  emoji    - Emoji-based syntax

Error message languages (--lang):
  ja       - Japanese (default)
  (others) - raw message fallback
"""
    )

    parser.add_argument('-V', '--version', action='version',
                        version=f'Yui {__version__}')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Start in interactive mode')
    parser.add_argument('--syntax', type=str, metavar='FILE',
                        help='Specify syntax file (JSON) - required for execution')
    parser.add_argument('--convert-to', type=str, metavar='SYNTAX',
                        help='Convert files to target syntax and save in <SYNTAX>/ directory')
    parser.add_argument('--input', type=str, metavar='FILE',
                        help='Load environment variables from JSON file')
    parser.add_argument('--output', type=str, metavar='FILE',
                        help='Save environment variables to JSON file after execution')
    parser.add_argument('--make-examples', action='store_true',
                        help='Generate sample code files (.yui)')
    parser.add_argument('--show-examples', action='store_true',
                        help='Print sample code to stdout')
    parser.add_argument('--test-examples', action='store_true',
                        help='Test all examples with YuiRuntime')
    parser.add_argument('--pass@1', dest='pass_at_1', action='store_true',
                        help='Execute multiple scripts and show pass rate')
    parser.add_argument('--example', type=str, metavar='NAME',
                        help='Target specific example (use with --make-examples or --show-examples)')
    parser.add_argument('--list-examples', action='store_true',
                        help='List available examples')
    parser.add_argument('--list-syntax', action='store_true',
                        help='List available syntax files with examples')
    parser.add_argument('--find-syntax', action='store_true',
                        help='Find syntax files that can parse all given files')
    parser.add_argument('--syntax-dir', type=str, metavar='DIR',
                        help='Directory to search for syntax JSON files')
    parser.add_argument('--bnf', action='store_true',
                        help='Display BNF grammar for the specified syntax (requires --syntax)')
    parser.add_argument('--lang', type=str, metavar='LANG', default='ja',
                        help='Error message language (default: ja)')
    parser.add_argument('file', nargs='*', help='Yui file(s) to execute')

    args = parser.parse_args(argv)

    _message.set_language(args.lang)

    try:
        # List examples
        if args.list_examples:
            list_examples()
            return

        # List syntax
        if args.list_syntax:
            list_syntax(args.syntax_dir)
            return

        # Find syntax
        if args.find_syntax:
            if not args.file:
                print("Error: --find-syntax requires at least one file", file=sys.stderr)
                sys.exit(1)
            find_syntax(args.file, args.syntax_dir)
            return

        # Pass@1 mode
        if args.pass_at_1:
            if not args.syntax:
                print("Error: --syntax option is required", file=sys.stderr)
                print("Example: yui --syntax yui --pass@1 file1.yui file2.yui", file=sys.stderr)
                print("\nAvailable syntax files:", file=sys.stderr)
                print("  - yui  (Yui style)", file=sys.stderr)
                print("  - pylike   (Python style)", file=sys.stderr)
                print("  - emoji.json       (Emoji style)", file=sys.stderr)
                sys.exit(1)
            if not args.file:
                print("Error: --pass@1 requires at least one file", file=sys.stderr)
                sys.exit(1)
            pass_at_1_mode(args.file, args.syntax)
            return

        # Test examples mode
        if args.test_examples:
            if not args.syntax:
                print("Error: --syntax option is required", file=sys.stderr)
                print("Example: yui --syntax yui --test-examples", file=sys.stderr)
                print("\nAvailable syntax files:", file=sys.stderr)
                print("  - yui  (Yui style)", file=sys.stderr)
                print("  - pylike   (Python style)", file=sys.stderr)
                print("  - emoji.json       (Emoji style)", file=sys.stderr)
                sys.exit(1)
            test_examples(args.syntax)
            return

        # Show examples mode (stdout)
        if args.show_examples:
            if not args.syntax:
                print("Error: --syntax option is required", file=sys.stderr)
                print("Example: yui --syntax yui --show-examples", file=sys.stderr)
                sys.exit(1)
            show_examples(args.example, args.syntax)
            return

        # Example generation mode
        if args.make_examples:
            if not args.syntax:
                print("Error: --syntax option is required", file=sys.stderr)
                print("Example: yui --syntax yui --make-examples", file=sys.stderr)
                print("\nAvailable syntax files:", file=sys.stderr)
                print("  - yui  (Yui style)", file=sys.stderr)
                print("  - pylike   (Python style)", file=sys.stderr)
                print("  - emoji.json       (Emoji style)", file=sys.stderr)
                sys.exit(1)
            make_examples(args.example, args.syntax)
            return

        # Required syntax file check (execution, interactive, conversion modes)
        if not args.syntax:
            print("Error: --syntax option is required", file=sys.stderr)
            print("\nUsage:", file=sys.stderr)
            print("  yui --syntax <syntax-file> [options] [file]", file=sys.stderr)
            print("\nExamples:", file=sys.stderr)
            print("  yui --syntax yui file.yui", file=sys.stderr)
            print("  yui --syntax pylike -i", file=sys.stderr)
            print("\nAvailable syntax files:", file=sys.stderr)
            print("  - yui  (Yui style)", file=sys.stderr)
            print("  - pylike   (Python style)", file=sys.stderr)
            print("  - emoji.json       (Emoji style)", file=sys.stderr)
            sys.exit(1)

        syntax = args.syntax

        # --syntax-dir が指定されていれば、syntax 名をそのディレクトリ内で解決する
        if args.syntax_dir and not os.path.isfile(syntax):
            candidate = syntax if syntax.endswith('.json') else f"{syntax}.json"
            full_path = os.path.join(args.syntax_dir, candidate)
            if os.path.isfile(full_path):
                syntax = full_path

        # BNF display
        if args.bnf:
            terminals = load_syntax(syntax)
            print(generate_bnf(terminals))
            return

        # Initialize environment
        env = {}
        if args.input:
            env = load_env_from_json(args.input)
            print(f"Environment loaded: {args.input}")

        # Syntax conversion mode
        if args.convert_to:
            if not args.file:
                print("Error: --convert-to requires at least one input file", file=sys.stderr)
                sys.exit(1)
            for filename in args.file:
                convert_and_save(filename, syntax, args.convert_to)
            return

        # Execute file(s)
        if args.file:
            # If multiple files are provided, execute them sequentially
            if isinstance(args.file, list):
                for filename in args.file:
                    env = run_file(filename, env, syntax)
            else:
                env = run_file(args.file, env, syntax)

            # Save environment
            if args.output:
                save_env_to_json(env, args.output)
                print(f"Environment saved: {args.output}")

            return

        # Interactive mode
        if args.interactive or not args.file:
            interactive_mode(env, syntax)
            return

    except YuiError as e:
        print(f"\nError occurred:", file=sys.stderr)
        print(e.formatted_message("| "), file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExiting")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_file(filename: str, env: Dict[str, Any], syntax: str = 'yui') -> Dict[str, Any]:
    """Execute a file"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    runtime = YuiRuntime()
    for key, value in env.items():
        runtime.setenv(key, value)

    runtime.exec(code, syntax, eval_mode=False)

    # Return environment (from last scope)
    result_env = {}
    if runtime.environments:
        result_env = runtime.environments[-1].copy()

    return result_env


def interactive_mode(env: Dict[str, Any], syntax: str = 'yui'):
    """Interactive mode"""
    print(f"Yui v{__version__} - Interactive Mode")
    print(f"Syntax: {syntax}")
    print("Type 'quit' or 'exit' to exit\n")

    # Setup readline history file
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
                    # Display environment
                    if runtime.environments and len(runtime.environments[-1]) > 0:
                        print(json.dumps(runtime.environments[-1], indent=2, ensure_ascii=False))
                    continue

                # Parse and execute
                runtime.exec(code, syntax)

            except YuiError as e:
                print(runtime.format_error(e, "| "))
            except KeyboardInterrupt:
                print("\nExiting")
                break
            except EOFError:
                print("\nExiting")
                break
    finally:
        if READLINE_AVAILABLE:
            try:
                readline.write_history_file(history_file)
            except Exception:
                pass


def convert_and_save(input_file: str, source_syntax: str, target_syntax: str):
    """Convert a file to target syntax and save in <target_syntax>_examples/ directory"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert first, then save
    if input_file.endswith('.md'):
        converted = convert_markdown_to_string(content, source_syntax, target_syntax)
    else:
        parser = YuiParser(source_syntax)
        ast = parser.parse(content)
        visitor = CodingVisitor(target_syntax)
        converted = visitor.emit(ast)

    # Derive short name for directory (strip path and .json if given)
    target_name = os.path.basename(target_syntax)
    if target_name.endswith('.json'):
        target_name = target_name[:-len('.json')]

    out_dir = target_name
    os.makedirs(out_dir, exist_ok=True)

    out_filename = os.path.join(out_dir, os.path.basename(input_file))
    with open(out_filename, 'w', encoding='utf-8') as f:
        f.write(converted)
    print(f"Converted: {input_file} -> {out_filename}")


def convert_markdown_to_string(content: str, source_syntax: str, target_syntax: str) -> str:
    """Convert code blocks in Markdown content and return as string"""
    lines = content.split('\n')
    out_lines = []
    in_code_block = False
    current_block = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```yui") and not in_code_block:
            in_code_block = True
            current_block = []
            out_lines.append(line)
            continue

        if stripped.startswith("```") and in_code_block:
            code = '\n'.join(current_block)
            if code.strip():
                try:
                    parser = YuiParser(source_syntax)
                    ast = parser.parse(code)
                    visitor = CodingVisitor(target_syntax)
                    out_lines.append(visitor.emit(ast))
                except Exception as e:
                    out_lines.append(f"# Conversion error: {e}")
                    out_lines.append(code)
            out_lines.append(line)
            in_code_block = False
            current_block = []
            continue

        if in_code_block:
            current_block.append(line)
        else:
            out_lines.append(line)

    return '\n'.join(out_lines)


def load_env_from_json(filename: str) -> Dict[str, Any]:
    """Load environment from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_env_to_json(env: Dict[str, Any], filename: str):
    """Save environment to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(env, f, indent=2, ensure_ascii=False)


def list_examples():
    """List available examples"""
    examples = yuiexample.get_all_examples()
    print("\nAvailable examples:")
    print(f"{'Name':<30} {'Kind':<8} Description")
    print("-" * 70)
    for ex in examples:
        print(f"{ex.name:<30} {ex.kind:<8} {ex.description}")


def list_syntax(syntax_dir: str = None):
    """List available syntax files with an increment example for each"""
    example_node = IncrementNode(NameNode("x"))

    print("\nAvailable syntax files:")
    print(f"{'Name':<12}  {'File':<20}  {'x += 1 equivalent'}")
    print("-" * 60)

    from .yuisyntax import _DEFAULT_SYNTAX_DIR
    d = syntax_dir or _DEFAULT_SYNTAX_DIR
    for name in list_syntax_names(syntax_dir):
        filename = f"{name}.json"
        try:
            terminals = load_syntax(os.path.join(d, filename))
            if not terminals.get('if-begin', ''):
                continue
            visitor = CodingVisitor(terminals)
            code = visitor.emit(example_node).strip()
            if not code:
                code = "(no increment syntax defined)"
        except Exception as e:
            code = f"(error: {e})"
        print(f"{name:<12}  {filename:<20}  {code}")


def find_syntax(files: list, syntax_dir: str = None):
    """Find syntax files that can successfully parse all given files"""
    sources = {}
    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                sources[filename] = f.read()
        except FileNotFoundError:
            print(f"Error: File not found - {filename}", file=sys.stderr)
            sys.exit(1)

    results = find_matching_syntaxes(sources, syntax_dir)
    print(f"\nTrying {len(results)} syntax file(s) against {len(files)} file(s)...\n")

    matched = [name for name, ok, _ in results if ok]
    for name, ok, status in results:
        print(f"  {'✓' if ok else '✗'}  {name:<12}  {status}")

    print()
    if matched:
        print(f"Matching syntax: {', '.join(matched)}")
    else:
        print("No syntax matched all files.")


def show_examples(example_name: str = None, syntax: str = 'yui'):
    """サンプルコードを標準出力に表示する。

    Args:
        example_name: 特定のサンプル名（None の場合は全サンプル）
        syntax: 使用する構文ファイル
    """
    examples = yuiexample.get_samples()

    if example_name:
        examples = [ex for ex in examples if ex.name == example_name]
        if not examples:
            print(f"Error: Example '{example_name}' not found", file=sys.stderr)
            sys.exit(1)

    for i, example in enumerate(examples):
        if i > 0:
            print()
        print(f"# {example.name}: {example.description}")
        print(example.generate(syntax, include_asserts=False))


def make_examples(example_name: str = None, syntax: str = 'yui'):
    """
    Generate sample code files

    Args:
        example_name: Specific example name (all examples if None)
        syntax: Syntax file to use
    """
    examples = yuiexample.get_samples()

    # Derive syntax short name for directory (strip path and .json if given)
    syntax_name = os.path.basename(syntax)
    if syntax_name.endswith('.json'):
        syntax_name = syntax_name[:-len('.json')]

    examples_dir = f"{syntax_name}_examples"
    os.makedirs(examples_dir, exist_ok=True)

    # Generate specific example only
    if example_name:
        example = next((ex for ex in examples if ex.name == example_name), None)
        if not example:
            print(f"Error: Example '{example_name}' not found", file=sys.stderr)
            print("\nAvailable examples:")
            for ex in examples:
                print(f"  - {ex.name}")
            sys.exit(1)

        code = example.generate(syntax)
        filename = os.path.join(examples_dir, f"{example.name}.yui")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Generated: {filename}")
        return

    # Generate all examples
    for example in examples:
        code = example.generate(syntax)
        filename = os.path.join(examples_dir, f"{example.name}.yui")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Generated: {filename}")

    print(f"\nAll examples generated in {examples_dir}/ directory")


def test_examples(syntax: str = 'yui'):
    """
    Test all examples with YuiRuntime

    Args:
        syntax: Syntax file to use for parsing
    """
    examples = yuiexample.get_test_examples()

    print(f"\nTesting examples with syntax: {syntax}")
    print("=" * 60)

    passed = 0
    failed = 0

    for example in examples:
        try:
            # Generate code
            code = example.generate(syntax)

            runtime = YuiRuntime()
            runtime.exec(code, syntax)

            print(f"✓ {example.name:<20} PASSED")
            passed += 1

        except YuiError as e:
            print(f"✗ {example.name:<20} FAILED")
            print(runtime.format_error(e, "    | "))
            failed += 1

        except Exception as e:
            print(f"✗ {example.name:<20} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


def pass_at_1_mode(files: list, syntax: str = 'yui'):
    """
    Execute multiple script files and calculate pass rate

    - Files ending with _doctest.yui are ignored as standalone targets
    - For a.yui, if a_doctest.yui exists, both are concatenated and executed together

    Args:
        files: List of .yui files to execute
        syntax: Syntax file to use for parsing
    """
    # Filter .yui files, excluding _doctest.yui
    yui_files = [f for f in files if f.endswith('.yui') and not f.endswith('_doctest.yui')]

    if not yui_files:
        print("Error: No .yui files specified", file=sys.stderr)
        sys.exit(1)

    results = []

    for filename in yui_files:
        try:
            # Read main file
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()

            # Check for corresponding _doctest.yui
            base = filename[:-len('.yui')]
            doctest_file = base + '_doctest.yui'
            if os.path.exists(doctest_file):
                with open(doctest_file, 'r', encoding='utf-8') as f:
                    code = code + '\n' + f.read()
                label = f"{filename} + {os.path.basename(doctest_file)}"
            else:
                label = filename

            runtime = YuiRuntime()
            runtime.exec(code, syntax)

            # Success
            results.append(1)
            print(f"✓ {label}")

        except FileNotFoundError:
            # File not found
            results.append(0)
            print(f"✗ {filename} (File not found)")

        except YuiError as e:
            # Yui syntax or runtime error
            results.append(0)
            print(f"✗ {label}")
            print(runtime.format_error(e, "  | "))

        except Exception as e:
            # Other errors
            results.append(0)
            print(f"✗ {label}")
            print(f"  | Error: {e}")

    # Calculate pass rate
    total = len(results)
    passed = sum(results)
    pass_rate = passed / total if total > 0 else 0

    # Display results
    print(f"\n{'='*50}")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"pass@1: {pass_rate:.2%} ({passed}/{total})")
    print(f"{'='*50}")

    # Exit with error code if any failed
    if total - passed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
