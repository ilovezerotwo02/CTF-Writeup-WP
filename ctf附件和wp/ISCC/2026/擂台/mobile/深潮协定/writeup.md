# ISCC 深潮协定 (Deep Tide Protocol) — Mobile Challenge Writeup

**Category:** Mobile (Android Reverse Engineering)  
**Solves:** 1637  
**Flag:** `ISCC{abyssal_vows_bind_the_last_protocol}`

---

## Challenge Overview

The app `app-release.apk` presents a text input field and a "Verify" button. The goal is to find the correct `ISCC{...}` flag that passes verification.

The APK contains:
- **Java bytecode** (`classes.dex`) — input handling, flag transformation
- **Native library** (`libdeepseal.so` for ARM64) — core verification logic
- **Asset file** (`assets/telemetry.bin`) — encoded target and parameters

---

## Step 1 — Decompile the APK

Decompile with `jadx` or `apktool` to extract the Java sources and native library:

```
jadx app-release.apk -d sources/
apktool d app-release.apk -o resources/
```

Key Java classes found under `cn.iscc.deepseal`:

- `MainActivity.java` — UI, calls `FlagValidator.check()`
- `FlagValidator.java` — strips `ISCC{...}` wrapper, calls `CryptoEngine.transform()` then `NativeBridge.verify()`
- `CryptoEngine.java` — shift + XOR + accumulator transform on input
- `NativeBridge.java` — JNI bridge to `libdeepseal.so`
- `Telemetry.java` — loads `assets/telemetry.bin` (shifts, mask, alphabet, target)
- `Hex.java` — hex decode utility

---

## Step 2 — Analyze the Java Transform

### FlagValidator.check()
```java
public static boolean check(Context context, String str) {
    if (str.startsWith("ISCC{") && str.endsWith("}")) {
        return NativeBridge.verify(context,
            CryptoEngine.transform(context, str.substring(5, str.length() - 1)));
    }
    return false;
}
```

Strips the `ISCC{...}` wrapper and passes the inner string through `CryptoEngine.transform()`.

### CryptoEngine.transform()

```java
public static byte[] transform(Context context, String str) {
    Telemetry load = Telemetry.load(context);
    byte[] shifts = load.shifts();  // [11, 4, 17, 9, 22, 6, 13]
    byte[] mask = load.mask();      // [19, 55, 192, 222, 66, 165, 25, 127]

    byte[] bytes = str.getBytes(StandardCharsets.US_ASCII);
    byte[] result = new byte[bytes.length];
    int acc = 0;

    for (int i = 0; i < bytes.length; i++) {
        int c = bytes[i] & 0xFF;
        if (c >= 32 && c <= 126) {  // printable ASCII only
            c = ((c - 32) + (shifts[i % shifts.length] & 0xFF)) % 95 + 32;
        }
        acc = ((c ^ (mask[i % mask.length] & 0xFF)) + acc + (i * 3)) & 0xFF;
        result[i] = (byte) acc;
    }
    return result;
}
```

For each character:
1. **Caesar-like shift** within printable ASCII [32, 126]: `c' = (c - 32 + shift) % 95 + 32`
2. **XOR with mask byte**, then accumulate: `acc = (c' ^ mask[i]) + acc + i*3` (truncated to 1 byte)

This is a **chain-dependent transform**: each output byte depends on all previous bytes through the accumulator `acc`.

---

## Step 3 — Analyze the Native Library

### JNI Verify Function

`libdeepseal.so` (ARM64, stripped) exports `Java_cn_iscc_deepseal_NativeBridge_verify`. Key sub-functions:

| Mangled Name | Demangled Name | Purpose |
|---|---|---|
| `_Z21apply_native_lfsr_mixPhi` | `apply_native_lfsr_mix(unsigned char*, int)` | 8-bit LFSR XOR |
| `_Z17custom_b64_decode...` | `custom_b64_decode(string, string)` | Custom base64 decode |

The verify function:
1. Receives the byte array from `CryptoEngine.transform()`
2. Opens `telemetry.bin` natively via `AAssetManager`
3. Custom-base64-decodes the **target** string line using the **alphabet** line
4. Applies `apply_native_lfsr_mix` to the input bytes
5. Compares the LFSR-mixed input against the decoded target using `memcmp`

### LFSR Mix (apply_native_lfsr_mix)

Disassembled from `0x62770`:

