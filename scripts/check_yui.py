#!/usr/bin/env python3
"""
yui_examples/*.yui のカバレッジをチェックするスクリプト。

- yui 構文要素（AST ノード / 演算子 / 暗黙機能）
- 標準ライブラリ関数

のどれが実例で使われているか・使われていないかを報告する。

使い方:
    python3 scripts/check_yui.py                       # yui_examples/ 全体
    python3 scripts/check_yui.py --dir other_examples  # 別ディレクトリ
    python3 scripts/check_yui.py a.yui b.yui           # 個別ファイル指定
    python3 scripts/check_yui.py 'yui_examples/*.yui'  # グロブ（クォート推奨）
"""

import argparse
import csv
import glob
import os
import sys
from collections import Counter, defaultdict

# プロジェクトルートを import path に追加
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from yuichan.yuiparser import Source
from yuichan.yuiast import (
    ConstNode, NumberNode, StringNode, NameNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode, GetIndexNode, BinaryNode, FuncAppNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode, PassNode,
    FuncDefNode, ReturnNode, ImportNode, PrintExpressionNode, AssertNode,
)
from yuichan.yuistdlib import standard_lib


# ─────────────────────────────────────────────
# 構文要素カテゴリ
# ─────────────────────────────────────────────

SYNTAX_FEATURES = [
    # リテラル
    'lit:null', 'lit:boolean', 'lit:int', 'lit:float',
    'lit:string', 'lit:string-interp',
    'lit:array', 'lit:object',
    # 式
    'expr:unary-minus', 'expr:length', 'expr:index-array', 'expr:index-object',
    'expr:funcapp',
    # 文
    'stmt:assignment', 'stmt:assignment-to-index',
    'stmt:increment', 'stmt:decrement', 'stmt:append',
    'stmt:if', 'stmt:if-else', 'stmt:if-elif-nested',
    'stmt:repeat', 'stmt:break',
    'stmt:funcdef', 'stmt:funcdef-noarg',
    'stmt:return', 'stmt:return-implicit',
    'stmt:assert', 'stmt:import', 'stmt:pass', 'stmt:print-expression',
    # 比較演算子（IfNode の operator）
    'cmp:==', 'cmp:!=', 'cmp:<', 'cmp:<=', 'cmp:>', 'cmp:>=',
    'cmp:in', 'cmp:notin',
]


