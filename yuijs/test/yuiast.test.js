// yuiast.js の単体テスト (Python 版 yuichan/test_ast.py を部分移植)
// node --test test/yuiast.test.js
//
// このレイヤーはまだ runtime を持たないので、Python 側 test_ast のように
// evaluate() を走らせるケースは runtime 移植後に追加する。
// ここでは次を検証する:
//   - コンストラクタがフィールドを正しく初期化する
//   - _node() の coercion (null/bool/number/string/array/object/ASTNode)
//   - visit() が visit{ClassName} を正しくディスパッチする
//   - setpos/toString/extract が Python 版と同じ挙動を返す
//   - order_policy="reversed" が各種ノードで動く
//   - OPERATORS が BinaryNode/IfNode に反映される

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  ASTNode,
  ExpressionNode,
  StatementNode,
  _node,
  ConstNode,
  NumberNode,
  ArrayLenNode,
  MinusNode,
  StringNode,
  ArrayNode,
  ObjectNode,
  NameNode,
  GetIndexNode,
  BinaryNode,
  FuncAppNode,
  AssignmentNode,
  IncrementNode,
  DecrementNode,
  AppendNode,
  BlockNode,
  IfNode,
  BreakNode,
  PassNode,
  RepeatNode,
  ImportNode,
  ReturnNode,
  FuncDefNode,
  PrintExpressionNode,
  AssertNode,
  CatchNode,
} from '../src/yuiast.js';

import { OPERATORS } from '../src/yuitypes.js';

// ─────────────────────────────────────────────
// 基底クラス
// ─────────────────────────────────────────────

test('ASTNode: デフォルトフィールド', () => {
  const n = new ConstNode();
  assert.equal(n.filename, 'main.yui');
  assert.equal(n.source, '');
  assert.equal(n.pos, 0);
  assert.equal(n.end_pos, -1);
  assert.equal(n.comment, null);
});

test('ASTNode: クラス階層', () => {
  assert.ok(new ConstNode() instanceof ExpressionNode);
  assert.ok(new ConstNode() instanceof ASTNode);
  assert.ok(new BlockNode([]) instanceof StatementNode);
  assert.ok(new BlockNode([]) instanceof ASTNode);
  assert.ok(new GetIndexNode(new NameNode('a'), 0) instanceof ASTNode);
  // GetIndexNode と BinaryNode は Python 版と同様に ExpressionNode を継承しない
  assert.ok(!(new BinaryNode('+', 1, 2) instanceof ExpressionNode));
});

test('ASTNode.setpos: source/pos/end_pos/filename をセットして self を返す', () => {
  const n = new NumberNode(1);
  const ret = n.setpos('hello\nworld', 6, 11, 'test.yui');
  assert.equal(ret, n);
  assert.equal(n.source, 'hello\nworld');
  assert.equal(n.pos, 6);
  assert.equal(n.end_pos, 11);
  assert.equal(n.filename, 'test.yui');
  assert.equal(n.comment, null);
});

test('ASTNode.toString: source[pos:end_pos]', () => {
  const n = new NumberNode(1);
  n.setpos('hello world', 6, 11);
  assert.equal(n.toString(), 'world');
  assert.equal(String(n), 'world');
});

test('ASTNode.extract: 行番号・列番号・スニペット', () => {
  const src = 'abc\ndef ghi\njkl';
  // pos=5 は 2 行目の 'e' の次 ('f') にあたる
  //   a b c \n d e f ...
  //   0 1 2 3  4 5 6
  const n = new NumberNode(0);
  n.setpos(src, 5);
  const [line, col, snippet] = n.extract();
  assert.equal(line, 2);
  assert.equal(col, 2);
  assert.equal(snippet, 'def ghi');
});

test('ASTNode.extract: pos=0 で先頭行', () => {
  const src = 'xyz\nabc';
  const n = new NumberNode(0);
  n.setpos(src, 0);
  const [line, col, snippet] = n.extract();
  assert.equal(line, 1);
  assert.equal(col, 1);
  assert.equal(snippet, 'xyz');
});

