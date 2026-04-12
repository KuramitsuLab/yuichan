// sexpr 構文 roundtrip テスト (Python 版 yuichan/syntax/test_sexpr.py の移植)
// node --test test/sexpr_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('sexpr');
