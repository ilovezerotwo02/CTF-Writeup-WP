# EasyRevCheckin — Writeup

**题目类别：** Reverse / 逆向（签到）  
**题目名称：** EasyRevCheckin（题面标题显示为 `.. -.. .-`）  
**附件：** `EasyRevCheckin.exe`  
**分值：** 864 pts  
**Flag 格式：** `HTUCTF{...}`

## 题目描述

> 如呼吸般简单的签到题，谜底不就在谜面上吗？

## 解题思路

谜面本身就是提示：

1. 题目标题 `.. -.. .-` 是**摩斯电码**：`..` = I、`-..` = D、`.-` = A，合起来就是 **IDA**，提示用 IDA 做静态分析；
2. “谜底就在谜面上”——这题几乎不需要逆向算法，直接看程序里有哪些字符串即可；
3. 程序自己也把提示写进了数据里：`[+] Hint: strings and cross-references are your friends.`

## 解题过程

### 1. 文件特征

```bash
$ ls -la EasyRevCheckin.exe
-rwxr-xr-x 2048 EasyRevCheckin.exe
```

x86-64 PE，**只有 2048 字节**。节表：

| 节 | raw 偏移 | raw 大小 |
| --- | --- | --- |
| `.text` | 0x400 | 0x200 |
| `.rdata` | 0x600 | 0x200 |

文件尾正好落在 0x800，**无 overlay（附加数据 0 字节）**，也没有壳或加密段。

### 2. 代码是“空壳”

反汇编整个 `.text`：

```asm
140001000: 31 c0    xor eax, eax
140001002: c3       ret
```

有效指令只有 3 个字节：清零返回值后直接返回。实际运行 `./EasyRevCheckin.exe` **不会输出任何内容**，退出码为 0——它只是个装载容器，动态调试（x64dbg、IDA 调试器）看不到任何信息，只能走静态。

### 3. 所有内容都在 `.rdata`

```bash
$ strings -a -n 3 EasyRevCheckin.exe
Easy Rev Check-in
[+] Welcome to the beginner reverse challenge!
[+] Check-in complete. Now inspect this program with IDA.
[+] Hint: strings and cross-references are your friends.
HTUCTF{ida_static_analysis_is_easy}
```

IDA 里打开（或 `objdump -s -j .rdata`）能看到完整的数据布局：

```text
140002000  "Easy Rev Check-in"
140002014  "[+] Welcome to the beginner reverse challenge!"
140002041  "[+] Check-in complete. Now inspect this program with IDA."
140002078  "[+] Hint: strings and cross-references are your friends."
1400020b6  "HTUCTF{ida_static_analysis_is_easy}"      <- flag
```

flag 位于 RVA `0x1400020b6`、文件偏移 `0x6b4`。

### 4. 交叉验证

用正则在整份文件里扫描 `HTUCTF{...}`，**只命中一次**，不存在用来干扰的假 flag：

```python
import re
data = open("EasyRevCheckin.exe", "rb").read()
print(re.findall(rb"HTUCTF\{[^}]*\}", data))
# [b'HTUCTF{ida_static_analysis_is_easy}']
```

## Flag

```text
HTUCTF{ida_static_analysis_is_easy}
```

## 小结

这是道纯粹的签到题，考点是**别被空壳程序唬住**：入口只有 `xor eax,eax; ret`，运行毫无输出，容易让人以为要动调或脱壳。实际上题目描述（“谜底就在谜面上”）、标题（摩斯电码 IDA）、程序内提示（strings and cross-references）三重暗示都在指向同一件事——打开 IDA 看字符串。一条 `strings` 命令即可出 flag：

```bash
strings -a EasyRevCheckin.exe | grep HTUCTF
```

> 注：Flag 来自静态字符串提取，并已用全文件正则扫描确认唯一。
