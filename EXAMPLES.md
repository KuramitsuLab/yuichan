# Yui言語 サンプルコード集

Yui言語の主要な機能と書き方を理解するための実践的なサンプルコードです。

## 目次

1. [基礎編](#基礎編)
2. [制御構造](#制御構造)
3. [配列操作](#配列操作)
4. [文字列処理](#文字列処理)
5. [再帰アルゴリズム](#再帰アルゴリズム)
6. [探索アルゴリズム](#探索アルゴリズム)
7. [ソートアルゴリズム](#ソートアルゴリズム)
8. [数学的アルゴリズム](#数学的アルゴリズム)
9. [型変換と型判定](#型変換と型判定)
10. [ビット演算](#ビット演算)
11. [応用例](#応用例)

---

## 基礎編

### 1. Hello World (文字列の返却)

```yui
標準ライブラリを使う

hello = 入力なしに対し {
    "Hello, World!"が答え
}

>>> hello()
"Hello, World!"
```

### 2. 算術演算の基礎

```yui
標準ライブラリを使う

arithmetic = 入力 a, b に対し {
    sum = 和(a, b)
    diff = 差(a, b)
    prod = 積(a, b)
    quot = 商(a, b)
    rem = 剰余(a, b)

    result = []
    resultの末尾に sum を追加する
    resultの末尾に diff を追加する
    resultの末尾に prod を追加する
    resultの末尾に quot を追加する
    resultの末尾に rem を追加する

    resultが答え
}

>>> arithmetic(10, 3)
[13, 7, 30, 3, 1]
```

### 3. 絶対値の計算

```yui
標準ライブラリを使う

my_abs = 入力 x に対し {
    もし x が 0 より小さいならば、{
        差(0, x)が答え
    }
    そうでなければ {
        xが答え
    }
}

>>> my_abs(-5)
5
>>> my_abs(3)
3
```

---

## 制御構造

### 4. FizzBuzz

```yui
標準ライブラリを使う

fizzbuzz = 入力 n に対し {
    result = []
    i = 1

    n回、くり返す {
        mod3 = 剰余(i, 3)
        mod5 = 剰余(i, 5)

        もし mod3 が 0 ならば、{
            もし mod5 が 0 ならば、{
                resultの末尾に "FizzBuzz" を追加する
            }
            そうでなければ {
                resultの末尾に "Fizz" を追加する
            }
        }
        そうでなければ {
            もし mod5 が 0 ならば、{
                resultの末尾に "Buzz" を追加する
            }
            そうでなければ {
                resultの末尾に i を追加する
            }
        }

        iを増やす
    }

    resultが答え
}

>>> fizzbuzz(15)
[1, 2, "Fizz", 4, "Buzz", "Fizz", 7, 8, "Fizz", "Buzz", 11, "Fizz", 13, 14, "FizzBuzz"]
```

### 5. 最大値と最小値

```yui
標準ライブラリを使う

find_min_max = 入力 numbers に対し {
    length = |numbers|
    もし length が 0 ならば、{
        []が答え
    }

    min_val = numbers[0]
    max_val = numbers[0]

    i = 1
    times = 差(length, 1)
    times回、くり返す {
        current = numbers[i]
        もし current が min_val より小さいならば、{
            min_val = current
        }
        もし current が max_val より大きいならば、{
            max_val = current
        }
        iを増やす
    }

    result = []
    resultの末尾に min_val を追加する
    resultの末尾に max_val を追加する
    resultが答え
}

>>> find_min_max([3, 7, 2, 9, 1, 5])
[1, 9]
```

---

## 配列操作

### 6. 配列の反転

```yui
標準ライブラリを使う

reverse = 入力 array に対し {
    length = |array|
    result = []
    i = 0

    length回、くり返す {
        idx = 差(差(length, i), 1)
        resultの末尾に array[idx] を追加する
        iを増やす
    }

    resultが答え
}

>>> reverse([1, 2, 3, 4, 5])
[5, 4, 3, 2, 1]
```

### 7. 配列のフィルタリング（偶数のみ）

```yui
標準ライブラリを使う

filter_even = 入力 numbers に対し {
    length = |numbers|
    result = []
    i = 0

    length回、くり返す {
        num = numbers[i]
        remainder = 剰余(num, 2)
        もし remainder が 0 ならば、{
            resultの末尾に num を追加する
        }
        iを増やす
    }

    resultが答え
}

>>> filter_even([1, 2, 3, 4, 5, 6, 7, 8])
[2, 4, 6, 8]
```

### 8. 配列の合計

```yui
標準ライブラリを使う

array_sum = 入力 numbers に対し {
    length = |numbers|
    sum = 0
    i = 0

    length回、くり返す {
        sum = 和(sum, numbers[i])
        iを増やす
    }

    sumが答え
}

>>> array_sum([1, 2, 3, 4, 5])
15
```

### 9. 配列の連結

```yui
標準ライブラリを使う

concat = 入力 arr1, arr2 に対し {
    result = []

    len1 = |arr1|
    i = 0
    len1回、くり返す {
        resultの末尾に arr1[i] を追加する
        iを増やす
    }

    len2 = |arr2|
    i = 0
    len2回、くり返す {
        resultの末尾に arr2[i] を追加する
        iを増やす
    }

    resultが答え
}

>>> concat([1, 2, 3], [4, 5, 6])
[1, 2, 3, 4, 5, 6]
```

---

## 文字列処理

### 10. 文字列の長さ

```yui
標準ライブラリを使う

string_length = 入力 text に対し {
    |text|が答え
}

>>> string_length("Hello")
5
```

### 11. 文字列の連結

```yui
標準ライブラリを使う

string_concat = 入力 str1, str2 に対し {
    result = []

    len1 = |str1|
    i = 0
    len1回、くり返す {
        resultの末尾に str1[i] を追加する
        iを増やす
    }

    len2 = |str2|
    i = 0
    len2回、くり返す {
        resultの末尾に str2[i] を追加する
        iを増やす
    }

    resultが答え
}

>>> string_concat("Hello", "World")
"HelloWorld"
```

### 12. 回文判定

```yui
標準ライブラリを使う

is_palindrome = 入力 text に対し {
    length = |text|
    half = 商(length, 2)
    i = 0

    half回、くり返す {
        right_idx = 差(差(length, i), 1)
        もし text[i] が text[right_idx] 以外ならば、{
            0が答え
        }
        iを増やす
    }

    1が答え
}

>>> is_palindrome("racecar")
1
>>> is_palindrome("hello")
0
```

### 13. 文字カウント

```yui
標準ライブラリを使う

count_char = 入力 text, target に対し {
    target_code = target[0]
    length = |text|
    count = 0
    i = 0

    length回、くり返す {
        もし text[i] が target_code ならば、{
            countを増やす
        }
        iを増やす
    }

    countが答え
}

>>> count_char("hello world", "l")
3
```

### 14. 大文字を小文字に変換

```yui
標準ライブラリを使う

to_lower = 入力 text に対し {
    length = |text|
    result = []
    i = 0

    length回、くり返す {
        char = text[i]
        # 'A'(65) ~ 'Z'(90)
        もし char が 64 より大きいならば、{
            もし char が 91 より小さいならば、{
                # Convert to lowercase by adding 32
                char = 和(char, 32)
            }
        }
        resultの末尾に char を追加する
        iを増やす
    }

    resultが答え
}

>>> to_lower("Hello World")
"hello world"
```

---

## 再帰アルゴリズム

### 15. 階乗

```yui
標準ライブラリを使う

factorial = 入力 n に対し {
    もし n が 1 以下 ならば、{
        1が答え
    }
    そうでなければ {
        prev = 差(n, 1)
        積(n, factorial(prev))が答え
    }
}

>>> factorial(5)
120
>>> factorial(0)
1
```

### 16. フィボナッチ数列（再帰版）

```yui
標準ライブラリを使う

fib_recursive = 入力 n に対し {
    もし n が 0 ならば、{
        0が答え
    }
    もし n が 1 ならば、{
        1が答え
    }

    n1 = 差(n, 1)
    n2 = 差(n, 2)
    和(fib_recursive(n1), fib_recursive(n2))が答え
}

>>> fib_recursive(10)
55
```

### 17. フィボナッチ数列（反復版）

```yui
標準ライブラリを使う

fib_iterative = 入力 n に対し {
    もし n が 0 ならば、{
        0が答え
    }
    もし n が 1 ならば、{
        1が答え
    }

    a = 0
    b = 1
    i = 2
    times = 差(n, 1)
    times回、くり返す {
        temp = 和(a, b)
        a = b
        b = temp
        iを増やす
    }

    bが答え
}

>>> fib_iterative(10)
55
```

### 18. べき乗計算

```yui
標準ライブラリを使う

power = 入力 base, exp に対し {
    もし exp が 0 ならば、{
        1が答え
    }

    result = 1
    i = 0
    exp回、くり返す {
        result = 積(result, base)
        iを増やす
    }

    resultが答え
}

>>> power(2, 10)
1024
>>> power(3, 4)
81
```

---

## 探索アルゴリズム

### 19. 線形探索

```yui
標準ライブラリを使う

linear_search = 入力 array, target に対し {
    length = |array|
    i = 0

    length回、くり返す {
        もし array[i] が target ならば、{
            iが答え
        }
        iを増やす
    }

    -1が答え
}

>>> linear_search([3, 7, 2, 9, 1, 5], 9)
3
>>> linear_search([3, 7, 2, 9, 1, 5], 10)
-1
```

### 20. 二分探索（ソート済み配列）

```yui
標準ライブラリを使う

binary_search = 入力 array, target に対し {
    left = 0
    right = 差(|array|, 1)

    100回、くり返す {
        もし left が right より大きいならば、{
            -1が答え
        }

        mid = 商(和(left, right), 2)
        mid_val = array[mid]

        もし mid_val が target ならば、{
            midが答え
        }
        そうでなければ {
            もし mid_val が target より小さいならば、{
                left = 和(mid, 1)
            }
            そうでなければ {
                right = 差(mid, 1)
            }
        }
    }

    -1が答え
}

>>> binary_search([1, 2, 3, 5, 7, 9], 5)
3
>>> binary_search([1, 2, 3, 5, 7, 9], 4)
-1
```

---

## ソートアルゴリズム

### 21. バブルソート

```yui
標準ライブラリを使う

bubble_sort = 入力 array に対し {
    length = |array|
    result = []

    # Copy array
    i = 0
    length回、くり返す {
        resultの末尾に array[i] を追加する
        iを増やす
    }

    # Bubble sort
    i = 0
    length回、くり返す {
        j = 0
        limit = 差(差(length, i), 1)
        limit回、くり返す {
            next_j = 和(j, 1)
            もし result[j] が result[next_j] より大きいならば、{
                temp = result[j]
                result[j] = result[next_j]
                result[next_j] = temp
            }
            jを増やす
        }
        iを増やす
    }

    resultが答え
}

>>> bubble_sort([5, 2, 8, 1, 9, 3])
[1, 2, 3, 5, 8, 9]
```

### 22. 選択ソート

```yui
標準ライブラリを使う

selection_sort = 入力 array に対し {
    length = |array|
    result = []

    # Copy array
    i = 0
    length回、くり返す {
        resultの末尾に array[i] を追加する
        iを増やす
    }

    # Selection sort
    i = 0
    length回、くり返す {
        min_idx = i
        j = 和(i, 1)
        remaining = 差(length, i)
        remaining回、くり返す {
            もし j が length より小さいならば、{
                もし result[j] が result[min_idx] より小さいならば、{
                    min_idx = j
                }
            }
            jを増やす
        }

        # Swap
        もし min_idx が i 以外ならば、{
            temp = result[i]
            result[i] = result[min_idx]
            result[min_idx] = temp
        }

        iを増やす
    }

    resultが答え
}

>>> selection_sort([5, 2, 8, 1, 9, 3])
[1, 2, 3, 5, 8, 9]
```

---

## 数学的アルゴリズム

### 23. 最大公約数 (GCD)

```yui
標準ライブラリを使う

gcd = 入力 a, b に対し {
    もし b が 0 ならば、{
        aが答え
    }
    remainder = 剰余(a, b)
    gcd(b, remainder)が答え
}

>>> gcd(48, 18)
6
>>> gcd(100, 35)
5
```

### 24. 最小公倍数 (LCM)

```yui
標準ライブラリを使う

gcd = 入力 a, b に対し {
    もし b が 0 ならば、{
        aが答え
    }
    remainder = 剰余(a, b)
    gcd(b, remainder)が答え
}

lcm = 入力 a, b に対し {
    gcd_val = gcd(a, b)
    商(積(a, b), gcd_val)が答え
}

>>> lcm(12, 18)
36
>>> lcm(7, 5)
35
```

### 25. 素数判定

```yui
標準ライブラリを使う

is_prime = 入力 n に対し {
    もし n が 2 より小さいならば、{
        0が答え
    }
    もし n が 2 ならば、{
        1が答え
    }

    # Check divisibility from 2 to sqrt(n)
    i = 2
    limit = n
    limit回、くり返す {
        もし 積(i, i) が n より大きいならば、{
            くり返しを抜ける
        }

        remainder = 剰余(n, i)
        もし remainder が 0 ならば、{
            0が答え
        }

        iを増やす
    }

    1が答え
}

>>> is_prime(17)
1
>>> is_prime(18)
0
>>> is_prime(2)
1
```

### 26. 素因数分解

```yui
標準ライブラリを使う

prime_factors = 入力 n に対し {
    result = []
    factor = 2

    1000回、くり返す {
        もし n が 1 ならば、{
            くり返しを抜ける
        }

        remainder = 剰余(n, factor)
        もし remainder が 0 ならば、{
            resultの末尾に factor を追加する
            n = 商(n, factor)
        }
        そうでなければ {
            factorを増やす
        }
    }

    resultが答え
}

>>> prime_factors(60)
[2, 2, 3, 5]
>>> prime_factors(17)
[17]
```

---

## 型変換と型判定

### 27. 型判定の例

```yui
標準ライブラリを使う

get_type = 入力 value に対し {
    is_int = 整数判定(value)
    もし is_int が 1 ならば、{
        "integer"が答え
    }

    is_float = 小数判定(value)
    もし is_float が 1 ならば、{
        "float"が答え
    }

    is_str = 文字列判定(value)
    もし is_str が 1 ならば、{
        "string"が答え
    }

    "unknown"が答え
}

>>> get_type(42)
"integer"
>>> get_type(3.14)
"float"
>>> get_type("hello")
"string"
```

### 28. 型変換の例

```yui
標準ライブラリを使う

convert_types = 入力 value に対し {
    as_int = 整数化(value)
    as_float = 小数化(value)
    as_str = 文字列化(value)

    result = []
    resultの末尾に as_int を追加する
    resultの末尾に as_float を追加する
    resultの末尾に as_str を追加する

    resultが答え
}

>>> convert_types(42)
[42, 42.0, "42"]
```

---

## ビット演算

### 29. ビット演算の基礎

```yui
標準ライブラリを使う

bit_operations = 入力 a, b に対し {
    and_result = 論理積(a, b)
    or_result = 論理和(a, b)
    xor_result = 排他的論理和(a, b)
    not_a = ビット反転(a)
    left = 左シフト(a, 2)
    right = 右シフト(a, 2)

    result = []
    resultの末尾に and_result を追加する
    resultの末尾に or_result を追加する
    resultの末尾に xor_result を追加する
    resultの末尾に 剰余(not_a, 256) を追加する
    resultの末尾に left を追加する
    resultの末尾に right を追加する

    resultが答え
}

>>> bit_operations(12, 10)
[8, 14, 6, 243, 48, 3]
```

### 30. ビットカウント（1の個数）

```yui
標準ライブラリを使う

count_bits = 入力 n に対し {
    count = 0
    i = 0

    32回、くり返す {
        bit = 論理積(n, 1)
        もし bit が 1 ならば、{
            countを増やす
        }
        n = 右シフト(n, 1)
        iを増やす
    }

    countが答え
}

>>> count_bits(7)
3
>>> count_bits(15)
4
```

### 31. 2の累乗判定

```yui
標準ライブラリを使う

is_power_of_two = 入力 n に対し {
    もし n が 0 以下 ならば、{
        0が答え
    }

    # n & (n-1) should be 0 for powers of 2
    n_minus_1 = 差(n, 1)
    result = 論理積(n, n_minus_1)

    もし result が 0 ならば、{
        1が答え
    }
    そうでなければ {
        0が答え
    }
}

>>> is_power_of_two(16)
1
>>> is_power_of_two(15)
0
>>> is_power_of_two(1)
1
```

---

## 応用例

### 32. パスカルの三角形

```yui
標準ライブラリを使う

pascal_triangle = 入力 n に対し {
    result = []

    row_num = 0
    n回、くり返す {
        row = []

        col = 0
        row_len = 和(row_num, 1)
        row_len回、くり返す {
            もし col が 0 ならば、{
                rowの末尾に 1 を追加する
            }
            そうでなければ {
                もし col が row_num ならば、{
                    rowの末尾に 1 を追加する
                }
                そうでなければ {
                    prev_row = result[差(row_num, 1)]
                    left = prev_row[差(col, 1)]
                    right = prev_row[col]
                    sum = 和(left, right)
                    rowの末尾に sum を追加する
                }
            }
            colを増やす
        }

        resultの末尾に row を追加する
        row_numを増やす
    }

    resultが答え
}

>>> pascal_triangle(5)
[[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]
```

### 33. ハノイの塔（移動回数）

```yui
標準ライブラリを使う

hanoi_moves = 入力 n に対し {
    もし n が 1 ならば、{
        1が答え
    }

    # 2^n - 1
    result = 1
    i = 0
    n回、くり返す {
        result = 積(result, 2)
        iを増やす
    }

    差(result, 1)が答え
}

>>> hanoi_moves(3)
7
>>> hanoi_moves(4)
15
```

### 34. 配列の回転

```yui
標準ライブラリを使う

rotate_array = 入力 array, k に対し {
    length = |array|
    もし length が 0 ならば、{
        []が答え
    }

    # Normalize k
    k = 剰余(k, length)
    result = []

    # Add elements from k to end
    i = k
    times = 差(length, k)
    times回、くり返す {
        resultの末尾に array[i] を追加する
        iを増やす
    }

    # Add elements from start to k
    i = 0
    k回、くり返す {
        resultの末尾に array[i] を追加する
        iを増やす
    }

    resultが答え
}

>>> rotate_array([1, 2, 3, 4, 5], 2)
[3, 4, 5, 1, 2]
```

### 35. ランレングス符号化

```yui
標準ライブラリを使う

run_length_encode = 入力 text に対し {
    length = |text|
    もし length が 0 ならば、{
        []が答え
    }

    result = []
    current_char = text[0]
    count = 1
    i = 1

    times = 差(length, 1)
    times回、くり返す {
        もし text[i] が current_char ならば、{
            countを増やす
        }
        そうでなければ {
            resultの末尾に current_char を追加する
            resultの末尾に count を追加する
            current_char = text[i]
            count = 1
        }
        iを増やす
    }

    # Add last group
    resultの末尾に current_char を追加する
    resultの末尾に count を追加する

    resultが答え
}

>>> run_length_encode("aaabbcccc")
[97, 3, 98, 2, 99, 4]
```

### 36. 数値を文字列に変換

```yui
標準ライブラリを使う

number_to_string = 入力 n に対し {
    もし n が 0 ならば、{
        [48]が答え
    }

    # Handle negative
    is_negative = 0
    もし n が 0 より小さいならば、{
        is_negative = 1
        n = 差(0, n)
    }

    digits = []
    100回、くり返す {
        もし n が 0 ならば、{
            くり返しを抜ける
        }

        digit = 剰余(n, 10)
        digit_char = 和(48, digit)
        digitsの末尾に digit_char を追加する
        n = 商(n, 10)
    }

    # Reverse digits
    result = []
    もし is_negative が 1 ならば、{
        resultの末尾に 45 を追加する  # '-'
    }

    len = |digits|
    i = 0
    len回、くり返す {
        idx = 差(差(len, i), 1)
        resultの末尾に digits[idx] を追加する
        iを増やす
    }

    resultが答え
}

>>> number_to_string(12345)
"12345"
>>> number_to_string(-42)
"-42"
>>> number_to_string(0)
"0"
```

---

## まとめ

このサンプル集では以下の機能をカバーしています:

1. **基本構文**: 関数定義、条件分岐、ループ
2. **配列操作**: 反転、フィルタ、連結、合計
3. **文字列処理**: 連結、回文判定、文字カウント、大小変換
4. **再帰**: 階乗、フィボナッチ、GCD
5. **探索**: 線形探索、二分探索
6. **ソート**: バブルソート、選択ソート
7. **数学**: 素数判定、素因数分解、べき乗
8. **型システム**: 型判定、型変換
9. **ビット演算**: AND/OR/XOR/NOT、シフト、ビットカウント
10. **応用**: パスカルの三角形、配列回転、ランレングス符号化

すべてのサンプルコードは実行可能で、テストケースが含まれています。
