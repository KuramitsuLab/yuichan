# yuijs — Yui言語 JavaScript ランタイム

yuichan（日本語プログラミング言語 Yui）の JavaScript 移植版。
ブラウザ上で Yui プログラムを実行・コード生成するための ES Module ライブラリ。

---

## セットアップ

```bash
npm install          # vitest のみ（dev dependency）
npm test             # テスト実行（vitest）
```

`src/index.js` から必要なクラスをインポートして使う。

---

## クイックスタート

```javascript
import { Yui } from './src/index.js';

const yui = new Yui();
yui.exec('x = 42');
```

`Yui` クラスは高レベル API。毎回新しい `YuiRuntime` を使いたい場合は `yui.reset()` を呼ぶ。

---

## YuiRuntime — 低レベル API

Web UI では `YuiRuntime` を直接使うほうが柔軟。

```javascript
import { YuiRuntime } from './src/yuiruntime.js';
import { YuiError, YuiType } from './src/yuitypes.js';

const rt = new YuiRuntime();
```

### `rt.exec(source, syntax, timeout, evalMode)`

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `source` | `string` | — | 実行する Yui ソースコード |
| `syntax` | `string` | `'yui'` | 構文名（後述） |
| `timeout` | `number` | `30` | タイムアウト（秒）。`0` で無効 |
| `evalMode` | `boolean` | `true` | `true` → 最終値をネイティブ JS 値で返す。`false` → 変数環境オブジェクトを返す |

```javascript
// evalMode=true: 最後の式の値を返す
const result = rt.exec('x = 和(3, 4)', 'yui', 30, true);

// evalMode=false: 変数環境を返す
const env = rt.exec('x = 42', 'yui', 30, false);
console.log(YuiType.yuiToNative(env['x'])); // 42
```

### 利用可能な構文

| 構文名 | ファイル | 説明 |
|---|---|---|
| `'yui'` | `syntax/yui.json` | 日本語構文（標準） |
| `'pylike'` | `syntax/pylike.json` | Python 風 ASCII 構文 |
| `'jslike'` | `syntax/jslike.json` | JavaScript 風構文 |
| `'emoji'` | `syntax/emoji.json` | 絵文字構文 |
| `'nannan'` | `syntax/nannan.json` | nannan 構文 |

### 標準ライブラリ

`和`, `積`, `差`, `商` などの算術関数を使うにはソース先頭に一行追加する。

```javascript
const STDLIB = '標準ライブラリを使う\n';
rt.exec(STDLIB + 'x = 和(3, 4)');
```

---

## 出力のキャプチャ

デフォルトでは `console.log` に出力される。Web UI では `rt.print` を上書きする。

```javascript
const rt = new YuiRuntime();
const lines = [];

rt.print = (value, node) => {
    lines.push(String(value));
};

rt.exec('"Hello, world!"', 'yui', 30, false);
console.log(lines); // ["Hello, world!"]
```

`print(value, node)` の引数:

| 引数 | 型 | 説明 |
|---|---|---|
| `value` | `YuiValue` | 表示する値 |
| `node` | `ASTNode` | 呼び出し元ノード（行番号取得に使用） |

`node.extract()` で `[lineNumber, column, snippet]` を取得できる。

```javascript
rt.print = (value, node) => {
    const [line, col, snippet] = node.extract();
    lines.push({ line, value: String(value) });
};
```

---

## エラーハンドリング

`exec()` は構文エラー・実行時エラーで `YuiError` を投げる。

```javascript
import { YuiError } from './src/yuitypes.js';

try {
    rt.exec(source, 'yui', 30, false);
} catch (e) {
    if (e instanceof YuiError) {
        // 構文エラー: e.runtime === null
        // 実行時エラー: e.runtime !== null
        console.error(e.formattedMessage());
    } else {
        throw e; // 予期しない内部エラー
    }
}
```

### YuiError のプロパティ

| プロパティ | 型 | 説明 |
|---|---|---|
| `e.messages` | `string[]` | エラーメッセージトークンの配列 |
| `e.message` | `string` | `messages.join(' ')` |
| `e.lineno` | `number` | エラー発生行（1始まり、不明時は `0`） |
| `e.offset` | `number` | エラー発生列（1始まり） |
| `e.text` | `string` | エラー箇所のソース行テキスト |
| `e.runtime` | `YuiRuntime\|null` | `null` = 構文エラー、非null = 実行時エラー |

