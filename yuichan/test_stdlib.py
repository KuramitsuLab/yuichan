import math
import pytest

from .yuitypes import YuiError, YuiValue, YuiType, types
from .yuiruntime import YuiRuntime
from .yuiast import (
    ConstNode, NumberNode, StringNode,
    ArrayNode, ObjectNode,
    NameNode,
    MinusNode, ArrayLenNode, GetIndexNode, BinaryNode,
    AssignmentNode, IncrementNode, DecrementNode, AppendNode,
    BlockNode, IfNode, RepeatNode, BreakNode,
    FuncDefNode, FuncAppNode, ReturnNode,
    PrintExpressionNode, AssertNode, CatchNode
)

def init_runtime():
    runtime = YuiRuntime()
    runtime.setenv("a", YuiValue(1))
    runtime.setenv("x", YuiValue(1.23))
    runtime.setenv("s", YuiValue("abc"))
    runtime.setenv("A", YuiValue([1, 2, 3]))
    runtime.setenv("P", YuiValue({"x": 1, "y": 2, "z": 3}))
    runtime.setenv("M", YuiValue([[1,2], [3,4]]))
    runtime.allow_binary_ops = True
    runtime.load_stdlib()
    return runtime

testcases = {
    # ── abs ──
    "abs(5)":               (FuncAppNode(NameNode("abs"), [5]),           5),
    "abs(-3)":              (FuncAppNode(NameNode("abs"), [-3]),          3),
    "abs(0)":               (FuncAppNode(NameNode("abs"), [0]),           0),
    "abs(1.5)":             (FuncAppNode(NameNode("abs"), [1.5]),         1.5),
    "abs(-2.5)":            (FuncAppNode(NameNode("abs"), [-2.5]),        2.5),
    "abs() error":          (FuncAppNode(NameNode("abs"), []),            "💣mismatch-argument"),
    "abs(1,2) error":       (FuncAppNode(NameNode("abs"), [1, 2]),        "💣mismatch-argument"),
    "abs(str) error":       (FuncAppNode(NameNode("abs"), ["hello"]),     "💣type-error"),
    # ── sqrt ──
    "sqrt(4)":              (FuncAppNode(NameNode("sqrt"), [4]),          2.0),
    "sqrt(9)":              (FuncAppNode(NameNode("sqrt"), [9]),          3.0),
    "sqrt(0)":              (FuncAppNode(NameNode("sqrt"), [0]),          0.0),
    "sqrt(2)":              (FuncAppNode(NameNode("sqrt"), [2]),          math.sqrt(2)),
    "sqrt(2.0)":            (FuncAppNode(NameNode("sqrt"), [2.0]),        math.sqrt(2.0)),
    "sqrt(-1) error":       (FuncAppNode(NameNode("sqrt"), [-1]),         "💣not-negative-number"),
    "sqrt() error":         (FuncAppNode(NameNode("sqrt"), []),           "💣mismatch-argument"),
    "sqrt(1,2) error":      (FuncAppNode(NameNode("sqrt"), [1, 2]),       "💣mismatch-argument"),
    "sqrt(str) error":      (FuncAppNode(NameNode("sqrt"), ["hello"]),    "💣type-error"),
    # ── randint ──
    "randint(1)":           (FuncAppNode(NameNode("randint"), [1]),       0),
    "randint(0) error":     (FuncAppNode(NameNode("randint"), [0]),       "💣not-negative-number"),
    "randint(-1) error":    (FuncAppNode(NameNode("randint"), [-1]),      "💣not-negative-number"),
    # ── sum ──
    "sum(1,2)":             (FuncAppNode(NameNode("sum"), [1, 2]),        3),
    "sum(1,2,3)":           (FuncAppNode(NameNode("sum"), [1, 2, 3]),     6),
    "sum(1,2,3,4)":         (FuncAppNode(NameNode("sum"), [1, 2, 3, 4]), 10),
    "sum(-1,2)":            (FuncAppNode(NameNode("sum"), [-1, 2]),       1),
    "sum(1.5,2.5)":         (FuncAppNode(NameNode("sum"), [1.5, 2.5]),    4.0),
    "sum(1,2.5)":           (FuncAppNode(NameNode("sum"), [1, 2.5]),      3.5),
    "sum(A)":               (FuncAppNode(NameNode("sum"), [NameNode("A")]), 6),
    "sum() error":          (FuncAppNode(NameNode("sum"), []),            "💣mismatch-argument"),
    # ── diff ──
    "diff(10,3)":           (FuncAppNode(NameNode("diff"), [10, 3]),      7),
    "diff(10,3,2)":         (FuncAppNode(NameNode("diff"), [10, 3, 2]),   5),
    "diff(3,10)":           (FuncAppNode(NameNode("diff"), [3, 10]),      -7),
    "diff(5.0,2.0)":        (FuncAppNode(NameNode("diff"), [5.0, 2.0]),   3.0),
    "diff(5,2.5)":          (FuncAppNode(NameNode("diff"), [5, 2.5]),     2.5),
    "diff(5.0,2)":          (FuncAppNode(NameNode("diff"), [5.0, 2]),     3.0),
    # ── product ──
    "product(3,4)":         (FuncAppNode(NameNode("product"), [3, 4]),    12),
    "product(2,3,4)":       (FuncAppNode(NameNode("product"), [2, 3, 4]), 24),
    "product(2,3,4,5)":     (FuncAppNode(NameNode("product"), [2, 3, 4, 5]), 120),
    "product(5,0)":         (FuncAppNode(NameNode("product"), [5, 0]),    0),
    "product(2.0,3.0)":     (FuncAppNode(NameNode("product"), [2.0, 3.0]), 6.0),
    "product(2,3.0)":       (FuncAppNode(NameNode("product"), [2, 3.0]),  6.0),
    "product(A)":           (FuncAppNode(NameNode("product"), [NameNode("A")]), 6),
    # ── quotient ──
    "quotient(10,3)":       (FuncAppNode(NameNode("quotient"), [10, 3]),  3),
    "quotient(10,2)":       (FuncAppNode(NameNode("quotient"), [10, 2]),  5),
    "quotient(100,5,2)":    (FuncAppNode(NameNode("quotient"), [100, 5, 2]), 10),
    "quotient(10.0,4.0)":   (FuncAppNode(NameNode("quotient"), [10.0, 4.0]), 2.5),
    "quotient(10,4.0)":     (FuncAppNode(NameNode("quotient"), [10, 4.0]),   2.5),
    "quotient(10,0) error":   (FuncAppNode(NameNode("quotient"), [10, 0]),    "💣division-by-zero"),
    "quotient(10.0,0.0) error":(FuncAppNode(NameNode("quotient"), [10.0, 0.0]), "💣division-by-zero"),
    # ── remainder ──
    "remainder(10,3)":      (FuncAppNode(NameNode("remainder"), [10, 3]), 1),
    "remainder(9,3)":       (FuncAppNode(NameNode("remainder"), [9, 3]),  0),
    "remainder(100,7,3)":   (FuncAppNode(NameNode("remainder"), [100, 7, 3]), 2),
    "remainder(5.5,2.0)":   (FuncAppNode(NameNode("remainder"), [5.5, 2.0]), 1.5),
    "remainder(10,3.0)":    (FuncAppNode(NameNode("remainder"), [10, 3.0]),  1.0),
    "remainder(10,0) error":(FuncAppNode(NameNode("remainder"), [10, 0]), "💣division-by-zero"),
    # ── max / min ──
    "max(3,1,4,1,5)":      (FuncAppNode(NameNode("max"), [3, 1, 4, 1, 5]), 5),
    "max(-3,-1)":           (FuncAppNode(NameNode("max"), [-3, -1]),      -1),
    "max(1.5,2.5)":         (FuncAppNode(NameNode("max"), [1.5, 2.5]),    2.5),
    "max(1,3.0,2)":         (FuncAppNode(NameNode("max"), [1, 3.0, 2]),   3.0),
    "max(A)":               (FuncAppNode(NameNode("max"), [NameNode("A")]), 3),
    "max() error":          (FuncAppNode(NameNode("max"), []),            "💣mismatch-argument"),
    "min(3,1,4)":           (FuncAppNode(NameNode("min"), [3, 1, 4]),     1),
    "min(-3,-1)":           (FuncAppNode(NameNode("min"), [-3, -1]),      -3),
    "min(1.5,0.5)":         (FuncAppNode(NameNode("min"), [1.5, 0.5]),    0.5),
    "min(1.5,2,0.5)":       (FuncAppNode(NameNode("min"), [1.5, 2, 0.5]), 0.5),
    "min(A)":               (FuncAppNode(NameNode("min"), [NameNode("A")]), 1),
    "min() error":          (FuncAppNode(NameNode("min"), []),            "💣mismatch-argument"),
    # ── bitwise ──
    "and(0b1010,0b1100)":   (FuncAppNode(NameNode("and"),  [0b1010, 0b1100]), 0b1000),
    "or(0b1010,0b1100)":    (FuncAppNode(NameNode("or"),   [0b1010, 0b1100]), 0b1110),
    "xor(0b1010,0b1100)":   (FuncAppNode(NameNode("xor"),  [0b1010, 0b1100]), 0b0110),
    "xor(0b1010,0b1010)":   (FuncAppNode(NameNode("xor"),  [0b1010, 0b1010]), 0),
    "xor(0b1010,0b1100,0b0110)": (FuncAppNode(NameNode("xor"), [0b1010, 0b1100, 0b0110]), 0),
    "and(0b1111,0b0000)":   (FuncAppNode(NameNode("and"),  [0b1111, 0b0000]), 0),
    "and(0b1010,0b1100,0b1110)": (FuncAppNode(NameNode("and"), [0b1010, 0b1100, 0b1110]), 0b1000),
    "or(0b1010,0)":         (FuncAppNode(NameNode("or"),   [0b1010, 0]),  0b1010),
    "or(0b1010,0b1100,0b0001)":  (FuncAppNode(NameNode("or"),  [0b1010, 0b1100, 0b0001]), 0b1111),
    "not(0)":               (FuncAppNode(NameNode("not"),  [0]),          -1),
    "not(-1)":              (FuncAppNode(NameNode("not"),  [-1]),         0),
    "not(1)":               (FuncAppNode(NameNode("not"),  [1]),          -2),
    "shl(1,3)":             (FuncAppNode(NameNode("shl"),  [1, 3]),       8),
    "shl(5,0)":             (FuncAppNode(NameNode("shl"),  [5, 0]),       5),
    "shr(8,3)":             (FuncAppNode(NameNode("shr"),  [8, 3]),       1),
    "shr(5,0)":             (FuncAppNode(NameNode("shr"),  [5, 0]),       5),
    # ── type predicates ──
    "isint(42)":            (FuncAppNode(NameNode("isint"),    [42]),        True),
    "isint(1.0)":           (FuncAppNode(NameNode("isint"),    [1.0]),       False),
    "isint(str)":           (FuncAppNode(NameNode("isint"),    ["hello"]),   False),
    "isfloat(3.14)":        (FuncAppNode(NameNode("isfloat"),  [3.14]),      True),
    "isfloat(3)":           (FuncAppNode(NameNode("isfloat"),  [3]),         False),
    "isfloat(str)":         (FuncAppNode(NameNode("isfloat"),  ["3.14"]),    False),
    "isstring(str)":        (FuncAppNode(NameNode("isstring"), ["hello"]),   True),
    "isstring(42)":         (FuncAppNode(NameNode("isstring"), [42]),        False),
    "isstring(3.14)":       (FuncAppNode(NameNode("isstring"), [3.14]),      False),
    "isarray(A)":           (FuncAppNode(NameNode("isarray"),  [NameNode("A")]), True),
    "isarray(42)":          (FuncAppNode(NameNode("isarray"),  [42]),        False),
    "isobject(P)":          (FuncAppNode(NameNode("isobject"), [NameNode("P")]), True),
    "isobject(42)":         (FuncAppNode(NameNode("isobject"), [42]),        False),
    "isobject(A)":          (FuncAppNode(NameNode("isobject"), [NameNode("A")]), False),
    # ── type conversions ──
    "toint(3.9)":           (FuncAppNode(NameNode("toint"),    [3.9]),       3),
    "toint(-3.9)":          (FuncAppNode(NameNode("toint"),    [-3.9]),      -3),
    "toint(5)":             (FuncAppNode(NameNode("toint"),    [5]),         5),
    "tofloat(3)":           (FuncAppNode(NameNode("tofloat"),  [3]),         3.0),
    "tofloat(3.14)":        (FuncAppNode(NameNode("tofloat"),  [3.14]),      3.14),
    "tofloat(str 2.5)":     (FuncAppNode(NameNode("tofloat"),  ["2.5"]),     2.5),
    "tostring(42)":         (FuncAppNode(NameNode("tostring"), [42]),        "42"),
    "tostring(3.14)":       (FuncAppNode(NameNode("tostring"), [3.14]),      "3.140000"),
    "tostring(-5)":         (FuncAppNode(NameNode("tostring"), [-5]),        "-5"),
    "toarray(A)":           (FuncAppNode(NameNode("toarray"),  [NameNode("A")]), [1, 2, 3]),
    "toobject(P)":          (FuncAppNode(NameNode("toobject"), [NameNode("P")]), {"x": 1, "y": 2, "z": 3}),
}


@pytest.mark.parametrize("name", list(testcases.keys()))
def test_stdlib2(name):
    node, expected = testcases[name]
    runtime = init_runtime()
    if isinstance(expected, str) and expected.startswith("💣"):
        node = CatchNode(node)
    if isinstance(expected, tuple):
        key, value = expected
        result = node.evaluate(runtime)
        assert types.unbox(runtime.getenv(key)) == value
    else:
        result = node.evaluate(runtime)
        assert types.unbox(result) == expected
