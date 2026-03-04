import pytest

from .test_x_yui import gen_roundtrip_test, generate_random_test, testcases

SYNTAX_NAME = 'sexpr'

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_roundtrip_sexpr(name):
    test_func = gen_roundtrip_test(SYNTAX_NAME)
    test_func(name)

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_random_sexpr(name):
    test_func = generate_random_test(SYNTAX_NAME)
    test_func(name)
