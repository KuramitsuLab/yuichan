"""Jupyter / Google Colab 向け Yui 言語サポート

このモジュールは IPython 環境でのみ使用される。
通常の Python スクリプトからはインポートしないこと。
"""

import html as _html
from IPython.display import HTML, display as _display
from IPython.core.magic import register_magic_function

from .yuiruntime import YuiRuntime
from .yuitypes import YuiError


def _show_error(label: str, message: str) -> None:
    safe = _html.escape(str(message))
    _display(HTML(
        f'<pre style="'
        f'color:#c00;background:#fff8f8;'
        f'border-left:3px solid #c00;'
        f'padding:6px 10px;margin:4px 0;'
        f'font-size:13px;white-space:pre-wrap;">'
        f'<b>{label}</b>: {safe}</pre>'
    ))


def _run_yui(source: str, syntax: str, eval_mode: bool) -> None:
    rt = YuiRuntime()
    try:
        result = rt.exec(source, syntax=syntax, eval_mode=eval_mode)
        if eval_mode and result is not None:
            print(result)
    except YuiError as e:
        _show_error('YuiError', e)
    except Exception as e:
        _show_error(type(e).__name__, e)


def _yui_cell(line, cell):
    """セル全体を Yui として実行する。構文指定: %%yui pylike"""
    syntax = line.strip() or 'yui'
    _run_yui(cell, syntax=syntax, eval_mode=False)


def _yui_line(line):
    """1行の Yui 式を評価して結果を表示する。"""
    _run_yui(line.strip(), syntax='yui', eval_mode=True)


def register_magics() -> None:
    """%%yui / %yui マジックを IPython に登録する。"""
    register_magic_function(_yui_cell, magic_kind='cell', magic_name='yui')
    register_magic_function(_yui_line, magic_kind='line', magic_name='yui')


def setup() -> None:
    """Google Colab でシンタックスハイライトを有効化する。"""
    from ._colab import setup as _colab_setup
    _colab_setup()


def auto_setup() -> None:
    """IPython 環境を検出してマジックを登録し、Colab なら highlighting も有効化する。"""
    register_magics()
    try:
        import google.colab  # noqa: F401
        setup()
    except ImportError:
        pass
