// yui 構文 roundtrip テスト (Python 版 yuichan/syntax/test_yui.py の移植)
// node --test test/yui_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('yui');
