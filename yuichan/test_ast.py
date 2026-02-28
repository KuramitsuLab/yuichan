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
from .yuiexample import get_all_examples
_all_examples = get_all_examples()

def init_runtime():
    runtime = YuiRuntime()
    runtime.setenv("a", YuiValue(1))
    runtime.setenv("x", YuiValue(1.23))
    runtime.setenv("s", YuiValue("abc"))
    runtime.setenv("A", YuiValue([1, 2, 3]))
    runtime.setenv("P", YuiValue({"x": 1, "y": 2, "z": 3}))
    runtime.setenv("M", YuiValue([[1,2], [3,4]]))
    runtime.allow_binary_ops = True
    return runtime

testcases = {
    # ConstNode
    "null":  (ConstNode(None),None),
    "true":  (ConstNode(True),True),
    "false": (ConstNode(False),False),
    # NumberNode
    "int(42)":   (NumberNode(42),42),
    "float(3.5)": (NumberNode(3.5),3.5),
    # Variable
    "a:int":   (NameNode("a"),1),
    "x:float": (NameNode("x"),1.23),
    "undefined": (NameNode("undefined"),"💣undefined-variable"),
    #String
    '""': (StringNode(""), ""),
    '"A"': (StringNode("A"), "A"),
    '"A{a}B"': (StringNode(["A", NameNode("a"), "B"]), "A1B"),
    '"{a}B"': (StringNode([NameNode("a"), "B"]), "1B"),
    '"A{a}"': (StringNode(["A", NameNode("a")]), "A1"),
    '"A{a}{a}B"': (StringNode(["A", NameNode("a"), NameNode("a"), "B"]), "A11B"),
    
    # Array
    "empty_array": (ArrayNode([]), []),
    "array": (ArrayNode([NameNode("a"), NumberNode(2), NumberNode(3)]), [1, 2, 3]),
    # Object
    "object": (ObjectNode(["x", NameNode("a"), "y", NumberNode(2), "z", NumberNode(3)]), {"x": 1, "y": 2, "z": 3}),
    # MinusNode (negative literals)
    "minus/int":   (MinusNode(NumberNode(16)), -16),
    "minus/float": (MinusNode(NumberNode(3.14)), -3.14),
    "minus/string": (MinusNode(StringNode("A")), "💣type-error"),
    # ArrayLenNode
    "len(A)": (ArrayLenNode(NameNode("A")), 3),
    "len(s)": (ArrayLenNode(NameNode("s")), 3),
    "len(P)": (ArrayLenNode(NameNode("P")), 3), 
    "len(M)": (ArrayLenNode(NameNode("M")), 2), 
    "len(0)": (ArrayLenNode(0), 1),
    "len(11)": (ArrayLenNode(11), 4), # 11 = [1, 1, 0, 1]
    "len(true)": (ArrayLenNode(True), 1),
    "len(false)": (ArrayLenNode(False), 1),
    "len(null)": (ArrayLenNode(None), 0),
    "len(103.14)": (ArrayLenNode(103.14), 9),
    "len(0.01)": (ArrayLenNode(0.01), 7),
    # GetIndexNode
    "A[0]": (GetIndexNode(NameNode("A"), 0), 1),
    "A[1]": (GetIndexNode(NameNode("A"), 1), 2),
    "A[2]": (GetIndexNode(NameNode("A"), 2), 3),
    "A[3]": (GetIndexNode(NameNode("A"), 3), "💣index-error"),
    "s[0]": (GetIndexNode(NameNode("s"), 0), ord("a")),
    "s[1]": (GetIndexNode(NameNode("s"), 1), ord("b")),
    "s[2]": (GetIndexNode(NameNode("s"), 2), ord("c")),
    "s[3]": (GetIndexNode(NameNode("s"), 3), "💣index-error"),
    "P[\"x\"]": (GetIndexNode(NameNode("P"), "x"), 1),
    "P[\"y\"]": (GetIndexNode(NameNode("P"), "y"), 2),
    "P[\"z\"]": (GetIndexNode(NameNode("P"), "z"), 3),
    "P[\"w\"]": (GetIndexNode(NameNode("P"), "w"), None),
    "M[0][0]": (GetIndexNode(GetIndexNode(NameNode("M"), 0), 0), 1),
    "M[0][1]": (GetIndexNode(GetIndexNode(NameNode("M"), 0), 1), 2),
    "M[1][0]": (GetIndexNode(GetIndexNode(NameNode("M"), 1), 0), 3),
    "M[1][1]": (GetIndexNode(GetIndexNode(NameNode("M"), 1), 1), 4),
    "M[0]": (GetIndexNode(NameNode("M"), 0), [1, 2]),
    "M[1]": (GetIndexNode(NameNode("M"), 1), [3, 4]),
    # 11 = [1, 1, 0, 1]
    "11[0]": (GetIndexNode(11, 0), 1),
    "11[1]": (GetIndexNode(11, 1), 1),
    "11[2]": (GetIndexNode(11, 2), 0),
    "11[3]": (GetIndexNode(11, 3), 1),
    # 3.14 = [0, 0, 0, 0, 4, 1, 3]
    "3.14[0]": (GetIndexNode(3.14, 0), 0),
    "3.14[1]": (GetIndexNode(3.14, 1), 0),
    "3.14[2]": (GetIndexNode(3.14, 2), 0),
    "3.14[3]": (GetIndexNode(3.14, 3), 0),
    "3.14[4]": (GetIndexNode(3.14, 4), 4),
    "3.14[5]": (GetIndexNode(3.14, 5), 1),
    "3.14[6]": (GetIndexNode(3.14, 6), 3),
    # true/false
    "true[0]": (GetIndexNode(True, 0), 1),
    "false[0]": (GetIndexNode(False, 0), 0),
    # character
    "\"b\"[0]": (GetIndexNode("b", 0), ord("b")),
    # + operator (binary)
    "a+1": (BinaryNode("+", NameNode("a"), 1), 2),
    "a-1": (BinaryNode("-", NameNode("a"), 1), 0),
    "a*2": (BinaryNode("*", NameNode("a"), 2), 2),
    "7/2": (BinaryNode("/", 7, 2), 3),
    "7%2": (BinaryNode("%", 7, 2), 1),
    "7/a": (BinaryNode("/", 7, NameNode("a")), 7),
    "7%a": (BinaryNode("%", 7, NameNode("a")), 0),
    # == operator (binary): "a" は文字列リテラル、NameNode("a") は変数
    "\"a\"==0": (BinaryNode("==", "a", 0), False),
    "\"a\"==\"a\"": (BinaryNode("==", "a", "a"), True),
    "a==0": (BinaryNode("==", NameNode("a"), 0), False),
    "a==1": (BinaryNode("==", NameNode("a"), 1), True),
    # complex operatos # a=1
    "1+2+3": (BinaryNode("+", BinaryNode("+", 1, 2), 3), 6),
    "2*3*4": (BinaryNode("*", BinaryNode("*", 2, 3), 4), 24),
    "1-2-3": (BinaryNode("-", BinaryNode("-", 1, 2), 3), -4),
    "24/2/3": (BinaryNode("/", BinaryNode("/", 24, 2), 3), 4),
    "3*2+4": (BinaryNode("+", BinaryNode("*", 3, 2), 4), 10),
    "3*(2+4)": (BinaryNode("*", 3, BinaryNode("+", 2, 4)), 18),
    "a+3*2": (BinaryNode("+", NameNode("a"), BinaryNode("*", 3, 2)), 7),
    "(a+3)*2": (BinaryNode("*", BinaryNode("+", NameNode("a"), 3), 2), 8),


    # Assignment
    "x=42": (AssignmentNode(NameNode("x"), 42), ("x", 42)),
    "y=0": (AssignmentNode(NameNode("y"), 0), ("y", 0)),
    "\"s\"=\"hello\"": (AssignmentNode(StringNode("s"), "hello"), "💣expected-variable"),
    # Increment/Decrement
    "a+=1": (IncrementNode(NameNode("a")), ("a", 2)),
    "a-=1": (DecrementNode(NameNode("a")), ("a", 0)),
    "s+=1": (IncrementNode(NameNode("s")), "💣type-error"),
    "s-=1": (DecrementNode(NameNode("s")), "💣type-error"),
    "\"s\"+=1": (IncrementNode(StringNode("s")), "💣expected-variable"),
    "\"s\"-=1": (DecrementNode(StringNode("s")), "💣expected-variable"),
    "undefined+=1": (IncrementNode(NameNode("undefined")), "💣undefined-variable"),
    "undefined-=1": (DecrementNode(NameNode("undefined")), "💣undefined-variable"),
    "A[0]+=1": (IncrementNode(GetIndexNode(NameNode("A"), 0)), ("A", [2, 2, 3])),
    "A[0]-=1": (DecrementNode(GetIndexNode(NameNode("A"), 0)), ("A", [0, 2, 3])),
    "P[\"x\"]+=1": (IncrementNode(GetIndexNode(NameNode("P"), "x")), ("P", {"x": 2, "y": 2, "z": 3})),
    "P[\"x\"]-=1": (DecrementNode(GetIndexNode(NameNode("P"), "x")), ("P", {"x": 0, "y": 2, "z": 3})),
    "M[0][0]+=1": (IncrementNode(GetIndexNode(GetIndexNode(NameNode("M"), 0), 0)), ("M", [[2,2], [3,4]])),
    "M[0][0]-=1": (DecrementNode(GetIndexNode(GetIndexNode(NameNode("M"), 0), 0)), ("M", [[0,2], [3,4]])),
    # Append
    "A.append(4)": (AppendNode(NameNode("A"), 4), ("A", [1, 2, 3, 4])),
    "s.append(98)": (AppendNode(NameNode("s"), ord("d")), ("s", "abcd")),
    "null.append(1)": (AppendNode(None, 1), '💣immutable-append'),
    "s.append(\"d\")": (AppendNode(NameNode("s"), "d"), ("s", "abcd")),
    "P.append(\"w\")": (AppendNode(NameNode("P"), "w"), ("P", {"x": 1, "y": 2, "z": 3, "w": 4})),
    # if
    "if/true": (IfNode(1, "==", 1, 1, 0), 1),
    "if/false": (IfNode(1, "==", 0, 1, 0), 0),
    "if/!=": (IfNode(1, "!=", 1, 1, 0), 0),
    "if/<": (IfNode(1, "<", 1, 1, 0), 0),
    "if/<=": (IfNode(1, "<=", 1, 1, 0), 1),
    "if/>": (IfNode(1, ">", 1, 1, 0), 0),
    "if/>=": (IfNode(1, ">=", 1, 1, 0), 1),
    "if/in": (IfNode(1, "in", NameNode("A"), 1, 0), 1),
    "if/notin": (IfNode(1, "notin", NameNode("A"), 1, 0), 0),
    # repeat/break
    "repeat": (BlockNode([
        AssignmentNode(NameNode("x"), 0),
        RepeatNode(10, BlockNode([
            IncrementNode(NameNode("x")),
        ]))
    ]), ("x", 10)),
    "repeat/break": (BlockNode([
        AssignmentNode(NameNode("x"), 0),
        RepeatNode(10, BlockNode([
            IncrementNode(NameNode("x")),
            BreakNode()
        ]))
    ]), ("x", 1)),
    "repeat/if-break": (BlockNode([
        AssignmentNode(NameNode("x"), 0),
        RepeatNode(10, BlockNode([
            IncrementNode(NameNode("x")),
            IfNode(NameNode("x"), "==", NumberNode(5),BreakNode()),
        ]))
    ]), ("x", 5)),
    "break/outside": (BlockNode([
        BreakNode()
    ]), "💣unexpected-break"),
    # Function definition and application
    "function/succ(n)": (BlockNode([
        FuncDefNode(
            NameNode("succ"),[NameNode("n")],
            BlockNode([
                IncrementNode(NameNode("n")),
                ReturnNode(NameNode("n"))
            ])
        ),
        FuncAppNode(NameNode("succ"),[NumberNode(0)]
    )]), 1),    
    "function/max(a,b)": (BlockNode([
        FuncDefNode(
            NameNode("max"),[NameNode("a"), NameNode("b")],
            IfNode(NameNode("a"), ">", NameNode("b"),
                   ReturnNode(NameNode("a")),
                   ReturnNode(NameNode("b"))
            )
        ),
        FuncAppNode(NameNode("max"),[10, 20])
    ]), 20),
    "function/mul(a,b)": (BlockNode([
        FuncDefNode(NameNode("mul"),[NameNode("a"), NameNode("b")], 
            BlockNode([
                AssignmentNode(NameNode("result"), NumberNode(0)),
                RepeatNode(NameNode("b"), BlockNode([
                    RepeatNode(NameNode("a"), BlockNode([
                        IncrementNode(NameNode("result"))
                    ])),
                ])),
                ReturnNode(NameNode("result"))
            ])
        ),
        FuncAppNode(NameNode("mul"),[NumberNode(10), NumberNode(20)])
    ]), 200),
    "function/zero()": (BlockNode([
        FuncDefNode(NameNode("zero"),[], ReturnNode(NumberNode(0))),
        FuncAppNode(NameNode("zero"),[])
    ]), 0),
    "function/factorial(n)": (BlockNode([
        FuncDefNode(NameNode("factorial"),[NameNode("n")], BlockNode([
            IfNode(NameNode("n"), "==", NumberNode(0),
                   ReturnNode(NumberNode(1))),
            ReturnNode(BinaryNode("*", NameNode("n"), FuncAppNode(
                        NameNode("factorial"), [BinaryNode("-", NameNode("n"), NumberNode(1))]
            )))
        ])),
        FuncAppNode(NameNode("factorial"),[NumberNode(5)])
    ]), 120),
    "function/no-return": (BlockNode([
        FuncDefNode(
            NameNode("point"),[NameNode("x"), NameNode("y")],
            BlockNode([])
        ),
        FuncAppNode(NameNode("point"),[NumberNode(0), NumberNode(1)])
    ]), {"x": 0, "y": 1}),
    "function/undefined": (FuncAppNode(NameNode("sub"), [NumberNode(10)]), "💣undefined-function"),
    "function_argument_mismatch": (BlockNode([
        FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            BlockNode([ReturnNode(MinusNode(MinusNode(NameNode("a"))))])
        ),
        FuncAppNode(NameNode("add"),[NumberNode(10)])
    ]), "💣mismatch-arguments"),
    "function/too-many-recursion": (BlockNode([
        FuncDefNode(
            NameNode("add"),[NameNode("a"), NameNode("b")],
            ReturnNode(FuncAppNode(NameNode("add"),[10, 20]))
        ),
        FuncAppNode(NameNode("add"),[10, 20])       
    ]), "💣too-many-recursion"),
    "Return/outside": (BlockNode([
        ReturnNode(NumberNode(0))
    ]), "💣unexpected-return"),
    "Assert/a==1": (AssertNode(NameNode("a"), 1), True),
    "Assert/a==0": (AssertNode(NameNode("a"), 0), "💣assertion-failed"),
    "Assert/s==\"abc\"": (AssertNode(NameNode("s"), "abc"), True),
    "Assert/A==[1,2,3]": (AssertNode(NameNode("A"), [1,2,3]), True),
    "Assert/P=={\"x\":1,\"y\":2,\"z\":3}": (AssertNode(NameNode("P"), {"x":1,"y":2,"z":3}), True),
    "Assert/M==[[1,2],[3,4]]": (AssertNode(NameNode("M"), [[1,2],[3,4]]), True),
    "Assert/succ(0)==1": (BlockNode([
        FuncDefNode(
            NameNode("succ"),[NameNode("n")],
            BlockNode([
                IncrementNode(NameNode("n")),
                ReturnNode(NameNode("n"))
            ])
        ),
        AssertNode(FuncAppNode(NameNode("succ"),[NumberNode(0)]), 1)
    ]), True),
}

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_ast(name):
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



