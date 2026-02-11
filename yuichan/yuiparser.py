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
    YuiError, ASTNode,
    NameNode,
    StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode,
)

def load_syntax(filepath: Optional[str] = None) -> Dict[str, str]:
    """JSON文法ファイルから終端記号をロードする"""
    if filepath is None:
        filepath = "syntax-yui.json"

    if not os.path.exists(filepath):
        # デフォルト: yuichanフォルダのsyntax-yui.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, "syntax-yui.json")

    with open(filepath, 'r', encoding='utf-8') as f:
        terminals = json.load(f)
    return terminals

def get_first_match_string(pattern: str)-> str:
    """正規表現パターンから最初にマッチする文字列を取得する"""
    if "|" in pattern:
        pattern = pattern.replace("\\|", "▁/▁")
        pattern = pattern.split("|")[0].replace("▁/▁", "\\|")
    pattern = pattern.replace("\\]", "▁)▁")
    end_pos = pattern.find("]")
    if pattern.startswith("[") and end_pos != -1:
        head = pattern[:end_pos].replace("▁)▁", "\\]")
        if pattern[1] == "\\":
            head = pattern[1:3]
        else:
            head = pattern[1]
        remaining = pattern[end_pos+1:].replace("▁)▁", "\\]")
        if remaining.startswith("+"):
            remaining = remaining[1:]
        elif remaining.startswith("*") or remaining.startswith("?"):
            remaining = remaining[1:]
            head=""
        return get_first_match_string(head) + get_first_match_string(remaining)
    if pattern.startswith("\\"):
        if pattern[1] < 'A' or 'z' < pattern[1]:
            return pattern[1:]
    return pattern

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
    def __init__(self, source: str, filename: str = "main.yui", pos: int = 0, syntax_file = 'syntax-yui.json'):
        self.filename = filename
        self.source = source
        self.pos = pos
        self.length = len(source)
        self.terminals = load_syntax(syntax_file)
        self.memos = {}

    def load_syntax(self, syntax_file: Optional[str] = None):
        self.terminals = load_syntax(syntax_file)

    def update_syntax(self, **kwargs):
        self.terminals.update(kwargs)
    
    def p(self, node: ASTNode = None, 
          length: int = 0, 
          start_pos: int = None, end_pos: int = None) -> ASTNode:
        node = node or SourceNode()
        node.filename = self.filename
        node.source = self.source
        if length != 0:
            node.pos = self.pos
            node.end_pos = min(self.pos + length, self.length)
        elif start_pos is not None:
            node.pos = start_pos
            if end_pos is None:
                node.end_pos = self.pos
            else:
                node.end_pos = end_pos
        else:
            node.pos = max(self.pos-1, 0)
            node.end_pos = self.pos
        return node

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
                 unconsumed=False, skip_prefix_whitespace=False,
                 skip_whitespace = False, skip_linefeed=False, next_alpha=False):
        if isinstance(if_undefined, bool) and not self.is_defined(terminal):
            return if_undefined
        pattern = self.terminals.get(terminal, if_undefined if isinstance(if_undefined, str) else "")    
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
            self.terminals[terminal] = pattern
        saved_pos = self.pos    
        if skip_prefix_whitespace:
            self.skip_whitespaces_and_comments()
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            match_length = match_result.end() - match_result.start()
            if unconsumed:
                self.pos = saved_pos
                return True
            self.pos += match_length
            if skip_whitespace or skip_linefeed:
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
        return get_first_match_string(pattern.pattern)

    def try_match(self, terminal: str, if_undefined=True, unconsumed=False, 
              skip_whitespace = False, skip_linefeed=False, opening_pos: int = None, skip_prefix_whitespace=False):
        if self.is_match(terminal, if_undefined=if_undefined, unconsumed=unconsumed,
                         skip_whitespace=skip_whitespace, skip_linefeed=skip_linefeed,
                         skip_prefix_whitespace=skip_prefix_whitespace):
            return
        candidate = self.first_candidate(terminal)
        if opening_pos is not None:
            raise YuiError(("expected", "closing", f"`{candidate}`"), self.p(start_pos=opening_pos))
        snippet = self.source[self.pos:self.pos+10].split('\n')[0]
        raise YuiError(("expected", f"`{candidate}`", f"❌`{snippet}`",), self.p(length=1))

    def find_match(self, terminal: str, suffixes: List[str], skip_whitespace = False, skip_linefeed=False, skip_prefix_whitespace=False):
        for suffix in suffixes:
            key = f"{terminal}-{suffix}"
            if self.is_match(key, if_undefined=False, unconsumed=False, 
                             skip_whitespace=skip_whitespace, skip_linefeed=skip_linefeed,
                             skip_prefix_whitespace=skip_prefix_whitespace):
                return suffix
        return None

    def match_linefeed(self, unconsumed=False):
        return self.is_eos() or self.is_match("linefeed", unconsumed=unconsumed)

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
        # 行の先頭位置を探す
        while self.pos < self.length:
            char = self.source[self.pos]
            if char == '\n':
                return self.source[start_pos:self.pos]
            self.pos += 1
        return self.source[start_pos:]
    
    def get_memo(self, nonterminal: str, pos: int):
        return self.memos.get((nonterminal, pos), None) 
    
    def set_memo(self, nonterminal: str, pos: int, result: Any, new_pos: int):
        self.memos[(nonterminal, pos)] = (result, new_pos)

