#!/usr/bin/env node
// main.js — CLI
//
// Yui の主要なターゲットは Web アプリへの埋め込みなので、このファイルは
// Node 上のユースケースだけをカバーする。Python 版 yuichan/main.py の
// 主要機能 (--bnf / --pass@1 / --list-examples / --show-examples /
// --make-examples / --test-examples / --list-syntax / --find-syntax /
// --interactive / --convert-to) を移植。

import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';
import { createInterface } from 'node:readline';
import process from 'node:process';

import { run, convert } from './index.js';
import { YuiRuntime } from './yuiruntime.js';
import { YuiError, formatMessages } from './yuierror.js';
import {
  loadSyntax,
  listSyntaxNames,
  generateBnf,
  findMatchingSyntaxes,
} from './yuisyntax.js';
import { CodingVisitor } from './yuicoding.js';
import { IncrementNode, NameNode } from './yuiast.js';
import { getSamples, getTestExamples, getAllExamples } from './yuiexample.js';

const USAGE = `Usage:
  node src/main.js [options] <file.yui>
  cat file.yui | node src/main.js [options]

Options:
  --syntax NAME            syntax name (default: yui)
  --allow-binary-ops       enable +/-/*/// operators
  --syntax-list            list available syntax names and exit
  --pass@1                 execute multiple files and report pass@1 rate
                           (a_doctest.yui is concatenated to a.yui if it exists)
  --bnf                    show BNF grammar for the selected syntax
  --list-examples          list built-in examples
  --list-syntax            list syntax files with an "x += 1" sample for each
  --find-syntax <files>    detect which syntaxes can parse the given files
  --show-examples          print sample code (with --syntax)
  --make-examples          write sample code to <syntax>_examples/*.yui
  --test-examples          run all built-in test examples
  --convert-to SYNTAX      convert input file(s) from --syntax to SYNTAX
                           (output saved to <SYNTAX>/<basename>)
  -i, --interactive        start REPL (after executing any file)
  --example NAME           target a specific example (with --show/--make-examples)
  --random-seed N          random seed for code generation
  --indent-string STR      indent string (default "   ")
  --function-language LANG function name language: ja|en|emoji
  -h, --help               show this help and exit
`;

function parseArgs(argv) {
  const opts = {
    syntax: 'yui',
    allowBinaryOps: false,
    syntaxList: false,
    passAt1: false,
    bnf: false,
    listExamples: false,
    listSyntax: false,
    findSyntax: false,
    showExamples: false,
    makeExamples: false,
    testExamples: false,
    interactive: false,
    convertTo: null,
    example: null,
    randomSeed: null,
    indentString: null,
    functionLanguage: null,
    help: false,
    files: [],
  };

  // 値を取る系オプションのテーブル
  const valueOpts = {
    '--syntax':            (v) => { opts.syntax = v; },
    '--convert-to':        (v) => { opts.convertTo = v; },
    '--example':           (v) => { opts.example = v; },
    '--random-seed':       (v) => { opts.randomSeed = parseInt(v, 10); },
    '--indent-string':     (v) => { opts.indentString = v; },
    '--function-language': (v) => { opts.functionLanguage = v; },
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '-h' || arg === '--help') {
      opts.help = true;
    } else if (arg === '-i' || arg === '--interactive') opts.interactive = true;
    else   if (arg === '--allow-binary-ops')   opts.allowBinaryOps = true;
    else   if (arg === '--syntax-list')        opts.syntaxList     = true;
    else   if (arg === '--pass@1')             opts.passAt1        = true;
    else   if (arg === '--bnf')                opts.bnf            = true;
    else   if (arg === '--list-examples')      opts.listExamples   = true;
    else   if (arg === '--list-syntax')        opts.listSyntax     = true;
    else   if (arg === '--find-syntax')        opts.findSyntax     = true;
    else   if (arg === '--show-examples')      opts.showExamples   = true;
    else   if (arg === '--make-examples')      opts.makeExamples   = true;
    else   if (arg === '--test-examples')      opts.testExamples   = true;
    else if (arg in valueOpts) {
      const v = argv[++i];
      if (v == null) throw new Error(`${arg} requires a value`);
      valueOpts[arg](v);
    } else if (arg.startsWith('--') && arg.includes('=')) {
      // --key=value 形式
      const eq = arg.indexOf('=');
      const key = arg.slice(0, eq);
      if (!(key in valueOpts)) throw new Error(`unknown option: ${key}`);
      valueOpts[key](arg.slice(eq + 1));
    } else if (arg.startsWith('-')) {
      throw new Error(`unknown option: ${arg}`);
    } else {
      opts.files.push(arg);
    }
  }
  return opts;
}

