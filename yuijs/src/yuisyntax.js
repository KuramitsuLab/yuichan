// yuisyntax.js — syntax loading and YuiSyntax class (port of yuichan/yuisyntax.py)
// Browser-compatible: all built-in syntaxes are inlined as JS objects.
// No fs/path/url imports — works in both Node.js and browsers (including file://).

// ─────────────────────────────────────────────
// Built-in syntax definitions (inlined from syntax/*.json)
// ─────────────────────────────────────────────

const BUILTIN_SYNTAXES = {
    yui: {
            "syntax": "Yui-Classic",
            "function-language": "ja",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "line-comment-begin": "[#＃]",
            "comment-begin": "",
            "comment-end": "",
            "indent": "  ",
            "null": "値なし|null",
            "boolean-true": "真|true",
            "boolean-false": "偽|false",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_]*",
            "extra-name-begin": "「",
            "extra-name-end": "」",
            "string-begin": "\"",
            "string-end": "\"",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "string-content-end": "\\\\|\\{|\\\"",
            "!string-begin": "'|f\"",
            "array-begin": "\\[",
            "array-end": "\\]",
            "array-separator": "[,、，]",
            "object-begin": "\\{",
            "object-end": "\\}",
            "object-separator": "[,、，]",
            "key-value-separator": ":",
            "grouping-begin!": "\\(",
            "grouping-end!": "\\)",
            "length-begin": "\\|",
            "length-end": "\\|",
            "binary-infix+": "\\+",
            "binary-infix-": "-",
            "binary-infix*": "\\*",
            "binary-infix/": "/",
            "binary-infix%": "%",
            "binary-infix==": "==",
            "binary-infix!=": "!=",
            "binary-infix<=": "<=",
            "binary-infix>=": ">=",
            "binary-infix<": "<",
            "binary-infix>": ">",
            "unary-minus": "-",
            "array-indexer-suffix": "\\[",
            "array-indexer-end": "\\]",
            "property-length": "の大きさ",
            "funcapp-args-begin": "\\(",
            "funcapp-args-end": "\\)",
            "funcapp-separator": "[,、，]",
            "import-standard": "標準ライブラリを使う",
            "import-operator": "四則演算子を使う",
            "import-begin": "",
            "import-end": "を使う",
            "!block-begin": ":|：",
            "block-begin": "[\\{｛]",
            "block-end": "[\\}｝]",
            "block-line": "",
            "assignment-begin": "",
            "assignment-infix": "[=＝]",
            "assignment-end": "",
            "increment-begin": "",
            "increment-infix": "",
            "increment-end": "を増やす",
            "!increment-end": "\\+\\=|\\+\\+",
            "increment-lookahead": "増やす",
            "decrement-begin": "",
            "decrement-infix": "",
            "!decrement-end": "\\-\\=|\\-\\-",
            "decrement-end": "を減らす",
            "append-lookahead": "を追加する",
            "append-begin": "",
            "append-infix": "(の末尾)?に",
            "append-end": "を追加する",
            "append2-lookahead": "に追加する",
            "append2-begin": "",
            "append2-infix": "を",
            "append2-end": "に追加する",
            "print-begin": "",
            "print-end": "",
            "!break": "break",
            "break": "くり返しを抜ける",
            "pass": "何もしない",
            "!return-begin": "return",
            "return-begin": "",
            "return-end": "が[、]?答え",
            "return-none": "関数から抜ける",
            "repeat-begin": "",
            "repeat-times": "回[、]?",
            "!repeat-block": "繰り返す|くりかえす",
            "repeat-block": "くり返す",
            "repeat-end": "",
            "!if-begin": "if",
            "if-begin": "もし",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix": "が",
            "!if-infix": "は|==|!=|<|<=|>|>=|＝|≦|≧|≠",
            "if-suffix!=": "以外",
            "!if-suffix!=": "でない",
            "if-suffix<": "より小さい",
            "if-suffix<=": "以下",
            "if-suffix>": "より大きい",
            "if-suffix>=": "以上",
            "if-suffixin": "のいずれか",
            "if-suffixnotin": "のいずれでもない",
            "if-then": "ならば[、]?",
            "if-else": "そうでなければ[、]?",
            "if-end": "",
            "funcdef-begin": "",
            "funcdef-name-begin": "",
            "funcdef-name-end": "[=＝]",
            "funcdef-args-begin": "入力",
            "funcdef-arg-separator": "[,、]",
            "funcdef-args-end": "",
            "funcdef-noarg": "入力なし",
            "funcdef-block": "に対し[て]?[、]?",
            "funcdef-end": ""
    },
    pylike: {
            "syntax": "python-like",
            "function-language": "en",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "word-segmenter": " ",
            "line-comment-begin": "[#＃]",
            "comment-begin": "",
            "comment-end": "",
            "indent": "  ",
            "keywords": "def|return|if|else|elif|for|in|not|and|or|break|pass|assert|import|True|False|None",
            "null": "None",
            "boolean-true": "True",
            "boolean-false": "False",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_]*",
            "extra-name-begin": "",
            "extra-name-end": "",
            "string-begin": "\"",
            "string-end": "\"",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "string-content-end": "\\\\|\\{|\\\"",
            "array-begin": "\\[",
            "array-end": "\\]",
            "array-separator": ",",
            "object-begin": "\\{",
            "object-end": "\\}",
            "object-separator": ",",
            "key-value-separator": ":",
            "grouping-begin": "\\(",
            "grouping-end": "\\)",
            "length-begin": "len\\s*\\(",
            "length-end": "\\)",
            "binary-infix+": "\\+",
            "binary-infix-": "\\-",
            "binary-infix*": "\\*",
            "binary-infix/": "\\/",
            "binary-infix%": "\\%",
            "binary-infix==": "==",
            "binary-infix!=": "!=",
            "binary-infix<=": "<=",
            "binary-infix>=": ">=",
            "binary-infix<": "<",
            "binary-infix>": ">",
            "unary-minus": "\\-",
            "array-indexer-suffix": "\\[",
            "array-indexer-end": "\\]",
            "property-accessor": "\\.",
            "not-property-name": "append",
            "funcapp-args-begin": "\\(",
            "funcapp-args-end": "\\)",
            "funcapp-separator": ",",
            "block-begin": "\\:",
            "block-end": "",
            "block-else": "else|elif|except|finally",
            "block-line": "",
            "assignment-begin": "",
            "assignment-infix": "\\=",
            "assignment-end": "",
            "increment-begin": "",
            "increment-end": "\\+\\=\\s*1",
            "decrement-begin": "",
            "decrement-end": "\\-\\=\\s*1",
            "append-begin": "",
            "append-infix": ".append\\s*\\(",
            "append-end": "\\)",
            "print-begin": "",
            "print-end": "",
            "break": "break",
            "pass": "pass",
            "return-begin": "return\\s",
            "return-end": "",
            "repeat-begin": "while\\s+times\\s*\\(",
            "repeat-times": "\\)",
            "repeat-block": "",
            "repeat-end": "",
            "if-begin": "if\\s",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix==": "==",
            "if-infix!=": "!=",
            "if-infix<": "<",
            "if-infix<=": "<=",
            "if-infix>": ">",
            "if-infix>=": ">=",
            "if-infixin": "in\\s",
            "if-infixnotin": "not\\s+in\\s",
            "if-then": "",
            "if-else": "else\\s*",
            "if-end": "",
            "funcdef-begin": "def\\s",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "\\(",
            "funcdef-noarg": "",
            "funcdef-arg-separator": ",",
            "funcdef-args-end": "\\)",
            "funcdef-block": "",
            "funcdef-end": "",
            "import-standard": "import\\s+stdlib",
            "import-begin": "import\\s",
            "import-end": ""
    },
    jslike: {
            "syntax": "javascript-like",
            "function-language": "en",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "word-segmenter": " ",
            "line-comment-begin": "//",
            "comment-begin": "/\\*",
            "comment-end": "\\*/",
            "keywords": "function|return|if|else|for|in|not|and|or|break|assert",
            "statement-separator": ";",
            "null": "null",
            "boolean-true": "true",
            "boolean-false": "false",
            "!string-begin": "'|`",
            "grouping-begin": "\\(",
            "grouping-end": "\\)",
            "binary-infix+": "\\+",
            "binary-infix-": "\\-",
            "binary-infix*": "\\*",
            "binary-infix/": "\\/",
            "binary-infix%": "\\%",
            "binary-infix==": "==",
            "binary-infix!=": "!=",
            "binary-infix<=": "<=",
            "binary-infix>=": ">=",
            "binary-infix<": "<",
            "binary-infix>": ">",
            "unary-minus": "\\-",
            "array-indexer-suffix": "\\[",
            "array-indexer-end": "\\]",
            "property-length": "\\.length",
            "not-property-name": "push",
            "funcapp-args-begin": "\\(",
            "funcapp-args-end": "\\)",
            "funcapp-separator": ",",
            "block-begin-prefix": " ",
            "block-begin": "\\{",
            "block-end": "\\}",
            "assignment-begin": "",
            "assignment-infix": "\\=",
            "assignment-end": "",
            "increment-begin": "",
            "increment-end": "\\+\\+|\\+\\=\\s*1",
            "decrement-begin": "",
            "decrement-end": "\\-\\-|\\-\\=\\s*1",
            "append-begin": "",
            "append-infix": ".push\\s*\\(",
            "append-end": "\\)",
            "import-begin": "require\\s*\\(",
            "import-end": "\\)",
            "import-standard": "require\\s*\\(\"stdlib\"\\)",
            "print-begin": "",
            "print-end": "",
            "break": "break",
            "pass": "",
            "return-begin": "return\\s",
            "return-end": "",
            "return-noarg": "return",
            "repeat-begin": "while\\s*\\(\\s+times\\s*\\(",
            "repeat-times": "\\)\\s*\\)",
            "repeat-block": "",
            "repeat-end": "",
            "if-begin": "if\\s",
            "if-condition-begin": "\\(",
            "if-condition-end": "\\)",
            "if-prefix": "",
            "if-infix==": "==",
            "if-infix!=": "!=",
            "if-infix<": "<",
            "if-infix<=": "<=",
            "if-infix>": ">",
            "if-infix>=": ">=",
            "if-infixin": "in",
            "if-then": "",
            "if-else": "else\\s*",
            "if-end": "",
            "funcdef-begin": "function\\s",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "\\(",
            "funcdef-noarg": "",
            "funcdef-arg-separator": ",",
            "funcdef-args-end": "\\)",
            "funcdef-block": "",
            "funcdef-end": ""
    },
    emoji: {
            "syntax": "🪢",
            "function-language": "emoji",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "word-segmenter": " ",
            "linefeed": "[\\n]",
            "line-comment-begin": "💭|🗨️|📌|⚠️",
            "indent": "  ",
            "comment-begin": "",
            "comment-end": "",
            "special-name-pattern": "[^\\s\\[\\]\\(\\)\",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+",
            "special-name-variable": "({name_pattern})\\s+⬅️",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "null": "🫥|null",
            "boolean-true": "👍|true",
            "boolean-false": "👎|false",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_]*",
            "extra-name-begin": "",
            "extra-name-end": "",
            "string-begin": "\"",
            "string-end": "\"",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "string-content-end": "\\\\|\\{|\\\"",
            "array-begin": "\\[",
            "array-end": "\\]",
            "array-separator": ",",
            "object-begin": "\\{",
            "object-end": "\\}",
            "object-separator": ",",
            "key-value-separator": ":",
            "grouping-begin": "\\(",
            "grouping-end": "\\)",
            "unary-minus": "-",
            "unary-length": "📐",
            "binary-infix+": "➕|\\+|＋",
            "binary-infix-": "➖|\\-|－",
            "binary-infix*": "✖️|\\*|×",
            "binary-infix/": "➗|/|÷",
            "binary-infix%": "💔|%|％",
            "binary-infix==": "⚖️|==",
            "binary-infix!=": "🚫⚖️|!=",
            "binary-infix<=": "📈⚖️|<=",
            "binary-infix>=": "📉⚖️|>=",
            "binary-infix<": "📈|<",
            "binary-infix>": "📉|>",
            "binary-infixin": "📥|∈",
            "binary-infixnotin": "🚫📥|∉",
            "array-indexer-suffix": "\\[",
            "array-indexer-end": "\\]",
            "property-accessor": "",
            "property-type": "",
            "not-property-name": "",
            "funcapp-args-begin": "\\(",
            "funcapp-args-end": "\\)",
            "funcapp-separator": ",",
            "block-begin": "👉",
            "block-end": "🔚",
            "assignment-begin": "",
            "assignment-infix": "⬅️",
            "assignment-end": "",
            "increment-begin": "",
            "increment-end": "⬆️",
            "decrement-begin": "",
            "decrement-end": "⬇️",
            "append-begin": "",
            "append-infix": "🧲",
            "append-end": "",
            "print-begin": "",
            "print-end": "",
            "break": "🚀",
            "pass": "💤",
            "return-begin": "✅|💡",
            "return-end": "",
            "repeat-begin": "🌀",
            "repeat-times": "",
            "repeat-block": "",
            "repeat-end": "",
            "if-begin": "❓|🤔",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix==": "⚖️|==|＝",
            "if-infix!=": "🚫⚖️|!=|≠",
            "if-infix<": "📈|<",
            "if-infix<=": "📈⚖️|<=|≦",
            "if-infix>": "📉|>",
            "if-infix>=": "📉⚖️|>=|≧",
            "if-infixin": "📥|∈",
            "if-infixnotin": "🚫📥|∉",
            "if-then": "",
            "else-if": "❗❓",
            "if-else": "❗|🙅",
            "if-end": "",
            "funcdef-begin": "🧩",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "\\(",
            "funcdef-arg-separator": "\\,",
            "funcdef-args-end": "\\)",
            "funcdef-noarg": "",
            "funcdef-block": "",
            "funcdef-end": "",
            "import-standard": "🗝️\\s+📚",
            "import-begin": "🗝️",
            "import-end": ""
    },
    nannan: {
            "syntax": "なんなん？",
            "function-language": "ja",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "line-comment-begin": "⚠️",
            "comment-begin": "",
            "comment-end": "",
            "indent": "  ",
            "keywords": "def|return|if|else|elif|for|in|not|and|or|break|pass|assert|import|True|False|None",
            "null": "「しらんがな」|null",
            "boolean-true": "「そやな」|true",
            "boolean-false": "「ちゃうな」|false",
            "grouping-begin!": "\\(",
            "grouping-end!": "\\)",
            "length-begin": "\\|",
            "length-end": "\\|",
            "binary-infix+": "\\+|＋",
            "binary-infix-": "-|ー",
            "binary-infix*": "\\*|×",
            "binary-infix/": "/|÷",
            "binary-infix%": "%|％",
            "binary-infix==": "==|＝＝",
            "binary-infix!=": "!=|≠",
            "binary-infix<=": "<=|≦",
            "binary-infix>=": ">=|≧",
            "binary-infix<": "<|＜",
            "binary-infix>": ">|＞",
            "binary-infixin": "∈",
            "binary-infixnotin": "∉",
            "unary-minus": "-",
            "array-indexer-suffix": "\\[",
            "array-indexer-end": "\\]",
            "property-length": "の大きさ",
            "funcapp-args-begin": "\\(",
            "funcapp-args-end": "\\)",
            "funcapp-separator": ",",
            "import-standard": "標準のやつ使う",
            "import-begin": "",
            "import-end": "を使う",
            "block-begin": "？|❓",
            "block-end": "",
            "block-line": "",
            "assignment-begin": "",
            "assignment-infix": "=",
            "assignment-end": "",
            "increment-begin": "",
            "increment-infix": "",
            "increment-end": "上げとく",
            "increment-lookahead": "上げとく",
            "decrement-begin": "",
            "decrement-infix": "",
            "decrement-end": "下げとく",
            "decrement-lookahead": "下げとく",
            "append-begin": "",
            "append-infix": "に",
            "append-end": "を?入れとく",
            "print-begin": "",
            "print-end": "",
            "break": "もうええって",
            "pass": "ほっとく",
            "return-begin": "この",
            "return-end": "だよ",
            "return-none": "わからん",
            "repeat-begin": "",
            "repeat-times": "回[、]?",
            "repeat-block": "まわそうか",
            "repeat-end": "",
            "if-lookahead": "ほんま",
            "if-begin": "",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix": "が",
            "if-suffix==": "と同じ",
            "if-suffix!=": "やない",
            "if-suffix<": "より小さい",
            "if-suffix<=": "以下",
            "if-suffix>": "より大きい",
            "if-suffix>=": "以上",
            "if-suffixin": "のいずれか",
            "if-suffixnotin": "のいずれでもない",
            "if-then": "ってほんま",
            "if-else": "違うん",
            "if-end": "",
            "funcdef-lookahead": "なんなん",
            "funcdef-begin": "",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "\\(",
            "funcdef-arg-separator": "[,、]",
            "funcdef-args-end": "\\)",
            "funcdef-block": "ってなんなん",
            "funcdef-end": "",
            "assert-begin": ">>>\\s+",
            "assert-infix": "[\\n]",
            "assert-end": ""
    },
    sexpr: {
            "syntax": "s-expression",
            "function-language": "en",
            "whitespace": "[ \\t\\r\\n　]",
            "whitespaces": "[ \\t\\r\\n　]+",
            "linefeed": "[\\n]",
            "line-comment-begin": ";",
            "comment-begin": "",
            "comment-end": "",
            "word-segmenter": " ",
            "indent": "",
            "keywords": "begin\\b|require\\b|inc\\b|dec\\b|append\\b|set\\b|aref\\b|if\\b|repeat\\b|break\\b|print\\b|assert\\b|define\\b|return\\b",
            "special-name-pattern": "[^\\s\\[\\]\\(\\)\",]+",
            "special-name-funcname": "\\(({name_pattern})\\s",
            "special-name-variable": "\\(set\\!\\s+({name_pattern})\\s",
            "null": "nil|null",
            "boolean-true": "true",
            "boolean-false": "false",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_\\!\\?]*",
            "string-begin": "\"",
            "string-end": "\"",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "string-content-end": "\\\\|\\{|\\\"",
            "!string-begin": "'|f\"",
            "array-begin": "\\[",
            "array-end": "\\]",
            "array-separator": ",",
            "object-begin": "\\{",
            "object-end": "\\}",
            "object-separator": ",",
            "key-value-separator": ":",
            "grouping-begin": "",
            "grouping-end": "",
            "unary-minus": "",
            "minus-begin": "\\(-\\s+",
            "minus-end": "\\)",
            "length-begin": "\\(len\\s+",
            "length-end": "\\)",
            "binary-infix-prefix-begin": "\\(",
            "binary-infix-prefix+": "\\+",
            "binary-infix-prefix-": "-",
            "binary-infix-prefix*": "\\*",
            "binary-infix-prefix/": "/",
            "binary-infix-prefix%": "%",
            "binary-infix-prefix==": "==",
            "binary-infix-prefix!=": "!=",
            "binary-infix-prefix<=": "<=",
            "binary-infix-prefix>=": ">=",
            "binary-infix-prefix<": "<",
            "binary-infix-prefix>": ">",
            "binary-infix-prefix-end": "\\)",
            "array-indexer-begin": "\\(aref\\s+",
            "array-indexer-suffix": "",
            "array-indexer-end": "\\)",
            "funcapp-begin": "\\(",
            "funcapp-args-begin": "",
            "funcapp-args-end": "",
            "funcapp-separator": "",
            "funcapp-end": "\\)",
            "import-standard": "\\(require-standard\\)",
            "import-begin": "\\(require\\s+",
            "import-end": "\\)",
            "block-begin-prefix": " ",
            "block-begin": "\\(begin\\s+",
            "block-end": "\\)",
            "assignment-begin": "\\(set\\!\\s+",
            "assignment-infix": "",
            "assignment-end": "\\)",
            "increment-begin": "\\(inc\\!\\s+",
            "increment-end": "\\)",
            "decrement-begin": "\\(dec\\!\\s+",
            "decrement-end": "\\)",
            "append-begin": "\\(append\\s+",
            "append-infix": "",
            "append-end": "\\)",
            "#print-begin": "\\(print\\s+",
            "#print-end": "\\)",
            "break": "\\(break\\)",
            "pass": "",
            "return-begin": "\\(return\\s+",
            "return-end": "\\)",
            "return-none": "\\(return\\)",
            "repeat-begin": "\\(repeat\\s+",
            "repeat-times": "",
            "repeat-end": "\\)",
            "if-begin": "\\(if\\s+",
            "if-condition-begin": "\\(",
            "if-condition-end": "\\)",
            "if-prefix==": "==",
            "if-prefix!=": "!=",
            "if-prefix<": "<",
            "if-prefix<=": "<=",
            "if-prefix>": ">",
            "if-prefix>=": ">=",
            "if-prefixin": "in",
            "if-prefixnotin": "not-in",
            "if-then": "",
            "if-else": "",
            "if-end": "\\)",
            "funcdef-begin": "\\(define\\s+",
            "funcdef-name-begin": "\\(",
            "funcdef-name-end": "",
            "funcdef-args-begin": "",
            "funcdef-arg-separator": "",
            "funcdef-args-end": "\\)",
            "funcdef-noarg": "",
            "funcdef-block": "",
            "funcdef-end": "\\)",
            "assert-begin": "\\(assert\\s+",
            "assert-infix": "",
            "assert-end": "\\)"
    },
    bridget: {
            "syntax": "Plain English",
            "function-language": "en",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "line-comment-begin": "#",
            "word-segmenter": " ",
            "comment-begin": "",
            "comment-end": "",
            "indent": "  ",
            "special-name-pattern": "[^\\s\\[\\]\\(\\)\",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+",
            "special-name-funcname": "\\s(?:is|to)\\s+({name_pattern})\\s+of",
            "special-name-variable": "Remember\\s+that\\s+({name_pattern})\\s+is",
            "null": "[nN]othing|null",
            "boolean-true": "[yY]es|true",
            "boolean-false": "[nN]o|false",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_]*",
            "extra-name-begin": "`",
            "extra-name-end": "`",
            "string-begin": "\"",
            "string-end": "\"",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "string-content-end": "\\\\|\\{|\\\"",
            "binary-infix+": "\\+",
            "binary-infix-": "-",
            "binary-infix*": "\\*",
            "binary-infix/": "/",
            "binary-infix%": "%",
            "binary-infix==": "==",
            "binary-infix!=": "!=",
            "binary-infix<=": "<=",
            "binary-infix>=": ">=",
            "binary-infix<": "<",
            "binary-infix>": ">",
            "unary-minus": "-",
            "array-indexer-begin": "item",
            "array-indexer-infix": "in",
            "array-indexer-suffix": "",
            "array-indexer-end": "",
            "array-indexer-order": "reversed",
            "property-length": "'s\\s+length",
            "funcapp-args-begin": "of",
            "funcapp-args-end": "",
            "funcapp-separator": "and",
            "funcapp-noarg": ", do it",
            "import-standard": "Use the standard library",
            "import-begin": "Use",
            "import-end": "",
            "block-begin": ":",
            "block-end": "",
            "assignment-begin": "Remember\\s+that",
            "assignment-infix": "is",
            "assignment-end": "",
            "increment-begin": "Increase",
            "increment-end": "(by\\s+1)?",
            "decrement-begin": "Decrease",
            "decrement-end": "(by\\s+1)?",
            "append-begin": "Add",
            "append-infix": "to",
            "append-end": "",
            "append-order": "reverse",
            "!break": "break",
            "break": "Leave the loop",
            "pass": "Do nothing",
            "print-begin": "Now,",
            "print-end": "",
            "!return-begin": "return",
            "return-begin": "The answer is",
            "return-end": "",
            "return-none": "Stop here",
            "repeat-begin": "Do this",
            "repeat-times": "times",
            "repeat-block": "",
            "repeat-end": "End do",
            "!if-begin": "if",
            "if-begin": "When",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix==": "is\\s",
            "if-infix!=": "is not\\s",
            "if-infix<": "is less than",
            "if-infix<=": "is at least",
            "if-infix>": "is more than",
            "if-infix>=": "is at most",
            "if-infixin": "is in\\s",
            "if-infixnotin": "is not in",
            "if-then": ",\\s+then",
            "if-else": "But,\\s+if not",
            "if-end": "End when",
            "funcdef-begin": "This is how to",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "of",
            "funcdef-arg-separator": "and",
            "funcdef-args-end": "",
            "funcdef-noarg": "[^o][^f]",
            "funcdef-block": "",
            "funcdef-end": "Now you know"
    },
    wenyan: {
            "syntax": "Wenyan Like",
            "whitespace": "[ \\t\\r　]",
            "whitespaces": "[ \\t\\r　]+",
            "linefeed": "[\\n]",
            "line-comment-begin": "注(、|。)?",
            "word-segmenter": "",
            "comment-begin": "注始(。|)",
            "comment-end": "注終(。|)",
            "indent": "  ",
            "special-name-pattern": "[^\\s\\[\\]\\(\\)\",\\+\\-\\*\\/\\%\\=\\!\\<\\>]+",
            "special-name-funcname": "施\\s*({name_pattern})\\s*於",
            "special-name-variable": "名之曰\\s*({name_pattern})\\s*[。]",
            "null": "無|null",
            "boolean-true": "然|true",
            "boolean-false": "否|false",
            "number-first-char": "[0-9]",
            "number-chars": "[0-9]*",
            "number-dot-char": "[\\.]",
            "name-first-char": "[A-Za-z_]",
            "name-chars": "[A-Za-z0-9_]*",
            "extra-name-begin": "`",
            "extra-name-end": "`",
            "string-begin": "「",
            "string-end": "」",
            "string-escape": "\\\\",
            "string-interpolation-begin": "\\{",
            "string-interpolation-end": "\\}",
            "binary-infix+": "\\+",
            "binary-infix-": "-",
            "binary-infix*": "\\*",
            "binary-infix/": "/",
            "binary-infix%": "%",
            "binary-infix==": "==",
            "binary-infix!=": "!=",
            "binary-infix<=": "<=",
            "binary-infix>=": ">=",
            "binary-infix<": "<",
            "binary-infix>": ">",
            "unary-minus": "-",
            "array-indexer-begin": "取",
            "array-indexer-infix": "之第",
            "array-indexer-suffix": "",
            "array-indexer-end": "",
            "property-length": "之量",
            "funcapp-begin": "施",
            "funcapp-args-begin": "於",
            "funcapp-args-end": "",
            "funcapp-separator": "與",
            "funcapp-noarg": "以虛",
            "import-standard": "引標準庫",
            "import-begin": "引",
            "import-end": "",
            "block-begin": "",
            "block-end": "",
            "assignment-begin": "吾有一數(、|)曰",
            "assignment-infix": "(、|)名之曰",
            "assignment-end": "。",
            "assignment-order": "reversed",
            "increment-begin": "(增|増)",
            "increment-end": "以一(。|)",
            "decrement-begin": "減",
            "decrement-end": "以一(。|)",
            "append-begin": "納",
            "append-infix": "入",
            "append-end": "(。|)",
            "append-order": "reversed",
            "!break": "break",
            "break": "止(。|)",
            "pass": "無為(。|)",
            "print-begin": "吿曰",
            "print-end": "(。|)",
            "!return-begin": "return",
            "return-begin": "以",
            "return-end": "答(。|)",
            "return-none": "還無(。|)",
            "repeat-begin": "",
            "repeat-times": "度、",
            "repeat-block": "",
            "repeat-end": "度畢(。|)",
            "!if-begin": "if",
            "if-begin": "若",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix==": "等於",
            "if-infix!=": "異於",
            "if-infix<": "小於",
            "if-infix>": "大於",
            "if-infix<=": "不大於",
            "if-infix>=": "不小於",
            "if-infixin": "含",
            "if-infixnotin": "不含",
            "if-then": "乎(、|)則",
            "if-else": "否則",
            "if-end": "條畢(。|)",
            "funcdef-begin": "術曰",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "以",
            "funcdef-arg-separator": "與",
            "funcdef-args-end": "",
            "funcdef-noarg": "。",
            "funcdef-block": "",
            "funcdef-end": "術畢(。|)"
    },
    zup: {
            "syntax": "cryptic zup",
            "description": "Zup is a programming language designed to be deliberately opaque to anyone unfamiliar with its specification. All keywords follow a strict CVC (Consonant-Vowel-Consonant) syllable structure, drawn from a constrained phoneme set that avoids common patterns found in natural languages — making the vocabulary impossible to guess by intuition alone.",
            "function-language": "emoji",
            "word-segmenter": " ",
            "comment-begin": "",
            "comment-end": "",
            "indent": "  ",
            "special-name-variable": "Kem\\s+({name_pattern})\\s+par",
            "null": "zup",
            "boolean-true": "vak",
            "boolean-false": "mep",
            "binary-infix+": "rug",
            "binary-infix-": "dap",
            "binary-infix*": "gev",
            "binary-infix/": "kum",
            "binary-infix%": "zen",
            "binary-infix==": "paz",
            "binary-infix!=": "nup",
            "binary-infix<=": "dur",
            "binary-infix>=": "pev",
            "binary-infix<": "dup",
            "binary-infix>": "pep",
            "binary-infixin": "kag",
            "property-length": "\\@kez",
            "import-standard": "Nav rem vaz",
            "import-begin": "Nav",
            "import-end": "",
            "block-begin": ":",
            "block-end": "",
            "assignment-begin": "Kem",
            "assignment-infix": "par",
            "assignment-end": "",
            "increment-begin": "Rav",
            "increment-end": "",
            "decrement-begin": "Zar",
            "decrement-end": "",
            "append-begin": "Mev",
            "append-infix": "naz",
            "append-end": "",
            "break": "Dez kup",
            "pass": "Mup nek",
            "print-begin": "",
            "print-end": "",
            "return-begin": "Dup vem",
            "return-end": "",
            "return-none": "Nag pag",
            "repeat-begin": "Mup dum",
            "repeat-times": "pag",
            "repeat-block": "",
            "repeat-end": "Dam mup",
            "if-begin": "Nev",
            "if-condition-begin": "",
            "if-condition-end": "",
            "if-prefix": "",
            "if-infix==": "paz",
            "if-infix!=": "nup",
            "if-infix<": "dup",
            "if-infix<=": "dur",
            "if-infix>": "pep",
            "if-infix>=": "pev",
            "if-infixin": "kag",
            "if-infixnotin": "nag",
            "if-then": "ger",
            "if-else": "Zum",
            "if-end": "Dam nev",
            "funcdef-begin": "Dum",
            "funcdef-name-begin": "",
            "funcdef-name-end": "",
            "funcdef-args-begin": "\\(",
            "funcdef-arg-separator": ",",
            "funcdef-args-end": "\\)",
            "funcdef-noarg": "",
            "funcdef-block": "",
            "funcdef-end": "Pam dum"
    },
    empty: {
            "syntax": "empty"
    },
};

