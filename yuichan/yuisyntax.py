# Source
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod
from typing import Union, Any, List
import re
import json
import os
import random

def get_example_from_pattern(pattern: str, random_seed=None) -> str:
    """正規表現パターンからそのパターンにマッチする文字列の例（最初の例）を取得する"""
    # エスケープされた文字を一時的に置換
    global _random_seed
    if random_seed is not None:
        _random_seed = random_seed
    
    original_pattern = pattern
    ESC = [
        (r'\|', '▁｜'), (r'\[', '▁［'), (r'\]', '▁］'),
        (r'\(', '▁（'), (r'\)', '▁）'), (r'\*', '▁＊'), (r'\?', '▁？'),
        (r'\+', '▁＋'), (r'+', ''), (r'*', '?')
    ]
    for a, b in ESC:
        pattern = pattern.replace(a, b)
    #print(f"@pattern: `{original_pattern}` -> `{pattern}`")  # デバッグ用   
    processed = ''
    while len(pattern) > 0:
        s_pos = pattern.find('(') # シングルループだけ対応
        if s_pos == -1:
            processed += get_example_from_pattern_inner(pattern)
            break
        e_pos = pattern.find(')', s_pos+1)
        if e_pos == -1:
            raise ValueError(f"Unmatched parentheses in pattern: `{original_pattern}`")
        processed += get_example_from_pattern_inner(pattern[:s_pos])
        inner = pattern[s_pos+1:e_pos]
        pattern = pattern[e_pos+1:]
        if pattern.startswith('?'):
            pattern = pattern[1:]
            if _random(2) != 0:
                processed += get_example_from_pattern_inner(inner)
        else:
            processed += get_example_from_pattern_inner(inner)
    #print(f"@processed: `{pattern}` -> `{processed}`")  # デバッグ用
    # 置換した文字を元に戻す
    ESC2 = [
        ('▁｜', r'|'), ('▁［', r'['), ('▁］', r']'), ('▁（', r'('),
        ('▁）', r')'), ('▁？', r'?'), ('▁＋', r'+'), ('▁＊', r'*'),
    ]
    for a, b in ESC2:
        processed = processed.replace(a, b)
    assert '▁' not in processed, f"Unprocessed escape sequences remain in `{original_pattern}`: `{processed}`"
    return processed

_random_seed = None

def _random(n):
    global _random_seed
    if _random_seed is None:
        return 0
    random.seed(_random_seed)
    _random_seed += 1
    return random.randint(0, n - 1)

def split_heading_char(s: str):
    if s.startswith("\\"):
        # エスケープシーケンスの処理
        remaining = s[2:]
        if s.startswith('\\', 1):  # バックスラッシュ
            heading_char = '\\'
        elif s.startswith('s', 1):  # 空白文字
            heading_char = ' '
        elif s.startswith('t', 1):  # タブ
            heading_char = '\t'
        elif s.startswith('n', 1):  # 改行
            heading_char = '\n'
        elif s.startswith('r', 1):  # キャリッジリターン
            heading_char = '\r'
        elif s.startswith('d', 1):  # 数字
            heading_char = '1'
        elif s.startswith('w', 1):  # 単語文字
            heading_char = 'a'
        else:
            heading_char = s[1]
    elif s.startswith('▁', 0):
        heading_char = s[0:2]
        remaining = s[2:]
    elif s.startswith('\uFE0F', 1) or s.startswith('\u200D', 1): 
        #合字や絵文字のバリエーションセレクタを考慮
        heading_char = s[0:2]
        remaining = s[2:]
    else:
        heading_char = s[0]
        remaining = s[1:]
    if remaining.startswith("?"):
        if _random(2) == 0:
            return '', remaining[1:]
        return heading_char, remaining[1:]
    return heading_char, remaining

def get_example_from_pattern_inner(pattern: str)-> str:
    if pattern == "":
        return ""
    # 選択肢（|）の処理：最初の選択肢を使用
    if "|" in pattern:
        choice = pattern.split("|")
        pattern = choice[_random(len(choice))]

    # 文字クラス [abc] の処理 
    if pattern.startswith("["):
        end_pos = pattern.find("]")
        if pattern.startswith('?', end_pos + 1):
            return get_example_from_pattern_inner(pattern[end_pos+2:])
        heading_char, _ = split_heading_char(pattern[1:end_pos])
        return heading_char + get_example_from_pattern_inner(pattern[end_pos+1:])
    heading_char, remaining = split_heading_char(pattern)
    return heading_char + get_example_from_pattern_inner(remaining)


