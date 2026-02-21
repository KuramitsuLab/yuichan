import pytest
from .yuiparser import Source, parse
from .yuitypes import YuiError
from .yuisyntax import load_syntax

emoji_syntax = load_syntax('emoji')


class TestParseStatementNode_Emoji:

    def test_Assignment(self):
        source = Source("x ⬅️ 1 # コメント", syntax=emoji_syntax)
        assignment_node = parse("@Assignment", source, pc={})
        assert str(assignment_node) == "x ⬅️ 1"

    def test_AssignmentAsStatement(self):
        source = Source("x ⬅️ 1", syntax=emoji_syntax)
        assignment_node = parse("@Statement", source, pc={})
        assert str(assignment_node) == "x ⬅️ 1"

    def test_Increment(self):
        source = Source("x ⬆️", syntax=emoji_syntax)
        increment_node = parse("@Increment", source, pc={})
        assert str(increment_node) == "x ⬆️"

        source = Source("y ⬆️", syntax=emoji_syntax)
        increment_node = parse("@Statement", source, pc={})
        assert str(increment_node) == "y ⬆️"

    def test_Decrement(self):
        source = Source("x ⬇️", syntax=emoji_syntax)
        decrement_node = parse("@Decrement", source, pc={})
        assert str(decrement_node) == "x ⬇️"

        source = Source("y ⬇️", syntax=emoji_syntax)
        decrement_node = parse("@Statement", source, pc={})
        assert str(decrement_node) == "y ⬇️"

    def test_Append(self):
        source = Source("A 🧲 0", syntax=emoji_syntax)
        append_node = parse("@Append", source, pc={})
        assert str(append_node) == "A 🧲 0"

        source = Source("y 🧲 20 # コメント", syntax=emoji_syntax)
        append_node = parse("@Statement", source, pc={})
        assert str(append_node) == "y 🧲 20"

    def test_Break(self):
        source = Source("🚀", syntax=emoji_syntax)
        break_node = parse("@Break", source, pc={})
        assert str(break_node) == "🚀"

    def test_Return(self):
        source = Source("✅ 1", syntax=emoji_syntax)
        return_node = parse("@Return", source, pc={})
        assert str(return_node) == "✅ 1"

        source = Source("💡 1", syntax=emoji_syntax)
        return_node = parse("@Return", source, pc={})
        assert str(return_node) == "💡 1"

    def test_FuncDef(self):
        source = Source("🧩 f(x) 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "🧩 f(x) 👉\n  x ⬅️ 1\n🔚"

    def test_FuncDef_no_args(self):
        source = Source("🧩 f() 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "🧩 f() 👉\n  x ⬅️ 1\n🔚"

    def test_FuncDef_multiple_args(self):
        source = Source("🧩 f(x,y) 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = parse("@FuncDef", source, pc={})
        assert str(funcdef_node) == "🧩 f(x,y) 👉\n  x ⬅️ 1\n🔚"


class TestParseBlockNode_Emoji:

    def test_TopLevel(self):
        source = Source("x ⬅️ 1\ny ⬅️ 2", syntax=emoji_syntax)
        top_level_node = parse("@TopLevel", source, pc={})
        assert str(top_level_node) == "x ⬅️ 1\ny ⬅️ 2"

    def test_Block(self):
        source = Source("👉\n  x ⬅️ 1\n  y ⬅️ 2\n🔚", syntax=emoji_syntax)
        block_node = parse("@Block", source, pc={})
        assert str(block_node) == "👉\n  x ⬅️ 1\n  y ⬅️ 2\n🔚"

    def test_If(self):
        source = Source("❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚", syntax=emoji_syntax)
        if_node = parse("@If", source, pc={})
        assert str(if_node) == "❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚"

    def test_IfAsStatement(self):
        source = Source("❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚", syntax=emoji_syntax)
        if_node = parse("@Statement", source, pc={})
        assert str(if_node) == "❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚"

    def test_Repeat(self):
        source = Source("🌀 3 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        repeat_node = parse("@Repeat", source, pc={})
        assert str(repeat_node) == "🌀 3 👉\n  x ⬅️ 1\n🔚"

    def test_Repeat_with_break(self):
        source = Source("🌀 10 👉\n  count ⬆️\n  ❓ count ⚖️ 5 👉\n    🚀\n  🔚\n🔚", syntax=emoji_syntax)
        repeat_node = parse("@Repeat", source, pc={})
        assert "🚀" in str(repeat_node)
