# 进击的x64 — Writeup

**题目类别：** Reverse / 逆向  
**题目名称：** 进击的x64  
**附件：** `challenge.exe`  
**Flag 格式：** `HTUCTF{...}`

## 题目描述

程序运行后输出：

```text
========================================
  Welcome to RE Beginner Challenge!
========================================
Enter the flag:
```

输入正确 flag 时打印 `Correct! Flag: %s`，错误时打印 `Wrong flag. Keep trying!`，最后都提示 `Press any key to exit...`。

## 解题思路

这是一道 x64 的编码比较型 crackme：程序把**密文在栈上用立即数拼出来**，再用一个“看起来很复杂”的花指令函数做掩护，实际校验只是 **XOR 0x2A** 后逐字节比较。静态把 XOR 反演掉就能直接得到 flag；当然也可以输入任意 38 字符、在比较处动态下断点把内存里解密后的目标串 dump 出来。

## 解题过程

### 1. 文件特征

```text
x86-64 PE，147456 字节，ImageBase = 0x140000000，入口 RVA = 0x18f0（CRT 启动）
.text  0x1000 / 0x16510   .rdata 0x18000 / 0xaa7a
.data  0x23000 / 0x1bb0   .pdata / .fptable / .reloc
```

导入表来自 `KERNEL32.dll`，除 CRT 运行时所需外，与校验相关的只有两个：

```text
IsDebuggerPresent
GetTickCount      <- 被校验代码直接调用，用于制造干扰
```

主函数 `main` 位于 `0x1400010B0`（MSVC x64 栈布局，带 `__security_cookie` 栈溢出保护）。

### 2. 密文在栈上用立即数拼装

`main` 开头把 38 字节密文拆成若干 `mov dword` 立即数写到栈上 `[rsp+0x20..0x45]`：

```asm
1400010cc: mov dword ptr [rsp+0x20], 0x697f7e62
1400010d4: mov dword ptr [rsp+0x24], 0x5d516c7e
1400010dc: mov dword ptr [rsp+0x28], 0x1a494619
1400010e4: mov dword ptr [rsp+0x2c], 0x5e754f47
1400010ec: mov dword ptr [rsp+0x30], 0x1958751a
1400010f4: mov dword ptr [rsp+0x34], 0x5958195c
1400010fc: mov dword ptr [rsp+0x38], 0x44197519
140001104: mov dword ptr [rsp+0x3c], 0x19441b4d
140001114: mov word  ptr [rsp+0x44], 0x574d
```

按小端还原出完整密文（38 字节，`0x26`）：

```text
62 7e 7f 69 7e 6c 51 5d 19 46 49 1a 47 4f 75 5e
1a 75 58 19 5c 19 58 59 19 75 19 44 4d 1b 44 19
19 58 1b 44 4d 57
```

### 3. 花指令：GetTickCount + 无效计算

密文拼完后紧接着有这么一段：

```asm
14000111b: call qword ptr [rip+0x16ee7]   ; GetTickCount()
140001121: movzx ecx, al
140001124: call 0x140001010               ; "复杂计算"函数
140001129: mov eax, dword ptr [rsp+0x40]  ; 返回值立刻被覆盖
```

`0x140001010` 里是一大段迷惑性运算：10 轮 `imul ecx, 0x3e39b193` 迭代 + `btr` 清符号位、`0x3*eax+7`、`xor 0x5a`、魔数 `0xf0f0f0f1`/`0x78787879` 做除法取模……看起来像在生成密钥。**但它的返回值（eax）在每次调用后都被立即丢弃**，总共 3 处调用（解密前 1 处、长度判断后 1 处、比较前 1 处）全是同样处理。

结论：这是纯花指令，与 flag 无关。抗静态分析的手段还包括把密文拆成立即数（`strings` 里看不到任何 flag 痕迹，全文件搜 `HTUCTF` 命中 0 次）。

### 4. 真正的解密：整体 XOR 0x2A

