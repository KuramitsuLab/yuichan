// jslike 構文 roundtrip テスト (Python 版 yuichan/syntax/test_jslike.py の移植)
// node --test test/jslike_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('jslike');
