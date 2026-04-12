// pylike 構文 roundtrip テスト (Python 版 yuichan/syntax/test_pylike.py の移植)
// node --test test/pylike_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('pylike');
