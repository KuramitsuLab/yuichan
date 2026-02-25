import pytest

from .yuitypes import YuiError, YuiValue, YuiType, types
from .yuiruntime import YuiRuntime
from .yuiast import (
    ConstNode, NumberNode, StringNode,
    ArrayNode, ObjectNode,
    NameNode,
    MinusNode, ArrayLenNode, GetIndexNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode,
)
from .yuiexample import get_all_examples
_all_examples = get_all_examples()

class TestLiteral:
    """式の評価に関するテストクラス"""

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        return runtime  

    def test_int(self):
        runtime = self.init_runtime()
        expression = NumberNode(42)
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 42

    def test_float(self):
        runtime = self.init_runtime()
        expression = NumberNode(42.0)
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 42.0

    def test_string(self):
        runtime = self.init_runtime()
        expression = StringNode("A")
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == "A"

    def test_string_interpolation(self):
        runtime = self.init_runtime()
        expression = StringNode(["A", NumberNode(1), "B"])
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == "A1B"

    def test_array(self):
        runtime = self.init_runtime()
        expression = ArrayNode([1, 2, 3])
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == [1, 2, 3]

    def test_object(self):
        runtime = self.init_runtime()
        expression = ObjectNode([StringNode("x"), NumberNode(1), StringNode("y"), NumberNode(2), StringNode("z"), NumberNode(3)])
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == {"x": 1, "y": 2, "z": 3}

class TestVariable:
    """式の評価に関するテストクラス"""

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        return runtime  

    def test_variable(self):
        runtime = self.init_runtime()
        expression = NameNode("x")
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 1

    def test_undefined_variable(self):
        runtime = self.init_runtime()
        expression = NameNode("y")
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
            result = types.unbox(result)
            assert result == 1
        assert "undefined" in str(excinfo.value.args[0])
        assert "variable" in str(excinfo.value.args[0])

class TestUnaryOperator:
    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        return runtime
    
    def test_minus_int(self):
        runtime = self.init_runtime()
        expression = MinusNode(NumberNode(1))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == -1

    def test_minus_float(self):
        runtime = self.init_runtime()
        expression = MinusNode(NumberNode(1.0))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == -1.0

    def test_minus_string(self):
        runtime = self.init_runtime()
        expression = MinusNode(StringNode("A"))
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
            result = types.unbox(result)
            assert result == "A"
        assert "type" in str(excinfo.value)

    def test_length_array(self):
        runtime = self.init_runtime()
        expression = ArrayLenNode(NameNode("A"))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 3

    def test_length_string(self):
        runtime = self.init_runtime()
        expression = ArrayLenNode(StringNode("abc"))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 3

    def test_length_int(self):
        runtime = self.init_runtime()
        expression = ArrayLenNode(NumberNode(1))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 1  # 可変長: 1 は [1] (1ビット)

class TestGetIndex:
    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def test_get_array(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("A"), NumberNode(1))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 2

    def test_get_string(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("s"), NumberNode(1))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 98 # 'b'のASCIIコード

    def test_get_charcode(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(StringNode("b"), NumberNode(0))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 98 # 'b'のASCIIコード

    def test_object_string(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("O"), StringNode("y"))
        result = expression.evaluate(runtime)
        result = types.unbox(result)
        assert result == 2

    def test_get_array_out_of_index(self):
        runtime = self.init_runtime()
        expression = GetIndexNode(NameNode("A"), NumberNode(3))
        with pytest.raises(YuiError) as excinfo:    
            result = expression.evaluate(runtime)
        assert "index" in str(excinfo.value)

class TestAssignment:

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def test_variable_assignment(self):
        runtime = self.init_runtime()
        statement = AssignmentNode(NameNode("A"), NumberNode(3))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("A")) == 3

    def test_string_assignment(self):
        runtime = self.init_runtime()
        with pytest.raises(YuiError) as excinfo:
            statement = AssignmentNode(StringNode("A"), NumberNode(3))
            statement.evaluate(runtime)
        assert "expected" in str(excinfo.value)
        assert "variable" in str(excinfo.value)

    def test_variable_increment(self):
        runtime = self.init_runtime()
        statement = IncrementNode(NameNode("x"))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 2

    def test_variable_decrement(self):
        runtime = self.init_runtime()
        statement = DecrementNode(NameNode("x"))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 0

    def test_array_assignment(self):
        runtime = self.init_runtime()
        statement = AssignmentNode(GetIndexNode(NameNode("A"), NumberNode(0)), NumberNode(3))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("A").get_item(0)) == 3

    def test_array_increment(self):
        runtime = self.init_runtime()
        statement = IncrementNode(GetIndexNode(NameNode("A"), NumberNode(0)))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("A").get_item(0)) == 2

    def test_array_decrement(self):
        runtime = self.init_runtime()
        statement = DecrementNode(GetIndexNode(NameNode("A"), NumberNode(1)))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("A").get_item(1)) == 1

    def test_object_assignment(self):
        runtime = self.init_runtime()
        statement = AssignmentNode(GetIndexNode(NameNode("O"), StringNode("x")), NumberNode(3))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("O").get_item("x")) == 3

