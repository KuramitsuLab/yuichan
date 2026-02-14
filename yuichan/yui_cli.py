#!/usr/bin/env python
"""
ゆい言語のCLIインターフェース
使用方法: python -m yuip.yui_cli [ファイル名]
"""

import sys
from .yui import YuiRuntime, YuiError
import csv
import json
import traceback
import os

# readline を使用して履歴機能を有効化
try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

# バージョン情報をインポート
try:
    from . import __version__
except ImportError:
    __version__ = "0.3.4"

def main():
    env = {}
    try:
        # バージョン表示の処理
        if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v', '-V']:
            print(f"Yui (ゆい) version {__version__}")
            sys.exit(0)

        # ヘルプ表示の処理
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
            print(f"Yui (ゆい) version {__version__}")
            print("\n使用方法:")
            print("  python -m yuip.yui_cli [ファイル名]")
            print("  yuip [ファイル名]                  # インストール後")
            print("\nオプション:")
            print("  --version, -v, -V    バージョン情報を表示")
            print("  --help, -h           このヘルプメッセージを表示")
            print("  --pass@1             複数のスクリプトを実行して成功率を表示")
            print("\nファイル形式:")
            print("  .yui    Yuiプログラムファイル")
            print("  .csv       CSVデータファイル（環境変数として読み込み）")
            print("  .json      JSONデータファイル（環境変数として読み込み）")
            print("  .md        Yui言語コードスニペットを含むマークダウンファイル")
            print("\n例:")
            print("  python -m yuip.yui_cli examples/01basic.yui")
            print("  python -m yuip.yui_cli data.csv program.yui")
            print("  python -m yuip.yui_cli                    # インタラクティブモード")
            print("  yuip --pass@1 test1.yui test2.yui test3.yui")
            sys.exit(0)

        # --pass@1 モードの処理
        if len(sys.argv) > 1 and sys.argv[1] == '--pass@1':
            pass_at_1_mode(sys.argv[2:])
            sys.exit(0)

        run_interactive = True
        for file in sys.argv[1:]:
            if file.endswith('.json'):
                try:
                    env.update(load_env_from_json(file))
                except Exception as e:
                    print(f"エラー ({file}): {e}", file=sys.stderr)
                    sys.exit(1)
            elif file.endswith('.csv'):
                try:
                    data = read_csv_as_dict_of_lists(file)
                    env.update(data)
                except Exception as e:
                    print(f"エラー ({file}): {e}", file=sys.stderr)
                    sys.exit(1)
            elif file.endswith('.md'):
                try:
                    snippets = read_snippets_from_markdown(file)
                    for line_number_offset, snippet in snippets:
                        try :
                            runtime = YuiRuntime()
                            runtime.exec(snippet, {}, eval_mode=False)
                        except YuiError as e:
                            line_number = e.lineno+ line_number_offset
                            print(f"{snippet}\nエラー in {file} (行 {line_number})\n{e.formatted_message(lineoffset=line_number_offset)}", file=sys.stderr)
                    run_interactive = False
                except Exception as e:
                    print(f"エラー ({file}): {e}", file=sys.stderr)
                    traceback.print_exc()
                    sys.exit(1)
            elif file.endswith('.yui'):
                try:
                    env = run_file(file, env)
                    run_interactive = False
                except YuiError as e:
                    # Yuiの構文エラーや実行時エラー
                    print(f"\nエラーが発生しました: {file}", file=sys.stderr)
                    #print(f"|  行 {e.lineno}, 列 {e.offset}: {e.text}", file=sys.stderr)
                    print(e.formatted_message("| "), file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"\nエラーが発生しました: {file}", file=sys.stderr)
                    traceback.print_exc()
                    sys.exit(1)

        if run_interactive:
            env = interactive_mode(env)
        if len(env) > 0:
            runtime = YuiRuntime()
            print(runtime.stringfy_as_json(env))
    except KeyboardInterrupt:
        print("\n終了します", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

def pass_at_1_mode(files):
    """
    複数のスクリプトファイルを実行して成功率を計算

    Args:
        files: 実行する.yuiファイルのリスト
    """
    if not files:
        print("エラー: --pass@1 オプションには少なくとも1つのファイルが必要です", file=sys.stderr)
        sys.exit(1)

    # .yuiファイルのみをフィルタ
    yui_files = [f for f in files if f.endswith('.yui')]

    if not yui_files:
        print("エラー: .yuiファイルが指定されていません", file=sys.stderr)
        sys.exit(1)

    results = []

    for filename in yui_files:
        try:
            # ファイルを実行
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()

            runtime = YuiRuntime()
            _ = runtime.exec(code, {}, eval_mode=False)

            # 成功
            results.append(1)
            print(f"✓ {filename}")

        except FileNotFoundError:
            # ファイルが存在しない
            results.append(0)
            print(f"✗ {filename} (ファイルが見つかりません)")

        except YuiError as e:
            # Yuiの構文エラーや実行時エラー
            results.append(0)
            print(f"✗ {filename}")
            print(e.formatted_message("  | "))

        except Exception as e:
            # その他のエラー
            results.append(0)
            print(f"✗ {filename}")
            print(f"  | エラー: {e}")

    # 成功率を計算
    total = len(results)
    passed = sum(results)
    pass_rate = passed / total if total > 0 else 0

    # 結果を表示
    print(f"\n{'='*50}")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"pass@1: {pass_rate:.2%} ({passed}/{total})")
    print(f"{'='*50}")