密文随后被搬到 `[rbp-0x30]` 缓冲区并解密：

```asm
14000112d: movdqa xmm1, xmmword ptr [rip+0x172eb]  ; .rdata 0x140018420 处 16 字节密钥
140001155: xorps xmm0, xmm2                        ; 前 16 字节 xor 密钥
14000115c: xorps xmm1, xmm3                        ; 次 16 字节 xor 密钥
140001170: xor byte ptr [rbp+rax-0x30], 0x2a       ; rax = 0x20..0x26，尾部 7 字节 xor 0x2a
```

查看 `0x140018420` 处的"密钥"：

```text
2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a 2a
```

16 字节全是 `0x2A`。于是三层防护（XMM 密钥轮 + 尾部循环 + 立即数拼装）坍缩成一个操作：

```text
明文[i] = 密文[i] ^ 0x2A    （i = 0..37）
```

### 5. 校验逻辑

解密完成后程序打印 banner 和 `Enter the flag: `，然后：

```asm
1400011ea: lea rcx, [rsp+0x50]        ; 输入缓冲
1400011ef: mov edx, 0x80              ; fgets(buf, 0x80, stdin)
140001247: call strcspn(buf, "\n")    ; 去掉行尾换行
140001264: cmp rax, 0x26              ; strlen(input) == 0x26 = 38 ?
140001270: movzx ecx, byte [rsp+rax+0x50]
140001275: cmp byte [rbp+rax-0x30], cl ; 逐字节比较输入与解密缓冲
14000128f: lea rcx, "Correct! Flag: %s\n"
14000128b: lea rdx, [rbp-0x30]        ; 把解密后的目标串作为 flag 打印
```

即：**输入长度必须是 38，且与解密结果逐字节相同**；通过后程序把解密缓冲本身当作 flag 打印出来——所以 flag 就是 XOR 0x2A 的逆运算结果。退出码：正确返回 0（`ebx^1`），错误返回 1。

### 6. 静态解密

```python
ct = bytes.fromhex(
    "627e7f697e6c515d1946491a474f755e"
    "1a7558195c195859197519444d1b4419"
    "19581b444d57"
)                      # 38 字节，来自栈上立即数
pt = bytes(b ^ 0x2A for b in ct)
print(pt.decode())
# HTUCTF{w3lc0me_t0_r3v3rs3_3ng1n33r1ng}
```

### 7. 实机验证

```bash
$ printf 'HTUCTF{w3lc0me_t0_r3v3rs3_3ng1n33r1ng}\n\n' | ./challenge.exe
========================================
  Welcome to RE Beginner Challenge!
========================================
Enter the flag:
Correct! Flag: HTUCTF{w3lc0me_t0_r3v3rs3_3ng1n33r1ng}

Press any key to exit...        # exit 0

$ printf 'wrong\n\n' | ./challenge.exe
Enter the flag:
Wrong flag. Keep trying!        # exit 1
```

正确输入打印 `Correct! Flag: ...` 且退出码 0，错误输入退出码 1，flag 无歧义。

## Flag

```text
HTUCTF{w3lc0me_t0_r3v3rs3_3ng1n33r1ng}
```

## 小结

这题的三层“防护”都是纸老虎：

1. **立即数拼密文**——躲开 `strings`，但反汇编里一眼可见；
2. **花指令函数**——GetTickCount 的 AL 喂进一段 LCG+魔数除法的复杂运算，返回值却从未被使用，直接跳过即可；
3. **XMM 密钥 XOR + 尾部循环 XOR**——密钥是 16 个 `0x2A`，与尾部常量一致，整体退化为单字节 XOR 0x2A。

所以最佳解法是静态：把栈上的立即数抄下来整体 `^ 0x2A`。如果不想抄立即数，备选方案是动态——随便输 38 个字符，在 `0x140001275`（比较处）下断点，把 `[rbp-0x30]` 的 38 字节 dump 出来，同样直接得到 flag。

> 注：Flag 已通过运行程序实机验证（正确/错误双路径）。