DEFAULT_SYNTAX_JSON = {
    "whitespace": "[ \\t\\r　]",
    "whitespaces": "[ \\t\\r　]+",
    "linefeed": "[\\n]",
    "line-comment-begin": "[#＃]",

    "number-first-char": "[0-9]",
    "number-chars": "[0-9]*",
    "number-dot-char": "[\\.][0-9]",

    "name-first-char": "[A-Za-z_]",
    "name-chars": "[A-Za-z0-9_]*",
    
    "string-begin": "\"",
    "string-end": "\"",
    "string-escape": "\\\\",
    "string-interpolation-begin": "\\{",
    "string-interpolation-end": "\\}",
#    "string-content-end": "\\\\|\\{|\\\"",

    "grouping-begin": "\\(",
    "grouping-end": "\\)",

    "array-begin": "\\[",
    "array-end": "\\]",
    "array-separator": ",",

    "object-begin": "\\{",
    "object-end": "\\}",
    "object-separator": ",",
    "key-value-separator": ":",

    "array-indexer-suffix": "\\[",
    "array-indexer-end": "\\]",
    "unary-minus": "-",
    
    "funcapp-args-begin": "\\(",
    "funcapp-args-end": "\\)",
    "funcapp-separator": ",",

    "unary-inspect": "👀",
    "catch-begin": "🧤",
    "catch-end": "🧤",

    "print-begin": "",
    "print-end": "",

    "assert-begin": ">>>\\s+",
    "assert-infix": "[\\n]",
    "assert-end": "",

}

def load_syntax(filepath: Optional[str] = None) -> Dict[str, str]:
    """JSON文法ファイルから終端記号をロードする"""
    if filepath is None:
        filepath = "yui"

    if not os.path.isfile(filepath):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        syntax_dir = os.path.join(current_dir, 'syntax')
        if not filepath.endswith('.json'):
            filepath = f"{filepath}.json"
        new_filepath = os.path.join(syntax_dir, filepath)
        if os.path.isfile(new_filepath):
            filepath = new_filepath

    with open(filepath, 'r', encoding='utf-8') as f:
        terminals = json.load(f)
    
    for key, pattern in DEFAULT_SYNTAX_JSON.items():
        if key not in terminals:
            terminals[key] = pattern

    if 'string-content-end' not in terminals:
        escape = terminals.get('string-escape', r'\\')
        interpolation = terminals.get('string-interpolation-begin', r'\{')
        string_end = terminals.get('string-end', r'\"')
        terminals['string-content-end'] = f"{escape}|{interpolation}|{string_end}"

    # if 'identifiers' not in terminals:
    #     identifiers = extract_identifiers(json.dumps(terminals))
    #     terminals['identifiers'] = identifiers

    return terminals

_DEFAULT_SYNTAX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'syntax')

def list_syntax_names(syntax_dir: Optional[str] = None) -> List[str]:
    """syntax ディレクトリにある syntax 名の一覧を返す（.json 拡張子なし、ソート済み）。"""
    d = syntax_dir or _DEFAULT_SYNTAX_DIR
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith('.json'))


def find_matching_syntaxes(sources: Dict[str, str], syntax_dir: Optional[str] = None) -> List[tuple]:
    """
    利用可能な全 syntax に対して sources のソースコードを解析し、成否を返す。

    Args:
        sources:    {filename: source_code} の辞書
        syntax_dir: syntax JSON ファイルを探すディレクトリ（None なら組み込みディレクトリ）

    Returns:
        [(syntax_name, matched: bool, status_message: str), ...] のリスト
    """
    from .yuiparser import YuiParser  # 循環インポートを避けるため遅延インポート

    d = syntax_dir or _DEFAULT_SYNTAX_DIR
    results = []
    for name in list_syntax_names(syntax_dir):
        filepath = os.path.join(d, f"{name}.json")
        error_info = None
        for filename, code in sources.items():
            try:
                YuiParser(filepath).parse(code)
            except Exception as e:
                error_info = (filename, e)
                break
        if error_info is None:
            results.append((name, True, 'OK'))
        else:
            fname, err = error_info
            results.append((name, False, f"FAIL ({os.path.basename(fname)}: {err})"))
    return results


