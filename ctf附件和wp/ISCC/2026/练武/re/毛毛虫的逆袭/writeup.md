# ISCC 毛毛虫的逆袭 (The Caterpillar's Counterattack) Writeup

**Category:** Reverse Engineering  
**Difficulty:** 100  
**Solves:** 2238  
**Flag:** `ISCC{J'"D* `p6?B}sWNgBe)i}`

---

## 1. 程序概览

| 文件 | 说明 |
|------|------|
| `caterpillar36.exe` | UPX 加壳的原始程序 (111KB) |
| `caterpillar36_unpacked.exe` | UPX 脱壳后的程序 (266KB) |

程序是一个 x86-64 Windows 控制台程序，接受格式为 `ISCC{20_chars}` 的输入，输出 "Success!" 或 "Fail!"。

---

## 2. 静态分析

### 2.1 输入验证

主函数 `main` (0x140006D30) 的处理流程：

1. 读取输入，检查格式 `ISCC{xxxxxxxxxxxxxxxxxxxx}`
2. 提取花括号内的 20 个字符作为 flag 内容
3. 经过两项验证（OR 关系）：
   - **路径 1：LCG 流密码** — 对 flag 进行 LCG 加密后与固定密文比较
   - **路径 2：SHA-256 哈希** — 将 flag 分成两个 10 字符的半段分别做 SHA-256，与存储的哈希值比较
4. 任一路径通过即输出 "Success!"

### 2.2 LCG 路径

LCG 采用标准的 BSD LCG 参数：

```
state = (1103515245 * state + 12345) mod 2^32
初始 state = 36
```

加密过程：

```python
state = 36
for i in range(20):
    state = (1103515245 * state + 12345) & 0xFFFFFFFF
    key = ((state >> 24) & 0xFF) % 95    # ★ 关键在这里！
    encoded[i] = ((plain[i] - 32) + key) % 95 + 32
```

将加密结果与内存中的固定密文比较：
`*Y{4ZNrxfAYO,a_za&XG` (位于 0x14003F018)

### 2.3 SHA-256 路径

当程序运行时间超过 5 秒时，执行 SHA-256 路径：

- `SHA256(flag[0:10])` 与 `7c9a4772c5c1b43f5ccee4e81f46a33aa5a80ffb7d232ae5a118e80a7d558777` 比较
- `SHA256(flag[10:20])` 与 `0fc7f97b5dcd75e6c999ec614bd5522338ecc8fe3a2f7954a3536187d5ccc69d` 比较

SHA-256 实现为标准实现（初始常量验证正确）。

---

## 3. 关键陷阱：IDA 反编译错误

本题最大的坑点在于 **IDA 的反编译结果与汇编代码不一致**。

### 反编译代码显示：

```c
// IDA F5 反编译结果
key = HIBYTE(v48) % 95
```

### 实际汇编代码：

```asm
mov ecx, r10d       ; ecx = LCG state
shr ecx, 24         ; ★ 提取 bits 24-31（高字节），不是 bits 8-15！
; ... mod 95 计算 ...
```

IDA 将 `shr ecx, 24` 错误地标注为 `HIBYTE()`。但 `HIBYTE` 宏提取的是 bits 8-15（第二字节），而实际代码提取的是 bits 24-31（**最高字节**）。

这个差异导致第一次推导出的 flag 错误，输入平台被拒。

---

## 4. 解题脚本

核心思路：从固定密文反向推导明文，关键是使用 `(state >> 24) & 0xFF` 而不是 `(state >> 8) & 0xFF`。

```python
#!/usr/bin/env python3
"""
ISCC 毛毛虫的逆袭 - Solve Script
"""
import hashlib

def solve():
    LCG_MUL = 1103515245
    LCG_ADD = 12345
    LCG_MOD = 1 << 32
    initial_state = 36
    ciphertext = b"*Y{4ZNrxfAYO,a_za&XG"

    state = initial_state
    flag = bytearray(20)

    for i in range(20):
        state = (LCG_MUL * state + LCG_ADD) & 0xFFFFFFFF
        # ★ 注意：使用 shr 24（bits 24-31），不是 HIBYTE（bits 8-15）
        key = ((state >> 24) & 0xFF) % 95
        flag[i] = ((ciphertext[i] - 32) - key) % 95 + 32

    flag_str = flag.decode("ascii")
    print(f"Flag: ISCC{{{flag_str}}}")

    # SHA-256 验证（LCG 路径和 SHA-256 路径应一致）
    h1 = hashlib.sha256(flag_str[:10].encode()).hexdigest()
    h2 = hashlib.sha256(flag_str[10:20].encode()).hexdigest()
    assert h1 == "7c9a4772c5c1b43f5ccee4e81f46a33aa5a80ffb7d232ae5a118e80a7d558777"
    assert h2 == "0fc7f97b5dcd75e6c999ec614bd5522338ecc8fe3a2f7954a3536187d5ccc69d"
    print("[+] SHA-256 verification OK")

if __name__ == "__main__":
    solve()
```

**运行结果：**

```
Flag: ISCC{J'"D* `p6?B}sWNgBe)i}
[+] SHA-256 verification OK
```

---

## 5. 验证

使用脱壳后的程序验证：

```
> caterpillar36_unpacked.exe
Input flag in the format ISCC{xxxxxxxxxxxxxxxxxxxx}: ISCC{J'"D* `p6?B}sWNgBe)i}
Success!
```

程序输出 **"Success!"**，确认 flag 正确。

---

## 6. 总结

| 项目 | 内容 |
|------|------|
| **Flag** | `ISCC{J'"D* `p6?B}sWNgBe)i}` |
| **算法** | BSD LCG 流密码 (state >> 24 % 95) |
| **关键点** | IDA 反编译将 `shr 24` 误标为 `HIBYTE`，实际应取 bits 24-31 |
| **验证** | SHA-256 双路径验证与 LCG 路径结果一致 |
