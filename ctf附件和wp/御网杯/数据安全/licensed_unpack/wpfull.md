# licensed_unpack 题解

## 一、先判断这是不是正常 UPX

原始文件是 `licensed.exe`。  
把它拖进 IDA 之后，节区名字会让人很自然想到 UPX：

- `.UPX0`
- `.UPX1`

入口伪代码也确实很像壳：

```c
qmemcpy(dword_402000, dword_412200, 0x243u);
JUMPOUT(0x402000);
```

如果只看这一步，很容易认为它只是一个小型自解压 stub：先把 `.UPX1` 的一段数据复制到 `.UPX0`，然后跳过去执行。

但这里有两个明显不对劲的地方：

1. 文件里不是标准 `UPX!`，而是 `FPX!`
2. `0x412200` 对应的文件偏移是：

```text
0x412200 - 0x412000 + 0x200 = 0x400
```

也就是说，程序实际复制的是文件偏移 `0x400` 开始的 `0x243` 字节。

可问题在于：**这段数据直接当代码执行根本跑不通。**

到这里基本可以判断，这个“拷贝再跳转”的逻辑只是烟雾弹，外观像 UPX，但并不是标准 UPX 壳。

## 二、真正的入口：从假代码里找压缩流

继续看 `0x41205B` 一带的数据，会出现这样一串字节：

```text
CE B6 14 3D 43 54 0E 0E 02 0E 0E 0E CC 0A 31 31
```

如果这是正常机器码，它完全不像一段合理的 stub。  
但这里有个很自然的联想：常见 zlib 压缩头往往是：

```text
78 01
78 9C
78 DA
```

于是尝试把这段内容按单字节 `0xCE` 做异或，结果前几个字节变成了：

```text
00 78 DA ...
```

这就很像：

- 前面有一个填充字节 `00`
- 后面接标准 `zlib` 压缩流 `78 DA`

说明这里不是“代码执行不了”，而是**这整段数据本质上是异或过的压缩数据**。

## 三、外层恢复：XOR + zlib

外层数据范围根据入口复制长度可以直接确定：

- 起点：`0x25B`
- 长度：`0x245`
- 异或键：`0xCE`

恢复流程：

1. 从原始 `licensed.exe` 中取出 `0x25B ~ 0x49F`
2. 整段逐字节异或 `0xCE`
3. 丢掉首字节 `00`
4. 用 `zlib.decompress()` 解压

解压后可以得到一个新的 PE 文件，而且文件头是标准 `MZ`。

## 四、内层文件的性质

把解压出的内层 PE 再拖进 IDA，可以发现它不是原生程序，而是一个**很小的 .NET PE**。

继续看类和字段，会注意到两个非常关键的字段名：

- `_bfk`
- `_bfct`

这两个名字已经给了很强的提示：

- `bfk` 可以理解成 `blowfish key`
- `bfct` 可以理解成 `blowfish ciphertext`

再往下看对应方法里的长度：

- `_bfk` 长度为 `0x10`，也就是 `16` 字节
- `_bfct` 长度为 `0x30`，也就是 `48` 字节

这个长度组合非常适合 Blowfish：

- Blowfish 密钥长度可以灵活设置
- 分组大小是 `8` 字节
- `48` 恰好是 `8` 的整数倍

## 五、怎样从内层 PE 里拿到 key 和 ct

这里不需要动态调试，直接按照 .NET PE 结构取数据就行。

思路如下：

1. 解析 DOS 头，找到 PE 头偏移
2. 解析节表，准备做 `RVA -> Raw` 转换
3. 定位 CLR Header（数据目录第 14 项）
4. 从 CLR Header 里拿到 Metadata 的 RVA 和大小
5. 将 Metadata 的 RVA 换算成文件偏移
6. `metadata_raw + metadata_size` 的位置，正好就是那两段静态字段数据

于是：

- `key_off = metadata_raw + metadata_size`
- `ct_off = key_off + 16`

从这里读出：

```text
key = d1db19c8a2e38c60c1518b0301c8d7ea
ct  = bdd6d58928d8b2427410d6a9a41f5ad63c1ad4bfd555cc714d1615bb8931b48f7ff81240b075048ae644fe513b1120d7
```

## 六、最后一步：Blowfish-ECB 解密

拿到 `key` 和 `ct` 之后，直接试 `Blowfish ECB`。

原因很简单：

- 字段名已经提示是 Blowfish
- 密文长度是 `48` 字节，正好是 `8` 字节分组的整数倍
- 不需要额外 IV

解密后去掉尾部 `00` 填充，得到明文：

```text
flag{b301cd43-2918-4c96-bc1e-0e6addbe3ef3}
```

## 七、完整 exp

我把完整利用链整理成了脚本：

- [exp_full.py](/D:/桌面/yuwang/数据安全/licensed_unpack/exp_full.py)

这个脚本是**从原始 `licensed.exe` 一步跑到最终 flag** 的版本，不再是只拿现成 `key/ct` 验证。

运行方式：

```bash
python exp_full.py licensed.exe -o inner.exe
```

功能包括：

1. 取出外层伪壳数据
2. 异或 `0xCE`
3. zlib 解压得到内层 PE
4. 解析 CLR Header 和 Metadata
5. 提取 Blowfish key / ciphertext
6. 解密输出 flag

## 八、最终 flag

```text
flag{b301cd43-2918-4c96-bc1e-0e6addbe3ef3}
```