def generate_bnf(terminals: dict) -> str:
    """
    syntax dict から BNF 風の文法表記を生成する。
    各トークン名には for_example() で得た代表文字列を当てはめる。
    """
    s = YuiSyntax(terminals)
    syntax_name = terminals.get('syntax', '?')

    def ex(name: str) -> str:
        """トークンの代表文字列。未定義なら ''。"""
        if not s.is_defined(name):
            return ''
        val = s.for_example(name)
        # assert-infix が改行の場合は記号に置換
        if val == '\n':
            return '↵'
        return val

    E, N, B = '<expr>', '<name>', '<block>'

    out: list[str] = []

    def section(title: str):
        out.append('')
        out.append(f'{title}:')

    def r(lhs: str, *parts):
        """BNF規則を追加。空文字列の部品は無視する。"""
        tokens = [str(p) for p in parts if p is not None and str(p) != '']
        if tokens:
            out.append(f'  {lhs:<18} ::= {" ".join(tokens)}')

    # ── ヘッダ ────────────────────────────────────────────────
    out.append(f'Grammar for {syntax_name!r}')
    out.append('─' * 40)

    # ── Literals ─────────────────────────────────────────────
    section('Literals')

    r('Number', '0  |  3.14')

    sb, se = ex('string-begin'), ex('string-end')
    ib, ie = ex('string-interpolation-begin'), ex('string-interpolation-end')
    interp = f'  (interp: {ib}{E}{ie})' if ib else ''
    r('String', f'{sb}...{se}{interp}')

    ab, ae = ex('array-begin') or '[', ex('array-end') or ']'
    asep = ex('array-separator') or ','
    r('Array', f'{ab} {E} {{{asep} {E}}} {ae}')

    ob, oe = ex('object-begin') or '{', ex('object-end') or '}'
    kvsep = ex('key-value-separator') or ':'
    osep = ex('object-separator') or ','
    r('Object', f'{ob} "key"{kvsep}{E} {{{osep} "key"{kvsep}{E}}} {oe}')

    nl = ex('null')
    if nl:
        r('Null', nl)

    bt, bf = ex('boolean-true'), ex('boolean-false')
    if bt or bf:
        r('Boolean', bt or '?', '|', bf or '?')

    nb, ne = ex('extra-name-begin'), ex('extra-name-end')
    if nb:
        r('Name', f'{nb}...{ne}  |  letter...')
    else:
        r('Name', 'letter...')

    # ── Expressions ──────────────────────────────────────────
    section('Expressions')

    gb, ge = ex('grouping-begin'), ex('grouping-end')
    if gb:
        r('Grouping', f'{gb} {E} {ge}')

    if ex('length-begin'):
        r('Length', ex('length-begin') + E + ex('length-end'))
    elif ex('unary-length'):
        r('Length', ex('unary-length') + ' ' + E)
    elif ex('property-accessor') and ex('property-length'):
        r('Length', f'{E}{ex("property-accessor")}{ex("property-length")}')

    if ex('unary-minus'):
        r('Minus', ex('unary-minus') + E)

    fa_b, fa_e = ex('funcapp-args-begin'), ex('funcapp-args-end')
    fa_sep = ex('funcapp-separator') or ','
    if fa_b:
        r('FuncApp', f'{E}{fa_b}{E} {{{fa_sep} {E}}}{fa_e}')

    ai_b = ex('array-indexer-suffix') or '['
    ai_e = ex('array-indexer-end') or ']'
    r('Index', f'{E}{ai_b}{E}{ai_e}')

    pa = ex('property-accessor')
    if pa:
        props = [ex(k) for k in ('property-length', 'property-type') if ex(k)]
        if props:
            r('Property', f'{E}{pa}({" | ".join(props)})')

    arith = [(op, ex(f'binary{op}')) for op in ['+', '-', '*', '/', '%'] if ex(f'binary{op}')]
    if arith:
        r('Arithmetic', ' | '.join(f'{E} {t} {E}' for _, t in arith))

    comp_ops = [
        (op, ex(f'binary{op}'))
        for op in ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin']
        if ex(f'binary{op}')
    ]
    if comp_ops:
        r('Comparison', ' | '.join(f'{E} {t} {E}' for _, t in comp_ops))

    # ── Statements ───────────────────────────────────────────
    section('Statements')

    r('Assignment',
      ex('assignment-begin'), E, ex('assignment-infix'), E, ex('assignment-end'))
    r('Increment',
      ex('increment-begin'), E, ex('increment-infix'), ex('increment-end'))
    r('Decrement',
      ex('decrement-begin'), E, ex('decrement-infix'), ex('decrement-end'))
    r('Append',
      ex('append-begin'), E, ex('append-infix'), E, ex('append-end'))

    if ex('break'):    r('Break',    ex('break'))
    if ex('continue'): r('Continue', ex('continue'))
    if ex('pass'):     r('Pass',     ex('pass'))

    r('Return', ex('return-begin'), E, ex('return-end'))
    if ex('return-none'):
        r('Return (void)', ex('return-none'))

    r('Print', ex('print-begin'), E, ex('print-end'))

    r('Repeat',
      ex('repeat-begin'), E, ex('repeat-times'), ex('repeat-block'), B, ex('repeat-end'))

    # If ─ infix-op形式（pylike/emoji）か suffix形式（yui）かで分岐
    if_b  = ex('if-begin')
    if_cb = ex('if-condition-begin')
    if_ce = ex('if-condition-end')
    if_then = ex('if-then')
    if_else = ex('if-else')
    if_end  = ex('if-end')

    if_infix_ops = [
        (op, ex(f'if-infix{op}'))
        for op in ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin']
        if ex(f'if-infix{op}')
    ]
    if_suffix_ops = [
        ex(f'if-suffix{op}')
        for op in ['!=', '<', '<=', '>', '>=', 'in', 'notin', '==']
        if ex(f'if-suffix{op}')
    ]

    if if_infix_ops:
        op_alts = ' | '.join(f'{E} {t} {E}' for _, t in if_infix_ops)
        r('If', if_b, if_cb, f'({op_alts})', if_ce, if_then, B,
          f'[ {if_else} {B} ]' if if_else else '', if_end)
    else:
        infix_word = ex('if-infix')
        suffix_str = f'[ {" | ".join(if_suffix_ops[:3])}... ]' if if_suffix_ops else ''
        r('If', if_b, if_cb, E, infix_word, E, suffix_str, if_ce, if_then, B,
          f'[ {if_else} {B} ]' if if_else else '', if_end)

    # FuncDef
    fd_b    = ex('funcdef-begin')
    fd_nb   = ex('funcdef-name-begin')
    fd_ne   = ex('funcdef-name-end')
    fd_noarg = ex('funcdef-noarg')
    fd_ab   = ex('funcdef-args-begin')
    fd_ae   = ex('funcdef-args-end')
    fd_asep = ex('funcdef-arg-separator')
    fd_blk  = ex('funcdef-block')
    fd_end  = ex('funcdef-end')

    if fd_noarg:
        args_part = f'( {fd_noarg}  |  {fd_ab} {N} {{{fd_asep} {N}}} {fd_ae} )'
    else:
        args_part = f'{fd_ab} {N} {{{fd_asep} {N}}} {fd_ae}'

    r('FuncDef', fd_b, fd_nb, N, fd_ne, args_part, fd_blk, B, fd_end)

    # Assert
    if s.is_defined('assert-begin'):
        r('Assert', ex('assert-begin'), E, ex('assert-infix'), E, ex('assert-end'))

    if s.is_defined('import-standard'):
        r('Import', ex('import-standard'))

    # ── Blocks ───────────────────────────────────────────────
    section('Blocks')

    blk_b, blk_e = ex('block-begin'), ex('block-end')
    if blk_b and blk_e:
        r('Block', blk_b, '<stmt>...', blk_e)
    elif blk_b:
        r('Block', blk_b, '<stmt>...', '(indent-delimited)')
    else:
        r('Block', '<stmt>...', '(indent-delimited)')
    r('TopLevel', '<stmt>...')

    # ── Comments ─────────────────────────────────────────────
    section('Comments')
    if s.is_defined('line-comment-begin'):
        r('LineComment', ex('line-comment-begin') + ' ...')
    if s.is_defined('comment-begin') and s.is_defined('comment-end'):
        r('BlockComment', ex('comment-begin') + ' ... ' + ex('comment-end'))

    return '\n'.join(out)


