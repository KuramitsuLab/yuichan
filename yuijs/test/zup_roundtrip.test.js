// zup 構文 roundtrip テスト (Python 版 yuichan/syntax/test_zup.py の移植)
// node --test test/zup_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('zup');
