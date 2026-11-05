# rerere Writeup

## 题目信息

- 题目名称：`rerere`
- 题目分类：`REVERSE`
- 题目难度：初级
- 题目附件：`rerere.exe`

## 程序行为

运行程序后会提示输入：

```text
Input:
```

输入错误时输出：

```text
Wrong!
```

输入正确时输出：

```text
Correct!
```

## 主函数分析

查看反编译代码，主要逻辑在 `sub_1400014FB` 中。

程序使用 `fgets` 读取输入，然后去掉末尾换行符。之后先判断输入长度是否为 `38`，长度正确才会进入校验函数。

核心逻辑可以简化为：

```c
fgets(buf, 64, stdin);

if (strlen(buf) == 38 && check(buf, 38))
    puts("Correct!");
else
    puts("Wrong!");
```

因此可以确定，正确输入长度为 `38`。

## 校验函数分析

真正的校验逻辑在 `sub_140001480`，可以整理成下面的形式：

```c
for (int i = 0; i < len; i++) {
    if (sbox[input[i] ^ key[i & 7]] != target[i])
        return 0;
}
return 1;
```

这里用到了三组关键数据：

- `target`：虚拟地址 `0x140004020`，长度 `38`
- `key`：虚拟地址 `0x140004048`，长度 `8`
- `sbox`：虚拟地址 `0x140004060`，长度 `256`

校验公式为：

```text
sbox[input[i] ^ key[i % 8]] == target[i]
```

由于 `sbox` 是 256 字节查表，可以先建立逆表：

```text
inverse_sbox[sbox[x]] = x
```

然后反推输入：

```text
input[i] = inverse_sbox[target[i]] ^ key[i % 8]
```

## exp 思路

本题的 `exp.py` 没有直接写死 `target`、`key` 和 `sbox` 的完整内容，而是从 `rerere.exe` 中自动读取。

IDA 里看到的地址是虚拟地址，例如 `0x140004020`。如果要直接从文件中取数据，需要把虚拟地址转换成文件偏移。

脚本处理流程如下：

1. 读取 `rerere.exe` 文件内容。
2. 从 DOS 头 `0x3C` 处读取 `e_lfanew`，定位 PE 头。
3. 从 PE 头中读取节数量和 Optional Header 大小。
4. 根据节表找到目标 RVA 所属的节。
5. 使用 `PointerToRawData + (RVA - VirtualAddress)` 计算文件偏移。
6. 分别读取 `target`、`key`、`sbox`。
7. 建立 `sbox` 逆表，逐字节恢复 flag。

这样写的好处是脚本直接依赖附件本身，复现时只需要保证 `exp.py` 和 `rerere.exe` 在同一目录。

## 关键代码说明

脚本中 `BASE` 是程序镜像基址：

```python
BASE = 0x140000000
```

虚拟地址转 RVA：

```python
rva = va - BASE
```

RVA 转文件偏移：

```python
raw_address + (rva - virtual_address)
```

读取三组数据：

```python
target = read_va(data, 0x140004020, 38)
key = read_va(data, 0x140004048, 8)
table = read_va(data, 0x140004060, 256)
```

建立逆表并恢复输入：

```python
inverse_table = [0] * 256
for index, value in enumerate(table):
    inverse_table[value] = index

flag = bytearray()
for i, value in enumerate(target):
    flag.append(inverse_table[value] ^ key[i % len(key)])
```

## exp.py

```python
import struct
from pathlib import Path


BASE = 0x140000000
BINARY = Path(__file__).with_name("rerere.exe")


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def rva_to_file_offset(data, rva):
    pe_offset = u32(data, 0x3C)
    section_count = u16(data, pe_offset + 6)
    optional_header_size = u16(data, pe_offset + 20)
    section_table = pe_offset + 24 + optional_header_size

    for i in range(section_count):
        entry = section_table + i * 40
        virtual_size = u32(data, entry + 8)
        virtual_address = u32(data, entry + 12)
        raw_size = u32(data, entry + 16)
        raw_address = u32(data, entry + 20)
        size = max(virtual_size, raw_size)

        if virtual_address <= rva < virtual_address + size:
            return raw_address + (rva - virtual_address)

    raise ValueError(f"RVA not found: 0x{rva:x}")


def read_va(data, va, size):
    return data[rva_to_file_offset(data, va - BASE):][:size]


def main():
    data = BINARY.read_bytes()

    target = read_va(data, 0x140004020, 38)
    key = read_va(data, 0x140004048, 8)
    table = read_va(data, 0x140004060, 256)

    inverse_table = [0] * 256
    for index, value in enumerate(table):
        inverse_table[value] = index

    flag = bytearray()
    for i, value in enumerate(target):
        flag.append(inverse_table[value] ^ key[i % len(key)])

    print(flag.decode())


if __name__ == "__main__":
    main()
```

## 运行结果

运行：

```bash
python exp.py
```

得到：

```text
flag{b9481d6da561ee61edd3ea6f5dca9e25}
```

## 验证

将结果输入原程序，程序输出：

```text
Input: Correct!
```

说明结果正确。

## 最终 flag

```text
flag{b9481d6da561ee61edd3ea6f5dca9e25}
```
