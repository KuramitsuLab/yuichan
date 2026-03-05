# Standard Library API

Each function can be called by any of its three names: **emoji**, **Japanese**, or **English**.

```
📏(x)  ≡  絶対値(x)  ≡  abs(x)
```

To load the standard library, add the following line to your program:

```
use standard library
```

---

## Math

### `📏` / `絶対値` / `abs`
Returns the absolute value of a number.

| | |
|---|---|
| Arguments | `x` — int or float |
| Returns | int or float |

```
abs(-5)     → 5
abs(-2.5)   → 2.5
```

---

### `🧮` / `和` / `sum`
Returns the sum of all arguments. If any argument is a float, the result is a float.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
sum(1, 2, 3)       → 6
sum(1, 2.5)        → 3.5
sum(1, 2, 3, 4)    → 10
```

---

### `➖` / `差` / `diff`
Subtracts subsequent arguments from the first.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
diff(10, 3)        → 7
diff(10, 3, 2)     → 5
```

---

### `✖️` / `積` / `product`
Returns the product of all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
product(2, 3)      → 6
product(2, 3, 4)   → 24
```

---

### `✂️` / `商` / `quotient`
Divides the first argument by subsequent arguments. Integer division (`//`) is used when all arguments are ints.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int (integer division) or float |

```
quotient(10, 3)     → 3
quotient(10.0, 4.0) → 2.5
quotient(100, 5, 2) → 10
```

---

### `🍕` / `剰余` / `remainder`
Returns the remainder after dividing the first argument by subsequent arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
remainder(10, 3)    → 1
remainder(5.5, 2.0) → 1.5
```

---

### `👑` / `最大値` / `max`
Returns the maximum value among all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
max(3, 1, 4, 1, 5)  → 5
max(1.5, 2.5)        → 2.5
```

---

### `🐜` / `最小値` / `min`
Returns the minimum value among all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints or floats |
| Returns | int or float |

```
min(3, 1, 4)   → 1
min(1.5, 0.5)  → 0.5
```

---

## Random

### `🎲📊` / `乱数` / `random`
Returns a random float in the range `[0.0, 1.0)`.

| | |
|---|---|
| Arguments | none |
| Returns | float |

```
random()   → 0.472958   (example)
```

---

### `🎲📊` / `乱整数` / `randint`
Returns a random integer in the range `[0, n)`.

| | |
|---|---|
| Arguments | `n` — positive int |
| Returns | int |

```
randint(6)   → 4   (example, one of 0–5)
```

---

## Bitwise

### `💡✖️` / `論理積` / `and`
Returns the bitwise AND of all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints |
| Returns | int |

```
and(0b1010, 0b1100)          → 0b1000  (= 8)
and(0b1111, 0b1100, 0b1010)  → 0b1000  (= 8)
```

---

### `💡➕` / `論理和` / `or`
Returns the bitwise OR of all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints |
| Returns | int |

```
or(0b1010, 0b1100)   → 0b1110  (= 14)
```

---

### `💡🔀` / `排他的論理和` / `xor`
Returns the bitwise XOR of all arguments.

| | |
|---|---|
| Arguments | `x, y, ...` — one or more ints |
| Returns | int |

```
xor(0b1010, 0b1100)   → 0b0110  (= 6)
```

---

### `💡🔄` / `ビット反転` / `not`
Returns the bitwise NOT (one's complement) of the argument.

| | |
|---|---|
| Arguments | `x` — int |
| Returns | int |

```
not(0)    → -1
not(-1)   → 0
not(1)    → -2
```

---

### `💡⬅️` / `左シフト` / `shl`
Shifts `x` left by `n` bits.

| | |
|---|---|
| Arguments | `x` — int, `n` — int |
| Returns | int |

```
shl(1, 3)   → 8
shl(5, 2)   → 20
```

---

### `💡➡️` / `右シフト` / `shr`
Shifts `x` right by `n` bits.

| | |
|---|---|
| Arguments | `x` — int, `n` — int |
| Returns | int |

```
shr(8, 3)   → 1
shr(20, 2)  → 5
```

---

## Type predicates

All predicates return `1` (true) or `0` (false).

| Emoji | Japanese | English | Returns 1 when… |
|-------|----------|---------|-----------------|
| `💯❓` | `整数判定` | `isint` | argument is an int |
| `📊❓` | `小数判定` | `isfloat` | argument is a float |
| `💬❓` | `文字列判定` | `isstring` | argument is a string |
| `🍡❓` | `配列判定` | `isarray` | argument is an array |
| `🗂️❓` | `オブジェクト判定` | `isobject` | argument is an object |

```
isint(42)      → 1
isint(3.14)    → 0
isfloat(3.14)  → 1
isstring("hi") → 1
```

---

## Type conversions

| Emoji | Japanese | English | Description |
|-------|----------|---------|-------------|
| `💯` | `整数化` | `toint` | Convert to int (truncates toward zero) |
| `📊` | `小数化` | `tofloat` | Convert to float (also accepts numeric strings) |
| `💬` | `文字列化` | `tostring` | Convert to string |
| `🍡` | `配列化` | `toarray` | Return the internal array view of a value |
| `🗂️` | `オブジェクト化` | `toobject` | Convert JSON string to object; returns `{}` on failure |

```
toint(3.9)        → 3
toint(-3.9)       → -3
tofloat(3)        → 3.000000
tofloat("2.5")    → 2.5
tostring(42)      → "42"
tostring(3.14)    → "3.140000"
```
