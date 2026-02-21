# Syntax JSON Reference

Each `syntax/*.json` file is a flat dictionary that maps **token names** to **regex patterns**.
The parser (`yuiparser.py`) consumes tokens by matching these patterns against the source code.
The code generator (`yuicoding.py`, `CodingVisitor`) emits tokens by calling
`for_example(terminal)` which returns one representative string from the regex.

---

## Conventions

### Empty string = undefined

An empty string value `""` means the token is **not defined** for this syntax.
- Parser: `is_defined(terminal)` returns `False`; the token is silently skipped.
- Emitter: `terminal(key)` is a no-op; nothing is emitted.

```json
"block-end": ""       // indent-based syntax: no explicit block-end token
"repeat-end": ""      // loop body ends implicitly
```

### `!key` — wrong-token detector

A key prefixed with `!` defines a **error pattern**.
If `!key` matches where the normal `key` is expected, the parser raises an error
with a message showing what was matched and what was expected.

```json
"!string-begin": "'|f\""   // raise an error if a Python-style quote is used
```

### `key!` — grouping shorthand

A key suffixed with `!` (e.g., `"grouping-begin!": "\\("`) is treated the same as the
matching unprefixed key, but the `!` signals that the corresponding wrong-token detector
is auto-generated.  Both `grouping-begin` and `grouping-end` work as normal tokens.

### `*-lookahead` keys

Any token whose name ends with `-lookahead` holds a regex that is searched against the
**entire current line** before the parser decides whether backtracking is allowed.

- If the pattern is **found** on the current line: backtracking is **disabled** (`BK=False`).
  A parse failure becomes a hard error instead of trying the next alternative.
- If the pattern is **not found** (or the key is undefined): backtracking is **allowed**.

```json
"increment-lookahead": "増やす"   // if "増やす" appears on this line, must be Increment
```

### `word-segmenter`

When `word-segmenter` is defined, the emitter (`CodingVisitor`) automatically inserts
a space between tokens that are not punctuation.  This is used by `pylike` and `emoji`
syntaxes where words must be separated, but not by `yui` (Yui-Classic).

---

## Grammar Notation

BNF rules below use the following conventions:

- `token-name` — literal token from syntax.json (consumed by parser / emitted by generator)
- `@Nonterminal` — recursive grammar rule (parsed by a dedicated `ParserCombinator`)
- `[ ... ]` — optional
- `{ ... }` — zero or more repetitions
- `|` — alternatives (first match wins)
- `*` — defined only when the key is not the empty string

---

## 1. Whitespace and Comments

### Tokens

| Token | Description |
|-------|-------------|
| `whitespace` | Regex for a single horizontal whitespace character (space, tab, etc.) |
| `whitespaces` | Regex for one or more horizontal whitespace characters |
| `linefeed` | Regex for the newline character `\n` |
| `word-segmenter` | When defined, `CodingVisitor` inserts a space between adjacent tokens |
| `line-comment-begin` | Marks the start of a line comment; the rest of the line is consumed and ignored |
| `comment-begin` | Opening of a block comment (both `comment-begin` and `comment-end` must be defined) |
| `comment-end` | Closing of a block comment |

### Grammar

```
LineComment  ::= line-comment-begin <rest of line>
BlockComment ::= comment-begin <...> comment-end
Whitespace   ::= whitespaces | linefeed | LineComment | BlockComment
```

### Examples

| Token | yui (Yui-Classic) | pylike | emoji |
|-------|-------------------|--------|-------|
| `whitespace` | `[ \t\r　]` | same | same |
| `line-comment-begin` | `[#＃]` | `[#＃]` | `💭\|🗨️\|📌\|⚠️` |
| `word-segmenter` | *(undefined)* | `" "` | `" "` |
| `comment-begin` | *(undefined)* | *(undefined)* | *(undefined)* |

---

## 2. Numbers

### Tokens

