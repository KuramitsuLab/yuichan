// yuierror.js — error class and messages (port of yuichan/yuierror.py)

import { ASTNode } from './yuiast.js';

// ─────────────────────────────────────────────
// Verbose logging
// ─────────────────────────────────────────────
let _verbose = true;

export function setVerbose(flag) {
    _verbose = flag;
}

/** verbose モード時だけ stderr (Node.js) / console.error (browser) に出力する */
export function vprint(...args) {
    if (_verbose) {
        console.error(...args);
    }
}

// ─────────────────────────────────────────────
// エラーメッセージ辞書
// ─────────────────────────────────────────────
export const ERROR_MESSAGES = {
    // パーサーエラー
    'expected-token':           'トークンが不正です',
    'expected-number':          '数値が必要です',
    'expected-string':          '文字列が必要です',
    'expected-array':           '配列が必要です',
    'expected-object':          'オブジェクトが必要です',
    'expected-boolean':         '真偽値が必要です',
    'expected-closing':         '閉じ括弧が必要です',
    'expected-variable':        '変数が必要です',
    'frequent-mistake':         'よくある間違いです',
    'wrong-name':               '名前が不正です',
    'wrong-statement':          '不正な文です',
    'wrong-escape-sequence':    '不正なエスケープシーケンスです',
    'wrong-indent-level':       'インデントが不正です',
    // ランタイムエラー
    'undefined-variable':       '変数が未定義です',
    'undefined-function':       '関数が未定義です',
    'type-error':               '型エラーです',
    'division-by-zero':         'ゼロ除算です',
    'error-index':              'インデックスエラーです',
    'error-value':              '値エラーです',
    'too-many-recursion':      '再帰が深すぎます',
    'runtime-timeout':          'タイムアウトです',
    'unsupported-operator':     'サポートされていない演算子です',
    'imcomparable':   'サポートされていない比較です',
    'mismatch-argument': '引数の数が合いません',
    'not-negative-number':      '負の数は使えません',
    'float-conversion':         '少数への変換エラーです',
    'internal-error':           '内部エラーです',
    'immutable':                '変更できません',
    'array-format':             '配列フォーマットエラーです',
};

export function formatMessages(messages) {
    /** 先頭キーを ERROR_MESSAGES で置き換えて表示用文字列を返す */
    if (!messages || messages.length === 0) return '';
    const key = messages[0];
    const display = ERROR_MESSAGES[key] ?? key;
    const rest = messages.slice(1).join(' ');
    return rest ? `${display} ${rest}` : display;
}

function normalizeMessages(messages) {
    /** 非絵文字の連続する文字列を '-' で結合する。絵文字（codePoint > 127）で始まる文字列は独立要素として残す。 */
    const result = [];
    let parts = [];
    for (const msg of messages) {
        if (msg && msg.codePointAt(0) > 127) {
            if (parts.length > 0) { result.push(parts.join('-')); parts = []; }
            result.push(msg);
        } else {
            parts.push(msg);
        }
    }
    if (parts.length > 0) result.push(parts.join('-'));
    return result;
}

export class YuiError extends Error {
    constructor(messages, errorNode = null, BK = false) {
        const raw = Array.isArray(messages) ? messages : [String(messages)];
        const normalized = normalizeMessages(raw);
        super(normalized.join(' '));
        this.messages = normalized;
        this.errorNode = (errorNode instanceof ASTNode) ? errorNode : null;
        this.BK = BK;
        this.name = 'YuiError';
    }

    get lineno() {
        if (this.errorNode) {
            const [line] = this.errorNode.extract();
            return line;
        }
        return 0;
    }

    get offset() {
        if (this.errorNode) {
            const [, offset] = this.errorNode.extract();
            return offset;
        }
        return 0;
    }

    get text() {
        if (this.errorNode) {
            const [,, snippet] = this.errorNode.extract();
            return snippet;
        }
        return '';
    }

    formattedMessage(prefix = ' ', marker = '^', lineoffset = 0) {
        /** 構文エラーとして整形したメッセージを返す。ランタイムエラーは YuiRuntime.formatError() を使うこと。 */
        let message = formatMessages(this.messages);
        if (this.errorNode) {
            const [line, col, snippet] = this.errorNode.extract();
            const length = Math.max(
                this.errorNode.endPos != null ? this.errorNode.endPos - this.errorNode.pos : 3,
                3
            );
            const makePointer = marker.repeat(Math.min(length, 16));
            const firstLine = snippet.split('\n')[0];
            const indent = ' '.repeat(col - 1);
            message = `${message} line ${line + lineoffset}, column ${col}:\n${prefix}${firstLine}\n${prefix}${indent}${makePointer}`;
        }
        return `[構文エラー/SyntaxError] ${message}`;
    }
}