def run_file(filename, env):
    """ファイルを実行"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()
    runtime = YuiRuntime()
    # ファイル名情報を持ったままexecする
    env = runtime.exec(code, env, eval_mode=False)
    return env

def interactive_mode(env):
    """インタラクティブモード"""
    print(f"Yui (ゆい) version {__version__}")
    print("終了するには 'quit' または 'exit' を入力してください")

    # readline の履歴ファイルを設定
    history_file = os.path.expanduser("~/.yuip_history")
    if READLINE_AVAILABLE:
        try:
            # 履歴ファイルが存在すれば読み込む
            if os.path.exists(history_file):
                readline.read_history_file(history_file)
            # 履歴の最大サイズを設定（デフォルトは1000行）
            readline.set_history_length(1000)
        except Exception:
            # 履歴ファイルの読み込みに失敗しても続行
            pass

    try:
        while True:
            try:
                code = input(">>> ")
                if code.lower() in ['quit', 'exit']:
                    break

                code = code.strip()
                runtime = YuiRuntime()
                runtime.interactive_mode = True
                if code == "":
                    if len(env) > 0:
                        print(runtime.stringfy_as_json(env))
                else:
                    env = runtime.exec(code, env, eval_mode=False)
            except YuiError as e:
                print(e.formatted_message("| "))
            except KeyboardInterrupt:
                print("\n終了します")
                break
            except EOFError:
                print("\n終了します")
                break
    finally:
        # 終了時に履歴を保存
        if READLINE_AVAILABLE:
            try:
                readline.write_history_file(history_file)
            except Exception:
                # 履歴ファイルの保存に失敗しても無視
                pass

    return env

def load_env_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 文字列で整数配列に変換できるものは変換
    def try_convert(val):
        if isinstance(val, str):
            arr = [ord(c) for c in val]
            return arr
        if isinstance(val, bool):
            return int(val)
        elif isinstance(val, dict):
            return {k: try_convert(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [try_convert(x) for x in val]
        else:
            return val
    return {k: try_convert(v) for k, v in data.items()}

def read_snippets_from_markdown(filename: str)-> list[tuple[int, str]]:
    """
    マークダウンファイルからYui言語のコードスニペットを抽出
    ```yui で始まるブロックのみ抽出（```yui-snippet は無視）
    """
    snippets = []
    with open(filename, 'r', encoding='utf-8') as f:
        in_code_block = False
        current_snippet = []
        line_number = 0
        current_line_number = 0
        for line in f:
            line_number += 1
            stripped = line.strip()
            # ```yui で始まり、```yui-snippet ではないブロックのみ
            if stripped.startswith("```yui") and not stripped.startswith("```yui-") and not in_code_block:
                in_code_block = True
                current_snippet = []
                current_line_number = line_number
            elif stripped.startswith("```") and in_code_block:
                in_code_block = False
                snippets.append((current_line_number, ''.join(current_snippet)))
            elif in_code_block:
                current_snippet.append(line)
    return snippets
    

def read_csv_as_dict_of_lists(filename):
    """
    CSVファイルを読み込み、一行目をキー、各列の値をリストとして辞書で返す
    """
    result = {}
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for key in reader.fieldnames:
            result[key] = []
        for row in reader:
            for key in reader.fieldnames:
                try:
                    value = int(row[key])
                except ValueError:
                    value = str(row[key])
                result[key].append(value)
    return result

try:
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def yui(_line, cell):
        """
        Jupyter用セルマジック: %%yui
        セル内のゆい言語コードを実行し、環境を表示
        """
        try:
            runtime = YuiRuntime()
            env = runtime.exec(cell, {}, eval_mode=False)
            print(runtime.stringfy_as_json(env))
        except Exception as e:
            print(f"エラー: {e}")
except NameError:
    pass
except ImportError:
    pass

if __name__ == "__main__":
    main()