| Token | Description |
|-------|-------------|
| `number-first-char` | Regex for the first character of a number literal (typically `[0-9]`) |
| `number-chars` | Regex for the remaining digits |
| `number-dot-char` | Regex for the decimal point (`.`) |

### Grammar

```
Number ::= number-first-char number-chars
         | number-first-char number-chars number-dot-char number-first-char number-chars
```

Parses to `NumberNode(int)` or `NumberNode(float)`.

---

## 3. Booleans

### Tokens

| Token | Description |
|-------|-------------|
| `boolean-true` | Token for the boolean `true` value (parsed as `NumberNode(1)`) |
| `boolean-false` | Token for the boolean `false` value (parsed as `NumberNode(0)`) |

### Grammar

```
Boolean ::= boolean-true | boolean-false
```

Booleans are only defined in the emoji syntax (`👍` / `👎`).
In yui and pylike, booleans are parsed as names (`True`, `False`).

---

## 4. Names (Identifiers)

### Tokens

| Token | Description |
|-------|-------------|
| `name-first-char` | First character of an identifier (typically `[A-Za-z_]`) |
| `name-chars` | Remaining characters of an identifier |
| `name-end` | Optional suffix immediately after the name (no whitespace skip) |
| `extra-name-begin` | Opening delimiter for quoted identifiers (e.g., `「`) |
| `extra-name-end` | Closing delimiter for quoted identifiers (e.g., `」`) |

### Grammar

```
Name ::= extra-name-begin <any chars until extra-name-end> extra-name-end
       | name-first-char name-chars [ name-end ]
```

The parser first checks **special names** (identifiers with Unicode chars auto-detected
from the source) before applying the regex rules.

### Examples

| Token | yui | pylike | emoji |
|-------|-----|--------|-------|
| `name-first-char` | `[A-Za-z_]` | same | same |
| `extra-name-begin` | `「` | *(undefined)* | *(undefined)* |
| `extra-name-end` | `」` | *(undefined)* | *(undefined)* |

---

## 5. Strings

### Tokens

| Token | Description |
|-------|-------------|
| `string-begin` | Opening quote (e.g., `"`) |
| `string-end` | Closing quote (e.g., `"`) |
| `string-escape` | Escape character (e.g., `\\`) |
| `string-interpolation-begin` | Opens an interpolated expression (e.g., `\{`) |
| `string-interpolation-end` | Closes an interpolated expression (e.g., `\}`) |
| `string-content-end` | Regex matching any of: escape, interpolation-begin, or string-end; used to scan forward through string content |
| `!string-begin` | Wrong-token detector: raises an error if a disallowed quote style is used |

### Grammar

```
String        ::= string-begin { StringContent } string-end
StringContent ::= <raw chars until string-content-end>
               | string-escape <char>
               | string-interpolation-begin @Expression string-interpolation-end
```

Parses to `StringNode(str)` (no interpolation) or `StringNode(list)` (with interpolation).

---

## 6. Arrays

### Tokens

| Token | Description |
|-------|-------------|
| `array-begin` | Opening bracket (e.g., `[`) |
| `array-end` | Closing bracket (e.g., `]`) |
| `array-separator` | Element separator (e.g., `,`) |

### Grammar

```
Array ::= array-begin [ @Expression { array-separator @Expression } ] array-end
```

Parses to `ArrayNode(elements)`. Newlines inside the array are allowed.

---

## 7. Objects (Dictionaries)

### Tokens

| Token | Description |
|-------|-------------|
| `object-begin` | Opening brace (e.g., `{`) |
| `object-end` | Closing brace (e.g., `}`) |
| `object-separator` | Separator between key-value pairs (e.g., `,`) |
| `key-value-separator` | Separator between key and value (e.g., `:`) |

### Grammar

```
Object ::= object-begin
             [ @String key-value-separator @Expression
               { object-separator @String key-value-separator @Expression } ]
           object-end
```

Keys must be `@String` literals. Parses to `ObjectNode(elements)`.

---

## 8. Expressions

### 8.1 Grouping

