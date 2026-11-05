第一部分：灰签名回廊 Writeup

基本情况

附件是 Android APK，主包名为 com.example.gnd，核心逻辑由 Java 层和 JNI 层共同完成。APK 没有明显加固，native 库 libnative-verify.so 为 64 位 ELF 共享库，开启 NX、RELRO、PIE，并带有栈保护相关引用。

表层字符串里能看到 ISCC{F4k3_Fl4g_N0t_R34l}，但这是诱饵。真正的校验链需要依次触发 ContentProvider、BroadcastReceiver、深链 Activity，并且最后还会用 APK 签名哈希参与 native 链式校验。

逆向分析

我先看 MainActivity 和 SecureValidator，发现输入最终进入 SecureValidator.c。Java 层先构造前缀 ISCC{，要求 flag 以 ISCC{ 开头、以 } 结尾，内部长度必须等于 nativeGetMagicNumber 的返回值乘 2。nativeGetMagicNumber 返回 0x0c，所以内部长度为 24。

内部字符串被拆成四段。

```
inner = flag[5:-1]

part1 = inner[0:7]
part2 = inner[7:12]
part3 = inner[12:17]
part4 = inner[17:24]
```

这题的关键不是单点判断，而是把四段数据和运行路径串起来。几个隐藏入口分别负责写入后续 native 校验需要的 fragment。

ContentProvider 的 authority 是 com.example.gnd.secret.provider，路径是 keys/fragment。访问后会把数组异或 23，得到 E72T，再经过自定义 Base64 写入 key_cache.fragment2。

```
[82, 32, 37, 67] xor 23 -> E72T
fragment2 = custom_base64(E72T)
```

BroadcastReceiver 监听 com.example.gnd.SECRET_ACTION。先发送 code=auth 且 token=ISCC2026，之后在五分钟内发送 code=getkey 且 part=3，才能得到第三段 key。数组经过 i ^ value ^ 90 还原为 VGSj，再写入 key_cache.fragment3。

```
[12, 28, 11, 51] -> VGSj
fragment3 = custom_base64(VGSj)
```

SecretActivity 需要特定深链唤醒。

```
securevault://secret/unlock?token=RC4_KEY_PART4
```

成功后从字符串 ISCC202RV 中取出 RV，写入 key_cache.fragment4。

第一段 nativeVerifyPart1 的逻辑比较绕，因为它会把输入先变换，再和 Java 层 SecureValidator.a(sigHash) 的结果比较。正常无调试路径下，输入字节会执行：

```
((ch + 1) ^ 7) ^ sigHash[i % 4]
```

Java 层目标基础字节是 SB1QTIi，因此逆回第一段明文为：

```
part1 = SD5URMm
```

同时要注意，这里传入 nativeComputeChainToken 的不是 part1 明文，而是 nativeVerifyPart1 返回的变换后字节，也就是 SB1QTIi 再异或 APK 签名 SHA-256 的前 4 字节循环。漏掉这个点会导致最后一段 RC4 key 全错。

第二段 nativeVerifyPart2 使用 fragment2，也就是 E72T，经过一组字节异或和 pshufb 顺序还原，得到：

```
part2 = _Sgf8
```

第三段 nativeVerifyPart3 使用 fragment3，也就是 VGSj，逻辑是候选字节先异或 0x19，再按 key 字节做加法比较，得到：

```
part3 = _f7c3
```

前三段过完后，程序连续调用 nativeComputeChainToken。这个 token 是最后一段的 RC4 key 来源之一。

```
seed = 1597463007

chain = compute_chain(1, seed, nativeVerifyPart1_return)
chain = compute_chain(2, chain, E72T)
chain = compute_chain(3, chain, VGSj)
```

最后一段 nativeVerifyPart4 构造 14 字节 RC4 key。

```
key[0:4]   = low32(chain) xor "Secu"
key[4:12]  = "E72TVGSj"
key[12:14] = fragment4 xor "RV"
```

fragment4 本身就是 RV，所以最后两个字节为 00 00。native 只对 part4 前四个字符做位运算判断，后三个字符由最终 SHA-256 收口。Java 层最终比较完整 flag 的 SHA-256：

```
e0264b0931510ace2cfa21f781112143b3e58376e1b35b94b52ada765c6b23fb
```

综合签名哈希、链式 token、RC4 条件和最终 SHA-256，得到最终 flag：

```
ISCC{SD5URMm_Sgf8_f7c3_2vhUry}
```

解题脚本

脚本默认读取 ./附件，也可以通过命令行指定 APK 路径。脚本会解析 APK Signing Block 中的 v2 签名证书，计算签名 SHA-256，再根据逆向出的 native 逻辑求解最后一段。没有直接硬编码 flag。

```
import base64
import hashlib
import itertools
import multiprocessing
import os
import re
import struct
import sys
from pathlib import Path


STD_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CUSTOM_B64 = "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210+/"


def pick_apk_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    for name in ("./附件", "./attachment.apk", "./attachment-68.apk"):
        path = Path(name)
        if path.exists():
            return path

    raise FileNotFoundError("usage: python solve.py <apk_path>")


def read_u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def read_u64(buf, off):
    return struct.unpack_from("<Q", buf, off)[0]


def read_lv(buf, off):
    size = read_u32(buf, off)
    off += 4
    return buf[off:off + size], off + size


def extract_v2_cert_sha256(apk_data):
    eocd = apk_data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("EOCD not found")

    central_dir_off = read_u32(apk_data, eocd + 16)
    magic = b"APK Sig Block 42"

    if apk_data[central_dir_off - 16:central_dir_off] != magic:
        raise ValueError("APK Signing Block not found")

    size2 = read_u64(apk_data, central_dir_off - 24)
    block_start = central_dir_off - size2 - 8

    off = block_start + 8
    end = central_dir_off - 24
    v2_block = None

    while off < end:
        pair_size = read_u64(apk_data, off)
        off += 8
        pair_id = read_u32(apk_data, off)
        off += 4
        value = apk_data[off:off + pair_size - 4]
        off += pair_size - 4

        if pair_id == 0x7109871A:
            v2_block = value

    if v2_block is None:
        raise ValueError("APK v2 signature block not found")

    signers, _ = read_lv(v2_block, 0)
    signer, _ = read_lv(signers, 0)

    signed_data, off = read_lv(signer, 0)
    digests, off = read_lv(signed_data, 0)
    certs, off = read_lv(signed_data, off)
    cert, _ = read_lv(certs, 0)

    return hashlib.sha256(cert).digest()


def extract_target_hash(apk_data):
    matches = re.findall(rb"[0-9a-f]{64}", apk_data)
    for item in matches:
        value = item.decode()
        if value != "0" * 64:
            return value
    raise ValueError("target sha256 not found")


def custom_b64_decode(text):
    mapped = "".join(STD_B64[CUSTOM_B64.index(c)] if c in CUSTOM_B64 else c for c in text)
    return base64.b64decode(mapped)


def rol64(value, bits):
    value &= 0xffffffffffffffff
    return ((value << bits) & 0xffffffffffffffff) | (value >> (64 - bits))


def compute_chain(part, seed, data):
    prime = 0x100000001B3
    value = (seed ^ ((part * prime) & 0xffffffffffffffff)) & 0xffffffffffffffff

    for b in data:
        value = rol64(((value ^ b) * prime) & 0xffffffffffffffff, 13)

    value = (value ^ (value >> 33)) & 0xffffffffffffffff
    value = (value * 0xFF51AFD7ED558CCD) & 0xffffffffffffffff
    value = (value ^ (value >> 33)) & 0xffffffffffffffff
    return value


def rc4_stream(key, size):
    s = list(range(256))
    j = 0

    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xff
        s[i], s[j] = s[j], s[i]

    out = []
    i = 0
    j = 0

    for _ in range(size):
        i = (i + 1) & 0xff
        j = (j + s[i]) & 0xff
        s[i], s[j] = s[j], s[i]
        out.append(s[(s[i] + s[j]) & 0xff])

    return out


def build_part4_key(chain, fragment4):
    key = bytearray(14)
    low = chain & 0xffffffff

    for i, ch in enumerate(b"Secu"):
        key[i] = ((low >> (8 * i)) & 0xff) ^ ch

    key[4:12] = b"E72TVGSj"
    key[12] = fragment4[0] ^ ord("R")
    key[13] = fragment4[1] ^ ord("V")

    return bytes(key)


def verify_part4_first4(first4, ks):
    d0 = first4[0] ^ ks[0]
    d1 = first4[1] ^ ks[1]
    d2 = first4[2] ^ ks[2]
    d3 = first4[3] ^ ks[3]

    value = ((((d2 ^ (d1 << 3) ^ (d0 << 6)) << 12) ^ (d3 << 9)) & 0x3ff0000)
    return value == 0xe30000


def derive_known_parts(sig_hash):
    java_target = b"SB1QTIi"

    part1 = bytes(((b ^ 7) - 1) & 0xff for b in java_target)
    native_part1_return = bytes(java_target[i] ^ sig_hash[i % 4] for i in range(len(java_target)))

    fragment2 = bytes(x ^ 23 for x in [82, 32, 37, 67])
    fragment3 = bytes((i ^ x ^ 90) & 0xff for i, x in enumerate([12, 28, 11, 51]))
    fragment4 = b"RV"

    part2 = bytes([
        0x1a ^ fragment2[0],
        0x64 ^ fragment2[1],
        0x55 ^ fragment2[2],
        0x32 ^ fragment2[3],
        0x7d ^ fragment2[0],
    ])

    part3 = bytes([
        ((0x9c - fragment3[0]) & 0xff) ^ 0x19,
        ((0xc6 - fragment3[1]) & 0xff) ^ 0x19,
        ((0x81 - fragment3[2]) & 0xff) ^ 0x19,
        ((0xe4 - fragment3[3]) & 0xff) ^ 0x19,
        ((0x80 - fragment3[0]) & 0xff) ^ 0x19,
    ])

    chain = compute_chain(1, 1597463007, native_part1_return)
    chain = compute_chain(2, chain, fragment2)
    chain = compute_chain(3, chain, fragment3)

    ks = rc4_stream(build_part4_key(chain, fragment4), 4)

    return part1, part2, part3, ks


WORKER_DATA = None


def init_worker(prefix, target_hash, charset, ks):
    global WORKER_DATA
    WORKER_DATA = (prefix, target_hash, charset, ks)


def worker(first_char):
    prefix, target_hash, charset, ks = WORKER_DATA
    base = hashlib.sha256()
    base.update(prefix)

    for c2 in charset:
        for c3 in charset:
            first4 = ("_" + first_char + c2 + c3).encode()

            if not verify_part4_first4(first4, ks):
                continue

            state = base.copy()
            state.update(first4)

            for tail in itertools.product(charset, repeat=3):
                last3 = "".join(tail).encode()
                h = state.copy()
                h.update(last3 + b"}")

                if h.hexdigest() == target_hash:
                    return (prefix + first4 + last3 + b"}").decode()

    return None


def solve(apk_path):
    apk_data = apk_path.read_bytes()

    sig_hash = extract_v2_cert_sha256(apk_data)
    target_hash = extract_target_hash(apk_data)

    part1, part2, part3, ks = derive_known_parts(sig_hash)
    prefix = b"ISCC{" + part1 + part2 + part3

    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    workers = max(1, min(multiprocessing.cpu_count(), len(charset)))

    with multiprocessing.Pool(
        processes=workers,
        initializer=init_worker,
        initargs=(prefix, target_hash, charset, ks),
    ) as pool:
        for result in pool.imap_unordered(worker, charset, chunksize=1):
            if result:
                pool.terminate()
                return result

    raise RuntimeError("flag not found")


if __name__ == "__main__":
    apk_path = pick_apk_path()
    print(solve(apk_path))
```

第二部分：WP文件下载

灰签名回廊-Writeup.md
