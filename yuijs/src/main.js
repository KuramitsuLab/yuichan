#!/usr/bin/env node
// main.js — 簡易 CLI
//
// Yui の主要なターゲットは Web アプリへの埋め込みなので、このファイルは
// 「Node 上でファイルを実行したい」最小ユースケースだけをカバーする:
//
//   node src/main.js [--syntax NAME] [--allow-binary-ops] [--syntax-list] <file>
//   cat file.yui | node src/main.js [--syntax NAME]
//
// REPL / --pass@1 / --convert-to / --make-examples などの Python 版の高度な
// モードは実装しない。必要に応じて `import { run, convert } from 'yuijs'` を
// 直接使えば同等の処理が書ける。

import { readFileSync } from 'node:fs';
import process from 'node:process';

import { run } from './index.js';
import { YuiError, formatMessages } from './yuierror.js';
import { listSyntaxNames } from './yuisyntax.js';

const USAGE = `Usage:
  node src/main.js [options] <file.yui>
  cat file.yui | node src/main.js [options]

Options:
  --syntax NAME        syntax name (default: yui)
  --allow-binary-ops   enable +/-/*/// operators
  --syntax-list        list available syntax names and exit
  -h, --help           show this help and exit
`;

function parseArgs(argv) {
  const opts = {
    syntax: 'yui',
    allowBinaryOps: false,
    syntaxList: false,
    help: false,
    file: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '-h' || arg === '--help') {
      opts.help = true;
    } else if (arg === '--syntax') {
      opts.syntax = argv[++i];
      if (opts.syntax == null) {
        throw new Error('--syntax requires a value');
      }
    } else if (arg.startsWith('--syntax=')) {
      opts.syntax = arg.slice('--syntax='.length);
    } else if (arg === '--allow-binary-ops') {
      opts.allowBinaryOps = true;
    } else if (arg === '--syntax-list') {
      opts.syntaxList = true;
    } else if (arg.startsWith('-')) {
      throw new Error(`unknown option: ${arg}`);
    } else {
      if (opts.file != null) {
        throw new Error(`multiple files not supported: ${arg}`);
      }
      opts.file = arg;
    }
  }
  return opts;
}

function readStdinSync() {
  // Node で stdin を同期読みする簡易ヘルパ。
  // stdin が tty なら空文字列を返す。
  if (process.stdin.isTTY) return '';
  try {
    return readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function main(argv) {
  let opts;
  try {
    opts = parseArgs(argv);
  } catch (e) {
    process.stderr.write(`${e.message}\n\n${USAGE}`);
    return 2;
  }

  if (opts.help) {
    process.stdout.write(USAGE);
    return 0;
  }

  if (opts.syntaxList) {
    const names = listSyntaxNames();
    for (const name of names) {
      process.stdout.write(`${name}\n`);
    }
    return 0;
  }

  let source;
  if (opts.file) {
    try {
      source = readFileSync(opts.file, 'utf8');
    } catch (e) {
      process.stderr.write(`cannot read file ${opts.file}: ${e.message}\n`);
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
    // eval mode の結果を出力 (null なら何もしない)
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

// `node src/main.js ...` で直接呼ばれた場合のみ実行する。
// 他モジュールから import されたときは副作用なし。
const isEntry =
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url.endsWith(process.argv[1]);
if (isEntry) {
  process.exit(main(process.argv.slice(2)));
}

export { main, parseArgs };
