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
    AssertNode, CatchNode, ImportNode,
)

from .yuitypes import YuiValue, YuiType, YuiError, vprint
from .yuisyntax import YuiSyntax, load_syntax


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
        self.extract_special_names(source)
        self.current_indent = ""     
        self.memos = {}
    
    def has_next(self):
        return self.pos < self.length

    def is_eos(self):
        return self.pos >= self.length

    def consume_string(self, text: str):
        if self.source.startswith(text, self.pos):
            self.pos += len(text)
            return True
        return False
    
    def match_(self, terminal: str, if_undefined=False, unconsumed=False, start_pos: int = None, check_typo=True):
        if not self.is_defined(terminal):
            if start_pos is not None:
                self.pos = start_pos  # 未定義のターミナルでも ws スキップ前の位置に戻す
            return if_undefined
        saved_pos = self.pos if start_pos is None else start_pos
        if check_typo and self.is_defined(f"!{terminal}"):
            pattern = self.get_pattern(f"!{terminal}")
            match_result = pattern.match(self.source, self.pos)
            if match_result:
                matched = self.source[self.pos:match_result.end()]
                expected = self.for_example(terminal)
                raise YuiError(("typo", f"❌`{matched}`", f"✅{expected}", f"🧬{terminal}"), self.p(length=len(matched)))
        pattern = self.get_pattern(terminal)
        match_result = pattern.match(self.source, self.pos)
        if match_result:
            self.matched_string = self.source[self.pos:match_result.end()]
            if unconsumed:
                self.pos = saved_pos
                return True
            self.pos = match_result.end()
            return True
        self.matched_string = ""
        self.pos = saved_pos
        return False

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
            if self.match_("whitespace", check_typo=False):
                continue
            if include_linefeed and self.match_("linefeed", check_typo=False):
                continue
            if self.match_("line-comment-begin"):
                self.consume_until("linefeed", until_eof=True)
                continue
            if self.match_("comment-begin"):
                opening_pos = self.pos - len(self.matched_string)
                self.consume_until("comment-end", until_eof=True)
                self.require_("comment-end", lskip_ws=False, opening_pos=opening_pos)
                continue
            break

    def is_eos_or_linefeed(self, lskip_ws=True, unconsumed=False):
        saved_pos = self.pos    
        if lskip_ws:
            self.skip_whitespaces_and_comments(include_linefeed=False)
        if self.is_eos():
            if unconsumed:
                self.pos = saved_pos
            return True
        return self.is_("linefeed", lskip_ws=False, lskip_lf=False, unconsumed=unconsumed)

    def is_(self, terminal: str, suffixes=None, if_undefined=False, unconsumed=False, lskip_ws=True, lskip_lf=False):
        start_pos = self.pos
        if lskip_ws or lskip_lf:
            self.skip_whitespaces_and_comments(include_linefeed=lskip_lf)
        if suffixes is not None:
            self.matched_suffix = None
            saved_pos = self.pos
            for suffix in suffixes:
                key = f"{terminal}{suffix}"
                if self.match_(key, unconsumed=unconsumed, start_pos=start_pos):
                    self.matched_suffix = suffix
                    return True
                self.pos = saved_pos
            self.pos = start_pos
            return False
        if '|' in terminal:
            for option in terminal.split('|'):
                if self.match_(option, if_undefined=if_undefined, unconsumed=unconsumed, start_pos=start_pos):
                    return True
            self.pos = start_pos
            return False
        return self.match_(terminal, if_undefined=if_undefined, unconsumed=unconsumed, start_pos=start_pos)

    def require_(self, terminal: str, suffixes=None, if_undefined=True, unconsumed=False, lskip_ws=True, lskip_lf=False, opening_pos: int = None, BK=False):
        if not self.is_defined(terminal):
            return
        if self.is_(terminal, suffixes=suffixes, if_undefined=if_undefined, unconsumed=unconsumed, lskip_ws=lskip_ws, lskip_lf=lskip_lf):
            return
        expected_token = self.for_example(terminal)
        if opening_pos is not None:
            raise YuiError(("expected-closing", f"✅`{expected_token}`"), self.p(start_pos=opening_pos))
        snippet = self.capture_line()
        raise YuiError(("expected-token", f"❌`{snippet}`", f"✅`{expected_token}`", f"🧬{terminal}"), self.p(length=1), BK=BK)

    def save(self):
        return (self.pos, self.current_indent)

    def backtrack(self, saved):
        self.pos, self.current_indent = saved

    def get_memo(self, nonterminal: str, pos: int):
        """Pakrat parsingのメモを取得する"""
        return self.memos.get((nonterminal, pos), None) 
    
    def set_memo(self, nonterminal: str, pos: int, result: Any, new_pos: int):
        """Pakrat parsingのメモを設定する"""
        self.memos[(nonterminal, pos)] = (result, new_pos)

    def parse(self, nonterminal: str, lskip_ws=True, lskip_lf=False, BK=False) -> Any:
        global NONTERMINALS
        patterns = NONTERMINALS[nonterminal]
        if lskip_ws or lskip_lf:
            self.skip_whitespaces_and_comments(include_linefeed=lskip_lf)
        
        memo = self.get_memo(nonterminal, self.pos)
        if memo is not None:
            result = memo[0]
            self.pos = memo[1]
            return result

        saved = self.save()
        try:
            saved_pos = self.pos
            result = patterns.match(self)
            self.set_memo(nonterminal, saved_pos, result, self.pos)
        except YuiError as e:
            #print(f"@fail {nonterminal} BK={e.BK} {e}")
            if e.BK == True and BK == False:
                self.backtrack(saved)
                snippet = self.capture_line()
                raise YuiError((f"expected-{nonterminal[1:].lower()}", f"❌{snippet}", f"⚠️{e}"), self.p(length=1))
            raise e
        return result

    def can_backtrack(self, lookahead: List[str]) -> bool:
        if self.is_defined(lookahead):
            pattern = self.get_pattern(lookahead)
            captured = self.capture_line()
            return not pattern.search(captured)
        return True

    def extract_special_names(self, text: str) -> List[str]:
        ...
        if self.is_defined("special-names"):
            names = self.terminals.get("special-names", "").split("|")
        else:
            names = []        
    
        name_pattern = self.terminals.get("special-name-pattern", r'[^\s\[\]\(\)",\.+*/%=!<>-]+')
        
        # 1. 変数定義のパターン（例: `name =` だが `==` は除外）
        var_pattern = self.terminals.get("special-name-variable", r'\n\s*({name_pattern})\s*=(?!=)')
        var_pattern = var_pattern.replace("{name_pattern}", name_pattern)
        matches1 = re.findall(var_pattern, text)
        names.extend(matches1)
        
        # 2. 関数名のパターン（例: `name(` ）
        funcapp_pattern = self.terminals.get("special-name-funcname", r'({name_pattern})\s*[\(]')
        funcapp_pattern = funcapp_pattern.replace("{name_pattern}", name_pattern)
        matches2 = re.findall(funcapp_pattern, text)
        names.extend(matches2)


        # Unicodeなど特殊な名前をあらかじめ抽出しておく（例: `λ` など）。ただし、英数字とアンダースコアのみで構成される名前は除外する。
        names = list(set(name.strip() for name in names if not _is_alnum(name) and name.strip() != ""))
        vprint(f"@extracted special names: {names}")  
        self.special_names = sorted(names, key=len, reverse=True)

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
            if self.is_("linefeed|line-comment-begin|comment-begin|statement-separator", lskip_ws=False, unconsumed=True):
                captured = self.source[start_pos:self.pos]
                self.pos = start_pos
                return captured
            self.pos += 1
        self.pos = start_pos
        return self.source[start_pos:].split('\n')[0]

    def capture_comment(self):
        """コメントを位置を変えずに習得する。行コメントとブロックコメントの両方に対応。"""
        save_pos = self.pos
        comment = None
        if self.is_("line-comment-begin"):
            start_pos = self.pos
            self.consume_until("linefeed", until_eof=True)
            comment =self.source[start_pos:self.pos]
        if self.is_("comment-begin"):
            start_pos = self.pos
            self.consume_until("comment-end", until_eof=True)
            comment = self.source[start_pos:self.pos]
        self.pos = save_pos # コメントは位置を変えずに取得
        return comment

    def p(self, node: ASTNode = None, start_pos: int = None, end_pos: int = None, length: int = 0) -> ASTNode:
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

    def print_debug(self, message: str):
        linenum, col, line = self.p(start_pos=self.pos).extract()
        print(f"@debug {message} at pos={self.pos} line={linenum} col={col}")
        print(f"{line}\n{' '*(col-1)}^")

