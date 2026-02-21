# Source
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
import re

from .yuiast import (
    ASTNode,
    ConstNode, NameNode, StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, ImportNode,
)

from .yuitypes import YuiValue, YuiType, YuiError
from .yuisyntax import YuiSyntax, load_syntax

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

@dataclass
class SourceNode(ASTNode):
    """null値（?）を表すノード"""
    def __init__(self):
        super().__init__()

class Source(YuiSyntax):
    """ソースコード"""
    def __init__(self, source: str, filename: str = "main.yui", pos: int = 0, syntax = 'yui'):
        terminals = load_syntax(syntax) if isinstance(syntax, str) else syntax
        super().__init__(terminals)
        self.filename = filename
        self.source = source
        self.pos = pos
        self.length = len(source)
        self.special_names = []
        self.add_special_names(extract_identifiers(source))      
        self.memos = {}
        # self.backtrack = True
    
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
    
    def matched_string(self, terminal: str) -> Optional[str]:
        pattern = self.get_pattern(terminal)
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            return match_result.group(0)
        return ''

    def is_match(self, terminal: str, if_undefined:Union[bool, str]=False, unconsumed=False, lskip_ws=True, lskip_lf=False):
        if isinstance(if_undefined, bool) and not self.is_defined(terminal):
            return if_undefined
        if terminal.startswith('!'): # よくある間違いを検出
            wrong_terminal = f"!{terminal}"
            if self.is_defined(wrong_terminal) and self.is_match(wrong_terminal, unconsumed=True, lskip_ws=lskip_ws):
                expected = self.for_example(terminal)
                matched = self.matched_string(wrong_terminal)
                raise YuiError(("wrong", "token", f"❌`{matched}`", f"✅`{expected}`"), self.p(length=1))
        saved_pos = self.pos    
        if lskip_ws or lskip_lf:
            self.skip_whitespaces_and_comments(include_linefeed=lskip_lf)
        pattern = self.get_pattern(terminal, if_undefined=if_undefined if isinstance(if_undefined, str) else "")
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            match_length = match_result.end() - match_result.start()
            if unconsumed:
                self.pos = saved_pos
                return True
            self.pos += match_length
            return True
        self.pos = saved_pos
        return False
    
    def try_match(self, terminal: str, if_undefined=True, unconsumed=False, 
                  BK=False, lskip_ws=True, lskip_lf=False, opening_pos: int = None):
        if self.is_match(terminal, if_undefined=if_undefined, unconsumed=unconsumed, lskip_ws=lskip_ws, lskip_lf=lskip_lf):
            return
        expected_token = self.for_example(terminal)
        if opening_pos is not None:
            raise YuiError(("expected", "closing", f"✅`{expected_token}`"), self.p(start_pos=opening_pos))
        snippet = self.capture_line()
        raise YuiError(("expected", "token", f"✅`{expected_token}`", f"❌`{snippet}`", f"🔍{terminal}"), self.p(length=1), BK=BK)

    def find_match(self, terminal: str, suffixes: List[str], lskip_lf=False) -> Optional[str]:
        for suffix in suffixes:
            key = f"{terminal}{suffix}"
            if self.is_match(key, if_undefined=False, unconsumed=False, lskip_ws=True, lskip_lf=lskip_lf):
                return suffix
        return None

    def can_backtrack(self, lookahead: List[str]) -> bool:
        if self.is_defined(lookahead):
            pattern = self.get_pattern(lookahead)
            captured = self.capture_line()
            return not pattern.search(captured)
        return True

    def is_eos_or_linefeed(self, lskip_ws=True, unconsumed=False):
        saved_pos = self.pos    
        if lskip_ws:
            self.skip_whitespaces_and_comments(include_linefeed=False)
        if self.is_eos():
            if unconsumed:
                self.pos = saved_pos
            return True
        return self.is_match("linefeed", lskip_ws=False, lskip_lf=False, unconsumed=unconsumed)

    def consume_until(self, terminal:str, until_eof=True, disallow_string:str=None):
        pattern = self.get_pattern(terminal)
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
            if self.is_match("whitespaces", lskip_ws=False):
                continue
            if include_linefeed and self.is_match("linefeed", lskip_ws=False):
                continue
            if self.is_match("line-comment-begin", if_undefined=False, lskip_ws=False):
                self.consume_until("linefeed", until_eof=True)
                continue
            if self.is_defined("comment-begin") and self.is_defined("comment-end"):
                opening_pos = self.pos
                if self.is_match("comment-begin", lskip_ws=False):
                    self.consume_until("comment-end", until_eof=True)
                    self.try_match("comment-end", lskip_ws=False, opening_pos=opening_pos)
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
            if self.is_match("linefeed", lskip_ws=False, unconsumed=True) or \
                 self.is_match("line-comment-begin", lskip_ws=False, unconsumed=True) or \
                self.is_match("comment-begin", lskip_ws=False, unconsumed=True) or \
                self.is_match("statement-separator", lskip_ws=False, unconsumed=True):
                captured = self.source[start_pos:self.pos]
                self.pos = start_pos
                return captured
            self.pos += 1
        self.pos = start_pos
        return self.source[start_pos:].split('\n')[0]

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

    def p(self, node: ASTNode = None, start_pos: int = None, end_pos: int = None, length: int = 0) -> ASTNode:
        node = node or SourceNode()
        node.filename = self.filename
        node.source = self.source
        ### FIXME: node.comment = self.capture_comment()

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

