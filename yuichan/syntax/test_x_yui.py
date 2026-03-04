import pytest

from ..test_ast import testcases, init_runtime

from ..yuiparser import BlockNode
from ..yuisyntax import load_syntax
from ..yuicoding import CodingVisitor
from ..yuiruntime import YuiRuntime, YuiError
from ..yuitypes import types

syntax = load_syntax('yui')

def gen_roundtrip_test(syntax):
    syntax = load_syntax(syntax)

    def test_roundtrip(name):
        node, expected = testcases[name]
        if isinstance(node, BlockNode):
            node.top_level = True

        visitor = CodingVisitor(syntax)
        code = visitor.emit(node)
        print(f"Generated code for {name}:\n{code}\n")
        runtime = init_runtime()
        try:   
            result = runtime.exec(code, syntax=syntax, eval_mode=True)
            if isinstance(expected, tuple):
                key, value = expected
                assert types.unbox(runtime.getenv(key)) == value
            else:
                assert types.unbox(result) == expected
        except YuiError as e:
            msg = f"💣{e.messages[0]}"
            assert msg == expected
    return test_roundtrip

def generate_random_test(syntax):
    syntax = load_syntax(syntax)

    def test_random(name):
        node, expected = testcases[name]
        if isinstance(node, BlockNode):
            node.top_level = True

        visitor = CodingVisitor(syntax)
        code0 = visitor.emit(node)
        for random_seed in range(100):
            code = visitor.emit(node, random_seed=random_seed)
            if code != code0:
                break
        if code == code0:
            pytest.skip(f"same: {code0}")
        print(f"Generated code for {name}:\n{code}\n")
        runtime = init_runtime()
        try:   
            result = runtime.exec(code, syntax=syntax, eval_mode=True)
            if isinstance(expected, tuple):
                key, value = expected
                assert types.unbox(runtime.getenv(key)) == value
            else:
                assert types.unbox(result) == expected
        except YuiError as e:
            msg = f"💣{e.messages[0]}"
            assert msg == expected
    return test_random

SYNTAX_NAME='yui'

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_roundtrip_yui(name):
    test_func = gen_roundtrip_test(SYNTAX_NAME)
    test_func(name)

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_random_yui(name):
    test_func = generate_random_test(SYNTAX_NAME)
    test_func(name)
