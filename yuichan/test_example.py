"""
Round-trip tests: generate code from yuiexample ASTs, then parse the
generated code back.  A test fails if parsing raises an exception.
"""
import pytest
from .yuiexample import get_all_examples
from .yuiparser import Source
from .yuisyntax import load_syntax

SYNTAXES = ['yui', 'pylike', 'emoji']
_all_examples = get_all_examples()
_examples_by_name = {ex.name: ex for ex in _all_examples}

_params = [
    pytest.param(syntax_name, example.name, id=f"{syntax_name}/{example.name}")
    for syntax_name in SYNTAXES
    for example in _all_examples
]


@pytest.mark.parametrize("syntax_name,example_name", _params)
def test_generate_then_parse(syntax_name, example_name):
    """Generate code from an example AST and verify it can be parsed back."""
    syntax = load_syntax(syntax_name)
    example = _examples_by_name[example_name]
    code = example.generate(syntax)
    source = Source(code, syntax=syntax)
    source.parse("@TopLevel")
