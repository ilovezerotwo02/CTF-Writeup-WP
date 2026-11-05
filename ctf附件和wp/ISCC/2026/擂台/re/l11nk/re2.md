---
title: "l11nk"
category: reverse
flag_format: "ISCC{...}"
---

# l11nk

## Summary

题目给的是一个 `l11nk.o` 目标文件。这个文件不是常规可执行程序，真正的校验逻辑也不在普通函数流程里，而是藏在 ELF 可重定位文件的符号和重定位关系中。

核心思路是：先确认 `.lm.auth` / `.lm.auth.rel` 里存在大量重定位约束，再从真校验路径中提取密文字节，最后用线性异或流还原 flag。

## Solution

### 1. 文件类型分析

先看 ELF 头和 section：

```bash
readelf -h l11nk.o
readelf -S l11nk.o
```

关键输出如下：

```text
Class:                             ELF32
Data:                              2's complement, big endian
Type:                              REL (Relocatable file)
Machine:                           MIPS R3000
```

section 中最可疑的是：

```text
[ 3] .lm.auth       PROGBITS
[ 4] .lm.auth.rel   REL
```

其中 `.lm.auth.rel` 的重定位项数量非常大：

```text
Relocation section '.lm.auth.rel' contains 507065 entries
```

这说明题目并不是让我们运行程序输入 flag，而是把校验关系拆进了链接阶段的重定位信息里。

### 2. 定位输入符号

继续查看符号表：

```bash
readelf -s l11nk.o | grep '__lm_cacheline'
```

可以看到 26 个未定义符号：

```text
__lm_cacheline_00
__lm_cacheline_01
...
__lm_cacheline_25
```

这些符号对应 26 个输入位置。重定位表里大量 `R_MIPS_32` 项引用这些符号，把输入位置接入到 `.lm.auth` 中的布尔约束网络。

题目里也有一些看起来像校验提示或 flag 的字符串，但这些字符串主要是干扰项。真正有效的信息来自 `.lm.auth.rel` 的符号引用关系。

### 3. 还原最终数据

沿着真实约束链路还原后，可以得到最终用于解密的 26 字节密文：

```python
encrypted = bytes([
    19, 56, 63, 206, 229, 193, 249, 128, 214, 133, 92, 34, 77,
    5, 24, 105, 7, 55, 232, 165, 252, 138, 164, 184, 136, 126,
])
```

最后一层变换是线性异或流。第 `i` 个字节的 mask 为：

```text
(0x5A + 17 * i) & 0xff
```

所以解密公式为：

```text
plain[i] = encrypted[i] ^ ((0x5A + 17 * i) & 0xff)
```

完整脚本如下：

```python
import re

encrypted = bytes([
    19, 56, 63, 206, 229, 193, 249, 128, 214, 133, 92, 34, 77,
    5, 24, 105, 7, 55, 232, 165, 252, 138, 164, 184, 136, 126,
])

flag = bytes(
    c ^ ((0x5A + 17 * i) & 0xff)
    for i, c in enumerate(encrypted)
).decode("latin1")

assert re.fullmatch(r"ISCC\{[ -~]{20}\}", flag)
print(flag)
```

运行结果：

```text
ISCC{n9Q4vX7k2P0mLd8R5tYz}
```

## Flag

```text
ISCC{n9Q4vX7k2P0mLd8R5tYz}
```

## Notes

这题的关键点不是字符串搜索，而是识别它是一个可重定位目标文件，并把 `.lm.auth.rel` 当成逻辑关系图来分析。大量伪提示字符串会把方向带偏，真正的输入通道是 `__lm_cacheline_00` 到 `__lm_cacheline_25` 这组未定义符号。
