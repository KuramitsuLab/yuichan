// wenyan 構文 roundtrip テスト (Python 版 yuichan/syntax/test_wenyan.py の移植)
// node --test test/wenyan_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('wenyan');