def collect_features(node, features):
    """AST を走査して構文要素の出現回数を features (Counter) に記録する。"""
    if node is None:
        return

    t = type(node)

    if t is ConstNode:
        if node.native_value is None:
            features['lit:null'] += 1
        else:
            features['lit:boolean'] += 1

    elif t is NumberNode:
        v = node.native_value
        if isinstance(v, bool):
            features['lit:boolean'] += 1
        elif isinstance(v, float):
            features['lit:float'] += 1
        else:
            features['lit:int'] += 1

    elif t is StringNode:
        if isinstance(node.contents, list):
            features['lit:string-interp'] += 1
            for part in node.contents:
                if not isinstance(part, str):
                    collect_features(part, features)
        else:
            features['lit:string'] += 1

    elif t is ArrayNode:
        features['lit:array'] += 1
        for e in node.elements:
            collect_features(e, features)

    elif t is ObjectNode:
        features['lit:object'] += 1
        for e in node.elements:
            collect_features(e, features)

    elif t is MinusNode:
        features['expr:unary-minus'] += 1
        collect_features(node.element, features)

    elif t is ArrayLenNode:
        features['expr:length'] += 1
        collect_features(node.element, features)

    elif t is GetIndexNode:
        # 添字が文字列なら object、それ以外は array
        idx = node.index_node
        if isinstance(idx, StringNode):
            features['expr:index-object'] += 1
        else:
            features['expr:index-array'] += 1
        collect_features(node.collection, features)
        collect_features(idx, features)

    elif t is BinaryNode:
        collect_features(node.left_node, features)
        collect_features(node.right_node, features)

    elif t is FuncAppNode:
        features['expr:funcapp'] += 1
        collect_features(node.name_node, features)
        for a in node.arguments:
            collect_features(a, features)

    elif t is AssignmentNode:
        if isinstance(node.variable, GetIndexNode):
            features['stmt:assignment-to-index'] += 1
        else:
            features['stmt:assignment'] += 1
        collect_features(node.variable, features)
        collect_features(node.expression, features)

    elif t is IncrementNode:
        features['stmt:increment'] += 1
        collect_features(node.variable, features)

    elif t is DecrementNode:
        features['stmt:decrement'] += 1
        collect_features(node.variable, features)

    elif t is AppendNode:
        features['stmt:append'] += 1
        collect_features(node.variable, features)
        collect_features(node.expression, features)

    elif t is IfNode:
        features['stmt:if'] += 1
        op_sym = getattr(node.operator, 'symbol', str(node.operator))
        features[f'cmp:{op_sym}'] += 1
        # else_block が PassNode のときは else 節なし
        has_else = isinstance(node.else_block, BlockNode)
        if has_else:
            features['stmt:if-else'] += 1
            nested = any(isinstance(s, IfNode) for s in node.else_block.statements)
            if nested:
                features['stmt:if-elif-nested'] += 1
        collect_features(node.left, features)
        collect_features(node.right, features)
        collect_features(node.then_block, features)
        if has_else:
            collect_features(node.else_block, features)

    elif t is RepeatNode:
        features['stmt:repeat'] += 1
        collect_features(node.count_node, features)
        collect_features(node.block_node, features)

    elif t is BreakNode:
        features['stmt:break'] += 1

    elif t is PassNode:
        # PassNode with a comment は単なる行コメント。comment なしは `何もしない` 文
        if not getattr(node, 'comment', None):
            features['stmt:pass'] += 1

    elif t is FuncDefNode:
        features['stmt:funcdef'] += 1
        if not node.parameters:
            features['stmt:funcdef-noarg'] += 1
        # 本体に ReturnNode がなければ暗黙戻り値
        if not _has_return(node.body):
            features['stmt:return-implicit'] += 1
        for p in node.parameters:
            collect_features(p, features)
        collect_features(node.body, features)

    elif t is ReturnNode:
        features['stmt:return'] += 1
        collect_features(node.expression, features)

    elif t is AssertNode:
        features['stmt:assert'] += 1
        collect_features(node.test, features)
        collect_features(node.reference, features)

    elif t is ImportNode:
        features['stmt:import'] += 1

    elif t is PrintExpressionNode:
        features['stmt:print-expression'] += 1
        collect_features(node.expression, features)

    elif t is BlockNode:
        for s in node.statements:
            collect_features(s, features)


def _has_return(block):
    """BlockNode（またはそれに類するもの）内に ReturnNode が含まれるか。"""
    if block is None:
        return False
    if isinstance(block, ReturnNode):
        return True
    if isinstance(block, BlockNode):
        return any(_has_return(s) for s in block.statements)
    if isinstance(block, IfNode):
        return _has_return(block.then_block) or (
            isinstance(block.else_block, BlockNode)
            and _has_return(block.else_block)
        )
    if isinstance(block, RepeatNode):
        return _has_return(block.block_node)
    return False


# ─────────────────────────────────────────────
# 標準ライブラリ関数の収集
# ─────────────────────────────────────────────

def collect_funcapps(node, names):
    """FuncAppNode の呼び出し先名を names に集める。"""
    if node is None:
        return
    if isinstance(node, FuncAppNode):
        if isinstance(node.name_node, NameNode):
            names[node.name_node.name] += 1
        for a in node.arguments:
            collect_funcapps(a, names)
    elif isinstance(node, BlockNode):
        for s in node.statements:
            collect_funcapps(s, names)
    elif isinstance(node, IfNode):
        collect_funcapps(node.left, names)
        collect_funcapps(node.right, names)
        collect_funcapps(node.then_block, names)
        if isinstance(node.else_block, BlockNode):
            collect_funcapps(node.else_block, names)
    elif isinstance(node, RepeatNode):
        collect_funcapps(node.count_node, names)
        collect_funcapps(node.block_node, names)
    elif isinstance(node, FuncDefNode):
        collect_funcapps(node.body, names)
    else:
        for attr in ('expression', 'variable', 'test', 'reference',
                     'collection', 'index_node', 'element',
                     'count_node', 'block_node', 'body',
                     'left', 'right', 'then_block', 'else_block',
                     'name_node'):
            if hasattr(node, attr):
                v = getattr(node, attr)
                if v is not None and not isinstance(v, str):
                    collect_funcapps(v, names)
        if hasattr(node, 'elements'):
            for e in node.elements:
                collect_funcapps(e, names)
        if hasattr(node, 'contents') and isinstance(node.contents, list):
            for p in node.contents:
                if not isinstance(p, str):
                    collect_funcapps(p, names)


