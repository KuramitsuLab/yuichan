// test_example.js — tests for yuiexample.js
import { describe, test, expect } from 'vitest';
import { YuiRuntime } from '../src/yuiruntime.js';
import {
    getAllExamples,
    exampleHelloWorld,
    exampleVariables,
    exampleLoop,
    exampleFizzBuzz,
    exampleNestedConditionalBranches,
    exampleArithmetic,
    exampleComparisons,
    exampleArray,
    exampleStrings,
    exampleObjects,
    exampleFunction,
    exampleFunctionNoArgument,
    exampleFunctionWithoutReturn,
    exampleRecursiveFunction,
    exampleFloatAdd,
    exampleMonteCarlo,
    exampleNullAssignment,
    exampleBooleanAssignment,
    exampleBooleanBranch,
    exampleNullCheck,
} from '../src/yuiexample.js';

// Helper: generate Yui code from example and execute it
function runExample(example, syntax = 'yui') {
    const code = example.generate(syntax);
    const rt = new YuiRuntime();
    rt.exec(code, syntax, 30, false);
    return rt;
}

describe('YuiExample metadata', () => {
    test('getAllExamples returns 20 examples', () => {
        expect(getAllExamples()).toHaveLength(20);
    });

    test('each example has name, description, and astNode', () => {
        for (const ex of getAllExamples()) {
            expect(typeof ex.name).toBe('string');
            expect(typeof ex.description).toBe('string');
            expect(ex.astNode).toBeDefined();
        }
    });

    test('generate() returns non-empty string', () => {
        for (const ex of getAllExamples()) {
            const code = ex.generate('yui');
            expect(typeof code).toBe('string');
            expect(code.length).toBeGreaterThan(0);
        }
    });
});

describe('example execution', () => {
    test('hello_world — generates and executes without error', () => {
        // PrintExpressionNode just logs; no assertions in this example
        expect(() => runExample(exampleHelloWorld())).not.toThrow();
    });

    test('variables — x=2, y=-3', () => {
        const rt = runExample(exampleVariables());
        expect(rt.testPassed).toHaveLength(2);
    });

    test('loop — count=5 after breaking at 5', () => {
        const rt = runExample(exampleLoop());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('fizzbuzz — 100 items, Fizz/Buzz/FizzBuzz at correct positions', () => {
        const rt = runExample(exampleFizzBuzz());
        expect(rt.testPassed).toHaveLength(4);
    });

    test('nested_conditional_branches — y incremented', () => {
        const rt = runExample(exampleNestedConditionalBranches());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('comparisons — y=3, z=3', () => {
        const rt = runExample(exampleComparisons());
        expect(rt.testPassed).toHaveLength(2);
    });

    test('array — creation and manipulation', () => {
        const rt = runExample(exampleArray());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('strings — "hello" → "Hello world"', () => {
        const rt = runExample(exampleStrings());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('objects — x=1, y=2', () => {
        const rt = runExample(exampleObjects());
        expect(rt.testPassed).toHaveLength(2);
    });

    test('function — succ(0)=1', () => {
        const rt = runExample(exampleFunction());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('function_no_argument — zero()=0', () => {
        const rt = runExample(exampleFunctionNoArgument());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('function_without_return — point returns local env', () => {
        const rt = runExample(exampleFunctionWithoutReturn());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('recursive_function — fact(0)=1, fact(5)=120', () => {
        const rt = runExample(exampleRecursiveFunction());
        expect(rt.testPassed).toHaveLength(2);
    });

    test('float_add — digit-array addition with carry', () => {
        const rt = runExample(exampleFloatAdd());
        expect(rt.testPassed).toHaveLength(8);
    });

    test('arithmetic — add/subtract/multiply/divide/modulo', () => {
        const rt = runExample(exampleArithmetic());
        expect(rt.testPassed).toHaveLength(10);
    });

    test('null_assignment — x=null', () => {
        const rt = runExample(exampleNullAssignment());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('boolean_assignment — t=true, f=false', () => {
        const rt = runExample(exampleBooleanAssignment());
        expect(rt.testPassed).toHaveLength(2);
    });

    test('boolean_branch — result=1 when flag=true', () => {
        const rt = runExample(exampleBooleanBranch());
        expect(rt.testPassed).toHaveLength(1);
    });

    test('monte_carlo — executes without error and returns a float', () => {
        const rt = runExample(exampleMonteCarlo());
        // result is non-deterministic; just verify it runs cleanly
        expect(rt.testPassed).toHaveLength(0);
    });

    test('null_check — is_null(null)=true, is_null(0)=false', () => {
        const rt = runExample(exampleNullCheck());
        expect(rt.testPassed).toHaveLength(3);
    });
});

describe('generate for multiple syntaxes', () => {
    test('pylike syntax generates different code than yui', () => {
        const ex = exampleVariables();
        const yui = ex.generate('yui');
        const pylike = ex.generate('pylike');
        expect(yui).not.toBe(pylike);
    });

    test('pylike code executes correctly', () => {
        const ex = exampleVariables();
        const rt = runExample(ex, 'pylike');
        expect(rt.testPassed).toHaveLength(2);
    });
});
