"""Google Colab 向け Yui 言語シンタックスハイライト

Usage:
    import yuichan._colab
    yuichan._colab.setup()   # セッション開始時に1回

以降、%%yui セルを追加するたびに highlight() を再呼び出しすると
新しいセルにもハイライトが適用される:
    yuichan._colab.highlight()

%%yui マジック自体は yuichan を import した時点で自動登録済み。
"""

import json
from IPython.display import Javascript, display as _display

# キーワード（長い語が先に来るよう並べる。JS 側でもソートするが Python 側でも整理する）
_KEYWORDS = [
    "標準ライブラリを使う", "四則演算子を使う",
    "くり返しを抜ける", "のいずれでもない", "そうでなければ",
    "関数から抜ける", "くりかえす", "繰り返す", "くり返す",
    "のいずれか", "入力なし", "何もしない",
    "値なし", "ならば", "もし", "入力", "真", "偽",
]

# 述語・演算語（keyword より優先度低め → builtin クラス）
_BUILTINS = [
    "より小さい", "より大きい", "に対して",
    "の大きさ", "を追加する", "に追加する",
    "を増やす", "を減らす", "が答え",
    "に対し", "以外", "以下", "以上",
]


def _build_define_mode_js() -> str:
    """CodeMirror 5 の defineMode 呼び出しを含む JS 文字列を返す。"""
    kw_json = json.dumps(_KEYWORDS, ensure_ascii=False)
    bi_json = json.dumps(_BUILTINS, ensure_ascii=False)

    return f"""
(function() {{
  if (typeof CodeMirror === 'undefined') {{
    console.warn('[yuichan] CodeMirror not found. Yui highlighting skipped.');
    return;
  }}

  var keywords = {kw_json};
  var builtins = {bi_json};

  // 長い語を優先してマッチさせる
  keywords.sort(function(a, b) {{ return b.length - a.length; }});
  builtins.sort(function(a, b) {{ return b.length - a.length; }});

  function defineYuiMode(name) {{
    if (CodeMirror.modes[name]) return;
    CodeMirror.defineMode(name, function() {{
      return {{
        token: function(stream, state) {{
          // 行コメント: # または ＃
          if (stream.match(/^[#＃]/)) {{
            stream.skipToEnd();
            return 'comment';
          }}

          // 文字列 "..." (バックスラッシュエスケープと補間 {{}} を考慮)
          if (stream.match('"')) {{
            var ch;
            while ((ch = stream.next()) != null) {{
              if (ch === '\\\\') {{ stream.next(); continue; }}
              if (ch === '"') break;
            }}
            return 'string';
          }}

          // 数値
          if (stream.match(/^[0-9]+(\.[0-9]+)?/)) return 'number';

          // キーワード
          for (var i = 0; i < keywords.length; i++) {{
            if (stream.match(keywords[i])) return 'keyword';
          }}

          // 述語・演算語
          for (var i = 0; i < builtins.length; i++) {{
            if (stream.match(builtins[i])) return 'builtin';
          }}

          // ASCII 識別子
          if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/)) return 'variable';

          stream.next();
          return null;
        }}
      }};
    }});
  }}

  // yui モードを登録（%%yui 引数なし用）
  defineYuiMode('yui');

  // %%yui [syntax] セルを探してハイライトを適用する
  function applyHighlight() {{
    if (typeof Jupyter === 'undefined') {{
      console.info('[yuichan] Jupyter object not found. Cell highlighting skipped.');
      return;
    }}
    var cells = Jupyter.notebook.get_cells();
    cells.forEach(function(cell) {{
      if (cell.cell_type !== 'code') return;
      var text = cell.get_text();
      var m = text.match(/^%%yui(\\s+(\\S+))?/);
      if (!m) return;
      var syntax = (m[2] || 'yui');
      defineYuiMode(syntax);
      cell.code_mirror.setOption('mode', syntax);
    }});
  }}

  applyHighlight();
  console.log('[yuichan] Yui syntax highlighting ready.');
}})();
"""


def _build_highlight_js() -> str:
    """既存の %%yui セルにモードを再適用する JS 文字列を返す（defineMode は呼ばない）。"""
    return """
(function() {
  if (typeof Jupyter === 'undefined' || typeof CodeMirror === 'undefined') return;
  var cells = Jupyter.notebook.get_cells();
  cells.forEach(function(cell) {
    if (cell.cell_type !== 'code') return;
    var text = cell.get_text();
    var m = text.match(/^%%yui(\\s+(\\S+))?/);
    if (!m) return;
    var syntax = m[2] || 'yui';
    if (CodeMirror.modes[syntax]) {
      cell.code_mirror.setOption('mode', syntax);
    }
  });
})();
"""


_SUPPRESS_DIAGNOSTICS_JS = """
(function() {
  // %%yui を含むセルのルート要素を探す
  function findCellRoot(el) {
    while (el) {
      if (el.classList && (
        el.classList.contains('cell') ||
        el.tagName === 'COLAB-NOTEBOOK-CELL' ||
        (el.getAttribute && el.getAttribute('data-cell-id'))
      )) return el;
      el = el.parentElement;
    }
    return null;
  }

  function isYuiCell(el) {
    var cell = findCellRoot(el);
    if (!cell) return false;
    var lines = cell.querySelectorAll('.cm-line, .view-line');
    if (!lines.length) return false;
    return /^%%yui/.test(lines[0].textContent.trimStart());
  }

  function removeDiagnosticsIn(root) {
    root.querySelectorAll(
      '.cm-lintRange-error, .cm-lintRange-warning, .cm-lintRange-info, .cm-diagnostic'
    ).forEach(function(marker) {
      if (isYuiCell(marker)) marker.remove();
    });
  }

  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(m) {
      m.addedNodes.forEach(function(node) {
        if (node.nodeType !== 1) return;
        if (node.className && /cm-lintRange|cm-diagnostic/.test(node.className)) {
          if (isYuiCell(node)) { node.remove(); return; }
        }
        if (node.querySelectorAll) removeDiagnosticsIn(node);
      });
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
  removeDiagnosticsIn(document.body);
  console.log('[yuichan] %%yui diagnostic suppression active (DOM observer).');
})();
"""


def setup() -> None:
    """CodeMirror に Yui モードを登録し、既存の %%yui セルにハイライトを適用する。
    また Monaco editor の %%yui セルへの診断エラー表示を抑制する。

    セッション開始時に1回呼び出す。
    """
    _display(Javascript(_build_define_mode_js()))
    # _display(Javascript(_SUPPRESS_DIAGNOSTICS_JS))  # TODO: Colab DOM 構造確認後に再有効化


def highlight() -> None:
    """全セルを再スキャンして %%yui セルにハイライトを適用する。

    setup() 後に新しい %%yui セルを追加したときに呼び出す。
    """
    _display(Javascript(_build_highlight_js()))
