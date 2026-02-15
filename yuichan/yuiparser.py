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
    AssertNode,
)

def get_example_from_pattern(pattern: str) -> str:
    """正規表現パターンからそのパターンにマッチする文字列の例（最初の例）を取得する"""
    # エスケープされた文字を一時的に置換
    pattern = pattern.replace(r'\|', '▁｜▁') 
    pattern = pattern.replace(r'\[', '▁［▁') 
    pattern = pattern.replace(r'\]', '▁］▁') 
    pattern = pattern.replace(r'\*', '▁＊▁') 
    pattern = pattern.replace(r'\?', '▁？▁') 
    pattern = pattern.replace(r'\+', '▁＋▁')
    pattern = pattern.replace(r'+', '') # 
    pattern = pattern.replace(r'*', '?') #
    example = get_example_from_pattern_inner(pattern)
    # 置換した文字を元に戻す
    example = example.replace('▁｜▁', r'|')
    example = example.replace('▁［▁', r'[')
    example = example.replace('▁］▁', r']')
    example = example.replace('▁＊▁', r'*')
    example = example.replace('▁？▁', r'?')
    example = example.replace('▁＋▁', r'+')
    return example

def get_example_from_pattern_inner(pattern: str)-> str:
    if pattern == "":
        return ""
    # 選択肢（|）の処理：最初の選択肢を使用
    if "|" in pattern:
        pattern = pattern.split("|")[0]
    
    # 文字クラス [abc] の処理 
    if pattern.startswith("["):
        end_pos = pattern.find("]")
        head = pattern[1:end_pos]
        tail = pattern[end_pos+1:]
        if tail.startswith("?"):
            return get_example_from_pattern_inner(tail[1:])
        head_char = get_example_from_pattern_inner(head)[0]
        return head_char + get_example_from_pattern_inner(tail)
    if pattern.startswith("\\"):
        # エスケープシーケンスの処理
        next_char = pattern[1]
        remaining = pattern[2:]
        if remaining.startswith("?"):
            return get_example_from_pattern_inner(remaining[1:])
        if next_char == '\\':  # バックスラッシュ
            char = '\\'
        elif next_char == 's':  # 空白文字
            char = ' '
        elif next_char == 't':  # タブ
            char = '\t'
        elif next_char == 'n':  # 改行
            char = '\n'
        elif next_char == 'r':  # キャリッジリターン
            char = '\r'
        elif next_char == 'd':  # 数字
            char = '1'
        elif next_char == 'w':  # 単語文字
            char = 'a'
        else:
            char = next_char
        return char + get_example_from_pattern_inner(remaining)
    char = pattern[0]
    remaining = pattern[1:]
    if remaining.startswith("?"):
        return get_example_from_pattern_inner(remaining[1:])
    return char + get_example_from_pattern_inner(remaining)

