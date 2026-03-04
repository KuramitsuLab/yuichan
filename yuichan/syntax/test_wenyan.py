import pytest

from .test_yui import gen_roundtrip_test, generate_random_test, testcases

SYNTAX_NAME = 'wenyan'

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_roundtrip_wenyan(name):
    test_func = gen_roundtrip_test(SYNTAX_NAME)
    test_func(name)

@pytest.mark.parametrize("name", list(testcases.keys()))
def test_random_wenyan(name):
    test_func = generate_random_test(SYNTAX_NAME)
    test_func(name)
