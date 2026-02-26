from __future__ import annotations
from typing import Optional, TYPE_CHECKING

ERROR_MESSAGES = {
    # パーサーエラー
    "expected-token":           "書き方が間違っています",
    "expected-number":          "数値が必要です",
    "expected-string":          "文字列が必要です",
    "expected-array":           "配列が必要です",
    "expected-object":          "オブジェクトが必要です",
    "expected-boolean":         "真偽値が必要です",
    "expected-closing":         "閉じ括弧が必要です",
    "expected-variable":        "変数が必要です",
    "expected-expression":      "変数や値が必要です",
    "expected-variable":        "ここは変数が必要です",

    "typo":                     "うっかり間違えてませんか？",
    "wrong-name":               "名前が不正です",
    "wrong-statement":          "何とも解釈できない書き方です",
    "wrong-escape-sequence":    "不正なエスケープシーケンスです",
    "wrong-indent-level":       "インデントが不正です",
    "unexpected-return":        "関数内でのみ使えます",
    "unexpected-break":         "くり返しの中でのみ使えます",

    # ランタイムエラー
    "undefined-variable":       "変数が定義されていません",
    "undefined-function":       "関数が定義されていません",
    "type-error":               "データの種類（型）が違っています",
    "division-by-zero":         "ゼロで割ってしまいました",
    "error-index":              "配列のインデックスが範囲外です",
    "error-value":              "値エラーです",
    "too-many-recursion":       "再帰が深すぎます",
    "runtime-timeout":          "タイムアウトしました",
    "unsupported-operator":     "サポートされていない演算子です",
    "imcomparable":             "両者は直接比較できません",
    "mismatch-argument":        "引数の数が合いません",
    "not-negative-number":      "負の数は使えません",
    "float-conversion":         "少数への変換エラーです",
    "internal-error":           "内部エラーです",
    "immutable":                "変更できません",
    "array-format":             "配列フォーマットエラーです",
    "assertion-failed":         "テストを失敗",
}


def _format_messages(messages: tuple) -> str:
    """先頭キーを ERROR_MESSAGES で置き換えて表示用文字列を返す"""
    if not messages:
        return ""
    key = messages[0]
    display = ERROR_MESSAGES.get(key, key)
    rest = ' '.join(messages[1:])
    return f"{display} {rest}".strip() if rest else display


def _normalize_messages(messages) -> tuple:
    """非絵文字の連続する文字列を '-' で結合する。絵文字（ord > 127）で始まる文字列は独立要素として残す。"""
    if isinstance(messages, str):
        messages = (messages,)
    result = []
    parts: list = []
    for msg in messages:
        if msg and ord(msg[0]) > 127:
            if parts:
                result.append('-'.join(parts))
                parts = []
            result.append(msg)
        else:
            parts.append(msg)
    if parts:
        result.append('-'.join(parts))
    return tuple(result)


class YuiError(RuntimeError):
    """Yui言語のエラーを表現するクラス"""
    messages: tuple
    error_node: Optional[ASTNode]
    BK: bool

    def __init__(self, messages: tuple, error_node: Optional[ASTNode] = None,
                 BK: bool = False):
        """YuiErrorを初期化する"""
        self.messages = _normalize_messages(messages)
        super().__init__(' '.join(self.messages))
        from .yuiast import ASTNode as _ASTNode
        self.error_node = error_node if isinstance(error_node, _ASTNode) else None
        self.BK = BK

    @property
    def lineno(self) -> int:
        """エラー箇所の行番号を返す（1始まり）"""
        if self.error_node:
            line, _, _ = self.error_node.extract()
            return line
        return 0

    @property
    def offset(self) -> int:
        """エラー箇所の列番号を返す（1始まり）"""
        if self.error_node:
            _, offset, _ = self.error_node.extract()
            return offset
        return 0

    @property
    def text(self) -> str:
        """エラー箇所のコードスニペットを返す"""
        if self.error_node:
            _, _, snippet = self.error_node.extract()
            return snippet
        return ""

    def formatted_message(self, prefix: str = " ", marker: str = '^', lineoffset: int = 0) -> str:
        """構文エラーとして整形したメッセージを返す。ランタイムエラーは YuiRuntime.format_error() を使うこと。"""
        message = _format_messages(self.messages)
        if self.error_node:
            line, col, snippet = self.error_node.extract()
            length = max(self.error_node.end_pos - self.error_node.pos, 3) if self.error_node.end_pos is not None else 3
            make_pointer = marker * min(length, 16)
            snippet = snippet.split('\n')[0]
            indent = " " * (col - 1)
            message = f"{message} line {line + lineoffset}, column {col}:\n{prefix}{snippet}\n{prefix}{indent}{make_pointer}"
        return f"[構文エラー/SyntaxError] {message}"
