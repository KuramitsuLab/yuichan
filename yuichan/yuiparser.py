# Source
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from types import FunctionType
from abc import ABC, abstractmethod
from typing import Union, Any, List
import re
import json
import os

from .yuiast import (
    YuiError, ASTNode, set_from_outside,
    NameNode,
    StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, ImportNode, 
)


def get_example_from_pattern(pattern: str) -> str:
    """正規表現パターンからそのパターンにマッチする文字列の例（最初の例）を取得する"""
    # エスケープされた文字を一時的に置換
    ESC = [
        (r'\|', '▁｜▁'), (r'\[', '▁［▁'), (r'\]', '▁］▁'),
        (r'\(', '▁（▁'), (r'\)', '▁）▁'), (r'\*', '▁＊▁'), (r'\?', '▁？▁'),
        (r'\+', '▁＋▁'), (r'+', ''), (r'*', '?')
    ]
    for a, b in ESC:
        pattern = pattern.replace(a, b)
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
    # 置換した文字を元に戻す
    ESC2 = [
        ('▁｜▁', r'|'), ('▁［▁', r'['), ('▁］▁', r']'), ('▁（▁', r'('),
        ('▁）▁', r')'), ('▁＊▁', r'*'), ('▁？▁', r'?'), ('▁＋▁', r'+'),
    ]
    for a, b in ESC2:
        processed = processed.replace(a, b)
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
    elif s.startswith('▁', 0) and s.endswith('▁', 2):
        heading_char = s[0:3]
        remaining = s[3:]
    elif s.startswith('\uFE0F', 1) or s.startswith('\u200D', 1): #合字や絵文字のバリエーションセレクタを考慮
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

def load_syntax(filepath: Optional[str] = None) -> Dict[str, str]:
    """JSON文法ファイルから終端記号をロードする"""
    if filepath is None:
        filepath = "yui"

    if not os.path.exists(filepath):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        syntax_dir = os.path.join(current_dir, 'syntax')
        if not filepath.endswith('.json'):
            filepath = f"{filepath}.json"
        new_filepath = os.path.join(syntax_dir, filepath)
        if os.path.exists(new_filepath):
            filepath = new_filepath

    with open(filepath, 'r', encoding='utf-8') as f:
        terminals = json.load(f)
    
    if 'keywords' not in terminals:
        keywords = set()
        for key, pattern in terminals.items():
            word = get_example_from_pattern(pattern).strip()
            if is_all_alnum(word):
                if word not in keywords:
                    keywords.add(word)
        terminals['keywords'] = keywords        
    return terminals

@dataclass
class SourceNode(ASTNode):
    """null値（?）を表すノード"""
    def __init__(self):
        super().__init__()

    def evaluate(self, runtime):
        return 0

