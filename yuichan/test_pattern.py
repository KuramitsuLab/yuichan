import pytest
from .yuiparser import (
    get_example_from_pattern
)

class TestGetFirstMatchString:

    def test_basic(self):
        pattern = r'abc'
        result = get_example_from_pattern(pattern)
        assert result == 'abc'

    def test_escape(self):
        pattern = r'\d+'
        result = get_example_from_pattern(pattern)
        assert result == '1'

    def test_charclass(self):
        pattern = r'[xyz]a'
        result = get_example_from_pattern(pattern)
        assert result == 'xa'

    def test_charclass2(self):
        pattern = r'a[AB]?b'
        result = get_example_from_pattern(pattern)
        assert result == 'ab'


    def test_optional(self):
        pattern = r'colou?r'
        result = get_example_from_pattern(pattern)
        assert result == 'color'  

    def test_alternation(self):
        pattern = r'foo|bar|baz'
        result = get_example_from_pattern(pattern)
        assert result == 'foo'

    def test_space(self):
        pattern = r'foo\s+'
        result = get_example_from_pattern(pattern)
        assert result == 'foo '

    def test_bracket(self):
        pattern = r'\['
        result = get_example_from_pattern(pattern)
        assert result == '['

    def test_bracket(self):
        pattern = r'\|'
        result = get_example_from_pattern(pattern)
        assert result == '|'

    def test_emoji(self):
        pattern = r'[⬇️⬆️]'
        result = get_example_from_pattern(pattern)
        assert result == '⬇️'
    
    def test_emoji2(self):
        pattern = r'⬇️⬆️?⬆️'
        result = get_example_from_pattern(pattern)
        assert result == '⬇️⬆️'

    def test_group(self):
        pattern = r'ab([A-Z]+)(XXX|XYZ)'
        result = get_example_from_pattern(pattern)
        assert result == 'abAXXX'

    def test_group2(self):
        pattern = r'ab([A-Z]+)?XXX'
        result = get_example_from_pattern(pattern)
        assert result == 'abXXX'
