"""Yui Programming Language"""

__version__ = "0.5.4"


try:
    get_ipython  # noqa: F821 — only defined in IPython/Jupyter
    from .notebook import auto_setup
    auto_setup()
except NameError:
    pass
