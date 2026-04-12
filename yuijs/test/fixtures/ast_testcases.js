// test/fixtures/ast_testcases.js
// Python 版 yuichan/test_ast.py の `testcases` 辞書を JS に移植したフィクスチャ。
//
// 目的:
//   - 各 syntax (yui / pylike / jslike / ...) の roundtrip テストで共通利用
//   - 将来的に yuiast.test.js の evaluate() レイヤーからも再利用
//
// 各エントリは `[name, node, expected]` の形式で格納する (Python の dict と同じ順序)。
// `expected` は以下のいずれか:
//   - プリミティブ (number/string/boolean/null) や配列/オブジェクト — result 値と deep 比較
//   - env(name, value) — 実行後に環境変数 `name` が `value` と等しいか検査
//   - "💣xxx" で始まる文字列 — YuiError を期待し、`messages[0] === xxx` を検査
//
// 共通ヘルパ `initRuntime()` は Python 版 `init_runtime()` と同じく
// 事前バインドされた変数 (a, x, s, A, P, M) を持つランタイムを返す。

import {
  ConstNode,
  NumberNode,
  StringNode,
  ArrayNode,
  ObjectNode,
  NameNode,
  MinusNode,
  ArrayLenNode,
  GetIndexNode,
  BinaryNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  IfNode,
  RepeatNode,
  BreakNode,
  FuncDefNode,
  FuncAppNode,
  ReturnNode,
  AssertNode,
} from '../../src/yuiast.js';
import { YuiValue } from '../../src/yuitypes.js';
import { YuiRuntime } from '../../src/yuiruntime.js';

// env マーカー: 「実行後に環境変数 `name` が `value` と等しいこと」を検査するためのセンチネル。
const ENV = Symbol('env-check');
export function env(name, value) {
  return { [ENV]: true, name, value };
}
export function isEnvExpected(x) {
  return x != null && typeof x === 'object' && x[ENV] === true;
}

export function initRuntime() {
  const rt = new YuiRuntime();
  rt.setenv('a', new YuiValue(1));
  rt.setenv('x', new YuiValue(1.23));
  rt.setenv('s', new YuiValue('abc'));
  rt.setenv('A', new YuiValue([1, 2, 3]));
  rt.setenv('P', new YuiValue({ x: 1, y: 2, z: 3 }));
  rt.setenv('M', new YuiValue([[1, 2], [3, 4]]));
  rt.allow_binary_ops = true;
  return rt;
}

// Python: ord('a') / ord('b') / ord('c') / ord('d')
const ORD_A = 'a'.charCodeAt(0);
const ORD_B = 'b'.charCodeAt(0);
const ORD_C = 'c'.charCodeAt(0);
const ORD_D = 'd'.charCodeAt(0);

// 短縮ヘルパ
const N = (name) => new NameNode(name);
const Num = (v) => new NumberNode(v);
const Str = (c) => new StringNode(c);
const Arr = (els) => new ArrayNode(els);
const Obj = (els) => new ObjectNode(els);
const Const = (v) => new ConstNode(v);
const Idx = (col, i) => new GetIndexNode(col, i);
const Bin = (op, l, r) => new BinaryNode(op, l, r);
const If = (l, op, r, t, e) => new IfNode(l, op, r, t, e);
const Blk = (stmts) => new BlockNode(stmts);

