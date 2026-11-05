# Dual Protection 逆向分析

## 题目信息

- 题目名称：Dual Protection（双重保护）
- 平台：ISCC 2025
- 类型：Reverse
-  flag 长度：36 字符

---

## 1. 题目总览

拿到 `Dual Protection.exe`，首先用 `file` 命令和 `strings` 快速探测：

```bash
file Dual Protection.exe  
# PE32 executable (console) Intel 80386, for MS Windows

strings Dual Protection.exe | grep -E "Input|Correct|Wrong|flag|Flag"
# Input Flag:
# Correct.
# Wrong.
```

确认是 Windows 控制台程序，读取用户输入后判断对错。

IDA 打开后看到三个关键函数：

| 地址 | 大小 | 作用 |
|------|------|------|
| `0x401000` | 0x48 | 字节变换函数 1 |
| `0x401050` | 0x7B | 字节变换函数 2 |
| `0x4010D0` | 0x23 | 字节变换函数 3 |
| `0x4013EC` | — | main 函数（含解密引擎） |

---

## 2. 第一层保护：三层字节混淆

main 函数中读取输入后，先检查长度是否为 `0x24`（36），然后对每个字节依次经过三个变换函数处理。

### 2.1 变换函数 1（0x401000）

IDA 反编译结果：

```c
int __stdcall sub_401000(int buf, int idx) {
    *(_BYTE *)(idx + buf) = ((*(_BYTE *)(idx + buf) ^ 0x55) >> 6) 
                           | (4 * (*(_BYTE *)(idx + buf) ^ 0x55));
    *(_BYTE *)(idx + buf) += idx;
    return idx + buf;
}
```

这里 `a >> 6 | 4 * a` 本质是 **8 位循环左移 2 位**（ROL2）。所以：

```
x = buf[i] ^ 0x55
x = ROL2(x)
buf[i] = (x + i) & 0xFF
```

### 2.2 变换函数 2（0x401050）

```c
int __stdcall sub_401050(int buf, int idx) {
    char key[8] = {0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF};
    *(_BYTE *)(idx + buf) ^= key[idx % 8];
    *(_BYTE *)(idx + buf) += 127;
    return *(unsigned char *)(idx + buf) + 127;
}
```

等价于：

```
buf[i] ^= key[i & 7]
buf[i] = (buf[i] + 0x7F) & 0xFF
```

其中 key 是一个 8 字节循环异或表：`[0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF]`。

### 2.3 变换函数 3（0x4010D0）

```c
int __stdcall sub_4010D0(int buf, int idx) {
    *(_BYTE *)(idx + buf) = (idx + 32) ^ *(unsigned char *)(idx + buf);
    return (idx + 32) ^ *(unsigned char *)(idx + buf);
}
```

等价于：

```
buf[i] ^= (i + 0x20) & 0xFF
```

### 2.4 正向变换总结

```python
# 三个变换依次作用于 buf[i]
# T1
x = buf[i] ^ 0x55
x = ROL2(x)
buf[i] = (x + i) & 0xFF

# T2
buf[i] ^= key[i & 7]
buf[i] = (buf[i] + 0x7F) & 0xFF

# T3
buf[i] ^= (i + 0x20) & 0xFF
```

---

## 3. 第二层保护：LCG 解密引擎

三层变换结束后，输入并没有被直接拿去和常量比较。main 函数后半段才是真正的校验逻辑：
它使用 `VirtualAlloc` 申请可执行内存，复制一段加密的 shellcode
进去，用 LCG（线性同余生成器）解密，然后跳转执行。

### 3.1 反调试保护

在执行解密前，main 中有一段反调试代码：

```c
DWORD seed = 0xDEADBEEF;
BOOL dbg = FALSE;
GetCurrentProcess();
CheckRemoteDebuggerPresent(GetCurrentProcess(), &dbg);
if (dbg) seed = 0x0BADF00D;
```

如果检测到调试器，seed 会被篡改为 `0x0BADF00D`，导致后续 LCG 解密产生完全不同的 shellcode，逻辑被破坏。

### 3.2 密文位置和大小

加密 shellcode 位于 `0x40FEE0`，大小 `0x118`（280 字节），存储在 PE 文件的 `.data` 节。

### 3.3 LCG 算法

```c
state = seed;  // 0xDEADBEEF
for (each byte) {
    state = state * 0x19660D + 0x3C6EF35F;  // 32-bit LCG
    output[i] = encrypted[i] ^ (state >> 24);  // 取高8位作密钥流
}
```

这是一个典型的 LCG 流密码：用线性同余发生器产生伪随机字节流，与密文异或。

---

## 4. 解密 shellcode 分析

用 Python 实现 LCG 解密后，得到一段 x86 shellcode：

```asm
; 开头反调试
mov eax, fs:[0x30]         ; PEB
mov bl, byte ptr [eax+2]   ; BeingDebugged flag
cmp bl, 0
jne error_path

; 主校验逻辑
mov esi, [esp+4]           ; 指向变换后的输入
xor ecx, ecx

; 逐字节比较（共36字节）
mov al, [esi+0x00]         ; buf[0]
xor al, 0xC1               ; 与常数比较
or  cl, al                 ; 累积到 cl

mov al, [esi+0x01]
xor al, 0x8D
or  cl, al
; ... 重复至第35字节 ...

mov al, [esi+0x23]
xor al, 0x79
or  cl, al

xor eax, eax
test cl, cl
sete al                    ; 全等则返回1（成功）
ret
```

本质就是：**将变换后的 36 字节与一组固定常量逐字节异或，若结果全为 0 则通过**。

从 shellcode 中提取这 36 个比较常量：