def is_all_alnum(s: str) -> bool:
    for ch in s:
        if not (('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or (ch == '_')):
            return False
    return True

def load_syntax(filepath: Optional[str] = None) -> Dict[str, str]:
    """JSON文法ファイルから終端記号をロードする"""
    if filepath is None:
        filepath = "syntax-yui.json"

    if not os.path.exists(filepath):
        # デフォルト: yuichanフォルダのsyntax-yui.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, filepath)

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
    """
    null値（?）を表すノード
    """
    def __init__(self):
        super().__init__()

    def evaluate(self, runtime):
        return 0

class Source(object):
    """ソースコード"""
    def __init__(self, source: str, filename: str = "main.yui", pos: int = 0, syntax = 'syntax-yui.json'):
        self.filename = filename
        self.source = source
        self.pos = pos
        self.length = len(source)
        if isinstance(syntax, dict):
            self.terminals = syntax.copy()
        else:
            self.terminals = load_syntax(syntax)
        self.memos = {}

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

    def is_match(self, terminal: str, if_undefined:Union[bool, str]=False, 
                 unconsumed=False, lskip_ws=False,
                 skip_ws = False, skip_linefeed=False, next_alpha=False):
        if isinstance(if_undefined, bool) and not self.is_defined(terminal):
            return if_undefined
        pattern = self.terminals.get(terminal, if_undefined if isinstance(if_undefined, str) else "")    
        if isinstance(pattern, str):
            try:
                pattern = re.compile(pattern)
            except re.error:
                raise ValueError(f"Invalid regex pattern for terminal '{terminal}': {pattern}")
        saved_pos = self.pos    
        if lskip_ws:
            self.skip_whitespaces_and_comments()
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
    
    def first_candidate(self, terminal: str) -> str:
        pattern = self.terminals.get(terminal, "")
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
            self.terminals[terminal] = pattern
        return get_example_from_pattern(pattern.pattern)

    def try_match(self, terminal: str, if_undefined=True, unconsumed=False, 
              skip_ws = False, skip_linefeed=False, opening_pos: int = None, lskip_ws=False):
        if self.is_match(terminal, if_undefined=if_undefined, unconsumed=unconsumed,
                         skip_ws=skip_ws, skip_linefeed=skip_linefeed,
                         lskip_ws=lskip_ws):
            return
        candidate = self.first_candidate(terminal)
        snippet = self.source[self.pos:self.pos+10].replace('\n', '\\n')
        if opening_pos is not None:
            raise YuiError(("expected", "closing", f"`{candidate}`", f"❌`{snippet}`"), self.p(start_pos=opening_pos))
        raise YuiError(("expected", f"`{candidate}`", f"❌`{snippet}`"), self.p(length=1))

    def find_match(self, terminal: str, suffixes: List[str], skip_ws = False, skip_linefeed=False, lskip_ws=False):
        for suffix in suffixes:
            key = f"{terminal}-{suffix}"
            if self.is_match(key, if_undefined=False, unconsumed=False, 
                             skip_ws=skip_ws, skip_linefeed=skip_linefeed, lskip_ws=lskip_ws):
                return suffix
        return None

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

def parse(nonterminal: str, source: Source, pc: dict, skip_ws: bool = False, skip_linefeed: bool = False, lskip_ws=False) -> Any:
    global NONTERMINALS
    patterns = NONTERMINALS[nonterminal]
    saved_pos = source.pos
    if lskip_ws:
        source.skip_whitespaces_and_comments()
    if isinstance(patterns, ParserCombinator):
        memo = source.get_memo(nonterminal, source.pos)
        if memo is not None:
            source.pos = memo[1]
            result = memo[0]
        else:
            saved_pos = source.pos
            result = patterns.match(source, pc)
            source.set_memo(nonterminal, saved_pos, result, source.pos)
        if skip_ws or skip_linefeed:
            source.skip_whitespaces_and_comments(include_linefeed=skip_linefeed)
        return result
    else:
        saved_pos = source.pos
        raise YuiError(("undefined", f"`{nonterminal}`"), source.p(length=1))

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
        return source.is_match("number-begin", if_undefined=r"[0-9]", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        if source.is_match("number-begin", if_undefined=r"[0-9]"):
            source.try_match("number-chars", if_undefined=r"[0-9]")
            if source.is_match("number-dot-char", if_undefined=r"\."):
                source.try_match("number-begin")
                source.try_match("number-chars")
                number = source.source[saved_pos:source.pos]
                return source.p(NumberNode(float(number)), start_pos=saved_pos)
            else:
                number = source.source[saved_pos:source.pos]
            return source.p(NumberNode(int(number)), start_pos=saved_pos)
        raise YuiError(("expected", "number"), source.p(length=1))

NONTERMINALS["@Number"] = NumberParser()

class StringParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("string-begin", if_undefined=r'"', unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("string-begin", if_undefined=r'"'):
            string_content = []
            expression_count = 0
            while source.pos < source.length:
                source.consume_until("string-content-end", until_eof=True)
                string_content.append(source.source[opening_pos:source.pos])
                if source.is_match("string-end"):
                    if expression_count == 0:
                        string_content = ''.join(string_content)
                    return source.p(StringNode(string_content), start_pos=opening_pos)
                if source.is_match("string-escape"):
                    if source.is_eos():
                        raise YuiError(("bad", "escape sequence"), source.p(length=1))
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
                    expression = parse("@Expression", source, pc, skip_ws=True)
                    source.try_match("string-interpolation-end", opening_pos=start_inter_pos)
                    string_content.append(expression)
                    expression_count += 1
                    continue
            candidate = source.first_candidate("string-end")
            raise YuiError(("expected", "closing", f"`{candidate}`"), source.p(start_pos=opening_pos))
        raise YuiError(("expected", "string"), source.p(length=1))

NONTERMINALS["@String"] = StringParser()

class ArrayParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("array-begin", if_undefined=r"\[", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("array-begin", if_undefined=r"\[", skip_linefeed=True):
            arguments = []
            while not source.is_match("array-end", if_undefined=r"\]", unconsumed=True):
                arguments.append(parse("@Expression", source, pc, skip_linefeed=True))
                if source.is_match("array-end", if_undefined=r"\]"):
                    return source.p(ArrayNode(arguments), start_pos=opening_pos)
                if source.is_match("array-separator", skip_linefeed=True):
                    continue
                break
            if is_parsable("@Expression", source, pc):
                candidate = source.first_candidate("array-separator")
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
                arguments.append(parse("@String", source, pc, skip_linefeed=True))
                source.try_match("object-key-value-separator", if_undefined=r"\:", skip_linefeed=True)
                arguments.append(parse("@Expression", source, pc, skip_linefeed=True))
                if source.is_match("object-end", if_undefined=r"\}"):
                    return source.p(ObjectNode(arguments), start_pos=opening_pos)
                if source.is_match("object-separator", skip_linefeed=True):
                    continue
                break
            if is_parsable("@String", source, pc):
                candidate = source.first_candidate("object-separator")
                raise YuiError(("expected", f"`{candidate}`"), source.p(length=1))
            source.try_match("object-end", if_undefined=r"\}", opening_pos=opening_pos)
            return source.p(ObjectNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", "object"), source.p(length=1))

NONTERMINALS["@Object"] = ObjectParser()

class NameParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        if source.is_defined("keywords"):
            for keyword in source.terminals["keywords"]:
                if source.is_match(keyword, if_undefined=False, unconsumed=True):
                    return False
        return source.is_match("identifier-begin", if_undefined=r"[A-Za-z_]", unconsumed=True) or source.is_match("extra-identifier-begin", if_undefined=True, unconsumed=True)

    def match(self, source: Source, pc: dict):
        if source.is_match("extra-identifier-begin", if_undefined=False):
            start_pos = source.pos
            source.consume_until("extra-identifier-end", disallow_string="\n")
            name = source.source[start_pos:source.pos]
            node = source.p(NameNode(name), start_pos=start_pos)
            source.try_match("extra-identifier-end", opening_pos=start_pos-1)
            return node
        start_pos = source.pos
        if source.is_match("identifier-begin", if_undefined=r"[A-Za-z_]"):
            source.try_match("identifier-chars", if_undefined=r"[A-Za-z0-9_]*")
            source.try_match("identifier-end", if_undefined=True)
            name = source.source[start_pos:source.pos]
            return source.p(NameNode(name), start_pos=start_pos)
        raise YuiError(("expected", "identifier"), source.p(length=1))

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
            expression_node = parse("@Expression", source, pc, skip_ws=True)
            source.try_match("group-end", skip_ws=True, opening_pos=opening_pos)
            return expression_node
        if source.is_match("length-begin", skip_ws=True):
            expression_node = parse("@Expression", source, pc, skip_ws=True)
            source.try_match("length-end", skip_ws=True, opening_pos=opening_pos)
            return source.p(ArrayLenNode(expression_node), start_pos=opening_pos)
        for literal in LITERALS:
            if NONTERMINALS[literal].quick_check(source):
                return parse(literal, source, pc)
        return parse("@Name", source, pc)

NONTERMINALS["@Term"] = TermParser()

class PrimaryParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        if source.is_match('unary-', if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(MinusNode(node), start_pos=start_pos)
        if source.is_match('unary-inspection', if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(PrintExpressionNode(node, inspection=True), start_pos=start_pos)
        node = parse("@Term", source, pc)
        while source.has_next():
            opening_pos = source.pos
            if source.is_match("funcapp-args-begin", if_undefined=r"\(", skip_linefeed=True):
                arguments = []
                while not source.is_match("funcapp-args-end", if_undefined=r"\)", skip_ws=True, unconsumed=True):
                    arguments.append(parse("@Expression", source, pc, skip_ws=True))
                    if source.is_match("funcapp-args-separator", if_undefined=r"\,", skip_linefeed=True):
                        continue
                    break
                source.try_match("funcapp-args-end", if_undefined=r"\)", skip_ws=True, opening_pos=opening_pos)
                node = source.p(FuncAppNode(node, arguments), start_pos=start_pos)
                continue
            if source.is_match("array-index-begin", skip_ws=True):
                index_node = parse("@Expression", source, pc, skip_ws=True)
                source.try_match("array-index-end", skip_ws=True, opening_pos=opening_pos)
                node = source.p(GetIndexNode(node, index_node), start_pos=start_pos)
                continue
            if source.is_match("property-accessor", if_undefined=False):
                if source.is_match("property-length", if_undefined=False):
                    node = source.p(ArrayLenNode(node), start_pos=start_pos)
                    continue
                if source.is_match("property-type", if_undefined=False):
                    ...
                if source.is_match("not-property-name", if_undefined=False, unconsumed=True):
                    # python .append()のようなとき、エラーを避ける
                    source.pos = opening_pos # backtrack
                    return node
                try:
                    property_name = str(parse("@Name", source, pc))
                    raise YuiError(("bad", "property", "name", property_name), source.p(length=len(property_name)))
                except YuiError:
                    source.pos = opening_pos # backtrack
                    snippet = source.capture_line()[:10]
                    raise YuiError(("expected", "property", "name", f"❌{snippet}"), source.p(start_pos=opening_pos))
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
                return source.p(BinaryNode(left_node, "*", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary/", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "/", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary%", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "%", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
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
                return source.p(BinaryNode(left_node, "+", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary-", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "-", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
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
                return source.p(BinaryNode(left_node, "==", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary!=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "!=", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary<=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<=", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary>=", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">=", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary<", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binary>", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binaryin", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "in", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
            if source.is_match("binarynotin", if_undefined=False, lskip_ws=True, skip_linefeed=True):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "notin", right_node, comparative=True), start_pos=start_pos, end_pos=right_node.end_pos)
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
        left_node = parse("@Expression", source, pc, skip_ws=True)
        source.try_match('assignment-infix', skip_ws=True)
        right_node = parse("@Expression", source, pc)
        source.try_match('assignment-end', lskip_ws=True)
        return source.p(AssignmentNode(left_node, right_node), start_pos=start_pos)
    
NONTERMINALS["@Assignment"] = AssignmentParser()

class IncrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('increment-begin', skip_ws=True)       
        lvalue_node = parse("@Expression", source, pc, skip_ws=True)
        source.try_match('increment-infix', lskip_ws=True)
        source.try_match('increment-end', lskip_ws=True)
        return source.p(IncrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Increment"] = IncrementParser()

class DecrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('decrement-begin', skip_ws=True)
        lvalue_node = parse("@Expression", source, pc, skip_ws=True)
        source.try_match('decrement-infix', lskip_ws=True)
        source.try_match('decrement-end', lskip_ws=True)
        return source.p(DecrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Decrement"] = DecrementParser()

class AppendParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('append-begin', skip_ws=True)
        lvalue_node = parse("@Expression", source, pc, skip_ws=True)
        source.try_match('append-infix', skip_ws=True)
        value = parse("@Expression", source, pc)
        source.try_match('append-suffix', lskip_ws=True)
        source.try_match('append-end', lskip_ws=True)
        return source.p(AppendNode(lvalue_node, value), start_pos=start_pos)

NONTERMINALS["@Append"] = AppendParser()

class BreakParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('break')
        return source.p(BreakNode(), start_pos=start_pos)
    
NONTERMINALS["@Break"] = BreakParser()

class ReturnParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('return-begin', skip_ws=True)
        expr_node = parse("@Expression", source, pc)
        source.try_match('return-end', lskip_ws=True)
        return source.p(ReturnNode(expr_node), start_pos=start_pos)
    
NONTERMINALS["@Return"] = ReturnParser()

class PrintExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('print-begin', skip_ws=True)
        expr_node = parse("@Expression", source, pc)
        source.try_match('print-end', lskip_ws=True)
        return source.p(PrintExpressionNode(expr_node), start_pos=start_pos)

NONTERMINALS["@PrintExpression"] = PrintExpressionParser()

class RepeatParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('repeat-begin', skip_ws=True)
        times_node = parse("@Expression", source, pc, skip_ws=True)
        source.try_match('repeat-times', skip_ws=True)
        source.try_match('repeat-block', skip_ws=True)
        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        block_node = parse("@Block", source, pc)     
        source.try_match('repeat-end', lskip_ws=True)
        return source.p(RepeatNode(times_node, block_node), start_pos=start_pos)

NONTERMINALS["@Repeat"] = RepeatParser()

class IfParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('if-begin', skip_ws=True) # もし
        source.try_match('if-condition-begin', skip_ws=True) # ～ならば

        left_node = parse("@Expression", source, pc, skip_ws=True)
        if isinstance(left_node, BinaryNode) and left_node.comparative:
            operator = left_node.operator
            right_node = left_node.right
            left_node = left_node.left
            pass
        else:
            operator = source.find_match('if-infix', ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin'])
            if not operator:
                source.try_match('if-infix', skip_ws=True) # が
            right_node = parse("@Expression", source, pc, skip_ws=True)

            if not operator:
                operator = source.find_match('if-suffix', ['!=', '<', '<=', '>', '>=', 'in', 'notin'])
                source.skip_whitespaces_and_comments()
                if operator is None:
                    operator = "=="

        source.try_match('if-condition-end', lskip_ws=True) # )

        pc = pc.copy()
        pc['indent'] = source.capture_indent()

        source.try_match('if-then', skip_linefeed=True) # ならば                

        then_node = parse("@Block", source, pc)

        save_pos = source.pos
        source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.is_match('if-else', skip_linefeed=True):
            else_node = parse("@Block", source, pc)
        else:
            source.pos = save_pos
            else_node = None
        source.try_match('if-end', lskip_ws=True)
        return source.p(IfNode(left_node, operator, right_node, then_node, else_node), start_pos=start_pos)

NONTERMINALS["@If"] = IfParser()

class FuncDefParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('funcdef-begin', skip_ws=True) # もし
        source.try_match('funcdef-name-begin', skip_ws=True) # ～ならば
        name_node = parse("@Name", source, pc, skip_ws=True)
        source.try_match('funcdef-name-end', skip_ws=True) # =

        source.try_match('funcdef-args-begin', skip_ws=True) # ～ならば

        arguments = []
        if not source.is_match('funcdef-noarg', unconsumed=True): 
            while not source.is_match('funcdef-args-end', unconsumed=True):
                arg_node = parse("@Name", source, pc, skip_ws=True)
                arguments.append(arg_node)
                if source.is_match('funcdef-arg-separator', skip_ws=True):
                    continue
                break
            source.try_match('funcdef-args-end', skip_ws=True)

        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        source.try_match('funcdef-block', skip_ws=True) 
        body_node = parse("@Block", source, pc)
        source.try_match('funcdef-end', lskip_ws=True)
        return source.p(FuncDefNode(name_node, arguments, body_node), start_pos=start_pos)

NONTERMINALS["@FuncDef"] = FuncDefParser()


class AssertParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('assert-begin', skip_ws=True)
        test_node = parse("@Expression", source, pc)
        source.try_match('assert-infix', skip_ws=True)
        reference_node = parse("@Expression", source, pc)
        source.try_match('assert-end', lskip_ws=True)
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
                        raise YuiError(("bad", "indent", f"☝️`{end_level_indent}`"), source.p(start_pos=linestart_pos, length=len(end_level_indent)))
                    statements.extend(parse("@Statement[]", source, pc, skip_ws=True))
                    continue
                else: # end_level_indent reached
                    source.try_match("block-end", opening_pos=saved_pos)
                    return source.p(BlockNode(statements), start_pos=saved_pos)
            break
        #print('@@@', source.pos, source.source[source.pos:])
        if source.is_defined("block-end"):
            candidate = source.first_candidate("block-end")
            raise YuiError(("expected", "closing", candidate), source.p(start_pos=saved_pos))
        return source.p(BlockNode(statements), start_pos=saved_pos)

NONTERMINALS["@Block"] = BlockParser()

class TopLevelParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments()
        saved_pos = source.pos
        statements = []
        while source.has_next():
            statements.extend(parse("@Statement[]", source, pc, skip_linefeed=True))
        return source.p(BlockNode(statements, top_level=True), start_pos=saved_pos)

NONTERMINALS["@TopLevel"] = TopLevelParser()

STATEMENTS = [
    "@FuncDef",
    "@Assignment",
    "@Assert",
    "@If",
    "@Repeat",
    "@Increment",
    "@Decrement",
    "@Append",
    "@Return",
    "@PrintExpression",
]

class StatementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        for parser_name in STATEMENTS:
            source.pos = saved_pos # backtrack
            try:
                return parse(parser_name, source, pc)
            except YuiError as e:
                continue
        source.pos = saved_pos
        if source.is_match("statement-separator", lskip_ws=True, unconsumed=True) or source.match_eos_or_linefeed(lskip_ws=True, unconsumed=True):
            return source.p(PassNode(), start_pos=saved_pos)
        line = source.capture_line()
        raise YuiError(("bad", "statement", f"❌{line}"), source.p(length=1))

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
    def __init__(self, syntax: Union[str, dict] = 'yui_syntax.json'):
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
    
    def push_linefeed(self, ignore = False):
        if not ignore:
            self.buffer.append('\n' + '   ' * self.indent)

    def push_word_segmenter(self, always=False):
        if always or self.is_defined('word-segmenter'):
            if len(self.buffer) > 0:
                last_char = self.buffer[-1][-1]
                if last_char != ' ' and last_char != '\n':
                    self.buffer.append(' ')

    def push(self, terminal: str, if_undefined = None, push_linefeed_before=False):
        pattern = None
        if terminal == 'linefeed':
            self.push_linefeed()
            return
        if self.is_defined(terminal):
            pattern = self.terminals[terminal]
        elif if_undefined is not None:
            pattern = if_undefined
        if pattern: 
            token = get_example_from_pattern(pattern)
            if token == "": return
            if token[0] not in ",()[]{}:\"'.":
                self.push_word_segmenter()
            if push_linefeed_before:
                self.push_linefeed()
            self.buffer.append(token)

    def push_comment(self, comment: str):
        if comment:
            comment = comment.splitlines()[0]
            if self.is_defined('line-comment-begin'):
                self.push('line-comment-begin')
                self.print(comment)
                return
            if self.is_defined('comment-begin') and self.is_defined('comment-end'):
                self.push('comment-begin')
                self.print(comment)
                self.push('comment-end')

    def push_expression(self, node: ASTNode):
        self.push_word_segmenter(always=True)
        node.visit(self)

    def push_statement(self, node: ASTNode):
        node.visit(self)
        self.push_comment(node.comment)

    def push_block(self, node: ASTNode):
        if not isinstance(node, BlockNode):
            BlockNode([node]).visit(self)
        else:
            node.visit(self)

    def visitASTNode(self, node: ASTNode):
        self.print(f'FIXME: {node.__class__.__name__}')

    def visitNumberNode(self, node: NumberNode):
        self.print(str(node.value))

    def visitStringNode(self, node: StringNode):
        self.push('string-begin', if_undefined=r'"')
        if isinstance(node.contents,str):
            self.print(node.contents.replace('"', '\\"').replace('\n', '\\n'))
        else:
            for content in node.contents:
                if isinstance(content, str):
                    self.print(content.replace('"', '\\"').replace('\n', '\\n'))
                else:
                    self.push('string-interpolation-begin', if_undefined=r"\{")
                    content.visit(self)
                    self.push('string-interpolation-end', if_undefined=r"\}")
        self.push('string-end', if_undefined=r'"')
    
    def visitNameNode(self, node: NameNode):
        self.print(node.name)

    def visitArrayNode(self, node: ArrayNode):
        self.push('array-begin', if_undefined=r'\[')
        for i, element in enumerate(node.elements):
            if i > 0:
                self.push('array-separator', if_undefined=r'\,')
            self.push_expression(element)
        self.push('array-end', if_undefined=r'\]')

    def visitObjectNode(self, node: ObjectNode):
        ignore_linefeed = "\n" not in str(node)
        self.push('object-begin', if_undefined=r'\{')
        self.indent += 1
        self.push_linefeed(ignore=ignore_linefeed)
        for i in range(0, len(node.elements), 2):
            if i > 0:
                self.push('object-separator', if_undefined=r'\,')
                self.push_linefeed(ignore=ignore_linefeed)
            key_node = node.elements[i]
            value_node = node.elements[i+1]
            self.push_expression(key_node)
            self.push('key-value-separator', if_undefined=r'\:')
            self.push_expression(value_node)
        self.indent -= 1
        self.push_linefeed(ignore=ignore_linefeed)
        self.push('object-end', if_undefined=r'\}')

    def visitMinusNode(self, node: MinusNode):
        if self.is_defined('unary-'):
            self.push('unary-')
            node.element.visit(self) # avoid extra word segmenter for negative numbers

    def visitBinaryNode(self, node: BinaryNode):
        self.push_expression(node.left_node)
        self.push_word_segmenter()
        # 演算子をそのまま出力（*, /, %, +, -, ==, != など）
        self.push(f"binary{node.operator}", if_undefined=node.operator)
        self.push_word_segmenter()
        self.push_expression(node.right_node)

    def visitArrayLenNode(self, node: ArrayLenNode):
        if self.is_defined('property-length'):
            self.push_expression(node.element)
            self.push('property-accessor')
            self.push('property-length')
            return
        if self.is_defined('length-begin'):
            self.push('length-begin')
            node.element.visit(self)
            self.push('length-end')

    def visitGetIndexNode(self, node: GetIndexNode):
        node.collection.visit(self)
        self.push('array-index-begin')
        node.index_node.visit(self)
        self.push('array-index-end')
    
    def visitFuncAppNode(self, node: FuncAppNode):
        node.name_node.visit(self)
        self.push('funcapp-begin', if_undefined=r'\(')
        for i, arg in enumerate(node.arguments):
            if i > 0:
                self.push('funcapp-separator', if_undefined=r'\,')
            arg.visit(self)
        self.push('funcapp-end', if_undefined=r'\)')

    def visitAssignmentNode(self, node: AssignmentNode):
        self.push('assignment-begin')
        node.variable.visit(self)
        self.push('assignment-infix')
        node.expression.visit(self)
        self.push('assignment-end')
    
    def visitIncrementNode(self, node: IncrementNode):
        self.push('increment-begin')
        self.push_expression(node.variable)
        self.push('increment-infix')
        if isinstance(node.expression, ASTNode):
            self.push_expression(node.expression)
        self.push('increment-end')

    def visitDecrementNode(self, node: DecrementNode):
        self.push('decrement-begin')
        self.push_expression(node.variable)
        self.push('decrement-infix')
        if isinstance(node.expression, ASTNode):
            self.push_expression(node.expression)
        self.push('decrement-end')

    def visitAppendNode(self, node: AppendNode):
        self.push('append-begin')
        self.push_expression(node.variable)
        self.push('append-infix')
        self.push_expression(node.expression)
        self.push('append-suffix')
        self.push('append-end')

    def visitBreakNode(self, node: BreakNode):
        self.push('break')
    
    def visitPassNode(self, node: PassNode):
        # block 内で処理される
        # self.push('pass')
        pass

    def visitReturnNode(self, node: ReturnNode):
        if isinstance(node.expression, ASTNode):
            self.push('return-begin')
            self.push_expression(node.expression)
            self.push('return-end')
        else:
            self.push('return-none')
        
    def visitPrintExpressionNode(self, node: PrintExpressionNode):
        if node.groping:
            self.push('groping-begin', if_undefined=r"\(")
            self.push_expression(node.expression)
            self.push('groping-end', if_undefined=r"\)")
            return
        if node.inspection and self.is_defined('unary-inspection'):
            self.push('unary-inspection')
            self.push_expression(node.expression)
            return
        self.push('print-begin')
        self.push_expression(node.expression)
        self.push('print-end')

    def visitIfNode(self, node: IfNode):
        self.push('if-begin')
        self.push('if-condition-begin')
        self.push_expression(node.left)
        if isinstance(node.left, BinaryNode) and node.left.comparative:
            pass
        else:
            if self.is_defined(f'if-infix{node.operator}'):
                self.push(f'if-infix{node.operator}')
            else:
                self.push('if-infix')
            self.push_expression(node.right)
            if self.is_defined(f'if-suffix{node.operator}'):
                self.push(f'if-suffix{node.operator}')
            else:
                self.push('if-suffix')
            self.push('if-condition-end')
        self.push('if-then')
        self.push_block(node.then_block)
        if node.else_block:
            if self.is_defined('if-else-if') and isinstance(node.else_block, IfNode):
                self.push('if-else-if', push_linefeed_before=True)
                self.push_block(node.else_block)
            else:
                self.push('if-else', push_linefeed_before=True)
                self.push_block(node.else_block)
        self.push('if-end', push_linefeed_before=True)

    def visitRepeatNode(self, node: RepeatNode):
        self.push('repeat-begin')
        self.push_expression(node.count_node)
        self.push('repeat-times')
        self.push('repeat-block')
        self.push_block(node.block_node)
        self.push('repeat-end', push_linefeed_before=True)

    def visitFuncDefNode(self, node: FuncDefNode):
        self.push('funcdef-begin')
        self.push('funcdef-name-begin')
        self.push_expression(node.name_node)
        self.push('funcdef-name-end')
        if self.is_defined('funcdef-noarg') and len(node.parameters) == 0:
            self.push('funcdef-noarg')
        else:
            self.push('funcdef-args-begin')
            for i, arg_node in enumerate(node.parameters):
                if i > 0:
                    self.push('funcdef-arg-separator')
                self.push_expression(arg_node)
            self.push('funcdef-args-end')
        self.push('funcdef-block')
        self.push_block(node.body)
        self.push('funcdef-end', push_linefeed_before=True)

    def visitAssertNode(self, node: AssertNode):
        self.push('assert-begin')
        self.push_expression(node.test)
        self.push('assert-infix')
        self.push_expression(node.reference)
        self.push('assert-end')

    def visitBlockNode(self, node: BlockNode):
        if not node.top_level:
            self.push('block-begin')
            self.indent += 1
            self.push_linefeed()

        if len(node.statements) == 0:
            self.push('pass')
        else: 
            for i, statement in enumerate(node.statements):
                if i > 0:
                    self.push_linefeed()
                statement.visit(self)
                self.push_comment(statement.comment)

        if not node.top_level:
            self.indent -= 1
            self.push('block-end', push_linefeed_before=True)

set_from_outside(YuiParser, CodingVisitor)