def get_stdlib_aliases():
    """標準ライブラリの (英語名, [全ての別名]) のリストを返す。"""
    modules = []
    standard_lib(modules)
    aliases = []
    for alias_str, _ in modules:
        parts = alias_str.split('|')
        # 日本語名（中間）を代表名として採用
        rep = parts[1] if len(parts) >= 2 else parts[0]
        aliases.append((rep, parts))
    return aliases


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

def analyze_file(path):
    """1 ファイルを解析して (features_counter, func_names_counter) を返す。"""
    with open(path, encoding='utf-8') as f:
        source = f.read()
    ast = Source(source, syntax='yui').parse('@TopLevel')
    features = Counter()
    names = Counter()
    collect_features(ast, features)
    collect_funcapps(ast, names)
    return features, names


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('paths', nargs='*',
                    help='対象ファイル / ディレクトリ / グロブ（未指定時は --dir を使う）')
    ap.add_argument('--dir', default='yui_examples',
                    help='paths 未指定時の対象ディレクトリ (default: yui_examples)')
    ap.add_argument('-o', '--output', default='-',
                    help='CSV 出力先ファイル (default: 標準出力)')
    args = ap.parse_args()

    # paths が与えられていればそれを、なければ --dir 配下の *.yui を使う
    if args.paths:
        files = []
        for p in args.paths:
            if os.path.isdir(p):
                files.extend(glob.glob(os.path.join(p, '*.yui')))
            elif any(ch in p for ch in '*?['):
                files.extend(glob.glob(p))
            elif os.path.isfile(p):
                files.append(p)
            else:
                print(f'Warning: not found: {p}', file=sys.stderr)
        files = sorted(set(files))
    else:
        files = sorted(glob.glob(os.path.join(args.dir, '*.yui')))

    if not files:
        print('No *.yui files found.', file=sys.stderr)
        sys.exit(1)

    # 各ファイルを解析
    file_names = []            # ファイル短縮名（順序保持）
    feat_counts = {}           # short_name -> Counter
    func_counts = {}           # short_name -> Counter
    errors = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            features, names = analyze_file(path)
        except Exception as e:
            errors.append((name, str(e)))
            continue
        file_names.append(name)
        feat_counts[name] = features
        func_counts[name] = names

    if errors:
        for name, msg in errors:
            print(f'parse error: {name}: {msg}', file=sys.stderr)

    # 標準ライブラリ関数テーブル（日本語名を行キーに使う）
    aliases = get_stdlib_aliases()

    # CSV 組み立て
    rows = []
    header = ['category', 'name', 'total'] + file_names
    rows.append(header)

    # 構文要素
    for feat in SYNTAX_FEATURES:
        per_file = [feat_counts.get(n, Counter()).get(feat, 0) for n in file_names]
        rows.append(['syntax', feat, sum(per_file)] + per_file)

    # 標準ライブラリ関数（全エイリアスの合計をその関数の出現数とする）
    for rep, parts in aliases:
        per_file = []
        for n in file_names:
            c = func_counts.get(n, Counter())
            per_file.append(sum(c.get(p, 0) for p in parts))
        rows.append(['stdlib', rep, sum(per_file)] + per_file)

    # 出力
    if args.output == '-':
        writer = csv.writer(sys.stdout)
        for r in rows:
            writer.writerow(r)
    else:
        with open(args.output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for r in rows:
                writer.writerow(r)
        print(f'Wrote {args.output}', file=sys.stderr)


if __name__ == '__main__':
    main()
