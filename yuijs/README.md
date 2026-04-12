# yuijs

Yui 言語 (日本語プログラミング言語) の JavaScript 実装。Python 版 [`yuichan`](../yuichan/) の 1:1 移植。

**主な用途は Web アプリへの埋め込み**: 学習環境 / オンライン REPL / ブラウザ内実行環境で Yui コードを解析・実行するために設計されています。Node CLI としても使えますが、そちらはおまけ扱いです。

## 特徴

- **Pure ESM**. core モジュールは `node:*` に一切依存しない (`node --test` と CLI のみ Node 固有 API を使う)
- **組み込み grammar 11 個**: `yui`, `pylike`, `jslike`, `sexpr`, `wenyan`, `bridget`, `emoji`, `nannan`, `zup`, `ast`, `empty` — すべて `src/yuigrammars.js` に辞書としてインライン化されているので fetch 不要
- **外部 grammar の URL ロード**: `loadSyntaxFromUrl(url)` で JSON を非同期取得
- **yui ↔ 他構文への変換**: `convert(source, {from, to})` で構文間の相互変換
- **統一された Runtime**: `run(source, {syntax, env})` で 1 呼び出し完結、低レベルな `YuiRuntime` / `YuiParser` / `CodingVisitor` も直接使用可

---

## インストール / 要件

- Node.js 20 以上 (global `fetch` が使える環境)
- ブラウザ用途では ES2022 対応のバンドラ (Vite / esbuild / Rollup / webpack 5+)

現時点では npm に未公開です。ローカルで試す場合:

```sh
git clone <this repo>
cd yuichan/yuijs
npm test
```

### バンドルサイズ目安 (esbuild, browser, ESM)

検証済み (esbuild 0.25):

| variant | bytes | gzipped |
|---|---|---|
| no minify | 235 KB | — |
| minify | 124 KB | **31 KB** |

組み込み grammar 11 個 (30 KB 相当) がすべて含まれてこのサイズです。
`--keep-names` などのミニファイヤ固有オプションは不要 — AST 自身が minify 耐性のある visitor dispatch (`constructor.nodeName`) を内蔵しているため、esbuild / terser / webpack の default 設定でそのままバンドルできます。

---

## クイックスタート

### Node で実行

```js
import { run } from './src/index.js';

const source = `
x=1
y=2
`;

const { value, env, runtime } = run(source, { syntax: 'yui' });

console.log(value); // 最後の式の値 (eval モード)
console.log(env);   // { x: 1, y: 2 }
```

### ブラウザで埋め込み

```html
<script type="module">
  import { run, YuiError } from '/path/to/yuijs/src/index.js';

  const source = document.querySelector('#editor').value;
  try {
    const { env } = run(source, { syntax: 'yui' });
    console.log('env:', env);
  } catch (err) {
    if (err instanceof YuiError) {
      console.error('Yui error:', err.messages);
    } else {
      throw err;
    }
  }
</script>
```

バンドラを使う場合は通常の `import { run } from 'yuijs'` で OK です (package.json の `main`/`exports` で解決)。

---

## 公開 API

### `run(source, options?) → { value, env, runtime }`

Yui ソースを 1 発で実行し、結果と変数環境を返す。Web アプリからの主要な呼び出し口です。

| option | default | 説明 |
|---|---|---|
| `syntax` | `'yui'` | grammar 名 (`SYNTAX_NAMES` のいずれか) または terminals オブジェクト |
| `timeout` | `30` | 実行タイムアウト (秒) |
| `allowBinaryOps` | `false` | `+ - * / %` を許可する (標準ライブラリの `和()`/`積()` などを使わない場合) |
| `env` | `{}` | 実行開始時の初期変数環境 (JS ネイティブ値が自動で YuiValue に box される) |

戻り値:

- `value` — eval モードでアンボックスしたネイティブ値
- `env` — 最終スコープのスナップショット (`@` 始まりの関数エントリは除外)
- `runtime` — 使い終わった `YuiRuntime` インスタンス (`runtime.test_passed` / `runtime.increment_count` など統計を取得できる)

エラーは `YuiError` を throw します。呼び出し側で `instanceof YuiError` で捕捉してください。

```js
import { run, YuiError, formatMessages } from './src/index.js';

try {
  run('x を増やす', { syntax: 'yui' });
} catch (err) {
  if (err instanceof YuiError) {
    console.error(formatMessages(err.messages));
  }
}
```

---

### `convert(source, {from, to, indentString?, functionLanguage?}) → string`

ソースコードを別の構文に変換する (parser + CodingVisitor の組み合わせ)。

```js
import { convert } from './src/index.js';

const yuiSrc = 'x=1\ny=2\n';
const pylike = convert(yuiSrc, { from: 'yui', to: 'pylike' });
// → "x = 1\ny = 2\n"
```

`functionLanguage` は標準ライブラリ関数名の言語 (`'ja'` / `'en'` / `'emoji'`)。