NONTERMINALS = {}

class ParserCombinator(object):

    def quick_check(self, source: Source) -> bool:
        return True
    
    def match(self, source: Source, pc: dict):
        return True

def parse(nonterminal: str, source: Source, pc: dict, skip_whitespace: bool = False, skip_linefeed: bool = False, skip_prefix_whitespace=False) -> Any:
    global NONTERMINALS
    patterns = NONTERMINALS[nonterminal]
    saved_pos = source.pos
    if skip_prefix_whitespace:
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
        if skip_whitespace or skip_linefeed:
            source.skip_whitespaces_and_comments(include_linefeed=skip_linefeed)
        return result
    else:
        saved_pos = source.pos
        raise YuiError(("undefined", f"`{nonterminal}`"), source.p(length=1))

def is_parsable(nonterminal: str, source: Source, pc: dict, skip_prefix_whitespace=False) -> bool:
    try:
        parse(nonterminal, source, pc, skip_prefix_whitespace=skip_prefix_whitespace)
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
                if source.is_match("string-interpolation-begin", skip_whitespace=True):
                    expression = parse("@Expression", source, pc, skip_whitespace=True)
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
            while not source.is_match("array-end", unconsumed=True):
                arguments.append(parse("@Expression", source, pc, skip_linefeed=True))
                if source.is_match("array-separator", skip_linefeed=True):
                    continue
                break
            if is_parsable("@Expression", source, pc):
                candidate = source.first_candidate("array-separator")
                raise YuiError(("expected", f"`{candidate}`"), source.p(length=1))
            source.try_match("array-end", opening_pos=opening_pos)
            return ArrayNode(arguments)
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
                arguments.append(parse("@String", source, pc, skip_whitespace=True))
                source.try_match("object-key-value-separator", skip_linefeed=True)
                arguments.append(parse("@Expression", source, pc, skip_whitespace=True))
                if source.is_match("object-separator", skip_linefeed=True):
                    continue
                break
            source.try_match("object-end", ifopening_pos=opening_pos)
            return source.p(ObjectNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", "object"), source.p(length=1))

NONTERMINALS["@Object"] = ObjectParser()

class NameParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("identifier-begin", if_undefined=r"[A-Za-z_]", unconsumed=True) or source.is_match("extra-identifier-begin", if_undefined=False)

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
        if source.is_match("group-begin", skip_whitespace=True):
            expression_node = parse("@Expression", source, pc, skip_whitespace=True)
            source.try_match("group-end", skip_whitespace=True, opening_pos=opening_pos)
            return expression_node
        if source.is_match("length-begin", skip_whitespace=True):
            expression_node = parse("@Expression", source, pc, skip_whitespace=True)
            source.try_match("length-end", skip_whitespace=True, opening_pos=opening_pos)
            return source.p(ArrayLenNode(expression_node), start_pos=opening_pos)
        for literal in LITERALS:
            if NONTERMINALS[literal].quick_check(source):
                return parse(literal, source, pc)
        return parse("@Name", source, pc)

NONTERMINALS["@Term"] = TermParser()

class PrimaryParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        if source.is_match('unary-minus', if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(MinusNode(node), start_pos=start_pos)
        node = parse("@Term", source, pc)
        while source.has_next():
            opening_pos = source.pos
            if source.is_match("funcapp-args-begin", if_undefined=r"\(", skip_linefeed=True):
                arguments = []
                while not source.is_match("funcapp-args-end", if_undefined=r"\)", skip_whitespace=True, unconsumed=True):
                    arguments.append(parse("@Expression", source, pc), skip_whitespace=True)
                    if source.is_match("funcapp-args-separator", if_undefined=r"\,", skip_linefeed=True):
                        continue
                    break
                source.try_match("funcapp-args-end", if_undefined=r"\)", skip_whitespace=True, opening_pos=opening_pos)
                node = source.p(FuncAppNode(node, arguments), start_pos=start_pos)
                continue
            if source.is_match("array-index-begin", skip_whitespace=True):
                index_node = parse("@Expression", source, pc, skip_whitespace=True)
                source.try_match("array-index-end", skip_whitespace=True, opening_pos=opening_pos)
                node = source.p(GetIndexNode(node, index_node), start_pos=start_pos)
                continue
            if source.is_match("property-accessor", if_undefined=False):
                if source.is_match("property-length", if_undefined=False):
                    node = source.p(ArrayLenNode(node), start_pos=start_pos)
                    continue
                if source.is_match("property-type", if_undefined=False):
                    ...
                raise YuiError(("expected", "property", "name"), source.p(start_pos=opening_pos))
            break
        return node
    
NONTERMINALS["@Primary"] = PrimaryParser()

class MultiplicativeParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Primary", source, pc, skip_whitespace=True)
        if source.is_match("binary-multiply", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Multiplicative", source, pc, skip_whitespace=True)
            return source.p(BinaryNode(left_node, "*", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        if source.is_match("binary-divide", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Multiplicative", source, pc, skip_whitespace=True)
            return source.p(BinaryNode(left_node, "/", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        if source.is_match("binary-modulo", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Multiplicative", source, pc, skip_whitespace=True)
            return source.p(BinaryNode(left_node, "%", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Multiplicative"] = MultiplicativeParser()

class AdditiveParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Multiplicative", source, pc, skip_whitespace=True)
        if source.is_match("binary-plus", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Additive", source, pc, skip_whitespace=True)
            return source.p(BinaryNode(left_node, "+", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        if source.is_match("binary-minus", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Additive", source, pc, skip_whitespace=True)
            return source.p(BinaryNode(left_node, "-", right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Additive"] = AdditiveParser()

class ComparativeParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        left_node = parse("@Additive", source, pc, skip_whitespace=True)
        operator_pos = source.pos
        if source.is_match("binary-compare", if_undefined=False, skip_linefeed=True):
            right_node = parse("@Additive", source, pc, skip_whitespace=True)
            operator = source.source[operator_pos:source.pos].strip()
            return source.p(BinaryNode(left_node, operator, right_node), start_pos=start_pos, end_pos=right_node.end_pos)
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Comparative"] = ComparativeParser()

class ExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        return parse("@Additive", source, pc, skip_whitespace=True)

NONTERMINALS["@Expression"] = ExpressionParser()

## Statement

class AssignmentParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('assignment-begin', skip_whitespace=True)
        left_node = parse("@Expression", source, pc, skip_whitespace=True)
        source.try_match('assignment-infix', skip_whitespace=True)
        right_node = parse("@Expression", source, pc)
        source.try_match('assignment-end', skip_prefix_whitespace=True)
        return source.p(AssignmentNode(left_node, right_node), start_pos=start_pos)
    
NONTERMINALS["@Assignment"] = AssignmentParser()

class IncrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('increment-begin', skip_whitespace=True)       
        lvalue_node = parse("@Expression", source, pc, skip_whitespace=True)
        source.try_match('increment-infix')
        try:
            value = parse("@Expression", source, pc, skip_prefix_whitespace=True)
        except YuiError:
            value = None
        source.try_match('increment-end', skip_prefix_whitespace=True)
        return source.p(IncrementNode(lvalue_node, value), start_pos=start_pos)

NONTERMINALS["@Increment"] = IncrementParser()

class DecrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('decrement-begin', skip_whitespace=True)
        lvalue_node = parse("@Expression", source, pc, skip_whitespace=True)
        source.try_match('decrement-infix')
        try:
            value = parse("@Expression", source, pc, skip_prefix_whitespace=True)
        except YuiError:
            value = None
        source.try_match('decrement-end', skip_prefix_whitespace=True)
        return source.p(DecrementNode(lvalue_node, value), start_pos=start_pos)

NONTERMINALS["@Decrement"] = DecrementParser()

class AppendParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('append-begin', skip_whitespace=True)
        lvalue_node = parse("@Expression", source, pc, skip_whitespace=True)
        source.try_match('append-infix', skip_whitespace=True)
        value = parse("@Expression", source, pc)
        source.try_match('append-suffix', skip_prefix_whitespace=True)
        source.try_match('append-end', skip_prefix_whitespace=True)
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
        source.try_match('return-begin', skip_whitespace=True)
        expr_node = parse("@Expression", source, pc)
        source.try_match('return-end', skip_prefix_whitespace=True)
        return source.p(ReturnNode(expr_node), start_pos=start_pos)
    
NONTERMINALS["@Return"] = ReturnParser()

class PrintExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('print-begin', skip_whitespace=True)
        expr_node = parse("@Expression", source, pc)
        source.try_match('print-end', skip_prefix1whitespace=True)
        return source.p(PrintExpressionNode(expr_node), start_pos=start_pos)

NONTERMINALS["@PrintExpression"] = PrintExpressionParser()

class RepeatParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('repeat-begin', skip_whitespace=True)
        times_node = parse("@Expression", source, pc, skip_whitespace=True)
        source.try_match('repeat-times', skip_whitespace=True)
        source.try_match('repeat-end', skip_whitespace=True)
        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        block_node = parse("@Block", source, pc)       
        return source.p(RepeatNode(times_node, block_node), start_pos=start_pos)

NONTERMINALS["@Repeat"] = RepeatParser()

class IfParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('if-begin', skip_whitespace=True) # もし
        source.try_match('if-condition-begin', skip_whitespace=True) # ～ならば
        left_node = parse("@Expression", source, pc, skip_whitespace=True)
        operator = source.find_match('if-infix', ['eq', 'ne', 'le', 'lt', 'ge', 'gt', 'in', 'not-in'])
        if not operator:
            source.try_match('if-infix', skip_whitespace=True) # が
        right_node = parse("@Expression", source, pc, skip_whitespace=True)

        if not operator:
            operator = source.find_match('if-suffix', ['ne', 'le', 'lt', 'ge', 'gt', 'in', 'not-in', 'eq'])
            source.skip_whitespaces_and_comments()
            if operator is None:
                operator = "eq"

        source.try_match('if-condition-end', skip_prefix_whitespace=True) # )

        pc = pc.copy()
        pc['indent'] = source.capture_indent()

        source.try_match('if-then', skip_linefeed=True) # ならば                

        then_node = parse("@Block", source, pc)

        save_pos = source.pos
        source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.try_match('if-else', skip_linefeed=True):
            else_node = parse("@Block", source, pc)
            return source.p(IfNode(left_node, right_node, operator, then_node, else_node), start_pos=start_pos)
        else:
            source.pos = save_pos
            return source.p(IfNode(left_node, right_node, operator, then_node), start_pos=start_pos)


class BlockParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments(include_linefeed=True)
        saved_pos = source.pos
        # 単一ブロックを認めるか { statement }
        source.try_match("block-begin", skip_whitespace=True)
        if source.is_match('block-end'):
            return source.p(BlockNode(), start_pos=saved_pos)
        
        statements = parse("@Statement[]", source, pc, skip_whitespace=True)
        if source.is_match('block-end'):
            return source.p(BlockNode(*statements), start_pos=saved_pos)

        end_level_indent = pc.get('indent', '')
        while source.has_next():
            source.match_linefeed()
            linestart_pos = source.pos
            if source.consume_string(end_level_indent): 
                if source.is_match('whitespace', skip_whitespace=True): # deeper end_level_indent
                    if source.is_match("block-end", unconsumed=True):
                        raise YuiError(("bad", "indent", f"☝️`{end_level_indent}`"), source.p(start_pos=linestart_pos, length=len(end_level_indent)))
                    statements.extend(parse("@Statement[]", source, pc, skip_whitespace=True))
                    continue
                else: # end_level_indent reached
                    source.try_match("block-end", opening_pos=saved_pos)
                    return source.p(BlockNode(*statements), start_pos=saved_pos)
            break
        #print('@@@', source.pos, source.source[source.pos:])
        if source.is_defined("block-end"):
            candidate = source.first_candidate("block-end")
            raise YuiError(("expected", "closing", candidate), source.p(start_pos=saved_pos))
        return source.p(BlockNode(*statements), start_pos=saved_pos)

NONTERMINALS["@Block"] = BlockParser()

class TopLevelParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments()
        saved_pos = source.pos
        statements = []
        while source.has_next():
            statements.extend(parse("@Statement[]", source, pc, skip_linefeed=True))
        return source.p(BlockNode(*statements), start_pos=saved_pos)

NONTERMINALS["@TopLevel"] = TopLevelParser()

STATEMENTS = [
    "@Assignment",
    "@Increment",
    "@Decrement",
    "@Append",
    "@Repeat",
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
        if source.is_match("statement-separator", unconsumed=True) or source.match_linefeed(unconsumed=True):
            return source.p(PassNode(), start_pos=saved_pos)
        raise YuiError(("bad", "statement"), source.p(length=1))

NONTERMINALS["@Statement"] = StatementParser()

class StatementsParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        statements = [parse("@Statement", source, pc, skip_whitespace=True)]
        while source.is_match('statement-separator', if_undefined=False, skip_whitespace=True):
            while source.is_match('statement-separator', if_undefined=False, skip_whitespace=True):
                statements.append(parse("@Statement", source, pc, skip_whitespace=True))
        return statements

NONTERMINALS["@Statement[]"] = StatementsParser()