test('ASTNode.extract: 改行のない単一行', () => {
  const n = new NumberNode(0);
  n.setpos('hello', 3);
  const [line, col, snippet] = n.extract();
  assert.equal(line, 1);
  assert.equal(col, 4);
  assert.equal(snippet, 'hello');
});

// ─────────────────────────────────────────────
// _node() 変換
// ─────────────────────────────────────────────

test('_node: null → ConstNode(null)', () => {
  const n = _node(null);
  assert.ok(n instanceof ConstNode);
  assert.equal(n.native_value, null);
});

test('_node: true/false → ConstNode(bool)', () => {
  const t = _node(true);
  const f = _node(false);
  assert.ok(t instanceof ConstNode);
  assert.ok(f instanceof ConstNode);
  assert.equal(t.native_value, true);
  assert.equal(f.native_value, false);
});

test('_node: number → NumberNode', () => {
  const i = _node(42);
  const fl = _node(3.5);
  assert.ok(i instanceof NumberNode);
  assert.ok(fl instanceof NumberNode);
  assert.equal(i.native_value, 42);
  assert.equal(fl.native_value, 3.5);
});

test('_node: string → StringNode', () => {
  const s = _node('hello');
  assert.ok(s instanceof StringNode);
  assert.equal(s.contents, 'hello');
});

test('_node: 📦 接頭辞 → NameNode (前後の空白を trim)', () => {
  const n = _node('📦 foo ');
  assert.ok(n instanceof NameNode);
  assert.equal(n.name, 'foo');
});

test('_node: 📦 接頭辞 (空白なし) → NameNode', () => {
  const n = _node('📦bar');
  assert.ok(n instanceof NameNode);
  assert.equal(n.name, 'bar');
});

test('_node: array → ArrayNode (要素は再帰変換)', () => {
  const a = _node([1, 'x', null, true]);
  assert.ok(a instanceof ArrayNode);
  assert.equal(a.elements.length, 4);
  assert.ok(a.elements[0] instanceof NumberNode);
  assert.ok(a.elements[1] instanceof StringNode);
  assert.ok(a.elements[2] instanceof ConstNode);
  assert.equal(a.elements[2].native_value, null);
  assert.ok(a.elements[3] instanceof ConstNode);
  assert.equal(a.elements[3].native_value, true);
});

test('_node: plain object → ObjectNode ([key, value, ...] の並び)', () => {
  const o = _node({ x: 1, y: 2 });
  assert.ok(o instanceof ObjectNode);
  assert.equal(o.elements.length, 4);
  assert.ok(o.elements[0] instanceof StringNode);
  assert.equal(o.elements[0].contents, 'x');
  assert.ok(o.elements[1] instanceof NumberNode);
  assert.equal(o.elements[1].native_value, 1);
  assert.ok(o.elements[2] instanceof StringNode);
  assert.equal(o.elements[2].contents, 'y');
  assert.ok(o.elements[3] instanceof NumberNode);
  assert.equal(o.elements[3].native_value, 2);
});

test('_node: ASTNode はそのまま通す', () => {
  const orig = new NumberNode(7);
  const out = _node(orig);
  assert.equal(out, orig);
});

test('_node: undefined は null と同じ扱い', () => {
  const n = _node(undefined);
  assert.ok(n instanceof ConstNode);
  assert.equal(n.native_value, null);
});

// ─────────────────────────────────────────────
// visit() ディスパッチ
// ─────────────────────────────────────────────

test('visit(): visit{ClassName} を呼び出す', () => {
  const log = [];
  const visitor = {
    visitConstNode(n) { log.push(['const', n.native_value]); return 'c'; },
    visitNumberNode(n) { log.push(['num', n.native_value]); return 'n'; },
    visitNameNode(n) { log.push(['name', n.name]); return 'v'; },
  };
  assert.equal(new ConstNode(true).visit(visitor), 'c');
  assert.equal(new NumberNode(42).visit(visitor), 'n');
  assert.equal(new NameNode('x').visit(visitor), 'v');
  assert.deepEqual(log, [
    ['const', true],
    ['num', 42],
    ['name', 'x'],
  ]);
});