class TestAppend:

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def test_append_array(self):
        runtime = self.init_runtime()
        statement = AppendNode(NameNode("A"), NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("A").get_item(3)) == 0

    def test_append_string(self):
        runtime = self.init_runtime()
        statement = AppendNode(NameNode("s"), NumberNode(ord("d")))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("s").get_item(3)) == ord("d")

    def test_append_int(self):
        # 可変長: x=YuiValue(1)=[1]、ビット1を追加すると[1,1]=3
        runtime = self.init_runtime()
        statement = AppendNode(NameNode("x"), NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 3

class TestIfCondition:

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def make_if_statement(self, left, operator, right):
        return IfNode(left, operator, right,
            AssignmentNode(NameNode("result"), 1),
            AssignmentNode(NameNode("result"), 0)
        )

    def test_if_eq(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "==", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "==", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

    def test_if_ne(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "!=", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "!=", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

    def test_if_lt(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<", NumberNode(2))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

    def test_if_le(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<=", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<=", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), "<=", NumberNode(2))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

    def test_if_gt(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">", NumberNode(2))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

    def test_if_ge(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">=", NumberNode(0))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 1

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">=", NumberNode(1))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1

        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("x"), ">=", NumberNode(2))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

    def test_if_eq_string(self):
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("s"), "==", StringNode("abc"))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1
        runtime = self.init_runtime()
        statement = self.make_if_statement(NameNode("s"), "==", StringNode("ABC"))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0

    def test_if_eq_float(self):
        runtime = self.init_runtime()
        runtime.setenv("f", YuiValue(3.14))
        statement = self.make_if_statement(NameNode("f"), "==", NumberNode(3.14))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 1
        runtime = self.init_runtime()
        runtime.setenv("f", YuiValue(3.1))
        statement = self.make_if_statement(NameNode("f"), "==", NumberNode(3.145))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("result")) == 0


class TestStatement:

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def test_block(self):
        runtime = self.init_runtime()
        statement = BlockNode([
            AssignmentNode(NameNode("x"), NumberNode(10)),
            IncrementNode(NameNode("x")),
            IncrementNode(NameNode("x")),
        ])
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 12
    
    def test_repeat(self):
        runtime = self.init_runtime()
        statement = RepeatNode(3,IncrementNode(NameNode("x")))
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 4

    def test_repeat_break(self):
        runtime = self.init_runtime()
        statement = RepeatNode(
            NumberNode(10),
            BlockNode([
                IncrementNode(NameNode("x")),
                IfNode(
                    left=NameNode("x"),
                    operator="==",
                    right=NumberNode(4),
                    then_block=BlockNode([BreakNode()])
                )
            ])
        )
        statement.evaluate(runtime)
        assert types.unbox(runtime.getenv("x")) == 4

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
            BlockNode([])
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
        expression = AssertNode(NameNode("x"), NumberNode(1))
        expression.evaluate(runtime)
        assert len(runtime.test_passed) == 1

    def test_assert_fail(self):
        runtime = self.init_runtime()
        expression = AssertNode(NameNode("x"), NumberNode(0))
        with pytest.raises(YuiError) as excinfo:
            expression.evaluate(runtime)
            assert len(runtime.test_passed) == 0
        assert "failed" in str(excinfo.value.args[0])