// ─────────────────────────────────────────────
// Default syntax (merged into every loaded syntax)
// ─────────────────────────────────────────────

const DEFAULT_SYNTAX_JSON = {
    'whitespace':  '[ \\t\\r\u3000]',
    'whitespaces': '[ \\t\\r\u3000]+',
    'linefeed':    '[\\n]',
    'line-comment-begin': '[#\uff03]',

    'number-first-char': '[0-9]',
    'number-chars':      '[0-9]*',
    'number-dot-char':   '[\\.][0-9]',

    'name-first-char': '[A-Za-z_]',
    'name-chars':      '[A-Za-z0-9_]*',

    'string-begin': '"',
    'string-end':   '"',
    'string-escape': '\\\\',
    'string-interpolation-begin': '\\{',
    'string-interpolation-end':   '\\}',

    'grouping-begin': '\\(',
    'grouping-end':   '\\)',

    'array-begin':     '\\[',
    'array-end':       '\\]',
    'array-separator': ',',

    'object-begin':         '\\{',
    'object-end':           '\\}',
    'object-separator':     ',',
    'key-value-separator':  ':',

    'array-indexer-suffix': '\\[',
    'array-indexer-end':    '\\]',
    'unary-minus':          '-',

    'funcapp-args-begin':   '\\(',
    'funcapp-args-end':     '\\)',
    'funcapp-separator':    ',',

    'unary-inspect':  '👀',
    'catch-begin':    '🧤',
    'catch-end':      '🧤',

    'print-begin':    '',
    'print-end':      '',

    'assert-begin':   '>>>\\s+',
    'assert-infix':   '[\\n]',
    'assert-end':     '',
};