def parse(nonterminal: str, source: Source, pc: dict, lskip_ws=True, lskip_lf=False, BK=False) -> Any:
    global NONTERMINALS
    patterns = NONTERMINALS[nonterminal]
    saved_pos = source.pos
    if lskip_ws or lskip_lf:
        source.skip_whitespaces_and_comments(include_linefeed=lskip_lf)
    
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
            #print(f"@fail {nonterminal} BK={e.BK} {e}")
            if e.BK == True and BK == False:
                source.pos = saved_pos
                snippet = source.capture_line()
                raise YuiError(("expected", nonterminal[1:].lower(), f"❌{snippet}", f"⚠️{e}"), source.p(length=1))
            raise e
    return result

def is_parsable(nonterminal: str, source: Source, pc: dict, lskip_ws=True, lskip_lf=False) -> bool:
    try:
        parse(nonterminal, source, pc, lskip_ws=lskip_ws, lskip_lf=lskip_lf)
        return True
    except YuiError:
        return False

class ConstParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("null", if_undefined=False) or \
            source.is_match("boolean-true", if_undefined=False) or \
            source.is_match("boolean-false", if_undefined=False)

    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        if source.is_match("null", if_undefined=False):
            return source.p(ConstNode(None), start_pos=saved_pos)
        if source.is_match("boolean-true", if_undefined=False):
            return source.p(ConstNode(True), start_pos=saved_pos)
        if source.is_match("boolean-false", if_undefined=False):
            return source.p(ConstNode(False), start_pos=saved_pos)
        raise YuiError(("expected", "null or boolean"), source.p(length=1), BK=True)

NONTERMINALS["@Boolean"] = ConstParser()

class NumberParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("number-first-char", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        if source.is_match("number-first-char"):
            source.try_match("number-chars", lskip_ws=False)
            if source.is_match("number-dot-char", lskip_ws=False):
                source.try_match("number-first-char", lskip_ws=False)
                source.try_match("number-chars", lskip_ws=False)
                number = source.source[saved_pos:source.pos]
                return source.p(NumberNode(float(number)), start_pos=saved_pos)
            else:
                number = source.source[saved_pos:source.pos]
            return source.p(NumberNode(int(number)), start_pos=saved_pos)
        raise YuiError(("expected", "number"), source.p(length=1), BK=True)

NONTERMINALS["@Number"] = NumberParser()

class StringParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("string-begin", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_quote_pos = source.pos
        if source.is_match("string-begin"):
            opening_pos = source.pos
            string_content = []
            expression_count = 0
            while source.pos < source.length:
                source.consume_until("string-content-end", until_eof=True)
                string_content.append(source.source[opening_pos:source.pos])
                if source.is_match("string-end", unconsumed=True):
                    break
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
                if source.is_match("string-interpolation-begin", lskip_ws=False):
                    expression = parse("@Expression", source, pc)
                    source.try_match("string-interpolation-end", opening_pos=start_inter_pos)
                    string_content.append(expression)
                    expression_count += 1
                    continue
            source.try_match("string-end", lskip_ws=False, opening_pos=opening_quote_pos)
            if expression_count == 0:
                string_content = ''.join(string_content)
            return source.p(StringNode(string_content), start_pos=opening_quote_pos)
        raise YuiError(("expected", "string"), source.p(length=1), BK=True)

NONTERMINALS["@String"] = StringParser()

class ArrayParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_match("array-begin", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("array-begin"):
            arguments = []
            while not source.is_match("array-end", lskip_lf=True, unconsumed=True):
                arguments.append(parse("@Expression", source, pc, lskip_lf=True))
                if source.is_match("array-separator", lskip_lf=True):
                    continue
            source.try_match("array-end", lskip_lf=True, opening_pos=opening_pos)
            return source.p(ArrayNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", "array"), source.p(length=1), BK=True)

NONTERMINALS["@Array"] = ArrayParser()

class ObjectParser(ParserCombinator):
    def quick_check(self, source: Source) -> bool:
        return source.is_match("object-begin", unconsumed=True)
    
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("object-begin", lskip_lf=True):
            arguments = []
            while not source.is_match("object-end", lskip_lf=True, unconsumed=True):
                arguments.append(parse("@String", source, pc, lskip_lf=True))
                source.try_match("key-value-separator", lskip_lf=True)
                arguments.append(parse("@Expression", source, pc, lskip_lf=True))
                if source.is_match("object-separator", lskip_lf=True):
                    continue
            source.try_match("object-end", lskip_lf=True, opening_pos=opening_pos)
            return source.p(ObjectNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected", "object"), source.p(length=1), BK=True)

NONTERMINALS["@Object"] = ObjectParser()

class NameParser(ParserCombinator):

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
        if source.is_match("name-first-char"):
            source.try_match("name-chars", lskip_ws=False)
            source.try_match("name-end", lskip_ws=False)
            name = source.source[start_pos:source.pos]
            return source.p(NameNode(name), start_pos=start_pos)
        snippet = source.capture_line().strip()
        raise YuiError(("wrong", "name", f"❌{snippet}"), source.p(length=1), BK=True)

NONTERMINALS["@Name"] = NameParser()

LITERALS = ["@Number","@String","@Array","@Object","@Boolean"]

class TermParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        opening_pos = source.pos
        if source.is_match("grouping-begin"):
            expression_node = parse("@Expression", source, pc)
            source.try_match("grouping-end", opening_pos=opening_pos)
            return expression_node
        if source.is_match("length-begin"):
            expression_node = parse("@Expression", source, pc)
            source.try_match("length-end", opening_pos=opening_pos)
            return source.p(ArrayLenNode(expression_node), start_pos=opening_pos)
        for literal in LITERALS:
            if NONTERMINALS[literal].quick_check(source):
                source.pos = opening_pos
                return parse(literal, source, pc, BK=True)
        return parse("@Name", source, pc, BK=True)

NONTERMINALS["@Term"] = TermParser()

class PrimaryParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        if source.is_match("unary-minus", if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(MinusNode(node), start_pos=start_pos)
        if source.is_match('unary-inspection', if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(PrintExpressionNode(node, inspection=True), start_pos=start_pos)
        if source.is_match('unary-length', if_undefined=False):
            node = parse('@Primary', source, pc)
            return source.p(ArrayLenNode(node), start_pos=start_pos)
        node = parse("@Term", source, pc, BK=True)
        while source.has_next():
            opening_pos = source.pos
            if source.is_match("funcapp-args-suffix"):
                arguments = []
                while not source.is_match("funcapp-args-end", unconsumed=True):
                    arguments.append(parse("@Expression", source, pc, lskip_lf=True))
                    if source.is_match("funcapp-args-separator"):
                        continue
                    #break
                source.try_match("funcapp-args-end", opening_pos=opening_pos)
                node = source.p(FuncAppNode(node, arguments), start_pos=start_pos)
                continue
            if source.is_match("array-indexer-suffix", if_undefined=r"\["):
                index_node = parse("@Expression", source, pc)
                source.try_match("array-indexer-end", opening_pos=opening_pos)
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
        left_node = parse("@Primary", source, pc, BK=True)
        try:
            if source.is_match("binary*", if_undefined=False):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "*", right_node), start_pos=start_pos)
            if source.is_match("binary/", if_undefined=False):
                right_node = parse("@Multiplicative", source, pc)
                return source.p(BinaryNode(left_node, "/", right_node), start_pos=start_pos)
            if source.is_match("binary%", if_undefined=False):
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
        left_node = parse("@Multiplicative", source, pc, BK=True)
        try:
            if source.is_match("binary+", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "+", right_node), start_pos=start_pos)
            if source.is_match("binary-", if_undefined=False):
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
        left_node = parse("@Additive", source, pc, BK=True)
        try:
            if source.is_match("binary==", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "==", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary!=", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "!=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary<=", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary>=", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">=", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary<", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "<", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binary>", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, ">", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binaryin", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "in", right_node, comparative=True), start_pos=start_pos)
            if source.is_match("binarynotin", if_undefined=False):
                right_node = parse("@Additive", source, pc)
                return source.p(BinaryNode(left_node, "notin", right_node, comparative=True), start_pos=start_pos)
        except YuiError:
            pass
        source.pos = left_node.end_pos
        return left_node

NONTERMINALS["@Comparative"] = ComparativeParser()

class ExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        return parse("@Comparative", source, pc, BK=True)

NONTERMINALS["@Expression"] = ExpressionParser()

## Statement

class AssignmentParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('assignment-lookahead')
        start_pos = source.pos
        source.try_match('assignment-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        left_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('assignment-infix', BK=BK)
        right_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('assignment-end', BK=BK) # E E 代入もありえる
        return source.p(AssignmentNode(left_node, right_node), start_pos=start_pos)
    
NONTERMINALS["@Assignment"] = AssignmentParser()

class IncrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('increment-lookahead')
        start_pos = source.pos
        source.try_match('increment-begin', BK=BK)
        if BK: BK = source.pos == start_pos

        lvalue_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('increment-infix', BK=BK)
        source.try_match('increment-end', BK=BK)
        return source.p(IncrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Increment"] = IncrementParser()

class DecrementParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('decrement-lookahead')
        start_pos = source.pos
        source.try_match('decrement-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        lvalue_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('decrement-infix', BK=BK)
        source.try_match('decrement-end', BK=BK)
        return source.p(DecrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Decrement"] = DecrementParser()

class AppendParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('append-lookahead')
        start_pos = source.pos
        source.try_match('append-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        lvalue_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('append-infix', BK=BK)
        value = parse("@Expression", source, pc, BK=BK)
        source.try_match('append-suffix', BK=BK)
        source.try_match('append-end', BK=BK)
        return source.p(AppendNode(lvalue_node, value), start_pos=start_pos)

NONTERMINALS["@Append"] = AppendParser()

class BreakParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('break', BK=True)
        return source.p(BreakNode(), start_pos=start_pos)

NONTERMINALS["@Break"] = BreakParser()

class ImportParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('import-standard', BK=True)
        return source.p(ImportNode(), start_pos=start_pos)

NONTERMINALS["@Import"] = ImportParser()


class PassParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        source.try_match('pass', BK=True)
        return source.p(PassNode(), start_pos=start_pos)
    
NONTERMINALS["@Pass"] = PassParser()

class ReturnParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('return-lookahead')
        start_pos = source.pos
        source.try_match('return-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        expr_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('return-end', BK=BK)
        return source.p(ReturnNode(expr_node), start_pos=start_pos)
    
NONTERMINALS["@Return"] = ReturnParser()

class PrintExpressionParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('print-lookahead')
        start_pos = source.pos
        source.try_match('print-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        expr_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('print-end', BK=BK)
        return source.p(PrintExpressionNode(expr_node), start_pos=start_pos)

NONTERMINALS["@PrintExpression"] = PrintExpressionParser()

class RepeatParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('repeat-lookahead')
        start_pos = source.pos
        source.try_match('repeat-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        times_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('repeat-times', BK=BK)
        source.try_match('repeat-block', BK=BK)
        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        block_node = parse("@Block", source, pc)
        source.try_match('repeat-end', BK=False)
        return source.p(RepeatNode(times_node, block_node), start_pos=start_pos)

NONTERMINALS["@Repeat"] = RepeatParser()

class IfParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        BK = source.can_backtrack('if-lookahead')
        source.try_match('if-begin', BK=BK) # もし
        source.try_match('if-condition-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        left_node = parse("@Expression", source, pc, BK=BK)
        if isinstance(left_node, BinaryNode) and left_node.comparative:
            operator = left_node.operator
            right_node = left_node.right
            left_node = left_node.left
        else:
            operator = source.find_match('if-infix', ['==', '!=', '<=', '<', '>=', '>', 'notin', 'in'])
            if not operator:
                source.try_match('if-infix', BK=BK) # が
            right_node = parse("@Expression", source, pc, BK=BK)
            
            if not operator:
                operator = source.find_match('if-suffix', ['!=', '<=', '<', '>=', '>', 'notin', 'in', '=='])
                source.skip_whitespaces_and_comments()
                if operator is None:
                    operator = "=="

        source.try_match('if-condition-end', BK=BK) # )

        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        source.try_match('if-then', BK=False) # ならば                

        then_node = parse("@Block", source, pc, BK=False)

        save_pos = source.pos
        source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.is_match('if-else'):
            else_node = parse("@Block", source, pc, BK=False)
        else:
            source.pos = save_pos
            else_node = None
        source.try_match('if-end', BK=False)
        return source.p(IfNode(left_node, operator, right_node, then_node, else_node), start_pos=start_pos)

NONTERMINALS["@If"] = IfParser()

class FuncDefParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        BK = source.can_backtrack('funcdef-lookahead')
        start_pos = source.pos
        source.try_match('funcdef-begin', BK=BK) # もし
        source.try_match('funcdef-name-begin', BK=BK) #
        if BK: BK = source.pos == start_pos
        name_node = parse("@Name", source, pc, BK=BK)
        source.try_match('funcdef-name-end', BK=BK) # =

        arguments = []
        if not source.is_match('funcdef-noarg'): # 引数なし
            source.try_match('funcdef-args-begin', BK=BK) # 入力
            while not source.is_match('funcdef-args-end', unconsumed=True):
                arg_node = parse("@Name", source, pc)
                arguments.append(arg_node)
                if source.is_match('funcdef-arg-separator'):
                    continue
                break
            source.try_match('funcdef-args-end', BK=False)

        pc = pc.copy()
        pc['indent'] = source.capture_indent()
        source.try_match('funcdef-block', BK=BK) # に対し
        body_node = parse("@Block", source, pc, BK=False)
        source.try_match('funcdef-end', BK=False)
        return source.p(FuncDefNode(name_node, arguments, body_node), start_pos=start_pos)

NONTERMINALS["@FuncDef"] = FuncDefParser()

class AssertParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        start_pos = source.pos
        BK = source.can_backtrack('assert-lookahead')
        source.try_match('assert-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        test_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('assert-infix', BK=BK)
        reference_node = parse("@Expression", source, pc, BK=BK)
        source.try_match('assert-end', BK=BK)
        return source.p(AssertNode(test_node, reference_node), start_pos=start_pos)

NONTERMINALS["@Assert"] = AssertParser()

class BlockParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        saved_pos = source.pos
        source.try_match("block-begin")
        if source.is_match('block-end'): # 単一ブロックを認めるか { statement }
            return source.p(BlockNode([]), start_pos=saved_pos)
        
        statements = parse("@Statement[]", source, pc)
        if source.is_match('block-end'):
            return source.p(BlockNode(statements), start_pos=saved_pos)

        end_level_indent = pc.get('indent', '')
        #print(f"@Block in indent='{len(end_level_indent)}'", source.pos, source.capture_line())
        while source.has_next():
            source.is_eos_or_linefeed()
            linestart_pos = source.pos
            if source.consume_string(end_level_indent): 
                if source.is_match('whitespace', lskip_ws=False): # deeper end_level_indent
                    if source.is_match("block-end", unconsumed=True):
                        raise YuiError(("wrong", "indent", f"✅`{end_level_indent}`"), source.p(start_pos=linestart_pos, length=len(end_level_indent)))
                    #print('>>>', source.pos, source.capture_line())
                    statements.extend(parse("@Statement[]", source, pc))
                    #print('<<<', source.pos, source.capture_line())
                    continue
            if source.is_match("linefeed", unconsumed=True):
                continue # ただの空行はブロックの終わりにしない              
            break
        source.try_match("block-end", opening_pos=saved_pos)
        return source.p(BlockNode(statements), start_pos=saved_pos)

NONTERMINALS["@Block"] = BlockParser()

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
        #print("@Statement", source.pos, source.capture_line())
        for parser_name in STATEMENTS:
            source.pos = saved_pos # for backtrack
            try:
                statement = parse(parser_name, source, pc, BK=True)
                return statement
            except YuiError as e:
                if e.BK: continue
                raise e
        source.pos = saved_pos
        line = source.capture_line()
        raise YuiError(("wrong", "statement", f"❌{line}"), source.p(length=1))

NONTERMINALS["@Statement"] = StatementParser()

class StatementsParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        if source.is_eos_or_linefeed(lskip_ws=True, unconsumed=True):
            statements = []
        else:
            statements = [parse("@Statement", source, pc)]
        while source.is_match('statement-separator', if_undefined=False):
            statements.append(parse("@Statement", source, pc))
        return statements

NONTERMINALS["@Statement[]"] = StatementsParser()

class TopLevelParser(ParserCombinator):
    def match(self, source: Source, pc: dict):
        source.skip_whitespaces_and_comments(include_linefeed=True)
        saved_pos = source.pos
        statements = []
        while source.has_next():
            cur_pos = source.pos
            statements.extend(parse("@Statement[]", source, pc))
            if cur_pos == source.pos:                
                break
            source.skip_whitespaces_and_comments(include_linefeed=True)
        return source.p(BlockNode(statements, top_level=True), start_pos=saved_pos)

NONTERMINALS["@TopLevel"] = TopLevelParser()

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
        return parse("@TopLevel", source, {})