class TestAssert:
    """AssertNode の型別テスト"""

    def rt(self):
        return YuiRuntime()

    # ── boolean ──────────────────────────────────────────────
    def test_bool_true(self):
        rt = self.rt()
        AssertNode(ConstNode(True), ConstNode(True)).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_bool_false(self):
        rt = self.rt()
        AssertNode(ConstNode(False), ConstNode(False)).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_bool_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(ConstNode(True), ConstNode(False)).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    # ── int ──────────────────────────────────────────────────
    def test_int_equal(self):
        rt = self.rt()
        AssertNode(NumberNode(42), NumberNode(42)).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_int_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(NumberNode(1), NumberNode(2)).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    def test_int_vs_bool(self):
        """int と bool は等値にならない"""
        rt = self.rt()
        with pytest.raises(YuiError):
            AssertNode(NumberNode(1), ConstNode(True)).evaluate(rt)

    # ── float ─────────────────────────────────────────────────
    def test_float_equal(self):
        rt = self.rt()
        AssertNode(NumberNode(3.14), NumberNode(3.14)).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_float_rounding(self):
        """小数は小数点6桁で丸めて比較"""
        rt = self.rt()
        AssertNode(NumberNode(1.0000001), NumberNode(1.0000002)).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_float_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(NumberNode(3.14), NumberNode(3.15)).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    # ── string ────────────────────────────────────────────────
    def test_string_equal(self):
        rt = self.rt()
        AssertNode(StringNode("hello"), StringNode("hello")).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_string_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(StringNode("hello"), StringNode("world")).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    # ── array ─────────────────────────────────────────────────
    def test_array_equal(self):
        rt = self.rt()
        AssertNode(ArrayNode([1, 2, 3]), ArrayNode([1, 2, 3])).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_array_nested(self):
        rt = self.rt()
        AssertNode(
            ArrayNode([ArrayNode([1, 2]), ArrayNode([3, 4])]),
            ArrayNode([ArrayNode([1, 2]), ArrayNode([3, 4])]),
        ).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_array_charcode_vs_string(self):
        """文字コード配列と文字列は等値になる"""
        rt = self.rt()
        # [72, 105] == "Hi"
        AssertNode(ArrayNode([72, 105]), StringNode("Hi")).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_array_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(ArrayNode([1, 2, 3]), ArrayNode([1, 2, 4])).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    def test_array_length_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(ArrayNode([1, 2]), ArrayNode([1, 2, 3])).evaluate(rt)
        assert "failed" in str(exc.value.args[0])

    # ── object ────────────────────────────────────────────────
    def test_object_equal(self):
        rt = self.rt()
        obj = lambda: ObjectNode([StringNode("x"), NumberNode(1), StringNode("y"), NumberNode(2)])
        AssertNode(obj(), obj()).evaluate(rt)
        assert len(rt.test_passed) == 1

    def test_object_mismatch(self):
        rt = self.rt()
        with pytest.raises(YuiError) as exc:
            AssertNode(
                ObjectNode([StringNode("x"), NumberNode(1)]),
                ObjectNode([StringNode("x"), NumberNode(2)]),
            ).evaluate(rt)
        assert "failed" in str(exc.value.args[0])


class TestFunction:

    def init_runtime(self):
        runtime = YuiRuntime()
        runtime.setenv("x", YuiValue(1))
        runtime.setenv("s", YuiValue("abc"))
        runtime.setenv("A", YuiValue([1, 2, 3]))
        runtime.setenv("O", YuiValue({"x": 1, "y": 2, "z": 3}))
        return runtime

    def test_function(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode([ReturnNode(MinusNode(MinusNode(NameNode("a"))))])
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(10), NumberNode(20)]
        )
        result = func_app.evaluate(runtime)
        assert types.unbox(result) == 10

    def test_function_return_none(self):
        runtime = self.init_runtime()
        func_def = FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode([
                AssignmentNode(NameNode("a"), 1),
                AssignmentNode(NameNode("c"), 3)
            ])
        )
        func_def.evaluate(runtime)
        func_app = FuncAppNode(
            name=NameNode("add"),
            arguments=[NumberNode(0), NumberNode(1)]
        )
        result = func_app.evaluate(runtime)
        assert types.is_object(result)
        result = types.unbox(result)
        assert result["a"] == 1
        assert result["b"] == 1
        assert result["c"] == 3

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
            BlockNode([ReturnNode(MinusNode(MinusNode(NameNode("a"))))])
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

    
class TestExample:

    def get_example_ast(self, name):
        from .yuiexample import get_all_examples
        examples = get_all_examples()
        for example in examples:
            if name in example.name:
                return example.ast_node

    def test_example_hello_world(self):
        runtime = YuiRuntime()
        program = self.get_example_ast("hello")
        program.evaluate(runtime)

    @pytest.mark.parametrize("example", _all_examples, ids=lambda e: e.name)
    def test_all_examples(self, example):
        runtime = YuiRuntime()
        example.ast_node.evaluate(runtime)