| Token | Description |
|-------|-------------|
| `grouping-begin` | Opening parenthesis for grouped expressions |
| `grouping-end` | Closing parenthesis |

```
Grouping ::= grouping-begin @Expression grouping-end
```

### 8.2 Length Operator

Three alternative forms:

| Tokens | Form | Description |
|--------|------|-------------|
| `length-begin` + `length-end` | Bracket: `\|expr\|` | Surrounding the expression |
| `unary-length` | Prefix: `📐 expr` | Prefix operator |
| `property-accessor` + `property-length` | Property: `expr.len` | Property access form |

Only one form is typically defined per syntax.

### 8.3 Unary Operators

| Token | Description |
|-------|-------------|
| `unary-minus` | Negation prefix (e.g., `-`) |
| `unary-inspection` | Inspection/debug print prefix |

```
Unary ::= unary-minus @Primary
        | unary-inspection @Primary
        | unary-length @Primary
        | @Term
```

### 8.4 Binary Operators

| Token | Operator | Precedence |
|-------|----------|------------|
| `binary*` | multiplication | Multiplicative |
| `binary/` | division | Multiplicative |
| `binary%` | modulo | Multiplicative |
| `binary+` | addition | Additive |
| `binary-` | subtraction | Additive |
| `binary==` | equal | Comparative |
| `binary!=` | not equal | Comparative |
| `binary<` | less than | Comparative |
| `binary<=` | less or equal | Comparative |
| `binary>` | greater than | Comparative |
| `binary>=` | greater or equal | Comparative |
| `binaryin` | membership test | Comparative |
| `binarynotin` | non-membership test | Comparative |

```
@Expression    ::= @Comparative
@Comparative   ::= @Additive [ binary== @Additive | binary!= @Additive | ... ]
@Additive      ::= @Multiplicative [ binary+ @Additive | binary- @Additive ]
@Multiplicative::= @Primary [ binary* @Multiplicative | binary/ @Multiplicative | binary% @Multiplicative ]
@Primary       ::= @Term { @Postfix }
@Term          ::= Grouping | Length | @Number | @String | @Array | @Object | @Boolean | @Name
```

Comparative operators produce `BinaryNode(..., comparative=True)` which is recognized
specially by `IfParser` (see §10.7).

### 8.5 Array Indexing

| Token | Description |
|-------|-------------|
| `array-indexer-suffix` | Opens the index bracket (e.g., `[`) — immediately after the expression |
| `array-indexer-end` | Closes the index bracket (e.g., `]`) |

```
IndexAccess ::= @Expression array-indexer-suffix @Expression array-indexer-end
```

Parses to `GetIndexNode(collection, index)`.

### 8.6 Property Access

