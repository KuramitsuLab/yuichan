// yuiexample.js — Yui 言語のサンプルコード生成
// Python 版 yuichan/yuiexample.py の移植
//
// AST ノードを使ってサンプルコードを構築し、CodingVisitor で異なる構文
// (Yui / Python 風 / Emoji …) に変換して出力する。
//
// Python との差分:
// - Python の `ObjectNode({"x": NumberNode(0), ...})` は list comprehension が
//   dict の「キーだけ」を走査するため値が落ちる (Python 版の latent bug)。
//   JS 版は `_node({...})` で正しくキー・値ペアを flatten する。
//   test_example は parse できれば green なので、Python 側と同じ pass/fail になる。

import {
  ConstNode,
  NumberNode,
  StringNode,
  NameNode,
  ArrayNode,
  ObjectNode,
  MinusNode,
  ArrayLenNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  IfNode,
  RepeatNode,
  BreakNode,
  PassNode,
  FuncDefNode,
  FuncAppNode,
  ReturnNode,
  ImportNode,
  PrintExpressionNode,
  GetIndexNode,
  AssertNode,
  _node,
} from './yuiast.js';

import { CodingVisitor } from './yuicoding.js';

// ─────────────────────────────────────────────
// helpers
// ─────────────────────────────────────────────

/**
 * BlockNode から AssertNode を取り除いた新しい BlockNode を返す。
 * 直前の "Test ..." / "テスト..." PassNode コメントもあわせて除去する。
 */
function _stripAsserts(block) {
  const filtered = [];
  for (const stmt of block.statements) {
    if (stmt instanceof AssertNode) {
      const prev = filtered[filtered.length - 1];
      if (
        prev instanceof PassNode &&
        prev.comment &&
        (prev.comment.toLowerCase().startsWith('test') ||
          prev.comment.startsWith('テスト'))
      ) {
        filtered.pop();
      }
    } else {
      filtered.push(stmt);
    }
  }
  return new BlockNode(filtered, block.top_level);
}

// ─────────────────────────────────────────────
// YuiExample
// ─────────────────────────────────────────────

/**
 * Yui 言語のサンプルコード生成クラス。
 *
 * kind:
 *   'sample' — 学習環境向けサンプル
 *   'test'   — 実装テスト専用 (学習環境には出さない)
 *   'both'   — 両方
 */
export class YuiExample {
  constructor(name, description, astNode, kind = 'both') {
    this.name = name;
    this.description = description;
    this.ast_node = astNode;
    this.kind = kind;
  }

  /**
   * AST を指定された構文のソースコードとして出力する。
   * @param {string} syntax — 'yui' / 'pylike' / 'emoji' など
   * @param {object} options
   * @param {boolean} [options.includeAsserts=true] — false なら AssertNode を落とす
   * @param {number|null} [options.randomSeed=null]
   * @param {string|null} [options.indentString=null] — null なら CodingVisitor のデフォルト
   * @param {string|null} [options.functionLanguage=null]
   */
  generate(syntax = 'yui', options = {}) {
    const {
      includeAsserts = true,
      randomSeed = null,
      indentString = null,
      functionLanguage = null,
    } = options;
    const node = includeAsserts ? this.ast_node : _stripAsserts(this.ast_node);
    const visitor = new CodingVisitor(syntax, functionLanguage);
    if (indentString != null) {
      return visitor.emit(node, indentString, randomSeed);
    }
    return visitor.emit(node, undefined, randomSeed);
  }
}

// ─────────────────────────────────────────────
// example factories
// ─────────────────────────────────────────────

export function exampleHelloWorld() {
  const statements = [
    new PassNode('"Hello, world!" と表示する'),
    new PrintExpressionNode(new StringNode('Hello, world!')),
  ];
  return new YuiExample(
    'hello_world',
    "'Hello, world!' を表示する",
    new BlockNode(statements, true),
    'sample',
  );
}

