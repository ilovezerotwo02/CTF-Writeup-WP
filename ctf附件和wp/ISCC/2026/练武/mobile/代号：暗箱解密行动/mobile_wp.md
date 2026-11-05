## WriteUp：CTFmobile 逆向分析

### 1. 题目信息

- **题目名称**：代号：暗箱解密行动（CTFmobile）
    
- **附件**：`attachment-7.apk`
    
- **描述**：分析 APK，破解四组口令，解密得到 `ISCC{...}` 格式的 flag。
    
- **工具**：JADX（静态分析）、Python（爆破与解密）
    

### 2. 静态分析（JADX）

用 JADX 打开 APK，包名 `com.example.scm`，关键类：

|类名|作用|
|---|---|
|`MainActivity`|入口，加载 Compose UI|
|`MainActivityKt`|定义四个输入框（p1~p4），限制 6 位可打印 ASCII|
|`PasswordValidator`|核心校验，四步验证 + 解密调度|
|`Transforms`|提供 FNV 哈希、双重 SHA-256、Atbash、循环移位等|
|`NativeBridge`|加载 `libscm_native.so`，native 校验与 RC4 解密|

#### 2.1 界面与输入

`AsciiField` 组件限制输入为 ASCII(0x20~0x7E)，截断至 6 字符。点击“验证并解密”后调用 `PasswordValidator.INSTANCE.validateAndDecrypt()`。

#### 2.2 四步校验逻辑摘要

1. **Part1**：`doubleSha256Ascii6(p1)` 的 hex 必须等于 `5475D82A...5215`。
    
2. **Part2**：`u1=fold(p1)`, `u2=fold(p2)`，经过 `异或 0xAAAAAA → AtbashHex → 循环左移 8 → AtbashHex` 后应等于 `u1`，由此互锁。
    
3. **Part3**：Native 方法验证 `p1,p2,p3`，依赖 `assets/data.bin` 中的数据。
    
4. **Part4**：Native 方法基于 p1~p3 生成自定义 Base64，解码固定串 `gGH52dkV` 得到 p4，且最终密钥的 SHA-256 需匹配 SO 内硬编码哈希。
    
5. **解密**：通过全部后，用 `p1+p2+p3+p4` 作为 RC4 密钥解密 `assets/flag.enc`。
    

#### 2.3 关键算法（`Transforms`）

- `foldAscii6ToU24(s)`：FNV-1a 变种，初始值 `0x1C9DC5`，乘数 `0x193`，结果保留 24 位。
    
- `doubleSha256Ascii6(s)`：SHA-256(SHA-256(s))。
    
- `atbashHex6(s)`：十六进制倒序映射（0↔9, A↔F）。
    
- `rol24(x, r)`：24 位循环左移。
    
- `xorAsciiAll(s)`：6 字节异或和（低 8 位）。
    

#### 2.4 Native 层与 assets

- `libscm_native.so` 导出三个 JNI 函数：`nativeValidatePart3`、`nativeValidatePart4`、`nativeDecryptFlag`。
    
- `assets/data.bin`：加密的 p2/p3 约束数据，每 3 字节 `raw` 解码公式 `dec = (raw ^ 0xDEADBE) & 0xFFFFFF`。
    
- `assets/flag.enc`：RC4 加密的 flag。
    
- SO 内嵌 SHA-256 哈希：`a950927d04e7936e1ebdb7ee03f59f7a17adf1a3d962475e0c772b7899c4ff2d`，用于验证最终密钥。
    

### 3. 解题步骤

#### 3.1 爆破 p1

6 位可打印 ASCII 枚举空间 ≈ 7.35×10^11，Python 可在数分钟内完成。计算双重 SHA-256 并与硬编码哈希比对，得到：

text

p1 = CT.=6`

（末尾为反引号）

#### 3.2 计算 p2 期望值并枚举

由 p1 计算期望 `fold(p2)` = `targetU2`：


```

u1 = fold(p1)
dHex = u24ToHex6(u1)
c = hex6ToU24(atbashHex6(dHex))
b = rol24(c, 16)          // 等价 ror(c,8)
a = hex6ToU24(atbashHex6(u24ToHex6(b)))
targetU2 = (a ^ 0xAAAAAA) & 0xFFFFFF

然后枚举 6 字节 ASCII 串，满足 `fold(p2) == targetU2` 且 `xorAscii(p2)` 等于 `data.bin` 中对应字节，得到：

text

p2 = NTgWmG
```

#### 3.3 提取 p3 约束并枚举

遍历 `data.bin`，对每个偏移 3 字节 `raw`：

text
```

dec = (raw ^ 0xDEADBE) & 0xFFFFFF
high = dec >> 16
if high == xorAscii(p1):
    p2_xor = (dec >> 8) & 0xFF
    p3_xor = dec & 0xFF
    p3_fold = (offset ^ 0xAAAAAA) & 0xFFFFFF
