// nannan 構文 roundtrip テスト (Python 版 yuichan/syntax/test_nannan.py の移植)
// node --test test/nannan_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('nannan');
