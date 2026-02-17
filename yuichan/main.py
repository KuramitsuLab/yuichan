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
from .yuiparser import YuiParser, CodingVisitor
from .yuiast import YuiRuntime, YuiError
from . import yuiexample


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
  yui file.yui                              # Execute a file
  yui -i                                    # Interactive mode
  yui --input input.json file.yui           # Load environment and execute
  yui file.yui --output output.json         # Save environment after execution
  yui --syntax pylike file.yui     # Execute with custom syntax
  yui --syntax yui file.yui --syntax-to pylike  # Convert syntax
  yui --syntax yui file.md --syntax-to pylike   # Convert Markdown
  yui --list-examples                       # List available examples
  yui --make-examples                       # Generate all examples (Yui + Python style)
  yui --make-examples --example loop        # Generate specific example only
  yui --make-examples --syntax yui  # Generate with Yui syntax only
"""
    )

    parser.add_argument('-V', '--version', action='version',
                        version=f'Yui {__version__}')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Start in interactive mode')
    parser.add_argument('--syntax', type=str, metavar='FILE',
                        help='Specify syntax file (JSON) - required for execution')
    parser.add_argument('--syntax-to', type=str, metavar='FILE',
                        help='Target syntax file for conversion (use with --syntax)')
    parser.add_argument('--input', type=str, metavar='FILE',
                        help='Load environment variables from JSON file')
    parser.add_argument('--output', type=str, metavar='FILE',
                        help='Save environment variables to JSON file after execution')
    parser.add_argument('--make-examples', action='store_true',
                        help='Generate sample code files (.yui)')
    parser.add_argument('--test-examples', action='store_true',
                        help='Test all examples with YuiRuntime')
    parser.add_argument('--pass@1', dest='pass_at_1', action='store_true',
                        help='Execute multiple scripts and show pass rate')
    parser.add_argument('--example', type=str, metavar='NAME',
                        help='Generate specific example only (use with --make-examples)')
    parser.add_argument('--list-examples', action='store_true',
                        help='List available examples')
    parser.add_argument('file', nargs='*', help='Yui file(s) to execute')

    args = parser.parse_args(argv)

    try:
        # List examples
        if args.list_examples:
            list_examples()
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

        # Initialize environment
        env = {}
        if args.input:
            env = load_env_from_json(args.input)
            print(f"Environment loaded: {args.input}")

        # Syntax conversion mode
        if args.syntax_to:
            if not args.file:
                print("Error: --syntax-to requires an input file", file=sys.stderr)
                sys.exit(1)
            convert_syntax(args.file, syntax, args.syntax_to)
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
        print(f"\n{e}", file=sys.stderr)
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

    # Generate AST with parser
    parser = YuiParser(syntax)
    ast = parser.parse(code)

    # Execute with runtime
    runtime = YuiRuntime()
    for key, value in env.items():
        runtime.setenv(key, value)

    ast.evaluate(runtime)

    # Return environment (from last scope)
    result_env = {}
    if runtime.enviroments:
        result_env = runtime.enviroments[-1].copy()

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
                    if runtime.enviroments and len(runtime.enviroments[-1]) > 0:
                        print(json.dumps(runtime.enviroments[-1], indent=2, ensure_ascii=False))
                    continue

                # Parse and execute
                parser = YuiParser(syntax)
                ast = parser.parse(code)
                ast.evaluate(runtime)

            except YuiError as e:
                print(f"Error: {e}")
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


def convert_syntax(input_file: str, source_syntax: str, target_syntax: str):
    """Convert syntax"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Markdown file conversion
    if input_file.endswith('.md'):
        convert_markdown(content, source_syntax, target_syntax)
    else:
        # Regular file conversion
        parser = YuiParser(source_syntax)
        ast = parser.parse(content)

        visitor = CodingVisitor(target_syntax)
        converted = visitor.emit(ast)

        print(converted)


def convert_markdown(content: str, source_syntax: str, target_syntax: str):
    """Convert code blocks in Markdown files"""
    lines = content.split('\n')
    in_code_block = False
    current_block = []

    for line in lines:
        stripped = line.strip()

        # Detect blocks starting with ```yui
        if stripped.startswith("```yui") and not in_code_block:
            in_code_block = True
            current_block = []
            print(line)  # Output code block start as-is
            continue

        # End of code block
        if stripped.startswith("```") and in_code_block:
            # Convert code block
            code = '\n'.join(current_block)
            if code.strip():
                try:
                    parser = YuiParser(source_syntax)
                    ast = parser.parse(code)

                    visitor = CodingVisitor(target_syntax)
                    converted = visitor.emit(ast)

                    print(converted)
                except Exception as e:
                    print(f"# Conversion error: {e}")
                    print(code)

            print(line)  # Output code block end as-is
            in_code_block = False
            current_block = []
            continue

        # Inside code block
        if in_code_block:
            current_block.append(line)
        else:
            # Outside code block - output as-is
            print(line)


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
    print(f"{'Name':<20} Description")
    print("-" * 60)
    for ex in examples:
        print(f"{ex.name:<20} {ex.description}")


def make_examples(example_name: str = None, syntax: str = 'yui'):
    """
    Generate sample code files

    Args:
        example_name: Specific example name (all examples if None)
        syntax: Syntax file to use
    """
    examples = yuiexample.get_all_examples()

    # Create examples directory if it doesn't exist
    examples_dir = 'examples'
    if not os.path.exists(examples_dir):
        os.makedirs(examples_dir)
        print(f"Created directory: {examples_dir}/")

    # Determine file extension from syntax
    syntax_basename = os.path.basename(syntax)
    if 'py' in syntax_basename:
        ext = 'py'
    elif 'emoji' in syntax_basename:
        ext = 'yui'  # Use .yui for emoji syntax
    else:
        ext = 'yui'

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
        filename = os.path.join(examples_dir, f"{example.name}.{ext}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Generated: {filename}")
        return

    # Generate all examples
    for example in examples:
        code = example.generate(syntax)
        filename = os.path.join(examples_dir, f"{example.name}.{ext}")
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
    examples = yuiexample.get_all_examples()

    print(f"\nTesting examples with syntax: {syntax}")
    print("=" * 60)

    passed = 0
    failed = 0

    for example in examples:
        try:
            # Generate code
            code = example.generate(syntax)

            # Parse and execute
            parser = YuiParser(syntax)
            ast = parser.parse(code)

            runtime = YuiRuntime()
            ast.evaluate(runtime)

            print(f"✓ {example.name:<20} PASSED")
            passed += 1

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

    Args:
        files: List of .yui files to execute
        syntax: Syntax file to use for parsing
    """
    # Filter .yui files only
    yui_files = [f for f in files if f.endswith('.yui')]

    if not yui_files:
        print("Error: No .yui files specified", file=sys.stderr)
        sys.exit(1)

    results = []

    for filename in yui_files:
        try:
            # Read and execute file
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()

            # Parse and execute
            parser = YuiParser(syntax)
            ast = parser.parse(code)

            runtime = YuiRuntime()
            ast.evaluate(runtime)

            # Success
            results.append(1)
            print(f"✓ {filename}")

        except FileNotFoundError:
            # File not found
            results.append(0)
            print(f"✗ {filename} (File not found)")

        except YuiError as e:
            # Yui syntax or runtime error
            results.append(0)
            print(f"✗ {filename}")
            print(f"  | {e}")

        except Exception as e:
            # Other errors
            results.append(0)
            print(f"✗ {filename}")
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