```

已知 p1，可唯一确定 p3_fold 和 p3_xor。枚举 ASCII 串使 `fold(p3)=p3_fold` 且 `xorAscii(p3)=p3_xor`，解得：



```
p3 = OhvppQ
```

#### 3.4 计算 p4



```
seed = (fold(p1) ^ rol24(fold(p2),3) ^ rol24(fold(p3),7)) & 0xFFFFFF
shift = seed & 0x3F
自定义 Base64 表 = 标准 Base64 循环左移 shift 位
目标字节 gGH52dkV 逐字符解码，异或种子指定位得到 6 字节 p4
```

结果：`p4 = C0DE!!`

#### 3.5 解密 Flag

拼接密钥：`CT.=6`NTgWmGOhvppQC0DE!!`，验证 SHA-256 通过后，对`flag.enc` 执行 RC4 解密，得到：



```
ISCC{1ec96564c8f34813d6de1aa2cbf7f1055032514f59b41bd2c18f476bf8a8fb6f}
```

### 4. 自动化脚本

将以下脚本与 `attachment-7.apk` 放在同一目录，运行 `python solve.py` 即可自动输出口令与 flag。



```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTFmobile Auto-solver (modified – automatic APK detection)
将 APK 放在脚本同目录下，双击运行或 python solve.py 即可。
"""
import sys
import os
import zipfile
import hashlib
import itertools
import re
from pathlib import Path
from collections import defaultdict
# ========== 常量 ==========
ASCII_MIN, ASCII_MAX = 0x20, 0x7E
PRINTABLE = bytes(range(ASCII_MIN, ASCII_MAX + 1))
MOD24 = 1 << 24
FNV_PRIME = 0x193
FNV_INV = pow(FNV_PRIME, -1, MOD24)
FNV_INIT = 0x1C9DC5
BASE64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
P4_TARGET = b"gGH52dkV"
PIN_HASH_HEX = "a950927d04e7936e1ebdb7ee03f59f7a17adf1a3d962475e0c772b7899c4ff2d"
P1_HASH_HEX = "5475D82A7B1E7BAD1C0D50487C52AD17D8C7E5F1FF68E361ACC725CD301A5215"
P1_HEX = "43542E3D3660"   # CT.=6`
def err(msg):
    print(f"[-] {msg}")
    sys.exit(1)
def is_ascii6(data):
    return len(data) == 6 and all(ASCII_MIN <= b <= ASCII_MAX for b in data)
def fnv24(data):
    h = FNV_INIT
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & 0xFFFFFF
    return h
def xor_all(data):
    acc = 0
    for b in data:
        acc ^= b
    return acc & 0xFF
def rol24(v, n):
    n %= 24
    v &= 0xFFFFFF
    return ((v << n) | (v >> (24 - n))) & 0xFFFFFF
def ror24(v, n):
    n %= 24
    v &= 0xFFFFFF
    return ((v >> n) | (v << (24 - n))) & 0xFFFFFF
def int2hex6(v):
    return f"{v & 0xFFFFFF:06X}"
def atbash_hex6(s):
    res = []
    for c in s.upper():
        if '0' <= c <= '9':
            res.append(chr(ord('9') - ord(c) + ord('0')))
        elif 'A' <= c <= 'F':
            res.append(chr(ord('F') - ord(c) + ord('A')))
        else:
            raise ValueError(f"bad hex: {c}")
    return ''.join(res)
def compute_p2_target(p1):
    u1 = fnv24(p1)
    c = int(atbash_hex6(int2hex6(u1)), 16)
    b = ror24(c, 8)
    a = int(atbash_hex6(int2hex6(b)), 16)
    return (a ^ 0xAAAAAA) & 0xFFFFFF
def build_prefix_table():
    tbl = defaultdict(list)
    for trip in itertools.product(PRINTABLE, repeat=3):
        pre = bytes(trip)
        tbl[(fnv24(pre), xor_all(pre))].append(pre)
    return tbl
def find_ascii6(fold, xor, prefixes):
    res = []
    for d3, d4, d5 in itertools.product(PRINTABLE, repeat=3):
        suff = bytes((d3, d4, d5))
        f = fold
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d5
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d4
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d3
        px = xor ^ d3 ^ d4 ^ d5
        for pre in prefixes.get((f, px), []):
            res.append(pre + suff)
    return res
def derive_p4(p1, p2, p3, target):
    seed = (fnv24(p1) ^ rol24(fnv24(p2), 3) ^ rol24(fnv24(p3), 7)) & 0xFFFFFF
    shift = seed & 0x3F
    custom_b64 = bytes((BASE64[(i + shift) % 64]) for i in range(64))
    rev = {c: i for i, c in enumerate(custom_b64)}
    indices = []
    for i, ch in enumerate(target):
        if ch not in rev:
            return None
        indices.append((rev[ch] ^ ((seed >> ((i * 7) % 24)) & 0x3F)) & 0x3F)
    raw = bytearray()
    for blk in range(2):
        off = blk * 4
        val = (indices[off] << 18) | (indices[off+1] << 12) | (indices[off+2] << 6) | indices[off+3]
        raw.append((val >> 16) & 0xFF)
        raw.append((val >> 8) & 0xFF)
        raw.append(val & 0xFF)
    p4 = bytes(raw)
    return p4 if is_ascii6(p4) else None