test('evaluate() は visit() に委譲する', () => {
  const visitor = {
    visitNumberNode(n) { return n.native_value * 2; },
  };
  assert.equal(new NumberNode(21).evaluate(visitor), 42);
});

test('visit(): 未定義メソッドは TypeError', () => {
  const visitor = {};
  assert.throws(
    () => new ConstNode().visit(visitor),
    /visitConstNode/
  );
});

// ─────────────────────────────────────────────
// 各ノードのコンストラクタ
// ─────────────────────────────────────────────

test('ConstNode: デフォルトは null', () => {
  assert.equal(new ConstNode().native_value, null);
  assert.equal(new ConstNode(null).native_value, null);
  assert.equal(new ConstNode(true).native_value, true);
  assert.equal(new ConstNode(false).native_value, false);
});

test('NumberNode', () => {
  assert.equal(new NumberNode(42).native_value, 42);
  assert.equal(new NumberNode(3.14).native_value, 3.14);
});

test('ArrayLenNode: element は _node で coerce される', () => {
  const n = new ArrayLenNode('hello');
  assert.ok(n.element instanceof StringNode);
  const n2 = new ArrayLenNode(new NameNode('A'));
  assert.ok(n2.element instanceof NameNode);
  assert.equal(n2.element.name, 'A');
});

test('MinusNode: element は _node で coerce される', () => {
  const n = new MinusNode(16);
  assert.ok(n.element instanceof NumberNode);
  assert.equal(n.element.native_value, 16);
});

test('StringNode: 素の文字列', () => {
  const s = new StringNode('');
  assert.equal(s.contents, '');
  const s2 = new StringNode('hello');
  assert.equal(s2.contents, 'hello');
});

test('StringNode: 補間ありの配列コンテンツ', () => {
  const s = new StringNode(['A', new NameNode('a'), 'B']);
  assert.ok(Array.isArray(s.contents));
  assert.equal(s.contents[0], 'A');
  assert.ok(s.contents[1] instanceof NameNode);
  assert.equal(s.contents[1].name, 'a');
  assert.equal(s.contents[2], 'B');
});

test('ArrayNode: 要素が _node で coerce される', () => {
  const a = new ArrayNode([1, 'x', new NameNode('y')]);
  assert.equal(a.elements.length, 3);
  assert.ok(a.elements[0] instanceof NumberNode);
  assert.ok(a.elements[1] instanceof StringNode);
  assert.ok(a.elements[2] instanceof NameNode);
});

test('ArrayNode: 空配列', () => {
  const a = new ArrayNode([]);
  assert.deepEqual(a.elements, []);
});

test('ObjectNode: 要素の並び [key, value, ...]', () => {
  const o = new ObjectNode(['x', new NumberNode(1), 'y', new NumberNode(2)]);
  assert.equal(o.elements.length, 4);
  assert.ok(o.elements[0] instanceof StringNode);
  assert.ok(o.elements[1] instanceof NumberNode);
});

test('NameNode', () => {
  const n = new NameNode('foo');
  assert.equal(n.name, 'foo');
});

test('NameNode.update(): visitor.setenv を呼ぶ', () => {
  const log = [];
  const visitor = {
    setenv(name, value) { log.push([name, value]); },
  };
  new NameNode('a').update(42, visitor);
  assert.deepEqual(log, [['a', 42]]);
});

test('GetIndexNode: collection/index が _node で coerce される', () => {
  const n = new GetIndexNode(new NameNode('A'), 0);
  assert.ok(n.collection instanceof NameNode);
  assert.ok(n.index_node instanceof NumberNode);
  assert.equal(n.index_node.native_value, 0);
});

test('GetIndexNode: order_policy="reversed" で引数入れ替え', () => {
  const n = new GetIndexNode(0, new NameNode('A'), 'reversed');
  assert.ok(n.collection instanceof NameNode);
  assert.equal(n.collection.name, 'A');
  assert.ok(n.index_node instanceof NumberNode);
});