---

### `loadSyntax(name | terminals) → terminals`

組み込み grammar の終端記号辞書を取得する (同期)。デフォルト値 (`DEFAULT_SYNTAX_JSON`) も自動で補完されます。

```js
import { loadSyntax } from './src/index.js';

const yui = loadSyntax('yui');
// 未知の名前は明示的に throw
loadSyntax('unknown');
// → Error: unknown syntax: unknown (available: ast, bridget, ...)
```

オブジェクトを渡すとそのまま shallow copy + デフォルト補完されます (テスト用の custom grammar を注入したいときに便利)。

---

### `loadSyntaxFromUrl(url, {fetch?}?) → Promise<terminals>`

外部サイトから grammar JSON を fetch する。**Web 埋め込みで独自構文を配信したい場合の主要 API**。

```js
import { loadSyntaxFromUrl, run } from './src/index.js';

const terminals = await loadSyntaxFromUrl('/grammars/my-lang.json');
const { env } = run(source, { syntax: terminals });
```

`globalThis.fetch` を使います。テスト等で差し替えたい場合は `{ fetch: mockFetch }` を渡してください。

- HTTP 非 2xx → 例外
- JSON が object でない → 例外
- `globalThis.fetch` が無い環境 → 例外 (`Node 18+` またはブラウザが必要)

---

### 低レベル API

埋め込み先で細かく制御したい場合:

```js
import {
  YuiRuntime,
  YuiParser,
  CodingVisitor,
  types,
  YuiValue,
  FloatType,
} from './src/index.js';

const rt = new YuiRuntime();
rt.allow_binary_ops = true;
rt.setenv('x', new YuiValue(10));
const env = rt.exec('x を増やす\n', 'yui', { evalMode: false });
console.log(types.unbox(env.x)); // 11
```

エクスポートされる主なシンボル:

- **ランタイム**: `YuiRuntime`, `YuiFunction`, `LocalFunction`, `NativeFunction`, `YuiBreakException`, `YuiReturnException`
- **パーサ / コード生成**: `YuiParser`, `Source`, `SourceNode`, `CodingVisitor`, `YuiSyntax`
- **型システム**: `YuiValue`, `types`, `OPERATORS`, `YuiNullType`/`YuiBooleanType`/`YuiIntType`/`YuiFloatType`/`YuiNumberType`/`YuiStringType`/`YuiArrayType`/`YuiObjectType` (とそれぞれの singleton `NullType`/`BoolType`/...)
- **AST ノード**: `ConstNode`, `NumberNode`, `StringNode`, `NameNode`, `ArrayNode`, `ObjectNode`, `MinusNode`, `ArrayLenNode`, `GetIndexNode`, `BinaryNode`, `FuncAppNode`, `AssignmentNode`, `IncrementNode`, `DecrementNode`, `AppendNode`, `BlockNode`, `IfNode`, `RepeatNode`, `BreakNode`, `PassNode`, `ImportNode`, `ReturnNode`, `FuncDefNode`, `PrintExpressionNode`, `AssertNode`, `CatchNode`, 変換ヘルパ `_node`
- **エラー**: `YuiError`, `ERROR_MESSAGES`, `formatMessages`, `normalizeMessages`, `setVerbose`, `isVerbose`
- **grammar**: `loadSyntax`, `loadSyntaxFromUrl`, `listSyntaxNames`, `findMatchingSyntaxes`, `generateBnf`, `GRAMMARS`, `SYNTAX_NAMES`, `getGrammar`, `DEFAULT_SYNTAX_JSON`
- **標準ライブラリ**: `standardLib`
- **サンプル**: `YuiExample`, `getAllExamples`, `getSamples`, `getTestExamples`
- **メタ**: `VERSION`

---

## 組み込み grammar

| name | 説明 |
|---|---|
| `yui` | 日本語基本構文 (`x=1`, `x を増やす`, `もし x == 0 ならば`) |
| `pylike` | Python 風 |
| `jslike` | JavaScript 風 |
| `sexpr` | S 式 |
| `wenyan` | 古典中国語風 |
| `bridget` | 英語風 |
| `emoji` | 絵文字構文 |
| `nannan` | ナンナン構文 |
| `zup` | ZUP 構文 |
| `ast` | AST 直書き |
| `empty` | 空の雛形 |

すべて `src/yuigrammars.js` にインラインで埋め込まれています (合計 約 30 KB)。元の JSON は `syntax/*.json` にあり、編集後は `npm run build-grammars` で再生成してください:

```sh
npm run build-grammars
# → Generated yuijs/src/yuigrammars.js (11 grammars, 30.6 KB)
```

---

## サンプルコード (YuiExample)

Yui の機能を網羅するビルトインサンプル 20 種を提供しています:

```js
import { getAllExamples, getSamples } from './src/index.js';

for (const ex of getSamples()) {
  console.log(`=== ${ex.name}: ${ex.description} ===`);
  console.log(ex.generate('yui')); // 'pylike' や 'emoji' も指定可
}
```