export const astTestcases = [
  // ─── ConstNode ────────────────────────────────────────
  ['null',  Const(null),  null],
  ['true',  Const(true),  true],
  ['false', Const(false), false],

  // ─── NumberNode ───────────────────────────────────────
  ['int(42)',   Num(42),  42],
  ['float(3.5)', Num(3.5), 3.5],

  // ─── Variable ─────────────────────────────────────────
  ['a:int',      N('a'), 1],
  ['x:float',    N('x'), 1.23],
  ['undefined',  N('undefined'), '💣undefined-variable'],

  // ─── String ───────────────────────────────────────────
  ['""',          Str(''), ''],
  ['"A"',         Str('A'), 'A'],
  ['"A{a}B"',     Str(['A', N('a'), 'B']), 'A1B'],
  ['"{a}B"',      Str([N('a'), 'B']), '1B'],
  ['"A{a}"',      Str(['A', N('a')]), 'A1'],
  ['"A{a}{a}B"',  Str(['A', N('a'), N('a'), 'B']), 'A11B'],

  // ─── Array ────────────────────────────────────────────
  ['empty_array', Arr([]), []],
  ['array',       Arr([N('a'), Num(2), Num(3)]), [1, 2, 3]],

  // ─── Object ───────────────────────────────────────────
  ['object', Obj(['x', N('a'), 'y', Num(2), 'z', Num(3)]), { x: 1, y: 2, z: 3 }],

  // ─── MinusNode ────────────────────────────────────────
  ['minus/int',    new MinusNode(Num(16)),   -16],
  ['minus/float',  new MinusNode(Num(3.14)), -3.14],
  ['minus/string', new MinusNode(Str('A')),  '💣type-error'],

  // ─── ArrayLenNode ─────────────────────────────────────
  ['len(A)',      new ArrayLenNode(N('A')), 3],
  ['len(s)',      new ArrayLenNode(N('s')), 3],
  ['len(P)',      new ArrayLenNode(N('P')), 3],
  ['len(M)',      new ArrayLenNode(N('M')), 2],
  ['len(0)',      new ArrayLenNode(0), 0],
  ['len(11)',     new ArrayLenNode(11), 4],
  ['len(true)',   new ArrayLenNode(true), 1],
  ['len(false)',  new ArrayLenNode(false), 1],
  ['len(null)',   new ArrayLenNode(null), 0],
  ['len(103.14)', new ArrayLenNode(103.14), 9],
  ['len(0.01)',   new ArrayLenNode(0.01), 7],

  // ─── GetIndexNode ─────────────────────────────────────
  ['A[0]', Idx(N('A'), 0), 1],
  ['A[1]', Idx(N('A'), 1), 2],
  ['A[2]', Idx(N('A'), 2), 3],
  ['A[3]', Idx(N('A'), 3), '💣index-error'],
  ['s[0]', Idx(N('s'), 0), ORD_A],
  ['s[1]', Idx(N('s'), 1), ORD_B],
  ['s[2]', Idx(N('s'), 2), ORD_C],
  ['s[3]', Idx(N('s'), 3), '💣index-error'],
  ['P["x"]', Idx(N('P'), 'x'), 1],
  ['P["y"]', Idx(N('P'), 'y'), 2],
  ['P["z"]', Idx(N('P'), 'z'), 3],
  ['P["w"]', Idx(N('P'), 'w'), null],
  ['M[0][0]', Idx(Idx(N('M'), 0), 0), 1],
  ['M[0][1]', Idx(Idx(N('M'), 0), 1), 2],
  ['M[1][0]', Idx(Idx(N('M'), 1), 0), 3],
  ['M[1][1]', Idx(Idx(N('M'), 1), 1), 4],
  ['M[0]', Idx(N('M'), 0), [1, 2]],
  ['M[1]', Idx(N('M'), 1), [3, 4]],
  // 11 = [1, 1, 0, 1]
  ['11[0]', Idx(11, 0), 1],
  ['11[1]', Idx(11, 1), 1],
  ['11[2]', Idx(11, 2), 0],
  ['11[3]', Idx(11, 3), 1],
  // 3.14 = [0, 0, 0, 0, 4, 1, 3]
  ['3.14[0]', Idx(3.14, 0), 0],
  ['3.14[1]', Idx(3.14, 1), 0],
  ['3.14[2]', Idx(3.14, 2), 0],
  ['3.14[3]', Idx(3.14, 3), 0],
  ['3.14[4]', Idx(3.14, 4), 4],
  ['3.14[5]', Idx(3.14, 5), 1],
  ['3.14[6]', Idx(3.14, 6), 3],
  // true/false
  ['true[0]',  Idx(true, 0),  1],
  ['false[0]', Idx(false, 0), 0],
  // character
  ['"b"[0]', Idx('b', 0), ORD_B],

  // ─── Binary arithmetic ────────────────────────────────
  ['a+1', Bin('+', N('a'), 1), 2],
  ['a-1', Bin('-', N('a'), 1), 0],
  ['a*2', Bin('*', N('a'), 2), 2],
  ['7/2', Bin('/', 7, 2), 3],
  ['7%2', Bin('%', 7, 2), 1],
  ['7/a', Bin('/', 7, N('a')), 7],
  ['7%a', Bin('%', 7, N('a')), 0],

  // ─── Binary equality on literals / names ──────────────
  ['"a"==0', Bin('==', 'a', 0), false],
  ['"a"=="a"', Bin('==', 'a', 'a'), true],
  ['a==0', Bin('==', N('a'), 0), false],
  ['a==1', Bin('==', N('a'), 1), true],

  // ─── Complex arithmetic ───────────────────────────────
  ['1+2+3',   Bin('+', Bin('+', 1, 2), 3), 6],
  ['2*3*4',   Bin('*', Bin('*', 2, 3), 4), 24],
  ['1-2-3',   Bin('-', Bin('-', 1, 2), 3), -4],
  ['24/2/3',  Bin('/', Bin('/', 24, 2), 3), 4],
  ['3*2+4',   Bin('+', Bin('*', 3, 2), 4), 10],
  ['3*(2+4)', Bin('*', 3, Bin('+', 2, 4)), 18],
  ['a+3*2',   Bin('+', N('a'), Bin('*', 3, 2)), 7],
  ['(a+3)*2', Bin('*', Bin('+', N('a'), 3), 2), 8],

  // ─── Assignment ───────────────────────────────────────
  ['x=42', new AssignmentNode(N('x'), 42), env('x', 42)],
  ['y=0',  new AssignmentNode(N('y'), 0),  env('y', 0)],
  ['"s"="hello"', new AssignmentNode(Str('s'), 'hello'), '💣expected-variable'],

  // ─── 特殊変数名 ───────────────────────────────────────
  ['2times=100',       new AssignmentNode(N('2times'), 22),        env('2times', 22)],
  ['日本語変数名=100',  new AssignmentNode(N('日本語変数名'), 100), env('日本語変数名', 100)],
  ['あをによし=100',    new AssignmentNode(N('あをによし'), 100),   env('あをによし', 100)],
  ['🐼=100',           new AssignmentNode(N('🐼'), 100),           env('🐼', 100)],
  ['百=100',           new AssignmentNode(N('百'), 100),            env('百', 100)],

  // ─── Increment / Decrement ────────────────────────────
  ['a+=1', new IncrementNode(N('a')), env('a', 2)],
  ['a-=1', new DecrementNode(N('a')), env('a', 0)],
  ['s+=1', new IncrementNode(N('s')), '💣type-error'],
  ['s-=1', new DecrementNode(N('s')), '💣type-error'],
  ['"s"+=1', new IncrementNode(Str('s')), '💣expected-variable'],
  ['"s"-=1', new DecrementNode(Str('s')), '💣expected-variable'],
  ['undefined+=1', new IncrementNode(N('undefined')), '💣undefined-variable'],
  ['undefined-=1', new DecrementNode(N('undefined')), '💣undefined-variable'],
  ['A[0]+=1', new IncrementNode(Idx(N('A'), 0)), env('A', [2, 2, 3])],
  ['A[0]-=1', new DecrementNode(Idx(N('A'), 0)), env('A', [0, 2, 3])],
  ['P["x"]+=1', new IncrementNode(Idx(N('P'), 'x')), env('P', { x: 2, y: 2, z: 3 })],
  ['P["x"]-=1', new DecrementNode(Idx(N('P'), 'x')), env('P', { x: 0, y: 2, z: 3 })],
  ['M[0][0]+=1', new IncrementNode(Idx(Idx(N('M'), 0), 0)), env('M', [[2, 2], [3, 4]])],
  ['M[0][0]-=1', new DecrementNode(Idx(Idx(N('M'), 0), 0)), env('M', [[0, 2], [3, 4]])],

  // ─── Append ───────────────────────────────────────────
  ['A.append(4)',      new AppendNode(N('A'), 4),      env('A', [1, 2, 3, 4])],
  ['s.append(98)',     new AppendNode(N('s'), ORD_D),  env('s', 'abcd')],
  ['null.append(1)',   new AppendNode(null, 1),        '💣immutable-append'],
  ['s.append("d")',    new AppendNode(N('s'), 'd'),    env('s', 'abcd')],
  ['P.append("w")',    new AppendNode(N('P'), 'w'),    env('P', { x: 1, y: 2, z: 3, w: 4 })],

  // ─── if ───────────────────────────────────────────────
  ['if/true',  If(1, '==', 1, 1, 0), 1],
  ['if/false', If(1, '==', 0, 1, 0), 0],
  ['if/!=',    If(1, '!=', 1, 1, 0), 0],
  ['if/<',     If(1, '<', 1, 1, 0),  0],
  ['if/<=',    If(1, '<=', 1, 1, 0), 1],
  ['if/>',     If(1, '>', 1, 1, 0),  0],
  ['if/>=',    If(1, '>=', 1, 1, 0), 1],
  ['if/in',    If(1, 'in', N('A'), 1, 0), 1],
  ['if/notin', If(1, 'notin', N('A'), 1, 0), 0],

  // ─── repeat / break ───────────────────────────────────
  ['repeat', Blk([
    new AssignmentNode(N('x'), 0),
    new RepeatNode(10, Blk([new IncrementNode(N('x'))])),
  ]), env('x', 10)],
  ['repeat/break', Blk([
    new AssignmentNode(N('x'), 0),
    new RepeatNode(10, Blk([
      new IncrementNode(N('x')),
      new BreakNode(),
    ])),
  ]), env('x', 1)],
  ['repeat/if-break', Blk([
    new AssignmentNode(N('x'), 0),
    new RepeatNode(10, Blk([
      new IncrementNode(N('x')),
      If(N('x'), '==', Num(5), new BreakNode()),
    ])),
  ]), env('x', 5)],
  ['break/outside', Blk([new BreakNode()]), '💣unexpected-break'],

  // ─── Function definition and application ──────────────
  ['function/succ(n)', Blk([
    new FuncDefNode(N('succ'), [N('n')], Blk([
      new IncrementNode(N('n')),
      new ReturnNode(N('n')),
    ])),
    new FuncAppNode(N('succ'), [Num(0)]),
  ]), 1],
  ['function/max(a,b)', Blk([
    new FuncDefNode(N('max'), [N('a'), N('b')],
      If(N('a'), '>', N('b'),
        new ReturnNode(N('a')),
        new ReturnNode(N('b')))),
    new FuncAppNode(N('max'), [10, 20]),
  ]), 20],
  ['function/mul(a,b)', Blk([
    new FuncDefNode(N('mul'), [N('a'), N('b')], Blk([
      new AssignmentNode(N('result'), Num(0)),
      new RepeatNode(N('b'), Blk([
        new RepeatNode(N('a'), Blk([
          new IncrementNode(N('result')),
        ])),
      ])),
      new ReturnNode(N('result')),
    ])),
    new FuncAppNode(N('mul'), [Num(10), Num(20)]),
  ]), 200],
  ['function/zero()', Blk([
    new FuncDefNode(N('zero'), [], new ReturnNode(Num(0))),
    new FuncAppNode(N('zero'), []),
  ]), 0],
  ['function/factorial(n)', Blk([
    new FuncDefNode(N('factorial'), [N('n')], Blk([
      If(N('n'), '==', Num(0), new ReturnNode(Num(1))),
      new ReturnNode(Bin('*', N('n'),
        new FuncAppNode(N('factorial'), [Bin('-', N('n'), Num(1))]))),
    ])),
    new FuncAppNode(N('factorial'), [Num(5)]),
  ]), 120],
  ['function/no-return', Blk([
    new FuncDefNode(N('point'), [N('x'), N('y')], Blk([])),
    new FuncAppNode(N('point'), [Num(0), Num(1)]),
  ]), { x: 0, y: 1 }],
  ['function/undefined', new FuncAppNode(N('sub'), [Num(10)]), '💣undefined-function'],
  ['function_argument_mismatch', Blk([
    new FuncDefNode(N('add'), [N('a'), N('b')], Blk([
      new ReturnNode(new MinusNode(new MinusNode(N('a')))),
    ])),
    new FuncAppNode(N('add'), [Num(10)]),
  ]), '💣mismatch-argument'],
  ['function/too-many-recursion', Blk([
    new FuncDefNode(N('add'), [N('a'), N('b')],
      new ReturnNode(new FuncAppNode(N('add'), [10, 20]))),
    new FuncAppNode(N('add'), [10, 20]),
  ]), '💣too-many-recursion'],
  ['Return/outside', Blk([new ReturnNode(Num(0))]), '💣unexpected-return'],

  // ─── AssertNode ───────────────────────────────────────
  ['Assert/a==1',              new AssertNode(N('a'), 1), true],
  ['Assert/a==0',              new AssertNode(N('a'), 0), '💣assertion-failed'],
  ['Assert/s=="abc"',          new AssertNode(N('s'), 'abc'), true],
  ['Assert/A==[1,2,3]',        new AssertNode(N('A'), [1, 2, 3]), true],
  ['Assert/P=={"x":1,...}',    new AssertNode(N('P'), { x: 1, y: 2, z: 3 }), true],
  ['Assert/M==[[1,2],[3,4]]',  new AssertNode(N('M'), [[1, 2], [3, 4]]), true],
  ['Assert/succ(0)==1', Blk([
    new FuncDefNode(N('succ'), [N('n')], Blk([
      new IncrementNode(N('n')),
      new ReturnNode(N('n')),
    ])),
    new AssertNode(new FuncAppNode(N('succ'), [Num(0)]), 1),
  ]), true],
];
