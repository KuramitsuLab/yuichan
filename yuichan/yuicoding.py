import random
from typing import Dict, Union

from .yuiast import (
    ASTNode, ConstNode, NameNode,
    StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode, StatementNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, CatchNode, ImportNode,
)
from .yuitypes import YuiType, types
from .yuisyntax import load_syntax, YuiSyntax

class CodingVisitor(YuiSyntax):

    def __init__(self, syntax_json: Union[str, Dict[str, str]], function_language=None):
        if isinstance(syntax_json, str):
            syntax_json = load_syntax(syntax_json)
        super().__init__(syntax_json)
        self.buffer = []
        self.indent_string = "   "
        self.indent_level = 0
        self.just_linefeeded = False
        self.funcnamemap = {}
        self.load_functionmap(function_language)

    def load_functionmap(self, function_language=None) -> bool:
        from .yuistdlib import standard_lib
        if function_language is None:
            self.funcnamemap = {}
            return
        targets, modules = standard_lib([])
        targets = targets.lower().split('|')
        index = targets.index(function_language)
        if index < 0:
            raise ValueError(f"Name '{function_language}' not found in standard library targets: {targets}")
        for names, _ in modules:
            names = names.split('|')
            for name in names:
                self.funcnamemap[name] = names[index]
        return True

    def emit(self, node: ASTNode, indent_string="   ", random_seed=None) -> str:
        self.buffer = []
        self.indent_level = 0
        self.indent_string = indent_string
        self.just_linefeeded = True
        self.random_seed = random_seed
        if not isinstance(node, StatementNode) and self.is_defined('print-begin'):
            PrintExpressionNode(node).visit(self)
        else:
            node.visit(self)
        return ''.join(self.buffer)

    def last_char(self) -> str:
        if len(self.buffer) == 0:
            return '\n'
        return self.buffer[-1][-1]

    def linefeed(self):
        if not self.just_linefeeded:
            if self.indent_string:
                self.buffer.append('\n' + self.indent_string * self.indent_level)
            else:
                self.buffer.append(' ')
            self.just_linefeeded = True

    def string(self, text: str):
        if '\n' in text:
            lines = text.split('\n')
            for line in lines[:-1]:
                self.string(line)
                self.linefeed()
            self.string(lines[-1])
            return
        if len(text) == 0:
            return
        if text == " " and self.last_char() == ' ':
            return # avoid consecutive spaces
        self.buffer.append(text)
        self.just_linefeeded = False

    def word_segment(self, no_spaece_if_last_chars=' \n([{'):
        if self.is_defined('word-segmenter'):
            if self.last_char() not in no_spaece_if_last_chars:
                self.string(' ')
        else:
            if self.random_seed is not None:
                if self.last_char() not in no_spaece_if_last_chars:
                    if random.random() < 0.5:
                        self.string(' ')

    def terminal(self, terminal: str, if_undefined = None, linefeed_before=False):
        if terminal == 'linefeed':
            self.linefeed()
            return
        if not self.is_defined(terminal):
            return
        token = self.for_example(terminal)
        if token == "": 
            #print(f"Warning: terminal '{terminal}' is empty string")
            return
        if linefeed_before:
            self.linefeed()
        if token[0] not in ",()[]{}:;\"'.":
            # avoid unnecessary word segmentation before terminals
            self.word_segment()
        self.string(token)

    def comment(self, comment: str):
        if not comment:
            return
        if self.is_defined('comment-begin') and self.is_defined('comment-end'):
            self.terminal('comment-begin')
            self.string(f' {comment}')
            self.terminal('comment-end')
        elif self.is_defined('line-comment-begin'):
            for line in comment.splitlines():
                self.terminal('line-comment-begin')
                self.string(f' {line}')
                self.linefeed()

    def expression(self, node: ASTNode, grouping=None):
        self.word_segment()
        if grouping and self.is_defined('grouping-begin') and self.is_defined('grouping-end'):
            self.terminal('grouping-begin')
            node.visit(self)
            self.terminal('grouping-end')
        else:
            node.visit(self)

    def statement(self, node: ASTNode):
        node.visit(self)
        self.comment(node.comment)

    def block(self, node: ASTNode):
        if not isinstance(node, BlockNode):
            BlockNode([node]).visit(self)
        else:
            node.visit(self)
        # self.word_segment()  # pylike で末尾スペースが付きパースエラーになるため無効化

    def escape(self, text: str) -> str:
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    # AST Node Visitors

    def visitASTNode(self, node: ASTNode):
        self.string(f'FIXME: {node.__class__.__name__}')

    def visitConstNode(self, node: ConstNode):
        if node.native_value is None:
            self.terminal('null')
        elif node.native_value is True:
            self.terminal('boolean-true')
        else:
            self.terminal('boolean-false')

    def visitNumberNode(self, node: NumberNode):
        self.terminal("number-begin")
        if isinstance(node.native_value, float):
            self.string(f"{node.native_value:.6f}")
        else:
            self.string(str(node.native_value))
        self.terminal("number-end")

    def visitStringNode(self, node: StringNode):
        self.terminal('string-begin')
        if isinstance(node.contents, str):
            self.string(self.escape(node.contents))
        else:
            for content in node.contents:
                if isinstance(content, str):
                    self.string(self.escape(content))
                else:
                    self.terminal('string-interpolation-begin')
                    content.visit(self)
                    self.terminal('string-interpolation-end')
        self.terminal('string-end')
    
    def visitNameNode(self, node: NameNode):
        self.terminal("name-begin")
        self.string(node.name)
        self.terminal("name-end")

    def visitArrayNode(self, node: ArrayNode):
        saved_buffer = self.buffer
        self.buffer = []
        self.terminal('array-begin')
        for i, element in enumerate(node.elements):
            if i > 0:
                self.terminal('array-separator')
            self.expression(element)
        self.terminal('array-end')
        content = ''.join(self.buffer)
        self.buffer = saved_buffer
        if len(content) <= 80 and '\n' not in content:
            self.string(content)
            return
        self.terminal('array-begin')
        self.indent_level += 1
        self.linefeed()
        for i, element in enumerate(node.elements):
            if i > 0:
                self.terminal('array-separator')
                self.linefeed()
            self.expression(element)
        self.indent_level -= 1
        self.linefeed()        
        self.terminal('array-end')
        
    def visitObjectNode(self, node: ObjectNode):
        saved_buffer = self.buffer
        self.buffer = []
        self.terminal('object-begin')
        for i in range(0, len(node.elements), 2):
            if i > 0:
                self.terminal('object-separator')
            key_node = node.elements[i]
            value_node = node.elements[i+1]
            self.expression(key_node)
            self.terminal('key-value-separator')
            self.expression(value_node)
        self.terminal('object-end')
        content = ''.join(self.buffer)
        self.buffer = saved_buffer
        if len(content) <= 80 and '\n' not in content:
            self.string(content)
            return
        self.terminal('object-begin')
        self.indent_level += 1
        self.linefeed()
        for i in range(0, len(node.elements), 2):
            if i > 0:
                self.terminal('object-separator')
                self.linefeed()
            key_node = node.elements[i]
            value_node = node.elements[i+1]
            self.expression(key_node)
            self.terminal('key-value-separator')
            self.expression(value_node)
        self.indent_level -= 1
        self.linefeed()
        self.terminal('object-end')

    def visitMinusNode(self, node: MinusNode):
        if self.is_defined('minus-begin'):
            self.terminal('minus-begin')
            self.expression(node.element)
            self.terminal('minus-end')
        elif self.is_defined("unary-minus"):
            self.terminal("unary-minus")
            node.element.visit(self) # avoid extra word segmenter for negative numbers
        else:
            self.visitASTNode(node)

    def visitBinaryNode(self, node: BinaryNode):
        symbol = node.operator.symbol
        if self.is_defined('binary-infix-prefix-begin'):
            self.terminal(f'binary-infix-prefix{symbol}')
            self.word_segment()
            self.expression(node.left_node)
            self.word_segment()
            self.expression(node.right_node)
            self.terminal('binary-infix-prefix-end')
        else:
            self.expression(node.left_node, grouping=self.check_left_grouping(node, node.left_node))
            self.word_segment()
            self.terminal(f"binary-infix{symbol}")
            self.word_segment()
            self.expression(node.right_node, grouping=self.check_right_grouping(node, node.right_node))

    def check_left_grouping(self, parent: BinaryNode, child: ASTNode) -> bool:
        if not isinstance(child, BinaryNode):
            return False
        parent_prec = parent.operator.precedence
        child_prec = child.operator.precedence
        #print(f"check_left_grouping: parent {parent.operator.symbol} (prec {parent_prec}), child {child.operator.symbol} (prec {child_prec})" )
        if child_prec <= parent_prec:
            return False
        return True

    def check_right_grouping(self, parent: BinaryNode, child: ASTNode) -> bool:
        if not isinstance(child, BinaryNode):
            return False
        parent_prec = parent.operator.precedence
        child_prec = child.operator.precedence
        #print(f"check_right_grouping: parent {parent.operator.symbol} (prec {parent_prec}), child {child.operator.symbol} (prec {child_prec})" )
        if child_prec < parent_prec:
            return False
        return True

    def visitArrayLenNode(self, node: ArrayLenNode):
        if self.is_defined('property-length'):
            self.expression(node.element)
            self.terminal('property-length')
        elif self.is_defined('unary-length'):
            self.terminal('unary-length')
            self.expression(node.element)
        elif self.is_defined('length-begin'):
            self.terminal('length-begin')
            self.expression(node.element)
            self.terminal('length-end')

    def visitGetIndexNode(self, node: GetIndexNode):
        collection, index = node.collection, node.index_node
        if self.get('array-indexer-order') == 'reversed':
            collection, index = index, collection
        self.terminal('array-indexer-begin')
        self.expression(collection)
        self.terminal('array-indexer-infix')
        self.terminal('array-indexer-suffix')
        self.expression(index)
        self.terminal('array-indexer-end')
    
    def visitFuncAppNode(self, node: FuncAppNode):
        self.terminal('funcapp-begin')
        name = self.funcnamemap.get(node.name_node.name, node.name_node.name)
        self.string(name)

        if self.is_defined('funcapp-noarg') and len(node.arguments) == 0:
            self.terminal('funcapp-noarg')
        else:
            self.terminal('funcapp-args-begin')
            for i, arg in enumerate(node.arguments):
                if i > 0:
                    self.terminal('funcapp-separator')
                self.expression(arg, grouping=(isinstance(arg, FuncAppNode) and not self.is_defined(f'funcapp-args-end')))
            self.terminal('funcapp-args-end')
            self.terminal('funcapp-end')

    def visitAssignmentNode(self, node: AssignmentNode):
        variable, expression = node.variable, node.expression
        if self.get('assignment-order') == 'reversed':
            variable, expression = expression, variable

        self.terminal('assignment-begin')
        self.expression(variable)
        self.terminal('assignment-infix')
        self.expression(expression)
        self.terminal('assignment-end')
    
    def visitIncrementNode(self, node: IncrementNode):
        self.terminal('increment-begin')
        self.expression(node.variable)
        self.terminal('increment-end')

    def visitDecrementNode(self, node: DecrementNode):
        self.terminal('decrement-begin')
        self.expression(node.variable)
        self.terminal('decrement-end')

    def visitAppendNode(self, node: AppendNode):
        variable, expression = node.variable, node.expression
        if self.get('assignment-order') == 'reversed':
            variable, expression = expression, variable

        self.terminal('append-begin')
        self.expression(variable)
        self.terminal('append-infix')
        self.expression(expression)
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
        if node.grouping:
            self.terminal('grouping-begin')
            self.expression(node.expression)
            self.terminal('grouping-end')
            return
        if node.inspection:
            self.terminal('unary-inspect')
            self.expression(node.expression)
        else:
            self.terminal('print-begin')
            self.expression(node.expression)
            self.terminal('print-end')

    def visitIfNode(self, node: IfNode):
        self.terminal('if-begin')
        self.terminal('if-condition-begin')
        if isinstance(node.left, BinaryNode) and node.left.comparative:
            self.expression(node.left)
        else:
            op_symbol = str(node.operator)
            if self.is_defined(f'if-prefix{op_symbol}'):
                self.terminal(f'if-prefix{op_symbol}')
                self.expression(node.left)
                self.expression(node.right)
            else:
                self.expression(node.left)
                if self.is_defined(f'if-infix{op_symbol}'):
                    self.terminal(f'if-infix{op_symbol}')
                else:
                    self.terminal('if-infix')
                self.expression(node.right)
                if self.is_defined(f'if-suffix{op_symbol}'):
                    self.terminal(f'if-suffix{op_symbol}')
                else:
                    self.terminal('if-suffix')
        self.terminal('if-condition-end')
        self.terminal('if-then')
        self.block(node.then_block)
        if node.else_block and not isinstance(node.else_block, PassNode):
            if self.is_defined('if-else-if') and isinstance(node.else_block, IfNode):
                self.terminal('if-else-if', linefeed_before=True)
                self.block(node.else_block)
            else:
                self.terminal('if-else', linefeed_before=True)
                self.block(node.else_block)
        self.terminal('if-end', linefeed_before=True)

    def visitRepeatNode(self, node: RepeatNode):
        count_node, block_node = node.count_node, node.block_node
        if self.get('repeat-order') == 'reversed':
            count_node, block_node = block_node, count_node

        self.terminal('repeat-begin')
        self.expression(count_node)
        self.terminal('repeat-times')
        self.terminal('repeat-block')
        self.block(block_node)
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

    def visitImportNode(self, node: ImportNode):
        self.terminal('import-standard')

    def visitAssertNode(self, node: AssertNode):
        test_node, reference_node = node.test, node.reference
        if self.get('assert-order') == 'reversed':
            test_node, reference_node = reference_node, test_node   
        self.terminal('assert-begin')
        self.expression(test_node)
        self.terminal('assert-infix')
        self.expression(reference_node)
        self.terminal('assert-end')

    def visitCatchNode(self, node: CatchNode):
        self.terminal('catch-begin')
        self.expression(node.expression)
        self.terminal('catch-end')

    def visitBlockNode(self, node: BlockNode):
        if not node.top_level:
            self.terminal('block-begin-prefix')
            self.terminal('block-begin')
            self.indent_level += 1
            self.linefeed()

        if len(node.statements) == 0:
            self.terminal('pass')
        else:
            for i, statement in enumerate(node.statements):
                if i > 0:
                    self.linefeed()
                if not isinstance(statement, StatementNode) and self.is_defined('print-begin'):
                    PrintExpressionNode(statement).visit(self)
                else:
                    statement.visit(self)
                if isinstance(statement, FuncDefNode):
                    self.linefeed()
                if not self.just_linefeeded:
                    self.terminal("statement-separator")
                if isinstance(statement, PassNode):
                    self.linefeed()
                self.comment(statement.comment)

        if not node.top_level:
            self.indent_level -= 1
            self.just_linefeeded = False  # indent 変化後に正しいインデントで linefeed させる
            self.terminal('block-end', linefeed_before=True)