def rc4_crypt(data, key):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)
def load_apk(path):
    with zipfile.ZipFile(path, 'r') as zf:
        data_bin = zf.read("assets/data.bin")
        flag_enc = zf.read("assets/flag.enc")
        dex_blob = b"".join(zf.read(n) for n in zf.namelist() if re.fullmatch(r'classes\d*\.dex', n))
        sos = [zf.read(n) for n in zf.namelist() if n.endswith("libscm_native.so")]
    if not sos:
        err("No libscm_native.so found in APK")
    return data_bin, flag_enc, sos, dex_blob
def get_data_targets(dat, p1):
    want_hi = xor_all(p1)
    targets = defaultdict(list)
    for off in range(len(dat) - 2):
        raw = int.from_bytes(dat[off:off+3], 'little')
        dec = (raw ^ 0xDEADBE) & 0xFFFFFF
        if (dec >> 16) == want_hi:
            p2_xor = (dec >> 8) & 0xFF
            targets[p2_xor].append(((off ^ 0xAAAAAA) & 0xFFFFFF, dec & 0xFF))
    return targets
def solve(apk_path):
    print(f"[*] Solving {apk_path.name} ...")
    data_bin, flag_enc, so_blobs, dex_blob = load_apk(apk_path)
    p1 = bytes.fromhex(P1_HEX)
    if hashlib.sha256(hashlib.sha256(p1).digest()).hexdigest().upper() != P1_HASH_HEX:
        err("p1 hash mismatch")
    # 从 native 中提取校验用哈希
    default_pin = bytes.fromhex(PIN_HASH_HEX)
    pins = set()
    for blob in so_blobs:
        if default_pin in blob:
            pins.add(default_pin)
    if not pins:
        for blob in so_blobs:
            for i in range(len(blob) - 31):
                pins.add(blob[i:i+32])
    prefixes = build_prefix_table()
    p2_fold_target = compute_p2_target(p1)
    targets_by_xor = get_data_targets(data_bin, p1)
    p2_cache, p3_cache = {}, {}
    checked = 0
    for p2_xor, data_targets in targets_by_xor.items():
        if p2_xor not in p2_cache:
            p2_cache[p2_xor] = find_ascii6(p2_fold_target, p2_xor, prefixes)
        for p2 in p2_cache[p2_xor]:
            for p3_fold, p3_xor in data_targets:
                ck = (p3_fold, p3_xor)
                if ck not in p3_cache:
                    p3_cache[ck] = find_ascii6(p3_fold, p3_xor, prefixes)
                for p3 in p3_cache[ck]:
                    p4 = derive_p4(p1, p2, p3, P4_TARGET)
                    if not p4:
                        continue
                    key = p1 + p2 + p3 + p4
                    checked += 1
                    if hashlib.sha256(key).digest() not in pins:
                        continue
                    flag = rc4_crypt(flag_enc, key).decode('utf-8')
                    print(f"p1 = {p1.decode('ascii')}")
                    print(f"p2 = {p2.decode('ascii')}")
                    print(f"p3 = {p3.decode('ascii')}")
                    print(f"p4 = {p4.decode('ascii')}")
                    print(f"key = {key.decode('ascii')}")
                    print(f"flag = {flag}")
                    print(f"candidates checked = {checked}")
                    return
    print(f"[-] No valid key found (checked {checked})")
def find_apk():
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.exists():
            return p
        err(f"指定的 APK 不存在: {p}")
    script_dir = Path(__file__).resolve().parent
    default = script_dir / "attachment-7.apk"
    if default.exists():
        return default
    apks = list(script_dir.glob("*.apk"))
    if not apks:
        apks = list(Path.cwd().glob("*.apk"))
    if not apks:
        err("未找到任何 APK 文件，请将 APK 放在脚本同目录或命令行指定。")
    if len(apks) > 1:
        print(f"[*] 发现多个 APK: {[a.name for a in apks]}，默认使用第一个: {apks[0].name}")
    return apks[0]
if __name__ == "__main__":
    apk_path = find_apk()
    solve(apk_path)
```

### 5. 运行方式

- 将脚本与 `attachment-7.apk` 放在同一目录，执行：
    
    bash
    
```
    python solve.py
```
    
- 若 APK 名称不同，可手动指定：
    
    bash
    
```
    python solve.py yourfile.apk
```
    

### 6. 最终结果


```

p1 = CT.=6`
p2 = NTgWmG
p3 = OhvppQ
p4 = C0DE!!
key = CT.=6`NTgWmGOhvppQC0DE!!
flag = ISCC{1ec96564c8f34813d6de1aa2cbf7f1055032514f59b41bd2c18f476bf8a8fb6f}
```