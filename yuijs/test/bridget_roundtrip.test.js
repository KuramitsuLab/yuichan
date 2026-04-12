// bridget 構文 roundtrip テスト (Python 版 yuichan/syntax/test_bridget.py の移植)
// node --test test/bridget_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('bridget');