test('GetIndexNode: ネストできる (M[0][1])', () => {
  const n = new GetIndexNode(
    new GetIndexNode(new NameNode('M'), 0),
    1
  );
  assert.ok(n.collection instanceof GetIndexNode);
  assert.ok(n.index_node instanceof NumberNode);
});

test('BinaryNode: OPERATORS から operator を引く', () => {
  const n = new BinaryNode('+', new NameNode('a'), 1);
  assert.equal(n.operator, OPERATORS['+']);
  assert.equal(n.comparative, false);
  assert.ok(n.left_node instanceof NameNode);
  assert.ok(n.right_node instanceof NumberNode);
});

test('BinaryNode: 比較演算子は comparative=true', () => {
  const n = new BinaryNode('==', 0, 0);
  assert.equal(n.operator, OPERATORS['==']);
  assert.equal(n.comparative, true);
});

test('BinaryNode: 不明な演算子はエラー', () => {
  assert.throws(() => new BinaryNode('??', 0, 0), /unknown operator/);
});

test('FuncAppNode: 名前に文字列を渡すと NameNode 化 (StringNode ではない)', () => {
  const n = new FuncAppNode('succ', [0]);
  assert.ok(n.name_node instanceof NameNode);
  assert.equal(n.name_node.name, 'succ');
  assert.equal(n.arguments.length, 1);
  assert.ok(n.arguments[0] instanceof NumberNode);
});

test('FuncAppNode: NameNode を直接渡す', () => {
  const n = new FuncAppNode(new NameNode('max'), [10, 20]);
  assert.ok(n.name_node instanceof NameNode);
  assert.equal(n.name_node.name, 'max');
});

test('FuncAppNode: order_policy="reversed"', () => {
  const n = new FuncAppNode([10, 20], 'max', 'reversed');
  assert.ok(n.name_node instanceof NameNode);
  assert.equal(n.name_node.name, 'max');
  assert.equal(n.arguments.length, 2);
});

test('FuncAppNode: snippet プロパティ', () => {
  const n = new FuncAppNode('f', []);
  // source="" なので snippet は "".slice(0, -1) = "" (Python 版と同じ)
  assert.equal(typeof n.snippet, 'string');
});

test('AssignmentNode', () => {
  const n = new AssignmentNode(new NameNode('x'), 42);
  assert.ok(n.variable instanceof NameNode);
  assert.ok(n.expression instanceof NumberNode);
});

test('AssignmentNode: order_policy="reversed"', () => {
  const n = new AssignmentNode(42, new NameNode('x'), 'reversed');
  assert.ok(n.variable instanceof NameNode);
  assert.ok(n.expression instanceof NumberNode);
});

test('IncrementNode / DecrementNode', () => {
  const inc = new IncrementNode(new NameNode('a'));
  const dec = new DecrementNode(new NameNode('a'));
  assert.ok(inc.variable instanceof NameNode);
  assert.ok(dec.variable instanceof NameNode);
});

test('IncrementNode: GetIndexNode を variable に渡せる', () => {
  const inc = new IncrementNode(new GetIndexNode(new NameNode('A'), 0));
  assert.ok(inc.variable instanceof GetIndexNode);
});

test('AppendNode', () => {
  const n = new AppendNode(new NameNode('A'), 4);
  assert.ok(n.variable instanceof NameNode);
  assert.ok(n.expression instanceof NumberNode);
});

test('AppendNode: order_policy="reversed"', () => {
  const n = new AppendNode(4, new NameNode('A'), 'reversed');
  assert.ok(n.variable instanceof NameNode);
  assert.ok(n.expression instanceof NumberNode);
});

test('BlockNode: 配列を受け取る', () => {
  const b = new BlockNode([new BreakNode(), new PassNode()]);
  assert.equal(b.statements.length, 2);
  assert.equal(b.top_level, false);
});

test('BlockNode: 単一の StatementNode を配列にラップする', () => {
  const b = new BlockNode(new BreakNode());
  assert.equal(b.statements.length, 1);
  assert.ok(b.statements[0] instanceof BreakNode);
});

test('BlockNode: 不正な入力はエラー', () => {
  assert.throws(() => new BlockNode(42), /statements/);
});