| Token | Description |
|-------|-------------|
| `property-accessor` | Separator between object and property name (e.g., `.`, `の`) |
| `property-length` | Property name that maps to array length (e.g., `大きさ\|個数`) |
| `property-type` | Property name that maps to type query (e.g., `__class__.__name__`) |
| `not-property-name` | A name that must **not** follow `property-accessor` (e.g., `append` — it's an `@Append` statement, not a property) |

```
PropertyAccess ::= @Expression property-accessor ( property-length | property-type )
```

### 8.7 Function Application

| Token | Description |
|-------|-------------|
| `funcapp-args-suffix` | Opens the argument list (e.g., `(`) — immediately after the function name |
| `funcapp-args-separator` | Separates arguments (e.g., `,`) |
| `funcapp-args-end` | Closes the argument list (e.g., `)`) |

```
FuncApp ::= @Expression funcapp-args-suffix
              [ @Expression { funcapp-args-separator @Expression } ]
            funcapp-args-end
```

Parses to `FuncAppNode(name, arguments)`.

---

## 9. Blocks

Blocks appear inside `if`, `repeat`, and `funcdef` constructs, and at the top level.

### Tokens

| Token | Description |
|-------|-------------|
| `block-begin` | Opens an explicit block (e.g., `{`, `👉`, `:`) |
| `block-end` | Closes an explicit block (e.g., `}`, `🔚`). When empty, the block is indent-delimited. |
| `block-separator` | Emitter only: emitted between statements in a block (e.g., `;`). Usually undefined. |
| `statement-separator` | Separates multiple statements on a single line (e.g., `;`). If undefined, only one statement per line. |

### Grammar

```
@Block ::= block-begin [ block-end ]       // empty block
         | block-begin @Statement[] block-end   // explicit delimiters (yui/emoji)
         | block-begin @Statement[]             // indent-based (pylike: block-end is empty)
```

For **indent-based** syntaxes (`block-end` is empty), `BlockParser` tracks the indentation
level of the line that introduced the block and stops when indentation decreases.

For **explicit-delimiter** syntaxes, the parser reads until it matches `block-end`.

Parses to `BlockNode(statements)`.

### Top-Level

```
@TopLevel ::= { whitespace | linefeed } { @Statement[] { whitespace | linefeed } }
```

Parses to `BlockNode(statements, top_level=True)`. Top-level blocks do not emit
`block-begin`/`block-end`.

---

## 10. Statements

The parser tries each statement type in order:
`@FuncDef`, `@Assignment`, `@Assert`, `@If`, `@Repeat`, `@Break`, `@Increment`,
`@Decrement`, `@Append`, `@Return`, `@Import`, `@Pass`, `@PrintExpression`.

Backtracking is controlled by `*-lookahead` tokens (see §Conventions).

### 10.1 Assignment

| Token | Description |
|-------|-------------|
| `assignment-begin` | Optional prefix before the left-hand side |
| `assignment-infix` | The assignment operator (e.g., `=`, `⬅️`) |
| `assignment-end` | Optional suffix after the right-hand side |
| `assignment-lookahead` | Lookahead regex to disable backtracking |

```
@Assignment ::= [ assignment-begin ] @Expression assignment-infix @Expression [ assignment-end ]
```

Parses to `AssignmentNode(variable, expression)`.

### 10.2 Increment

| Token | Description |
|-------|-------------|
| `increment-begin` | Optional prefix |
| `increment-infix` | The increment operator (e.g., `を` / `+=` / `⬆️`) |
| `increment-end` | Optional suffix (e.g., `増やす` / `1`) |
| `increment-lookahead` | Lookahead regex |

```
@Increment ::= [ increment-begin ] @Expression increment-infix [ increment-end ]
```

Parses to `IncrementNode(variable)`.

### 10.3 Decrement

| Token | Description |
|-------|-------------|
| `decrement-begin` | Optional prefix |
| `decrement-infix` | The decrement operator (e.g., `を` / `-=` / `⬇️`) |
| `decrement-end` | Optional suffix (e.g., `減らす` / `1`) |
| `decrement-lookahead` | Lookahead regex |

```
@Decrement ::= [ decrement-begin ] @Expression decrement-infix [ decrement-end ]
```

Parses to `DecrementNode(variable)`.

### 10.4 Append

| Token | Description |
|-------|-------------|
| `append-begin` | Optional prefix |
| `append-infix` | Separator between list and value (e.g., `に` / `.append\s*(` / `🧲`) |
| `append-suffix` | After value (e.g., `を` / `)`) |
| `append-end` | Final suffix (e.g., `追加する`) |
| `append-lookahead` | Lookahead regex |

```
@Append ::= [ append-begin ] @Expression append-infix @Expression [ append-suffix ] [ append-end ]
```

Parses to `AppendNode(variable, expression)`.

### 10.5 Break / Continue / Pass

| Token | Description |
|-------|-------------|
| `break` | Single token for break (e.g., `くり返しを抜ける` / `break` / `🚀`) |
| `continue` | Single token for continue (e.g., `もう一度くり返す` / `continue`) |
| `pass` | Single token for no-op (e.g., `何もしない` / `pass` / `💤`) |

```
@Break    ::= break
@Pass     ::= pass
```

`continue` has no dedicated parser; it falls through to `@PrintExpression` when used
(where the name `continue` is a valid expression). The token is available for emitter use.

### 10.6 Return

| Token | Description |
|-------|-------------|
| `return-begin` | Keyword/prefix before the return value (e.g., `return ` / `✅\|💡`) |
| `return-end` | Suffix after the return value (e.g., `が[、 ]?答え`) |
| `return-none` | Token for void/bare return (e.g., `関数から抜ける`) |
| `return-lookahead` | Lookahead regex |

```
@Return ::= return-begin @Expression [ return-end ]
```

The `return-none` token is used by the emitter when returning `None` (no expression).
The parser does not handle `return-none` separately; it falls through to `@PrintExpression`.

Parses to `ReturnNode(expression)`.

### 10.7 If / Else

| Token | Description |
|-------|-------------|
| `if-begin` | Opening keyword (e.g., `もし` / `if ` / `❓\|🤔`) |
| `if-condition-begin` | Optional opening around the condition (e.g., `\(?`) |
| `if-condition-end` | Optional closing around the condition (e.g., `\)?`) |
| `if-infix` | Generic comparison word between left and right sides (e.g., `が`) |
| `if-infix==` | Infix token for `==` comparison |
| `if-infix!=` | Infix token for `!=` comparison |
| `if-infix<` | Infix token for `<` comparison |
| `if-infix<=` | Infix token for `<=` comparison |
| `if-infix>` | Infix token for `>` comparison |
| `if-infix>=` | Infix token for `>=` comparison |
| `if-infixin` | Infix token for `in` membership |
| `if-infixnotin` | Infix token for `not in` membership |
| `if-suffix` | Generic suffix after the right side that determines operator (e.g., implies `==` by default) |
| `if-suffix!=` | Suffix meaning `!=` |
| `if-suffix<` | Suffix meaning `<` |
| `if-suffix<=` | Suffix meaning `<=` |
| `if-suffix>` | Suffix meaning `>` |
| `if-suffix>=` | Suffix meaning `>=` |
| `if-suffixin` | Suffix meaning `in` |
| `if-suffixnotin` | Suffix meaning `not in` |
| `if-then` | Separator before the then-block (e.g., `ならば` / `block-begin` in pylike) |
| `if-else` | Else keyword (e.g., `そうでなければ` / `else` / `❗\|🙅`) |
| `if-else-if` | Else-if keyword used by the **emitter** when the else branch is itself an `IfNode` |
| `if-end` | End of if statement (e.g., empty in pylike/emoji; used when needed) |
| `if-lookahead` | Lookahead regex |

The condition can be written in two forms:

**Comparative expression form** — when `binary==`, `binary!=`, etc. are defined, the
parser parses the whole condition as a `@Comparative` expression, which produces a
`BinaryNode(..., comparative=True)`. The operator is extracted from the `BinaryNode`.

**Infix form** — the parser reads: left-expression, then scans for any `if-infix*` token,
then right-expression, then scans for any `if-suffix*` token. The matched suffix
(or infix, if defined) determines the comparison operator. If none matches, defaults to `==`.

```
@If ::= if-begin [ if-condition-begin ]
          ( @Comparative_comparative              // binary== etc. recognized
          | @Expression if-infix @Expression [ if-suffix* ] )
        [ if-condition-end ]
        if-then @Block
        [ if-else @Block | if-else @If ]
        [ if-end ]
```

Parses to `IfNode(left, operator, right, then_block, else_block)`.

### 10.8 Repeat

| Token | Description |
|-------|-------------|
| `repeat-begin` | Loop keyword/prefix (e.g., empty / `for _ in range(` / `🌀`) |
| `repeat-times` | Between count expression and block (e.g., `回[、]?` / `)\s*`) |
| `repeat-block` | Keyword before block (e.g., `くり返す`) |
| `repeat-end` | End of loop (usually empty; explicit when `block-end` is empty) |
| `repeat-lookahead` | Lookahead regex |

```
@Repeat ::= [ repeat-begin ] @Expression repeat-times [ repeat-block ] @Block [ repeat-end ]
```

Parses to `RepeatNode(count, block)`.

### 10.9 Function Definition

| Token | Description |
|-------|-------------|
| `funcdef-begin` | Opening keyword (e.g., empty / `def ` / `🧩`) |
| `funcdef-name-begin` | Optional token before the function name |
| `funcdef-name-end` | Optional token after the function name (e.g., `=` in yui) |
| `funcdef-noarg` | Token that signals zero parameters (e.g., `入力なし`); skips `funcdef-args-begin/end` |
| `funcdef-args-begin` | Opens the parameter list (e.g., `入力` / `(`) |
| `funcdef-arg-separator` | Separates parameters (e.g., `[,、]` / `,`) |
| `funcdef-args-end` | Closes the parameter list (e.g., `)`) |
| `funcdef-block` | Separator before the body (e.g., `に対し[て]?[、]?`) |
| `funcdef-end` | End of function definition (usually empty; explicit when `block-end` is empty) |
| `funcdef-lookahead` | Lookahead regex |

```
@FuncDef ::= [ funcdef-begin ] [ funcdef-name-begin ] @Name [ funcdef-name-end ]
               ( funcdef-noarg
               | funcdef-args-begin { @Name [ funcdef-arg-separator ] } funcdef-args-end )
             [ funcdef-block ] @Block [ funcdef-end ]
```

Parses to `FuncDefNode(name, parameters, body)`.

### 10.10 Assert

| Token | Description |
|-------|-------------|
| `assert-begin` | Prefix (e.g., `>>> ` / `assert ` / `🧪`) |
| `assert-infix` | Between the test expression and reference value (e.g., `[\n]` / `==` / `✅`) |
| `assert-end` | Optional suffix |
| `assert-lookahead` | Lookahead regex |

```
@Assert ::= assert-begin @Expression assert-infix @Expression [ assert-end ]
```

Parses to `AssertNode(test, reference)`.

### 10.11 Import

| Token | Description |
|-------|-------------|
| `import-standard` | Full token for importing the standard library |
| `import-operator` | Full token for importing arithmetic operators |
| `import-begin` | Prefix for a general import statement |
| `import-end` | Suffix for a general import statement |

```
@Import ::= import-standard
```

Only `import-standard` is currently handled by the parser.
`import-begin`/`import-end` are available for future use.

Parses to `ImportNode()`.

### 10.12 Print Expression

| Token | Description |
|-------|-------------|
| `print-begin` | Optional prefix (e.g., `print(` in some syntaxes; usually empty) |
| `print-end` | Optional suffix (e.g., `)`) |
| `print-lookahead` | Lookahead regex |

```
@PrintExpression ::= [ print-begin ] @Expression [ print-end ]
```

This is the **catch-all** statement: any expression that does not match a more specific
statement form is parsed as a `PrintExpressionNode`.  In execution, its value is printed.

Parses to `PrintExpressionNode(expression)`.

---

## 11. Complete Token Index

| Token | Used by | Notes |
|-------|---------|-------|
| `whitespace` | `Source.skip_whitespaces_and_comments` | Single whitespace char |
| `whitespaces` | `Source.skip_whitespaces_and_comments` | One or more whitespace |
| `linefeed` | Parser, BlockParser | Newline `\n` |
| `word-segmenter` | `CodingVisitor.word_segment` | When defined, spaces inserted between tokens |
| `line-comment-begin` | `Source.skip_whitespaces_and_comments` | Line comment trigger |
| `comment-begin` | `Source.skip_whitespaces_and_comments` | Block comment open |
| `comment-end` | `Source.skip_whitespaces_and_comments` | Block comment close |
| `number-first-char` | `NumberParser` | First digit |
| `number-chars` | `NumberParser` | Rest of digits |
| `number-dot-char` | `NumberParser` | Decimal separator |
| `boolean-true` | `BooleanParser` | `true` literal → `NumberNode(1)` |
| `boolean-false` | `BooleanParser` | `false` literal → `NumberNode(0)` |
| `name-first-char` | `NameParser` | First identifier char |
| `name-chars` | `NameParser` | Rest of identifier |
| `name-end` | `NameParser` | Optional suffix after name |
| `extra-name-begin` | `NameParser` | Opening of quoted identifier |
| `extra-name-end` | `NameParser` | Closing of quoted identifier |
| `string-begin` | `StringParser` | Opening quote |
| `string-end` | `StringParser` | Closing quote |
| `string-escape` | `StringParser` | Escape character |
| `string-interpolation-begin` | `StringParser` | Start of `${...}` interpolation |
| `string-interpolation-end` | `StringParser` | End of interpolation |
| `string-content-end` | `StringParser` | Lookahead: end of raw string segment |
| `!string-begin` | `Source.is_match` | Wrong-token detector for strings |
| `array-begin` | `ArrayParser` | `[` |
| `array-end` | `ArrayParser` | `]` |
| `array-separator` | `ArrayParser` | `,` between elements |
| `object-begin` | `ObjectParser` | `{` |
| `object-end` | `ObjectParser` | `}` |
| `object-separator` | `ObjectParser` | `,` between key-value pairs |
| `key-value-separator` | `ObjectParser` | `:` between key and value |
| `grouping-begin` | `TermParser` | `(` for expression grouping |
| `grouping-end` | `TermParser` | `)` |
| `length-begin` | `TermParser` | Opening of `|expr|` length form |
| `length-end` | `TermParser` | Closing of `|expr|` length form |
| `unary-minus` | `PrimaryParser` | Negation prefix |
| `unary-length` | `PrimaryParser` | Length prefix (e.g., `📐`) |
| `unary-inspection` | `PrimaryParser` | Debug-print prefix |
| `binary+` | `AdditiveParser` | Addition |
| `binary-` | `AdditiveParser` | Subtraction |
| `binary*` | `MultiplicativeParser` | Multiplication |
| `binary/` | `MultiplicativeParser` | Division |
| `binary%` | `MultiplicativeParser` | Modulo |
| `binary==` | `ComparativeParser` | Equal |
| `binary!=` | `ComparativeParser` | Not equal |
| `binary<` | `ComparativeParser` | Less than |
| `binary<=` | `ComparativeParser` | Less or equal |
| `binary>` | `ComparativeParser` | Greater than |
| `binary>=` | `ComparativeParser` | Greater or equal |
| `binaryin` | `ComparativeParser` | Membership |
| `binarynotin` | `ComparativeParser` | Non-membership |
| `array-indexer-suffix` | `PrimaryParser` | `[` after expression |
| `array-indexer-end` | `PrimaryParser` | `]` closing index |
| `property-accessor` | `PrimaryParser` | `.` or `の` |
| `property-length` | `PrimaryParser` | Property name for length |
| `property-type` | `PrimaryParser` | Property name for type |
| `not-property-name` | `PrimaryParser` | Name excluded from property access |
| `funcapp-args-suffix` | `PrimaryParser` | `(` opening args |
| `funcapp-args-separator` | `PrimaryParser` | `,` between args |
| `funcapp-args-end` | `PrimaryParser` | `)` closing args |
| `import-standard` | `ImportParser` | Full standard-library import token |
| `import-operator` | *(emitter only)* | Full operator-library import token |
| `import-begin` | *(emitter only)* | Prefix for generic import |
| `import-end` | *(emitter only)* | Suffix for generic import |
| `block-begin` | `BlockParser` | `{` / `👉` / `:` |
| `block-end` | `BlockParser` | `}` / `🔚` / `""` for indent-based |
| `block-separator` | `CodingVisitor` (emitter only) | Between statements in a block |
| `statement-separator` | `StatementsParser`, `Source.capture_line` | Multiple statements per line |
| `assignment-begin` | `AssignmentParser` | Optional prefix |
| `assignment-infix` | `AssignmentParser` | `=` / `⬅️` |
| `assignment-end` | `AssignmentParser` | Optional suffix |
| `assignment-lookahead` | `AssignmentParser` | Disable-backtrack regex |
| `increment-begin` | `IncrementParser` | Optional prefix |
| `increment-infix` | `IncrementParser` | `を` / `+=` / `⬆️` |
| `increment-end` | `IncrementParser` | `増やす` / `1` |
| `increment-lookahead` | `IncrementParser` | Disable-backtrack regex |
| `decrement-begin` | `DecrementParser` | Optional prefix |
| `decrement-infix` | `DecrementParser` | `を` / `-=` / `⬇️` |
| `decrement-end` | `DecrementParser` | `減らす` / `1` |
| `decrement-lookahead` | `DecrementParser` | Disable-backtrack regex |
| `append-begin` | `AppendParser` | Optional prefix |
| `append-infix` | `AppendParser` | `に` / `.append(` / `🧲` |
| `append-suffix` | `AppendParser` | `を` / `)` |
| `append-end` | `AppendParser` | `追加する` |
| `append-lookahead` | `AppendParser` | Disable-backtrack regex |
| `break` | `BreakParser` | Break token |
| `continue` | *(emitter only)* | Continue token |
| `pass` | `PassParser` | No-op token |
| `return-begin` | `ReturnParser` | Return keyword/prefix |
| `return-end` | `ReturnParser` | Optional suffix |
| `return-none` | `CodingVisitor` (emitter only) | Void return |
| `return-lookahead` | `ReturnParser` | Disable-backtrack regex |
| `print-begin` | `PrintExpressionParser` | Optional print prefix |
| `print-end` | `PrintExpressionParser` | Optional print suffix |
| `print-lookahead` | `PrintExpressionParser` | Disable-backtrack regex |
| `repeat-begin` | `RepeatParser` | Loop keyword |
| `repeat-times` | `RepeatParser` | After count, before block |
| `repeat-block` | `RepeatParser` | Before block |
| `repeat-end` | `RepeatParser` | After block |
| `repeat-lookahead` | `RepeatParser` | Disable-backtrack regex |
| `if-begin` | `IfParser` | `もし` / `if ` / `❓` |
| `if-condition-begin` | `IfParser` | Optional `(` around condition |
| `if-condition-end` | `IfParser` | Optional `)` around condition |
| `if-infix` | `IfParser` | Generic comparison word |
| `if-infix==` … `if-infixnotin` | `IfParser` | Specific comparison infixes |
| `if-suffix` … `if-suffixnotin` | `IfParser` | Suffixes determining operator |
| `if-then` | `IfParser` | Before then-block |
| `if-else` | `IfParser` | Else keyword |
| `if-else-if` | `CodingVisitor` (emitter only) | Else-if shorthand in emitter |
| `if-end` | `IfParser` | After if statement |
| `if-lookahead` | `IfParser` | Disable-backtrack regex |
| `funcdef-begin` | `FuncDefParser` | `def ` / `🧩` |
| `funcdef-name-begin` | `FuncDefParser` | Before function name |
| `funcdef-name-end` | `FuncDefParser` | After function name |
| `funcdef-noarg` | `FuncDefParser` | Signals zero-parameter function |
| `funcdef-args-begin` | `FuncDefParser` | Opens parameter list |
| `funcdef-arg-separator` | `FuncDefParser` | Between parameters |
| `funcdef-args-end` | `FuncDefParser` | Closes parameter list |
| `funcdef-block` | `FuncDefParser` | Before body block |
| `funcdef-end` | `FuncDefParser` | After body block |
| `funcdef-lookahead` | `FuncDefParser` | Disable-backtrack regex |
| `assert-begin` | `AssertParser` | `>>> ` / `assert ` / `🧪` |
| `assert-infix` | `AssertParser` | Between test and reference |
| `assert-end` | `AssertParser` | Optional suffix |
| `assert-lookahead` | `AssertParser` | Disable-backtrack regex |