binary_testcases = {
    # + operator (binary)
    "0+1": (BinaryNode("+", 0, 1), 1),
    "0.0+1.0": (BinaryNode("+", 0.0, 1.0), 1.0),
    "0+1.0": (BinaryNode("+", 0, 1.0), 1.0),
    "1.0+0": (BinaryNode("+", 1.0, 0), 1.0),
    "\"A\"+\"B\"": (BinaryNode("+", "A", "B"), "AB"),
    "A+A": (BinaryNode("+", NameNode("A"), NameNode("A")), [1, 2, 3, 1, 2, 3]),
    # - operator (binary)
    "1-0": (BinaryNode("-", 1, 0), 1),
    "1.0-0.0": (BinaryNode("-", 1.0, 0.0), 1.0),
    "1-0.0": (BinaryNode("-", 1, 0.0), 1.0),
    "1.0-0": (BinaryNode("-", 1.0, 0), 1.0),
    "s-s": (BinaryNode("-", NameNode("s"), NameNode("s")), "💣type-error"),
    "A-A": (BinaryNode("-", NameNode("A"), NameNode("A")), "💣type-error"),
    # * operator (binary)
    "2*3": (BinaryNode("*", 2, 3), 6),
    "2.0*3.0": (BinaryNode("*", 2.0, 3.0), 6.0),
    "2*3.0": (BinaryNode("*", 2, 3.0), 6.0),
    "2.0*3": (BinaryNode("*", 2.0, 3), 6.0),
    "s*s": (BinaryNode("*", NameNode("s"), NameNode("s")), "💣type-error"),
    "A*A": (BinaryNode("*", NameNode("A"), NameNode("A")), "💣type-error"),
    # / operator (binary)
    "7/2": (BinaryNode("/", 7, 2), 3),
    "7.0/2.0": (BinaryNode("/", 7.0, 2.0), 3.5),
    "7/2.0": (BinaryNode("/", 7, 2.0), 3.5),
    "7.0/2": (BinaryNode("/", 7.0, 2), 3.5),
    "7/0": (BinaryNode("/", 7, 0), "💣division-by-zero"),
    '"A"/"B"': (BinaryNode("/", "A", "B"), "💣type-error"),
    # % operator (binary)
    "7%3": (BinaryNode("%", 7, 3), 1),
    "7.0%3.0": (BinaryNode("%", 7.0, 3.0), 1.0),
    "7%3.0": (BinaryNode("%", 7, 3.0), 1.0),
    "7.0%3": (BinaryNode("%", 7.0, 3), 1.0),
    "7%0": (BinaryNode("%", 7, 0), "💣division-by-zero"),
    '"A"%"B"': (BinaryNode("%", "A", "B"), "💣type-error"),

    # == operator (binary)
    "0==0": (BinaryNode("==", 0, 0), True),
    "0==1": (BinaryNode("==", 0, 1), False),
    "0.0==0.0": (BinaryNode("==", 0.0, 0.0), True),
    "0.0==1.0": (BinaryNode("==", 0.0, 1.0), False),
    "0==1.0": (BinaryNode("==", 0, 1.0), False),  
    "1.0==0": (BinaryNode("==", 1.0, 0), False),
    "1==1.0": (BinaryNode("==", 1, 1.0), True),  
    "1.0==1": (BinaryNode("==", 1.0, 1), True),
    "\"A\"==\"A\"": (BinaryNode("==", "A", "A"), True),
    "\"A\"==\"B\"": (BinaryNode("==", "A", "B"), False),
    "A==A": (BinaryNode("==", NameNode("A"), NameNode("A")), True),
    "A==[1, 2]": (BinaryNode("==", NameNode("A"), ArrayNode([1, 2])), False),
    "x==a": (BinaryNode("==", NameNode("x"), NameNode("a")), False),
    "x==s": (BinaryNode("==", NameNode("x"), NameNode("s")), False),
    # != operator (binary)
    "0!=0": (BinaryNode("!=", 0, 0), False),
    "0!=1": (BinaryNode("!=", 0, 1), True),
    "0.0!=0.0": (BinaryNode("!=", 0.0, 0.0), False),
    "0.0!=1.0": (BinaryNode("!=", 0.0, 1.0), True),
    "0!=1.0": (BinaryNode("!=", 0, 1.0), True),  
    "1.0!=0": (BinaryNode("!=", 1.0, 0), True),
    "1!=1.0": (BinaryNode("!=", 1, 1.0), False),  
    "1.0!=1": (BinaryNode("!=", 1.0, 1), False),
    "\"A\"!=\"A\"": (BinaryNode("!=", "A", "A"), False),
    "\"A\"!=\"B\"": (BinaryNode("!=", "A", "B"), True),
    "A!=A": (BinaryNode("!=", NameNode("A"), NameNode("A")), False),
    "A!=[1, 2]": (BinaryNode("!=", NameNode("A"), ArrayNode([1, 2])), True),
    # < operator (binary)
    "0<1": (BinaryNode("<", 0, 1), True),
    "1<0": (BinaryNode("<", 1, 0), False),
    "0.0<1.0": (BinaryNode("<", 0.0, 1.0), True),
    "1.0<0.0": (BinaryNode("<", 1.0, 0.0), False),
    "0<1.0": (BinaryNode("<", 0, 1.0), True),
    "1.0<0": (BinaryNode("<", 1.0, 0), False),
    "\"A\"<\"B\"": (BinaryNode("<", "A", "B"), True),
    "\"B\"<\"A\"": (BinaryNode("<", "B", "A"), False),
    "A<[1, 2]": (BinaryNode("<", NameNode("A"), ArrayNode([1, 2])), "💣imcomparable"),
    # > operator (binary)
    "0>1": (BinaryNode(">", 0, 1), False),
    "1>0": (BinaryNode(">", 1, 0), True),
    "0.0>1.0": (BinaryNode(">", 0.0, 1.0), False),
    "1.0>0.0": (BinaryNode(">", 1.0, 0.0), True),
    "0>1.0": (BinaryNode(">", 0, 1.0), False),
    "1.0>0": (BinaryNode(">", 1.0, 0), True),
    "\"A\">\"B\"": (BinaryNode(">", "A", "B"), False),
    "\"B\">\"A\"": (BinaryNode(">", "B", "A"), True),
    "\"A\">\"A\"": (BinaryNode(">", "A", "A"), False),
    "A>[1, 2]": (BinaryNode(">", NameNode("A"), ArrayNode([1, 2])), "💣imcomparable"),
    # <= operator (binary)
    "0<=1": (BinaryNode("<=", 0, 1), True),
    "1<=0": (BinaryNode("<=", 1, 0), False),
    "1<=1": (BinaryNode("<=", 1, 1), True),
    "0.0<=1.0": (BinaryNode("<=", 0.0, 1.0), True),
    "1.0<=0.0": (BinaryNode("<=", 1.0, 0.0), False),
    "0<=1.0": (BinaryNode("<=", 0, 1.0), True),
    "1.0<=0": (BinaryNode("<=", 1.0, 0), False),
    "1<=1.0": (BinaryNode("<=", 1, 1.0), True),
    "1.0<=1": (BinaryNode("<=", 1.0, 1), True),        
    "\"A\"<=\"B\"": (BinaryNode("<=", "A", "B"), True),
    "\"B\"<=\"A\"": (BinaryNode("<=", "B", "A"), False),
    "\"A\"<=\"A\"": (BinaryNode("<=", "A", "A"), True),
    "A<=[1, 2]": (BinaryNode("<=", NameNode("A"), ArrayNode([1, 2])), "💣imcomparable"),
    # >= operator (binary)
    "0>=1": (BinaryNode(">=", 0, 1), False),
    "1>=0": (BinaryNode(">=", 1, 0), True),
    "0.0>=1.0": (BinaryNode(">=", 0.0, 1.0), False),
    "1.0>=0.0": (BinaryNode(">=", 1.0, 0.0), True),
    "0>=1.0": (BinaryNode(">=", 0, 1.0), False),
    "1.0>=0": (BinaryNode(">=", 1.0, 0), True),
    "\"A\">=\"B\"": (BinaryNode(">=", "A", "B"), False),
    "\"B\">=\"A\"": (BinaryNode(">=", "B", "A"), True),
    "\"A\">=\"A\"": (BinaryNode(">=", "A", "A"), True),
    "A>=[1, 2]": (BinaryNode(">=", NameNode("A"), ArrayNode([1, 2])), "💣imcomparable"),
}

@pytest.mark.parametrize("name", list(binary_testcases.keys()))
def test_binary_ops(name):
    node, expected = binary_testcases[name]
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