```
C1 8D A9 81 8F 54 E3 F0 36 30 4E E5 57 DD 8C 2C
E9 45 42 E9 BB A4 7F A1 49 41 6D 61 57 AD 67 41
1A 09 19 79
```

---

## 5. "Dual Protection" 名字的含义

至此可以看到"双重保护"的两个层面：

| 层面 | 保护方式 | 位置 |
|------|---------|------|
| 第一重 | 三层逐字节混淆变换 | 静态代码 `0x401000~0x4010D0` |
| 第二重 | LCG 加密 shellcode + 反调试 | 动态解密执行 `VirtualAlloc` 区域 |

输入必须依次穿透这两层才能通过校验。

---

## 6. 逆推 Flag

从 shellcode 提取到 36 个目标常量后，从后往前逆向三层变换即可恢复原始输入。

### 6.1 逆推公式

```
T3 逆运算：buf[i] ^= (i + 0x20)
T2 逆运算：buf[i] = (buf[i] - 0x7F) & 0xFF; buf[i] ^= key[i & 7]
T1 逆运算：buf[i] = (buf[i] - i) & 0xFF; buf[i] = ROR2(buf[i]); buf[i] ^= 0x55
```

### 6.2 求解脚本

完整的 `solve.py` 实现了完整求解流程：

```python
#!/usr/bin/env python3
import struct

# === PE 解析 ===
def read_pe_bytes(filepath, rva, size):
    with open(filepath, 'rb') as f:
        dos = f.read(0x40)
        e_lfanew = struct.unpack_from('<I', dos, 0x3C)[0]
        f.seek(e_lfanew)
        assert f.read(4) == b'PE\x00\x00'
        fh = f.read(20)
        num_sections = struct.unpack_from('<H', fh, 2)[0]
        opt_size = struct.unpack_from('<H', fh, 16)[0]
        f.read(opt_size)

        sections = []
        for _ in range(num_sections):
            raw = f.read(40)
            sections.append({
                'name': raw[:8].rstrip(b'\x00').decode(errors='replace'),
                'vaddr': struct.unpack_from('<I', raw, 12)[0],
                'vsize': struct.unpack_from('<I', raw, 8)[0],
                'rptr': struct.unpack_from('<I', raw, 20)[0],
                'rsize': struct.unpack_from('<I', raw, 16)[0],
            })

        for sec in sections:
            if sec['vaddr'] <= rva < sec['vaddr'] + sec['vsize']:
                offset = rva - sec['vaddr'] + sec['rptr']
                avail = min(size, sec['rptr'] + sec['rsize'] - offset)
                f.seek(offset)
                data = bytearray(f.read(avail))
                if len(data) < size:
                    data.extend(b'\x00' * (size - len(data)))
                return data
        raise ValueError(f"RVA 0x{rva:X} not found")

# === LCG 解密 ===
def lcg_decrypt(data, seed=0xDEADBEEF, mul=0x19660D, add=0x3C6EF35F):
    out = bytearray()
    state = seed
    for b in data:
        state = (state * mul + add) & 0xFFFFFFFF
        out.append(b ^ ((state >> 24) & 0xFF))
    return out

# === 提取比较常量 ===
def extract_targets(shellcode):
    targets = [0] * 36
    i = 0
    while i < len(shellcode) - 4:
        if shellcode[i] == 0x8A and shellcode[i+1] == 0x46 and shellcode[i+3] == 0x34:
            pos = shellcode[i+2]
            if pos < 36:
                targets[pos] = shellcode[i+4]
                i += 5
                continue
        i += 1
    return targets

# === 主流程 ===
def main():
    key_tbl = [0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF]

    # 1. 从 PE 读取加密 shellcode
    encrypted = read_pe_bytes("Dual Protection.exe", 0xFEE0, 0x118)

    # 2. LCG 解密
    shellcode = lcg_decrypt(encrypted)

    # 3. 提取 36 个比较常量
    target = extract_targets(shellcode)

    # 4. 逆向三层变换
    flag = bytearray(target)

    # 逆 T3
    for i in range(36):
        flag[i] ^= (i + 0x20) & 0xFF

    # 逆 T2
    for i in range(36):
        flag[i] = (flag[i] - 0x7F) & 0xFF
        flag[i] ^= key_tbl[i & 7]

    # 逆 T1
    for i in range(36):
        x = (flag[i] - i) & 0xFF
        x = ((x >> 2) | (x << 6)) & 0xFF  # ROR2
        x ^= 0x55
        flag[i] = x

    print(f"FLAG: {flag.decode()}")

if __name__ == "__main__":
    main()
```

运行输出：

```
FLAG: ISCC{@4y4<?^M&mB[y0QN|)-gxHwM2+)?bO}
```

---

## 7. 验证

在控制台用正确 flag 运行程序：

```bash
echo 'ISCC{@4y4<?^M&mB[y0QN|)-gxHwM2+)?bO}' | ./Dual\ Protection.exe
```

输出：

```
Input Flag: Correct.
```

验证通过。

---

## 8. 技术要点总结

| 要点 | 说明 |
|------|------|
| 混淆链 | ROL2 + XOR + ADD 组合，三层递进 |
| 循环异或表 | 8 字节 key：`0x12,0x34,0x56,0x78,0x90,0xAB,0xCD,0xEF` |
| LCG 参数 | `x_{n+1} = x_n * 0x19660D + 0x3C6EF35F` |
| 反调试 | `PEB.BeingDebugged` 检查 + seed 篡改 |
| 密文大小 | 0x118 字节，RVA 0xFEE0 |
| 目标比较 | 36 字节逐位 XOR + OR 累积 |
| 最终 flag | `ISCC{@4y4<?^M&mB[y0QN|)-gxHwM2+)?bO}` |
