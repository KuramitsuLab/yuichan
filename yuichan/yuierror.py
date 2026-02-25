from typing import Optional

from .yuiast import ASTNode


ERROR_MESSAGES = {
    # パーサーエラー
    "expected-token":           "トークンが不正です",
    "expected-number":          "数値が必要です",
    "expected-string":          "文字列が必要です",
    "expected-array":           "配列が必要です",
    "expected-object":          "オブジェクトが必要です",
    "expected-boolean":         "真偽値が必要です",
    "expected-closing":         "閉じ括弧が必要です",
    "expected-variable":        "変数が必要です",
    "frequent-mistake":         "よくある間違いです",
    "wrong-name":               "名前が不正です",
    "wrong-statement":          "不正な文です",
    "wrong-escape-sequence":    "不正なエスケープシーケンスです",
    "wrong-indent-level":       "インデントが不正です",
    # ランタイムエラー
    "undefined-variable":       "変数が未定義です",
    "undefined-function":       "関数が未定義です",
    "type-error":               "型エラーです",
    "division-by-zero":         "ゼロ除算です",
    "error-index":              "インデックスエラーです",
    "error-value":              "値エラーです",
    "too-many-recursions":      "再帰が深すぎます",
    "runtime-timeout":          "タイムアウトです",
    "unsupported-operator":     "サポートされていない演算子です",
    "unsupported-comparison":   "サポートされていない比較です",
    "mismatch-argument-number": "引数の数が合いません",
    "not-negative-number":      "負の数は使えません",
    "float-conversion":         "少数への変換エラーです",
    "internal-error":           "内部エラーです",
    "immutable":                "変更できません",
    "array-format":             "配列フォーマットエラーです",
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
        self.error_node = error_node if isinstance(error_node, ASTNode) else None
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