`exampleHelloWorld()` / `exampleFizzbuzz()` / `exampleRecursiveFunction()` / `exampleMonteCarlo()` などの factory 関数を直接 import することもできます (AST レベルで編集したい時に便利)。

---

## CLI (簡易)

Web 埋め込みが主用途なので CLI は最低限です:

```sh
# ファイル実行
node src/main.js --syntax yui path/to/file.yui

# stdin から実行
echo 'x=1
y=2' | node src/main.js --syntax yui

# 使える grammar 一覧
node src/main.js --syntax-list

# ヘルプ
node src/main.js --help
```

`package.json#bin` で `yuijs` コマンドとしても呼べます (npm link 後):

```sh
yuijs --syntax yui path/to/file.yui
```

Python 版 `main.py` にある REPL / `--pass@1` / `--convert-to` / `--make-examples` などは未実装です。必要なら `import { run, convert } from 'yuijs'` を直接使ってください。

---

## 開発

```sh
npm test                  # node --test 'test/**/*.test.js' → 666 passed
npm run build-grammars    # syntax/*.json → src/yuigrammars.js を再生成
npm start -- --help       # CLI ヘルプ
```

### ディレクトリ構成

```
yuijs/
├── src/
│   ├── index.js         # 公開 API エントリ (Web 埋め込み向け)
│   ├── main.js          # CLI (Node 専用 / 簡易)
│   ├── yuierror.js
│   ├── yuisyntax.js     # Pure ESM: loadSyntax / loadSyntaxFromUrl
│   ├── yuigrammars.js   # 自動生成: 組み込み grammar の辞書
│   ├── yuitypes.js      # YuiValue / YuiType / types / OPERATORS
│   ├── yuiast.js        # AST ノード定義
│   ├── yuistdlib.js     # 標準ライブラリ (和 / 積 / 最大値 / ...)
│   ├── yuicoding.js     # CodingVisitor (ソースコード生成)
│   ├── yuiparser.js     # Packrat パーサ
│   ├── yuiruntime.js    # RuntimeVisitor
│   └── yuiexample.js    # ビルトインサンプル 20 種
├── syntax/              # 組み込み grammar の元ファイル (JSON)
├── scripts/
│   └── build-grammars.js
├── test/                # node --test ファイル群
└── package.json
```

---

## ブラウザバンドル手順 (再現)

```sh
# esbuild で ESM ブラウザバンドルを作る
npx esbuild src/index.js --bundle --format=esm --platform=browser --minify \
  --outfile=dist/yuijs.min.js
```

Vite / Rollup で使う場合、`yuijs` を依存として追加するだけで自動的に解決されます:

```js
// vite.config.js / rollup.config.js 等での import
import { run, convert } from 'yuijs';
```

### バンドルの注意点

- **core モジュールは `node:*` を一切 import しない** ので、`platform: 'browser'` の warning は出ません
- `src/main.js` (CLI) は `node:fs` / `node:process` を使用するため、ブラウザバンドルには含めないこと (`src/index.js` をエントリにすれば main.js は tree-shake で除外される)
- visitor dispatch は静的 `nodeName` 登録 (`yuiast.js` 末尾) を使っているので、ミニファイヤの class 名 mangling に**影響されません**。`--keep-names` / `keep_classnames` 相当のオプションは不要

---

## アーキテクチャメモ

### 型システム

- `YuiValue` は native 値 + 型タグ。`types.box(x)` / `types.unbox(x)` で相互変換
- `Number.isInteger(x)` で int/float を判別するので、`1.0` は int 扱い。明示的に float にしたい場合は `new YuiValue(1, FloatType)` を使う
- `int OP float → float` の保全は `yuiruntime.js:visitBinaryNode` 側で明示的に `new YuiValue(result, FloatType)` して行う (Python の `isinstance(x, float)` に相当する判別が JS にないため)

### パーサ

- Packrat (メモ化付きの parser combinator)。Python 版と構造は同じ
- `Source extends YuiSyntax` で terminals を持つ
- 正規表現は sticky フラグ (`y`) で `regex.lastIndex = pos; regex.exec(source)` が Python の `pattern.match(s, pos)` と等価

### バイナリ演算子

- `rt.allow_binary_ops = true` で明示的に有効化する必要あり (デフォルト無効)
- 代わりに標準ライブラリの `和(a,b)` / `積(a,b)` / `商(a,b)` などを使える
- 標準ライブラリ使用には Yui ソース先頭に `標準ライブラリを使う` が必要

### テスト

`node --test` (Node 標準のテストランナー) を使用しています。vitest / jest などの依存はありません。

現在の状況: **666 passed / 0 failed**

---

## ライセンス / 関連プロジェクト

- Python 実装: [yuichan](../yuichan/) (SSoT)
- Yui 言語仕様: `doc/` 配下を参照