class Source(object):
    """ソースコード"""
    def __init__(self, source: str, filename: str = "main.yui", pos: int = 0, syntax = 'yui'):
        self.filename = filename
        self.source = source
        self.pos = pos
        self.length = len(source)
        if isinstance(syntax, dict):
            self.terminals = syntax.copy()
        else:
            self.terminals = load_syntax(syntax)
        self.special_names = []
        self.add_special_names(extract_identifiers(source))      
        self.memos = {}
        # self.backtrack = True

    def update_syntax(self, **kwargs):
        self.terminals.update(kwargs)
    
    def get_memo(self, nonterminal: str, pos: int):
        """Pakrat parsingのメモを取得する"""
        return self.memos.get((nonterminal, pos), None) 
    
    def set_memo(self, nonterminal: str, pos: int, result: Any, new_pos: int):
        """Pakrat parsingのメモを設定する"""
        self.memos[(nonterminal, pos)] = (result, new_pos)

    def has_next(self):
        return self.pos < self.length

    def is_eos(self):
        return self.pos >= self.length

    def consume_string(self, text: str):
        if self.source.startswith(text, self.pos):
            self.pos += len(text)
            return True
        return False
    
    def is_defined(self, terminal: str) -> bool:
        return self.terminals.get(terminal, "") != ""

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
        pattern = self.get_pattern(terminal)
        return get_example_from_pattern(pattern.pattern)

    def matched_string(self, terminal: str) -> Optional[str]:
        pattern = self.get_pattern(terminal)
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            return match_result.group(0)
        return None

    def is_match(self, terminal: str, if_undefined:Union[bool, str]=False, 
                 unconsumed=False, lskip_ws=False,
                 skip_ws = False, skip_linefeed=False, next_alpha=False):
        if isinstance(if_undefined, bool) and not self.is_defined(terminal):
            return if_undefined
        if not terminal.startswith('!'): # よくある間違いを検出
            wrong_terminal = f"!{terminal}"
            if self.is_defined(wrong_terminal) and self.is_match(wrong_terminal, unconsumed=True, lskip_ws=lskip_ws):
                expected = self.for_example(terminal)
                matched = self.matched_string(wrong_terminal)
                raise YuiError(("expected", "syntax", f"✅{expected}", f"❌{matched}"), self.p(length=1), avoid_backtrack=True)
        saved_pos = self.pos    
        if lskip_ws:
            self.skip_whitespaces_and_comments()
        pattern = self.get_pattern(terminal, if_undefined=if_undefined if isinstance(if_undefined, str) else "")
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            match_length = match_result.end() - match_result.start()
            if unconsumed:
                self.pos = saved_pos
                return True
            self.pos += match_length
            if skip_ws or skip_linefeed:
                if next_alpha and self.pos - 1 >= 0 and 'A' <= self.source[self.pos - 1] <= 'z':
                    self.try_match("whitespace", if_undefined=r"[ \t\r]")
                self.skip_whitespaces_and_comments(include_linefeed=skip_linefeed)
            return True
        self.pos = saved_pos
        return False
    
    def try_match(self, terminal: str, if_undefined=True, unconsumed=False, avoid_backtrack=False,
              skip_ws = False, skip_linefeed=False, opening_pos: int = None, lskip_ws=False):
        if self.is_match(terminal, if_undefined=if_undefined, unconsumed=unconsumed,
                         skip_ws=skip_ws, skip_linefeed=skip_linefeed,
                         lskip_ws=lskip_ws):
            return
        candidate = self.for_example(terminal)
        if opening_pos is not None:
            raise YuiError(("expected", "syntax", "closing", f"✅`{candidate}`"), self.p(start_pos=opening_pos), avoid_backtrack=True)
        snippet = self.source[self.pos:self.pos+10].replace('\n', '\\n')
        raise YuiError(("expected", f"`{candidate}`", f"❌`{snippet}`"), self.p(length=1), avoid_backtrack=avoid_backtrack)

    def find_match(self, terminal: str, suffixes: List[str], skip_ws = False, skip_linefeed=False, lskip_ws=False):
        for suffix in suffixes:
            key = f"{terminal}{suffix}"
            if self.is_match(key, if_undefined=False, unconsumed=False, 
                             skip_ws=skip_ws, skip_linefeed=skip_linefeed, lskip_ws=lskip_ws):
                return suffix
        return None

    def contains_in_line(self, terminal: List[str]):
        if self.is_defined(terminal):
            pattern = self.get_pattern(terminal)
            end_pos = self.find('\n', self.pos)
            line = self.source[self.pos:end_pos]
            return pattern.search(line)
        return False

    def match_eos_or_linefeed(self, lskip_ws=False, unconsumed=False):
        saved_pos = self.pos    
        if lskip_ws:
            self.skip_whitespaces_and_comments()
        if self.is_eos():
            if unconsumed:
                self.pos = saved_pos
            return True
        return self.is_match("linefeed", lskip_ws=lskip_ws, unconsumed=unconsumed)

    def consume_until(self, terminal:str, until_eof=True, disallow_string:str=None):
        pattern = self.terminals[terminal]
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
            self.terminals[terminal] = pattern
        pattern = re.compile(pattern)
        match_result = pattern.search(self.source, self.pos)
        if match_result:
            self.pos = match_result.start()
            if disallow_string:
                if disallow_string in self.source[self.pos:match_result.start()]:
                    return False
            return True
        if until_eof:
            self.pos = self.length
            return True
        return False

    def skip_whitespaces_and_comments(self, include_linefeed=False):
        """空白文字とコメントをスキップする"""
        while self.has_next():
            if self.is_match("whitespaces", if_undefined=r"[ \t\r]+"):
                continue
            if include_linefeed and self.is_match("linefeed", if_undefined=r"\n"):
                continue
            if self.is_match("line-comment-begin", if_undefined=False):
                self.consume_until("linefeed", until_eof=True)
                continue
            if self.is_defined("comment-begin") and self.is_defined("comment-end"):
                opening_pos = self.pos
                if self.is_match("comment-begin"):
                    self.consume_until("comment-end", until_eof=True)
                    self.try_match("comment-end", opening_pos=opening_pos)
                    continue
            break

    def add_special_names(self, names: List[str]):
        special_names = set(self.special_names + names)
        self.special_names = sorted(special_names, key=len, reverse=True)

    def match_special_name(self, unconsumed=False) -> Optional[str]:
        for name in self.special_names:
            if self.source.startswith(name, self.pos):
                if not unconsumed:
                    self.pos += len(name)
                return name
        return None

    def capture_indent(self, indent_chars: str = " \t　"):
        start_pos = self.pos - 1
        # 行の先頭位置を探す
        while 0 <= start_pos:
            char = self.source[start_pos]
            if char == '\n':
                start_pos += 1
                break
            start_pos -= 1
        end_pos = start_pos
        while end_pos < self.length:
            char = self.source[end_pos]
            if char in indent_chars:
                end_pos += 1
            else:
                break
        return self.source[start_pos:end_pos]

    def capture_line(self):
        start_pos = self.pos
        while self.pos < self.length:
            char = self.source[self.pos]
            if char == '\n':
                return self.source[start_pos:self.pos]
            self.pos += 1
        return self.source[start_pos:]

    def capture_comment(self):
        """コメントを位置を変えずに習得する。行コメントとブロックコメントの両方に対応。"""
        save_pos = self.pos
        self.is_match("whitespaces", if_undefined=r"[ \t\r]+")
        comment = None
        if self.is_match("line-comment-begin", if_undefined=False):
            start_pos = self.pos
            self.consume_until("linefeed", until_eof=True)
            comment =self.source[start_pos:self.pos]
        if self.is_match("comment-begin", if_undefined=False):
            start_pos = self.pos
            self.consume_until("comment-end", until_eof=True)
            comment = self.source[start_pos:self.pos]
        self.pos = save_pos # コメントは位置を変えずに取得
        return comment

    def p(self, node: ASTNode = None, 
          start_pos: int = None, end_pos: int = None, length: int = 0) -> ASTNode:
        node = node or SourceNode()
        node.filename = self.filename
        node.source = self.source
        #node.comment = self.capture_comment()

        save_pos = self.pos
        if start_pos is not None:
            node.pos = start_pos
            if end_pos is not None:
                node.end_pos = end_pos
            elif length != 0:
                node.end_pos = min(start_pos + length, self.length)
            else:
                node.end_pos = save_pos           
        elif length != 0:
            node.pos = self.pos
            node.end_pos = min(self.pos + length, self.length)
        else:
            node.pos = max(self.pos-1, 0)
            node.end_pos = self.pos
        return node

NONTERMINALS = {}

class ParserCombinator(object):

    def quick_check(self, source: Source) -> bool:
        return True
    
    def match(self, source: Source, pc: dict):
        return True

