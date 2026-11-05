# 北极星混淆 解题记录

**题目附件**: `traditional_re` (64-bit ELF, x86-64, stripped, PIE)
**考点**: splitmix64 白盒混淆 + Chow's white-box AES
**Flag**: `ISCC{real_whitebox_AES_with_polaris_mir}`

---

## 0x00 初探

拿到文件先跑一下:

```
$ ./traditional_re
anything
no
```

无论输什么都是 `no`。查一下文件信息和导入表:

```
$ file traditional_re
traditional_re: ELF 64-bit LSB pie executable, x86-64, ...
$ readelf -s traditional_re
# stripped, 没有符号
```

导入有: `ptrace`, `open`, `read`, `write`, `clock_gettime`, `getppid`, `memset`, `memcpy`。

明显有反调试(ptrace检测)，以及读文件操作。

## 0x01 结构分析

IDA 打开，函数窗口有 ~990 个函数。大量短函数是控制流平坦化混淆的产物。

关键发现：`.data.rel.ro` 段有 5 组指针数组，指向 `.rodata` 里的加密数据:

| 数组地址 | 指针数 | 指向区域 | 输出地址 | 输出大小 |
|---------|-------|---------|---------|---------|
| 0x183BC0 | 5 | 0x14E0C0 | 0x184C80 | 48 |
| 0x183BF0 | 11 | 0x14E200 | 0x184CC0 | 40960 |
| 0x183C50 | 13 | 0x158440 | 0x18ECC0 | 147456 |
| 0x183CC0 | 7 | 0x17C6C0 | 0x1B2CC0 | 4096 |
| 0x183D00 | 9 | 0x17D840 | 0x1B3CC0 | 16384 |

通过交叉引用找到 `sub_CF710` 调用 `sub_14CFF0` 完成 5 次解密。这就是核心解密函数。

## 0x02 核心算法逆向

### splitmix64 PRNG (`sub_14D250`, 0x14D250)

```
state -= 0x61C8864680B583EB        // 等价于 += 0x9E3779B97F4A7C15
z     = ((state >> 30) ^ state) * 0xBF58476D1CE4E5B9
z     = ((z >> 27) ^ z) * 0x94D049BB133111EB
return (z >> 31) ^ z
```

这是一个标准 splitmix64，输入 64-bit seed，每步产生 64-bit 伪随机数。

### 置换-XOR 解密 (`sub_14CFF0`, 0x14CFF0)

```
v14 = init(key, length, byte_param)     // 4轮 splitmix64 混合
step = coprime(length, v14)              // 置换步长
off  = hash(v14, length) >> 19 % length  // 起始偏移

for i in range(length):
    dst = (off + step * i) % length      // 目标位置
    src_idx  = (src_base + src_step * i) % n_src
    src_byte = source_arrays[src_idx][i // n_src]
    prng_byte = splitmix64(state) >> (8 * (i & 7)) & 0xFF
    key_byte  = (61*i - 89*dst) & 0xFF ^ prng_byte
    output[dst] = src_byte ^ key_byte
```

本质是一个**置换网络 + 异或流密码**。输入来自多个指针数组的字节交错，经过置换和异或得到输出。

## 0x03 GDB 调参

关键技术参数需要通过动态调试获取:

```
$ gdb -batch -ex "set disable-randomization on" \
       -ex "file traditional_re" \
       -ex "break *0x555555554000+0xcf710" \
       -ex "run" \
       -ex "info registers rdi"
```

结果: `rdi = 0x14`，即字节参数为 20。

`finish` 跳出后 dump 内存验证:

```
(gdb) x/48bx 0x555555554000+0x184CC0
0x5555556d8cc0: 0x07 0xe1 0x2f 0xaf 0x04 0x62 0x4e 0x17
```

## 0x04 Python 实现

按照逆向结果实现解密:

```python
M = 0xFFFFFFFFFFFFFFFF

def splitmix(state):
    state[0] = (state[0] - 0x61C8864680B583EB) & M
    z = state[0]
    z = (((z >> 30) ^ z) * 0xBF58476D1CE4E5B9) & M
    z = (((z >> 27) ^ z) * 0x94D049BB133111EB) & M
    return ((z >> 31) ^ z) & M

# ... 完整实现见附录
```

Python 输出与 GDB dump 一致，验证实现正确。

## 0x05 第一层结果

解密后的区段2 (40960 bytes) 偏移 54 处:

```
62 6c 75 7b   -> "blu{"
c5 18 60 06 43 b4 8a 1a bc 2d db 21 8f 92 c6 fd 6b c5 e1 f4 bb  -> 21 bytes encrypted
7d            -> "}"
```

`blu{` 和 `}` 可读，中间 21 字节被第二层保护。

区段 2-5 总大小约 200KB，结构符合 Chow 方案白盒 AES 的 T-box 布局。

## 0x06 DFA 恢复 AES 密钥

用 `LD_PRELOAD` 写 oracle，在 `write()` 中 dump 栈上加密结果 (偏移 `trbp - 0x1A80` 的前 36 字节)。

对第 7 轮 T3 表 (区段3, `0x18ECC0`) 的每个 T-box 入口做 XOR 0x01 故障注入，收集故障密文对。

