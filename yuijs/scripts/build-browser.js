#!/usr/bin/env node
// scripts/build-browser.js
//
// yuijs を esbuild でブラウザ向け IIFE バンドルにまとめる。
// 出力先: ../webapp/yui_bundle.js
//
// グローバル名 `YuiEditor` で公開 API がすべて参照可能になる。
//
// 使い方: node scripts/build-browser.js

import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const entry = resolve(__dirname, '../src/index.js');
const outfile = resolve(__dirname, '../../webapp/yui_bundle.js');

execSync(
  `npx esbuild "${entry}" --bundle --format=iife --global-name=YuiEditor --outfile="${outfile}" --charset=utf8`,
  { stdio: 'inherit' },
);

console.log(`\n✅ Bundle written to ${outfile}`);