// ─────────────────────────────────────────────
// extract identifiers from JSON text (for special-name support)
// ─────────────────────────────────────────────

function extractIdentifiers(text) {
    const identifiers = [];

    // 1. Between newline+= (not ==)
    const pattern1 = /\n\s*([^\s\]\[\(\)"]+)\s*=(?!=)/g;
    let m;
    while ((m = pattern1.exec(text)) !== null) {
        identifiers.push(m[1]);
    }

    // 2. Before ( — function names
    const pattern2 = /([^\s\]\[\(\)"]+)\s*\(/g;
    while ((m = pattern2.exec(text)) !== null) {
        identifiers.push(m[1]);
    }

    // Keep only those with non-ASCII characters
    const withUnicode = identifiers.filter(id => /[^\x00-\x7F]/.test(id));
    return [...new Set(withUnicode)];
}

// ─────────────────────────────────────────────
// loadSyntax — synchronous file-based loading (Node.js / Vitest)
// For browser, pass pre-loaded JSON object as second argument.
// ─────────────────────────────────────────────

export function loadSyntax(nameOrPath = 'yui') {
    let terminals;

    if (typeof nameOrPath === 'object' && nameOrPath !== null) {
        // Already a loaded JSON object
        terminals = { ...nameOrPath };
    } else if (Object.prototype.hasOwnProperty.call(BUILTIN_SYNTAXES, nameOrPath)) {
        // Built-in syntax name
        terminals = { ...BUILTIN_SYNTAXES[nameOrPath] };
    } else {
        throw new Error(`Unknown syntax: "${nameOrPath}". Built-in syntaxes: ${Object.keys(BUILTIN_SYNTAXES).join(', ')}`);
    }

    // Merge defaults
    for (const [key, value] of Object.entries(DEFAULT_SYNTAX_JSON)) {
        if (!(key in terminals)) {
            terminals[key] = value;
        }
    }

    // Build string-content-end
    if (!('string-content-end' in terminals)) {
        const escape = terminals['string-escape'] ?? '\\\\';
        const interp  = terminals['string-interpolation-begin'] ?? '\\{';
        const strEnd  = terminals['string-end'] ?? '\\"';
        terminals['string-content-end'] = `${escape}|${interp}|${strEnd}`;
    }

    // Extract identifiers for special name matching
    if (!('identifiers' in terminals)) {
        terminals['identifiers'] = extractIdentifiers(JSON.stringify(terminals));
    }

    return terminals;
}

// ─────────────────────────────────────────────
// get_example_from_pattern helpers (for CodingVisitor / BNF generation)
// ─────────────────────────────────────────────

function splitHeadingChar(s) {
    if (s.startsWith('\\')) {
        const remaining = s.slice(2);
        let headingChar;
        const next = s[1];
        if (next === '\\') headingChar = '\\';
        else if (next === 's') headingChar = ' ';
        else if (next === 't') headingChar = '\t';
        else if (next === 'n') headingChar = '\n';
        else if (next === 'r') headingChar = '\r';
        else if (next === 'd') headingChar = '1';
        else if (next === 'w') headingChar = 'a';
        else headingChar = next;
        if (remaining.startsWith('?')) return ['', remaining.slice(1)];
        return [headingChar, remaining];
    }
    if (s.startsWith('\u25c1')) { // ▁
        const headingChar = s.slice(0, 2);
        const remaining = s.slice(2);
        if (remaining.startsWith('?')) return ['', remaining.slice(1)];
        return [headingChar, remaining];
    }
    // Handle emoji variation selectors
    if (s.length >= 2 && (s.codePointAt(1) === 0xFE0F || s.codePointAt(1) === 0x200D)) {
        const headingChar = s.slice(0, 2);
        const remaining = s.slice(2);
        if (remaining.startsWith('?')) return ['', remaining.slice(1)];
        return [headingChar, remaining];
    }
    const headingChar = s[0];
    const remaining = s.slice(1);
    if (remaining.startsWith('?')) return ['', remaining.slice(1)];
    return [headingChar, remaining];
}

function getExampleFromPatternInner(pattern) {
    if (pattern === '') return '';
    if (pattern.includes('|')) pattern = pattern.split('|')[0];
    if (pattern.startsWith('[')) {
        const endPos = pattern.indexOf(']');
        if (pattern[endPos + 1] === '?') {
            return getExampleFromPatternInner(pattern.slice(endPos + 2));
        }
        const [headingChar] = splitHeadingChar(pattern.slice(1, endPos));
        return headingChar + getExampleFromPatternInner(pattern.slice(endPos + 1));
    }
    const [headingChar, remaining] = splitHeadingChar(pattern);
    return headingChar + getExampleFromPatternInner(remaining);
}

export function getExampleFromPattern(pattern) {
    const ESC = [
        ['\\|', '\u25c1\uff5c'], ['\\[', '\u25c1\uff3b'], ['\\]', '\u25c1\uff3d'],
        ['\\(', '\u25c1\uff08'], ['\\)', '\u25c1\uff09'], ['\\*', '\u25c1\uff0a'],
        ['\\?', '\u25c1\uff1f'], ['\\+', '\u25c1\uff0b'], ['+', ''], ['*', '?'],
    ];
    for (const [a, b] of ESC) {
        pattern = pattern.split(a).join(b);
    }
    let processed = '';
    while (pattern.length > 0) {
        const sPos = pattern.indexOf('(');
        if (sPos === -1) {
            processed += getExampleFromPatternInner(pattern);
            break;
        }
        const ePos = pattern.indexOf(')', sPos + 1);
        processed += getExampleFromPatternInner(pattern.slice(0, sPos));
        const inner = pattern.slice(sPos + 1, ePos);
        pattern = pattern.slice(ePos + 1);
        if (pattern.startsWith('?')) {
            pattern = pattern.slice(1);
        } else {
            processed += getExampleFromPatternInner(inner);
        }
    }
    const ESC2 = [
        ['\u25c1\uff5c', '|'], ['\u25c1\uff3b', '['], ['\u25c1\uff3d', ']'],
        ['\u25c1\uff08', '('], ['\u25c1\uff09', ')'], ['\u25c1\uff1f', '?'],
        ['\u25c1\uff0b', '+'], ['\u25c1\uff0a', '*'],
    ];
    for (const [a, b] of ESC2) {
        processed = processed.split(a).join(b);
    }
    return processed;
}

// ─────────────────────────────────────────────
// YuiSyntax class
// ─────────────────────────────────────────────

export class YuiSyntax {
    constructor(syntaxJson) {
        if (typeof syntaxJson !== 'object' || syntaxJson === null) {
            throw new Error('Terminals must be a dictionary');
        }
        this.terminals = { ...syntaxJson };
        // compiled regex cache
        this._patterns = {};
    }

    isDefined(terminal) {
        return (this.terminals[terminal] ?? '') !== '';
    }

    updateSyntax(updates) {
        Object.assign(this.terminals, updates);
        // clear cached patterns for updated keys
        for (const key of Object.keys(updates)) {
            delete this._patterns[key];
        }
    }

    getPattern(terminal, ifUndefined = '') {
        if (this._patterns[terminal]) return this._patterns[terminal];
        let pattern = this.terminals[terminal] ?? ifUndefined;
        if (pattern === '' || pattern === null || pattern === undefined) {
            // Return a regex that never matches
            const never = /(?!)/;
            this._patterns[terminal] = never;
            return never;
        }
        if (typeof pattern === 'string') {
            try {
                pattern = new RegExp(pattern, 'u');
            } catch {
                try {
                    pattern = new RegExp(pattern); // retry without unicode
                } catch (e2) {
                    throw new Error(`Invalid regex '${terminal}': ${pattern}: ${e2}`);
                }
            }
            this._patterns[terminal] = pattern;
        }
        return pattern;
    }

    forExample(terminal) {
        if (!this.isDefined(terminal)) return '';
        let p = this.terminals[terminal];
        if (p instanceof RegExp) p = p.source;
        return getExampleFromPattern(p);
    }
}