### `e.formattedMessage(prefix, marker, lineoffset)`

人間が読みやすい形式のエラー文字列を返す。

```javascript
e.formattedMessage()
// "[構文エラー/SyntaxError] wrong name ❌foo line 2, column 3:\n  foo\n  ^^^"
// "[実行時エラー/RuntimeError] undefined variable ❌x line 1, column 1:\n  x\n  ^^^\n[環境/Environment] ..."
```

### エディタとの連携例

`e.lineno` と `e.offset` を使ってエラー箇所をハイライトできる。

```javascript
try {
    rt.exec(source, 'yui', 30, false);
} catch (e) {
    if (e instanceof YuiError) {
        markError({
            line: e.lineno,           // 1始まり
            col: e.offset,            // 1始まり
            message: e.messages.join(' '),
        });
    }
}
```

---

## 実行停止

`rt.shouldStop = true` をセットすると、次のループ反復またはネストした処理の境界で
`YuiError(['interrupted'])` が投げられ実行が中断される。

```javascript
const rt = new YuiRuntime();

// 別スレッド（Worker）や setTimeout から停止させる
const timer = setTimeout(() => { rt.shouldStop = true; }, 5000);

try {
    rt.exec(infiniteLoopSource, 'yui', 0 /* timeout無効 */, false);
} catch (e) {
    if (e instanceof YuiError && e.messages[0] === 'interrupted') {
        console.log('実行を中断しました');
    }
}
clearTimeout(timer);
```

> **Note**: `timeout` 引数（秒）でも自動停止できる（デフォルト 30 秒）。
> `timeout: 0` で自動停止を無効化し、`shouldStop` で手動制御できる。

---

## 変数環境へのアクセス

`evalMode=false` のとき `exec()` は変数環境オブジェクト `{ [name]: YuiValue }` を返す。

```javascript
const env = rt.exec('x = 42\ny = [1, 2, 3]', 'yui', 30, false);

// YuiValue → JS ネイティブ値への変換
const x = YuiType.yuiToNative(env['x']); // 42
const y = YuiType.yuiToNative(env['y']); // [1, 2, 3]
```

関数は `'@' + 名前` で格納されている（例: `env['@succ']`）。

```javascript
const env = rt.exec('succ = 入力 n に対し { nを増やす  nが答え }', 'yui', 30, false);
const func = env['@succ']; // LocalFunctionV インスタンス
```

複数回 `exec()` を続けて呼ぶと変数環境は累積される（REPL 的な使い方）。

```javascript
rt.exec('x = 1', 'yui', 30, false);
rt.exec('xを増やす', 'yui', 30, false);
const env = rt.exec('', 'yui', 30, false);
YuiType.yuiToNative(env['x']); // 2
```

---

## テスト / アサート追跡

`>>>` 構文（doctest 形式）を使うと `rt.testPassed` / `rt.testFailed` に記録される。

```javascript
const rt = new YuiRuntime();
const STDLIB = '標準ライブラリを使う\n';
rt.exec(STDLIB + '>>> 和(1, 2)\n3', 'yui', 30, false);

console.log(rt.testPassed.length); // 1
console.log(rt.testFailed.length); // 0
```

`testPassed` と `testFailed` はそれぞれ文字列の配列（テスト式のスニペット）。

---

## コード生成（CodingVisitor）

AST から Yui ソースコードを生成する。パーサーの逆変換。

```javascript
import { CodingVisitor } from './src/yuicoding.js';
import { BlockNode, AssignmentNode, NumberNode, NameNode } from './src/yuiast.js';

const ast = new BlockNode([
    new AssignmentNode(new NameNode('x'), new NumberNode(42)),
], true);

const visitor = new CodingVisitor('yui');
const code = visitor.emit(ast);
// "x=42"
```

異なる構文に変換することも可能。

```javascript
const yuiCode   = new CodingVisitor('yui').emit(ast);
const pylikeCode = new CodingVisitor('pylike').emit(ast);
```

---

## サンプルコード生成（YuiExample）

`yuiexample.js` は 17 種類のサンプル AST を提供する。

```javascript
import { getAllExamples, exampleRecursiveFunction } from './src/yuiexample.js';

// すべてのサンプル
const examples = getAllExamples();
for (const ex of examples) {
    console.log(ex.name);          // "recursive_function"
    console.log(ex.description);   // "Recursive function definition and call ..."
    console.log(ex.generate('yui'));  // Yui ソースコード文字列
}

// 特定のサンプルを実行
const ex = exampleRecursiveFunction();
const rt = new YuiRuntime();
rt.exec(ex.generate('yui'), 'yui', 30, false);
console.log(rt.testPassed.length); // 2
```

