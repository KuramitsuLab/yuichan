// test_x_roundtrip.js — roundtrip tests: generate code from AST via CodingVisitor,
// execute via YuiRuntime.exec(), verify result matches expected value.
// Port of test_x_yui.py, test_x_pylike.py, test_x_sexpr.py

import { describe, test, expect } from 'vitest';
import { testcases, initRuntime } from './test_ast.js';
import { CodingVisitor } from '../src/yuicoding.js';
import { BlockNode } from '../src/yuiast.js';
import { types, YuiError } from '../src/yuitypes.js';
import { YuiBreakException, YuiReturnException } from '../src/yuiruntime.js';

// ─────────────────────────────────────────────
// Core helper
// ─────────────────────────────────────────────

function runRoundtrip(syntaxName, name) {
    const [node, expected] = testcases[name];
    if (node instanceof BlockNode) {
        node.topLevel = true;
    }

    const visitor = new CodingVisitor(syntaxName);
    const code = visitor.emit(node);

    const runtime = initRuntime();
    try {
        const result = runtime.exec(code, syntaxName);
        if (expected && expected.__env__) {
            expect(types.unbox(runtime.getenv(expected.key))).toEqual(expected.value);
        } else {
            expect(result).toEqual(expected);
        }
    } catch (e) {
        let msg;
        if (e instanceof YuiError) {
            msg = `💣${e.messages[0]}`;
        } else if (e instanceof YuiBreakException) {
            msg = '💣unexpected-break';
        } else if (e instanceof YuiReturnException) {
            msg = '💣unexpected-return';
        } else {
            throw e;
        }
        expect(msg).toBe(expected);
    }
}

// ─────────────────────────────────────────────
// Roundtrip tests for each syntax
// ─────────────────────────────────────────────

describe('roundtrip yui', () => {
    test.each(Object.keys(testcases))('%s', (name) => {
        runRoundtrip('yui', name);
    });
});

describe('roundtrip pylike', () => {
    test.each(Object.keys(testcases))('%s', (name) => {
        runRoundtrip('pylike', name);
    });
});

describe('roundtrip sexpr', () => {
    test.each(Object.keys(testcases))('%s', (name) => {
        runRoundtrip('sexpr', name);
    });
});

describe('roundtrip bridget', () => {
    test.each(Object.keys(testcases))('%s', (name) => {
        runRoundtrip('bridget', name);
    });
});
