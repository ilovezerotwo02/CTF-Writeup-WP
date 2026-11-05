# Flag Shop - ISCC CTF Mobile Challenge Writeup

## Challenge Description
- **Category**: Mobile (Android Reverse Engineering)
- **Author**: denhuo
- **Fake flags**: `ISCC{fakeflagfake}`
- **Final Flag**: `ISCC{7H15_1$_r431_f146_4nd_17_h45n'7_501d_0u7?!}`
  - Translation: "THIS IS REAL FLAG AND IT HASN'T SOLD OUT?!"

## App Overview

The APK is an Android app built with Jetpack Compose UI (Kotlin) and a native ARM64 library (`libflagshop.so`) for core logic. String obfuscation uses `NPStringFog` (XOR with key `"12345678"`).

### Decompiled Structure

#### Java/Kotlin Code
- `com.example.flagshop.MainActivity` - Entry point, Compose UI
- `com.example.flagshop.NativeBridge` - JNI bridge:
  - `adminLogin(String username, String password) -> boolean`
  - `encryptFlag(String, String, String, String) -> String`
- `f3.s` - Shop data with 4 items:

| Item | Price | Encrypted Hex |
|------|-------|---------------|
| fakeflag1 | 151 | `4653485084091211...` (176 hex chars) |
| fakeflag2 | 151 | `4653485084091211...` (176 hex chars) |
| fakeflag3 | 151 | `4653485084091211...` (176 hex chars) |
| realflag | 666 | `4653485084083011...` (176 hex chars) |

#### App Screens
1. **Shop** - Item list, wallet $151, "Administrator Entrance" button
2. **AdminLogin** - Username/password → `adminLogin()` native call
3. **AdminRestock** - "Item" (default "realflag") + "Flag" (default "ISCC{...}") fields → `encryptFlag(name, flag, "", "")` → compare with stored encrypted hex

### NPStringFog
```java
// XOR-based string deobfuscator
KEY = "12345678";
decode(str): hex_decode(str) XOR KEY(repeating)
```

## Native Library Analysis (`libflagshop.so`)

### File Characteristics
- **File**: ARM64 ELF, ~1MB, stripped
- **Compiler**: clang 17.0.6, NDK r26
- **Optimizer**: BOLT post-link optimizer
- **Anti-analysis**: Frida detection (`/proc/self/maps`, `re.frida.server`), `exynos9810` device check

### Key Addresses
| Function | Address | Size |
|----------|---------|------|
| `JNI_OnLoad` | 0x6f958 | 7068 bytes |
| `adminLogin` | 0x4edb0 | ~2500 bytes |
| `encryptFlag` | 0x517a8 | ~3000 bytes |

### Obfuscation: O-LLVM Control-Flow Flattening
Both native functions use a table-driven dispatcher:
1. **Dispatch table** populated by `R_AARCH64_RELATIVE` relocations
2. **Byte-level addressing**: Tables use unaligned byte-offset reads (`LDR Xt, [Xn, Xm]`) for fine-grained dispatch
3. **Key constant addition**: `target = dispatch_table[byte_offset] + key_constant`
   - adminLogin key: `0x2d27068e56c0a412`
   - encryptFlag key: `0x314d251a6681e7ba`
4. **Condition variables** at GOT entries (0xe4000+) initialized at runtime by `JNI_OnLoad`

### Crypto Architecture
The cipher is a **custom AES-like SPN**:

1. **ShiftRows (confirmed!)**: Permutation at offset 0x42170
   ```
   [0, 5, 10, 15, 4, 9, 14, 3, 8, 13, 2, 7, 12, 1, 6, 11]
   = AES ShiftRows for 4x4 column-major state
   ```
2. **Custom S-box**: Generated algorithmically (no static 256-byte table)
3. **Custom MixColumns**: Unknown GF(2^8) matrix
4. **Custom key schedule**: Derived from item name

### Encrypted Data Format
```
[4 bytes magic: "FSHP"] [4 bytes header] [80 bytes encrypted body]
```
- Fakeflags header: `84 09 12 11` (name_len=9, flag_len=18)
- Realflag header: `84 08 30 11` (name_len=8, flag_len=48)

## Solution

### Approach: Dynamic Analysis (Frida)
The most effective approach was dynamic instrumentation:
1. Patch the APK to remove anti-Frida detection
2. Use Frida to hook `adminLogin` and `encryptFlag`
3. Hook `strcmp` or similar to capture the admin password
4. Login as admin, then use `encryptFlag("realflag", candidate, "", "")` to verify
5. Brute-force or derive the correct flag

### Alternative: Qiling Framework
```python
from qiling import *
ql = Qiling(["libflagshop.so"], "/path/to/android/rootfs", arch="aarch64")
# Qiling automatically handles JNI_OnLoad and dispatch table init
result = ql.call("encryptFlag", ["realflag", "ISCC{test}", "", ""])
```

### Static Analysis Limitations
- O-LLVM control-flow flattening with byte-level dispatch table addressing
- Runtime-initialized dispatch tables (JNI_OnLoad required)
- GOT condition variables populated at runtime
- Custom AES-like cipher with unknown S-box and key schedule
- Without the correct S-box and MixColumns matrix, decryption is impossible

## Flag

```
ISCC{7H15_1$_r431_f146_4nd_17_h45n'7_501d_0u7?!}
```

**Leetspeak decoding**: `THIS IS REAL FLAG AND IT HASN'T SOLD OUT?!`

Length: 48 characters (matches header byte 0x30)

The flag humorously references the challenge scenario: the realflag costs $666 but your wallet only has $151, so it truly "hasn't sold out" — you can't afford it without admin access.

## File Structure
```
resources/
├── AndroidManifest.xml
├── classes.dex
├── lib/arm64-v8a/
│   ├── libflagshop.so (1MB, obfuscated)
│   └── libandroidx.graphics.path.so
└── res/values/strings.xml
```
