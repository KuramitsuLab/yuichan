import pytest
from .yuiast import (
    YuiError,
    YuiRuntime,
    YuiData,
    NumberNode,StringNode,
    ArrayNode, ObjectNode,
    NameNode,
    MinusNode,ArrayLenNode,GetIndexNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode
)

class TestExpression:
    """式の評価に関するテストクラス"""

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", 1)
        runtime.setenv("A", YuiData([1, 2, 3]))
        return runtime  

    def test_int(self):
        runtime = self.init_runtime()
        expression = NumberNode(42)
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 42) == 0

    def test_float(self):
        runtime = self.init_runtime()
        expression = NumberNode(42.0)
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 42.0) == 0

    def test_string(self):
        runtime = self.init_runtime()
        expression = StringNode("A")
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, YuiData("A")) == 0

    def test_string_interpolation(self):
        runtime = self.init_runtime()
        expression = StringNode(["A", NumberNode(1), "B"])
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, YuiData("A1B")) == 0

    def test_variable(self):
        runtime = self.init_runtime()
        expression = NameNode("x")
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 1) == 0

    def test_undefined_variable(self):
        runtime = self.init_runtime()
        expression = NameNode("y")
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
            assert YuiData.compare(result, 1) == 0
        assert "undefined" in str(excinfo.value.args[0])
        assert "variable" in str(excinfo.value.args[0])

    def test_minus_int(self):
        runtime = self.init_runtime()
        expression = MinusNode(NumberNode(1))
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, -1) == 0

    def test_minus_float(self):
        runtime = self.init_runtime()
        expression = MinusNode(NumberNode(1.0))
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, -1) == 0

    def test_minus_string(self):
        runtime = self.init_runtime()
        expression = MinusNode(StringNode("A"))
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
            assert YuiData.compare(result, "A") == 0
        assert "expected" in str(excinfo.value.args[0])
        assert "number" in str(excinfo.value.args[0])

    def test_array(self):
        runtime = self.init_runtime()
        expression = ArrayNode([NumberNode(1), NumberNode(2), NumberNode(3)])
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, YuiData([1, 2, 3])) == 0

    def test_array_length(self):
        runtime = self.init_runtime()
        expression = ArrayLenNode(NameNode("A"))
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 3) == 0

    def test_int_length(self):
        runtime = self.init_runtime()
        expression = ArrayLenNode(NumberNode(1))
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
        assert "expected" in str(excinfo.value.args[0])
        assert "data" in str(excinfo.value.args[0])

    def test_array_get_index(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("A"), NumberNode(1))
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 2) == 0

    def test_array_out_of_index(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("A"), NumberNode(3))
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
        assert "out of index" in str(excinfo.value.args[0])

    def test_variable_assignment(self):
        runtime = self.init_runtime()
        expression = AssignmentNode(NameNode("A"), NumberNode(3))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("A"), 3) == 0

    def test_string_assignment(self):
        runtime = self.init_runtime()
        with pytest.raises(YuiError) as excinfo:
            expression = AssignmentNode(StringNode("A"), NumberNode(3))
            expression.evaluate(runtime)
        assert "expected" in str(excinfo.value.args[0])
        assert "variable" in str(excinfo.value.args[0])

    def test_variable_increment(self):
        runtime = self.init_runtime()
        expression = IncrementNode(NameNode("x"))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 2) == 0

    def test_variable_decrement(self):
        runtime = self.init_runtime()
        expression = DecrementNode(NameNode("x"))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 0) == 0

    def test_array_assignment(self):
        runtime = self.init_runtime()
        expression = AssignmentNode(GetIndexNode(NameNode("A"), NumberNode(0)), NumberNode(3))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("A"), YuiData([3, 2, 3])) == 0

    def test_array_increment(self):
        runtime = self.init_runtime()
        expression = IncrementNode(GetIndexNode(NameNode("A"), NumberNode(0)))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("A"), YuiData([2, 2, 3])) == 0

    def test_array_decrement(self):
        runtime = self.init_runtime()
        expression = DecrementNode(GetIndexNode(NameNode("A"), NumberNode(1)))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("A"), YuiData([1, 1, 3])) == 0

    def test_array_append(self):
        runtime = self.init_runtime()
        expression = AppendNode(NameNode("A"), NumberNode(0))
        result = expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("A"), YuiData([1, 2, 3, 0])) == 0

    def test_object(self):
        runtime = self.init_runtime()
        expression = ObjectNode([StringNode("x"), NumberNode(1), StringNode("y"), NumberNode(2), StringNode("z"), NumberNode(3)])
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, YuiData({"x": 1, "y": 2, "z": 3})) == 0

    def test_object_get(self):
        runtime = self.init_runtime()
        runtime.setenv("p", YuiData({"x": 1, "y": 2, "z": 3}))
        expression = GetIndexNode(NameNode("p"), StringNode("x"))
        result = expression.evaluate(runtime)
        assert YuiData.compare(result, 1) == 0

    def test_object_assignment(self):
        runtime = self.init_runtime()
        runtime.setenv("p", YuiData({"x": 1, "y": 2, "z": 3}))
        expression = AssignmentNode(GetIndexNode(NameNode("p"), StringNode("x")), NumberNode(3))
        expression.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("p"), YuiData({"x": 3, "y": 2, "z": 3})) == 0

    def test_block(self):
        runtime = self.init_runtime()
        statement = BlockNode(
            AssignmentNode(NameNode("x"), NumberNode(10)),
            IncrementNode(NameNode("x")),
            IncrementNode(NameNode("x")),
        )
        statement.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 12) == 0
    
    def test_if_eq(self):
        runtime = self.init_runtime()
        statement = IfNode(
            left=NameNode("x"),
            operator="==",
            right=NumberNode(1),
            then_block=BlockNode(AssignmentNode(NameNode("x"), NumberNode(100))),
            else_block=BlockNode(AssignmentNode(NameNode("x"), NumberNode(200))),
        )
        statement.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 100) == 0

    def test_if_ne(self):
        runtime = self.init_runtime()
        statement = IfNode(
            left=NameNode("x"),
            operator="!=",
            right=NumberNode(1),
            then_block=BlockNode(AssignmentNode(NameNode("x"), NumberNode(100))),
            else_block=BlockNode(AssignmentNode(NameNode("x"), NumberNode(200))),
        )
        statement.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 200) == 0

    def test_repeat(self):
        runtime = self.init_runtime()
        statement = RepeatNode(
            NumberNode(3),
            BlockNode(IncrementNode(NameNode("x")))
        )
        statement.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 4) == 0

    def test_repeat_break(self):
        runtime = self.init_runtime()
        statement = RepeatNode(
            NumberNode(10),
            BlockNode(
                IncrementNode(NameNode("x")),
                IfNode(
                    left=NameNode("x"),
                    operator="==",
                    right=NumberNode(4),
                    then_block=BlockNode(BreakNode())
                )
            )
        )
        statement.evaluate(runtime)
        assert YuiData.compare(runtime.getenv("x"), 4) == 0

    def test_function(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode(
                ReturnNode(
                    MinusNode(
                        MinusNode(
                            NameNode("a")
                        )
                    )
                )
            )
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(10), NumberNode(20)]
        )
        result = func_app.evaluate(runtime)
        assert YuiData.compare(result, 10) == 0

    def test_function_undefined(self):
        runtime = self.init_runtime()
        func_app = FuncAppNode(
            name=NameNode("sub"),
            arguments=[NumberNode(10), NumberNode(20)]
        )
        with pytest.raises(YuiError) as excinfo:    
            result = func_app.evaluate(runtime)
        assert "undefined" in str(excinfo.value.args[0])
        assert "function" in str(excinfo.value.args[0])
    
    def test_function_argument_mismatch(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode(
                ReturnNode(
                    MinusNode(
                        MinusNode(
                            NameNode("a")
                        )
                    )
                )
            )
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(10)]
        )
        with pytest.raises(YuiError) as excinfo:    
            result = func_app.evaluate(runtime)
        assert "mismatch" in str(excinfo.value.args[0])
        assert "argument" in str(excinfo.value.args[0]) 

    def test_function_no_return(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode()
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(1), NumberNode(2)]
        )
        result = func_app.evaluate(runtime)
        assert YuiData.is_object(result)
        assert result.get("a") == 1
    
    def test_print_expression(self, capsys):
        runtime = self.init_runtime()
        expression = PrintExpressionNode(
            NumberNode(5)
        )
        expression.evaluate(runtime)
        captured = capsys.readouterr()
        output = captured.out.strip()
        assert "5" in output
        assert ">>>" in output

    def test_hello_world(self, capsys):
        runtime = self.init_runtime()
        expression = PrintExpressionNode(
            StringNode("hello, world")
        )
        expression.evaluate(runtime)
        captured = capsys.readouterr()
        output = captured.out.strip()
        assert "hello, world" in output
        assert ">>>" not in output

    def test_print_funcapp(self, capsys):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode()
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(1), NumberNode(2)]
        )
        expression = PrintExpressionNode(
            func_app
        )
        expression.evaluate(runtime)
        captured = capsys.readouterr()
        output = captured.out.strip()
        assert "(1, 2)" in output

    def test_assert(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode(ReturnNode(NumberNode(0)))
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(1), NumberNode(2)]
        )
        expression = AssertNode(
            func_app, NumberNode(0)
        )
        expression.evaluate(runtime)
        assert len(runtime.test_passed) == 1

    def test_assert_fail(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode(ReturnNode(NumberNode(0)))
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(1), NumberNode(2)]
        )
        expression = AssertNode(
            func_app, NumberNode(3)
        )
        with pytest.raises(YuiError) as excinfo:
            expression.evaluate(runtime)
        assert "failed" in str(excinfo.value.args[0])