def _is_alnum(s: str) -> bool:
    for ch in s:
        if not (('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or (ch == '_')):
            return False
    return True

NONTERMINALS = {}

class ParserCombinator(object):

    def quick_check(self, source: Source) -> bool:
        return True
    
    def match(self, source: Source):
        return True


class ConstParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_("null|boolean-true|boolean-false")
    
    def match(self, source: Source):
        saved_pos = source.pos
        if source.is_("null"):
            return source.p(ConstNode(None), start_pos=saved_pos)
        if source.is_("boolean-true"):
            return source.p(ConstNode(True), start_pos=saved_pos)
        if source.is_("boolean-false"):
            return source.p(ConstNode(False), start_pos=saved_pos)
        raise YuiError(("expected-boolean",), source.p(length=1), BK=True)

NONTERMINALS["@Boolean"] = ConstParser()

class NumberParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_("number-first-char", unconsumed=True)
    
    def match(self, source: Source):
        start_pos = source.pos
        if source.is_("number-first-char"):
            source.require_("number-chars", lskip_ws=False)
            if source.is_("number-dot-char", lskip_ws=False):
                source.is_("number-chars", lskip_ws=False)
                number = source.source[start_pos:source.pos]
                return source.p(NumberNode(float(number)), start_pos=start_pos)
            else:
                number = source.source[start_pos:source.pos]
            return source.p(NumberNode(int(number)), start_pos=start_pos)
        raise YuiError(("expected-number",), source.p(length=1), BK=True)

NONTERMINALS["@Number"] = NumberParser()

_escaped_string = {
    'n': '\n',
    't': '\t',
}

class StringParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_("string-begin", unconsumed=True)
    
    def match(self, source: Source):
        opening_quote_pos = source.pos
        if source.is_("string-begin"):
            opening_pos = source.pos
            string_content = []
            expression_count = 0
            while source.pos < source.length:
                source.consume_until("string-content-end", until_eof=True)
                string_content.append(source.source[opening_pos:source.pos])
                if source.is_("string-end", unconsumed=True):
                    break
                if source.is_("string-escape"):
                    if source.is_eos():
                        raise YuiError(("wrong-escape-sequence"), source.p(length=1))
                    next_char = source.source[source.pos]
                    source.pos += 1
                    string_content.append(_escaped_string.get(next_char, next_char))
                    opening_pos = source.pos
                    continue
                start_inter_pos = source.pos
                if source.is_("string-interpolation-begin", lskip_ws=False):
                    expression = source.parse("@Expression")
                    source.require_("string-interpolation-end", opening_pos=start_inter_pos)
                    string_content.append(expression)
                    expression_count += 1
                    opening_pos = source.pos
                    continue
            source.require_("string-end", lskip_ws=False, opening_pos=opening_quote_pos)
            if expression_count == 0:
                string_content = ''.join(string_content)
            return source.p(StringNode(string_content), start_pos=opening_quote_pos)
        raise YuiError(("expected-string",), source.p(length=1), BK=True)

NONTERMINALS["@String"] = StringParser()

class ArrayParser(ParserCombinator):

    def quick_check(self, source: Source) -> bool:
        return source.is_("array-begin", unconsumed=True)
    
    def match(self, source: Source):
        opening_pos = source.pos
        if source.is_("array-begin"):
            arguments = []
            while not source.is_("array-end", lskip_lf=True, unconsumed=True):
                arguments.append(source.parse("@Expression", lskip_lf=True))
                if source.is_("array-separator", lskip_lf=True):
                    continue
            source.require_("array-end", lskip_lf=True, opening_pos=opening_pos)
            return source.p(ArrayNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected-array",), source.p(length=1), BK=True)

NONTERMINALS["@Array"] = ArrayParser()

class ObjectParser(ParserCombinator):
    def quick_check(self, source: Source) -> bool:
        return source.is_("object-begin", unconsumed=True)
    
    def match(self, source: Source):
        opening_pos = source.pos
        if source.is_("object-begin", lskip_lf=True):
            arguments = []
            while not source.is_("object-end", lskip_lf=True, unconsumed=True):
                arguments.append(source.parse("@String", lskip_lf=True))
                source.require_("key-value-separator", lskip_lf=True)
                arguments.append(source.parse("@Expression", lskip_lf=True))
                if source.is_("object-separator", lskip_lf=True):
                    continue
            source.require_("object-end", lskip_lf=True, opening_pos=opening_pos)
            return source.p(ObjectNode(arguments), start_pos=opening_pos)
        raise YuiError(("expected-object",), source.p(length=1), BK=True)

NONTERMINALS["@Object"] = ObjectParser()

class NameParser(ParserCombinator):

    def match(self, source: Source):
        start_pos = source.pos
        if source.is_("keywords"):
            matched_keyword = source.matched_string
            saved_pos = source.pos
            source.is_("name-chars", lskip_ws=False)
            if source.pos == saved_pos: #続かないとキーワード確定
                raise YuiError(("keyword-name", f"❌`{matched_keyword}`"), source.p(start_pos=start_pos), BK=True)
            source
        special_name = source.match_special_name()
        if special_name is not None:
            return source.p(NameNode(special_name), start_pos=source.pos-len(special_name))
        if source.is_("extra-name-begin"):
            start_pos = source.pos
            source.consume_until("extra-name-end", disallow_string="\n")
            name = source.source[start_pos:source.pos]
            node = source.p(NameNode(name), start_pos=start_pos)
            source.require_("extra-name-end", opening_pos=start_pos-1)
            return node
        start_pos = source.pos
        if source.is_("name-first-char"):
            source.require_("name-chars", lskip_ws=False)
            source.require_("name-last-char", lskip_ws=False)
            name = source.source[start_pos:source.pos]
            return source.p(NameNode(name), start_pos=start_pos)
        snippet = source.capture_line().strip()
        raise YuiError(("wrong-name", f"❌{snippet}"), source.p(length=1), BK=True)

NONTERMINALS["@Name"] = NameParser()

LITERALS = ["@Number","@String","@Array","@Object","@Boolean"]

class TermParser(ParserCombinator):
    def match(self, source: Source):
        opening_pos = source.pos
        if source.is_("array-indexer-begin"):
            expression = source.parse("@Expression")
            source.require_("array-indexer-infix")
            index = source.parse("@Expression")
            source.require_("array-indexer-end", opening_pos=opening_pos)
            order_policy = source.get("array-indexer-order")
            return source.p(GetIndexNode(expression, index, order_policy=order_policy), start_pos=opening_pos)
        if source.is_("minus-begin"):
            expression = source.parse("@Expression", BK=False)
            if source.is_("minus-end"):
                return source.p(MinusNode(expression), start_pos=opening_pos)
            source.pos = opening_pos
        if source.is_("length-begin"):
            expression_node = source.parse("@Expression")
            source.require_("length-end", opening_pos=opening_pos)
            return source.p(ArrayLenNode(expression_node), start_pos=opening_pos)
        if source.is_("catch-begin"):
            opening_pos = source.pos - len(source.matched_string)
            expression = source.parse("@Expression", BK=False)
            source.require_("catch-end", opening_pos=opening_pos)
            return source.p(CatchNode(expression), start_pos=opening_pos)
        if source.is_("grouping-begin"):
            expression_node = source.parse("@Expression")
            source.require_("grouping-end", opening_pos=opening_pos)
            return source.p(PrintExpressionNode(expression_node, grouping=True), start_pos=opening_pos)
        if source.is_defined("binary-infix-prefix-begin"):
            if source.is_("binary-infix-prefix", suffixes=["+","-","*","/","%","==","!=","<=",">=","<",">","in","notin"]):
                operator = source.matched_suffix
                left_node = source.parse("@Expression", BK=False)
                right_node = source.parse("@Expression", BK=False)
                source.require_('binary-infix-prefix-end')
                return source.p(BinaryNode(operator, left_node, right_node), start_pos=opening_pos)
        try:
            saved = source.save()
            if source.is_("funcapp-begin"):
                name = source.parse("@Name", BK=True)
                arguments = []
                while not source.is_("funcapp-end", unconsumed=True):
                    source.require_("funcapp-separator")
                    expression = source.parse("@Expression", BK=False)
                    arguments.append(expression)
                source.require_("funcapp-end")
                return source.p(FuncAppNode(name, arguments), start_pos=opening_pos)
        except YuiError:
            source.backtrack(saved)

        for literal in LITERALS:
            if NONTERMINALS[literal].quick_check(source):
                source.pos = opening_pos
                return source.parse(literal, BK=True)
        return source.parse("@Name", BK=True)

NONTERMINALS["@Term"] = TermParser()

class PrimaryParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        if source.is_("unary-minus"):
            return source.p(MinusNode(source.parse('@Primary')), start_pos=start_pos)
        if source.is_('unary-length'):
            return source.p(ArrayLenNode(source.parse('@Primary')), start_pos=start_pos)
        if source.is_('unary-inspect'):
            node = source.parse('@Primary')
            return source.p(PrintExpressionNode(node, inspection=True), start_pos=start_pos)
        node = source.parse("@Term", BK=True)
        while source.has_next():
            opening_pos = source.pos
            if source.is_("funcapp-noarg"):
                node = source.p(FuncAppNode(node, []), start_pos=start_pos)
                continue
            if source.is_("funcapp-args-begin"):
                arguments = []
                while not source.is_("funcapp-args-end", unconsumed=True):
                    arguments.append(source.parse("@Expression", lskip_lf=True))
                    if source.is_("funcapp-separator"):
                        continue
                    break
                source.require_("funcapp-args-end", opening_pos=opening_pos)
                node = source.p(FuncAppNode(node, arguments), start_pos=start_pos)
                continue
            if source.is_("array-indexer-suffix"):
                index_node = source.parse("@Expression")
                source.require_("array-indexer-end", opening_pos=opening_pos)
                node = source.p(GetIndexNode(node, index_node), start_pos=start_pos)
                continue
            if source.is_("property-length"):
                node = source.p(ArrayLenNode(node), start_pos=start_pos)
                continue
            break
        return node
    
NONTERMINALS["@Primary"] = PrimaryParser()

class MultiplicativeParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        left_node = source.parse("@Primary", BK=True)
        saved = source.save()
        try:
            while source.is_("binary-infix", suffixes=["*","/","%"]):
                operator = source.matched_suffix
                right_node = source.parse("@Primary")
                left_node = source.p(BinaryNode(operator, left_node, right_node), start_pos=start_pos)
                saved = source.save()
        except YuiError:
            pass
        source.backtrack(saved)
        return left_node

NONTERMINALS["@Multiplicative"] = MultiplicativeParser()

class AdditiveParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        left_node = source.parse("@Multiplicative", BK=True)
        saved = source.save()
        try:
            while source.is_("binary-infix", suffixes=["+","-"]):
                operator = source.matched_suffix
                right_node = source.parse("@Multiplicative")
                left_node = source.p(BinaryNode(operator, left_node, right_node), start_pos=start_pos)
                saved = source.save()
        except YuiError:
            pass
        source.backtrack(saved)
        return left_node

NONTERMINALS["@Additive"] = AdditiveParser()

class ComparativeParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        left_node = source.parse("@Additive", BK=True)
        saved = source.save()
        try:
            if source.is_("binary-infix", suffixes=["==","!=","<=",">=","<",">","in","notin"]):
                operator = source.matched_suffix
                right_node = source.parse("@Additive")
                return source.p(BinaryNode(operator, left_node, right_node), start_pos=start_pos)
        except YuiError:
            pass
        source.backtrack(saved)
        return left_node

#NONTERMINALS["@Comparative"] = ComparativeParser()

NONTERMINALS["@Expression"] = ComparativeParser()

## Statement

class AssignmentParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('assignment-lookahead')
        start_pos = source.pos
        source.require_('assignment-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        left_node = source.parse("@Expression", BK=BK)
        source.require_('assignment-infix', BK=BK)
        right_node = source.parse("@Expression", BK=BK)
        source.require_('assignment-end', BK=BK)
        order_policy = source.get('assignment-order')
        return source.p(AssignmentNode(left_node, right_node, order_policy=order_policy), start_pos=start_pos)
    
NONTERMINALS["@Assignment"] = AssignmentParser()

class IncrementParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('increment-lookahead')
        start_pos = source.pos
        source.require_('increment-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        lvalue_node = source.parse("@Expression", BK=BK)
        source.require_('increment-end', BK=BK)
        return source.p(IncrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Increment"] = IncrementParser()

class DecrementParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('decrement-lookahead')
        start_pos = source.pos
        source.require_('decrement-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        lvalue_node = source.parse("@Expression", BK=BK)
        source.require_('decrement-end', BK=BK)
        return source.p(DecrementNode(lvalue_node), start_pos=start_pos)

NONTERMINALS["@Decrement"] = DecrementParser()

class AppendParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('append-lookahead')
        start_pos = source.pos
        source.require_('append-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        lvalue_node = source.parse("@Expression", BK=BK)
        source.require_('append-infix', BK=BK)
        value = source.parse("@Expression", BK=BK)
        source.require_('append-end', BK=BK)
        order_policy = source.get('append-order')
        return source.p(AppendNode(lvalue_node, value, order_policy=order_policy), start_pos=start_pos)

NONTERMINALS["@Append"] = AppendParser()

class BreakParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        source.require_('break', BK=True)
        return source.p(BreakNode(), start_pos=start_pos)

NONTERMINALS["@Break"] = BreakParser()

class ImportParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        source.require_('import-standard', BK=True)
        return source.p(ImportNode(), start_pos=start_pos)

NONTERMINALS["@Import"] = ImportParser()

class PassParser(ParserCombinator):
    def match(self, source: Source):
        if not source.is_defined('pass'):
            raise YuiError(("pass-not-defined",), source.p(length=1), BK=True)
        start_pos = source.pos
        source.require_('pass', BK=True)
        return source.p(PassNode(), start_pos=start_pos)
    
NONTERMINALS["@Pass"] = PassParser()

class ReturnParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('return-lookahead')
        start_pos = source.pos
        source.require_('return-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        expr_node = source.parse("@Expression", BK=BK)
        source.require_('return-end', BK=BK)
        return source.p(ReturnNode(expr_node), start_pos=start_pos)
    
NONTERMINALS["@Return"] = ReturnParser()

class PrintExpressionParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('print-lookahead')
        start_pos = source.pos
        source.require_('print-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        expr_node = source.parse("@Expression", BK=BK)
        source.require_('print-end', BK=BK)
        return source.p(PrintExpressionNode(expr_node), start_pos=start_pos)

NONTERMINALS["@PrintExpression"] = PrintExpressionParser()

class RepeatParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('repeat-lookahead')
        start_pos = source.pos
        source.require_('repeat-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        times_node = source.parse("@Expression", BK=BK)
        source.require_('repeat-times', BK=BK)
        source.require_('repeat-block', BK=BK)
        block_node = source.parse("@Block")
        source.require_('repeat-end', lskip_lf=True, BK=False)
        order_policy = source.get('repeat-order')
        return source.p(RepeatNode(times_node, block_node, order_policy=order_policy), start_pos=start_pos, end_pos=block_node.end_pos)

NONTERMINALS["@Repeat"] = RepeatParser()

class IfParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        BK = source.can_backtrack('if-lookahead')
        source.require_('if-begin', BK=BK) # もし
        source.require_('if-condition-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        if source.is_("if-prefix", ['==', '!=', '<=', '<', '>=', '>', 'notin', 'in']):
            operator = source.matched_suffix
            BK=False
            left_node = source.parse("@Expression", BK=BK)
            right_node = source.parse("@Expression", BK=BK)
        else:
            left_node = source.parse("@Expression", BK=BK)
            if isinstance(left_node, BinaryNode) and left_node.comparative:
                operator = str(left_node.operator)
                right_node = left_node.right_node
                left_node = left_node.left_node
            elif source.is_("if-infix", ['notin', 'in', '!=', '<=', '<', '>=', '>', '==']):
                operator = source.matched_suffix
                BK=False
                right_node = source.parse("@Expression", BK=BK)
            else:
                source.require_('if-infix', BK=BK) # が
                right_node = source.parse("@Expression", BK=BK)
                if source.is_("if-suffix", ['!=', '<=', '<', '>=', '>', 'notin', 'in', '==']):
                    operator = source.matched_suffix
                else:
                    operator = "=="
        source.require_('if-condition-end', BK=BK)

        source.require_('if-then', BK=BK) # ならば
        then_node = source.parse("@Block", BK=False)
        else_end_pos = source.pos
        node_end_pos = then_node.end_pos

        source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.is_('if-else'):
            else_node = source.parse("@Block", BK=False)
            node_end_pos = else_node.end_pos
        elif (source.is_defined('if-end') and not source.is_('if-end', unconsumed=True)):
            try:
                else_node = source.parse("@Block", BK=False)
                node_end_pos = else_node.end_pos
            except:
                source.pos = else_end_pos
                else_node = None
        else:
            source.pos = else_end_pos
            else_node = None
        source.require_('if-end', lskip_lf=True, BK=False)
        return source.p(IfNode(left_node, operator, right_node, then_node, else_node), start_pos=start_pos, end_pos=node_end_pos)

NONTERMINALS["@If"] = IfParser()

class FuncDefParser(ParserCombinator):
    def match(self, source: Source):
        BK = source.can_backtrack('funcdef-lookahead')
        start_pos = source.pos
        source.require_('funcdef-begin', BK=BK) # もし
        source.require_('funcdef-name-begin', BK=BK) #
        if BK: BK = source.pos == start_pos
        name_node = source.parse("@Name", BK=BK)
        source.require_('funcdef-name-end', BK=BK) # =

        arguments = []
        if not source.is_('funcdef-noarg'): # 引数なし
            source.require_('funcdef-args-begin', BK=BK) # 入力
            while not source.is_('funcdef-args-end', unconsumed=True):
                arguments.append(source.parse("@Name", BK=BK))
                if source.is_('funcdef-arg-separator', if_undefined=True):
                    continue
                break
            source.require_('funcdef-args-end', BK=BK)

        source.require_('funcdef-block', BK=BK) # に対し
        body_node = source.parse("@Block", BK=False)
        source.require_('funcdef-end', lskip_lf=True, BK=False)
        return source.p(FuncDefNode(name_node, arguments, body_node), start_pos=start_pos, end_pos=body_node.end_pos)

NONTERMINALS["@FuncDef"] = FuncDefParser()

yui_syntax = load_syntax("yui")

class AssertParser(ParserCombinator):
    def match(self, source: Source):
        start_pos = source.pos
        BK = source.can_backtrack('assert-lookahead')
        source.require_('assert-begin', BK=BK)
        if BK: BK = source.pos == start_pos
        saved = source.save()
        try:
            test_node = source.parse("@Expression", BK=BK)
            if isinstance(test_node, BinaryNode) and test_node.comparative:
                reference_node = test_node.right_node
                test_node = test_node.left_node
            else:
                source.require_('assert-infix', BK=BK)
                reference_node = source.parse("@Expression", BK=BK)
            source.require_('assert-end', BK=BK)
            order_policy = source.get('assert-order')
            return source.p(AssertNode(test_node, reference_node, order_policy=order_policy), start_pos=start_pos)
        except YuiError as e:
            source.backtrack(saved)
        saved = source.terminals
        try:
            # Yuiの構文で再度試す
            global yui_syntax
            source.terminals = yui_syntax
            test_node = source.parse("@Expression", BK=BK)
            source.require_('assert-infix', BK=BK)
            reference_node = source.parse("@Expression", BK=BK)
            source.require_('assert-end', BK=BK)
            order_policy = source.get('assert-order')
            return source.p(AssertNode(test_node, reference_node, order_policy=order_policy), start_pos=start_pos)
        except YuiError:
            raise e
        finally:
            source.terminals = saved

NONTERMINALS["@Assert"] = AssertParser()

class BlockParser(ParserCombinator):
    def match(self, source: Source):
        saved = source.save()
        if source.is_('line-block-begin'): # 単一ブロックを認めるか { statement }
            opening_pos = source.pos - len(source.matched_string)
            if source.is_('line-block-end'): # 空のブロック
                return source.p(BlockNode([]), start_pos=opening_pos)
            try:
                statements = source.parse("@Statement[]")
                source.require_('line-block-end', BK=False)
                return source.p(BlockNode(statements), start_pos=opening_pos)
            except YuiError:
                source.backtrack(saved)

        source.require_("block-begin", lskip_lf=True) #
        opening_pos = source.pos - len(source.matched_string)
        statements = []
        if source.is_defined('indent') and not source.is_defined('block-end'): # indentが必要な場合
            indent = source.capture_indent()
            block_end_pos = None
            while source.has_next():
                saved_before_lf = source.save()
                source.require_("linefeed", lskip_ws=True)
                if source.is_("linefeed", unconsumed=True):
                    continue # ただの空行はブロックの終わりにしない
                if source.consume_string(indent):
                    if source.is_('block-end', lskip_ws=False, unconsumed=True):
                        break
                    if source.is_('whitespace', lskip_ws=False):
                        statements.extend(source.parse("@Statement[]"))
                        continue
                block_end_pos = source.pos  # \n 消費後の位置を記録
                source.backtrack(saved_before_lf) # \n を戻す（外側ブロック用）
                break
            source.require_("block-end", opening_pos=opening_pos)
            return source.p(BlockNode(statements), start_pos=opening_pos, end_pos=block_end_pos)
        
        while not source.is_("block-end", lskip_lf=True, unconsumed=True):
            cur_pos = source.pos
            statements.extend(source.parse("@Statement[]", lskip_lf=True))
            if cur_pos == source.pos:
                break  # Safety: prevent infinite loop if no progress
        source.require_("block-end", lskip_lf=True, opening_pos=opening_pos)
        return source.p(BlockNode(statements), start_pos=opening_pos)

NONTERMINALS["@Block"] = BlockParser()

STATEMENTS = [
    "@FuncDef",
    "@Increment",
    "@Decrement",
    "@Append",
    "@Import",
    "@Break",
    "@Assignment",
    "@Assert",
    "@If",
    "@Repeat",
    "@Return",
    "@Pass",
    "@PrintExpression",
]

class StatementParser(ParserCombinator):
    def match(self, source: Source):
        saved = source.save()
        for parser_name in STATEMENTS:
            try:
                statement = source.parse(parser_name, BK=True)
                return statement
            except YuiError as e:
                if not e.BK: 
                    raise e
            source.backtrack(saved)
        line = source.capture_line()
        if line.strip() == "" and not source.is_defined('pass'):
            return source.p(PassNode(), start_pos=source.pos)
        raise YuiError(("wrong-statement", f"❌{line}"), source.p(length=1))

NONTERMINALS["@Statement"] = StatementParser()

class StatementsParser(ParserCombinator):
    def match(self, source: Source):
        if source.is_eos_or_linefeed(lskip_ws=True, unconsumed=True):
            statements = []
        else:
            statements = [source.parse("@Statement")]
        while source.is_('statement-separator'):
            statements.append(source.parse("@Statement"))
        return statements

NONTERMINALS["@Statement[]"] = StatementsParser()

class TopLevelParser(ParserCombinator):
    def match(self, source: Source):
        source.skip_whitespaces_and_comments(include_linefeed=True)
        saved_pos = source.pos
        statements = []
        while source.has_next():
            cur_pos = source.pos
            statements.extend(source.parse("@Statement[]"))
            if cur_pos == source.pos:                
                break
            source.skip_whitespaces_and_comments(include_linefeed=True)
        if source.has_next():
            line = source.capture_line()
            raise YuiError(("wrong-statement", f"❌{line}"), source.p(length=1))
        return source.p(BlockNode(statements, top_level=True), start_pos=saved_pos)

NONTERMINALS["@TopLevel"] = TopLevelParser()

class YuiParser:
    def __init__(self, syntax: Union[str, dict]):
        self.syntax = syntax
        if isinstance(syntax, dict):
            self.terminals = syntax.copy()
        else:
            self.terminals = load_syntax(syntax)
    
    def parse(self, source_code: str) -> ASTNode:
        source = Source(source_code, syntax=self.terminals)
        return source.parse("@TopLevel")

