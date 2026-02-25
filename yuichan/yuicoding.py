from typing import Dict, Union

from .yuiast import (
    ASTNode, ConstNode, NameNode,
    StringNode, NumberNode, ArrayNode, ObjectNode,
    MinusNode, ArrayLenNode,
    FuncAppNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, PrintExpressionNode, PassNode,
    IfNode, BreakNode, RepeatNode, FuncDefNode, ReturnNode,
    AssertNode, ImportNode,
)
from .yuitypes import YuiType
from .yuisyntax import load_syntax, YuiSyntax

class CodingVisitor(YuiSyntax):

    def __init__(self, syntax_json: Union[str, Dict[str, str]]):
        if isinstance(syntax_json, str):
            syntax_json = load_syntax(syntax_json)
        super().__init__(syntax_json)
        self.buffer = []
        self.indent = 0
        self.just_linefeeded = False

    def emit(self, node: ASTNode) -> str:
        self.buffer = []
        self.indent = 0
        self.just_linefeeded = True
        node.visit(self)
        return ''.join(self.buffer)

    def last_char(self) -> str:
        if len(self.buffer) == 0:
            return '\n'
        return self.buffer[-1][-1]

    def linefeed(self):
        if not self.just_linefeeded:
            self.buffer.append('\n' + '  ' * self.indent)
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

    def terminal(self, terminal: str, if_undefined = None, linefeed_before=False):
        if terminal == 'linefeed':
            self.linefeed()
            return
        if not self.is_defined(terminal):
            return
        token = self.for_example(terminal)
        if token == "": 
            print(f"Warning: terminal '{terminal}' is empty string")
            return
        if token[0] not in ",()[]{}:\"'.": 
            # avoid unnecessary word segmentation before terminals
            self.word_segment()
        if linefeed_before:
            self.linefeed()
        self.string(token)

    def comment(self, comment: str):
        if not comment:
            return
        if self.is_defined('comment-begin') and self.is_defined('comment-end'):
            self.terminal('comment-begin')
            self.string(comment)
            self.terminal('comment-end')
        elif self.is_defined('line-comment-begin'):
            for line in comment.splitlines():
                self.terminal('line-comment-begin')
                self.string(f' {line}')
                self.linefeed()

    def expression(self, node: ASTNode):
        self.word_segment()
        node.visit(self)

    def statement(self, node: ASTNode):
        node.visit(self)
        self.comment(node.comment)

    def block(self, node: ASTNode):
        if not isinstance(node, BlockNode):
            BlockNode([node]).visit(self)
        else:
            node.visit(self)
        self.word_segment()

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
        self.string(YuiType.arrayview_s(node.native_value))
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
        self.indent += 1
        self.linefeed()
        for i, element in enumerate(node.elements):
            if i > 0:
                self.terminal('array-separator')
                self.linefeed()
            self.expression(element)
        self.indent -= 1
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
        self.indent += 1
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
        self.indent -= 1
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
        if self.is_defined('binary-infix-prefix-begin'):
            self.terminal(f'binary-infix-prefix{node.operator}')
            self.word_segment()
            self.expression(node.left_node)
            self.word_segment()
            self.expression(node.right_node)
            self.terminal(f'binary-infix-prefix-end')
        else:
            self.expression(node.left_node)
            self.word_segment()
            self.terminal(f"binary{node.operator}")
            self.word_segment()
            self.expression(node.right_node)

    def visitArrayLenNode(self, node: ArrayLenNode):
        if self.is_defined('property-length'):
            self.expression(node.element)
            self.terminal('property-accessor')
            self.terminal('property-length')
        elif self.is_defined('unary-length'):
            self.terminal('unary-length')
            self.expression(node.element)
        elif self.is_defined('length-begin'):
            self.terminal('length-begin')
            self.expression(node.element)
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
        self.terminal('funcapp-args-begin')
        for i, arg in enumerate(node.arguments):
            if i > 0:
                self.terminal('funcapp-separator')
            self.expression(arg)
        self.terminal('funcapp-args-end')
        self.terminal('funcapp-end')

    def visitAssignmentNode(self, node: AssignmentNode):
        self.terminal('assignment-begin')
        self.expression(node.variable)
        self.terminal('assignment-infix')
        self.expression(node.expression)
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
        self.terminal('append-begin')
        self.expression(node.variable)
        self.terminal('append-infix')
        self.expression(node.expression)
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
            self.terminal('groping-begin')
            self.expression(node.expression)
            self.terminal('groping-end')
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

    def visitImportNode(self, node: ImportNode):
        self.terminal('import-standard')

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
                if isinstance(statement, FuncDefNode):
                    self.linefeed()
                self.terminal("block-separator")
                if isinstance(statement, PassNode):
                    self.linefeed()
                self.comment(statement.comment)

        if not node.top_level:
            self.indent -= 1
            self.just_linefeeded = False  # indent 変化後に正しいインデントで linefeed させる
            self.terminal('block-end', linefeed_before=True)

