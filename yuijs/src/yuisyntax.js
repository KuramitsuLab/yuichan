// yuisyntax.js — syntax loading and YuiSyntax class (port of yuichan/yuisyntax.py)
// Browser-compatible: all built-in syntaxes are inlined as JS objects.
// No fs/path/url imports — works in both Node.js and browsers (including file://).

// ─────────────────────────────────────────────
// Built-in syntax definitions (inlined from syntax/*.json)
// ─────────────────────────────────────────────

const BUILTIN_SYNTAXES = {
    yui: {
        "syntax": "Yui-Classic",
        "whitespace": "[ \\t\\r\u3000]",
        "whitespaces": "[ \\t\\r\u3000]+",
        "linefeed": "[\\n]",
        "word-segmenter": " ",
        "line-comment-begin": "[#\uff03]",
        "comment-begin": "",
        "comment-end": "",
        "null": "\u5024\u306a\u3057|null",
        "boolean-true": "\u771f|true",
        "boolean-false": "\u507d|false",
        "number-first-char": "[0-9]",
        "number-chars": "[0-9]*",
        "number-dot-char": "[\\.]",
        "name-first-char": "[A-Za-z_]",
        "name-chars": "[A-Za-z0-9_]*",
        "extra-name-begin": "\u300c",
        "extra-name-end": "\u300d",
        "string-begin": "\"",
        "string-end": "\"",
        "string-escape": "\\\\",
        "string-interpolation-begin": "\\{",
        "string-interpolation-end": "\\}",
        "string-content-end": "\\\\|\\{|\\\"",
        "!string-begin": "'|f\"",
        "array-begin": "\\[",
        "array-end": "\\]",
        "array-separator": "[,\u3001\uff0c]",
        "object-begin": "\\{",
        "object-end": "\\}",
        "object-separator": "[,\u3001\uff0c]",
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
        "unary-minus": "-",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "property-accessor": "\u306e",
        "property-length": "\u5927\u304d\u3055",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": "[,\u3001\uff0c]",
        "import-standard": "\u6a19\u6e96\u30e9\u30a4\u30d6\u30e9\u30ea\u3092\u4f7f\u3046",
        "import-operator": "\u56db\u5247\u6f14\u7b97\u5b50\u3092\u4f7f\u3046",
        "import-begin": "",
        "import-end": "\u3092\u4f7f\u3046",
        "block-begin": "[\\{｛]",
        "block-end": "[\\}｝]",
        "block-line": "",
        "assignment-begin": "",
        "assignment-infix": "[=\uff1d]",
        "assignment-end": "",
        "increment-begin": "",
        "increment-infix": "",
        "increment-end": "\u3092\u5897\u3084\u3059",
        "increment-lookahead": "\u5897\u3084\u3059",
        "decrement-begin": "",
        "decrement-infix": "",
        "decrement-end": "\u3092\u6e1b\u3089\u3059",
        "append-begin": "",
        "append-infix": "(\u306e\u672b\u5c3e)?\u306b",
        "append-end": "\u3092\u8ffd\u52a0\u3059\u308b",
        "print-begin": "",
        "print-end": "",
        "break": "\u304f\u308a\u8fd4\u3057\u3092\u629c\u3051\u308b",
        "pass": "\u4f55\u3082\u3057\u306a\u3044",
        "return-begin": "",
        "return-end": "\u304c[\u3001]?\u7b54\u3048",
        "return-none": "\u95a2\u6570\u304b\u3089\u629c\u3051\u308b",
        "repeat-begin": "",
        "repeat-times": "\u56de[\u3001]?",
        "repeat-block": "\u304f\u308a\u8fd4\u3059",
        "repeat-end": "",
        "if-begin": "\u3082\u3057",
        "if-condition-begin": "",
        "if-condition-end": "",
        "if-prefix": "",
        "if-infix": "\u304c",
        "if-suffix!=": "\u4ee5\u5916",
        "if-suffix<": "\u3088\u308a\u5c0f\u3055\u3044",
        "if-suffix<=": "\u4ee5\u4e0b",
        "if-suffix>": "\u3088\u308a\u5927\u304d\u3044",
        "if-suffix>=": "\u4ee5\u4e0a",
        "if-suffixin": "\u306e\u3044\u305a\u308c\u304b",
        "if-suffixnotin": "\u306e\u3044\u305a\u308c\u3067\u3082\u306a\u3044",
        "if-then": "\u306a\u3089\u3070[\u3001]?",
        "if-else": "\u305d\u3046\u3067\u306a\u3051\u308c\u3070[\u3001]?",
        "if-end": "",
        "funcdef-begin": "",
        "funcdef-name-begin": "",
        "funcdef-name-end": "[=\uff1d]",
        "funcdef-args-begin": "\u5165\u529b",
        "funcdef-arg-separator": "[,\u3001]",
        "funcdef-args-end": "",
        "funcdef-noarg": "\u5165\u529b\u306a\u3057",
        "funcdef-block": "\u306b\u5bfe\u3057[\u3066]?[\u3001]?",
        "funcdef-end": "",
        "assert-begin": ">>>\\s+",
        "assert-infix": "[\\n]",
        "assert-end": "",
    },
    pylike: {
        "syntax": "yui",
        "whitespace": "[ \\t\\r\u3000]",
        "whitespaces": "[ \\t\\r\u3000]+",
        "linefeed": "[\\n]",
        "word-segmenter": " ",
        "line-comment-begin": "[#\uff03]",
        "comment-begin": "",
        "comment-end": "",
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
        "grouping-begin!": "\\(",
        "grouping-end!": "\\)",
        "length-begin": "len\\s*\\(",
        "length-end": "\\)  ",
        "binary-infix+": "\\+",
        "binary-infix-": "-",
        "binary-infix*": "\\*",
        "binary-infix/": "/",
        "binary-infix%": "%",
        "unary-minus": "-",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "property-accessor": "\\.",
        "property-type": "__class__.__name__",
        "not-property-name": "append",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": ",",
        "block-begin": "\\:",
        "block-end": "",
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
        "block-else": "else\\b|elif\\b|except\\b|finally\\b",
        "break": "break",
        "pass": "pass",
        "return-begin": "return\\s+",
        "return-end": "",
        "repeat-begin": "for\\s+_\\s+in\\s+range\\s*\\(\\s*",
        "repeat-times": "\\)\\s*",
        "repeat-block": "",
        "repeat-end": "",
        "if-begin": "if\\s",
        "if-condition-begin": "\\(?",
        "if-condition-end": "\\)?",
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
        "assert-begin": "assert\\s",
        "assert-infix": "==",
        "assert-end": "",
        "import-standard": "import\\s+stdlib",
        "import-begin": "import\\s",
        "import-end": "",
    },
    jslike: {
        "syntax": "javascript-like",
        "whitespace": "[ \\t\\r\u3000]",
        "whitespaces": "[ \\t\\r\u3000]+",
        "linefeed": "[\\n]",
        "word-segmenter": " ",
        "line-comment-begin": "//",
        "comment-begin": "/\\*",
        "comment-end": "\\*/",
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
        "grouping-begin!": "\\(",
        "grouping-end!": "\\)",
        "binary-infix+": "\\+",
        "binary-infix-": "-",
        "binary-infix*": "\\*",
        "binary-infix/": "/",
        "binary-infix%": "%",
        "unary-minus": "-",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "property-accessor": "\\.",
        "property-length": "length",
        "not-property-name": "push",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": ",",
        "block-begin": "\\:",
        "block-end": "",
        "block-line": "",
        "assignment-begin": "",
        "assignment-infix": "\\=",
        "assignment-end": "",
        "increment-begin": "",
        "increment-infix": "\\+\\+|\\+\\=\\s*1",
        "increment-end": "1",
        "decrement-begin": "",
        "decrement-infix": "\\-\\-|\\-\\=\\s*1",
        "decrement-end": "1",
        "append-begin": "",
        "append-infix": ".push\\s*\\(",
        "append-suffix": "\\)",
        "append-end": "",
        "import-begin": "import\\s",
        "import-end": "",
        "print-begin": "",
        "print-end": "",
        "break": "break\\s?",
        "continue": "continue\\s?",
        "pass": "",
        "return-begin": "return\\s",
        "return-end": "",
        "repeat-begin": "for\\s+_\\s+in\\s+range\\s*\\(\\s*",
        "repeat-times": "\\)\\s*",
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
        "if-infixin": "in\\s",
        "if-infixnotin": "not\\s+in\\s",
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
        "funcdef-end": "",
        "assert-begin": "assert\\s*",
        "assert-infix": "==",
        "assert-end": "",
    },
    emoji: {
        "syntax": "\ud83e\udea2",
        "whitespace": "[ \\t\\r\u3000]",
        "whitespaces": "[ \\t\\r\u3000]+",
        "word-segmenter": " ",
        "linefeed": "[\\n]",
        "line-comment-begin": "\ud83d\udcad|\ud83d\udde8\ufe0f|\ud83d\udccc|\u26a0\ufe0f",
        "comment-begin": "",
        "comment-end": "",
        "number-first-char": "[0-9]",
        "number-chars": "[0-9]*",
        "number-dot-char": "[\\.]",
        "null": "\ud83e\udeb5",
        "boolean-true": "\ud83d\udc4d",
        "boolean-false": "\ud83d\udc4e",
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
        "unary-length": "\ud83d\udcd0",
        "unary-inspect": "\ud83d\udc40",
        "binary-infix+": "\u2795",
        "binary-infix-": "\u2796",
        "binary-infix*": "\u2716\ufe0f",
        "binary-infix/": "\u2797",
        "binary-infix%": "\ud83c\udf55",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "property-accessor": "",
        "property-type": "",
        "not-property-name": "",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": ",",
        "block-begin": "\ud83d\udc49",
        "block-end": "\ud83d\udd1a",
        "assignment-begin": "",
        "assignment-infix": "\u2b05\ufe0f",
        "assignment-end": "",
        "increment-begin": "",
        "increment-infix": "\u2b06\ufe0f",
        "increment-end": "",
        "decrement-begin": "",
        "decrement-infix": "\u2b07\ufe0f",
        "decrement-end": "",
        "append-begin": "",
        "append-infix": "\ud83e\uddf2",
        "append-suffix": "",
        "append-end": "",
        "print-begin": "",
        "print-end": "",
        "break": "\ud83d\ude80",
        "pass": "\ud83d\udca4",
        "return-begin": "\u2705|\ud83d\udca1",
        "return-end": "",
        "repeat-begin": "\ud83c\udf00",
        "repeat-times": "",
        "repeat-block": "",
        "repeat-end": "",
        "if-begin": "\u2753|\ud83e\udd14",
        "if-condition-begin": "",
        "if-condition-end": "",
        "if-prefix": "",
        "if-infix==": "\u2696\ufe0f",
        "if-infix!=": "\ud83d\udeab\u2696\ufe0f",
        "if-infix<": "\ud83d\udcc8",
        "if-infix<=": "\ud83d\udcc8\u2696\ufe0f",
        "if-infix>": "\ud83d\udcc9",
        "if-infix>=": "\ud83d\udcc9\u2696\ufe0f",
        "if-infixin": "\ud83d\udce5",
        "if-infixnotin": "\ud83d\udeab\ud83d\udce5",
        "if-then": "",
        "else-if": "\u2757\u2753",
        "if-else": "\u2757|\ud83d\ude45",
        "if-end": "",
        "funcdef-begin": "\ud83e\udde9",
        "funcdef-name-begin": "",
        "funcdef-name-end": "",
        "funcdef-args-begin": "\\(",
        "funcdef-arg-separator": "\\,",
        "funcdef-args-end": "\\)",
        "funcdef-noarg": "",
        "funcdef-block": "",
        "funcdef-end": "",
        "assert-begin": "\ud83e\uddea",
        "assert-infix": "\u2705",
        "assert-end": "",
        "import-standard": "\ud83d\uddf3\ufe0f\\s+\ud83d\udcda",
        "import-operator": "\ud83d\uddf3\ufe0f\\s+\u2795\u2796\u2716\ufe0f\u2797",
        "import-begin": "\ud83d\uddf3\ufe0f",
        "import-end": "",
    },
    nannan: {
        "syntax": "\u306a\u3093\u306a\u3093\uff1f",
        "whitespace": "[ \\t\\r\u3000]",
        "whitespaces": "[ \\t\\r\u3000]+",
        "linefeed": "[\\n]",
        "line-comment-begin": "\u26a0\ufe0f",
        "comment-begin": "",
        "comment-end": "",
        "number-first-char": "[0-9]",
        "number-chars": "[0-9]*",
        "number-dot-char": "[\\.]",
        "name-first-char": "[A-Za-z_]",
        "name-chars": "[A-Za-z0-9_]*",
        "extra-name-begin": "\u300c",
        "extra-name-end": "\u300d",
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
        "grouping-begin!": "\\(",
        "grouping-end!": "\\)",
        "length-begin": "\\|",
        "length-end": "\\|",
        "binary-infix+": "\\+",
        "binary-infix-": "-",
        "binary-infix*": "\\*",
        "binary-infix/": "/",
        "binary-infix%": "%",
        "unary-minus": "-",
        "array-indexer-suffix": "\\[",
        "array-indexer-end": "\\]",
        "property-accessor": "\u306e",
        "property-length": "\u5927\u304d\u3055",
        "funcapp-args-begin": "\\(",
        "funcapp-args-end": "\\)",
        "funcapp-separator": ",",
        "import-standard": "\u6a19\u6e96\u306e\u3084\u3064\u4f7f\u3046",
        "import-operator": "\u56db\u5247\u6f14\u7b97\u5b50[\u3001]?\u4f7f\u3046",
        "import-begin": "",
        "import-end": "\u3092\u4f7f\u3046",
        "block-begin": "[\uff1f\\?]",
        "block-end": "",
        "block-line": "",
        "assignment-begin": "",
        "assignment-infix": "=",
        "assignment-end": "",
        "increment-begin": "",
        "increment-infix": "",
        "increment-end": "\u4e0a\u3052\u3068\u304f",
        "increment-lookahead": "\u4e0a\u3052\u3068\u304f",
        "decrement-begin": "",
        "decrement-infix": "",
        "decrement-end": "\u4e0b\u3052\u3068\u304f",
        "decrement-lookahead": "\u4e0b\u3052\u3068\u304f",
        "append-begin": "",
        "append-infix": "\u306b",
        "append-suffix": "\u3092?",
        "append-end": "\u5165\u308c\u3068\u304f",
        "print-begin": "",
        "print-end": "",
        "break": "\u3082\u3046\u3048\u3048\u3063\u3066",
        "pass": "\u307b\u3063\u3068\u304f",
        "return-begin": "\u261d\ufe0f\u3053\u306e",
        "return-end": "\u3060\u3088",
        "return-none": "\u308f\u304b\u3089\u3093",
        "repeat-begin": "",
        "repeat-times": "\u56de[\u3001]?",
        "repeat-block": "\u3084\u308d\u304b",
        "repeat-end": "",
        "if-begin": "",
        "if-condition-begin": "",
        "if-condition-end": "",
        "if-prefix": "",
        "if-infix": "\u304c",
        "if-suffix==": "\u3068\u540c\u3058",
        "if-suffix!=": "\u3084\u306a\u3044",
        "if-suffix<": "\u3088\u308a\u5c0f\u3055\u3044",
        "if-suffix<=": "\u4ee5\u4e0b",
        "if-suffix>": "\u3088\u308a\u5927\u304d\u3044",
        "if-suffix>=": "\u4ee5\u4e0a",
        "if-suffixin": "\u306e\u3044\u305a\u308c\u304b",
        "if-suffixnotin": "\u306e\u3044\u305a\u308c\u3067\u3082\u306a\u3044",
        "if-then": "\u3063\u3066\u307b\u3093\u307e",
        "if-else": "\u9055\u3046\u3093",
        "if-end": "",
        "funcdef-begin": "",
        "funcdef-name-begin": "",
        "funcdef-name-end": "",
        "funcdef-args-begin": "\\(",
        "funcdef-arg-separator": "[,\u3001]",
        "funcdef-args-end": "\\)",
        "funcdef-block": "\u3063\u3066\u306a\u3093\u306a\u3093",
        "funcdef-end": "",
        "assert-begin": ">>>\\s+",
        "assert-infix": "[\\n]",
        "assert-end": "",
    },
    sexpr: {
        "syntax": "s-expression",
        "whitespace": "[ \\t\\r\\n\u3000]",
        "whitespaces": "[ \\t\\r\\n\u3000]+",
        "linefeed": "[\\n]",
        "line-comment-begin": ";",
        "comment-begin": "",
        "comment-end": "",
        "word-segmenter": " ",
        "indent": "",
        "keywords": "begin\\b|require\\b|inc\\b|dec\\b|append\\b|set\\b|aref\\b|if\\b|repeat\\b|break\\b|print\\b|assert\\b|define\\b|return\\b",
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
        "grouping-begin!": "",
        "grouping-end!": "",
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
        "print-begin": "\\(print\\s+",
        "print-end": "\\)",
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
        "if-condition-end": "\\)\\s+",
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
        "funcdef-args-end": "\\)\\s+",
        "funcdef-noarg": "",
        "funcdef-block": "",
        "funcdef-end": "\\)",
        "assert-begin": "\\(assert\\s+",
        "assert-infix": "",
        "assert-end": "\\)",
    },
    empty: {
        "syntax": "empty",
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
    'number-dot-char':   '[\\.]',

    'name-first-char': '[A-Za-z_]',
    'name-chars':      '[A-Za-z0-9_]*',

    'string-begin': '"',
    'string-end':   '"',
    'string-escape': '\\\\',
    'string-interpolation-begin': '\\{',
    'string-interpolation-end':   '\\}',

    'array-begin':     '\\[',
    'array-end':       '\\]',
    'array-separator': ',',

    'object-begin':         '\\{',
    'object-end':           '\\}',
    'object-separator':     ',',
    'key-value-separator':  ':',

    'array-indexer-suffix': '\\[',
    'array-indexer-end':    '\\]',

    'funcapp-args-begin':    '\\(',
    'funcapp-args-end':       '\\)',
    'funcapp-separator': ',',
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
