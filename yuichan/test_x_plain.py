import pytest

from .test_x_yui import gen_roundtrip_test, generate_random_test, testcases

SYNTAX_NAME = 'plain'

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_roundtrip_plain(name):
    test_func = gen_roundtrip_test(SYNTAX_NAME)
    test_func(name)

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_random_plain(name):
    test_func = generate_random_test(SYNTAX_NAME)
    test_func(name)