class YuiSyntax(object):
    terminals: Dict[str, str]

    def __init__(self, syntax_json: Dict[str, str]):
        super().__init__()
        assert isinstance(syntax_json, dict), "Terminals must be a dictionary"
        self.terminals = syntax_json.copy()
        self.random_seed = None

    def is_defined(self, terminal):
        return self.terminals.get(terminal, "") != ""

    def update_syntax(self, **kwargs):
        self.terminals.update(kwargs)

    def get(self, terminal: str):
        pattern = self.terminals.get(terminal, "")
        if not isinstance(pattern, str):
            return pattern.pattern
        return pattern

    def get_pattern(self, terminal: str, if_undefined = "") -> re.Pattern:
        pattern = self.terminals.get(terminal, if_undefined)
        if isinstance(pattern, str):
            try:
                pattern = re.compile(pattern)
            except re.error:
                raise ValueError(f"Invalid regex '{terminal}': {pattern}")
            self.terminals[terminal] = pattern
        return pattern

    def for_example(self, terminal: str) -> str:
        if self.is_defined(terminal):
            pattern = self.terminals[terminal]
            if not isinstance(pattern, str):
                pattern = pattern.pattern
            #print(f"@for_example: terminal `{terminal}` with pattern `{pattern}`")  # デバッグ用
            example = get_example_from_pattern(pattern, random_seed=self.random_seed)
            return example
        return ""