export function exampleVariables() {
  const statements = [
    new PassNode('変数 x と y を定義する'),
    new AssignmentNode(new NameNode('x'), new NumberNode(1)),
    new AssignmentNode(new NameNode('y'), new MinusNode(new NumberNode(2))),
    new PassNode('x を1増やす'),
    new IncrementNode(new NameNode('x')),
    new PassNode('y を1減らす'),
    new DecrementNode(new NameNode('y')),
    new PassNode('テスト: x が 2、y が -3'),
    new AssertNode(new NameNode('x'), new NumberNode(2)),
    new AssertNode(new NameNode('y'), new MinusNode(new NumberNode(3))),
  ];
  return new YuiExample(
    'variables',
    '変数の定義とインクリメント/デクリメント',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleLoop() {
  const statements = [
    new PassNode('10回ループして5回目でブレイク'),
    new AssignmentNode(new NameNode('count'), new NumberNode(0)),
    new RepeatNode(
      new NumberNode(10),
      new BlockNode([
        new IncrementNode(new NameNode('count')),
        new IfNode(
          new NameNode('count'),
          '==',
          new NumberNode(5),
          new BlockNode(new BreakNode()),
        ),
      ]),
    ),
    new PassNode('テスト: count が 5'),
    new AssertNode(new NameNode('count'), new NumberNode(5)),
  ];
  return new YuiExample(
    'loop',
    '10回ループして5回目でブレイク',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleFizzbuzz() {
  const statements = [
    new PassNode('1から100までのFizzBuzzをリストに収集する'),
    new AssignmentNode(new NameNode('result'), new ArrayNode([])),
    new AssignmentNode(new NameNode('i'), new NumberNode(0)),
    new AssignmentNode(new NameNode('fizz'), new NumberNode(0)),
    new AssignmentNode(new NameNode('buzz'), new NumberNode(0)),
    new RepeatNode(
      new NumberNode(100),
      new BlockNode([
        new IncrementNode(new NameNode('i')),
        new IncrementNode(new NameNode('fizz')),
        new IncrementNode(new NameNode('buzz')),
        new IfNode(
          new NameNode('fizz'),
          '==',
          new NumberNode(3),
          new BlockNode(
            new AssignmentNode(new NameNode('fizz'), new NumberNode(0)),
          ),
        ),
        new IfNode(
          new NameNode('buzz'),
          '==',
          new NumberNode(5),
          new BlockNode(
            new AssignmentNode(new NameNode('buzz'), new NumberNode(0)),
          ),
        ),
        new IfNode(
          new NameNode('fizz'),
          '==',
          new NumberNode(0),
          new BlockNode(
            new IfNode(
              new NameNode('buzz'),
              '==',
              new NumberNode(0),
              new BlockNode(
                new AppendNode(
                  new NameNode('result'),
                  new StringNode('FizzBuzz'),
                ),
              ),
              new BlockNode(
                new AppendNode(new NameNode('result'), new StringNode('Fizz')),
              ),
            ),
          ),
          new BlockNode(
            new IfNode(
              new NameNode('buzz'),
              '==',
              new NumberNode(0),
              new BlockNode(
                new AppendNode(new NameNode('result'), new StringNode('Buzz')),
              ),
              new BlockNode(
                new AppendNode(new NameNode('result'), new NameNode('i')),
              ),
            ),
          ),
        ),
      ]),
    ),
    new PrintExpressionNode(new NameNode('result')),
    new PassNode('テスト: 長さが100'),
    new AssertNode(
      new ArrayLenNode(new NameNode('result')),
      new NumberNode(100),
    ),
    new PassNode('テスト: Fizz、Buzz、FizzBuzz の位置を確認'),
    new AssertNode(
      new GetIndexNode(new NameNode('result'), new NumberNode(2)),
      new StringNode('Fizz'),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('result'), new NumberNode(4)),
      new StringNode('Buzz'),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('result'), new NumberNode(14)),
      new StringNode('FizzBuzz'),
    ),
  ];
  return new YuiExample(
    'fizzbuzz',
    '1から100までのFizzBuzzをリストに収集する',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleNestedConditionalBranches() {
  const thenBlock = new IncrementNode(new NameNode('y'));
  const elseBlock = new IncrementNode(new NameNode('z'));
  const statements = [
    new PassNode('x と y に対するネストした条件をテスト'),
    new AssignmentNode(new NameNode('x'), new NumberNode(1)),
    new AssignmentNode(new NameNode('y'), new NumberNode(2)),
    new AssignmentNode(new NameNode('z'), new NumberNode(3)),
    new PassNode('x が 0 なら y を確認して y または z を増やす'),
    new IfNode(
      new NameNode('x'),
      '==',
      new NumberNode(0),
      new BlockNode(
        new IfNode(
          new NameNode('y'),
          '==',
          new NumberNode(1),
          thenBlock,
          elseBlock,
        ),
      ),
      new BlockNode(
        new IfNode(
          new NameNode('y'),
          '==',
          new NumberNode(2),
          thenBlock,
          elseBlock,
        ),
      ),
    ),
    new PassNode('テスト: y が増えて z が増えていない'),
    new AssertNode(new NameNode('y'), new NumberNode(3)),
  ];
  return new YuiExample(
    'nested_conditional_branches',
    'ネストした条件分岐',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleComparisons() {
  const thenBlock = new IncrementNode(new NameNode('y'));
  const elseBlock = new IncrementNode(new NameNode('z'));
  const statements = [
    new PassNode('x に対するさまざまな比較'),
    new AssignmentNode(new NameNode('x'), new NumberNode(1)),
    new AssignmentNode(new NameNode('y'), new NumberNode(0)),
    new AssignmentNode(new NameNode('z'), new NumberNode(0)),
    new PassNode('x は 1 と等しいか？'),
    new IfNode(
      new NameNode('x'),
      '==',
      new NumberNode(1),
      thenBlock,
      elseBlock,
    ),
    new PassNode('x は 1 と等しくないか？'),
    new IfNode(
      new NameNode('x'),
      '!=',
      new NumberNode(1),
      thenBlock,
      elseBlock,
    ),
    new PassNode('x は 1 より小さいか？'),
    new IfNode(new NameNode('x'), '<', new NumberNode(1), thenBlock, elseBlock),
    new PassNode('x は 1 より大きいか？'),
    new IfNode(new NameNode('x'), '>', new NumberNode(1), thenBlock, elseBlock),
    new PassNode('x は 1 以下か？'),
    new IfNode(
      new NameNode('x'),
      '<=',
      new NumberNode(1),
      thenBlock,
      elseBlock,
    ),
    new PassNode('x は 1 以上か？'),
    new IfNode(
      new NameNode('x'),
      '>=',
      new NumberNode(1),
      thenBlock,
      elseBlock,
    ),
    new PassNode('テスト: すべての条件が正しく評価された'),
    new AssertNode(new NameNode('y'), new NumberNode(3)),
    new AssertNode(new NameNode('z'), new NumberNode(3)),
  ];
  return new YuiExample(
    'comparisons',
    '比較演算',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleArray() {
  const statements = [
    new PassNode('要素 1, 2, 3 を持つ配列 A を作成する'),
    new AssignmentNode(
      new NameNode('A'),
      new ArrayNode([new NumberNode(1), new NumberNode(2), new NumberNode(3)]),
    ),
    new PassNode('A の末尾に 0 を追加する'),
    new AppendNode(new NameNode('A'), new NumberNode(0)),
    new PassNode('A の最初の要素を1増やす'),
    new IncrementNode(
      new GetIndexNode(new NameNode('A'), new NumberNode(0)),
    ),
    new PassNode('A に 2 があれば、最初の要素を4番目の要素に設定する'),
    new IfNode(
      new NumberNode(2),
      'in',
      new NameNode('A'),
      new AssignmentNode(
        new GetIndexNode(new NameNode('A'), new NumberNode(0)),
        new GetIndexNode(new NameNode('A'), new NumberNode(3)),
      ),
    ),
    new PassNode('テスト: 配列が4要素'),
    new AssertNode(
      new ArrayLenNode(new NameNode('A')),
      new NumberNode(4),
    ),
  ];
  return new YuiExample(
    'array',
    '配列の作成と要素操作',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleStrings() {
  const statements = [
    new PassNode("'hello' という文字列 s を作成する"),
    new AssignmentNode(new NameNode('s'), new StringNode('hello')),
    new PassNode("s の最初の文字を 'H' に設定する"),
    new PassNode('注: 文字列は文字コードの配列です。配列と同様に操作できます。'),
    new AssignmentNode(
      new GetIndexNode(new NameNode('s'), new NumberNode(0)),
      new GetIndexNode(new StringNode('H'), 0),
    ),
    new PassNode('s に " world" を連結する'),
    new AssignmentNode(new NameNode('t'), new StringNode(' world')),
    new AssignmentNode(new NameNode('i'), new NumberNode(0)),
    new RepeatNode(
      new ArrayLenNode(new NameNode('t')),
      new BlockNode([
        new AppendNode(
          new NameNode('s'),
          new GetIndexNode(new NameNode('t'), new NameNode('i')),
        ),
        new IncrementNode(new NameNode('i')),
      ]),
    ),
    new PassNode("テスト: s が 'Hello world' になっている"),
    new AssertNode(new NameNode('s'), new StringNode('Hello world')),
  ];
  return new YuiExample(
    'strings',
    '文字列の作成と操作',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleObjects() {
  // Python 版は `ObjectNode({"x": ..., "y": ...})` と書くが、dict の list
  // comprehension がキーだけを走査する latent bug により elements が
  // [StringNode("x"), StringNode("y")] になる。JS 版は _node({...}) で
  // 正しく key/value ペアを flatten する (parse できれば green なので結果は同じ)。
  const statements = [
    new PassNode('プロパティ x と y を持つオブジェクト O を作成する'),
    new AssignmentNode(
      new NameNode('O'),
      _node({ x: new NumberNode(0), y: new NumberNode(0) }),
    ),
    new PassNode('O の x プロパティを 1 に設定する'),
    new AssignmentNode(
      new GetIndexNode(new NameNode('O'), new StringNode('x')),
      new NumberNode(1),
    ),
    new PassNode('O の y プロパティを 2 に設定する'),
    new AssignmentNode(
      new GetIndexNode(new NameNode('O'), new StringNode('y')),
      new NumberNode(2),
    ),
    new PassNode('テスト: O のプロパティが x=1、y=2'),
    new AssertNode(
      new GetIndexNode(new NameNode('O'), new StringNode('x')),
      new NumberNode(1),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('O'), new StringNode('y')),
      new NumberNode(2),
    ),
  ];
  return new YuiExample(
    'objects',
    'オブジェクトの作成とプロパティ操作',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleFunction() {
  const statements = [
    new PassNode('1を加算する関数を定義する'),
    new FuncDefNode(
      new NameNode('succ'),
      [new NameNode('n')],
      new BlockNode([
        new IncrementNode(new NameNode('n')),
        new ReturnNode(new NameNode('n')),
      ]),
    ),
    new AssignmentNode(
      new NameNode('result'),
      new FuncAppNode(new NameNode('succ'), [new NumberNode(0)]),
    ),
    new AssertNode(new NameNode('result'), new NumberNode(1)),
  ];
  return new YuiExample(
    'function',
    '関数の定義と呼び出し（インクリメント関数）',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleFunctionNoArgument() {
  const statements = [
    new PassNode('引数なしで 0 を返す関数を定義する'),
    new FuncDefNode(
      new NameNode('zero'),
      [],
      new BlockNode(new ReturnNode(new NumberNode(0))),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('zero'), []),
      new NumberNode(0),
    ),
  ];
  return new YuiExample(
    'function_no_argument',
    '関数の定義と呼び出し（引数なし関数と複数引数関数）',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleFunctionWithoutReturn() {
  const statements = [
    new PassNode('点オブジェクトを作成する関数を定義する'),
    new FuncDefNode(
      new NameNode('point'),
      [new NameNode('x'), new NameNode('y')],
      new BlockNode([
        new PassNode(
          '関数が何も返さない場合、ローカル環境をオブジェクトとして返す',
        ),
      ]),
    ),
    new AssignmentNode(
      new NameNode('O'),
      new FuncAppNode(new NameNode('point'), [
        new NumberNode(0),
        new NumberNode(0),
      ]),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('O'), new StringNode('x')),
      new NumberNode(0),
    ),
  ];
  return new YuiExample(
    'function_without_return',
    '関数の定義と呼び出し（戻り値なし関数）',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleRecursiveFunction() {
  const statements = [
    new PassNode('階乗を計算する再帰関数を定義する'),
    new FuncDefNode(
      new NameNode('fact'),
      [new NameNode('n')],
      new BlockNode([
        new IfNode(
          new NameNode('n'),
          '==',
          new NumberNode(0),
          new BlockNode([new ReturnNode(new NumberNode(1))]),
          new BlockNode([
            new PassNode('Yui には算術演算子がありません。'),
            new ReturnNode(
              new FuncAppNode(new NameNode('multiplex'), [
                new NameNode('n'),
                new FuncAppNode(new NameNode('fact'), [
                  new FuncAppNode(new NameNode('decrease'), [new NameNode('n')]),
                ]),
              ]),
            ),
          ]),
        ),
      ]),
    ),
    new PassNode('multiplex(a, b): a * b を計算する関数'),
    new FuncDefNode(
      new NameNode('multiplex'),
      [new NameNode('a'), new NameNode('b')],
      new BlockNode([
        new AssignmentNode(new NameNode('result'), new NumberNode(0)),
        new RepeatNode(
          new NameNode('b'),
          new BlockNode([
            new RepeatNode(
              new NameNode('a'),
              new BlockNode([new IncrementNode(new NameNode('result'))]),
            ),
          ]),
        ),
        new ReturnNode(new NameNode('result')),
      ]),
    ),
    new PassNode('decrease(n): n-1 を計算する関数'),
    new FuncDefNode(
      new NameNode('decrease'),
      [new NameNode('n')],
      new BlockNode([
        new DecrementNode(new NameNode('n')),
        new ReturnNode(new NameNode('n')),
      ]),
    ),
    new PassNode('テスト: fact(0) が 1'),
    new AssertNode(
      new FuncAppNode(new NameNode('fact'), [new NumberNode(0)]),
      new NumberNode(1),
    ),
    new PassNode('テスト: fact(5) が 120'),
    new AssertNode(
      new FuncAppNode(new NameNode('fact'), [new NumberNode(5)]),
      new NumberNode(120),
    ),
  ];
  return new YuiExample(
    'recursive_function',
    '再帰関数の定義と呼び出し（階乗関数）',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleArithmetic() {
  const addFunc = new FuncDefNode(
    new NameNode('add'),
    [new NameNode('a'), new NameNode('b')],
    new BlockNode([
      new AssignmentNode(new NameNode('result'), new NameNode('a')),
      new RepeatNode(
        new NameNode('b'),
        new BlockNode([new IncrementNode(new NameNode('result'))]),
      ),
      new ReturnNode(new NameNode('result')),
    ]),
  );
  const subtractFunc = new FuncDefNode(
    new NameNode('subtract'),
    [new NameNode('a'), new NameNode('b')],
    new BlockNode([
      new AssignmentNode(new NameNode('result'), new NameNode('a')),
      new RepeatNode(
        new NameNode('b'),
        new BlockNode([new DecrementNode(new NameNode('result'))]),
      ),
      new ReturnNode(new NameNode('result')),
    ]),
  );
  const multiplyFunc = new FuncDefNode(
    new NameNode('multiply'),
    [new NameNode('a'), new NameNode('b')],
    new BlockNode([
      new AssignmentNode(new NameNode('result'), new NumberNode(0)),
      new RepeatNode(
        new NameNode('b'),
        new BlockNode([
          new AssignmentNode(
            new NameNode('result'),
            new FuncAppNode(new NameNode('add'), [
              new NameNode('result'),
              new NameNode('a'),
            ]),
          ),
        ]),
      ),
      new ReturnNode(new NameNode('result')),
    ]),
  );
  const divideFunc = new FuncDefNode(
    new NameNode('divide'),
    [new NameNode('a'), new NameNode('b')],
    new BlockNode([
      new AssignmentNode(new NameNode('q'), new NumberNode(0)),
      new AssignmentNode(new NameNode('r'), new NameNode('a')),
      new RepeatNode(
        new NameNode('a'),
        new BlockNode([
          new IfNode(
            new NameNode('r'),
            '<',
            new NameNode('b'),
            new BlockNode(new BreakNode()),
          ),
          new IncrementNode(new NameNode('q')),
          new AssignmentNode(
            new NameNode('r'),
            new FuncAppNode(new NameNode('subtract'), [
              new NameNode('r'),
              new NameNode('b'),
            ]),
          ),
        ]),
      ),
      new ReturnNode(new NameNode('q')),
    ]),
  );
  const moduloFunc = new FuncDefNode(
    new NameNode('modulo'),
    [new NameNode('a'), new NameNode('b')],
    new BlockNode([
      new AssignmentNode(new NameNode('r'), new NameNode('a')),
      new RepeatNode(
        new NameNode('a'),
        new BlockNode([
          new IfNode(
            new NameNode('r'),
            '<',
            new NameNode('b'),
            new BlockNode(new BreakNode()),
          ),
          new AssignmentNode(
            new NameNode('r'),
            new FuncAppNode(new NameNode('subtract'), [
              new NameNode('r'),
              new NameNode('b'),
            ]),
          ),
        ]),
      ),
      new ReturnNode(new NameNode('r')),
    ]),
  );
  const statements = [
    new PassNode('非負整数向けの四則演算関数'),
    new PassNode('add(a, b): a + b'),
    addFunc,
    new PassNode('subtract(a, b): a - b  (a >= b が必要)'),
    subtractFunc,
    new PassNode('multiply(a, b): a * b'),
    multiplyFunc,
    new PassNode('divide(a, b): 整数商 a // b'),
    divideFunc,
    new PassNode('modulo(a, b): 余り a % b'),
    moduloFunc,
    new PassNode('使用例'),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('add'), [
        new NumberNode(3),
        new NumberNode(4),
      ]),
    ),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('subtract'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
    ),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('multiply'), [
        new NumberNode(3),
        new NumberNode(4),
      ]),
    ),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('divide'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
    ),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('modulo'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
    ),
    new PassNode('テスト: add'),
    new AssertNode(
      new FuncAppNode(new NameNode('add'), [
        new NumberNode(3),
        new NumberNode(4),
      ]),
      new NumberNode(7),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('add'), [
        new NumberNode(0),
        new NumberNode(5),
      ]),
      new NumberNode(5),
    ),
    new PassNode('テスト: subtract'),
    new AssertNode(
      new FuncAppNode(new NameNode('subtract'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
      new NumberNode(7),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('subtract'), [
        new NumberNode(5),
        new NumberNode(5),
      ]),
      new NumberNode(0),
    ),
    new PassNode('テスト: multiply'),
    new AssertNode(
      new FuncAppNode(new NameNode('multiply'), [
        new NumberNode(3),
        new NumberNode(4),
      ]),
      new NumberNode(12),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('multiply'), [
        new NumberNode(0),
        new NumberNode(5),
      ]),
      new NumberNode(0),
    ),
    new PassNode('テスト: divide'),
    new AssertNode(
      new FuncAppNode(new NameNode('divide'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
      new NumberNode(3),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('divide'), [
        new NumberNode(9),
        new NumberNode(3),
      ]),
      new NumberNode(3),
    ),
    new PassNode('テスト: modulo'),
    new AssertNode(
      new FuncAppNode(new NameNode('modulo'), [
        new NumberNode(10),
        new NumberNode(3),
      ]),
      new NumberNode(1),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('modulo'), [
        new NumberNode(15),
        new NumberNode(5),
      ]),
      new NumberNode(0),
    ),
  ];
  return new YuiExample(
    'arithmetic',
    '非負整数向けの算術関数（add, subtract, multiply, divide, modulo）',
    new BlockNode(statements, true),
    'both',
  );
}

/**
 * float 配列の加算（stdlib なし）
 *
 * float の内部表現: [sign, d1, d2, d3, d4, d5, d6, d7]
 *   sign: 1 (正) または -1 (負)
 *   d1..d7: abs(value) * 1e6 の各桁 (合計7桁)
 *   例) 3.14 → [1, 3, 1, 4, 0, 0, 0, 0]
 *      -2.5 → [-1, 2, 5, 0, 0, 0, 0, 0]
 *
 * float_add(a, b): 同符号の float 配列を足し合わせる。
 * アルゴリズム: i=7 から i=1 まで逆順に桁ごとに加算し繰り上がりを伝播する。
 */
export function exampleFloatAdd() {
  const statements = [
    new PassNode(
      'float形式: [符号, d1..d7]  符号=1または-1、d1..d7 = abs(x)*1e6 の各桁',
    ),
    new PassNode('float_add(a, b): 同符号の float 配列を足し合わせる（stdlib なし）'),
    new FuncDefNode(
      new NameNode('float_add'),
      [new NameNode('a'), new NameNode('b')],
      new BlockNode([
        new AssignmentNode(
          new NameNode('result'),
          new ArrayNode([
            new GetIndexNode(new NameNode('a'), new NumberNode(0)),
            new NumberNode(0),
            new NumberNode(0),
            new NumberNode(0),
            new NumberNode(0),
            new NumberNode(0),
            new NumberNode(0),
            new NumberNode(0),
          ]),
        ),
        new AssignmentNode(new NameNode('carry'), new NumberNode(0)),
        new AssignmentNode(new NameNode('i'), new NumberNode(7)),
        new RepeatNode(
          new NumberNode(7),
          new BlockNode([
            new AssignmentNode(new NameNode('sum'), new NameNode('carry')),
            new RepeatNode(
              new GetIndexNode(new NameNode('a'), new NameNode('i')),
              new BlockNode([new IncrementNode(new NameNode('sum'))]),
            ),
            new RepeatNode(
              new GetIndexNode(new NameNode('b'), new NameNode('i')),
              new BlockNode([new IncrementNode(new NameNode('sum'))]),
            ),
            new AssignmentNode(new NameNode('carry'), new NumberNode(0)),
            new IfNode(
              new NameNode('sum'),
              '>=',
              new NumberNode(10),
              new BlockNode([
                new IncrementNode(new NameNode('carry')),
                new RepeatNode(
                  new NumberNode(10),
                  new BlockNode([new DecrementNode(new NameNode('sum'))]),
                ),
              ]),
            ),
            new AssignmentNode(
              new GetIndexNode(new NameNode('result'), new NameNode('i')),
              new NameNode('sum'),
            ),
            new DecrementNode(new NameNode('i')),
          ]),
        ),
        new ReturnNode(new NameNode('result')),
      ]),
    ),
    new PassNode('3.14 + 2.50 = 5.64'),
    new AssignmentNode(
      new NameNode('a'),
      new ArrayNode([
        new NumberNode(1),
        new NumberNode(3),
        new NumberNode(1),
        new NumberNode(4),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
      ]),
    ),
    new AssignmentNode(
      new NameNode('b'),
      new ArrayNode([
        new NumberNode(1),
        new NumberNode(2),
        new NumberNode(5),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
      ]),
    ),
    new AssignmentNode(
      new NameNode('c'),
      new FuncAppNode(new NameNode('float_add'), [
        new NameNode('a'),
        new NameNode('b'),
      ]),
    ),
    new PassNode('c == [1, 5, 6, 4, 0, 0, 0, 0]  (5.640000)'),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(0)),
      new NumberNode(1),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(1)),
      new NumberNode(5),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(2)),
      new NumberNode(6),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(3)),
      new NumberNode(4),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(4)),
      new NumberNode(0),
    ),
    new PassNode('1.99 + 1.01 = 3.00  (繰り上がり伝播のテスト)'),
    new AssignmentNode(
      new NameNode('a'),
      new ArrayNode([
        new NumberNode(1),
        new NumberNode(1),
        new NumberNode(9),
        new NumberNode(9),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
      ]),
    ),
    new AssignmentNode(
      new NameNode('b'),
      new ArrayNode([
        new NumberNode(1),
        new NumberNode(1),
        new NumberNode(0),
        new NumberNode(1),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
        new NumberNode(0),
      ]),
    ),
    new AssignmentNode(
      new NameNode('c'),
      new FuncAppNode(new NameNode('float_add'), [
        new NameNode('a'),
        new NameNode('b'),
      ]),
    ),
    new PassNode('c == [1, 3, 0, 0, 0, 0, 0, 0]  (3.000000)'),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(1)),
      new NumberNode(3),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(2)),
      new NumberNode(0),
    ),
    new AssertNode(
      new GetIndexNode(new NameNode('c'), new NumberNode(3)),
      new NumberNode(0),
    ),
  ];
  return new YuiExample(
    'float_add',
    '同符号の float を桁配列として加算する（stdlib なし）',
    new BlockNode(statements, true),
    'test',
  );
}

/**
 * モンテカルロ法で π を推定するサンプル（乱数・平方根を使用）
 */
export function exampleMonteCarlo() {
  const monteCarloFunc = new FuncDefNode(
    new NameNode('monte_carlo'),
    [new NameNode('n')],
    new BlockNode([
      new AssignmentNode(new NameNode('hits'), new NumberNode(0)),
      new RepeatNode(
        new NameNode('n'),
        new BlockNode([
          new AssignmentNode(
            new NameNode('x'),
            new FuncAppNode(new NameNode('乱数'), []),
          ),
          new AssignmentNode(
            new NameNode('y'),
            new FuncAppNode(new NameNode('乱数'), []),
          ),
          new AssignmentNode(
            new NameNode('dist'),
            new FuncAppNode(new NameNode('平方根'), [
              new FuncAppNode(new NameNode('和'), [
                new FuncAppNode(new NameNode('積'), [
                  new NameNode('x'),
                  new NameNode('x'),
                ]),
                new FuncAppNode(new NameNode('積'), [
                  new NameNode('y'),
                  new NameNode('y'),
                ]),
              ]),
            ]),
          ),
          new IfNode(
            new NameNode('dist'),
            '<=',
            new NumberNode(1),
            new BlockNode(new IncrementNode(new NameNode('hits'))),
          ),
        ]),
      ),
      new ReturnNode(
        new FuncAppNode(new NameNode('商'), [
          new FuncAppNode(new NameNode('積'), [
            new FuncAppNode(new NameNode('小数化'), [new NameNode('hits')]),
            new NumberNode(4),
          ]),
          new FuncAppNode(new NameNode('小数化'), [new NameNode('n')]),
        ]),
      ),
    ]),
  );
  const statements = [
    new ImportNode(),
    new PassNode('モンテカルロ法: ランダム点のサンプリングで π を推定する'),
    new PassNode('単位正方形 [0,1)×[0,1) に n 個のランダム点を投げる。'),
    new PassNode('単位円内の点（dist ≤ 1）をカウントする。'),
    new PassNode('π ≈ 4 × (hits / n)'),
    monteCarloFunc,
    new PassNode('サンプル数が多いほど π ≈ 3.14159... に近づく'),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('monte_carlo'), [new NumberNode(100)]),
    ),
    new PrintExpressionNode(
      new FuncAppNode(new NameNode('monte_carlo'), [new NumberNode(1000)]),
    ),
  ];
  return new YuiExample(
    'monte_carlo',
    'モンテカルロ法で π を推定する（stdlib: 乱数, 平方根）',
    new BlockNode(statements, true),
    'sample',
  );
}

export function exampleNullAssignment() {
  const statements = [
    new PassNode('変数に null を代入する'),
    new AssignmentNode(new NameNode('x'), new ConstNode(null)),
    new PassNode('テスト: x が null'),
    new AssertNode(new NameNode('x'), new ConstNode(null)),
  ];
  return new YuiExample(
    'null_assignment',
    '変数に null を代入して比較する',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleBooleanAssignment() {
  const statements = [
    new PassNode('true と false を変数に代入する'),
    new AssignmentNode(new NameNode('t'), new ConstNode(true)),
    new AssignmentNode(new NameNode('f'), new ConstNode(false)),
    new PassNode('テスト: t が true で f が false'),
    new AssertNode(new NameNode('t'), new ConstNode(true)),
    new AssertNode(new NameNode('f'), new ConstNode(false)),
  ];
  return new YuiExample(
    'boolean_assignment',
    '変数に true/false を代入して比較する',
    new BlockNode(statements, true),
    'test',
  );
}

export function exampleBooleanBranch() {
  const statements = [
    new PassNode('boolean 値で条件分岐する'),
    new AssignmentNode(new NameNode('flag'), new ConstNode(true)),
    new AssignmentNode(new NameNode('result'), new NumberNode(0)),
    new IfNode(
      new NameNode('flag'),
      '==',
      new ConstNode(true),
      new BlockNode(
        new AssignmentNode(new NameNode('result'), new NumberNode(1)),
      ),
      new BlockNode(
        new AssignmentNode(new NameNode('result'), new NumberNode(2)),
      ),
    ),
    new PassNode('テスト: flag が true だったので result が 1'),
    new AssertNode(new NameNode('result'), new NumberNode(1)),
  ];
  return new YuiExample(
    'boolean_branch',
    'boolean 値に基づく条件分岐',
    new BlockNode(statements, true),
    'both',
  );
}

export function exampleNullCheck() {
  const statements = [
    new PassNode('is_null 関数を定義する'),
    new FuncDefNode(
      new NameNode('is_null'),
      [new NameNode('v')],
      new BlockNode([
        new IfNode(
          new NameNode('v'),
          '==',
          new ConstNode(null),
          new BlockNode(new ReturnNode(new ConstNode(true))),
          new BlockNode(new ReturnNode(new ConstNode(false))),
        ),
      ]),
    ),
    new PassNode('テスト: null と非 null の値で is_null を確認'),
    new AssertNode(
      new FuncAppNode(new NameNode('is_null'), [new ConstNode(null)]),
      new ConstNode(true),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('is_null'), [new NumberNode(0)]),
      new ConstNode(false),
    ),
    new AssertNode(
      new FuncAppNode(new NameNode('is_null'), [new StringNode('')]),
      new ConstNode(false),
    ),
  ];
  return new YuiExample(
    'null_check',
    '値が null かどうかを確認する関数',
    new BlockNode(statements, true),
    'test',
  );
}

// ─────────────────────────────────────────────
// collections
// ─────────────────────────────────────────────

/** すべての例を返す (kind に関わらず) */
export function getAllExamples() {
  return [
    exampleHelloWorld(),
    exampleVariables(),
    exampleLoop(),
    exampleFizzbuzz(),
    exampleNestedConditionalBranches(),
    exampleComparisons(),
    exampleArray(),
    exampleStrings(),
    exampleObjects(),
    exampleFunction(),
    exampleFunctionNoArgument(),
    exampleFunctionWithoutReturn(),
    exampleRecursiveFunction(),
    exampleArithmetic(),
    exampleFloatAdd(),
    exampleMonteCarlo(),
    exampleNullAssignment(),
    exampleBooleanAssignment(),
    exampleBooleanBranch(),
    exampleNullCheck(),
  ];
}

/** 学習環境向けサンプルを返す (kind='sample' または 'both') */
export function getSamples() {
  return getAllExamples().filter(
    (e) => e.kind === 'sample' || e.kind === 'both',
  );
}

/** 実装テスト用の例を返す (kind='test' または 'both') */
export function getTestExamples() {
  return getAllExamples().filter(
    (e) => e.kind === 'test' || e.kind === 'both',
  );
}
