import pytest
from .yuiparser import Source
from .yuiast import ConstNode
from .yuitypes import YuiError
from .yuisyntax import load_syntax

emoji_syntax = load_syntax('emoji')


class TestParseStatementNode_Emoji:

    def test_Assignment(self):
        source = Source("x ⬅️ 1 # コメント", syntax=emoji_syntax)
        assignment_node = source.parse("@Assignment")
        assert str(assignment_node) == "x ⬅️ 1"

    def test_AssignmentAsStatement(self):
        source = Source("x ⬅️ 1", syntax=emoji_syntax)
        assignment_node = source.parse("@Statement")
        assert str(assignment_node) == "x ⬅️ 1"

    def test_Increment(self):
        source = Source("x ⬆️", syntax=emoji_syntax)
        increment_node = source.parse("@Increment")
        assert str(increment_node) == "x ⬆️"

        source = Source("y ⬆️", syntax=emoji_syntax)
        increment_node = source.parse("@Statement")
        assert str(increment_node) == "y ⬆️"

    def test_Decrement(self):
        source = Source("x ⬇️", syntax=emoji_syntax)
        decrement_node = source.parse("@Decrement")
        assert str(decrement_node) == "x ⬇️"

        source = Source("y ⬇️", syntax=emoji_syntax)
        decrement_node = source.parse("@Statement")
        assert str(decrement_node) == "y ⬇️"

    def test_Append(self):
        source = Source("A 🧲 0", syntax=emoji_syntax)
        append_node = source.parse("@Append")
        assert str(append_node) == "A 🧲 0"

        source = Source("y 🧲 20 # コメント", syntax=emoji_syntax)
        append_node = source.parse("@Statement")
        assert str(append_node) == "y 🧲 20"

    def test_Break(self):
        source = Source("🚀", syntax=emoji_syntax)
        break_node = source.parse("@Break")
        assert str(break_node) == "🚀"

    def test_Return(self):
        source = Source("✅ 1", syntax=emoji_syntax)
        return_node = source.parse("@Return")
        assert str(return_node) == "✅ 1"

        source = Source("💡 1", syntax=emoji_syntax)
        return_node = source.parse("@Return")
        assert str(return_node) == "💡 1"

    def test_FuncDef(self):
        source = Source("🧩 f(x) 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "🧩 f(x) 👉\n  x ⬅️ 1\n🔚"

    def test_FuncDef_no_args(self):
        source = Source("🧩 f() 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "🧩 f() 👉\n  x ⬅️ 1\n🔚"

    def test_FuncDef_multiple_args(self):
        source = Source("🧩 f(x,y) 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        funcdef_node = source.parse("@FuncDef")
        assert str(funcdef_node) == "🧩 f(x,y) 👉\n  x ⬅️ 1\n🔚"


class TestParseBlockNode_Emoji:

    def test_TopLevel(self):
        source = Source("x ⬅️ 1\ny ⬅️ 2", syntax=emoji_syntax)
        top_level_node = source.parse("@TopLevel")
        assert str(top_level_node) == "x ⬅️ 1\ny ⬅️ 2"

    def test_Block(self):
        source = Source("👉\n  x ⬅️ 1\n  y ⬅️ 2\n🔚", syntax=emoji_syntax)
        block_node = source.parse("@Block")
        assert str(block_node) == "👉\n  x ⬅️ 1\n  y ⬅️ 2\n🔚"

    def test_If(self):
        source = Source("❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚", syntax=emoji_syntax)
        if_node = source.parse("@If")
        assert str(if_node) == "❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚"

    def test_IfAsStatement(self):
        source = Source("❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚", syntax=emoji_syntax)
        if_node = source.parse("@Statement")
        assert str(if_node) == "❓ x ⚖️ 1 👉\n  x ⬅️ 0\n🔚"

    def test_Repeat(self):
        source = Source("🌀 3 👉\n  x ⬅️ 1\n🔚", syntax=emoji_syntax)
        repeat_node = source.parse("@Repeat")
        assert str(repeat_node) == "🌀 3 👉\n  x ⬅️ 1\n🔚"

    def test_Repeat_with_break(self):
        source = Source("🌀 10 👉\n  count ⬆️\n  ❓ count ⚖️ 5 👉\n    🚀\n  🔚\n🔚", syntax=emoji_syntax)
        repeat_node = source.parse("@Repeat")
        assert "🚀" in str(repeat_node)


class TestParseConstNode_Emoji:

    def test_null(self):
        source = Source("🫥", syntax=emoji_syntax)
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is None
        assert str(node) == "🫥"

    def test_true(self):
        source = Source("👍", syntax=emoji_syntax)
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is True
        assert str(node) == "👍"

    def test_false(self):
        source = Source("👎", syntax=emoji_syntax)
        node = source.parse("@Boolean")
        assert isinstance(node, ConstNode)
        assert node.native_value is False
        assert str(node) == "👎"

    def test_null_as_term(self):
        source = Source("🫥", syntax=emoji_syntax)
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is None

    def test_true_as_term(self):
        source = Source("👍", syntax=emoji_syntax)
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is True

    def test_false_as_term(self):
        source = Source("👎", syntax=emoji_syntax)
        node = source.parse("@Term")
        assert isinstance(node, ConstNode)
        assert node.native_value is False

    def test_null_in_assignment(self):
        source = Source("x ⬅️ 🫥", syntax=emoji_syntax)
        node = source.parse("@Assignment")
        assert str(node) == "x ⬅️ 🫥"

    def test_true_in_assignment(self):
        source = Source("x ⬅️ 👍", syntax=emoji_syntax)
        node = source.parse("@Assignment")
        assert str(node) == "x ⬅️ 👍"
