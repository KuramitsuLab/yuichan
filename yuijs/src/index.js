// index.js — public API for yuijs (browser-compatible)
// Replaces main.py for web use

import { YuiRuntime, YuiBreakException, YuiReturnException,
         YuiFunction, LocalFunctionV, NativeFunction } from './yuiruntime.js';
import { YuiParser } from './yuiparser.js';
import { CodingVisitor } from './yuicoding.js';
import { YuiValue, YuiType, YuiError,
         YuiNullType, YuiBooleanType, YuiIntType, YuiFloatType,
         YuiStringType, YuiArrayType, YuiObjectType,
         OPERATORS, TYPES } from './yuitypes.js';
import { loadSyntax, YuiSyntax } from './yuisyntax.js';
import { setVerbose, vprint } from './yuierror.js';

export * from './yuiast.js';
export { YuiValue, YuiType, YuiError, YuiNullType, YuiBooleanType,
         YuiIntType, YuiFloatType, YuiStringType, YuiArrayType,
         YuiObjectType, OPERATORS, TYPES };
export { YuiRuntime, YuiBreakException, YuiReturnException,
         YuiFunction, LocalFunctionV, NativeFunction };
export { YuiParser };
export { CodingVisitor };
export { loadSyntax, YuiSyntax };
export { setVerbose, vprint };

/**
 * High-level Yui language API for browser use.
 * Replaces the CLI main.py.
 */
export class Yui {
    constructor(syntax = 'yui') {
        this.syntax = syntax;
        this.runtime = new YuiRuntime();
    }

    exec(source) {
        return this.runtime.exec(source, this.syntax);
    }

    reset() {
        this.runtime = new YuiRuntime();
    }

    get testPassed() { return this.runtime.testPassed; }
    get testFailed() { return this.runtime.testFailed; }
}
