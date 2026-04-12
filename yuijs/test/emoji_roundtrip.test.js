// emoji 構文 roundtrip テスト (Python 版 yuichan/syntax/test_emoji.py の移植)
// node --test test/emoji_roundtrip.test.js

import { registerRoundtripTests } from './fixtures/roundtrip_helper.js';

registerRoundtripTests('emoji');