test('BlockNode: top_level=true', () => {
  const b = new BlockNode([], true);
  assert.equal(b.top_level, true);
});

test('IfNode: operator 解決と else デフォルト', () => {
  const n = new IfNode(1, '==', 1, new NumberNode(1));
  assert.equal(n.operator, OPERATORS['==']);
  assert.ok(n.left instanceof NumberNode);
  assert.ok(n.right instanceof NumberNode);
  assert.ok(n.then_block instanceof NumberNode); // _node() で coerce される
  assert.ok(n.else_block instanceof PassNode); // デフォルトは PassNode
});

test('IfNode: else_block が指定された場合', () => {
  const n = new IfNode(1, '!=', 0, new NumberNode(1), new NumberNode(0));
  assert.ok(n.else_block instanceof NumberNode);
  assert.equal(n.else_block.native_value, 0);
});

test('IfNode: 各種 operator を受け付ける', () => {
  const ops = ['==', '!=', '<', '<=', '>', '>=', 'in', 'notin'];
  for (const op of ops) {
    const n = new IfNode(1, op, 1, new NumberNode(1));
    assert.equal(n.operator, OPERATORS[op]);
  }
});

test('BreakNode: 空クラス', () => {
  const b = new BreakNode();
  assert.ok(b instanceof StatementNode);
});

test('PassNode: コメント', () => {
  const p = new PassNode('# memo');
  assert.equal(p.comment, '# memo');
});

test('PassNode: デフォルト', () => {
  const p = new PassNode();
  assert.equal(p.comment, null);
});

test('RepeatNode', () => {
  const n = new RepeatNode(10, new BlockNode([new BreakNode()]));
  assert.ok(n.count_node instanceof NumberNode);
  assert.ok(n.block_node instanceof BlockNode);
});

test('RepeatNode: order_policy="reversed"', () => {
  const n = new RepeatNode(new BlockNode([]), 10, 'reversed');
  assert.ok(n.count_node instanceof NumberNode);
  assert.ok(n.block_node instanceof BlockNode);
});

test('ImportNode: 文字列は NameNode 化', () => {
  const n = new ImportNode('標準ライブラリ');
  assert.ok(n.module_name instanceof NameNode);
  assert.equal(n.module_name.name, '標準ライブラリ');
});

test('ImportNode: NameNode を直接渡す', () => {
  const nn = new NameNode('mylib');
  const n = new ImportNode(nn);
  assert.equal(n.module_name, nn);
});

test('ReturnNode', () => {
  const n = new ReturnNode(42);
  assert.ok(n.expression instanceof NumberNode);
});

test('FuncDefNode', () => {
  const n = new FuncDefNode(
    new NameNode('succ'),
    [new NameNode('n')],
    new BlockNode([new ReturnNode(new NameNode('n'))])
  );
  assert.ok(n.name_node instanceof NameNode);
  assert.equal(n.name_node.name, 'succ');
  assert.equal(n.parameters.length, 1);
  assert.ok(n.parameters[0] instanceof NameNode);
  assert.ok(n.body instanceof BlockNode);
});

test('FuncDefNode: 引数なし', () => {
  const n = new FuncDefNode(
    new NameNode('zero'),
    [],
    new ReturnNode(0)
  );
  assert.deepEqual(n.parameters, []);
});

test('PrintExpressionNode: デフォルト', () => {
  const n = new PrintExpressionNode(new NumberNode(42));
  assert.ok(n.expression instanceof NumberNode);
  assert.equal(n.inspection, false);
  assert.equal(n.grouping, false);
});

test('PrintExpressionNode: フラグ', () => {
  const n = new PrintExpressionNode(new NumberNode(42), true, true);
  assert.equal(n.inspection, true);
  assert.equal(n.grouping, true);
});

test('AssertNode', () => {
  const n = new AssertNode(new NameNode('a'), 1);
  assert.ok(n.test instanceof NameNode);
  assert.ok(n.reference instanceof NumberNode);
});

test('AssertNode: order_policy="reversed"', () => {
  const n = new AssertNode(1, new NameNode('a'), 'reversed');
  assert.ok(n.test instanceof NameNode);
  assert.ok(n.reference instanceof NumberNode);
});

