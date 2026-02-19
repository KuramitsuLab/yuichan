"""
message.py  ─  言語別メッセージモジュールへのディスパッチャー

優先順位:
  1. set_language() で明示的に指定された言語
  2. システムの LOCALE（LC_ALL / LANG など）
  3. フォールバック: ' '.join(messages)
"""

import locale
import importlib
from typing import Union, Callable


def _fallback(messages: Union[tuple, str]) -> str:
    """言語モジュールが見つからない場合のデフォルト処理"""
    if isinstance(messages, tuple):
        return ' '.join(str(m) for m in messages)
    return str(messages)


_current_lang: str = ""
_to_message_func: Callable = _fallback


def _load_lang(lang: str) -> bool:
    """message_{lang}.py を動的にロードする。成功すれば True を返す"""
    global _to_message_func, _current_lang
    try:
        mod = importlib.import_module(f'.message_{lang}', package='yuichan')
        _to_message_func = mod.to_message
        _current_lang = lang
        return True
    except (ImportError, AttributeError):
        return False


def set_language(lang: str) -> bool:
    """
    メッセージ言語を切り替える。

    Parameters
    ----------
    lang : str
        言語コード（例: "ja", "en"）。
        対応するモジュール message_{lang}.py が存在しない場合は
        フォールバック（' '.join）のままになる。

    Returns
    -------
    bool
        モジュールのロードに成功すれば True
    """
    global _to_message_func, _current_lang
    ok = _load_lang(lang)
    if not ok:
        _to_message_func = _fallback
        _current_lang = ""
    return ok


def _detect_locale_lang() -> str:
    """システムの LOCALE から2文字の言語コードを返す。取得できなければ空文字"""
    try:
        # LC_ALL / LANG / LC_MESSAGES などを参照
        lang, _ = locale.getlocale()
        if lang:
            return lang[:2].lower()  # "ja_JP.UTF-8" → "ja"
    except Exception:
        pass
    return ""


def _init():
    """モジュールロード時に LOCALE から言語を自動検出して設定する"""
    lang = _detect_locale_lang()
    if lang:
        _load_lang(lang)   # 失敗してもフォールバックのまま続行


_init()


def to_message(messages: Union[tuple, str]) -> str:
    """
    YuiError の messages を現在の言語設定でメッセージ文字列に変換する。

    Parameters
    ----------
    messages : tuple | str
        YuiError.messages の値

    Returns
    -------
    str
        ユーザー向けのエラーメッセージ
    """
    return _to_message_func(messages)


def current_language() -> str:
    """現在ロードされている言語コードを返す。フォールバック中は空文字"""
    return _current_lang
