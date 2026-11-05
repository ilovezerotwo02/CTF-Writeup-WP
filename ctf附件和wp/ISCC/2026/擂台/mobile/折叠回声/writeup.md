# ISCC CTF Writeup — 折叠回声 (EchoFold)

**Category:** Mobile (Android Reverse Engineering)  
**Author:** 小许同学  
**Flag:** `ISCC{f0lded_echo_is_a_state_not_a_string}`

## Challenge Description

> 有人把一句话录进了回声里。第一声很像答案，第二声很像线索，第三声才开始说真话。

Someone recorded a sentence into the echo. The first sound seems like the answer, the second sound is like a clue, and the third sound tells the truth.

## Solution Overview

The APK contains three "echoes" hidden across multiple layers:

| Echo | What it is | Purpose |
|------|-----------|---------|
| 1st | `ISCC{this_is_only_the_first_echo}` in `FirstEchoCodec.java` | Decoy |
| 2nd | Encrypted bytecode + flag in a custom `ECH0` RIFF chunk inside `sleep_loop.webp` | Clue |
| 3rd | Real flag decrypted via VM + XOR | Flag |

## Step-by-Step Analysis

### 1. Static Analysis (jadx)

Decompiling with jadx reveals four key classes:

- **`MainActivity`** — Simple UI with an input field and a "Check" button. On click, it first checks `FirstEchoCodec.check()` (fake flag), then calls `EchoGate.verify()` (real check).
- **`FirstEchoCodec`** — Accepts `ISCC{this_is_only_the_first_echo}` only — a red herring.
- **`EchoGate`** — The real verification engine. Reads encrypted data from `sleep_loop.webp`, runs a custom VM, and validates user input.
- **`TraceRecorder`** — Contains a hardcoded 6-byte `TRACE` array `{17, 35, 122, 66, 81, 102}` used as environment entropy.
- **`Bytes`** — Utility class with byte XOR and hex conversion.

### 2. The ECH0 Chunk

Inside `resources/assets/sleep_loop.webp`, a custom RIFF chunk with FourCC `ECH0` (236 bytes) contains encrypted data. The app reads it and decrypts it using a SHA256-based stream cipher:

```
key = SHA256("fold-echo" || resourceKey || dexDigest || certDigest || snapshot)
```

Where:
- **`resourceKey`** (24 bytes) — Derived from `R.styleable.EchoFoldPulse` (32 values: `0x7f010000` through `0x7f01001f`)
- **`dexDigest`** (32 bytes) — `SHA256(classes.dex)` from the APK
- **`certDigest`** (32 bytes) — `SHA256(signing certificate)` from the APK
- **`snapshot`** (6 bytes) — `{17, 35, 122, 66, 81, 102}` from `TraceRecorder`

After decryption, the data has an `EFVM` magic header:

```
EFVM [1 byte version] [2 bytes bytecode_len] [2 bytes out_len] [bytecode] [encrypted_output]
```

- Bytecode: 192 bytes (48 instructions, 4 bytes each)
- Encrypted output: 35 bytes

### 3. The Custom VM

The VM has 8 x 32-bit registers initialized from:

```
seed = SHA256("vm-seed" || resourceKey || dexDigest || certDigest || snapshot)
regs[i] = read_LE32(seed[4*i:4*i+4]) XOR (0x9E3779B9 * i)   // TEA delta constant
```

Each instruction (4 bytes) encodes:
- **Byte 0** (bits 0-2): opcode (0-7) — 8 operations
- **Byte 1** (bits 0-2): destination register (rx)
- **Byte 2** (bits 0-2): source register (ry)
- **Byte 3** (bits 0-2): source register (rz)

Additionally, a per-instruction mixing value `i11` injects environment entropy:

```
i11 = dexDigest[(ip/2)%32] XOR resourceKey[(ip/4)%24] XOR certDigest[(ip/3)%32] XOR snapshot[(ip/4)%6]
```

The 8 VM opcodes implement standard TEA/XTEA-like primitives:

| Op | Operation |
|----|-----------|
| 0 | `r[rx] = rotl((r[ry]+i11)+ip, (rz+i11)&31) ^ r[rx]` |
| 1 | `r[rx] = rotl(r[rx]+r[ry]+(i11<<1)+rz, (ry+rz+ip)&31)` |
| 2 | `r[rx] = r[rx] ^ ((revbytes(r[rz]) ^ r[ry]) + i11)` |
| 3 | `r[rx] = r[ry]+i11; r[ry] = rotr(r[rz]+ip, i11&31) ^ tmp` |
| 4 | `r[rx] = r[rx] + rotr((i11^r[ry])^ip, (rz+rx+1)&31)` |
| 5 | `r[rx] = rotl((r[ry]+r[rz])+i11, (ip+rx+ry)&31) ^ r[rx]` |
| 6 | `r[rx] = (i11^(r[rx]^r[ry])) + revbits(r[rz]+ip)` |
| 7 | `r[rx] = r[rx] + (i11^(r[rz]^r[ry])) + ip` |

After all 48 instructions execute, the 35-byte VM key is generated:

```
vm_key[i] = (regs[i&7] XOR rotl(regs[(i+3)&7], i&31))
            XOR resourceKey[i%24]
            XOR dexDigest[i%32]
            XOR certDigest[i%32]
            XOR snapshot[i%6]
```

### 4. The jadx Pitfall (Key Insight)

The decompiled `EchoGate.verify()` appears to call:

```java
return equal(bArr2, xorStream(bytes, runVm(bArr, ...)));
```

However, jadx incorrectly merged two different functions here. The actual verification uses **`Bytes.xor`** (simple bytewise XOR), **NOT** the SHA256-based `xorStream`. This is the crucial distinction:

- The ECH0 chunk is encrypted with `xorStream` (SHA256 stream cipher) ✓
- The flag comparison uses `Bytes.xor` (simple XOR) ✓

So the flag content is simply:

```
flag_content = enc_output XOR vm_key
```

### 5. Recovering the Flag

With all pieces assembled:

```python
flag_content = bytes(e ^ k for e, k in zip(enc_output, vm_key))
# => "f0lded_echo_is_a_state_not_a_string"
flag = "ISCC{" + flag_content + "}"
```

**Flag: `ISCC{f0lded_echo_is_a_state_not_a_string}`**

## Tools Used

- **jadx** — APK decompilation to Java source
- **asn1crypto** — Extracting X.509 certificate from PKCS7 signature
- **Python** — VM emulation and flag decryption

## File List

| File | Purpose |
|------|---------|
| `exp.py` | Full exploit script — automates the entire solution |
| `resources/` | APK decompiled by jadx + apktool |
| `EchoFold.apk` | Original APK |
