# Source
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod
from typing import Union, Any, List
import re
import json
import os

def get_example_from_pattern(pattern: str) -> str:
    """正規表現パターンからそのパターンにマッチする文字列の例（最初の例）を取得する"""
    # エスケープされた文字を一時的に置換
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
        processed += get_example_from_pattern_inner(pattern[:s_pos])
        inner = pattern[s_pos+1:e_pos]
        pattern = pattern[e_pos+1:]
        if pattern.startswith('?'):
            pattern = pattern[1:]
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
        return '', remaining[1:]
    return heading_char, remaining

def get_example_from_pattern_inner(pattern: str)-> str:
    if pattern == "":
        return ""
    # 選択肢（|）の処理：最初の選択肢を使用
    if "|" in pattern:
        pattern = pattern.split("|")[0]
    # 文字クラス [abc] の処理 
    if pattern.startswith("["):
        end_pos = pattern.find("]")
        if pattern.startswith('?', end_pos + 1):
            return get_example_from_pattern_inner(pattern[end_pos+2:])
        heading_char, _ = split_heading_char(pattern[1:end_pos])
        return heading_char + get_example_from_pattern_inner(pattern[end_pos+1:])
    heading_char, remaining = split_heading_char(pattern)
    return heading_char + get_example_from_pattern_inner(remaining)

def is_all_alnum(s: str) -> bool:
    for ch in s:
        if not (('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or (ch == '_')):
            return False
    return True

def extract_identifiers(text):
    identifiers = []
    
    # 識別子のパターン: アルファベットまたはアンダースコアで始まり、
    # その後に英数字とアンダースコアが続く
    identifier_pattern = r'[^\s\]\[\(\)"]+'
    
    # 1. 改行と= の間（==は除外）
    pattern1 = rf'\n\s*({identifier_pattern})\s*=(?!=)'
    matches1 = re.findall(pattern1, text)
    identifiers.extend(matches1)
    
    # 2. 関数名のパターン
    pattern2 = rf'({identifier_pattern})\s*[\(]'
    matches2 = re.findall(pattern2, text)
    identifiers.extend(matches2)
    
    def has_unicode(s):
        for ch in s:
            if ord(ch) > 127:
                return True
        return False

    # Unicode文字を含む文字列のみ
    identifiers = list(set(id for id in identifiers if has_unicode(id)))
    # print(f"@Extracted identifiers: {identifiers}")  
    return list(set(identifiers))

DEFAULT_SYNTAX_JSON = {
    "whitespace": "[ \\t\\r　]",
    "whitespaces": "[ \\t\\r　]+",
    "linefeed": "[\\n]",
    "line-comment-begin": "[#＃]",

    "number-first-char": "[0-9]",
    "number-chars": "[0-9]*",
    "number-dot-char": "[\\.]",

    "name-first-char": "[A-Za-z_]",
    "name-chars": "[A-Za-z0-9_]*",
    
    "string-begin": "\"",
    "string-end": "\"",
    "string-escape": "\\\\",
    "string-interpolation-begin": "\\{",
    "string-interpolation-end": "\\}",
#    "string-content-end": "\\\\|\\{|\\\"",

    "array-begin": "\\[",
    "array-end": "\\]",
    "array-separator": ",",

    "object-begin": "\\{",
    "object-end": "\\}",
    "object-separator": ",",
    "key-value-separator": ":",

    "array-indexer-suffix": "\\[",
    "array-indexer-end": "\\]",
    
    "funcapp-args-suffix": "\\(",
    "funcapp-args-end": "\\)",
    "funcapp-args-separator": ",",
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

    if 'identifiers' not in terminals:
        identifiers = extract_identifiers(json.dumps(terminals))
        terminals['identifiers'] = identifiers

    # if 'keywords' not in terminals:
    #     keywords = set()
    #     for key, pattern in terminals.items():
    #         word = get_example_from_pattern(pattern).strip()
    #         if is_all_alnum(word):
    #             if word not in keywords:
    #                 keywords.add(word)
    #     terminals['keywords'] = keywords        
    return terminals

class YuiSyntax(object):
    terminals: Dict[str, str]

    def __init__(self, syntax_json: Dict[str, str]):
        super().__init__()
        assert isinstance(syntax_json, dict), "Terminals must be a dictionary"
        self.terminals = syntax_json.copy()

    def is_defined(self, terminal):
        return self.terminals.get(terminal, "") != ""

    def update_syntax(self, **kwargs):
        self.terminals.update(kwargs)

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
            example = get_example_from_pattern(pattern)
            return example
        return ""