def parse(nonterminal: str, source: Source, pc: dict, avoid_backtrack=False,
          skip_ws: bool = False, skip_linefeed: bool = False, lskip_ws=False) -> Any:
    global NONTERMINALS
    patterns = NONTERMINALS[nonterminal]
    saved_pos = source.pos
    if lskip_ws:
        source.skip_whitespaces_and_comments()
    
    memo = source.get_memo(nonterminal, source.pos)
    if memo is not None:
        source.pos = memo[1]
        result = memo[0]
    else:
        saved_pos = source.pos
        try:
            result = patterns.match(source, pc)
            source.set_memo(nonterminal, saved_pos, result, source.pos)
        except YuiError as e:
            if e.avoid_backtrack:
                raise e
            source.pos = saved_pos
            if avoid_backtrack:
                snippet = source.capture_line()
                print(f"@Backtracking avoided for {e}")
                raise YuiError(("expected", "syntax", nonterminal[1:].lower(), f"❌{snippet}"), source.p(length=1), avoid_backtrack=True)
            raise e
    if skip_ws or skip_linefeed:
        source.skip_whitespaces_and_comments(include_linefeed=skip_linefeed)
    return result

def is_parsable(nonterminal: str, source: Source, pc: dict, lskip_ws=False) -> bool:
    try:
        parse(nonterminal, source, pc, lskip_ws=lskip_ws)
        return True
    except YuiError:
        return False

class BooleanParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("boolean-true", if_undefined=False) or source.is_match("boolean-false", if_undefined=False)
    
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        if source.is_match("boolean-true", if_undefined=False):
            return source.p(NumberNode(1), start_pos=saved_pos)
        if source.is_match("boolean-false", if_undefined=False):
            return source.p(NumberNode(0), start_pos=saved_pos)
        raise YuiError(("expected", "boolean"), source.p(length=1))

NONTERMINALS["@Boolean"] = BooleanParser()

class NumberParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("number-first-char", if_undefined=r"[0-9]", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        if source.is_match("number-first-char", if_undefined=r"[0-9]"):
            source.try_match("number-chars", if_undefined=r"[0-9]")
            if source.is_match("number-dot-char", if_undefined=r"\."):
                source.try_match("number-first-char", avoid_backtrack=True)
                source.try_match("number-chars")
                number = source.source[saved_pos:source.pos]
                return source.p(NumberNode(float(number)), start_pos=saved_pos)
            else:
                number = source.source[saved_pos:source.pos]
            return source.p(NumberNode(int(number)), start_pos=saved_pos)
        raise YuiError(("expected", pc.get("expected", "number")), source.p(length=1))

NONTERMINALS["@Number"] = NumberParser()

class StringParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("string-begin", if_undefined=r'"', unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_quote_pos = source.pos
        if source.is_match("string-begin", if_undefined=r'"'):
            opening_pos = source.pos
            string_content = []
            expression_count = 0
            while source.pos < source.length:
                source.consume_until("string-content-end", until_eof=True)
                string_content.append(source.source[opening_pos:source.pos])
                if source.is_match("string-end"):
                    if expression_count == 0:
                        string_content = ''.join(string_content)
                    return source.p(StringNode(string_content), start_pos=opening_quote_pos)
                if source.is_match("string-escape"):
                    if source.is_eos():
                        raise YuiError(("bad", "escape sequence"), source.p(length=1), avoid_backtrack=True)
                    next_char = source.source[source.pos]
                    source.pos += 1
                    if next_char == 'n':
                        string_content.append('\n')
                    elif next_char == 't':
                        string_content.append('\t')
                    else:
                        string_content.append(next_char)
                    continue
                start_inter_pos = source.pos
                if source.is_match("string-interpolation-begin", skip_ws=True):
                    expression = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack = True)
                    source.try_match("string-interpolation-end", opening_pos=start_inter_pos, avoid_backtrack = True)
                    string_content.append(expression)
                    expression_count += 1
                    continue
            candidate = source.for_example("string-end")
            raise YuiError(("expected", "syntax", "closing", f"✅`{candidate}`", f"`🔍{candidate}`"), source.p(start_pos=opening_quote_pos), avoid_backtrack = True)
        raise YuiError(("expected", pc.get("expected", "string")), source.p(length=1), avoid_backtrack = True)

NONTERMINALS["@String"] = StringParser()

class ArrayParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("array-begin", if_undefined=r"\[", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("array-begin", if_undefined=r"\[", skip_linefeed=True):
            arguments = []
            while not source.is_match("array-end", if_undefined=r"\]", unconsumed=True):
                arguments.append(parse("@Expression", source, pc, skip_linefeed=True, avoid_backtrack=True))
                if source.is_match("array-end", if_undefined=r"\]"):
                    return source.p(ArrayNode(arguments), start_pos=opening_pos)
                if source.is_match("array-separator", skip_linefeed=True):
                    continue
                break
            if is_parsable("@Expression", source, pc):
                candidate = source.for_example("array-separator")
                raise YuiError(("expected", f"`{candidate}`"), source.p(length=1))
            source.try_match("array-end", if_undefined=r"\]", opening_pos=opening_pos)
            return source.p(ArrayNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", "array"), source.p(length=1))

NONTERMINALS["@Array"] = ArrayParser()

class ObjectParser(ParserCombinator):
    def quick_check(self, source: Source) -> bool:
        return source.is_match("object-begin", if_undefined=r"\{", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("object-begin", if_undefined=r"\{", skip_linefeed=True):
            arguments = []
            while not source.is_match("object-end", if_undefined=r"\}", unconsumed=True):
                arguments.append(parse("@String", source, pc, skip_linefeed=True, avoid_backtrack=True))
                source.try_match("object-key-value-separator", if_undefined=r"\:", skip_linefeed=True, avoid_backtrack=True)
                arguments.append(parse("@Expression", source, pc, skip_linefeed=True, avoid_backtrack=True))
                if source.is_match("object-end", if_undefined=r"\}"):
                    return source.p(ObjectNode(arguments), start_pos=opening_pos)
                if source.is_match("object-separator", skip_linefeed=True):
                    continue
                break
            if is_parsable("@String", source, pc):
                candidate = source.for_example("object-separator")
                raise YuiError(("expected", f"`{candidate}`"), source.p(length=1), avoid_backtrack=True)
            source.try_match("object-end", if_undefined=r"\}", opening_pos=opening_pos)
            return source.p(ObjectNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", pc.get("expected", "object")), source.p(length=1))

NONTERMINALS["@Object"] = ObjectParser()

class NameParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        if source.is_defined("keywords"):
            for keyword in source.terminals["keywords"]:
                if source.is_match(keyword, if_undefined=False, unconsumed=True):
                    return False
        return source.is_match("name-first-char", if_undefined=r"[A-Za-z_]", unconsumed=True) or source.is_match("extra-name-begin", if_undefined=True, unconsumed=True)

    def match(self, source: Source, pc: dict):
        special_name = source.match_special_name()
        if special_name is not None:
            return source.p(NameNode(special_name), start_pos=source.pos-len(special_name))
        if source.is_match("extra-name-begin", if_undefined=False):
            start_pos = source.pos
            source.consume_until("extra-name-end", disallow_string="\n")
            name = source.source[start_pos:source.pos]
            node = source.p(NameNode(name), start_pos=start_pos)
            source.try_match("extra-name-end", opening_pos=start_pos-1)
            return node
        start_pos = source.pos
        if source.is_match("name-first-char", if_undefined=r"[A-Za-z_]"):
            source.try_match("name-chars", if_undefined=r"[A-Za-z0-9_]*")
            source.try_match("identifier-end", if_undefined=True)
            name = source.source[start_pos:source.pos]
            return source.p(NameNode(name), start_pos=start_pos)
        snippet = source.capture_line()
        raise YuiError(("expected", pc.get("expected", "identifier"), f"❌{snippet}"), source.p(length=1))

NONTERMINALS["@Name"] = NameParser()

LITERALS = [
    "@Number",
    "@String",
    "@Array",
    "@Object",
    "@Boolean",
]

class TermParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("group-begin", skip_ws=True):
            expression_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=True)
            source.try_match("group-end", skip_ws=True, opening_pos=opening_pos)
            return expression_node
        if source.is_match("length-begin", skip_ws=True):
            expression_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=True)
            source.try_match("length-end", skip_ws=True, opening_pos=opening_pos)
            return source.p(ArrayLenNode(expression_node), start_pos=opening_pos)
        for literal in LITERALS:
            if NONTERMINALS[literal].quick_check(source):
                source.pos = opening_pos
                return parse(literal, source, pc)
        return parse("@Name", source, pc)

NONTERMINALS["@Term"] = TermParser()

class PrimaryParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        if source.is_match('unary-', if_undefined=False):
            node = parse('@Primary', source, pc, avoid_backtrack=True)
            return source.p(MinusNode(node), start_pos=start_pos)
        if source.is_match('unary-inspection', if_undefined=False):
            node = parse('@Primary', source, pc, avoid_backtrack=True)
            return source.p(PrintExpressionNode(node, inspection=True), start_pos=start_pos)
        node = parse("@Term", source, pc)
        while source.has_next():
            opening_pos = source.pos
            if source.is_match("funcapp-args-begin", if_undefined=r"\(", skip_linefeed=True):
                arguments = []
                while not source.is_match("funcapp-args-end", if_undefined=r"\)", skip_ws=True, unconsumed=True):
                    arguments.append(parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=True))
                    if source.is_match("funcapp-args-separator", if_undefined=r"\,", skip_linefeed=True):
                        continue
                    break
                source.try_match("funcapp-args-end", if_undefined=r"\)", skip_ws=True, opening_pos=opening_pos)
                node = source.p(FuncAppNode(node, arguments), start_pos=start_pos)
                continue
            if source.is_match("array-indexer-suffix", skip_ws=True):
                index_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=True)
                source.try_match("array-indexer-end", skip_ws=True, opening_pos=opening_pos)
                node = source.p(GetIndexNode(node, index_node), start_pos=start_pos)
                continue
            save_pos = source.pos
            if source.is_match("property-accessor", if_undefined=False):
                if source.is_match("property-length", if_undefined=False):
                    node = source.p(ArrayLenNode(node), start_pos=start_pos)
                    continue
                if source.is_match("property-type", if_undefined=False):
                    ...
                source.pos = save_pos
            break
        return node
    
NONTERMINALS["@Primary"] = PrimaryParser()

class MultiplicativeParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Primary", source, pc)
        try:
            if source.is_match("binary*", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "*", right_node), start_pos=start_pos)
            if source.is_match("binary/", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "/", right_node), start_pos=start_pos)
            if source.is_match("binary%", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "%", right_node), start_pos=start_pos)
        except YuiError:
            pass
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Multiplicative"] = MultiplicativeParser()

class AdditiveParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Multiplicative", source, pc)
        try:
            if source.is_match("binary+", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "+", right_node), start_pos=start_pos)
            if source.is_match("binary-", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "-", right_node), start_pos=start_pos)
        except YuiError:
            pass
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Additive"] = AdditiveParser()

class ComparativeParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Additive", source, pc)
        try:
            if source.is_match("binary==", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "==", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary!=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "!=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary<=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary>=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary<", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary>", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binaryin", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "in", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binarynotin", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "notin", right_node, comparative=True), start_pos=start_pos)
        except YuiError:
            pass
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Comparative"] = ComparativeParser()

class ExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        return parse("@Comparative", source, pc)

NONTERMINALS["@Expression"] = ExpressionParser()

## Statement

class AssignmentParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('assignment-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        left_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('assignment-infix', skip_ws=True, avoid_backtrack = avoid_backtrack)
        right_node = parse("@Expression", source, pc, avoid_backtrack = avoid_backtrack)
        source.try_match('assignment-end', lskip_ws=True, avoid_backtrack = avoid_backtrack) # E E 代入もありえる
        return source.p(AssignmentNode(left_node, right_node), start_pos=start_pos)
    
NONTERMINALS["@Assignment"] = AssignmentParser()

class IncrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('increment-begin', skip_ws=True)       
        avoid_backtrack = source.pos > start_pos
        lvalue_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=avoid_backtrack)
        source.try_match('increment-infix', lskip_ws=True, avoid_backtrack=avoid_backtrack)
        source.try_match('increment-end', lskip_ws=True, avoid_backtrack=avoid_backtrack)
        return source.p(IncrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Increment"] = IncrementParser()

class DecrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('decrement-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        lvalue_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=avoid_backtrack)
        source.try_match('decrement-infix', lskip_ws=True, avoid_backtrack=avoid_backtrack)
        source.try_match('decrement-end', lskip_ws=True, avoid_backtrack=avoid_backtrack)
        return source.p(DecrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Decrement"] = DecrementParser()

class AppendParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('append-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        lvalue_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('append-infix', skip_ws=True, avoid_backtrack = avoid_backtrack)
        value = parse("@Expression", source, pc, lskip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('append-suffix', lskip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('append-end', lskip_ws=True, avoid_backtrack = avoid_backtrack)
        return source.p(AppendNode(lvalue_node, value), start_pos=start_pos)

NONTERMINALS["@Append"] = AppendParser()

class BreakParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('break')
        return source.p(BreakNode(), start_pos=start_pos)

NONTERMINALS["@Break"] = BreakParser()

class ImportParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('import-standard')
        return source.p(ImportNode(), start_pos=start_pos)

NONTERMINALS["@Import"] = ImportParser()


class PassParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('pass')
        return source.p(PassNode(), start_pos=start_pos)
    
NONTERMINALS["@Pass"] = PassParser()

class ReturnParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('return-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        expr_node = parse("@Expression", source, pc, avoid_backtrack=avoid_backtrack)
        source.try_match('return-end', lskip_ws=True, avoid_backtrack = avoid_backtrack)
        return source.p(ReturnNode(expr_node), start_pos=start_pos)
    
NONTERMINALS["@Return"] = ReturnParser()

class PrintExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('print-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        expr_node = parse("@Expression", source, pc, avoid_backtrack=avoid_backtrack)
        source.try_match('print-end', lskip_ws=True, avoid_backtrack = avoid_backtrack)
        return source.p(PrintExpressionNode(expr_node), start_pos=start_pos)

NONTERMINALS["@PrintExpression"] = PrintExpressionParser()

class RepeatParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('repeat-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        times_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('repeat-times', skip_ws=True, avoid_backtrack = avoid_backtrack)
        source.try_match('repeat-block', skip_ws=True, avoid_backtrack = avoid_backtrack)
        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        block_node = parse("@Block", source, pc, lskip_ws=True, avoid_backtrack=True)
        source.try_match('repeat-end', lskip_ws=True, avoid_backtrack = True)
        return source.p(RepeatNode(times_node, block_node), start_pos=start_pos)

NONTERMINALS["@Repeat"] = RepeatParser()

class IfParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('if-begin', skip_ws=True) # もし
        source.try_match('if-condition-begin', skip_ws=True) 
        avoid_backtrack = source.pos > start_pos
        left_node = parse("@Expression", source, pc, skip_ws=True, avoid_backtrack=avoid_backtrack)
        if isinstance(left_node, BinaryNode) and left_node.comparative:
            operator = left_node.operator
            right_node = left_node.right
            left_node = left_node.left
            pass
        else:
            operator = source.find_match('if-infix', ['==', '!=', '<=', '<', '>=', '>', 'notin', 'in'])
            if not operator:
                source.try_match('if-infix', skip_ws=True, avoid_backtrack=avoid_backtrack) # が
            right_node = parse("@Expression", source, pc, lskip_ws=True, skip_ws=True, avoid_backtrack=avoid_backtrack)

            if not operator:
                operator = source.find_match('if-suffix', ['!=', '<=', '<', '>=', '>', 'notin', 'in'])
                source.skip_whitespaces_and_comments()
                if operator is None:
                    operator = "=="

        source.try_match('if-condition-end', lskip_ws=True, avoid_backtrack = avoid_backtrack) # )

        pc = pc.copy()
        pc['indent'] = source.capture_indent()

        source.try_match('if-then', lskip_ws=True, skip_linefeed=True, avoid_backtrack = True) # ならば                

        then_node = parse("@Block", source, pc, lskip_ws=True,avoid_backtrack=True)

        save_pos = source.pos
        source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.is_match('if-else', skip_linefeed=True):
            else_node = parse("@Block", source, pc, lskip_ws=True, avoid_backtrack=True)
        else:
            source.pos = save_pos
            else_node = None
        source.try_match('if-end', lskip_ws=True, avoid_backtrack = True)
        return source.p(IfNode(left_node, operator, right_node, then_node, else_node), start_pos=start_pos)

NONTERMINALS["@If"] = IfParser()

class FuncDefParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('funcdef-begin', skip_ws=True) # もし
        source.try_match('funcdef-name-begin', skip_ws=True) #
        avoid_backtrack = source.pos > start_pos        
        name_node = parse("@Name", source, pc, skip_ws=True, avoid_backtrack=avoid_backtrack)
        source.try_match('funcdef-name-end', skip_ws=True, avoid_backtrack = avoid_backtrack) # =

        arguments = []
        if not source.is_match('funcdef-noarg', skip_ws=True): # 引数なし
            source.try_match('funcdef-args-begin', skip_ws=True, avoid_backtrack = avoid_backtrack) # ～ならば
            while not source.is_match('funcdef-args-end', unconsumed=True):
                arg_node = parse("@Name", source, pc, skip_ws=True, avoid_backtrack=True)
                arguments.append(arg_node)
                if source.is_match('funcdef-arg-separator', skip_ws=True):
                    continue
                break
            source.try_match('funcdef-args-end', skip_ws=True, avoid_backtrack = avoid_backtrack)

        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        source.try_match('funcdef-block', skip_ws=True, avoid_backtrack = True) # ならば
        body_node = parse("@Block", source, pc, lskip_ws=True, avoid_backtrack=True)
        source.try_match('funcdef-end', lskip_ws=True, avoid_backtrack = True)
        return source.p(FuncDefNode(name_node, arguments, body_node), start_pos=start_pos)

NONTERMINALS["@FuncDef"] = FuncDefParser()

class AssertParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('assert-begin', skip_ws=True)
        avoid_backtrack = source.pos > start_pos
        test_node = parse("@Expression", source, pc, avoid_backtrack=avoid_backtrack)
        source.try_match('assert-infix', lskip_ws=True, skip_ws=True, avoid_backtrack = avoid_backtrack)
        reference_node = parse("@Expression", source, pc, avoid_backtrack=avoid_backtrack)
        source.try_match('assert-end', lskip_ws=True, avoid_backtrack = avoid_backtrack)
        return source.p(AssertNode(test_node, reference_node), start_pos=start_pos)

NONTERMINALS["@Assert"] = AssertParser()

class BlockParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments(include_linefeed=True)
        saved_pos = source.pos
        # 単一ブロックを認めるか { statement }
        source.try_match("block-begin", skip_ws=True)
        if source.is_match('block-end'):
            return source.p(BlockNode([]), start_pos=saved_pos)
        
        statements = parse("@Statement[]", source, pc, skip_ws=True)
        if source.is_match('block-end'):
            return source.p(BlockNode(statements), start_pos=saved_pos)

        end_level_indent = pc.get('indent', '')
        while source.has_next():
            source.match_eos_or_linefeed()
            linestart_pos = source.pos
            if source.consume_string(end_level_indent): 
                if source.is_match('whitespace', skip_ws=True): # deeper end_level_indent
                    if source.is_match("block-end", unconsumed=True):
                        raise YuiError(("bad", "indent", f"☝️`{end_level_indent}`"), source.p(start_pos=linestart_pos, length=len(end_level_indent)), avoid_backtrack=True)
                    statements.extend(parse("@Statement[]", source, pc, skip_ws=True))
                    continue
                else: # end_level_indent reached
                    if source.is_match("linefeed", lskip_ws=True, unconsumed=True):
                        continue # ただの空行はブロックの終わりにしない
                    source.try_match("block-end", opening_pos=saved_pos, avoid_backtrack=True)
                    return source.p(BlockNode(statements), start_pos=saved_pos)
            if source.is_match("linefeed", lskip_ws=True, unconsumed=True):
                continue # ただの空行はブロックの終わりにしない              
            break
        #print('@@@', source.pos, source.source[source.pos:])
        if source.is_defined("block-end"):
            candidate = source.for_example("block-end")
            raise YuiError(("expected", "syntax", "closing", f"✅`{candidate}`"), source.p(start_pos=saved_pos), avoid_backtrack = True)
        return source.p(BlockNode(statements), start_pos=saved_pos)

NONTERMINALS["@Block"] = BlockParser()

class TopLevelParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments()
        saved_pos = source.pos
        statements = []
        while source.has_next():
            cur_pos = source.pos
            statements.extend(parse("@Statement[]", source, pc, skip_linefeed=True))
            if cur_pos == source.pos:
                #print('@@@', source.pos, saved_pos, source.source[source.pos:])
                break
            source.skip_whitespaces_and_comments()
        return source.p(BlockNode(statements, top_level=True), start_pos=saved_pos)

NONTERMINALS["@TopLevel"] = TopLevelParser()

STATEMENTS = [
    "@FuncDef",
    "@Assignment",
    "@Assert",
    "@If",
    "@Repeat",
    "@Break",
    "@Increment",
    "@Decrement",
    "@Append",
    "@Return",
    "@Import",
    "@Pass",
    "@PrintExpression",
]

class StatementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        #print(f'>>> {source.capture_line()}')
        for parser_name in STATEMENTS:
            source.pos = saved_pos # backtrack
            try:
                statement = parse(parser_name, source, pc)
                #print(f'🧪{parser_name} matched, {statement}')
                return statement
            except YuiError as e:
                #print(f'@{parser_name}, {saved_pos} < {e.error_node.pos}, error={e}')
                if e.avoid_backtrack:
                    raise e
                continue
        source.pos = saved_pos
        if source.is_match("statement-separator", lskip_ws=True, unconsumed=True) or source.match_eos_or_linefeed(lskip_ws=True, unconsumed=True):
            return source.p(PassNode(), start_pos=saved_pos)
        line = source.capture_line()
        raise YuiError(("bad", "statement", f"❌{line}"), source.p(length=1), avoid_backtrack=True)

NONTERMINALS["@Statement"] = StatementParser()

class StatementsParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        statements = [parse("@Statement", source, pc, skip_ws=True)]
        while source.is_match('statement-separator', if_undefined=False, skip_ws=True):
            while source.is_match('statement-separator', if_undefined=False, skip_ws=True):
                statements.append(parse("@Statement", source, pc, skip_ws=True))
        return statements

NONTERMINALS["@Statement[]"] = StatementsParser()

class YuiParser:
    def __init__(self, syntax: Union[str, dict]):
        self.syntax = syntax
        if isinstance(syntax, dict):
            self.terminals = syntax.copy()
        else:
            self.terminals = load_syntax(syntax)
        self.pc = {}
    
    def parse(self, source_code: str) -> ASTNode:
        source = Source(source_code, syntax=self.terminals)
        return parse("@TopLevel", source, {}, lskip_ws=True)


class CodingVisitor:
    def __init__(self, syntax: Union[str, dict] = 'yui'):
        self.buffer = []
        self.indent = 0
        if isinstance(syntax, dict):
            self.terminals = syntax.copy()
        else:
            self.terminals = load_syntax(syntax)
    
    def emit(self, node: ASTNode) -> str:
        self.buffer = []
        self.indent = 0
        node.visit(self)
        return ''.join(self.buffer)

    def is_defined(self, terminal: str) -> bool:
        return self.terminals.get(terminal, "") != ""

    def print(self, text: str):
        if len(text) == 0:
            return
        if text == " " and len(self.buffer) > 0 and self.buffer[-1][-1] == ' ':
            return
        self.buffer.append(text)
    
    def linefeed(self, ignore = False):
        if not ignore:
            self.buffer.append('\n' + '   ' * self.indent)

    def word_segment(self, always=False, no_space_last_chars=' \n([{'):
        if always or self.is_defined('word-segmenter'):
            if len(self.buffer) > 0:
                last_char = self.buffer[-1][-1]
                if not self.is_defined('word-segmenter') and ord(last_char) > 127:
                    return # 日本語向けのアドホック 
                if last_char not in no_space_last_chars:
                    self.buffer.append(' ')

    def terminal(self, terminal: str, if_undefined = None, linefeed_before=False):
        pattern = None
        if terminal == 'linefeed':
            self.linefeed()
            return
        if self.is_defined(terminal):
            pattern = self.terminals[terminal]
        elif if_undefined is not None:
            pattern = if_undefined
        if pattern: 
            token = get_example_from_pattern(pattern)
            if token == "": return
            if token[0] not in ",()[]{}:\"'.":
                self.word_segment()
            if linefeed_before:
                self.linefeed()
            self.buffer.append(token)

    def comment(self, comment: str):
        if comment:
            comment = comment.splitlines()[0]
            if self.is_defined('line-comment-begin'):
                self.terminal('line-comment-begin')
                self.print(comment)
                return
            if self.is_defined('comment-begin') and self.is_defined('comment-end'):
                self.terminal('comment-begin')
                self.print(comment)
                self.terminal('comment-end')

    def expression(self, node: ASTNode):
        self.word_segment(always=True)
        node.visit(self)

    def push_statement(self, node: ASTNode):
        node.visit(self)
        self.comment(node.comment)

    def block(self, node: ASTNode):
        if not isinstance(node, BlockNode):
            BlockNode([node]).visit(self)
        else:
            node.visit(self)

    def visitASTNode(self, node: ASTNode):
        self.print(f'FIXME: {node.__class__.__name__}')

    def visitNumberNode(self, node: NumberNode):
        self.terminal("number-begin")
        self.print(str(node.value))
        self.terminal("number-end")

    def visitStringNode(self, node: StringNode):
        self.terminal('string-begin', if_undefined=r'"')
        if isinstance(node.contents,str):
            self.print(node.contents.replace('"', '\\"').replace('\n', '\\n'))
        else:
            for content in node.contents:
                if isinstance(content, str):
                    self.print(content.replace('"', '\\"').replace('\n', '\\n'))
                else:
                    self.terminal('string-interpolation-begin', if_undefined=r"\{")
                    content.visit(self)
                    self.terminal('string-interpolation-end', if_undefined=r"\}")
        self.terminal('string-end', if_undefined=r'"')
    
    def visitNameNode(self, node: NameNode):
        self.terminal("name-begin")
        self.print(node.name)
        self.terminal("name-end")

    def visitArrayNode(self, node: ArrayNode):
        self.terminal('array-begin', if_undefined=r'\[')
        for i, element in enumerate(node.elements):
            if i > 0:
                self.terminal('array-separator', if_undefined=r'\,')
            self.expression(element)
        self.terminal('array-end', if_undefined=r'\]')

    def visitObjectNode(self, node: ObjectNode):
        ignore_linefeed = "\n" not in str(node)
        self.terminal('object-begin', if_undefined=r'\{')
        self.indent += 1
        self.linefeed(ignore=ignore_linefeed)
        for i in range(0, len(node.elements), 2):
            if i > 0:
                self.terminal('object-separator', if_undefined=r'\,')
                self.linefeed(ignore=ignore_linefeed)
            key_node = node.elements[i]
            value_node = node.elements[i+1]
            self.expression(key_node)
            self.terminal('key-value-separator', if_undefined=r'\:')
            self.expression(value_node)
        self.indent -= 1
        self.linefeed(ignore=ignore_linefeed)
        self.terminal('object-end', if_undefined=r'\}')

    def visitMinusNode(self, node: MinusNode):
        if self.is_defined('minus-begin'):
            self.terminal('minus-begin')
            self.expression(node.element)
            self.terminal('minus-end')
        elif self.is_defined('unary-'):
            self.terminal('unary-')
            node.element.visit(self) # avoid extra word segmenter for negative numbers
        else:
            self.visitASTNode(node)

    def visitBinaryNode(self, node: BinaryNode):
        self.expression(node.left_node)
        self.word_segment()
        # 演算子をそのまま出力（*, /, %, +, -, ==, != など）
        self.terminal(f"binary{node.operator}", if_undefined=node.operator)
        self.word_segment()
        self.expression(node.right_node)

    def visitArrayLenNode(self, node: ArrayLenNode):
        if self.is_defined('property-length'):
            self.expression(node.element)
            self.terminal('property-accessor')
            self.terminal('property-length')
            return
        if self.is_defined('length-begin'):
            self.terminal('length-begin')
            node.element.visit(self)
            self.terminal('length-end')

    def visitGetIndexNode(self, node: GetIndexNode):
        self.terminal('array-indexer-begin')
        self.expression(node.collection)
        self.terminal('array-indexer-suffix')
        self.expression(node.index_node)
        self.terminal('array-indexer-end')
    
    def visitFuncAppNode(self, node: FuncAppNode):
        self.terminal('funcapp-begin')
        self.expression(node.name_node)
        self.terminal('funcapp-suffix', if_undefined=r'\(')
        for i, arg in enumerate(node.arguments):
            if i > 0:
                self.terminal('funcapp-separator', if_undefined=r'\,')
            self.expression(arg)
        self.terminal('funcapp-end', if_undefined=r'\)')

    def visitAssignmentNode(self, node: AssignmentNode):
        self.terminal('assignment-begin')
        self.expression(node.variable)
        self.terminal('assignment-infix')
        self.expression(node.expression)
        self.terminal('assignment-end')
    
    def visitIncrementNode(self, node: IncrementNode):
        self.terminal('increment-begin')
        self.expression(node.variable)
        self.terminal('increment-infix')
        self.terminal('increment-end')

    def visitDecrementNode(self, node: DecrementNode):
        self.terminal('decrement-begin')
        self.expression(node.variable)
        self.terminal('decrement-infix')
        self.terminal('decrement-end')

    def visitAppendNode(self, node: AppendNode):
        self.terminal('append-begin')
        self.expression(node.variable)
        self.terminal('append-infix')
        self.expression(node.expression)
        self.terminal('append-suffix')
        self.terminal('append-end')

    def visitBreakNode(self, node: BreakNode):
        self.terminal('break')
    
    def visitPassNode(self, node: PassNode):
        # block 内で処理される
        # self.terminal('pass')
        pass

    def visitReturnNode(self, node: ReturnNode):
        if isinstance(node.expression, ASTNode):
            self.terminal('return-begin')
            self.expression(node.expression)
            self.terminal('return-end')
        else:
            self.terminal('return-none')
        
    def visitPrintExpressionNode(self, node: PrintExpressionNode):
        if node.groping:
            self.terminal('groping-begin', if_undefined=r"\(")
            self.expression(node.expression)
            self.terminal('groping-end', if_undefined=r"\)")
        elif node.inspection and self.is_defined('unary-inspection'):
            self.terminal('unary-inspection')
            self.expression(node.expression)
        else:
            self.terminal('print-begin')
            self.expression(node.expression)
            self.terminal('print-end')

    def visitIfNode(self, node: IfNode):
        self.terminal('if-begin')
        self.terminal('if-condition-begin')
        self.expression(node.left)
        if isinstance(node.left, BinaryNode) and node.left.comparative:
            pass
        else:
            if self.is_defined(f'if-infix{node.operator}'):
                self.terminal(f'if-infix{node.operator}')
            else:
                self.terminal('if-infix')
            self.expression(node.right)
            if self.is_defined(f'if-suffix{node.operator}'):
                self.terminal(f'if-suffix{node.operator}')
            else:
                self.terminal('if-suffix')
            self.terminal('if-condition-end')
        self.terminal('if-then')
        self.block(node.then_block)
        if node.else_block:
            if self.is_defined('if-else-if') and isinstance(node.else_block, IfNode):
                self.terminal('if-else-if', linefeed_before=True)
                self.block(node.else_block)
            else:
                self.terminal('if-else', linefeed_before=True)
                self.block(node.else_block)
        self.terminal('if-end', linefeed_before=True)

    def visitRepeatNode(self, node: RepeatNode):
        self.terminal('repeat-begin')
        self.expression(node.count_node)
        self.terminal('repeat-times')
        self.terminal('repeat-block')
        self.block(node.block_node)
        self.terminal('repeat-end', linefeed_before=True)

    def visitFuncDefNode(self, node: FuncDefNode):
        self.terminal('funcdef-begin')
        self.terminal('funcdef-name-begin')
        self.expression(node.name_node)
        self.terminal('funcdef-name-end')
        if self.is_defined('funcdef-noarg') and len(node.parameters) == 0:
            self.terminal('funcdef-noarg')
        else:
            self.terminal('funcdef-args-begin')
            for i, arg_node in enumerate(node.parameters):
                if i > 0:
                    self.terminal('funcdef-arg-separator')
                self.expression(arg_node)
            self.terminal('funcdef-args-end')
        self.terminal('funcdef-block')
        self.block(node.body)
        self.terminal('funcdef-end', linefeed_before=True)

    def visitAssertNode(self, node: AssertNode):
        self.terminal('assert-begin')
        self.expression(node.test)
        self.terminal('assert-infix')
        self.expression(node.reference)
        self.terminal('assert-end')

    def visitBlockNode(self, node: BlockNode):
        if not node.top_level:
            self.terminal('block-begin')
            self.indent += 1
            self.linefeed()

        if len(node.statements) == 0:
            self.terminal('pass')
        else: 
            for i, statement in enumerate(node.statements):
                if i > 0:
                    self.linefeed()
                statement.visit(self)
                self.terminal("block-separator")
                self.comment(statement.comment)

        if not node.top_level:
            self.indent -= 1
            self.terminal('block-end', linefeed_before=True)

set_from_outside(YuiParser, CodingVisitor)