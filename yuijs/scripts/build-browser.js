#!/usr/bin/env node
// scripts/build-browser.js
//
// yuijs を esbuild でブラウザ向け IIFE バンドルにまとめる。
// 出力先: ../webapp/yui_bundle.js
//
// グローバル名 `YuiEditor` で公開 API がすべて参照可能になる。
// ビルド後、参照する HTML の <script src="yui_bundle.js?v=..."> を
// package.json の version に合わせて書き換える (キャッシュバスティング)。
//
// 使い方: node scripts/build-browser.js

import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const __dirname  = dirname(fileURLToPath(import.meta.url));
const entry      = resolve(__dirname, '../src/index.js');
const outfile    = resolve(__dirname, '../../webapp/yui_bundle.js');
const pkgPath    = resolve(__dirname, '../package.json');
const tomlPath   = resolve(__dirname, '../../pyproject.toml');
const webappDir  = resolve(__dirname, '../../webapp');

// pyproject.toml がバージョンの正典。package.json はそれに追従させる。
const tomlText = readFileSync(tomlPath, 'utf8');
const tomlMatch = tomlText.match(/^version\s*=\s*"([^"]+)"/m);
if (!tomlMatch) {
  throw new Error(`Could not find version in ${tomlPath}`);
}
const version = tomlMatch[1];

const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
if (pkg.version !== version) {
  const oldVersion = pkg.version;
  pkg.version = version;
  writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
  console.log(`✏️  Updated package.json version: ${oldVersion} → ${version}`);
}

execSync(
  `npx esbuild "${entry}" --bundle --format=iife --global-name=YuiEditor --outfile="${outfile}" --charset=utf8`,
  { stdio: 'inherit' },
);

// yui_bundle.js を参照する HTML を更新
const htmlFiles = ['kogi.html'];
const scriptRe = /(<script\s+src=")yui_bundle\.js(?:\?v=[^"]*)?(")/g;

for (const name of htmlFiles) {
  const path = resolve(webappDir, name);
  if (!existsSync(path)) continue;
  const before = readFileSync(path, 'utf8');
  const after  = before.replace(scriptRe, `$1yui_bundle.js?v=${version}$2`);
  if (before !== after) {
    writeFileSync(path, after);
    console.log(`✏️  Updated ${name} → yui_bundle.js?v=${version}`);
  }
}

console.log(`\n✅ Bundle written to ${outfile} (v${version})`);