test('CatchNode', () => {
  const inner = new NumberNode(42);
  const n = new CatchNode(inner);
  assert.equal(n.expression, inner);
});

test('CatchNode: 非ノード値も _node で coerce', () => {
  const n = new CatchNode(42);
  assert.ok(n.expression instanceof NumberNode);
});

// ─────────────────────────────────────────────
// visit() によるディスパッチ網羅
// ─────────────────────────────────────────────
//
// 全ノードで visit{ClassName} が引かれることを確認する。ここでは visitor が
// 何を返すかは問わず、「正しいメソッド名を呼び出そうとする」ことのみを検証。

test('全ノードで visit{ClassName} が呼ばれる', () => {
  const calls = [];
  const handler = (name) => (_n) => { calls.push(name); return name; };
  const visitor = {
    visitConstNode: handler('ConstNode'),
    visitNumberNode: handler('NumberNode'),
    visitArrayLenNode: handler('ArrayLenNode'),
    visitMinusNode: handler('MinusNode'),
    visitStringNode: handler('StringNode'),
    visitArrayNode: handler('ArrayNode'),
    visitObjectNode: handler('ObjectNode'),
    visitNameNode: handler('NameNode'),
    visitGetIndexNode: handler('GetIndexNode'),
    visitBinaryNode: handler('BinaryNode'),
    visitFuncAppNode: handler('FuncAppNode'),
    visitAssignmentNode: handler('AssignmentNode'),
    visitIncrementNode: handler('IncrementNode'),
    visitDecrementNode: handler('DecrementNode'),
    visitAppendNode: handler('AppendNode'),
    visitBlockNode: handler('BlockNode'),
    visitIfNode: handler('IfNode'),
    visitBreakNode: handler('BreakNode'),
    visitPassNode: handler('PassNode'),
    visitRepeatNode: handler('RepeatNode'),
    visitImportNode: handler('ImportNode'),
    visitReturnNode: handler('ReturnNode'),
    visitFuncDefNode: handler('FuncDefNode'),
    visitPrintExpressionNode: handler('PrintExpressionNode'),
    visitAssertNode: handler('AssertNode'),
    visitCatchNode: handler('CatchNode'),
  };

  const nodes = [
    new ConstNode(null),
    new NumberNode(1),
    new ArrayLenNode(new NameNode('A')),
    new MinusNode(1),
    new StringNode('x'),
    new ArrayNode([]),
    new ObjectNode([]),
    new NameNode('a'),
    new GetIndexNode(new NameNode('A'), 0),
    new BinaryNode('+', 1, 2),
    new FuncAppNode('f', []),
    new AssignmentNode(new NameNode('x'), 1),
    new IncrementNode(new NameNode('x')),
    new DecrementNode(new NameNode('x')),
    new AppendNode(new NameNode('A'), 1),
    new BlockNode([]),
    new IfNode(1, '==', 1, new NumberNode(1)),
    new BreakNode(),
    new PassNode(),
    new RepeatNode(10, new BlockNode([])),
    new ImportNode('lib'),
    new ReturnNode(1),
    new FuncDefNode(new NameNode('f'), [], new BlockNode([])),
    new PrintExpressionNode(new NumberNode(1)),
    new AssertNode(new NameNode('a'), 1),
    new CatchNode(1),
  ];

  for (const n of nodes) {
    n.visit(visitor);
  }

  assert.deepEqual(calls, [
    'ConstNode',
    'NumberNode',
    'ArrayLenNode',
    'MinusNode',
    'StringNode',
    'ArrayNode',
    'ObjectNode',
    'NameNode',
    'GetIndexNode',
    'BinaryNode',
    'FuncAppNode',
    'AssignmentNode',
    'IncrementNode',
    'DecrementNode',
    'AppendNode',
    'BlockNode',
    'IfNode',
    'BreakNode',
    'PassNode',
    'RepeatNode',
    'ImportNode',
    'ReturnNode',
    'FuncDefNode',
    'PrintExpressionNode',
    'AssertNode',
    'CatchNode',
  ]);
});