```asm
cmp    w1, #1           ; if len < 1, return
b.lt   ret
ubfiz  x9, x1, #3, #32  ; x9 = len * 8
sub    x9, x9, x1        ; x9 = len * 7 (total iterations)
mov    w10, #0x5D        ; LFSR initial state = 93
mov    x8, xzr           ; i = 0
loop:
  ; LFSR feedback: taps at bits 0, 2, 3, 5
  ; polynomial: x^8 + x^5 + x^3 + x^2 + 1
  lsr    w11, w10, #3
  eor    w11, w11, w10, lsr #2
  eor    w11, w11, w10, lsr #5
  eor    w11, w11, w10
  ubfiz  w11, w11, #7, #1  ; feedback = (bit0 << 7)
  orr    w10, w11, w10, lsr #1  ; state = feedback | (state >> 1)

  ldrb   w11, [x0]         ; load data byte
  add    w12, w8, w10      ; mix_val = i*7 + state
  eor    w11, w11, w12     ; data[i] ^= mix_val
  strb   w11, [x0], #1     ; store, advance pointer
  add    x8, x8, #7        ; i += 7
  cmp    x9, x8
  b.ne   loop
```

Reconstructed in Python:
```python
state = 0x5D
for i in range(len(data)):
    feedback = ((state >> 2) ^ (state >> 3) ^ (state >> 5) ^ state) & 1
    state = ((feedback << 7) | (state >> 1)) & 0xFF
    data[i] ^= (i * 7 + state) & 0xFF
```

> Since XOR is its own inverse, the forward and reverse operations are identical.

---

## Step 4 — Extract telemetry.bin

From `assets/telemetry.bin` (4 lines):

| Line | Content | Meaning |
|---|---|---|
| 1 | `0b04110916060d` | **shifts** (7 bytes): `[11, 4, 17, 9, 22, 6, 13]` |
| 2 | `1337c0de42a5197f` | **mask** (8 bytes): `[19, 55, 192, 222, 66, 165, 25, 127]` |
| 3 | `Qh2s7Ca9VxN4fKpB8J1mL+zoF0ewAyOu3DrRYSgPItU6McdkXl/WTnGEZ5ivbHjq` | **custom base64 alphabet** (64 chars) |
| 4 | `T8GHtJzYDRX7siXzWKLJCGlrpi1sVwnvMhZCPj3jwDWYU4Y=` | **encoded target** (48 chars) |

The alphabet is a **custom Base64** variant. The target is encoded with this custom alphabet and must be decoded to get the expected verification bytes.

---

## Step 5 — Reverse the Transform

The full verification chain (forward):

```
flag_inner
    → CryptoEngine.transform()    (shift + mask + accumulate)
    → apply_native_lfsr_mix()     (LFSR XOR)
    → custom_b64_encode()
    → compare with target string
```

To recover the flag, we reverse each step:

### 5a. Custom Base64 Decode (target → expected_bytes)

Map the custom alphabet back to standard Base64, then decode:

```python
std_alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
trans = str.maketrans(custom_alphabet, std_alpha)
decoded = base64.b64decode(target.translate(trans))
```

Result: 35 bytes — these are what the flag *should* produce after LFSR mix.

### 5b. Reverse LFSR Mix (expected_bytes → transform_output)

Apply the same LFSR operation (XOR is self-inverse):

```python
state = 0x5D
for i in range(35):
    feedback = ((state>>2)^(state>>3)^(state>>5)^state) & 1
    state = ((feedback<<7) | (state>>1)) & 0xFF
    decoded[i] ^= (i*7 + state) & 0xFF
```

Result: the output that `CryptoEngine.transform()` should have produced.

### 5c. Reverse CryptoEngine.transform (transform_output → original string)

Each output byte `out[i]` is computed as:
```
acc[i] = ((char_shifted ^ mask[i]) + acc[i-1] + i*3) & 0xFF
```

Reverse:
```
char_shifted = ((out[i] - out[i-1] - i*3) & 0xFF) ^ mask[i]
original[i]  = ((char_shifted - 32 - shifts[i]) % 95) + 32
```

(Note: `out[-1]` = 0 for the first byte.)

---

## Step 6 — Recover the Flag

Running the full reverse solver:

```
$ python3 solve.py app-release.apk
[+] FLAG: ISCC{abyssal_vows_bind_the_last_protocol}
```

The inner string is `abyssal_vows_bind_the_last_protocol` — 35 characters matching the decoded target length.

---

## Summary

| Layer | Technique | Details |
|---|---|---|
| App entry | Decompile APK | `jadx` / `apktool` |
| Java transform | Caesar shift + XOR + accumulator | Printable-ASCII cyclic shift, dependent on position and previous output |
| Native lib | 8-bit LFSR | polynomial `x^8 + x^5 + x^3 + x^2 + 1`, initial state `0x5D`, XOR per byte |
| Telemetry | Custom Base64 | Non-standard 64-char alphabet encoding the target |
| Solve | Reverse each layer | LFSR is self-inverse; accumulator reverses via modular arithmetic |

**Flag:** `ISCC{abyssal_vows_bind_the_last_protocol}`
