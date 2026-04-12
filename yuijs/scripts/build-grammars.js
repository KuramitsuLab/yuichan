#!/usr/bin/env node
// scripts/build-grammars.js
//
// syntax/*.json を読んで src/yuigrammars.js を生成する。
// yuijs をブラウザ / Web アプリに埋め込むとき、fs アクセスを避けるために
// すべての組み込み grammar を 1 個の JS モジュールにインライン化する。
//
// 使い方: `node scripts/build-grammars.js`
//   (syntax/*.json を追加・編集したら再実行する)

import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..');
const SYNTAX_DIR = join(ROOT, 'syntax');
const OUT_FILE = join(ROOT, 'src', 'yuigrammars.js');

function main() {
  const files = readdirSync(SYNTAX_DIR)
    .filter((f) => f.endsWith('.json'))
    .sort();

  const grammars = {};
  for (const file of files) {
    const name = file.slice(0, -5); // drop .json
    const text = readFileSync(join(SYNTAX_DIR, file), 'utf-8');
    const parsed = JSON.parse(text); // validate JSON
    grammars[name] = parsed;
  }

  const header = `// yuigrammars.js — 組み込み構文 JSON をインライン化した辞書
//
// **自動生成ファイル** — 直接編集しないこと。
// syntax/*.json を更新したあと \`node scripts/build-grammars.js\` を実行して再生成する。
//
// Web アプリ埋め込み時に fs アクセスを避けるため、すべての組み込み grammar を
// 1 つの JS モジュールにインラインで持つ。外部 URL の grammar は
// \`loadSyntaxFromUrl(url)\` で非同期ロードする (yuisyntax.js 参照)。

`;

  const entries = Object.entries(grammars);
  const body =
    '/** 組み込み grammar 辞書 ({name: terminals}) */\n' +
    'export const GRAMMARS = Object.freeze({\n' +
    entries
      .map(
        ([name, terminals]) =>
          `  ${JSON.stringify(name)}: ${JSON.stringify(terminals, null, 2)
            .split('\n')
            .join('\n  ')},`,
      )
      .join('\n') +
    '\n});\n\n';

  const names = entries.map(([name]) => name);
  const namesExport =
    '/** 組み込み grammar 名の一覧 (ソート済み) */\n' +
    `export const SYNTAX_NAMES = Object.freeze(${JSON.stringify(names)});\n\n`;

  const getter = `/** 名前から grammar を取得 (見つからなければ null を返す) */
export function getGrammar(name) {
  return GRAMMARS[name] ?? null;
}
`;

  const out = header + body + namesExport + getter;
  writeFileSync(OUT_FILE, out, 'utf-8');
  const kb = (out.length / 1024).toFixed(1);
  process.stdout.write(
    `Generated ${OUT_FILE} (${entries.length} grammars, ${kb} KB)\n`,
  );
}

main();
