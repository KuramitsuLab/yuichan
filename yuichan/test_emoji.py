import pytest
from .yuiparser import (
    Source, parse, YuiError, load_syntax 
)

emoji_syntax = load_syntax('emoji')

class TestParseStatementNode:

    def test_Assignment_emoji(self):
        source = Source("x ⬅️ 1 # コメント", syntax=emoji_syntax)
        assignment_node = parse("@Assignment", source, pc={})
        assert str(assignment_node) == "x ⬅️ 1"

    def test_Increment_emoji(self):
        source = Source("x ⬆️", syntax=emoji_syntax)
        increment_node = parse("@Increment", source, pc={})
        assert str(increment_node) == "x ⬆️"

        source = Source("y ⬆️", syntax=emoji_syntax)
        increment_node = parse("@Statement", source, pc={})
        assert str(increment_node) == "y ⬆️"

    def test_Decrement_emoji(self):
        source = Source("x ⬇️", syntax=emoji_syntax)
        decrement_node = parse("@Decrement", source, pc={})
        assert str(decrement_node) == "x ⬇️"

        source = Source("y ⬇️", syntax=emoji_syntax)
        decrement_node = parse("@Statement", source, pc={})
        assert str(decrement_node) == "y ⬇️"
    
    def test_Append_emoji(self):
        source = Source("A 📎 0", syntax=emoji_syntax)
        append_node = parse("@Append", source, pc={})
        assert str(append_node) == "A 📎 0"

        source = Source("y 📎 20 # コメント", syntax=emoji_syntax)
        append_node = parse("@Statement", source, pc={})
        assert str(append_node) == "y 📎 20"