function readStdinSync() {
  if (process.stdin.isTTY) return '';
  try {
    return readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

async function main(argv) {
  let opts;
  try {
    opts = parseArgs(argv);
  } catch (e) {
    process.stderr.write(`${e.message}\n\n${USAGE}`);
    return 2;
  }

  if (opts.help)         { process.stdout.write(USAGE); return 0; }
  if (opts.syntaxList)   { return syntaxListMode(); }
  if (opts.listExamples) { return listExamplesMode(); }
  if (opts.listSyntax)   { return listSyntaxMode(); }
  if (opts.bnf)          { return bnfMode(opts.syntax); }
  if (opts.findSyntax)   { return findSyntaxMode(opts.files); }
  if (opts.showExamples) { return showExamplesMode(opts); }
  if (opts.makeExamples) { return makeExamplesMode(opts); }
  if (opts.testExamples) { return testExamplesMode(opts.syntax); }

  if (opts.passAt1) {
    if (opts.files.length === 0) {
      process.stderr.write(`Error: --pass@1 requires at least one file\n${USAGE}`);
      return 2;
    }
    return passAt1Mode(opts.files, opts.syntax);
  }

  if (opts.convertTo) {
    if (opts.files.length === 0) {
      process.stderr.write(`Error: --convert-to requires at least one input file\n`);
      return 1;
    }
    return convertToMode(opts);
  }

  // REPL: -i 明示 or (ファイル無し かつ stdin が tty)
  if (opts.interactive || (opts.files.length === 0 && process.stdin.isTTY)) {
    return interactiveMode(opts);
  }

  if (opts.files.length > 1) {
    process.stderr.write(`multiple files require --pass@1\n${USAGE}`);
    return 2;
  }

  return runFileMode(opts);
}

// ─────────────────────────────────────────────
// 単発実行モード
// ─────────────────────────────────────────────
function runFileMode(opts) {
  let source;
  if (opts.files.length === 1) {
    const file = opts.files[0];
    try {
      source = readFileSync(file, 'utf8');
    } catch (e) {
      process.stderr.write(`cannot read file ${file}: ${e.message}\n`);
      return 1;
    }
  } else {
    source = readStdinSync();
    if (!source) {
      process.stderr.write(`no input.\n\n${USAGE}`);
      return 2;
    }
  }

  try {
    const { value } = run(source, {
      syntax: opts.syntax,
      allowBinaryOps: opts.allowBinaryOps,
    });
    if (value !== null && value !== undefined) {
      process.stdout.write(`${JSON.stringify(value)}\n`);
    }
    return 0;
  } catch (e) {
    if (e instanceof YuiError) {
      process.stderr.write(`${formatMessages(e.messages)}\n`);
    } else {
      process.stderr.write(`${e.stack || e.message}\n`);
    }
    return 1;
  }
}

// ─────────────────────────────────────────────
// --syntax-list
// ─────────────────────────────────────────────
function syntaxListMode() {
  for (const name of listSyntaxNames()) {
    process.stdout.write(`${name}\n`);
  }
  return 0;
}

// ─────────────────────────────────────────────
// --bnf
// ─────────────────────────────────────────────
function bnfMode(syntaxName) {
  try {
    const terminals = loadSyntax(syntaxName);
    process.stdout.write(`${generateBnf(terminals)}\n`);
    return 0;
  } catch (e) {
    process.stderr.write(`Error: ${e.message}\n`);
    return 1;
  }
}

// ─────────────────────────────────────────────
// --list-examples
// ─────────────────────────────────────────────
function listExamplesMode() {
  const examples = getAllExamples();
  process.stdout.write('\nAvailable examples:\n');
  process.stdout.write(`${'Name'.padEnd(30)} ${'Kind'.padEnd(8)} Description\n`);
  process.stdout.write(`${'-'.repeat(70)}\n`);
  for (const ex of examples) {
    process.stdout.write(`${ex.name.padEnd(30)} ${ex.kind.padEnd(8)} ${ex.description}\n`);
  }
  return 0;
}

// ─────────────────────────────────────────────
// --list-syntax
// ─────────────────────────────────────────────
function listSyntaxMode() {
  const exampleNode = new IncrementNode(new NameNode('x'));
  process.stdout.write('\nAvailable syntax files:\n');
  process.stdout.write(`${'Name'.padEnd(12)}  ${'File'.padEnd(20)}  x += 1 equivalent\n`);
  process.stdout.write(`${'-'.repeat(60)}\n`);
  for (const name of listSyntaxNames()) {
    const filename = `${name}.json`;
    let code;
    try {
      const terminals = loadSyntax(name);
      if (!terminals['if-begin']) continue;
      const visitor = new CodingVisitor(terminals);
      code = visitor.emit(exampleNode).trim();
      if (!code) code = '(no increment syntax defined)';
    } catch (e) {
      code = `(error: ${e.message})`;
    }
    process.stdout.write(`${name.padEnd(12)}  ${filename.padEnd(20)}  ${code}\n`);
  }
  return 0;
}

// ─────────────────────────────────────────────
// --find-syntax
// ─────────────────────────────────────────────
async function findSyntaxMode(files) {
  if (files.length === 0) {
    process.stderr.write('Error: --find-syntax requires at least one file\n');
    return 1;
  }
  const sources = {};
  for (const filename of files) {
    try {
      sources[filename] = readFileSync(filename, 'utf8');
    } catch (e) {
      process.stderr.write(`Error: File not found - ${filename}\n`);
      return 1;
    }
  }
  const results = await findMatchingSyntaxes(sources);
  process.stdout.write(`\nTrying ${results.length} syntax file(s) against ${files.length} file(s)...\n\n`);
  const matched = results.filter((r) => r.matched).map((r) => r.name);
  for (const { name, matched: ok, status } of results) {
    process.stdout.write(`  ${ok ? '✓' : '✗'}  ${name.padEnd(12)}  ${status}\n`);
  }
  process.stdout.write('\n');
  if (matched.length > 0) {
    process.stdout.write(`Matching syntax: ${matched.join(', ')}\n`);
    return 0;
  }
  process.stdout.write('No syntax matched all files.\n');
  return 1;
}

// ─────────────────────────────────────────────
// --show-examples
// ─────────────────────────────────────────────
function showExamplesMode(opts) {
  let examples = getSamples();
  if (opts.example) {
    examples = examples.filter((ex) => ex.name === opts.example);
    if (examples.length === 0) {
      process.stderr.write(`Error: Example '${opts.example}' not found\n`);
      return 1;
    }
  }
  examples.forEach((ex, i) => {
    if (i > 0) process.stdout.write('\n');
    process.stdout.write(`# ${ex.name}: ${ex.description}\n`);
    process.stdout.write(`${ex.generate(opts.syntax, {
      includeAsserts: false,
      randomSeed: opts.randomSeed,
      indentString: opts.indentString,
      functionLanguage: opts.functionLanguage,
    })}\n`);
  });
  return 0;
}

// ─────────────────────────────────────────────
// --make-examples
// ─────────────────────────────────────────────
function makeExamplesMode(opts) {
  const examples = getSamples();
  const examplesDir = `${opts.syntax}_examples`;
  mkdirSync(examplesDir, { recursive: true });

  if (opts.example) {
    const ex = examples.find((e) => e.name === opts.example);
    if (!ex) {
      process.stderr.write(`Error: Example '${opts.example}' not found\n\nAvailable examples:\n`);
      for (const e of examples) process.stderr.write(`  - ${e.name}\n`);
      return 1;
    }
    writeExampleFile(ex, examplesDir, opts);
    return 0;
  }

  for (const ex of examples) {
    writeExampleFile(ex, examplesDir, opts);
  }
  process.stdout.write(`\nAll examples generated in ${examplesDir}/ directory\n`);
  return 0;
}

function writeExampleFile(ex, dir, opts) {
  const code = ex.generate(opts.syntax, {
    randomSeed: opts.randomSeed,
    indentString: opts.indentString,
    functionLanguage: opts.functionLanguage,
  });
  const filename = join(dir, `${ex.name}.yui`);
  writeFileSync(filename, code, 'utf8');
  process.stdout.write(`Generated: ${filename}\n`);
}

// ─────────────────────────────────────────────
// --test-examples
// ─────────────────────────────────────────────
function testExamplesMode(syntax = 'yui') {
  const examples = getTestExamples();
  process.stdout.write(`\nTesting examples with syntax: ${syntax}\n`);
  const sep = '='.repeat(60);
  process.stdout.write(`${sep}\n`);

  let passed = 0;
  let failed = 0;
  for (const example of examples) {
    let runtime = null;
    try {
      const code = example.generate(syntax);
      runtime = new YuiRuntime();
      runtime.exec(code, syntax, { evalMode: false });
      process.stdout.write(`✓ ${example.name.padEnd(20)} PASSED\n`);
      passed += 1;
    } catch (e) {
      if (e instanceof YuiError && runtime) {
        process.stdout.write(`✗ ${example.name.padEnd(20)} FAILED\n`);
        process.stdout.write(`${runtime.formatError(e, '    | ')}\n`);
      } else {
        process.stdout.write(`✗ ${example.name.padEnd(20)} FAILED: ${e.message ?? e}\n`);
      }
      failed += 1;
    }
  }

  process.stdout.write(`${sep}\n`);
  process.stdout.write(`\nResults: ${passed} passed, ${failed} failed\n`);
  return failed > 0 ? 1 : 0;
}

// ─────────────────────────────────────────────
// --pass@1
// ─────────────────────────────────────────────
/**
 * 複数の .yui ファイルを実行して pass@1 率を計算する。
 * Python 版 yuichan/main.py::pass_at_1_mode の移植。
 *
 * - `_doctest.yui` で終わるファイルは単独実行対象から除外
 * - `a.yui` に対し `a_doctest.yui` があれば連結して 1 つのプログラムとして実行
 */
function passAt1Mode(files, syntax = 'yui') {
  const yuiFiles = files.filter(
    (f) => f.endsWith('.yui') && !f.endsWith('_doctest.yui'),
  );

  if (yuiFiles.length === 0) {
    process.stderr.write('Error: No .yui files specified\n');
    return 1;
  }

  const results = [];
  /** @type {Map<string, number>} */
  const errorCounts = new Map();

  for (const filename of yuiFiles) {
    let label = filename;
    let runtime = null;
    try {
      let code = readFileSync(filename, 'utf8');
      const doctestFile = `${filename.slice(0, -'.yui'.length)}_doctest.yui`;
      if (existsSync(doctestFile)) {
        code = `${code}\n${readFileSync(doctestFile, 'utf8')}`;
        label = `${filename} + ${basename(doctestFile)}`;
      }
      runtime = new YuiRuntime();
      runtime.exec(code, syntax, { evalMode: false });
      results.push(1);
      process.stdout.write(`✓ ${label}\n`);
    } catch (e) {
      results.push(0);
      if (e instanceof YuiError) {
        errorCounts.set(e.messages[0], (errorCounts.get(e.messages[0]) ?? 0) + 1);
        process.stdout.write(`✗ ${label}\n`);
        if (runtime) {
          process.stdout.write(`${runtime.formatError(e, '  | ')}\n`);
        }
      } else if (e.code === 'ENOENT') {
        errorCounts.set('file-not-found', (errorCounts.get('file-not-found') ?? 0) + 1);
        process.stdout.write(`✗ ${filename} (File not found)\n`);
      } else {
        errorCounts.set('other-error', (errorCounts.get('other-error') ?? 0) + 1);
        process.stdout.write(`✗ ${label}\n  | Error: ${e.message ?? e}\n`);
      }
    }
  }

  const total = results.length;
  const passed = results.reduce((a, b) => a + b, 0);
  const failed = total - passed;
  const passRate = total > 0 ? passed / total : 0;

  const sep = '='.repeat(50);
  process.stdout.write(`\n${sep}\n`);
  process.stdout.write(`Total: ${total}\n`);
  process.stdout.write(`Passed: ${passed}\n`);
  process.stdout.write(`Failed: ${failed}\n`);
  process.stdout.write(`pass@1: ${(passRate * 100).toFixed(2)}% (${passed}/${total})\n`);

  if (errorCounts.size > 0) {
    process.stdout.write(`\nError breakdown (${failed} failures):\n`);
    const sorted = [...errorCounts].sort((a, b) => b[1] - a[1]);
    for (const [errorType, count] of sorted) {
      const bar = '█'.repeat(count);
      process.stdout.write(`  ${errorType.padEnd(30)} ${String(count).padStart(4)}  ${bar}\n`);
    }
  }
  process.stdout.write(`${sep}\n`);

  return failed > 0 ? 1 : 0;
}

// ─────────────────────────────────────────────
// --convert-to
// ─────────────────────────────────────────────
/**
 * 入力ファイル群を別の構文に変換して <target>/<basename> に書き出す。
 * `.md` ファイルは ```yui コードブロックだけ変換する。
 */
function convertToMode(opts) {
  const { convertTo: targetSyntax, syntax: sourceSyntax } = opts;
  const outDir = targetSyntax;
  mkdirSync(outDir, { recursive: true });

  for (const inputFile of opts.files) {
    let content;
    try {
      content = readFileSync(inputFile, 'utf8');
    } catch (e) {
      process.stderr.write(`cannot read file ${inputFile}: ${e.message}\n`);
      return 1;
    }

    let converted;
    try {
      converted = inputFile.endsWith('.md')
        ? convertMarkdown(content, sourceSyntax, targetSyntax, opts)
        : convert(content, {
            from: sourceSyntax,
            to: targetSyntax,
            indentString: opts.indentString ?? '   ',
            functionLanguage: opts.functionLanguage,
          });
    } catch (e) {
      if (e instanceof YuiError) {
        process.stderr.write(`${inputFile}: ${formatMessages(e.messages)}\n`);
      } else {
        process.stderr.write(`${inputFile}: ${e.message ?? e}\n`);
      }
      return 1;
    }

    const outFilename = join(outDir, basename(inputFile));
    writeFileSync(outFilename, converted, 'utf8');
    process.stdout.write(`Converted: ${inputFile} -> ${outFilename}\n`);
  }
  return 0;
}

/** Markdown 内の ```yui コードブロックを変換する。他の部分はそのまま通す。 */
function convertMarkdown(content, sourceSyntax, targetSyntax, opts) {
  const lines = content.split('\n');
  const out = [];
  let inBlock = false;
  let buffer = [];

  for (const line of lines) {
    const stripped = line.trim();
    if (!inBlock && stripped.startsWith('```yui')) {
      inBlock = true;
      buffer = [];
      out.push(line);
    } else if (inBlock && stripped.startsWith('```')) {
      const code = buffer.join('\n');
      if (code.trim()) {
        try {
          out.push(convert(code, {
            from: sourceSyntax,
            to: targetSyntax,
            indentString: opts.indentString ?? '   ',
            functionLanguage: opts.functionLanguage,
          }));
        } catch (e) {
          out.push(`# Conversion error: ${e.message ?? e}`);
          out.push(code);
        }
      }
      out.push(line);
      inBlock = false;
    } else if (inBlock) {
      buffer.push(line);
    } else {
      out.push(line);
    }
  }
  return out.join('\n');
}

// ─────────────────────────────────────────────
// --interactive (REPL)
// ─────────────────────────────────────────────
/**
 * 対話モード。`>>> ` プロンプトで 1 行受け取り実行する。
 * 空行で最終スコープの環境を表示、`quit` / `exit` で終了。
 * Python 版の readline 履歴ファイル (~/.yui_history) は Node 側では省略。
 */
async function interactiveMode(opts) {
  const runtime = new YuiRuntime();
  runtime.interactive_mode = true;
  runtime.allow_binary_ops = opts.allowBinaryOps;

  // ファイルが指定されていれば先に読み込んで環境を構築する
  for (const file of opts.files) {
    try {
      const source = readFileSync(file, 'utf8');
      runtime.exec(source, opts.syntax, { evalMode: false });
    } catch (e) {
      if (e instanceof YuiError) {
        process.stderr.write(`${runtime.formatError(e, '| ')}\n`);
      } else {
        process.stderr.write(`cannot load ${file}: ${e.message ?? e}\n`);
      }
      return 1;
    }
  }

  process.stdout.write(`yuijs - Interactive Mode\nSyntax: ${opts.syntax}\nType 'quit' or 'exit' to exit\n\n`);

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: true,
    historySize: 1000,
    prompt: '>>> ',
  });

  return new Promise((resolve) => {
    rl.prompt();
    rl.on('line', (raw) => {
      const code = raw.trim();
      if (code === 'quit' || code === 'exit') {
        rl.close();
        return;
      }
      if (code === '') {
        // 空行で最終環境を表示
        const top = runtime.getTopEnv();
        if (top.size > 0) {
          const obj = Object.fromEntries(
            [...top].filter(([k]) => !k.startsWith('@')),
          );
          process.stdout.write(`${runtime.stringifyEnv(-1, '')}\n`);
          void obj; // kept for symmetry with Python JSON dump
        }
        rl.prompt();
        return;
      }
      try {
        runtime.exec(code, opts.syntax, { evalMode: false });
      } catch (e) {
        if (e instanceof YuiError) {
          process.stdout.write(`${runtime.formatError(e, '| ')}\n`);
        } else {
          process.stdout.write(`Error: ${e.message ?? e}\n`);
        }
      }
      rl.prompt();
    });
    rl.on('close', () => {
      process.stdout.write('\nExiting\n');
      resolve(0);
    });
    // Ctrl+C で終了
    rl.on('SIGINT', () => {
      process.stdout.write('\nExiting\n');
      rl.close();
    });
  });
}

// `node src/main.js ...` で直接呼ばれた場合のみ実行する。
const isEntry =
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url.endsWith(process.argv[1]);
if (isEntry) {
  main(process.argv.slice(2)).then((code) => process.exit(code));
}

export {
  main,
  parseArgs,
  passAt1Mode,
  bnfMode,
  listExamplesMode,
  listSyntaxMode,
  showExamplesMode,
  makeExamplesMode,
  testExamplesMode,
  findSyntaxMode,
  convertToMode,
  interactiveMode,
};