### 利用可能なサンプル

| 関数名 | 内容 |
|---|---|
| `exampleHelloWorld()` | "Hello, world!" を表示 |
| `exampleVariables()` | 変数の定義とインクリメント/デクリメント |
| `exampleLoop()` | 10回ループして5で break |
| `exampleNestedConditionalBranches()` | ネストした条件分岐 |
| `exampleComparisons()` | 比較演算子（==, !=, <, >, <=, >=） |
| `exampleArray()` | 配列の作成・追加・インデックスアクセス |
| `exampleStrings()` | 文字列の作成・文字操作 |
| `exampleObjects()` | オブジェクトの作成・プロパティ操作 |
| `exampleFunction()` | 関数定義と呼び出し |
| `exampleFunctionNoArgument()` | 引数なし関数 |
| `exampleFunctionWithoutReturn()` | 戻り値なし関数（ローカル環境をオブジェクトとして返す） |
| `exampleRecursiveFunction()` | 再帰関数（階乗） |
| `exampleFloatAdd()` | 浮動小数点加算（標準ライブラリなし、桁配列方式） |
| `exampleNullAssignment()` | null の代入と比較 |
| `exampleBooleanAssignment()` | true/false の代入と比較 |
| `exampleBooleanBranch()` | boolean による条件分岐 |
| `exampleNullCheck()` | null チェック関数 |

---

## Web UI 統合パターン

### 最小構成

```javascript
import { YuiRuntime } from './src/yuiruntime.js';
import { YuiError, YuiType } from './src/yuitypes.js';

function runYui(source, onOutput, onError) {
    const rt = new YuiRuntime();
    rt.print = (value) => onOutput(String(value));

    try {
        rt.exec(source, 'yui', 10, false);
    } catch (e) {
        if (e instanceof YuiError) {
            onError({
                line: e.lineno,
                col: e.offset,
                message: e.messages.join(' '),
                formatted: e.formattedMessage(),
            });
        } else {
            onError({ message: String(e) });
        }
    }

    return {
        testPassed: rt.testPassed.length,
        testFailed: rt.testFailed.length,
    };
}
```

### キャンセル対応（Web Worker 例）

```javascript
// worker.js
import { YuiRuntime } from './src/yuiruntime.js';
import { YuiError } from './src/yuitypes.js';

let rt = null;

self.onmessage = ({ data }) => {
    if (data.type === 'run') {
        rt = new YuiRuntime();
        rt.print = (value) => self.postMessage({ type: 'output', text: String(value) });
        try {
            rt.exec(data.source, 'yui', 0 /* timeout無効: shouldStop で手動停止 */, false);
            self.postMessage({ type: 'done' });
        } catch (e) {
            const err = e instanceof YuiError
                ? { line: e.lineno, message: e.messages.join(' ') }
                : { message: String(e) };
            self.postMessage({ type: 'error', error: err });
        }
    } else if (data.type === 'stop') {
        if (rt) rt.shouldStop = true;
    }
};
```

---

## ファイル構成

```
yuijs/
├── src/
│   ├── index.js        # public API（Yui クラス + 全エクスポート）
│   ├── yuiast.js       # AST ノード定義
│   ├── yuitypes.js     # YuiValue, YuiType, YuiError, OPERATORS
│   ├── yuisyntax.js    # YuiSyntax, loadSyntax（構文 JSON の読み込み）
│   ├── yuiparser.js    # YuiParser（ソース → AST）
│   ├── yuistdlib.js    # 標準ライブラリ関数（和, 積, 最大値 など）
│   ├── yuiruntime.js   # YuiRuntime（AST → 実行）
│   ├── yuicoding.js    # CodingVisitor（AST → ソース文字列）
│   └── yuiexample.js   # YuiExample + サンプル生成関数
├── syntax/
│   ├── yui.json        # 日本語構文定義
│   ├── pylike.json     # Python 風構文定義
│   └── ...             # その他の構文定義
└── test/
    ├── test_types.js   # 型システムのテスト（46）
    ├── test_runtime.js # ランタイムのテスト（33）
    ├── test_coding.js  # コード生成のテスト（11）
    └── test_example.js # サンプルのテスト（22）
```