DFA 原理: 对 AES 第 9 轮 SubBytes 前注入单字节故障，根据故障传播模式 (4 字节差异) 反推最后轮密钥。

```
收集故障对 → 按列组划分 → 枚举密钥字节 → 匹配列混合模式 → 得到 16 字节最后轮密钥
→ 逆密钥扩展 → AES-128 主密钥
```

恢复结果:

```
AES-128 key = 8f4d2a91c736e05bb8a4f01762de39ac
验证: AES_ECB(0x00*16) = 34a18e6249552a855747d6d53781b589  ✓
```

## 0x07 最终 Flag

用该密钥解密 BSS 中的 48 字节密文:

```
c6bae55d0275ac4f4a5da18fda143fa9
486079b58b82039a59c160821547e384
25af09ae621b3fe309e45f929f64002c
```

```python
>>> from Crypto.Cipher import AES
>>> k = bytes.fromhex('8f4d2a91c736e05bb8a4f01762de39ac')
>>> c = bytes.fromhex('c6bae55d0275ac4f4a5da18fda143fa9'
...                   '486079b58b82039a59c160821547e384'
...                   '25af09ae621b3fe309e45f929f64002c')
>>> AES.new(k, AES.MODE_ECB).decrypt(c)
b'ISCC{real_whitebox_AES_with_polaris_mir}\x08\x08\x08\x08\x08\x08\x08\x08'
```

去 PKCS#7 padding 后:

```
Flag: ISCC{real_whitebox_AES_with_polaris_mir}
```

## 0x08 题目解谜

原诗"白鹤山人如鹤白"出自元代虞集的《白鹤观》。题目将"白鹤观"改为"白盒观"（鹤→盒），谐音暗示 **white-box cryptography**，对应程序中的白盒 AES 实现。

---

## 附: 完整脚本

```python
import struct
from Crypto.Cipher import AES

M = 0xFFFFFFFFFFFFFFFF

class SM:
    """splitmix64"""
    def __init__(self, seed):
        self.s = seed & M
    def next(self):
        self.s = (self.s - 0x61C8864680B583EB) & M
        z = self.s
        z = (((z >> 30) ^ z) * 0xBF58476D1CE4E5B9) & M
        z = (((z >> 27) ^ z) * 0x94D049BB133111EB) & M
        return ((z >> 31) ^ z) & M

def gcd(a, b):
    while b: a, b = b, a % b
    return a

def coprime(mod, val):
    v = ((val >> 17) | 1) % mod
    if v == 0: v = 1
    while gcd(v, mod) != 1:
        v = (v + 2) % mod
        if v == 0: v = 1
    return v

def init(key, length, bp):
    v8 = ((0x6A09E667F3BCC909 * bp) ^ (0xD1342543DE82EF95 * length) ^ key) & M
    v7 = 0
    for _ in range(4):
        r = SM(v7 ^ v8)
        o = r.next()
        v8 = r.s
        v7 = (v7 ^ o) & M
    return v7

def decrypt(src, n_src, size, key):
    k = key & M
    v14 = init(k, size, 0x14)
    step = coprime(size, v14)
    off = (init((v14 ^ 0xA5A5A5A55A5A5A5A) & M, size, 0) >> 19) % size
    ss = coprime(n_src, k)
    s0 = (k >> 23) % n_src
    r = SM(v14)
    out = bytearray(size)
    for i in range(size):
        d = (off + step * i) % size
        si = (s0 + ss * i) % n_src
        bi = i // n_src
        x = ((61*i - 89*d) & 0xFF) ^ ((r.next() >> (8*(i&7))) & 0xFF)
        out[d] = src[si][bi] ^ x
    return bytes(out)

if __name__ == '__main__':
    with open('traditional_re', 'rb') as f:
        elf = f.read()

    # 解密区段1 (48 bytes)
    src1 = [bytearray(elf[a:a+10]) for a in [0x14e0c0, 0x14e100, 0x14e140, 0x14e180, 0x14e1c0]]
    sec1 = decrypt(src1, 5, 48, 0x61F29C0D87A453B1)

    # 解密区段2 (40960 bytes)
    src2 = [bytearray(elf[0x14e200+i*0xec0:0x14e200+i*0xec0+3724]) for i in range(11)]
    sec2 = decrypt(src2, 11, 40960, 0xD3B5407C19EA8F26)

    # 验证
    assert sec2[54:58] == b'blu{'
    print('blu{' + sec2[58:79].hex() + '}')

    # AES 解密 (DFA 恢复的密钥)
    key = bytes.fromhex('8f4d2a91c736e05bb8a4f01762de39ac')
    ct = bytes.fromhex('c6bae55d0275ac4f4a5da18fda143fa9'
                       '486079b58b82039a59c160821547e384'
                       '25af09ae621b3fe309e45f929f64002c')
    pt = AES.new(key, AES.MODE_ECB).decrypt(ct)
    flag = pt[:-pt[-1]].decode()
    print('flag:', flag)
```

运行：

```
$ python3 solve.py
blu{c518600643b48a1abc2ddb218f92c6fd6bc5e1f4bb}
flag: ISCC{real_whitebox_AES_with_polaris_mir}
```
