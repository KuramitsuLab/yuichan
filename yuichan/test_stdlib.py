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
    # "randint(1)":           (FuncAppNode(NameNode("randint"), [1]),       0),
    # "randint(0) error":     (FuncAppNode(NameNode("randint"), [0]),       "💣not-negative-number"),
    # "randint(-1) error":    (FuncAppNode(NameNode("randint"), [-1]),      "💣not-negative-number"),
    # ── sum ──
    "sum(1,2)":             (FuncAppNode(NameNode("sum"), [1, 2]),        3),
    "sum(1,2,3)":           (FuncAppNode(NameNode("sum"), [1, 2, 3]),     6),
    "sum(1,2,3,4)":         (FuncAppNode(NameNode("sum"), [1, 2, 3, 4]), 10),
    "sum(-1,2)":            (FuncAppNode(NameNode("sum"), [-1, 2]),       1),
    "sum(1.5,2.5)":         (FuncAppNode(NameNode("sum"), [1.5, 2.5]),    4.0),
    "sum(1,2.5)":           (FuncAppNode(NameNode("sum"), [1, 2.5]),      3.5),
    "sum(2.5,1)":           (FuncAppNode(NameNode("sum"), [2.5, 1]),    3.5),
    "sum(3,-1)":           (FuncAppNode(NameNode("sum"), [3, -1]),    2),
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

    # ── type predicates ──
    "isbool(null)":         (FuncAppNode(NameNode("isbool"),   [None]),   False),
    "isbool(true)":         (FuncAppNode(NameNode("isbool"),   [True]),   True),
    "isbool(false)":        (FuncAppNode(NameNode("isbool"),   [False]),  True),
    "isbool(0)":            (FuncAppNode(NameNode("isbool"),   [0]),      False),
    "isbool(str)":          (FuncAppNode(NameNode("isbool"),   ["hello"]),   False),
    "isbool(A)":            (FuncAppNode(NameNode("isbool"),   [NameNode("A")]),   False),
    "isbool(P)":            (FuncAppNode(NameNode("isbool"),   [NameNode("P")]),   False),

    "isint(null)":           (FuncAppNode(NameNode("isint"),    [None]),   False),
    "isint(true)":           (FuncAppNode(NameNode("isint"),    [True]),   False),
    "isint(42)":             (FuncAppNode(NameNode("isint"),    [42]),        True),
    "isint(1.0)":            (FuncAppNode(NameNode("isint"),    [1.0]),       False),
    "isint(str)":            (FuncAppNode(NameNode("isint"),    ["hello"]),   False),
    "isint(A)":              (FuncAppNode(NameNode("isint"),    [NameNode("A")]),   False),
    "isint(P)":              (FuncAppNode(NameNode("isint"),    [NameNode("P")]),   False),

    "isfloat(null)":        (FuncAppNode(NameNode("isfloat"),  [None]),   False),
    "isfloat(true)":        (FuncAppNode(NameNode("isfloat"),  [True]),   False),
    "isfloat(3.14)":        (FuncAppNode(NameNode("isfloat"),  [3.14]),      True),
    "isfloat(3)":           (FuncAppNode(NameNode("isfloat"),  [3]),         False),
    "isfloat(str)":         (FuncAppNode(NameNode("isfloat"),  ["3.14"]),    False),
    "isfloat(A)":           (FuncAppNode(NameNode("isfloat"),  [NameNode("A")]),   False),
    "isfloat(P)":           (FuncAppNode(NameNode("isfloat"),  [NameNode("P")]),   False),

    "isstring(null)":       (FuncAppNode(NameNode("isstring"),   [None]),   False),
    "isstring(true)":       (FuncAppNode(NameNode("isstring"),   [True]),   False),
    "isstring(false)":      (FuncAppNode(NameNode("isstring"),   [False]),  False),
    "isstring(str)":        (FuncAppNode(NameNode("isstring"), ["hello"]),   True),
    "isstring(42)":         (FuncAppNode(NameNode("isstring"), [42]),        False),
    "isstring(3.14)":       (FuncAppNode(NameNode("isstring"), [3.14]),      False),
    "isstring(A)":          (FuncAppNode(NameNode("isstring"), [NameNode("A")]),   False),
    "isstring(P)":          (FuncAppNode(NameNode("isstring"), [NameNode("P")]),   False),
    
    "isarray(null)":        (FuncAppNode(NameNode("isarray"),  [None]),       False),
    "isarray(true)":        (FuncAppNode(NameNode("isarray"),  [True]),       False), 
    "isarray(42)":          (FuncAppNode(NameNode("isarray"),  [42]),        False),
    "isarray(3.14)":        (FuncAppNode(NameNode("isarray"),   [3.14]),      False),
    "isarray(str)":         (FuncAppNode(NameNode("isarray"),  ["hello"]),    False),
    "isarray(A)":           (FuncAppNode(NameNode("isarray"),  [NameNode("A")]), True),
    "isarray(P)":           (FuncAppNode(NameNode("isarray"),  [NameNode("P")]), False),

    "isobject(null)":       (FuncAppNode(NameNode("isobject"), [None]),       False),
    "isobject(true)":       (FuncAppNode(NameNode("isobject"), [True]),       False),
    "isobject(42)":         (FuncAppNode(NameNode("isobject"), [42]),        False),
    "isobject(1.23)":      (FuncAppNode(NameNode("isobject"), [1.23]),  False),
    "isobject(str)":        (FuncAppNode(NameNode("isobject"), ["hello"]),    False),
    "isobject(A)":          (FuncAppNode(NameNode("isobject"), [NameNode("A")]), False),
    "isobject(P)":          (FuncAppNode(NameNode("isobject"), [NameNode("P")]), True),

    # ── type conversions ──
    "toint(null)":           (FuncAppNode(NameNode("toint"),    [None]),      0),
    "toint(true)":           (FuncAppNode(NameNode("toint"),    [True]),      1),
    "toint(false)":          (FuncAppNode(NameNode("toint"),    [False]),     0),
    "toint(5)":             (FuncAppNode(NameNode("toint"),    [5]),         5),
    "toint(3.9)":           (FuncAppNode(NameNode("toint"),    [3.9]),       3),
    "toint(-3.9)":          (FuncAppNode(NameNode("toint"),    [-3.9]),      -3),
    "toint(str 42)":        (FuncAppNode(NameNode("toint"),    ["42"]),      42),
    "toint(str -3.9)":      (FuncAppNode(NameNode("toint"),    ["-3.9"]),     -3),
    "toint(\"hello\")":      (FuncAppNode(NameNode("toint"),    ["hello"]),   "💣int-conversion"),
    "toint(A)":      (FuncAppNode(NameNode("toint"),    [NameNode("A")]),   "💣int-conversion"),
    "toint(P)":      (FuncAppNode(NameNode("toint"),    [NameNode("P")]),   "💣int-conversion"),
    "toint([1,0,1])":      (FuncAppNode(NameNode("toint"),    [ArrayNode([1,0,1])]),   5),

    "tofloat(null)":         (FuncAppNode(NameNode("tofloat"),  [None]),      0.0),
    "tofloat(true)":         (FuncAppNode(NameNode("tofloat"),  [True]),      1.0),
    "tofloat(false)":        (FuncAppNode(NameNode("tofloat"),  [False]),     0.0),
    "tofloat(3)":           (FuncAppNode(NameNode("tofloat"),  [3]),         3.0),
    "tofloat(3.14)":        (FuncAppNode(NameNode("tofloat"),  [3.14]),      3.14),
    "tofloat(str 2.5)":     (FuncAppNode(NameNode("tofloat"),  ["2.5"]),     2.5),
    "tofloat(str -3.9)":    (FuncAppNode(NameNode("tofloat"),  ["-3.9"]),    -3.9),
    "tofloat(\"hello\")":    (FuncAppNode(NameNode("tofloat"),  ["hello"]),   "💣float-conversion"),
    "tofloat(A)":           (FuncAppNode(NameNode("tofloat"),  [NameNode("A")]),   0.000321),
    "tofloat(P)":           (FuncAppNode(NameNode("tofloat"),  [NameNode("P")]),   "💣float-conversion"),
    "tofloat([0,0,0,0,4,1,3])":     (FuncAppNode(NameNode("tofloat"),  [ArrayNode([0,0,0,0,4,1,3])]),   3.14),

    "tostring(null)":        (FuncAppNode(NameNode("tostring"), [None]),      "null"),
    "tostring(true)":        (FuncAppNode(NameNode("tostring"), [True]),      "true"),
    "tostring(false)":       (FuncAppNode(NameNode("tostring"), [False]),     "false"),
    "tostring(42)":         (FuncAppNode(NameNode("tostring"), [42]),        "42"),
    "tostring(3.14)":       (FuncAppNode(NameNode("tostring"), [3.14]),      "3.140000"),
    "tostring(0.14)":       (FuncAppNode(NameNode("tostring"), [0.0000011]),  "0.000001"),
    "tostring(-5)":         (FuncAppNode(NameNode("tostring"), [-5]),        "-5"),
    "tostring(str)":        (FuncAppNode(NameNode("tostring"), ["hello"]),   "hello"),
    "tostring(A)":          (FuncAppNode(NameNode("tostring"), [NameNode("A")]),   "[1, 2, 3]"),
    # "tostring(P)":          (FuncAppNode(NameNode("tostring"), [NameNode("P")]),   "{\"x\": 1, \"y\": 2, \"z\": 3}"),
    # "tostring(M)":          (FuncAppNode(NameNode("tostring"), [NameNode("M")]),   "[[1, 2], [3, 4]]]"),

    "toarray(null)":         (FuncAppNode(NameNode("toarray"),  [None]),       []),
    "toarray(true)":         (FuncAppNode(NameNode("toarray"),  [True]),       [1]),
    "toarray(false)":        (FuncAppNode(NameNode("toarray"),  [False]),     [0]),
    "toarray(42)":          (FuncAppNode(NameNode("toarray"),  [5]),        [1, 0, 1]),
    "toarray(3.14)":        (FuncAppNode(NameNode("toarray"),  [3.14]),      [0,0,0,0,4,1,3]),
    "toarray(str)":        (FuncAppNode(NameNode("toarray"),  ["ABC"]),    [65, 66, 67]),
    "toarray(A)":           (FuncAppNode(NameNode("toarray"),  [NameNode("A")]), [1, 2, 3]),
    "toarray(P)":           (FuncAppNode(NameNode("toarray"),  [NameNode("P")]), ["x", "y", "z"]),

    #"toobject(P)":          (FuncAppNode(NameNode("toobject"), [NameNode("P")]), {"x": 1, "y": 2, "z": 3}),
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
